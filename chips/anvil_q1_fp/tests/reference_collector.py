#!/usr/bin/env python3
"""Qualify and collect complete FP64 teacher arrays; never create DUT results."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import load_json, require, sha
from benchmark_inputs import write_json
from teacher_reference import (MODES, descriptor, qualified, reference_case,
                               validate_inputs)
from awq_prepare import numerics
from verify import Evidence, ROOT


REFERENCE_SOURCES = ("tests/teacher_reference.py", "tests/fp64_reference.py",
                     "tests/awq_prepare.py")


def collect(source, destination, positions, *, shared=None):
    require(type(positions) is int and 0 < positions <= 32768,
            "invalid collector position count")
    layers_path, logits_path = source / "layers.f64", source / "logits.f64"
    require(layers_path.stat().st_size == positions * 24 * 896 * 8 and
            logits_path.stat().st_size == 151936 * positions * 8,
            "collector source dimensions differ")
    if shared is not None:
        return shared_collect(source, destination, positions, shared)
    layers = np.memmap(layers_path, dtype="<f8", mode="r",
                       shape=(positions, 24, 896))
    logits = np.memmap(logits_path, dtype="<f8", mode="r",
                       shape=(151936, positions))
    require(np.isfinite(layers).all() and np.isfinite(logits).all(),
            "nonfinite collector source")
    destination.mkdir(parents=True, exist_ok=False)
    rows = []
    for position in range(positions):
        directory = destination / f"position-{position:05d}"
        directory.mkdir()
        row = {"position": position, "layers": []}
        for layer in range(24):
            path = directory / f"layer-{layer:02d}.f64"
            expected = layers[position, layer].tobytes()
            with path.open("xb") as output:
                output.write(expected)
            require(path.read_bytes() == expected, "collected layer byte mismatch")
            row["layers"].append({"layer": layer, "fp64_output": descriptor(path)})
        path = directory / "logits.f64"
        expected = logits[:, position].tobytes()
        with path.open("xb") as output:
            output.write(expected)
        require(path.read_bytes() == expected, "collected logits byte mismatch")
        row["fp64_logits"] = descriptor(path)
        rows.append(row)
    write_json(destination / "positions.json", {
        "schema": 1, "purpose": "collected-fp64-teacher-reference",
        "acceptance_evidence": False, "dtype": "<f8",
        "sources": {"layers": descriptor(layers_path), "logits": descriptor(logits_path)},
        "positions": rows})
    return rows


def shared_collect(source, destination, positions, shared):
    """Keep the original file contract, sharing only immutable reference views.

    Repeats and DUT observations never enter this cache. An incomplete or changed
    cache is an error, not permission to rebuild or overwrite retained evidence.
    """
    require(not destination.exists() and shared != destination and
            shared.resolve().is_relative_to(source.resolve()) and
            not shared.is_symlink(), "invalid shared reference destination")
    inputs = {kind: descriptor(source / (kind + ".f64"))
              for kind in ("layers", "logits")}
    if not shared.exists():
        collect(source, shared, positions)
    index = load_json(shared / "positions.json")
    require(index["schema"] == 1 and index["dtype"] == "<f8" and
            index["purpose"] == "collected-fp64-teacher-reference" and
            index["sources"] == inputs and len(index["positions"]) == positions,
            "shared reference identity or coverage differs")
    destination.mkdir(parents=True, exist_ok=False)
    rows = []
    for position, original in enumerate(index["positions"]):
        require(original["position"] == position and len(original["layers"]) == 24,
                "shared reference positions/layers differ")
        directory = destination / f"position-{position:05d}"
        directory.mkdir()
        row = {"position": position, "layers": []}

        def link(item, name, size):
            cached = shared / f"position-{position:05d}" / name
            target = directory / name
            require(not cached.is_symlink() and cached.is_file() and
                    cached.stat().st_size == size and descriptor(cached) == item,
                    "shared reference bytes or binding changed")
            os.link(cached, target, follow_symlinks=False)
            require(os.path.samefile(cached, target) and sha(target) == item["sha256"],
                    "linked reference bytes differ")
            return descriptor(target)

        for layer, value in enumerate(original["layers"]):
            require(value["layer"] == layer, "shared reference layer order differs")
            row["layers"].append({"layer": layer, "fp64_output": link(
                value["fp64_output"], f"layer-{layer:02d}.f64", 896 * 8)})
        row["fp64_logits"] = link(original["fp64_logits"], "logits.f64", 151936 * 8)
        rows.append(row)
    require(inputs == {kind: descriptor(source / (kind + ".f64"))
                       for kind in inputs}, "raw references changed while linking")
    write_json(destination / "positions.json", {
        "schema": 1, "purpose": "collected-fp64-teacher-reference",
        "acceptance_evidence": False, "dtype": "<f8",
        "sources": inputs, "positions": rows})
    return rows


def retained_batched(ev, relative):
    record = qualified(ev, relative)
    require(any(row["name"] == "teacher_reference_qualification_completed" and
                row["passed"] for row in record["assertions"]),
            "missing retained batched qualification")
    require(all(record["source_sha256"][name] == sha(ROOT / name)
                for name in REFERENCE_SOURCES), "qualified mathematics changed")
    return record


def qualification_worker(args):
    numerics()
    record = load_json(ROOT / args.reference_receipt)
    model = load_json(ROOT / "tests/data/model_manifest.json")
    config = load_json(ROOT / model["config"]["path"])
    args.destination.mkdir(parents=True, exist_ok=False)
    comparisons = 0
    for mode in MODES:
        paths = {}
        for kind in ("layers", "logits"):
            matches = [name for name in record["outputs"]
                       if name.endswith(f"/{mode}/{kind}.f64")]
            require(len(matches) == 1, "missing qualified collector input")
            paths[kind] = ROOT / matches[0]
            require(sha(paths[kind]) == record["outputs"][matches[0]],
                    "qualified collector input changed")
        require(paths["layers"].parent == paths["logits"].parent,
                "collector inputs belong to different modes")
        recomputed = args.destination / ("recomputed-" + mode)
        reference_case(model, config, mode, [config["bos_token_id"], 17, 53], recomputed)
        for kind, path in paths.items():
            require(sha(recomputed / (kind + ".f64")) == sha(path),
                    "fresh-process teacher bytes differ from qualified reference")
        rows = collect(paths["layers"].parent, args.destination / mode, 3)
        # Compare with a separate explicit flat-offset traversal, not memmap indexing.
        for position, row in enumerate(rows):
            with paths["layers"].open("rb") as source:
                for layer, output in enumerate(row["layers"]):
                    source.seek(((position * 24 + layer) * 896) * 8)
                    require((ROOT / output["fp64_output"]["path"]).read_bytes() ==
                            source.read(896 * 8), "flat-offset layer comparison differs")
                    comparisons += 1
            with paths["logits"].open("rb") as source:
                expected = bytearray()
                for vocabulary in range(151936):
                    source.seek((vocabulary * 3 + position) * 8)
                    expected.extend(source.read(8))
            require((ROOT / row["fp64_logits"]["path"]).read_bytes() == expected,
                    "flat-offset logit comparison differs")
            comparisons += 1
    rejected = 0
    for positions in (0, -1, True, 32769, 2, 4):
        try:
            collect(paths["layers"].parent,
                    args.destination / f"invalid-{rejected}", positions)
        except ValueError:
            rejected += 1
        else:
            raise ValueError("collector accepted invalid shape/count")
    write_json(args.destination / "qualification.json", {
        "purpose": "fp64-position-collector-qualification",
        "acceptance_evidence": False, "complete_vector_byte_comparisons": comparisons,
        "rejected_invalid_counts_or_shapes": rejected,
        "modes": list(MODES), "qualified_positions_per_mode": 3,
        "fresh_process_complete_array_comparisons": 8,
        "scope": "Complete three-position arrays and actual fresh-process FP64 inference; "
                 "no DUT execution or complete-suite capacity guarantee."})


def full_worker(args):
    numerics()
    model = load_json(ROOT / "tests/data/model_manifest.json")
    suite = load_json(ROOT / "tests/data/benchmark_manifest.json")
    config = load_json(ROOT / model["config"]["path"])
    args.destination.mkdir(parents=True, exist_ok=False)
    index = {"schema": 1, "purpose": "complete-collected-teacher-reference-preparation",
             "acceptance_evidence": False, "arithmetic": "ieee-fp64",
             "independent_of_rtl": True, "cases": [],
             "model_manifest": descriptor(ROOT / "tests/data/model_manifest.json"),
             "benchmark_manifest": descriptor(ROOT / "tests/data/benchmark_manifest.json"),
             "reference_sources": {name: sha(ROOT / name) for name in REFERENCE_SOURCES},
             "collector_source": descriptor(ROOT / "tests/reference_collector.py"),
             "dependencies": {"numpy": np.__version__, "python": sys.version},
             "limitations": "Teacher references only; no DUT, repeat, greedy generation, "
                             "cycle, timing, resource or physical evidence."}
    for domain, group in suite["domains"].items():
        for case in group["cases"]:
            number = len(index["cases"])
            tokens = load_json(ROOT / case["teacher_tokens"]["path"])
            row = {"case": domain + "/" + case["id"],
                   "teacher_tokens": case["teacher_tokens"], "modes": {}}
            for mode in MODES:
                directory = args.destination / f"case-{number:02d}" / mode
                raw = reference_case(model, config, mode, tokens, directory / "raw")
                positions = collect(directory / "raw", directory / "collected", len(tokens))
                require(len(positions) == len(tokens), "collector omitted a teacher position")
                row["modes"][mode] = {
                    "raw": raw, "positions": descriptor(directory / "collected/positions.json")}
                print(json.dumps({"case": row["case"], "mode": mode,
                                  "teacher_positions": len(tokens), "collected_vectors":
                                  len(positions) * 25}), flush=True)
            write_json(args.destination / f"completed-through-{number:02d}.json", row)
            index["cases"].append(row)
    require(len(index["cases"]) == 50, "incomplete frozen teacher suite")
    write_json(args.destination / "teacher_references.json", index)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualify", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--reference-receipt", type=Path, required=True)
    parser.add_argument("--collector-receipt", type=Path)
    parser.add_argument("--capacity-receipt", type=Path)
    parser.add_argument("--repair-of", type=Path)
    args = parser.parse_args()
    for value in vars(args).values():
        if isinstance(value, Path):
            require(not value.is_absolute() and ".." not in value.parts and
                    (ROOT / value).resolve().is_relative_to(ROOT), "nonportable collector path")
    if args.worker:
        require(args.destination is not None, "missing collector destination")
        args.destination = (ROOT / args.destination).resolve()
        (qualification_worker if args.qualify else full_worker)(args)
        return 0
    ev = Evidence("reference-collector-qualification" if args.qualify else "reference-collector-full")
    ok = False
    try:
        if args.repair_of is not None:
            ev.receipt["repair_of"] = descriptor(ROOT / args.repair_of)
        retained_batched(ev, args.reference_receipt)
        ev.receipt["tool_versions"] = {"python": sys.version, "numpy": np.__version__}
        ev.receipt["numerical_threads"] = {key: os.environ.get(key) for key in
                                          ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")}
        command = [sys.executable, "tests/reference_collector.py", "--worker",
                   "--reference-receipt", str(args.reference_receipt),
                   "--destination", str((ev.path / "collected-reference").relative_to(ROOT))]
        if args.qualify:
            command += ["--qualify"]
        else:
            model, suite, cases, _ = validate_inputs(ev)
            require(args.collector_receipt is not None and args.capacity_receipt is not None,
                    "missing collector/capacity qualification")
            collector = qualified(ev, args.collector_receipt)
            require(collector["source_sha256"]["tests/reference_collector.py"] ==
                    sha(ROOT / "tests/reference_collector.py") and any(
                        row["name"] == "position_collector_qualified" and row["passed"]
                        for row in collector["assertions"]), "collector qualification differs")
            capacity = load_json(ROOT / args.capacity_receipt)
            require(capacity["status"] == "passed" and any(
                row["name"] == "projected_complete_reference_capacity" and row["passed"]
                for row in capacity["assertions"]), "capacity preflight did not pass")
            ev.receipt["capacity_preflight"] = descriptor(ROOT / args.capacity_receipt)
            ev.receipt["original_capacity_failure"] = descriptor(
                ROOT / "evidence/preparation/verifier-teacher-reference-full-kujiwuf1/receipt.json")
            positions = sum(len(case[3]) for case in cases.values())
            raw_bytes = positions * len(MODES) * (24 * 896 + 151936) * 8
            # Keep both layouts, and conservatively budget one filesystem block
            # beyond each file's payload plus JSON indexes.
            vectors = positions * len(MODES) * 25
            required = 2 * raw_bytes + vectors * 8192 + 1024 ** 3
            free = shutil.disk_usage(ROOT).free
            reserve = max(1024 ** 3, free // 10)
            require(ev.assertion("complete_raw_and_collected_capacity",
                                 required + reserve <= free, required_bytes=required,
                                 available_bytes=free, reserve_bytes=reserve,
                                 teacher_positions=positions, vector_files=vectors),
                    "insufficient storage for complete raw and collected reference arrays")
        ok = ev.run("reference-collector", command, timeout=82800)
        destination = ev.path / "collected-reference"
        ev.receipt["outputs"] = {str(path.relative_to(ROOT)): sha(path)
                                 for path in destination.rglob("*") if path.is_file()}
        name = "position_collector_qualified" if args.qualify else "complete_teacher_reference_collected"
        ok = ev.assertion(name, ok, acceptance_evidence=False) and ok
    except (ValueError, KeyError, OSError) as error:
        ok = False
        ev.assertion("reference_collector_exception", False, error=repr(error))
    finally:
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
