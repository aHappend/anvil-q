"""Complete official DeepSeek tables and independent public-port RTL comparisons.

Raw tokenizer.json policy is explicit: identity normalization, enabled literal
AddedTokens and no automatic BOS/EOS. The model-level tokenizer_config.json
add_bos_token setting is recorded separately, not silently applied or certified.
No weights, SPI boot or inference are supplied by this fixture.
"""

import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deepseek_assets import reference, ROOT
from deepseek_dfa import classify, compile_profile
from deepseek_preprocessing import Preprocessor, require
from official import installed_identity
from qwen_integration import rtl_case, run_rtl, save
from qwen_regex import serialize
from qwen_tables import BASE, audit_fragments, encode_fragments, inverse_byte_alphabet, table


VOCABULARY = 128815


def prepare(directory):
    installed_identity(directory)
    reference(directory)
    source = json.loads((ROOT / "tests/data/deepseek-tokenizer.json").read_bytes())
    config = json.loads((ROOT / "tests/data/deepseek-tokenizer_config.json").read_bytes())
    assets = json.loads((ROOT / "tests/data/assets.json").read_bytes())
    entry, = [item for item in assets["official_tokenizers"] if item["family_id"] == 2]
    model = source["model"]
    require({key: value for key, value in model.items() if key not in ("vocab", "merges")} == {
        "type": "BPE", "dropout": None, "unk_token": None,
        "continuing_subword_prefix": None, "end_of_word_suffix": None,
        "fuse_unk": False, "byte_fallback": False,
    }, "Unrepresented DeepSeek BPE policy")
    alphabet = inverse_byte_alphabet()
    vocab = model["vocab"]
    specials = {item["id"]: item for item in source["added_tokens"]}
    pieces, flags = [None] * VOCABULARY, [0] * VOCABULARY
    for spelling, token in vocab.items():
        require(type(token) is int and 0 <= token < VOCABULARY and pieces[token] is None,
                "Duplicate/out-of-range base token")
        # DeepSeek includes three literal specials in its base vocabulary.
        if token not in specials:
            pieces[token] = bytes(alphabet[char] for char in spelling)
            flags[token] = 1
        else:
            require(spelling == specials[token]["content"],
                    "AddedToken shadows a different base spelling")
    for item in source["added_tokens"]:
        require(set(item) == {"id", "content", "special", "single_word",
                              "lstrip", "rstrip", "normalized"} and
                not any(item[key] for key in ("single_word", "lstrip", "rstrip")),
                "Unrepresented DeepSeek AddedToken policy")
        token = item["id"]
        require(0 <= token < VOCABULARY and pieces[token] is None,
                "Duplicate/out-of-range AddedToken")
        pieces[token] = item["content"].encode()
        flags[token] = 2 if item["special"] else 3
    require(all(piece is not None and piece for piece in pieces),
            "Missing/empty complete DeepSeek vocabulary")
    byte_spelling = {byte: char for char, byte in alphabet.items()}
    byte_ids = [vocab[byte_spelling[byte]] for byte in range(256)]
    merges = []
    for rank, pair in enumerate(model["merges"]):
        left, right = pair.split(" ") if isinstance(pair, str) else pair
        merges.append((vocab[left], vocab[right], vocab[left + right], rank))
    tables = encode_fragments(pieces, flags, byte_ids, merges, source["added_tokens"])
    audit = audit_fragments(tables, source, VOCABULARY)
    preprocessor = Preprocessor()
    symbols, _, ranges = classify(preprocessor)
    profile = compile_profile(symbols)
    tables.update(serialize(profile))
    # Identity normalization never consumes decompositions or compositions.
    tables[0x207] = table(16, b"".join(struct.pack("<4I", *row) for row in ranges))
    tables.update({kind: table(width, b"")
                   for kind, width in ((0x20D, 16), (0x20E, 4), (0x20F, 16))})
    require(set(tables) == set(range(0x201, 0x210)), "Missing complete DeepSeek table kind")
    bases, counts, entries, combined = [0] * 16, [0] * 16, [], bytearray()
    for kind, blob in sorted(tables.items()):
        index = kind - 0x200
        bases[index] = BASE + len(combined)
        counts[index] = struct.unpack_from("<I", blob, 12)[0]
        with (directory / f"table-{kind:03x}.bin").open("xb") as output:
            output.write(blob)
        entries.append({"kind": kind, "base": bases[index], "bytes": len(blob),
                        "record_count": counts[index],
                        "sha256": hashlib.sha256(blob).hexdigest()})
        combined.extend(blob + bytes(-len(blob) % 4))
    metadata = [2, 2, VOCABULARY, 0, 1, 0, 0, 1, 0x100000,
                profile["classes"], profile["start"], profile["dead"],
                32, 0, max(map(len, pieces)), 4096]
    metadata.extend(struct.unpack("<8I", bytes.fromhex(entry["bundle_sha256"])))
    metadata.extend([0x100000, 0x100000, *([0] * 6)])
    require(len(metadata) == 32, "Wrong DeepSeek metadata extent")
    with (directory / "tables.hex").open("x", encoding="ascii") as output:
        output.write("".join(f"{word:08x}\n" for word, in struct.iter_unpack("<I", combined)))
    vectors = json.loads((directory / "official-vectors.json").read_bytes())
    info = {
        "scope": "Complete pinned DeepSeek raw-text tables supplied to public "
                 "tokenizer/detokenizer ports; not boot or weighted inference",
        "bootable": False, "metadata": metadata, "bases": bases, "counts": counts,
        "tables": entries, "memory_base": BASE, "memory_bytes": len(combined),
        "memory_sha256": hashlib.sha256(combined).hexdigest(),
        "memory_hex_sha256": hashlib.sha256((directory / "tables.hex").read_bytes()).hexdigest(),
        "source_audit": audit, "official_vector_comparisons": len(vectors["vectors"]),
        "unicode_source_sha256": preprocessor.unicode_hashes,
        "raw_policy": vectors["policy"],
        "model_config_add_bos_token": config["add_bos_token"],
        "model_wrapper_policy_scope": "Not applied by raw tokenizer.json fixture. "
                                      "Automatic-BOS profile integration remains separate",
    }
    save(directory / "complete-table-fixture.json", info)
    print(f"DEEPSEEK_COMPLETE_TABLES {len(tables)}; "
          f"OFFICIAL_VECTORS {len(vectors['vectors'])}")


def run_deepseek_integration(evidence):
    evidence.tools(("python3", "verilator", "g++", "make"))
    evidence.child([
        "./.venv/bin/python", "tests/deepseek_integration.py", evidence.relative(evidence.path),
    ], "deepseek-complete-table-preparation")
    info = json.loads((evidence.path / "complete-table-fixture.json").read_bytes())
    record = json.loads((evidence.path / "official-vectors.json").read_bytes())
    vectors = [{"case": index, "input_utf8_hex": row["utf8_hex"],
                "token_ids": row["token_ids"], "decoded_utf8_hex": row["decoded_utf8_hex"]}
               for index, row in enumerate(record["vectors"])]
    ordinary = [row for row in vectors if len(bytes.fromhex(row["input_utf8_hex"])) <= 4096]
    large = [row for row in vectors if len(bytes.fromhex(row["input_utf8_hex"])) > 4096]
    require(len(large) == 1 and len(ordinary) + len(large) == len(vectors),
            "Unexpected DeepSeek prompt-capacity partition")
    largest = max(len(bytes.fromhex(row["input_utf8_hex"])) for row in large)
    capacity = 1 << (largest - 1).bit_length()
    save(evidence.path / "rtl-capacity-partition.json", {
        "default_capacity": 4096, "default_capacity_vectors": len(ordinary),
        "large_capacity": capacity, "large_capacity_vectors": len(large),
        "large_input_bytes": largest,
        "scope": "The original whole-AddedToken concatenation is retained and executed "
                 "at a larger legal parameter value, not admitted as a default-capacity prompt. "
                 "All individual AddedTokens and 32-token concatenations execute at 4096. "
                 "Existing default-capacity rejection tests remain mandatory",
    })
    run_rtl(evidence, info, ordinary, "deepseek")
    evidence.run_cases([
        (f"deepseek-large-profile-{seed}",
         lambda scope, seed=seed: rtl_case(
             scope, info, large, seed, "verilator", capacity, 50000000, "deepseek-large"))
        for seed in (1, 17, 89)
    ])


if __name__ == "__main__":
    require(len(sys.argv) == 2, "Usage: ./.venv/bin/python tests/deepseek_integration.py FRESH")
    directory = Path(sys.argv[1])
    require(not directory.is_absolute() and ".." not in directory.parts and
            directory.parts[:2] in (("evidence", "preparation"), ("evidence", "verification"))
            and directory.is_dir(), "A present project-relative evidence directory is required")
    prepare(directory)
