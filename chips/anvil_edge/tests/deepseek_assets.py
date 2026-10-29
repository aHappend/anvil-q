"""Immutable official DeepSeek tokenizer intake, not functional acceptance."""

import hashlib
import json
from pathlib import Path
import random
import re
import sys
import urllib.request


IDENTITY = "deepseek-ai/DeepSeek-V3"
REVISION = "e815299b0bcbac849fa540c768ef21845365c9eb"
FILES = ("LICENSE-CODE", "LICENSE-MODEL", "README.md",
         "tokenizer.json", "tokenizer_config.json")
HASHES = (
    (1064, "1c8f573e830ca9b3ebfeb7ace1823146e22b66f99ee223840e7637c9e745e1c7"),
    (13759, "ccfee4895df06bcab524151c278e8dde88bbe76165a24ecbcbcf9fafd71fd2b3"),
    (19626, "3739763a851074c810f1565f9823956f3a095231f8c591dd3c254581bdd3cf08"),
    (7847652, "621ac2e32d0dba658404412318818aaa8ce8cda492e59830109d8da6b517fb41"),
    (3128, "637bcd1a08cf7c772ce6a383196b22930921c79c3c73223c5afc0c7f41545546"),
)
ROOT = Path(__file__).resolve().parent.parent


def intake(directory):
    records = []
    bundle = hashlib.sha256()
    for name, (size, expected_hash) in zip(FILES, HASHES):
        url = f"https://huggingface.co/{IDENTITY}/resolve/{REVISION}/{name}"
        request = urllib.request.Request(url, headers={"User-Agent": "Anvil-Edge-verifier/1"})
        with urllib.request.urlopen(request, timeout=120) as response:
            commit = response.headers.get("X-Repo-Commit")
            if commit is not None and commit != REVISION:
                raise RuntimeError(f"Immutable revision mismatch for {name}: {commit}")
            data = response.read(32 * 1024 * 1024 + 1)
        if len(data) > 32 * 1024 * 1024:
            raise RuntimeError(f"Tokenizer intake exceeds bounded payload size: {name}")
        if len(data) != size or hashlib.sha256(data).hexdigest() != expected_hash:
            raise RuntimeError(f"Pinned payload length/hash mismatch: {name}")
        with (directory / ("deepseek-" + name)).open("xb") as output:
            output.write(data)
        records.append({
            "upstream_path": name, "file": "deepseek-" + name,
            "url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        })
        bundle.update(data)
    tokenizer = json.loads((directory / "deepseek-tokenizer.json").read_bytes())
    config = json.loads((directory / "deepseek-tokenizer_config.json").read_bytes())
    record = {
        "identity": IDENTITY, "revision": REVISION,
        "license_status": "Raw upstream license texts retained; no inferred SPDX grant",
        "ordered_files": records, "bundle_sha256": bundle.hexdigest(),
        "normalizer": tokenizer.get("normalizer"),
        "pre_tokenizer": tokenizer.get("pre_tokenizer"),
        "decoder": tokenizer.get("decoder"),
        "post_processor": tokenizer.get("post_processor"),
        "model_type": tokenizer["model"]["type"],
        "base_vocabulary": len(tokenizer["model"]["vocab"]),
        "ranked_merges": len(tokenizer["model"]["merges"]),
        "added_tokens": tokenizer["added_tokens"],
        "bos_token": config.get("bos_token"),
        "eos_token": config.get("eos_token"),
        "add_bos_token": config.get("add_bos_token"),
        "add_eos_token": config.get("add_eos_token"),
        "functional_comparisons": 0, "acceptance_evidence": False,
        "scope": "Immutable raw intake only; conversion and official/RTL comparisons unexecuted",
    }
    with (directory / "intake.json").open("x", encoding="ascii") as output:
        json.dump(record, output, indent=2, ensure_ascii=True)
        output.write("\n")
    print(json.dumps(record, indent=2, ensure_ascii=True))


def discover(directory):
    url = f"https://huggingface.co/api/models/{IDENTITY}"
    request = urllib.request.Request(url, headers={"User-Agent": "Anvil-Edge-verifier/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
        status = response.status
    with (directory / "model-api.json").open("xb") as output:
        output.write(raw)
    metadata = json.loads(raw)
    revision = metadata.get("sha", "")
    if metadata.get("id") != IDENTITY or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("Official metadata did not establish the requested immutable identity")
    record = {
        "identity": IDENTITY,
        "revision": revision,
        "declared_license": metadata.get("cardData", {}).get("license"),
        "metadata_url": url,
        "http_status": status,
        "metadata_sha256": hashlib.sha256(raw).hexdigest(),
        "upstream_files": sorted(item["rfilename"] for item in metadata["siblings"]),
        "payloads_retrieved": False,
        "functional_comparisons": 0,
        "acceptance_evidence": False,
    }
    with (directory / "discovery.json").open("x", encoding="ascii") as output:
        json.dump(record, output, indent=2, ensure_ascii=True)
        output.write("\n")
    print(json.dumps(record, indent=2, ensure_ascii=True))


def validate(directory):
    assets = json.loads((ROOT / "tests/data/assets.json").read_bytes())
    entry, = [item for item in assets["official_tokenizers"] if item["family_id"] == 2]
    if entry["identity"] != IDENTITY or entry["revision"] != REVISION:
        raise RuntimeError("DeepSeek manifest identity/revision differs from pinned intake")
    records = []
    bundle = hashlib.sha256()
    if len(entry["ordered_files"]) != len(FILES):
        raise RuntimeError("DeepSeek manifest has incomplete ordered inputs")
    for item, name, (size, expected_hash) in zip(entry["ordered_files"], FILES, HASHES):
        relative = f"tests/data/deepseek-{name}"
        if (item["path"] != relative or item["upstream_path"] != name
                or item["bytes"] != size or item["sha256"] != expected_hash):
            raise RuntimeError(f"DeepSeek manifest differs from pinned input: {name}")
        data = (ROOT / relative).read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != expected_hash:
            raise RuntimeError(f"Local DeepSeek asset length/hash mismatch: {relative}")
        bundle.update(data)
        records.append(dict(item))
    if bundle.hexdigest() != entry["bundle_sha256"]:
        raise RuntimeError("DeepSeek ordered bundle hash mismatch")
    tokenizer = json.loads((ROOT / "tests/data/deepseek-tokenizer.json").read_bytes())
    vocab = tokenizer["model"]["vocab"]
    if tokenizer["model"]["type"] != "BPE" or len(set(vocab.values())) != len(vocab):
        raise RuntimeError("DeepSeek base vocabulary is not a unique-ID BPE vocabulary")
    for pair in tokenizer["model"]["merges"]:
        left, right = pair.split(" ") if isinstance(pair, str) else pair
        if left not in vocab or right not in vocab or left + right not in vocab:
            raise RuntimeError("DeepSeek merge operand/concatenation absent from vocabulary")
    tokens = {token: spelling for spelling, token in vocab.items()}
    for item in tokenizer["added_tokens"]:
        if item["id"] in tokens and tokens[item["id"]] != item["content"]:
            raise RuntimeError("DeepSeek AddedToken shadows a different base token")
        tokens[item["id"]] = item["content"]
    if set(tokens) != set(range(len(tokens))):
        raise RuntimeError("DeepSeek token IDs are not contiguous")
    record = {
        "identity": IDENTITY, "revision": REVISION, "ordered_files": records,
        "bundle_sha256": bundle.hexdigest(),
        "base_vocabulary": len(vocab), "complete_vocabulary": len(tokens),
        "ordered_merge_comparisons": len(tokenizer["model"]["merges"]),
        "acceptance_evidence": False,
        "scope": "Offline raw-asset integrity and table consistency, not RTL equivalence",
    }
    with (directory / "asset-validation.json").open("x", encoding="ascii") as output:
        json.dump(record, output, indent=2)
        output.write("\n")
    print(json.dumps(record, indent=2))


def reference(directory):
    validate(directory)
    import tokenizers
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from protocol import bpe_reference
    from qwen_integration import split_added
    from qwen_tables import inverse_byte_alphabet
    from deepseek_preprocessing import Preprocessor, compare

    if tokenizers.__version__ != "0.21.4":
        raise RuntimeError("DeepSeek oracle requires the already installed tokenizers==0.21.4")
    tokenizer = tokenizers.Tokenizer.from_file(str(ROOT / "tests/data/deepseek-tokenizer.json"))
    source = json.loads((ROOT / "tests/data/deepseek-tokenizer.json").read_bytes())
    if source["normalizer"] != {"type": "Sequence", "normalizers": []}:
        raise RuntimeError("Independent DeepSeek comparison requires pinned identity normalization")
    preprocessor = Preprocessor()
    preprocessing = compare(preprocessor, source, tokenizer, tokenizers, directory)
    vocab = source["model"]["vocab"]
    alphabet = inverse_byte_alphabet()
    byte_spelling = {byte: char for char, byte in alphabet.items()}
    specials = {item["id"]: item["content"].encode("utf-8")
                for item in source["added_tokens"]}
    pieces = {
        token: specials[token] if token in specials else bytes(alphabet[char] for char in spelling)
        for spelling, token in vocab.items()
    }
    pieces.update(specials)
    merges = {}
    for rank, pair in enumerate(source["model"]["merges"]):
        left, right = pair.split(" ") if isinstance(pair, str) else pair
        key = (vocab[left], vocab[right])
        if key in merges:
            raise RuntimeError("Duplicate DeepSeek merge pair")
        merges[key] = (vocab[left + right], rank)
    requirements = json.loads((ROOT / "tests/data/requirements.json").read_bytes())
    corpus = requirements["prompts"] + [
        "caf\u00e9 e\u0301 \u4e2d\u6587 \U0001f600", "  \t\n12345\r\n",
        "I'm WE'RE she'd can't we'll", "\u212b \ufb03 \u1100\u1161",
        "a!Hello \u3042\u3044\u30a2\u30a4 1234567",
        "<\uff5cbegin\u2581of\u2581sentence\uff5c>hello",
        "<\uff5cend\u2581of\u2581sentence\uff5c>",
        "e\u0301",
    ]
    corpus.extend(item["content"] for item in source["added_tokens"]
                  if item["content"] not in corpus)
    corpus.append(" ".join(item["content"] for item in source["added_tokens"]))
    for first in range(0, len(source["added_tokens"]), 32):
        corpus.append(" ".join(item["content"]
                               for item in source["added_tokens"][first:first + 32]))
    for seed in (1, 17, 89):
        rng = random.Random(seed)
        chars = list("aAzZ019 \t\r\n!?'") + [
            "\u00e9", "\u0301", "\u4e2d", "\U0001f600", "\u00b2",
            "\u2163", "\u200d", "\u00a0", "\u3042", "\u30a2",
        ]
        corpus.extend("".join(rng.choice(chars) for _ in range(32)) for _ in range(8))
    vectors = []
    for index, text in enumerate(corpus):
        encoded = tokenizer.encode(text, add_special_tokens=False)
        independent = []
        for raw in split_added(text, source["added_tokens"], False):
            for part in ([raw] if isinstance(raw, int)
                         else split_added(raw, source["added_tokens"], True)):
                if isinstance(part, int):
                    independent.append(part)
                else:
                    for piece in preprocessor.split(part):
                        independent.extend(bpe_reference(
                            [vocab[byte_spelling[byte]] for byte in piece.encode("utf-8")],
                            merges))
        if independent != encoded.ids:
            raise RuntimeError(f"Independent DeepSeek ranked-BPE vector mismatch: corpus {index}")
        actual = tokenizer.decode(encoded.ids, skip_special_tokens=False)
        independent_bytes = b"".join(pieces[token] for token in independent)
        if (actual.encode("utf-8") != text.encode("utf-8")
                or independent_bytes != actual.encode("utf-8")):
            raise RuntimeError(f"Official DeepSeek raw-text round trip mismatch: corpus {index}")
        if index < len(requirements["prompts"]) and len(encoded.ids) <= 1:
            raise RuntimeError("Required benchmark prompt does not exercise multitoken prefill")
        vectors.append({
            "text": text, "utf8_hex": text.encode("utf-8").hex(),
            "token_ids": encoded.ids, "decoded_utf8_hex": actual.encode("utf-8").hex(),
        })
    record = {
        "identity": IDENTITY, "revision": REVISION,
        "tokenizers_version": tokenizers.__version__,
        "policy": "Raw text, no chat template, add_special_tokens=False, skip_special_tokens=False",
        "vectors": vectors, "compared_byte_vectors": len(vectors),
        "compared_ranked_bpe_vectors": len(vectors),
        "preprocessing_comparisons": preprocessing,
        "scope": "Independent ranked-BPE and byte concatenation against the official software oracle. "
                 "Pre-tokenization is independently evaluated from pinned Unicode16 data "
                 "and compared to the installed official library. Hardware conversion "
                 "and RTL comparisons remain pending",
        "acceptance_evidence": False,
    }
    with (directory / "official-vectors.json").open("x", encoding="ascii") as output:
        json.dump(record, output, indent=2, ensure_ascii=True)
        output.write("\n")
    print(f"DEEPSEEK_RANKED_BPE_VECTORS {len(vectors)}; "
          f"OFFICIAL_BYTE_VECTORS {len(vectors)}; RTL_COMPARISONS 0")


def run_deepseek_discovery(evidence):
    evidence.tools(("python3",))
    evidence.child(
        ["python3", "tests/deepseek_assets.py", "discover", evidence.relative(evidence.path)],
        "deepseek-provenance-discovery",
    )


def run_deepseek_intake(evidence):
    evidence.tools(("python3",))
    evidence.child(
        ["python3", "tests/deepseek_assets.py", "intake", evidence.relative(evidence.path)],
        "deepseek-immutable-intake",
    )


def run_deepseek_assets(evidence):
    evidence.tools(("python3",))
    evidence.child(
        ["python3", "tests/deepseek_assets.py", "validate", evidence.relative(evidence.path)],
        "deepseek-offline-asset-validation",
    )


def run_deepseek_reference(evidence):
    from official import run_official_identity
    run_official_identity(evidence)
    evidence.child(
        ["./.venv/bin/python", "tests/deepseek_assets.py", "reference",
         evidence.relative(evidence.path)],
        "deepseek-official-software-vectors",
    )


if __name__ == "__main__":
    actions = {"discover": discover, "intake": intake,
               "validate": validate, "reference": reference}
    if len(sys.argv) != 3 or sys.argv[1] not in actions:
        raise SystemExit(
            "Usage: python3 tests/deepseek_assets.py discover|intake|validate|reference "
            "evidence/preparation/FRESH"
        )
    directory = Path(sys.argv[2])
    if (directory.is_absolute() or ".." in directory.parts
            or directory.parts[:2] not in (("evidence", "preparation"),
                                          ("evidence", "verification"))
            or not directory.is_dir()):
        raise SystemExit("A present project-relative evidence directory is required")
    actions[sys.argv[1]](directory)
