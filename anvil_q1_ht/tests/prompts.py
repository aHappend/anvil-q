"""Prepare the five D5 inputs from the pinned tokenizer, not inference results.

Run ``python3 -B tests/verify.py --probe checkpoint-prompts``. The frozen inputs
are ASCII. Their Unicode-property pretokenizer is specialized only for that
domain, with explicit rejection outside it; this is not a general tokenizer.
The pinned Jinja template is rendered using the already installed Jinja2.
Independent scan-and-merge and linked-list/heap BPE algorithms must agree on
every token. Output retains complete text, IDs, input hashes and round trips.
"""

import hashlib
import heapq
import importlib.metadata
import json
import re
import unicodedata

from fixtures import project_path


PROMPTS = (
    "Explain why the sky is blue.",
    "Write a Python function that reverses a list.",
    "Solve 17 * 23 and explain the calculation.",
    "All roses are flowers. Some flowers fade quickly. Must all roses fade quickly?",
    "Translate hello into French, Spanish, and German.",
)
SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
PINNED_SPLIT = (
    r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}|"
    r" ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
)
ASCII_SPLIT = re.compile(
    r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\nA-Za-z0-9]?[A-Za-z]+|[0-9]|"
    r" ?[^\sA-Za-z0-9]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+",
    re.ASCII,
)


def byte_alphabet():
    visible = [*range(33, 127), *range(161, 173), *range(174, 256)]
    result = {byte: chr(byte) for byte in visible}
    for byte in range(256):
        if byte not in result:
            result[byte] = chr(256 + byte - sum(value < byte for value in visible))
    if len(set(result.values())) != 256:
        raise AssertionError("byte alphabet is not bijective")
    return result


def split_ascii(text):
    if not text.isascii():
        raise ValueError("frozen-prompt tokenizer accepts ASCII input only")
    pieces = ASCII_SPLIT.findall(unicodedata.normalize("NFC", text))
    if "".join(pieces) != text:
        raise AssertionError("pretokenization lost input characters")
    return pieces


def merge_scan(piece, ranks):
    symbols = list(piece)
    while len(symbols) > 1:
        candidates = [
            (ranks[pair], pair) for pair in zip(symbols, symbols[1:]) if pair in ranks
        ]
        if not candidates:
            break
        _, pair = min(candidates)
        following, index = [], 0
        while index < len(symbols):
            if index + 1 < len(symbols) and tuple(symbols[index:index + 2]) == pair:
                following.append(symbols[index] + symbols[index + 1])
                index += 2
            else:
                following.append(symbols[index])
                index += 1
        symbols = following
    return symbols


def merge_heap(piece, ranks):
    words = list(piece)
    previous = [index - 1 for index in range(len(words))]
    following = [index + 1 for index in range(len(words))]
    alive = [True] * len(words)
    queue = []

    def candidate(left):
        if left < 0 or not alive[left]:
            return
        right = following[left]
        if right >= len(words) or not alive[right]:
            return
        pair = words[left], words[right]
        if pair in ranks:
            heapq.heappush(queue, (ranks[pair], left, right, *pair))

    for index in range(len(words) - 1):
        candidate(index)
    while queue:
        _, left, right, first, second = heapq.heappop(queue)
        if (not alive[left] or not alive[right] or following[left] != right or
                words[left] != first or words[right] != second):
            continue
        words[left] = first + second
        alive[right] = False
        following[left] = following[right]
        if following[right] < len(words):
            previous[following[right]] = left
        candidate(previous[left])
        candidate(left)
    return [word for word, present in zip(words, alive) if present]


class FrozenTokenizer:
    def __init__(self, tokenizer, config):
        if tokenizer["normalizer"] != {"type": "NFC"}:
            raise ValueError("unsupported pinned tokenizer normalization")
        expected_byte = {"type": "ByteLevel", "add_prefix_space": False,
                         "trim_offsets": False, "use_regex": False}
        expected_split = {
            "type": "Split", "pattern": {"Regex": PINNED_SPLIT},
            "behavior": "Isolated", "invert": False,
        }
        if (tokenizer["pre_tokenizer"] != {
                "type": "Sequence", "pretokenizers": [expected_split, expected_byte]} or
                tokenizer["post_processor"] != expected_byte or
                tokenizer["decoder"] != expected_byte):
            raise ValueError("unsupported pinned tokenizer byte/split pipeline")
        model = tokenizer["model"]
        if (model["type"] != "BPE" or model["dropout"] is not None or
                model["unk_token"] is not None or model["continuing_subword_prefix"] or
                model["end_of_word_suffix"] or model["byte_fallback"] or
                model["fuse_unk"] or config["add_bos_token"] or config["add_prefix_space"]):
            raise ValueError("unsupported pinned tokenizer BPE options")
        pairs = [tuple(merge.split(" ")) for merge in model["merges"]]
        if any(len(pair) != 2 for pair in pairs) or len(set(pairs)) != len(pairs):
            raise ValueError("invalid or duplicate BPE merge rule")
        self.ranks = {pair: rank for rank, pair in enumerate(pairs)}
        self.vocab = model["vocab"]
        self.added = {}
        for token in tokenizer["added_tokens"]:
            if (type(token["special"]) is not bool or token["single_word"] or
                    token["lstrip"] or token["rstrip"] or token["normalized"]):
                raise ValueError("unsupported added-token semantics")
            if config["added_tokens_decoder"][str(token["id"])] != {
                    key: value for key, value in token.items() if key != "id"}:
                raise ValueError("added-token ID differs from tokenizer configuration")
            self.added[token["content"]] = token["id"]
        self.split_special = re.compile("(" + "|".join(
            re.escape(token) for token in sorted(self.added, key=len, reverse=True)) + ")")
        self.alphabet = byte_alphabet()
        self.inverse_bytes = {character: byte for byte, character in self.alphabet.items()}
        self.inverse_ids = {index: token for token, index in self.vocab.items()}
        if len(self.inverse_ids) != len(self.vocab):
            raise ValueError("duplicate vocabulary ID")
        for token, index in self.added.items():
            if index in self.inverse_ids and self.inverse_ids[index] != token:
                raise ValueError("added-token ID aliases vocabulary")
            self.inverse_ids[index] = token
        if any(character not in self.vocab for character in self.alphabet.values()):
            raise ValueError("missing byte token")

    def encode(self, text, algorithm):
        split_ascii(text)
        output = []
        for part in self.split_special.split(text):
            if part in self.added:
                output.append(self.added[part])
                continue
            for piece in split_ascii(part):
                encoded = "".join(self.alphabet[byte] for byte in piece.encode("utf-8"))
                output.extend(self.vocab[word] for word in algorithm(encoded, self.ranks))
        return output

    def decode(self, tokens):
        output = bytearray()
        for index in tokens:
            word = self.inverse_ids[index]
            if word in self.added:
                output.extend(word.encode("utf-8"))
            else:
                output.extend(self.inverse_bytes[character] for character in word)
        return output.decode("utf-8")


def canonical_chat(prompt):
    return (f"<|im_start|>system\n{SYSTEM}<|im_end|>\n"
            f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n")


def prepare(evidence):
    from jinja2.sandbox import ImmutableSandboxedEnvironment

    evidence.command(["python3", "tests/fixtures.py"], "prompt-fixture-validation")
    evidence.command(
        ["python3", "-c", "import importlib.metadata; print(importlib.metadata.version('jinja2'))"],
        "prompt-template-tool-version")
    root = project_path("fixtures/qwen2.5-0.5b")
    inputs = [root / "manifest.json"] + [
        root / mode / name for mode in ("awq", "bf16")
        for name in ("tokenizer.json", "tokenizer_config.json")
    ]
    evidence.record.setdefault("runtime_input_sha256", {}).update({
        str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs
    })
    environment = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    rows = []
    split_cases = (
        ("We're 17!", ["We", "'re", " ", "1", "7", "!"]),
        (" hello\n\n", [" hello", "\n\n"]),
        ("a  b", ["a", " ", " b"]),
        ("\tword", ["\tword"]),
    )
    for text, expected in split_cases:
        if split_ascii(text) != expected:
            raise AssertionError(f"ASCII pretokenizer mismatch: {text!r}")
    try:
        split_ascii("\u00e9")
    except ValueError:
        pass
    else:
        raise AssertionError("ASCII-only domain guard accepted non-ASCII")
    for mode in ("AWQ", "BF16"):
        folder = root / mode.lower()
        config = json.loads((folder / "tokenizer_config.json").read_text())
        tokenizer = FrozenTokenizer(json.loads((folder / "tokenizer.json").read_text()), config)
        template = environment.from_string(config["chat_template"])
        for index, prompt in enumerate(PROMPTS):
            rendered = template.render(
                messages=[{"role": "user", "content": prompt}], tools=None,
                add_generation_prompt=True,
            )
            if rendered != canonical_chat(prompt):
                raise AssertionError("pinned chat template differs from independently expected text")
            tokens = tokenizer.encode(rendered, merge_heap)
            expected = tokenizer.encode(canonical_chat(prompt), merge_scan)
            if (tokens != expected or not tokens or tokenizer.decode(tokens) != rendered or
                    any(not 0 <= token < 151936 for token in tokens) or
                    tokens.count(151644) != 3 or tokens.count(151645) != 2 or
                    tokens[0] != 151644 or tokens[-3:] != tokenizer.encode(
                        "<|im_start|>assistant\n", merge_scan)):
                raise AssertionError(f"frozen prompt token/reference mismatch: {mode}/{index}")
            if tokenizer.encode(rendered, lambda piece, ranks: list(piece)) == expected:
                raise AssertionError("disabled-merge defect escaped frozen prompt comparison")
            damaged = rendered.replace("assistant\n", "user\n")
            if tokenizer.encode(damaged, merge_heap) == expected:
                raise AssertionError("generation-role defect escaped frozen prompt comparison")
            rows.append({
                "mode": mode, "prompt_index": index, "prompt": prompt,
                "messages": [{"role": "user", "content": prompt}],
                "add_generation_prompt": True, "rendered_chat": rendered,
                "rendered_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
                "token_ids": tokens, "prefill_tokens": len(tokens),
                "greedy_decode_tokens": 16, "tie_policy": "lowest_vocabulary_index",
                "reference_compared_ids": len(expected), "round_trip_compared": True,
            })
    if [row["token_ids"] for row in rows[:5]] != [row["token_ids"] for row in rows[5:]]:
        raise AssertionError("AWQ/BF16 pinned tokenizers disagree on frozen prompts")
    result = {
        "schema": 1, "scope": "D5_frozen_input_preparation_not_model_or_RTL_inference",
        "tokenizer_domain": "ASCII frozen prompts and their pinned default-system chat",
        "tokenizer_implementations": ["linked_list_heap_BPE", "global_pair_scan_BPE"],
        "template_tool": {"name": "jinja2", "version": importlib.metadata.version("jinja2")},
        "input_sha256": {str(path): evidence.record["runtime_input_sha256"][str(path)]
                         for path in inputs},
        "warmup": "not_executed", "measured_decode_tokens": 0,
        "ordered_logit_vectors_compared": 0, "rows": rows,
        "limitations": [
            "No RTL, floating-point software-model, or full-model numerical comparison.",
            "No prefill/decode cycles, token throughput, or physical-board result.",
            "No claim of arbitrary Unicode, tools, or multi-message tokenizer support.",
        ],
    }
    output = evidence.folder / "frozen-prompts.json"
    with output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    relative = evidence.relative(output)
    evidence.record["runtime_input_sha256"][relative] = hashlib.sha256(output.read_bytes()).hexdigest()
    evidence.record["observations"].append({
        "scope": result["scope"], "manifest": relative,
        "prompt_mode_rows": len(rows),
        "token_ids_compared": sum(row["reference_compared_ids"] for row in rows),
        "pretokenizer_cases_compared": len(split_cases),
        "non_ascii_rejections": 1, "disabled_merge_rejections": len(rows),
        "generation_role_rejections": len(rows),
        "full_model_acceptance": False,
    })
    evidence.flush()
