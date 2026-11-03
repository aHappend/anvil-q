#!/usr/bin/env python3
"""Independent NumPy/IEEE-FP64 Qwen2 inference and native stream conversion.

This evaluates decoded checkpoint/native weights, not DUT helper arithmetic.
Inputs are explicit token IDs; this is not a substitute for pinned tokenization,
AWQ calibration, integrated RTL execution or the fifty-case benchmark.
"""

import argparse
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import load_json


DTYPES = {"BF16": np.dtype("<u2"), "F16": np.dtype("<f2"), "F32": np.dtype("<f4")}
PROJECTIONS = {"self_attn.q_proj": 0, "self_attn.k_proj": 1,
               "self_attn.v_proj": 2, "self_attn.o_proj": 3,
               "mlp.gate_proj": 4, "mlp.up_proj": 5, "mlp.down_proj": 6}


def decode(values, encoding):
    if encoding == "BF16":
        return (np.asarray(values, dtype="<u2").astype("<u4") << 16).view("<f4").astype("<f8")
    return np.asarray(values).astype("<f8")


def encode(values, mode):
    if mode == "fp16":
        with np.errstate(over="raise", invalid="raise"):
            return np.asarray(values).astype("<f2")
    if mode != "bf16":
        raise ValueError("conversion mode must be bf16 or fp16")
    f32 = np.asarray(values, dtype="<f4")
    bits = f32.view("<u4")
    rounded = (bits + np.uint32(0x7fff) + ((bits >> 16) & 1)) >> 16
    return np.where(np.isnan(f32), 0x7fc0, rounded).astype("<u2")


class SafeTensors:
    def __init__(self, path):
        self.path = Path(path)
        with self.path.open("rb") as source:
            prefix = source.read(8)
            if len(prefix) != 8:
                raise ValueError("missing safetensors header")
            length, = struct.unpack("<Q", prefix)
            if length > 100 * 1024 * 1024 or length + 8 > self.path.stat().st_size:
                raise ValueError("invalid safetensors header size")
            self.header = json.loads(source.read(length))
        self.start = length + 8
        self.tensors = {name: item for name, item in self.header.items() if name != "__metadata__"}
        intervals = []
        for name, item in self.tensors.items():
            dtype = DTYPES[item["dtype"]]
            shape, (low, high) = item["shape"], item["data_offsets"]
            if (not shape or any(type(x) is not int or x <= 0 for x in shape) or
                    low < 0 or high - low != math.prod(shape) * dtype.itemsize or
                    self.start + high > self.path.stat().st_size):
                raise ValueError("invalid tensor bounds: " + name)
            intervals.append((low, high))
        ordered = sorted(intervals)
        if any(a[1] != b[0] for a, b in zip(ordered, ordered[1:])) or (
                ordered and (ordered[0][0] != 0 or
                             ordered[-1][1] + self.start != self.path.stat().st_size)):
            raise ValueError("overlapping, incomplete or trailing safetensors data")

    def get(self, name):
        item = self.tensors[name]
        return np.memmap(self.path, dtype=DTYPES[item["dtype"]], mode="r",
                         offset=self.start + item["data_offsets"][0], shape=tuple(item["shape"]))

    def weight(self, name, mode="checkpoint"):
        values = self.get(name)
        encoding = self.tensors[name]["dtype"]
        decoded = decode(values, encoding)
        if not np.isfinite(decoded).all():
            raise ValueError("nonfinite external checkpoint tensor: " + name)
        if mode != "checkpoint":
            decoded = decode(encode(decoded, mode), "BF16" if mode == "bf16" else "F16")
        return decoded


class NativeStream:
    def __init__(self, directory, mode):
        directory = Path(directory)
        layout = load_json(directory / "layout.json")
        if layout["encoding"] != mode or layout["rounding"] != "nearest-even":
            raise ValueError("native stream encoding/rounding mismatch")
        self.path, self.mode = directory / "weights.bin", mode
        self.layout = layout["tensors"]
        self.tensors = {
            name: dict(shape=item["shape"], dtype="BF16" if mode == "bf16" else "F16")
            for name, item in self.layout.items()}
        cursor = 0
        for name in sorted(self.layout):
            item = self.layout[name]
            if item["byte_offset"] != cursor or item["byte_length"] != math.prod(item["shape"]) * 2:
                raise ValueError("native stream tensor coverage mismatch: " + name)
            cursor += item["byte_length"]
        if cursor != self.path.stat().st_size:
            raise ValueError("native stream size mismatch")

    def get(self, name):
        item = self.layout[name]
        return np.memmap(self.path, dtype="<u2" if self.mode == "bf16" else "<f2",
                         mode="r", offset=item["byte_offset"], shape=tuple(item["shape"]))

    def weight(self, name, mode):
        if mode != self.mode:
            raise ValueError("reference requested another stream precision")
        values = decode(self.get(name), self.tensors[name]["dtype"])
        if not np.isfinite(values).all():
            raise ValueError("nonfinite external stream tensor: " + name)
        return values


def validate_config(config, tensors):
    expected = dict(num_hidden_layers=24, hidden_size=896, intermediate_size=4864,
                    num_attention_heads=14, num_key_value_heads=2, vocab_size=151936,
                    rope_theta=1000000, rms_norm_eps=1e-6, tie_word_embeddings=True)
    for key, value in expected.items():
        if config[key] != value:
            raise ValueError("wrong production checkpoint configuration: " + key)
    required = {"model.embed_tokens.weight": [151936, 896],
                "model.norm.weight": [896]}
    for layer in range(24):
        p = f"model.layers.{layer}."
        for sub, shape in {
            "input_layernorm.weight": [896], "post_attention_layernorm.weight": [896],
            "self_attn.q_proj.weight": [896, 896],
            "self_attn.k_proj.weight": [128, 896], "self_attn.v_proj.weight": [128, 896],
            "self_attn.o_proj.weight": [896, 896], "self_attn.q_proj.bias": [896],
            "self_attn.k_proj.bias": [128], "self_attn.v_proj.bias": [128],
            "mlp.gate_proj.weight": [4864, 896], "mlp.up_proj.weight": [4864, 896],
            "mlp.down_proj.weight": [896, 4864],
        }.items():
            required[p + sub] = shape
    if set(required) != set(tensors):
        raise ValueError("checkpoint tensor inventory differs from tied Qwen2 model")
    for name, shape in required.items():
        if tensors[name]["shape"] != shape:
            raise ValueError("checkpoint tensor shape differs: " + name)


def rmsnorm(x, gamma, epsilon):
    return x * gamma / np.sqrt(np.mean(x * x, dtype=np.float64) + epsilon)


def rope(x, position, theta):
    half = x.shape[-1] // 2
    angles = position * theta ** (-np.arange(half, dtype=np.float64) / half)
    c, s = np.cos(angles), np.sin(angles)
    return np.concatenate((x[..., :half] * c - x[..., half:] * s,
                           x[..., half:] * c + x[..., :half] * s), axis=-1)


def attention(q, keys, values):
    # Explicit group expansion is mathematical indexing, not the DUT's counters.
    grouping = q.shape[0] // keys.shape[1]
    scores = np.einsum("hd,thd->ht", q, np.repeat(keys, grouping, axis=1)) / np.sqrt(q.shape[1])
    exponentials = np.exp(scores - scores.max(axis=1, keepdims=True))
    probabilities = exponentials / exponentials.sum(axis=1, keepdims=True)
    return np.einsum("ht,thd->hd", probabilities, np.repeat(values, grouping, axis=1))


def silu(x):
    # Both branches avoid overflow without clipping the mathematical sigmoid.
    exp_negative_abs = np.exp(-np.abs(x))
    sigmoid = np.where(x >= 0, 1 / (1 + exp_negative_abs),
                       exp_negative_abs / (1 + exp_negative_abs))
    return x * sigmoid


class QwenFP64:
    def __init__(self, config, checkpoint, mode):
        validate_config(config, checkpoint.tensors)
        if mode not in ("checkpoint", "bf16", "fp16", "w4a16"):
            raise ValueError("AWQ requires an actual independently calibrated stream")
        if mode == "w4a16" and not callable(getattr(checkpoint, "decode_rows", None)):
            raise ValueError("AWQ requires an actual decoded compatibility stream")
        self.config, self.checkpoint, self.mode = config, checkpoint, mode
        self.keys, self.values = [[] for _ in range(24)], [[] for _ in range(24)]
        self.position = 0
        self.epsilon = (config["rms_norm_eps"] if mode in ("checkpoint", "w4a16")
                        else float(np.float32(config["rms_norm_eps"])))

    def weight(self, name):
        return self.checkpoint.weight(name, self.mode)

    def linear(self, x, prefix, bias=False):
        result = self.weight(prefix + ".weight") @ x
        return result + self.weight(prefix + ".bias") if bias else result

    def decoded_rows(self, raw):
        if self.mode == "w4a16":
            return self.checkpoint.decode_rows(raw)
        dtype = self.checkpoint.tensors["model.embed_tokens.weight"]["dtype"]
        values = decode(raw, dtype)
        if self.mode != "checkpoint":
            values = decode(encode(values, self.mode), "BF16" if self.mode == "bf16" else "F16")
        return values

    def step(self, token):
        if type(token) is not int or not 0 <= token < self.config["vocab_size"]:
            raise ValueError("invalid reference token")
        if self.position >= self.config["max_position_embeddings"]:
            raise ValueError("reference context exceeds maximum sequence length")
        embedding = self.checkpoint.get("model.embed_tokens.weight")[token]
        x = self.decoded_rows(embedding)
        layers = []
        for layer in range(24):
            p = f"model.layers.{layer}."
            normalized = rmsnorm(x, self.weight(p + "input_layernorm.weight"), self.epsilon)
            q = self.linear(normalized, p + "self_attn.q_proj", True).reshape(14, 64)
            k = self.linear(normalized, p + "self_attn.k_proj", True).reshape(2, 64)
            v = self.linear(normalized, p + "self_attn.v_proj", True).reshape(2, 64)
            q, k = (rope(t, self.position, self.config["rope_theta"]) for t in (q, k))
            self.keys[layer].append(k)
            self.values[layer].append(v)
            context = attention(q, np.asarray(self.keys[layer]), np.asarray(self.values[layer]))
            x = x + self.linear(context.reshape(896), p + "self_attn.o_proj")
            normalized = rmsnorm(x, self.weight(p + "post_attention_layernorm.weight"), self.epsilon)
            gate = self.linear(normalized, p + "mlp.gate_proj")
            up = self.linear(normalized, p + "mlp.up_proj")
            x = x + self.linear(silu(gate) * up, p + "mlp.down_proj")
            if not np.isfinite(x).all():
                raise ValueError("nonfinite FP64 layer output")
            layers.append(x.copy())
        final = rmsnorm(x, self.weight("model.norm.weight"), self.epsilon)
        # Chunk the vocabulary so FP64 embeddings need not occupy another GB.
        raw = self.checkpoint.get("model.embed_tokens.weight")
        logits = np.empty(151936, dtype="<f8")
        for start in range(0, len(raw), 1024):
            rows = self.decoded_rows(raw[start:start + 1024])
            logits[start:start + len(rows)] = rows @ final
        if not np.isfinite(logits).all():
            raise ValueError("nonfinite FP64 logits")
        self.position += 1
        return np.asarray(layers, dtype="<f8"), logits


def request_layout(name, shape):
    if name == "model.embed_tokens.weight":
        return dict(kind=0, address="row=token,col=component")
    if name == "model.norm.weight":
        return dict(kind=7, address="layer=0,row=0,col=component")
    parts = name.split(".")
    layer, suffix = int(parts[2]), ".".join(parts[3:])
    if suffix == "input_layernorm.weight":
        return dict(kind=5, layer=layer, address="row=0,col=component")
    if suffix == "post_attention_layernorm.weight":
        return dict(kind=6, layer=layer, address="row=0,col=component")
    operator = suffix.rsplit(".", 1)[0]
    proj = PROJECTIONS[operator]
    return dict(kind=4 if suffix.endswith(".bias") else 12, layer=layer, projection=proj,
                address=("row=0,col=component" if len(shape) == 1 else
                         "row=input,col=output; element_index=col*shape[1]+row"))


def convert(checkpoint, mode, destination, revision):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    layout = dict(schema=1, model_revision=revision, encoding=mode,
                  rounding="nearest-even", tensors={})
    with (destination / "weights.bin").open("xb") as output:
        for name in sorted(checkpoint.tensors):
            item = checkpoint.tensors[name]
            values = checkpoint.get(name)
            begin = output.tell()
            for start in range(0, len(values), 256):
                decoded = decode(values[start:start + 256], item["dtype"])
                if not np.isfinite(decoded).all():
                    raise ValueError("nonfinite external tensor: " + name)
                output.write(encode(decoded, mode).tobytes(order="C"))
            layout["tensors"][name] = dict(
                shape=item["shape"], byte_offset=begin, byte_length=output.tell() - begin,
                **request_layout(name, item["shape"]))
    (destination / "layout.json").write_text(json.dumps(layout, indent=2) + "\n")
    return layout


def selftest():
    encodings = np.arange(65536, dtype="<u2")
    finite_count = 0
    for mode, encoding in (("bf16", "BF16"), ("fp16", "F16")):
        raw = encodings if mode == "bf16" else encodings.view("<f2")
        decoded = decode(raw, encoding)
        finite = np.isfinite(decoded)
        finite_count += int(finite.sum())
        encoded = encode(decoded[finite], mode).view("<u2")
        np.testing.assert_array_equal(encoded, encodings[finite])
    ties = np.array([1 + 2 ** -8, 1 + 3 * 2 ** -8], dtype="<f4")
    np.testing.assert_array_equal(encode(ties, "bf16"), [0x3f80, 0x3f82])
    np.testing.assert_array_equal(encode([1 + 2 ** -11, 1 + 3 * 2 ** -11], "fp16").view("<u2"),
                                  [0x3c00, 0x3c02])
    vector = np.arange(1, 9, dtype=np.float64).reshape(1, 8)
    rotated = rope(vector, 1, 1000000)
    for i in range(4):
        angle = 1000000 ** (-i / 4)
        np.testing.assert_allclose(rotated[0, i],
                                   vector[0, i] * math.cos(angle) - vector[0, i + 4] * math.sin(angle))
    np.testing.assert_array_equal(rope(vector, 0, 1000000), vector)
    q = np.arange(28, dtype=np.float64).reshape(14, 2) / 10
    k = np.arange(12, dtype=np.float64).reshape(3, 2, 2) / 10
    v = k + 1
    actual = attention(q, k, v)
    for head in range(14):
        scores = [sum(q[head, d] * k[t, head // 7, d] for d in range(2)) / math.sqrt(2)
                  for t in range(3)]
        probabilities = [math.exp(s - max(scores)) for s in scores]
        expected = [sum(probabilities[t] * v[t, head // 7, d] for t in range(3)) /
                    sum(probabilities) for d in range(2)]
        np.testing.assert_allclose(actual[head], expected, rtol=1e-14)
    np.testing.assert_allclose(silu(np.array([-1000., 0., 1000.])), [0., 0., 1000.])
    print(json.dumps(dict(scope="reference self-test only", finite_encoding_roundtrips=finite_count,
                          gqa_heads_compared=14, passed=True)))


def prepare(checkpoint_dir, destination, revision):
    checkpoint_dir, destination = Path(checkpoint_dir), Path(destination)
    checkpoint = SafeTensors(checkpoint_dir / "model.safetensors")
    config = load_json(checkpoint_dir / "config.json")
    validate_config(config, checkpoint.tensors)
    destination.mkdir(parents=True, exist_ok=False)
    for mode in ("bf16", "fp16"):
        convert(checkpoint, mode, destination / mode, revision)
    print(json.dumps(dict(scope="complete native weight conversion only",
                          tensor_count=len(checkpoint.tensors), numpy=np.__version__,
                          modes=["bf16", "fp16"])))


def validate_streams(checkpoint, streams_dir):
    random = np.random.default_rng(17)
    comparisons = 0
    for mode in ("bf16", "fp16"):
        stream = NativeStream(Path(streams_dir) / mode, mode)
        if set(stream.tensors) != set(checkpoint.tensors):
            raise ValueError("native stream/checkpoint inventory mismatch")
        for name in sorted(checkpoint.tensors):
            source = checkpoint.get(name).reshape(-1)
            actual = stream.get(name).reshape(-1).view("<u2")
            if stream.tensors[name]["shape"] != checkpoint.tensors[name]["shape"]:
                raise ValueError("native stream/checkpoint shape mismatch")
            if mode == "bf16" and checkpoint.tensors[name]["dtype"] == "BF16":
                np.testing.assert_array_equal(actual, source)
            indices = random.integers(0, len(source), size=min(512, len(source)))
            values = decode(source[indices], checkpoint.tensors[name]["dtype"])
            # Python's binary16 packer is independent of the NumPy conversion path.
            for index, value in zip(indices, values):
                if mode == "fp16":
                    expected, = struct.unpack("<H", struct.pack("<e", float(value)))
                    if int(actual[index]) != expected:
                        raise ValueError("binary16 conversion differs from independent packer")
                comparisons += 1
    return comparisons


def diagnostic(checkpoint_dir, destination, streams_dir):
    checkpoint_dir, destination = Path(checkpoint_dir), Path(destination)
    checkpoint = SafeTensors(checkpoint_dir / "model.safetensors")
    config = load_json(checkpoint_dir / "config.json")
    destination.mkdir(parents=True, exist_ok=False)
    comparisons = validate_streams(checkpoint, streams_dir)
    print(json.dumps(dict(stream_conversion_scalar_comparisons=comparisons,
                          bf16_complete_bit_comparison=True)), flush=True)
    # Explicit actual model tokens, not a standardized benchmark or task score.
    token_ids = [config["bos_token_id"], 17, 53]
    for mode in ("checkpoint", "bf16", "fp16"):
        selected = checkpoint if mode == "checkpoint" else NativeStream(Path(streams_dir) / mode, mode)
        reference = QwenFP64(config, selected, mode)
        for position, token in enumerate(token_ids):
            layers, logits = reference.step(token)
            prefix = destination / f"{mode}-position-{position}"
            layers.astype("<f8").tofile(str(prefix) + "-layers.f64")
            logits.astype("<f8").tofile(str(prefix) + "-logits.f64")
            print(json.dumps(dict(mode=mode, position=position, token=token,
                                  layers=layers.shape[0], logit_count=len(logits),
                                  lowest_id_argmax=int(np.argmax(logits)),
                                  logits_finite=bool(np.isfinite(logits).all()))), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--checkpoint-dir", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--revision")
    parser.add_argument("--streams-dir", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
    elif args.prepare or args.diagnostic:
        if args.checkpoint_dir is None or args.destination is None:
            parser.error("checkpoint-dir and destination are required")
        if args.prepare:
            if not args.revision:
                parser.error("prepare requires revision")
            prepare(args.checkpoint_dir, args.destination, args.revision)
        else:
            if args.streams_dir is None:
                parser.error("diagnostic requires actual selected native streams")
            diagnostic(args.checkpoint_dir, args.destination, args.streams_dir)
    else:
        parser.error("use retained tests/input_prerequisites.py reference probes")


if __name__ == "__main__":
    main()
