#!/usr/bin/env python3
"""Bounded no-inference/no-RTL tests for the proposed packed evidence format."""

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import random
import struct
import sys
import subprocess
import time
import zlib

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import Validator, artifact_path, load_json, require, sha
from packed_storage import (CHUNK_BYTES, END, ENTRY, FOOTER, HEADER_LIMIT, MAGIC,
                            RECORD, Reader, Writer, array_bytes, array_descriptor,
                            bound, delta_decode,
                            delta_encode, dimensions, pack_array, take_varint,
                            transactions, varint)
from verify import Evidence, ROOT, now


def direct_producers(destination, report, reject):
    """Run the exact observer storage classes, independently of any RTL build."""
    import io
    import ast
    import shutil
    from types import SimpleNamespace
    from unittest.mock import patch
    from collection_capacity import packed_workload_accounting
    from packed_storage import array_output, observation_vector
    from packed_stream import write_stream

    directory = destination / "direct-producers"
    directory.mkdir()
    parsed = ("tests/production_sim.py", "tests/teacher_reference.py",
              "tests/reference_collector.py", "tests/production_resume.py",
              "tests/packed_storage.py", "tests/packed_stream.py",
              "tests/collection_capacity.py", "tests/packed_storage_checks.py")
    for name in parsed:
        ast.parse((ROOT / name).read_text(), filename=name)
    from production_sim import run_collection, storage_preflight
    try:
        run_collection(None, SimpleNamespace(packed_storage=True))
    except ValueError as error:
        require("collection paused pending independent capacity" in str(error),
                "packed collection failed for the wrong prerequisite")
    else:
        raise ValueError("unqualified packed production collection was not blocked")
    require("numpy" not in sys.modules and "teacher_reference" not in sys.modules,
            "paused packed collector imported inference dependencies")
    report["positive_cases"].append({
        "name": "producer-source-syntax-and-collection-pause",
        "python_sources_parsed": list(parsed),
        "packed_collection_rejected_before_inference_import": True})
    suite = {"domains": {
        str(domain): {"cases": [
            {"id": str(case), "teacher_tokens": {}, "prompt_tokens": {}}
            for case in range(10)]} for domain in range(5)}}
    for packed in (False, True):
        for sufficient in (False, True):
            assertions = []
            def assertion(name, passed, **detail):
                assertions.append((name, passed, detail))
                return passed
            holder = SimpleNamespace(path=directory, receipt={}, assertion=assertion)
            args = SimpleNamespace(case_start=0, case_count=50, teacher_prefix=None,
                                   modes=["bf16", "fp16", "w4a16"], packed_storage=packed)
            stat = SimpleNamespace(f_frsize=4096, f_bavail=10**18 if sufficient else 0,
                                   f_favail=10**18)
            with patch("production_sim.checked", return_value="synthetic-tokens"), \
                    patch("production_sim.load_json", return_value=[1]), \
                    patch("production_sim.os.statvfs", return_value=stat):
                try:
                    selected = storage_preflight(holder, args, suite)
                except ValueError as error:
                    require(not sufficient, "sufficient array budget was rejected")
                    diagnostic = str(error)
                    require(("raw-fallback budget" in diagnostic and
                             "not a lower bound on actual encoded size" in diagnostic and
                             "need at least" not in diagnostic) if packed else
                            "need at least" in diagnostic,
                            "storage preflight conflates packed budget with actual minimum")
                else:
                    require(sufficient and len(selected) == 50,
                            "insufficient array budget was accepted")
            expected = ("collection_array_storage_fallback_budget" if packed else
                        "collection_array_storage_lower_bound")
            require(len(assertions) == 1 and assertions[0][:2] == (expected, sufficient)
                    and not holder.receipt["collection_storage_preflight"][
                        "full_workload_storage_qualified"],
                    "array preflight changed its guard or certified complete storage")
    report["positive_cases"].append({
        "name": "array-preflight-budget-not-capacity-qualification",
        "synthetic_cases": 50, "format_availability_comparisons": 4,
        "packed_fallback_not_reported_as_actual_minimum": True,
        "full_workload_capacity_qualified": False})
    commands = []
    report["producer_commands"] = commands
    bindings = {name: sha(ROOT / name) for name in (
        "tests/packed_producer_fixture.cpp", "tests/production_storage.hpp",
        "tests/packed_stream.hpp", "tests/packed_stream.py", "tests/packed_storage.py")}

    def run(label, argv, passed=True, data=None):
        stdout, stderr = directory / (label + ".stdout"), directory / (label + ".stderr")
        record = {"label": label, "argv": argv, "cwd": ".", "started_at": now(), "timeout_s": 3600,
                  "source_sha256": bindings, "stdout": str(stdout.relative_to(ROOT)),
                  "stderr": str(stderr.relative_to(ROOT))}
        commands.append(record)
        started = time.monotonic()
        try:
            with stdout.open("xb") as out, stderr.open("xb") as err:
                child = subprocess.run(argv, cwd=ROOT, input=data, stdout=out, stderr=err,
                                       timeout=3600, check=False)
            record.update(timed_out=False, exit_code=child.returncode)
        except subprocess.TimeoutExpired:
            record.update(timed_out=True, exit_code=None)
            raise
        finally:
            record.update(ended_at=now(), elapsed_s=time.monotonic()-started)
            with (directory / (label + ".command.json")).open("x") as output:
                json.dump(record, output, indent=2)
        require((child.returncode == 0) == passed, "unexpected producer command exit: " + label)
        return stdout, stderr

    require(shutil.which("c++") is not None, "synthetic packed producer requires existing c++")
    run("cxx-version", ["c++", "--version"])
    run("python-version", ["python3", "--version"])
    executable = directory / "producer"
    run("compile-storage-only", ["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "-Itests", "tests/packed_producer_fixture.cpp", "-lz", "-o",
        str(executable.relative_to(ROOT))])
    command = [str(executable.relative_to(ROOT))]
    specials = [0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x00800000, 0x3f800000,
                0xbf800000, 0x7f7fffff, 0x7f800000, 0xff800000, 0x7fc00017, 0x7f800001]
    repeats = []
    for repeat in range(2):
        packed = directory / ("packed-repeat-" + str(repeat))
        repeats.append(packed)
        legacy = directory / ("legacy-repeat-" + str(repeat))
        for storage, target in (("packed", packed), ("legacy", legacy)):
            run(f"produce-{storage}-{repeat}", [
                *command, "produce", str(target.relative_to(ROOT)), storage])
        for kind, width in (("layers", 24*896), ("logits", 151936)):
            expected = b"".join(struct.pack("<I", specials[i % len(specials)])
                                for i in range(width))
            require(b"".join(Reader(packed / (kind + ".aqp")).chunks()) == expected ==
                    (legacy / (kind + ".f32")).read_bytes(),
                    "direct C++ packed/legacy producer changed observed bits")
        expected_rows = []
        random_ = 17
        for i in range(30000):
            random_ ^= random_ << 13 & 0xffffffff
            random_ ^= random_ >> 17
            random_ ^= random_ << 5 & 0xffffffff
            cycle = (1 << 32) + i*9
            expected_rows.append((cycle & 0xffffffff, cycle >> 32, (cycle+3) & 0xffffffff,
                                  (cycle+3) >> 32, i % 2, i % 13, i % 24, i % 7, i,
                                  151935-i, random_ if i % 2 else random_ ^ 0xffffffff))
        require(list(transactions(packed / "transactions.aqp")) == expected_rows ==
                list(transactions(legacy / "transactions.u32.gz")),
                "direct C++ transaction producer changed cycles/order/fields/write payloads")
    require(not __import__("os").path.samefile(repeats[0] / "logits.aqp",
                                              repeats[1] / "logits.aqp"),
            "direct producer repeats share payloads")
    for operation in ("fragment", "empty"):
        target = directory / operation
        run(operation, [*command, operation, str(target.relative_to(ROOT)), "packed"])
        if operation == "empty":
            require(not (target / "layers.aqp").exists() and not (target / "logits.aqp").exists(),
                    "empty observation created a false complete vector")
        else:
            for kind, count in (("layers", 897), ("logits", 3)):
                reader = Reader(target / (kind + ".aqp"), dtype="<f4",
                                shape=[count], axes=["fragment"])
                require(b"".join(reader.chunks()) == b"".join(
                    struct.pack("<I", specials[i % len(specials)]) for i in range(count)),
                    "direct paused fragment lost bytes")
                reject("fragment-not-complete-" + kind, lambda kind=kind: observation_vector(
                    ROOT, target, kind))
    for operation, expected in (("overlong", "packed append length/overflow"),
                                ("codec-failure", "FileExistsError"),
                                ("badtransaction", "overlapping or out-of-order transaction")):
        target = directory / operation
        _, error = run(operation, [*command, operation, str(target.relative_to(ROOT)), "packed"],
                       passed=False)
        diagnostic = error.read_text()
        require(expected in diagnostic and "PACKED_" in diagnostic,
                "direct C++ producer swallowed a codec error or failed for another reason")
        if operation == "codec-failure":
            require((target / "layers.aqp").read_text() == "retained-occupied-output",
                    "direct producer overwrote an occupied output")
    overflow = directory / "overlong.aqp"
    reject("producer-overlong-vector", lambda: write_stream(
        io.BytesIO(bytes((24*896+1)*4)), overflow, "layers"))
    reject("producer-partial-float", lambda: write_stream(
        io.BytesIO(b"\x01"), directory / "partial.aqp", "logits"))
    reject("producer-partial-transaction", lambda: write_stream(
        io.BytesIO(bytes(43)), directory / "partial-trace.aqp", "transactions"))
    reject("producer-failed-seal-not-readable", lambda: Reader(overflow))
    for kind in ("layers", "logits"):
        damaged = directory / ("damaged-" + kind + ".aqp")
        shutil.copy2(repeats[0] / (kind + ".aqp"), damaged)
        reader = Reader(damaged)
        with damaged.open("r+b") as output:
            output.seek(reader.entries[0][0])
            value = output.read(1)[0]
            output.seek(reader.entries[0][0]); output.write(bytes([value ^ 1]))
        reject("direct-observation-corrupt-" + kind,
               lambda path=damaged: b"".join(Reader(path).chunks()))
    # Fresh direct FP64 producers exercise the same helper reference_case uses.
    # Values are finite and chosen by integer bit patterns, not DUT arithmetic.
    reference = directory / "references"
    reference.mkdir()
    reference_bits = (0, 1 << 63, 1, (1 << 63) | 1, 0x3ff0000000000000,
                      0xbff0000000000000, 0x0010000000000000)
    raws = {}
    for kind, shape, axes in (
        ("layers", [2, 24, 896], ["position", "layer", "component"]),
        ("logits", [151936, 2], ["vocabulary", "position"])):
        width = dimensions("<f8", shape, axes) // 8
        raw = b"".join(struct.pack("<Q", reference_bits[i % len(reference_bits)])
                       for i in range(width))
        raws[kind] = raw
        path, writer = array_output(reference, kind, "<f8", shape, axes, packed=True)
        with writer:
            for start in range(0, len(raw), 8192):
                writer.write(raw[start:start+8192])
        require(b"".join(Reader(path).chunks()) == raw and
                not (reference / (kind + ".f64")).exists(),
                "direct FP64 producer changed bytes or staged a raw file")
    response = directory / "reference-views.raw"
    run("cpp-reference-consumer", [*command, "reference", str(response.relative_to(ROOT)),
        str((reference / "layers.aqp").relative_to(ROOT)),
        str((reference / "logits.aqp").relative_to(ROOT))])
    golden = b"".join(
        raws["layers"][position*24*896*8:(position+1)*24*896*8] +
        b"".join(raws["logits"][(v*2+position)*8:(v*2+position+1)*8]
                 for v in range(151936)) for position in range(2))
    require(response.read_bytes() == golden, "C++ FP64 reference views changed bits/axes")
    corrupt = directory / "corrupt-reference.aqp"
    shutil.copy2(reference / "layers.aqp", corrupt)
    first = Reader(corrupt).entries[0][0]
    with corrupt.open("r+b") as output:
        output.seek(first)
        value = output.read(1)[0]
        output.seek(first); output.write(bytes([value ^ 1]))
    _, diagnostic = run("cpp-corrupt-reference", [
        *command, "reference", str((directory / "rejected-views.raw").relative_to(ROOT)),
        str(corrupt.relative_to(ROOT)), str((reference / "logits.aqp").relative_to(ROOT))],
        passed=False)
    require("damaged/truncated packed payload" in diagnostic.read_text() and
            "PACKED_PIPE_READ" in diagnostic.read_text(),
            "corrupt reference failed for an unrelated reason")
    reject("producer-occupied-reference", lambda: array_output(
        reference, "layers", "<f8", [2, 24, 896], ["position", "layer", "component"],
        packed=True), errors=(FileExistsError,))
    rows = [{"teacher_positions": i % 3 + 1, "prompt_positions": 1,
             "greedy_positions_maximum": i % 5 + 2}
            for i in range(50)]
    accounting = packed_workload_accounting(rows, 4096)
    require(accounting["cases"] == 50 and accounting["repeats"] == 2 and
            accounting["bounded_data_blocks_success_plus_one_retained_failure"] ==
            2 * accounting["bounded_data_blocks_one_successful_attempt"] and
            accounting["complete_capacity_bound_bytes"] is None and
            accounting["trace_data_block_bound_one_attempt"] > 0 and
            all(item["bound_bytes"] is None for item in accounting["additional_costs"].values())
            and not accounting["full_workload_storage_qualified"] and
            not accounting["collection_resumption_authorized"],
            "whole-workload accounting omitted failure/trace/unbounded costs")
    report["positive_cases"].append({
        "name": "direct-python-cpp-producer-consumers", "independent_producer_repeats": 2,
        "transactions_compared_per_repeat": 30000, "reference_view_bytes": len(golden),
        "raw_production_staging_bytes": 0, "cpp_build_contains_rtl": False,
        "synthetic_complete_capacity_accounting": accounting})


def trace_index_floors(destination, report, reject):
    """Check index floors against actual sealed bytes and enumerated schedules."""
    from architecture import CONFIGURATIONS
    from collection_capacity import packed_trace_index_floor
    from production_schedule import schedule

    per_chunk = CHUNK_BYTES // RECORD.size
    boundaries = (0, 1, per_chunk - 1, per_chunk, per_chunk + 1, 2 * per_chunk)
    for count in boundaries:
        path = destination / ("index-floor-" + str(count) + ".aqp")
        with Writer(path, transactions=True) as output:
            for start in range(0, count, 4096):
                output.append(b"".join(
                    RECORD.pack(2*i+1, 0, 2*i+2, 0, 0, 8, 0, 0, i, 0, i)
                    for i in range(start, min(start + 4096, count))))
        raw = path.read_bytes()
        offset, entries, total, _, _ = FOOTER.unpack(raw[-FOOTER.size:])
        expected = (count + per_chunk - 1) // per_chunk
        require(entries == expected and total == count * RECORD.size and
                len(raw) - FOOTER.size - offset == expected * ENTRY.size and
                len(raw) >= expected * ENTRY.size and
                len(Reader(path).entries) == expected,
                "compression-independent index floor differs from sealed bytes")
    comparisons = 0
    for config in CONFIGURATIONS.values():
        rows = [{"teacher_positions": config[-1], "prompt_positions": 1}]
        for modes in (("bf16",), ("fp16", "w4a16"), ("bf16", "fp16", "w4a16")):
            result = packed_trace_index_floor(rows, modes, config)
            counts = [
                sum(1 for _ in schedule(config, {"w4a16": 0, "bf16": 1, "fp16": 2}[mode],
                                       [index % config[-2] for index in range(positions)]))
                for mode in modes for positions in (config[-1], 1)]
            expected_entries = 2 * sum((value + per_chunk - 1) // per_chunk
                                       for value in counts)
            require(result["mandatory_transaction_records"] == 2 * sum(counts) and
                    result["mandatory_index_entries"] == expected_entries and
                    result["minimum_logical_index_bytes_one_successful_attempt"] ==
                    expected_entries * ENTRY.size and
                    result["largest_mandatory_container_index_bytes"] ==
                    max((value + per_chunk - 1) // per_chunk for value in counts) * ENTRY.size
                    and not result["collection_resumption_authorized"],
                    "mandatory index floor differs from enumerated architectural workload")
            comparisons += 1
    for name, row in (
        ("boolean-prompt", {"teacher_positions": 1, "prompt_positions": True}),
        ("zero-prompt", {"teacher_positions": 1, "prompt_positions": 0}),
        ("prompt-after-teacher", {"teacher_positions": 1, "prompt_positions": 2}),
    ):
        reject("index-floor-" + name, lambda row=row: packed_trace_index_floor([row]))
    reject("index-floor-duplicate-modes", lambda: packed_trace_index_floor(
        [{"teacher_positions": 1, "prompt_positions": 1}], ("bf16", "bf16")))
    report["positive_cases"].append({
        "name": "compression-independent-mandatory-trace-index-floor",
        "sealed_container_boundary_comparisons": len(boundaries),
        "enumerated_workload_comparisons": comparisons,
        "production_model_executed": False, "collection_resumption_authorized": False})


def integrated(destination, report, reject):
    """Exercise production consumers with synthetic full-width arrays, not inference."""
    import os
    import shutil
    from unittest.mock import patch
    from packed_storage import ArraySource
    from collection_capacity import packed_array_allocation
    from production_checkpoint import trace_rows
    from production_schedule import audit_rows, binary_rows, schedule
    from production_sim import compare_greedy, compare_teacher
    from production_trace import replay
    from production_resume import audit as audit_prefix, exact_fragments
    from reference_collector import collect
    from retention_inventory import selftest as retention_selftest
    from transaction_retention import inspect_trace

    directory = destination / "integrated"
    directory.mkdir()
    retention_selftest(directory / "legacy-retention-regressions")
    capacity_comparisons = 0
    for modes in (1, 2, 3):
        for block in (1, 4096):
            rows = [{"teacher_positions": 1, "greedy_positions_maximum": 0},
                    {"teacher_positions": 3, "greedy_positions_maximum": 5}]
            sizes = []
            for row in rows:
                for _ in range(modes + 1):
                    sizes.extend((row["teacher_positions"] * 24 * 896 * 8,
                                  row["teacher_positions"] * 151936 * 8))
                for _ in range(modes):
                    for _ in range(2):
                        for workload in ("teacher_positions", "greedy_positions_maximum"):
                            for _ in range(row[workload]):
                                sizes.extend((24 * 896 * 4, 151936 * 4))
            expected = sum((bound(size) + block - 1) // block * block for size in sizes)
            actual = packed_array_allocation(rows, block, modes)
            require(actual["rounded_array_raw_fallback_bound_one_successful_attempt"] == expected
                    and actual["array_payload_inodes_one_successful_attempt"] == len(sizes)
                    and actual["rounded_array_raw_fallback_bound_success_plus_one_retained_failure"]
                    == 2 * expected and not actual["full_workload_storage_qualified"],
                    "prospective complete-array bound differs from enumerated containers")
            capacity_comparisons += 1
    report["positive_cases"].append({"name": "prospective-packed-array-bound",
                                     "enumerated_layout_comparisons": capacity_comparisons,
                                     "full_workload_capacity_qualified": False})
    positions = 2
    values = (0., -0., 2.0 ** -149, -(2.0 ** -149), 1., -2., 3.)
    layer_values = [values[index % len(values)] for index in range(24 * 896)]
    logit_values = [values[index % len(values)] for index in range(151936)]
    logit_values[17] = 4.
    references = {}
    for mode in ("checkpoint", "bf16", "fp16", "w4a16"):
        source = directory / "references" / mode
        source.mkdir(parents=True)
        references[mode] = {}
        for kind, data, shape, axes in (
                ("layers", layer_values * positions, [positions, 24, 896],
                 ["position", "layer", "component"]),
                ("logits", [value for value in logit_values for _ in range(positions)],
                 [151936, positions], ["vocabulary", "position"])):
            path = source / (kind + ".aqp")
            with Writer(path, dtype="<f8", shape=shape, axes=axes) as writer:
                writer.append(struct.pack("<" + "d" * len(data), *data))
            references[mode][kind] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}
        before = {path.name: sha(path) for path in source.iterdir()}
        for consumer in range(2):
            output = directory / (mode + "-consumer-" + str(consumer))
            rows = collect(source, output, positions, shared=source / "position-views")
            require(len(rows) == positions and len(list(output.rglob("*"))) == 1,
                    "packed collector materialized duplicate payloads")
            for position, row in enumerate(rows):
                for layer, item in enumerate(row["layers"]):
                    raw = array_bytes(ROOT / item["fp64_output"]["path"],
                                      item["fp64_output"], "<f8", 896)
                    require(raw == struct.pack("<896d", *layer_values[layer*896:(layer+1)*896]),
                            "integrated packed layer offsets/bits differ")
                item = row["fp64_logits"]
                require(array_bytes(ROOT / item["path"], item, "<f8", 151936) ==
                        struct.pack("<151936d", *logit_values),
                        "integrated vocabulary-major position offsets/bits differ")
            reject(mode + "-occupied-collector", lambda: collect(source, output, positions),
                   errors=(FileExistsError,))
        require(before == {path.name: sha(path) for path in source.iterdir()},
                "collecting views changed immutable reference sources")
        reject(mode + "-collector-wrong-count", lambda: collect(
            source, directory / (mode + "-wrong-count"), 1))
    invalid = directory / "wrong-reference-axes"
    invalid.mkdir()
    with Writer(invalid / "layers.aqp", dtype="<f8", shape=[positions, 24, 896],
                axes=["position", "component", "layer"]) as writer:
        writer.append(struct.pack("<" + "d" * (positions * len(layer_values)),
                                  *(layer_values * positions)))
    os.link(source / "logits.aqp", invalid / "logits.aqp")
    reject("integrated-collector-wrong-axes", lambda: collect(
        invalid, directory / "wrong-axes-consumer", positions))
    changing = directory / "changed-view-source.aqp"
    shutil.copy2(source / "layers.aqp", changing)
    verified = ArraySource(ROOT, changing, dtype="<f8", shape=[positions, 24, 896],
                           axes=["position", "layer", "component"])
    with changing.open("r+b") as stream:
        stream.seek(-1, 2)
        stream.write(b"\xff")
    reject("changed-source-after-index-verification", verified.descriptor)

    class Observations:
        receipt = {}

        def assertion(self, name, passed, **details):
            require(passed, "integrated assertion failed: " + name)
            return passed

    for mode in ("bf16", "fp16", "w4a16"):
        runs = []
        for repeat in range(2):
            run = directory / f"{mode}-repeat-{repeat}"
            runs.append(run)
            for position in range(positions):
                target = run / f"position-{position}"
                target.mkdir(parents=True)
                for kind, data, shape, axes in (
                        ("layers", layer_values, [24, 896], ["layer", "component"]),
                        ("logits", logit_values, [151936], ["vocabulary"])):
                    with Writer(target / (kind + ".aqp"), dtype="<f4",
                                shape=shape, axes=axes) as writer:
                        writer.append(struct.pack("<" + "f" * len(data), *data))
            with (run / "summary.json").open("x") as stream:
                json.dump({"generated_tokens": [17], "positions_completed": positions}, stream)
        compare_teacher(Observations(), "synthetic-integrated", mode, runs, references,
                        positions, directory / (mode + "-teacher"), synthetic=True)
        compare_greedy(Observations(), "synthetic-integrated", mode, runs, [53, 89],
                       directory / (mode + "-greedy.json"), [17])
        events = runs[0] / "events.jsonl"
        with events.open("x") as output:
            for position in range(positions):
                for layer in range(24):
                    output.write(json.dumps({"event": "layer", "position": position,
                                             "layer": layer, "cycle": 100+position*24+layer})
                                 + "\n")
        artifacts = [{"path": str(path.relative_to(ROOT)), "sha256": sha(path)}
                     for path in [events, *(runs[0] / f"position-{position}" / "layers.aqp"
                                            for position in range(positions))]]
        head = {"binding": {"workload": "teacher", "mode": mode,
                           "arguments": ["-"]*8 + [
                               references[mode]["layers"]["path"],
                               references[mode]["logits"]["path"], str(positions)]},
                "artifacts": artifacts}
        observer = Observations()
        observer.path = directory / (mode + "-synthetic-prefix-audit")
        observer.path.mkdir()

        def ancestry(ev, item, chain):
            chain.append(head)
            return head

        # Ancestry admission is deliberately mocked; only storage-consumer
        # numerical/shape assertions are exercised, never a genuine checkpoint.
        with patch("production_resume.validate_segment", side_effect=ancestry):
            audit_prefix(observer, {"synthetic": True})
        require(load_json(observer.path / "layer-prefix-comparisons.json")["layers"] and
                bytes(exact_fragments([runs[0]], "layers.f32", 0)) ==
                struct.pack("<" + "f"*len(layer_values), *layer_values),
                "packed prefix audit/fragment consumer failed")
        require(not list((directory / (mode + "-teacher")).rglob("*.f32")),
                "packed teacher comparison duplicated observation layers")
        reject(mode + "-repeat-run-alias", lambda: compare_greedy(
            Observations(), "synthetic-integrated", mode, [runs[0], runs[0]], [53, 89],
            directory / (mode + "-alias.json"), [17]))
        alias = directory / (mode + "-hard-linked-repeat")
        shutil.copytree(runs[0], alias, copy_function=os.link)
        reject(mode + "-repeat-payload-alias", lambda: compare_greedy(
            Observations(), "synthetic-integrated", mode, [runs[0], alias], [53, 89],
            directory / (mode + "-payload-alias.json"), [17]))
        mutant = directory / (mode + "-damaged-repeat")
        shutil.copytree(runs[1], mutant)
        damaged = mutant / "position-0/logits.aqp"
        with damaged.open("r+b") as stream:
            stream.seek(12 + struct.unpack("<I", stream.read(12)[8:])[0])
            byte = stream.read(1)
            stream.seek(-1, 1)
            stream.write(bytes([byte[0] ^ 1]))
        reject(mode + "-integrated-teacher-damaged-payload", lambda: compare_teacher(
            Observations(), "synthetic-integrated", mode, [runs[0], mutant], references,
            positions, directory / (mode + "-damaged-teacher"), synthetic=True))
        reject(mode + "-integrated-greedy-damaged-payload", lambda: compare_greedy(
            Observations(), "synthetic-integrated", mode, [runs[0], mutant], [53, 89],
            directory / (mode + "-damaged-greedy.json"), [17]))
        report["positive_cases"].append({
            "name": "production-packed-comparison-call-sites", "mode": mode,
            "synthetic_positions": positions, "separately_written_repeats": 2,
            "layer_comparisons": positions * 24, "logit_comparisons": positions,
            "synthetic_prefix_audit_comparisons": positions * 24,
            "inference_executed": False, "rtl_executed": False})

    # Keep mathematical reference code out of this standard-library-only probe.
    require("numpy" not in sys.modules and "teacher_reference" not in sys.modules,
            "bounded storage integration imported inference dependencies")
    config = (1, 8, 8, 1, 1, 8, 1, 1, 1)
    for mode in range(3):
        expected = list(schedule(config, mode, [0]))
        records = [RECORD.pack(10 + 3*i, 0, 11 + 3*i, 0, *item[:6], i)
                   for i, item in enumerate(expected)]
        raw = b"".join(records)
        packed = directory / f"schedule-{mode}.aqp"
        with Writer(packed, transactions=True) as writer:
            writer.append(raw)
        legacy = directory / f"schedule-{mode}.gz"
        with legacy.open("xb") as stream:
            stream.write(gzip.compress(raw, mtime=0))
        require(list(trace_rows(packed)) == list(trace_rows(legacy)),
                "checkpoint packed/legacy transaction reader differs")
        for path in (packed, legacy):
            result = audit_rows(binary_rows(path), iter(expected), False)
            require(result["transactions_compared"] == len(records) and
                    result["complete_memory_schedule"], "integrated schedule audit incomplete")
            observed = inspect_trace(path, directory / (path.name + "-inspection.json"))
            require(observed["decompressed_sha256"] == hashlib.sha256(raw).hexdigest(),
                    "integrated trace retention changed decoded bits/order/cycles")
        report["positive_cases"].append({"name": "packed-legacy-transaction-consumers",
                                         "mode": mode, "records": len(records)})

    class SyntheticTensor:
        def read(self, *coordinates):
            return 0x3f80

    rows = [(1, 0, 2, 0, 0, 0, 0, 0, 17, 0, 0x3f80),
            (4, 0, 5, 0, 1, 8, 0, 0, 0, 0, 0x3f800000),
            (7, 0, 8, 0, 0, 8, 0, 0, 0, 0, 0x3f800000)]
    with patch("production_trace.StreamOracle", lambda mode: SyntheticTensor()):
        raw = b"".join(RECORD.pack(*row) for row in rows)
        packed = directory / "replay.aqp"
        with Writer(packed, transactions=True) as writer:
            writer.append(raw)
        replay(packed, "bf16", directory / "replay-pristine.json")
        changed = list(rows)
        changed[1] = (*rows[1][:-1], 0x40000000)
        damaged = directory / "replay-wrong-write.aqp"
        with Writer(damaged, transactions=True) as writer:
            writer.append(b"".join(RECORD.pack(*row) for row in changed))
        reject("integrated-public-replay-write-payload", lambda: replay(
            damaged, "bf16", directory / "replay-damaged.json"))
    report["positive_cases"].append({"name": "unchanged-public-memory-replay",
                                     "synthetic_tensor_oracle": True, "records": len(rows)})


def checkpoint_fragments(destination, report, reject):
    """Synthetic segment packing only; no checkpoint execution or result assembly."""
    from production_checkpoint import packed_fragments

    directory = destination / "checkpoint-fragments"
    directory.mkdir()
    words = (0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x00800000,
             0x3f800000, 0x7f800000, 0x7f800001, 0x7fc01234)
    expected = {
        kind: b"".join(struct.pack("<I", words[index % len(words)])
                       for index in range(count))
        for kind, count in (("layers", 24 * 896), ("logits", 151936))}
    segments = []
    records = []
    event_bytes = b""
    for number in range(2):
        source = directory / f"segment-{number}"
        source.mkdir()
        artifacts = []

        def artifact(path):
            artifacts.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path)})

        raw = RECORD.pack(1 + 3 * number, 1, 2 + 3 * number, 1,
                          number, 8, 0, 0, 0, number, 0xffffffff - number)
        records.append(raw)
        trace = source / ("transactions.u32.gz" if number == 0 else "transactions.aqp")
        if number == 0:
            with trace.open("xb") as stream:
                stream.write(gzip.compress(raw, mtime=0))
        else:
            with Writer(trace, transactions=True) as stream:
                stream.append(raw)
        artifact(trace)
        events = source / "events.jsonl"
        line = (json.dumps({"segment": number, "cycle": (1 << 32) + 2 + 3 * number})
                + "\n").encode()
        events.write_bytes(line)
        event_bytes += line
        artifact(events)
        for position in range(2):
            target = source / f"position-{position}"
            target.mkdir()
            for kind, raw in expected.items():
                split = (17 if kind == "layers" else 65537) * 4
                raw = raw[:split] if number == 0 else raw[split:]
                path = target / (kind + (".f32" if number == 0 else ".aqp"))
                if number == 0:
                    with path.open("xb") as stream:
                        stream.write(raw)
                else:
                    with Writer(path, dtype="<f4", shape=[len(raw) // 4],
                                axes=["fragment"]) as stream:
                        stream.append(raw)
                artifact(path)
        summary = source / "summary.json"
        if number == 1:
            with summary.open("x") as stream:
                json.dump({"positions_completed": 2, "cycles": (1 << 32) + 10}, stream)
            artifact(summary)
        segments.append({"status": "paused" if number == 0 else "completed",
                         "summary": None if number == 0 else
                         {"path": str(summary.relative_to(ROOT)), "sha256": sha(summary)},
                         "artifacts": artifacts})
    chain = list(reversed(segments))
    before = {item["path"]: sha(ROOT / item["path"])
              for segment in segments for item in segment["artifacts"]}
    output = directory / "packed"
    output.mkdir()
    require(packed_fragments(chain, output) == 2, "checkpoint event count differs")
    require(b"".join(Reader(output / "transactions.aqp").chunks()) == b"".join(records) and
            (output / "events.jsonl").read_bytes() == event_bytes,
            "checkpoint trace fields/order/cycles or event bytes changed")
    for position in range(2):
        for kind, raw in expected.items():
            path = output / f"position-{position}" / (kind + ".aqp")
            require(b"".join(Reader(path).chunks()) == raw,
                    "checkpoint fragment concatenation changed floating-point bits")
            shape, axes = ([24, 896], ["layer", "component"]) if kind == "layers" else (
                [151936], ["vocabulary"])
            Reader(path, dtype="<f4", shape=shape, axes=axes)
    require(not list(output.rglob("*.f32")) and not list(output.rglob("*.gz")),
            "packed assembly materialized raw staging outputs")
    require(before == {path: sha(ROOT / path) for path in before},
            "packed assembly changed immutable input fragments")
    reject("checkpoint-occupied-output", lambda: packed_fragments(chain, output),
           errors=(FileExistsError,))

    def mutant(label, change):
        changed = copy.deepcopy(chain)
        change(changed)
        target = directory / label
        target.mkdir()
        reject("checkpoint-" + label, lambda: packed_fragments(changed, target))

    mutant("segment-order", lambda rows: rows.reverse())
    mutant("duplicate-vector", lambda rows: rows[0]["artifacts"].append(
        next(item for item in rows[0]["artifacts"] if item["path"].endswith("layers.aqp"))))
    mutant("missing-vector", lambda rows: rows[0].update(artifacts=[
        item for item in rows[0]["artifacts"]
        if not item["path"].endswith("position-1/layers.aqp")]))
    mutant("missing-trace", lambda rows: rows[0].update(artifacts=[
        item for item in rows[0]["artifacts"]
        if not item["path"].endswith("transactions.aqp")]))
    mutant("duplicate-trace", lambda rows: rows[0]["artifacts"].append(
        next(item for item in rows[0]["artifacts"]
             if item["path"].endswith("transactions.aqp"))))

    def replace(rows, suffix, path):
        for item in rows[0]["artifacts"]:
            if item["path"].endswith(suffix):
                item.update(path=str(path.relative_to(ROOT)), sha256=sha(path))

    broken = directory / "truncated" / "position-0" / "layers.f32"
    broken.parent.mkdir(parents=True)
    broken.write_bytes(b"\x00")
    mutant("partial-float", lambda rows: replace(rows, "position-0/layers.aqp", broken))
    wrong = directory / "wrong-axes" / "position-0" / "layers.aqp"
    wrong.parent.mkdir(parents=True)
    with Writer(wrong, dtype="<f4", shape=[1], axes=["wrong-axis"]) as stream:
        stream.append(b"\x00" * 4)
    mutant("wrong-fragment-axes", lambda rows: replace(
        rows, "position-0/layers.aqp", wrong))
    damaged = directory / "damaged" / "position-0" / "layers.aqp"
    damaged.parent.mkdir(parents=True)
    original = ROOT / next(item["path"] for item in chain[0]["artifacts"]
                           if item["path"].endswith("position-0/layers.aqp"))
    raw = bytearray(original.read_bytes())
    raw[12 + struct.unpack("<I", raw[8:12])[0]] ^= 1
    damaged.write_bytes(raw)
    mutant("damaged-packed-fragment", lambda rows: replace(
        rows, "position-0/layers.aqp", damaged))
    for label, raw in (("partial-event", b'{"cycle":1}'),
                       ("duplicate-event-key", b'{"cycle":1,"cycle":2}\n'),
                       ("nonfinite-event", b'{"cycle":NaN}\n'),
                       ("nonobject-event", b"[]\n")):
        path = directory / label / "events.jsonl"
        path.parent.mkdir()
        path.write_bytes(raw)
        mutant(label + "-rejection", lambda rows, path=path: replace(
            rows, "/events.jsonl", path))
    paused = directory / "paused"
    paused.mkdir()
    require(packed_fragments([segments[0]], paused) == 1 and
            not (paused / "summary.json").exists(), "partial assembly claimed completion")
    for kind, raw in expected.items():
        path = paused / "position-0" / (kind + ".aqp")
        reader = Reader(path)
        require(reader.header["axes"] == ["fragment"] and
                b"".join(reader.chunks()) == raw[:(17 if kind == "layers" else 65537) * 4],
                "partial fragment shape/bits changed")
    empty_trace = directory / "empty-trace" / "transactions.aqp"
    empty_trace.parent.mkdir()
    with Writer(empty_trace, transactions=True):
        pass
    require(list(transactions(empty_trace)) == [] and
            empty_trace.stat().st_size <= bound(0, transactions=True),
            "empty transaction witness did not preserve its zero count")
    reject("checkpoint-incomplete-array", lambda: Writer(
        directory / "incomplete-array.aqp", dtype="<f4", shape=[1], axes=["element"]).close())
    no_observations = copy.deepcopy(segments[0])
    no_observations["artifacts"] = [
        item for item in no_observations["artifacts"]
        if Path(item["path"]).name in ("events.jsonl", "transactions.u32.gz")]
    for item in no_observations["artifacts"]:
        if item["path"].endswith("transactions.u32.gz"):
            item.update(path=str(empty_trace.relative_to(ROOT)), sha256=sha(empty_trace))
    empty_output = directory / "paused-before-first-response"
    empty_output.mkdir()
    require(packed_fragments([no_observations], empty_output) == 1 and
            list(transactions(empty_output / "transactions.aqp")) == [] and
            not list(empty_output.glob("position-*")) and
            not (empty_output / "summary.json").exists(),
            "pre-response partial assembly fabricated observations or completion")
    report["positive_cases"].append({
        "name": "synthetic-packed-checkpoint-fragments", "segments": 2, "positions": 2,
        "vectors_compared": 4, "transaction_records_compared": 2,
        "legacy_and_packed_inputs": True, "raw_staging_copies": 0,
        "original_inputs_unchanged": True, "partial_completion_claimed": False,
        "rtl_executed": False, "genuine_checkpoint_assembled": False})


def worker(destination):
    destination.mkdir(parents=True, exist_ok=False)
    report = {"schema": 1, "acceptance_evidence": False,
              "scope": "synthetic codec only; no RTL, inference, collection or result assembly",
              "positive_cases": [], "rejections": []}

    def reject(name, function, errors=(ValueError,)):
        try:
            function()
        except errors as error:
            report["rejections"].append({"name": name, "diagnostic": str(error)})
        else:
            raise ValueError("packed storage defect was not rejected: " + name)

    def put(name, data):
        path = destination / name
        with path.open("xb") as stream:
            stream.write(data)
        return path

    def decoded(path):
        return b"".join(Reader(path).chunks())

    # Bit patterns, not float conversions: include both zeros, denormals,
    # infinities and multiple signaling/quiet NaN payloads in both widths.
    patterns = {
        "<f4": (0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x00800000,
                0x3f800000, 0x7f7fffff, 0x7f800000, 0xff800000, 0x7f800001,
                0x7fc01234, 0xffc04321),
        "<f8": (0, 0x8000000000000000, 1, 0x8000000000000001, 0xfffffffffffff,
                0x10000000000000, 0x3ff0000000000000, 0x7fefffffffffffff,
                0x7ff0000000000000, 0xfff0000000000000, 0x7ff0000000000001,
                0x7ff8123456789abc, 0xfff823456789abcd),
    }
    rng = random.Random(17)
    for dtype, words in patterns.items():
        width = 8 if dtype == "<f8" else 4
        raw = b"".join(word.to_bytes(width, "little") for word in words)
        source = put(dtype[1:] + "-bits.raw", raw)
        path = destination / (dtype[1:] + "-bits.aqp")
        pack_array(source, path, dtype, [len(words)], ["element"])
        require(decoded(path) == raw and Reader(path).read(0, len(raw)) == raw,
                "floating-point payload bits changed")
        report["positive_cases"].append({"name": dtype + "-special-bits",
                                         "compared_bytes": len(raw)})

    # Independently construct a C-order 3D array with unique per-coordinate words.
    # Distinct extents catch axis swaps. Include cross-chunk and strided reads.
    shape, axes = [3, 5, 12001], ["position", "layer", "component"]
    raw = b"".join(struct.pack("<Q", (p << 48) | (layer << 32) | component)
                   for p in range(shape[0]) for layer in range(shape[1])
                   for component in range(shape[2]))
    source = put("coordinate-array.raw", raw)
    path = destination / "coordinate-array.aqp"
    pack_array(source, path, "<f8", shape, axes)
    reader = Reader(path, dtype="<f8", shape=shape, axes=axes)
    require(decoded(path) == raw, "complete 3D raw offset traversal differs")
    for origin, extent, steps in (
            ([0, 0, 0], [3, 5, 12001], [1, 1, 1]),
            ([1, 2, 11997], [2, 2, 2], [1, 2, 2]),
            ([0, 1, 130], [2, 3, 100], [2, 1, 19]),
            ([2, 4, 12000], [1, 1, 1], [1, 1, 1])):
        expected = b"".join(struct.pack("<Q", (p << 48) | (layer << 32) | component)
                            for p in range(origin[0], origin[0] + extent[0] * steps[0], steps[0])
                            for layer in range(origin[1], origin[1] + extent[1] * steps[1], steps[1])
                            for component in range(origin[2], origin[2] + extent[2] * steps[2], steps[2]))
        actual = reader.view(origin, extent, steps)
        require(actual == expected, "strided 3D coordinate view differs")
        report["positive_cases"].append({"name": "3D-view", "origin": origin,
                                         "shape": extent, "steps": steps,
                                         "compared_bytes": len(actual)})
    offset = CHUNK_BYTES - 16
    require(reader.read(offset, 64) == raw[offset:offset + 64], "cross-chunk read differs")
    reject("wrong-axis-order", lambda: Reader(path, dtype="<f8", shape=shape,
                                              axes=["layer", "position", "component"]))
    reject("wrong-shape", lambda: Reader(path, dtype="<f8", shape=[5, 3, 12001], axes=axes))
    for name, origin, extent, steps in (
            ("negative-origin", [-1, 0, 0], [1, 1, 1], None),
            ("end-overflow", [2, 4, 12000], [1, 1, 2], None),
            ("boolean-origin", [True, 0, 0], [1, 1, 1], None),
            ("stride-overflow", [0, 0, 0], [2, 1, 1], [3, 1, 1]),
            ("zero-stride", [0, 0, 0], [1, 1, 1], [0, 1, 1]),
            ("wrong-rank", [0], [1], None)):
        reject(name, lambda origin=origin, extent=extent, steps=steps:
               reader.view(origin, extent, steps))
    for name, offset_, length in (("unaligned-offset", 1, 8), ("unaligned-count", 0, 1),
                                  ("read-overrun", len(raw), 8), ("negative-count", 0, -8)):
        reject(name, lambda offset_=offset_, length=length: reader.read(offset_, length))

    # Vocabulary-major logits: extracting one position must stride over positions,
    # not reinterpret the flat payload as position-major.
    raw_logits = b"".join(struct.pack("<Q", v * 13 + p)
                          for v in range(10007) for p in range(13))
    logits = destination / "vocabulary-major.aqp"
    with Writer(logits, dtype="<f8", shape=[10007, 13],
                axes=["vocabulary", "position"]) as output:
        output.append(raw_logits)
    for position in (0, 5, 12):
        observed = Reader(logits).view([0, position], [10007, 1])
        expected = b"".join(struct.pack("<Q", v * 13 + position) for v in range(10007))
        require(observed == expected, "vocabulary-major position offsets differ")
        report["positive_cases"].append({"name": "vocabulary-position-view",
                                         "position": position, "compared_bytes": len(observed)})

    # Incompressible raw fallback must never exceed the proven format bound.
    for number, count in enumerate((4, CHUNK_BYTES, CHUNK_BYTES + 12)):
        raw_noise = rng.randbytes(count)
        noise = destination / f"noise-{number}.aqp"
        with Writer(noise, dtype="<f4", shape=[count // 4], axes=["word"]) as output:
            for start in range(0, count, 32768):
                output.append(raw_noise[start:start + 32768])
        require(decoded(noise) == raw_noise and noise.stat().st_size <= bound(count) and
                any(entry[3] == 0 for entry in Reader(noise).entries),
                "raw fallback/bound differs")
        report["positive_cases"].append({"name": "raw-fallback-bound", "raw_bytes": count,
                                         "actual_bytes": noise.stat().st_size, "bound": bound(count)})

    # Complete independent repeats remain independently written payload files.
    repeats = []
    for repeat in range(2):
        repeat_path = destination / f"independent-repeat-{repeat}.aqp"
        with Writer(repeat_path, dtype="<f8", shape=[len(patterns["<f8"])],
                    axes=["element"]) as output:
            output.append((destination / "f8-bits.raw").read_bytes())
        repeats.append(repeat_path)
    require(repeats[0].stat().st_ino != repeats[1].stat().st_ino and
            decoded(repeats[0]) == decoded(repeats[1]), "independent repeat was aliased")
    reject("exclusive-output", lambda: Writer(repeats[0], dtype="<f8", shape=[1], axes=["x"]),
           errors=(FileExistsError,))
    reject("dimension-overflow", lambda: dimensions("<f8", [1 << 62], ["x"]))
    reject("boolean-dimension", lambda: dimensions("<f8", [True], ["x"]))
    reject("duplicate-axes", lambda: dimensions("<f8", [2, 2], ["x", "x"]))

    # Regenerate valid outer hashes for structural mutations so checks cannot
    # merely rely on one enclosing digest to reject malformed indices.
    pristine = path.read_bytes()
    prefix_size = 12 + struct.unpack("<I", pristine[8:12])[0]
    index_start, entry_count, total, _, _ = FOOTER.unpack(pristine[-FOOTER.size:])
    entries = [list(entry) for entry in ENTRY.iter_unpack(pristine[index_start:-FOOTER.size])]

    def index_mutant(name, mutate):
        changed = copy.deepcopy(entries)
        mutate(changed)
        index = b"".join(ENTRY.pack(*entry) for entry in changed)
        payload = pristine[:index_start] + index + FOOTER.pack(
            index_start, entry_count, total,
            hashlib.sha256(pristine[:prefix_size] + index).digest(), END)
        mutant = put(name + ".aqp", payload)
        reject(name, lambda: decoded(mutant))

    index_mutant("overlapping-offset", lambda rows: rows[1].__setitem__(0, rows[0][0]))
    index_mutant("skipped-offset", lambda rows: rows[0].__setitem__(0, rows[0][0] + 1))
    index_mutant("reordered-index", lambda rows: rows.reverse())
    index_mutant("decoded-size", lambda rows: rows[0].__setitem__(2, rows[0][2] - 8))
    index_mutant("encoded-size-overflow", lambda rows: rows[0].__setitem__(1, (1 << 64) - 1))
    index_mutant("wrong-codec", lambda rows: rows[0].__setitem__(3, 255))
    index_mutant("raw-hash", lambda rows: rows[0].__setitem__(5, b"\x00" * 32))
    for name, mutant in (
            ("truncated-magic", pristine[:7]),
            ("truncated-header", pristine[:prefix_size - 1]),
            ("truncated-payload", pristine[:index_start - 1]),
            ("truncated-index", pristine[:-FOOTER.size - 1]),
            ("truncated-footer", pristine[:-1]),
            ("appended-junk", pristine + b"x"),
            ("version", b"AQPACK99" + pristine[8:]),
            ("bad-header", pristine[:13] + bytes([pristine[13] ^ 1]) + pristine[14:]),
            ("bad-index-hash", pristine[:-40] + bytes([pristine[-40] ^ 1]) + pristine[-39:])):
        damaged = put(name + ".aqp", mutant)
        reject(name, lambda damaged=damaged: decoded(damaged))
    payload_damage = bytearray(pristine)
    payload_damage[prefix_size] ^= 1
    damaged = put("damaged-payload.aqp", payload_damage)
    reject("payload-bit-flip", lambda: decoded(damaged))

    # Construct records independently, exercising every u32 field and both halves
    # of 64-bit cycles. Alternating fields exercise negative and positive deltas.
    record_rows = []
    cycle = (1 << 32) - 5
    for index in range(CHUNK_BYTES // 44 + 17):
        accepted = cycle + index % 7
        completed = accepted + 1 + index % 11
        fields = (index % 2, (0xffffffff if index % 2 else 0), index % 24,
                  index % 7, index * 7919 & 0xffffffff,
                  (0xffffffff - index * 17) & 0xffffffff, rng.getrandbits(32))
        record_rows.append((accepted & 0xffffffff, accepted >> 32,
                            completed & 0xffffffff, completed >> 32, *fields))
        cycle = completed
    record_rows.append((0xfffffffe, 0xffffffff, 0xffffffff, 0xffffffff,
                        1, 0, 0, 0, 0, 0, 0xffffffff))
    records = b"".join(RECORD.pack(*row) for row in record_rows)
    trace = destination / "transactions.aqp"
    with Writer(trace, transactions=True) as output:
        for start in range(0, len(records), 44 * 37):
            output.append(records[start:start + 44 * 37])
    require(list(transactions(trace)) == record_rows and decoded(trace) == records and
            trace.stat().st_size <= bound(len(records), transactions=True),
            "transaction fields/order/cycles changed")
    legacy = put("transactions.u32.gz", gzip.compress(records, mtime=0))
    require(list(transactions(legacy)) == record_rows, "backward gzip reader differs")
    report["positive_cases"].append({"name": "trace-lossless-and-legacy",
                                     "records": len(record_rows), "decoded_bytes": len(records),
                                     "actual_bytes": trace.stat().st_size,
                                     "bound": bound(len(records), transactions=True)})

    first = RECORD.pack(*record_rows[0])
    second = RECORD.pack(*record_rows[1])
    for name, data in (("partial-record", first[:-1]), ("reordered-record", second + first),
                        ("duplicate-record", first + first),
                        ("invalid-write", RECORD.pack(*record_rows[0][:4], 2,
                                                     *record_rows[0][5:]))):
        reject(name, lambda data=data: delta_encode(data))
    for value in (0, 1, 127, 128, (1 << 32) - 1, (1 << 64) - 1):
        require(take_varint(varint(value), 0) == (value, len(varint(value))),
                "varint boundary differs")
    for name, data in (("varint-overflow", b"\xff" * 9 + b"\x02"),
                        ("varint-unterminated", b"\xff" * 10),
                        ("varint-truncated", b"\x80"),
                        ("varint-noncanonical", b"\x80\x00")):
        reject(name, lambda data=data: take_varint(data, 0))
    reject("encode-varint-overflow", lambda: varint(1 << 64))
    reject("delta-trailing-bytes", lambda: delta_decode(delta_encode(first) + b"x", 1))
    reject("delta-truncated-payload", lambda: delta_decode(delta_encode(first)[:-1], 1))
    cycle_overflow = varint((1 << 64) - 1) + varint(1) + b"\x00" * 6 + b"\x00" * 4
    reject("delta-cycle-overflow", lambda: delta_decode(cycle_overflow, 1))
    field_overflow = b"\x00\x01" + varint(1 << 33) + b"\x00" * 5 + b"\x00" * 4
    reject("delta-field-overflow", lambda: delta_decode(field_overflow, 1))
    bad_zlib = zlib.compress(delta_encode(first)) + b"x"
    from packed_storage import inflate
    reject("compressed-trailing-stream", lambda: inflate(bad_zlib, 54))
    reject("compressed-expansion", lambda: inflate(zlib.compress(b"x" * 1024), 54))

    class Inputs:
        def __init__(self):
            self.receipt = {}

    validator = Validator(ROOT, Inputs())
    actual_path = destination / "validator-actual.aqp"
    reference_path = destination / "validator-reference.aqp"
    repeat_path = destination / "validator-repeat.aqp"
    for selected_path, dtype in ((actual_path, "<f4"), (repeat_path, "<f4"),
                                 (reference_path, "<f8")):
        encoding = "f" if dtype == "<f4" else "d"
        with Writer(selected_path, dtype=dtype, shape=[2, 3],
                    axes=["position", "component"]) as output:
            output.append(struct.pack("<6" + encoding, 1., -2., 3., 1., -2., -3.))
    actual = array_descriptor(ROOT, actual_path, origin=[0, 0], shape=[1, 3])
    repeated = array_descriptor(ROOT, repeat_path, origin=[0, 0], shape=[1, 3])
    reference = array_descriptor(ROOT, reference_path, origin=[0, 0], shape=[1, 3])
    validator.arrays(actual, reference, repeated, 3, (.9999, .002), "packed-pristine")
    flat_actual = put("validator-legacy.f32", struct.pack("<3f", 1., -2., 3.))
    flat_reference = put("validator-legacy.f64", struct.pack("<3d", 1., -2., 3.))
    legacy_actual = {"path": str(flat_actual.relative_to(ROOT)), "sha256": sha(flat_actual)}
    legacy_reference = {"path": str(flat_reference.relative_to(ROOT)), "sha256": sha(flat_reference)}
    validator.arrays(legacy_actual, reference, repeated, 3, (.9999, .002), "mixed-formats")
    validator.arrays(actual, legacy_reference, legacy_actual, 3, (.9999, .002), "legacy-reference")
    changed_view = array_descriptor(ROOT, actual_path, origin=[1, 0], shape=[1, 3])
    reject("same-container-different-repeat-view", lambda: validator.arrays(
        actual, reference, changed_view, 3, (.9999, .002), "view-repeat-mutant"))
    reject("numerical-defect-packed-view", lambda: validator.arrays(
        changed_view, reference, changed_view, 3, (.9999, .002), "numerical-mutant"))
    for name, key, value in (
            ("descriptor-wrong-shape", "array_shape", [3, 2]),
            ("descriptor-wrong-axes", "axes", ["component", "position"]),
            ("descriptor-wrong-dtype", "dtype", "<f8"),
            ("descriptor-wrong-decoded-hash", "decoded_sha256", "0" * 64),
            ("descriptor-unknown-format", "format", "unknown"),
            ("descriptor-missing-index", "origin", None)):
        mutant = copy.deepcopy(actual)
        mutant["storage"][key] = value
        reject(name, lambda mutant=mutant: validator.array_bytes(mutant, "<f4", 3))
    reject("descriptor-width-overflow", lambda: array_bytes(actual_path, actual, "<f4", 6))
    changed_binding = copy.deepcopy(actual)
    changed_binding["sha256"] = "0" * 64
    reject("descriptor-outer-file-hash", lambda: validator.array_bytes(changed_binding, "<f4", 3))
    report["positive_cases"].append({"name": "unchanged-validator-numerics",
                                     "comparisons": 3, "minimum_cosine": .9999,
                                     "maximum_normalized_error": .002})

    # A complete read must check cycle ordering across chunk boundaries, not only
    # within each delta frame. Both chunks below have valid internal hashes.
    split = destination / "cross-chunk-order.aqp"
    with Writer(split, transactions=True) as output:
        output.append(records)
    split_bytes = split.read_bytes()
    start, count, total, _, _ = FOOTER.unpack(split_bytes[-FOOTER.size:])
    split_entries = [list(entry) for entry in ENTRY.iter_unpack(split_bytes[start:-FOOTER.size])]
    # Replace the second chunk's contents with valid earlier records of its size.
    count_raw = split_entries[1][2] // 44
    early = b"".join(RECORD.pack(*row) for row in record_rows[:count_raw])
    encoded = zlib.compress(delta_encode(early), 6)
    entry = split_entries[1]
    entry[1], entry[3], entry[4], entry[5] = len(encoded), 2, hashlib.sha256(encoded).digest(), hashlib.sha256(early).digest()
    prefix = split_bytes[:entry[0]] + encoded
    index = b"".join(ENTRY.pack(*row) for row in split_entries)
    footer = FOOTER.pack(len(prefix), count, total,
                         hashlib.sha256(split_bytes[:12 + struct.unpack("<I", split_bytes[8:12])[0]] +
                                        index).digest(), END)
    reordered = put("cross-chunk-reordered.aqp", prefix + index + footer)
    reject("cross-chunk-transaction-order", lambda: list(transactions(reordered)))
    integrated(destination, report, reject)
    checkpoint_fragments(destination, report, reject)
    direct_producers(destination, report, reject)
    trace_index_floors(destination, report, reject)
    report["tools"] = {"python": sys.version, "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION}
    report["full_workload_capacity_qualified"] = False
    report["direct_packed_producers_opt_in_implemented"] = True
    report["production_collection_enabled"] = False
    with (destination / "qualification.json").open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--repair-of", type=Path)
    parser.add_argument("--preceding-receipt", type=Path)
    args = parser.parse_args()
    if args.worker:
        require(args.destination is not None, "packed diagnostic destination missing")
        worker(artifact_path(ROOT, str(args.destination)))
        return 0
    require(args.destination is None, "destination is worker-only")
    ev = Evidence("packed-storage")
    passed = False
    try:
        ev.receipt["scope"] = "bounded codec diagnostics only; collection remains paused"
        ev.receipt["tool_versions"] = {"python": sys.version, "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION}
        if args.repair_of:
            previous = artifact_path(ROOT, str(args.repair_of))
            require(load_json(previous)["status"] == "failed", "repair link did not fail")
            ev.receipt["repair_of"] = {"path": str(args.repair_of), "sha256": sha(previous)}
        if args.preceding_receipt:
            previous = artifact_path(ROOT, str(args.preceding_receipt))
            load_json(previous)
            ev.receipt["preceding_diagnostic"] = {
                "path": str(args.preceding_receipt), "sha256": sha(previous)}
        passed = ev.run("codec-roundtrip-corruption", [
            sys.executable, "tests/packed_storage_checks.py", "--worker", "--destination",
            str((ev.path / "synthetic").relative_to(ROOT))], timeout=3600)
        ev.assertion("packed_codec_roundtrip_and_corruption", passed,
                     full_workload_capacity_qualified=False, collection_resumption_authorized=False)
        if passed:
            ev.receipt["qualification"] = load_json(ev.path / "synthetic/qualification.json")
            assessed = ev.run("complete-packed-capacity-assessment", [
                sys.executable, "tests/collection_capacity.py", "--worker"], timeout=3600)
            require(assessed, "complete capacity accounting diagnostic failed")
            assessment = load_json(ev.path / "complete-packed-capacity-assessment.stdout")
            ev.receipt["complete_packed_capacity"] = assessment[
                "direct_packed_complete_workload_accounting"]
            require(assessment["scope"]["cases"] == 50 and
                    assessment["scope"]["repeats"] == 2 and
                    assessment["scope"]["modes"] == ["bf16", "fp16", "w4a16"],
                    "capacity assessment omitted required workload")
            ev.assertion("full_workload_storage_accounted_not_qualified", True,
                         complete_capacity_bound_bytes=None,
                         full_workload_storage_qualified=False,
                         collection_resumption_authorized=False)
    except (ValueError, OSError, KeyError) as error:
        passed = False
        ev.assertion("packed_codec_diagnostic_exception", False, diagnostic=repr(error))
    finally:
        ev.receipt["outputs"] = {str(path.relative_to(ROOT)): sha(path)
                                 for path in ev.path.rglob("*")
                                 if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
