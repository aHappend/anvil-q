#!/usr/bin/env python3
"""Immutable, source/data-bound production simulator segments.

Checkpointing suspends actual RTL execution, not a software substitute. Every
segment owns new output fragments and a complete Verilator/driver snapshot.
Only a completed process can publish a sealed segment descriptor. A pause is
explicitly incomplete, never a completed token or benchmark result.
"""

import argparse
import gzip
import json
import os
from pathlib import Path
import shutil
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import artifact_path, load_json, require, sha
from benchmark_inputs import write_json
from production_sim import (MODES, checked, compile_simulator, descriptor, identity,
                            memory_table, prepare_rope)
from verify import Evidence, ROOT


CONTROLLERS = ("tests/production_checkpoint.py", "tests/production_sim.py",
               "tests/production_trace.py")


def controllers():
    return {name: sha(ROOT / name) for name in CONTROLLERS}


def sync_file(path):
    with path.open("rb") as source:
        os.fsync(source.fileno())


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def seal(path, value):
    require(not path.exists(), "sealed output already exists")
    write_json(path, value)
    sync_file(path)
    sync_directory(path.parent)
    sync_directory(path.parent.parent)
    return descriptor(path)


def validate_segment(ev, item, expected_binding=None, chain=None):
    """Verify every immutable ancestor and artifact before deserializing bytes."""
    seen = set()
    verified = {}
    head = None
    expected_end = None

    def payload(item):
        name, digest = item["path"], item["sha256"]
        if name not in verified:
            checked(ev, item)
            verified[name] = digest
        require(verified[name] == digest, "checkpoint conflicting artifact hashes")
        return artifact_path(ROOT, name)

    while item is not None:
        path = payload(item)
        require(str(path) not in seen, "checkpoint ancestry cycle")
        seen.add(str(path))
        row = load_json(path)
        if head is None:
            head = row
        require(row["schema"] == 1 and row["acceptance_evidence"] is False and
                row["status"] in ("paused", "completed"), "not a simulator segment")
        if expected_end is not None:
            require(row["status"] == "paused" and row["end_cycle"] == expected_end,
                    "checkpoint ancestry cycle discontinuity")
        binding = row["binding"]
        require(binding["build_sources"] == identity(), "checkpoint RTL/C++ changed")
        require(binding["controllers"] == controllers(), "checkpoint controller changed")
        if expected_binding is None:
            expected_binding = binding
        require(binding == expected_binding, "checkpoint execution binding differs")
        for entry in [binding["executable"], *binding["inputs"], *row["artifacts"]]:
            payload(entry)
        if row["status"] == "paused":
            payload(row["state"])
            observed_end = load_json(payload(row["paused"]))["cycle"]
        else:
            require(row["state"] is None and row["paused"] is None,
                    "completed process is not a resumable checkpoint")
            observed_end = load_json(payload(row["summary"]))["cycles"]
        require(observed_end == row["end_cycle"] and
                row["end_cycle"] > row["start_cycle"] >= 0,
                "checkpoint cycle metadata differs")
        require((row["parent"] is None) == (row["start_cycle"] == 0),
                "checkpoint root/parent mismatch")
        expected_end = row["start_cycle"]
        if chain is not None:
            chain.append(row)
        item = row["parent"]
    return head


def execution(ev, binding, destination, target, parent=None, parent_item=None,
              observer=None):
    destination.mkdir()
    start = parent["end_cycle"] if parent else 0
    require(parent is None or parent["status"] == "paused",
            "cannot resume a completed process")
    require(target > start, "checkpoint must advance simulation")
    command = [binding["executable"]["path"], *binding["arguments"]]
    # output is argument 4 in the executable interface, index 3 in arguments.
    command[4] = str(destination.relative_to(ROOT))
    command += [parent["state"]["path"] if parent else "-", str(target)]
    succeeded = ev.run(destination.name, command, timeout=86400)
    if observer is not None:
        observer("after-child")
    require(succeeded,
            "checkpoint segment child failed; no new checkpoint admitted")
    paused_path = destination / "paused.json"
    summary_path = destination / "summary.json"
    require(paused_path.is_file() != summary_path.is_file(),
            "segment must pause or complete, not neither/both")
    paused = load_json(paused_path) if paused_path.is_file() else None
    if paused is not None:
        require(paused["cycle"] == target and
                paused["requests"] == paused["responses"] + int(paused["pending"]),
                "checkpoint progress/conservation mismatch")
        end, status = target, "paused"
    else:
        summary = load_json(summary_path)
        require(start < summary["cycles"] < target and
                summary["requests"] == summary["responses"] and
                summary["positions_completed"] > 0,
                "completed segment progress/conservation mismatch")
        end, status = summary["cycles"], "completed"
    artifacts = []
    for path in sorted(destination.rglob("*")):
        if path.is_file():
            sync_file(path)
            artifacts.append(descriptor(path))
    for path in sorted(destination.rglob("*"), reverse=True):
        if path.is_dir():
            sync_directory(path)
    row = {
        "schema": 1, "status": status, "acceptance_evidence": False,
        "complete_benchmark": False, "binding": binding, "parent": parent_item,
        "start_cycle": start, "end_cycle": end,
        "state": descriptor(destination / "simulator.bin") if paused else None,
        "paused": descriptor(paused_path) if paused else None,
        "summary": None if paused else descriptor(summary_path), "artifacts": artifacts,
        "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
    }
    item = seal(destination / "checkpoint.json", row)
    if observer is not None:
        observer("after-seal")
    ev.assertion(destination.name + "_sealed_" + status, True,
                 checkpoint=item, **(paused if paused else summary))
    return row, item


def assemble(ev, item, label="assembled"):
    """Join immutable fragments, without inventing missing records or logits."""
    chain = []
    head = validate_segment(ev, item, chain=chain)
    destination = ev.path / label
    destination.mkdir()
    event_count = 0
    with gzip.open(destination / "transactions.u32.gz", "xb") as trace:
        with (destination / "events.jsonl").open("xb") as events:
            for row in reversed(chain):
                artifacts = {Path(entry["path"]).name: entry for entry in row["artifacts"]}
                # Each segment is sealed before assembly. Gzip concatenation is
                # decoded/re-encoded; snapshots are never appended or rewritten.
                with gzip.open(ROOT / artifacts["transactions.u32.gz"]["path"], "rb") as source:
                    shutil.copyfileobj(source, trace)
                path = ROOT / artifacts["events.jsonl"]["path"]
                with path.open("rb") as source:
                    for line in source:
                        require(line.endswith(b"\n"), "partial checkpoint event record")
                        load_json_line = json.loads(line)
                        require(type(load_json_line) is dict, "malformed checkpoint event")
                        events.write(line)
                        event_count += 1
                for entry in row["artifacts"]:
                    path = ROOT / entry["path"]
                    if path.name not in ("layers.f32", "logits.f32"):
                        continue
                    require(path.parent.name.startswith("position-"), "invalid vector fragment path")
                    target = destination / path.parent.name / path.name
                    target.parent.mkdir(exist_ok=True)
                    with path.open("rb") as source, target.open("ab") as output:
                        shutil.copyfileobj(source, output)
    completed = head["status"] == "completed"
    if completed:
        summary = load_json(ROOT / head["summary"]["path"])
        require(len(list(destination.glob("position-*"))) == summary["positions_completed"],
                "assembled position count differs")
        for position in range(summary["positions_completed"]):
            path = destination / f"position-{position}"
            require((path / "layers.f32").stat().st_size == 24*896*4 and
                    (path / "logits.f32").stat().st_size == 151936*4,
                    "assembled completed position has missing/duplicate output fragments")
        shutil.copy2(ROOT / head["summary"]["path"], destination / "summary.json")
    seal(destination / "assembly.json", {
        "schema": 1, "segment": item, "segments": len(chain),
        "completed_process": completed, "complete_benchmark": False,
        "events": event_count, "end_cycle": head["end_cycle"],
        "artifacts": [descriptor(path) for path in sorted(destination.rglob("*"))
                      if path.is_file()],
    })
    ev.assertion("immutable_segment_fragment_assembly", True, segments=len(chain),
                 completed_process=completed, events=event_count)
    return destination


def make_binding(ev, model, suite, config, executable, args, mode):
    cases = [(domain + "/" + case["id"], case)
             for domain, group in suite["domains"].items() for case in group["cases"]]
    require(len(cases) == 50 and 0 <= args.case_index < len(cases),
            "invalid frozen benchmark selection")
    key, case = cases[args.case_index]
    teacher = args.workload == "teacher"
    tokens = load_json(checked(ev, case["teacher_tokens" if teacher else "prompt_tokens"]))
    if args.teacher_prefix is not None:
        require(teacher and 0 < args.teacher_prefix <= len(tokens),
                "invalid explicitly incomplete teacher prefix")
        tokens = tokens[:args.teacher_prefix]
    table = memory_table(ev, model, mode, ev.path / (mode + ".memory"))
    rope = prepare_rope(ev.path / (mode + ".rope"),
                        len(tokens) + (0 if teacher else 128), mode)
    token_path = ev.path / (mode + ".tokens")
    with token_path.open("x") as output:
        output.write("\n".join(map(str, tokens)) + "\n")
    layers = logits = "-"
    input_paths = [table, rope, token_path,
                   ROOT / "tests/data/model_manifest.json",
                   ROOT / "tests/data/benchmark_manifest.json"]
    if teacher:
        json_tokens = ev.path / (mode + "-reference-tokens.json")
        write_json(json_tokens, tokens)
        destination = ev.path / (mode + "-references")
        require(ev.run(mode + "-independent-reference", [
            sys.executable, "tests/production_sim.py", "--reference-worker",
            "--tokens", str(json_tokens.relative_to(ROOT)),
            "--destination", str(destination.relative_to(ROOT)), "--modes", mode],
            timeout=86400), "independent production reference failed")
        refs = load_json(destination / "references.json")
        layers, logits = (refs[mode][name]["path"] for name in ("layers", "logits"))
        input_paths.extend([json_tokens, *(path for path in destination.rglob("*")
                                          if path.is_file())])
    # Bind all backing tensors, not just their textual mapping descriptors.
    input_paths.extend(ROOT / line.split()[-1] for line in table.read_text().splitlines())
    eos = config["eos_token_id"]
    arguments = [
        str(table.relative_to(ROOT)), str(token_path.relative_to(ROOT)),
        str(rope.relative_to(ROOT)), "-", str(MODES[mode]), args.workload,
        ",".join(map(str, eos if isinstance(eos, list) else [eos])),
        "preparation-only", layers, logits, str(len(tokens)),
    ]
    return {
        "build_sources": identity(), "controllers": controllers(),
        "executable": descriptor(executable),
        "inputs": [descriptor(path) for path in sorted(set(input_paths))],
        "arguments": arguments, "case": key, "mode": mode,
        "workload": args.workload, "teacher_prefix": args.teacher_prefix,
        "production_dimensions_unchanged": True,
    }


def trace_rows(path):
    with gzip.open(path, "rb") as source:
        while data := source.read(44):
            require(len(data) == 44, "truncated checkpoint trace")
            yield struct.unpack("<11I", data)


def qualify(ev, args, model, suite, config, executable):
    # Real production RTL, public transactions and actual pretrained streams.
    # Five-cycle suspension catches the token acceptance boundary; later stops
    # cross pending responses, request stalls and initialized scratch storage.
    for mode in MODES:
        binding = make_binding(ev, model, suite, config, executable, args, mode)
        baseline, _ = execution(ev, binding, ev.path / (mode + "-uninterrupted"), 12005)
        parent = item = None
        runs = []
        for target in (5, 101, 4005, 8005, 12005):
            if parent:
                validate_segment(ev, item, binding)
            run = ev.path / f"{mode}-resume-{target}"
            parent, item = execution(ev, binding, run, target, parent, item)
            runs.append(run)
        continuous = ev.path / (mode + "-uninterrupted")
        reference = list(trace_rows(continuous / "transactions.u32.gz"))
        resumed = [row for run in runs for row in trace_rows(run / "transactions.u32.gz")]
        require(reference == resumed and len(reference) >= 2000,
                "checkpoint public transaction trace differs")
        assembled = assemble(ev, item, mode + "-assembled")
        require(list(trace_rows(assembled / "transactions.u32.gz")) == reference,
                "assembled checkpoint trace differs")
        # Identical complete serialized state checks more than the trace prefix:
        # RNG, pending request/reply, all DUT registers and initialized memory.
        require(sha(ROOT / baseline["state"]["path"]) == sha(ROOT / parent["state"]["path"]),
                "checkpoint final DUT/host state differs from uninterrupted execution")
        require((continuous / "events.jsonl").read_bytes() ==
                b"".join((run / "events.jsonl").read_bytes() for run in runs),
                "checkpoint public event stream differs")
        for filename in ("layers.f32", "logits.f32"):
            require((continuous / "position-0" / filename).read_bytes() ==
                    b"".join((run / "position-0" / filename).read_bytes() for run in runs),
                    "checkpoint output fragments differ")
        merged = ev.path / (mode + "-joined-trace.u32.gz")
        with gzip.open(merged, "xb") as output:
            for row in resumed:
                output.write(struct.pack("<11I", *row))
        # Replay in an independent process to retain its unchanged assertions.
        require(ev.run(mode + "-independent-joined-trace", [
            sys.executable, "tests/production_trace.py", "--worker", "--mode", mode,
            "--trace", str(merged.relative_to(ROOT)), "--destination",
            str((ev.path / (mode + "-trace-comparisons.json")).relative_to(ROOT))],
            timeout=3600), "independent checkpoint trace replay failed")
        marker = load_json(runs[1] / "paused.json")
        require(marker["pending"] and marker["requests"] > marker["responses"],
                "qualification missed an outstanding response at suspension")
        ev.assertion("checkpoint_real_production_equivalence_" + mode, True,
                     transactions=len(reference), segments=len(runs),
                     completed_tokens=0, final_state_bit_identical=True,
                     intermediate_pending=marker["pending"])
        for label, mutate, diagnostic in (
            ("changed-source", lambda row: row["binding"]["build_sources"].update(
                {"rtl/changed.sv": "0"*64}), "checkpoint RTL/C++ changed"),
            ("changed-input", lambda row: row["binding"]["inputs"][0].update(
                {"sha256": "0"*64}), "checkpoint execution binding differs"),
            ("changed-snapshot", lambda row: row["state"].update(
                {"sha256": "0"*64}), "checkpoint conflicting artifact hashes"),
            ("cycle-gap", lambda row: row.update(start_cycle=row["start_cycle"]-1),
             "checkpoint ancestry cycle discontinuity"),
        ):
            mutant = json.loads(json.dumps(parent))
            mutate(mutant)
            path = ev.path / (mode + "-" + label + ".json")
            item_mutant = seal(path, mutant)
            try:
                validate_segment(ev, item_mutant, binding)
            except ValueError as error:
                require(diagnostic in str(error), "wrong checkpoint rejection: " + str(error))
                ev.assertion("reject_checkpoint_" + mode + "_" + label, True,
                             diagnostic=str(error), no_mutant_rtl_execution=True)
            else:
                raise ValueError("changed checkpoint escaped binding validation")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualify", action="store_true")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--assemble", type=Path)
    parser.add_argument("--build-receipt", type=Path)
    parser.add_argument("--mode", choices=tuple(MODES), default="bf16")
    parser.add_argument("--workload", choices=("teacher", "greedy"), default="teacher")
    parser.add_argument("--case-index", type=int, default=0)
    parser.add_argument("--teacher-prefix", type=int)
    parser.add_argument("--cycles", type=int, default=100000000)
    args = parser.parse_args()
    ev = Evidence("production-checkpoint")
    passed = False
    try:
        require(args.cycles > 0 and
                sum((bool(args.resume), bool(args.assemble), args.qualify)) <= 1,
                "invalid checkpoint operation")
        snapshot = ev.path / "collector-sources"
        snapshot.mkdir()
        for name in (*CONTROLLERS, "tests/production_sim.cpp"):
            shutil.copy2(ROOT / name, snapshot / Path(name).name)
        if args.assemble:
            path = artifact_path(ROOT, str(args.assemble))
            assemble(ev, descriptor(path))
        elif args.resume:
            path = artifact_path(ROOT, str(args.resume))
            item = descriptor(path)
            parent = validate_segment(ev, item)
            binding = parent["binding"]
            # Query the actual executable environment even when no rebuild occurs.
            require(ev.run("verilator-version", ["verilator", "--version"], timeout=30),
                    "Verilator unavailable")
            execution(ev, binding, ev.path / "segment",
                      parent["end_cycle"] + args.cycles, parent, item)
        else:
            from teacher_reference import validate_inputs
            model, suite, _, config = validate_inputs(ev)
            executable = compile_simulator(ev, args.build_receipt)
            if args.qualify:
                # Prefix qualification does not need an expensive full reference.
                args.workload = "greedy"
                require(args.teacher_prefix is None, "qualification uses full prompt input")
                qualify(ev, args, model, suite, config, executable)
            else:
                binding = make_binding(ev, model, suite, config, executable, args, args.mode)
                execution(ev, binding, ev.path / "segment", args.cycles)
        passed = True
    except (ValueError, OSError, KeyError, ImportError) as error:
        ev.assertion("checkpoint_failure", False, diagnostic=str(error))
    finally:
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                          "complete_benchmark": False}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
