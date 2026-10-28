"""Acquire and validate pinned public input data without installing dependencies.

From the project root: python3 tests/fixtures.py --acquire
Validate a supplied bundle: python3 tests/fixtures.py --root fixtures/qwen2.5-0.5b
These commands establish input identity, not model inference or RTL acceptance.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import urllib.request
import uuid


PINNED = {
    "AWQ": {
        "repository": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
        "revision": "db09cd27ead7fee40cdee309693cf83601b9c899",
        "tensor_sha256": "c50d807b7bed7ff314308972e0f4bcf4e5a70bc60ad88fc7df53940831ed0c1b",
    },
    "BF16": {
        "repository": "Qwen/Qwen2.5-0.5B-Instruct",
        "revision": "7ae557604adf67be50417f59c2c2f167def9a775",
        "tensor_sha256": "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe",
    },
}
FILES = ("config.json", "generation_config.json", "tokenizer.json",
         "tokenizer_config.json", "merges.txt", "vocab.json", "model.safetensors", "LICENSE")
COMMON_SHA256 = {
    "tokenizer.json": "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539",
    "tokenizer_config.json": "5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583",
    "merges.txt": "599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3",
    "vocab.json": "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910",
    "LICENSE": "832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e",
}
MODE_SHA256 = {
    "AWQ": {
        "config.json": "bd20ae34a91eb38230b870d39f56677d1cda1e8b6688ad627e6efb6ca9f44090",
        "generation_config.json": "091fc0fd8cf33ecb3ded1399ffe17cca80fefdb167ac4c241c1ca42c6bc116e5",
    },
    "BF16": {
        "config.json": "18e18afcaccafade98daf13a54092927904649e1dd4eba8299ab717d5d94ff45",
        "generation_config.json": "e558847a8b4402616f1273797b015104dc266fe4b520056fca88823ba8f8ebe6",
    },
}
DIMENSIONS = {"num_hidden_layers": 24, "hidden_size": 896, "intermediate_size": 4864,
              "num_attention_heads": 14, "num_key_value_heads": 2, "vocab_size": 151936,
              "max_position_embeddings": 32768}
WIDTHS = {"BF16": 2, "F16": 2, "F32": 4, "I32": 4, "I64": 8}


def project_path(value):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("fixture paths must be nonempty and project-relative")
    for part in path.parts:
        if part in (".vulcan", ".git", ".tooling", "VULCAN"):
            raise ValueError("runtime metadata is not a fixture directory")
    if not path.resolve().is_relative_to(Path.cwd().resolve()):
        raise ValueError("fixture paths cannot escape the project through symlinks")
    return path


def hashes(path):
    size = path.stat().st_size
    sha = hashlib.sha256()
    blob = hashlib.sha1(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as source:
        while block := source.read(4 * 1024 * 1024):
            sha.update(block)
            blob.update(block)
    return {"size": size, "sha256": sha.hexdigest(), "git_blob_sha1": blob.hexdigest()}


def download(url, destination, expected):
    if destination.exists():
        actual = hashes(destination)
        check_digest(actual, expected, destination)
        return actual
    temporary = destination.with_name(destination.name + ".partial-" + uuid.uuid4().hex)
    print(json.dumps({"download": url, "partial": str(temporary)}), flush=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Anvil-Q1-HT-input-acquisition/1"})
    with urllib.request.urlopen(request, timeout=3600) as response, temporary.open("xb") as sink:
        while block := response.read(4 * 1024 * 1024):
            sink.write(block)
    actual = hashes(temporary)
    check_digest(actual, expected, temporary)
    temporary.rename(destination)
    return actual


def check_digest(actual, expected, path):
    for key, value in expected.items():
        if actual.get(key) != value:
            raise ValueError(f"checkpoint input mismatch: {path}: {key}: "
                             f"{actual.get(key)} != {value}")


def safetensors_inventory(path):
    with path.open("rb") as source:
        raw_length = source.read(8)
        if len(raw_length) != 8:
            raise ValueError(f"truncated safetensors input: {path}")
        length = struct.unpack("<Q", raw_length)[0]
        if not 2 <= length <= 64 * 1024 * 1024:
            raise ValueError(f"invalid safetensors header length: {path}")
        header = json.loads(source.read(length))
    payload_bytes = path.stat().st_size - 8 - length
    intervals = []
    inventory = {}
    for name, tensor in header.items():
        if name == "__metadata__":
            continue
        dtype, shape, offsets = tensor["dtype"], tensor["shape"], tensor["data_offsets"]
        if dtype not in WIDTHS or not shape or any(type(n) is not int or n <= 0 for n in shape):
            raise ValueError(f"unsupported checkpoint tensor: {name}: {tensor}")
        count = 1
        for dimension in shape:
            count *= dimension
        if (len(offsets) != 2 or any(type(n) is not int for n in offsets)
                or offsets[0] < 0 or offsets[1] > payload_bytes
                or offsets[1] - offsets[0] != count * WIDTHS[dtype]):
            raise ValueError(f"invalid checkpoint tensor interval: {name}")
        intervals.append((offsets[0], offsets[1], name))
        inventory[name] = {"dtype": dtype, "shape": shape, "data_offsets": offsets}
    cursor = 0
    for start, end, name in sorted(intervals):
        if start != cursor:
            raise ValueError(f"overlapping or incomplete checkpoint tensor payload: {name}")
        cursor = end
    if cursor != payload_bytes or not inventory:
        raise ValueError("incomplete safetensors tensor inventory")
    return {"header_bytes": length, "payload_bytes": payload_bytes, "tensors": inventory}


def validate_model(folder, mode):
    config = json.loads((folder / "config.json").read_text())
    for name, expected in DIMENSIONS.items():
        if config.get(name) != expected:
            raise ValueError(f"{mode} checkpoint dimension {name} != {expected}")
    if config.get("model_type") != "qwen2" or not config.get("tie_word_embeddings"):
        raise ValueError(f"{mode} checkpoint is not the required tied Qwen2 model")
    if mode == "AWQ":
        quant = config.get("quantization_config", {})
        if (quant.get("quant_method") != "awq" or quant.get("bits") != 4
                or quant.get("group_size") != 128 or quant.get("zero_point") is not True
                or str(quant.get("version", "")).lower() != "gemm"):
            raise ValueError(f"unsupported original AWQ quantization metadata: {quant}")
    tokenizer = json.loads((folder / "tokenizer_config.json").read_text())
    if not isinstance(tokenizer.get("chat_template"), str) or not tokenizer["chat_template"]:
        raise ValueError(f"{mode} checkpoint has no documented chat template")
    inventory = safetensors_inventory(folder / "model.safetensors")
    tensors = inventory["tensors"]
    embedding = tensors.get("model.embed_tokens.weight")
    if embedding is None or embedding["shape"] != [151936, 896]:
        raise ValueError(f"{mode} checkpoint embedding shape mismatch")
    projections = ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
                   "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")
    outputs = (896, 128, 128, 896, 4864, 4864, 896)
    for layer in range(24):
        for projection, output in zip(projections, outputs):
            inputs = 4864 if projection == "mlp.down_proj" else 896
            prefix = f"model.layers.{layer}.{projection}."
            expected = ({"qweight": ("I32", [inputs, output // 8]),
                         "qzeros": ("I32", [inputs // 128, output // 8]),
                         "scales": ("F16", [inputs // 128, output])}
                        if mode == "AWQ" else {"weight": ("BF16", [output, inputs])})
            for suffix, (dtype, shape) in expected.items():
                tensor = tensors.get(prefix + suffix)
                if tensor is None or tensor["dtype"] != dtype or tensor["shape"] != shape:
                    raise ValueError(f"checkpoint tensor contract mismatch: {prefix + suffix}: {tensor}")
    return inventory


def acquire(root):
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        return validate(root)
    manifest = {"schema": 1, "kind": "real_public_checkpoint_inputs_not_verification_results",
                "models": {}}
    for mode, pin in PINNED.items():
        folder = root / mode.lower()
        folder.mkdir(exist_ok=True)
        metadata_url = (f"https://huggingface.co/api/models/{pin['repository']}/revision/"
                        f"{pin['revision']}?blobs=true")
        with urllib.request.urlopen(metadata_url, timeout=3600) as response:
            metadata_bytes = response.read()
        metadata = json.loads(metadata_bytes)
        if metadata.get("sha") != pin["revision"] or metadata.get("id") != pin["repository"]:
            raise ValueError(f"immutable model revision mismatch: {mode}")
        metadata_path = folder / ("metadata-" + uuid.uuid4().hex + ".json")
        metadata_path.write_bytes(metadata_bytes)
        remote = {entry["rfilename"]: entry for entry in metadata["siblings"]}
        records = {}
        for filename in FILES:
            entry = remote[filename]
            expected = {"size": entry["size"]}
            if entry.get("lfs"):
                expected["sha256"] = entry["lfs"]["sha256"]
            else:
                expected["git_blob_sha1"] = entry["blobId"]
            if filename == "model.safetensors":
                expected["sha256"] = pin["tensor_sha256"]
            else:
                expected["sha256"] = {**COMMON_SHA256, **MODE_SHA256[mode]}[filename]
            url = f"https://huggingface.co/{pin['repository']}/resolve/{pin['revision']}/{filename}"
            records[filename] = download(url, folder / filename, expected)
            print(json.dumps({"mode": mode, "file": filename, **records[filename]}), flush=True)
        manifest["models"][mode] = {
            **pin, "files": records, "metadata_url": metadata_url,
            "metadata_file": str(metadata_path.relative_to(root)),
            "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
            "inventory": validate_model(folder, mode),
        }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return validate(root)


def validate(root):
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest.get("schema") != 1 or set(manifest.get("models", {})) != set(PINNED):
        raise ValueError("checkpoint manifest is incomplete")
    for mode, pin in PINNED.items():
        model = manifest["models"][mode]
        if any(model.get(key) != value for key, value in pin.items()) or set(model["files"]) != set(FILES):
            raise ValueError(f"checkpoint manifest identity mismatch: {mode}")
        folder = root / mode.lower()
        for filename, expected in model["files"].items():
            if not re.fullmatch("[0-9a-f]{64}", expected["sha256"]):
                raise ValueError("invalid checkpoint SHA-256 inventory")
            pinned_sha = (pin["tensor_sha256"] if filename == "model.safetensors"
                          else {**COMMON_SHA256, **MODE_SHA256[mode]}[filename])
            if expected["sha256"] != pinned_sha:
                raise ValueError(f"checkpoint manifest SHA-256 differs from pinned input: {mode}/{filename}")
            check_digest(hashes(folder / filename), expected, folder / filename)
        if model["files"]["model.safetensors"]["sha256"] != pin["tensor_sha256"]:
            raise ValueError("checkpoint tensor SHA-256 does not match independent pin")
        metadata_file = project_path(model["metadata_file"])
        metadata = (root / metadata_file).read_bytes()
        if hashlib.sha256(metadata).hexdigest() != model["metadata_sha256"]:
            raise ValueError("checkpoint metadata provenance mismatch")
        if validate_model(folder, mode) != model["inventory"]:
            raise ValueError("checkpoint tensor inventory mismatch")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=project_path, default=Path("fixtures/qwen2.5-0.5b"))
    parser.add_argument("--acquire", action="store_true")
    args = parser.parse_args()
    manifest = acquire(args.root) if args.acquire else validate(args.root)
    print(json.dumps({"validated_models": {
        mode: {"revision": model["revision"],
               "tensor_sha256": model["tensor_sha256"],
               "tensor_count": len(model["inventory"]["tensors"])}
        for mode, model in manifest["models"].items()
    }, "scope": "Input identity only; no numerical, benchmark or RTL acceptance."}), flush=True)


if __name__ == "__main__":
    main()
