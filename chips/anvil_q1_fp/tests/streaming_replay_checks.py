#!/usr/bin/env python3
"""Compact real-RTL replay/corruption regression, never full-model evidence."""

import argparse
import copy
import gzip
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import Validator, load_json, require, sha
from streaming_production import compare_window
from streaming_replay import (Process, Resolver, item, now, specification, validate_manifest,
                              vector_descriptor, write_new)
from verify import Evidence, ROOT


def worker(args):
    directory = ROOT / args.destination
    tokens = load_json(ROOT / args.tokens)
    replaying = directory.parent.name.startswith("replay-")
    for position, token in enumerate(tokens):
        if replaying and args.defect == "missing-window" and position == 1:
            return 0
        window = directory / f"position-{position}"
        window.mkdir()
        values = [(index + 1) / 4 for index in range(8)]
        expected = [math.fsum([value] * 8 + [float(position)]) for value in values]
        if args.role != "reference":
            stimulus = directory / f"stimulus-{position}.txt"
            output = directory / f"observed-{position}.txt"
            mode = 1 if args.mode == "bf16" else 2
            with stimulus.open("x") as stream:
                for value in values:
                    def encoding(number):
                        if mode == 1:
                            return struct.unpack("<I", struct.pack("<f", number))[0] >> 16
                        return struct.unpack("<H", struct.pack("<e", number))[0]
                    a = sum(encoding(value) << (16*lane) for lane in range(8))
                    b = sum(encoding(1.) << (16*lane) for lane in range(8))
                    seed = struct.unpack("<I", struct.pack("<f", position))[0]
                    stream.write(f"1 1 {mode} {a:032x} {b:032x} ff {seed:08x} 3f000000\n")
                for _ in range(30):
                    stream.write(f"1 0 {mode} 0 0 0 0 0\n")
            with (directory / f"rtl-{position}.stdout").open("xb") as stdout, (
                    directory / f"rtl-{position}.stderr").open("xb") as stderr:
                argv = ["vvp", args.executable, "+input=" + str(stimulus.relative_to(ROOT)),
                        "+output=" + str(output.relative_to(ROOT))]
                started = now()
                completed = subprocess.run(
                    argv,
                    cwd=ROOT, stdout=stdout, stderr=stderr, timeout=3600, check=False)
            write_new(directory / f"rtl-{position}.json", dict(
                argv=argv, cwd=".", started_at=started, ended_at=now(),
                timeout_s=3600, timed_out=False, exit_code=completed.returncode,
                stdout=item(ROOT, directory / f"rtl-{position}.stdout"),
                stderr=item(ROOT, directory / f"rtl-{position}.stderr"),
                inputs=[item(ROOT, ROOT / args.executable), item(ROOT, stimulus)],
                output=item(ROOT, output)))
            require(completed.returncode == 0, "compact RTL execution failed")
            observed = []
            for line in output.read_text().splitlines():
                fields = line.split()
                if fields[1] == "1":
                    require(fields[3] == "00", "unexpected compact arithmetic exception")
                    observed.append(struct.unpack("<f", struct.pack("<I", int(fields[2], 16)))[0])
            require(len(observed) == 8 and observed == expected,
                    "real RTL differs from independent FP64 dot inference")
            if args.defect == "numerical":
                observed[0] = 100.
            if args.defect == "repeat-only":
                observed[0] += .125
            for name, width in (("layers", 24*896), ("logits", 151936)):
                raw = struct.pack("<8f", *observed) * (width // 8)
                with (window / (name + ".f32")).open("xb") as stream:
                    stream.write(raw)
            # Synthetic serialization fixture; not a production memory trace.
            (window / "transactions.u32.gz").write_bytes(
                gzip.compress(struct.pack("<11I", 1, 0, 3, 0, 0, 8, 0, 0, 0, 0, 0), mtime=0))
        else:
            for prefix in ("selected-", "checkpoint-"):
                for name, width in (("layers", 24*896), ("logits", 151936)):
                    raw = struct.pack("<8d", *expected) * (width // 8)
                    with (window / (prefix + name + ".f64")).open("xb") as stream:
                        stream.write(raw)
        write_new(window / "window.json", dict(position=position, token_id=token))
        if replaying and position == 1:
            if args.defect == "altered":
                path = window / "logits.f32"
                with path.open("r+b") as stream:
                    first = stream.read(1)
                    stream.seek(0)
                    stream.write(bytes([first[0] ^ 1]))
            elif args.defect == "truncated":
                with (window / "logits.f32").open("r+b") as stream:
                    stream.truncate(151936*4 - 1)
        emitted_position = 2 if replaying and position == 1 and args.defect == "reordered" else position
        print(f"WINDOW_READY {emitted_position}", flush=True)
        require(sys.stdin.readline() == f"ACK {position}\n", "fixture ACK missing")
    write_new(directory / "summary.json", dict(positions_completed=len(tokens), fixture=True))
    return 0


def origin(ev, executable, tokens, mode, role, defect="pristine"):
    entry = item(ROOT, executable)
    token_entry = item(ROOT, tokens)
    argv = ["python3", "tests/streaming_replay_checks.py", "--worker",
            "--destination", "{output}", "--tokens", token_entry["path"],
            "--executable", entry["path"], "--mode", mode, "--role", role, "--defect", defect]
    spec = specification(ROOT, argv=argv, output_index=4, role=role, case="synthetic/compact-dot",
                         mode=mode, workload="teacher", tokens=load_json(tokens),
                         inputs={entry["path"]: entry["sha256"],
                                 token_entry["path"]: token_entry["sha256"]},
                         tool_names=("python3", "vvp"), fixture=True)
    return Process(ROOT, ev.path / f"{mode}-{role}-{defect}-{uuid.uuid4().hex}",
                   spec, 3600, allow_fixture=True)


def collect_origins(ev, executable, tokens, mode):
    processes = []
    try:
        for role in ("observation", "repeat", "reference"):
            processes.append(origin(ev, executable, tokens, mode, role))
        all_metrics = []
        for position in range(3):
            for process in processes:
                process.next()
            all_metrics.extend(compare_window(ROOT, ev, *processes, mode,
                                               f"original/{mode}/{position}"))
            for process in processes:
                process.release()
        manifests = []
        for process in processes:
            process.finish()
            manifests.append(process.seal())
        require(len({process.record["execution_id"] for process in processes}) == 3 and
                len({process.record["pid"] for process in processes}) == 3,
                "original reset-origin executions were substituted")
        require(all(not any(process.output.glob("position-*")) for process in processes),
                "original transient arrays were not released")
        return processes, manifests, all_metrics
    finally:
        for process in processes:
            if not process.finished:
                process.abort()


def replay_comparisons(ev, processes, manifests, mode):
    resolver = Resolver(ROOT, ev, allow_fixture=True)
    validator = Validator(ROOT, ev)
    # Only the fixture regression opts into compact recipes. Normal validation
    # creates a production-only resolver.
    validator.replay = resolver
    success = False
    try:
        for position in range(3):
            def vector(index, name, dtype, width, offset=0):
                return vector_descriptor(ROOT, manifests[index],
                                         dict(windows=processes[index].windows),
                                         position, name, dtype, width, offset)
            for layer in range(24):
                a = vector(0, "layers.f32", "<f4", 896, layer*896*4)
                b = vector(1, "layers.f32", "<f4", 896, layer*896*4)
                reference = vector(2, "selected-layers.f64", "<f8", 896, layer*896*8)
                validator.arrays(a, reference, b, 896, (.9999, .002),
                                 f"original/{mode}/{position}/layers/{layer}")
            a = vector(0, "logits.f32", "<f4", 151936)
            b = vector(1, "logits.f32", "<f4", 151936)
            reference = vector(2, "selected-logits.f64", "<f8", 151936)
            checkpoint = vector(2, "checkpoint-logits.f64", "<f8", 151936)
            validator.arrays(a, reference, b, 151936, (.999, .01),
                             f"original/{mode}/{position}/logits/0")
            validator.arrays(reference, checkpoint, reference, 151936, (-1, float("inf")),
                             f"original/{mode}/{position}/storage-quantization", wide=True)
        success = True
    finally:
        resolver.close(success)
    return validator.metrics


def rejection(ev, name, operation, diagnostic):
    try:
        operation()
    except (ValueError, OSError, KeyError) as error:
        require(diagnostic in str(error), f"{name}: wrong rejection: {error}")
        ev.assertion("reject_" + name, True, diagnostic=str(error),
                     scope="synthetic compact replay regression")
        return
    raise ValueError(name + " escaped unchanged assertion")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--destination")
    parser.add_argument("--tokens")
    parser.add_argument("--executable")
    parser.add_argument("--mode", choices=("bf16", "fp16"))
    parser.add_argument("--role", choices=("observation", "repeat", "reference"))
    parser.add_argument("--defect", default="pristine")
    args = parser.parse_args()
    if args.worker:
        return worker(args)
    ev = Evidence("streaming-replay")
    passed = False
    try:
        original_failure = ROOT / "evidence/preparation/verifier-production-simulation-6s9_bb4j/receipt.json"
        if original_failure.is_file():
            ev.receipt["diagnosed_failure"] = item(ROOT, original_failure)
        previous = ROOT / "evidence/preparation/verifier-streaming-replay-v5_veqlg/receipt.json"
        if previous.is_file():
            ev.receipt["repair_of"] = item(ROOT, previous)
        require(ev.run("python-version", ["python3", "--version"], timeout=3600) and
                ev.run("icarus-version", ["iverilog", "-V"], timeout=3600) and
                ev.run("vvp-version", ["vvp", "-V"], timeout=3600),
                "required compact simulation tools unavailable")
        executable = ev.path / "leaf.vvp"
        require(ev.run("compact-leaf-build", [
            "iverilog", "-g2012", "-Wall", "-DICARUS_SMOKE", "-s", "leaf_tb",
            "-o", str(executable.relative_to(ROOT)),
            *[str(path.relative_to(ROOT)) for path in sorted((ROOT / "rtl").glob("*.sv"))],
            "tests/leaf_tb.sv"], timeout=3600), "compact real-RTL build failed")
        tokens = ev.path / "fixture-tokens.json"
        write_new(tokens, [17, 53, 89])
        bindings = None
        for mode in ("bf16", "fp16"):
            processes, manifests, expected = collect_origins(ev, executable, tokens, mode)
            actual = replay_comparisons(ev, processes, manifests, mode)
            # The collection walks layers before logits in compare_window too.
            require(actual == expected and len(actual) == 78,
                    "fresh replay numerical comparisons differ from original bytes")
            ev.assertion("actual_rtl_and_independent_fp64_replay_" + mode, True,
                         numerical_comparisons=len(actual), original_processes=3,
                         original_manifest=manifests, full_model_execution=False,
                         geometry="compact dot8, expanded synthetic vector fixtures")
            bindings = processes, manifests
        processes, manifests = bindings
        pristine = load_json(ROOT / manifests[0]["path"])

        def altered_manifest(name, change):
            value = copy.deepcopy(pristine)
            change(value)
            path = ev.path / (name + ".json")
            write_new(path, value)
            return item(ROOT, path)

        for name, change, diagnostic in (
            ("missing-prerequisite",
             lambda value: value["spec"]["inputs"].update({
                 str((ev.path / "absent-replay-input").relative_to(ROOT)): "0"*64}),
             "missing or altered replay prerequisite"),
            ("missing-window", lambda value: value["windows"].pop(), "incomplete replay window coverage"),
            ("reordered-windows", lambda value: value["windows"].reverse(), "incomplete/reordered replay coverage"),
            ("incomplete-vectors", lambda value: value["windows"][0]["vectors"].pop(),
             "incomplete/reordered per-vector digest coverage"),
            ("reordered-vectors", lambda value: value["windows"][0]["vectors"].reverse(),
             "incomplete/reordered per-vector digest coverage"),
            ("changed-source", lambda value: value["spec"]["source_sha256"].update(
                {"tests/streaming_replay.py": "0"*64}), "replay sources changed"),
        ):
            descriptor = altered_manifest(name, change)
            rejection(ev, name, lambda descriptor=descriptor: validate_manifest(
                ROOT, descriptor, allow_fixture=True), diagnostic)
        rejection(ev, "substituted-repeat-origin", lambda: validate_manifest(
            ROOT, manifests[0], role="repeat", allow_fixture=True),
            "substituted repeat/reference origin")
        rejection(ev, "fixture-as-full-model", lambda: validate_manifest(ROOT, manifests[0]),
                  "fixture cannot establish production replay")
        rejection(ev, "ordinary-missing-artifact", lambda: Validator(ROOT, ev).artifact(
            dict(path=str((ev.path / "missing.f32").relative_to(ROOT)), sha256="0"*64)),
            "missing artifact:")
        resolver = Resolver(ROOT, ev, allow_fixture=True)
        context_validator = Validator(ROOT, ev)
        context_validator.replay = resolver
        vector = vector_descriptor(ROOT, manifests[0], pristine, 0,
                                   "logits.f32", "<f4", 151936)
        for name, case, mode, workload, contexts, position, payload in (
            ("case", "other-case", "fp16", "teacher", [17, 53, 89], 0, "logits.f32"),
            ("mode", "synthetic/compact-dot", "bf16", "teacher", [17, 53, 89], 0, "logits.f32"),
            ("context", "synthetic/compact-dot", "fp16", "teacher", [17, 53, 90], 0, "logits.f32"),
            ("workload", "synthetic/compact-dot", "fp16", "greedy", [17, 53, 89], 0, "logits.f32"),
            ("position", "synthetic/compact-dot", "fp16", "teacher", [17, 53, 89], 1, "logits.f32"),
            ("payload", "synthetic/compact-dot", "fp16", "teacher", [17, 53, 89], 0, "layers.f32"),
        ):
            rejection(ev, "substituted-" + name, lambda case=case, mode=mode, workload=workload,
                      contexts=contexts, position=position, payload=payload:
                      context_validator.replay_context(
                          vector, case, mode, workload, contexts, position, payload, "<f4", 151936),
                      "replay case/mode/context substituted" if name in
                      ("case", "mode", "context", "workload") else
                      "replay numerical vector substituted/reordered")
        resolver.close(False)
        for defect, diagnostic in (
            ("altered", "replayed payload/ordered observation differs"),
            ("truncated", "truncated replay vector"),
            ("missing-window", "producer ended before complete ordered coverage"),
            ("reordered", "incomplete/reordered replay coverage"),
        ):
            process = origin(ev, executable, tokens, "bf16", "observation", defect)
            try:
                for _ in range(3):
                    process.next()
                    process.release()
                process.finish()
                manifest = process.seal()
            finally:
                if not process.finished:
                    process.abort()
            resolver = Resolver(ROOT, ev, allow_fixture=True)
            descriptor = vector_descriptor(ROOT, manifest, dict(windows=process.windows),
                                           2, "logits.f32", "<f4", 151936)
            try:
                rejection(ev, "replay-" + defect,
                          lambda: resolver.read(descriptor, "<f4", 151936), diagnostic)
            finally:
                resolver.close(False)
        # A digest-only implementation cannot pass: both originals contain the
        # same numerical defect, and the unchanged fidelity assertion rejects it.
        bad = []
        try:
            for role in ("observation", "repeat"):
                bad.append(origin(ev, executable, tokens, "bf16", role, "numerical"))
            bad.append(origin(ev, executable, tokens, "bf16", "reference", "numerical"))
            for process in bad:
                process.next()
            rejection(ev, "shared-numerical-defect", lambda: compare_window(
                ROOT, ev, *bad, "bf16", "injected-shared-error"), "numerical fidelity failed")
        finally:
            for process in bad:
                process.abort()
        bad = []
        try:
            bad.append(origin(ev, executable, tokens, "bf16", "observation"))
            bad.append(origin(ev, executable, tokens, "bf16", "repeat", "repeat-only"))
            for process in bad:
                process.next()
            rejection(ev, "independent-repeat-payload", lambda: compare_window(
                ROOT, ev, *bad, None, "bf16", "repeat-corruption"), "nondeterministic output")
        finally:
            for process in bad:
                process.abort()
        from benchmark_fixtures import library_entrypoint_check
        require(library_entrypoint_check(ROOT, ev), "benchmark library entrypoint regressed")
        passed = True
    except (ValueError, OSError, KeyError, ImportError) as error:
        ev.assertion("streaming_replay_regression_failure", False, diagnostic=str(error))
        print(str(error), file=sys.stderr, flush=True)
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path) for path in ev.path.rglob("*")
            if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if passed else "failed")
        print(json.dumps(dict(status=ev.receipt["status"],
                              receipt=str((ev.path / "receipt.json").relative_to(ROOT)),
                              full_model_execution=False, benchmark_acceptance=False)), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
