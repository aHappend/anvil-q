#!/usr/bin/env python3
"""Exact supported Qwen tokenizer rules with independent Unicode/BPE parity.

This is input preparation, not a replacement for RTL or model execution.
Unknown tokenizer policies fail instead of being approximated.
"""

import argparse
import ctypes
import ctypes.util
import heapq
import json
from pathlib import Path
import random
import re
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import load_json, require, sha
from benchmark_inputs import write_json

ROOT = Path(__file__).resolve().parents[1]
PATTERN = (r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}|"
           r" ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+")
BYTE_POLICY = {"type": "ByteLevel", "add_prefix_space": False,
               "trim_offsets": False, "use_regex": False}


class UnicodeSplit:
    def __init__(self):
        library = ctypes.util.find_library("pcre2-8")
        require(library is not None, "existing PCRE2 Unicode engine is unavailable")
        self.library = ctypes.CDLL(library)
        self.compile = self.library.pcre2_compile_8
        self.compile.argtypes = (ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32,
                                 ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_size_t),
                                 ctypes.c_void_p)
        self.compile.restype = ctypes.c_void_p
        self.match_data_create = self.library.pcre2_match_data_create_from_pattern_8
        self.match_data_create.argtypes = (ctypes.c_void_p, ctypes.c_void_p)
        self.match_data_create.restype = ctypes.c_void_p
        self.match = self.library.pcre2_match_8
        self.match.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t,
                               ctypes.c_size_t, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p)
        self.match.restype = ctypes.c_int
        self.offsets = self.library.pcre2_get_ovector_pointer_8
        self.offsets.argtypes = (ctypes.c_void_p,)
        self.offsets.restype = ctypes.POINTER(ctypes.c_size_t)
        self.code_free = self.library.pcre2_code_free_8
        self.code_free.argtypes = (ctypes.c_void_p,)
        self.code_free.restype = None
        self.match_data_free = self.library.pcre2_match_data_free_8
        self.match_data_free.argtypes = (ctypes.c_void_p,)
        self.match_data_free.restype = None
        self.config = self.library.pcre2_config_8
        self.config.argtypes = (ctypes.c_uint32, ctypes.c_void_p)
        self.config.restype = ctypes.c_int
        versions = {}
        for key, index in (("pcre2", 11), ("unicode", 10)):
            buffer = ctypes.create_string_buffer(128)
            require(self.config(index, buffer) >= 0, "PCRE2 version query failed")
            versions[key] = buffer.value.decode("ascii")
        self.versions = versions
        error, position = ctypes.c_int(), ctypes.c_size_t()
        pattern = PATTERN.encode("ascii")
        # PCRE2_UCP | PCRE2_UTF; no JIT, locale, or unchecked UTF input.
        self.code = self.compile(pattern, len(pattern), 0x00020000 | 0x00080000,
                                 ctypes.byref(error), ctypes.byref(position), None)
        require(self.code is not None,
                f"pinned Unicode regex compilation failed: {error.value}@{position.value}")
        self.data = self.match_data_create(self.code, None)
        if not self.data:
            self.code_free(self.code)
            self.code = None
            raise ValueError("PCRE2 match-data allocation failed")

    def close(self):
        if self.data:
            self.match_data_free(self.data)
            self.data = None
        if self.code:
            self.code_free(self.code)
            self.code = None

    def split(self, text):
        encoded = text.encode("utf-8")
        cursor, pieces = 0, []
        while cursor < len(encoded):
            count = self.match(self.code, encoded, len(encoded), cursor, 0x80000000,
                               self.data, None)
            require(count > 0, f"Unicode tokenizer did not cover input at byte {cursor}: {count}")
            offsets = self.offsets(self.data)
            start, end = offsets[0], offsets[1]
            require(start == cursor and end > start, "empty or noncontiguous Unicode token")
            pieces.append(encoded[start:end].decode("utf-8"))
            cursor = end
        return pieces


def byte_alphabet():
    ordinary = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
    remaining = [value for value in range(256) if value not in ordinary]
    return {byte: chr(byte) for byte in ordinary} | {
        byte: chr(256 + index) for index, byte in enumerate(remaining)}


def ranked_pairs(symbols, ranks):
    while len(symbols) > 1:
        candidates = [(ranks[pair], index, pair)
                      for index, pair in enumerate(zip(symbols, symbols[1:])) if pair in ranks]
        if not candidates:
            break
        _, _, pair = min(candidates)
        merged, index = [], 0
        while index < len(symbols):
            if index + 1 < len(symbols) and (symbols[index], symbols[index+1]) == pair:
                merged.append(symbols[index] + symbols[index+1])
                index += 2
            else:
                merged.append(symbols[index])
                index += 1
        symbols = merged
    return symbols


def heap_pairs(symbols, ranks):
    size = len(symbols)
    if size < 2:
        return symbols
    values = symbols[:]
    previous = list(range(-1, size-1))
    following = list(range(1, size)) + [-1]
    generation = [0] * size
    active = [True] * size
    queue = []

    def offer(left):
        if left < 0 or not active[left]:
            return
        right = following[left]
        if right < 0:
            return
        rank = ranks.get((values[left], values[right]))
        if rank is not None:
            heapq.heappush(queue, (rank, left, right, generation[left], generation[right]))

    for index in range(size-1):
        offer(index)
    while queue:
        _, left, right, left_generation, right_generation = heapq.heappop(queue)
        if (not active[left] or not active[right] or following[left] != right or
                generation[left] != left_generation or generation[right] != right_generation):
            continue
        values[left] += values[right]
        generation[left] += 1
        active[right] = False
        following[left] = following[right]
        if following[right] >= 0:
            previous[following[right]] = left
        offer(previous[left])
        offer(left)
    return [values[index] for index in range(size) if active[index]]


class PinnedDecoder:
    def __init__(self, specification):
        require(specification["decoder"] == BYTE_POLICY, "unsupported byte decoder")
        self.byte_map = byte_alphabet()
        self.inverse_bytes = {value: key for key, value in self.byte_map.items()}
        self.vocab = specification["model"]["vocab"]
        added = specification["added_tokens"]
        self.added = {row["content"]: row["id"] for row in added}
        require(len(self.added) == len(added), "duplicate added token text")
        self.special = {row["id"] for row in added if row["special"]}
        self.token_ids = {**self.vocab, **self.added}
        self.inverse_tokens = {value: key for key, value in self.token_ids.items()}
        require(len(self.inverse_tokens) == len(self.token_ids), "duplicate token IDs")

    def decode(self, tokens, skip_special=False):
        output = bytearray()
        added_ids = set(self.added.values())
        for token in tokens:
            require(type(token) is int and token in self.inverse_tokens, "unknown token ID")
            if skip_special and token in self.special:
                continue
            text = self.inverse_tokens[token]
            if token in added_ids:
                output.extend(text.encode("utf-8"))
            else:
                require(all(character in self.inverse_bytes for character in text),
                        "token outside byte alphabet")
                output.extend(self.inverse_bytes[character] for character in text)
        return output.decode("utf-8", errors="replace")


class PinnedTokenizer(PinnedDecoder):
    def __init__(self, directory):
        specification = load_json(directory / "tokenizer.json")
        super().__init__(specification)
        require(specification["normalizer"] == {"type": "NFC"}, "unsupported normalizer")
        require(specification["pre_tokenizer"] == {
            "type": "Sequence", "pretokenizers": [
                {"type": "Split", "pattern": {"Regex": PATTERN},
                 "behavior": "Isolated", "invert": False}, BYTE_POLICY]},
            "unsupported Unicode/byte pretokenizer")
        require(specification["decoder"] == BYTE_POLICY and
                specification["post_processor"] == BYTE_POLICY and
                specification["padding"] is None and specification["truncation"] is None,
                "unsupported post-processing/decoder/padding/truncation")
        model = specification["model"]
        require({key: value for key, value in model.items() if key not in ("vocab", "merges")} == {
            "type": "BPE", "dropout": None, "unk_token": None, "continuing_subword_prefix": "",
            "end_of_word_suffix": "", "fuse_unk": False, "byte_fallback": False},
            "unsupported BPE policy")
        pairs = [tuple(row.split() if isinstance(row, str) else row) for row in model["merges"]]
        require(len(pairs) == len(set(pairs)) and all(len(pair) == 2 for pair in pairs),
                "malformed or duplicate BPE merge ranks")
        self.ranks = {pair: index for index, pair in enumerate(pairs)}
        require(len(self.inverse_bytes) == 256 and
                all(value in self.vocab for value in self.byte_map.values()),
                "incomplete byte alphabet")
        require(all(left in self.vocab and right in self.vocab and left + right in self.vocab
                    for left, right in pairs), "BPE merge references unknown symbols")
        added = specification["added_tokens"]
        require(all(row["single_word"] is False and row["lstrip"] is False and
                    row["rstrip"] is False and row["normalized"] is False for row in added),
                "unsupported added-token extraction policy")
        self.added_pattern = re.compile("(" + "|".join(
            re.escape(text) for text in sorted(self.added, key=lambda text: (-len(text), text))) + ")")
        self.splitter = UnicodeSplit()

    def parts(self, text):
        return [piece for piece in self.added_pattern.split(text) if piece]

    def encode(self, text, heap=False):
        output = []
        merge = heap_pairs if heap else ranked_pairs
        for part in self.parts(text):
            if part in self.added:
                output.append(self.added[part])
                continue
            for piece in self.splitter.split(unicodedata.normalize("NFC", part)):
                symbols = [self.byte_map[byte] for byte in piece.encode("utf-8")]
                output.extend(self.vocab[token] for token in merge(symbols, self.ranks))
        return output

    def normalized_text(self, text):
        return "".join(piece if piece in self.added else unicodedata.normalize("NFC", piece)
                       for piece in self.parts(text))


def artifact(descriptor):
    path = Path(descriptor["path"])
    require(not path.is_absolute() and ".." not in path.parts, "nonportable tokenizer input")
    full = (ROOT / path).resolve()
    require(full.is_relative_to(ROOT) and sha(full) == descriptor["sha256"],
            "tokenizer input binding failed")
    return full


def prepare(args, tokenizer):
    preparation = load_json(args.preparation)
    integrity = load_json(args.integrity_report)
    rendered = {(row["domain"], row["id"]): row for row in integrity["rendered_cases"]}
    cases, texts = [], []
    for domain, group in preparation["domains"].items():
        for selected in load_json(artifact(group["selected"])):
            content = load_json(artifact(selected["content"]))
            prompt = load_json(artifact(rendered[domain, selected["id"]]["rendered"]))
            require(prompt["messages"] == [{"role": "user", "content": content["prompt"]}],
                    "rendered prompt not bound to selected case")
            cases.append({"domain": domain, "id": selected["id"], "content": selected["content"],
                          "prompt": prompt["text"], "teacher_answer": content["answers"][0]})
            texts.extend((prompt["text"], content["answers"][0]))
    require(len(cases) == 50, "requires fifty selected tokenization cases")
    texts += ["", " ", " \n\n", "\r\n\t  ", "can't I'll WE'RE she's 'd 's 't 've 'm 'll",
              "e\u0301 \u00e9 \u212b A\u030a", "\u03a3\u03c2\u03c3 \u4e2d\u6587 \u0639\u0631\u0628\u064a",
              "\u00bd \u2163 0123456789", "  \u00a0\u2003\n\u2028\r",
              "\x00\x01\x1f\x7f", "\U0001f642\U0001f1fa\U0001f1f8 \u200d",
              "a" * 257, " " * 257]
    texts.extend(tokenizer.added)
    texts.extend("prefix" + token + "suffix" for token in tokenizer.added)
    texts.append("".join(tokenizer.added))
    rng = random.Random(17)
    alphabet = list("ABCxyz'0129_-! \t\r\n") + [
        "\u00e9", "\u0301", "\u00a0", "\u2003", "\u2028", "\u00bd", "\u2163",
        "\u03a3", "\u03c2", "\u4e2d", "\u0639", "\U0001f642", "\u200d"]
    texts.extend("".join(rng.choice(alphabet) for _ in range(rng.randrange(1, 65)))
                 for _ in range(1000))
    segments = sorted({part for text in texts for part in tokenizer.parts(text)
                       if part not in tokenizer.added})
    args.destination.mkdir(parents=True, exist_ok=False)
    write_json(args.destination / "unicode_request.json", {"pattern": PATTERN, "texts": segments})
    write_json(args.destination / "tokenization_cases.json", {
        "cases": cases, "texts": texts, "preparation_sha256": sha(args.preparation),
        "integrity_report_sha256": sha(args.integrity_report)})
    print(json.dumps({"unicode_segments": len(segments), "tokenizer_cases": len(texts),
                      "versions": tokenizer.splitter.versions,
                      "python_unicode_version": unicodedata.unidata_version}))


def qualify(args, tokenizer):
    request = load_json(args.destination / "unicode_request.json")
    reference = load_json(args.destination / "perl_unicode_reference.json")
    require(len(request["texts"]) == len(reference["texts"]), "incomplete Unicode reference")
    for text, expected in zip(request["texts"], reference["texts"]):
        normalized = unicodedata.normalize("NFC", text)
        require(normalized == expected["normalized"], "independent NFC normalization mismatch")
        require(tokenizer.splitter.split(normalized) == expected["pieces"],
                "PCRE2/Perl pinned regex split mismatch")
    data = load_json(args.destination / "tokenization_cases.json")
    for index, text in enumerate(data["texts"]):
        tokens = tokenizer.encode(text)
        require(tokens == tokenizer.encode(text, heap=True),
                f"independent BPE rank/heap mismatch in case {index}")
        require(tokenizer.decode(tokens) == tokenizer.normalized_text(text),
                f"NFC byte-level roundtrip mismatch in case {index}")
    for text, identifier in tokenizer.added.items():
        require(tokenizer.encode(text) == [identifier], "added-token extraction mismatch")
    # Rank order must win over leftmost adjacency; overlapping equal pairs merge left-to-right.
    for symbols, ranks, expected in (
        (["a", "b", "c"], {("a", "b"): 1, ("b", "c"): 0}, ["a", "bc"]),
        (["a"] * 3, {("a", "a"): 0}, ["aa", "a"]),
        (["a"] * 4, {("a", "a"): 0, ("aa", "aa"): 1}, ["aaaa"]),
    ):
        require(ranked_pairs(symbols, ranks) == expected and
                heap_pairs(symbols, ranks) == expected, "BPE analytical rank/tie test failed")
    token_cases = []
    for index, case in enumerate(data["cases"]):
        prompt = tokenizer.encode(case["prompt"])
        answer = tokenizer.encode(case["teacher_answer"])
        require(prompt and len(prompt) + 128 <= 32768, "prompt exceeds admitted capacity")
        require(all(0 <= token < 151936 for token in prompt + answer), "token outside vocabulary")
        prefix = f"case-{index:02d}"
        token_cases.append({
            "domain": case["domain"], "id": case["id"], "content": case["content"],
            "prompt_tokens": write_json(args.destination / (prefix + "-prompt.json"), prompt),
            "teacher_tokens": write_json(args.destination / (prefix + "-teacher.json"),
                                         prompt + answer[:128]),
            "answer_tokens": write_json(args.destination / (prefix + "-answer.json"), answer),
        })
    report = {
        "schema": 1, "purpose": "qualified-token-input-preparation", "acceptance_evidence": False,
        "unicode_segments_compared": len(request["texts"]),
        "tokenizer_cases_compared": len(data["texts"]), "added_tokens_compared": len(tokenizer.added),
        "analytical_bpe_cases": 3, "versions": tokenizer.splitter.versions,
        "perl_version": reference["perl_version"], "perl_unicode_version": reference["unicode_version"],
        "python_unicode_version": unicodedata.unidata_version,
        "preparation_sha256": data["preparation_sha256"],
        "integrity_report_sha256": data["integrity_report_sha256"],
        "teacher_policy": "Shared rendered prompt followed by up to 128 tokens of the first "
                          "published reference answer, with no fabricated EOS or sampling",
        "backend": "Exact pinned NFC/Split/ByteLevel/BPE rules; PCRE2 and independent Perl "
                   "Unicode/NFC parity, independent ranked-pair and heap BPE parity",
        "limitations": "No installed Hugging Face tokenizer backend comparison, model inference, "
                      "Code execution, DUT fidelity or benchmark scores are claimed.",
        "cases": token_cases,
    }
    write_json(args.destination / "tokenization_preparation.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))


def decoder_check(args, tokenizer):
    comparisons = 0
    for value in range(256):
        identifier = tokenizer.vocab[tokenizer.byte_map[value]]
        require(tokenizer.decode([identifier]) == bytes([value]).decode("utf-8", errors="replace"),
                "single-byte decode mismatch")
        comparisons += 1
    marker = "<|im_end|>"
    for raw in (b"\xc3\xa9", b"\xf0\x9f\x99\x82", b"\xe2\x82\xac", b"\xc0\xaf"):
        ids = [tokenizer.vocab[tokenizer.byte_map[value]] for value in raw]
        ids.insert(1, tokenizer.added[marker])
        require(tokenizer.decode(ids) ==
                (raw[:1] + marker.encode("ascii") + raw[1:]).decode("utf-8", errors="replace"),
                "literal special-token byte-stream decode mismatch")
        require(tokenizer.decode(ids, skip_special=True) == raw.decode("utf-8", errors="replace"),
                "skipping special tokens must precede UTF-8 byte-stream decoding")
        comparisons += 2
    require(tokenizer.decode([tokenizer.added["<tool_call>"]], skip_special=True) == "<tool_call>",
            "nonspecial added token was incorrectly skipped")
    comparisons += 1
    args.destination.mkdir(parents=True, exist_ok=False)
    report = {"byte_stream_comparisons": comparisons,
              "scope": "Independent UTF-8 decoder semantics; no model or generated Code executes"}
    write_json(args.destination / "decoder_report.json", report)
    print(json.dumps(report))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    phase = parser.add_mutually_exclusive_group(required=True)
    phase.add_argument("--prepare", action="store_true")
    phase.add_argument("--qualify", action="store_true")
    phase.add_argument("--decoder-check", action="store_true")
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--integrity-report", type=Path)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    for name in ("preparation", "integrity_report", "checkpoint_dir", "destination"):
        value = getattr(args, name)
        if value is not None:
            require(not value.is_absolute() and ".." not in value.parts, "nonportable tokenizer argument")
            value = (ROOT / value).resolve()
            require(value.is_relative_to(ROOT), "tokenizer argument escapes project")
            setattr(args, name, value)
    tokenizer = PinnedTokenizer(args.checkpoint_dir)
    try:
        if args.prepare:
            require(args.preparation is not None and args.integrity_report is not None,
                    "prepare requires canonical preparation and integrity report")
            prepare(args, tokenizer)
        elif args.qualify:
            qualify(args, tokenizer)
        else:
            decoder_check(args, tokenizer)
    finally:
        tokenizer.splitter.close()


if __name__ == "__main__":
    main()
