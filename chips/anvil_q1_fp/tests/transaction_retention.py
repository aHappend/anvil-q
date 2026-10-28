#!/usr/bin/env python3
"""Bounded production prefixes with independent trace retention reads.

This is an advisory diagnosis, not checkpoint equivalence, numerical acceptance
or a completed benchmark. Integrity identifiers are retained only in evidence.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import artifact_path, load_json, require, sha
from benchmark_inputs import write_json
from verify import Evidence, ROOT, now


def inspect_trace(path, destination):
    started = now()
    before = path.stat()
    count = reads = writes = 0
    decoded = hashlib.sha256()
    first = []
    last = None
    kinds = {}
    # Reading through EOF validates the gzip trailer/CRC as well as every record.
    with gzip.open(path, "rb") as source:
        while data := source.read(44):
            require(len(data) == 44, "partial 44-byte transaction record")
            decoded.update(data)
            words = struct.unpack("<11I", data)
            accepted = words[0] | (words[1] << 32)
            completed = words[2] | (words[3] << 32)
            require(accepted < completed and words[4] in (0, 1),
                    "invalid decoded transaction timing/write field")
            require(last is None or accepted >= last["completed_cycle"],
                    "overlapping or out-of-order transaction at record " + str(count))
            sample = {
                "accepted_cycle": accepted, "completed_cycle": completed,
                "write": bool(words[4]), "kind": words[5], "layer": words[6],
                "projection": words[7], "row": words[8], "column": words[9],
                "payload_hex": f"{words[10]:08x}",
            }
            if len(first) < 3:
                first.append(sample)
            last = sample
            count += 1
            writes += words[4]
            reads += 1 - words[4]
            kinds[str(words[5])] = kinds.get(str(words[5]), 0) + 1
    require(count > 0, "empty transaction witness")
    compressed_hash = sha(path)
    after = path.stat()
    require((before.st_size, before.st_mtime_ns, before.st_ino) ==
            (after.st_size, after.st_mtime_ns, after.st_ino),
            "transaction witness changed during inspection")
    result = {
        "schema": 1, "acceptance_evidence": False,
        "started_at": started, "ended_at": now(),
        "trace": str(path.relative_to(ROOT)),
        "compressed_bytes": after.st_size, "compressed_sha256": compressed_hash,
        "decompressed_bytes": count * 44, "decompressed_sha256": decoded.hexdigest(),
        "record_bytes": 44, "records": count, "reads": reads, "writes": writes,
        "kinds": kinds, "first_records": first, "last_record": last,
        "gzip_eof_crc_checked": True,
    }
    write_json(destination, result)
    print(json.dumps({key: result[key] for key in
                      ("trace", "compressed_bytes", "decompressed_bytes",
                       "records", "reads", "writes", "first_records", "last_record")}))
    return result


def witness(args):
    ev = Evidence("transaction-retention")
    passed = False
    try:
        from production_checkpoint import CONTROLLERS, execution, make_binding
        from production_sim import compile_simulator

        ev.receipt["scope"] = "one reset-origin production prefix; no completed benchmark"
        if args.repair_of:
            previous = artifact_path(ROOT, str(args.repair_of))
            require(load_json(previous)["status"] == "failed", "repair receipt did not fail")
            ev.receipt["repair_of"] = {"path": str(args.repair_of), "sha256": sha(previous)}
        snapshot = ev.path / "source-snapshot"
        names = [*CONTROLLERS, "tests/transaction_retention.py",
                 "tests/production_sim.cpp", "tests/verify.py"]
        paths = [*(ROOT / name for name in names), *(ROOT / "rtl").glob("*.sv")]
        for path in paths:
            target = snapshot / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        require(ev.run("python-version", [sys.executable, "--version"], timeout=30),
                "Python version query failed")
        from teacher_reference import validate_inputs

        model, suite, _, config = validate_inputs(ev)
        executable = compile_simulator(ev, args.build_receipt)
        selection = argparse.Namespace(
            case_index=0, workload="greedy", teacher_prefix=None)
        binding = make_binding(ev, model, suite, config, executable, selection, "bf16")
        destination = ev.path / "segment"
        observations = {}

        def observe(phase):
            output = ev.path / (phase + ".json")
            require(ev.run(phase, [
                sys.executable, "tests/transaction_retention.py", "--inspect",
                str((destination / "transactions.u32.gz").relative_to(ROOT)),
                "--destination", str(output.relative_to(ROOT)),
            ], timeout=3600), "transaction retention inspection failed: " + phase)
            observations[phase] = load_json(output)
            ev.assertion("transaction_retention_" + phase, True,
                         observation=str(output.relative_to(ROOT)),
                         records=observations[phase]["records"])

        row, item = execution(ev, binding, destination, 12005, observer=observe)
        before, after = (observations[phase] for phase in ("after-child", "after-seal"))
        for key in before.keys() - {"started_at", "ended_at"}:
            require(before[key] == after[key], "trace changed across sealing: " + key)
        marker = load_json(destination / "paused.json")
        require(row["start_cycle"] == 0 and row["end_cycle"] == 12005 and
                row["parent"] is None and before["records"] == marker["responses"],
                "witness reset-origin/cycle/response accounting differs")
        require(marker["completed_tokens"] == 0, "prefix unexpectedly completed a token")
        ev.assertion("transaction_retention_across_seal", True,
                     checkpoint=item, records=after["records"], cycles=12005,
                     completed_tokens=0, trace=after["trace"])
        ev.receipt["observations"] = {
            phase: str((ev.path / (phase + ".json")).relative_to(ROOT))
            for phase in observations}
        passed = True
    except (ValueError, OSError, KeyError, ImportError) as error:
        ev.assertion("transaction_retention_failure", False, diagnostic=str(error))
    finally:
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                          "complete_benchmark": False}), flush=True)
    return 0 if passed else 1


def continuation(args):
    ev = Evidence("retention-continuation")
    passed = False
    try:
        from production_checkpoint import CONTROLLERS, execution, validate_segment

        ev.receipt["scope"] = (
            "one admitted cycle-12005 to cycle-24005 retention continuation; "
            "no checkpoint equivalence or completed benchmark")
        require(args.build_receipt is None and args.repair_of is None,
                "continuation cannot rebuild or replace its parent")
        witness_path = artifact_path(ROOT, str(args.resume_witness))
        original_path = witness_path / "receipt.json"
        original = load_json(original_path)
        require(original["status"] == "passed", "original witness receipt did not pass")
        items = [entry["checkpoint"] for entry in original["assertions"]
                 if entry["name"] == "transaction_retention_across_seal"
                 and entry["passed"]]
        require(len(items) == 1, "missing or ambiguous original sealed descriptor")
        parent_item = items[0]
        ev.receipt["original_witness"] = {
            "path": str(original_path.relative_to(ROOT)),
            "sha256": sha(original_path), "checkpoint": parent_item,
        }
        snapshot = ev.path / "source-snapshot"
        for name in (*CONTROLLERS, "tests/transaction_retention.py",
                     "tests/retention_handoff.py", "tests/production_sim.cpp",
                     "tests/verify.py"):
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        require(ev.run("python-version", [sys.executable, "--version"], timeout=30),
                "Python version query failed")
        require(ev.run("verilator-version", ["verilator", "--version"], timeout=30),
                "Verilator version query failed")
        chain = []
        parent = validate_segment(ev, parent_item, chain=chain)
        require(len(chain) == 1 and parent["parent"] is None and
                parent["status"] == "paused" and parent["start_cycle"] == 0 and
                parent["end_cycle"] == 12005, "parent witness bounds differ")
        initial = load_json(artifact_path(ROOT, parent["paused"]["path"]))
        require(initial["completed_tokens"] == 0 and
                initial["requests"] == initial["responses"] + int(initial["pending"]),
                "parent witness progress/conservation differs")

        def inspect(label, trace):
            output = ev.path / (label + ".json")
            require(ev.run(label, [
                sys.executable, "tests/transaction_retention.py", "--inspect",
                str(trace.relative_to(ROOT)), "--destination",
                str(output.relative_to(ROOT)),
            ], timeout=3600), "transaction retention inspection failed: " + label)
            return load_json(output)

        def check_parent(label):
            observation = inspect(label, witness_path / "segment/transactions.u32.gz")
            require(ev.run(label + "-validate", [
                sys.executable, "tests/retention_handoff.py",
                str(witness_path.relative_to(ROOT)), "--validate",
                str((ev.path / (label + ".json")).relative_to(ROOT)),
            ], timeout=3600), "parent retention/inventory validation failed: " + label)
            require(sha(original_path) == ev.receipt["original_witness"]["sha256"],
                    "original witness receipt changed")
            return observation

        parent_before = check_parent("parent-before")
        destination = ev.path / "segment"
        observations = {}

        def observe(phase):
            observations[phase] = inspect(
                phase, destination / "transactions.u32.gz")
            ev.assertion("continuation_retention_" + phase, True,
                         observation=str((ev.path / (phase + ".json")).relative_to(ROOT)),
                         records=observations[phase]["records"])

        row, item = execution(ev, parent["binding"], destination, 24005,
                              parent, parent_item, observer=observe)
        before, after = (observations[phase] for phase in ("after-child", "after-seal"))
        require(before.keys() == after.keys(), "new observation fields differ")
        for key in before.keys() - {"started_at", "ended_at"}:
            require(before[key] == after[key], "trace changed across sealing: " + key)
        require(row["status"] == "paused" and row["start_cycle"] == 12005 and
                row["end_cycle"] == 24005 and row["parent"] == parent_item,
                "continuation bounds/parent differ")
        final = load_json(destination / "paused.json")
        responses = final["responses"] - initial["responses"]
        require(before["records"] == responses and responses ==
                final["requests"] - initial["requests"] +
                int(initial["pending"]) - int(final["pending"]),
                "fragment records differ from cumulative response increase")
        require(final["completed_tokens"] == 0, "prefix unexpectedly completed a token")
        parent_after = check_parent("parent-after")
        for key in parent_before.keys() - {"started_at", "ended_at"}:
            require(parent_before[key] == parent_after[key],
                    "parent observation changed across continuation: " + key)
        validated_chain = []
        validate_segment(ev, parent_item, parent["binding"])
        validate_segment(ev, item, parent["binding"], chain=validated_chain)
        require(len(validated_chain) == 2, "continuation inventory ancestry differs")
        ev.assertion("single_continuation_retention_and_inventories", True,
                     checkpoint=item, parent=parent_item, start_cycle=12005,
                     end_cycle=24005, records=responses,
                     inherited_pending=initial["pending"],
                     final_pending=final["pending"], completed_tokens=0,
                     sealed_inventories_valid=True, complete_benchmark=False)
        passed = True
    except (ValueError, OSError, KeyError, ImportError) as error:
        ev.assertion("retention_continuation_failure", False, diagnostic=str(error))
    finally:
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                          "complete_benchmark": False}), flush=True)
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-receipt", type=Path)
    parser.add_argument("--repair-of", type=Path)
    parser.add_argument("--inspect", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--resume-witness", type=Path)
    args = parser.parse_args()
    if args.inspect:
        require(args.resume_witness is None, "inspection cannot resume a witness")
        require(args.destination is not None, "inspection destination is required")
        inspect_trace(artifact_path(ROOT, str(args.inspect)),
                      artifact_path(ROOT, str(args.destination)))
        return 0
    require(args.destination is None, "destination requires --inspect")
    if args.resume_witness:
        return continuation(args)
    return witness(args)


if __name__ == "__main__":
    raise SystemExit(main())
