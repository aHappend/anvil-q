"""Complete official DeepSeek tables and independent public-port RTL comparisons.

Raw tokenizer.json policy is explicit: identity normalization, enabled literal
AddedTokens and no automatic BOS/EOS. The model-level tokenizer_config.json
add_bos_token setting is recorded separately, not silently applied or certified.
No weights, SPI boot or inference are supplied by this fixture.
"""

import copy
import difflib
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


def bos_vectors(directory, config, source):
    """Compare explicit model-config policy with the installed tokenizer backend."""
    import tokenizers

    require(config["add_bos_token"] is True and config["add_eos_token"] is False
            and config["clean_up_tokenization_spaces"] is False,
            "Unrepresented DeepSeek model-level token policy")
    bos = config["bos_token"]
    require(bos == {"__type": "AddedToken",
                    "content": "<\uff5cbegin\u2581of\u2581sentence\uff5c>",
                    "lstrip": False, "normalized": True, "rstrip": False,
                    "single_word": False}, "Unexpected pinned BOS policy")
    added, = [item for item in source["added_tokens"] if item["content"] == bos["content"]]
    require(added["id"] == 0 and added["special"] and added["normalized"] is False,
            "BOS does not resolve to the pinned special token")
    official = tokenizers.Tokenizer.from_file(str(ROOT / "tests/data/deepseek-tokenizer.json"))
    require(json.loads(official.to_str())["post_processor"] == source["post_processor"],
            "Unexpected raw backend postprocessor")
    official.post_processor = tokenizers.processors.Sequence([
        official.post_processor,
        tokenizers.processors.TemplateProcessing(
            single=f"{bos['content']}:0 $A:0",
            special_tokens=[(bos["content"], added["id"])]),
    ])
    raw = json.loads((directory / "official-vectors.json").read_bytes())
    prefix = bos["content"].encode()
    vectors = []
    for row in raw["vectors"]:
        expected = [added["id"], *row["token_ids"]]
        text = bytes.fromhex(row["utf8_hex"]).decode()
        observed = official.encode(text, add_special_tokens=True)
        decoded = official.decode(observed.ids, skip_special_tokens=False).encode()
        require(observed.ids == expected and
                observed.special_tokens_mask == [1, *([0] * len(row["token_ids"]))],
                "Backend automatic-BOS token/mask mismatch")
        require(decoded == prefix + bytes.fromhex(row["decoded_utf8_hex"]),
                "Automatic-BOS decoded bytes differ from independent concatenation")
        require(official.encode(text, add_special_tokens=False).ids == row["token_ids"],
                "Automatic-BOS configuration altered raw-text policy")
        vectors.append({**row, "token_ids": expected, "decoded_utf8_hex": decoded.hex()})
    literal = [row for row in vectors if row["text"] == bos["content"]]
    require(len(literal) == 1 and literal[0]["token_ids"] == [0, 0],
            "Literal BOS must not silently suppress the automatic prefix")
    save(directory / "model-bos-vectors.json", {
        "policy": "Raw single-sequence text, no chat template; exactly one automatic "
                  "BOS before the complete raw vector, no automatic EOS; "
                  "decode with skip_special_tokens=False",
        "oracle": "Independent prefix/byte concatenation from pinned model configuration "
                  "cross-checked with installed tokenizers==0.21.4 TemplateProcessing",
        "limit": "Transformers is not installed or executed. This checks the declared "
                 "single-sequence configuration semantics, not that wrapper implementation, "
                 "chat templates, paired input, model weights or inference",
        "bos_token_id": added["id"], "bos_utf8_hex": prefix.hex(),
        "normalization_policy": "The pinned raw AddedToken has normalized=false, "
                                "whereas model config declares normalized=true. "
                                "Preserve the raw table's policy; normalization is "
                                "identity for this profile. No wrapper override is inferred",
        "compared_token_vectors": len(vectors), "compared_byte_vectors": len(vectors),
        "vectors": vectors,
    })
    return added["id"]


def prepare(directory, model_bos=False):
    installed_identity(directory)
    reference(directory)
    source = json.loads((ROOT / "tests/data/deepseek-tokenizer.json").read_bytes())
    config = json.loads((ROOT / "tests/data/deepseek-tokenizer_config.json").read_bytes())
    bos_id = bos_vectors(directory, config, source) if model_bos else 0
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
    metadata = [2, 2, VOCABULARY, 0, 1, int(model_bos), bos_id, 1, 0x100000,
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
    if model_bos:
        info["model_wrapper_policy_scope"] = (
            "Declared single-sequence automatic-BOS semantics applied in metadata. "
            "Independent prefix/byte concatenation compared to the installed backend "
            "configured with TemplateProcessing. Transformers wrapper is not executed")
        info["scope"] = "Complete DeepSeek tables with declared automatic-BOS policy; " \
                        "not SPI boot or weighted inference"
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


def run_deepseek_bos(evidence):
    evidence.tools(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
    evidence.child([
        "./.venv/bin/python", "tests/deepseek_integration.py",
        evidence.relative(evidence.path), "--model-bos",
    ], "deepseek-model-bos-preparation")
    info = json.loads((evidence.path / "complete-table-fixture.json").read_bytes())
    record = json.loads((evidence.path / "model-bos-vectors.json").read_bytes())
    vectors = [{"case": index, "input_utf8_hex": row["utf8_hex"],
                "token_ids": row["token_ids"], "decoded_utf8_hex": row["decoded_utf8_hex"]}
               for index, row in enumerate(record["vectors"])]
    ordinary = [row for row in vectors if len(bytes.fromhex(row["input_utf8_hex"])) <= 4096]
    large = [row for row in vectors if len(bytes.fromhex(row["input_utf8_hex"])) > 4096]
    require(len(large) == 1 and len(ordinary) + len(large) == len(vectors) == 881,
            "Incomplete automatic-BOS matrix")
    largest = max(len(bytes.fromhex(row["input_utf8_hex"])) for row in large)
    capacity = 1 << (largest - 1).bit_length()
    run_rtl(evidence, info, ordinary, "deepseek-bos")
    evidence.run_cases([
        (f"deepseek-bos-large-profile-{seed}",
         lambda scope, seed=seed: rtl_case(
             scope, info, large, seed, "verilator", capacity, 50000000,
             "deepseek-bos-large"))
        for seed in (1, 17, 89)
    ])
    compact = [row for row in ordinary if row["input_utf8_hex"] == "65cc81"]
    require(len(compact) == 1, "Missing BOS sensitivity vector")
    bos_mutations(evidence, info, compact)


def bos_mutations(evidence, info, vectors):
    source = "rtl/anvil_edge_bpe_tokenizer.sv"
    original = (ROOT / source).read_text()
    mutations = (
        ("missing-prefix", "token_count<=cfg_metadata[5*32+:32];", "token_count<=0;"),
        ("wrong-prefix", "tokens[0]<=cfg_metadata[6*32+:32];",
         "tokens[0]<=cfg_metadata[6*32+:32]^32'd1;"),
    )
    for name, before, after in mutations:
        require(original.count(before) == 1, f"Ambiguous BOS mutation: {name}")
        directory = evidence.path / ("bos-mutant-" + name)
        directory.mkdir()
        path = directory / Path(source).name
        changed = original.replace(before, after)
        path.write_text(changed, encoding="ascii")
        diff = directory / "mutation.diff"
        diff.write_text("".join(difflib.unified_diff(
            original.splitlines(True), changed.splitlines(True),
            fromfile=source, tofile="mutant/" + source)), encoding="ascii")
        mutant = copy.copy(evidence)
        mutant.path = directory
        mutant.source_overrides = {**evidence.source_overrides, source: evidence.relative(path)}
        mutant.name_prefix = "bos-mutant-" + name + "-"
        first = len(evidence.record["coverage"])
        failure = None
        try:
            rtl_case(mutant, info, vectors, 17, "verilator", 64, 500000, "deepseek-bos")
        except Exception as error:
            failure = error
        rows = evidence.record["coverage"][first:]
        require(len(rows) == 1 and failure is not None,
                f"BOS mutant lacks exactly one executed functional rejection: {name}; "
                f"observed error={failure}")
        row = rows[0]
        child = row.get("simulation_receipt", {})
        require(row.get("compile_receipt", {}).get("exit_code") == 0 and
                child.get("exit_code") not in (0, None) and not child.get("timed_out") and
                child.get("child_settled") and child.get("process_group_settled"),
                f"BOS mutant lacks a compiled, settled functional rejection: {name}")
        output = (ROOT / child["stdout"]).read_text() + (ROOT / child["stderr"]).read_text()
        assertion = "DEEPSEEK-BOS_OFFICIAL_TOKEN"
        require(assertion in output and "%Error:" in output,
                f"BOS mutant missed original token assertion: {name}")
        row.update(status="expected-functional-rejection", mutation_assertion=assertion)
        evidence.record.setdefault("bos_mutations", []).append({
            "name": name, "status": "killed", "assertion": assertion,
            "diff": evidence.relative(diff), "simulation": child,
        })


def run_deepseek_boot(evidence):
    from storage import boot_test, synthetic_image, words

    evidence.tools(("python3", "verilator", "g++", "make"))
    evidence.child([
        "./.venv/bin/python", "tests/deepseek_integration.py", evidence.relative(evidence.path),
    ], "deepseek-complete-table-preparation")
    info = json.loads((evidence.path / "complete-table-fixture.json").read_bytes())
    payloads = {0x200: words(*info["metadata"])}
    for entry in info["tables"]:
        data = (evidence.path / f"table-{entry['kind']:03x}.bin").read_bytes()
        require(hashlib.sha256(data).hexdigest() == entry["sha256"],
                "DeepSeek table changed before boot serialization")
        payloads[entry["kind"]] = data
    fixture = synthetic_image(VOCABULARY, capacity=131072, table_payloads=payloads)
    fixture["synthetic_only"] = False
    fixture["input_provenance"] = {
        "tokenizer_tables": "Complete pinned official DeepSeek raw-text table conversion",
        "weights": "Synthetic zero tensors, minimum geometry, not a pretrained model",
    }
    save(evidence.path / "official-boot-scope.json", {
        "scope": "Real SPI-to-DDR boot and full table-validation pipeline only, "
                 "with complete pinned DeepSeek raw-text tables and synthetic H8/L1 "
                 "zero weights; not inference or physical memory",
        "image_sha256": hashlib.sha256(fixture["image"]).hexdigest(),
        "image_bytes": len(fixture["image"]), "active_vocabulary": VOCABULARY,
        "physical_capacity": 131072, "synthetic_core_geometry": fixture["geometry"],
        "seed": 17,
    })
    boot_test(evidence, VOCABULARY, 17, capacity=131072,
              fixture=fixture, label="complete-official-deepseek-tables")


if __name__ == "__main__":
    require(len(sys.argv) in (2, 3) and
            (len(sys.argv) == 2 or sys.argv[2] == "--model-bos"),
            "Usage: ./.venv/bin/python tests/deepseek_integration.py FRESH [--model-bos]")
    directory = Path(sys.argv[1])
    require(not directory.is_absolute() and ".." not in directory.parts and
            directory.parts[:2] in (("evidence", "preparation"), ("evidence", "verification"))
            and directory.is_dir(), "A present project-relative evidence directory is required")
    prepare(directory, model_bos=len(sys.argv) == 3)
