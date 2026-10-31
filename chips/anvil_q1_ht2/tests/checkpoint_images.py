#!/usr/bin/env python3
"""Streaming checkpoint-to-HT2 conversion and independent image comparison.

Tensor records name official BF16 row-major tensors, shape, dtype and an
artifact. storage is raw_le (exact tensor bytes) or safetensors (named tensor
inside the hash-bound container). W4 provenance supplies quantized_tensors:
name plus q, zero and scale tensor records. q/zero are row-major U8 values
0..15 with shapes [outputs, inputs] / [outputs, inputs/128]; scale is FP16
with the latter shape. No quantization or calibration is invented here.

Image descriptors are {index,kind,layer,projection,base,length}. Each image
tensor maps descriptor_index to a raw binary artifact including padding.
Layout identity is ht2-panel-major-column-64-v1. validate_image compares every
converted byte, including padding and scratch/KV zeros, to checkpoint-derived
streams; an asserted conversion receipt or layout label alone cannot pass.

Portable conversion:
python3 tests/checkpoint_images.py --inputs inputs.json --mode bf16
The externally supplied manifest must already identify the official checkpoint
and frozen AWQ provenance. Output uses a fresh official-image-* evidence group.
"""

import argparse
import contextlib
import hashlib
import mmap
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmark_manifest import DEFAULT_GEOMETRY
from evidence import digest, execute, fresh, relative, require_success, write_json
import hardware_workload as bridge


LAYOUT = "ht2-panel-major-column-64-v1"
PROJECTIONS = ("self_attn.q_proj.weight", "self_attn.k_proj.weight",
               "self_attn.v_proj.weight", "self_attn.o_proj.weight",
               "mlp.gate_proj.weight", "mlp.up_proj.weight", "mlp.down_proj.weight")


def expected_shapes(g=DEFAULT_GEOMETRY):
    h, inter, kv = g["HIDDEN_SIZE"], g["INTERMEDIATE_SIZE"], g["NUM_KV_HEADS"] * g["HEAD_DIM"]
    result = {"model.embed_tokens.weight": [g["VOCAB_SIZE"], h], "model.norm.weight": [h]}
    for layer in range(g["NUM_LAYERS"]):
        prefix = f"model.layers.{layer}."
        result.update({prefix + key: [rows, columns] for key, rows, columns in zip(
            PROJECTIONS, (h, kv, kv, h, inter, inter, h), (h, h, h, h, h, h, inter))})
        result.update({prefix + "self_attn." + key + "_proj.bias": [width]
                       for key, width in (("q", h), ("k", kv), ("v", kv))})
        for key in ("input_layernorm.weight", "post_attention_layernorm.weight"):
            result[prefix + key] = [h]
    return result


class Tensor:
    def __init__(self, record, stack):
        self.record = record
        path = bridge.artifact(record["artifact"])
        stream = stack.enter_context(path.open("rb"))
        if path.stat().st_size == 0:
            raise ValueError("empty checkpoint tensor artifact")
        self.data = stack.enter_context(mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ))
        self.dtype, self.shape = record["dtype"], record["shape"]
        if self.dtype not in ("BF16", "FP16", "U8") or not self.shape:
            raise ValueError("unsupported tensor storage/dtype")
        elements = 1
        for dimension in self.shape:
            bridge.positive(bridge.uint(dimension, "tensor shape"), "tensor shape")
            elements *= dimension
        self.width = 1 if self.dtype == "U8" else 2
        self.offset = 0
        if record.get("storage") == "safetensors":
            if len(self.data) < 8:
                raise ValueError("truncated safetensors header")
            header_length = struct.unpack_from("<Q", self.data)[0]
            if header_length > 100000000 or header_length + 8 > len(self.data):
                raise ValueError("invalid safetensors header length")
            import json
            def unique(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError("duplicate safetensors tensor/key")
                    result[key] = value
                return result
            header = json.loads(self.data[8:8 + header_length], object_pairs_hook=unique)
            entry = header[record["name"]]
            dtype = {"BF16": "BF16", "FP16": "F16", "U8": "U8"}[self.dtype]
            begin, end = entry["data_offsets"]
            bridge.uint(begin, "safetensors begin")
            bridge.uint(end, "safetensors end")
            if (entry["dtype"] != dtype or entry["shape"] != self.shape or
                end - begin != elements * self.width or 8 + header_length + end > len(self.data)):
                raise ValueError("checkpoint header shape/dtype/length mismatch")
            self.offset = 8 + header_length + begin
        elif record.get("storage") != "raw_le" or len(self.data) != elements * self.width:
            raise ValueError("raw tensor storage/length mismatch")
        self.elements = elements

    def at(self, row, column=0):
        index = row * (self.shape[1] if len(self.shape) == 2 else 1) + column
        if not 0 <= index < self.elements:
            raise ValueError("tensor conversion index overflow")
        offset = self.offset + index * self.width
        return self.data[offset] if self.width == 1 else struct.unpack_from("<H", self.data, offset)[0]

    def validate_values(self):
        end = self.offset + self.elements * self.width
        for begin in range(self.offset, end, 1048576):
            part = self.data[begin:min(end, begin + 1048576)]
            if self.dtype == "U8":
                if any(value > 15 for value in part):
                    raise ValueError("AWQ weight/zero outside unsigned nibble range")
            else:
                exponent = 0x7F80 if self.dtype == "BF16" else 0x7C00
                for (value,) in struct.iter_unpack("<H", part):
                    if value & exponent == exponent:
                        raise ValueError("nonfinite checkpoint/scale value")
                    if self.dtype == "FP16" and value & 0x8000 and value & 0x7FFF:
                        raise ValueError("negative AWQ scale")


def inventory(model, stack, g=DEFAULT_GEOMETRY):
    records = model["tensors"]
    keyed = {item["name"]: item for item in records}
    expected = expected_shapes(g)
    if len(keyed) != len(records) or set(keyed) != set(expected):
        raise ValueError("official checkpoint tensor inventory mismatch (tied head required)")
    tensors = {}
    for name, shape in expected.items():
        record = keyed[name]
        if record["shape"] != shape or record["dtype"] != "BF16":
            raise ValueError(f"official checkpoint tensor shape/dtype mismatch: {name}")
        tensor = Tensor(record, stack)
        tensor.validate_values()
        tensors[name] = tensor
    return tensors


def quantized_inventory(document, stack, g=DEFAULT_GEOMETRY):
    records = document["quantized_tensors"]
    keyed = {item["name"]: item for item in records}
    expected = {name: shape for name, shape in expected_shapes(g).items()
                if any(name.endswith(key) for key in PROJECTIONS)}
    if len(keyed) != len(records) or set(keyed) != set(expected):
        raise ValueError("AWQ quantized tensor inventory mismatch")
    result = {}
    for name, (rows, columns) in expected.items():
        fields = {}
        for field in ("q", "zero", "scale"):
            record = keyed[name][field]
            shape = [rows, columns if field == "q" else columns // g["GROUP_SIZE"]]
            if record["shape"] != shape or record["dtype"] != ("FP16" if field == "scale" else "U8"):
                raise ValueError(f"AWQ tensor shape/dtype mismatch: {name}/{field}")
            fields[field] = Tensor(record, stack)
            fields[field].validate_values()
        result[name] = fields
    return result


def awq_pack(values):
    words = [0] * 8
    for lane, value in enumerate(values):
        # Independent published nibble order, not a call into the seeded fixture.
        index = lane % 8
        nibble = (index % 2) * 4 + index // 2
        words[lane // 8] |= value << (4 * nibble)
    return struct.pack("<8I", *words) + bytes(32)


def panel(tensor):
    rows, columns = tensor.shape
    for base in range(0, rows, 64):
        for column in range(columns):
            yield struct.pack("<64H", *(tensor.at(row, column) if row < rows else 0
                                       for row in range(base, base + 64)))


def vector(tensor):
    data = bytes(tensor.data[tensor.offset:tensor.offset + tensor.elements * 2])
    yield data + bytes((-len(data)) % 64)


def zeros(length):
    for offset in range(0, length, 65536):
        yield bytes(min(65536, length - offset))


def streams(tensors, quantized, mode, g=DEFAULT_GEOMETRY):
    """Yield ABI identity, exact length and bounded binary chunks."""
    h, inter = g["HIDDEN_SIZE"], g["INTERMEDIATE_SIZE"]
    kv = g["NUM_KV_HEADS"] * g["HEAD_DIM"]
    def item(kind, layer, projection, length, chunks):
        return {"index": 96 * layer + 8 * kind + projection, "kind": kind,
                "layer": layer, "projection": projection, "length": length}, chunks
    yield item(0, 0, 0, ((g["VOCAB_SIZE"] + 63) // 64) * h * 128,
               panel(tensors["model.embed_tokens.weight"]))
    for layer in range(g["NUM_LAYERS"]):
        prefix = f"model.layers.{layer}."
        for projection, suffix in enumerate(PROJECTIONS):
            name = prefix + suffix
            rows, columns = tensors[name].shape
            panels = (rows + 63) // 64
            if mode == "bf16":
                yield item(1, layer, projection, panels * columns * 128, panel(tensors[name]))
            else:
                fields = quantized[name]
                groups = columns // g["GROUP_SIZE"]
                def encoded(field, fields=fields, rows=rows, columns=columns, groups=groups):
                    for base in range(0, rows, 64):
                        for column in range(columns if field == "q" else groups):
                            values = [fields[field].at(row, column) if row < rows else 0
                                      for row in range(base, base + 64)]
                            yield struct.pack("<64H", *values) if field == "scale" else awq_pack(values)
                for kind, field, length in ((1, "q", panels * columns * 64),
                                            (2, "zero", panels * groups * 64),
                                            (3, "scale", panels * groups * 128)):
                    yield item(kind, layer, projection, length, encoded(field))
        for projection, key, width in ((0, "q", h), (1, "k", kv), (2, "v", kv)):
            yield item(4, layer, projection, ((width * 2 + 63) // 64) * 64,
                       vector(tensors[prefix + f"self_attn.{key}_proj.bias"]))
        for kind, suffix in ((5, "input_layernorm.weight"), (6, "post_attention_layernorm.weight")):
            yield item(kind, layer, 0, ((2 * h + 63) // 64) * 64, vector(tensors[prefix + suffix]))
        for kind in (9, 10):
            length = g["MAX_SEQ_LEN"] * ((2 * kv + 63) // 64) * 64
            yield item(kind, layer, 0, length, zeros(length))
    for kind, length, chunks in (
        (7, ((2 * h + 63) // 64) * 64, vector(tensors["model.norm.weight"])),
        (8, ((15 * max(h, inter) * 4 + 63) // 64) * 64,
         zeros(((15 * max(h, inter) * 4 + 63) // 64) * 64)),
        (11, ((g["MAX_SEQ_LEN"] * g["HEAD_DIM"] * 4 + 63) // 64) * 64,
         zeros(((g["MAX_SEQ_LEN"] * g["HEAD_DIM"] * 4 + 63) // 64) * 64))):
        yield item(kind, 0, 0, length, chunks)


def compare_or_write(tensors, quantized, mode, image=None, directory=None, g=DEFAULT_GEOMETRY):
    descriptors, artifacts, intervals = [], [], []
    supplied = {} if image is None else {item["index"]: item for item in image["descriptors"]}
    supplied_data = {} if image is None else {
        item["descriptor_index"]: item for item in image["tensors"]}
    if image is not None and (image["layout"] != LAYOUT or
                             len(supplied) != len(image["descriptors"]) or
                             len(supplied_data) != len(image["tensors"])):
        raise ValueError("converted image layout/duplicate descriptor mismatch")
    address = 4096
    for descriptor, chunks in streams(tensors, quantized, mode, g):
        index, length = descriptor["index"], descriptor["length"]
        descriptor["base"] = address if image is None else supplied[index]["base"]
        base = bridge.uint(descriptor["base"], "descriptor base", (1 << 33) - 1)
        if base % 64 or base + length > 1 << 33:
            raise ValueError("converted descriptor address overflow/alignment")
        intervals.append((base, base + length))
        if image is not None:
            if supplied[index] != descriptor:
                raise ValueError("converted descriptor geometry/identity mismatch")
            path = bridge.artifact(supplied_data[index]["artifact"])
            if path.stat().st_size != length:
                raise ValueError("converted descriptor binary length mismatch")
        else:
            path = directory / f"descriptor-{index:04d}.bin"
        count, digest_expected = 0, hashlib.sha256()
        with path.open("rb" if image is not None else "xb") as stream:
            for chunk in chunks:
                digest_expected.update(chunk)
                count += len(chunk)
                if image is None:
                    stream.write(chunk)
                elif stream.read(len(chunk)) != chunk:
                    raise ValueError(f"checkpoint-to-image byte mismatch at descriptor {index}")
        if count != length:
            raise ValueError("converter generated wrong descriptor length")
        descriptors.append(descriptor)
        artifacts.append({"descriptor_index": index,
                          "artifact": {"path": relative(path), "sha256": digest_expected.hexdigest()}})
        address = base + length
    if image is not None and (set(supplied) != {item["index"] for item in descriptors} or
                              set(supplied_data) != set(supplied)):
        raise ValueError("missing/extra converted descriptor")
    intervals.sort()
    if any(left[1] > right[0] for left, right in zip(intervals, intervals[1:])):
        raise ValueError("converted tensor intervals overlap")
    return descriptors, artifacts


def validate_images(document):
    with contextlib.ExitStack() as stack:
        tensors = inventory(document["model"], stack)
        quantization = bridge.load_json(bridge.artifact(document["awq_provenance"]))
        quantized = quantized_inventory(quantization, stack)
        for mode in ("bf16", "w4"):
            image = bridge.load_json(bridge.artifact(document["images"][mode]))
            compare_or_write(tensors, quantized, mode, image=image)


def convert(manifest, mode, directory):
    document = bridge.load_json(bridge.project_path(manifest))
    with contextlib.ExitStack() as stack:
        tensors = inventory(document["model"], stack)
        quantized = (quantized_inventory(bridge.load_json(bridge.artifact(
            document["awq_provenance"])), stack) if mode == "w4" else {})
        descriptors, artifacts = compare_or_write(tensors, quantized, mode, directory=directory)
    write_json(directory / "image.json", {
        "schema_version": 1, "layout": LAYOUT, "mode": mode, "geometry": DEFAULT_GEOMETRY,
        "model_revision": document["model"]["revision"],
        "config_sha256": document["model"]["config"]["sha256"],
        "descriptors": descriptors, "tensors": artifacts,
        "source_manifest": {"path": manifest, "sha256": digest(bridge.project_path(manifest))}})


def selfcheck(directory):
    """Compare conversion to the independently authored seeded image writer."""
    from decoder_reference import Geometry, Image
    import uuid
    g = Geometry()
    geometry = {**DEFAULT_GEOMETRY, **g.parameters()}
    comparisons, rejections = 0, []
    for mode_name, mode in (("bf16", 0), ("w4", 2)):
        work = directory / f"conversion-{mode_name}-{uuid.uuid4().hex[:8]}"
        work.mkdir()
        image = Image(g, mode, 17)
        records = []
        def tensor(name, shape, dtype, values):
            path = work / (name.replace(".", "_") + ".bin")
            path.write_bytes(bytes(values) if dtype == "U8" else
                             b"".join(struct.pack("<H", word) for word in values))
            return {"name": name, "shape": shape, "dtype": dtype, "storage": "raw_le",
                    "artifact": {"path": relative(path), "sha256": digest(path)}}
        for name, shape in expected_shapes(geometry).items():
            if name == "model.embed_tokens.weight":
                values = [value for row in image.embedding for value in row]
            elif name == "model.norm.weight":
                values = image.norms[7, 0]
            else:
                parts = name.split(".")
                layer = int(parts[2])
                suffix = ".".join(parts[3:])
                if suffix in PROJECTIONS:
                    values = [value for row in image.weights[layer, PROJECTIONS.index(suffix)] for value in row]
                elif suffix.endswith(".bias"):
                    projection = ("q", "k", "v").index(suffix.split(".")[1][0])
                    values = image.biases[layer, projection]
                else:
                    values = image.norms[5 if suffix == "input_layernorm.weight" else 6, layer]
            records.append(tensor(name, shape, "BF16", values))
        quantized_records = []
        if mode == 2:
            for name, shape in expected_shapes(geometry).items():
                suffix = ".".join(name.split(".")[3:])
                if suffix not in PROJECTIONS:
                    continue
                layer, projection = int(name.split(".")[2]), PROJECTIONS.index(suffix)
                descriptors = {entry[1]: entry for entry in image.descriptors
                               if entry[2:4] == (layer, projection) and entry[1] in (1, 2, 3)}
                def nibble(kind, row, column):
                    base = descriptors[kind][4] + (row // 64 * shape[1] + column) * 64
                    # Literal inverse table independent of converter awq_pack.
                    offsets = (0, 16, 4, 20, 8, 24, 12, 28)
                    word = struct.unpack_from("<I", image.memory, base + row % 64 // 8 * 4)[0]
                    return (word >> offsets[row % 8]) & 15
                fields = {"name": name}
                for field, kind in (("q", 1), ("zero", 2), ("scale", 3)):
                    columns = shape[1] if field == "q" else shape[1] // g.group
                    values = []
                    for row in range(shape[0]):
                        for column in range(columns):
                            if field == "scale":
                                offset = descriptors[kind][4] + (
                                    row // 64 * columns + column) * 128 + row % 64 * 2
                                values.append(struct.unpack_from("<H", image.memory, offset)[0])
                            else:
                                values.append(nibble(kind, row, column))
                    fields[field] = tensor(name + "-" + field, [shape[0], columns],
                                           "FP16" if field == "scale" else "U8", values)
                quantized_records.append(fields)
        with contextlib.ExitStack() as stack:
            tensors = inventory({"tensors": records}, stack, geometry)
            quantized = quantized_inventory({"quantized_tensors": quantized_records}, stack, geometry) if mode == 2 else {}
            entries, artifacts = [], []
            for index, kind, layer, projection, base, length in image.descriptors:
                entries.append(dict(index=index, kind=kind, layer=layer,
                                    projection=projection, base=base, length=length))
                path = work / f"expected-{index:04d}.bin"
                expected_bytes = bytearray(image.memory[base:base + length])
                if mode == 2 and kind in (1, 2, 3):
                    rows = len(image.weights[layer, projection])
                    stride = 128 if kind == 3 else 64
                    for offset in range(0, length, stride):
                        for row in range(rows, 64):
                            if kind == 3:
                                struct.pack_into("<H", expected_bytes, offset + row * 2, 0)
                            else:
                                word_offset = offset + row // 8 * 4
                                word = struct.unpack_from("<I", expected_bytes, word_offset)[0]
                                shift = (0, 16, 4, 20, 8, 24, 12, 28)[row % 8]
                                struct.pack_into("<I", expected_bytes, word_offset, word & ~(15 << shift))
                path.write_bytes(expected_bytes)
                artifacts.append({"descriptor_index": index,
                                  "artifact": {"path": relative(path), "sha256": digest(path)}})
            converted = {"layout": LAYOUT, "descriptors": entries, "tensors": artifacts}
            actual, _ = compare_or_write(tensors, quantized, mode_name, image=converted, g=geometry)
            comparisons += len(actual)
            import copy
            for defect in ("descriptor", "overlap", "bytes"):
                bad = copy.deepcopy(converted)
                if defect == "descriptor":
                    bad["descriptors"][0]["length"] += 64
                elif defect == "overlap":
                    bad["descriptors"][1]["base"] = bad["descriptors"][0]["base"]
                else:
                    original = bridge.artifact(bad["tensors"][0]["artifact"]).read_bytes()
                    path = work / "wrong-embedding.bin"
                    path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
                    bad["tensors"][0]["artifact"] = {"path": relative(path), "sha256": digest(path)}
                try:
                    compare_or_write(tensors, quantized, mode_name, image=bad, g=geometry)
                except ValueError:
                    rejections.append(mode_name + "-" + defect)
                else:
                    raise AssertionError("checkpoint conversion defect escaped: " + defect)
    if comparisons == 0 or len(rejections) != 6:
        raise AssertionError("empty checkpoint conversion coverage")
    return {"name": "checkpoint-conversion", "compared_descriptors": comparisons,
            "rejections": rejections, "scope": "compact independent converter fixtures"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True)
    parser.add_argument("--mode", choices=("bf16", "w4"), required=True)
    parser.add_argument("--output", help=argparse.SUPPRESS)
    options = parser.parse_args()
    if options.output:
        convert(options.inputs, options.mode, bridge.project_path(options.output))
    else:
        output = fresh("official-image-" + options.mode)
        require_success(execute(
            ["python3", "tests/checkpoint_images.py", "--inputs", options.inputs,
             "--mode", options.mode, "--output", relative(output)], output,
            "checkpoint-conversion", timeout=2400,
            inputs=[bridge.project_path(options.inputs)]))
        print(relative(output / "image.json"))
