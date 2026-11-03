"""Ordered native decoder oracle and deterministic external-memory fixtures."""

from collections import Counter
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
import random

from attention import attention
from ieee import convert, exp_frozen, operation, pack, sqrt_round
from images import export_static, load


@lru_cache(maxsize=262144)
def op(code, a, b=0):
    return operation(code, a, b)[0]


@lru_cache(maxsize=65536)
def exp(bits):
    return exp_frozen(bits)[0]


def descriptor(*, banks=16, element=0, cache=0, layers=1, dimension=2,
               ratio=1, kv_heads=1, intermediate=3, vocabulary=19,
               context=5, page_tokens=2, bias=1):
    query_heads = kv_heads * ratio
    hidden = query_heads * dimension
    return [2, 5, element, 0, 0, cache, banks, layers, hidden, intermediate,
            query_heads, kv_heads, dimension, vocabulary, context, 1, bias,
            0x461c4000, pack(Fraction(1, 1000000))[0], page_tokens,
            (context + page_tokens - 1) // page_tokens, 0, ratio, 1] + [0] * 8


class Fixture:
    """Only mutable DUT writes populate scratch/cache in the simulator."""

    def __init__(self, words, seed=17, tokens=2, *, epoch=1, pages=None,
                 constant_profile=False):
        self.words = words
        self.seed = seed
        self.constant_profile = constant_profile
        self.tokens = ([((seed + 3 * index) % words[13]) for index in range(tokens)]
                       if isinstance(tokens, int) else list(tokens))
        self.initial = {}
        self.writes = []
        self.logits = []
        self.steps = []
        self.tensors = []
        self.format = "fp16" if words[2] else "bf16"
        self.cache_format = ("bf16", "fp16", "fp8")[words[5]]
        self.rng = random.Random(seed)
        self.epoch = epoch
        self.pages = list(reversed(range(words[20]))) if pages is None else list(pages)
        self.cache = {}
        self.build_image()
        self.infer()

    def number(self, denominator=64):
        numerator = self.rng.choice(tuple(range(-15, 0)) + tuple(range(1, 16)))
        return pack(Fraction(numerator, denominator), self.format)[0]

    def tensor(self, kind, layer, projection, rows, columns, *, gamma=False):
        data = [[pack(Fraction(1) if gamma else
                      Fraction(1, 2) if kind==0 and projection==0 else Fraction(0),
                      self.format)[0] if self.constant_profile else
                 pack(Fraction(self.rng.randrange(24, 41), 32), self.format)[0]
                 if gamma else self.number(8 if kind == 0 and projection == 0 else 64)
                 for _ in range(columns)] for _ in range(rows)]
        for row, vector in enumerate(data):
            for col, value in enumerate(vector):
                self.initial[kind, layer, projection, row, col] = value
        self.tensors.append((kind, layer, projection, data))
        return data

    def build_image(self):
        w = self.words
        h, inter, kd, vocabulary = w[8], w[9], w[11] * w[12], w[13]
        self.embedding = self.tensor(0, 0, 0, vocabulary, h)
        self.lm_head = self.tensor(0, 0, 1, vocabulary, h)
        self.weights, self.biases, self.gamma = {}, {}, {}
        for layer in range(w[7]):
            for projection, rows, columns in (
                    (0, h, h), (1, kd, h), (2, kd, h), (3, h, h),
                    (4, inter, h), (5, inter, h), (6, h, inter)):
                self.weights[layer, projection] = self.tensor(
                    1, layer, projection, rows, columns)
                if projection < 3 and w[16]:
                    self.biases[layer, projection] = self.tensor(
                        4, layer, projection, 1, rows)[0]
            for kind in (5, 6):
                self.gamma[layer, kind] = self.tensor(kind, layer, 0, 1, h, gamma=True)[0]
        self.final_gamma = self.tensor(7, 0, 0, 1, h, gamma=True)[0]
        self.rope = {}
        for position in range(w[14]):
            table = []
            for pair in range(w[12] // 2):
                # Synthetic supplied unit-circle tables, exact rationals rounded
                # once. No checkpoint/scaled-Llama measurement is implied.
                t = Fraction(0) if self.constant_profile else Fraction(position * (pair + 1), 16)
                table.extend((pack((1-t*t)/(1+t*t))[0], pack(2*t/(1+t*t))[0]))
            self.rope[position] = table
            for col, value in enumerate(table):
                self.initial[11, 1, 0, position, col] = value
        logical_pages = (w[14] + w[19] - 1) // w[19]
        for page, physical in enumerate(self.pages[:logical_pages]):
            self.initial[15, self.epoch, 0, page, 0] = 0x80000000 | physical

    def widen(self, value):
        return convert(value, self.format, "fp32")[0]

    def narrow(self, value):
        return convert(value, "fp32", self.format)[0]

    def store(self, slot, vector):
        for col, value in enumerate(vector):
            self.writes.append(((8, 0, 0, slot, col), value))
        return vector

    def gemv(self, matrix, vector, bias=None):
        inputs = [self.widen(self.narrow(x)) for x in vector]
        result = []
        for row, weights in enumerate(matrix):
            accumulator = 0
            for x, weight in zip(inputs, weights, strict=True):
                accumulator = op(0, accumulator, op(2, x, self.widen(weight)))
            if bias is not None:
                accumulator = op(0, accumulator, self.widen(bias[row]))
            result.append(accumulator)
        return result

    def norm(self, vector, gamma):
        total = 0
        for x in vector:
            total = op(0, total, op(2, x, x))
        mean = op(3, total, pack(Fraction(len(vector)))[0])
        root = op(4, op(0, mean, self.words[18]))
        return [op(3, op(2, x, self.widen(g)), root)
                for x, g in zip(vector, gamma, strict=True)]

    def rotate(self, vector, position, slot):
        dimension = self.words[12]
        result = list(vector)
        table = self.rope[position]
        for base in range(0, len(vector), dimension):
            for pair in range(dimension // 2):
                a, b = vector[base + pair], vector[base + pair + dimension // 2]
                cosine, sine = table[2 * pair:2 * pair + 2]
                y0 = op(1, op(2, a, cosine), op(2, b, sine))
                y1 = op(0, op(2, a, sine), op(2, b, cosine))
                result[base + pair] = y0
                result[base + pair + dimension // 2] = y1
                self.writes.extend((
                    ((8, 0, 0, slot, base + pair), y0),
                    ((8, 0, 0, slot, base + pair + dimension // 2), y1)))
        return result

    def cache_store(self, layer, position, vector, value_select):
        w = self.words
        elements = [convert(x, "fp32", self.cache_format)[0] for x in vector]
        physical_row = self.pages[position // w[19]] * w[19] + position % w[19]
        per_word, width = (4, 8) if w[5] == 2 else (2, 16)
        kind = (13 if value_select else 12) if w[5] == 2 else (10 if value_select else 9)
        for base in range(0, len(elements), per_word):
            payload = sum(x << (width * lane)
                          for lane, x in enumerate(elements[base:base + per_word]))
            self.writes.append(((kind, layer, 0, physical_row, base // per_word), payload))
        decoded = [convert(x, self.cache_format, "fp32")[0] for x in elements]
        self.cache[layer, position, value_select] = decoded

    def attend(self, layer, position, queries):
        w = self.words
        dimension, ratio = w[12], w[22]
        result = []
        for head in range(w[10]):
            kv_base = (head // ratio) * dimension
            keys = [self.cache[layer, pos, False][kv_base:kv_base + dimension]
                    for pos in range(position + 1)]
            values = [self.cache[layer, pos, True][kv_base:kv_base + dimension]
                      for pos in range(position + 1)]
            query = queries[head * dimension:(head + 1) * dimension]
            result.extend(attention(query, keys, values,
                                    sqrt_round(Fraction(1, dimension))[0])["result"])
        return result

    def infer(self):
        for position, token in enumerate(self.tokens):
            if token is None:
                token = self.greedy(self.logits[-self.words[13]:])
                self.tokens[position] = token
            write_start, logit_start = len(self.writes), len(self.logits)
            x = self.store(0, [self.widen(v) for v in self.embedding[token]])
            for layer in range(self.words[7]):
                normalized = self.store(1, self.norm(x, self.gamma[layer, 5]))
                projected = []
                for projection, slot in ((0, 2), (1, 3), (2, 4)):
                    projected.append(self.store(slot, self.gemv(
                        self.weights[layer, projection], normalized,
                        self.biases.get((layer, projection)))))
                q = self.rotate(projected[0], position, 2)
                k = self.rotate(projected[1], position, 3)
                self.cache_store(layer, position, k, False)
                self.cache_store(layer, position, projected[2], True)
                context = self.store(5, self.attend(layer, position, q))
                output = self.store(6, self.gemv(self.weights[layer, 3], context))
                residual = self.store(7, [op(0, a, b) for a, b in zip(x, output, strict=True)])
                normalized = self.store(8, self.norm(residual, self.gamma[layer, 6]))
                gate = self.store(9, self.gemv(self.weights[layer, 4], normalized))
                up = self.store(10, self.gemv(self.weights[layer, 5], normalized))
                activated = self.store(11, [op(2, op(3, g, op(0, 0x3f800000,
                    exp(g ^ 0x80000000))), u) for g, u in zip(gate, up, strict=True)])
                down = self.store(12, self.gemv(self.weights[layer, 6], activated))
                x = self.store(0, [op(0, a, b) for a, b in zip(residual, down, strict=True)])
            final = self.store(14, self.norm(x, self.final_gamma))
            self.logits.extend(self.gemv(self.lm_head, final))
            self.steps.append({"token": token, "position": position,
                               "writes": self.writes[write_start:],
                               "logits": self.logits[logit_start:]})

    @staticmethod
    def greedy(logits):
        from ieee import decode
        best, value = 0, None
        for index, bits in enumerate(logits):
            sign, kind, number = decode(bits)
            if kind == "nan":
                continue
            ordered = ((0 if sign else 2), Fraction(0)) if kind == "inf" else (1, number)
            if value is None or ordered > value:
                best, value = index, ordered
        return best

    def export(self, directory):
        source_manifest = export_static(directory / "checkpoint-images",
                                        self.words, self.initial, self.seed)
        actual_initial = load(source_manifest)
        if actual_initial != self.initial:
            raise AssertionError("Exported binary image differs from source tensor tuples")
        fixture = directory / "native-image.txt"
        with fixture.open("w") as stream:
            stream.write(" ".join(f"{word:x}" for word in self.words) + "\n")
            stream.write(f"{len(self.tokens)}\n")
            stream.write(" ".join(f"{token:x}" for token in self.tokens) + "\n")
            stream.write(f"{len(actual_initial)}\n")
            for key, value in sorted(actual_initial.items()):
                stream.write(" ".join(f"{v:x}" for v in (*key, value)) + "\n")
            stream.write(f"{len(self.writes)}\n")
            for key, value in self.writes:
                stream.write(" ".join(f"{v:x}" for v in (*key, value)) + "\n")
            stream.write(f"{len(self.logits)}\n")
            stream.writelines(f"{word:x}\n" for word in self.logits)
        manifest = {
            "schema": 1, "layout": 1, "synthetic": True, "checkpoint": None,
            "seed": self.seed, "descriptor_words": self.words,
            "sequence_epoch": self.epoch, "physical_page_mapping": self.pages,
            "constant_zero_weight_profile": self.constant_profile,
            "tokens": self.tokens, "image_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
            "source_manifest": "checkpoint-images/manifest.json",
            "source_manifest_sha256": hashlib.sha256(source_manifest.read_bytes()).hexdigest(),
            "expected_logits": len(self.logits), "expected_writes": len(self.writes),
            "write_kinds": dict(Counter(key[0] for key, _ in self.writes)),
            "rope_generation": "synthetic rational unit circle t=position*(pair+1)/16",
            "reference": "integer/rational IEEE RNE; ordered unfused FP32 operations",
        }
        (directory / "reference.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return fixture
