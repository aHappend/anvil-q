"""Independent NumPy FP64 Qwen equations and strict scored-logit comparisons.

No RTL helpers, parent outputs, external model services or generated code run
inside this oracle. Safetensors is read as data, never deserialized executable code.
"""

import json
import math
import struct
import unicodedata
import re

import numpy as np

from run_compatibility import logit_check


QWEN_PATTERN = (r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|"
                r"\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+")


def pieces(text):
    """Scan precisely the pinned tokenizer's Unicode pretokenization alternatives."""
    i = 0
    letter = lambda c: unicodedata.category(c).startswith("L")
    number = lambda c: unicodedata.category(c).startswith("N")
    punct = lambda c: not c.isspace() and not letter(c) and not number(c)
    while i < len(text):
        contraction = re.match(r"'(?:s|t|re|ve|m|ll|d)", text[i:], re.IGNORECASE)
        if contraction:
            j = i+len(contraction[0])
        elif letter(text[i]) or (text[i] not in "\r\n" and not number(text[i])
                                and i+1 < len(text) and letter(text[i+1])):
            j = i+int(not letter(text[i]))
            while j < len(text) and letter(text[j]):
                j += 1
        elif number(text[i]):
            j = i+1
        elif punct(text[i]) or (text[i] == " " and i+1 < len(text) and punct(text[i+1])):
            j = i+int(text[i] == " ")
            while j < len(text) and punct(text[j]):
                j += 1
            while j < len(text) and text[j] in "\r\n":
                j += 1
        elif text[i].isspace():
            end = i
            while end < len(text) and text[end].isspace():
                end += 1
            newlines = [k for k in range(i, end) if text[k] in "\r\n"]
            j = (newlines[-1]+1 if newlines else
                 end-1 if end < len(text) and end-i > 1 else end)
        else:
            raise AssertionError("unhandled tokenizer Unicode category")
        if j <= i:
            raise AssertionError("tokenizer scanner failed to advance")
        yield text[i:j]
        i = j


class Tokenizer:
    def __init__(self, path):
        data = json.loads(path.read_text())
        expected = {"type": "NFC"}
        split, byte = data["pre_tokenizer"]["pretokenizers"]
        if (data["normalizer"] != expected or split["pattern"]["Regex"] != QWEN_PATTERN
                or data["model"]["type"] != "BPE" or byte["type"] != "ByteLevel"
                or byte["use_regex"] or byte["add_prefix_space"]
                or data["model"]["dropout"] is not None
                or data["model"]["continuing_subword_prefix"] not in (None, "")
                or data["model"]["end_of_word_suffix"] not in (None, "")):
            raise ValueError("unsupported pinned tokenizer configuration")
        self.vocab = data["model"]["vocab"]
        self.ranks = {}
        for index, pair in enumerate(data["model"]["merges"]):
            pair = tuple(pair.split(" ")) if isinstance(pair, str) else tuple(pair)
            if len(pair) != 2:
                raise ValueError("invalid BPE merge")
            self.ranks[pair] = index
        self.special = {row["content"]: row["id"] for row in data["added_tokens"]}
        if any(row["lstrip"] or row["rstrip"] or row["single_word"]
               for row in data["added_tokens"]):
            raise ValueError("unsupported added-token matching policy")
        values = list(range(33, 127))+list(range(161, 173))+list(range(174, 256))
        codes, extension = list(values), 0
        for value in range(256):
            if value not in values:
                values.append(value)
                codes.append(256+extension)
                extension += 1
        self.byte_encoder = dict(zip(values, map(chr, codes)))
        self.byte_decoder = {v: k for k, v in self.byte_encoder.items()}
        self.inverse = {v: k for k, v in self.vocab.items()}
        self.inverse.update({v: k for k, v in self.special.items()})
        self.special_split = re.compile("("+"|".join(re.escape(s) for s in
                                       sorted(self.special, key=len, reverse=True))+")")

    def encode(self, text):
        result = []
        for segment in self.special_split.split(text):
            if segment in self.special:
                result.append(self.special[segment])
                continue
            for piece in pieces(unicodedata.normalize("NFC", segment)):
                symbols = [self.byte_encoder[b] for b in piece.encode("utf-8")]
                while len(symbols) > 1:
                    candidates = [(self.ranks[(a, b)], i) for i, (a, b) in
                                  enumerate(zip(symbols, symbols[1:])) if (a, b) in self.ranks]
                    if not candidates:
                        break
                    _, i = min(candidates)
                    symbols[i:i+2] = [symbols[i]+symbols[i+1]]
                result.extend(self.vocab[s] for s in symbols)
        return result

    def decode(self, tokens):
        parts, raw = [], bytearray()
        for token in tokens:
            word = self.inverse[token]
            if word in self.special:
                parts.append(raw.decode("utf-8", errors="replace"))
                raw.clear()
                parts.append(word)
            else:
                raw.extend(self.byte_decoder[c] for c in word)
        parts.append(raw.decode("utf-8", errors="replace"))
        return "".join(parts)


class Checkpoint:
    def __init__(self, path):
        with path.open("rb") as stream:
            prefix = stream.read(8)
            if len(prefix) != 8:
                raise ValueError("truncated safetensors prefix")
            length = struct.unpack("<Q", prefix)[0]
            if length > path.stat().st_size-8:
                raise ValueError("invalid safetensors header extent")
            header = stream.read(length)
        self.entries = json.loads(header)
        self.entries.pop("__metadata__", None)
        self.mapping = np.memmap(path, dtype=np.uint8, mode="r")
        self.offset = 8+length
        extents = []
        for name, row in self.entries.items():
            if row["dtype"] not in ("BF16", "F16", "F32"):
                raise ValueError(f"unsupported tensor dtype: {name}")
            start, end = row["data_offsets"]
            size = math.prod(row["shape"])*(4 if row["dtype"] == "F32" else 2)
            if start < 0 or end-start != size or self.offset+end > self.mapping.size:
                raise ValueError(f"invalid tensor extent: {name}")
            extents.append((start, end))
        if any(a[1] > b[0] for a, b in zip(sorted(extents), sorted(extents)[1:])):
            raise ValueError("overlapping safetensors tensors")

    def tensor(self, name, selection=None):
        row = self.entries[name]
        start, end = row["data_offsets"]
        dtype = "<f4" if row["dtype"] == "F32" else "<f2" if row["dtype"] == "F16" else "<u2"
        values = self.mapping[self.offset+start:self.offset+end].view(dtype).reshape(row["shape"])
        if selection is not None:
            values = values[selection]
        if row["dtype"] == "BF16":
            values = (values.astype(np.uint32) << 16).view(np.float32)
        result = values.astype(np.float64)
        if not np.isfinite(result).all():
            raise AssertionError(f"nonfinite official tensor {name}")
        return result


def narrow_bf16(values):
    fp32 = np.asarray(values, dtype=np.float32)
    bits = fp32.view(np.uint32)
    rounded = ((bits + np.uint32(0x7fff) + ((bits >> 16) & 1)) >> 16) << 16
    if not np.isfinite(fp32).all():
        raise AssertionError("nonfinite represented-image activation")
    result = rounded.astype(np.uint32).view(np.float32).astype(np.float64)
    if not np.isfinite(result).all():
        raise AssertionError("nonfinite represented-image BF16 narrowing")
    return result


class QwenFP64:
    def __init__(self, config, checkpoint, represented=False):
        self.c, self.weights, self.represented = config, checkpoint, represented
        self.cache = [[] for _ in range(config["num_hidden_layers"])]
        if (config["hidden_size"] != config["num_attention_heads"]*64
                or config["rope_theta"] != 1000000 or config["hidden_act"] != "silu"
                or config["use_sliding_window"] or not config["tie_word_embeddings"]):
            raise ValueError("unsupported official Qwen architecture")
        self.position = 0

    def norm(self, x, gamma):
        epsilon = (float(np.float32(self.c["rms_norm_eps"])) if self.represented
                   else self.c["rms_norm_eps"])
        return x/np.sqrt(np.mean(x*x, dtype=np.float64)+epsilon)*gamma

    def boundary(self, x):
        return narrow_bf16(x) if self.represented else x

    def step(self, token):
        c, w, p = self.c, self.weights, self.position
        if p >= c["max_position_embeddings"] or not 0 <= token < c["vocab_size"]:
            raise ValueError("official model token/position outside contract")
        qh, kh, d = c["num_attention_heads"], c["num_key_value_heads"], 64
        x = w.tensor("model.embed_tokens.weight", token)
        angles = p*c["rope_theta"]**(-np.arange(0, d, 2, dtype=np.float64)/d)
        cosine, sine = np.cos(angles), np.sin(angles)

        def rotary(v):
            first, second = v[:, :d//2], v[:, d//2:]
            return np.concatenate((first*cosine-second*sine, first*sine+second*cosine), axis=1)

        for layer in range(c["num_hidden_layers"]):
            prefix = f"model.layers.{layer}."
            n = self.boundary(self.norm(x, w.tensor(prefix+"input_layernorm.weight")))
            qkv = [w.tensor(prefix+f"self_attn.{name}_proj.weight") @ n+
                   w.tensor(prefix+f"self_attn.{name}_proj.bias") for name in ("q", "k", "v")]
            q = self.boundary(rotary(qkv[0].reshape(qh, d)))
            k = self.boundary(rotary(qkv[1].reshape(kh, d)))
            v = self.boundary(qkv[2].reshape(kh, d))
            self.cache[layer].append((k, v))
            attention = []
            for head in range(qh):
                group = head//(qh//kh)
                keys = np.stack([kv[0][group] for kv in self.cache[layer]])
                values = np.stack([kv[1][group] for kv in self.cache[layer]])
                scores = keys @ q[head]/math.sqrt(d)
                probabilities = np.exp(scores-np.max(scores))
                attention.append((probabilities @ values)/np.sum(probabilities, dtype=np.float64))
            a = self.boundary(np.concatenate(attention))
            x = x+w.tensor(prefix+"self_attn.o_proj.weight") @ a
            post = self.boundary(self.norm(x, w.tensor(prefix+"post_attention_layernorm.weight")))
            gate = w.tensor(prefix+"mlp.gate_proj.weight") @ post
            up = w.tensor(prefix+"mlp.up_proj.weight") @ post
            # Stable finite sigmoid avoids overflow for large negative gates.
            exp = np.exp(-np.abs(gate))
            sigmoid = np.where(gate >= 0, 1/(1+exp), exp/(1+exp))
            hidden = self.boundary(gate*sigmoid*up)
            x = x+w.tensor(prefix+"mlp.down_proj.weight") @ hidden
        final = self.boundary(self.norm(x, w.tensor("model.norm.weight")))
        logits = np.empty(c["vocab_size"], dtype=np.float64)
        for start in range(0, len(logits), 1024):
            logits[start:start+1024] = w.tensor("model.embed_tokens.weight",
                                               slice(start, start+1024)) @ final
        if not np.isfinite(logits).all():
            raise AssertionError("nonfinite FP64 official model logits")
        self.position += 1
        return logits


def scored_position(actual, reference, target):
    if not 0 <= target < len(reference):
        raise AssertionError("shifted target outside model vocabulary")
    metric = logit_check(list(actual), list(reference))
    maximum = max(actual)
    log_z = maximum+math.log(math.fsum(math.exp(x-maximum) for x in actual))
    nll = log_z-actual[target]
    if not math.isfinite(nll) or nll < 0:
        raise AssertionError("invalid scored negative log likelihood")
    return dict(**metric, target=target, nll=nll, greedy_token=int(np.argmax(actual)))


def perplexity(positions, required=128):
    indices = [p["position"] for p in positions]
    if len(positions) < required or indices != list(range(indices[0], indices[0]+len(indices))):
        raise AssertionError("missing/noncontiguous WikiText scored tokens")
    total = math.fsum(p["nll"] for p in positions)
    return dict(scored_tokens=len(positions), total_nll=total,
                perplexity=math.exp(total/len(positions)), padding_tokens=0)
