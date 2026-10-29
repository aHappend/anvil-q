"""Reset-origin collection with three bounded, independently produced windows."""

import math
import struct
from pathlib import Path
import uuid

from benchmark import Validator, greedy_stop, load_json, require
from streaming_replay import (Process, data_bindings, item, specification,
                              vector_descriptor, write_new)


class WindowValidator(Validator):
    """Run the unchanged numerical assertions on bytes just read from producers."""

    def __init__(self, root, ev):
        super().__init__(root, ev)
        self.buffers = {}

    def array_bytes(self, descriptor, dtype, width):
        key = descriptor["buffer"]
        raw = self.buffers[key]
        require(len(raw) == width * (8 if dtype == "<f8" else 4),
                "incomplete streamed numerical array")
        return raw

    def buffer(self, name, raw):
        self.buffers[name] = raw
        return {"buffer": name}


def compare_window(root, ev, actual, repeated, reference, mode, label):
    validator = WindowValidator(root, ev)
    if reference is not None:
        require(actual.position == repeated.position == reference.position,
                "substituted/reordered repeat/reference observation")
    else:
        require(actual.position == repeated.position, "substituted repeat position")
    for kind, width in (("layers", 24 * 896), ("logits", 151936)):
        a = actual.vector(kind + ".f32", "<f4", width)
        b = repeated.vector(kind + ".f32", "<f4", width)
        require(a == b, "nondeterministic output: " + label + "/" + kind)
        require(all(math.isfinite(value) for value, in struct.iter_unpack("<f", a)),
                "nonfinite streamed output: " + label)
        if reference is None:
            continue
        selected = reference.vector("selected-" + kind + ".f64", "<f8", width)
        checkpoint = reference.vector("checkpoint-" + kind + ".f64", "<f8", width)
        indices = range(24) if kind == "layers" else range(1)
        count = 896 if kind == "layers" else 151936
        for layer in indices:
            start = layer * count
            validator.buffers.clear()
            values = [validator.buffer(name, raw) for name, raw in (
                ("actual", a[start*4:(start+count)*4]),
                ("repeat", b[start*4:(start+count)*4]),
                ("selected", selected[start*8:(start+count)*8]),
                ("checkpoint", checkpoint[start*8:(start+count)*8]))]
            threshold = ((.9999, .002) if kind == "layers" else (.999, .01))
            if mode == "w4a16":
                threshold = (-1, float("inf"))
            validator.arrays(values[0], values[2], values[1], count, threshold,
                             f"{label}/{kind}/{layer}")
            if kind == "logits":
                validator.arrays(values[2], values[3], values[2], count,
                                 (-1, float("inf")), label + "/storage-quantization",
                                 wide=True)
    return validator.metrics


def select_cases(root, args, suite, checked, ev):
    cases = [(domain + "/" + case["id"], case)
             for domain, group in suite["domains"].items() for case in group["cases"]]
    require(len(cases) == 50, "frozen suite is not fifty cases")
    selected = cases[args.case_start:args.case_start + args.case_count]
    require(len(selected) == args.case_count, "case selection exceeds frozen suite")
    for _, case in selected:
        for name in ("teacher_tokens", "prompt_tokens"):
            tokens = load_json(checked(ev, case[name]))
            require(tokens and all(type(token) is int and 0 <= token < 151936
                                   for token in tokens), "invalid collection context")
            require(len(tokens) + (127 if name == "prompt_tokens" else 0) <= 32768,
                    "collection exceeds legal sequence depth")
    return selected


def collect(ev, args, executable, model, suite, config, selected):
    from production_sim import MODES, memory_table, prepare_rope
    root = Path(__file__).resolve().parents[1]
    build = ev.path / "streaming-build.json"
    write_new(build, dict(build_sources=ev.receipt["build_sources"],
                          executable=item(root, executable),
                          records=ev.receipt["records"],
                          build_receipt=ev.receipt.get("build_receipt")))
    inputs = data_bindings(root, model, suite)
    for path in (root / "tests/data/model_manifest.json",
                 root / "tests/data/benchmark_manifest.json", build, executable):
        entry = item(root, path)
        inputs[entry["path"]] = entry["sha256"]
    index = dict(schema=1, purpose="streamed-production-rtl-observations",
                 acceptance_evidence=False, complete_benchmark=False,
                 evidence_lifetime="bounded-windows-with-executable-replay",
                 build=item(root, build), cases=[],
                 limitations="Collection is not benchmark assembly, isolated Code evaluation, "
                 "cycle attribution, Quartus/resource closure or physical HIL.")
    for number, (key, case) in enumerate(selected, args.case_start):
        teacher = load_json(root / case["teacher_tokens"]["path"])
        prompt = load_json(root / case["prompt_tokens"]["path"])
        if args.teacher_prefix is not None:
            teacher = teacher[:args.teacher_prefix]
        directory = ev.path / f"case-{number:02d}"
        directory.mkdir()
        reference_tokens = directory / "reference-tokens.json"
        write_new(reference_tokens, teacher)
        eos = config["eos_token_id"]
        eos = eos if isinstance(eos, list) else [eos]
        for mode in args.modes:
            table = memory_table(ev, model, mode, directory / (mode + ".memory"))
            for workload in (("teacher",) if args.teacher_prefix is not None else
                             ("teacher", "greedy")):
                tokens = teacher if workload == "teacher" else prompt
                token_path = directory / (mode + "-" + workload + ".tokens")
                with token_path.open("x") as stream:
                    stream.write("\n".join(map(str, tokens)) + "\n")
                rope = prepare_rope(directory / (mode + "-" + workload + ".rope"),
                                    len(tokens) + (128 if workload == "greedy" else 0), mode)
                dependencies = dict(inputs)
                for path in (table, token_path, reference_tokens, rope):
                    entry = item(root, path)
                    dependencies[entry["path"]] = entry["sha256"]
                recipes = []
                for role in ("observation", "repeat"):
                    recipes.append(specification(
                        root, argv=[str(executable.relative_to(root)),
                                    str(table.relative_to(root)), str(token_path.relative_to(root)),
                                    str(rope.relative_to(root)), "{output}", str(MODES[mode]),
                                    workload, ",".join(map(str, eos)), "preparation-only",
                                    "-", "-", str(len(tokens)), "--stream-windows"],
                        output_index=4, role=role, case=key, mode=mode, workload=workload,
                        tokens=tokens, inputs=dependencies, tool_names=("python3", "verilator", "c++"),
                        build=item(root, build)))
                if workload == "teacher":
                    recipes.append(specification(
                        root, argv=["python3", "tests/streaming_replay.py", "--reference-worker",
                                    "--tokens", str(reference_tokens.relative_to(root)),
                                    "--destination", "{output}", "--mode", mode],
                        output_index=6, role="reference", case=key, mode=mode, workload=workload,
                        tokens=tokens, inputs=dependencies, tool_names=("python3",)))
                processes = []
                try:
                    for recipe in recipes:
                        processes.append(Process(root, directory / (mode + "-" + workload +
                                                                   "-" + recipe["role"] +
                                                                   "-" + uuid.uuid4().hex),
                                                 recipe, args.timeout))
                    actual, repeated = processes[:2]
                    reference = processes[2] if workload == "teacher" else None
                    generated = []
                    position = 0
                    while True:
                        for process in processes:
                            process.next()
                        observation = actual.current["observation"]
                        require(observation == repeated.current["observation"],
                                "independent repeat public-pin observations differ")
                        metrics = compare_window(root, ev, actual, repeated, reference, mode,
                                                 f"{key}/{mode}/{workload}/{position}")
                        if workload == "greedy":
                            raw = actual.vector("logits.f32", "<f4", 151936)
                            values = struct.unpack("<151936f", raw)
                            token = max(range(151936), key=values.__getitem__)
                            require(token == observation["argmax"], "incorrect greedy argmax")
                            if position >= len(prompt)-1:
                                generated.append(token)
                            if position >= len(prompt):
                                require(observation["token_id"] == generated[-2],
                                        "greedy continuation input differs")
                        write_new(directory / f"{mode}-{workload}-comparison-{position:05d}.json",
                                  dict(position=position, metrics=metrics, original_executions=[
                                      process.record["execution_id"] for process in processes]))
                        # A failed comparison never reaches release; all failing bytes remain.
                        for process in processes:
                            process.release()
                        position += 1
                        if workload == "teacher" and position == len(tokens):
                            break
                        if workload == "greedy" and generated and (
                                generated[-1] in eos or len(generated) == 128):
                            break
                    if workload == "greedy":
                        greedy_stop(generated, "eos" if generated[-1] in eos else "max_new_tokens", eos)
                    manifests = []
                    for process in processes:
                        process.finish()
                        manifests.append(process.seal())
                    rows = []
                    for position in range(len(actual.windows)):
                        row = dict(position=position, layers=[])

                        def vector(process_index, name, dtype, width, offset=0):
                            process = processes[process_index]
                            manifest = dict(windows=process.windows)
                            return vector_descriptor(root, manifests[process_index], manifest,
                                                     position, name, dtype, width, offset)

                        row.update(logits=vector(0, "logits.f32", "<f4", 151936),
                                   repeat_logits=vector(1, "logits.f32", "<f4", 151936))
                        if workload == "teacher":
                            row.update(fp64_logits=vector(2, "selected-logits.f64", "<f8", 151936),
                                       decoded_weight_logits=vector(2, "selected-logits.f64", "<f8", 151936),
                                       checkpoint_fp64_logits=vector(2, "checkpoint-logits.f64", "<f8", 151936))
                            for layer in range(24):
                                row["layers"].append(dict(
                                    layer=layer,
                                    output=vector(0, "layers.f32", "<f4", 896, layer*896*4),
                                    repeat_output=vector(1, "layers.f32", "<f4", 896, layer*896*4),
                                    fp64_output=vector(2, "selected-layers.f64", "<f8", 896, layer*896*8)))
                        rows.append(row)
                    entry = dict(case=key, mode=mode, workload=workload,
                                 manifests=manifests, positions=rows, generated_tokens=generated)
                    index["cases"].append(entry)
                    write_new(directory / f"{mode}-{workload}-collection.json", entry)
                    ev.assertion("streamed_reset_origin_" + mode + "_" + workload, True,
                                 case=key, positions=len(rows), manifests=manifests,
                                 original_execution_ids=[process.record["execution_id"]
                                                         for process in processes])
                finally:
                    for process in processes:
                        if not process.finished:
                            process.abort()
    write_new(ev.path / "collection.json", index)
    ev.assertion("selected_streamed_collection_completed_not_benchmark_acceptance", True,
                 workloads=len(index["cases"]), teacher_prefix=args.teacher_prefix)
