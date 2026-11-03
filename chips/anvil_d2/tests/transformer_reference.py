"""Integer mathematical target model and synthetic, nonsymmetric weight images.

No RTL, RTL output, simulator state or parent implementation is imported. Tensor
identities are the public native image format. All rounding is integer exact.
"""

from dataclasses import dataclass, replace
from math import isqrt
import random

from reference import bf16_to_q16, dequantize, quantize_group


def signed32(value):
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & (1 << 31) else value


def saturate(value):
    return min((1 << 31) - 1, max(-(1 << 31), value))


def round_boundary(value, shift=16):
    magnitude = abs(value)
    if shift:
        magnitude = (magnitude + (1 << (shift - 1))) >> shift
    return saturate(-magnitude if value < 0 else magnitude)


def trunc_div(numerator, denominator):
    quotient = abs(numerator) // denominator
    return -quotient if numerator < 0 else quotient


def rms(values, gains):
    denominator = isqrt((sum(x*x for x in values) << 32) // len(values) + (1 << 48))
    reciprocal = (1 << 64) // denominator
    return [round_boundary(x*g*reciprocal, 48) for x, g in zip(values, gains)]


def exp_q24(argument):
    if argument >= 0:
        return 1 << 24
    if argument < -(16 << 16):
        return 0
    exponent, remainder = divmod(-argument << 8, 11629080)
    term = total = 1 << 24
    for factorial_index in range(1, 7):
        term = trunc_div(-term*remainder, factorial_index << 24)
        total += term
    return max(0, total) >> exponent


def silu(value):
    exponential = exp_q24(-abs(value))
    sigmoid = ((exponential << 24) if value < 0 else (1 << 48)) // (
        (1 << 24) + exponential)
    return round_boundary(value*sigmoid, 24)


def matvec(matrix, values, shift=16, bias=None):
    if bias is None:
        bias = [0]*len(matrix)
    return [round_boundary(sum(a*b for a, b in zip(row, values)) + (b << shift), shift)
            for row, b in zip(matrix, bias)]


def fp8_roundtrip(values):
    result = []
    for base in range(0, len(values), 128):
        scale, codes = quantize_group(values[base:base+128])
        for code in codes:
            _, bf16, error = dequantize(code, scale)
            q16, qerror = bf16_to_q16(bf16)
            assert not error and not qerror
            result.append(signed32(q16))
    return result


def key(kind, layer, projection, row, column):
    return (kind << 99) | (layer << 67) | (projection << 64) | (row << 32) | column


@dataclass(frozen=True)
class Geometry:
    hidden: int = 8
    intermediate: int = 8
    layers: int = 1
    heads: int = 2
    rank: int = 3
    nope: int = 2
    rope: int = 2
    value: int = 2
    experts: int = 3
    top_k: int = 2
    moe_intermediate: int = 8
    first_dense: int = 1
    vocab: int = 7
    capacity: int = 16
    banks: int = 2
    queue: int = 3


class WeightImage:
    def __init__(self, geometry=Geometry(), seed=17):
        self.geometry = geometry
        self.seed = seed
        self.words = {}
        self.expected_absorption = {}
        rng = random.Random(seed)
        g = geometry

        def matrix(rows, columns, amplitude=8192):
            return [[rng.randrange(-amplitude, amplitude+1) for _ in range(columns)]
                    for _ in range(rows)]

        def store(kind, layer, projection, row, values):
            for column, value in enumerate(values):
                self.words[key(kind, layer, projection, row, column)] = value & 0xFFFFFFFF

        self.embedding = matrix(g.vocab, g.hidden, 49152)
        self.final_gain = [rng.randrange(49152, 81921) for _ in range(g.hidden)]
        for token, row in enumerate(self.embedding):
            store(0, 0, 0, token, row)
        store(7, 0, 0, 0, self.final_gain)
        self.layers = []
        for layer in range(g.layers):
            weights = {
                "attn_gain": [rng.randrange(49152, 81921) for _ in range(g.hidden)],
                "ffn_gain": [rng.randrange(49152, 81921) for _ in range(g.hidden)],
                "down": matrix(g.rank, g.hidden),
                "key_rope": matrix(g.rope, g.hidden),
                "query": [matrix(g.nope, g.hidden) for _ in range(g.heads)],
                "query_rope": [matrix(g.rope, g.hidden) for _ in range(g.heads)],
                "up_key": [matrix(g.nope, g.rank) for _ in range(g.heads)],
                "up_value": [matrix(g.value, g.rank) for _ in range(g.heads)],
                "output": matrix(g.hidden, g.heads*g.value),
                "router": matrix(g.experts, g.hidden),
                "experts": {},
            }
            self.layers.append(weights)
            store(5, layer, 0, 0, weights["attn_gain"])
            store(6, layer, 0, 0, weights["ffn_gain"])
            for name, row_base in (("down", 0), ("key_rope", 0x10000000),
                                   ("output", 0x60000000)):
                for row_index, row in enumerate(weights[name]):
                    store(15, layer, 0, row_base+row_index, row)
            for head in range(g.heads):
                for name, row_base in (("query", 0x20000000),
                                       ("query_rope", 0x30000000),
                                       ("up_key", 0x40000000),
                                       ("up_value", 0x50000000)):
                    for row_index, row in enumerate(weights[name][head]):
                        store(15, layer, 0, row_base+(head << 24)+row_index, row)
            for position in range(g.capacity):
                # Nontrivial exact Q16 rotations, not a floating-point oracle.
                store(15, layer, 6, position,
                      [value for _ in range(g.rope//2) for value in (
                          65536-position*1024, position*2048)])
            for row_index, row in enumerate(weights["router"]):
                store(15, layer, 4, row_index, row)
            for expert in [*range(g.experts+2), 127]:
                width = g.intermediate if expert == 127 else g.moe_intermediate
                expert_weights = {
                    "gate": matrix(width, g.hidden),
                    "up": matrix(width, g.hidden),
                    "down": matrix(g.hidden, width),
                    "bias": [[rng.randrange(-4096, 4097) for _ in range(size)]
                             for size in (width, width, g.hidden)],
                }
                weights["experts"][expert] = expert_weights
                for projection, name in enumerate(("gate", "up", "down")):
                    for row_index, row in enumerate(expert_weights[name]):
                        row_id = (expert << 25) | (projection << 23) | row_index
                        store(15, layer, 5, row_id, row)
                    for row_index, bias in enumerate(expert_weights["bias"][projection]):
                        self.words[key(15, layer, 5, (expert << 25) |
                                       (3 << 23) | row_index, projection)] = bias & 0xFFFFFFFF
            # Compare the exact unrounded absorbed coefficients at public writes.
            for head in range(g.heads):
                a = [[sum(weights["up_key"][head][d][r]*weights["query"][head][d][h]
                          for d in range(g.nope)) for h in range(g.hidden)]
                     for r in range(g.rank)]
                b = [[sum(weights["output"][h][head*g.value+d]*
                          weights["up_value"][head][d][r] for d in range(g.value))
                      for r in range(g.rank)] for h in range(g.hidden)]
                for projection, tensor in ((1, a), (2, b)):
                    for row_index, row in enumerate(tensor):
                        for column, coefficient in enumerate(row):
                            for word in range(3):
                                self.expected_absorption[key(
                                    15, layer, projection, (head << 28)+row_index,
                                    column*3+word)] = (coefficient >> (word*32)) & 0xFFFFFFFF

    def add_mtp(self, fixture="random"):
        g = self.geometry
        native = WeightImage(replace(g, layers=4, first_dense=0), self.seed+1000)
        rng = random.Random(self.seed+2000)
        self.mtp_native = native
        self.mtp_projections = []
        for head in range(4):
            layer = g.layers+head
            gains = [[rng.randrange(49152, 81921) for _ in range(g.hidden)]
                     for _ in range(2)]
            projection = [[rng.randrange(-8192, 8193) for _ in range(2*g.hidden)]
                          for _ in range(g.hidden)]
            if fixture == "reject-first" and head == 0:
                projection = [[1]*g.hidden + [
                    -65536 if column == row else 0 for column in range(g.hidden)]
                              for row in range(g.hidden)]
            self.mtp_projections.append((gains, projection))
            for role, values in enumerate(gains, 1):
                for column, value in enumerate(values):
                    self.words[key(12, layer, role, 0, column)] = value
            for row, values in enumerate(projection):
                for column, value in enumerate(values):
                    self.words[key(12, layer, 0, row, column)] = value & 0xFFFFFFFF
        for address, word in native.words.items():
            kind = address >> 99
            source_layer = (address >> 67) & 0xFFFFFFFF
            projection = (address >> 64) & 7
            row, column = (address >> 32) & 0xFFFFFFFF, address & 0xFFFFFFFF
            layer = g.layers+source_layer
            if kind in (5, 6, 7):
                if kind == 7:
                    for head in range(4):
                        self.words[key(12, g.layers+head, 3, 2, column)] = word
                else:
                    self.words[key(12, layer, 3, kind-5, column)] = word
            elif kind == 15:
                if projection == 0:
                    self.words[key(12, layer, 4, row, column)] = word
                elif projection == 4:
                    self.words[key(12, layer, 4, 0x70000000+row, column)] = word
                elif projection == 5:
                    self.words[key(12, layer, 5, row, column)] = word
                elif projection == 6:
                    # The head uses absolute rather than relative rotary positions.
                    self.words[key(12, layer, 4, 0x80000000+row, column)] = word
        for address, word in native.expected_absorption.items():
            source_layer = (address >> 67) & 0xFFFFFFFF
            projection = (address >> 64) & 7
            row, column = (address >> 32) & 0xFFFFFFFF, address & 0xFFFFFFFF
            mapped_row = (row & 0xF0000000) | ((projection == 2) << 27) | (row & 0x07FFFFFF)
            self.expected_absorption[key(12, g.layers+source_layer, 7, mapped_row, column)] = word

    def external_words(self, fp8):
        words = self.words.copy()
        if fp8:
            for layer, weights in enumerate(self.layers):
                for expert in range(self.geometry.experts):
                    for projection, name in enumerate(("gate", "up", "down")):
                        for row_index, row in enumerate(weights["experts"][expert][name]):
                            row_id = (expert << 25) | (projection << 23) | row_index
                            words.update(packed_group_words(layer, 5, row_id, row))
            if hasattr(self, "mtp_native"):
                for head, weights in enumerate(self.mtp_native.layers):
                    for expert in range(self.geometry.experts):
                        for projection, name in enumerate(("gate", "up", "down")):
                            for row_index, row in enumerate(weights["experts"][expert][name]):
                                row_id = (expert << 25) | (projection << 23) | row_index
                                words.update(packed_group_words(
                                    self.geometry.layers+head, 5, row_id, row))
        return words


def packed_group_words(layer, projection, row, values):
    words = {}
    for base in range(0, len(values), 128):
        scale, codes = quantize_group(values[base:base+128])
        words[key(14, layer, projection, row, base >> 7)] = scale
        for offset in range(0, len(codes), 4):
            words[key(13, layer, projection, row, (base+offset) >> 2)] = sum(
                code << (8*lane) for lane, code in enumerate(codes[offset:offset+4]))
    return words


class Target:
    def __init__(self, image, fp8=False):
        self.image = image
        self.g = image.geometry
        self.fp8 = fp8
        self.cache = [[] for _ in range(self.g.layers)]
        self.raw_cache = [[] for _ in range(self.g.layers)]
        self.last_hidden = None

    def rotate(self, values, position):
        cosine, sine = 65536-position*1024, position*2048
        return [result for x, y in zip(values[::2], values[1::2])
                for result in (round_boundary(x*cosine-y*sine),
                               round_boundary(x*sine+y*cosine))]

    def expert(self, weights, vector, compressed):
        gate, up, down = (weights[name] for name in ("gate", "up", "down"))
        if compressed:
            gate, up, down = ([fp8_roundtrip(row) for row in tensor]
                              for tensor in (gate, up, down))
        gate_values = matvec(gate, vector, bias=weights["bias"][0])
        up_values = matvec(up, vector, bias=weights["bias"][1])
        product = [round_boundary(silu(a)*b) for a, b in zip(gate_values, up_values)]
        return matvec(down, product, bias=weights["bias"][2])

    def process(self, token):
        return self.process_hidden(self.image.embedding[token])

    def process_hidden(self, vector, absolute_position=None):
        g = self.g
        position = len(self.cache[0]) if absolute_position is None else absolute_position
        hidden = list(vector)
        for layer, weights in enumerate(self.image.layers):
            norm = rms(hidden, weights["attn_gain"])
            latent = matvec(weights["down"], norm)
            rope_key = self.rotate(matvec(weights["key_rope"], norm), position)
            self.raw_cache[layer].append([*latent, *rope_key])
            self.cache[layer].append([*(fp8_roundtrip(latent) if self.fp8 else latent),
                                      *rope_key])
            contexts = []
            # Evaluate the unabsorbed equations in arbitrary-precision integers.
            # No intermediate Q16 truncation occurs at the absorbed boundary.
            for head in range(g.heads):
                unrounded_query = [sum(a*b for a, b in zip(row, norm))
                                   for row in weights["query"][head]]
                query = [round_boundary(sum(weights["up_key"][head][d][r]*
                                            unrounded_query[d] for d in range(g.nope)), 32)
                         for r in range(g.rank)]
                query_rope = self.rotate(matvec(weights["query_rope"][head], norm), position)
                query += query_rope
                scores = [saturate(trunc_div(sum(a*b for a, b in zip(query, cache)),
                                             isqrt((g.nope+g.rope) << 32)))
                          for cache in self.cache[layer]]
                maximum = max(scores)
                probabilities = [exp_q24(score-maximum) for score in scores]
                denominator = sum(probabilities)
                context = []
                for component in range(g.rank):
                    exact = sum(p*cache[component] for p, cache in zip(
                        probabilities, self.cache[layer]))
                    magnitude = (2*abs(exact)+denominator)//(2*denominator)
                    context.append(saturate(-magnitude if exact < 0 else magnitude))
                contexts.append(context)
            attention = []
            for output in range(g.hidden):
                exact = sum(weights["output"][output][head*g.value+d] *
                            weights["up_value"][head][d][r]*contexts[head][r]
                            for head in range(g.heads) for d in range(g.value)
                            for r in range(g.rank))
                attention.append(round_boundary(exact, 32))
            hidden = [saturate(x+a) for x, a in zip(hidden, attention)]
            norm = rms(hidden, weights["ffn_gain"])
            if layer < g.first_dense:
                ffn = self.expert(weights["experts"][127], norm, False)
            else:
                scores = matvec(weights["router"], norm)
                exponentials = [exp_q24(score-max(scores)) for score in scores]
                probabilities = [(value << 24)//sum(exponentials) for value in exponentials]
                winners = sorted(range(g.experts), key=lambda e: (-scores[e], e))[:g.top_k]
                total = sum(probabilities[e] for e in winners)
                coefficients = [(probabilities[e] << 24)//total for e in winners]
                for index in range((1 << 24)-sum(coefficients)):
                    coefficients[index] += 1
                outputs = [self.expert(weights["experts"][e], norm, False)
                           for e in (g.experts, g.experts+1)]
                mixture = [(a+b) << 24 for a, b in zip(*outputs)]
                for e, coefficient in zip(winners, coefficients):
                    routed = self.expert(weights["experts"][e], norm, self.fp8)
                    mixture = [a+b*coefficient for a, b in zip(mixture, routed)]
                ffn = [round_boundary(value, 24) for value in mixture]
            hidden = [saturate(x+y) for x, y in zip(hidden, ffn)]
        self.last_raw_hidden = hidden.copy()
        self.last_hidden = rms(hidden, self.image.final_gain)
        return matvec(self.image.embedding, self.last_hidden)

    def expected_cache_words(self):
        words = {}
        for layer, rows in enumerate(self.raw_cache):
            for position, row in enumerate(rows):
                if self.fp8:
                    words.update(packed_group_words(layer, 3, position, row[:self.g.rank]))
                for column, value in enumerate(row):
                    if not self.fp8 or column >= self.g.rank:
                        words[key(15, layer, 3, position, column)] = value & 0xFFFFFFFF
        return words


def argmax(logits):
    return max(range(len(logits)), key=lambda index: (logits[index], -index))
