"""Official-asset intake diagnostics; never substitutes for RTL integration."""

import importlib
import importlib.metadata
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request


QWEN_IDENTITY = "Qwen/Qwen2.5-0.5B-Instruct"
QWEN_REVISION = "7ae557604adf67be50417f59c2c2f167def9a775"
QWEN_FILES = ("LICENSE", "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt")


def discover(directory):
    """Resolve immutable provenance before any tokenizer payload retrieval."""
    directory = Path(directory)
    dependencies = {}
    for name in ("tokenizers", "transformers", "regex", "huggingface_hub"):
        try:
            module = importlib.import_module(name)
        except ImportError as error:
            dependencies[name] = {"available": False, "diagnostic": str(error)}
        else:
            dependencies[name] = {
                "available": True,
                "version": importlib.metadata.version(name),
                "unicode_version": getattr(module, "UNICODE_VERSION", None),
            }
    (directory / "dependencies.json").write_text(
        json.dumps(dependencies, indent=2) + "\n", encoding="utf-8")
    url = f"https://huggingface.co/api/models/{QWEN_IDENTITY}"
    request = urllib.request.Request(url, headers={"User-Agent": "Anvil-Edge-verifier/1"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read()
            status = response.status
            headers = dict(response.headers)
    except urllib.error.URLError as error:
        diagnostic = {
            "url": url, "stage": "immutable-revision-and-license-discovery",
            "error_type": type(error).__name__, "error": str(error),
            "payloads_retrieved": False,
        }
        if isinstance(error, urllib.error.HTTPError):
            diagnostic["http_status"] = error.code
            (directory / "discovery-error-body.bin").write_bytes(error.read())
        (directory / "discovery-error.json").write_text(
            json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(
            "Official Qwen metadata retrieval failed before revision/license resolution; "
            "see discovery-error.json; conversion and RTL coverage remain unexecuted"
        ) from error
    (directory / "model-api.json").write_bytes(raw)
    metadata = json.loads(raw)
    revision = metadata.get("sha", "")
    license_name = metadata.get("cardData", {}).get("license")
    if not re.fullmatch(r"[0-9a-f]{40}", revision) or license_name != "apache-2.0":
        raise RuntimeError("Qwen discovery did not establish immutable SHA and expected Apache-2.0 license")
    record = {
        "identity": QWEN_IDENTITY, "revision": revision, "license": license_name,
        "url": url, "status": status, "response_headers": headers,
        "payloads_retrieved": False,
        "next_required": "Retrieve only immutable-revision files, hash and inspect exact semantics",
    }
    (directory / "discovery.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


def run_official_discovery(evidence):
    evidence.tools(("python3",))
    evidence.child(
        ["python3", "tests/official.py", "discover", evidence.relative(evidence.path)],
        "qwen-provenance-discovery",
    )


def fetch(directory):
    """Keep immutable raw files and their ordered bundle digest for inspection."""
    directory = Path(directory)
    records = []
    bundle = hashlib.sha256()
    for name in QWEN_FILES:
        url = f"https://huggingface.co/{QWEN_IDENTITY}/resolve/{QWEN_REVISION}/{name}"
        request = urllib.request.Request(url, headers={"User-Agent": "Anvil-Edge-verifier/1"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
            commit = response.headers.get("X-Repo-Commit")
            if commit is not None and commit != QWEN_REVISION:
                raise RuntimeError(f"Unexpected immutable asset revision for {name}: {commit}")
        (directory / ("qwen-" + name)).write_bytes(data)
        bundle.update(data)
        records.append({
            "upstream_path": name, "file": "qwen-" + name, "url": url,
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
        })
    tokenizer = json.loads((directory / "qwen-tokenizer.json").read_bytes())
    config = json.loads((directory / "qwen-tokenizer_config.json").read_bytes())
    license_text = (directory / "qwen-LICENSE").read_text()
    if "Apache License" not in license_text or "Version 2.0" not in license_text:
        raise RuntimeError("Pinned LICENSE does not contain expected Apache-2.0 terms")
    record = {
        "identity": QWEN_IDENTITY, "revision": QWEN_REVISION, "license": "Apache-2.0",
        "ordered_files": records, "bundle_sha256": bundle.hexdigest(),
        "normalizer": tokenizer.get("normalizer"),
        "pre_tokenizer": tokenizer.get("pre_tokenizer"),
        "post_processor": tokenizer.get("post_processor"),
        "decoder": tokenizer.get("decoder"),
        "model_options": {key: value for key, value in tokenizer["model"].items()
                          if key not in ("vocab", "merges")},
        "base_vocab_count": len(tokenizer["model"]["vocab"]),
        "merge_count": len(tokenizer["model"]["merges"]),
        "added_tokens": tokenizer["added_tokens"],
        "eos_token": config.get("eos_token"),
        "official_reference_comparisons": 0,
        "rtl_boot_or_tokenization_executed": False,
        "scope": "Provenance-checked raw intake only; converter remains unimplemented",
    }
    (directory / "qwen-intake.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps(record, indent=2, ensure_ascii=True))


def run_official_intake(evidence):
    evidence.tools(("python3",))
    evidence.child(
        ["python3", "tests/official.py", "fetch", evidence.relative(evidence.path)],
        "qwen-immutable-asset-intake",
    )
    evidence.child(
        ["python3", "-c",
         "import tokenizers; print(tokenizers.__version__)"],
        "independent-official-tokenizer-dependency",
    )


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("discover", "fetch"):
        raise SystemExit("Usage: python3 tests/official.py discover|fetch PROJECT_RELATIVE_EVIDENCE_DIRECTORY")
    {"discover": discover, "fetch": fetch}[sys.argv[1]](sys.argv[2])
