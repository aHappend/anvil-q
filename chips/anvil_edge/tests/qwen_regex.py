"""Exact Qwen ordered Split compilation over a symbolic Unicode alphabet.

The alphabet is a required input, not a Unicode database. Directed RTL fixtures
classify only their explicitly listed scalars. No complete official profile,
normalization conversion, or official-library equivalence is claimed here.
"""

from collections import deque
import itertools
import json
from pathlib import Path
import random
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from official import ROOT, validate


PATTERN = (r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|"
           r"\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+")
SYMBOLS = ("s", "t", "r", "e", "v", "m", "l", "d", "letter", "number",
           "space", "cr", "lf", "white", "quote", "other")
LETTERS = frozenset(range(9))
NUMBER, SPACE, CR, LF, WHITE, QUOTE, OTHER = range(9, 16)
WHITES = frozenset((SPACE, CR, LF, WHITE))
NEWLINES = frozenset((CR, LF))
PUNCT = frozenset((QUOTE, OTHER))
PREFIX = frozenset((SPACE, WHITE, QUOTE, OTHER))
DEAD = (-1,) * 7
START = (0,) * 7
SCOPE = (
    "Exact ordered Qwen regex over a symbolic classifier, plus selected-scalar "
    "RTL fixtures; not complete Unicode tables, official tokenizer equivalence, "
    "a bootable image, or inference"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def advance(state, symbol):
    """Product of seven anchored rule recognizers; tags retain byte endpoints."""
    next_state, operations = [], []
    for rule, old in enumerate(state):
        new, end_opcode = -1, None
        if symbol == len(SYMBOLS):
            if rule == 5 and old == 1:
                new, end_opcode = 2, 2
        elif old >= 0:
            if rule == 0:
                if old == 0 and symbol == QUOTE:
                    new = 1
                elif old == 1:
                    new = {0: 6, 1: 6, 2: 2, 4: 3, 5: 6, 6: 4, 7: 6}.get(symbol, -1)
                elif (old, symbol) in ((2, 3), (3, 3), (4, 6)):
                    new = 6
                if new == 6:
                    end_opcode = 2
            elif rule == 1:
                if old in (0, 1, 2) and symbol in LETTERS:
                    new, end_opcode = 2, 2
                elif old == 0 and symbol in PREFIX:
                    new = 1
            elif rule == 2:
                if old == 0 and symbol == NUMBER:
                    new, end_opcode = 1, 2
            elif rule == 3:
                if old == 0 and symbol == SPACE:
                    new = 1
                elif old in (0, 1, 2) and symbol in PUNCT:
                    new, end_opcode = 2, 2
                elif old in (2, 3) and symbol in NEWLINES:
                    new, end_opcode = 3, 2
            elif rule == 4:
                if old in (0, 1, 2) and symbol in WHITES:
                    new = 2 if symbol in NEWLINES else 1
                    if new == 2:
                        end_opcode = 2
            elif rule == 5:
                if old in (0, 1) and symbol in WHITES:
                    new = 1
                    if old == 1:
                        end_opcode = 1
            elif rule == 6:
                if old in (0, 1) and symbol in WHITES:
                    new, end_opcode = 1, 2
        next_state.append(new)
        if end_opcode is not None:
            operations.append((end_opcode, rule, 0, 0))
    return tuple(next_state), operations


def accepting(state):
    conditions = (state[0] == 6, state[1] == 2, state[2] == 1,
                  state[3] in (2, 3), state[4] == 2,
                  state[5] in (1, 2), state[6] == 1)
    return [(rule, rule, 0, 0) for rule, enabled in enumerate(conditions) if enabled]


def compile_profile():
    """Serialize deterministic transition/actions, including synthetic EOF."""
    identities = {START: 0, DEAD: 1}
    pending = deque((START, DEAD))
    states, transitions, operations, accepts = [], [], [], []
    while pending:
        state = pending.popleft()
        require(identities[state] == len(states), "Nondeterministic state numbering")
        rows = accepting(state)
        states.append((len(transitions), len(accepts), len(rows), 0))
        accepts.extend(rows)
        for symbol in range(len(SYMBOLS) + 1):
            target, actions = advance(state, symbol)
            if target not in identities:
                identities[target] = len(identities)
                pending.append(target)
            transitions.append((identities[target], len(operations), len(actions), 0))
            operations.extend(actions)
    require(not accepting(DEAD), "Dead state accepts")
    first = states[1][0]
    require(all(row[0] == 1 and row[2] == 0
                for row in transitions[first:first + len(SYMBOLS) + 1]),
            "Dead state is not actionless/self-looping")
    return {"states": states, "transitions": transitions, "ops": operations,
            "accepts": accepts, "start": 0, "dead": 1,
            "classes": len(SYMBOLS), "registers": 32}


def rule_oracle(symbols):
    """Independent ordered-expression evaluation, not table interpretation."""
    spans, anchor = [], 0
    while anchor < len(symbols):
        rest = symbols[anchor:]
        candidates = [None] * 7
        for contraction in ((QUOTE, 0), (QUOTE, 1), (QUOTE, 2, 3),
                            (QUOTE, 4, 3), (QUOTE, 5), (QUOTE, 6, 6), (QUOTE, 7)):
            if tuple(rest[:len(contraction)]) == contraction:
                candidates[0] = len(contraction)
                break
        cursor = int(rest[0] in PREFIX)
        begin = cursor
        while cursor < len(rest) and rest[cursor] in LETTERS:
            cursor += 1
        if cursor > begin:
            candidates[1] = cursor
        if rest[0] == NUMBER:
            candidates[2] = 1
        cursor = int(rest[0] == SPACE)
        begin = cursor
        while cursor < len(rest) and rest[cursor] in PUNCT:
            cursor += 1
        if cursor > begin:
            while cursor < len(rest) and rest[cursor] in NEWLINES:
                cursor += 1
            candidates[3] = cursor
        cursor = 0
        last_newline = None
        while cursor < len(rest) and rest[cursor] in WHITES:
            cursor += 1
            if rest[cursor - 1] in NEWLINES:
                last_newline = cursor
        candidates[4] = last_newline
        if cursor:
            # Greedy whitespace backtracks exactly one scalar for (?!\S).
            if cursor == len(rest):
                candidates[5] = cursor
            elif cursor >= 2:
                candidates[5] = cursor - 1
            candidates[6] = cursor
        length = next((value for value in candidates if value is not None), None)
        require(length is not None and length > 0, "Ordered regex made no progress")
        spans.append((anchor, anchor + length))
        anchor += length
    return spans


def table_oracle(symbols, profile, widths=None):
    """Interpret reparsed ANVLEDG3 tags/priorities with byte-accurate rewinding."""
    widths = [1] * len(symbols) if widths is None else widths
    offsets = [0]
    for width in widths:
        offsets.append(offsets[-1] + width)
    spans, anchor = [], 0
    while anchor < len(symbols):
        state, best = profile["start"], None
        tags = [None] * profile["registers"]
        for cursor in range(anchor, len(symbols) + 1):
            at_end = cursor == len(symbols)
            symbol = profile["classes"] if at_end else symbols[cursor]
            before, after = offsets[cursor], offsets[cursor if at_end else cursor + 1]
            first = profile["states"][state][0]
            state, op_first, count, _ = profile["transitions"][first + symbol]
            for opcode, dest, source, _ in profile["ops"][op_first:op_first + count]:
                tags[dest] = (None if opcode == 0 else before if opcode == 1
                              else after if opcode == 2 else tags[source])
            _, accept_first, count, _ = profile["states"][state]
            for priority, register, policy, reserved in profile["accepts"][accept_first:accept_first + count]:
                require(policy == reserved == 0, "Unexpected acceptance policy")
                end = tags[register]
                if end is not None and offsets[anchor] < end <= after:
                    candidate = (priority, -end, end)
                    best = candidate if best is None else min(best, candidate)
            if at_end or state == profile["dead"]:
                break
        require(best is not None, "DFA made no progress")
        end = best[2]
        spans.append((offsets[anchor], end))
        anchor = offsets.index(end)
    return spans


def serialize(profile):
    from qwen_tables import table
    return {kind: table(16, b"".join(struct.pack("<4I", *row) for row in profile[name]))
            for kind, name in ((0x208, "states"), (0x209, "transitions"),
                               (0x20B, "ops"), (0x20C, "accepts"))}


def reparse(blobs, expected):
    result = {key: expected[key] for key in ("start", "dead", "classes", "registers")}
    for kind, name in ((0x208, "states"), (0x209, "transitions"),
                       (0x20B, "ops"), (0x20C, "accepts")):
        blob = blobs[kind]
        magic, version, width, count, size, reserved = struct.unpack_from("<4I2Q", blob)
        require((magic, version, width, reserved) == (0x334C4254, 1, 16, 0)
                and size == 16 * count and len(blob) == 32 + size,
                "Malformed serialized regex header/extent")
        result[name] = list(struct.iter_unpack("<4I", blob[32:]))
    require(result == expected, "Serialized regex fields differ")
    return result


def audit(directory):
    source = validate(directory)
    split, bytelevel = source["pre_tokenizer"]["pretokenizers"]
    require(source["pre_tokenizer"]["type"] == "Sequence" and split == {
        "type": "Split", "pattern": {"Regex": PATTERN}, "behavior": "Isolated", "invert": False,
    }, "Pinned ordered Split semantics changed")
    require(bytelevel == {"type": "ByteLevel", "add_prefix_space": False,
                         "trim_offsets": False, "use_regex": False},
            "Unexpected ByteLevel second-stage splitting")
    profile = compile_profile()
    blobs = serialize(profile)
    reparsed = reparse(blobs, profile)
    count = 0
    for length in range(5):
        for symbols in itertools.product(range(len(SYMBOLS)), repeat=length):
            require(table_oracle(symbols, reparsed) == rule_oracle(symbols),
                    f"Regex exhaustive mismatch {symbols}")
            count += 1
    random_counts = {}
    for seed in (1, 17, 89):
        rng = random.Random(seed)
        for _ in range(1000):
            symbols = [rng.randrange(len(SYMBOLS)) for _ in range(rng.randrange(1, 129))]
            widths = [rng.randrange(1, 5) for _ in symbols]
            ends = [0]
            for width in widths:
                ends.append(ends[-1] + width)
            expected = [(ends[start], ends[end]) for start, end in rule_oracle(symbols)]
            require(table_oracle(symbols, reparsed, widths) == expected,
                    f"Regex randomized byte-end mismatch seed={seed}")
        random_counts[str(seed)] = 1000
    # Converter sensitivity, not one of the required compiled RTL mutation kills.
    mutant = dict(profile)
    mutant["ops"] = [(2 if op == 1 else op, dest, src, zero)
                     for op, dest, src, zero in profile["ops"]]
    witness = (SPACE, SPACE, OTHER)
    require(rule_oracle(witness) == [(0, 1), (1, 3)] and
            table_oracle(witness, mutant) != rule_oracle(witness),
            "Trailing-lookahead converter mutation survived")
    for kind, blob in blobs.items():
        with (Path(directory) / f"qwen-regex-{kind:03x}.bin").open("xb") as output:
            output.write(blob)
    result = {
        "scope": SCOPE, "pattern": PATTERN, "symbols": SYMBOLS,
        "exhaustive_max_length": 4, "exhaustive_sequences": count,
        "random_sequences_by_seed": random_counts,
        "counts": {name: len(profile[name]) for name in ("states", "transitions", "ops", "accepts")},
        "converter_sensitivity": "set-before to set-after fails the unchanged two-space lookahead witness",
        "missing": ["Pinned official reference implementation/build and Unicode semantics",
                    "Complete scalar-to-symbol classification, including Unicode case folding",
                    "NFC conversion", "Official-library token vectors", "Complete official image boot"],
        "official_reference_comparisons": 0, "bootable": False,
    }
    with (Path(directory) / "qwen-regex-audit.json").open("x", encoding="ascii") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(json.dumps(result, indent=2))


FIXTURE_CLASSES = {
    **{ord(char): SYMBOLS.index(char.lower()) for char in "sStTrReEvVmMlLdD"},
    **{ord(char): SYMBOLS.index("letter") for char in "aAbBcCfFgGhHiIjJkKnNoOpPqQuUwWxXyYzZ"
       "\u00e9\u4e2d\u6587"},
    **{ord(char): NUMBER for char in "0123456789"},
    ord(" "): SPACE, ord("\r"): CR, ord("\n"): LF, ord("\t"): WHITE,
    ord("\u00a0"): WHITE, ord("'"): QUOTE,
    **{ord(char): OTHER for char in "!?.,+-_\u0301\U0001f600"},
}
FIXTURE_TEXT = (
    "I'm WE'RE she'd can't we'll you've 's 'T 'RE 'VE 'M 'LL 'D 'x\n"
    "a!!\r\n  b  ! \t x \t\n \r \n  12345 caf\u00e9 \u4e2d\u6587 "
    "\U0001f600 e\u0301 a_b\r\n\t\u00a0"
)


def rtl_test(evidence, seed):
    from text import record, ranges_for, run_text_case, word_memory
    profile = compile_profile()
    ranges = ranges_for({}, FIXTURE_CLASSES)
    memory = word_memory(0x1000, ranges)
    for base, name in ((0x10000, "states"), (0x20000, "transitions"),
                       (0x30000, "ops"), (0x40000, "accepts")):
        memory.update(word_memory(base, [record(*row) for row in profile[name]]))
    text = FIXTURE_TEXT
    symbols = [FIXTURE_CLASSES[ord(char)] for char in text]
    ends = [0]
    for char in text:
        ends.append(ends[-1] + len(char.encode()))
    spans = [(ends[start], ends[end]) for start, end in rule_oracle(symbols)]
    require(len(spans) > 40 and spans == table_oracle(
        symbols, profile, [len(char.encode()) for char in text]),
        "Missing substantive ordered-regex fixture coverage")
    dut = f"""
  wire [31:0] span_start,span_end;
  assign out_value={{span_start,span_end}};
  anvil_edge_tagged_dfa #(.MAX_SPAN_BYTES(512)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_ranges_base(64'h1000),.cfg_states_base(64'h10000),
    .cfg_transitions_base(64'h20000),.cfg_tag_ops_base(64'h30000),
    .cfg_accepts_base(64'h40000),.cfg_range_count(32'd{len(ranges)}),
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
    run_text_case(evidence, "qwen-symbolic-regex", seed, dut, memory,
                  list(map(ord, text)), [(start << 32) | end for start, end in spans],
                  provenance={"scope": SCOPE, "selected_scalar_classes": FIXTURE_CLASSES,
                              "input_utf8_hex": text.encode().hex(), "expected_byte_spans": spans})


def run_qwen_regex(evidence):
    evidence.tools(("python3", "verilator", "g++", "make"))
    evidence.child(["python3", "tests/qwen_regex.py", evidence.relative(evidence.path)],
                   "qwen-ordered-symbolic-regex-audit")
    for seed in (1, 17, 89):
        rtl_test(evidence, seed)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 tests/qwen_regex.py PROJECT_RELATIVE_EVIDENCE_DIRECTORY")
    destination = Path(sys.argv[1])
    if (destination.is_absolute() or ".." in destination.parts
            or destination.parts[:2] not in (
                ("evidence", "preparation"), ("evidence", "verification"))
            or not destination.is_dir()):
        raise SystemExit("Output must be an existing project-relative fresh evidence directory")
    audit(destination)
