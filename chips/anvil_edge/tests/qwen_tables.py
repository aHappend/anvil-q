"""Independent ANVLEDG3 vocabulary fragments, never a bootable official image.

Only the pinned Qwen byte vocabulary, merges and AddedToken trie are converted.
NFC, Unicode classification and ordered-regex/tagged-DFA conversion are absent.
The RTL probes bypass boot deliberately and cannot establish tokenizer equivalence.
"""

import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from official import ROOT, manifest, validate


MAGIC = 0x334C4254
BASE = 0x100000
VOCABULARY = 151665
WIDTHS = {0x201: 16, 0x202: 1, 0x203: 4, 0x204: 16,
          0x205: 16, 0x206: 8, 0x20A: 16}
SCOPE = (
    "Partial official-asset vocabulary/merge/AddedToken table fragments only; "
    "not a bootable image, official tokenizer equivalence, or model inference"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inverse_byte_alphabet():
    visible = [*range(33, 127), *range(161, 173), *range(174, 256)]
    alphabet = {chr(value): value for value in visible}
    for index, value in enumerate(value for value in range(256) if value not in visible):
        alphabet[chr(256 + index)] = value
    require(len(alphabet) == 256 and set(alphabet.values()) == set(range(256)),
            "Inverse ByteLevel alphabet is not bijective")
    return alphabet


def load_source():
    source = json.loads((ROOT / "tests/data/qwen-tokenizer.json").read_bytes())
    config = json.loads((ROOT / "tests/data/qwen-tokenizer_config.json").read_bytes())
    require(source["decoder"] == {
        "type": "ByteLevel", "add_prefix_space": False,
        "trim_offsets": False, "use_regex": False,
    }, "Unsupported pinned decoder semantics")
    require(source["normalizer"] == {"type": "NFC"}, "Pinned normalization changed")
    require(config["add_bos_token"] is False, "Unexpected automatic BOS")
    alphabet = inverse_byte_alphabet()
    vocab = source["model"]["vocab"]
    added = source["added_tokens"]
    require(len(vocab) == 151643 and len(added) == 22, "Pinned vocabulary counts changed")
    pieces, flags = [None] * VOCABULARY, [0] * VOCABULARY
    for spelling, token in vocab.items():
        require(type(token) is int and 0 <= token < VOCABULARY and pieces[token] is None,
                "Duplicate/out-of-range source token ID")
        pieces[token] = bytes(alphabet[char] for char in spelling)
        flags[token] = 1
    for item in added:
        token = item["id"]
        require(0 <= token < VOCABULARY and pieces[token] is None,
                "Duplicate/out-of-range AddedToken ID")
        require(set(item) == {"id", "content", "special", "single_word",
                              "lstrip", "rstrip", "normalized"},
                "Unrepresented AddedToken field")
        for field in ("special", "single_word", "lstrip", "rstrip", "normalized"):
            require(type(item[field]) is bool, "Nonboolean AddedToken policy")
        require(config["added_tokens_decoder"][str(token)] ==
                {key: value for key, value in item.items() if key != "id"},
                "AddedToken policies differ between official encodings")
        pieces[token] = item["content"].encode("utf-8")
        # Bit1 is required for trie eligibility; bit0 retains ordinary AddedTokens.
        flags[token] = 2 if item["special"] else 3
    require(all(piece is not None and len(piece) > 0 for piece in pieces),
            "Missing/empty pinned token piece")
    byte_ids = []
    for byte in range(256):
        spelling, = [char for char, value in alphabet.items() if value == byte]
        byte_ids.append(vocab[spelling])
    require(len(set(byte_ids)) == 256, "Byte map has aliases")
    merges = []
    for rank, pair in enumerate(source["model"]["merges"]):
        left, right = pair.split(" ") if isinstance(pair, str) else pair
        merges.append((vocab[left], vocab[right], vocab[left + right], rank))
    require(len(merges) == 151387, "Pinned merge count changed")
    return source, pieces, flags, byte_ids, merges


def table(width, data):
    require(len(data) % width == 0, "Table extent is not an integral record count")
    return struct.pack("<IIIIQQ", MAGIC, 1, width, len(data) // width, len(data), 0) + data


def encode_fragments(pieces, flags, byte_ids, merges, added):
    raw, records = bytearray(), bytearray()
    for token, piece in enumerate(pieces):
        records.extend(struct.pack("<QII", len(raw), len(piece), flags[token]))
        raw.extend(piece)
    nodes = [{"edges": {}, "terminal": 0xFFFFFFFF}]
    for index, item in enumerate(added):
        node = 0
        for byte in pieces[item["id"]]:
            edges = nodes[node]["edges"]
            if byte not in edges:
                edges[byte] = len(nodes)
                nodes.append({"edges": {}, "terminal": 0xFFFFFFFF})
            node = edges[byte]
        require(nodes[node]["terminal"] == 0xFFFFFFFF, "Ambiguous AddedToken spelling")
        nodes[node]["terminal"] = index
    edges, node_records = bytearray(), bytearray()
    for node in nodes:
        node_records.extend(struct.pack("<IIII", len(edges) // 8, len(node["edges"]),
                                        node["terminal"], 0))
        for byte, next_node in sorted(node["edges"].items()):
            edges.extend(struct.pack("<II", byte, next_node))
    specials = bytearray()
    for item in added:
        policy = (1 | int(item["lstrip"]) << 1 | int(item["rstrip"]) << 2 |
                  int(item["single_word"]) << 3 | int(item["normalized"]) << 4)
        specials.extend(struct.pack("<IIII", item["id"], policy, 0, 0))
    payloads = {
        0x201: bytes(records), 0x202: bytes(raw),
        0x203: struct.pack("<256I", *byte_ids),
        0x204: b"".join(struct.pack("<IIII", *row) for row in sorted(merges)),
        0x205: bytes(node_records), 0x206: bytes(edges), 0x20A: bytes(specials),
    }
    return {kind: table(WIDTHS[kind], payload) for kind, payload in payloads.items()}


def audit_fragments(fragments, source, vocabulary=VOCABULARY):
    """Reparse serialized bytes and compare every field against official source."""
    data, counts = {}, {}
    require(set(fragments) == set(WIDTHS), "Unexpected/missing fragment")
    for kind, blob in fragments.items():
        magic, version, width, count, size, reserved = struct.unpack_from("<IIIIQQ", blob)
        require((magic, version, width, reserved) == (MAGIC, 1, WIDTHS[kind], 0),
                "Malformed table header")
        require(size == width * count and len(blob) == 32 + size,
                "Malformed serialized table extent")
        data[kind], counts[kind] = blob[32:], count
    require(counts[0x201] == vocabulary and counts[0x203] == 256,
            "Actual vocabulary was padded/truncated or byte count changed")
    records = list(struct.iter_unpack("<QII", data[0x201]))
    alphabet = inverse_byte_alphabet()
    original = {}
    added_by_id = {item["id"]: item for item in source["added_tokens"]}
    require(len(added_by_id) == len(source["added_tokens"]), "Duplicate AddedToken ID")
    for spelling, token in source["model"]["vocab"].items():
        if token in added_by_id:
            require(spelling == added_by_id[token]["content"],
                    "AddedToken shadows a different base spelling")
            continue
        original[token] = (bytes(alphabet[c] for c in spelling), 1)
    for item in source["added_tokens"]:
        original[item["id"]] = (item["content"].encode(), 2 if item["special"] else 3)
    end = 0
    pieces = []
    for token, (offset, length, flags) in enumerate(records):
        require(offset == end and length > 0 and offset + length <= len(data[0x202]),
                "Token extent/address mismatch")
        piece = data[0x202][offset:offset + length]
        require((piece, flags) == original[token], f"Source piece/flags mismatch at ID {token}")
        pieces.append(piece)
        end += length
    require(end == len(data[0x202]), "Unreferenced token bytes")
    mapped = list(struct.unpack("<256I", data[0x203]))
    require(len(set(mapped)) == 256, "Serialized byte-map alias")
    for byte, token in enumerate(mapped):
        require(token < vocabulary and records[token][2] & 1 and
                pieces[token] == bytes([byte]), "Incorrect serialized base-byte map")
    merge_rows = list(struct.iter_unpack("<IIII", data[0x204]))
    source_pairs = {}
    vocab = source["model"]["vocab"]
    for rank, pair in enumerate(source["model"]["merges"]):
        left, right = pair.split(" ") if isinstance(pair, str) else pair
        key = vocab[left], vocab[right]
        require(key not in source_pairs, "Duplicate official merge key")
        source_pairs[key] = (vocab[left + right], rank)
    require(len(merge_rows) == len(source_pairs), "Merge count mismatch")
    previous = None
    for left, right, result, rank in merge_rows:
        key = left, right
        require(previous is None or previous < key, "Merge key order/uniqueness")
        require(source_pairs[key] == (result, rank), "Source merge ID/rank mismatch")
        require(all(token < vocabulary and records[token][2] & 1
                    for token in (left, right, result)), "Nonordinary merge token")
        require(pieces[left] + pieces[right] == pieces[result],
                "Decoded merge concatenation mismatch")
        previous = key
    special_rows = list(struct.iter_unpack("<IIII", data[0x20A]))
    require(len(special_rows) == len(source["added_tokens"]), "AddedToken record count")
    for row, item in zip(special_rows, source["added_tokens"]):
        token, flags, reserved0, reserved1 = row
        expected = 1
        for bit, field in enumerate(("lstrip", "rstrip", "single_word", "normalized"), 1):
            expected |= int(item[field]) << bit
        require((token, flags, reserved0, reserved1) == (item["id"], expected, 0, 0),
                "AddedToken policy mismatch")
        require(records[token][2] & 2, "Trie token lacks eligibility flag")
    nodes = list(struct.iter_unpack("<IIII", data[0x205]))
    edges = list(struct.iter_unpack("<II", data[0x206]))
    visited, used_edges, terminals = set(), set(), set()
    pending = [(0, b"")]
    while pending:
        index, path = pending.pop()
        require(index < len(nodes) and index not in visited, "Trie cycle/shared child")
        visited.add(index)
        first, count, terminal, reserved = nodes[index]
        require(reserved == 0 and first + count <= len(edges), "Invalid node extent")
        previous_byte = -1
        for edge_index in range(first, first + count):
            byte, child = edges[edge_index]
            require(previous_byte < byte < 256 and edge_index not in used_edges,
                    "Unsorted/duplicate/shared trie edge")
            used_edges.add(edge_index)
            pending.append((child, path + bytes([byte])))
            previous_byte = byte
        if terminal != 0xFFFFFFFF:
            require(terminal < len(special_rows) and terminal not in terminals,
                    "Invalid/duplicate terminal")
            require(path == pieces[special_rows[terminal][0]], "Trie path/source bytes mismatch")
            terminals.add(terminal)
    require(len(visited) == len(nodes) and len(used_edges) == len(edges) and
            len(terminals) == len(special_rows), "Unreachable trie records")
    return {"tokens": len(records), "decoded_bytes": end, "base_byte_records": len(mapped),
            "ranked_merges": len(merge_rows), "added_tokens": len(special_rows),
            "trie_nodes": len(nodes), "trie_edges": len(edges)}


def convert(directory):
    directory = Path(directory)
    source = validate(directory)
    loaded, pieces, flags, byte_ids, merges = load_source()
    require(source == loaded, "Source changed during conversion")
    fragments = encode_fragments(pieces, flags, byte_ids, merges, source["added_tokens"])
    comparisons = audit_fragments(fragments, source)
    # These are converter checks, not RTL mutation kills.
    sensitivity = []
    for kind, offset, label in ((0x201, 32, "token-offset"),
                                (0x203, 32, "base-byte-id"),
                                (0x204, 44, "merge-rank"),
                                (0x20A, 36, "added-token-policy"),
                                (0x205, 44, "trie-reserved")):
        changed = dict(fragments)
        blob = bytearray(changed[kind])
        blob[offset] ^= 1
        changed[kind] = bytes(blob)
        try:
            audit_fragments(changed, source)
        except (ValueError, KeyError, IndexError):
            sensitivity.append(label)
        else:
            raise ValueError(f"Serialized auditor accepted corrupt {label}")
    combined, entries, cursor = bytearray(), [], BASE
    for kind, blob in sorted(fragments.items()):
        filename = f"qwen-{kind:03x}.bin"
        with (directory / filename).open("xb") as output:
            output.write(blob)
        count = struct.unpack_from("<I", blob, 12)[0]
        entries.append({
            "kind": kind, "file": filename, "base": cursor, "bytes": len(blob),
            "data_base": cursor + 32, "record_bytes": WIDTHS[kind], "record_count": count,
            "sha256": hashlib.sha256(blob).hexdigest(),
        })
        combined.extend(blob)
        padding = bytes(-len(blob) % 4)
        combined.extend(padding)
        cursor += len(blob) + len(padding)
    with (directory / "fragments.hex").open("x", encoding="ascii") as output:
        for offset in range(0, len(combined), 4):
            output.write(f"{int.from_bytes(combined[offset:offset+4], 'little'):08x}\n")
    pinned = manifest()
    result = {
        "scope": SCOPE, "bootable": False, "identity": pinned["identity"],
        "revision": pinned["revision"], "bundle_sha256": pinned["bundle_sha256"],
        "vocabulary": VOCABULARY, "maximum_token_bytes": max(map(len, pieces)),
        "fragments": entries, "memory_base": BASE, "memory_bytes": len(combined),
        "memory_hex_sha256": hashlib.sha256((directory / "fragments.hex").read_bytes()).hexdigest(),
        "source_comparisons": comparisons, "converter_corruption_rejections": sensitivity,
        "ordinary_added_token_encoding": "flags=3: ordinary plus trie-eligible; official special=false retained below",
        "added_token_source_policies": source["added_tokens"],
        "missing": ["official library reference execution", "upstream Unicode implementation/version",
                    "NFC and Unicode tables", "ordered-regex/tagged-DFA tables",
                    "complete image boot and official tokenizer-equivalence comparison"],
        "official_reference_comparisons": 0,
    }
    with (directory / "qwen-fragments.json").open("x", encoding="ascii") as output:
        json.dump(result, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps({"scope": SCOPE, "source_comparisons": comparisons,
                      "converter_corruption_rejections": sensitivity}, indent=2))


def audit_layout(directory, info):
    """Check public addresses against each serialized word, including final lanes."""
    directory = Path(directory)
    pinned = manifest()
    require(info["scope"] == SCOPE and info["bootable"] is False and
            info["vocabulary"] == VOCABULARY and
            info["bundle_sha256"] == pinned["bundle_sha256"],
            "Fragment provenance/scope changed")
    raw_hex = (directory / "fragments.hex").read_bytes()
    require(hashlib.sha256(raw_hex).hexdigest() == info["memory_hex_sha256"],
            "Fragment memory file changed")
    words = [int(line, 16) for line in raw_hex.splitlines()]
    reconstructed = b"".join(struct.pack("<I", word) for word in words)
    require(info["memory_base"] == BASE and len(reconstructed) == info["memory_bytes"],
            "Fragment memory extent changed")
    cursor, fragments = BASE, {}
    for entry in info["fragments"]:
        kind = entry["kind"]
        require(kind not in fragments and kind in WIDTHS and
                entry["file"] == f"qwen-{kind:03x}.bin", "Invalid fragment identity")
        blob = (directory / entry["file"]).read_bytes()
        require(hashlib.sha256(blob).hexdigest() == entry["sha256"] and
                len(blob) == entry["bytes"], "Serialized fragment hash/length mismatch")
        _, _, width, count, size, _ = struct.unpack_from("<IIIIQQ", blob)
        require(entry["base"] == cursor and cursor % 4 == 0 and
                entry["data_base"] == cursor + 32 and
                entry["record_bytes"] == width == WIDTHS[kind] and
                entry["record_count"] == count and size == count * width,
                "Serialized record address/count mismatch")
        start = cursor - BASE
        padded_end = start + ((len(blob) + 3) & ~3)
        require(reconstructed[start:start + len(blob)] == blob and
                reconstructed[start + len(blob):padded_end] ==
                bytes(-len(blob) % 4), "Memory word/lane/address mismatch")
        cursor = BASE + padded_end
        fragments[kind] = blob
    require(cursor == BASE + len(reconstructed) and set(fragments) == set(WIDTHS),
            "Missing/overlapping/trailing fragment memory")
    return fragments


def memory_function(evidence, manifest_data, allowed):
    hex_path = evidence.relative(evidence.path / "fragments.hex")
    conditions = " || ".join(
        f"(address>=64'h{entry['data_base']:x} && "
        f"address<64'h{(entry['base'] + entry['bytes'] + 3) & ~3:x})"
        for entry in manifest_data["fragments"] if entry["kind"] in allowed
    )
    return f"""
  reg [31:0] fragment_memory[0:{manifest_data['memory_bytes']//4-1}];
  initial $readmemh("{hex_path}",fragment_memory);
  function automatic [31:0] memory(input [63:0] address);
    begin
      if (address[1:0]!=0 || !({conditions}))
        $fatal(1,"QWEN_FRAGMENT_READ_BOUNDS address=%h",address);
      memory=fragment_memory[(address-64'h{BASE:x})>>2];
    end
  endfunction
"""


def replace_memory(bench, replacement):
    first = bench.index("  function automatic [31:0] memory(")
    last = bench.index("  endfunction", first) + len("  endfunction")
    return bench[:first] + replacement + bench[last:]


def detokenizer_probe(evidence, info, pieces, byte_ids, seed):
    from protocol import DETOKENIZER
    entries = {item["kind"]: item for item in info["fragments"]}
    # Explicit vectors, not official tokenization: split Unicode scalars at bytes.
    raw = "caf\u00e9 \u4e2d\u6587 \U0001f600 e\u0301\n".encode()
    tokens = [byte_ids[byte] for byte in raw]
    tokens += list(range(151643, VOCABULARY))
    # Also exercise high ordinary IDs and the longest valid UTF-8 ordinary piece.
    valid = []
    for token in range(151643):
        try:
            pieces[token].decode("utf-8")
        except UnicodeDecodeError:
            continue
        valid.append(token)
    longest = max(valid, key=lambda token: len(pieces[token]))
    tokens += [valid[-1], longest]
    expected = b"".join(pieces[token] for token in tokens)
    expected.decode("utf-8")
    blob = (evidence.path / entries[0x201]["file"]).read_bytes()
    addresses = []
    for token in tokens:
        offset, length, _ = struct.unpack_from("<QII", blob, 32 + token * 16)
        addresses.extend(entries[0x201]["data_base"] + token * 16 + word * 4
                         for word in range(4))
        addresses.extend((entries[0x202]["data_base"] + offset + byte) & ~3
                         for byte in range(length))
    bench = replace_memory(DETOKENIZER, memory_function(evidence, info, {0x201, 0x202}))
    bench = bench.replace("cfg_vocab_size=257", f"cfg_vocab_size={VOCABULARY}")
    bench = bench.replace("cfg_token_records_base=64'h1000,cfg_token_bytes_base=64'h4000",
                          f"cfg_token_records_base=64'h{entries[0x201]['base']:x},"
                          f"cfg_token_bytes_base=64'h{entries[0x202]['base']:x}")
    bench = bench.replace("addresses[0:255]", f"addresses[0:{len(addresses)-1}]")
    bench = bench.replace("expected[0:255]", f"expected[0:{len(expected)-1}]")
    replacements = {
        "SEED": str(seed), "MAX_TOKEN_LENGTH": str(info["maximum_token_bytes"]),
        "BYTE_COUNT": str(entries[0x202]["record_count"]), "BUS_ERROR": "0",
        "ERROR_CODE": "8'h00", "REQUESTS": str(len(addresses)), "OUTPUTS": str(len(expected)),
        "VECTORS": "\n".join(
            [f"addresses[{i}]=64'h{address:x};" for i, address in enumerate(addresses)] +
            [f"expected[{i}]=8'h{value:x};" for i, value in enumerate(expected)]),
        "STIMULUS": "\n".join(f"token({token},{int(i==len(tokens)-1)});"
                              for i, token in enumerate(tokens)),
    }
    for key, value in replacements.items():
        bench = bench.replace(f"@{key}@", value)
    bench = bench.replace('    $display("DETOK_REQUESTS', """
    if (request_stalls==0 || output_stalls==0)
      $fatal(1,"QWEN_DETOK_MISSING_STALL_COVERAGE");
    $display("DETOK_REQUESTS""")
    evidence.simulate(f"qwen-fragment-detok-s{seed}", bench,
                      ["rtl/anvil_edge_detokenizer.sv"],
                      len(addresses) + len(expected) + 1, simulator="verilator")
    return {"tokens": tokens, "expected_utf8_hex": expected.hex(),
            "expected_read_addresses": addresses, "seed": seed}


def bpe_probe(evidence, info, byte_ids, merges, seed):
    from protocol import bpe_reference
    from text import BENCH
    entry, = [item for item in info["fragments"] if item["kind"] == 0x204]
    raw = "hello caf\u00e9 \u4e2d\u6587 \U0001f600 12345".encode()
    tokens = [byte_ids[byte] for byte in raw]
    merge_map = {(left, right): (result, rank) for left, right, result, rank in merges}
    expected = bpe_reference(tokens, merge_map)
    require(len(expected) < len(tokens) and len(expected) > 1, "No substantive BPE merges")
    dut = f"""
  wire [31:0] token_id;
  assign out_value={{32'd0,token_id}};
  anvil_edge_ranked_bpe #(.MAX_PRETOKEN_BYTES(128)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_vocab_size(32'd{VOCABULARY}),.cfg_merge_base(64'h{entry['base']:x}),
    .cfg_merge_count(32'd{entry['record_count']}),
    .in_valid(in_valid),.in_ready(in_ready),.in_token_id(in_value),.in_last(in_last),
    .out_valid(out_valid),.out_ready(out_ready),.out_token_id(token_id),.out_last(out_last),
    .busy(busy),.done(done),.error(error),.error_code(error_code),
    .tbl_req_valid(tbl_req_valid),.tbl_req_ready(tbl_req_ready),.tbl_req_addr(tbl_req_addr),
    .tbl_rsp_valid(tbl_rsp_valid),.tbl_rsp_ready(tbl_rsp_ready),
    .tbl_rsp_data(tbl_rsp_data),.tbl_rsp_error(tbl_rsp_error));
"""
    bench = replace_memory(BENCH, memory_function(evidence, info, {0x204}))
    replacements = {
        "DUT": dut, "SEED": str(seed), "BUS_ERROR": "0", "ERROR_CODE": "8'h00",
        "OUTPUTS": str(len(expected)), "INPUTS": str(len(tokens)),
        "ARRAY_LAST": str(len(expected)-1), "CYCLES": "2000000",
        "VECTORS": "\n".join(f"expected[{i}]=64'd{token};"
                             for i, token in enumerate(expected)),
        "STIMULUS": "\n".join(f"item(32'd{token},{int(i==len(tokens)-1)});"
                              for i, token in enumerate(tokens)),
    }
    for key, value in replacements.items():
        bench = bench.replace(f"@{key}@", value)
    evidence.simulate(f"qwen-fragment-bpe-s{seed}", bench,
                      ["rtl/anvil_edge_ranked_bpe.sv"], None, simulator="verilator")
    return {"scope": "One explicitly isolated BPE span, no regex/normalization/special processing",
            "input_utf8_hex": raw.hex(), "base_tokens": tokens, "expected_tokens": expected,
            "seed": seed}


def trie_probe(evidence, info, source, seed):
    from text import BENCH
    entries = {item["kind"]: item for item in info["fragments"]}
    bases = [0] * 20
    lengths = [0] * 20
    counts = [0] * 16
    for kind, entry in entries.items():
        # Version-1 descriptor order: four core segments followed by tables.
        index = 4 + (kind - 0x200)
        bases[index], lengths[index] = entry["base"], entry["bytes"]
        counts[kind - 0x200] = entry["record_count"]
    metadata = [0] * 32
    metadata[2], metadata[13], metadata[14] = VOCABULARY, 0, info["maximum_token_bytes"]
    pack = lambda values, width: sum(value << (width * index)
                                     for index, value in enumerate(values))
    expected_reads = set()
    for kind in (0x205, 0x206, 0x20A):
        entry = entries[kind]
        expected_reads.update(range(entry["data_base"], entry["base"] + entry["bytes"], 4))
    records = (evidence.path / entries[0x201]["file"]).read_bytes()
    for item in source["added_tokens"]:
        token = item["id"]
        expected_reads.update(entries[0x201]["data_base"] + token * 16 + word * 4
                              for word in range(4))
        offset, length, _ = struct.unpack_from("<QII", records, 32 + token * 16)
        expected_reads.update((entries[0x202]["data_base"] + offset + byte) & ~3
                              for byte in range(length))
    expected_reads = sorted(expected_reads)
    dut = f"""
  wire valid_special_trie;
  assign in_ready=0;
  assign out_valid=0;
  assign out_value=0;
  assign out_last=0;
  anvil_edge_special_trie_validator #(
    .MAX_TRIE_NODES({entries[0x205]['record_count']}),
    .MAX_SPECIAL_RECORDS({len(source['added_tokens'])}),
    .MAX_TOKEN_BYTES({info['maximum_token_bytes']})) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.manifest_valid(1'b1),.tokens_valid(1'b1),
    .staged_segment_bases(1280'h{pack(bases,64):x}),
    .staged_segment_bytes(1280'h{pack(lengths,64):x}),
    .staged_metadata(1024'h{pack(metadata,32):x}),
    .staged_table_counts(512'h{pack(counts,32):x}),
    .busy(busy),.done(done),.valid_special_trie(valid_special_trie),
    .error(error),.error_code(error_code),.ddr_req_valid(tbl_req_valid),
    .ddr_req_ready(tbl_req_ready),.ddr_req_addr(tbl_req_addr),
    .ddr_rsp_valid(tbl_rsp_valid),.ddr_rsp_ready(tbl_rsp_ready),
    .ddr_rsp_rdata(tbl_rsp_data),.ddr_rsp_error(tbl_rsp_error));
  reg [63:0] required_address[0:{len(expected_reads)-1}];
  reg visited[0:{len(expected_reads)-1}];
  integer lookup_index,matched_index,visited_index;
  always @(posedge clk) if (rst_n) begin
    if (tbl_req_valid && tbl_req_ready) begin
      matched_index=-1;
      for (lookup_index=0; lookup_index<{len(expected_reads)}; lookup_index=lookup_index+1)
        if (tbl_req_addr===required_address[lookup_index]) matched_index=lookup_index;
      if (matched_index<0) $fatal(1,"QWEN_TRIE_UNACCOUNTED_READ address=%h",tbl_req_addr);
      visited[matched_index]=1;
    end
    if (done) begin
      if (valid_special_trie!==1) $fatal(1,"QWEN_TRIE_NOT_VALID");
      for (visited_index=0; visited_index<{len(expected_reads)}; visited_index=visited_index+1)
        if (visited[visited_index]!==1)
          $fatal(1,"QWEN_TRIE_MISSING_READ address=%h",required_address[visited_index]);
    end
  end
"""
    bench = replace_memory(BENCH, memory_function(
        evidence, info, {0x201, 0x202, 0x205, 0x206, 0x20A}))
    bench = bench.replace("tbl_req_valid,tbl_req_addr,tbl_rsp_ready} !== '0)",
                          "tbl_req_valid,tbl_req_addr,tbl_rsp_ready,valid_special_trie} !== '0)")
    replacements = {
        "DUT": dut, "SEED": str(seed), "BUS_ERROR": "0", "ERROR_CODE": "8'h00",
        "OUTPUTS": "0", "INPUTS": "0", "ARRAY_LAST": "0", "CYCLES": "2000000",
        "VECTORS": "\n".join(
            f"required_address[{index}]=64'h{address:x}; visited[{index}]=0;"
            for index, address in enumerate(expected_reads)),
        "STIMULUS": "",
    }
    for key, value in replacements.items():
        bench = bench.replace(f"@{key}@", value)
    evidence.simulate(f"qwen-fragment-trie-s{seed}", bench, [
        "rtl/anvil_edge_special_trie_validator.sv", "rtl/anvil_edge_boot_segment_reader.sv",
    ], None, simulator="verilator")
    return {"scope": "Isolated real AddedToken trie validator; manifest/tokens admission supplied, not boot tested",
            "required_read_addresses": expected_reads, "seed": seed}


def run_qwen_fragments(evidence):
    evidence.tools(("python3", "verilator", "g++", "make"))
    evidence.child(
        ["python3", "tests/qwen_tables.py", evidence.relative(evidence.path)],
        "qwen-independent-fragment-conversion",
    )
    info = json.loads((evidence.path / "qwen-fragments.json").read_bytes())
    source, pieces, _, byte_ids, merges = load_source()
    fragments = audit_layout(evidence.path, info)
    audit_fragments(fragments, source)
    results = {"scope": SCOPE, "detokenizer": [], "ranked_bpe": [], "special_trie": []}
    for seed in (1, 17, 89):
        results["detokenizer"].append(detokenizer_probe(evidence, info, pieces, byte_ids, seed))
        results["ranked_bpe"].append(bpe_probe(evidence, info, byte_ids, merges, seed))
        results["special_trie"].append(trie_probe(evidence, info, source, seed))
    with (evidence.path / "qwen-fragment-rtl.json").open("x", encoding="ascii") as output:
        json.dump(results, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 tests/qwen_tables.py PROJECT_RELATIVE_EVIDENCE_DIRECTORY")
    destination = Path(sys.argv[1])
    if (destination.is_absolute() or ".." in destination.parts or not destination.is_dir()
            or destination.parts[:2] not in (
                ("evidence", "preparation"), ("evidence", "verification"))):
        raise SystemExit("Destination must be an existing fresh project evidence directory")
    convert(destination)
