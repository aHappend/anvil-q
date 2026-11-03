#!/usr/bin/env python3
"""Assemble source-bound native HT2 DDR images; no device/performance claims."""

import argparse
import json
import math
from pathlib import Path
import struct
import sys
import uuid

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmarks import digest, portable_path, require, validate_asset
from quantized_checkpoint import header

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = ("tests/device_image.py", "tests/device_image_checks.py",
                  "tests/device_image_config_tb.sv", "tests/top_tb.sv",
                  "tests/quantized_checkpoint.py", "tests/benchmarks.py",
                  "tests/reference.py", "design/SPEC.md")
MODES = ("bf16", "fp16", "w4", "w2")


def geometry(config, sequence, group, block):
    h, q, k = (config[key] for key in
               ("hidden_size", "num_attention_heads", "num_key_value_heads"))
    require(all(type(v) is int and v > 0 for v in (h, q, k)), "invalid head geometry")
    require(h % q == 0 and q % k == 0, "incompatible head geometry")
    d = h // q
    result = dict(NUM_LAYERS=config["num_hidden_layers"], HIDDEN_SIZE=h,
                  INTERMEDIATE_SIZE=config["intermediate_size"], NUM_Q_HEADS=q,
                  NUM_KV_HEADS=k, HEAD_DIM=d, VOCAB_SIZE=config["vocab_size"],
                  MAX_SEQ_LEN=sequence, GROUP_SIZE=group, CACHE_BLOCK=block)
    limits = {"NUM_LAYERS": (1, 28), "HIDDEN_SIZE": (8, 1536),
              "INTERMEDIATE_SIZE": (8, 8960), "NUM_Q_HEADS": (1, 16),
              "NUM_KV_HEADS": (1, 2), "HEAD_DIM": (2, 128),
              "VOCAB_SIZE": (1, 151936), "MAX_SEQ_LEN": (1, 32768),
              "GROUP_SIZE": (1, 128), "CACHE_BLOCK": (1, 128)}
    for key, value in result.items():
        lo, hi = limits[key]
        require(type(value) is int and lo <= value <= hi, f"invalid {key}: {value!r}")
    require(d % 2 == 0 and h % 8 == 0 and result["INTERMEDIATE_SIZE"] % 8 == 0
            and k*d % 8 == 0, "incompatible native dimensions")
    require(group & (group-1) == 0 and h % group == 0
            and result["INTERMEDIATE_SIZE"] % group == 0, "incompatible GROUP_SIZE")
    require(block & (block-1) == 0 and d % block == 0, "incompatible CACHE_BLOCK")
    require(sequence <= config["max_position_embeddings"], "sequence exceeds checkpoint")
    require(config["hidden_act"] == "silu" and config["rms_norm_eps"] == 1e-6
            and not config.get("use_sliding_window", False) and not config.get("rope_scaling"),
            "unsupported model activation/normalization/attention configuration")
    theta = config["rope_theta"]
    require(type(theta) in (int, float) and math.isfinite(theta) and theta > 0,
            "invalid checkpoint RoPE theta")
    return result


def tensors(config, g):
    h, d, k, v = (g[key] for key in
                  ("HIDDEN_SIZE", "HEAD_DIM", "NUM_KV_HEADS", "VOCAB_SIZE"))
    result = [(0, "model.embed_tokens.weight", v, h, False),
              (1, "model.embed_tokens.weight" if config["tie_word_embeddings"] else
               "lm_head.weight", v, h, True),
              (2, "model.norm.weight", 1, h, False),
              (3, None, g["MAX_SEQ_LEN"], d, False)]
    for layer in range(g["NUM_LAYERS"]):
        prefix = f"model.layers.{layer}."
        for offset, role, rows, columns, matrix in (
                (0, "self_attn.q_proj.weight", h, h, True),
                (1, "self_attn.k_proj.weight", k*d, h, True),
                (2, "self_attn.v_proj.weight", k*d, h, True),
                (3, "self_attn.o_proj.weight", h, h, True),
                (4, "mlp.gate_proj.weight", g["INTERMEDIATE_SIZE"], h, True),
                (5, "mlp.up_proj.weight", g["INTERMEDIATE_SIZE"], h, True),
                (6, "mlp.down_proj.weight", h, g["INTERMEDIATE_SIZE"], True),
                (7, "input_layernorm.weight", 1, h, False),
                (8, "post_attention_layernorm.weight", 1, h, False),
                (9, "self_attn.q_proj.bias", 1, h, False),
                (10, "self_attn.k_proj.bias", 1, k*d, False),
                (11, "self_attn.v_proj.bias", 1, k*d, False)):
            result.append((16+16*layer+offset, prefix+role, rows, columns, matrix))
    return result


def native_words(words, half):
    require(bool(np.all((words & 0x7f80) != 0x7f80)), "nonfinite source weight")
    if not half:
        return words
    values = (words.astype("<u4") << np.uint32(16)).view("<f4")
    with np.errstate(over="ignore"):
        result = values.astype("<f2").view("<u2")
    require(bool(np.all((result & 0x7c00) != 0x7c00)), "FP16 weight conversion overflow")
    return result


def rope_words(config, g, half):
    dimension = g["HEAD_DIM"]
    frequencies = np.power(float(config["rope_theta"]),
                           -np.arange(dimension//2, dtype="float64")*2/dimension)
    for start in range(0, g["MAX_SEQ_LEN"], 256):
        positions = np.arange(start, min(start+256, g["MAX_SEQ_LEN"]), dtype="float64")
        angles = positions[:, None]*frequencies[None, :]
        coefficients = np.stack((np.cos(angles), np.sin(angles)), axis=-1).astype("<f4")
        if half:
            yield coefficients.astype("<f2").view("<u2").tobytes()
        else:
            raw = coefficients.view("<u4").astype("<u8")
            yield ((raw+0x7fff+((raw >> 16) & 1)) >> 16).astype("<u2").tobytes()


def assemble(root, manifest, output, mode, sequence=32768, group=128, block=16):
    require(mode in MODES, "invalid image mode")
    require(len(manifest["checkpoint_shards"]) == 1, "expected one bound checkpoint shard")
    source_binding = manifest["checkpoint_shards"][0]
    source = validate_asset(root, source_binding)
    config_binding = manifest["assets"]["config"]
    config = json.loads(validate_asset(root, config_binding).read_text())
    g = geometry(config, sequence, group, block)
    entries, data_base = header(source)
    inputs = [source_binding, config_binding]
    qentries, qpaths = {}, {}
    if mode in ("w4", "w2"):
        for binding in manifest["quantized_weight_inputs"]:
            path = validate_asset(root, binding)
            inputs.append(binding)
            qpaths[path.name] = path
        require("manifest.json" in qpaths, "missing bound quantized manifest")
        quantized = json.loads(qpaths["manifest.json"].read_text())
        require(quantized["source"] == source_binding and quantized["config"] == config_binding
                and quantized["group_size"] == group, "quantized provenance/group mismatch")
        for entry in quantized["tensors"]:
            if entry["bits"] == int(mode[1]):
                require(entry["descriptor"] not in qentries, "duplicate quantized descriptor")
                qentries[entry["descriptor"]] = entry
    output.mkdir(parents=True, exist_ok=False)
    memory = output / "memory.bin"
    descriptors = [bytes(64) for _ in range(16+16*g["NUM_LAYERS"])]
    segments, aliases = [], {}
    cursor = 4096
    with memory.open("wb") as stream:
        def append(chunks, size, index, role, name):
            nonlocal cursor
            address = cursor
            require(size > 0 and cursor+size <= 1 << 33, "DDR image address overflow")
            stream.seek(address)
            total = 0
            for chunk in chunks:
                total += len(chunk)
                require(total <= size, "payload exceeded declared extent")
                stream.write(chunk)
            require(total == size, "truncated payload source")
            segments.append(dict(address=address, bytes=size, descriptor=index,
                                 role=role, source_tensor=name))
            cursor = (cursor+size+63) & ~63
            return address

        def read_chunks(path, offset, size):
            with path.open("rb") as source_stream:
                source_stream.seek(offset)
                while size:
                    chunk = source_stream.read(min(size, 1 << 20))
                    require(bool(chunk), "truncated input segment")
                    size -= len(chunk)
                    yield chunk

        for index, name, rows, columns, matrix in tensors(config, g):
            quant = matrix and mode in ("w4", "w2")
            zero = scale = zs = ss = 0
            if quant:
                require(index in qentries, f"missing quantized descriptor {index}")
                entry = qentries[index]
                require((entry["source_tensor"], entry["rows"], entry["columns"]) ==
                        (name, rows, columns), "quantized tensor shape/name mismatch")
                bits = int(mode[1])
                stride = (columns*bits+7)//8
                zs, ss = ((columns//group)*bits+7)//8, 2*(columns//group)
                addresses = []
                for role, row_stride in (("payload", stride), ("zeros", zs), ("scales", ss)):
                    span = entry[role]
                    require(span["stride"] == row_stride, "unsupported quantized row padding")
                    require(span["file"] in qpaths, "unbound quantized data file")
                    require(type(span["offset"]) is int and span["offset"] >= 0,
                            "invalid quantized offset")
                    addresses.append(append(read_chunks(qpaths[span["file"]], span["offset"],
                                                        rows*row_stride),
                                            rows*row_stride, index, role, name))
                address, zero, scale = addresses
                flags = 0x100 if bits == 4 else 0x103
            else:
                stride = 2*columns
                if name is None:
                    chunks = rope_words(config, g, mode == "fp16")
                else:
                    require(name in entries, f"missing checkpoint tensor {name}")
                    tensor = entries[name]
                    require(tensor["shape"] in ([rows, columns], [columns] if rows == 1 else []),
                            f"checkpoint shape mismatch: {name}")
                    start, end = tensor["data_offsets"]
                    require(end-start == rows*stride, "checkpoint tensor length mismatch")
                    chunks = (native_words(np.frombuffer(chunk, dtype="<u2"), mode == "fp16")
                              .tobytes() for chunk in read_chunks(source, data_base+start, end-start))
                key = (name, mode == "fp16")
                if name is not None and key in aliases:
                    address = aliases[key]
                else:
                    address = append(chunks, rows*stride, index, "payload", name)
                    if name is not None:
                        aliases[key] = address
                flags = 0x102 if mode == "fp16" else 0x101
            descriptors[index] = struct.pack("<QQQQIIIIIIQ", address, rows*stride, zero, scale,
                                             rows, columns, stride, zs, ss, flags, 0)
        stream.truncate(cursor)
    bank = output / "descriptors.bin"
    bank.write_bytes(b"".join(descriptors))
    records = g["NUM_LAYERS"]*2*g["NUM_KV_HEADS"]*(g["HEAD_DIM"]//block)*(sequence+4)
    configurations = []
    for kv in ("bf16", "int8"):
        extent = (records*(2*block if kv == "bf16" else block+2)+63) & ~63
        require(cursor+extent <= 1 << 33, "DDR cache address overflow")
        for sparse in (False, True):
            mode_word = (2 if mode == "fp16" else 1) | {"bf16": 0, "fp16": 0,
                         "w4": 4, "w2": 8}[mode] | (16 if sparse else 0) | (32 if kv == "int8" else 0)
            for width in (1, 2, 4):
                writes = [(0x40, mode_word), (0x44, width), (0x18, cursor & 0xffffffff),
                          (0x1c, cursor >> 32), (0x20, extent & 0xffffffff), (0x24, extent >> 32)]
                for index, descriptor in enumerate(descriptors):
                    writes.extend((0x1000+64*index+4*word, value) for word, value in
                                  enumerate(struct.unpack("<16I", descriptor)))
                writes.append((8, 1))
                path = output / f"{kv}-s{int(sparse)}-k{width}.txt"
                path.write_text(f"{len(writes)}\n"+"".join(f"{a:04x} {b:08x}\n" for a, b in writes))
                configurations.append(dict(kv=kv, sparse=sparse, k=width, ht2_mode=mode_word,
                                           cache_base=cursor, cache_bytes=extent,
                                           path=str(path.relative_to(root)), sha256=digest(path)))
    result = dict(schema=1, kind="ht2-native-ddr-image", mode=mode, geometry=g, inputs=inputs,
                  implementation_sha256={p: digest(root / p) for p in IMPLEMENTATION},
                  memory=dict(path=str(memory.relative_to(root)), sha256=digest(memory),
                              bytes=memory.stat().st_size),
                  descriptors=dict(path=str(bank.relative_to(root)), sha256=digest(bank)),
                  segments=segments, configurations=configurations,
                  rope_policy="checkpoint theta; rotate-half pairs; binary64 trig -> RNE FP32 -> native",
                  cache_policy="Uninitialized isolated cache reservation; no valid cache state is shipped.",
                  scope="Input image only. No official-model RTL fidelity, timing, board or TPM claim.")
    (output / "manifest.json").write_text(json.dumps(result, indent=2)+"\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build", "_build"))
    parser.add_argument("--modes", choices=MODES, nargs="+", default=list(MODES))
    parser.add_argument("--sequence", type=int, default=32768)
    parser.add_argument("--group", type=int, default=128)
    parser.add_argument("--cache-block", type=int, default=16)
    parser.add_argument("--output")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    if args.command == "_build":
        require(len(args.modes) == 1, "internal build expects exactly one mode")
        output = portable_path(ROOT, args.output)
        require(output.parent.name == "checkpoint-images" or output.name.startswith("official-image-"),
                "weight images must use checkpoint-images/ or official-image-*")
        manifest = json.loads((ROOT / "tests/benchmark_manifest.json").read_text())
        result = assemble(ROOT, manifest, output, args.modes[0], args.sequence,
                          args.group, args.cache_block)
        print(json.dumps({"image": str(output.relative_to(ROOT)), "mode": result["mode"],
                          "memory_bytes": result["memory"]["bytes"]}), flush=True)
        return 0
    from verify import Run
    run = Run("device-image-"+args.command, preparation=True, repair_of=args.repair_of)
    run.receipt["argv"] = ["python3", "tests/device_image.py", *sys.argv[1:]]
    run.save()
    try:
        run.tool("python3")
        run.command(["python3", "-c", "import numpy; print('numpy', numpy.__version__)"],
                    "numpy-version")
        run.command(["python3", "tests/device_image_checks.py", "--fixtures",
                     run.relative(run.path / "checkpoint-images")], "independent-image-controls")
        from device_image_checks import smoke
        fixtures = json.loads((run.path / "checkpoint-images/fixture-results.json").read_text())
        run.receipt["image_controls"] = fixtures
        run.save()
        smoke(run, fixtures["images"])
        if args.command == "build":
            base = portable_path(ROOT, args.output) if args.output else (
                ROOT / "checkpoint-images" / f"official-image-ht2-{run.path.name}")
            require(not base.exists(), "refusing to overwrite image output")
            require(len(set(args.modes)) == len(args.modes), "duplicate modes")
            run.receipt["images"] = []
            for mode in args.modes:
                base.mkdir(parents=True, exist_ok=True)
                destination = base / f"official-image-{mode}-{uuid.uuid4().hex[:8]}"
                run.command(["python3", "tests/device_image.py", "_build", "--modes", mode,
                             "--sequence", str(args.sequence), "--group", str(args.group),
                             "--cache-block", str(args.cache_block), "--output",
                             run.relative(destination)], "assemble-"+mode)
                run.command(["python3", "tests/device_image_checks.py", "--image",
                             run.relative(destination / "manifest.json")], "independent-bytes-"+mode)
                run.receipt["images"].append(dict(mode=mode, manifest=run.relative(
                    destination / "manifest.json"), sha256=digest(destination / "manifest.json")))
                run.save()
        return run.finish(True, "DDR image assembly/independent checks completed; not production acceptance")
    except Exception as exc:
        return run.finish(False, f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
