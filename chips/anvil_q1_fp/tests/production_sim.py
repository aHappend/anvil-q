#!/usr/bin/env python3
"""Collect real production RTL observations; never fabricate benchmark results.

Default selection is all fifty cases, three modes and two independent processes
for both teacher forcing and greedy generation. --teacher-prefix explicitly
collects an incomplete prefix, without changing RTL parameters or acceptance.
All outputs are advisory preparation, not tests/data/full_model_results.json.
"""

import argparse
import gzip
import json
import os
from pathlib import Path
import shutil
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import Validator, artifact_path, load_json, require, sha
from benchmark_inputs import write_json
from verify import Evidence, ROOT


MODES = {"bf16": 1, "fp16": 2, "w4a16": 0}
BUILD_SOURCES = ("tests/production_sim.cpp", "tests/packed_stream.hpp",
                 "tests/production_storage.hpp", "tests/packed_stream.py",
                 "tests/packed_storage.py", "tests/sparse_transactions.py")


def descriptor(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def identity():
    return {str(path.relative_to(ROOT)): sha(path) for path in
            [*sorted((ROOT / "rtl").glob("*.sv")),
             *(ROOT / name for name in BUILD_SOURCES)]}


def checked(ev, item):
    path = artifact_path(ROOT, item["path"])
    require(path.is_file() and sha(path) == item["sha256"],
            "missing or changed production input: " + item["path"])
    ev.receipt.setdefault("data_sha256", {})[item["path"]] = item["sha256"]
    return path


def memory_table(ev, model, mode, destination):
    """Map request coordinates to declared streams, not Cartesian dense memory."""
    from fp64_reference import PROJECTIONS
    stream = model["streams"][mode]
    layout = load_json(checked(ev, stream["layout"]))
    paths = {"weights": checked(ev, stream["weights"])}
    if mode == "w4a16":
        paths.update({key: checked(ev, stream[key]) for key in ("zeros", "scales")})
    rows = []
    seen = set()

    def add(kind, layer, projection, height, width, item, size, offset, transpose=False):
        key = (kind, layer, projection)
        require(key not in seen, "duplicate production memory binding")
        seen.add(key)
        path = str(paths[item].relative_to(ROOT))
        require(not any(character.isspace() for character in path),
                "whitespace in production memory-table path")
        require(offset + height * width * size <= paths[item].stat().st_size,
                "production memory binding exceeds stream")
        rows.append((kind, layer, projection, height, width, size, offset,
                     int(transpose), path))

    for name, item in sorted(layout["tensors"].items()):
        shape, offset = item["shape"], item["byte_offset"]
        layer = int(name.split(".")[2]) if name.startswith("model.layers.") else 0
        if name == "model.embed_tokens.weight":
            require(shape == [151936, 896], "wrong production embedding shape")
            add(0, 0, 0, *shape, "weights", 2, offset)
        elif name == "model.norm.weight":
            add(7, 0, 0, 1, 896, "weights", 2, offset)
        elif name.endswith("input_layernorm.weight"):
            add(5, layer, 0, 1, 896, "weights", 2, offset)
        elif name.endswith("post_attention_layernorm.weight"):
            add(6, layer, 0, 1, 896, "weights", 2, offset)
        else:
            projection = next((number for suffix, number in PROJECTIONS.items()
                               if name.endswith(suffix + ".weight") or
                               name.endswith(suffix + ".bias")), None)
            require(projection is not None, "unknown production tensor: " + name)
            if name.endswith(".bias"):
                add(4, layer, projection, 1, shape[0], "weights", 2, offset)
            elif mode == "w4a16":
                outputs, inputs = shape
                add(1, layer, projection, inputs, outputs // 8, "weights", 4, offset)
                add(2, layer, projection, inputs // 128, outputs // 8,
                    "zeros", 4, item["zero_offset"])
                add(3, layer, projection, inputs // 128, outputs,
                    "scales", 2, item["scale_offset"])
            else:
                add(12, layer, projection, shape[1], shape[0],
                    "weights", 2, offset, transpose=True)
    expected = 1 + 1 + 24 * (2 + 3 + (21 if mode == "w4a16" else 7))
    require(len(rows) == expected, "incomplete production tensor inventory")
    with destination.open("x") as output:
        for row in rows:
            output.write(" ".join(map(str, row)) + "\n")
    return destination


def prepare_rope(destination, positions, mode):
    # The declared Qwen split-half theta formula, evaluated independently in FP64.
    import numpy as np
    angles = np.arange(positions, dtype="<f8")[:, None] * (
        1000000.0 ** (-np.arange(32, dtype="<f8") / 32))
    values = np.stack((np.cos(angles), np.sin(angles)), axis=-1).reshape(positions, 64)
    require(np.isfinite(values).all(), "invalid independent RoPE coefficients")
    if mode == "w4a16":
        encoded = np.copysign(np.floor(np.abs(values) * 2**30 + .5), values).astype("<i4")
    else:
        encoded = values.astype("<f4")
    with destination.open("xb") as output:
        output.write(encoded.tobytes())
    return destination


def compile_simulator(ev, previous=None):
    require(ev.run("verilator-version", ["verilator", "--version"], timeout=30),
            "installed Verilator unavailable")
    require(ev.run("cxx-version", ["c++", "--version"], timeout=30),
            "installed C++ compiler unavailable")
    if previous:
        record = load_json(artifact_path(ROOT, str(previous)))
        require(record["build_sources"] == identity(), "retained simulator sources changed")
        require(any(row["label"] == "production-build" and row["exit_code"] == 0
                    for row in record["records"]), "retained production build failed")
        executable = checked(ev, record["executable"])
        ev.receipt["build_receipt"] = descriptor(ROOT / previous)
    else:
        directory = ev.path / "obj"
        # Absolute harness input is required by generated makefiles in their build
        # directory. The recorded command is reproducible after resolving this root.
        command = [
            "verilator", "--cc", "--exe", "--build", "--savable", "-j", "2", "-O3",
            "-Wno-fatal", "--top-module", "anvil_q1_fp_top",
            "--Mdir", str(directory.relative_to(ROOT)),
            "-CFLAGS", "-O3 -std=c++17", "-LDFLAGS", "-lz",
            *[str(path.relative_to(ROOT)) for path in sorted((ROOT / "rtl").glob("*.sv"))],
            str(ROOT / "tests/production_sim.cpp")]
        require(ev.run("production-build", command, timeout=14400),
                "production Verilator build failed")
        executable = directory / "Vanvil_q1_fp_top"
    ev.receipt["build_sources"] = identity()
    ev.receipt["executable"] = descriptor(executable)
    ev.finish("running")
    return executable


def compare_teacher(ev, key, mode, runs, references, positions, destination,
                    synthetic=False):
    """Use the existing independent validator and its unchanged per-case bounds."""
    from reference_collector import collect
    from packed_storage import observation_vector
    require(len(runs) == 2 and runs[0].resolve() != runs[1].resolve(),
            "teacher repeats must be separate observations")
    destination.mkdir()
    sources = {}
    for selected_mode in (mode, "checkpoint"):
        paths = [checked(ev, references[selected_mode][kind]) for kind in ("layers", "logits")]
        require(paths[0].parent == paths[1].parent, "reference arrays belong to different sources")
        sources[selected_mode] = paths[0].parent
    selected_source, checkpoint_source = sources[mode], sources["checkpoint"]
    selected = collect(
        selected_source, destination / "selected-reference", positions,
        shared=selected_source / "position-views")
    checkpoint = collect(
        checkpoint_source, destination / "checkpoint-reference", positions,
        shared=checkpoint_source / "position-views")
    validator = Validator(ROOT, ev)
    observed = []
    for position in range(positions):
        row = {"position": position, "layers": []}
        directory = destination / f"position-{position:05d}"
        directory.mkdir()
        for repeat, run in enumerate(runs):
            packed = run / f"position-{position}" / "layers.aqp"
            if packed.exists():
                # The per-layer descriptors below retain exact views, not copies.
                observation_vector(ROOT, packed.parent, "layers")
                continue
            aggregate = run / f"position-{position}" / "layers.f32"
            require(aggregate.stat().st_size == 24 * 896 * 4,
                    "incomplete observed production layers")
            with aggregate.open("rb") as source:
                for layer in range(24):
                    target = directory / f"repeat-{repeat}-layer-{layer:02d}.f32"
                    with target.open("xb") as output:
                        output.write(source.read(896 * 4))
        actual_logits, repeat_logits = [
            observation_vector(ROOT, run / f"position-{position}", "logits") for run in runs]
        require(not os.path.samefile(ROOT / actual_logits["path"], ROOT / repeat_logits["path"]),
                "teacher repeat payloads must be independently retained")
        threshold = (-1, float("inf")) if mode == "w4a16" else (.999, .01)
        validator.arrays(actual_logits, selected[position]["fp64_logits"],
                         repeat_logits, 151936, threshold, f"{key}/{mode}/{position}/logits")
        row.update(logits=actual_logits, repeat_logits=repeat_logits,
                   fp64_logits=selected[position]["fp64_logits"],
                   decoded_weight_logits=selected[position]["fp64_logits"],
                   checkpoint_fp64_logits=checkpoint[position]["fp64_logits"])
        for layer in range(24):
            actual, repeated = [
                observation_vector(ROOT, run / f"position-{position}", "layers", layer)
                if (run / f"position-{position}" / "layers.aqp").exists() else
                descriptor(directory / f"repeat-{repeat}-layer-{layer:02d}.f32")
                for repeat, run in enumerate(runs)]
            require(not os.path.samefile(ROOT / actual["path"], ROOT / repeated["path"]),
                    "teacher repeat payloads must be independently retained")
            reference = selected[position]["layers"][layer]["fp64_output"]
            threshold = (-1, float("inf")) if mode == "w4a16" else (.9999, .002)
            validator.arrays(actual, reference, repeated, 896, threshold,
                             f"{key}/{mode}/{position}/layer-{layer}")
            row["layers"].append({"layer": layer, "output": actual,
                                  "repeat_output": repeated, "fp64_output": reference})
        selected_logits = selected[position]["fp64_logits"]
        validator.arrays(selected_logits, checkpoint[position]["fp64_logits"],
                         selected_logits, 151936, (-1, float("inf")),
                         f"{key}/{mode}/{position}/storage-quantization", wide=True)
        observed.append(row)
    write_json(destination / "positions.json", {
        "case": key, "mode": mode, "positions": observed, "metrics": validator.metrics,
        "complete_benchmark": False, "acceptance_evidence": False})
    ev.assertion(("synthetic_" if synthetic else "") +
                 "teacher_repeat_and_independent_numerics_" + mode, True,
                 case=key, positions=positions, layer_comparisons=positions*24,
                 logit_comparisons=positions,
                 independent_processes=0 if synthetic else 2,
                 synthetic_observations=synthetic)


def compare_greedy(ev, key, mode, runs, prompt, destination, eos):
    from packed_storage import array_bytes, observation_vector
    require(len(runs) == 2 and runs[0].resolve() != runs[1].resolve(),
            "greedy repeats must be separate observations")
    first, repeated = [load_json(path / "summary.json") for path in runs]
    generated = first["generated_tokens"]
    require(generated == repeated["generated_tokens"] and 0 < len(generated) <= 128,
            "nondeterministic or incomplete production greedy output")
    from benchmark import greedy_stop
    stop = "eos" if generated[-1] in eos else "max_new_tokens"
    greedy_stop(generated, stop, eos)
    require(first["positions_completed"] == repeated["positions_completed"] ==
            len(prompt) + len(generated) - 1, "greedy input position count")
    for position in range(first["positions_completed"]):
        for kind in ("layers", "logits"):
            items = [observation_vector(ROOT, run / f"position-{position}", kind)
                     for run in runs]
            require(not os.path.samefile(*(ROOT / item["path"] for item in items)),
                    "greedy repeat payloads must be independently retained")
            width = 24 * 896 if kind == "layers" else 151936
            require(array_bytes(ROOT / items[0]["path"], items[0], "<f4", width) ==
                    array_bytes(ROOT / items[1]["path"], items[1], "<f4", width),
                    "nondeterministic greedy arrays")
    steps = []
    for index, token in enumerate(generated):
        position = len(prompt) + index - 1
        items = [observation_vector(ROOT, run / f"position-{position}", "logits")
                 for run in runs]
        values = struct.unpack("<151936f", array_bytes(
            ROOT / items[0]["path"], items[0], "<f4", 151936))
        import math
        require(all(math.isfinite(value) for value in values), "nonfinite greedy logits")
        require(max(range(151936), key=values.__getitem__) == token,
                "greedy output is not lowest-ID-tie argmax")
        steps.append({"context": prompt + generated[:index],
                      "logits": items[0], "repeat_logits": items[1]})
    write_json(destination, {
        "case": key, "mode": mode, "tokens": generated, "repeat_tokens": generated,
        "stop_reason": stop, "steps": steps, "complete_benchmark": False,
        "limitations": "Raw deterministic generation only; task decoding/evaluation and "
                        "benchmark execution-record/cycle assembly remain outstanding."})
    ev.assertion("greedy_independent_repeat_" + mode, True, case=key,
                 generated_tokens=len(generated), independent_processes=2)


def storage_preflight(ev, args, suite):
    """Reject an impossible array budget, never certify complete storage."""
    from collection_capacity import array_allocation, packed_array_allocation

    all_cases = [(domain + "/" + case["id"], case)
                 for domain, group in suite["domains"].items() for case in group["cases"]]
    require(len(all_cases) == 50, "frozen suite is not fifty cases")
    selected = all_cases[args.case_start:args.case_start + args.case_count]
    require(len(selected) == args.case_count, "case selection exceeds frozen suite")
    rows = []
    for _, case in selected:
        teacher = load_json(checked(ev, case["teacher_tokens"]))
        prompt = load_json(checked(ev, case["prompt_tokens"]))
        require(teacher and prompt and all(type(x) is int and 0 <= x < 151936
                                          for x in teacher + prompt), "invalid token IDs")
        n = len(teacher) if args.teacher_prefix is None else min(
            len(teacher), args.teacher_prefix)
        g = len(prompt) + 127 if args.teacher_prefix is None else 0
        require(n <= 32768 and g <= 32768, "collection exceeds legal sequence depth")
        rows.append({"teacher_positions": n, "greedy_positions_maximum": g})
    stat = os.statvfs(ev.path)
    packed = getattr(args, "packed_storage", False)
    allocation = (packed_array_allocation if packed else array_allocation)(
        rows, stat.f_frsize, modes=len(args.modes))
    # Include one additional retained failed attempt. Packed raw fallback is
    # a conservative budget, not a lower bound on actual encoded size.
    required_bytes = 2 * allocation[
        "rounded_array_raw_fallback_bound_one_successful_attempt" if packed else
        "rounded_array_data_bytes_one_successful_attempt"]
    required_inodes = 2 * allocation[
        "array_payload_inodes_one_successful_attempt" if packed else
        "unique_array_payload_file_inodes_one_attempt"]
    available_bytes = stat.f_bavail * stat.f_frsize
    report = {
        "cases": len(selected), "modes": list(args.modes), "packed_storage": packed,
        "teacher_prefix": args.teacher_prefix, "array_allocation": allocation,
        "required_array_bytes_with_one_retained_failure": required_bytes,
        "required_array_inodes_with_one_retained_failure": required_inodes,
        "available_bytes": available_bytes, "available_inodes": stat.f_favail,
        "reserved_bytes": 0, "full_workload_storage_qualified": False,
        "limitation": "Array-only budget check (raw fallback upper bound when packed), "
                      "not a reservation, encoded-size prediction or complete "
                      "trace/metadata/log/staging capacity qualification.",
    }
    ev.receipt["collection_storage_preflight"] = report
    enough = available_bytes >= required_bytes and stat.f_favail >= required_inodes
    assertion = ("collection_array_storage_fallback_budget" if packed else
                 "collection_array_storage_lower_bound")
    requirement = (f"raw-fallback budget {required_bytes} bytes and {required_inodes} inodes"
                   if packed else
                   f"need at least {required_bytes} bytes and {required_inodes} inodes")
    require(ev.assertion(assertion, enough, **report),
            "insufficient collection array storage before RTL build/inference: "
            f"{requirement} "
            f"including one retained failure; available {available_bytes} bytes and "
            f"{stat.f_favail} inodes; trace/metadata/log/staging capacity is additional" +
            ("; packed budget is not a lower bound on actual encoded size" if packed else ""))
    return selected


def run_collection(ev, args):
    # Storage diagnostics do not grant collection authority. Keep the opt-in
    # path fail-closed until separately reviewed capacity/environment recovery.
    require(not getattr(args, "packed_storage", False),
            "packed production collection paused pending independent capacity "
            "qualification and shared-runtime environment repair")
    from teacher_reference import validate_inputs
    model, suite, _, config = validate_inputs(ev)
    selected = None
    if not (args.build_only or args.qualify_trace or args.qualify_comparisons):
        selected = storage_preflight(ev, args, suite)
    if args.qualify_comparisons:
        import numpy as np
        first_case = next(iter(suite["domains"].values()))["cases"][0]
        tokens = load_json(checked(ev, first_case["teacher_tokens"]))[:1]
        token_path = ev.path / "fixture-reference-tokens.json"
        write_json(token_path, tokens)
        require(ev.run("independent-fixture-references", [
            sys.executable, "tests/production_sim.py", "--reference-worker",
            "--tokens", str(token_path.relative_to(ROOT)),
            "--destination", str((ev.path / "fixture-reference").relative_to(ROOT)),
            "--modes", *MODES], timeout=args.timeout), "fixture reference preparation failed")
        references = load_json(ev.path / "fixture-reference/references.json")
        for mode in MODES:
            runs = []
            for repeat in range(2):
                run = ev.path / f"synthetic-{mode}-repeat-{repeat}"
                target = run / "position-0"
                target.mkdir(parents=True)
                for kind in ("layers", "logits"):
                    values = np.fromfile(ROOT / references[mode][kind]["path"], dtype="<f8")
                    with (target / (kind + ".f32")).open("xb") as output:
                        output.write(values.astype("<f4").tobytes())
                runs.append(run)
            compare_teacher(ev, "synthetic-fixture", mode, runs, references, 1,
                            ev.path / (mode + "-pristine-comparison"), synthetic=True)
            mutant = ev.path / ("synthetic-" + mode + "-mutant-repeat")
            shutil.copytree(runs[1], mutant)
            path = mutant / "position-0/logits.f32"
            raw = path.read_bytes()
            with path.open("wb") as output:
                output.write(bytes([raw[0] ^ 1]) + raw[1:])
            try:
                compare_teacher(ev, "synthetic-fixture", mode, [runs[0], mutant],
                                references, 1, ev.path / (mode + "-mutant-comparison"),
                                synthetic=True)
            except ValueError as error:
                require(ev.assertion("reject_synthetic_repeat_" + mode,
                                     "nondeterministic output" in str(error),
                                     diagnostic=str(error), no_rtl_execution=True),
                        "wrong comparison-fixture failure")
            else:
                raise ValueError("synthetic repeat corruption escaped comparison")
        ev.assertion("comparison_wiring_qualified_not_dut_execution", True,
                     modes=3, no_rtl_execution=True, complete_benchmark=False)
        return
    executable = compile_simulator(ev, args.build_receipt)
    if args.qualify_trace:
        table = memory_table(ev, model, "bf16", ev.path / "fixture.memory")
        rope = prepare_rope(ev.path / "fixture.rope", 1, "bf16")
        trace = ev.path / "synthetic.u32.gz"
        require(ev.run("synthetic-trace-serialization", [
            str(executable.relative_to(ROOT)), "--trace-fixture",
            str(table.relative_to(ROOT)), str(rope.relative_to(ROOT)),
            str(trace.relative_to(ROOT))]), "synthetic trace serialization failed")
        command = [sys.executable, "tests/production_trace.py", "--worker",
                   "--mode", "bf16", "--trace", str(trace.relative_to(ROOT)),
                   "--destination", str((ev.path / "synthetic-comparisons.json").relative_to(ROOT))]
        require(ev.run("synthetic-pristine-replay", command),
                "pristine synthetic transaction trace rejected")
        rows = list(struct.iter_unpack("<11I", gzip.decompress(trace.read_bytes())))
        require(len(rows) == 3 and rows[1][4] == 1 and rows[1][-1] != 0,
                "trace fixture did not exercise nonzero write data")
        original = [list(row) for row in rows]
        for label, row_number, field, value, expected in (
            ("lost-write-payload", 1, 10, 0, "embedding scratch payload lost/incorrect"),
            ("overlap", 1, 0, 2, "single-outstanding cycle order"),
            ("readback", 2, 10, rows[2][-1] ^ 1, "scratch read differs"),
        ):
            mutant = [row.copy() for row in original]
            mutant[row_number][field] = value
            path = ev.path / ("synthetic-" + label + ".u32.gz")
            with gzip.open(path, "xb") as output:
                for row in mutant:
                    output.write(struct.pack("<11I", *row))
            defect_command = command.copy()
            defect_command[defect_command.index("--trace") + 1] = str(path.relative_to(ROOT))
            defect_command[-1] = str((ev.path / ("rejected-" + label + ".json")).relative_to(ROOT))
            completed = ev.run("synthetic-" + label, defect_command)
            diagnostic = (ev.path / ("synthetic-" + label + ".stderr")).read_text()
            require(ev.assertion("reject_synthetic_" + label,
                                 not completed and expected in diagnostic,
                                 no_rtl_execution=True), "synthetic trace defect escaped")
        ev.assertion("trace_serialization_qualified_not_dut_execution", True,
                     transactions=3, rejected_mutants=3)
        first_case = next(iter(suite["domains"].values()))["cases"][0]
        token = load_json(checked(ev, first_case["teacher_tokens"]))[0]
        for mode in MODES:
            actual = ev.path / (mode + "-real-pin-prefix")
            actual.mkdir()
            actual_table = (table if mode == "bf16" else
                            memory_table(ev, model, mode, ev.path / (mode + "-fixture.memory")))
            actual_rope = (rope if mode == "bf16" else
                           prepare_rope(ev.path / (mode + "-fixture.rope"), 1, mode))
            require(ev.run(mode + "-real-pin-prefix", [
                str(executable.relative_to(ROOT)), "--pin-prefix",
                str(actual_table.relative_to(ROOT)), str(actual_rope.relative_to(ROOT)),
                str(actual.relative_to(ROOT)), str(token), str(MODES[mode])], timeout=3600),
                "real production transaction-prefix observation failed")
            actual_command = command.copy()
            actual_command[actual_command.index("--mode") + 1] = mode
            actual_command[actual_command.index("--trace") + 1] = str(
                (actual / "transactions.u32.gz").relative_to(ROOT))
            actual_command[-1] = str((ev.path / (mode + "-real-prefix-comparisons.json")).relative_to(ROOT))
            require(ev.run(mode + "-real-prefix-independent-replay", actual_command),
                    "real production transaction prefix rejected")
            compared = load_json(ev.path / (mode + "-real-prefix-comparisons.json"))
            require(compared["embedding_comparisons"] == 896 and
                    compared["transactions"] == 2000,
                    "real prefix omitted required transaction/write comparisons")
            ev.assertion("real_production_prefix_trace_repaired_" + mode, True,
                         transactions=2000, embedding_comparisons=896, completed_tokens=0,
                         complete_benchmark=False)
        return
    if args.build_only:
        ev.assertion("production_binary_built_not_executed", True)
        return
    require(selected is not None, "collection selection was not preflighted")
    index = {
        "schema": 1, "purpose": "incomplete-production-rtl-observations",
        "acceptance_evidence": False, "backend": "verilator",
        "production_dimensions_unchanged": True, "required_cases": 50,
        "required_modes": list(MODES), "required_independent_repeats": 2,
        "model_manifest": descriptor(ROOT / "tests/data/model_manifest.json"),
        "benchmark_manifest": descriptor(ROOT / "tests/data/benchmark_manifest.json"),
        "runs": [], "complete_benchmark": False,
        "limitations": "Raw public-pin collection only. Full result assembly, independent "
        "repeat/numerical validation, task evaluation and arithmetic/control attribution "
        "remain mandatory. Simulation never replaces target timing/resources/physical HIL."}
    for case_number, (key, case) in enumerate(selected, args.case_start):
        teacher = load_json(checked(ev, case["teacher_tokens"]))
        prompt = load_json(checked(ev, case["prompt_tokens"]))
        if args.teacher_prefix is not None:
            teacher = teacher[:args.teacher_prefix]
        require(teacher and prompt and all(type(x) is int and 0 <= x < 151936
                                          for x in teacher + prompt), "invalid token IDs")
        directory = ev.path / f"case-{case_number:02d}"
        directory.mkdir()
        # Recompute missing references from independent mathematics, never saved
        # DUT outputs or an absent historical collector directory.
        reference_tokens = directory / "reference-tokens.json"
        write_json(reference_tokens, teacher)
        ev.receipt.setdefault("data_sha256", {})[str(reference_tokens.relative_to(ROOT))] = sha(reference_tokens)
        require(ev.run(f"case-{case_number:02d}-independent-fp64", [
            sys.executable, "tests/production_sim.py", "--reference-worker",
            "--tokens", str(reference_tokens.relative_to(ROOT)),
            "--destination", str((directory / "references").relative_to(ROOT)),
            "--modes", *args.modes, *(["--packed-storage"] if args.packed_storage else [])],
            timeout=args.timeout),
            "independent FP64 reference preparation failed")
        references = load_json(directory / "references/references.json")
        for mode in args.modes:
            table = memory_table(ev, model, mode, directory / (mode + ".memory"))
            for workload in (("teacher",) if args.teacher_prefix else ("teacher", "greedy")):
                tokens = teacher if workload == "teacher" else prompt
                token_path = directory / (mode + "-" + workload + ".tokens")
                with token_path.open("x") as output:
                    output.write("\n".join(map(str, tokens)) + "\n")
                rope_path = prepare_rope(
                    directory / (mode + "-" + workload + ".rope"),
                    len(tokens) + (128 if workload == "greedy" else 0), mode)
                runs = []
                for repeat in range(2):
                    run = directory / f"{mode}-{workload}-repeat-{repeat}"
                    run.mkdir()
                    runs.append(run)
                    label = f"case-{case_number:02d}-{mode}-{workload}-{repeat}"
                    command = [
                        str(executable.relative_to(ROOT)), str(table.relative_to(ROOT)),
                        str(token_path.relative_to(ROOT)), str(rope_path.relative_to(ROOT)),
                        str(run.relative_to(ROOT)), str(MODES[mode]), workload,
                        ",".join(map(str, config["eos_token_id"] if
                                     isinstance(config["eos_token_id"], list) else
                                     [config["eos_token_id"]])),
                        "preparation-only",
                        references[mode]["layers"]["path"] if workload == "teacher" else "-",
                        references[mode]["logits"]["path"] if workload == "teacher" else "-",
                        str(len(tokens))]
                    if args.packed_storage:
                        command.append("--packed-storage")
                    for path in (table, token_path, rope_path):
                        ev.receipt.setdefault("data_sha256", {})[str(path.relative_to(ROOT))] = sha(path)
                    passed = ev.run(label, command, timeout=args.timeout)
                    record = {"case": key, "mode": mode, "workload": workload,
                              "repeat": repeat, "teacher_positions": len(teacher),
                              "complete_process": passed, "path": str(run.relative_to(ROOT))}
                    index["runs"].append(record)
                    write_json(ev.path / f"progress-{len(index['runs']):04d}.json", index)
                    require(passed, "production simulation incomplete/failed; retained " + label)
                    summary = load_json(run / "summary.json")
                    require(summary["positions_completed"] >= len(tokens),
                            "simulator did not complete all supplied tokens")
                    ev.assertion(label + "_actual_rtl_completed", True, **record)
                if workload == "teacher":
                    compare_teacher(ev, key, mode, runs, references, len(teacher),
                                    directory / (mode + "-teacher-comparison"))
                else:
                    eos = config["eos_token_id"]
                    compare_greedy(ev, key, mode, runs, prompt,
                                   directory / (mode + "-greedy-comparison.json"),
                                   eos if isinstance(eos, list) else [eos])
    # A collection pass is not the complete benchmark check or a physical claim.
    write_json(ev.path / "collection.json", index)
    ev.assertion("selected_collection_completed_not_benchmark_acceptance", True,
                 runs=len(index["runs"]), teacher_prefix=args.teacher_prefix)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--qualify-trace", action="store_true")
    parser.add_argument("--qualify-comparisons", action="store_true")
    parser.add_argument("--build-receipt", type=Path)
    parser.add_argument("--repair-of", type=Path)
    parser.add_argument("--case-start", type=int, default=0)
    parser.add_argument("--case-count", type=int, default=50)
    parser.add_argument("--modes", nargs="+", choices=tuple(MODES), default=list(MODES))
    parser.add_argument("--teacher-prefix", type=int)
    parser.add_argument("--timeout", type=int, default=86400)
    parser.add_argument("--reference-worker", action="store_true")
    parser.add_argument("--tokens", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--packed-storage", action="store_true")
    args = parser.parse_args()
    if args.reference_worker:
        from awq_prepare import numerics
        from teacher_reference import reference_case
        numerics()
        require(args.tokens is not None and args.destination is not None,
                "missing worker tokens or destination")
        tokens = load_json(artifact_path(ROOT, str(args.tokens)))
        destination = artifact_path(ROOT, str(args.destination))
        model = load_json(ROOT / "tests/data/model_manifest.json")
        config = load_json(ROOT / model["config"]["path"])
        references = {}
        for mode in ("checkpoint", *args.modes):
            references[mode] = reference_case(model, config, mode, tokens, destination / mode,
                                              packed=args.packed_storage)
            print(json.dumps({"mode": mode, "reference": references[mode]}), flush=True)
        write_json(destination / "references.json", references)
        return 0
    ev = Evidence("production-simulation")
    passed = False
    try:
        snapshot = ev.path / "collector-sources"
        snapshot.mkdir()
        for name in ("production_sim.py", "production_sim.cpp", "production_trace.py",
                     "packed_stream.hpp", "production_storage.hpp",
                     "packed_stream.py", "packed_storage.py", "sparse_transactions.py"):
            shutil.copy2(ROOT / "tests" / name, snapshot / name)
        if args.repair_of:
            ev.receipt["repair_of"] = descriptor(artifact_path(ROOT, str(args.repair_of)))
        require(args.timeout >= 3600 and args.case_start >= 0 and args.case_count > 0,
                "invalid collection bounds or simulation allowance below 3600 seconds")
        require(sum((args.build_only, args.qualify_trace, args.qualify_comparisons)) <= 1,
                "select only one collector qualification/build operation")
        require(args.teacher_prefix is None or 0 < args.teacher_prefix <= 32768,
                "invalid explicitly partial teacher prefix")
        require(len(args.modes) == len(set(args.modes)), "duplicate collection mode")
        if args.build_receipt:
            artifact_path(ROOT, str(args.build_receipt))
        run_collection(ev, args)
        passed = True
    except (ValueError, OSError, KeyError, ImportError) as error:
        ev.assertion("production_collection_failure", False, diagnostic=str(error))
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path)
            for path in ev.path.rglob("*") if path.is_file() and
            path.name != "receipt.json" and "obj" not in path.relative_to(ev.path).parts}
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                          "benchmark_acceptance": False}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
