#!/usr/bin/env python3
"""Streaming ordered floating-point Qwen reference, independent of RTL helpers."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmarks import digest, portable_path, require, validate_asset

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = ("tests/official_reference.py", "tests/official_reference_tests.py",
                  "tests/reference.py", "tests/benchmarks.py")


def bits32(values):
    return np.asarray(values, dtype="<f4").view("<u4")


def expand(words, half=False):
    words = np.asarray(words, dtype="<u2")
    if half:
        return words.view("<f2").astype("<f4")
    return (words.astype("<u4") << np.uint32(16)).view("<f4")


def narrow(values, half=False):
    """FP32 -> native RNE, canonicalizing NaNs but retaining signed zero."""
    values = np.asarray(values, dtype="<f4")
    raw = bits32(values)
    if half:
        with np.errstate(over="ignore", invalid="ignore"):
            result = values.astype("<f2").view("<u2")
        return np.where(np.isnan(values), 0x7e00, result).astype("<u2")
    rounded = ((raw.astype("<u8") + np.uint64(0x7fff) +
                ((raw.astype("<u8") >> np.uint64(16)) & np.uint64(1))) >>
               np.uint64(16)).astype("<u2")
    return np.where(np.isnan(values), 0x7fc0, rounded).astype("<u2")


def boundary(values, half=False):
    result = expand(narrow(values, half), half)
    require(bool(np.all(np.isfinite(result))), "nonfinite native activation boundary")
    return result


def plus(a, b):
    with np.errstate(over="ignore", invalid="ignore"):
        result = np.add(a, b, dtype=np.float32)
    return np.where(np.isnan(result), np.float32(np.nan), result).astype("<f4")


def times(a, b):
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        result = np.multiply(a, b, dtype=np.float32)
    return np.where(np.isnan(result), np.float32(np.nan), result).astype("<f4")


def statistic(values):
    """Adjacent binary-carry pairs; occupied final partials fold low to high."""
    values = np.asarray(values, dtype="<f4")
    require(values.shape[-1] > 0, "empty statistic")
    partials = []
    while values.shape[-1]:
        if values.shape[-1] & 1:
            partials.append(values[..., -1])
        values = plus(values[..., :values.shape[-1]//2*2:2],
                      values[..., 1:values.shape[-1]//2*2:2])
    total = np.zeros_like(partials[0])
    for partial in partials:
        total = plus(total, partial)
    return total


def ordered_rows(weights, activation, bias=None):
    """128 adjacent products per tile, increasing tile accumulation, then bias."""
    rows, columns = weights.shape
    require(activation.shape == (columns,), "projection shape mismatch")
    padded = ((columns + 127) // 128) * 128
    product = np.zeros((rows, padded), dtype="<f4")
    product[:, :columns] = times(weights, activation)
    product = product.reshape(rows, -1, 128)
    while product.shape[-1] > 1:
        product = plus(product[..., ::2], product[..., 1::2])
    tiles = plus(product[..., 0], np.float32(0))
    result = tiles[:, 0]
    for tile in range(1, tiles.shape[1]):
        result = plus(result, tiles[:, tile])
    return plus(result, np.float32(0) if bias is None else bias)


def dequantized(codes, zeros, scales):
    differences = codes.astype("int16") - zeros.astype("int16")
    return boundary(times(differences.astype("<f4"), expand(scales)))


def cache_block(values, int8):
    """Selected native -> BF16 -> native cache bytes and BF16 reconstruction."""
    words = narrow(values)
    require(bool(np.all((words & 0x7f80) != 0x7f80)), "nonfinite cache input")
    values = expand(words)
    if not int8:
        return words.tobytes(), values
    maximum = np.max(np.abs(values).astype("float64"))
    # Binary64 division followed by FP32 could double-round a BF16 scale.
    # At this boundary use direct significand rounding on the binary64 ratio.
    ratio = maximum / 127 if maximum else 1.0
    _, exponent = np.frexp(ratio)
    quantum = max(int(exponent) - 8, -133)
    scale_value = np.ldexp(np.rint(np.ldexp(ratio, -quantum)), quantum)
    scale = max(1, int(narrow(np.float32(scale_value))))
    s = float(expand(np.uint16(scale)))
    codes = np.clip(np.rint(values.astype("float64") / s), -127, 127).astype("int8")
    reconstructed = boundary(times(codes.astype("<f4"), np.float32(s)))
    return np.asarray(scale, dtype="<u2").tobytes() + codes.tobytes(), reconstructed


def summaries(values):
    x = np.asarray(values, dtype="<f4")
    require(x.size > 0 and bool(np.all(np.isfinite(x))), "invalid numerical summary")
    wide = x.astype("float64")
    return {"count": int(x.size), "sha256_fp32_le": hashlib.sha256(x.tobytes()).hexdigest(),
            "min": float(wide.min()), "max": float(wide.max()),
            "mean": float(wide.mean()), "rms": float(np.sqrt(np.mean(wide * wide))),
            "first_values": [float(v) for v in x.ravel()[:8]]}


class Checkpoint:
    def __init__(self, mode):
        from official_reference_tests import Audit
        self.audit = Audit()
        require(mode in ("bf16", "fp16", "w4", "w2"), "unsupported reference mode")
        self.mode, self.half = mode, mode == "fp16"
        self.manifest = json.loads((ROOT / "tests/benchmark_manifest.json").read_text())
        self.source = validate_asset(ROOT, self.manifest["checkpoint_shards"][0])
        self.config = json.loads(validate_asset(ROOT, self.manifest["assets"]["config"]).read_text())
        with self.source.open("rb") as stream:
            size = int.from_bytes(stream.read(8), "little")
            require(0 < size <= 16 * 1024 * 1024, "invalid checkpoint header length")
            self.tensors = json.loads(stream.read(size))
        self.base = 8 + size
        self.inputs = [self.manifest["checkpoint_shards"][0], self.manifest["assets"]["config"]]
        c = self.config
        require(c["num_hidden_layers"] == 28 and c["hidden_size"] == 1536 and
                c["hidden_act"] == "silu" and c["tie_word_embeddings"] and
                not c["use_sliding_window"] and not c.get("rope_scaling"),
                "unsupported official model configuration")
        require(c["num_attention_heads"] % c["num_key_value_heads"] == 0,
                "nonintegral GQA ratio")
        self.data = np.memmap(self.source, mode="r", dtype="uint8")
        self.quantized = {}
        self.qfiles = {}
        if mode in ("w4", "w2"):
            bindings = self.manifest["quantized_weight_inputs"]
            require(len(bindings) == 7, "incomplete quantized bindings")
            for binding in bindings:
                path = validate_asset(ROOT, binding)
                self.inputs.append(binding)
                if path.name == "manifest.json":
                    image = json.loads(path.read_text())
                else:
                    self.qfiles[path.name] = np.memmap(path, mode="r", dtype="uint8")
            require(image["source"] == self.manifest["checkpoint_shards"][0] and
                    image["config"] == self.manifest["assets"]["config"],
                    "quantized source/configuration mismatch")
            self.group = image["group_size"]
            self.quantized = {e["source_tensor"]: e for e in image["tensors"]
                              if e["bits"] == int(mode[1])}

    def native(self, name, start=None, end=None):
        tensor = self.tensors[name]
        require(tensor["dtype"] == "BF16", f"{name}: not BF16")
        offset, limit = tensor["data_offsets"]
        shape = tensor["shape"]
        require(limit-offset == 2 * int(np.prod(shape)) and self.base+limit <= self.data.size,
                f"{name}: invalid tensor extent")
        words = self.data[self.base+offset:self.base+limit].view("<u2").reshape(shape)
        if start is not None:
            words = words[start:end]
        return boundary(expand(words), self.half)

    def rows(self, name, start, end):
        if not self.quantized:
            return self.native(name, start, end)
        e = self.quantized[name]
        width, columns = e["bits"], e["columns"]
        fields = 8 // width

        def part(role):
            entry = e[role]
            offset, stride = entry["offset"], entry["stride"]
            return self.qfiles[entry["file"]][offset+start*stride:offset+end*stride].reshape(
                end-start, stride)

        def unpack(raw, count):
            shifts = np.arange(fields, dtype="uint8") * width
            return ((raw[..., None] >> shifts) & ((1 << width)-1)).reshape(
                end-start, -1)[:, :count]

        q = unpack(part("payload"), columns)
        z = unpack(part("zeros"), columns // self.group)
        s = part("scales").copy().view("<u2")
        values = dequantized(q.reshape(end-start, -1, self.group),
                             z[..., None], s[..., None])
        return values.reshape(end-start, columns)

    def projection(self, x, name, bias=None):
        rows = self.tensors[name]["shape"][0]
        result = np.empty(rows, dtype="<f4")
        for start in range(0, rows, 64):
            end = min(start+64, rows)
            result[start:end] = ordered_rows(self.rows(name, start, end), x,
                                            None if bias is None else bias[start:end])
            if start == 0:
                self.audit.projection(x, self.rows(name, start, end), result[start:end],
                                      self.half, bool(self.quantized),
                                      None if bias is None else bias[start:end], name)
        require(bool(np.all(np.isfinite(result))), f"{name}: arithmetic overflow/invalid")
        return result


class Model:
    def __init__(self, checkpoint, kv="bf16", cache_size=128):
        self.weights, self.c = checkpoint, checkpoint.config
        require(kv in ("bf16", "int8"), "invalid KV mode")
        self.half, self.int8 = checkpoint.half, kv == "int8"
        self.dim = self.c["hidden_size"] // self.c["num_attention_heads"]
        require(cache_size in (1, 2, 4, 8, 16, 32, 64, 128) and self.dim % cache_size == 0,
                "invalid CACHE_BLOCK")
        self.block = cache_size
        self.history = [[] for _ in range(self.c["num_hidden_layers"])]
        self.last_softmax_error = 0.0

    def bound(self, x):
        return boundary(x, self.half)

    def norm(self, x, name):
        total = statistic(times(x, x))
        mean = times(total, np.float32(1 / x.size))
        inv = np.float32(1 / np.sqrt(float(plus(mean, np.float32(self.c["rms_norm_eps"])))))
        self.weights.audit.normalizer(x, inv, self.c["rms_norm_eps"])
        return self.bound(times(times(x, inv), self.weights.native(name)))

    def rope(self, values, position):
        exponent = np.arange(self.dim//2, dtype="float64") * (-2/self.dim)
        angles = position * np.power(float(self.c["rope_theta"]), exponent)
        cosine = self.bound(np.cos(angles).astype("<f4"))
        sine = self.bound(np.sin(angles).astype("<f4"))
        self.weights.audit.rope(position, self.c["rope_theta"], self.dim, cosine, sine, self.half)
        x = values.reshape(-1, self.dim)
        lo, hi = x[:, :self.dim//2], x[:, self.dim//2:]
        return self.bound(np.concatenate((plus(times(lo, cosine), -times(hi, sine)),
                                         plus(times(hi, cosine), times(lo, sine))), axis=1))

    def cache(self, values):
        flat = values.ravel()
        decoded, records = [], []
        for start in range(0, flat.size, self.block):
            record, words = cache_block(flat[start:start+self.block], self.int8)
            self.weights.audit.cache(flat[start:start+self.block], self.int8, record, words)
            records.append(record)
            decoded.append(words)
        return np.concatenate(decoded).reshape(values.shape), b"".join(records)

    def attention(self, query, history):
        keys = np.stack([r[0] for r in history])
        values = np.stack([r[1] for r in history])
        contexts = []
        ratio = self.c["num_attention_heads"] // self.c["num_key_value_heads"]
        for head, q in enumerate(query):
            kv_head = head // ratio
            # Attention's contract is increasing-component non-fused accumulation.
            score = np.zeros(len(history), dtype="<f4")
            for component in range(self.dim):
                score = plus(score, times(q[component], keys[:, kv_head, component]))
            score = times(score, np.float32(1 / np.sqrt(self.dim)))
            exp = np.exp(plus(score, -np.max(score)).astype("float64")).astype("<f4")
            self.weights.audit.nonlinear(4, plus(score, -np.max(score)), exp)
            probability = times(exp, np.float32(1 / float(statistic(exp))))
            self.last_softmax_error = max(self.last_softmax_error,
                                          abs(float(probability.astype("float64").sum())-1))
            require(self.last_softmax_error <= 2e-4, "softmax row sum error")
            context = np.zeros(self.dim, dtype="<f4")
            for index in range(len(history)):
                context = plus(context, times(probability[index], values[index, kv_head]))
            contexts.append(context)
        return self.bound(np.concatenate(contexts))

    def infer(self, token, position, observe):
        require(0 <= token < self.c["vocab_size"] and
                0 <= position < self.c["max_position_embeddings"], "invalid token/position")
        require(all(len(h) == position for h in self.history), "nonconsecutive reference sequence")
        x = self.weights.native("model.embed_tokens.weight", token, token+1)[0]
        staged = []
        for layer in range(self.c["num_hidden_layers"]):
            p = f"model.layers.{layer}."
            n = self.norm(x, p+"input_layernorm.weight")
            projections = [self.bound(self.weights.projection(
                n, p+f"self_attn.{role}_proj.weight",
                self.weights.native(p+f"self_attn.{role}_proj.bias"))) for role in ("q", "k", "v")]
            q = self.rope(projections[0], position)
            k, kb = self.cache(self.rope(projections[1], position))
            v, vb = self.cache(projections[2].reshape(-1, self.dim))
            record = (k, v, kb+vb)
            context = self.attention(q, self.history[layer] + [record])
            output = self.bound(self.weights.projection(context, p+"self_attn.o_proj.weight"))
            x = self.bound(plus(x, output))
            n = self.norm(x, p+"post_attention_layernorm.weight")
            gate, up = [self.bound(self.weights.projection(n, p+f"mlp.{role}_proj.weight"))
                        for role in ("gate", "up")]
            sigmoid = (1 / (1 + np.exp(-gate.astype("float64")))).astype("<f4")
            self.weights.audit.nonlinear(5, gate, sigmoid)
            activated = self.bound(times(times(gate, sigmoid), up))
            down = self.bound(self.weights.projection(activated, p+"mlp.down_proj.weight"))
            x = self.bound(plus(x, down))
            staged.append(record)
            observe(layer, x, record)
        logits = self.weights.projection(
            self.norm(x, "model.norm.weight"), "model.embed_tokens.weight")
        # Publish only after all layers and final projection succeeded.
        for history, record in zip(self.history, staged):
            history.append(record)
        return logits


def smoke(args):
    checkpoint = Checkpoint(args.mode)
    model = Model(checkpoint, args.kv, args.cache_block)
    output = portable_path(ROOT, args.output)
    output.mkdir(parents=True, exist_ok=False)
    records = []
    with (output / "layers.jsonl").open("x") as stream:
        for position in range(len(args.tokens) + args.decode):
            token = args.tokens[position] if position < len(args.tokens) else records[-1]["greedy_id"]
            phase = "prefill" if position < len(args.tokens) else "decode"
            started = time.monotonic()

            def observe(layer, activation, record):
                item = {"position": position, "phase": phase, "input_id": token,
                        "layer": layer, "activation": summaries(activation),
                        "key": summaries(record[0]), "value": summaries(record[1]),
                        "kv_bytes": len(record[2]),
                        "kv_sha256": hashlib.sha256(record[2]).hexdigest()}
                stream.write(json.dumps(item, allow_nan=False) + "\n")
                if layer % 7 == 6:
                    stream.flush()
                    print(f"reference {args.mode}/{args.kv} position={position} layer={layer}",
                          flush=True)

            logits = model.infer(token, position, observe)
            greedy = int(np.argmax(logits))
            # Retain small usable numerical outputs, not the whole model's intermediates.
            np.save(output / f"logits-{position}.npy", logits, allow_pickle=False)
            records.append({"position": position, "phase": phase, "input_id": token,
                            "greedy_id": greedy, "logits": summaries(logits),
                            "elapsed_reference_seconds": time.monotonic()-started})
    result = {"schema": 1, "kind": "software-reference-only", "mode": args.mode, "kv": args.kv,
              "cache_block": args.cache_block, "inputs": checkpoint.inputs,
              "implementation_sha256": {p: digest(ROOT / p) for p in IMPLEMENTATION},
              "tokens": records, "layers_executed": len(records)*checkpoint.config["num_hidden_layers"],
              "max_softmax_sum_error": model.last_softmax_error,
              "numerical_audit": checkpoint.audit.summary(),
              "limits": "Bounded sequential official reference execution, not RTL fidelity, "
                        "speculative-tree, corpus, performance, timing or hardware acceptance."}
    (output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps(result, allow_nan=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "smoke", "_check", "_smoke"))
    parser.add_argument("--mode", choices=("bf16", "fp16", "w4", "w2"), default="bf16")
    parser.add_argument("--kv", choices=("bf16", "int8"), default="bf16")
    parser.add_argument("--cache-block", type=int, default=128)
    parser.add_argument("--tokens", type=int, nargs="+", default=[151644, 8948])
    parser.add_argument("--decode", type=int, default=1)
    parser.add_argument("--output")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    require(args.decode >= 1 and len(args.tokens) >= 2, "smoke needs prefill and greedy decode")
    if args.command == "_check":
        from official_reference_tests import execute
        execute()
        return 0
    if args.command == "_smoke":
        smoke(args)
        return 0
    from verify import Run
    run = Run("official-reference-"+args.command, preparation=True, repair_of=args.repair_of)
    run.receipt["argv"] = ["python3", "tests/official_reference.py", *sys.argv[1:]]
    run.save()
    try:
        run.tool("python3")
        run.command(["python3", "-c", "import numpy; print('numpy', numpy.__version__)"],
                    "numpy-version")
        run.command(["python3", "tests/official_reference.py", "_check"],
                    "exact-numerical-and-corruption-controls")
        if args.command == "smoke":
            output = args.output or run.relative(run.path / "reference-output")
            run.command(["python3", "tests/official_reference.py", "_smoke",
                         "--mode", args.mode, "--kv", args.kv, "--cache-block", str(args.cache_block),
                         "--tokens", *map(str, args.tokens), "--decode", str(args.decode),
                         "--output", output], "official-prefill-decode")
            result = json.loads((portable_path(ROOT, output) / "result.json").read_text())
            run.receipt["reference_execution"] = result
            run.receipt["asset_hashes"] = {b["path"]: b["sha256"] for b in result["inputs"]}
        return run.finish(True, "Independent software reference controls/execution completed; "
                          "not accelerator or benchmark acceptance")
    except Exception as exc:
        return run.finish(False, f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
