"""Independent integer equations and immutable synthetic decoder fixtures.

Only public tensor coordinates and the frozen mathematical contract are used.
This module does not import product RTL, host mapping utilities or parent RTL.
"""

from dataclasses import asdict, dataclass
from decimal import Decimal, localcontext, ROUND_HALF_UP
from fractions import Fraction
from math import isqrt
import hashlib
import json
import random
import struct


def sat32(x):
    return min(2147483647, max(-2147483648, x))


def rounded_div(x, denominator):
    if denominator <= 0:
        raise ValueError("nonpositive denominator")
    return (-1 if x < 0 else 1) * ((abs(x) + denominator // 2) // denominator)


def rshift(x, bits):
    return rounded_div(x, 1 << bits) if bits else x


def f16_fraction(bits):
    # struct implements the external IEEE source format, not a DUT algorithm.
    value = struct.unpack(">e", struct.pack(">H", bits))[0]
    return Fraction(value)


def f16_q16(bits, scale=False):
    if bits & 0x7c00 == 0x7c00:
        raise ValueError("NaN/Inf")
    value = f16_fraction(bits)
    if scale and value < 0:
        raise ValueError("negative scale")
    q = rounded_div(value.numerator << 16, value.denominator)
    return q if scale else sat32(q)


def half(value):
    return struct.unpack(">H", struct.pack(">e", value))[0]


def exp_q24(x):
    if x < -1048576:
        return 0
    if x >= 0:
        return 16777216
    n, residue = divmod((-x) << 8, 11629080)
    terms = [16777216]
    for j in range(1, 7):
        previous = terms[-1]
        magnitude = ((abs(previous) * residue) // (1 << 24)) // j
        terms.append(-magnitude if previous > 0 else magnitude if previous < 0 else 0)
    return max(0, sum(terms)) >> n


def silu(x):
    e = exp_q24(-abs(x))
    sigmoid = ((1 << 48) if x >= 0 else (e << 24)) // ((1 << 24) + e)
    return sat32(rshift(x * sigmoid, 24))


def rmsnorm(values, gamma):
    mean = (sum(x * x for x in values) << 32) // len(values) + 18446744073710
    reciprocal = (1 << 64) // isqrt(mean)
    return [sat32(rshift(x * g * reciprocal, 48)) for x, g in zip(values, gamma)]


def rope_samples(position, dim):
    # 80-digit Decimal Taylor evaluation, independent of host libm and RTL.
    with localcontext() as ctx:
        ctx.prec = 80
        pi = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286")
        result = []
        for pair in range(dim // 2):
            angle = Decimal(position) * (-(Decimal(2 * pair) / dim) * Decimal(1000000).ln()).exp()
            angle %= 2 * pi
            if angle > pi:
                angle -= 2 * pi
            sine, cosine = angle, Decimal(1)
            st, ct = sine, cosine
            for n in range(1, 180):
                st *= -angle * angle / ((2 * n) * (2 * n + 1))
                ct *= -angle * angle / ((2 * n - 1) * (2 * n))
                sine += st
                cosine += ct
                if max(abs(st), abs(ct)) < Decimal("1e-75"):
                    break
            result.extend(int((v * (1 << 30)).to_integral_value(rounding=ROUND_HALF_UP))
                          for v in (cosine, sine))
        return result


def rotate(values, dim, coefficients):
    out = list(values)
    for head in range(len(values) // dim):
        for i in range(dim // 2):
            a, b = values[head * dim + i], values[head * dim + i + dim // 2]
            c, s = coefficients[2 * i:2 * i + 2]
            out[head * dim + i] = sat32(rshift(a * c - b * s, 30))
            out[head * dim + i + dim // 2] = sat32(rshift(b * c + a * s, 30))
    return out


def encode_block(values, mode, asymmetric=False):
    if mode == 0:
        return list(values), 0, list(values)
    limit = 127 if mode == 1 else 7
    for exponent in range((25 if mode == 1 else 32 if asymmetric else 29) + 1):
        rounded = [rshift(x, exponent) for x in values]
        if asymmetric:
            feasible = [z for z in range(-8, 8) if all(-8 <= q + z <= 7 for q in rounded)]
            if not feasible:
                continue
            z = min(feasible, key=lambda x: (abs(x), x))
        else:
            z = 0
            if max(map(abs, values)) > limit * (1 << exponent):
                continue
        codes = [min(limit, max(-8 if asymmetric else -limit, q + z)) for q in rounded]
        decoded = [sat32((q - z) << exponent) for q in codes]
        for x, y in zip(values, decoded):
            if exponent == 0:
                assert x == y
            elif -2147483648 < (rshift(x, exponent) << exponent) < 2147483647:
                assert abs(x - y) <= 1 << (exponent - 1)
        return codes, exponent | ((z & 15) << 8), decoded
    raise ValueError("unrepresentable block")


@dataclass(frozen=True)
class Geometry:
    PROFILE: int = 3
    NUM_LAYERS: int = 1
    HIDDEN_SIZE: int = 16
    INTERMEDIATE_SIZE: int = 24
    NUM_Q_HEADS: int = 8
    NUM_KV_HEADS: int = 1
    HEAD_DIM: int = 2
    GROUP_SIZE: int = 8
    AWQ_BITS: int = 4
    VOCAB_SIZE: int = 17
    MAX_SEQ_LEN: int = 9
    BANKS: int = 8
    CACHE_MODE: int = 0
    INT4_ASYM: int = 0
    CACHE_BLOCK: int = 1
    QUEUE_DEPTH: int = 3
    TILE_K: int = 24
    TILE_ROWS: int = 3

    def dimensions(self, projection):
        return ((self.INTERMEDIATE_SIZE if projection == 6 else self.HIDDEN_SIZE),
                (self.NUM_KV_HEADS * self.HEAD_DIM if projection in (1, 2)
                 else self.INTERMEDIATE_SIZE if projection in (4, 5) else self.HIDDEN_SIZE))

    @property
    def capacity(self):
        return (1 if not self.CACHE_MODE else
                (64 if self.CACHE_MODE == 2 else 32) if self.PROFILE == 3
                else self.CACHE_BLOCK)

    @property
    def blocks(self):
        return (self.HEAD_DIM + self.capacity - 1) // self.capacity


class Fixture:
    """Frozen public tensors, not official weights or trained-model reasoning."""

    def __init__(self, geometry, seed):
        self.g = geometry
        self.seed = seed
        rng = random.Random(seed)
        g = geometry
        self.memory = {}
        self.weights = {}
        self.gamma = {}
        self.bias = {}
        self.embeddings = []

        def put(kind, layer, proj, row, col, value):
            self.memory[kind, layer, proj, row, col] = value & 0xffffffff

        for token in range(g.VOCAB_SIZE):
            row = [half(rng.randint(-16, 16) / 32) for _ in range(g.HIDDEN_SIZE)]
            self.embeddings.append([f16_q16(h) for h in row])
            for col, h in enumerate(row):
                put(0, 0, 0, token, col, h)
        for layer in range(g.NUM_LAYERS):
            for kind in (5, 6):
                row = [half(rng.randint(24, 40) / 32) for _ in range(g.HIDDEN_SIZE)]
                self.gamma[layer, kind] = [f16_q16(h) for h in row]
                for col, h in enumerate(row):
                    put(kind, layer, 0, 0, col, h)
            for projection in range(7):
                inputs, outputs = g.dimensions(projection)
                q = [[rng.randrange(16) for _ in range(outputs)] for _ in range(inputs)]
                z = [[rng.randrange(4, 12) for _ in range(outputs)]
                     for _ in range(inputs // g.GROUP_SIZE)]
                scales = [[half(rng.randint(1, 4) / 1024) for _ in range(outputs)]
                          for _ in range(inputs // g.GROUP_SIZE)]
                self.weights[layer, projection] = [
                    [(q[i][o] - z[i // g.GROUP_SIZE][o]) *
                     f16_q16(scales[i // g.GROUP_SIZE][o], scale=True) for i in range(inputs)]
                    for o in range(outputs)]
                offsets = [0, 16, 4, 20, 8, 24, 12, 28]
                for kind, source in ((1, q), (2, z)):
                    for row, values in enumerate(source):
                        for word in range((outputs + 7) // 8):
                            packed = sum(values[o] << offsets[o % 8]
                                         for o in range(word * 8, min(outputs, (word + 1) * 8)))
                            put(kind, layer, projection, row, word, packed)
                for row, values in enumerate(scales):
                    for col, h in enumerate(values):
                        put(3, layer, projection, row, col, h)
                if projection <= 2:
                    bias = [half(rng.randint(-8, 8) / 256) for _ in range(outputs)]
                    self.bias[layer, projection] = [f16_q16(h) for h in bias]
                    for col, h in enumerate(bias):
                        put(4, layer, projection, 0, col, h)
        row = [half(rng.randint(24, 40) / 32) for _ in range(g.HIDDEN_SIZE)]
        self.gamma[0, 7] = [f16_q16(h) for h in row]
        for col, h in enumerate(row):
            put(7, 0, 0, 0, col, h)
        for pos in range(g.MAX_SEQ_LEN):
            for col, coefficient in enumerate(rope_samples(pos, g.HEAD_DIM)):
                put(11, 0, 0, pos, col, coefficient)

    def oracle(self, tokens, restart_at=None):
        g = self.g
        cache = {}
        writes = []
        logits = []
        current_token = 0

        def write(kind, layer, row, col, value):
            writes.append([current_token, kind, layer, 0, row, col, value & 0xffffffff])

        def scratch(slot, values):
            for col, value in enumerate(values):
                write(8, 0, slot, col, value)
            return values

        def project(layer, p, x):
            values = []
            for row, w in enumerate(self.weights[layer, p]):
                value = sum(a * b for a, b in zip(x, w))
                if p <= 2:
                    value += self.bias[layer, p][row] << 16
                values.append(sat32(rshift(value, 16)))
            return scratch([2, 3, 4, 6, 9, 10, 12][p], values)

        def commit(layer, pos, kind, values):
            decoded = []
            for head in range(g.NUM_KV_HEADS):
                for block in range(g.blocks):
                    start = head * g.HEAD_DIM + block * g.capacity
                    size = min(g.capacity, g.HEAD_DIM - block * g.capacity)
                    codes, metadata, reconstruction = encode_block(
                        values[start:start + size], g.CACHE_MODE, bool(g.INT4_ASYM))
                    decoded.extend(reconstruction)
                    if not g.CACHE_MODE:
                        write(kind, layer, pos, start, codes[0])
                    else:
                        bits = 8 if g.CACHE_MODE == 1 else 4
                        packed = sum((q & ((1 << bits) - 1)) << (i * bits)
                                     for i, q in enumerate(codes))
                        words = (g.capacity * bits + 31) // 32
                        block_index = head * g.blocks + block
                        for word in range(words):
                            write(kind + 3, layer, pos, block_index * words + word,
                                  (packed >> (word * 32)) & 0xffffffff)
                        write(kind + 5, layer, pos, block_index, metadata)
            cache[layer, pos, kind] = decoded

        for current_token, token in enumerate(tokens):
            if current_token == restart_at:
                cache = {}
            pos = current_token - restart_at if restart_at is not None and current_token >= restart_at else current_token
            x = scratch(0, self.embeddings[token])
            for layer in range(g.NUM_LAYERS):
                n = scratch(1, rmsnorm(x, self.gamma[layer, 5]))
                q, k, v = (project(layer, p, n) for p in range(3))
                coeff = rope_samples(pos, g.HEAD_DIM)
                q = scratch(2, rotate(q, g.HEAD_DIM, coeff))
                k = scratch(3, rotate(k, g.HEAD_DIM, coeff))
                commit(layer, pos, 9, k)
                commit(layer, pos, 10, v)
                context = []
                for head in range(g.NUM_Q_HEADS):
                    kvhead = head // (g.NUM_Q_HEADS // g.NUM_KV_HEADS)
                    query = q[head * g.HEAD_DIM:(head + 1) * g.HEAD_DIM]
                    scores = []
                    for t in range(pos + 1):
                        key = cache[layer, t, 9][kvhead * g.HEAD_DIM:(kvhead + 1) * g.HEAD_DIM]
                        scores.append(rounded_div(sum(a * b for a, b in zip(query, key)),
                                                  isqrt(g.HEAD_DIM << 32)))
                    weights = [exp_q24(s - max(scores)) for s in scores]
                    for component in range(g.HEAD_DIM):
                        total = sum(cache[layer, t, 10][kvhead * g.HEAD_DIM + component] * weight
                                    for t, weight in enumerate(weights))
                        context.append(sat32(rounded_div(total, sum(weights))))
                context = scratch(5, context)
                out = project(layer, 3, context)
                residual = scratch(7, [sat32(a + b) for a, b in zip(x, out)])
                n = scratch(8, rmsnorm(residual, self.gamma[layer, 6]))
                gate, up = (project(layer, p, n) for p in (4, 5))
                activated = scratch(11, [sat32(rshift(silu(a) * b, 16)) for a, b in zip(gate, up)])
                down = project(layer, 6, activated)
                x = scratch(0, [sat32(a + b) for a, b in zip(residual, down)])
            final = scratch(14, rmsnorm(x, self.gamma[0, 7]))
            logits.append([sat32(rshift(sum(a * b for a, b in zip(final, embedding)), 16))
                           for embedding in self.embeddings])
        return {"writes": writes, "logits": logits}

    def digest(self):
        serialized = json.dumps({"geometry": asdict(self.g), "seed": self.seed,
                                 "tensors": sorted((list(k), v) for k, v in self.memory.items())},
                                separators=(",", ":")).encode()
        return hashlib.sha256(serialized).hexdigest()


class AdversarialFixture(Fixture):
    """Separate exact-oracle corpus; never used to replace frozen quality inputs."""

    def __init__(self, geometry, seed):
        super().__init__(geometry, seed)
        source = (0x7bff, 0xfbff, 1, 0x8001, 0x3c00, 0xbc00, 0, 0x8000)
        for token, values in enumerate(self.embeddings):
            for col in range(len(values)):
                bits = source[(col + token) % len(source)]
                self.memory[0, 0, 0, token, col] = bits
                values[col] = f16_q16(bits)
        for (layer, kind), values in self.gamma.items():
            for col in range(len(values)):
                bits = source[(col + layer + kind) % len(source)]
                self.memory[kind, layer, 0, 0, col] = bits
                values[col] = f16_q16(bits)
        for (layer, proj), values in self.bias.items():
            for col in range(len(values)):
                bits = source[(col + proj) % len(source)]
                self.memory[4, layer, proj, 0, col] = bits
                values[col] = f16_q16(bits)
        offsets = (0, 16, 4, 20, 8, 24, 12, 28)
        scales = (0x7bff, 1, 0x8000, 0x3c00)
        for (layer, proj), matrix in self.weights.items():
            inputs, outputs = geometry.dimensions(proj)
            for group in range(inputs // geometry.GROUP_SIZE):
                for output in range(outputs):
                    bits = scales[(group + output + proj) % len(scales)]
                    self.memory[3, layer, proj, group, output] = bits
                    scale = f16_q16(bits, scale=True)
                    shift = offsets[output % 8]
                    zero = (self.memory[2, layer, proj, group, output // 8] >> shift) & 15
                    for row in range(group * geometry.GROUP_SIZE,
                                     (group + 1) * geometry.GROUP_SIZE):
                        quantized = (self.memory[1, layer, proj, row, output // 8] >> shift) & 15
                        matrix[output][row] = (quantized - zero) * scale
