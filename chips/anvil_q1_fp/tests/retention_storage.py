#!/usr/bin/env python3
"""Synthetic retention qualification and read-only complete-workload capacity.

No RTL build, inference, production collection or benchmark assembly is allowed
on this path. A passing codec diagnostic is not proof of available capacity.
"""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import artifact_path, load_json, require, sha
from benchmark_inputs import write_json
from verify import Evidence, ROOT


def synthetic(destination):
    import numpy as np
    from production_sim import checked, compare_teacher, descriptor
    from reference_collector import collect
    from transaction_retention import inspect_trace
    from collection_capacity import array_allocation

    destination.mkdir(parents=True, exist_ok=False)
    report = {"purpose": "synthetic-retention-only", "acceptance_evidence": False,
              "inference_executed": False, "rtl_built": False, "cases": [],
              "negative_cases": [], "independent_observations_deduplicated": False}

    def reject(name, function, errors=(ValueError,)):
        try:
            function()
        except errors as error:
            report["negative_cases"].append({"name": name, "diagnostic": str(error)})
        else:
            raise ValueError("retention defect was not rejected: " + name)

    # Enumerate physical files independently of the closed-form capacity sum.
    physical = []
    for mode in range(4):
        physical.extend((2 * 24 * 896 * 8, 151936 * 2 * 8))
        for position in range(2):
            physical.extend([896 * 8] * 24 + [151936 * 8])
    for mode in range(3):
        for repeat in range(2):
            for position in range(2):
                physical.extend([896 * 4] * 24)
            for position in range(2 + 3):
                physical.extend((24 * 896 * 4, 151936 * 4))
    for fragment in (512, 4096, 65536):
        actual = array_allocation(
            [{"teacher_positions": 2, "greedy_positions_maximum": 3}], fragment)
        expected = sum(((size + fragment - 1) // fragment) * fragment for size in physical)
        require(actual["rounded_array_data_bytes_one_successful_attempt"] == expected and
                actual["unique_array_payload_file_inodes_one_attempt"] == len(physical) and
                actual["hard_link_alias_pathnames_one_attempt"] == 6 * 2 * 25,
                "array allocation differs from independently enumerated files")
    report["enumerated_filesystem_fragment_cases"] = 3

    positions = 2
    reference_values = {}
    for mode_number, mode in enumerate(("checkpoint", "bf16", "fp16", "w4a16")):
        source = destination / mode / "raw"
        source.mkdir(parents=True)
        originals = {}
        for kind, shape in (("layers", (positions, 24, 896)),
                            ("logits", (151936, positions))):
            # Finite, exactly representable values with distinct axes and modes.
            array = (np.arange(np.prod(shape), dtype="<f8") / 1024 +
                     16 * mode_number).reshape(shape)
            array.flat[:6] = [0.0, -0.0, np.nextafter(0.0, 1.0),
                              -np.nextafter(0.0, 1.0), 2.0**100, -2.0**100]
            originals[kind] = array
            with (source / (kind + ".f64")).open("xb") as stream:
                stream.write(array.tobytes())
        reference_values[mode] = originals
        cache = source / "position-views"
        aliases = []
        for consumer in range(3):
            target = destination / mode / f"consumer-{consumer}"
            rows = collect(source, target, positions, shared=cache)
            compared = 0
            for position, row in enumerate(rows):
                for layer, item in enumerate(row["layers"]):
                    observed = artifact_path(ROOT, item["fp64_output"]["path"])
                    cached = cache / f"position-{position:05d}" / f"layer-{layer:02d}.f64"
                    expected = originals["layers"][position, layer].tobytes()
                    require(observed.read_bytes() == expected and
                            os.path.samefile(observed, cached) and
                            observed.stat().st_nlink == consumer + 2,
                            "layer axis, bytes or actual hard-link sharing differs")
                    compared += len(expected)
                observed = artifact_path(ROOT, row["fp64_logits"]["path"])
                expected = originals["logits"][:, position].tobytes()
                require(observed.read_bytes() == expected and os.path.samefile(
                    observed, cache / f"position-{position:05d}" / "logits.f64"),
                    "vocabulary-major transpose or hard-link sharing differs")
                compared += len(expected)
            require(compared == positions * (24 * 896 + 151936) * 8,
                    "reference byte comparisons incomplete")
            aliases.append(target)
            report["cases"].append({"mode": mode, "consumer": consumer,
                                    "positions": positions, "compared_bytes": compared})
        reject(mode + "/occupied-output", lambda: collect(
            source, aliases[0], positions, shared=cache))
        reject(mode + "/wrong-position-count", lambda: collect(
            source, destination / mode / "wrong-count", 1, shared=cache))

        # All linked aliases are intentionally immutable shared references. A
        # damaged cache fails by its original binding; never repair it in place.
        damaged = cache / "position-00000/layer-00.f64"
        with damaged.open("r+b") as stream:
            stream.write(b"\xff")
        reject(mode + "/changed-cache-payload", lambda: collect(
            source, destination / mode / "damaged-cache-consumer",
            positions, shared=cache))
        with (source / "layers.f64").open("r+b") as stream:
            stream.write(b"\x01")
        reject(mode + "/changed-raw-reference", lambda: collect(
            source, destination / mode / "damaged-source-consumer",
            positions, shared=cache))
        incomplete = source / "incomplete-cache"
        incomplete.mkdir()
        reject(mode + "/incomplete-cache", lambda: collect(
            source, destination / mode / "incomplete-cache-consumer",
            positions, shared=incomplete), errors=(OSError,))

    # Execute the actual production comparison call sites, without running a
    # model or simulator. The two synthetic observation files are independent.
    integration = destination / "comparison-call-sites"
    references = {}
    for mode, arrays in reference_values.items():
        source = integration / "references" / mode
        source.mkdir(parents=True)
        references[mode] = {}
        for kind, array in arrays.items():
            path = source / (kind + ".f64")
            with path.open("xb") as stream:
                stream.write(array.tobytes())
            references[mode][kind] = descriptor(path)

    class Comparisons:
        receipt = {}
        assertions = []

        def assertion(self, name, passed, **details):
            require(passed, name)
            self.assertions.append({"name": name, "passed": passed, **details})

    comparison = Comparisons()
    for mode in ("bf16", "fp16", "w4a16"):
        runs = []
        for repeat in range(2):
            run = integration / f"{mode}-repeat-{repeat}"
            runs.append(run)
            for position in range(positions):
                directory = run / f"position-{position}"
                directory.mkdir(parents=True)
                for kind, values in (
                        ("layers", reference_values[mode]["layers"][position]),
                        ("logits", reference_values[mode]["logits"][:, position])):
                    with (directory / (kind + ".f32")).open("xb") as stream:
                        stream.write(values.astype("<f4").tobytes())
        compare_teacher(comparison, "synthetic-retention", mode, runs, references,
                        positions, integration / (mode + "-comparison"), synthetic=True)
        require(not os.path.samefile(
            runs[0] / "position-0/logits.f32", runs[1] / "position-0/logits.f32"),
            "independent synthetic observations unexpectedly share an inode")
    cache = integration / "references/checkpoint/position-views"
    for position in range(positions):
        original = cache / f"position-{position:05d}" / "logits.f64"
        require(original.stat().st_nlink == 4, "checkpoint reference was copied per mode")
        for mode in ("bf16", "fp16", "w4a16"):
            alias = (integration / (mode + "-comparison") / "checkpoint-reference" /
                     f"position-{position:05d}" / "logits.f64")
            require(os.path.samefile(original, alias), "comparison bypassed shared reference views")
    report["synthetic_production_comparison_call_sites"] = comparison.assertions

    # Exercise the unchanged 44-byte ordered gzip witness decoder. No ratio is
    # extrapolated to a real transaction workload.
    rng = random.Random(17)
    records = []
    cycle = 0
    for number in range(4096):
        accepted = cycle + rng.randrange(1, 5)
        cycle = accepted + rng.randrange(1, 5)
        records.append(struct.pack("<11I", accepted, 0, cycle, 0, number % 2,
                                   number % 13, number % 24, number % 7,
                                   rng.getrandbits(32), rng.getrandbits(32),
                                   rng.getrandbits(32)))
    raw = b"".join(records)
    path = destination / "transactions.u32.gz"
    with path.open("xb") as stream:
        stream.write(gzip.compress(raw, compresslevel=1, mtime=0))
    require(gzip.decompress(path.read_bytes()) == raw, "gzip complete byte comparison differs")
    observation = inspect_trace(path, destination / "trace-inspection.json")
    require(observation["decompressed_sha256"] == hashlib.sha256(raw).hexdigest() and
            observation["records"] == len(records), "trace decode omitted or altered records")
    baseline = descriptor(path)

    class Inputs:
        receipt = {}

    require(checked(Inputs(), baseline) == path, "pristine trace binding rejected")
    encoded = path.read_bytes()
    crc_damage = bytearray(encoded)
    crc_damage[-8] ^= 1
    for name, payload in (
            ("truncated-trailer", encoded[:-1]),
            ("bad-crc", bytes(crc_damage)),
            ("trailing-junk", encoded + b"x"),
            ("partial-record", gzip.compress(raw[:-1], mtime=0)),
            ("out-of-order", gzip.compress(records[1] + records[0], mtime=0))):
        mutant = destination / (name + ".gz")
        with mutant.open("xb") as stream:
            stream.write(payload)
        reject("trace/" + name, lambda mutant=mutant, name=name: inspect_trace(
            mutant, destination / (name + ".json")),
            errors=(ValueError, OSError, EOFError, zlib.error))
    altered = destination / "valid-gzip-altered-payload.gz"
    with altered.open("xb") as stream:
        stream.write(gzip.compress(raw[:-1] + bytes([raw[-1] ^ 1]), mtime=0))
    reject("trace/recomputed-crc-binding", lambda: checked(
        Inputs(), {"path": str(altered.relative_to(ROOT)), "sha256": baseline["sha256"]}))
    report["trace"] = {"records": len(records), "compared_decoded_bytes": len(raw),
                       "gzip_eof_crc_checked": True, "complete_workload_capacity_claim": False}
    report["tools"] = {"python": sys.version, "numpy": np.__version__,
                       "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION}
    write_json(destination / "qualification.json", report)
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("synthetic", "capacity"))
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--repair-of", type=Path)
    args = parser.parse_args()
    if args.worker == "synthetic":
        require(args.destination is not None, "synthetic worker needs a destination")
        synthetic(artifact_path(ROOT, str(args.destination)))
        return 0
    if args.worker == "capacity":
        require(args.destination is None, "capacity worker is read-only")
        from collection_capacity import assess, selftest
        comparisons = selftest()
        report = assess()
        report["enumerated_schedule_count_comparisons"] = comparisons
        print(json.dumps(report, indent=2))
        return 0
    require(args.destination is None, "destination is only for a synthetic worker")
    ev = Evidence("retention-storage")
    ok = False
    try:
        ev.receipt["tool_versions"] = {"python": sys.version,
                                       "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION}
        ev.receipt["repair_of"] = [
            {"path": name, "sha256": sha(ROOT / name)} for name in (
                "evidence/preparation/verifier-collection-capacity-hqpj7fhp/receipt.json",
                "evidence/preparation/verifier-production-simulation-ppyyw3sv/receipt.json")]
        if args.repair_of is not None:
            previous = artifact_path(ROOT, str(args.repair_of))
            require(load_json(previous)["status"] == "failed",
                    "repair link is not a failed receipt")
            ev.receipt["repair_of"].append(
                {"path": str(args.repair_of), "sha256": sha(previous)})
        ev.receipt["scope"] = "Synthetic diagnostics and read-only assessment only"
        diagnostic = ev.run("synthetic-retention", [
            sys.executable, "tests/retention_storage.py", "--worker", "synthetic",
            "--destination", str((ev.path / "synthetic").relative_to(ROOT))], timeout=3600)
        require(ev.assertion("synthetic_retention_qualified", diagnostic),
                "synthetic retention failed; retained diagnostics must be repaired first")
        ev.receipt["qualification"] = load_json(ev.path / "synthetic/qualification.json")
        require(ev.run("complete-capacity", [
            sys.executable, "tests/retention_storage.py", "--worker", "capacity"],
            timeout=3600), "complete-workload assessment failed")
        report = load_json(ev.path / "complete-capacity.stdout")
        ev.receipt["assessment"] = report
        ok = report["full_suite_capacity_proven"]
        ev.assertion("complete_workload_storage_qualified", ok,
                     external_prerequisite=report["external_storage_prerequisite"],
                     reserved_bytes=0, collection_resumption_authorized=False)
    except (ValueError, KeyError, OSError, ImportError) as error:
        ev.assertion("retention_recovery_exception", False, diagnostic=repr(error))
    finally:
        ev.receipt["outputs"] = {str(path.relative_to(ROOT)): sha(path)
                                 for path in ev.path.rglob("*")
                                 if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if ok else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
