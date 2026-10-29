#!/usr/bin/env python3
"""Synthetic AWQ/reference lifetime and metadata diagnostics, never collection."""

import argparse
import gc
import inspect
import json
import os
from pathlib import Path
import resource
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import load_json, require, sha
from memory_capacity_checks import Monitor, availability, process_sample
from reference_memory_checks import extents
from verify import Evidence, ROOT


PRIOR = "evidence/preparation/verifier-reference-component-memory-_62eqypi/receipt.json"
SHAPES = {"q": (896, 896), "k": (128, 896), "v": (128, 896),
          "o": (896, 896), "gate": (4864, 896), "up": (4864, 896),
          "down": (896, 4864)}


def fixture(directory, patterned=False):
    import numpy as np
    from awq_prepare import AWQStream, GROUP, NIBBLE_ORDER, RECIPE

    directory.mkdir()
    tensors = {}
    with (directory / "weights.bin").open("xb") as weights, \
            (directory / "zeros.bin").open("xb") as zeros, \
            (directory / "scales.bin").open("xb") as scales:
        for name, (outputs, inputs) in SHAPES.items():
            groups = inputs // GROUP
            # Physical nibble positions derive from the frozen stream contract.
            word = (sum((lane + 1) << (4 * nibble)
                        for lane, nibble in enumerate(NIBBLE_ORDER))
                    if patterned else 0x11111111)
            item = {"shape": [outputs, inputs], "encoding": "packed-u4",
                    "byte_offset": weights.tell(), "byte_length": outputs * inputs // 2,
                    "zero_offset": zeros.tell(), "scale_offset": scales.tell()}
            tensors[name] = item
            weights.write(np.full((inputs, outputs // 8), word, dtype="<u4").tobytes())
            zeros.write(np.full((groups, outputs // 8),
                               0x33333333 if patterned else 0x11111111,
                               dtype="<u4").tobytes())
            scales.write(np.full((groups, outputs), .125, dtype="<f2").tobytes())
    (directory / "layout.json").write_text(json.dumps({
        "recipe": RECIPE, "nibble_order": list(NIBBLE_ORDER),
        "group_size": GROUP, "tensors": tensors}, indent=2) + "\n")
    return AWQStream(directory)


def deep_size(value):
    seen = set()

    def visit(item):
        if id(item) in seen:
            return 0
        seen.add(id(item))
        children = (list(item.keys()) + list(item.values()) if isinstance(item, dict)
                    else item if isinstance(item, (list, tuple)) else ())
        return sys.getsizeof(item) + sum(visit(child) for child in children)

    return visit(value)


def raw_storage(rows, block):
    from collection_capacity import array_allocation, transactions
    from production_schedule import PRODUCTION

    allocation = array_allocation(rows, block)
    counts = {bound: 0 for bound in ("minimum", "maximum")}
    for row in rows:
        for precision in range(3):
            teacher = transactions(PRODUCTION, precision, row["teacher_positions"])
            for bound, positions in (
                    ("minimum", row["prompt_positions"]),
                    ("maximum", row["greedy_positions_maximum"])):
                counts[bound] += 2 * (teacher + transactions(PRODUCTION, precision, positions))
    return {
        "format": "admitted raw arrays and gzip level-1 44-byte transaction records",
        "cases": len(rows), "modes": 3, "independent_repeats": 2,
        "independent_observer_processes_and_gzip_containers": len(rows) * 3 * 2 * 2,
        "rounded_array_bytes_success_plus_one_retained_failure":
            2 * allocation["rounded_array_data_bytes_one_successful_attempt"],
        "array_payload_inodes_success_plus_one_retained_failure":
            2 * allocation["unique_array_payload_file_inodes_one_attempt"],
        "decoded_trace_records_one_successful_attempt": counts,
        "decoded_trace_bytes_one_successful_attempt":
            {key: value * 44 for key, value in counts.items()},
        "decoded_trace_bytes_success_plus_one_retained_failure":
            {key: value * 88 for key, value in counts.items()},
        "gzip_retained_bytes_bound": None,
        "additional_costs": {
            "gzip_payloads_and_flush_overhead": None,
            "events_and_child_stdout_stderr": None,
            "reference_and_comparison_position_indexes": None,
            "600_cumulative_progress_indexes_and_collection_index": None,
            "receipts_and_atomic_serialization_staging": None,
            "build_products_and_compiler_linker_staging": None,
            "memory_tables_rope_tokens_and_other_check_native_gate_artifacts": None,
            "directory_entries_inode_extent_metadata": None},
        "complete_raw_gzip_storage_requirement_bytes": None,
        "full_workload_storage_qualified": False,
        "compression_ratio_assumed": False,
        "packed_collection_enabled": False,
        "limitation": "Decoded trace bytes are workload counts, not a gzip size bound "
                     "or a compressed-size lower bound. Flush/log/metadata/build costs "
                     "are not capped by the admitted command. No complete finite "
                     "filesystem bound is established; arrays alone already require "
                     "the stated budget. Existing retained evidence is not deleted.",
    }


def metadata_fixture(rows, snapshot):
    """Replay only the admitted record schemas, not execution or numerical results."""
    index = {"schema": 1, "purpose": "synthetic-metadata-only", "runs": [],
             "acceptance_evidence": False}
    evidence = {"records": [], "assertions": [], "data_sha256": {}}
    largest_serialized = cumulative = peak_object = 0
    for case_number, row in enumerate(rows):
        base = f"synthetic/case-{case_number:02d}"
        evidence["records"].append({
            "label": f"case-{case_number:02d}-independent-fp64",
            "argv": ["python3", "tests/production_sim.py", "--reference-worker"],
            "cwd": ".", "timeout_s": 86400, "exit_code": 0, "timed_out": False,
            "started_at": "synthetic", "ended_at": "synthetic",
            "stdout": base + "/reference.stdout", "stderr": base + "/reference.stderr"})
        for mode in ("bf16", "fp16", "w4a16"):
            for workload in ("teacher", "greedy"):
                for repeat in range(2):
                    label = f"case-{case_number:02d}-{mode}-{workload}-{repeat}"
                    record = {"case": base, "mode": mode, "workload": workload,
                              "repeat": repeat, "teacher_positions": row["teacher_positions"],
                              "complete_process": True, "path": base + "/" + label}
                    index["runs"].append(record)
                    evidence["records"].append({
                        "label": label, "argv": [base + "/simulator", base + "/memory",
                        base + "/tokens", base + "/rope", record["path"], mode, workload,
                        "151645,151643", "preparation-only", base + "/layers.f64",
                        base + "/logits.f64", str(row["teacher_positions"])],
                        "cwd": ".", "timeout_s": 86400, "started_at": "synthetic",
                        "ended_at": "synthetic", "exit_code": 0, "timed_out": False,
                        "stdout": base + "/" + label + ".stdout",
                        "stderr": base + "/" + label + ".stderr"})
                    evidence["assertions"].append(
                        {"name": label + "_actual_rtl_completed", "passed": True, **record})
                    for kind in ("memory", "tokens", "rope"):
                        evidence["data_sha256"][base + "/" + mode + "-" +
                                                workload + "." + kind] = "0" * 64
                    serialized = json.dumps(index, indent=2) + "\n"
                    cumulative += len(serialized.encode())
                    largest_serialized = max(largest_serialized, len(serialized.encode()))
                evidence["assertions"].append({
                    "name": "synthetic-comparison-schema", "passed": True,
                    "case": base, "mode": mode, "workload": workload})
        # Size the actual surviving metadata containers, not fifty concurrent references.
        encoded = json.dumps(evidence, indent=2) + "\n"
        peak_object = max(peak_object, deep_size((index, evidence, serialized, encoded)))
    require(len(index["runs"]) == 600 and len(evidence["records"]) == 650 and
            len(evidence["assertions"]) == 900, "metadata schema replay incomplete")
    snapshot("metadata-after-600-runs", deep_object_graph_bytes=peak_object)
    positions = max(row["teacher_positions"] for row in rows)

    def descriptor(path):
        return {"path": path, "sha256": "0" * 64}

    reference_indexes = []
    for kind in ("selected-reference", "checkpoint-reference"):
        reference_indexes.append([{
            "position": position,
            "layers": [{"layer": layer, "fp64_output": descriptor(
                f"synthetic/{kind}/position-{position:05d}/layer-{layer:02d}.f64")}
                for layer in range(24)],
            "fp64_logits": descriptor(f"synthetic/{kind}/position-{position:05d}/logits.f64")}
            for position in range(positions)])
    observed, metrics = [], []
    for position in range(positions):
        row = {"position": position, "layers": []}
        for field in ("logits", "repeat_logits", "fp64_logits",
                      "decoded_weight_logits", "checkpoint_fp64_logits"):
            row[field] = descriptor(f"synthetic/{field}/position-{position:05d}/logits.f64")
        for layer in range(24):
            row["layers"].append({"layer": layer, **{
                field: descriptor(f"synthetic/{field}/position-{position:05d}/"
                                  f"layer-{layer:02d}.f64")
                for field in ("output", "repeat_output", "fp64_output")}})
        observed.append(row)
        for item in ("logits", *(f"layer-{layer}" for layer in range(24)),
                     "storage-quantization"):
            metrics.append({"label": f"synthetic/{position}/{item}", "cosine": 1.,
                            "normalized_error": 0., "max_ulp": 0, "max_xor": 0,
                            "zero_pairs": 0, "nan_pairs": 0, "infinity_pairs": 0,
                            "signed_zero_differences": 0})
    comparison = {"case": "synthetic", "mode": "w4a16", "positions": observed,
                  "metrics": metrics, "complete_benchmark": False,
                  "acceptance_evidence": False}
    comparison_json = json.dumps(comparison, indent=2) + "\n"
    comparison_size = deep_size((index, evidence, reference_indexes,
                                 comparison, comparison_json, encoded))
    snapshot("maximum-teacher-comparison-metadata",
             deep_object_graph_bytes=comparison_size,
             reference_position_records=2 * positions,
             observed_layer_records=positions * 24, metric_records=positions * 26)
    del reference_indexes, observed, metrics, comparison, comparison_json
    greedy_steps = [{"context": [17] * (row["greedy_positions_maximum"] - 127 + step),
                     "logits": descriptor(f"synthetic/greedy-{step}/logits.f32"),
                     "repeat_logits": descriptor(f"synthetic/repeat-{step}/logits.f32")}
                    for step in range(128)]
    greedy_size = deep_size((index, evidence, greedy_steps, encoded))
    require(len(greedy_steps[-1]["context"]) == max(
        row["greedy_positions_maximum"] for row in rows),
        "greedy metadata maximum extent differs")
    snapshot("maximum-greedy-context-metadata", deep_object_graph_bytes=greedy_size)
    return {"runs": 600, "child_records": 650, "assertions": 900,
            "fixture_object_graph_peak_bytes": peak_object,
            "teacher_comparison_fixture_object_graph_bytes": comparison_size,
            "greedy_fixture_object_graph_bytes": greedy_size,
            "largest_progress_json_bytes": largest_serialized,
            "cumulative_progress_json_bytes": cumulative,
            "final_evidence_json_bytes": len(encoded.encode()),
            "complete_orchestrator_memory_bound_bytes": None,
            "limitation": "Synthetic schema/short-path fixture, not run_collection. "
                         "No tool output or claimed RTL result is published. Real paths, "
                         "timestamps, diagnostics, additional hashes and comparison "
                         "objects add costs. sys.getsizeof excludes allocator arenas, "
                         "modules and native allocations; serialized sizes are not caps."}


def worker(destination):
    import numpy as np
    from unittest.mock import patch
    import awq_prepare
    import teacher_reference
    from collection_capacity import memory_accounting

    awq_prepare.numerics()
    positions, observer, bindings, rows = extents()
    destination.mkdir()
    report = {"purpose": "synthetic-complete-reference-lifetime-diagnostic",
              "acceptance_evidence": False, "collection_launched": False,
              "whole_process_memory_qualified": False, "numpy_version": np.__version__,
              "python_version": sys.version, "teacher_positions": positions,
              "observer_positions": observer, "token_sha256": bindings,
              "phases": [], "repeats": []}

    def snapshot(phase, **detail):
        samples = process_sample(os.getpid())
        require(len(samples) == 1, "unexpected lifetime worker subprocess")
        report["phases"].append({"phase": phase, **samples[0][1],
            "ru_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            **detail})
        print(json.dumps({"phase": phase}), flush=True)

    patterned = fixture(destination / "patterned-awq", patterned=True)
    for name in ("gate", "down"):
        values = patterned.weight(name)
        expected = ((np.arange(SHAPES[name][0]) % 8 + 1) - 3) * .125
        require(values.shape == SHAPES[name] and
                np.all(values == expected[:, None]), "maximum AWQ shape known answer differs")
        snapshot("maximum-awq-" + name, decoded_payload_bytes=values.nbytes)
        del values
    del patterned
    stream = fixture(destination / "zero-matrix-awq")

    class SyntheticStream:
        tensors = {"model.embed_tokens.weight": {"dtype": "F16"}}

        def get(self, name):
            require(name == "model.embed_tokens.weight", "unexpected synthetic get")
            return np.broadcast_to(np.array(.125, dtype="<f2"), (151936, 896))

        decode_rows = staticmethod(awq_prepare.AWQStream.decode_rows)

        def weight(self, name, mode):
            require(mode == "w4a16", "fixture only supports AWQ")
            if "layernorm.weight" in name or name == "model.norm.weight":
                return np.ones(896, dtype="<f8")
            if name.endswith(".bias"):
                return np.zeros(128 if ".k_proj." in name or ".v_proj." in name
                                else 896, dtype="<f8")
            suffix = name.split(".")[-2].removesuffix("_proj")
            return stream.weight(suffix, mode)

    # Observe the actual unchanged functions; do not retain frame/array references.
    selected = {}
    for function, prefixes in (
            (awq_prepare.batch_activations, ("layers.append(", "return np.asarray(")),
            (teacher_reference.reference_case, ("rows = decoded_rows(", "logits = rows @",
                                                "output.write(logits.", "return {"))):
        lines, start = inspect.getsourcelines(function)
        selected[function.__code__] = {
            start + offset: line.strip() for offset, line in enumerate(lines)
            if line.strip().startswith(prefixes)}
    events = {}

    def trace(frame, event, unused):
        if frame.f_code not in selected:
            return None
        if event == "line" and frame.f_lineno in selected[frame.f_code]:
            label = selected[frame.f_code][frame.f_lineno]
            events[label] = events.get(label, 0) + 1
            count = events[label]
            if count in (1, 2, 24, 148, 149):
                arrays = {key: value.nbytes for key, value in frame.f_locals.items()
                          if isinstance(value, np.ndarray)}
                layer_list = frame.f_locals.get("layers")
                if isinstance(layer_list, list):
                    arrays["retained_layer_list"] = sum(value.nbytes for value in layer_list)
                snapshot(label + f"/{count}", logical_named_array_bytes=arrays,
                         named_views_may_alias=True)
        return trace

    config = {"rms_norm_eps": 1e-6, "rope_theta": 1000000.}
    expected_logit = 896 * .125 * (.125 / np.sqrt(.125 ** 2 + 1e-6))
    for repeat in range(2):
        events.clear()
        with patch.object(teacher_reference, "selected_stream",
                          return_value=SyntheticStream()):
            sys.settrace(trace)
            try:
                actual = teacher_reference.reference_case(
                    {}, config, "w4a16", [17] * positions,
                    destination / f"reference-{repeat}", packed=False)
            finally:
                sys.settrace(None)
        layers = np.memmap(ROOT / actual["layers"]["path"], dtype="<f8",
                           mode="r", shape=(positions, 24, 896))
        require(np.all(layers == .125), "synthetic full-reference residual differs")
        del layers
        logits = np.memmap(ROOT / actual["logits"]["path"], dtype="<f8",
                           mode="r", shape=(151936, positions))
        maximum_error = 0.
        for start in range(0, 151936, 1024):
            maximum_error = max(maximum_error,
                                float(np.max(np.abs(logits[start:start + 1024] - expected_logit))))
        require(maximum_error < 1e-10 and actual["lowest_id_argmax"] == [0] * positions,
                "synthetic complete vocabulary known answer differs")
        del logits
        blocks = (151936 + 1023) // 1024
        require(events.get("layers.append(x.copy())") == 24 and
                events.get("rows = decoded_rows(stream, embedding[start:start + 1024], mode)") ==
                blocks and events.get("output.write(logits.astype(\"<f8\").tobytes())") == blocks,
                "actual layer or vocabulary loop coverage incomplete")
        report["repeats"].append({"repeat": repeat, "layers": 24, "vocabulary_blocks": blocks,
            "last_block_rows": 151936 % 1024, "positions": positions,
            "maximum_logit_known_answer_error": maximum_error,
            "layer_sha256": actual["layers"]["sha256"],
            "logit_sha256": actual["logits"]["sha256"], "line_event_counts": dict(events)})
        del actual
        gc.collect()
        snapshot(f"reference-{repeat}-released")
    require(report["repeats"][0]["layer_sha256"] == report["repeats"][1]["layer_sha256"] and
            report["repeats"][0]["logit_sha256"] == report["repeats"][1]["logit_sha256"],
            "synthetic serial repeats differ")
    report["metadata_fixture"] = metadata_fixture(rows, snapshot)
    report["visible_payload_accounting"] = memory_accounting(rows)
    report["scope"] = (
        "Actual unchanged AWQStream decoding in both maximum matrix orientations; "
        "two serial complete 24-layer reference_case calls at maximum frozen teacher "
        "extent, including raw serialization and all 149 vocabulary blocks. Synthetic "
        "zero matrices, broadcast constant embedding, unit norm and zero bias only. "
        "No checkpoint inference, DUT, independent production repeat, Code evaluator, "
        "comparison execution, build, hardware or collection. File-backed output pages "
        "may remain in kernel cache. Sampled RSS and visible allocation planning do not "
        "bound NumPy/BLAS/native allocator retention, library workspaces, build/kernel "
        "costs or complete production orchestration. No memory/storage reserved.")
    (destination / "report.json").write_text(json.dumps(report, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker is not None:
        require(not args.worker.is_absolute() and ".." not in args.worker.parts and
                (ROOT / args.worker).resolve().is_relative_to(ROOT),
                "worker destination must be project-relative")
        worker(ROOT / args.worker)
        return 0
    ev = Evidence("reference-lifetimes")
    ok = False
    try:
        require((ROOT / PRIOR).is_file(), "retained component receipt missing")
        ev.receipt["extends"] = {"path": PRIOR, "sha256": sha(ROOT / PRIOR)}
        positions, observer, bindings, rows = extents()
        suite = load_json(ROOT / "tests/data/benchmark_manifest.json")
        ordered = [case for group in suite["domains"].values() for case in group["cases"]]
        for row, case in zip(rows, ordered):
            row["prompt_positions"] = len(load_json(ROOT / case["prompt_tokens"]["path"]))
        ev.receipt["data_sha256"] = bindings
        ev.receipt["observed_availability"] = availability()
        stat = os.statvfs(ev.path)
        ev.receipt["admitted_raw_gzip_storage"] = raw_storage(rows, stat.f_frsize)
        ev.receipt["admitted_raw_gzip_storage"]["available_bytes_at_probe"] = (
            stat.f_bavail * stat.f_frsize)
        ev.receipt["admitted_raw_gzip_storage"]["reserved_bytes"] = 0
        # Bound only this synthetic fixture's raw files; never invoke production preflight.
        synthetic_array_bytes = 2 * positions * (24 * 896 + 151936) * 8
        require(stat.f_bavail * stat.f_frsize >= synthetic_array_bytes + 1024 ** 3,
                "insufficient space for bounded synthetic reference fixture")
        destination = ev.path / "synthetic"
        with Monitor() as monitor:
            ok = ev.run("reference-lifetime-worker", [
                sys.executable, "tests/reference_lifetime_checks.py", "--worker",
                str(destination.relative_to(ROOT))], timeout=3600)
        ev.receipt["sampled_orchestrator_and_worker"] = monitor.report()
        require(ok, "reference lifetime worker failed")
        require((ev.path / "reference-lifetime-worker.stderr").stat().st_size == 0,
                "reference lifetime worker emitted stderr")
        report = load_json(destination / "report.json")
        require(report["teacher_positions"] == positions and
                report["observer_positions"] == observer and
                report["token_sha256"] == bindings and len(report["repeats"]) == 2 and
                report["metadata_fixture"]["runs"] == 600 and
                report["collection_launched"] is False and
                report["whole_process_memory_qualified"] is False,
                "incomplete or overclaimed lifetime diagnostic")
        ev.assertion("synthetic_complete_reference_lifetimes", True,
                     positions=positions, layers=24, serial_repeats=2,
                     vocabulary_blocks_per_repeat=149,
                     complete_process_bound=False, capacity_admitted=False)
        ev.receipt["scope"] = report["scope"]
    except (OSError, ValueError, KeyError, ImportError) as error:
        ok = False
        ev.assertion("reference_lifetime_exception", False, error=repr(error))
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path) for path in ev.path.rglob("*")
            if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
