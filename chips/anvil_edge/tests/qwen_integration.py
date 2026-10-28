"""Complete Qwen table fixture and public-port tokenizer/oracle comparisons.

This fixture supplies configuration directly, not through SPI boot. It contains
no weights or inference model. Candidate Unicode source identities are kept
distinct from the installed official library's measured behavior.
"""

import hashlib
import json
from pathlib import Path
import random
import re
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from official import ROOT, TOKENIZERS_VERSION, installed_identity, manifest, validate
from protocol import bpe_reference
from qwen_regex import PATTERN, rule_oracle
from qwen_tables import (
    BASE, VOCABULARY, audit_fragments, encode_fragments, inverse_byte_alphabet,
    load_source, require,
)
from unicode_tables import Converted, LIMIT, scalar


SCOPE = (
    "Complete pinned Qwen tables supplied to public tokenizer/detokenizer ports; "
    "not SPI boot, weighted inference, other vocabulary families or hardware acceptance"
)


def save(path, value):
    with path.open("x", encoding="ascii") as output:
        json.dump(value, output, indent=2, ensure_ascii=True)
        output.write("\n")


def corpus(source):
    prompts = json.loads((ROOT / "tests/data/requirements.json").read_bytes())["prompts"]
    cases = prompts + [
        "caf\u00e9 e\u0301 \u4e2d\u6587 \U0001f600",
        "  \t\n12345\r\n",
        "<|im_start|>user\nhello<|im_end|>",
        "<tool_call>hello</tool_call>",
        "I'm WE'RE she'd can't we'll",
        "\u212b \ufb03 \u1100\u1161",
        "a\u0315\u0300 \u0344 A\u030a\u0301 \U00011099\U000110ba \U0001d15e",
        "\U00011935\U00011930 \u1c89 \u1c8a \U0001e030",
        "'\u017f 'S 'T 'RE 'VE 'M 'LL 'D \u00df \ufb05 \ufb06",
        "x  y  !\t \r\n\n \u00a0  ",
        "a", "\U0001f600", "e\u0301", "\x00\x01\x7f",
    ]
    cases.extend(item["content"] for item in source["added_tokens"])
    cases.append(" ".join(item["content"] for item in source["added_tokens"]))
    for seed in (1, 17, 89):
        rng = random.Random(seed)
        alphabet = list("aAzZ019 \t\r\n!?'") + [
            "\u00e9", "\u0301", "\u017f", "\u4e2d", "\U0001f600", "\u1c89",
        ]
        cases.extend("".join(rng.choice(alphabet) for _ in range(32)) for _ in range(8))
    require(len(cases) == len(set(cases)), "Duplicate official integration cases")
    return cases


def split_added(text, added, normalized):
    """Direct longest source-string matching, independent of serialized trie."""
    for item in added:
        require(not any(item[field] for field in ("single_word", "lstrip", "rstrip")),
                "Pinned AddedToken requires additional matching semantics")
    parts, pending, position = [], "", 0
    while position < len(text):
        candidates = [
            (-len(item["content"].encode()), index, item)
            for index, item in enumerate(added)
            if item["normalized"] == normalized and text.startswith(item["content"], position)
        ]
        if not candidates:
            pending += text[position]
            position += 1
            continue
        _, _, item = min(candidates)
        if pending:
            parts.append(pending)
            pending = ""
        parts.append(item["id"])
        position += len(item["content"])
    if pending:
        parts.append(pending)
    return parts


def encode(text, source, converted, byte_ids, merges):
    result = []
    for raw in split_added(text, source["added_tokens"], False):
        if isinstance(raw, int):
            result.append(raw)
            continue
        normalized = "".join(map(chr, converted.normalize(tuple(map(ord, raw)))))
        for part in split_added(normalized, source["added_tokens"], True):
            if isinstance(part, int):
                result.append(part)
                continue
            for first, last in rule_oracle([converted.symbol(ord(char)) for char in part]):
                base = [byte_ids[byte] for byte in part[first:last].encode()]
                result.extend(bpe_reference(base, merges))
    return result


def compare_components(converted, tokenizer, tokenizers):
    """Measure official behavior without inferring the wheel's Rust dependency graph."""
    normalizer = tokenizer.normalizer
    split = tokenizers.pre_tokenizers.Split(tokenizers.Regex(PATTERN), behavior="isolated")
    digest = hashlib.sha256()
    normalizations, classifications = 0, 0
    for value in range(LIMIT):
        if not scalar(value):
            continue
        text = chr(value)
        expected = "".join(map(chr, converted.normalize([value])))
        actual = normalizer.normalize_str(text)
        require(actual == expected, f"Official scalar NFC mismatch U+{value:04X}")
        digest.update(struct.pack("<I", value) + actual.encode())
        normalizations += 1
        text = "a" + text + "b"
        spans = rule_oracle([converted.symbol(ord(char)) for char in text])
        expected_parts = [(text[first:last], (first, last)) for first, last in spans]
        actual_parts = split.pre_tokenize_str(text)
        require(actual_parts == expected_parts,
                f"Official contextual classification mismatch U+{value:04X}: "
                f"{actual_parts!r} != {expected_parts!r}")
        classifications += 1
    # Scalar NFC alone does not test composition, canonical order or blocking.
    conformance = 0
    for line in converted.raw["ucd-9.0.0-NormalizationTest.txt"].decode().splitlines():
        content = line.split("#", 1)[0].strip()
        if not content or content.startswith("@"):
            continue
        columns = ["".join(chr(int(value, 16)) for value in field.split())
                   for field in content.split(";")[:5]]
        for given, target in zip(columns, (1, 1, 1, 3, 3)):
            require(normalizer.normalize_str(given) == columns[target],
                    f"Official NFC conformance mismatch row={conformance // 5}")
            conformance += 1
    for seed in (1, 17, 89):
        rng = random.Random(seed)
        values = [value for row in converted.ranges for value in row[:2]]
        for _ in range(1000):
            text = "".join(chr(rng.choice(values)) for _ in range(rng.randrange(1, 32)))
            spans = rule_oracle([converted.symbol(ord(char)) for char in text])
            expected_parts = [(text[first:last], (first, last)) for first, last in spans]
            require(split.pre_tokenize_str(text) == expected_parts,
                    f"Official ordered regex mismatch seed={seed}")
            classifications += 1
    require(normalizations == LIMIT - 0x800 and
            classifications == normalizations + 3000 and
            conformance == converted.normalization_vectors * 5,
            "Incomplete official component comparison counts")
    witnesses = {}
    for text in ("\U00011935\U00011930", "a\u1c89b", "'\u017f", "a\u0315\u0300"):
        witnesses[text.encode().hex()] = {
            "nfc_utf8_hex": normalizer.normalize_str(text).encode().hex(),
            "split": split.pre_tokenize_str(text),
        }
    return {
        "all_scalar_nfc_comparisons": normalizations,
        "all_scalar_context_and_random_split_comparisons": classifications,
        "ucd9_nfc_conformance_comparisons": conformance,
        "scalar_nfc_transcript_sha256": digest.hexdigest(),
        "witnesses": witnesses,
        "limit": "Measured semantic agreement, not identification of embedded Rust dependencies "
                 "or an exhaustive proof over all Unicode strings/AddedToken interactions",
    }


def prepare(directory):
    import tokenizers

    directory = Path(directory)
    require(tokenizers.__version__ == TOKENIZERS_VERSION, "Wrong official library version")
    installed_identity(directory)
    source = validate(directory)
    loaded, pieces, flags, byte_ids, merge_rows = load_source()
    require(source == loaded, "Official source changed while preparing fixture")
    converted = Converted()
    official = tokenizers.Tokenizer.from_file(str(ROOT / "tests/data/qwen-tokenizer.json"))
    components = compare_components(converted, official, tokenizers)
    save(directory / "official-component-comparisons.json", components)
    merges = {(left, right): (result, rank) for left, right, result, rank in merge_rows}
    vectors = []
    alphabet = inverse_byte_alphabet()
    for index, text in enumerate(corpus(source)):
        expected = official.encode(text, add_special_tokens=False).ids
        calculated = encode(text, source, converted, byte_ids, merges)
        require(calculated == expected,
                f"Independent complete Qwen vector mismatch case={index}: {calculated} != {expected}")
        decoded = b"".join(pieces[token] for token in expected)
        official_bytes = official.decode(expected, skip_special_tokens=False).encode()
        require(decoded == official_bytes, f"Official decoded bytes mismatch case={index}")
        require(bool(expected) and bool(decoded), "Empty fixture would not test public output")
        # Also compare official ByteLevel stage's byte alphabet where exposed.
        for spelling, _ in official.pre_tokenizer.pre_tokenize_str(text):
            require(all(char in alphabet for char in spelling), "Unrepresented ByteLevel alphabet")
        vectors.append({"case": index, "input_utf8_hex": text.encode().hex(),
                        "token_ids": expected, "decoded_utf8_hex": decoded.hex()})
    require(all(len(row["token_ids"]) > 1 for row in vectors[:5]),
            "A mandatory benchmark prompt did not produce multiple tokens")
    save(directory / "official-vectors.json", vectors)
    tables = encode_fragments(pieces, flags, byte_ids, merge_rows, source["added_tokens"])
    audit = audit_fragments(tables, source)
    require(not set(tables).intersection(converted.blobs), "Conflicting serialized table kinds")
    tables.update(converted.blobs)
    require(set(tables) == set(range(0x201, 0x210)), "Missing complete tokenizer table")
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
    metadata = [2, 1, VOCABULARY, 1, 1, 0, 0, 151645, 0x100000,
                converted.profile["classes"], converted.profile["start"],
                converted.profile["dead"], 32, 0, max(map(len, pieces)), 4096]
    metadata.extend(struct.unpack("<8I", bytes.fromhex(manifest()["bundle_sha256"])))
    metadata.extend([0x090000, 0x100000, *([0] * 6)])
    require(len(metadata) == 32, "Wrong metadata extent")
    with (directory / "tables.hex").open("x", encoding="ascii") as output:
        output.write("".join(f"{word:08x}\n" for word, in struct.iter_unpack("<I", combined)))
    info = {
        "scope": SCOPE, "bootable": False, "metadata": metadata,
        "bases": bases, "counts": counts, "tables": entries,
        "memory_base": BASE, "memory_bytes": len(combined),
        "memory_sha256": hashlib.sha256(combined).hexdigest(),
        "memory_hex_sha256": hashlib.sha256((directory / "tables.hex").read_bytes()).hexdigest(),
        "source_audit": audit, "official_vector_comparisons": len(vectors),
        "components": components,
        "unicode_table_identity": "Pinned candidate source maps, primary-UCD audited; measured "
                                  "official agreement is recorded separately, not inferred linkage",
    }
    save(directory / "complete-table-fixture.json", info)
    print(f"OFFICIAL_QWEN_VECTORS {len(vectors)} SCALAR_NFC {components['all_scalar_nfc_comparisons']}")


def run_qwen_integration(evidence):
    evidence.tools(("python3", "verilator", "g++", "make"))
    evidence.child([
        "./.venv/bin/python", "tests/qwen_integration.py", evidence.relative(evidence.path),
    ], "official-qwen-complete-table-preparation")
    info = json.loads((evidence.path / "complete-table-fixture.json").read_bytes())
    vectors = json.loads((evidence.path / "official-vectors.json").read_bytes())
    run_rtl(evidence, info, vectors)


def run_qwen_boot(evidence):
    from storage import boot_test, synthetic_image, words

    evidence.tools(("python3", "verilator", "g++", "make"))
    evidence.child([
        "./.venv/bin/python", "tests/qwen_integration.py", evidence.relative(evidence.path),
    ], "official-qwen-complete-table-preparation")
    info = json.loads((evidence.path / "complete-table-fixture.json").read_bytes())
    payloads = {0x200: words(*info["metadata"])}
    for entry in info["tables"]:
        data = (evidence.path / f"table-{entry['kind']:03x}.bin").read_bytes()
        require(hashlib.sha256(data).hexdigest() == entry["sha256"],
                "Pinned complete tables changed before boot-image serialization")
        payloads[entry["kind"]] = data
    fixture = synthetic_image(VOCABULARY, capacity=151936, table_payloads=payloads)
    fixture["synthetic_only"] = False
    fixture["input_provenance"] = {
        "tokenizer_bundle_sha256": manifest()["bundle_sha256"],
        "tokenizer_tables": "Complete pinned official Qwen asset conversion; source hashes "
                            "and official comparisons are retained in this invocation",
        "weights": "Synthetic zero tensors, minimum geometry, not an actual pretrained model",
    }
    save(evidence.path / "official-boot-scope.json", {
        "scope": "Real SPI-to-DDR boot and complete table-validation pipeline only, "
                 "with all pinned official Qwen tables and synthetic minimum-geometry "
                 "zero weights. Not inference, production default geometry or physical memory.",
        "tokenizer_bundle_sha256": manifest()["bundle_sha256"],
        "image_sha256": hashlib.sha256(fixture["image"]).hexdigest(),
        "image_bytes": len(fixture["image"]),
        "active_vocabulary": VOCABULARY, "physical_capacity": 151936,
        "synthetic_core_geometry": fixture["geometry"], "seed": 17,
    })
    boot_test(evidence, VOCABULARY, 17, capacity=151936,
              fixture=fixture, label="complete-official-qwen-tables")


def run_rtl(evidence, info, vectors):
    raw = (evidence.path / "tables.hex").read_bytes()
    require(hashlib.sha256(raw).hexdigest() == info["memory_hex_sha256"],
            "Complete table memory changed before RTL execution")
    memory = b"".join(struct.pack("<I", int(word, 16)) for word in raw.splitlines())
    require(len(memory) == info["memory_bytes"] and
            hashlib.sha256(memory).hexdigest() == info["memory_sha256"],
            "Complete table memory contents differ from serialized inputs")
    for entry in info["tables"]:
        blob = (evidence.path / f"table-{entry['kind']:03x}.bin").read_bytes()
        start = entry["base"] - BASE
        require(hashlib.sha256(blob).hexdigest() == entry["sha256"] and
                len(blob) == entry["bytes"] and memory[start:start + len(blob)] == blob,
                "Serialized complete table differs from RTL memory")
    compact = [row for row in vectors if row["input_utf8_hex"] == "65cc81"]
    require(len(compact) == 1, "Missing compact complete-profile portability case")
    rtl_case(evidence, info, compact, 17, "iverilog", 64, 500000)
    evidence.run_cases([
        (f"qwen-complete-profile-{seed}",
         lambda scope, seed=seed: rtl_case(scope, info, vectors, seed, "verilator", 4096, 50000000))
        for seed in (1, 17, 89)
    ])


def rtl_case(evidence, info, vectors, seed, simulator, capacity, cycles):
    directory = evidence.path / f"qwen-vectors-{simulator}-s{seed}"
    directory.mkdir()
    flat = {"input": [], "token": [], "byte": [], "length": []}
    for row in vectors:
        inputs = list(bytes.fromhex(row["input_utf8_hex"]))
        outputs = list(bytes.fromhex(row["decoded_utf8_hex"]))
        require(0 < len(inputs) <= capacity and len(row["token_ids"]) <= capacity,
                "Fixture exceeds declared tokenizer capacity")
        flat["input"].extend(inputs)
        flat["token"].extend(row["token_ids"])
        flat["byte"].extend(outputs)
        flat["length"].extend((len(inputs), len(row["token_ids"]), len(outputs)))
    paths = {}
    for name, values in flat.items():
        path = directory / f"{name}.hex"
        with path.open("x", encoding="ascii") as output:
            output.write("".join(f"{value:08x}\n" for value in values))
        paths[name] = evidence.relative(path)
    # A case scope lives below the preparation root; tables remain immutable there.
    table_path = evidence._root.path / "tables.hex"
    pack = lambda values, width: sum(value << (width * index) for index, value in enumerate(values))
    allowed = " || ".join(
        f"(address>=64'h{entry['base'] + 32:x} && "
        f"address<64'h{(entry['base'] + entry['bytes'] + 3) & ~3:x})"
        for entry in info["tables"] if entry["bytes"] > 32
    )
    bench = r"""
module bench;
  reg clk=0,rst_n;
  always #5 clk=~clk;
  reg start=0,in_valid=0,in_last=0,byte_ready=0;
  reg [7:0] in_data=0;
  wire in_ready,token_valid,token_ready,token_last,byte_valid,byte_last;
  wire [31:0] token_id;
  wire [7:0] byte_data;
  wire [1:0] busy,done,error,req_valid,rsp_ready;
  wire [7:0] error_code[0:1];
  wire [63:0] req_address[0:1];
  reg [1:0] req_ready=0,rsp_valid=0;
  reg [31:0] rsp_data[0:1];
  wire finish_ready;
  anvil_edge_bpe_tokenizer #(.MAX_PROMPT_BYTES(@CAPACITY@),
    .MAX_PROMPT_TOKENS(@CAPACITY@),.MAX_PRETOKEN_BYTES(4096)) tokenizer(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_table_bases(1024'h@BASES@),.cfg_table_counts(512'h@COUNTS@),
    .cfg_metadata(1024'h@METADATA@),
    .in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),.in_last(in_last),
    .out_valid(token_valid),.out_ready(token_ready),
    .out_token_id(token_id),.out_last(token_last),
    .busy(busy[0]),.done(done[0]),.error(error[0]),.error_code(error_code[0]),
    .tbl_req_valid(req_valid[0]),.tbl_req_ready(req_ready[0]),.tbl_req_addr(req_address[0]),
    .tbl_rsp_valid(rsp_valid[0]),.tbl_rsp_ready(rsp_ready[0]),
    .tbl_rsp_data(rsp_data[0]),.tbl_rsp_error(1'b0));
  anvil_edge_detokenizer detokenizer(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_vocab_size(32'd@VOCABULARY@),
    .cfg_token_records_base(64'h@RECORD_BASE@),.cfg_token_bytes_base(64'h@BYTE_BASE@),
    .cfg_token_bytes_count(64'd@BYTE_COUNT@),
    .cfg_max_token_byte_length(32'd@MAX_TOKEN_BYTES@),
    .in_valid(token_valid),.in_ready(token_ready),.in_token_id(token_id),.in_last(token_last),
    .out_valid(byte_valid),.out_ready(byte_ready),.out_data(byte_data),.out_last(byte_last),
    .finish_valid(1'b0),.finish_ready(finish_ready),
    .busy(busy[1]),.done(done[1]),.error(error[1]),.error_code(error_code[1]),
    .tbl_req_valid(req_valid[1]),.tbl_req_ready(req_ready[1]),.tbl_req_addr(req_address[1]),
    .tbl_rsp_valid(rsp_valid[1]),.tbl_rsp_ready(rsp_ready[1]),
    .tbl_rsp_data(rsp_data[1]),.tbl_rsp_error(1'b0));
  reg [31:0] table_words[0:@MEMORY_LAST@];
  reg [31:0] inputs[0:@INPUT_LAST@],tokens[0:@TOKEN_LAST@];
  reg [31:0] bytes_expected[0:@BYTE_LAST@],lengths[0:@LENGTH_LAST@];
  initial begin
    $readmemh("@TABLE_PATH@",table_words);
    $readmemh("@INPUT_PATH@",inputs);
    $readmemh("@TOKEN_PATH@",tokens);
    $readmemh("@BYTE_PATH@",bytes_expected);
    $readmemh("@LENGTH_PATH@",lengths);
  end
  function automatic [31:0] memory(input [63:0] address);
    begin
      if (address[1:0]!==0 || !(@ALLOWED@))
        $fatal(1,"QWEN_TABLE_ADDRESS address=%h",address);
      memory=table_words[(address-64'h@MEMORY_BASE@)>>2];
    end
  endfunction
  reg [31:0] rng=@SEED@;
  reg pending[0:1],req_held[0:1];
  reg [63:0] saved_address[0:1],held_address[0:1];
  integer delay_count[0:1],requests[0:1],responses[0:1],stalls[0:1];
  integer frame=0,input_count=0,token_count=0,byte_count=0;
  integer frame_inputs=0,frame_tokens=0,frame_bytes=0;
  integer token_done=0,byte_done=0,compared=0,completed_frames=0;
  integer token_stalls=0,byte_stalls=0;
  reg token_held=0,byte_held=0;
  reg [32:0] held_token=0;
  reg [8:0] held_byte=0;
  task automatic reset_check;
    begin
      if ({in_ready,token_valid,token_ready,token_last,token_id,byte_valid,
           byte_last,byte_data,busy,done,error,error_code[0],error_code[1],
           req_valid,rsp_ready,req_address[0],req_address[1],finish_ready} !== '0)
        $fatal(1,"QWEN_COMPLETE_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
    req_ready={rng[2],rng[0]};
    byte_ready=rng[1] && rng[3];
    for (integer port_index=0;port_index<2;port_index=port_index+1) begin
      if (pending[port_index] && !rsp_valid[port_index]) begin
        if (delay_count[port_index]==0) begin
          rsp_valid[port_index]<=1;
          rsp_data[port_index]=memory(saved_address[port_index]);
        end else delay_count[port_index]=delay_count[port_index]-1;
      end
    end
  end
  always @(posedge clk) if (rst_n) begin
    if ((^{in_ready,token_valid,token_ready,token_last,token_id,byte_valid,
           byte_last,byte_data,busy,done,error,error_code[0],error_code[1],
           req_valid,rsp_ready,req_address[0],req_address[1],finish_ready})===1'bx)
      $fatal(1,"QWEN_COMPLETE_XZ");
    if (error!==0)
      $fatal(1,"QWEN_COMPLETE_ERROR frame=%0d code=%h/%h",
             frame,error_code[0],error_code[1]);
    if (token_held && (!token_valid || {token_last,token_id}!==held_token))
      $fatal(1,"QWEN_TOKEN_STABILITY");
    if (byte_held && (!byte_valid || {byte_last,byte_data}!==held_byte))
      $fatal(1,"QWEN_BYTE_STABILITY");
    token_held=token_valid && !token_ready; held_token={token_last,token_id};
    byte_held=byte_valid && !byte_ready; held_byte={byte_last,byte_data};
    if (token_held) token_stalls=token_stalls+1;
    if (byte_held) byte_stalls=byte_stalls+1;
    if (in_valid && in_ready) begin
      if (input_count>=@INPUT_COUNT@ || in_data!==inputs[input_count][7:0] ||
          in_last!==(frame_inputs==lengths[frame*3]-1))
        $fatal(1,"QWEN_INPUT_SOURCE_BINDING");
      input_count=input_count+1; frame_inputs=frame_inputs+1; compared=compared+1;
    end
    if (token_valid) begin
      if (frame_inputs!=lengths[frame*3])
        $fatal(1,"QWEN_PARTIAL_PROMPT_PUBLICATION");
      if (token_count>=@TOKEN_COUNT@ ||
          token_id!==tokens[token_count] ||
          token_last!==(frame_tokens==lengths[frame*3+1]-1))
        $fatal(1,"QWEN_OFFICIAL_TOKEN frame=%0d item=%0d expected=%h got=%h",
               frame,frame_tokens,tokens[token_count],token_id);
      if (token_ready) begin
        token_count=token_count+1; frame_tokens=frame_tokens+1; compared=compared+1;
      end
    end
    if (byte_valid && byte_ready) begin
      if (byte_count>=@BYTE_COUNT_TOTAL@ ||
          byte_data!==bytes_expected[byte_count][7:0] ||
          byte_last!==(frame_bytes==lengths[frame*3+2]-1))
        $fatal(1,"QWEN_OFFICIAL_BYTE frame=%0d item=%0d expected=%h got=%h",
               frame,frame_bytes,bytes_expected[byte_count],byte_data);
      byte_count=byte_count+1; frame_bytes=frame_bytes+1; compared=compared+1;
    end
    for (integer port_index=0;port_index<2;port_index=port_index+1) begin
      if (req_held[port_index] &&
          (!req_valid[port_index] || req_address[port_index]!==held_address[port_index]))
        $fatal(1,"QWEN_TABLE_REQUEST_STABILITY");
      req_held[port_index]=req_valid[port_index] && !req_ready[port_index];
      held_address[port_index]=req_address[port_index];
      if (req_held[port_index]) stalls[port_index]=stalls[port_index]+1;
      if (rsp_valid[port_index] && rsp_ready[port_index]) begin
        if (!pending[port_index]) $fatal(1,"QWEN_ORPHAN_TABLE_RESPONSE");
        pending[port_index]=0; rsp_valid[port_index]<=0;
        responses[port_index]=responses[port_index]+1; compared=compared+1;
      end
      if (req_valid[port_index] && req_ready[port_index]) begin
        if (pending[port_index]) $fatal(1,"QWEN_TABLE_OUTSTANDING");
        pending[port_index]=1; saved_address[port_index]=req_address[port_index];
        delay_count[port_index]=1+rng[5:4];
        requests[port_index]=requests[port_index]+1;
      end
    end
    if (done[0]) begin
      if (frame_tokens!=lengths[frame*3+1] || token_done!=0)
        $fatal(1,"QWEN_TOKEN_DONE_COUNT");
      token_done=token_done+1;
    end
    if (done[1]) begin
      if (frame_bytes!=lengths[frame*3+2] || byte_done!=0)
        $fatal(1,"QWEN_BYTE_DONE_COUNT");
      byte_done=byte_done+1;
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic send_byte(input [7:0] value,input bit last);
    begin
      @(negedge clk); #1; in_valid=1; in_data=value; in_last=last;
      do begin @(posedge clk); end while (!in_ready);
      #1; @(negedge clk); #1; in_valid=0;
    end
  endtask
  integer source_cursor=0;
  initial begin
    rst_n=0;
    for (integer port_index=0;port_index<2;port_index=port_index+1) begin
      rsp_data[port_index]=0; pending[port_index]=0; req_held[port_index]=0;
      saved_address[port_index]=0; held_address[port_index]=0;
      delay_count[port_index]=0; requests[port_index]=0;
      responses[port_index]=0; stalls[port_index]=0;
    end
    #0; reset_check();
    repeat (2) tick();
    @(negedge clk); #1; rst_n=1;
    for (frame=0;frame<@FRAMES@;frame=frame+1) begin
      token_done=0; byte_done=0; frame_inputs=0; frame_tokens=0; frame_bytes=0;
      @(negedge clk); #1; start=1; tick();
      @(negedge clk); #1; start=0;
      for (integer item=0;item<lengths[frame*3];item=item+1) begin
        send_byte(inputs[source_cursor][7:0],item==lengths[frame*3]-1);
        source_cursor=source_cursor+1;
      end
      while (token_done==0 || byte_done==0) tick();
      repeat (4) tick();
      if (busy!==0 || req_valid!==0 || rsp_valid!==0 ||
          pending[0] || pending[1] || requests[0]!=responses[0] ||
          requests[1]!=responses[1] || token_done!=1 || byte_done!=1)
        $fatal(1,"QWEN_FRAME_DRAIN frame=%0d",frame);
      completed_frames=completed_frames+1; compared=compared+1;
      $display("QWEN_FRAME %0d inputs=%0d tokens=%0d bytes=%0d",
               frame,frame_inputs,frame_tokens,frame_bytes);
    end
    if (input_count!=@INPUT_COUNT@ || token_count!=@TOKEN_COUNT@ ||
        byte_count!=@BYTE_COUNT_TOTAL@ || completed_frames!=@FRAMES@ ||
        stalls[0]==0 || stalls[1]==0 || byte_stalls==0 ||
        (@FRAMES@>1 && token_stalls==0) ||
        compared!=input_count+token_count+byte_count+responses[0]+responses[1]+completed_frames)
      $fatal(1,"QWEN_COMPLETE_COVERAGE");
    $display("QWEN_COUNTS frames=%0d inputs=%0d tokens=%0d bytes=%0d reads=%0d/%0d stalls=%0d/%0d",
             completed_frames,input_count,token_count,byte_count,responses[0],responses[1],
             token_stalls,byte_stalls);
    $display("COMPARED %0d",compared); $finish;
  end
  initial begin
    repeat (@CYCLES@) @(posedge clk);
    $fatal(1,"QWEN_COMPLETE_CYCLE_BOUND frame=%0d",frame);
  end
endmodule
"""
    values = {
        "CAPACITY": capacity, "BASES": f"{pack(info['bases'], 64):x}",
        "COUNTS": f"{pack(info['counts'], 32):x}",
        "METADATA": f"{pack(info['metadata'], 32):x}", "VOCABULARY": VOCABULARY,
        "RECORD_BASE": f"{info['bases'][1]:x}", "BYTE_BASE": f"{info['bases'][2]:x}",
        "BYTE_COUNT": info["counts"][2], "MAX_TOKEN_BYTES": info["metadata"][14],
        "MEMORY_LAST": info["memory_bytes"] // 4 - 1,
        "INPUT_LAST": len(flat["input"]) - 1, "TOKEN_LAST": len(flat["token"]) - 1,
        "BYTE_LAST": len(flat["byte"]) - 1, "LENGTH_LAST": len(flat["length"]) - 1,
        "TABLE_PATH": evidence.relative(table_path),
        **{name.upper() + "_PATH": path for name, path in paths.items()},
        "MEMORY_BASE": f"{BASE:x}", "ALLOWED": allowed, "SEED": seed,
        "FRAMES": len(vectors), "INPUT_COUNT": len(flat["input"]),
        "TOKEN_COUNT": len(flat["token"]), "BYTE_COUNT_TOTAL": len(flat["byte"]),
        "CYCLES": cycles,
    }
    for name, value in values.items():
        bench = bench.replace(f"@{name}@", str(value))
    require(not re.search(r"@[A-Z_]+@", bench), "Unexpanded Qwen bench placeholder")
    sources = ["rtl/anvil_edge_numeric_pkg.sv"] + [
        str(path.relative_to(ROOT)) for path in sorted((ROOT / "rtl").glob("*.sv"))
        if path.name != "anvil_edge_numeric_pkg.sv"
    ]
    evidence.simulate(f"qwen-complete-{simulator}-s{seed}", bench, sources,
                      None, simulator=simulator)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: ./.venv/bin/python tests/qwen_integration.py PROJECT_RELATIVE_EVIDENCE_DIRECTORY")
    directory = Path(sys.argv[1])
    require(not directory.is_absolute() and ".." not in directory.parts and directory.is_dir()
            and directory.parts[:2] in (("evidence", "preparation"), ("evidence", "verification")),
            "Destination must be a fresh existing project evidence directory")
    prepare(directory)
