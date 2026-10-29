"""Independent raw-text DeepSeek Split semantics from pinned Unicode source data.

This is a verification oracle, not runtime tokenization or a hardware converter.
"""

import hashlib
import json
import random

from unicode_tables import LIMIT, SCALAR_COUNT, inputs, primary_whitespace, scalar


PATTERNS = (
    r"\p{N}{1,3}",
    "[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff]+",
    r"""[!"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~][A-Za-z]+|[^\r\n\p{L}\p{P}\p{S}]?[\p{L}\p{M}]+| ?[\p{P}\p{S}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+""".replace(r"\r", "\r").replace(r"\n", "\n"),
)
ASCII_PUNCTUATION = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Preprocessor:
    def __init__(self):
        raw, _ = inputs()
        self.categories = bytearray(LIMIT)
        codes = {"L": 1, "N": 2, "M": 3, "P": 4, "S": 5}
        pending, previous = None, -1
        for line in raw["ucd-16.0.0-UnicodeData.txt"].decode().splitlines():
            fields = line.split(";")
            require(len(fields) == 15, "Malformed primary DeepSeek Unicode input")
            value = int(fields[0], 16)
            require(previous < value < LIMIT, "Unordered primary DeepSeek Unicode input")
            previous = value
            category = codes.get(fields[2][0], 0)
            first = value
            if fields[1].endswith(", First>"):
                require(pending is None, "Nested primary Unicode range")
                pending = (value, fields[1].removesuffix(", First>"), category)
                continue
            if fields[1].endswith(", Last>"):
                require(pending is not None and
                        pending[1:] == (fields[1].removesuffix(", Last>"), category),
                        "Unmatched primary Unicode range")
                first, _, _ = pending
                pending = None
            else:
                require(pending is None, "Unclosed primary Unicode range")
            self.categories[first:value + 1] = bytes([category]) * (value - first + 1)
        require(pending is None, "Unclosed final primary Unicode range")
        self.whitespace = primary_whitespace(raw["ucd-16.0.0-PropList.txt"])
        self.unicode_hashes = {
            name: hashlib.sha256(raw[name]).hexdigest()
            for name in ("ucd-16.0.0-UnicodeData.txt", "ucd-16.0.0-PropList.txt")
        }

    def length(self, text, position, stage):
        """Evaluate ordered alternatives directly, without regex/table machinery."""
        end = len(text)
        categories, whites = self.categories, self.whitespace
        first = text[position]
        category = categories[ord(first)]
        if stage == 0:
            if category != 2:
                return 0
            cursor = position + 1
            while cursor < min(position + 3, end) and categories[ord(text[cursor])] == 2:
                cursor += 1
            return cursor - position
        if stage == 1:
            def cjk(char):
                return ("\u4e00" <= char <= "\u9fa5" or
                        "\u3040" <= char <= "\u30ff")
            if not cjk(first):
                return 0
            cursor = position + 1
            while cursor < end and cjk(text[cursor]):
                cursor += 1
            return cursor - position
        require(stage == 2, "Invalid DeepSeek preprocessing stage")
        if first in ASCII_PUNCTUATION:
            cursor = position + 1
            while cursor < end and ("a" <= text[cursor] <= "z" or
                                    "A" <= text[cursor] <= "Z"):
                cursor += 1
            if cursor > position + 1:
                return cursor - position
        optional = first not in "\r\n" and category not in (1, 4, 5)
        # A leading mark can itself satisfy the required run if the optional
        # prefix greedily consumed its only character.
        for begin in ((position + 1, position) if optional else (position,)):
            cursor = begin
            while cursor < end and categories[ord(text[cursor])] in (1, 3):
                cursor += 1
            if cursor > begin:
                return cursor - position
        begin = position + int(first == " ")
        cursor = begin
        while cursor < end and categories[ord(text[cursor])] in (4, 5):
            cursor += 1
        if cursor > begin:
            while cursor < end and text[cursor] in "\r\n":
                cursor += 1
            return cursor - position
        cursor, last_newline = position, None
        while cursor < end and whites[ord(text[cursor])]:
            cursor += 1
            if text[cursor - 1] in "\r\n":
                last_newline = cursor
        if last_newline is not None:
            return last_newline - position
        if cursor > position:
            if cursor == end:
                return cursor - position
            if cursor - position >= 2:
                return cursor - position - 1
            return cursor - position
        return 0

    def stage(self, text, stage):
        """Isolated Split retains unmatched gaps as well as each regex match."""
        spans, gap, position = [], 0, 0
        while position < len(text):
            length = self.length(text, position, stage)
            if not length:
                position += 1
                continue
            if gap < position:
                spans.append((gap, position))
            spans.append((position, position + length))
            position += length
            gap = position
        if gap < len(text):
            spans.append((gap, len(text)))
        return spans

    def split(self, text):
        pieces = [text]
        for stage in range(3):
            pieces = [part[first:last] for part in pieces
                      for first, last in self.stage(part, stage)]
        require("".join(pieces) == text, "Independent preprocessing lost input")
        return pieces


def validate_definition(source):
    expected = [
        {"type": "Split", "pattern": {"Regex": pattern},
         "behavior": "Isolated", "invert": False}
        for pattern in PATTERNS
    ] + [{"type": "ByteLevel", "add_prefix_space": False,
          "trim_offsets": True, "use_regex": False}]
    require(source["normalizer"] == {"type": "Sequence", "normalizers": []} and
            source["pre_tokenizer"] == {"type": "Sequence", "pretokenizers": expected},
            "Pinned DeepSeek preprocessing definition changed")


def compare(preprocessor, source, tokenizer, tokenizers, directory):
    """Official calls are observations only; expected spans come from this oracle."""
    validate_definition(source)
    splitters = [tokenizers.pre_tokenizers.Split(tokenizers.Regex(pattern),
                                                behavior="isolated")
                 for pattern in PATTERNS]
    transcript = hashlib.sha256()
    counts = [0, 0, 0]

    def check(text, stage):
        expected = [(text[first:last], (first, last))
                    for first, last in preprocessor.stage(text, stage)]
        actual = splitters[stage].pre_tokenize_str(text)
        require(actual == expected,
                f"DeepSeek Split mismatch stage={stage} text={text!r}: "
                f"{actual!r} != {expected!r}")
        transcript.update(json.dumps([stage, text, actual], ensure_ascii=True,
                                     separators=(",", ":")).encode())
        counts[stage] += 1

    for value in range(LIMIT):
        if not scalar(value):
            continue
        char = chr(value)
        for stage, text in enumerate(("12" + char + "4567",
                                      "\u4e00" + char + "\u3042",
                                      "a" + char + "b")):
            check(text, stage)
    directed = [
        "", "a", "\u0301", "\u0301\u0300", "\x00\x01", "  x", " \t!",
        " \r \n \r\n x", "!Hello", "!!Hello", "1234567", "a\u4e00\u3042b",
        "\u9fa5\u9fa6 \u303f\u3040\u309f\u30a0\u30ff\u3100",
        "a\u1c89b \U0001f600 e\u0301", "3\u00b2\u2163\u0664\u096b0",
    ]
    for text in directed:
        for stage in range(3):
            check(text, stage)
    random_texts = []
    for seed in (1, 17, 89):
        rng = random.Random(seed)
        alphabet = list("aAzZ019 \t\r\n!?'") + [
            "\u00e9", "\u0301", "\u017f", "\u4e2d", "\U0001f600", "\u1c89",
            "\u00b2", "\u2163", "\u200d", "\u00a0", "\u3042", "\u30a2",
        ]
        for _ in range(1000):
            text = "".join(rng.choice(alphabet) for _ in range(rng.randrange(1, 65)))
            random_texts.append(text)
            for stage in range(3):
                check(text, stage)
    # Compare complete chained preprocessing, including ByteLevel spelling.
    from qwen_tables import inverse_byte_alphabet
    byte_spelling = {byte: char for char, byte in inverse_byte_alphabet().items()}
    chained = 0
    for text in directed + random_texts:
        expected, offset = [], 0
        for part in preprocessor.split(text):
            expected.append(("".join(byte_spelling[byte] for byte in part.encode()),
                             (offset, offset + len(part))))
            offset += len(part)
        require(tokenizer.pre_tokenizer.pre_tokenize_str(text) == expected,
                f"DeepSeek chained ByteLevel preprocessing mismatch: {text!r}")
        chained += 1
    require(counts == [SCALAR_COUNT + len(directed) + 3000] * 3 and
            chained == len(directed) + 3000, "Incomplete DeepSeek preprocessing comparisons")
    record = {
        "unicode_source_sha256": preprocessor.unicode_hashes,
        "candidate_classification_version": "16.0.0",
        "all_scalar_context_comparisons_per_stage": SCALAR_COUNT,
        "directed_comparisons_per_stage": len(directed),
        "random_comparisons_per_stage": 3000,
        "stage_comparisons": counts,
        "chained_bytelevel_comparisons": chained,
        "split_transcript_sha256": transcript.hexdigest(),
        "seeds": [1, 17, 89], "acceptance_evidence": False,
        "scope": "Independent raw-text Split oracle, not exhaustive string proof, "
                 "table conversion, RTL, boot or model inference",
    }
    with (directory / "preprocessing-comparisons.json").open("x", encoding="ascii") as output:
        json.dump(record, output, indent=2)
        output.write("\n")
    print(f"DEEPSEEK_SPLIT_COMPARISONS {sum(counts)}; "
          f"CHAINED_BYTELEVEL_COMPARISONS {chained}")
    return record
