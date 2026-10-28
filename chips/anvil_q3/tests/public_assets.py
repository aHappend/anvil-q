"""Content validation/acquisition for explicitly pinned, licensed public assets.

Each asset has category (weight_slice/tokenizer/baseline), identifier, a 40-hex
revision, license_identifier, license_file and nonempty files. File descriptors
have url, sha256, size_bytes and optional local path under tests/assets/.
An optional inclusive byte_range permits bounded official safetensors slices.
Local retained slices obey the same range/length rules as downloaded slices.
Baselines also declare generation and implementation=native; compatibility
wrappers cannot satisfy the independent-Q1/Q4 prerequisite.
"""

from pathlib import Path
import re
from urllib.parse import urlsplit

from execution import ROOT, sha256


def descriptor(run, item, revision):
    if not isinstance(item, dict):
        raise ValueError("public asset file descriptor must be an object")
    digest = item.get("sha256")
    size = item.get("size_bytes")
    url = item.get("url")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("public asset needs an expected SHA256")
    if type(size) is not int or not 0 < size < 1 << 64:
        raise ValueError("public asset needs a positive, explicitly bounded expected byte count")
    if not isinstance(url, str):
        raise ValueError("public URL required")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in
            ("huggingface.co", "raw.githubusercontent.com", "github.com") or
            parsed.username or parsed.password or parsed.query or parsed.fragment or
            revision not in parsed.path.split("/")):
        raise ValueError("asset URL must identify an immutable public revision without credentials")
    byte_range = item.get("byte_range")
    if byte_range is not None:
        if (not isinstance(byte_range, list) or len(byte_range) != 2 or
                any(type(n) is not int for n in byte_range) or
                byte_range[0] < 0 or byte_range[1] - byte_range[0] + 1 != size):
            raise ValueError("invalid inclusive public byte slice")
    value = item.get("path")
    if value is not None:
        relative = Path(value)
        if (relative.is_absolute() or ".." in relative.parts or
                relative.parts[:2] != ("tests", "assets") or
                any(p.startswith(".") for p in relative.parts)):
            raise ValueError("local public assets must be nonhidden project-relative tests/assets/ files")
        path = ROOT / relative
        if not path.is_file() or not path.resolve().is_relative_to(ROOT / "tests/assets"):
            raise ValueError("declared local asset absent/outside tests/assets: " + value)
        receipt = None
    else:
        headers = run.path / f"public-asset-headers-{len(run.records):04d}.txt"
        command = ["curl", "--disable", "--silent", "--show-error", "--fail", "--location",
                   "--proto", "=https", "--proto-redir", "=https",
                   "--max-filesize", str(max(size, 65536) if item.get("byte_range") else size),
                   "--max-time", "3600",
                   "--dump-header", run.rel(headers)]
        if byte_range is not None:
            command += ["--range", f"{byte_range[0]}-{byte_range[1]}"]
        _, receipt = run.tool([*command, url], timeout=7200)
        path = ROOT / receipt["stdout"]
        if byte_range is not None:
            ranges = re.findall(r"(?im)^Content-Range:\s*bytes\s+(\d+)-(\d+)/\d+\s*$",
                                headers.read_text())
            if not ranges or tuple(map(int, ranges[-1])) != tuple(byte_range):
                raise AssertionError("server did not return the declared exact public byte range")
    if path.stat().st_size != size or sha256(path) != digest:
        raise AssertionError("public asset content length/SHA256 mismatch: " + url)
    return {"url": url, "revision": revision, "sha256": digest, "size_bytes": size,
            "retained_path": run.rel(path), "tool_receipt": receipt,
            "byte_range": item.get("byte_range")}


def validate_assets(run, records):
    if not isinstance(records, list):
        raise ValueError("public assets must be a list")
    result = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("public asset record must be an object")
        category = record.get("category")
        revision = record.get("revision")
        if category not in ("weight_slice", "tokenizer", "baseline"):
            raise ValueError("unknown public asset category")
        if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{40}", revision):
            raise ValueError("immutable 40-hex public revision required")
        for field in ("identifier", "license_identifier"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError("public asset requires " + field)
        files = record.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("public asset has no content files")
        license_evidence = descriptor(run, record["license_file"], revision)
        if record["license_identifier"] == "LicenseRef-Qwen-Research-2024-09-19":
            text = (ROOT / license_evidence["retained_path"]).read_text()
            if ("Qwen RESEARCH LICENSE AGREEMENT Release Date: September 19, 2024" not in text or
                    "FOR NON-COMMERCIAL PURPOSES ONLY" not in text):
                raise AssertionError("model evaluation license identity mismatch")
            notice = run.path / "QWEN_NOTICE"
            if not notice.exists():
                notice.write_text("Qwen is licensed under the Qwen RESEARCH LICENSE AGREEMENT, "
                                  "Copyright (c) Alibaba Cloud. All Rights Reserved.\n")
        contents = [descriptor(run, item, revision) for item in files]
        if category == "baseline":
            if record.get("generation") not in ("Q1", "Q2", "Q4"):
                raise ValueError("baseline generation must be Q1/Q2/Q4, not relabeled Q3")
            if record.get("implementation") != "native":
                raise ValueError("compatibility wrapper is not an independent baseline implementation")
        if category in ("weight_slice", "tokenizer") and (
                record["identifier"] != "Qwen/Qwen2.5-3B-Instruct-AWQ"):
            raise ValueError("official AWQ slice/tokenizer must identify the requested trained model")
        result.append({"category": category, "identifier": record["identifier"],
                       "generation": record.get("generation"), "revision": revision,
                       "license_identifier": record["license_identifier"],
                       "license_scope": record.get("license_scope"),
                       "license_evidence": license_evidence, "contents": contents,
                       "scope": "content/provenance only; numerical execution remains mandatory"})
    return result
