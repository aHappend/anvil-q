#!/usr/bin/env python3
"""Prepare actual four-weight-semantics FP64 teacher references, not DUT results."""

import argparse
import json
from pathlib import Path
import shutil
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from awq_prepare import AWQStream, batch_activations, numerics
from benchmark import Validator, load_json, require, sha
from benchmark_inputs import checked_payload, write_json
from fp64_reference import NativeStream, SafeTensors, decode
from verify import Evidence, ROOT


MODES = ("checkpoint", "bf16", "fp16", "w4a16")


def descriptor(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def selected_stream(model, mode):
    if mode == "checkpoint":
        return SafeTensors(ROOT / model["checkpoint"][0]["path"])
    directory = (ROOT / model["streams"][mode]["layout"]["path"]).parent
    return AWQStream(directory) if mode == "w4a16" else NativeStream(directory, mode)


def decoded_rows(stream, raw, mode):
    if mode == "w4a16":
        return stream.decode_rows(raw)
    return decode(raw, stream.tensors["model.embed_tokens.weight"]["dtype"])


def reference_case(model, config, mode, tokens, destination):
    require(tokens and len(tokens) <= 32768 and
            all(type(token) is int and 0 <= token < 151936 for token in tokens),
            "invalid full teacher context")
    stream = selected_stream(model, mode)
    layers = batch_activations(stream, tokens, config, mode=mode)
    require(layers.shape == (24, len(tokens), 896) and np.isfinite(layers).all(),
            "invalid teacher layer references")
    destination.mkdir(parents=True, exist_ok=False)
    layers_path, logits_path = destination / "layers.f64", destination / "logits.f64"
    with layers_path.open("xb") as output:
        output.write(np.transpose(layers, (1, 0, 2)).astype("<f8").tobytes())
    final = layers[-1]
    epsilon = (float(np.float32(config["rms_norm_eps"])) if mode in ("bf16", "fp16")
               else config["rms_norm_eps"])
    final = final * stream.weight("model.norm.weight", mode) / np.sqrt(
        np.mean(final * final, axis=-1, keepdims=True) + epsilon)
    embedding = stream.get("model.embed_tokens.weight")
    argmax = np.zeros(len(tokens), dtype=np.int64)
    maximum = np.full(len(tokens), -np.inf)
    with logits_path.open("xb") as output:
        for start in range(0, len(embedding), 1024):
            rows = decoded_rows(stream, embedding[start:start + 1024], mode)
            logits = rows @ final.T
            require(np.isfinite(logits).all(), "nonfinite teacher reference logits")
            output.write(logits.astype("<f8").tobytes())
            local_index = np.argmax(logits, axis=0)
            local_value = logits[local_index, np.arange(len(tokens))]
            changed = local_value > maximum
            argmax[changed] = start + local_index[changed]
            maximum[changed] = local_value[changed]
    # All positions are retained. Vocabulary-major logits allow bounded memory
    # and sequential file writes; consumers must use this explicit axis order.
    return {
        "mode": mode, "positions": len(tokens), "arithmetic": "ieee-fp64",
        "weight_semantics": "decoded-selected-stream" if mode != "checkpoint" else "original-checkpoint",
        "layers": {**descriptor(layers_path), "dtype": "<f8", "shape": [len(tokens), 24, 896],
                   "axes": ["position", "layer", "component"]},
        "logits": {**descriptor(logits_path), "dtype": "<f8", "shape": [151936, len(tokens)],
                   "axes": ["vocabulary", "position"]},
        "lowest_id_argmax": argmax.tolist(),
    }


def validate_inputs(ev):
    validator = Validator(ROOT, ev)
    model = load_json(ROOT / "tests/data/model_manifest.json")
    suite = load_json(ROOT / "tests/data/benchmark_manifest.json")
    validator.model(model)
    cases = validator.suite(suite, model)
    config = load_json(validator.artifact(model["config"]))
    return model, suite, cases, config


def qualified(ev, path):
    require(path is not None, "missing sequential reference receipt")
    full = ROOT / path
    require(full.resolve().is_relative_to(ROOT), "reference receipt escapes project")
    record = load_json(full)
    require(record["status"] == "passed", "sequential reference incomplete")
    ev.receipt.setdefault("sequential_reference_receipts", []).append(descriptor(full))
    for name, hashed in record["outputs"].items():
        checked_payload(ev, {"path": name, "sha256": hashed})
    return record


def qualification_worker(args):
    numerics()
    model = load_json(ROOT / "tests/data/model_manifest.json")
    config = load_json(ROOT / model["config"]["path"])
    args.destination.mkdir(parents=True, exist_ok=False)
    tokens = [config["bos_token_id"], 17, 53]
    report = {"purpose": "batched-teacher-reference-qualification", "modes": {}}
    native = load_json(args.native_reference_receipt)
    awq = load_json(args.awq_reference_receipt)
    for mode in MODES:
        actual = reference_case(model, config, mode, tokens, args.destination / mode)
        layers = np.fromfile(ROOT / actual["layers"]["path"], dtype="<f8").reshape(3, 24, 896)
        logits = np.fromfile(ROOT / actual["logits"]["path"], dtype="<f8").reshape(151936, 3)
        retained = awq if mode == "w4a16" else native
        maximum_layer, maximum_logit = 0., 0.
        for position in range(3):
            def expected(kind, shape):
                suffix = f"/{mode}-position-{position}-{kind}.f64"
                candidates = [name for name in retained["outputs"] if name.endswith(suffix)]
                require(len(candidates) == 1, "missing unmodified sequential FP64 expected data")
                path = ROOT / candidates[0]
                require(sha(path) == retained["outputs"][candidates[0]],
                        "sequential reference binding differs")
                return np.fromfile(path, dtype="<f8").reshape(shape)
            expected_layers = expected("layers", (24, 896))
            expected_logits = expected("logits", (151936,))
            layer_error = float(np.max(np.abs(layers[position] - expected_layers)))
            logit_error = float(np.max(np.abs(logits[:, position] - expected_logits)))
            require(layer_error <= 1e-11 * max(1., float(np.max(np.abs(expected_layers)))) and
                    logit_error <= 1e-11 * max(1., float(np.max(np.abs(expected_logits)))),
                    "batched reference differs from retained sequential inference")
            maximum_layer = max(maximum_layer, layer_error)
            maximum_logit = max(maximum_logit, logit_error)
        report["modes"][mode] = {
            "layer_vectors_compared": 72, "complete_logit_vectors_compared": 3,
            "maximum_absolute_layer_error": maximum_layer,
            "maximum_absolute_logit_error": maximum_logit}
        print(json.dumps({"mode": mode, **report["modes"][mode]}), flush=True)
    write_json(args.destination / "qualification.json", report)


def full_worker(args):
    numerics()
    model = load_json(ROOT / "tests/data/model_manifest.json")
    suite = load_json(ROOT / "tests/data/benchmark_manifest.json")
    config = load_json(ROOT / model["config"]["path"])
    args.destination.mkdir(parents=True, exist_ok=False)
    result = {
        "schema": 1, "purpose": "full-suite-teacher-reference-preparation",
        "acceptance_evidence": False, "model_manifest": descriptor(ROOT / "tests/data/model_manifest.json"),
        "benchmark_manifest": descriptor(ROOT / "tests/data/benchmark_manifest.json"),
        "arithmetic": "ieee-fp64", "independent_of_rtl": True,
        "dependencies": {"numpy": np.__version__, "python": sys.version},
        "reference_sources": {name: sha(ROOT / name) for name in (
            "tests/teacher_reference.py", "tests/fp64_reference.py", "tests/awq_prepare.py")},
        "limitations": "Complete teacher reference arrays only; no DUT comparisons, "
                        "greedy outputs, task scores, cycles, timing, resources or hardware evidence.",
        "cases": []}
    for domain, group in suite["domains"].items():
        for case in group["cases"]:
            tokens = load_json(ROOT / case["teacher_tokens"]["path"])
            identifier = domain + "/" + case["id"]
            number = len(result["cases"])
            row = {"case": identifier, "teacher_tokens": case["teacher_tokens"], "modes": {}}
            for mode in MODES:
                row["modes"][mode] = reference_case(
                    model, config, mode, tokens, args.destination / f"case-{number:02d}" / mode)
                print(json.dumps({"case": identifier, "mode": mode,
                                  "teacher_positions": len(tokens), "layers": 24, "vocabulary": 151936}),
                      flush=True)
            result["cases"].append(row)
            # Incremental indexes never assert that the remaining cases ran.
            write_json(args.destination / f"completed-through-{number:02d}.json", row)
    require(len(result["cases"]) == 50, "incomplete teacher suite")
    write_json(args.destination / "teacher_references.json", result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualify", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--native-reference-receipt", type=Path)
    parser.add_argument("--awq-reference-receipt", type=Path)
    parser.add_argument("--qualification-receipt", type=Path)
    args = parser.parse_args()
    for key, value in vars(args).items():
        if isinstance(value, Path):
            require(not value.is_absolute() and ".." not in value.parts and
                    (ROOT / value).resolve().is_relative_to(ROOT), "nonportable reference argument")
            if args.worker:
                setattr(args, key, (ROOT / value).resolve())
    if args.worker:
        require(args.destination is not None, "worker output directory missing")
        (qualification_worker if args.qualify else full_worker)(args)
        return 0
    ev = Evidence("teacher-reference-qualification" if args.qualify else "teacher-reference-full")
    ok = False
    try:
        model, suite, cases, _ = validate_inputs(ev)
        destination = ev.path / "reference-outputs"
        command = [sys.executable, "tests/teacher_reference.py", "--worker",
                   "--destination", str(destination.relative_to(ROOT))]
        require(ev.run("numpy-version", [sys.executable, "-c",
                                       "import numpy,sys; print(sys.version); print(numpy.__version__)"],
                       timeout=30), "reference dependency missing")
        if args.qualify:
            native = qualified(ev, args.native_reference_receipt)
            awq = qualified(ev, args.awq_reference_receipt)
            checkpoint_path = model["checkpoint"][0]["path"]
            require(native["data_sha256"][checkpoint_path] == model["checkpoint"][0]["sha256"] and
                    awq["data_sha256"][checkpoint_path] == model["checkpoint"][0]["sha256"],
                    "sequential reference used a different checkpoint")
            for mode in ("bf16", "fp16"):
                retained = load_json(ROOT / native["selected_streams_receipt"]["path"])
                require(all(retained["outputs"][model["streams"][mode][key]["path"]] ==
                            model["streams"][mode][key]["sha256"] for key in ("weights", "layout")),
                        "native sequential reference used different selected streams")
            retained = load_json(ROOT / awq["streams_receipt"]["path"])
            require(all(retained["outputs"][model["streams"]["w4a16"][key]["path"]] ==
                        model["streams"]["w4a16"][key]["sha256"]
                        for key in ("weights", "layout", "zeros", "scales")),
                    "AWQ sequential reference used different selected streams")
            command += ["--qualify", "--native-reference-receipt", str(args.native_reference_receipt),
                        "--awq-reference-receipt", str(args.awq_reference_receipt)]
        else:
            qualification = qualified(ev, args.qualification_receipt)
            require(any(row["name"] == "teacher_reference_qualification_completed" and row["passed"]
                        for row in qualification["assertions"]), "missing batched qualification assertion")
            dependencies = ("tests/teacher_reference.py", "tests/fp64_reference.py", "tests/awq_prepare.py")
            require(all(qualification["source_sha256"][name] == sha(ROOT / name)
                        for name in dependencies), "qualified reference implementation changed")
            require(all(qualification["data_sha256"][model[key]["path"]] == model[key]["sha256"]
                        for key in ("config", "tokenizer")), "qualified model inputs changed")
            positions = sum(len(case[3]) for case in cases.values())
            expected_bytes = positions * len(MODES) * (24 * 896 + 151936) * 8
            free = shutil.disk_usage(ROOT).free
            reserve = max(1024 ** 3, free // 10)
            require(ev.assertion("reference_output_capacity", free >= expected_bytes + reserve,
                                 teacher_positions=positions, required_bytes=expected_bytes,
                                 available_bytes=free, reserved_bytes=reserve),
                    "insufficient shared storage for complete reference arrays")
        ok = ev.run("teacher-reference", command, timeout=86400)
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path)
            for path in destination.rglob("*") if path.is_file()}
        ev.receipt["scope"] = (
            "Four-weight-semantics FP64 teacher preparation or qualification only. "
            "No integrated DUT, greedy task result, cycle, PPA, timing or physical acceptance.")
        label = "teacher_reference_qualification_completed" if args.qualify else "full_teacher_reference_completed"
        ok = ev.assertion(label, ok, frozen_cases=len(cases)) and ok
    except (ValueError, KeyError, OSError) as error:
        ev.assertion("teacher_reference_exception", False, error=repr(error))
    finally:
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
