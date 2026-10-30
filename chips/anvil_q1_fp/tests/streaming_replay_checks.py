#!/usr/bin/env python3
"""Compact real-RTL replay/corruption regression, never full-model evidence."""

import argparse
import copy
import gzip
import json
import math
from pathlib import Path
import queue
import shutil
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import Validator, load_json, require, sha
from streaming_production import compare_window
from streaming_replay import (Process, Resolver, data_bindings, forward_progress, item, now, production_bindings,
                              specification, validate_manifest, validate_spec,
                              vector_descriptor, write_new)
from verify import Evidence, ROOT


def worker(args):
    directory = ROOT / args.destination
    tokens = load_json(ROOT / args.tokens)
    replaying = directory.parent.name.startswith("replay-")
    for position, token in enumerate(tokens):
        if args.defect in ("progress-gated", "failed-child", "failed-exit", "ordered-progress"):
            print(f"PROGRESS cycle={(position+1)*10000000} requests={position+1}"
                  f" responses={position+1} position={position} layers=0 logits=0", flush=True)
        if args.defect == "progress-gated" and position == 0:
            require(sys.stdin.readline() == "CONTINUE\n", "fixture progress gate missing")
        if args.defect == "failed-child":
            (directory / "failed.partial").write_bytes(b"retain failed producer bytes")
            print("injected fixture child failure", file=sys.stderr, flush=True)
            return 7
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
            if args.defect == "nonfinite":
                observed[0] = float("nan")
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
        emitted_position = (position + 1 if args.defect == "ordered-progress" else
                            2 if replaying and position == 1 and args.defect == "reordered"
                            else position)
        print(f"WINDOW_READY {emitted_position}", flush=True)
        require(sys.stdin.readline() == f"ACK {position}\n", "fixture ACK missing")
        if args.defect in ("progress-gated", "awaiting-ack", "failed-exit"):
            write_new(directory / f"ack-{position}.json", dict(position=position))
    if args.defect == "failed-exit":
        (directory / "failed.partial").write_bytes(b"retain failed producer exit")
        print("injected fixture failed exit", file=sys.stderr, flush=True)
        return 7
    write_new(directory / "summary.json", dict(positions_completed=len(tokens), fixture=True))
    return 0


def origin(ev, executable, tokens, mode, role, defect="pristine", *, progress=forward_progress):
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
                   spec, 3600, allow_fixture=True, progress=progress)


def progress_checks(ev, executable, tokens):
    events = queue.Queue()
    captured = []

    def observe(event):
        forward_progress(event)
        events.put(event)

    processes = []
    try:
        for role in ("observation", "repeat", "reference"):
            processes.append(origin(
                ev, executable, tokens, "bf16", role,
                "awaiting-ack" if role == "reference" else "progress-gated", progress=observe))
        actual, repeated, reference = processes
        with ThreadPoolExecutor(max_workers=1) as executor:
            waiting = executor.submit(actual.next)
            try:
                pending = {process.record["execution_id"]: process for process in processes}
                while pending:
                    event = events.get(timeout=3600)
                    captured.append(event)
                    process = pending.pop(event["execution_id"])
                    require(event == dict(
                        event="producer_window_ready" if process is reference else "producer_progress",
                        role=process.spec["role"], execution_id=process.record["execution_id"],
                        case=process.spec["case"], mode="bf16", workload="teacher",
                        message="WINDOW_READY 0" if process is reference else
                        "PROGRESS cycle=10000000 requests=1 responses=1 position=0 layers=0 logits=0"),
                        "producer progress identity/message differs")
                require(not waiting.done() and actual.current is None and
                        all(process.process.poll() is None for process in processes) and
                        all(not list(process.output.glob("ack-*.json")) for process in processes) and
                        all(not (process.output / "position-0").exists()
                            for process in (actual, repeated)),
                        "progress forwarding completed or acknowledged an unfinished window")
                ev.assertion("genuine_progress_visible_before_window_while_next_waits", True,
                             roles=[event["role"] for event in captured],
                             execution_ids=[event["execution_id"] for event in captured])
                require(reference.current is None and reference.position == -1 and
                        (reference.output / "position-0/window.json").is_file(),
                        "reference readiness was consumed or suppressed behind observation")
                reference.next()
                require(reference.current is not None and
                        not (reference.output / "ack-0.json").exists() and
                        reference.process.poll() is None,
                        "reference window did not wait for comparison/ACK")
                ev.assertion("reference_window_reported_without_premature_ack", True,
                             execution_id=reference.record["execution_id"])
                for process in (actual, repeated):
                    process.process.stdin.write(b"CONTINUE\n")
                    process.process.stdin.flush()
                waiting.result(timeout=3600)
                repeated.next()
                for position in range(3):
                    if position:
                        for process in processes:
                            process.next()
                    require(all(process.position == position for process in processes),
                            "progress changed ordered window positions")
                    metrics = compare_window(ROOT, ev, *processes, "bf16",
                                             f"progress-protocol/{position}")
                    require(len(metrics) == 26, "progress fixture comparisons missing")
                    for process in processes:
                        process.release()
                for process in processes:
                    process.finish()
                    require(not any(process.output.glob("position-*")) and
                            [load_json(process.output / f"ack-{position}.json")["position"]
                             for position in range(3)] == [0, 1, 2],
                            "verified window disposal or ordered ACKs changed")
                    raw = (process.directory / "stdout.txt").read_bytes()
                    require(all(f"WINDOW_READY {position}\n".encode() in raw
                                for position in range(3)) and
                            (process is reference or b"PROGRESS cycle=10000000 " in raw),
                            "forwarding lost raw producer output")
                ev.assertion("progress_preserves_three_ordered_compared_released_windows", True,
                             positions=3, producers=3, numerical_comparisons=78,
                             full_model_execution=False)
            finally:
                # Settle a gated fixture even when an assertion fails.
                for process in processes:
                    if not process.finished:
                        process.abort()
    finally:
        for process in processes:
            if not process.finished:
                process.abort()
        while not events.empty():
            captured.append(events.get_nowait())
        write_new(ev.path / "progress-events.json", captured)

    filtered = []
    probe = SimpleNamespace(spec=actual.spec, record=actual.record,
                            last_progress=float("-inf"), progress=filtered.append)
    raw = b"PROGRESS cycle=10000000 requests=1 responses=1 position=0 layers=0 logits=0\n"
    with patch("streaming_replay.time.monotonic", side_effect=[0., .5, 1.]):
        for _ in range(3):
            Process._progress(probe, raw)
    for line in (b"unrelated log\n", b"PROGRESS unparsed\n",
                 b"PROGRESS cycle=" + b"1"*1000 + b"\n", b"WINDOW_READY malformed\n"):
        Process._progress(probe, line)
    Process._progress(probe, b"WINDOW_READY 1\n")
    require(len(filtered) == 3 and
            [entry["event"] for entry in filtered] ==
            ["producer_progress", "producer_progress", "producer_window_ready"],
            "progress output is not bounded/filtered or suppressed window readiness")
    ev.assertion("progress_rate_and_message_bounds_without_keepalives", True,
                 progress_per_second=1, forwarded=3, malformed_or_unrelated=4,
                 scope="synthetic filtering only; no live progress fabricated")

    for defect, diagnostic in (
        ("failed-child", "producer ended before complete ordered coverage"),
        ("failed-exit", "replay producing process failed"),
        ("ordered-progress", "incomplete/reordered replay coverage"),
    ):
        process = origin(ev, executable, tokens, "bf16", "observation", defect)
        try:
            def operation():
                for _ in range(3):
                    process.next()
                    process.release()
                process.finish()
            rejection(ev, "progress-" + defect, operation, diagnostic)
            if defect.startswith("failed-"):
                process.process.wait(timeout=3600)
        finally:
            if not process.finished:
                process.abort()
        record = load_json(process.directory / "process.json")
        require(record["exit_code"] == process.process.returncode and
                not record["timed_out"], "failed producer exit not retained")
        if defect.startswith("failed-"):
            require(record["exit_code"] == 7 and
                    (process.output / "failed.partial").is_file() and
                    b"injected fixture" in (process.directory / "stderr.txt").read_bytes(),
                    "failed child status/raw bytes lost")
        else:
            require((process.output / "position-0/logits.f32").is_file() and
                    not process.windows, "unordered failed window was acknowledged/disposed")
        rejection(ev, "seal-progress-" + defect, process.seal, "cannot seal a failed producer")
        ev.assertion("progress_failure_retention_" + defect, True,
                     execution=item(ROOT, process.directory / "process.json"))


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


def binding_checks(ev):
    """Exercise collection and production replay binding rules without a model run."""
    root = ev.path / ("binding-pristine-" + uuid.uuid4().hex)
    data = root / "tests/data"
    data.mkdir(parents=True)
    descriptors = {}
    for name in ("checkpoint", "tokenizer", "chat-template", "corpus", "calibration",
                 "recipe", "layout", "weights", "zeros", "scales"):
        path = data / (name + ".bin")
        path.write_bytes(("binding-fixture:" + name).encode())
        descriptors[name] = item(root, path)
    tokens = data / "tokens.json"
    write_new(tokens, [17, 53, 89])
    descriptors["tokens"] = item(root, tokens)
    # A real dependency in evidence/preparation must still be checked. Only the
    # explicit manifest field, not a path prefix, determines advisory status.
    real_path = root / "evidence/preparation/real-input-fixture/recipe.json"
    real_path.parent.mkdir(parents=True)
    write_new(real_path, {"fixture": True})
    descriptors["preparation-path-input"] = item(root, real_path)
    advisory = dict(path="evidence/preparation/absent-history-fixture/receipt.json",
                    sha256="0"*64)
    model = dict(revision="fixed-binding-fixture-revision",
                 checkpoint=[descriptors["checkpoint"]],
                 tokenizer=descriptors["tokenizer"], chat_template=descriptors["chat-template"],
                 streams={"fixture": {name: descriptors[name]
                                      for name in ("layout", "weights", "zeros", "scales")}},
                 quantization={name: descriptors[name] for name in ("calibration", "recipe")},
                 executable_recipe=descriptors["preparation-path-input"],
                 preparation_receipts=[advisory])
    suite = dict(corpus=descriptors["corpus"], teacher_tokens=descriptors["tokens"])
    write_new(data / "model_manifest.json", model)
    write_new(data / "benchmark_manifest.json", suite)
    inputs = production_bindings(root, model, suite)
    require(len(inputs) == len(descriptors) + 2 and advisory["path"] not in inputs and
            all(inputs[entry["path"]] == entry["sha256"] for entry in descriptors.values()),
            "advisory exclusion dropped executable data or manifests")
    spec = specification(
        root, argv=["python3", "tests/streaming_replay.py", "--reference-worker",
                    "--tokens", descriptors["tokens"]["path"], "--destination",
                    "{output}", "--mode", "bf16"],
        output_index=6, role="reference", case="synthetic/binding-only", mode="bf16",
        workload="teacher", tokens=[17, 53, 89], inputs=inputs, tool_names=("python3",))
    validate_spec(root, spec)
    ev.assertion("missing_advisory_history_not_execution_input", True,
                 bound_inputs=len(inputs), production_execution=False)

    import production_sim
    args = SimpleNamespace(build_only=True, qualify_trace=False, qualify_comparisons=False,
                           build_receipt=None)
    preparation = SimpleNamespace(
        receipt={}, assertion=lambda name, passed, **details: ev.assertion(
            "binding_fixture_" + name, passed, simulator_compilation_mocked=True, **details))

    def prepare(project, documents):
        with patch.object(production_sim, "ROOT", project), patch(
                "teacher_reference.validate_inputs", return_value=(*documents, {}, {})), patch.object(
                    production_sim, "compile_simulator", return_value=None) as compiler:
            production_sim.run_collection(preparation, args)
            compiler.assert_called_once_with(preparation, None)

    prepare(root, (model, suite))
    ev.assertion("collection_preparation_ignores_absent_advisory_receipts", True,
                 simulator_compilation_mocked=True, production_execution=False)
    advisory_path = root / advisory["path"]
    advisory_path.parent.mkdir(parents=True)
    advisory_path.write_bytes(b"not the recorded historical receipt")
    require(production_bindings(root, model, suite) == inputs,
            "advisory receipt bytes altered executable input bindings")
    validate_spec(root, spec)
    ev.assertion("altered_advisory_history_not_execution_input", True)

    for name, descriptor in descriptors.items():
        for defect in ("missing", "altered"):
            project = ev.path / ("binding-" + name + "-" + defect + "-" + uuid.uuid4().hex)
            shutil.copytree(root, project)
            path = project / descriptor["path"]
            if defect == "missing":
                path.unlink()
            else:
                path.write_bytes(b"altered executable prerequisite")
            documents = (load_json(project / "tests/data/model_manifest.json"),
                         load_json(project / "tests/data/benchmark_manifest.json"))
            rejection(ev, name + "-" + defect + "-collection",
                      lambda: production_bindings(project, *documents),
                      "missing or altered replay prerequisite")
            rejection(ev, name + "-" + defect + "-replay",
                      lambda: validate_spec(project, spec), "missing or altered replay prerequisite")
            with patch.object(production_sim, "ROOT", project), patch(
                    "teacher_reference.validate_inputs", return_value=(*documents, {}, {})), patch.object(
                        production_sim, "compile_simulator",
                        side_effect=AssertionError("expensive compilation preceded binding preflight")) as compiler:
                rejection(ev, name + "-" + defect + "-before-build",
                          lambda: production_sim.run_collection(preparation, args),
                          "missing or altered replay prerequisite")
                compiler.assert_not_called()
        incomplete = copy.deepcopy(spec)
        incomplete["inputs"].pop(descriptor["path"])
        rejection(ev, name + "-omitted-replay-binding",
                  lambda: validate_spec(root, incomplete),
                  "incomplete replay model/dataset input bindings")

    conflict = copy.deepcopy(suite)
    conflict["duplicate_checkpoint"] = {
        **descriptors["checkpoint"], "sha256": "0"*64}
    rejection(ev, "conflicting-executable-hashes-collection",
              lambda: production_bindings(root, model, conflict),
              "conflicting replay input hashes")
    project = ev.path / ("binding-conflicting-replay-" + uuid.uuid4().hex)
    shutil.copytree(root, project)
    suite_path = project / "tests/data/benchmark_manifest.json"
    suite_path.write_text(json.dumps(conflict))
    conflicting_spec = copy.deepcopy(spec)
    conflicting_spec["inputs"][str(suite_path.relative_to(project))] = sha(suite_path)
    rejection(ev, "conflicting-executable-hashes-replay",
              lambda: validate_spec(project, conflicting_spec), "conflicting replay input hashes")
    nested = {"execution": {"preparation_receipts": [advisory]}}
    rejection(ev, "nested-field-not-an-advisory-exemption",
              lambda: data_bindings(root, nested), "missing or altered replay prerequisite")
    for manifest in ("model_manifest", "benchmark_manifest"):
        project = ev.path / ("binding-altered-" + manifest + "-" + uuid.uuid4().hex)
        shutil.copytree(root, project)
        path = project / ("tests/data/" + manifest + ".json")
        path.write_text(path.read_text() + "\n")
        rejection(ev, "altered-hash-bound-" + manifest,
                  lambda: validate_spec(project, spec), "missing or altered replay prerequisite")


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
        progress_failure = ROOT / "evidence/preparation/verifier-production-simulation-ogwn3_h7/receipt.json"
        ev.receipt["progress_repair_diagnosis"] = dict(
            attempt=758, receipt_path=str(progress_failure.relative_to(ROOT)),
            receipt_present=progress_failure.is_file(),
            scope="producer observability only; no production restart or throughput qualification")
        if progress_failure.is_file():
            ev.receipt["progress_repair_diagnosis"]["receipt"] = item(ROOT, progress_failure)
        attempt701 = ROOT / "evidence/preparation/verifier-production-simulation-boqrk5kr/receipt.json"
        if attempt701.is_file():
            ev.receipt["repair_of"] = item(ROOT, attempt701)
            ev.receipt["diagnosed_attempt"] = 701
        original_failure = ROOT / "evidence/preparation/verifier-production-simulation-6s9_bb4j/receipt.json"
        if original_failure.is_file():
            ev.receipt["diagnosed_failure"] = item(ROOT, original_failure)
        previous = ROOT / "evidence/preparation/verifier-streaming-replay-v5_veqlg/receipt.json"
        if previous.is_file():
            ev.receipt["earlier_repair"] = item(ROOT, previous)
        binding_checks(ev)
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
        progress_checks(ev, executable, tokens)
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
        for with_reference in (False, True):
            bad = []
            try:
                for role in ("observation", "repeat"):
                    bad.append(origin(ev, executable, tokens, "bf16", role, "nonfinite"))
                if with_reference:
                    bad.append(origin(ev, executable, tokens, "bf16", "reference"))
                for process in bad:
                    process.next()
                reference = bad[2] if with_reference else None
                rejection(ev, "nonfinite-" + ("teacher" if with_reference else "greedy"),
                          lambda: compare_window(
                              ROOT, ev, bad[0], bad[1], reference, "bf16", "nonfinite"),
                          "nonfinite numerical array" if with_reference else
                          "nonfinite streamed output")
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
