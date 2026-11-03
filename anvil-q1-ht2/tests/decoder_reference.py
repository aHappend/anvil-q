"""Seeded compact images and an independent ordered native-format decoder.

The image layout follows the published descriptor ABI. Arithmetic follows N2,
not the DUT controller. The same stored tensors feed a separate FP64 decoder.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
import math
import random

import ieee_reference as fp
from operator_checks import norm_reference, swiglu_reference


@dataclass(frozen=True)
class Geometry:
    layers: int = 1
    hidden: int = 8
    intermediate: int = 8
    query_heads: int = 1
    kv_heads: int = 1
    head_dim: int = 8
    group: int = 1
    vocabulary: int = 7
    sequence: int = 9
    tile: int = 1
    window: int = 3

    def parameters(self):
        return dict(zip(
            ("NUM_LAYERS", "HIDDEN_SIZE", "INTERMEDIATE_SIZE", "NUM_Q_HEADS",
             "NUM_KV_HEADS", "HEAD_DIM", "GROUP_SIZE", "VOCAB_SIZE", "MAX_SEQ_LEN",
             "TILE_BEATS", "KV_WINDOW"), self.__dict__.values()))


def align64(value):
    return (value + 63) // 64 * 64


def contexts(products, indices=None):
    sums = [0] * 4
    for index, product in zip(range(len(products)) if indices is None else indices, products):
        sums[index % 4] = fp.add(sums[index % 4], product)
    return fp.add(fp.add(fp.add(sums[0], sums[1]), sums[2]), sums[3])


def frequency(pair, dimensions):
    with localcontext() as ctx:
        ctx.prec = 100
        exact = Decimal(1000000) ** (-Decimal(2 * pair) / Decimal(dimensions))
        return fp.rounded(Fraction(exact))


class Image:
    def __init__(self, geometry=Geometry(), mode=0, seed=17):
        self.geometry, self.mode = geometry, mode
        self.fmt = fp.FP16 if mode == 1 else fp.BF16
        self.memory = bytearray(4096)
        self.descriptors = []
        self.tensors = {}
        self.rng = random.Random(seed)
        g = geometry
        self.embedding = self.matrix(g.vocabulary, g.hidden, 16)
        self.norms = {}
        self.weights, self.biases = {}, {}
        self.append(0, 0, 0, self.panel(self.embedding))
        for layer in range(g.layers):
            for projection in range(7):
                rows = (g.kv_heads * g.head_dim if projection in (1, 2) else
                        g.intermediate if projection in (4, 5) else g.hidden)
                columns = g.intermediate if projection == 6 else g.hidden
                weights = self.matrix(rows, columns, 128)
                if mode == 2:
                    packed, zeros, scales, weights = self.awq(rows, columns)
                    self.append(1, layer, projection, packed)
                    self.append(2, layer, projection, zeros)
                    self.append(3, layer, projection, scales)
                else:
                    self.append(1, layer, projection, self.panel(weights))
                self.weights[layer, projection] = weights
            for projection in range(3):
                width = g.hidden if projection == 0 else g.kv_heads * g.head_dim
                bias = self.matrix(1, width, 256)[0]
                self.biases[layer, projection] = bias
                self.append(4, layer, projection, self.halfwords(bias))
            for kind in (5, 6):
                norm = [fp.rounded(Fraction(self.rng.randrange(56, 73), 64), self.fmt)
                        for _ in range(g.hidden)]
                self.norms[kind, layer] = norm
                self.append(kind, layer, 0, self.halfwords(norm))
            for kind in (9, 10):
                self.append(kind, layer, 0, bytes(g.sequence * align64(g.kv_heads * g.head_dim * 2)))
        self.norms[7, 0] = [fp.rounded(1, self.fmt)] * g.hidden
        self.append(7, 0, 0, self.halfwords(self.norms[7, 0]))
        self.append(8, 0, 0, bytes(15 * max(g.hidden, g.intermediate) * 4))
        self.append(11, 0, 0, bytes(g.sequence * g.head_dim * 4))

    def matrix(self, rows, columns, denominator):
        return [[fp.rounded(Fraction(self.rng.randrange(-16, 17), denominator), self.fmt)
                 for _ in range(columns)] for _ in range(rows)]

    @staticmethod
    def halfwords(values):
        return b"".join(x.to_bytes(2, "little") for x in values)

    def panel(self, matrix):
        rows, columns = len(matrix), len(matrix[0])
        return self.halfwords([
            matrix[row][column] if row < rows else 0
            for panel in range((rows + 63) // 64)
            for column in range(columns)
            for row in range(panel * 64, panel * 64 + 64)
        ])

    def awq(self, rows, columns):
        g = self.geometry
        weight_data, zero_data, scale_data = bytearray(), bytearray(), bytearray()
        matrix = [[0] * columns for _ in range(rows)]
        for panel in range((rows + 63) // 64):
            for group in range(columns // g.group):
                zeros = [self.rng.randrange(5, 11) for _ in range(64)]
                scales = [fp.rounded(Fraction(self.rng.randrange(1, 5), 256), fp.FP16)
                          for _ in range(64)]
                zero_data.extend(self.pack_awq(zeros) + bytes(32))
                scale_data.extend(self.halfwords(scales))
                for column in range(group * g.group, (group + 1) * g.group):
                    qs = [self.rng.randrange(16) for _ in range(64)]
                    weight_data.extend(self.pack_awq(qs) + bytes(32))
                    for lane in range(64):
                        row = panel * 64 + lane
                        if row < rows:
                            difference = fp.rounded(qs[lane] - zeros[lane])
                            scaled = fp.multiply(difference, fp.convert(scales[lane], fp.FP16, fp.FP32))
                            matrix[row][column] = fp.convert(scaled, fp.FP32, fp.BF16)
        return bytes(weight_data), bytes(zero_data), bytes(scale_data), matrix

    @staticmethod
    def pack_awq(values):
        words = [0] * 8
        for lane, value in enumerate(values):
            shift = ((lane & 1) * 4 + ((lane & 7) >> 1)) * 4
            words[lane // 8] |= value << shift
        return b"".join(x.to_bytes(4, "little") for x in words)

    def append(self, kind, layer, projection, data):
        size = align64(len(data))
        address = len(self.memory)
        self.memory.extend(data)
        self.memory.extend(bytes(size - len(data)))
        self.descriptors.append((96 * layer + 8 * kind + projection,
                                 kind, layer, projection, address, size))


class Decoder:
    def __init__(self, image, fp64=False):
        self.image, self.g, self.fp64 = image, image.geometry, fp64
        self.observations = []

    def expand(self, x):
        return float(fp.value(x, self.image.fmt)) if self.fp64 else fp.convert(
            x, self.image.fmt, fp.FP32)

    def narrow(self, x):
        return float(fp.value(fp.rounded(Fraction(x), self.image.fmt), self.image.fmt)) if self.fp64 else self.expand(
            fp.convert(x, fp.FP32, self.image.fmt))

    def add(self, a, b):
        return a + b if self.fp64 else fp.add(a, b)

    def mul(self, a, b):
        return a * b if self.fp64 else fp.multiply(a, b)

    def dot(self, a, b, indices=None):
        products = [self.mul(x, y) for x, y in zip(a, b)]
        return math.fsum(products) if self.fp64 else contexts(products, indices)

    def observe(self, name, values):
        self.observations.append((name, list(values)))
        return values

    def project(self, x, weights, bias=None):
        x = [self.narrow(v) for v in x]
        result = [self.dot(x, [self.expand(v) for v in row]) for row in weights]
        return result if bias is None else [self.add(x, self.expand(b)) for x, b in zip(result, bias)]

    def norm(self, x, gamma):
        if not self.fp64:
            return norm_reference(x, gamma, self.image.mode == 1)
        inverse = 1 / math.sqrt(math.fsum(v * v for v in x) / len(x) + 1e-6)
        return [v * inverse * self.expand(g) for v, g in zip(x, gamma)]

    def rope(self, values, position):
        result = list(values)
        d = self.g.head_dim
        for head in range(len(values) // d):
            for j in range(d // 2):
                first, second = head * d + j, head * d + j + d // 2
                if self.fp64:
                    angle = position * (1000000 ** (-2 * j / d))
                    sine, cosine = math.sin(angle), math.cos(angle)
                    negative = -self.mul(values[second], sine)
                else:
                    angle = fp.multiply(fp.rounded(position), frequency(j, d))
                    sine, cosine, error = fp.sincos32(angle)
                    if error:
                        raise ArithmeticError("reference RoPE range")
                    negative = self.mul(values[second], sine) ^ fp.FP32.sign
                result[first] = self.add(self.mul(values[first], cosine), negative)
                result[second] = self.add(self.mul(values[second], cosine), self.mul(values[first], sine))
        return [self.narrow(v) for v in result]

    def token(self, token, position, prefix):
        g, image = self.g, self.image
        residual = [self.expand(x) for x in image.embedding[token]]
        kv = []
        for layer in range(g.layers):
            label = f"layer{layer}."
            norm = self.observe(label + "attention_norm", self.norm(residual, image.norms[5, layer]))
            q, k, v = [self.observe(label + name, self.project(
                norm, image.weights[layer, index], image.biases[layer, index]))
                for index, name in enumerate(("q", "k", "v"))]
            q = self.observe(label + "rope_q", self.rope(q, position))
            k = self.observe(label + "rope_k", self.rope(k, position))
            v = [self.narrow(x) for x in v]
            kv.append((k, v))
            visible = [state[layer] for state in prefix] + [(k, v)]
            scale = (1 / math.sqrt(g.head_dim) if self.fp64 else fp.divide(
                fp.rounded(1), fp.sqrt(fp.rounded(g.head_dim))))
            attention = []
            for head in range(g.query_heads):
                kh = head // (g.query_heads // g.kv_heads)
                begin, end = kh * g.head_dim, (kh + 1) * g.head_dim
                scores = [self.mul(self.dot(q[head * g.head_dim:(head + 1) * g.head_dim],
                                          key[begin:end]), scale) for key, _ in visible]
                maximum = max(scores, key=(None if self.fp64 else fp.as_float))
                if self.fp64:
                    exps = [math.exp(score - maximum) for score in scores]
                    total = math.fsum(exps)
                    probabilities = [self.narrow(x / total) for x in exps]
                else:
                    exps = [fp.exp32(fp.add(score, maximum ^ fp.FP32.sign)) for score in scores]
                    total = 0
                    for x in exps:
                        total = fp.add(total, x)
                    probabilities = [self.narrow(fp.divide(x, total)) for x in exps]
                attention.extend([self.dot(probabilities, [value[begin + j] for _, value in visible])
                                  for j in range(g.head_dim)])
            self.observe(label + "attention", attention)
            projected = self.observe(label + "o", self.project(attention, image.weights[layer, 3]))
            residual = [self.add(x, y) for x, y in zip(residual, projected)]
            norm = self.observe(label + "ffn_norm", self.norm(residual, image.norms[6, layer]))
            gate, up = [self.observe(label + name, self.project(norm, image.weights[layer, index]))
                        for index, name in ((4, "gate"), (5, "up"))]
            if self.fp64:
                activation = [x / (1 + math.exp(-x)) * y for x, y in zip(gate, up)]
            else:
                activation = [swiglu_reference(x, y, image.mode == 1)[0] for x, y in zip(gate, up)]
            self.observe(label + "swiglu", activation)
            down = self.observe(label + "down", self.project(activation, image.weights[layer, 6]))
            residual = [self.add(x, y) for x, y in zip(residual, down)]
        norm = self.observe("final_norm", self.norm(residual, image.norms[7, 0]))
        logits = self.observe("logits", self.project(norm, image.embedding))
        target = max(range(g.vocabulary), key=lambda i: logits[i] if self.fp64 else fp.as_float(logits[i]))
        return logits, target, kv
