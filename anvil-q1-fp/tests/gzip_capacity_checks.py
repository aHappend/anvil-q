#!/usr/bin/env python3
"""Focused gzip accounting assertions. Requires independent admission before execution."""

import argparse
import gzip
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import artifact_path, load_json, require, sha
from gzip_capacity import round_data, trace_bound, workload
from verify import Evidence, ROOT


def reject(call, label):
    try:
        call()
    except ValueError:
        return label
    raise ValueError("insensitive assertion: " + label)


def validate(report):
    require(report["trace_containers_one_attempt"] == 12 * report["cases"],
            "container coverage omitted")
    require(report["trace_containers_success_plus_one_retained_failure"] ==
            2 * report["trace_containers_one_attempt"], "retained failure omitted")
    items = report["containers"]
    require(len(items) == report["trace_containers_one_attempt"], "missing containers")
    require(len({(item["case"], item["mode"], item["workload"], item["repeat"])
                 for item in items}) == len(items), "aliased repeats")
    for item in items:
        require(item["writes_charged"] == item["scheduled_records"] + 1,
                "failed append allowance missing")
        raw = 44 * item["writes_charged"]
        require(item["input_bytes_charged"] == raw and
                item["nonempty_blocks_bytes"] == 5 * raw and
                item["productive_sync_flush_bytes"] == 32 * (item["writes_charged"] + 1)
                and item["finish_and_failure_cleanup_bytes"] == 64 and
                item["gzip_header_and_trailer_bytes"] == 18, "bound components differ")
        require(item["logical_bytes_bound"] == 252 * item["writes_charged"] + 114,
                "gzip framing/flush/finish bound differs")
        require(item["rounded_data_bytes"] == round_data(
            item["logical_bytes_bound"], report["fragment_bytes"]), "rounding differs")
    require(report["trace_logical_bound_one_schedule_envelope"] ==
            sum(item["logical_bytes_bound"] for item in items), "trace total differs")
    require(report["trace_rounded_data_budget_one_schedule_envelope"] ==
            sum(item["rounded_data_bytes"] for item in items), "rounded trace total differs")
    require(report["trace_rounded_data_budget_success_plus_one_failed_schedule_envelope"] ==
            2 * report["trace_rounded_data_budget_one_schedule_envelope"], "failure bytes omitted")
    cases, n, g = (report[key] for key in
                   ("cases", "teacher_positions", "greedy_positions_maximum"))
    namespace = report["namespace_one_successful_schedule_envelope"]
    expected = {
        "array_payload_inodes": 8*cases + 256*n + 12*g,
        "hard_link_alias_pathnames_not_additional_file_inodes": 150*n,
        "trace_payload_inodes": 12*cases,
        "known_case_file_inodes_including_payload_and_support": 77*cases + 256*n + 12*g,
        "known_case_file_pathnames_including_aliases": 77*cases + 406*n + 12*g,
        "known_case_directory_inodes": 31*cases + 19*n + 6*g,
        "known_collection_root_files_excluding_build_and_receipt_staging":
            8 + 2*(3 + cases + 12*cases) + 12*cases + 2,
        "known_collection_root_directories_excluding_build": 2,
    }
    require(namespace == expected, "file/inode/alias/directory accounting differs")
    require(report["namespace_success_plus_one_failed_schedule_envelope"] ==
            {key: 2*value for key, value in expected.items()}, "failed namespace omitted")
    require(report["staging"]["live_atomic_receipt_temporary_files_success_path"] == 1
            and report["staging"]["live_atomic_receipt_temporary_inodes_two_attempt_budget"] == 2
            and report["staging"]["trace_spool_files"] == 0
            and report["staging"]["ancillary_and_receipt_staging_bytes_bound"] is None,
            "staging paths or unresolved staging changed")
    for key in ("compression_ratio_assumed", "filesystem_allocation_bound",
                "full_workload_storage_qualified", "collection_launched",
                "packed_collection_enabled"):
        require(report[key] is False, "overclaimed " + key)
    require(report["failure_policy"]["unconditional_failed_attempt_trace_bound_bytes"] is None
            and report["unresolved"]["complete_filesystem_storage_bound_bytes"] is None,
            "unresolved costs hidden")


def namespace_fixture(rows):
    """Enumerate named files/links/directories, independently of count formulas."""
    files, aliases, directories = set(), set(), set()

    def file(path):
        require(path not in files | aliases, "duplicate fixture filename")
        files.add(path)

    def directory(path):
        require(path not in directories, "duplicate fixture directory")
        directories.add(path)

    for number, row in enumerate(rows):
        base = f"case-{number}"
        n, g = row["teacher_positions"], row["greedy_positions_maximum"]
        directory(base)
        directory(base + "/references")
        file(base + "/reference-tokens.json")
        file(base + "/references/references.json")
        for mode in ("checkpoint", "bf16", "fp16", "w4a16"):
            source = base + "/references/" + mode
            directory(source)
            for kind in ("layers", "logits"):
                file(source + "/" + kind + ".f64")
            directory(source + "/position-views")
            file(source + "/position-views/positions.json")
            for position in range(n):
                view = source + f"/position-views/position-{position}"
                directory(view)
                for name in [*(f"layer-{i}.f64" for i in range(24)), "logits.f64"]:
                    file(view + "/" + name)
        for mode in ("bf16", "fp16", "w4a16"):
            file(base + "/" + mode + ".memory")
            for kind, positions in (("teacher", n), ("greedy", g)):
                for suffix in ("tokens", "rope"):
                    file(base + "/" + mode + "-" + kind + "." + suffix)
                for repeat in range(2):
                    run = base + f"/{mode}-{kind}-repeat-{repeat}"
                    directory(run)
                    for name in ("transactions.u32.gz", "events.jsonl", "summary.json"):
                        file(run + "/" + name)
                    for position in range(positions):
                        output = run + f"/position-{position}"
                        directory(output)
                        for name in ("layers.f32", "logits.f32"):
                            file(output + "/" + name)
            comparison = base + "/" + mode + "-teacher-comparison"
            directory(comparison)
            file(comparison + "/positions.json")
            file(base + "/" + mode + "-greedy-comparison.json")
            for kind in ("selected-reference", "checkpoint-reference"):
                directory(comparison + "/" + kind)
                file(comparison + "/" + kind + "/positions.json")
                for position in range(n):
                    view = comparison + "/" + kind + f"/position-{position}"
                    directory(view)
                    for name in [*(f"layer-{i}.f64" for i in range(24)), "logits.f64"]:
                        aliases.add(view + "/" + name)
            for position in range(n):
                view = comparison + f"/position-{position}"
                directory(view)
                for repeat in range(2):
                    for layer in range(24):
                        file(view + f"/repeat-{repeat}-layer-{layer}.f32")
    return {"files": len(files), "aliases": len(aliases), "directories": len(directories)}


def mathematics():
    from copy import deepcopy
    # RFC 1951 fixed Huffman tokens: literal <=9 bits, length+distance
    # <=31 bits; length three uses <=7+5+13=25 bits, hence <=9/input byte.
    for length in range(3, 259):
        require((25 if length == 3 else 31) <= 9*length, "fixed match token bound")
    for size in range(1, 65537):
        require((9*size + 10 + 7)//8 + 2 <= 5*size,
                "nonempty block bound including prior bit alignment")
    for writes in (0, 1, 185, 186, 187, 2**32-1, 2**32, 2**64):
        require(trace_bound(writes)["logical_bytes_bound"] == 252*writes + 114,
                "integer gzip bound boundary")
    for size in (0, 1, 4095, 4096, 4097, 2**64):
        for block in (1, 512, 4096, 65536):
            rounded = round_data(size, block)
            require(rounded >= size and rounded % block == 0 and
                    rounded - size < block, "fragment boundary")
    rejected = [reject(lambda: trace_bound(-1), "negative writes"),
                reject(lambda: trace_bound(True), "boolean writes"),
                reject(lambda: trace_bound(1, "1.2.13"), "unreviewed zlib"),
                reject(lambda: round_data(1, 0), "zero fragment")]
    rows = [{"teacher_positions": 1, "greedy_positions_maximum": 1},
            {"teacher_positions": 3, "greedy_positions_maximum": 5}]
    report = workload(rows, 4096)
    validate(report)
    counts = namespace_fixture(rows)
    namespace = report["namespace_one_successful_schedule_envelope"]
    require(counts == {
        "files": namespace["known_case_file_inodes_including_payload_and_support"],
        "aliases": namespace["hard_link_alias_pathnames_not_additional_file_inodes"],
        "directories": namespace["known_case_directory_inodes"]}, "namespace fixture differs")
    for name in ("retained-failure", "missing-mode", "shared-repeat", "raw-as-gzip",
                 "flush-omitted", "round-down", "failed-append", "capacity-claim",
                 "alias-omitted", "alias-as-inode", "directory-omitted",
                 "failed-namespace-omitted", "receipt-staging-omitted"):
        mutant = deepcopy(report)
        if name == "retained-failure":
            mutant["trace_containers_success_plus_one_retained_failure"] //= 2
        elif name == "missing-mode":
            mutant["containers"] = mutant["containers"][:-4]
        elif name == "shared-repeat":
            mutant["containers"][1]["repeat"] = 0
        elif name == "raw-as-gzip":
            mutant["containers"][0]["logical_bytes_bound"] = (
                mutant["containers"][0]["input_bytes_charged"])
        elif name == "flush-omitted":
            mutant["containers"][0]["logical_bytes_bound"] -= 32
        elif name == "round-down":
            mutant["containers"][0]["rounded_data_bytes"] -= 4096
        elif name == "failed-append":
            mutant["containers"][0]["writes_charged"] -= 1
        elif name == "capacity-claim":
            mutant["full_workload_storage_qualified"] = True
        elif name == "alias-omitted":
            mutant["namespace_one_successful_schedule_envelope"][
                "hard_link_alias_pathnames_not_additional_file_inodes"] = 0
        elif name == "alias-as-inode":
            mutant["namespace_one_successful_schedule_envelope"]["array_payload_inodes"] += 150
        elif name == "directory-omitted":
            mutant["namespace_one_successful_schedule_envelope"]["known_case_directory_inodes"] -= 1
        elif name == "failed-namespace-omitted":
            mutant["namespace_success_plus_one_failed_schedule_envelope"] = (
                mutant["namespace_one_successful_schedule_envelope"])
        else:
            mutant["staging"]["live_atomic_receipt_temporary_files_success_path"] = 0
        rejected.append(reject(lambda: validate(mutant), name))
    return {"boundary_assertions": 256 + 65536 + 8 + 6*4, "namespace": counts,
            "rejected_mutants_and_invalid_inputs": rejected}


def frozen_rows(ev):
    suite_path = ROOT / "tests/data/benchmark_manifest.json"
    suite = load_json(suite_path)
    ev.receipt.setdefault("data_sha256", {})["tests/data/benchmark_manifest.json"] = sha(suite_path)
    require(len(suite["domains"]) == 5, "not five domains")
    rows = []
    for domain in suite["domains"].values():
        require(len(domain["cases"]) == 10, "not ten cases per domain")
        for case in domain["cases"]:
            lengths = {}
            for key in ("teacher_tokens", "prompt_tokens"):
                item = case[key]
                path = artifact_path(ROOT, item["path"])
                require(path.is_file() and sha(path) == item["sha256"], "changed token input")
                tokens = load_json(path)
                require(isinstance(tokens, list) and tokens and
                        all(type(token) is int and 0 <= token < 151936 for token in tokens),
                        "invalid token input")
                lengths[key] = len(tokens)
                ev.receipt["data_sha256"][item["path"]] = sha(path)
            rows.append({"teacher_positions": lengths["teacher_tokens"],
                         "greedy_positions_maximum": lengths["prompt_tokens"] + 127})
    require(len(rows) == 50, "not complete fifty-case workload")
    return rows


def fixture_check(directory, report):
    require(report["header_version"] == report["linked_version"] == "1.3",
            "fixture zlib source family differs")
    cases = report["cases"]
    require(len(cases) == 24 and len({case["file"] for case in cases}) == 24,
            "fixture coverage missing")
    require({(case["records"], case["flush_each"], case["exception_cleanup"])
             for case in cases} ==
            {(count, flush, cleanup) for count in (0, 1, 185, 186, 187, 8192)
             for flush in (False, True) for cleanup in (False, True)},
            "fixture boundary/flush/cleanup cross missing")
    compared = 0
    for case in cases:
        path = directory / case["file"]
        require(path.parent == directory and path.is_file(), "fixture path escaped")
        count = case["records"]
        require(path.stat().st_size == case["encoded_bytes"] <=
                trace_bound(count)["logical_bytes_bound"], "encoded bytes exceed bound")
        with gzip.open(path, "rb") as stream:
            for i in range(count):
                expected = struct.pack("<11I", 2*i+1, 0, 2*i+2, 0,
                                       0, 8, 0, 0, i, 0, i*2654435761 & 0xffffffff)
                require(stream.read(44) == expected, "trace bytes/order differ")
                compared += 1
            require(stream.read(1) == b"", "trace has unexpected extra records")
    return compared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--math-worker", action="store_true")
    args = parser.parse_args()
    if args.math_worker:
        print(json.dumps(mathematics(), indent=2))
        return 0
    ev = Evidence("gzip-capacity")
    ok = False
    try:
        ev.receipt["tool_versions"] = {"python": sys.version}
        require(ev.run("mathematical-boundaries", [
            sys.executable, "tests/gzip_capacity_checks.py", "--math-worker"]),
            "mathematical boundary/sensitivity assertions failed")
        math = load_json(ev.path / "mathematical-boundaries.stdout")
        ev.assertion("mathematical_boundaries_and_negative_sensitivity", True, **math)
        require(ev.run("cxx-version", ["c++", "--version"]), "C++ compiler unavailable")
        executable = ev.path / "gzip-fixture"
        require(ev.run("compile-writer-fixture", [
            "c++", "-std=c++17", "-O2", "tests/gzip_capacity_fixture.cpp",
            "-lz", "-o", str(executable.relative_to(ROOT))]), "writer fixture compile failed")
        directory = ev.path / "containers"
        require(ev.run("writer-fixture", [str(executable.relative_to(ROOT)),
                                         str(directory.relative_to(ROOT))]),
                "writer/flush/exception-cleanup fixture failed")
        result = load_json(ev.path / "writer-fixture.stdout")
        compared = fixture_check(directory, result)
        ev.assertion("actual_legacy_writer_roundtrip_and_exception_cleanup", True,
                     containers=24, compared_records=compared, zlib=result["linked_version"],
                     compile_flags=result["compile_flags"],
                     io_error_or_process_kill_injected=False)
        # A diagnostic budget needs an explicit fragment assumption, not a
        # claimed filesystem guarantee. No free-space observation authorizes collection.
        report = workload(frozen_rows(ev), 4096)
        validate(report)
        require(report["trace_containers_one_attempt"] == 600, "full-suite container count")
        require(sum(item["scheduled_records"] * 44 for item in report["containers"]) ==
                4278003500187648, "frozen full-workload decoded trace volume changed")
        ev.receipt["assessment"] = report
        ev.assertion("complete_schedule_envelope_accounted_not_capacity_qualified", True,
                     trace_containers=600, attempts_charged=2,
                     storage_qualified=False, reserved_bytes=0, collection_launched=False)
        for label in ("mathematical-boundaries", "writer-fixture"):
            require((ev.path / (label + ".stderr")).stat().st_size == 0,
                    label + " emitted stderr")
        ok = True
    except (ValueError, KeyError, OSError, ImportError, EOFError, struct.error) as error:
        ev.assertion("gzip_capacity_diagnostic_exception", False, diagnostic=repr(error))
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path) for path in ev.path.rglob("*")
            if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                      "full_workload_storage_qualified": False}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
