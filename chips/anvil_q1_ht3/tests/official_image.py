"""Streaming official BF16 checkpoint packing for the inherited memory ABI."""

import json
import math

import numpy as np

from execution import ROOT, hashes, relative
from official_reference import Checkpoint
from retention import digest


DEPENDENCIES = ("tests/official_image.py", "tests/official_reference.py",
                "tests/official_inputs.json", "design/SPEC.md")


def codes(checkpoint, name, shape):
    row = checkpoint.entries[name]
    if row["dtype"] != "BF16" or row["shape"] != list(shape):
        raise ValueError(f"official BF16 tensor layout mismatch: {name}")
    start, end = row["data_offsets"]
    return checkpoint.mapping[checkpoint.offset+start:checkpoint.offset+end].view("<u2").reshape(shape)


def panel_bytes(matrix):
    """Panel, input column, 64 ascending output rows; native words are LE."""
    for start in range(0, matrix.shape[0], 64):
        block = matrix[start:start+64]
        if np.any((block & 0x7f80) == 0x7f80):
            raise ValueError("nonfinite active official weight")
        packed = np.zeros((matrix.shape[1], 64), dtype="<u2")
        packed[:, :len(block)] = block.T
        yield packed.tobytes()


def check_panel(image, base, matrix):
    """Decode independently by physical byte address, checking every code/pad."""
    rows, columns = matrix.shape
    for panel in range(math.ceil(rows/64)):
        count = min(64, rows-64*panel)
        image.seek(base+panel*columns*128)
        payload = image.read(columns*128)
        if len(payload) != columns*128:
            raise AssertionError("short official packed panel")
        words = np.frombuffer(payload, dtype="<u2").reshape(columns, 64)
        if (not np.array_equal(words[:, :count].T, matrix[64*panel:64*panel+count])
                or np.any(words[:, count:])):
            raise AssertionError("official image panel code, row/column order or padding mismatch")


def layout(config):
    h, intermediate = config["hidden_size"], config["intermediate_size"]
    layers, vocab = config["num_hidden_layers"], config["vocab_size"]
    dimension = h//config["num_attention_heads"]
    kv = config["num_key_value_heads"]*dimension
    seq = config["max_position_embeddings"]
    if (h, intermediate, layers, vocab, dimension, kv, seq) != (
            896, 4864, 24, 151936, 64, 128, 32768):
        raise ValueError("image geometry must be the full pinned Qwen checkpoint")
    regions, offset = [], 0

    def region(kind, layer, projection, shape=None, tensor=None, zero_bytes=None):
        nonlocal offset
        size = (math.ceil(shape[0]/64)*shape[1]*128 if shape and len(shape) == 2
                else math.prod(shape)*2 if shape else zero_bytes)
        length = (size+63)//64*64
        regions.append(dict(index=96*layer+8*kind+projection, kind=kind, layer=layer,
                            projection=projection, base=offset, length=length,
                            active_bytes=size, shape=shape, tensor=tensor))
        offset += length

    region(0, 0, 0, (vocab, h), "model.embed_tokens.weight")
    projections = ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
                   "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")
    shapes = ((h,h), (kv,h), (kv,h), (h,h), (intermediate,h),
              (intermediate,h), (h,intermediate))
    for layer in range(layers):
        prefix = f"model.layers.{layer}."
        for projection, (name, shape) in enumerate(zip(projections, shapes)):
            region(1, layer, projection, shape, prefix+name+".weight")
        for projection, rows in enumerate((h, kv, kv)):
            region(4, layer, projection, (rows,), prefix+projections[projection]+".bias")
        region(5, layer, 0, (h,), prefix+"input_layernorm.weight")
        region(6, layer, 0, (h,), prefix+"post_attention_layernorm.weight")
        for kind in (9, 10):
            region(kind, layer, 0, zero_bytes=seq*((2*kv+63)//64*64))
    region(7, 0, 0, (h,), "model.norm.weight")
    region(8, 0, 0, zero_bytes=15*max(h, intermediate)*4)
    region(11, 0, 0, zero_bytes=seq*dimension*4)
    if offset > 1 << 33 or len({r["index"] for r in regions}) != len(regions):
        raise AssertionError("official image address or descriptor identity overflow")
    return regions, offset


def build(directory, checkpoint_path, config_path, checkpoint_sha256):
    if digest(checkpoint_path) != checkpoint_sha256:
        raise AssertionError("official checkpoint hash mismatch before image packing")
    config = json.loads(config_path.read_text())
    checkpoint = Checkpoint(checkpoint_path)
    regions, length = layout(config)
    directory.mkdir()
    image_path = directory/"image.bin"
    with image_path.open("xb") as image:
        for region in regions:
            image.seek(region["base"])
            if region["tensor"] is not None:
                matrix = codes(checkpoint, region["tensor"], region["shape"])
                if matrix.ndim == 2:
                    for payload in panel_bytes(matrix):
                        image.write(payload)
                else:
                    if np.any((matrix & 0x7f80) == 0x7f80):
                        raise ValueError("nonfinite official bias/norm gamma")
                    image.write(matrix.tobytes())
                image.write(bytes(region["length"]-region["active_bytes"]))
            # Zero-filled cache/reservations are sparse extents, not missing data.
            image.seek(region["base"]+region["length"])
        image.truncate(length)
    checked_codes, zero_bytes = 0, 0
    with image_path.open("rb") as image:
        for region in regions:
            if region["tensor"] is not None:
                matrix = codes(checkpoint, region["tensor"], region["shape"])
                if matrix.ndim == 2:
                    check_panel(image, region["base"], matrix)
                else:
                    image.seek(region["base"])
                    if image.read(matrix.size*2) != matrix.tobytes():
                        raise AssertionError("official bias/norm image mismatch")
                checked_codes += matrix.size
                image.seek(region["base"]+region["active_bytes"])
                if any(image.read(region["length"]-region["active_bytes"])):
                    raise AssertionError("nonzero official descriptor padding")
            else:
                image.seek(region["base"])
                left = region["length"]
                while left:
                    payload = image.read(min(left, 1024*1024))
                    if not payload or any(payload):
                        raise AssertionError("official cache/reservation extent not zero")
                    left -= len(payload)
                    zero_bytes += len(payload)
    current = hashes()
    result = dict(status="passed", scope="checkpoint packing/readback, not RTL inference",
                  format=0, extension_control=0, geometry=config,
                  image=relative(image_path), image_bytes=length, image_sha256=digest(image_path),
                  checkpoint_sha256=checkpoint_sha256, config_sha256=digest(config_path),
                  source_sha256={p: current[p] for p in DEPENDENCIES},
                  checked_codes=int(checked_codes), checked_zero_bytes=zero_bytes,
                  descriptors=regions)
    with (directory/"image-manifest.json").open("x") as out:
        json.dump(result, out, indent=2)
    return result
