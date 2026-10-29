#!/usr/bin/env python3
"""Synthetic streaming/retained equivalence; does not authorize collection."""

import argparse
import gzip
import json
import math
from pathlib import Path
import resource
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import Validator, artifact_path, load_json, require, sha
from benchmark_inputs import write_json
from packed_storage import transactions
from verify import Evidence, ROOT


HEADER = struct.Struct("<4sIIII")
RECORD = struct.Struct("<11I")
POSITIONS = 3


def vectors():
    for position in range(POSITIONS):
        for layer in range(25):
            yield position, layer, 896 if layer < 24 else 151936


def expected_transactions():
    for number in range(POSITIONS * 4):
        request = 6 * number + 1
        yield (request, 0, request + 2, 0, number % 2, 8, 0, 0,
               0, number // 2, 0x3f800000)


def allocation(directory):
    seen = set()
    total = 0
    for path in (directory, *directory.rglob("*")):
        info = path.stat()
        key = info.st_dev, info.st_ino
        if key not in seen:
            total += info.st_blocks * 512
            seen.add(key)
    return total


def item(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def prepare(directory, defect):
    directory.mkdir()
    for name in ("actual", "repeat", "reference", "checkpoint"):
        with (directory / (name + ".bin")).open("xb") as stream:
            for position, layer, width in vectors():
                wide = name in ("reference", "checkpoint")
                values = [math.sin(index * .03125 + position + layer) * .5
                          for index in range(width)]
                if name == "checkpoint":
                    values = [value * 1.0001 for value in values]
                if defect == "numerical" and name in ("actual", "repeat"):
                    values[0] = 4.0
                raw = struct.pack("<" + ("d" if wide else "f") * width, *values)
                if defect == "repeat" and name == "repeat":
                    raw = bytes([raw[0] ^ 1]) + raw[1:]
                stream.write(HEADER.pack(b"AQSC", position, layer, width, len(raw)))
                stream.write(raw)
    if defect == "truncated-array":
        path = directory / "actual.bin"
        with path.open("r+b") as stream:
            stream.truncate(path.stat().st_size - 1)
    rows = list(expected_transactions())
    if defect == "missing-transaction":
        del rows[4]
    elif defect == "duplicate-transaction":
        rows.insert(4, rows[3])
    with gzip.open(directory / "transactions.u32.gz", "xb") as stream:
        for row in rows:
            stream.write(RECORD.pack(*row))
        if defect == "truncated-transaction":
            stream.write(b"\x01")


class Observation:
    def __init__(self):
        self.receipt = {}


def worker(args):
    directory = artifact_path(ROOT, str(args.directory))
    inputs = artifact_path(ROOT, str(args.inputs))
    directory.mkdir()
    report = {"synthetic": True, "rtl_executions": 0, "complete_benchmark": False,
              "lifecycle": args.lifecycle, "vectors_compared": 0,
              "transactions_compared": 0, "metrics": [],
              "peak_fixture_allocated_bytes": allocation(inputs),
              "peak_fixture_and_output_allocated_bytes": allocation(inputs) + allocation(directory)}
    streams = []
    try:
        observed = transactions(inputs / "transactions.u32.gz")
        try:
            for expected in expected_transactions():
                require(next(observed, None) == expected,
                        "transaction missing/duplicate/reordered")
                report["transactions_compared"] += 1
            require(next(observed, None) is None, "extra transaction")
        finally:
            observed.close()
        names = ("actual", "repeat", "reference", "checkpoint")
        streams = [(inputs / (name + ".bin")).open("rb") for name in names]
        validator = Validator(ROOT, Observation())
        report["metrics"] = validator.metrics
        released = None
        for position, layer, width in vectors():
            paths = []
            descriptors = []
            for name, stream in zip(names, streams):
                wide = name in ("reference", "checkpoint")
                header = stream.read(HEADER.size)
                require(len(header) == HEADER.size, "truncated array header")
                require(HEADER.unpack(header) == (
                    b"AQSC", position, layer, width, width * (8 if wide else 4)),
                    "array stream shape/order differs")
                raw = stream.read(width * (8 if wide else 4))
                require(len(raw) == width * (8 if wide else 4), "truncated array payload")
                path = directory / f"{position}-{layer}-{name}.bin"
                with path.open("xb") as output:
                    output.write(raw)
                paths.append(path)
                descriptors.append(item(path))
            report["peak_fixture_and_output_allocated_bytes"] = max(
                report["peak_fixture_and_output_allocated_bytes"],
                allocation(inputs) + allocation(directory))
            actual, repeated, reference, checkpoint = descriptors
            threshold = ((.9999, .002) if layer < 24 else (.999, .01))
            validator.arrays(actual, reference, repeated, width, threshold,
                             f"{position}/{layer}")
            validator.arrays(reference, checkpoint, reference, width,
                             (-1, float("inf")), f"{position}/{layer}/storage", wide=True)
            report["vectors_compared"] += 1
            if args.lifecycle == "streaming":
                released = actual
                for path in paths:
                    path.unlink()
        require(all(stream.read(1) == b"" for stream in streams),
                "trailing array stream payload")
        if args.lifecycle == "streaming":
            # A fresh validator must reread the bytes; cached hashes are not evidence.
            try:
                Validator(ROOT, Observation()).artifact(released)
            except ValueError as error:
                require("missing artifact:" in str(error), "unexpected retention failure")
                report["retained_contract_rejection"] = str(error)
            else:
                raise ValueError("released array unexpectedly satisfied retained contract")
        report["status"] = "passed"
    except (ValueError, OSError, EOFError) as error:
        report.update(status="failed", diagnostic=str(error))
        print(str(error), file=sys.stderr, flush=True)
    finally:
        for stream in streams:
            stream.close()
        report["peak_process_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        report["final_fixture_and_output_allocated_bytes"] = (
            allocation(inputs) + allocation(directory))
        write_json(directory / "measurement.json", report)
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--lifecycle", choices=("streaming", "retained"))
    args = parser.parse_args()
    if args.worker:
        return worker(args)
    ev = Evidence("streaming-collection")
    passed = False
    try:
        for field, name in (
            ("diagnosed_collection_failure",
             "verifier-production-simulation-6s9_bb4j"),
            ("repair_of", "verifier-streaming-collection-0nxrhbxm"),
        ):
            previous = ROOT / "evidence/preparation" / name / "receipt.json"
            if previous.is_file():
                ev.receipt[field] = item(previous)
        require(ev.run("python-version", [sys.executable, "--version"], timeout=30),
                "Python version unavailable")
        inputs = ev.path / "pristine-inputs"
        prepare(inputs, "pristine")
        measurements = {}
        for lifecycle in ("retained", "streaming"):
            directory = ev.path / lifecycle
            require(ev.run(lifecycle, [
                sys.executable, "tests/streaming_collection_checks.py", "--worker",
                "--directory", str(directory.relative_to(ROOT)),
                "--inputs", str(inputs.relative_to(ROOT)), "--lifecycle", lifecycle],
                timeout=3600), lifecycle + " pristine comparison failed")
            measurements[lifecycle] = load_json(directory / "measurement.json")
        retained, streamed = measurements["retained"], measurements["streaming"]
        require(retained["metrics"] == streamed["metrics"] and
                retained["vectors_compared"] == streamed["vectors_compared"] == 75 and
                retained["transactions_compared"] == streamed["transactions_compared"] == 12,
                "retained/streaming metrics or comparison counts differ")
        ev.assertion("streaming_matches_unchanged_retained_numerical_assertions", True,
                     positions=POSITIONS, layers_per_position=24, logits_per_position=151936,
                     metrics_compared=len(streamed["metrics"]), synthetic=True)
        require(streamed["peak_fixture_and_output_allocated_bytes"] <
                retained["peak_fixture_and_output_allocated_bytes"],
                "streaming did not reduce measured allocation")
        ev.assertion("measured_storage_and_process_memory", True, measurements={
            name: {key: value for key, value in report.items()
                   if "bytes" in key} for name, report in measurements.items()},
            storage_scope="allocated fixture/output blocks measured at each synchronous write batch",
            memory_scope="Linux per-worker kernel RSS high-water, not production capacity")
        ev.assertion("released_arrays_rejected_by_existing_benchmark_contract", True,
                     diagnostic=streamed["retained_contract_rejection"])
        for defect, diagnostic in (
            ("numerical", "numerical fidelity failed"),
            ("repeat", "nondeterministic output"),
            ("missing-transaction", "transaction missing/duplicate/reordered"),
            ("duplicate-transaction", "single-outstanding cycle order"),
            ("truncated-array", "truncated array payload"),
            ("truncated-transaction", "partial"),
        ):
            inputs = ev.path / (defect + "-inputs")
            prepare(inputs, defect)
            directory = ev.path / (defect + "-output")
            result = ev.run(defect, [
                sys.executable, "tests/streaming_collection_checks.py", "--worker",
                "--directory", str(directory.relative_to(ROOT)),
                "--inputs", str(inputs.relative_to(ROOT)), "--lifecycle", "streaming"],
                timeout=3600)
            report = load_json(directory / "measurement.json")
            require(not result and report["status"] == "failed" and
                    diagnostic in report["diagnostic"], "defect escaped/wrong failure: " + defect)
            ev.assertion("reject_" + defect, True, diagnostic=report["diagnostic"],
                         synthetic=True)
        passed = True
    except (ValueError, OSError, KeyError) as error:
        ev.assertion("streaming_regression_failure", False, diagnostic=str(error))
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path) for path in ev.path.rglob("*")
            if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                          "benchmark_acceptance": False}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
