"""Import genuine staged tensors into the admitted tiled DDR image layout."""

import argparse
import hashlib
import json
import math
import mmap
from pathlib import Path
import random
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment
from rope_reference import write_table


PROJECTIONS = ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
               "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")
GEOMETRY = {"num_hidden_layers": 28, "hidden_size": 1536, "intermediate_size": 8960,
            "num_attention_heads": 12, "num_key_value_heads": 2, "vocab_size": 151936,
            "max_position_embeddings": 32768, "rope_theta": 1000000.0}


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


class Source:
    def __init__(self, root, mode):
        manifest_path = root / "data/model/official_inputs.json"
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("synthetic") is not False:
            raise ValueError("official checkpoint provenance must not be synthetic")
        self.info = manifest["sources"][mode]
        self.files = {item["remote_path"]: item for item in self.info["files"]}
        for item in self.info["files"]:
            path = root / item["path"]
            if path.stat().st_size != item["bytes"] or file_hash(path) != item["sha256"]:
                raise ValueError("staged source hash mismatch: " + item["path"])
        self.path = root / self.files["model.safetensors"]["path"]
        self.config = json.loads((root / self.files["config.json"]["path"]).read_text())
        for key, expected in GEOMETRY.items():
            if self.config.get(key) != expected:
                raise ValueError("unexpected official model geometry: " + key)
        self.stream = self.path.open("rb")
        self.data = mmap.mmap(self.stream.fileno(), 0, access=mmap.ACCESS_READ)
        length = struct.unpack_from("<Q", self.data)[0]
        if length > 16 * 1024 * 1024:
            raise ValueError("unbounded safetensors header")
        self.header = json.loads(self.data[8:8 + length])
        self.start = 8 + length
        self.used = set()
        extents = []
        for name, item in self.header.items():
            if name == "__metadata__":
                continue
            start, end = item["data_offsets"]
            if start < 0 or start >= end or self.start + end > len(self.data):
                raise ValueError("invalid safetensors extent")
            extents.append((start, end))
        extents.sort()
        if any(a[1] > b[0] for a, b in zip(extents, extents[1:])):
            raise ValueError("overlapping safetensors tensors")

    def tensor(self, name, shape, dtype):
        item = self.header[name]
        if item["shape"] != shape or item["dtype"] != dtype:
            raise ValueError("unexpected checkpoint tensor shape/dtype: " + name)
        size = math.prod(shape) * (4 if dtype == "I32" else 2)
        start, end = item["data_offsets"]
        if end - start != size:
            raise ValueError("incorrect source tensor byte extent: " + name)
        self.used.add(name)
        return self.start + start, size

    def close(self):
        self.data.close()
        self.stream.close()


def prepare(source, mode, directory):
    descriptors = [bytes(64) for _ in range(464)]
    tasks = []
    allocations = []
    cursor = 0
    fmt = 1 if mode == "awq" else 2
    dtype = "F16" if mode == "awq" else "BF16"

    def allocate(size, label):
        nonlocal cursor
        cursor = (cursor + 63) & ~63
        base = cursor
        cursor += size
        allocations.append({"label": label, "base": base, "bytes": size})
        if cursor > 8 * 1024 ** 3:
            raise ValueError("weight image exceeds DDR region")
        return base

    def descriptor(index, base, length, rows, cols, stride, tensor_fmt,
                   zeros=0, scales=0, zero_stride=0, scale_stride=0):
        descriptors[index] = struct.pack("<QQQQIIIIIIQ", base, length, zeros, scales, rows, cols,
                                         stride, zero_stride, scale_stride, 0x100 | tensor_fmt, 0)

    def plain(index, name, rows, cols):
        shape = [cols] if rows == 1 else [rows, cols]
        offset, length = source.tensor(name, shape, dtype)
        base = allocate(length, name)
        tasks.append((dtype, offset, rows, cols, base))
        descriptor(index, base, length, rows, cols, cols * 2, fmt)
        return offset, length

    embedding_offset, embedding_length = plain(0, "model.embed_tokens.weight", 151936, 1536)
    alias = False
    if "lm_head.weight" in source.header:
        head_offset, length = source.tensor("lm_head.weight", [151936, 1536], dtype)
        alias = (length == embedding_length and
                 source.data[head_offset:head_offset + length] ==
                 source.data[embedding_offset:embedding_offset + embedding_length])
    elif source.config.get("tie_word_embeddings") is True:
        alias = True
    else:
        raise ValueError("missing untied LM head")
    if alias:
        descriptors[1] = descriptors[0]
    else:
        plain(1, "lm_head.weight", 151936, 1536)
    plain(2, "model.norm.weight", 1, 1536)
    rope_length = 32768 * 128 * 4
    rope_base = allocate(rope_length, "explicit_q30_rope")
    descriptor(3, rope_base, rope_length, 32768, 128, 512, 3)
    checks = []
    for layer in range(28):
        prefix = f"model.layers.{layer}."
        for projection, suffix in enumerate(PROJECTIONS):
            rows = 256 if projection in (1, 2) else (8960 if projection in (4, 5) else 1536)
            cols = 8960 if projection == 6 else 1536
            tiles = ((rows + 15) // 16) * ((cols + 127) // 128)
            stride = 1024 if mode == "awq" else 4096
            base = allocate(tiles * stride, prefix + suffix)
            if mode == "awq":
                offset, _ = source.tensor(prefix + suffix + ".qweight", [cols, rows // 8], "I32")
                tasks.append(("W4", offset, rows, cols, base))
                groups = cols // 128
                zero_offset, _ = source.tensor(prefix + suffix + ".qzeros",
                                               [groups, rows // 8], "I32")
                scale_offset, _ = source.tensor(prefix + suffix + ".scales", [groups, rows], "F16")
                zero_stride = (groups + 1) // 2
                scale_stride = groups * 2
                zeros = allocate(rows * zero_stride, prefix + suffix + ".qzeros")
                scales = allocate(rows * scale_stride, prefix + suffix + ".scales")
                tasks += [("ZERO", zero_offset, rows, groups, zeros),
                          ("SCALE", scale_offset, rows, groups, scales)]
                descriptor(16 + 16 * layer + projection, base, tiles * stride, rows, cols, stride, 0,
                           zeros, scales, zero_stride, scale_stride)
            else:
                offset, _ = source.tensor(prefix + suffix + ".weight", [rows, cols], "BF16")
                tasks.append(("TBF16", offset, rows, cols, base))
                descriptor(16 + 16 * layer + projection, base, tiles * stride, rows, cols, stride, 2)
            checks.append({"layer": layer, "projection": projection, "entry": 16 + 16 * layer + projection,
                           "source_offset": offset, "rows": rows, "cols": cols})
        for slot, suffix in (
                (7, "input_layernorm.weight"), (8, "post_attention_layernorm.weight"),
                (9, "self_attn.q_proj.bias"), (10, "self_attn.k_proj.bias"), (11, "self_attn.v_proj.bias")):
            plain(16 + 16 * layer + slot, prefix + suffix, 1, 256 if slot in (10, 11) else 1536)
    unused = set(source.header) - source.used - {"__metadata__"}
    if unused:
        raise ValueError("unhandled official tensors: " + ", ".join(sorted(unused)))
    (directory / "pack.tasks").write_text("".join(" ".join(map(str, task)) + "\n" for task in tasks))
    (directory / "descriptors.bin").write_bytes(b"".join(descriptors))
    image_size = (cursor + 63) & ~63
    kv_bytes = 28 * 2 * 32768 * 2 * 128 * 4
    if image_size + kv_bytes > 8 * 1024 ** 3:
        raise ValueError("full default Q16 KV allocation overlaps/exceeds DDR")
    return {"mode": mode, "tied_embedding_alias": alias, "image_bytes": image_size,
            "rope_base": rope_base, "rope_bytes": rope_length,
            "allocations": allocations, "projection_checks": checks,
            "kv_base": image_size, "maximum_q16_kv_bytes": kv_bytes,
            "geometry": GEOMETRY, "source": {key: source.info[key]
                                             for key in ("repository", "revision", "license_metadata")}}


def inspect_packed(source, image_path, descriptors_path, info):
    descriptors = descriptors_path.read_bytes()
    permutation = (0, 4, 1, 5, 2, 6, 3, 7)
    rng = random.Random(101)
    compared = 0
    with image_path.open("rb") as stream:
        image = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            for check in info["projection_checks"]:
                entry = struct.unpack_from("<QQQQIIIIIIQ", descriptors, check["entry"] * 64)
                base, _, zeros, scales, rows, cols, _, zero_stride, scale_stride, _, _ = entry
                coords = {(row, col) for row in (0, 7, 8, 15, rows - 1)
                          for col in (0, 1, 7, 8, 127, 128, cols - 1)}
                coords.update((rng.randrange(rows), rng.randrange(cols)) for _ in range(256))
                for row, col in coords:
                    tile = (row // 16) * ((cols + 127) // 128) + col // 128
                    element = (row % 16) * 128 + col % 128
                    if info["mode"] == "awq":
                        address = check["source_offset"] + 4 * (col * (rows // 8) + row // 8)
                        word = struct.unpack_from("<I", source.data, address)[0]
                        expected = (word >> (4 * permutation[row % 8])) & 15
                        byte = image[base + tile * 1024 + element // 2]
                        if ((byte >> (4 * (element % 2))) & 15) != expected:
                            raise ValueError("AWQ tile permutation mismatch")
                        prefix = f"model.layers.{check['layer']}." + PROJECTIONS[check["projection"]]
                        zero_offset, _ = source.tensor(prefix + ".qzeros", [cols // 128, rows // 8], "I32")
                        scale_offset, _ = source.tensor(prefix + ".scales", [cols // 128, rows], "F16")
                        group = col // 128
                        packed_zero = struct.unpack_from("<I", source.data,
                            zero_offset + 4 * (group * (rows // 8) + row // 8))[0]
                        expected_zero = (packed_zero >> (4 * permutation[row % 8])) & 15
                        actual_zero = (image[zeros + row * zero_stride + group // 2] >>
                                       (4 * (group % 2))) & 15
                        expected_scale = struct.unpack_from("<H", source.data,
                                                            scale_offset + 2 * (group * rows + row))[0]
                        actual_scale = struct.unpack_from("<H", image,
                                                          scales + row * scale_stride + 2 * group)[0]
                        if actual_zero != expected_zero or actual_scale != expected_scale:
                            raise ValueError("AWQ zero/scale transpose mismatch")
                    else:
                        expected = struct.unpack_from("<H", source.data,
                            check["source_offset"] + 2 * (row * cols + col))[0]
                        actual = struct.unpack_from("<H", image, base + tile * 4096 + element * 2)[0]
                        if actual != expected:
                            raise ValueError("BF16 tensor word was not retained")
                    compared += 1
        finally:
            image.close()
    return compared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", choices=("awq", "bf16"), required=True)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    experiment = Experiment(root, args.output, sys.orig_argv,
        ["tests/checkpoint_import.py", "tests/checkpoint_pack.cpp", "tests/retention.py",
         "tests/rope_reference.py",
         "data/model/official_inputs.json", "data/model/" + args.mode + "__config.json"])
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    source = None
    try:
        experiment.run(["g++", "--version"], "compiler-version")
        source = Source(root, args.mode)
        info = prepare(source, args.mode, experiment.directory)
        experiment.run(["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                        str(args.output / "sources/tests/checkpoint_pack.cpp"),
                        "-o", str(args.output / "checkpoint_pack")], "compile")
        image = experiment.directory / "weights.ddr.bin"
        experiment.run([str(args.output / "checkpoint_pack"),
                        str(source.path.relative_to(root)), str(args.output / "pack.tasks"),
                        str(args.output / "weights.ddr.bin")], "pack")
        info["rope"] = write_table(image, info["rope_base"])
        with image.open("r+b") as stream:
            stream.truncate(info["image_bytes"])
        info["compared_packed_coordinates"] = inspect_packed(
            source, image, experiment.directory / "descriptors.bin", info)
        info["image_sha256"] = file_hash(image)
        info["descriptors_sha256"] = file_hash(experiment.directory / "descriptors.bin")
        info["scope"] = "official image packing/provenance, not RTL projection or full-token execution"
        (experiment.directory / "import.json").write_text(json.dumps(info, indent=2) + "\n")
        experiment.receipt["import"] = {key: value for key, value in info.items()
                                       if key not in ("allocations", "projection_checks")}
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1
    finally:
        if source is not None:
            source.close()


if __name__ == "__main__":
    raise SystemExit(main())
