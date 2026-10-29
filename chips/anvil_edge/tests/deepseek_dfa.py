"""Tagged-DFA compilation of the three pinned DeepSeek Isolated Split stages.

The independent expected spans come from deepseek_preprocessing, not this DFA.
Only pretokenization is tested here; this is not a complete tokenizer image.
"""

from collections import deque
import copy
import hashlib
import itertools
import json
import random
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deepseek_preprocessing import Preprocessor, require
from official import ROOT
from qwen_regex import reparse, serialize, table_oracle
from unicode_tables import LIMIT, scalar
from deepseek_preprocessing import ASCII_PUNCTUATION


START = ("start",)
DEAD = ("dead",)


def properties(preprocessor, value):
    char = chr(value)
    category = preprocessor.categories[value]
    cjk = 0x4E00 <= value <= 0x9FA5 or 0x3040 <= value <= 0x30FF
    ascii_letter = "a" <= char <= "z" or "A" <= char <= "Z"
    # Distinguish the ASCII punctuation prefix from all other P/S scalars.
    return (category, bool(preprocessor.whitespace[value]), cjk,
            ascii_letter, char in ASCII_PUNCTUATION,
            char == " ", char in "\r\n")


def classify(preprocessor):
    symbols, identifiers, classes, ranges = [], {}, [], []
    for value in range(LIMIT):
        if not scalar(value):
            classes.append(None)
            continue
        key = properties(preprocessor, value)
        if key not in identifiers:
            identifiers[key] = len(symbols)
            symbols.append(key)
        identity = identifiers[key]
        classes.append(identity)
        props = (preprocessor.ccc[value] | preprocessor.whitespace[value] << 8 |
                 preprocessor.word[value] << 9)
        if (ranges and ranges[-1][1] == value - 1 and
                ranges[-1][2:] == (identity, props)):
            ranges[-1] = (ranges[-1][0], value, identity, props)
        else:
            ranges.append((value, value, identity, props))
    require(len(classes) == LIMIT, "Incomplete classifier")
    return symbols, classes, ranges


def advance(state, symbol):
    if state == DEAD or state[0] == "terminal":
        return DEAD, []
    if state == START:
        if symbol is None:
            return DEAD, []
        if symbol[0] == 2:
            return ("number", 1), [(2, 0, 0, 0)]
        state = ("text", symbol[2], (0,) * 6, 0)
    if state[0] == "number":
        if symbol is not None and symbol[0] == 2 and state[1] < 3:
            return ("number", state[1] + 1), [(2, 0, 0, 0)]
        return DEAD, []
    _, domain, old_rules, old_gap = state
    actions = []
    # Earlier Split stages establish hard EOFs for the final Split. At a cut
    # the current scalar belongs to the next span, so final tags use set-before.
    boundary = symbol is None or symbol[0] == 2 or symbol[2] != domain
    if boundary:
        accept = []
        if old_rules[4] == 1:
            actions.append((1, 5, 0, 0))
            accept.append(5)
        if old_gap in (1, 2):
            actions.append((1, 7, 0, 0))
            accept.append(7)
        return (("terminal", tuple(accept)) if accept else DEAD), actions
    category, white, _, ascii_letter, ascii_punct, space, newline = symbol
    letters = category in (1, 3)
    punctuation = category in (4, 5)
    prefix = not newline and category not in (1, 4, 5)
    rules = [-1] * 6
    # ASCII punctuation followed by one or more ASCII letters.
    if old_rules[0] == 0 and ascii_punct:
        rules[0] = 1
    elif old_rules[0] in (1, 2) and ascii_letter:
        rules[0] = 2
        actions.append((2, 1, 0, 0))
    # Optional prefix followed by an L/M run.
    if old_rules[1] in (0, 1, 2) and letters:
        rules[1] = 2
        actions.append((2, 2, 0, 0))
    elif old_rules[1] == 0 and prefix:
        rules[1] = 1
    # Optional ASCII space, punctuation/symbol run, optional newline suffix.
    if old_rules[2] == 0 and space:
        rules[2] = 1
    elif old_rules[2] in (0, 1, 2) and punctuation:
        rules[2] = 2
        actions.append((2, 3, 0, 0))
    elif old_rules[2] in (2, 3) and newline:
        rules[2] = 3
        actions.append((2, 3, 0, 0))
    # Whitespace up through the last newline.
    if old_rules[3] in (0, 1, 2) and white:
        rules[3] = 2 if newline else 1
        if newline:
            actions.append((2, 4, 0, 0))
    # Greedy whitespace with negative lookahead backtracks one scalar.
    if old_rules[4] in (0, 1) and white:
        rules[4] = 1
        if old_rules[4] == 1:
            actions.append((1, 5, 0, 0))
    if old_rules[5] in (0, 1) and white:
        rules[5] = 1
        actions.append((2, 6, 0, 0))
    # Isolated Split preserves unmatched gaps. Delay their acceptance by one
    # scalar so the last control can become the prefix of a following L/M run.
    gap = -1
    unmatched = category not in (1, 2, 3, 4, 5) and not white
    if old_gap in (0, 1, 2) and unmatched:
        gap = 1 if old_gap == 0 else 2
        if old_gap in (1, 2):
            actions.append((1, 7, 0, 0))
    elif old_gap in (1, 2):
        if not letters:
            actions.append((1, 7, 0, 0))
            gap = 3
        elif old_gap == 2:
            gap = 3
    if all(value == -1 for value in rules) and gap == -1:
        return DEAD, actions
    return ("text", domain, tuple(rules), gap), actions


def accepting(state):
    if state == START or state == DEAD:
        return []
    if state[0] == "number":
        registers = [0]
    elif state[0] == "terminal":
        registers = state[1]
    else:
        rules, gap = state[2:]
        conditions = (rules[0] == 2, rules[1] == 2, rules[2] in (2, 3),
                      rules[3] == 2, rules[4] == 1, rules[5] == 1)
        registers = [index + 1 for index, valid in enumerate(conditions) if valid]
        if gap in (2, 3):
            registers.append(7)
    return [(register, register, 0, 0) for register in registers]


def compile_profile(symbols):
    identities = {START: 0, DEAD: 1}
    pending = deque((START, DEAD))
    states, transitions, operations, accepts = [], [], [], []
    while pending:
        state = pending.popleft()
        require(identities[state] == len(states), "Nondeterministic DeepSeek state numbering")
        rows = accepting(state)
        states.append((len(transitions), len(accepts), len(rows), 0))
        accepts.extend(rows)
        for symbol in [*symbols, None]:
            target, actions = advance(state, symbol)
            if target not in identities:
                identities[target] = len(identities)
                pending.append(target)
            transitions.append((identities[target], len(operations), len(actions), 0))
            operations.extend(actions)
    return {"states": states, "transitions": transitions, "ops": operations,
            "accepts": accepts, "start": 0, "dead": 1,
            "classes": len(symbols), "registers": 32}


def spans(preprocessor, text):
    result, offset = [], 0
    for part in preprocessor.split(text):
        last = offset + len(part.encode())
        result.append((offset, last))
        offset = last
    return result


def audit(directory):
    preprocessor = Preprocessor()
    symbols, classes, ranges = classify(preprocessor)
    profile = compile_profile(symbols)
    blobs = serialize(profile)
    profile = reparse(blobs, profile)
    representatives = [classes.index(index) for index in range(len(symbols))]
    count, transcript = 0, hashlib.sha256()

    def check(text):
        nonlocal count
        expected = spans(preprocessor, text)
        observed = table_oracle([classes[ord(char)] for char in text], profile,
                                [len(char.encode()) for char in text])
        require(observed == expected,
                f"DeepSeek compiled Split mismatch text={text!r}: {observed} != {expected}")
        transcript.update(json.dumps([text, observed], ensure_ascii=True).encode())
        count += 1

    for length in range(4):
        for values in itertools.product(representatives, repeat=length):
            check("".join(map(chr, values)))
    directed = [
        "\x00\x01Hello", "\x00\x01!", "\x00\x01 ", "\x00\x01",
        "\x00a\x01b", "   \u4e00", "   12", " \t\u3040",
        "\u3040\u3041\u3099\u309b\u309f\u30a0\u30a1\u30fb\u30ff",
        "a\u4e00b\u3042c", "  \r \n  \u4e00", "a1234567b",
        "a\u00b2\u2163\u0664\u096b0b", "!\u4e00!Hello",
    ]
    for text in directed:
        check(text)
    random_texts = []
    for seed in (1, 17, 89):
        rng = random.Random(seed)
        for _ in range(1000):
            text = "".join(chr(rng.choice(representatives))
                           for _ in range(rng.randrange(1, 129)))
            random_texts.append(text)
            check(text)
    for kind, blob in blobs.items():
        with (directory / f"deepseek-dfa-{kind:03x}.bin").open("xb") as output:
            output.write(blob)
    record = {
        "classes": len(symbols),
        "counts": {name: len(profile[name])
                   for name in ("states", "transitions", "ops", "accepts")},
        "unicode_source_sha256": preprocessor.unicode_hashes,
        "range_records": len(ranges), "symbol_representatives": representatives,
        "exhaustive_max_length": 3,
        "exhaustive_sequences": sum(len(symbols) ** length for length in range(4)),
        "directed_sequences": len(directed), "random_sequences": 3000,
        "total_span_vectors": count, "span_transcript_sha256": transcript.hexdigest(),
        "scope": "Compiled pretokenization only, no complete profile/tokenizer/boot/inference",
        "acceptance_evidence": False,
    }
    with (directory / "deepseek-dfa-audit.json").open("x", encoding="ascii") as output:
        json.dump(record, output, indent=2)
        output.write("\n")
    print(f"DEEPSEEK_COMPILED_SPAN_VECTORS {count}")


def run_deepseek_dfa(evidence):
    evidence.tools(("python3", "verilator", "g++", "make"))
    evidence.child(["python3", "tests/deepseek_dfa.py", evidence.relative(evidence.path)],
                   "deepseek-compiled-preprocessing-audit")
    preprocessor = Preprocessor()
    symbols, classes, ranges = classify(preprocessor)
    profile = compile_profile(symbols)
    for kind, blob in serialize(profile).items():
        require((evidence.path / f"deepseek-dfa-{kind:03x}.bin").read_bytes() == blob,
                "DeepSeek DFA serialized bytes differ before RTL")
    compact = copy.copy(evidence)
    compact.simulator_override = "iverilog"
    rtl_case(compact, preprocessor, profile, ranges, "\x00\x01Hello", 17,
             "deepseek-dfa-compact", 64, 500000)
    text = (
        "\x00\x01Hello \x00\x01! \x00\x01 \x00a\x01b "
        "   \u4e00   12 \t\u3040 "
        "\u3040\u3041\u3099\u309b\u309f\u30a0\u30a1\u30fb\u30ff "
        "a\u4e00b\u3042c  \r \n  \u4e00 a1234567b "
        "a\u00b2\u2163\u0664\u096b0b !\u4e00!Hello "
        "caf\u00e9 e\u0301 \U0001f600 \u1c89 \r\n"
    )
    representatives = [classes.index(index) for index in range(len(symbols))]
    selected = sorted(set(representatives) | {
        value for index, row in enumerate(ranges) if index % 37 == 0
        for value in row[:2]
    } | {0x10FFFF, 0x9FA5, 0x9FA6, 0x303F, 0x3040, 0x30FF, 0x3100})
    text += " ".join(map(chr, selected)) + "\r\n\t\u00a0  "
    require(len(text.encode()) < 4096 and len(spans(preprocessor, text)) > 100,
            "Missing DeepSeek RTL span coverage")
    evidence.run_cases([
        (f"deepseek-dfa-s{seed}",
         lambda scope, seed=seed: rtl_case(
             scope, preprocessor, profile, ranges, text, seed,
             "deepseek-dfa-full-classifier", 4096, 5000000))
        for seed in (1, 17, 89)
    ])


def rtl_case(evidence, preprocessor, profile, ranges, text, seed, name, capacity, cycles):
    from text import record, run_text_case, word_memory

    memory = word_memory(0x1000, [record(*row) for row in ranges])
    for base, key in ((0x40000, "states"), (0x50000, "transitions"),
                      (0x60000, "ops"), (0x70000, "accepts")):
        memory.update(word_memory(base, [record(*row) for row in profile[key]]))
    expected = spans(preprocessor, text)
    dut = f"""
  wire [31:0] span_start,span_end;
  assign out_value={{span_start,span_end}};
  anvil_edge_tagged_dfa #(.MAX_SPAN_BYTES({capacity})) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_ranges_base(64'h1000),.cfg_states_base(64'h40000),
    .cfg_transitions_base(64'h50000),.cfg_tag_ops_base(64'h60000),
    .cfg_accepts_base(64'h70000),.cfg_range_count(32'd{len(ranges)}),
    .cfg_class_count(32'd{profile['classes']}),.cfg_state_count(32'd{len(profile['states'])}),
    .cfg_transition_count(32'd{len(profile['transitions'])}),
    .cfg_tag_op_count(32'd{len(profile['ops'])}),
    .cfg_accept_count(32'd{len(profile['accepts'])}),
    .cfg_start_state(32'd{profile['start']}),.cfg_dead_state(32'd{profile['dead']}),
    .cfg_tag_register_count(32'd{profile['registers']}),
    .in_valid(in_valid),.in_ready(in_ready),.in_scalar(in_value),.in_last(in_last),
    .out_valid(out_valid),.out_ready(out_ready),.out_start(span_start),
    .out_end(span_end),.out_last(out_last),.busy(busy),.done(done),
    .error(error),.error_code(error_code),.tbl_req_valid(tbl_req_valid),
    .tbl_req_ready(tbl_req_ready),.tbl_req_addr(tbl_req_addr),
    .tbl_rsp_valid(tbl_rsp_valid),.tbl_rsp_ready(tbl_rsp_ready),
    .tbl_rsp_data(tbl_rsp_data),.tbl_rsp_error(tbl_rsp_error));
"""
    run_text_case(evidence, name, seed, dut, memory, list(map(ord, text)),
                  [(first << 32) | end for first, end in expected], cycles=cycles,
                  provenance={
                      "scope": "Complete Unicode16 classifier with composed DeepSeek "
                               "Split pretokenization only; no complete tokenizer or inference",
                      "unicode_source_sha256": preprocessor.unicode_hashes,
                      "input_utf8_hex": text.encode().hex(), "expected_byte_spans": expected,
                  })


if __name__ == "__main__":
    require(len(sys.argv) == 2, "Usage: python3 tests/deepseek_dfa.py FRESH_EVIDENCE_DIRECTORY")
    destination = Path(sys.argv[1])
    require(not destination.is_absolute() and ".." not in destination.parts and
            destination.parts[:2] in (("evidence", "preparation"), ("evidence", "verification"))
            and destination.is_dir(), "A present project-relative evidence directory is required")
    audit(destination)
