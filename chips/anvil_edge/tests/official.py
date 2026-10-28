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
ROOT = Path(__file__).resolve().parent.parent


def manifest():
    assets = json.loads((ROOT / "tests/data/assets.json").read_bytes())
    entry, = [item for item in assets["official_tokenizers"] if item["family_id"] == 1]
    if (entry["identity"] != QWEN_IDENTITY or entry["revision"] != QWEN_REVISION
            or entry["license"] != "Apache-2.0"
            or tuple(item["upstream_path"] for item in entry["ordered_files"]) != QWEN_FILES):
        raise RuntimeError("Qwen asset manifest identity/revision/license/file order changed")
    for item in entry["ordered_files"]:
        relative = Path(item["path"])
        if (relative.is_absolute() or relative.parts[:2] != ("tests", "data")
                or len(relative.parts) != 3):
            raise RuntimeError("Qwen inputs must be flat portable tests/data files")
    return entry


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
    pinned = manifest()
    for item in pinned["ordered_files"]:
        name = item["upstream_path"]
        url = f"https://huggingface.co/{QWEN_IDENTITY}/resolve/{QWEN_REVISION}/{name}"
        request = urllib.request.Request(url, headers={"User-Agent": "Anvil-Edge-verifier/1"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
            commit = response.headers.get("X-Repo-Commit")
            if commit is not None and commit != QWEN_REVISION:
                raise RuntimeError(f"Unexpected immutable asset revision for {name}: {commit}")
        if (len(data) != item["bytes"]
                or hashlib.sha256(data).hexdigest() != item["sha256"]):
            raise RuntimeError(f"Pinned Qwen asset length/hash mismatch: {name}")
        with (directory / ("qwen-" + name)).open("xb") as output:
            output.write(data)
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


def validate(directory):
    """Verify every retained raw input, independent of network or optional libraries."""
    pinned = manifest()
    bundle = hashlib.sha256()
    records = []
    for item in pinned["ordered_files"]:
        data = (ROOT / item["path"]).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if len(data) != item["bytes"] or actual != item["sha256"]:
            raise RuntimeError(f"Local immutable Qwen asset length/hash mismatch: {item['path']}")
        bundle.update(data)
        records.append(dict(item))
    if bundle.hexdigest() != pinned["bundle_sha256"]:
        raise RuntimeError("Qwen ordered bundle digest mismatch")
    tokenizer = json.loads((ROOT / "tests/data/qwen-tokenizer.json").read_bytes())
    vocab = json.loads((ROOT / "tests/data/qwen-vocab.json").read_bytes())
    if tokenizer["model"]["vocab"] != vocab:
        raise RuntimeError("Qwen tokenizer.json and vocab.json disagree")
    merges = (ROOT / "tests/data/qwen-merges.txt").read_text().splitlines()
    if not merges or not merges[0].startswith("#version:"):
        raise RuntimeError("Qwen merges.txt has no expected version header")
    pairs = [line.split(" ") for line in merges[1:]]
    embedded = tokenizer["model"]["merges"]
    embedded = [pair.split(" ") if isinstance(pair, str) else pair for pair in embedded]
    if pairs != embedded or any(len(pair) != 2 for pair in pairs):
        raise RuntimeError("Qwen merge order differs between official asset encodings")
    for left, right in pairs:
        if left not in vocab or right not in vocab or left + right not in vocab:
            raise RuntimeError("Qwen merge refers to absent operand/concatenation")
    ids = list(vocab.values()) + [token["id"] for token in tokenizer["added_tokens"]]
    if len(set(ids)) != len(ids) or set(ids) != set(range(len(ids))):
        raise RuntimeError("Qwen actual tokenizer IDs are duplicate or noncontiguous")
    record = {
        "identity": pinned["identity"], "revision": pinned["revision"],
        "license": pinned["license"], "ordered_files": records,
        "bundle_sha256": bundle.hexdigest(),
        "base_vocabulary": len(vocab), "actual_tokenizer_vocabulary": len(ids),
        "model_embedding_capacity_is_not_tokenizer_vocabulary": True,
        "ordered_merge_comparisons": len(pairs),
        "normalizer": tokenizer["normalizer"],
        "pre_tokenizer": tokenizer["pre_tokenizer"],
        "added_tokens": tokenizer["added_tokens"],
        "conversion_status": pinned["conversion_status"],
        "official_reference_comparisons": 0,
        "rtl_boot_or_tokenization_executed": False,
    }
    with (Path(directory) / "qwen-asset-validation.json").open("x", encoding="ascii") as output:
        json.dump(record, output, indent=2, ensure_ascii=True)
        output.write("\n")
    print(json.dumps(record, indent=2, ensure_ascii=True))
    return tokenizer


def reference(directory):
    """Official library vectors only: an independent oracle, never runtime inference."""
    tokenizer_data = validate(directory)
    try:
        import tokenizers
    except ImportError as error:
        raise RuntimeError(
            "Pinned Qwen assets are present, but independent official-reference execution "
            "requires the unavailable tokenizers package. No installation is authorized. "
            "Exact tagged-DFA/Unicode/AddedToken conversion is separately unimplemented."
        ) from error
    tokenizer = tokenizers.Tokenizer.from_file(str(ROOT / "tests/data/qwen-tokenizer.json"))
    requirements = json.loads((ROOT / "tests/data/requirements.json").read_bytes())
    corpus = requirements["prompts"] + [
        "caf\u00e9 e\u0301 \u4e2d\u6587 \U0001f600", "  \t\n12345\r\n",
        "<|im_start|>user\nhello<|im_end|>", "<tool_call>hello</tool_call>",
        "I'm WE'RE she'd can't we'll", "\u212b \ufb03 \u1100\u1161",
    ]
    visible = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
    byte_map = {chr(value): value for value in visible}
    for offset, value in enumerate(value for value in range(256) if value not in visible):
        byte_map[chr(256 + offset)] = value
    pieces = {
        token: bytes(byte_map[char] for char in spelling)
        for spelling, token in tokenizer_data["model"]["vocab"].items()
    }
    pieces.update({item["id"]: item["content"].encode("utf-8")
                   for item in tokenizer_data["added_tokens"]})
    vectors = []
    for text in corpus:
        encoded = tokenizer.encode(text, add_special_tokens=False)
        raw = b"".join(pieces[token] for token in encoded.ids)
        official_bytes = tokenizer.decode(encoded.ids, skip_special_tokens=False).encode("utf-8")
        if raw != official_bytes:
            raise RuntimeError("Independent inverse-byte-map vector differs from official decoder")
        if text in requirements["prompts"] and len(encoded.ids) < 2:
            raise RuntimeError("Mandatory benchmark prompt did not produce multiple tokens")
        vectors.append({
            "input_utf8_hex": text.encode("utf-8").hex(), "token_ids": encoded.ids,
            "decoded_utf8_hex": raw.hex(),
        })
    with (Path(directory) / "qwen-official-reference.json").open("x", encoding="ascii") as output:
        json.dump({
            "tokenizers_version": tokenizers.__version__, "vectors": vectors,
            "scope": "Software oracle only; no RTL integration or weighted benchmark pass",
        }, output, indent=2)
        output.write("\n")
    print(f"OFFICIAL_REFERENCE_VECTORS {len(vectors)}")


def run_official_assets(evidence):
    evidence.tools(("python3",))
    evidence.child(
        ["python3", "tests/official.py", "validate", evidence.relative(evidence.path)],
        "qwen-pinned-local-asset-validation",
    )


def run_official_checkpoint(evidence):
    evidence.tools(("python3",))
    evidence.child(
        ["python3", "tests/official.py", "reference", evidence.relative(evidence.path)],
        "qwen-independent-official-reference",
    )
    from verify import VerificationFailure
    raise VerificationFailure(
        "Official-profile RTL integration incomplete: exact Qwen tagged-DFA, normalization "
        "and AddedToken image conversion/boot/tokenization are not implemented. "
        "DeepSeek-V3, Llama-3.2 and weighted default-geometry hardware coverage remain mandatory."
    )


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
    actions = {"discover": discover, "fetch": fetch, "validate": validate, "reference": reference}
    if len(sys.argv) != 3 or sys.argv[1] not in actions:
        raise SystemExit("Usage: python3 tests/official.py discover|fetch|validate|reference PROJECT_RELATIVE_EVIDENCE_DIRECTORY")
    actions[sys.argv[1]](sys.argv[2])
