"""Repack the pinned checkpoints into the frozen HT storage contract.

Run through ``python3 tests/verify.py --probe checkpoint-repack``. Output is
retained in that probe's fresh evidence directory. Each immutable descriptor
names separate logical and physical little-endian files. The upload recipe
contains only physical files and zero padding, never scratch/cache reservations.

BF16 projections retain their original bits. Embedding, bias and gamma use
FP16 storage in both modes: BF16 inputs convert by IEEE nearest-even binary16
rounding, with nonfinite/overflow rejected. Conversion differences are reported,
not described as exact BF16 software-model equivalence. Generated RoPE tables
use the checkpoint theta and ties-away Q2.30 rounding of binary64 sin/cos.
These table-generation semantics are explicit inputs to later reference/HIL
workloads, not a claim that the published floating-point model is reproduced.
"""

from array import array
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import project_path, validate


PROJECTIONS = ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
               "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")
BANK_BYTES = 1 << 33


def digest(data):
    return hashlib.sha256(data).hexdigest()


def words(data, width):
    result = array("H" if width == 2 else "I")
    if result.itemsize != width:
        raise RuntimeError("unsupported native array element width")
    result.frombytes(data)
    if sys.byteorder != "little":
        result.byteswap()
    return result


def little_bytes(values):
    if sys.byteorder == "little":
        return values.tobytes()
    copy = array(values.typecode, values)
    copy.byteswap()
    return copy.tobytes()


def transpose(values, rows, columns):
    if len(values) != rows * columns:
        raise ValueError("matrix element count mismatch")
    result = array(values.typecode, [0]) * len(values)
    for column in range(columns):
        result[column * rows:(column + 1) * rows] = values[column::columns]
    return result


def panels(values, rows, columns, width):
    if len(values) != rows * columns or width <= 0:
        raise ValueError("invalid panel shape")
    result = array(values.typecode)
    for start in range(0, columns, width):
        end = min(columns, start + width)
        for row in range(rows):
            result.extend(values[row * columns + start:row * columns + end])
    return result


def inverse_panels(values, rows, columns, width):
    result = array(values.typecode, [0]) * len(values)
    cursor = 0
    for start in range(0, columns, width):
        end = min(columns, start + width)
        for row in range(rows):
            count = end - start
            result[row * columns + start:row * columns + end] = values[cursor:cursor + count]
            cursor += count
    if cursor != len(values):
        raise AssertionError("inverse panel mapping does not conserve every element")
    return result


def mapping_selfcheck():
    compared = 0
    for rows in (1, 3, 7):
        for columns in (1, 8, 17, 64, 67, 128):
            source = array("I", range(rows * columns))
            expected_transpose = array("I", (row * columns + column
                                            for column in range(columns) for row in range(rows)))
            if transpose(source, rows, columns) != expected_transpose:
                raise AssertionError("transpose differs from independent coordinate equations")
            for width in (8, 64):
                result = panels(source, rows, columns, width)
                for row in range(rows):
                    for column in range(columns):
                        base = (column // width) * width
                        tail = min(width, columns - base)
                        offset = base * rows + row * tail + column - base
                        if result[offset] != row * columns + column:
                            raise AssertionError("physical panel offset differs from frozen equation")
                        compared += 1
                if inverse_panels(result, rows, columns, width) != source:
                    raise AssertionError("inverse mapping lost a logical coordinate")
    print(json.dumps({"mapping_selfcheck_compared_coordinates": compared}), flush=True)


def fp16_storage(raw, dtype):
    if dtype not in ("F16", "BF16"):
        raise ValueError(f"unsupported FP16 source dtype: {dtype}")
    counts = Counter(raw)
    converted = {}
    changed = 0
    max_difference = 0.0
    for bits, count in counts.items():
        exponent = (bits >> (10 if dtype == "F16" else 7)) & (31 if dtype == "F16" else 255)
        if exponent == (31 if dtype == "F16" else 255):
            raise ValueError("nonfinite immutable checkpoint value")
        if dtype == "F16":
            converted[bits] = bits
            continue
        value = struct.unpack("<f", struct.pack("<I", bits << 16))[0]
        try:
            encoded = struct.pack("<e", value)
        except OverflowError as exc:
            raise ValueError("finite BF16 value overflows the required FP16 storage") from exc
        converted[bits] = int.from_bytes(encoded, "little")
        restored = struct.unpack("<e", encoded)[0]
        if restored != value:
            changed += count
            max_difference = max(max_difference, abs(restored - value))
    result = raw if dtype == "F16" else array("H", (converted[value] for value in raw))
    return result, {"source_dtype": dtype, "storage_dtype": "F16",
                    "rounding": "IEEE binary16 nearest-even",
                    "compared_elements": len(raw), "changed_values": changed,
                    "maximum_absolute_storage_conversion_difference": max_difference}


class Checkpoint:
    def __init__(self, folder, model):
        self.path = folder / "model.safetensors"
        self.inventory = model["inventory"]
        self.used = set()

    def read(self, name):
        item = self.inventory["tensors"][name]
        start, end = item["data_offsets"]
        with self.path.open("rb") as source:
            source.seek(8 + self.inventory["header_bytes"] + start)
            data = source.read(end - start)
        if len(data) != end - start:
            raise ValueError(f"truncated checkpoint tensor: {name}")
        self.used.add(name)
        return item, data


class Image:
    def __init__(self, folder, mode, model):
        self.folder, self.mode, self.cursor = folder, mode, 0
        folder.mkdir(exist_ok=False)
        self.record = {
            "schema": 1, "mode": mode, "repository": model["repository"],
            "revision": model["revision"], "input_files": model["files"],
            "tensor_sha256": model["tensor_sha256"], "descriptors": [],
            "upload": [], "acceptance_evidence": False,
            "limitations": ["repacking and conversion identity only, not RTL inference",
                            "no floating-point software-model equivalence claim"],
        }

    def add(self, kind, layer, proj, logical_shape, logical, physical,
            source=None, conversion=None, packed=False):
        if kind == 0:
            vocab, hidden = logical_shape
            restored = inverse_panels(physical, hidden, vocab, 64)
            if transpose(restored, hidden, vocab) != logical:
                raise AssertionError("nonbijective tied-embedding repacking")
        elif kind in (1, 2, 3):
            width = 8 if packed else 64
            rows, columns = logical_shape
            if inverse_panels(physical, rows, columns, width) != logical:
                raise AssertionError(f"nonbijective tensor repacking: {source}")
        elif physical != logical:
            raise AssertionError("linear tensor mapping changed values")
        logical_data, physical_data = little_bytes(logical), little_bytes(physical)
        if len(logical_data) != len(physical_data):
            raise AssertionError("repacking changed tensor byte count")
        name = f"kind{kind}-layer{layer}-proj{proj}"
        logical_path, physical_path = name + "-logical.bin", name + "-physical.bin"
        (self.folder / logical_path).write_bytes(logical_data)
        (self.folder / physical_path).write_bytes(physical_data)
        logical_hash, physical_hash = digest(logical_data), digest(physical_data)
        if (digest((self.folder / logical_path).read_bytes()) != logical_hash or
                digest((self.folder / physical_path).read_bytes()) != physical_hash):
            raise AssertionError("persisted tensor file differs from checked repacking")
        entry = self.reserve(kind, layer, proj, len(physical_data), logical_shape)
        entry.update(source_tensor=source, source_conversion=conversion,
                     logical_file=logical_path, physical_file=physical_path,
                     logical_sha256=logical_hash, physical_sha256=physical_hash,
                     element_bytes=logical.itemsize, inverse_compared_elements=len(logical))
        self.record["upload"].append({
            "descriptor_index": entry["index"], "base": entry["base"],
            "file": physical_path, "file_bytes": len(physical_data),
            "sha256": entry["physical_sha256"],
            "zero_padding_bytes": entry["length_bytes"] - len(physical_data),
        })
        print(json.dumps({"mode": self.mode, "tensor": source or name,
                          "descriptor": entry["index"], "compared_elements": len(logical)}),
              flush=True)

    def reserve(self, kind, layer, proj, size, shape):
        if size <= 0 or self.cursor % 64:
            raise ValueError("invalid descriptor range")
        padded = (size + 63) & ~63
        if self.cursor + padded > BANK_BYTES:
            raise ValueError("model image exceeds the 8 GiB DDR bank")
        entry = {"index": ((layer * 12 + kind) * 8 + proj),
                 "kind": kind, "layer": layer, "proj": proj, "base": self.cursor,
                 "length_bytes": padded, "payload_bytes": size, "logical_shape": shape,
                 "immutable": kind not in (8, 9, 10)}
        self.cursor += padded
        self.record["descriptors"].append(entry)
        return entry

    def finish(self):
        expected = {0, 7 * 8, 8 * 8, 11 * 8}
        for layer in range(24):
            for kind in (1, 2, 3) if self.mode == "AWQ" else (1,):
                expected.update(((layer * 12 + kind) * 8 + proj) for proj in range(7))
            expected.update(((layer * 12 + 4) * 8 + proj) for proj in range(3))
            expected.update(((layer * 12 + kind) * 8) for kind in (5, 6, 9, 10))
        entries = self.record["descriptors"]
        observed = {entry["index"] for entry in entries}
        if observed != expected or len(observed) != len(entries):
            raise AssertionError("complete model descriptor set differs from frozen contract")
        previous = 0
        for entry in entries:
            if entry["base"] != previous or entry["length_bytes"] % 64:
                raise AssertionError("overlapping or unaligned descriptor regions")
            previous += entry["length_bytes"]
        self.record.update(bank_extent_bytes=self.cursor,
                           immutable_upload_bytes=sum(
                               entry["length_bytes"] for entry in entries if entry["immutable"]),
                           descriptor_count=len(entries),
                           inverse_compared_elements=sum(
                               entry.get("inverse_compared_elements", 0) for entry in entries))
        (self.folder / "descriptors.json").write_text(json.dumps(self.record, indent=2) + "\n")
        return self.record


def repack_model(root, output, mode, model):
    checkpoint = Checkpoint(root / mode.lower(), model)
    image = Image(output / mode.lower(), mode, model)
    config = json.loads((root / mode.lower() / "config.json").read_text())

    def linear(name, kind, layer=0, proj=0):
        item, data = checkpoint.read(name)
        converted, statistics = fp16_storage(words(data, 2), item["dtype"])
        image.add(kind, layer, proj, item["shape"], converted, converted,
                  name, statistics)

    name = "model.embed_tokens.weight"
    item, data = checkpoint.read(name)
    original_embedding_digest = digest(data)
    embedding, statistics = fp16_storage(words(data, 2), item["dtype"])
    logical_embedding = transpose(embedding, 151936, 896)
    if transpose(logical_embedding, 896, 151936) != embedding:
        raise AssertionError("embedding logical transpose changed checkpoint elements")
    image.add(0, 0, 0, [151936, 896], embedding,
              panels(logical_embedding, 896, 151936, 64), name, statistics)
    del data, embedding, logical_embedding
    if "lm_head.weight" in checkpoint.inventory["tensors"]:
        item, data = checkpoint.read("lm_head.weight")
        if (item["dtype"] != "F16" or item["shape"] != [151936, 896] or
                digest(data) != original_embedding_digest):
            raise ValueError("checkpoint lm_head is not bit-identical to tied embedding")
        image.record["tied_embedding_duplicate_sha256"] = digest(data)
        del data
    for layer in range(24):
        prefix = f"model.layers.{layer}."
        linear(prefix + "input_layernorm.weight", 5, layer)
        linear(prefix + "post_attention_layernorm.weight", 6, layer)
        for proj, projection in enumerate(PROJECTIONS):
            base = prefix + projection + "."
            for kind, suffix in (((1, "qweight"), (2, "qzeros"), (3, "scales"))
                                 if mode == "AWQ" else ((1, "weight"),)):
                name = base + suffix
                item, data = checkpoint.read(name)
                width = 4 if suffix in ("qweight", "qzeros") else 2
                values = words(data, width)
                rows, columns = item["shape"]
                if mode == "BF16":
                    if any((value & 0x7f80) == 0x7f80 for value in set(values)):
                        raise ValueError("nonfinite BF16 projection checkpoint value")
                    values = transpose(values, rows, columns)
                    if little_bytes(transpose(values, columns, rows)) != data:
                        raise AssertionError("BF16 transpose changed checkpoint bits")
                    rows, columns = columns, rows
                elif suffix == "scales":
                    for bits in set(values):
                        if bits & 0x7c00 == 0x7c00 or (bits & 0x8000 and bits & 0x7fff):
                            raise ValueError("invalid AWQ scale checkpoint encoding")
                panel_width = 8 if width == 4 else 64
                image.add(kind, layer, proj, [rows, columns], values,
                          panels(values, rows, columns, panel_width), name,
                          {"source_dtype": item["dtype"], "storage_dtype": item["dtype"],
                           "bit_preserving": True, "qzero_plus_one": False,
                           "packed_nibble_shifts": [0, 16, 4, 20, 8, 24, 12, 28]
                           if width == 4 else None}, packed=width == 4)
                del data, values
            if proj < 3:
                linear(base + "bias", 4, layer, proj)
    linear("model.norm.weight", 7)
    remaining = set(checkpoint.inventory["tensors"]) - checkpoint.used
    if remaining:
        raise ValueError(f"unmapped checkpoint tensors: {sorted(remaining)}")
    theta = config["rope_theta"]
    if not isinstance(theta, (int, float)) or not math.isfinite(theta) or theta <= 0:
        raise ValueError("invalid checkpoint RoPE theta")
    rope = array("I")
    frequencies = [theta ** (-2 * pair / 64) for pair in range(32)]
    for position in range(32768):
        for frequency in frequencies:
            angle = position * frequency
            for value in (math.cos(angle), math.sin(angle)):
                magnitude = math.floor(abs(value) * (1 << 30) + 0.5)
                rope.append((-magnitude if value < 0 else magnitude) & 0xffffffff)
    image.add(11, 0, 0, [32768, 64], rope, rope,
              conversion={"generator": "binary64 theta**(-2*pair/64), position multiply, "
                                      "libm cos/sin, Q2.30 nearest ties-away",
                          "rope_theta": theta, "python_version": sys.version})
    image.reserve(8, 0, 0, 15 * 4864 * 4, [15, 4864])
    for layer in range(24):
        for kind in (9, 10):
            image.reserve(kind, layer, 0, 32768 * 128 * 4, [32768, 128])
    return image.finish()


def repack(evidence):
    root = Path("fixtures/qwen2.5-0.5b")
    evidence.command(["python3", "tests/fixtures.py"], "repack-fixture-validation")
    output = evidence.folder / "checkpoint-images"
    evidence.command(
        ["python3", "tests/repack.py", "--root", str(root),
         "--output", evidence.relative(output)], "checkpoint-repacking", timeout=14400)
    for mode in ("AWQ", "BF16"):
        path = output / mode.lower() / "descriptors.json"
        record = json.loads(path.read_text())
        if record["inverse_compared_elements"] <= 0 or not record["upload"]:
            raise AssertionError("checkpoint repacking contains no observed inverse comparisons")
        evidence.record["observations"].append({
            "scope": "checkpoint_repacking_not_model_inference",
            "mode": mode, "descriptor_manifest": evidence.relative(path),
            "descriptor_manifest_sha256": digest(path.read_bytes()),
            "descriptor_count": record["descriptor_count"],
            "inverse_compared_elements": record["inverse_compared_elements"],
            "immutable_upload_bytes": record["immutable_upload_bytes"],
            "bank_extent_bytes": record["bank_extent_bytes"],
        })
    evidence.flush()


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=project_path, required=True)
    parser.add_argument("--output", type=project_path, required=True)
    args = parser.parse_args()
    mapping_selfcheck()
    manifest = validate(args.root)
    args.output.mkdir(parents=True, exist_ok=False)
    for mode, model in manifest["models"].items():
        repack_model(args.root, args.output, mode, model)


if __name__ == "__main__":
    main()
