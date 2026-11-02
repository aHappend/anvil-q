"""Sequential mathematical decoder; no RTL-derived state or execution schedule."""

from dataclasses import dataclass
from fractions import Fraction
import random

import reference as fp


@dataclass(frozen=True)
class Geometry:
    hidden: int = 8
    intermediate: int = 8
    q_heads: int = 2
    kv_heads: int = 1
    head_dim: int = 8
    layers: int = 1
    vocabulary: int = 8
    max_sequence: int = 16
    group: int = 8

    @property
    def q_dimension(self):
        return self.q_heads * self.head_dim

    @property
    def kv_dimension(self):
        return self.kv_heads * self.head_dim

    @property
    def maximum(self):
        return max(self.hidden, self.intermediate, self.q_dimension)

    def extents(self, projection):
        return ((self.hidden, self.q_dimension),
                (self.hidden, self.kv_dimension),
                (self.hidden, self.kv_dimension),
                (self.q_dimension, self.hidden),
                (self.hidden, self.intermediate),
                (self.hidden, self.intermediate),
                (self.intermediate, self.hidden))[projection]


class Image:
    def __init__(self, geometry=Geometry(), seed=17):
        self.geometry = geometry
        rng = random.Random(seed)
        self.embeddings = [[fp.encode(Fraction(rng.randrange(-64, 65), 64), 16)
                            for _ in range(geometry.hidden)]
                           for _ in range(geometry.vocabulary)]
        self.quantized, self.zeros, self.scales, self.gammas = {}, {}, {}, {}
        for layer in range(geometry.layers):
            for kind in (5, 6, 12, 13):
                extent = geometry.head_dim if kind >= 12 else geometry.hidden
                self.gammas[layer, kind] = [
                    fp.encode(Fraction(rng.randrange(96, 161), 128), 16)
                    for _ in range(extent)]
            for projection in range(7):
                inputs, outputs = geometry.extents(projection)
                self.quantized[layer, projection] = [
                    [rng.randrange(4, 13) for _ in range(inputs)]
                    for _ in range(outputs)]
                self.zeros[layer, projection] = [
                    [rng.randrange(7, 10) for _ in range(inputs // geometry.group)]
                    for _ in range(outputs)]
                self.scales[layer, projection] = [
                    [fp.encode(Fraction(rng.randrange(1, 5), 128), 16)
                     for _ in range(inputs // geometry.group)]
                    for _ in range(outputs)]
        self.gammas[0, 7] = [fp.encode(Fraction(rng.randrange(96, 161), 128), 16)
                            for _ in range(geometry.hidden)]

    def linear(self, layer, projection, activation, logits=False):
        geometry = self.geometry
        inputs = len(activation)
        rows = self.embeddings if logits else self.quantized[layer, projection]
        output = []
        for row_index, row in enumerate(rows):
            accumulator = 0
            for base in range(0, inputs, 256):
                length = min(256, inputs - base)
                products = []
                for coordinate in range(base, base + length):
                    if logits:
                        weight = row[coordinate] << 16
                    else:
                        group = coordinate // geometry.group
                        delta = row[coordinate] - self.zeros[layer, projection][row_index][group]
                        scale = self.scales[layer, projection][row_index][group]
                        weight = fp.multiply(fp.encode(delta), scale << 16)
                    products.append(fp.multiply(weight, activation[coordinate] << 16))
                products += [0] * (256 - length)
                accumulator = fp.add(accumulator, fp.balanced_sum(products))
            output.append(accumulator if logits else fp.bf16(accumulator))
        return output

    def memory_tables(self):
        g = self.geometry
        blocks = (g.maximum + 7) // 8
        embeddings = [item for row in self.embeddings for item in row]
        qweight = [0] * (g.layers * 7 * g.maximum * blocks)
        zeros = [0] * len(qweight)
        scales = [0] * (g.layers * 7 * g.maximum * g.maximum)
        gamma = [0] * (g.layers * 16 * g.maximum)
        shifts = (0, 16, 4, 20, 8, 24, 12, 28)
        for layer in range(g.layers):
            for projection in range(7):
                inputs, outputs = g.extents(projection)
                for row in range(outputs):
                    for coordinate in range(inputs):
                        offset = ((layer * 7 + projection) * g.maximum + coordinate) * blocks + row // 8
                        qweight[offset] |= self.quantized[layer, projection][row][coordinate] << shifts[row % 8]
                    for group in range(inputs // g.group):
                        offset = ((layer * 7 + projection) * g.maximum + group) * blocks + row // 8
                        zeros[offset] |= self.zeros[layer, projection][row][group] << shifts[row % 8]
                        scale_offset = ((layer * 7 + projection) * g.maximum + group) * g.maximum + row
                        scales[scale_offset] = self.scales[layer, projection][row][group]
            for kind in (5, 6, 7, 12, 13):
                if (layer, kind) in self.gammas:
                    for coordinate, value in enumerate(self.gammas[layer, kind]):
                        gamma[(layer * 16 + kind) * g.maximum + coordinate] = value
        rope = []
        for position in range(g.max_sequence):
            c, s = fp.coefficients(g.head_dim, position)
            rope.extend(value for pair in zip(c, s) for value in pair)
        return {"embedding": embeddings, "qweight": qweight, "zero": zeros,
                "scale": scales, "gamma": gamma, "rope": rope}


def rmsnorm(data, gamma):
    sum_squares = fp.balanced_sum(fp.multiply(value << 16, value << 16) for value in data)
    mean = fp.divide(sum_squares, fp.encode(len(data)))
    reciprocal = fp.divide(0x3F800000, fp.sqrt32(fp.add(mean, 0x358637BD)))
    unit = [fp.bf16(fp.multiply(value << 16, reciprocal)) for value in data]
    return [fp.bf16(fp.multiply(u << 16, g << 16)) for u, g in zip(unit, gamma)]


def residual(a, b):
    return [fp.bf16(fp.add(x << 16, y << 16)) for x, y in zip(a, b)]


class Decoder:
    def __init__(self, image):
        self.image = image
        self.keys, self.values = {}, {}
        self.maximum_absolute_score = 0

    def evaluate(self, token, position):
        image, g = self.image, self.image.geometry
        if not 0 <= token < g.vocabulary or not 0 <= position < g.max_sequence:
            raise ValueError("illegal decoder input")
        scratch, stages = {}, {}
        initial = list(image.embeddings[token])
        hidden = initial
        cosine, sine = fp.coefficients(g.head_dim, position)
        for layer in range(g.layers):
            scratch[0] = hidden
            scratch[1] = rmsnorm(hidden, image.gammas[layer, 5])
            raw_q = image.linear(layer, 0, scratch[1])
            raw_k = image.linear(layer, 1, scratch[1])
            scratch[4] = image.linear(layer, 2, scratch[1])
            scratch[2], scratch[3] = [], []
            for head in range(g.q_heads):
                start = head * g.head_dim
                scratch[2].extend(fp.qknorm(raw_q[start:start + g.head_dim],
                                          image.gammas[layer, 12], cosine, sine, position))
            for head in range(g.kv_heads):
                start = head * g.head_dim
                scratch[3].extend(fp.qknorm(raw_k[start:start + g.head_dim],
                                          image.gammas[layer, 13], cosine, sine, position))
            self.keys[layer, position] = list(scratch[3])
            self.values[layer, position] = list(scratch[4])
            scratch[5] = self.attention(layer, position, scratch[2])
            scratch[6] = image.linear(layer, 3, scratch[5])
            scratch[7] = residual(hidden, scratch[6])
            scratch[8] = rmsnorm(scratch[7], image.gammas[layer, 6])
            scratch[9] = image.linear(layer, 4, scratch[8])
            scratch[10] = image.linear(layer, 5, scratch[8])
            activated = [fp.bf16(fp.silu32(x << 16)) for x in scratch[9]]
            scratch[11] = [fp.bf16(fp.multiply(x << 16, y << 16))
                           for x, y in zip(activated, scratch[10])]
            scratch[12] = image.linear(layer, 6, scratch[11])
            hidden = residual(scratch[7], scratch[12])
            scratch[0] = hidden
            stages[layer] = {slot: list(data) for slot, data in scratch.items()}
        scratch[14] = rmsnorm(hidden, image.gammas[0, 7])
        stages[g.layers - 1][14] = list(scratch[14])
        logits = image.linear(0, 0, scratch[14], logits=True)
        argmax = max(range(g.vocabulary), key=lambda index: (fp.decode(logits[index]), -index))
        return {"initial": initial, "stages": stages, "logits": logits, "argmax": argmax,
                "keys": [self.keys[layer, position] for layer in range(g.layers)],
                "values": [self.values[layer, position] for layer in range(g.layers)]}

    def attention(self, layer, position, query):
        g = self.image.geometry
        scale = fp.divide(0x3F800000, fp.sqrt32(fp.encode(g.head_dim)))
        contexts = []
        for head in range(g.q_heads):
            kv_head = head // (g.q_heads // g.kv_heads)
            scores = []
            for past in range(position + 1):
                key = self.keys[layer, past]
                products = [fp.multiply(query[head * g.head_dim + coordinate] << 16,
                                        key[kv_head * g.head_dim + coordinate] << 16)
                            for coordinate in range(g.head_dim)]
                scores.append(fp.multiply(fp.balanced_sum(products), scale))
            self.maximum_absolute_score = max(
                self.maximum_absolute_score, *(score & 0x7FFFFFFF for score in scores))
            maximum = max(scores, key=fp.decode)
            weights = [fp.exp32(fp.subtract(score, maximum)) for score in scores]
            denominator = 0
            numerators = [0] * g.head_dim
            for past, weight in enumerate(weights):
                denominator = fp.add(denominator, weight)
                values = self.values[layer, past]
                for coordinate in range(g.head_dim):
                    product = fp.multiply(values[kv_head * g.head_dim + coordinate] << 16,
                                          weight)
                    numerators[coordinate] = fp.add(numerators[coordinate], product)
            contexts.extend(fp.bf16(fp.divide(numerator, denominator)) for numerator in numerators)
        return contexts
