"""Portable layout-1 binary images with strict shape and SHA-256 binding."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def dimensions(words):
    return dict(zip(("layers", "hidden", "intermediate", "query_heads", "kv_heads",
                     "head_dim", "vocabulary", "context"), words[7:15]))


def valid_native(w, banks):
    positive = lambda bits: not (bits >> 31) and bits & 0x7fffffff and (
        (bits >> 23) & 255) != 255
    power = lambda value: value > 0 and value & (value - 1) == 0
    return bool(
        len(w) == 32 and all(type(value) is int and 0 <= value < 2**32 for value in w)
        and w[:2] == [2, 5] and w[2] in (0, 1) and w[3:5] == [0, 0]
        and w[5] in (0, 1, 2) and power(w[6]) and w[6] <= banks
        and 1 <= w[7] <= 64 and 2 <= w[8] <= 8192
        and 1 <= w[9] <= 32768 and 1 <= w[10] <= 128 and 1 <= w[11] <= 128
        and 2 <= w[12] <= 256 and w[12] % 2 == 0
        and 1 <= w[13] <= 262144 and 1 <= w[14] <= 131072 and w[15] == 1
        and w[16] in (0, 1) and positive(w[17]) and positive(w[18])
        and power(w[19]) and w[19] <= 32 and 1 <= w[20] <= 131072
        and w[21] == 0 and 1 <= w[22] <= 8 and w[23] == 1
        and w[24:] == [0] * 8 and w[8] == w[10] * w[12]
        and w[10] == w[11] * w[22] and w[19] * w[20] >= w[14])


def tensor_shapes(words):
    h, inter, kd, vocabulary = words[8], words[9], words[11] * words[12], words[13]
    shapes = {(0, 0, 0): (vocabulary, h), (0, 0, 1): (vocabulary, h),
              (7, 0, 0): (1, h)}
    for layer in range(words[7]):
        for projection, shape in enumerate(((h, h), (kd, h), (kd, h), (h, h),
                                            (inter, h), (inter, h), (h, inter))):
            shapes[1, layer, projection] = shape
            if words[16] and projection < 3:
                shapes[4, layer, projection] = (1, h if projection == 0 else kd)
        shapes[5, layer, 0] = shapes[6, layer, 0] = (1, h)
    return shapes


def export_static(directory, words, initial, seed):
    """Export synthetic source tensors only; expected mutable results stay separate."""
    directory.mkdir(parents=True, exist_ok=False)
    groups = defaultdict(dict)
    for (kind, layer, projection, row, column), value in initial.items():
        if kind not in (0, 1, 4, 5, 6, 7, 11, 15):
            raise ValueError(f"Static fixture contains mutable or unknown kind {kind}")
        groups[kind, layer, projection][row, column] = value
    tensors = []
    for (kind, layer, projection), elements in sorted(groups.items()):
        rows = max(row for row, _ in elements) + 1
        columns = max(column for _, column in elements) + 1
        dtype = ("fp32" if kind == 11 else "u32" if kind == 15 else
                 "fp16" if words[2] else "bf16")
        code = "<H" if dtype in ("bf16", "fp16") else "<I"
        data = b"".join(struct.pack(code, elements[row, column])
                        for row in range(rows) for column in range(columns))
        path = f"kind-{kind}-layer-{layer}-proj-{projection}.bin"
        (directory / path).write_bytes(data)
        tensors.append({
            "path": path, "sha256": digest(data), "kind": kind, "layer": layer,
            "projection": projection, "rows": rows, "columns": columns, "dtype": dtype,
            "byte_order": "little", "layout": "row-major",
        })
    rope_tensors = [tensor for tensor in tensors if tensor["kind"] == 11]
    if len(rope_tensors) != 1:
        raise ValueError("A synthetic fixture requires exactly one supplied RoPE table")
    rope = {
        "source": "synthetic rational unit circle",
        "generator": "t=position*(pair+1)/16; cos=(1-t*t)/(1+t*t); sin=2*t/(1+t*t)",
        "original_checkpoint_configuration": None, "generation": rope_tensors[0]["layer"],
        "context": words[14], "shape": [words[14], words[12]],
        "rounding": "exact rational to FP32 RNE", "sha256": rope_tensors[0]["sha256"],
    }
    configuration = {
        "descriptor_words": words, "original_checkpoint_configuration": None,
        "dimensions": dimensions(words), "native_format": "fp16" if words[2] else "bf16",
        "tuple_layout": 1, "rope": rope,
    }
    manifest = {
        "schema": 1, "layout": 1, "descriptor_words": words,
        "synthetic": True, "checkpoint": None, "seed": seed,
        "configuration": configuration, "configuration_sha256": digest(canonical(configuration)),
        "rope": rope, "tensors": tensors,
    }
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path


def load(path):
    """Reject missing, stale, malformed or escaping inputs; never substitute zeros."""
    manifest = json.loads(path.read_text())
    if manifest["schema"] != 1 or manifest["layout"] != 1:
        raise ValueError("Unsupported native image schema/layout")
    words = manifest["descriptor_words"]
    if not valid_native(words, 16):
        raise ValueError("Invalid native image descriptor")
    configuration = manifest["configuration"]
    if digest(canonical(configuration)) != manifest["configuration_sha256"]:
        raise ValueError("Configuration SHA-256 mismatch")
    if (configuration["descriptor_words"] != words or
            configuration["dimensions"] != dimensions(words) or
            configuration["native_format"] != ("fp16" if words[2] else "bf16") or
            configuration["tuple_layout"] != 1 or configuration["rope"] != manifest["rope"]):
        raise ValueError("Manifest/configuration binding mismatch")
    base = path.parent.resolve()
    required = tensor_shapes(words)
    initial, keys, paths = {}, set(), set()
    rope_hashes = []
    for tensor in manifest["tensors"]:
        if tensor["layout"] != "row-major" or tensor["byte_order"] != "little":
            raise ValueError("Unsupported tensor layout/byte order")
        filename = Path(tensor["path"])
        if filename.is_absolute() or ".." in filename.parts:
            raise ValueError("Tensor path must stay relative to its manifest")
        resolved = (base / filename).resolve()
        if not resolved.is_relative_to(base):
            raise ValueError("Tensor symlink escapes its manifest")
        key = tuple(tensor[name] for name in ("kind", "layer", "projection"))
        if (key in keys or resolved in paths or
                any(type(value) is not int or not 0 <= value < 2**32 for value in key)):
            raise ValueError("Duplicate or malformed tensor identity/path")
        keys.add(key)
        paths.add(resolved)
        rows, columns = tensor["rows"], tensor["columns"]
        if (type(rows) is not int or type(columns) is not int or rows < 1 or columns < 1):
            raise ValueError("Tensor shape must be positive integral extents")
        shape = (required.get(key) if key[0] not in (11, 15) else
                 (words[14], words[12]) if key[0] == 11 else
                 ((words[14] + words[19] - 1) // words[19], 1))
        if (rows, columns) != shape:
            raise ValueError("Tensor shape/identity disagrees with descriptor")
        dtype = tensor["dtype"]
        if dtype not in ("bf16", "fp16", "fp32", "u32"):
            raise ValueError("Unsupported tensor dtype")
        expected_dtype = ("fp32" if key[0] == 11 else "u32" if key[0] == 15 else
                          "fp16" if words[2] else "bf16")
        if key[0] not in (0, 1, 4, 5, 6, 7, 11, 15) or dtype != expected_dtype:
            raise ValueError("Tensor kind/dtype is not an immutable native source")
        data = resolved.read_bytes()
        element_bytes = 2 if dtype in ("bf16", "fp16") else 4
        if len(data) != rows * columns * element_bytes:
            raise ValueError("Tensor byte length/shape mismatch")
        if digest(data) != tensor["sha256"]:
            raise ValueError("Tensor SHA-256 mismatch")
        values = struct.iter_unpack("<H" if element_bytes == 2 else "<I", data)
        for index, (value,) in enumerate(values):
            initial[(*key, index // columns, index % columns)] = value
        if key[0] == 11:
            if ([rows, columns] != manifest["rope"]["shape"] or
                    key[1:] != (manifest["rope"]["generation"], 0)):
                raise ValueError("RoPE table shape/generation mismatch")
            rope_hashes.append(tensor["sha256"])
        if key[0] == 15 and key[2] != 0:
            raise ValueError("Page map projection must be zero")
    if rope_hashes != [manifest["rope"]["sha256"]]:
        raise ValueError("Supplied RoPE table hash binding mismatch")
    if not required.keys() <= keys or not any(key[0] == 15 for key in keys):
        raise ValueError("Missing required native source tensor/page map")
    return initial


def self_test(directory):
    from native_model import Fixture, descriptor

    fixture = Fixture(descriptor(dimension=2, intermediate=3, vocabulary=3), tokens=1)
    manifest_path = export_static(directory / "checkpoint-images",
                                  fixture.words, fixture.initial, fixture.seed)
    if load(manifest_path) != fixture.initial:
        raise AssertionError("Binary image roundtrip differs from source tuples")
    original = json.loads(manifest_path.read_text())
    failures = []
    for label in ("hash", "configuration", "duplicate", "shape", "escape",
                  "byte-order", "missing", "descriptor"):
        bad = json.loads(json.dumps(original))
        if label == "hash":
            bad["tensors"][0]["sha256"] = "0" * 64
        elif label == "configuration":
            bad["configuration"]["dimensions"]["hidden"] += 1
        elif label == "duplicate":
            bad["tensors"].append(bad["tensors"][0])
        elif label == "shape":
            bad["tensors"][0]["columns"] += 1
        elif label == "escape":
            bad["tensors"][0]["path"] = "../outside.bin"
        elif label == "byte-order":
            bad["tensors"][0]["byte_order"] = "big"
        elif label == "missing":
            del bad["tensors"][0]
        else:
            bad["descriptor_words"][19] = 0
        path = manifest_path.parent / f"invalid-{label}.json"
        path.write_text(json.dumps(bad) + "\n")
        try:
            load(path)
        except ValueError as error:
            failures.append({"case": label, "rejected": str(error)})
        else:
            raise AssertionError(f"Invalid image accepted: {label}")
    print(json.dumps({"roundtrip_tuples": len(fixture.initial),
                      "negative_cases": failures}), flush=True)


if __name__ == "__main__":
    from evidence import execute, new_run, relative

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output:
        self_test(args.output)
    else:
        directory = new_run("images", args.preparation)
        execute(directory / "python-images", [
            "python3", "tests/images.py", "--output", relative(directory)])
        print(f"Image receipts: {relative(directory)}", flush=True)
