#!/usr/bin/env python3
"""Read-only whole-collector storage assessment, never collection permission."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import FORBIDDEN, load_json, require, sha, validate_input_manifests
from production_schedule import PRODUCTION, schedule
from reference_capacity import measurement, measurement_selftest
from verify import Evidence, ROOT, now


MODES = ("bf16", "fp16", "w4a16")
REPEATS = 2
REFERENCE_BYTES = (24 * 896 + 151936) * 8
OBSERVATION_BYTES = REFERENCE_BYTES // 2
BINDINGS = (
    "tests/benchmark.py",
    "tests/collection_capacity.py", "tests/production_sim.py", "tests/production_sim.cpp",
    "tests/production_schedule.py", "tests/teacher_reference.py",
    "tests/reference_collector.py", "tests/fp64_reference.py", "tests/awq_prepare.py",
    "tests/reference_capacity.py", "tests/data/model_manifest.json",
    "tests/data/benchmark_manifest.json", "tests/retention_storage.py",
    "tests/packed_storage.py",
    "tests/packed_stream.py", "tests/packed_stream.hpp", "tests/production_storage.hpp",
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


def packed_array_allocation(rows, block, modes=3):
    """Direct-producer no-ratio bound; not production permission or a fit certificate."""
    from packed_storage import CHUNK_BYTES, ENTRY, bound
    require(type(block) is int and block > 0 and type(modes) is int and 1 <= modes <= 3,
            "invalid packed capacity block/modes")
    total = files = maximum_case = maximum_index = 0
    for row in rows:
        n, g = row["teacher_positions"], row["greedy_positions_maximum"]
        require(type(n) is int and 0 < n <= 32768 and type(g) is int and 0 <= g <= 32768,
                "invalid packed capacity position count")
        # References: one immutable aggregate pair per selected weight semantics.
        # Observations: separate pairs for every position in each actual repeat.
        sizes = [(modes + 1, n * 24 * 896 * 8), (modes + 1, n * 151936 * 8),
                 (modes * REPEATS * (n + g), 24 * 896 * 4),
                 (modes * REPEATS * (n + g), 151936 * 4)]
        maximum_index = max(maximum_index, *(
            (raw + CHUNK_BYTES - 1) // CHUNK_BYTES * ENTRY.size for _, raw in sizes))
        case = sum(count * ((bound(raw) + block - 1) // block * block)
                   for count, raw in sizes)
        total += case
        files += sum(count for count, _ in sizes)
        maximum_case = max(maximum_case, case)
    return {
        "format": "anvil-packed-v1", "prospective_only": False,
        "producer_opt_in_implemented": True, "production_collection_enabled": False,
        "fragment_bytes": block, "cases": len(rows), "modes": modes, "repeats": REPEATS,
        "rounded_array_raw_fallback_bound_one_successful_attempt": total,
        "rounded_array_raw_fallback_bound_success_plus_one_retained_failure": 2 * total,
        "array_payload_inodes_one_successful_attempt": files,
        "array_payload_inodes_success_plus_one_retained_failure": 2 * files,
        "largest_case_array_raw_fallback_bound": maximum_case,
        "largest_array_index_spool_logical_bytes": maximum_index,
        "reference_position_and_observation_layer_payload_copies": 0,
        "compression_ratio_assumed": False,
        "metadata_logs_builds_staging_and_traces_included": False,
        "full_workload_storage_qualified": False,
        "limitation": "Logical container raw-fallback bounds rounded to data blocks only. "
                      "Not measured encoded bytes, a compression-ratio prediction, a full "
                      "filesystem allocation bound, storage reservation or collection authority.",
    }


def packed_workload_accounting(rows, block, modes=MODES):
    """Charge the full retained workload, explicitly exposing unbounded costs."""
    from packed_storage import CHUNK_BYTES, ENTRY, RECORD, bound
    require(isinstance(modes, (tuple, list)) and modes and len(set(modes)) == len(modes)
            and all(mode in MODES for mode in modes), "invalid accounting modes")
    arrays = packed_array_allocation(rows, block, len(modes))

    def rounded(size):
        return (size + block - 1) // block * block

    traces = support = trace_files = support_files = 0
    largest_case = largest_trace_index = 0
    transaction_count = 0
    for row in rows:
        n, g = row["teacher_positions"], row["greedy_positions_maximum"]
        require(type(n) is int and 0 < n <= 32768 and type(g) is int and 0 <= g <= 32768,
                "invalid complete accounting positions")
        # A partial teacher-only run has no greedy work. Full qualification
        # always supplies the prompt+127 maximum, not observed early EOS.
        case_traces = case_support = 0
        for mode in modes:
            precision = 0 if mode == "w4a16" else 1 if mode == "bf16" else 2
            for positions in (n, g):
                if not positions:
                    continue
                count = transactions(PRODUCTION, precision, positions)
                entries = (count + CHUNK_BYTES // RECORD.size - 1) // (
                    CHUNK_BYTES // RECORD.size)
                largest_trace_index = max(largest_trace_index, entries * ENTRY.size)
                case_traces += REPEATS * rounded(bound(count * 44, transactions=True))
                transaction_count += REPEATS * count
                trace_files += REPEATS
                # Collector retains one token-text and one RoPE file per
                # workload/mode; repeats share inputs, never observations.
                case_support += rounded(positions * 7) + rounded((positions + 1) * 64 * 4)
                support_files += 2
        case_support += rounded(n * 10 + 5)  # indented reference-worker JSON tokens
        support_files += 1
        traces += case_traces
        support += case_support
        case_arrays = packed_array_allocation([row], block, len(modes))[
            "rounded_array_raw_fallback_bound_one_successful_attempt"]
        largest_case = max(largest_case, case_arrays + case_traces + case_support)
    finite = arrays["rounded_array_raw_fallback_bound_one_successful_attempt"] + traces + support
    # The serial observer has three concurrent codec children: the full trace
    # plus two single-position arrays. FP64 layer/logit writers run sequentially.
    # A failed observer can retain all three spools while a retry is active.
    observation_indexes = sum(rounded(
        (raw + CHUNK_BYTES - 1) // CHUNK_BYTES * ENTRY.size)
        for raw in (24 * 896 * 4, 151936 * 4))
    index_staging = max(rounded(arrays["largest_array_index_spool_logical_bytes"]),
                        rounded(largest_trace_index) + observation_indexes)
    files = arrays["array_payload_inodes_one_successful_attempt"] + trace_files + support_files
    return {
        "format": "anvil-packed-v1", "cases": len(rows), "modes": list(modes),
        "repeats": REPEATS, "greedy_limit": 128,
        "array_data": arrays,
        "mandatory_trace_index_floor": packed_trace_index_floor(rows, modes),
        "transactions_one_attempt_maximum": transaction_count,
        "trace_data_block_bound_one_attempt": traces,
        "token_and_rope_data_block_bound_one_attempt": support,
        "bounded_data_blocks_one_successful_attempt": finite,
        "bounded_data_blocks_success_plus_one_retained_failure": 2 * finite + 2 * index_staging,
        "bounded_payload_inodes_one_successful_attempt": files,
        "bounded_payload_inodes_success_plus_one_retained_failure": 2 * files + 6,
        "retained_failed_attempt": {
            "count": 1, "charged_bounded_data_blocks": finite + index_staging,
            "policy": "Charge a complete additional attempt; never discard partial failures. "
                      "Already retained attempts are included in current filesystem used bytes."},
        "peak_staging": {
            "collection_parallelism": 1,
            "maximum_concurrent_index_writers": 3,
            "raw_array_or_trace_duplicate_disk_bytes": 0,
            "index_spool_data_block_bound_one_active_collection": index_staging,
            "index_spool_data_block_bound_success_plus_retained_failure": 2 * index_staging,
            "successful_index_spool_removed_after_seal": True,
            "failed_index_spool_retained": True,
            "largest_case_bounded_data_blocks": largest_case,
            "cumulative_retained_bounded_data_blocks": 2 * finite + 2 * index_staging,
            "receipt_atomic_staging_bound_bytes": None,
            "build_products_and_temporary_files_bound_bytes": None,
            "note": "All case outputs accumulate. Final indexes are included in container "
                    "bounds. Disk-backed index spools add one active plus one retained "
                    "failed-collection allowance, each up to three concurrent writers. "
                    "Unknown receipt/build staging is additional."},
        "host_memory": {
            "payload_chunk_bytes": 1024 * 1024,
            "complete_host_memory_bound_bytes": None,
            "index_block_bytes": CHUNK_BYTES // ENTRY.size * ENTRY.size,
            "workload_sized_index_python_lists": False,
            "limitation": "Writer index entries spool to disk and Reader scans bounded blocks "
                         "with on-disk random access. This bounds codec index buffers, not "
                         "total RSS. FP64 model/activation temporaries, JSON metadata and "
                         "whole-process memory have not been qualified."},
        "additional_costs": {
            "reference_and_comparison_view_json_indexes": {
                "bound_bytes": None, "reason": "No enforced serialized metadata byte limit."},
            "events_stdout_stderr_and_tool_logs": {
                "bound_bytes": None, "reason": "No enforced cumulative producer/log byte limit."},
            "incremental_collection_indexes_and_receipts": {
                "bound_bytes": None, "reason": "Retained progress and atomic receipt staging "
                "depend on unbounded metadata/log records and path lengths."},
            "memory_mapping_tables": {
                "bound_bytes": None, "reason": "No enforced path/serialized table byte limit."},
            "build_products_and_peak_build_staging": {
                "bound_bytes": None, "reason": "Tool output size has no enforced capacity cap."},
            "filesystem_directories_extents_and_inode_metadata": {
                "bound_bytes": None, "reason": "Data-block rounding is not a filesystem "
                "metadata allocation guarantee."},
        },
        "compression_ratio_assumed": False,
        "reference_view_payload_duplicates": 0,
        "repeat_observations_shared": False,
        "complete_capacity_bound_bytes": None,
        "full_workload_storage_qualified": False,
        "collection_resumption_authorized": False,
    }


def packed_trace_index_floor(rows, modes=MODES, config=PRODUCTION):
    """Uncompressed indexes impose a floor even if every payload compresses."""
    from packed_storage import CHUNK_BYTES, ENTRY, RECORD
    require(isinstance(modes, (tuple, list)) and modes and len(set(modes)) == len(modes)
            and all(mode in MODES for mode in modes), "invalid index-floor modes")
    records_per_chunk = CHUNK_BYTES // RECORD.size
    chunks = records = containers = largest_index = 0
    for row in rows:
        teacher, prompt = row["teacher_positions"], row["prompt_positions"]
        require(type(teacher) is int and type(prompt) is int and
                0 < prompt <= teacher <= config[-1], "invalid mandatory workload positions")
        for mode in modes:
            precision = 0 if mode == "w4a16" else 1 if mode == "bf16" else 2
            for positions in (teacher, prompt):
                count = transactions(config, precision, positions)
                entries = (count + records_per_chunk - 1) // records_per_chunk
                records += REPEATS * count
                chunks += REPEATS * entries
                containers += REPEATS
                largest_index = max(largest_index, entries * ENTRY.size)
    return {
        "format": "anvil-packed-v1",
        "basis": "Complete teacher sequences and all prompt tokens, even with immediate EOS. "
                 "No optional post-prompt generation or future failed attempt is charged.",
        "cases": len(rows), "modes": list(modes), "repeats": REPEATS,
        "mandatory_transaction_records": records,
        "mandatory_trace_containers": containers,
        "records_per_chunk": records_per_chunk, "index_entry_bytes": ENTRY.size,
        "mandatory_index_entries": chunks,
        "minimum_logical_index_bytes_one_successful_attempt": chunks * ENTRY.size,
        "largest_mandatory_container_index_bytes": largest_index,
        "compression_ratio_assumed": False,
        "excluded_costs": "All encoded payload, headers, footers, arrays, logs, metadata, "
                          "builds, staging and retained failures are additional.",
        "host_memory": "Writer spools entries to disk; Reader validates bounded blocks and "
                       "fetches entries on demand. Largest index bytes remain a disk cost, "
                       "not a requirement to hold the index in RAM or a full RSS bound.",
        "limitation": "Logical index bytes, not a filesystem allocation guarantee. "
                      "Transparent filesystem compression/deduplication and storage reservation "
                      "are not qualified by this accounting.",
        "full_workload_storage_qualified": False,
        "collection_resumption_authorized": False,
    }


def assess():
    # Validate genuine inputs, not a three-position predictor's unrelated subset.
    # The holder records the validator's data binding without launching inference.
    class Inputs:
        receipt = {}

        def assertion(self, name, passed, **detail):
            require(passed, name + ": " + str(detail))
            return passed

    holder = Inputs()
    model, suite, _, _ = validate_input_manifests(ROOT, holder)
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
    packed_allocation = packed_array_allocation(rows, filesystem["fragment_bytes"])
    packed_complete = packed_workload_accounting(rows, filesystem["fragment_bytes"])
    packed_complete["available_bytes_at_assessment"] = available_bytes
    packed_complete["bounded_data_budget_gap_before_unbounded_costs"] = max(
        0, packed_complete["bounded_data_blocks_success_plus_one_retained_failure"] -
        available_bytes)
    packed_complete["budget_gap_meaning"] = (
        "Additional bytes to provision the no-compression-fallback data-block budget, "
        "not a lower bound on actual encoded size or proof that a compression ratio fits.")
    index_floor = packed_complete["mandatory_trace_index_floor"]
    index_floor["available_bytes_at_assessment"] = available_bytes
    index_floor["logical_index_bytes_exceed_available_bytes"] = (
        index_floor["minimum_logical_index_bytes_one_successful_attempt"] > available_bytes)
    from packed_storage import bound as packed_bound
    packed_trace_bound = sum(
        REPEATS * sum(packed_bound(row["trace_workload"][mode][name] * 44,
                                  transactions=True)
                      for name in ("teacher_transactions_per_repeat",
                                   "greedy_transactions_per_repeat_maximum"))
        for row in rows for mode in MODES)
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
        "prospective_packed_array_data_bound": packed_allocation,
        "direct_packed_complete_workload_accounting": packed_complete,
        "prospective_packed_trace_bound": {
            "format": "anvil-packed-v1", "producer_enabled": False,
            "raw_fallback_logical_bytes_one_successful_attempt": packed_trace_bound,
            "raw_fallback_logical_bytes_success_plus_one_retained_failure": 2 * packed_trace_bound,
            "independently_retained_files_one_successful_attempt": 50 * 3 * REPEATS * 2,
            "compression_ratio_assumed": False,
            "metadata_logs_builds_staging_and_filesystem_allocation_included": False,
            "full_workload_storage_qualified": False},
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
