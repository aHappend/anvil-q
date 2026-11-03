"""Streaming local safetensors importer; no network, torch or credentials required.

AutoAWQ GEMM packs logical lanes [0,2,4,6,1,3,5,7] into successive nibbles.
Their inverse bit shifts [0,16,4,20,8,24,12,28] are exactly the image ABI.
GEMV, Marlin, GPTQ and implicit zero-code offsets are not interchangeable.
"""

from contextlib import ExitStack
import hashlib
import json
import math
import mmap
from pathlib import Path
import struct

from model import BASES, PRODUCTION, Geometry, Image, image_layout


PROJECTIONS = ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
               "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")
CHUNK = 1 << 20


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def local_path(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or any(
            name in (".vulcan", ".git", ".tooling", "VULCAN") for name in path.relative_to(root).parts):
        raise ValueError("checkpoint and output paths must be public project-relative paths")
    return path


class SafeTensors:
    def __init__(self, directory, stack):
        self.tensors = {}
        self.files = {}
        shards = sorted(directory.glob("*.safetensors"))
        if not shards:
            raise FileNotFoundError("checkpoint has no *.safetensors")
        for path in shards:
            stream = stack.enter_context(path.open("rb"))
            view = stack.enter_context(mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ))
            if len(view) < 8:
                raise ValueError(f"truncated safetensors: {path.name}")
            length = struct.unpack_from("<Q", view)[0]
            if length > min(len(view) - 8, 100_000_000):
                raise ValueError(f"invalid safetensors header: {path.name}")
            header = json.loads(view[8:8 + length])
            end_header = 8 + length
            spans = []
            for name, info in header.items():
                if name == "__metadata__":
                    continue
                if name in self.tensors:
                    raise ValueError(f"duplicate tensor: {name}")
                shape, dtype = info["shape"], info["dtype"]
                if dtype not in ("I32", "F16", "BF16", "F32"):
                    raise ValueError(f"unsupported tensor dtype {dtype}: {name}")
                if not shape or any(not isinstance(size, int) or size <= 0 for size in shape):
                    raise ValueError(f"invalid tensor shape: {name}")
                start, end = info["data_offsets"]
                size = math.prod(shape) * (4 if dtype in ("I32", "F32") else 2)
                if not 0 <= start <= end <= len(view) - end_header or end - start != size:
                    raise ValueError(f"invalid tensor extent: {name}")
                spans.append((start, end))
                self.tensors[name] = (view, end_header + start, end_header + end, dtype, shape)
            spans.sort()
            if (not spans or spans[0][0] != 0 or spans[-1][1] != len(view) - end_header
                    or any(left[1] != right[0] for left, right in zip(spans, spans[1:]))):
                raise ValueError(f"overlapping or incomplete safetensors storage: {path.name}")
            self.files[path.name] = digest_file(path)

    def get(self, name, shape, dtype=None):
        if name not in self.tensors:
            raise ValueError(f"missing checkpoint tensor: {name}")
        view, start, end, actual_dtype, actual_shape = self.tensors[name]
        if list(shape) != actual_shape or (dtype is not None and dtype != actual_dtype):
            raise ValueError(f"tensor shape/dtype mismatch: {name}")
        return view, start, end, actual_dtype


def half_blocks(tensor, nonnegative=False):
    view, start, end, dtype = tensor
    step = 4 if dtype == "F32" else 2
    for offset in range(start, end, CHUNK):
        data = view[offset:min(end, offset + CHUNK)]
        if dtype == "BF16":
            values = [struct.unpack("<f", b"\0\0" + data[i:i + 2])[0]
                      for i in range(0, len(data), 2)]
        elif dtype in ("F16", "F32"):
            values = [value for (value,) in struct.iter_unpack("<e" if step == 2 else "<f", data)]
        else:
            raise ValueError(f"expected floating point tensor, got {dtype}")
        if any(not math.isfinite(value) or (nonnegative and value < 0) for value in values):
            raise ValueError("nonfinite tensor value or negative AWQ scale")
        try:
            yield (data if dtype == "F16" else
                   b"".join(struct.pack("<e", value) for value in values))
        except OverflowError as error:
            raise ValueError("checkpoint value does not fit binary16 image storage") from error


def import_checkpoint(root, checkpoint, output, revision, synthetic=False):
    root = Path(root).resolve()
    directory = local_path(root, checkpoint)
    output = local_path(root, output)
    if not directory.is_dir():
        raise FileNotFoundError(f"checkpoint directory: {checkpoint}")
    if not revision or any(character.isspace() for character in revision):
        raise ValueError("explicit repository revision is required")
    config_path = directory / "config.json"
    config = json.loads(config_path.read_text())
    quant = config.get("quantization_config", {})
    if (str(quant.get("quant_method", "")).lower() != "awq" or quant.get("bits") != 4
            or str(quant.get("version", "")).lower() != "gemm" or quant.get("zero_point") is not True):
        raise ValueError("only explicit AWQ 4-bit GEMM zero-point checkpoints are supported")
    if config.get("model_type") != "qwen2" or config.get("rope_scaling"):
        raise ValueError("expected Qwen2 architecture without unsupported RoPE scaling")
    geometry = Geometry(
        layers=config["num_hidden_layers"], hidden=config["hidden_size"],
        intermediate=config["intermediate_size"], q_heads=config["num_attention_heads"],
        kv_heads=config["num_key_value_heads"],
        head_dim=config["hidden_size"] // config["num_attention_heads"],
        group=quant["group_size"], vocab=config["vocab_size"],
        context=config["max_position_embeddings"])
    if not synthetic and geometry != PRODUCTION:
        raise ValueError("official image must retain every production Qwen2.5-3B dimension")
    layout = image_layout(geometry)
    output.mkdir(parents=True, exist_ok=False)
    manifest = dict(schema=1, image_kind="synthetic" if synthetic else "official-checkpoint",
                    repository="Qwen/Qwen2.5-3B-Instruct-AWQ", revision=revision,
                    geometry=geometry.__dict__, config_sha256=digest_file(config_path),
                    packing="autoawq-gemm-output-order-02461357",
                    zero_code="direct-q-minus-z", regions={}, tensors={})
    with ExitStack() as stack:
        tensors = SafeTensors(directory, stack)
        manifest["checkpoint_files_sha256"] = tensors.files
        files = {}
        for name, length in layout["component_bytes"].items():
            path = output / f"{name}.bin"
            files[name] = stack.enter_context(path.open("w+b"))
            files[name].truncate(length)

        def write_tensor(name, shape, region, address, dtype=None, scale=False):
            tensor = tensors.get(name, shape, dtype)
            target = files[region]
            target.seek(address - BASES[region])
            digest = hashlib.sha256()
            if tensor[3] == "I32":
                view, start, end, _ = tensor
                blocks = (view[offset:min(end, offset + CHUNK)]
                          for offset in range(start, end, CHUNK))
            else:
                blocks = half_blocks(tensor, scale)
            count = 0
            for block in blocks:
                target.write(block); digest.update(block); count += len(block)
            if target.tell() > layout["component_bytes"][region]:
                raise ValueError(f"tensor overflows region: {name}")
            manifest["tensors"][name] = dict(address=address, bytes=count,
                                            image_sha256=digest.hexdigest())

        for layer in range(geometry.layers):
            for projection, (n, m) in enumerate(geometry.shapes):
                prefix = f"model.layers.{layer}.{PROJECTIONS[projection]}"
                matrix = layout["matrices"][layer, projection]
                write_tensor(prefix + ".qweight", (n, (m + 7) // 8),
                             "qweight", matrix["qweight"], "I32")
                write_tensor(prefix + ".qzeros", (n // geometry.group, (m + 7) // 8),
                             "qzeros", matrix["qzeros"], "I32")
                write_tensor(prefix + ".scales", (n // geometry.group, m),
                             "scales", matrix["scales"], "F16", scale=True)
                if projection < 3:
                    per_layer = (geometry.hidden + 2 * geometry.kv_heads * geometry.head_dim) * 2
                    before = (0, geometry.hidden, geometry.hidden +
                              geometry.kv_heads * geometry.head_dim)[projection]
                    write_tensor(prefix + ".bias", (m,), "bias",
                                 BASES["bias"] + layer * per_layer + before * 2)
            for which, name in enumerate(("input_layernorm", "post_attention_layernorm")):
                write_tensor(f"model.layers.{layer}.{name}.weight", (geometry.hidden,),
                             "norm", BASES["norm"] + (2 * layer + which) * geometry.hidden * 2)
        write_tensor("model.norm.weight", (geometry.hidden,), "norm",
                     BASES["norm"] + 2 * geometry.layers * geometry.hidden * 2)
        write_tensor("model.embed_tokens.weight", (geometry.vocab, geometry.hidden),
                     "embedding", BASES["embedding"])
        if "lm_head.weight" in tensors.tensors:
            head = tensors.get("lm_head.weight", (geometry.vocab, geometry.hidden))
            head_digest = hashlib.sha256()
            for block in half_blocks(head):
                head_digest.update(block)
            if head_digest.hexdigest() != manifest["tensors"]["model.embed_tokens.weight"]["image_sha256"]:
                raise ValueError("output head is not tied to embedding")
        elif config.get("tie_word_embeddings") is not True:
            raise ValueError("checkpoint does not declare tied embedding/output weights")
        theta = float(config.get("rope_theta", 10000.0))
        if not math.isfinite(theta) or theta <= 0:
            raise ValueError("invalid RoPE theta")
        manifest["rope_theta"] = theta
        for position in range(geometry.context):
            for pair in range(geometry.head_dim // 2):
                angle = position / theta ** (2 * pair / geometry.head_dim)
                files["rope"].write(struct.pack("<ii", round(math.cos(angle) * (1 << 30)),
                                                round(math.sin(angle) * (1 << 30))))
        for stream in files.values():
            stream.flush()
    for name, length in layout["component_bytes"].items():
        path = output / f"{name}.bin"
        manifest["regions"][name] = dict(base=BASES[name], bytes=length,
                                         file=path.name, sha256=digest_file(path))
    manifest["persistent_image_bytes"] = layout["persistent_image_bytes"]
    manifest["kv_bytes"] = layout["kv_bytes"]
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def importer_fixture(root, directory):
    """Generate an independent logical image, export official packing, reimport."""
    root, directory = Path(root), Path(directory)
    geometry = Geometry(layers=2, hidden=64, intermediate=64, head_dim=8)
    image = Image(geometry, 89)
    source = directory / "checkpoint-images" / "fixture-input"
    source.mkdir(parents=True)
    config = dict(model_type="qwen2", num_hidden_layers=geometry.layers,
                  hidden_size=geometry.hidden, intermediate_size=geometry.intermediate,
                  num_attention_heads=geometry.q_heads, num_key_value_heads=geometry.kv_heads,
                  vocab_size=geometry.vocab, max_position_embeddings=geometry.context,
                  tie_word_embeddings=True, rope_theta=10000.0,
                  quantization_config=dict(quant_method="awq", bits=4, version="gemm",
                                           group_size=geometry.group, zero_point=True))
    (source / "config.json").write_text(json.dumps(config))
    tensors, payload = {}, bytearray()

    def add(name, dtype, shape, address, data=None):
        size = math.prod(shape) * (4 if dtype == "I32" else 2)
        start = len(payload)
        payload.extend(data if data is not None else
                       (image.data[address + index] for index in range(size)))
        if len(payload) - start != size:
            raise AssertionError("independent safetensors fixture extent")
        tensors[name] = dict(dtype=dtype, shape=list(shape), data_offsets=[start, len(payload)])

    def official_pack(rows):
        data = bytearray()
        for row in rows:
            for base in range(0, len(row), 8):
                word = sum(row[base + lane] << (nibble * 4)
                           for nibble, lane in enumerate((0, 2, 4, 6, 1, 3, 5, 7)))
                data.extend(struct.pack("<I", word))
        return data

    for layer in range(geometry.layers):
        for projection, (n, m) in enumerate(geometry.shapes):
            prefix = f"model.layers.{layer}.{PROJECTIONS[projection]}"
            qw, qz, sc = image.matrix_bases[layer, projection]
            q, z, _ = image.matrices[layer, projection]
            add(prefix + ".qweight", "I32", (n, m // 8), qw, official_pack(q))
            add(prefix + ".qzeros", "I32", (n // geometry.group, m // 8), qz, official_pack(z))
            add(prefix + ".scales", "F16", (n // geometry.group, m), sc)
            if projection < 3:
                per_layer = (geometry.hidden + 2 * geometry.kv_heads * geometry.head_dim) * 2
                before = (0, geometry.hidden, geometry.hidden + geometry.kv_heads * geometry.head_dim)[projection]
                add(prefix + ".bias", "F16", (m,), BASES["bias"] + layer * per_layer + 2 * before)
        for which, name in enumerate(("input_layernorm", "post_attention_layernorm")):
            add(f"model.layers.{layer}.{name}.weight", "F16", (geometry.hidden,),
                BASES["norm"] + (layer * 2 + which) * geometry.hidden * 2)
    add("model.norm.weight", "F16", (geometry.hidden,),
        BASES["norm"] + geometry.layers * geometry.hidden * 4)
    add("model.embed_tokens.weight", "F16", (geometry.vocab, geometry.hidden), BASES["embedding"])
    header = json.dumps(tensors, separators=(",", ":")).encode()
    (source / "fixture.safetensors").write_bytes(struct.pack("<Q", len(header)) + header + payload)
    output = directory / "checkpoint-images" / "fixture-imported"
    manifest = import_checkpoint(root, source.relative_to(root), output.relative_to(root),
                                 "synthetic-fixture-seed89", synthetic=True)
    compared = 0
    for region, entry in manifest["regions"].items():
        data = (output / entry["file"]).read_bytes()
        expected = bytes(image.data.get(BASES[region] + offset, 0) for offset in range(len(data)))
        if data != expected:
            raise AssertionError(f"checkpoint import numerical/packing mismatch: {region}")
        compared += len(data)
    return dict(case="checkpoint-importer", image_kind="synthetic", compared_bytes=compared,
                tensors=len(tensors), layers=geometry.layers, projections=7,
                manifest=str((output / "manifest.json").relative_to(root)))
