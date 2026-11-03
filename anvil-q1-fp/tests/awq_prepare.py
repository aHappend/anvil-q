#!/usr/bin/env python3
"""Retained activation-aware W4 stream preparation, never DUT execution."""

import argparse
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import DIMENSIONS, MODEL, Validator, load_json, require, sha
from benchmark_inputs import checked_payload, write_json
from input_prerequisites import fetch
from pinned_tokenizer import PATTERN, PinnedTokenizer
from verify import Evidence, ROOT


NIBBLE_ORDER = (0, 4, 1, 5, 2, 6, 3, 7)
CLIP_RATIOS = (1.0, .975, .95, .925, .90, .875, .85, .825, .80)
GROUP = 128
RECIPE = "anvil-activation-weighted-asymmetric-w4-v1"


def numerics():
    global np, PROJECTIONS, QwenFP64, SafeTensors, decode, encode, rope, silu, validate_config
    import numpy as np
    from fp64_reference import (PROJECTIONS, QwenFP64, SafeTensors, decode, encode,
                                rope, silu, validate_config)


def relative(path):
    return str(path.resolve().relative_to(ROOT))


def descriptor(path):
    return {"path": relative(path), "sha256": sha(path)}


def receipt(ev, path, key):
    require(path is not None, "missing " + key)
    full = (ROOT / path).resolve()
    require(full.is_relative_to(ROOT), "receipt escapes project")
    data = load_json(full)
    require(data["status"] == "passed", "incomplete " + key)
    ev.receipt[key] = descriptor(full)
    for name, hashed in data.get("outputs", {}).items():
        checked_payload(ev, {"path": name, "sha256": hashed})
    return data


def output_named(data, suffix):
    matches = [ROOT / name for name in data["outputs"] if name.endswith(suffix)]
    require(len(matches) == 1, "ambiguous or missing prepared output: " + suffix)
    return matches[0]


def checkpoint_input(ev, acquisition):
    data = receipt(ev, acquisition, "acquisition_receipt")
    for item in data["retrievals"]:
        if "/model/" in item["path"]:
            require(item["complete"], "incomplete checkpoint input")
            checked_payload(ev, item)
    directory = ROOT / "tests/data/acquired" / acquisition.parent.name / "model"
    return directory, data["acquired_repositories"]["model"]["revision"]


def q16_values(values):
    values = np.asarray(values, dtype=np.float64)
    require(np.isfinite(values).all(), "nonfinite compatibility data")
    magnitudes = np.floor(np.abs(values) * 65536 + .5)
    signed = np.where(np.signbit(values), -magnitudes, magnitudes)
    return np.clip(signed, -2147483648, 2147483647).astype(np.int64)


def scale_integers(scales):
    scales = np.asarray(scales, dtype="<f2").astype(np.float64)
    require(np.isfinite(scales).all() and np.all(scales >= 0),
            "invalid AWQ scale")
    result = np.floor(scales * 65536 + .5).astype(np.int64)
    require(np.all(result <= 0xffffffff), "AWQ scale exceeds parent integer range")
    return result


def pack_lanes(codes):
    require(codes.ndim == 2 and codes.shape[0] % 8 == 0 and
            np.all((codes >= 0) & (codes <= 15)), "invalid nibble array")
    output = np.zeros((codes.shape[1], codes.shape[0] // 8), dtype="<u4")
    for lane, nibble in enumerate(NIBBLE_ORDER):
        output |= codes[lane::8].T.astype("<u4") << (4 * nibble)
    return output


def unpack_lanes(words, outputs):
    require(words.ndim == 2 and words.shape[1] * 8 == outputs,
            "invalid packed output shape")
    result = np.empty((outputs, words.shape[0]), dtype=np.uint8)
    for lane, nibble in enumerate(NIBBLE_ORDER):
        result[lane::8] = ((words >> (4 * nibble)) & 15).T
    return result


def batch_activations(checkpoint, tokens, config, observer=None, mode="checkpoint"):
    """FP64 causal prefill; independent sequential inference qualifies this path."""
    embedding = checkpoint.get("model.embed_tokens.weight")[tokens]
    x = (checkpoint.decode_rows(embedding) if mode == "w4a16" else
         decode(embedding, checkpoint.tensors["model.embed_tokens.weight"]["dtype"]))
    epsilon = (float(np.float32(config["rms_norm_eps"])) if mode in ("bf16", "fp16")
               else config["rms_norm_eps"])
    positions = np.arange(len(tokens), dtype=np.float64)[:, None, None]
    mask = np.triu(np.ones((len(tokens), len(tokens)), dtype=bool), 1)
    layers = []
    for layer in range(24):
        prefix = f"model.layers.{layer}."

        def norm(value, suffix):
            return value * checkpoint.weight(prefix + suffix, mode) / np.sqrt(
                np.mean(value * value, axis=-1, keepdims=True) + epsilon)

        def linear(value, suffix, bias=False):
            name = prefix + suffix + ".weight"
            if observer is not None:
                observer(name, value)
            output = value @ checkpoint.weight(name, mode).T
            return output + checkpoint.weight(prefix + suffix + ".bias", mode) if bias else output

        normalized = norm(x, "input_layernorm.weight")
        q = linear(normalized, "self_attn.q_proj", True).reshape(-1, 14, 64)
        k = linear(normalized, "self_attn.k_proj", True).reshape(-1, 2, 64)
        v = linear(normalized, "self_attn.v_proj", True).reshape(-1, 2, 64)
        q = rope(q, positions, config["rope_theta"])
        k = rope(k, positions, config["rope_theta"])
        context = np.empty_like(q)
        for head in range(14):
            scores = q[:, head] @ k[:, head // 7].T / 8
            scores[mask] = -np.inf
            exponentials = np.exp(scores - scores.max(axis=1, keepdims=True))
            probabilities = exponentials / exponentials.sum(axis=1, keepdims=True)
            context[:, head] = probabilities @ v[:, head // 7]
        x = x + linear(context.reshape(-1, 896), "self_attn.o_proj")
        normalized = norm(x, "post_attention_layernorm.weight")
        gate = linear(normalized, "mlp.gate_proj")
        up = linear(normalized, "mlp.up_proj")
        x = x + linear(silu(gate) * up, "mlp.down_proj")
        require(np.isfinite(x).all(), "nonfinite calibration layer")
        layers.append(x.copy())
    return np.asarray(layers)


def quantize_groups(weights, second_moments):
    require(weights.ndim == 2 and weights.shape[1] % GROUP == 0 and
            second_moments.shape == (weights.shape[1],) and
            np.isfinite(weights).all() and np.isfinite(second_moments).all() and
            np.all(second_moments >= 0) and np.any(second_moments > 0),
            "invalid calibration/weight group")
    grouped = weights.reshape(weights.shape[0], -1, GROUP)
    importance = second_moments.reshape(1, -1, GROUP)
    low = np.minimum(grouped.min(axis=-1), 0)
    high = np.maximum(grouped.max(axis=-1), 0)
    best_error = np.full(low.shape, np.inf)
    best_codes = np.zeros(grouped.shape, dtype=np.uint8)
    best_zeros = np.zeros(low.shape, dtype=np.uint8)
    best_scales = np.zeros(low.shape, dtype="<f2")
    best_ratio = np.zeros(low.shape, dtype=np.uint8)
    baseline = None
    for index, ratio in enumerate(CLIP_RATIOS):
        scales = ((high - low) * ratio / 15).astype("<f2")
        integers = scale_integers(scales)
        effective = integers.astype(np.float64) / 65536
        # Zero groups use a positive computational divisor but store scale zero.
        divisor = np.where(effective > 0, effective, 1)
        zeros = np.clip(np.rint(-low * ratio / divisor), 0, 15).astype(np.uint8)
        codes = np.clip(np.rint(grouped / divisor[..., None]) + zeros[..., None],
                        0, 15).astype(np.uint8)
        decoded = (codes.astype(np.int16) - zeros[..., None]) * effective[..., None]
        errors = np.sum((decoded - grouped) ** 2 * importance, axis=-1, dtype=np.float64)
        if baseline is None:
            baseline = errors.copy()
        changed = errors < best_error
        best_codes[changed] = codes[changed]
        best_zeros[changed] = zeros[changed]
        best_scales[changed] = scales[changed]
        best_ratio[changed] = index
        best_error[changed] = errors[changed]
    require(np.all(best_error <= baseline), "clipping worsened the admitted search objective")
    return (best_codes.reshape(weights.shape), best_zeros, best_scales, best_ratio,
            float(best_error.sum()), float(baseline.sum()))


class AWQStream:
    def __init__(self, directory):
        numerics()
        self.directory = Path(directory)
        self.layout = load_json(self.directory / "layout.json")
        require(self.layout["recipe"] == RECIPE and
                self.layout["nibble_order"] == list(NIBBLE_ORDER) and
                self.layout["group_size"] == GROUP, "unsupported AWQ stream")
        self.tensors = self.layout["tensors"]
        files = {"packed-u4": "weights.bin", "F16": "weights.bin"}
        totals = {"weights.bin": [], "scales.bin": [], "zeros.bin": []}
        for name, item in self.tensors.items():
            outputs = item["shape"][0]
            matrix = item["encoding"] == "packed-u4"
            count = (item["shape"][1] * outputs // 8 * 4 if matrix
                     else int(np.prod(item["shape"])) * 2)
            require(item["byte_length"] == count, "AWQ tensor byte length differs: " + name)
            totals[files[item["encoding"]]].append((item["byte_offset"], count))
            if matrix:
                groups = item["shape"][1] // GROUP
                totals["scales.bin"].append((item["scale_offset"], groups * outputs * 2))
                totals["zeros.bin"].append((item["zero_offset"], groups * outputs // 8 * 4))
        for filename, intervals in totals.items():
            cursor = 0
            for offset, count in sorted(intervals):
                require(offset == cursor, "AWQ stream gap or overlap: " + filename)
                cursor += count
            require(cursor == (self.directory / filename).stat().st_size,
                    "AWQ stream incomplete/trailing data: " + filename)

    def get(self, name):
        item = self.tensors[name]
        require(item["encoding"] == "F16", "get requires an unpacked external tensor")
        return np.memmap(self.directory / "weights.bin", mode="r", dtype="<f2",
                         offset=item["byte_offset"], shape=tuple(item["shape"]))

    @staticmethod
    def decode_rows(values):
        return q16_values(values).astype(np.float64) / 65536

    def weight(self, name, mode="w4a16"):
        require(mode == "w4a16", "AWQ precision mismatch")
        item = self.tensors[name]
        if item["encoding"] == "F16":
            return self.decode_rows(self.get(name))
        outputs, inputs = item["shape"]
        words = np.memmap(self.directory / "weights.bin", mode="r", dtype="<u4",
                          offset=item["byte_offset"], shape=(inputs, outputs // 8))
        scales = np.memmap(self.directory / "scales.bin", mode="r", dtype="<f2",
                           offset=item["scale_offset"], shape=(inputs // GROUP, outputs))
        zeros = np.memmap(self.directory / "zeros.bin", mode="r", dtype="<u4",
                          offset=item["zero_offset"], shape=(inputs // GROUP, outputs // 8))
        codes = unpack_lanes(words, outputs).astype(np.int16)
        z = np.repeat(unpack_lanes(zeros, outputs), GROUP, axis=1).astype(np.int16)
        s = np.repeat(scale_integers(scales).T, GROUP, axis=1).astype(np.float64)
        return (codes - z) * s / 65536


def selftest():
    codes = np.tile(np.arange(16, dtype=np.uint8)[:, None], (1, GROUP))
    packed = pack_lanes(codes)
    require(int(packed[0, 0]) == 0x75316420 and int(packed[0, 1]) == 0xfdb9eca8,
            "AWQ known physical nibble order differs")
    np.testing.assert_array_equal(unpack_lanes(packed, 16), codes)
    # Independent binary16 unpack and exact rational integer rounding.
    compared = 0
    for bits in range(0x7c00):
        value, = struct.unpack("<e", struct.pack("<H", bits))
        numerator, denominator = value.as_integer_ratio()
        expected = (numerator * 65536 * 2 + denominator) // (2 * denominator)
        actual = int(scale_integers(np.array([bits], dtype="<u2").view("<f2"))[0])
        require(actual == expected, "scale integer rounding differs")
        compared += 1
    np.testing.assert_array_equal(q16_values([2 ** -17, -2 ** -17, 65504, -65504]),
                                  [1, -1, 2147483647, -2147483648])
    weights = np.zeros((8, GROUP), dtype=np.float64)
    weights[:, :3] = [-1, .125, 2]
    moments = np.ones(GROUP)
    moments[2] = .000001
    q, z, s, ratio, error, baseline = quantize_groups(weights, moments)
    require(error < baseline and np.any(ratio > 0),
            "activation-weighted search not sensitive to actual activation importance")
    decoded = (q.astype(np.int16) - z) * scale_integers(s) / 65536
    np.testing.assert_allclose(np.sum((decoded - weights) ** 2 * moments), error, rtol=1e-14)
    print(json.dumps({"scale_encodings_compared": compared,
                      "nibble_known_words": 2, "clipping_sensitivity": True,
                      "scope": "Quantization helper self-test, not RTL or model fidelity"}))


def input_worker(checkpoint_dir, train, destination):
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    configuration = load_json(checkpoint_dir / "tokenizer_config.json")
    template = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(
        configuration["chat_template"])
    rows = [json.loads(line) for line in train.read_text().splitlines() if line]
    require(len(rows) == 7473, "unexpected complete GSM8K training inventory")
    tokenizer = PinnedTokenizer(checkpoint_dir)
    cases, segments = [], set()
    destination.mkdir(parents=True, exist_ok=False)
    try:
        for index, row in enumerate(rows[:8]):
            text = template.render(messages=[{"role": "user", "content": row["question"]}],
                                   tools=None, add_generation_prompt=True) + row["answer"]
            tokens = tokenizer.encode(text)
            require(tokens == tokenizer.encode(text, heap=True) and
                    tokenizer.decode(tokens) == tokenizer.normalized_text(text),
                    "calibration BPE/roundtrip disagreement")
            require(len(tokens) >= 2 and all(0 <= token < 151936 for token in tokens),
                    "invalid calibration token")
            segments.update(part for part in tokenizer.parts(text) if part not in tokenizer.added)
            cases.append({"id": f"train/{index:06d}", "source": row,
                          "rendered": text, "tokens": tokens[:128]})
        write_json(destination / "unicode_request.json", {"pattern": PATTERN,
                                                         "texts": sorted(segments)})
        write_json(destination / "calibration_inputs.json", {
            "schema": 1, "purpose": "awq-calibration-inputs", "recipe": RECIPE,
            "dataset": "openai/grade-school-math:train",
            "revision": "3101c7d5072418e28b9008a6636bde82a006892c",
            "source": descriptor(train), "source_records": len(rows),
            "selection": "first eight original training rows; first 128 tokens per row",
            "tokenizer": descriptor(checkpoint_dir / "tokenizer.json"),
            "tokenizer_config": descriptor(checkpoint_dir / "tokenizer_config.json"),
            "cases": cases, "token_count": sum(len(row["tokens"]) for row in cases)})
        print(json.dumps({"cases": len(cases), "tokens": sum(len(row["tokens"]) for row in cases),
                          "scope": "Actual training input preparation, not benchmark execution"}))
    finally:
        tokenizer.splitter.close()


def qualify_inputs(directory, checkpoint_dir):
    import unicodedata
    tokenizer = PinnedTokenizer(checkpoint_dir)
    try:
        request = load_json(directory / "unicode_request.json")
        expected = load_json(directory / "perl_unicode_reference.json")
        require(len(request["texts"]) == len(expected["texts"]), "missing calibration Unicode cases")
        for text, reference in zip(request["texts"], expected["texts"]):
            normalized = unicodedata.normalize("NFC", text)
            require(normalized == reference["normalized"] and
                    tokenizer.splitter.split(normalized) == reference["pieces"],
                    "calibration Unicode independent parity differs")
        print(json.dumps({"segments_compared": len(request["texts"]),
                          "pcre_versions": tokenizer.splitter.versions,
                          "perl_version": expected["perl_version"],
                          "scope": "Calibration tokenizer qualification only"}))
    finally:
        tokenizer.splitter.close()


def capture_worker(checkpoint_dir, inputs, destination):
    checkpoint = SafeTensors(checkpoint_dir / "model.safetensors")
    config = load_json(checkpoint_dir / "config.json")
    validate_config(config, checkpoint.tensors)
    data = load_json(inputs)
    require(data["purpose"] == "awq-calibration-inputs" and data["recipe"] == RECIPE,
            "wrong calibration input purpose")
    destination.mkdir(parents=True, exist_ok=False)
    # The calibration prefill is qualified against a differently organized
    # sequential inference implementation, on the actual complete checkpoint.
    sequence = [17, 53, 89]
    batch = batch_activations(checkpoint, sequence, config)
    sequential = QwenFP64(config, checkpoint, "checkpoint")
    max_error = 0.
    for position, token in enumerate(sequence):
        layers, _ = sequential.step(token)
        error = float(np.max(np.abs(layers - batch[:, position])))
        require(error / max(1., float(np.max(np.abs(layers)))) <= 1e-11,
                "batched calibration differs from independent sequential FP64 inference")
        max_error = max(max_error, error)
    print(json.dumps({"batch_sequential_layer_vectors_compared": 72,
                      "maximum_absolute_error": max_error}), flush=True)
    statistics = {}

    def observe(name, value):
        second = np.sum(value * value, axis=0, dtype=np.float64)
        if name not in statistics:
            statistics[name] = [second, len(value)]
        else:
            statistics[name][0] += second
            statistics[name][1] += len(value)

    for case in data["cases"]:
        batch_activations(checkpoint, case["tokens"], config, observe)
        print(json.dumps({"calibration_case": case["id"], "tokens": len(case["tokens"]),
                          "layers_executed": 24}), flush=True)
    require(len(statistics) == 168, "missing calibration projection")
    report = {
        "schema": 1, "purpose": "actual-activation-calibration", "recipe": RECIPE,
        "inputs": descriptor(inputs), "checkpoint": descriptor(checkpoint_dir / "model.safetensors"),
        "config": descriptor(checkpoint_dir / "config.json"), "arithmetic": "ieee-fp64",
        "approximation": "diagonal input second moment; no inter-channel covariance",
        "batch_sequential_comparisons": 72, "batch_sequential_maximum_absolute_error": max_error,
        "statistics": {}, "dependencies": {"numpy": np.__version__, "python": sys.version},
    }
    for index, (name, (sums, count)) in enumerate(sorted(statistics.items())):
        require(count == data["token_count"] and np.isfinite(sums).all() and
                np.all(sums >= 0) and np.any(sums > 0), "invalid actual activation statistic")
        path = destination / f"second-moment-{index:03d}.f64"
        with path.open("xb") as output:
            output.write((sums / count).astype("<f8").tobytes())
        report["statistics"][name] = {"second_moment": descriptor(path), "tokens": count}
    write_json(destination / "calibration.json", report)
    print(json.dumps({"projections_calibrated": len(statistics),
                      "tokens_per_projection": data["token_count"],
                      "scope": "Actual full-dimension calibration, not DUT benchmark execution"}))


def quantize_worker(checkpoint_dir, calibration_path, destination, revision):
    calibration = load_json(calibration_path)
    require(calibration["purpose"] == "actual-activation-calibration" and
            calibration["recipe"] == RECIPE and
            calibration["checkpoint"] == descriptor(checkpoint_dir / "model.safetensors"),
            "calibration checkpoint/recipe mismatch")
    checkpoint = SafeTensors(checkpoint_dir / "model.safetensors")
    validate_config(load_json(checkpoint_dir / "config.json"), checkpoint.tensors)
    destination.mkdir(parents=True, exist_ok=False)
    layout = {"schema": 1, "model_revision": revision, "recipe": RECIPE,
              "group_size": GROUP, "nibble_order": list(NIBBLE_ORDER), "tensors": {}}
    report = {"schema": 1, "purpose": "activation-calibrated-awq-conversion",
              "recipe": RECIPE, "calibration": descriptor(calibration_path),
              "checkpoint": descriptor(checkpoint_dir / "model.safetensors"),
              "clip_ratios_in_order": CLIP_RATIOS,
              "objective": "sum(input_second_moment * (weight - parent_decoded_weight)^2)",
              "rounding": "nearest-even quantization; parent half-away Q16 scale decoding",
              "rescaling": "none; no hidden changes to norms, bias, embeddings or architecture",
              "tool_version": {"numpy": np.__version__, "python": sys.version}, "matrices": {}}
    with (destination / "weights.bin").open("xb") as weights_out, (
            destination / "scales.bin").open("xb") as scales_out, (
            destination / "zeros.bin").open("xb") as zeros_out:
        for name in sorted(checkpoint.tensors):
            shape = checkpoint.tensors[name]["shape"]
            item = {"shape": shape, "byte_offset": weights_out.tell()}
            matrix = len(shape) == 2 and name != "model.embed_tokens.weight"
            if not matrix:
                raw = checkpoint.get(name)
                for start in range(0, len(raw), 256):
                    values = decode(raw[start:start + 256], checkpoint.tensors[name]["dtype"])
                    weights_out.write(encode(values, "fp16").tobytes())
                item.update(encoding="F16", address="parent kind-0/4/5/6/7 binary16 data in low half")
            else:
                statistic = calibration["statistics"][name]
                moments_path = ROOT / statistic["second_moment"]["path"]
                require(descriptor(moments_path) == statistic["second_moment"],
                        "calibration statistic hash mismatch")
                moments = np.fromfile(moments_path, dtype="<f8")
                original = checkpoint.weight(name)
                codes = np.empty(shape, dtype=np.uint8)
                scales = np.empty((shape[0], shape[1] // GROUP), dtype="<f2")
                zeros = np.empty(scales.shape, dtype=np.uint8)
                histogram = np.zeros(len(CLIP_RATIOS), dtype=np.int64)
                error, baseline = 0., 0.
                for start in range(0, shape[0], 32):
                    q, z, s, ratio, e, b = quantize_groups(original[start:start + 32], moments)
                    codes[start:start + len(q)] = q
                    zeros[start:start + len(q)] = z
                    scales[start:start + len(q)] = s
                    histogram += np.bincount(ratio.reshape(-1), minlength=len(CLIP_RATIOS))
                    error += e
                    baseline += b
                item.update(
                    encoding="packed-u4", scale_offset=scales_out.tell(), zero_offset=zeros_out.tell(),
                    layer=int(name.split(".")[2]),
                    projection=PROJECTIONS[".".join(name.split(".")[3:-1])],
                    kind1="row=input,col=output_block; little-endian u32",
                    kind2="row=input_group,col=output_block; little-endian u32",
                    kind3="row=input_group,col=output; binary16 in low half")
                weights_out.write(pack_lanes(codes).tobytes())
                scales_out.write(scales.T.astype("<f2").tobytes())
                zeros_out.write(pack_lanes(zeros).tobytes())
                report["matrices"][name] = {
                    "weighted_squared_error": error, "unclipped_weighted_squared_error": baseline,
                    "selected_ratio_histogram": histogram.tolist(), "calibration_tokens": statistic["tokens"]}
                print(json.dumps({"matrix": name, **report["matrices"][name]}), flush=True)
            item["byte_length"] = weights_out.tell() - item["byte_offset"]
            layout["tensors"][name] = item
    require(len(report["matrices"]) == 168, "incomplete AWQ conversion")
    write_json(destination / "layout.json", layout)
    write_json(destination / "recipe.json", report)


def validate_worker(checkpoint_dir, directory, destination):
    selftest()
    checkpoint = SafeTensors(checkpoint_dir / "model.safetensors")
    stream = AWQStream(directory)
    validate_config(load_json(checkpoint_dir / "config.json"), stream.tensors)
    require(set(checkpoint.tensors) == set(stream.tensors), "AWQ tensor inventory mismatch")
    report = load_json(directory / "recipe.json")
    calibration = load_json(ROOT / report["calibration"]["path"])
    require(descriptor(ROOT / report["calibration"]["path"]) == report["calibration"],
            "AWQ recipe calibration binding mismatch")
    checked = 0
    scalar_samples = []
    matrix_metrics = {}
    rng = np.random.default_rng(17)
    for name in sorted(stream.tensors):
        item = stream.tensors[name]
        if item["encoding"] == "F16":
            raw = stream.get(name)
            source = checkpoint.get(name)
            for start in range(0, len(raw), 256):
                expected = encode(decode(source[start:start + 256],
                                         checkpoint.tensors[name]["dtype"]), "fp16")
                np.testing.assert_array_equal(raw[start:start + 256].view("<u2"), expected.view("<u2"))
                checked += expected.size
            continue
        outputs, inputs = item["shape"]
        decoded = stream.weight(name)
        original = checkpoint.weight(name)
        moments = np.fromfile(ROOT / calibration["statistics"][name]["second_moment"]["path"],
                              dtype="<f8")
        error = float(np.sum((decoded - original) ** 2 * moments, dtype=np.float64))
        stored = report["matrices"][name]
        require(abs(error - stored["weighted_squared_error"]) <= 1e-10 * max(1., error),
                "independent full-stream calibration objective differs")
        require(error <= stored["unclipped_weighted_squared_error"] * (1 + 1e-12),
                "calibration selection worsened unclipped objective")
        words = np.memmap(directory / "weights.bin", dtype="<u4", mode="r",
                          offset=item["byte_offset"], shape=(inputs, outputs // 8))
        zeros = np.memmap(directory / "zeros.bin", dtype="<u4", mode="r",
                          offset=item["zero_offset"], shape=(inputs // GROUP, outputs // 8))
        scales = np.memmap(directory / "scales.bin", dtype="<u2", mode="r",
                           offset=item["scale_offset"], shape=(inputs // GROUP, outputs))
        for row, col in zip(rng.integers(inputs, size=64), rng.integers(outputs, size=64)):
            w, z = int(words[row, col // 8]), int(zeros[row // GROUP, col // 8])
            bits = int(scales[row // GROUP, col])
            # Explicit wire-position table and Python binary16/rational arithmetic
            # are independent of the NumPy stream unpack/scale implementation.
            shift = (0, 16, 4, 20, 8, 24, 12, 28)[col % 8]
            scale, = struct.unpack("<e", struct.pack("<H", bits))
            n, d = scale.as_integer_ratio()
            integer = (2 * n * 65536 + d) // (2 * d)
            expected = (((w >> shift) & 15) - ((z >> shift) & 15)) * integer
            require(float(decoded[col, row]) == expected / 65536,
                    "independent scalar AWQ address/encoding mismatch")
            scalar_samples.append((w, z, bits, int(col % 8), expected, 0))
        checked += outputs * inputs
        matrix_metrics[name] = {"weighted_squared_error_recomputed": error}
    destination.mkdir(parents=True, exist_ok=False)
    with (destination / "dequant_vectors.txt").open("x") as output:
        # All scale encodings, every lane, both delta signs and invalid classes.
        for bits in range(65536):
            lane = bits % 8
            w, z = (0xfedcba98, 0x76543210) if bits & 8 else (0x76543210, 0xfedcba98)
            invalid = (bits & 0x7c00) == 0x7c00 or (bits >> 15 and bits & 0x7fff != 0)
            shift = (0, 16, 4, 20, 8, 24, 12, 28)[lane]
            if invalid:
                value = 0
            else:
                scale, = struct.unpack("<e", struct.pack("<H", bits))
                n, d = scale.as_integer_ratio()
                integer = (2 * n * 65536 + d) // (2 * d)
                value = (((w >> shift) & 15) - ((z >> shift) & 15)) * integer
            output.write(f"{w:08x} {z:08x} {bits:04x} {lane} {value} {int(invalid)}\n")
        for w, z, bits, lane, value, invalid in scalar_samples:
            output.write(f"{w:08x} {z:08x} {bits:04x} {lane} {value} {invalid}\n")
    write_json(destination / "validation.json", {
        "scope": "Complete converted-stream integrity and calibration objective; not DUT inference",
        "tensor_count": len(stream.tensors), "elements_checked": checked,
        "matrix_count": len(matrix_metrics), "scalar_stream_samples": len(scalar_samples),
        "dequant_scale_encodings": 65536, "matrices": matrix_metrics})
    print(json.dumps({"tensor_count": len(stream.tensors), "elements_checked": checked,
                      "matrix_count": len(matrix_metrics), "scalar_stream_samples": len(scalar_samples)}))


def reference_worker(checkpoint_dir, directory, destination):
    config = load_json(checkpoint_dir / "config.json")
    reference = QwenFP64(config, AWQStream(directory), "w4a16")
    destination.mkdir(parents=True, exist_ok=False)
    for position, token in enumerate([config["bos_token_id"], 17, 53]):
        layers, logits = reference.step(token)
        with (destination / f"w4a16-position-{position}-layers.f64").open("xb") as output:
            output.write(layers.astype("<f8").tobytes())
        with (destination / f"w4a16-position-{position}-logits.f64").open("xb") as output:
            output.write(logits.astype("<f8").tobytes())
        print(json.dumps({"mode": "w4a16", "position": position, "token": token,
                          "layers": len(layers), "logit_count": len(logits),
                          "lowest_id_argmax": int(np.argmax(logits)),
                          "scope": "Decoded-W4 FP64 reference only, not fixed-point DUT execution"}),
              flush=True)


def model_manifest(ev, args, checkpoint_dir, revision):
    native = receipt(ev, args.native_receipt, "native_receipt")
    converted = receipt(ev, args.streams_receipt, "streams_receipt")
    validated = receipt(ev, args.validation_receipt, "validation_receipt")
    require(validated["streams_receipt"] == descriptor(ROOT / args.streams_receipt),
            "AWQ validation did not check these streams")
    native_root = output_named(native, "/bf16/layout.json").parent.parent
    awq_root = output_named(converted, "/layout.json").parent
    native_version = next(row for row in native["records"] if row["label"] == "reference-numpy-version")
    version_text = (ROOT / native_version["stdout"]).read_text().strip()
    checkpoint_path = checkpoint_dir / "model.safetensors"
    header = SafeTensors(checkpoint_path)
    checkpoint_hashes = {relative(checkpoint_path): sha(checkpoint_path)}
    parity = load_json(ROOT / "tests/data/benchmark_manifest.json")
    # The exact template has already been extracted and qualified with the suite.
    suite_receipt = receipt(ev, args.suite_receipt, "suite_receipt")
    template_receipt = receipt(ev, args.template_receipt, "template_receipt")
    template_path = output_named(template_receipt, "/chat_template.jinja")
    require(sha(template_path) == parity["chat_template_sha256"] and
            suite_receipt["source_sha256"].get(relative(template_path)) == sha(template_path),
            "qualified template differs from frozen suite input")
    require((checkpoint_dir / "tokenizer.json").is_file() and
            sha(checkpoint_dir / "tokenizer.json") == parity["tokenizer_sha256"],
            "suite tokenizer differs from model")
    destination = ROOT / "tests/data/prepared" / ev.path.name
    destination.mkdir(parents=True, exist_ok=False)
    tensor_layout = write_json(destination / "tensor_layout.json", {
        "model_revision": revision, "tied_output_embedding": True,
        "tensors": {name: {"shape": item["shape"], "checkpoint_path": relative(checkpoint_path)}
                    for name, item in header.tensors.items()}})
    streams = {}
    for mode in ("bf16", "fp16"):
        streams[mode] = {
            "weights": descriptor(native_root / mode / "weights.bin"),
            "layout": descriptor(native_root / mode / "layout.json"),
            "checkpoint_sha256": checkpoint_hashes, "encoding": mode,
            "rounding": "nearest-even",
            "recipe": "Complete IEEE nearest-even conversion of original checkpoint tensors; "
                      "no activation quantization or matrix replacement",
            "tool_version": version_text}
    recipe = load_json(awq_root / "recipe.json")
    streams["w4a16"] = {
        "weights": descriptor(awq_root / "weights.bin"),
        "layout": descriptor(awq_root / "layout.json"),
        "scales": descriptor(awq_root / "scales.bin"),
        "zeros": descriptor(awq_root / "zeros.bin"),
        "calibration": recipe["calibration"], "checkpoint_sha256": checkpoint_hashes,
        "bits": 4, "group_size": GROUP, "nibble_order": list(NIBBLE_ORDER),
        "recipe": RECIPE + "; full algorithm and per-matrix search results in recipe_artifact",
        "recipe_artifact": descriptor(awq_root / "recipe.json"),
        "tool_version": json.dumps(recipe["tool_version"], sort_keys=True)}
    model = {
        "schema": 1, "model": MODEL, "revision": revision,
        "dimensions": DIMENSIONS, "rope_theta": 1000000, "rms_norm_eps": 1e-6,
        "checkpoint": [descriptor(checkpoint_path)],
        "config": descriptor(checkpoint_dir / "config.json"),
        "tokenizer": descriptor(checkpoint_dir / "tokenizer.json"),
        "chat_template": descriptor(template_path), "tensor_layout": tensor_layout,
        "streams": streams,
        "preparation_receipts": {key: value for key, value in ev.receipt.items()
                                 if key.endswith("_receipt") and isinstance(value, dict)}}
    validator = Validator(ROOT, ev)
    validator.model(model)
    require(len(validator.suite(parity, model)) == 50, "incomplete genuine suite")
    candidate = write_json(destination / "model_manifest.json", model)
    manifest = ROOT / "tests/data/model_manifest.json"
    require(not manifest.exists(), "refusing to overwrite an existing model manifest")
    write_json(manifest, model)
    ev.receipt["outputs"] = {relative(path): sha(path) for path in destination.iterdir()}
    ev.receipt["outputs"][relative(manifest)] = sha(manifest)
    ev.receipt["scope"] = (
        "Genuine complete checkpoint/native/AWQ input manifest and unmodified model/suite validation. "
        "No placeholder result manifest, full-model execution, hardware result or acceptance.")
    return ev.assertion("genuine_three_mode_input_manifest_validated", True,
                        model_manifest=candidate, cases=50, tensors=len(header.tensors))


def worker(args):
    if args.phase == "inputs":
        input_worker(args.checkpoint_dir, args.train, args.destination)
    elif args.phase == "qualify-inputs":
        qualify_inputs(args.destination, args.checkpoint_dir)
    elif args.phase == "calibration":
        capture_worker(args.checkpoint_dir, args.inputs, args.destination)
    elif args.phase == "quantize":
        quantize_worker(args.checkpoint_dir, args.calibration, args.destination, args.revision)
    elif args.phase == "validate":
        validate_worker(args.checkpoint_dir, args.streams_dir, args.destination)
    elif args.phase == "reference":
        reference_worker(args.checkpoint_dir, args.streams_dir, args.destination)
    else:
        raise ValueError("unsupported worker phase")


def run_phase(ev, args):
    checkpoint_dir, revision = checkpoint_input(ev, args.acquisition_receipt)
    if args.phase == "model-manifest":
        numerics()
        return model_manifest(ev, args, checkpoint_dir, revision)
    input_phase = args.phase in ("inputs", "qualify-inputs")
    interpreter = args.input_python if input_phase else sys.executable
    version_script = ("import jinja2,sys; print(sys.version); print(jinja2.__version__)"
                      if input_phase else
                      "import numpy,sys; print(sys.version); print(numpy.__version__)")
    require(ev.run("awq-dependency-version", [interpreter, "-c", version_script], timeout=30),
            "selected preparation dependency failed")
    destination = (ev.path / "reference-outputs" if args.phase == "reference" else
                   ROOT / "tests/data" / (
                       "streams" if args.phase == "quantize" else "calibration") / ev.path.name)
    command = [interpreter, "tests/awq_prepare.py", "--worker", "--phase", args.phase,
               "--checkpoint-dir", relative(checkpoint_dir), "--destination", relative(destination)]
    if args.phase == "inputs":
        if args.training_receipt is not None:
            retained = load_json(ROOT / args.training_receipt)
            ev.receipt["training_receipt"] = descriptor(ROOT / args.training_receipt)
            matches = [row for row in retained["retrievals"]
                       if row["url"].endswith("/grade_school_math/data/train.jsonl")]
            require(len(matches) == 1 and matches[0]["complete"], "missing retained training data")
            train = checked_payload(ev, matches[0])
            ev.receipt["retrievals"] = matches
        else:
            train = ROOT / "tests/data/acquired" / ev.path.name / "gsm8k-train.jsonl"
            train.parent.mkdir(parents=True, exist_ok=False)
            url = ("https://raw.githubusercontent.com/openai/grade-school-math/"
                   "3101c7d5072418e28b9008a6636bde82a006892c/grade_school_math/data/train.jsonl")
            require(ev.run("curl-version", ["curl", "--version"], timeout=30), "curl unavailable")
            require(fetch(ev, "pinned-gsm8k-train", url, train, allowance=3600) is not None,
                    "calibration train acquisition failed")
        command += ["--train", relative(train)]
    elif args.phase == "calibration":
        inputs = receipt(ev, args.inputs_receipt, "inputs_receipt")
        command += ["--inputs", relative(output_named(inputs, "/calibration_inputs.json"))]
    elif args.phase == "quantize":
        previous = receipt(ev, args.calibration_receipt, "calibration_receipt")
        command += ["--calibration", relative(output_named(previous, "/calibration.json")),
                    "--revision", revision]
    elif args.phase in ("validate", "reference"):
        previous = receipt(ev, args.streams_receipt, "streams_receipt")
        command += ["--streams-dir", relative(output_named(previous, "/layout.json").parent)]
        if args.phase == "reference":
            validated = receipt(ev, args.validation_receipt, "validation_receipt")
            require(validated["streams_receipt"] == descriptor(ROOT / args.streams_receipt),
                    "reference requires successful validation of these actual streams")
    else:
        raise ValueError("unsupported preparation phase")
    ok = ev.run("awq-" + args.phase, command, timeout=86400)
    if ok and args.phase == "inputs":
        ok = ev.run("calibration-independent-unicode", [
            "perl", "tests/tokenizer_reference.pl", relative(destination / "unicode_request.json"),
            relative(destination / "perl_unicode_reference.json")], timeout=3600)
        if ok:
            qualify = command[:]
            qualify[qualify.index("inputs")] = "qualify-inputs"
            ok = ev.run("calibration-tokenizer-qualification", qualify, timeout=3600)
    if ok and args.phase == "validate":
        executable = ev.path / "parent-dequant.vvp"
        ok = ev.run("parent-dequant-compile", [
            "iverilog", "-g2012", "-Wall", "-s", "awq_dequant_tb", "-o", relative(executable),
            "anvil_q1_reference/rtl/anvil_q1_awq_dequant.sv", "tests/awq_dequant_tb.sv"])
        if ok:
            ok = ev.run("parent-dequant-behavior", [
                "vvp", relative(executable),
                "+INPUT=" + relative(destination / "dequant_vectors.txt")], timeout=3600)
    ev.receipt["outputs"] = {
        relative(path): sha(path) for path in sorted(destination.rglob("*")) if path.is_file()}
    ev.receipt["scope"] = (
        "Activation-calibrated AWQ input/stream preparation and read-only parent dequant validation. "
        "No integrated full-model DUT run, benchmark score, hardware access or acceptance is claimed.")
    return ev.assertion("awq_" + args.phase + "_completed", ok)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("inputs", "qualify-inputs", "calibration",
                                           "quantize", "validate", "reference", "model-manifest"),
                        required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--input-python", default="python3")
    for name in ("acquisition-receipt", "inputs-receipt", "calibration-receipt", "streams-receipt",
                 "checkpoint-dir", "destination", "train", "inputs", "calibration", "streams-dir",
                 "repair-of", "training-receipt", "native-receipt", "validation-receipt",
                 "suite-receipt", "template-receipt"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--revision")
    args = parser.parse_args()
    for key, value in vars(args).items():
        if isinstance(value, Path):
            require(not value.is_absolute() and ".." not in value.parts, "nonportable path: " + key)
    if args.worker:
        for key, value in vars(args).items():
            if isinstance(value, Path):
                value = (ROOT / value).resolve()
                require(value.is_relative_to(ROOT), "worker argument escapes project")
                setattr(args, key, value)
        if args.phase not in ("inputs", "qualify-inputs"):
            numerics()
        worker(args)
        return 0
    ev = Evidence("awq-" + args.phase)
    ok = False
    try:
        if args.repair_of is not None:
            ev.receipt["repair_of"] = descriptor(ROOT / args.repair_of)
        ok = run_phase(ev, args)
    except (ValueError, KeyError, OSError) as error:
        ev.assertion("awq_preparation_exception", False, error=repr(error))
    finally:
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"], "receipt": relative(ev.path / "receipt.json")}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
