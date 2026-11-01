#!/usr/bin/env python3
"""Streaming official-checkpoint quantization; no inference/performance claims."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmarks import digest, portable_path, require, validate_asset
from reference import BF16, decode, encode_ratio

ROOT = Path(__file__).resolve().parents[1]
POLICY = "zero-inclusive-minmax-stored-bf16-rne-v1"
IMPLEMENTATION = ("tests/quantized_checkpoint.py",
                  "tests/quantized_checkpoint_check.cpp", "design/SPEC.md")


def header(path):
    with path.open("rb") as stream:
        raw = stream.read(8)
        require(len(raw) == 8, "truncated safetensors length")
        length = struct.unpack("<Q", raw)[0]
        require(0 < length <= 16 * 1024 * 1024, "unbounded safetensors header")
        data = json.loads(stream.read(length))
    cursor = 0
    for name, tensor in sorted(((k, v) for k, v in data.items() if k != "__metadata__"),
                               key=lambda item: item[1]["data_offsets"][0]):
        require(tensor["dtype"] == "BF16", f"{name}: expected official BF16 tensor")
        size = 2
        for dimension in tensor["shape"]:
            require(type(dimension) is int and dimension > 0, "invalid tensor shape")
            size *= dimension
        start, end = tensor["data_offsets"]
        require(start == cursor and end - start == size, f"{name}: invalid tensor extent")
        cursor = end
    require(path.stat().st_size == 8 + length + cursor, "checkpoint EOF/extent mismatch")
    return data, 8 + length


def projections(config, tensors):
    result = []
    hidden, intermediate = config["hidden_size"], config["intermediate_size"]
    kv = config["num_key_value_heads"] * (hidden // config["num_attention_heads"])
    for layer in range(config["num_hidden_layers"]):
        prefix = f"model.layers.{layer}."
        for offset, role, shape in (
                (0, "self_attn.q_proj.weight", [hidden, hidden]),
                (1, "self_attn.k_proj.weight", [kv, hidden]),
                (2, "self_attn.v_proj.weight", [kv, hidden]),
                (3, "self_attn.o_proj.weight", [hidden, hidden]),
                (4, "mlp.gate_proj.weight", [intermediate, hidden]),
                (5, "mlp.up_proj.weight", [intermediate, hidden]),
                (6, "mlp.down_proj.weight", [hidden, intermediate])):
            name = prefix + role
            require(tensors.get(name, {}).get("shape") == shape, f"{name}: shape mismatch")
            result.append((name, 16 + 16 * layer + offset))
    name = "model.embed_tokens.weight" if config["tie_word_embeddings"] else "lm_head.weight"
    require(tensors.get(name, {}).get("shape") == [config["vocab_size"], hidden],
            "vocabulary projection shape mismatch")
    result.append((name, 1))
    return result


def rounded_bf16(values):
    """Direct binary64-to-BF16 RNE, without an intermediate FP32 rounding."""
    import numpy as np
    magnitude = np.abs(values)
    _, exponent = np.frexp(magnitude)
    quantum = np.maximum(exponent - 8, -133)
    significand = np.rint(np.ldexp(magnitude, -quantum))
    rounded = np.ldexp(significand, quantum)
    require(bool(np.all(np.isfinite(rounded))) and
            bool(np.all(rounded <= float.fromhex("0x1.fep+127"))),
            "quantization BF16 overflow")
    # rounded is already exactly BF16, including subnormals.
    bits = (rounded.astype("<f4").view("<u4") >> 16).astype("<u2")
    return bits | (np.signbit(values).astype("<u2") << 15)


def expand(bits):
    import numpy as np
    return (bits.astype("<u4") << 16).view("<f4").astype("float64")


def quantize(bits, width, group):
    import numpy as np
    require(bits.ndim == 2 and bits.shape[1] % group == 0, "incomplete quantization group")
    require(bool(np.all((bits & 0x7f80) != 0x7f80)), "nonfinite official BF16 weight")
    values = expand(bits).reshape(bits.shape[0], -1, group)
    low = np.minimum(values.min(axis=2), 0)
    high = np.maximum(values.max(axis=2), 0)
    limit = (1 << width) - 1
    scales = rounded_bf16((high - low) / limit)
    # Large exponent gaps can lose a midpoint term in binary64 subtraction.
    # Resolve those uncommon groups with exact integer/rational arithmetic.
    low_bits = rounded_bf16(low)
    high_bits = rounded_bf16(high)
    low_exp = (low_bits >> 7) & 255
    high_exp = (high_bits >> 7) & 255
    exceptional = ((low_bits & 0x7fff) != 0) & ((high_bits & 0x7fff) != 0) & (
        np.abs(low_exp.astype("int32") - high_exp.astype("int32")) > 32)
    for row, column in np.argwhere(exceptional):
        _, lm, lp, _ = decode(int(low_bits[row, column]), BF16)
        _, hm, hp, _ = decode(int(high_bits[row, column]), BF16)
        power = min(lp, hp)
        total = (lm << (lp-power)) + (hm << (hp-power))
        scales[row, column], error = encode_ratio(False, total, limit, power, BF16)
        require(not error, "exact group scale overflow")
    empty = (low == 0) & (high == 0)
    scales = np.where(empty, 0x3f80, np.maximum(scales, 1)).astype("<u2")
    scale_values = expand(scales)
    zeros = np.clip(np.rint(-low / scale_values), 0, limit).astype("uint8")
    codes = np.clip(np.rint(values / scale_values[..., None]) + zeros[..., None],
                    0, limit).astype("uint8").reshape(bits.shape)
    reconstruction = rounded_bf16(
        (codes.reshape(values.shape).astype("int16") - zeros[..., None]) *
        scale_values[..., None]).reshape(bits.shape)
    return codes, zeros, scales, reconstruction


def packed(values, width):
    import numpy as np
    rows, columns = values.shape
    fields = 8 // width
    result = np.zeros((rows, (columns + fields - 1) // fields), dtype="uint8")
    for field in range(fields):
        selected = values[:, field::fields]
        result[:, :selected.shape[1]] |= selected << (field * width)
    return result.tobytes()


def source_inputs():
    manifest = json.loads((ROOT / "tests/benchmark_manifest.json").read_text())
    require(len(manifest["checkpoint_shards"]) == 1, "converter expects one official shard")
    source = validate_asset(ROOT, manifest["checkpoint_shards"][0])
    config_path = validate_asset(ROOT, manifest["assets"]["config"])
    require(manifest["checkpoint_shards"][0]["sha256"] ==
            manifest["model_provenance"]["checkpoint_lfs_sha256"],
            "official upstream LFS hash mismatch")
    tensors, base = header(source)
    config = json.loads(config_path.read_text())
    return manifest, source, config, tensors, base


def generate(image, group):
    import numpy as np
    manifest, source, config, tensors, base = source_inputs()
    require(group in (1, 2, 4, 8, 16, 32, 64, 128), "illegal GROUP_SIZE")
    selected = projections(config, tensors)
    image.mkdir(parents=True, exist_ok=False)
    result = {
        "schema": 1, "kind": "derived-official-quantized-inputs", "policy": POLICY,
        "group_size": group, "model": manifest["model"],
        "upstream": manifest["model_provenance"],
        "source": manifest["checkpoint_shards"][0], "config": manifest["assets"]["config"],
        "implementation_sha256": {p: digest(ROOT / p) for p in IMPLEMENTATION},
        "native_tensor_policy": "Embedding, gamma and biases remain in source BF16; "
                                "RoPE coefficients must be generated from bound config separately.",
        "rounding": "Scale=RNE_BF16((max(0,w)-min(0,w))/(2^bits-1)); "
                    "positive minimum-subnormal floor; zero-only group scale=1, zero=0. "
                    "z=clip(RNE(-min(0,w)/stored_scale)); "
                    "q=clip(RNE(w/stored_scale)+z); reconstruction=RNE_BF16((q-z)*stored_scale).",
        "files": [], "tensors": [],
    }
    with source.open("rb") as checkpoint:
        for width in (4, 2):
            names = [f"w{width}-weights.bin", f"w{width}-zeros.bin", f"w{width}-scales.bf16"]
            handles = [(image / name).open("xb") for name in names]
            try:
                for name, descriptor in selected:
                    tensor = tensors[name]
                    rows, columns = tensor["shape"]
                    require(columns % group == 0, f"{name}: nonintegral metadata groups")
                    metadata_groups = columns // group
                    entry = {
                        "source_tensor": name, "descriptor": descriptor, "bits": width,
                        "rows": rows, "columns": columns, "flags": 0x100 if width == 4 else 0x103,
                        "source_offset": base + tensor["data_offsets"][0],
                        "payload": {"file": names[0], "offset": handles[0].tell(),
                                    "stride": (columns * width + 7) // 8},
                        "zeros": {"file": names[1], "offset": handles[1].tell(),
                                  "stride": (metadata_groups * width + 7) // 8},
                        "scales": {"file": names[2], "offset": handles[2].tell(),
                                   "stride": 2 * metadata_groups},
                    }
                    reconstruction_hash = hashlib.sha256()
                    checkpoint.seek(entry["source_offset"])
                    # Bound working storage independently of tensor/model size.
                    chunk_rows = max(1, (128 * 1024) // columns)
                    for start in range(0, rows, chunk_rows):
                        count = min(chunk_rows, rows-start)
                        raw = checkpoint.read(2 * count * columns)
                        require(len(raw) == 2 * count * columns, "truncated source tensor")
                        bits = np.frombuffer(raw, dtype="<u2").reshape(count, columns)
                        codes, zeros, scales, reconstruction = quantize(bits, width, group)
                        handles[0].write(packed(codes, width))
                        handles[1].write(packed(zeros, width))
                        handles[2].write(scales.astype("<u2").tobytes())
                        reconstruction_hash.update(reconstruction.astype("<u2").tobytes())
                    entry["reconstruction_sha256"] = reconstruction_hash.hexdigest()
                    result["tensors"].append(entry)
                    print(f"generated W{width} descriptor={descriptor} {name} rows={rows}",
                          flush=True)
            finally:
                for handle in handles:
                    handle.close()
            for name in names:
                path = image / name
                result["files"].append({"path": str(path.relative_to(ROOT)),
                                        "sha256": digest(path), "bytes": path.stat().st_size})
    (image / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")


def check(run, image, binary):
    manifest, source, config, tensors, base = source_inputs()
    data = json.loads((image / "manifest.json").read_text())
    require(data["schema"] == 1 and data["policy"] == POLICY and
            data["source"] == manifest["checkpoint_shards"][0] and
            data["config"] == manifest["assets"]["config"] and
            data["upstream"] == manifest["model_provenance"],
            "quantized provenance mismatch")
    require(data["implementation_sha256"] ==
            {p: digest(ROOT / p) for p in IMPLEMENTATION}, "converter source identity changed")
    group = data["group_size"]
    require(group in (1, 2, 4, 8, 16, 32, 64, 128), "illegal image GROUP_SIZE")
    expected = [(bits, name, descriptor) for bits in (4, 2)
                for name, descriptor in projections(config, tensors)]
    require([(e["bits"], e["source_tensor"], e["descriptor"]) for e in data["tensors"]] ==
            expected, "incomplete/duplicate/reordered official projection set")
    expected_files = {f"w{b}-{suffix}" for b in (4, 2)
                      for suffix in ("weights.bin", "zeros.bin", "scales.bf16")}
    require(len(data["files"]) == 6 and
            {Path(f["path"]).name for f in data["files"]} == expected_files,
            "incomplete image file set")
    sizes = {}
    for binding in data["files"]:
        path = validate_asset(ROOT, binding)
        require(path.parent == image and path.stat().st_size == binding["bytes"],
                "image file escaped directory or extent mismatch")
        sizes[path.name] = path.stat().st_size
    offsets = {name: 0 for name in expected_files}
    table = run.path / "quantized-check-table.tsv"
    with table.open("x") as stream:
        for entry in data["tensors"]:
            name, width = entry["source_tensor"], entry["bits"]
            rows, columns = tensors[name]["shape"]
            require([entry["rows"], entry["columns"]] == [rows, columns] and
                    entry["source_offset"] == base + tensors[name]["data_offsets"][0] and
                    entry["flags"] == (0x100 if width == 4 else 0x103) and
                    columns % group == 0, "tensor source/layout mismatch")
            fields = [name, width, group, str(source.relative_to(ROOT)),
                      entry["source_offset"], rows, columns]
            for role, suffix, stride in (
                    ("payload", "weights.bin", (columns * width + 7) // 8),
                    ("zeros", "zeros.bin", ((columns // group) * width + 7) // 8),
                    ("scales", "scales.bf16", 2 * (columns // group))):
                layout = entry[role]
                filename = f"w{width}-{suffix}"
                require(layout == {"file": filename, "offset": offsets[filename],
                                   "stride": stride}, f"{name}: invalid {role} layout")
                fields.extend((str((image / filename).relative_to(ROOT)), offsets[filename]))
                offsets[filename] += rows * stride
            stream.write("\t".join(map(str, fields)) + "\n")
    require(offsets == sizes, "image trailing bytes or truncated extents")
    _, output, _ = run.command([run.relative(binary), run.relative(table)],
                               "independent-all-weights-check")
    observed = [line.split() for line in output.splitlines() if line.startswith("CHECK ")]
    require(len(observed) == len(expected), "independent checker missed tensors")
    count = 0
    for fields, entry in zip(observed, data["tensors"]):
        require(fields == ["CHECK", entry["source_tensor"], str(entry["bits"]),
                           str(entry["rows"] * entry["columns"]),
                           entry["reconstruction_sha256"]],
                f"{entry['source_tensor']}: independent BF16 reconstruction mismatch")
        count += entry["rows"] * entry["columns"]
    run.receipt["quantized_image"] = {
        "manifest": str((image / "manifest.json").relative_to(ROOT)),
        "manifest_sha256": digest(image / "manifest.json"),
        "compared_weights": count, "compared_tensors": len(expected),
        "independent_checker": "exact integer/rational C++ plus OpenSSL SHA-256",
        "files": data["files"],
    }
    run.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "check", "_generate"))
    parser.add_argument("--image", help="project-relative fresh official-image-* directory")
    parser.add_argument("--group-size", type=int, default=128)
    args = parser.parse_args()
    if args.command == "_generate":
        generate(portable_path(ROOT, args.image), args.group_size)
        return 0
    from verify import Run
    run = Run("official-quantized-" + args.command, preparation=True)
    run.receipt["argv"] = ["python3", "tests/quantized_checkpoint.py", *sys.argv[1:]]
    run.save()
    try:
        run.tool("python3")
        run.tool("c++")
        run.command(["python3", "-c", "import numpy; print('numpy', numpy.__version__)"],
                    "numpy-version")
        binary = run.path / "quantized-check"
        run.command(["c++", "-std=c++17", "-O2", "tests/quantized_checkpoint_check.cpp",
                     "-lcrypto", "-o", run.relative(binary)], "compile-independent-checker")
        import quantized_checkpoint_tests
        quantized_checkpoint_tests.execute(run, binary)
        image_arg = args.image or ("checkpoint-images/official-image-qwen-w4w2-" +
                                   run.path.name.removeprefix("official-quantized-"))
        image = portable_path(ROOT, image_arg)
        require(image.name.startswith("official-image-"), "image must use official-image-* naming")
        if args.command == "generate":
            require(not image.exists(), "refusing to overwrite an existing image")
            run.command(["python3", "tests/quantized_checkpoint.py", "_generate",
                         "--image", image_arg, "--group-size", str(args.group_size)],
                        "stream-official-projections")
        else:
            require(args.image is not None, "check requires --image")
        check(run, image, binary)
        binary.unlink()
        return run.finish(True, "Official W4/W2 bytes and BF16 reconstruction independently checked; "
                          "not model inference or benchmark acceptance")
    except Exception as exc:
        return run.finish(False, f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
