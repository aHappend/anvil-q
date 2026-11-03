"""Bounded public-model intake; immutable descriptors, never inference claims."""

import json
import re
import struct

from execution import ROOT, sha256, write_json

IDENTIFIER = "Qwen/Qwen2.5-3B-Instruct-AWQ"
HOST = "https://huggingface.co/"


def acquire_assets(run):
    run.versions([("curl", "--version")])

    def fetch(url, maximum, byte_range=None):
        headers = run.path / ("intake-headers-%04d.txt" % len(run.records))
        command = ["curl", "--disable", "--silent", "--show-error", "--fail", "--location",
                   "--proto", "=https", "--proto-redir", "=https", "--max-time", "3600",
                   "--max-filesize", str(max(maximum, 65536) if byte_range else maximum),
                   "--dump-header", run.rel(headers)]
        if byte_range:
            command += ["--range", "%d-%d" % tuple(byte_range)]
        _, receipt = run.tool([*command, url], timeout=7200)
        path = ROOT / receipt["stdout"]
        if byte_range:
            ranges = re.findall(r"(?im)^Content-Range:\s*bytes\s+(\d+)-(\d+)/\d+\s*$",
                                headers.read_text())
            if (not ranges or tuple(map(int, ranges[-1])) != tuple(byte_range) or
                    path.stat().st_size != byte_range[1] - byte_range[0] + 1):
                raise AssertionError("official model server did not provide the exact requested range")
        record = {"url": url, "size_bytes": path.stat().st_size, "sha256": sha256(path)}
        if byte_range:
            record["byte_range"] = byte_range
        return path, record

    model, api_descriptor = fetch(HOST + "api/models/" + IDENTIFIER, 1048576)
    metadata = json.loads(model.read_text())
    revision = metadata["sha"]
    if not re.fullmatch("[a-f0-9]{40}", revision):
        raise AssertionError("official model revision is not immutable")
    if metadata.get("id") != IDENTIFIER:
        raise AssertionError("model identity mismatch")
    base = HOST + IDENTIFIER + "/resolve/" + revision + "/"
    license_path, license_descriptor = fetch(base + "LICENSE", 131072)
    license_text = license_path.read_text()
    if "Apache License" in license_text and "Version 2.0" in license_text:
        license_identifier = "Apache-2.0"
        license_scope = "Apache License 2.0; retain the actual license evidence"
    elif ("Qwen RESEARCH LICENSE AGREEMENT Release Date: September 19, 2024" in license_text and
          "research or evaluation purposes only" in license_text and
          "FOR NON-COMMERCIAL PURPOSES ONLY" in license_text):
        license_identifier = "LicenseRef-Qwen-Research-2024-09-19"
        license_scope = ("Non-commercial research/evaluation only. This bounded verification is "
                         "evaluation, not commercial deployment or permission to redistribute "
                         "the model under the accelerator's source license.")
        (run.path / "NOTICE").write_text(
            "Qwen is licensed under the Qwen RESEARCH LICENSE AGREEMENT, "
            "Copyright (c) Alibaba Cloud. All Rights Reserved.\n")
    else:
        raise AssertionError("official model license needs independent disposition")
    config, config_descriptor = fetch(base + "config.json", 131072)
    if sha256(config) != "9366ca39ab036f807f40ff93f03d77ce910d512174150821a87a87080c2b8c65":
        raise AssertionError("immutable model configuration differs from admitted official bytes")
    tokenizer = []
    for filename, limit in (("tokenizer.json", 16777216), ("tokenizer_config.json", 1048576)):
        _, file_descriptor = fetch(base + filename, limit)
        tokenizer.append(file_descriptor)
    keys = ["model.layers.0.self_attn.k_proj." + suffix for suffix in ("qweight", "qzeros", "scales")]
    siblings = {item["rfilename"] for item in metadata["siblings"]}
    descriptors = [config_descriptor]
    if "model.safetensors.index.json" in siblings:
        index_path, index_descriptor = fetch(base + "model.safetensors.index.json", 4194304)
        index = json.loads(index_path.read_text())
        descriptors.append(index_descriptor)
    elif "model.safetensors" in siblings:
        index = {"weight_map": {key: "model.safetensors" for key in keys}}
    else:
        raise AssertionError("official repository has no recognized safetensors layout")
    selected = {}
    headers = {}
    for key in keys:
        filename = index["weight_map"][key]
        if not re.fullmatch(r"model(?:-[0-9]+-of-[0-9]+)?\.safetensors", filename):
            raise AssertionError("unexpected official tensor shard name")
        url = base + filename
        if filename not in headers:
            length_path, length_descriptor = fetch(url, 8, [0, 7])
            length = struct.unpack("<Q", length_path.read_bytes())[0]
            if not 0 < length <= 16777216:
                raise AssertionError("unbounded safetensors header")
            header_path, header_descriptor = fetch(url, length, [8, length + 7])
            headers[filename] = json.loads(header_path.read_text()), length + 8
            descriptors += [length_descriptor, header_descriptor]
        header, data_start = headers[filename]
        tensor = header[key]
        shape = tensor["shape"]
        expected = {"qweight": ([2048, 32], "I32"), "qzeros": ([16, 32], "I32"),
                    "scales": ([16, 256], "F16")}[key.rsplit(".", 1)[1]]
        if (shape, tensor["dtype"]) != expected:
            raise AssertionError("unexpected official AWQ K projection shape/dtype " + key)
        element_bytes = 2 if tensor["dtype"] == "F16" else 4
        if tensor["data_offsets"][1] - tensor["data_offsets"][0] != shape[0] * shape[1] * element_bytes:
            raise AssertionError("official tensor byte extent mismatch")
        first_row, rows = (124, 8) if key.endswith("qweight") else (0, 2)
        start = data_start + tensor["data_offsets"][0] + first_row * shape[1] * element_bytes
        size = rows * shape[1] * element_bytes
        _, sliced = fetch(url, size, [start, start + size - 1])
        descriptors.append(sliced)
        selected[key] = {"shape": shape, "dtype": tensor["dtype"], "first_row": first_row,
                         "rows": rows, "descriptor": sliced,
                         "safetensors_data_offsets": tensor["data_offsets"]}
    common = {"identifier": IDENTIFIER, "revision": revision, "license_identifier": license_identifier,
              "license_scope": license_scope, "license_file": license_descriptor}
    manifest = {"schema": 1, "assets": [
        {**common, "category": "tokenizer", "files": tokenizer},
        {**common, "category": "weight_slice", "files": descriptors, "tensors": selected}],
        "intake_api": api_descriptor,
        "scope": "public immutable tokenizer and official K-projection slice; not full model inference"}
    write_json(run.path / "acquired-public-assets.json", manifest)
    return {"manifest": run.rel(run.path / "acquired-public-assets.json"), "revision": revision,
            "scope": manifest["scope"]}
