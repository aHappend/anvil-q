"""Memory-ABI fixture and independent compact decoder interpreter."""

from fractions import Fraction
import math
import random

from ieee import binary, bits_float, convert, dot, exact, float_bits, pack, sqrt
from cache_reference import decode, encode


class Fixture:
    def __init__(self, seed=17, fmt="bf16", hidden=16, intermediate=24,
                 heads=8, kv_heads=1, head_dim=2, layers=1, vocab=3, awq=False,
                 cache_mode=0, fp8=0, affine=0, check_budget=None):
        self.check_budget = check_budget or (lambda: None)
        self.seed, self.fmt = seed, fmt
        self.h, self.i, self.qh, self.kh, self.d = hidden, intermediate, heads, kv_heads, head_dim
        self.layers, self.vocab = layers, vocab
        self.cache_mode, self.fp8, self.affine = cache_mode, fp8, affine
        self.memory, self.writes, self.logits = {}, [], []
        self.rng = random.Random(seed)
        self.weights = {}
        self.cache = {}
        for token in range(vocab):
            self.check_budget()
            for col in range(hidden):
                self.memory[(0, 0, 0, token, col)] = self.sample(16)
        for layer in range(layers):
            self.check_budget()
            for kind in (5, 6, 7):
                for col in range(hidden):
                    self.memory[(kind, 0 if kind == 7 else layer, 0, 0, col)] = (
                        self.raw(Fraction(1) + Fraction(self.rng.choice((-1, 0, 1)), 64)))
            for projection in range(7):
                rows = kv_heads * head_dim if projection in (1, 2) else intermediate if projection in (4, 5) else hidden
                cols = intermediate if projection == 6 else hidden
                values = []
                for _ in range(rows):
                    self.check_budget()
                    values.append([self.sample(256) for _ in range(cols)])
                self.weights[layer, projection] = values
                for col in range(cols):
                    for row in range(0, rows, 2):
                        self.memory[(1, layer, projection, col, row // 2)] = (
                            values[row][col] | ((values[row + 1][col] if row + 1 < rows else 0) << 16))
                if projection < 3:
                    for row in range(rows):
                        self.memory[(4, layer, projection, 0, row)] = self.sample(1024)
        if awq:
            shifts = [0, 16, 4, 20, 8, 24, 12, 28]
            for (layer, projection), values in self.weights.items():
                self.check_budget()
                rows, cols = len(values), len(values[0])
                qs = [[self.rng.randrange(16) for _ in range(cols)] for _ in range(rows)]
                zeros = [[self.rng.randrange(5, 11) for _ in range((cols + 7) // 8)] for _ in range(rows)]
                for col in range(cols):
                    for base in range(0, rows, 8):
                        word = sum(qs[row][col] << shifts[row % 8] for row in range(base, min(base + 8, rows)))
                        self.memory[1, layer, projection, col, base // 8] = word
                for group in range((cols + 7) // 8):
                    for base in range(0, rows, 8):
                        word = sum(zeros[row][group] << shifts[row % 8]
                                   for row in range(base, min(base + 8, rows)))
                        self.memory[2, layer, projection, group, base // 8] = word
                    for row in range(rows):
                        self.memory[3, layer, projection, group, row] = pack(Fraction(1, 256), "fp16")[0]
                for row in range(rows):
                    for col in range(cols):
                        values[row][col] = self.raw(Fraction(qs[row][col] - zeros[row][col // 8], 256))

    def raw(self, value):
        return pack(value, self.fmt)[0]

    def sample(self, denominator):
        return self.raw(Fraction(self.rng.choice((-7, -5, -3, -1, 1, 3, 5, 7)), denominator))

    def wide(self, value):
        return convert(value, self.fmt, "fp32", True)[0]

    def narrow(self, value):
        return convert(value, "fp32", self.fmt)[0]

    def write(self, key, value):
        self.memory[key] = value
        self.writes.append((key, value))

    def scratch(self, slot, values):
        for col, value in enumerate(values):
            self.write((8, 0, 0, slot, col), value)
        return values

    def norm(self, values, layer, mode):
        total = 0
        for value in values:
            square = binary("mul", self.wide(value), self.wide(value))[0]
            total = binary("add", total, square)[0]
        mean = binary("div", total, pack(Fraction(len(values)))[0])[0]
        denominator = sqrt(binary("add", mean, float_bits(1e-6))[0])[0]
        reciprocal = binary("div", 0x3f800000, denominator)[0]
        kind = (5, 6, 7)[mode]
        result = []
        for col, value in enumerate(values):
            gamma = self.memory[kind, 0 if kind == 7 else layer, 0, 0, col]
            scaled = binary("mul", self.wide(value), self.wide(gamma))[0]
            result.append(self.narrow(binary("mul", scaled, reciprocal)[0]))
        return self.scratch((1, 8, 14)[mode], result)

    def projection(self, values, layer, projection):
        result = []
        for row, weights in enumerate(self.weights[layer, projection]):
            self.check_budget()
            total = 0
            for index in range(0, len(values), 8):
                a = values[index:index + 8]
                w = weights[index:index + 8]
                mask = (1 << len(a)) - 1
                reduced = dot(a + [0] * (8 - len(a)), w + [0] * (8 - len(w)), mask, self.fmt)[0]
                total = binary("add", total, reduced)[0]
            if projection < 3:
                total = binary("add", total, self.wide(self.memory[4, layer, projection, 0, row]))[0]
            result.append(self.narrow(total))
        return self.scratch((2, 3, 4, 6, 9, 10, 12)[projection], result)

    def rope(self, values, position, slot):
        result = list(values)
        half = self.d // 2
        for base in range(0, len(values), self.d):
            for pair in range(half):
                angle = position / (1000000.0 ** (2 * pair / self.d))
                cosine, sine = float_bits(math.cos(angle)), float_bits(math.sin(angle))
                self.memory[(11, 0, 0, position, 2 * pair)] = cosine
                self.memory[(11, 0, 0, position, 2 * pair + 1)] = sine
                x, y = self.wide(values[base + pair]), self.wide(values[base + pair + half])
                xc, ys = binary("mul", x, cosine)[0], binary("mul", y, sine)[0]
                yc, xs = binary("mul", y, cosine)[0], binary("mul", x, sine)[0]
                result[base + pair] = self.narrow(binary("add", xc, ys ^ 0x80000000)[0])
                result[base + pair + half] = self.narrow(binary("add", yc, xs)[0])
                self.write((8, 0, 0, slot, base + pair), result[base + pair])
                self.write((8, 0, 0, slot, base + pair + half), result[base + pair + half])
        return result

    def attention(self, query, key, value, layer, position):
        cached = []
        for kind, vector in ((9, key), (10, value)):
            decoded = []
            for head in range(self.kh):
                group = 2 if not self.cache_mode else 32 if self.cache_mode == 1 else 64
                blocks = (self.d + group - 1) // group
                for block, dimension in enumerate(range(0, self.d, group)):
                    values = vector[head * self.d + dimension:head * self.d + min(dimension + group, self.d)]
                    words = encode(values, self.fmt, self.cache_mode, self.fp8, self.affine)
                    decoded.extend(decode(words, len(values), self.fmt, self.cache_mode, self.fp8, self.affine))
                    logical_block = head * blocks + block
                    if not self.cache_mode:
                        self.write((kind, layer, 0, position, logical_block), words[0])
                    else:
                        self.write((14 + kind - 9, layer, 0, position, logical_block), words[0])
                        for word, payload in enumerate(words[1:]):
                            self.write((12 + kind - 9, layer, 0, position, logical_block * 8 + word), payload)
            cached.append(decoded)
        self.cache[layer, position] = tuple(cached)
        result = []
        root = sqrt(pack(Fraction(self.d))[0])[0]
        for head in range(self.qh):
            self.check_budget()
            kv = head // 8
            scores = []
            for time in range(position + 1):
                prior_key = self.cache[layer, time][0]
                total = 0
                for dimension in range(self.d):
                    term = binary("mul", self.wide(query[head * self.d + dimension]),
                                  self.wide(prior_key[kv * self.d + dimension]))[0]
                    total = binary("add", total, term)[0]
                scores.append(binary("div", total, root)[0])
            maximum = max(scores, key=bits_float)
            exponentials = [float_bits(math.exp(bits_float(binary("add", score, maximum ^ 0x80000000)[0])))
                            for score in scores]
            for component in range(self.d):
                self.check_budget()
                denominator, total = 0, 0
                for time, exponential in enumerate(exponentials):
                    denominator = binary("add", denominator, exponential)[0]
                    prior_value = self.cache[layer, time][1][kv * self.d + component]
                    total = binary("add", total, binary("mul", self.wide(prior_value), exponential)[0])[0]
                result.append(self.narrow(binary("div", total, denominator)[0]))
        return self.scratch(5, result)

    def residual(self, left, right, slot):
        return self.scratch(slot, [self.narrow(binary("add", self.wide(a), self.wide(b))[0])
                                   for a, b in zip(left, right)])

    def silu_product(self, gate, up):
        result = []
        for g, u in zip(gate, up):
            x = self.wide(g)
            exponential = float_bits(math.exp(-abs(bits_float(x))))
            denominator = binary("add", 0x3f800000, exponential)[0]
            numerator = binary("mul", x, exponential)[0] if x >> 31 else x
            silu = binary("div", numerator, denominator)[0]
            result.append(self.narrow(binary("mul", silu, self.wide(u))[0]))
        return self.scratch(11, result)

    def token(self, token=0, position=0):
        values = self.scratch(0, [self.memory[0, 0, 0, token, col] for col in range(self.h)])
        for layer in range(self.layers):
            self.check_budget()
            normalized = self.norm(values, layer, 0)
            query = self.projection(normalized, layer, 0)
            key = self.projection(normalized, layer, 1)
            value = self.projection(normalized, layer, 2)
            query = self.rope(query, position, 2)
            key = self.rope(key, position, 3)
            context = self.attention(query, key, value, layer, position)
            projected = self.projection(context, layer, 3)
            residual = self.residual(values, projected, 7)
            normalized = self.norm(residual, layer, 1)
            gate = self.projection(normalized, layer, 4)
            up = self.projection(normalized, layer, 5)
            mixed = self.silu_product(gate, up)
            down = self.projection(mixed, layer, 6)
            values = self.residual(residual, down, 0)
        final = self.norm(values, 0, 2)
        logits = []
        for row in range(self.vocab):
            total = 0
            for col, activation in enumerate(final):
                weight = self.memory[0, 0, 0, row, col]
                term = binary("mul", self.wide(activation), self.wide(weight))[0]
                total = binary("add", total, term)[0]
            logits.append(total)
        self.logits.append(logits)
        return logits


class FP64Fixture(Fixture):
    """Unrounded mathematical decoder using exactly the represented input image.

    Unlike the binary32 ABI interpreter, this path retains Python binary64
    activations throughout the decoder and uses math.exp/sqrt directly.
    """

    def wide(self, value):
        return bits_float(super().wide(value))

    def scratch(self, slot, values):
        return values

    def norm(self, values, layer, mode):
        reciprocal = 1.0 / math.sqrt(sum(x * x for x in values) / len(values) + 1e-6)
        kind = (5, 6, 7)[mode]
        return [x * self.wide(self.memory[kind, 0 if kind == 7 else layer, 0, 0, col]) * reciprocal
                for col, x in enumerate(values)]

    def projection(self, values, layer, projection):
        result = []
        for row, weights in enumerate(self.weights[layer, projection]):
            self.check_budget()
            total = sum(x * self.wide(w) for x, w in zip(values, weights))
            if projection < 3:
                total += self.wide(self.memory[4, layer, projection, 0, row])
            result.append(total)
        return result

    def rope(self, values, position, slot):
        result = list(values)
        half = self.d // 2
        for base in range(0, len(values), self.d):
            for pair in range(half):
                angle = position / (1000000.0 ** (2 * pair / self.d))
                cosine, sine = math.cos(angle), math.sin(angle)
                x, y = values[base + pair], values[base + pair + half]
                result[base + pair] = x * cosine - y * sine
                result[base + pair + half] = x * sine + y * cosine
        return result

    def attention(self, query, key, value, layer, position):
        self.cache[layer, position] = list(key), list(value)
        result = []
        for head in range(self.qh):
            self.check_budget()
            kv = head // 8
            scores = [sum(query[head * self.d + d] * self.cache[layer, t][0][kv * self.d + d]
                          for d in range(self.d)) / math.sqrt(self.d)
                      for t in range(position + 1)]
            maximum = max(scores)
            probabilities = [math.exp(score - maximum) for score in scores]
            denominator = sum(probabilities)
            for d in range(self.d):
                result.append(sum(p * self.cache[layer, t][1][kv * self.d + d]
                                  for t, p in enumerate(probabilities)) / denominator)
        return result

    def residual(self, left, right, slot):
        return [a + b for a, b in zip(left, right)]

    def silu_product(self, gate, up):
        return [(g / (1 + math.exp(-g)) if g >= 0 else
                 g * math.exp(g) / (1 + math.exp(g))) * u for g, u in zip(gate, up)]

    def token(self, token=0, position=0):
        values = [self.wide(self.memory[0, 0, 0, token, col]) for col in range(self.h)]
        for layer in range(self.layers):
            self.check_budget()
            normalized = self.norm(values, layer, 0)
            query, key, value = [self.projection(normalized, layer, p) for p in range(3)]
            query, key = self.rope(query, position, 2), self.rope(key, position, 3)
            context = self.attention(query, key, value, layer, position)
            residual = self.residual(values, self.projection(context, layer, 3), 7)
            normalized = self.norm(residual, layer, 1)
            gate, up = [self.projection(normalized, layer, p) for p in (4, 5)]
            down = self.projection(self.silu_product(gate, up), layer, 6)
            values = self.residual(residual, down, 0)
        final = self.norm(values, 0, 2)
        logits = [sum(x * self.wide(self.memory[0, 0, 0, row, col]) for col, x in enumerate(final))
                  for row in range(self.vocab)]
        self.logits.append(logits)
        return logits
