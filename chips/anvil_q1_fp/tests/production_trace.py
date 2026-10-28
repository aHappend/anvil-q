#!/usr/bin/env python3
"""Independently replay retained production public-memory transactions.

This diagnostic checks stream contents, acknowledged-write/readback consistency,
causal addresses and request/response ordering. It is not a complete architectural
scoreboard, benchmark completion, timing or hardware evidence.
"""

import argparse
import gzip
import json
import math
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import artifact_path, load_json, require, sha
from verify import Evidence, ROOT


PROJECTIONS = ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
               "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")


def embedding(bits, mode):
    if mode == "bf16":
        return bits << 16
    value, = struct.unpack("<e", struct.pack("<H", bits))
    require(math.isfinite(value), "nonfinite external embedding")
    if mode == "fp16":
        return struct.unpack("<I", struct.pack("<f", value))[0]
    magnitude = math.floor(abs(value) * 65536 + .5)
    result = -magnitude if math.copysign(1, value) < 0 else magnitude
    return max(-2147483648, min(2147483647, result)) & 0xffffffff


class StreamOracle:
    def __init__(self, mode):
        import numpy as np
        self.np, self.mode = np, mode
        model = load_json(ROOT / "tests/data/model_manifest.json")
        selected = model["streams"][mode]
        self.directory = artifact_path(ROOT, selected["layout"]["path"]).parent
        self.layout = load_json(self.directory / "layout.json")["tensors"]
        self.cache = {}

    def tensor(self, kind, layer, projection):
        prefix = f"model.layers.{layer}."
        require(layer < 24 and projection < 7, "model layer/projection address")
        if kind == 0:
            require(layer == projection == 0, "embedding layer/projection address")
            name = "model.embed_tokens.weight"
        elif kind == 7:
            require(layer == projection == 0, "final norm layer/projection address")
            name = "model.norm.weight"
        elif kind in (5, 6):
            require(projection == 0, "norm projection address")
            name = prefix + ("input_layernorm.weight" if kind == 5 else
                             "post_attention_layernorm.weight")
        else:
            require(kind in (1, 2, 3, 4, 12), "unknown model request kind")
            require(kind != 4 or projection < 3, "bias projection address")
            name = prefix + PROJECTIONS[projection] + (".bias" if kind == 4 else ".weight")
        item = self.layout[name]
        shape = item["shape"]
        if kind in (1, 2, 3):
            require(self.mode == "w4a16", "packed AWQ request in native mode")
            outputs, inputs = shape
            if kind == 1:
                filename, offset, dtype, shape = "weights.bin", item["byte_offset"], "<u4", (inputs, outputs // 8)
            elif kind == 2:
                filename, offset, dtype, shape = "zeros.bin", item["zero_offset"], "<u4", (inputs // 128, outputs // 8)
            else:
                filename, offset, dtype, shape = "scales.bin", item["scale_offset"], "<u2", (inputs // 128, outputs)
        else:
            require(kind != 12 or self.mode != "w4a16", "native matrix request in AWQ mode")
            filename, offset, dtype = "weights.bin", item["byte_offset"], "<u2"
        key = (kind, name)
        if key not in self.cache:
            self.cache[key] = self.np.memmap(self.directory / filename, mode="r",
                                            dtype=dtype, offset=offset, shape=tuple(shape))
        return self.cache[key]

    def read(self, kind, layer, projection, row, column):
        data = self.tensor(kind, layer, projection)
        if kind == 12:
            require(row < data.shape[1] and column < data.shape[0], "native matrix coordinate")
            return int(data[column, row])
        if data.ndim == 1:
            require(row == 0 and column < len(data), "scalar tensor coordinate")
            return int(data[column])
        require(row < data.shape[0] and column < data.shape[1], "matrix coordinate")
        return int(data[row, column])


def replay(path, mode, destination):
    oracle = StreamOracle(mode)
    scratch, cache = {}, {}
    previous_response = 0
    counts = {"transactions": 0, "reads": 0, "writes": 0, "embedding_comparisons": 0,
              "tensor_comparisons": 0, "mutable_read_comparisons": 0,
              "rope_comparisons": 0}
    embedding_expected = {}
    embedding_complete = False
    position = 0
    with gzip.open(path, "rb") as stream:
        while True:
            raw = stream.read(44)
            if not raw:
                break
            require(len(raw) == 44, "truncated production transaction record")
            req_lo, req_hi, rsp_lo, rsp_hi, write, kind, layer, proj, row, col, data = struct.unpack("<11I", raw)
            request, response = req_lo + (req_hi << 32), rsp_lo + (rsp_hi << 32)
            require(previous_response < request < response, "single-outstanding cycle order")
            previous_response = response
            require(write in (0, 1), "nonboolean memory write")
            counts["transactions"] += 1
            counts["writes" if write else "reads"] += 1
            if kind == 8:
                require(layer == proj == 0 and row in (*range(13), 14), "scratch slot/address")
                limit = 4864 if row in (9, 10, 11) else 128 if row in (3, 4) else 896
                require(col < limit, "scratch column")
                key = row, col
                if write:
                    if row == 0 and not embedding_complete:
                        require(col in embedding_expected, "embedding write without tensor read")
                        expected = embedding_expected[col]
                        require(data == expected,
                                f"embedding scratch payload lost/incorrect at column {col}: "
                                f"expected={expected:08x}, actual={data:08x}")
                        counts["embedding_comparisons"] += 1
                        if col == 895:
                            require(counts["embedding_comparisons"] == 896,
                                    "initial embedding incomplete")
                            embedding_complete = True
                    scratch[key] = data
                else:
                    require(key in scratch and data == scratch[key],
                            "scratch read differs from acknowledged write")
                    counts["mutable_read_comparisons"] += 1
            elif kind in (9, 10):
                require(layer < 24 and proj == 0 and row <= position and col < 128,
                        "causal KV address")
                key = kind, layer, row, col
                if write:
                    require(row == position, "KV write position")
                    cache[key] = data
                else:
                    require(key in cache and data == cache[key], "KV readback differs")
                    counts["mutable_read_comparisons"] += 1
            elif kind == 11:
                require(not write and layer == proj == 0 and col < 64,
                        "RoPE request address")
                require(row >= position and row < 32768, "RoPE position traversal")
                position = row
                angle = row * 1000000.0 ** (-(col // 2) / 32)
                value = math.sin(angle) if col % 2 else math.cos(angle)
                expected = (int(math.copysign(math.floor(abs(value)*2**30+.5), value)) & 0xffffffff
                            if mode == "w4a16" else
                            struct.unpack("<I", struct.pack("<f", value))[0])
                require(data == expected, "theta/split-half coefficient contents")
                counts["rope_comparisons"] += 1
            else:
                require(not write, "external model write")
                expected = oracle.read(kind, layer, proj, row, col)
                require(data == expected, "selected external tensor bytes differ")
                counts["tensor_comparisons"] += 1
                if kind == 0 and not embedding_complete:
                    embedding_expected[col] = embedding(data, mode)
    require(counts["transactions"] and counts["tensor_comparisons"] and
            counts["embedding_comparisons"], "no meaningful production trace comparisons")
    with destination.open("x") as output:
        json.dump({"scope": "public memory consistency only, not complete benchmark",
                   "complete_benchmark": False, "mode": mode, **counts}, output, indent=2)
    print(json.dumps(counts), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--mode", choices=("bf16", "fp16", "w4a16"), required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.worker:
        replay(artifact_path(ROOT, str(args.trace)), args.mode,
               artifact_path(ROOT, str(args.destination)))
        return 0
    ev = Evidence("production-trace")
    passed = False
    try:
        trace = artifact_path(ROOT, str(args.trace))
        # A running probe's trace may grow; this records the inspected prefix,
        # not a claim that the producer has completed or that the file is final.
        ev.receipt["inspected_trace"] = {"path": str(args.trace),
                                         "sha256_at_start": sha(trace),
                                         "bytes_at_start": trace.stat().st_size}
        passed = ev.run("trace-replay", [
            sys.executable, "tests/production_trace.py", "--worker", "--trace", str(args.trace),
            "--mode", args.mode, "--destination",
            str((ev.path / "comparisons.json").relative_to(ROOT))], timeout=3600)
        ev.assertion("public_memory_trace_replay", passed, acceptance_evidence=False)
    except (ValueError, OSError) as error:
        ev.assertion("trace_diagnostic_failure", False, diagnostic=str(error))
    finally:
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
