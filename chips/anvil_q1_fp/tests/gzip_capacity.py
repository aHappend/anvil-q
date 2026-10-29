"""Source-backed legacy gzip payload accounting, not filesystem qualification.

The derivation and its applicability limits are in tests/BENCHMARK.md.
No compression-ratio credit, collection permission or resource reservation.
"""

from benchmark import require


ZLIB_VERSION = "1.3"
ZLIB_COMMIT = "09155eaa2f9270dc4ed1fa13e2b4b2613e6e4851"
ZLIB_BLOBS = {
    "gzwrite.c": "435b4621b5349f2a98b92cff5fe7d9f6cd7ced59",
    "deflate.c": "bd011751920a87a6d94694751f1c36f3f48f86f2",
    "trees.c": "8dbdc40bacce1d101285b5944bf06e2647537f68",
    "gzguts.h": "f9375047e8c58f3c7e1907ed781a0388cacc9335",
}
MODES = ("bf16", "fp16", "w4a16")
RECORD_BYTES = 44


def natural(value, name):
    require(type(value) is int and value >= 0, "invalid " + name)
    return value


def round_data(size, fragment):
    natural(size, "logical size")
    require(type(fragment) is int and fragment > 0, "invalid fragment size")
    return ((size + fragment - 1) // fragment) * fragment


def trace_bound(writes, version=ZLIB_VERSION):
    """Bound one member for <=writes calls, each passing at most 44 bytes."""
    natural(writes, "trace write count")
    require(version == ZLIB_VERSION, "unreviewed zlib implementation")
    raw = RECORD_BYTES * writes
    return {
        "writes_charged": writes, "input_bytes_charged": raw,
        "nonempty_blocks_bytes": 5 * raw,
        "productive_sync_flush_bytes": 32 * (writes + 1),
        "finish_and_failure_cleanup_bytes": 64,
        "gzip_header_and_trailer_bytes": 18,
        "logical_bytes_bound": 5 * raw + 32 * (writes + 1) + 64 + 18,
    }


def workload(rows, fragment):
    """Schedule-envelope budget including one failed write per container.

    An erroneous DUT can exceed its expected schedule. The current collector
    does not cap that count, so this is not an unconditional failed-run bound.
    """
    from collection_capacity import array_allocation, transactions
    from production_schedule import PRODUCTION

    require(bool(rows), "empty workload")
    round_data(0, fragment)
    containers = []
    for number, row in enumerate(rows):
        n, g = row["teacher_positions"], row["greedy_positions_maximum"]
        require(type(n) is int and 0 < n <= 32768 and
                type(g) is int and 0 < g <= 32768, "invalid workload positions")
        for mode in MODES:
            precision = {"w4a16": 0, "bf16": 1, "fp16": 2}[mode]
            for kind, positions in (("teacher", n), ("greedy", g)):
                count = transactions(PRODUCTION, precision, positions)
                for repeat in range(2):
                    bound = trace_bound(count + 1)
                    containers.append({
                        "case": number, "mode": mode, "workload": kind, "repeat": repeat,
                        "positions": positions, "scheduled_records": count,
                        "one_failed_append_allowance": 1, **bound,
                        "rounded_data_bytes": round_data(bound["logical_bytes_bound"], fragment),
                    })
    arrays = array_allocation(rows, fragment)
    n = sum(row["teacher_positions"] for row in rows)
    g = sum(row["greedy_positions_maximum"] for row in rows)
    cases = len(rows)
    # Counts below are independently derived from producer/consumer namespaces.
    array_inodes = 8 * cases + 256 * n + 12 * g
    aliases = 150 * n
    require(array_inodes == arrays["unique_array_payload_file_inodes_one_attempt"] and
            aliases == arrays["hard_link_alias_pathnames_one_attempt"],
            "independent raw-array namespace accounting differs")
    trace_bytes = sum(item["logical_bytes_bound"] for item in containers)
    rounded = sum(item["rounded_data_bytes"] for item in containers)
    known_files = 77 * cases + 256 * n + 12 * g
    directories = 31 * cases + 19 * n + 6 * g
    root_files = 8 + 2 * (3 + cases + len(containers)) + len(containers) + 2
    namespace = {
        "array_payload_inodes": array_inodes,
        "hard_link_alias_pathnames_not_additional_file_inodes": aliases,
        "trace_payload_inodes": len(containers),
        "known_case_file_inodes_including_payload_and_support": known_files,
        "known_case_file_pathnames_including_aliases": known_files + aliases,
        "known_case_directory_inodes": directories,
        "known_collection_root_files_excluding_build_and_receipt_staging": root_files,
        "known_collection_root_directories_excluding_build": 2,
    }
    return {
        "purpose": "source-backed-raw-gzip-schedule-envelope-accounting",
        "zlib_source": {
            "version": ZLIB_VERSION, "commit": ZLIB_COMMIT,
            "git_blob_sha1": ZLIB_BLOBS,
            "base_url": f"https://github.com/madler/zlib/blob/{ZLIB_COMMIT}/",
            "linked_binary_source_and_build_options_attested": False,
        },
        "cases": cases, "modes": list(MODES), "repeats": 2, "workloads": 2,
        "teacher_positions": n, "greedy_positions_maximum": g,
        "trace_containers_one_attempt": len(containers),
        "trace_containers_success_plus_one_retained_failure": 2 * len(containers),
        "containers": containers, "fragment_bytes": fragment,
        "trace_logical_bound_one_schedule_envelope": trace_bytes,
        "trace_rounded_data_budget_one_schedule_envelope": rounded,
        "trace_rounded_data_budget_success_plus_one_failed_schedule_envelope": 2 * rounded,
        "array_rounded_data_budget_success_plus_one_failed_schedule_envelope":
            2 * arrays["rounded_array_data_bytes_one_successful_attempt"],
        "array_and_trace_rounded_data_budget_two_schedule_envelopes":
            2 * (rounded + arrays["rounded_array_data_bytes_one_successful_attempt"]),
        "namespace_one_successful_schedule_envelope": namespace,
        "namespace_success_plus_one_failed_schedule_envelope":
            {key: 2 * value for key, value in namespace.items()},
        "staging": {
            "trace_duplicate_payload_files": 0, "trace_spool_files": 0,
            "array_serialization_duplicate_payload_files": 0,
            "reference_layer_copy_temporary_on_disk": 0,
            "concurrent_gzip_writers": 1,
            "gzip_input_and_output_buffer_bytes_not_disk": 3 * 8192,
            "live_atomic_receipt_temporary_files_success_path": 1,
            "live_atomic_receipt_temporary_inodes_two_attempt_budget": 2,
            "receipt_old_and_new_serialization_coexist": True,
            "partial_final_payloads_already_charged_to_attempt_envelope": True,
            "retained_failed_receipt_temporary_count_bound": None,
            "build_products_and_compiler_temporary_count_bound": None,
            "ancillary_and_receipt_staging_bytes_bound": None,
        },
        "failure_policy": {
            "one_full_additional_schedule_envelope_charged": True,
            "gzclose_on_exception_and_explicit_close_charged": True,
            "partial_write_never_subtracted_or_reclaimed": True,
            "failed_attempt_record_envelope_enforced_by_current_collector": False,
            "unconditional_failed_attempt_trace_bound_bytes": None,
            "reason": "A finite schedule bounds expected completions, not arbitrary erroneous "
                      "DUT traffic. production_sim.cpp has no enforced trace-record ceiling. "
                      "Periodic stdout can also grow while a DUT stalls without new records.",
        },
        "unresolved": {
            "filesystem_inode_directory_extent_and_allocation_overhead_bytes": None,
            "json_indexes_events_stdout_stderr_receipts_and_hash_inventory_bytes": None,
            "build_snapshots_executable_compiler_and_linker_staging_bytes": None,
            "tables_rope_tokens_and_other_checks_native_gate_artifacts_bytes": None,
            "failed_receipt_publication_staging_bytes_and_inodes": None,
            "whole_process_memory_bound_bytes": None,
            "complete_filesystem_storage_bound_bytes": None,
        },
        "compression_ratio_assumed": False, "filesystem_allocation_bound": False,
        "full_workload_storage_qualified": False, "reserved_bytes": 0,
        "collection_launched": False, "packed_collection_enabled": False,
    }
