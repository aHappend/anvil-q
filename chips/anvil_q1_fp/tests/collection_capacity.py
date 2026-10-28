#!/usr/bin/env python3
"""Read-only whole-collector storage assessment, never collection permission."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import FORBIDDEN, load_json, require, sha
from production_schedule import PRODUCTION, schedule
from reference_capacity import measurement, measurement_selftest
from verify import Evidence, ROOT, now


MODES = ("bf16", "fp16", "w4a16")
REPEATS = 2
REFERENCE_BYTES = (24 * 896 + 151936) * 8
OBSERVATION_BYTES = REFERENCE_BYTES // 2
BINDINGS = (
    "tests/collection_capacity.py", "tests/production_sim.py", "tests/production_sim.cpp",
    "tests/production_schedule.py", "tests/teacher_reference.py",
    "tests/reference_collector.py", "tests/fp64_reference.py", "tests/awq_prepare.py",
    "tests/reference_capacity.py", "tests/data/model_manifest.json",
    "tests/data/benchmark_manifest.json", "tests/retention_storage.py",
)


def transactions(config, mode, positions):
    """Closed-form count of the independent architectural schedule, not RTL."""
    layers, hidden, intermediate, heads, kv_heads, dimension, group, vocab, depth = config
    require(type(positions) is int and 0 < positions <= depth and mode in (0, 1, 2),
            "invalid schedule count inputs")
    projection = 0
    for proj in range(7):
        inputs = intermediate if proj == 6 else hidden
        outputs = kv_heads * dimension if proj in (1, 2) else (
            intermediate if proj in (4, 5) else hidden)
        per_block = (inputs * 9 if mode else inputs * 2 + (inputs // group) * 9)
        projection += (outputs // 8) * per_block + outputs * (2 if proj < 3 else 1)
    per_layer = (14 * hidden + 3 * intermediate + projection +
                 3 * (heads + kv_heads) * dimension +
                 4 * kv_heads * dimension + heads * dimension)
    base = 6 * hidden + 2 * vocab * hidden + layers * per_layer
    causal = layers * heads * dimension * (2 * dimension + 3)
    return base * positions + causal * positions * (positions + 1) // 2


def selftest():
    from architecture import CONFIGURATIONS
    from types import SimpleNamespace
    from unittest.mock import patch
    measurement_selftest()
    for free_blocks, available_blocks in ((20, 20), (20, 7), (20, 0)):
        stat = SimpleNamespace(f_frsize=4096, f_blocks=100, f_bfree=free_blocks,
                               f_bavail=available_blocks, f_favail=37)
        with patch.object(os, "statvfs", return_value=stat):
            observed = filesystem_capacity(ROOT)
        require(observed["total_bytes"] == 409600 and
                observed["used_bytes"] == 327680 and
                observed["free_bytes_including_reserved"] == 81920 and
                observed["available_bytes"] == available_blocks * 4096 and
                observed["available_inodes"] == 37 and
                observed["fragment_bytes"] == 4096,
                "filesystem capacity includes unavailable reserved blocks")
    comparisons = 0
    for config in CONFIGURATIONS.values():
        for mode in range(3):
            for positions in range(1, config[-1] + 1):
                actual = sum(1 for _ in schedule(
                    config, mode, [index % config[-2] for index in range(positions)]))
                require(actual == transactions(config, mode, positions),
                        "analytical transaction count differs from enumerated schedule")
                comparisons += 1
    return comparisons


def filesystem_capacity(directory):
    stat = os.statvfs(directory)
    return {
        "total_bytes": stat.f_blocks * stat.f_frsize,
        "used_bytes": (stat.f_blocks - stat.f_bfree) * stat.f_frsize,
        "free_bytes_including_reserved": stat.f_bfree * stat.f_frsize,
        "available_bytes": stat.f_bavail * stat.f_frsize,
        "available_inodes": stat.f_favail,
        "fragment_bytes": stat.f_frsize,
    }


def retained_usage(directory):
    """Inventory sizes only; preserve failures, including unparseable receipts."""
    result = {"allocated_bytes": 0, "logical_bytes": 0, "files": 0,
              "receipt_status_counts": {}, "unreadable_receipts": [],
              "file_size_measurement_only": True, "started_at": now()}
    statuses = Counter()
    inodes = set()
    for parent, directories, filenames in os.walk(directory, followlinks=False):
        directories[:] = sorted(name for name in directories
                                if name not in FORBIDDEN and
                                not (Path(parent) / name).is_symlink())
        for name in sorted(filenames):
            path = Path(parent) / name
            info = path.lstat()
            result["files"] += 1
            require(result["files"] <= 1000000, "retained inventory exceeds bounded file limit")
            inode = (info.st_dev, info.st_ino)
            if inode not in inodes:
                result["allocated_bytes"] += info.st_blocks * 512
                inodes.add(inode)
            result["logical_bytes"] += info.st_size
            if name == "receipt.json" and not path.is_symlink():
                relative = str(path.relative_to(ROOT))
                if info.st_size > 8 * 1024 ** 2:
                    statuses["unparsed-size-limit"] += 1
                    result["unreadable_receipts"].append(
                        {"path": relative, "reason": "exceeds diagnostic 8 MiB read limit"})
                    continue
                try:
                    record = load_json(path)
                except (ValueError, OSError) as error:
                    statuses["unparseable"] += 1
                    result["unreadable_receipts"].append(
                        {"path": relative, "reason": str(error)})
                else:
                    statuses[record.get("status", "missing-status")] += 1
    result["receipt_status_counts"] = dict(statuses)
    result["unique_file_inodes"] = len(inodes)
    result["hard_link_aliases"] = result["files"] - len(inodes)
    result["ended_at"] = now()
    result["limitation"] = (
        "Live size inventory, not an atomic filesystem snapshot or integrity qualification. "
        "Existing retained failures already consume measured used space; do not add them twice.")
    return result


def array_allocation(rows, block, modes=3):
    """Data-block planning only; filesystem metadata is an additional cost."""
    require(type(block) is int and block > 0, "invalid filesystem fragment size")
    require(type(modes) is int and 1 <= modes <= 3, "invalid precision-mode count")
    references = modes + 1
    observations = modes * REPEATS

    def rounded(size):
        return (size + block - 1) // block * block

    payload_blocks = 0
    unique_files = namespace_files = 0
    for row in rows:
        n, g = row["teacher_positions"], row["greedy_positions_maximum"]
        payload_blocks += (
            references * (rounded(n * 24 * 896 * 8) + rounded(n * 151936 * 8)) +
            references * n * (24 * rounded(896 * 8) + rounded(151936 * 8)) +
            observations * (n + g) * (rounded(24 * 896 * 4) + rounded(151936 * 4)) +
            observations * n * 24 * rounded(896 * 4))
        unique_files += (2 * references + references * n * 25 +
                         observations * n * 24 + observations * (n + g) * 2)
        namespace_files += (2 * references + (references + observations) * n * 25 +
                            observations * n * 24 + observations * (n + g) * 2)
    return {
        "fragment_bytes": block,
        "rounded_array_data_bytes_one_successful_attempt": payload_blocks,
        "unique_array_payload_file_inodes_one_attempt": unique_files,
        "array_payload_pathnames_one_attempt": namespace_files,
        "hard_link_alias_pathnames_one_attempt": namespace_files - unique_files,
        "raw_reference_files_per_case": 2 * references,
        "reference_position_index_files_per_case": references + observations,
        "metadata_inodes_and_bytes_additional": True,
        "guaranteed_filesystem_allocation_bound": False,
        "limitation": "Rounded data payload is not a bound for directories, indexes, logs, "
                      "extent metadata, build products, transaction files or future failures. "
                      "Every hard-link alias needs a directory entry, not another payload inode.",
    }


def assess():
    from teacher_reference import validate_inputs
    # Validate genuine inputs, not a three-position predictor's unrelated subset.
    # The holder records the validator's data binding without launching inference.
    class Inputs:
        receipt = {}

        def assertion(self, name, passed, **detail):
            require(passed, name + ": " + str(detail))
            return passed

    holder = Inputs()
    model, suite, _, _ = validate_inputs(holder)
    rows = []
    for domain, group in suite["domains"].items():
        require(len(group["cases"]) == 10, "domain does not contain ten frozen cases")
        for case in group["cases"]:
            teacher = load_json(ROOT / case["teacher_tokens"]["path"])
            prompt = load_json(ROOT / case["prompt_tokens"]["path"])
            n, p = len(teacher), len(prompt)
            # The C++ collector executes prompt + generated[:-1], at most 128 new tokens.
            maximum_greedy = p + 127
            require(0 < n <= 32768 and 0 < maximum_greedy <= 32768,
                    "full workload exceeds legal sequence depth")
            fixed = {
                "four_raw_fp64_references": 4 * n * REFERENCE_BYTES,
                "four_unique_shared_reference_position_layouts":
                    4 * n * REFERENCE_BYTES,
                "teacher_arrays_three_modes_two_repeats":
                    3 * REPEATS * n * OBSERVATION_BYTES,
                "teacher_comparison_layer_copies":
                    3 * REPEATS * n * 24 * 896 * 4,
                "greedy_arrays_three_modes_two_repeats_maximum":
                    3 * REPEATS * maximum_greedy * OBSERVATION_BYTES,
            }
            traces = {}
            for mode in MODES:
                precision = 0 if mode == "w4a16" else 1 if mode == "bf16" else 2
                teacher_transactions = transactions(PRODUCTION, precision, n)
                greedy_minimum = transactions(PRODUCTION, precision, p)
                greedy_maximum = transactions(PRODUCTION, precision, maximum_greedy)
                traces[mode] = {
                    "teacher_transactions_per_repeat": teacher_transactions,
                    "greedy_transactions_per_repeat_minimum": greedy_minimum,
                    "greedy_transactions_per_repeat_maximum": greedy_maximum,
                    "raw_44_byte_trace_bytes_two_repeats_minimum":
                        REPEATS * (teacher_transactions + greedy_minimum) * 44,
                    "raw_44_byte_trace_bytes_two_repeats_maximum":
                        REPEATS * (teacher_transactions + greedy_maximum) * 44,
                }
            rows.append({
                "case": domain + "/" + case["id"], "teacher_tokens": case["teacher_tokens"],
                "prompt_tokens": case["prompt_tokens"], "teacher_positions": n,
                "prompt_positions": p, "greedy_positions_maximum": maximum_greedy,
                "fixed_payload_bytes": fixed, "trace_workload": traces,
            })
    require(len(rows) == 50 and len(suite["domains"]) == 5,
            "not the complete five-domain fifty-case suite")
    fixed = {name: sum(row["fixed_payload_bytes"][name] for row in rows)
             for name in rows[0]["fixed_payload_bytes"]}
    teacher_mandatory = sum(value for name, value in fixed.items()
                           if not name.startswith("greedy_"))
    fixed_maximum = sum(fixed.values())
    eliminated_duplicate_bytes = sum(2 * row["teacher_positions"] * REFERENCE_BYTES
                                     for row in rows)
    raw_trace = {
        bound: sum(row["trace_workload"][mode][
            f"raw_44_byte_trace_bytes_two_repeats_{bound}"] for row in rows for mode in MODES)
        for bound in ("minimum", "maximum")
    }
    retained = retained_usage(ROOT / "evidence/preparation")
    filesystem = filesystem_capacity(ROOT)
    available_bytes = filesystem["available_bytes"]
    allocation = array_allocation(rows, filesystem["fragment_bytes"])
    # These are explicit planning allowances, NOT measured/reserved output bytes.
    positions = sum(row["teacher_positions"] + row["greedy_positions_maximum"] for row in rows)
    log_index_allowance = positions * 3 * REPEATS * 256 * 1024
    build_staging_allowance = 2 * 1024 ** 3
    one_failed_attempt_allowance = fixed_maximum + raw_trace["maximum"]
    return {
        "purpose": "complete-collector-retention-capacity-assessment",
        "acceptance_evidence": False, "source_sha256": {name: sha(ROOT / name) for name in BINDINGS},
        "input_sha256": holder.receipt.get("data_sha256", {}),
        "scope": {"cases": 50, "domains": 5, "modes": list(MODES), "repeats": REPEATS,
                  "teacher_positions": sum(row["teacher_positions"] for row in rows),
                  "prompt_positions": sum(row["prompt_positions"] for row in rows),
                  "greedy_positions_maximum": sum(row["greedy_positions_maximum"] for row in rows),
                  "independent_simulator_processes": 50 * 3 * 2 * 2,
                  "maximum_generated_tokens_per_case_mode_repeat": 128},
        "cases": rows, "fixed_payload_bytes": fixed,
        "mandatory_teacher_payload_bytes_before_greedy_or_traces": teacher_mandatory,
        "full_fixed_payload_maximum_bytes": fixed_maximum,
        "reference_view_retention": {
            "format": "unchanged FP64 files and descriptors; same-filesystem hard links",
            "unique_position_layouts_per_case": 4,
            "logical_position_layouts_per_case": 10,
            "logical_layouts_include": "Four cache layouts plus six consumer aliases",
            "raw_aggregate_modes_retained": 4,
            "duplicate_payload_bytes_eliminated": eliminated_duplicate_bytes,
            "observations_and_independent_repeats_shared": False,
            "partial_or_corrupt_cache_rebuilt": False,
            "copy_fallback_allowed": False},
        "filesystem_array_data_planning": allocation,
        "transaction_trace_raw_bytes": raw_trace,
        "transaction_trace_storage": {
            "format": "gzip level 1; each decoded record is 44 bytes",
            "compressed_bytes": None,
            "capacity_proven": False,
            "reason": "Actual gzip ratio and progress-flush counts are unmeasured for complete "
                      "teacher/generation traces. Raw counts are not compressed-byte predictions. "
                      "No three-position compression ratio is extrapolated."},
        "filesystem": {"storage_root": ".", "measured_at": now(), **filesystem,
                       "free_bytes_are_not_reserved": True},
        "retained_preparation": retained,
        "mandatory_teacher_capacity": measurement(teacher_mandatory, available_bytes),
        "capacity_guard_policy": {
            "reserve_bytes_means": "Estimated headroom: max(1 GiB, available_bytes // 10)",
            "actually_reserved_bytes": 0,
            "raw_fixed_payload_shortfall_without_headroom_bytes":
                max(0, teacher_mandatory - available_bytes)},
        "planning_scenarios": {
            "fixed_arrays_plus_estimated_metadata_build": measurement(
                fixed_maximum + log_index_allowance + build_staging_allowance, available_bytes),
            "raw_trace_basis_with_one_additional_retained_failure": measurement(
                fixed_maximum + raw_trace["maximum"] + log_index_allowance +
                build_staging_allowance + one_failed_attempt_allowance, available_bytes)},
        "estimated_headroom": {
            "metadata_and_raw_log_allowance_bytes": log_index_allowance,
            "simultaneous_build_and_temporary_staging_allowance_bytes": build_staging_allowance,
            "one_future_failed_full_attempt_raw_basis_bytes": one_failed_attempt_allowance,
            "guaranteed_bounds": False, "actually_reserved_bytes": 0},
        "peak_staging": {
            "collection_parallelism": 1,
            "largest_case_fixed_payload_maximum_bytes":
                max(sum(row["fixed_payload_bytes"].values()) for row in rows),
            "retained_fixed_payload_peak_bytes": fixed_maximum,
            "note": "Four raw reference modes and four unique position layouts coexist. "
                    "The six consumer reference trees hard-link those layouts; their payload "
                    "is not charged again. Independent observations, comparison layers and "
                    "transaction logs remain distinct. All cases accumulate; no files are "
                    "deleted after staging. In-memory FP64 temporaries are not disk reservations."},
        "external_storage_prerequisite": {
            "minimum_additional_array_payload_bytes_without_headroom":
                max(0, fixed_maximum - available_bytes),
            "maximum_successful_attempt_array_payload_bytes": fixed_maximum,
            "success_plus_one_retained_failure_array_payload_bytes": 2 * fixed_maximum,
            "rounded_array_data_bytes_success_plus_one_retained_failure":
                2 * allocation["rounded_array_data_bytes_one_successful_attempt"],
            "array_file_inodes_success_plus_one_retained_failure":
                2 * allocation["unique_array_payload_file_inodes_one_attempt"],
            "trace_bytes_additional": None,
            "requirement": "Provide same-filesystem hard-link-capable project storage for "
                           "all arrays, plus independently qualified full-workload gzip "
                           "trace retention, metadata, logs, build/staging and one retained "
                           "failed attempt. Available bytes are not a reservation. The "
                           "uncompressed trace count is not a gzip capacity prediction.",
            "complete_capacity_requirement_known": False},
        "full_suite_capacity_proven": False, "storage_provisioned_by_probe": False,
        "full_model_results_present": (ROOT / "tests/data/full_model_results.json").is_file(),
        "collection_launched": False, "rtl_rebuilt": False, "results_assembled": False,
        "limitations": [
            "Fixed arrays count current production_sim/reference_collector output layouts. "
            "JSON, stdout, stderr, build outputs, filesystem allocation and future failed runs "
            "need additional capacity; allowances are estimates, not reservations.",
            "Hard-link reference views eliminate two duplicate position layouts, not raw "
            "aggregates, independent repeats or observation layer copies. Codec ratios "
            "from short synthetic or retained prefixes establish no complete-workload fit.",
            "Missing/damaged histories are inventoried only, never reconstructed or overwritten.",
            "Fit at a measured instant is not independent review or collection authorization.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        comparisons = selftest()
        report = assess()
        report["enumerated_schedule_count_comparisons"] = comparisons
        print(json.dumps(report, indent=2))
        return 0
    ev = Evidence("collection-capacity")
    ok = False
    try:
        ev.receipt["tool_versions"] = {"python": sys.version}
        damaged = ROOT / "evidence/preparation/verifier-production-simulation-ppyyw3sv/receipt.json"
        ev.receipt["retained_failure"] = {
            "path": str(damaged.relative_to(ROOT)), "sha256": sha(damaged),
            "reconstructed": False}
        completed = ev.run("whole-collector-assessment", [
            sys.executable, "tests/collection_capacity.py", "--worker"], timeout=3600)
        require(completed, "capacity assessment failed; inspect retained child diagnostics")
        report = load_json(ev.path / "whole-collector-assessment.stdout")
        ev.assertion("whole_workload_assessed", True, scope=report["scope"],
                     count_comparisons=report["enumerated_schedule_count_comparisons"])
        ev.receipt["assessment"] = report
        ok = report["full_suite_capacity_proven"]
        ev.assertion("full_suite_storage_capacity_proven", ok,
                     mandatory_teacher_capacity=report["mandatory_teacher_capacity"],
                     reserved_bytes=0, collection_launched=False)
    except (ValueError, KeyError, OSError, ImportError) as error:
        ev.assertion("capacity_assessment_exception", False, diagnostic=repr(error))
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path)
            for path in ev.path.iterdir() if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if ok else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
