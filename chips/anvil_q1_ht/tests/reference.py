"""Independent integer arithmetic and synthetic engineering tensors, not Qwen fixtures."""

import math
import random
import struct
from dataclasses import dataclass


def signed(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value >> (bits - 1) else value


def sat32(value):
    return min((1 << 31) - 1, max(-(1 << 31), value))


def round_div(value, denominator):
    if denominator <= 0:
        raise ValueError("positive denominator required")
    magnitude = (abs(value) + denominator // 2) // denominator
    return -magnitude if value < 0 else magnitude


def round_shift(value, bits):
    return round_div(value, 1 << bits)


def trunc_div(value, denominator):
    return (-1 if value < 0 else 1) * (abs(value) // denominator)


def fp_q16(bits, exponent_bits, fraction_bits, unsigned_scale=False):
    sign = bits >> 15
    exponent = (bits >> fraction_bits) & ((1 << exponent_bits) - 1)
    fraction = bits & ((1 << fraction_bits) - 1)
    if exponent == (1 << exponent_bits) - 1:
        raise ValueError("nonfinite encoding")
    if unsigned_scale and sign and (exponent or fraction):
        raise ValueError("negative scale")
    bias = (1 << (exponent_bits - 1)) - 1
    mantissa = fraction if exponent == 0 else (1 << fraction_bits) + fraction
    shift = (1 - bias if exponent == 0 else exponent - bias) - fraction_bits + 16
    magnitude = mantissa << shift if shift >= 0 else round_shift(mantissa, -shift)
    if unsigned_scale:
        return magnitude
    return sat32(-magnitude if sign else magnitude)


def fp16(bits):
    return fp_q16(bits, 5, 10)


def bf16(bits):
    return fp_q16(bits, 8, 7)


AWQ_SHIFTS = (0, 16, 4, 20, 8, 24, 12, 28)


def pack_awq(values):
    if len(values) % 8:
        raise ValueError("whole packed words required")
    words = []
    for start in range(0, len(values), 8):
        word = sum(values[start + lane] << shift for lane, shift in enumerate(AWQ_SHIFTS))
        if [word >> shift & 15 for shift in AWQ_SHIFTS] != values[start:start + 8]:
            raise AssertionError("AWQ inverse permutation")
        words.append(word)
    return words


def norm(vector, gamma):
    total = sum(x * x for x in vector) & ((1 << 96) - 1)
    mean = ((total << 32) // len(vector) + 18446744073710) & ((1 << 128) - 1)
    reciprocal = (1 << 64) // math.isqrt(mean)
    return [sat32(round_shift(x * fp16(g) * reciprocal, 48))
            for x, g in zip(vector, gamma)]


def exp_q24(value):
    if value < -1048576:
        return 0
    if value >= 0:
        return 16777216
    n, remainder = divmod((-value) << 8, 11629080)
    term = total = 16777216
    for index in range(1, 7):
        product = signed(-term * remainder, 64)
        term = trunc_div(product, 16777216 * index)
        total = signed(total + term, 64)
    return 0 if total < 0 else total >> n


def silu(value):
    exponential = exp_q24(-abs(value))
    numerator = (1 << 48) if value >= 0 else exponential << 24
    sigmoid = numerator // (16777216 + exponential)
    return sat32(round_shift(value * sigmoid, 24))


@dataclass(frozen=True)
class Shape:
    layers: int
    hidden: int
    intermediate: int
    qheads: int
    kvheads: int
    head_dim: int
    group: int
    vocab: int
    max_seq: int
    tile: int
    window: int

    @property
    def kv(self):
        return self.kvheads * self.head_dim


MATRIX = (
    Shape(1, 8, 8, 1, 1, 8, 1, 8, 1, 1, 1),
    Shape(2, 24, 40, 3, 1, 8, 8, 17, 9, 3, 3),
    Shape(2, 128, 256, 4, 2, 32, 128, 67, 17, 16, 5),
)


def panel_bytes(rows, element_bytes, packed=False):
    """Panel transpose with independently checked bijection of logical elements."""
    columns = len(rows[0])
    panel_columns = 8 if packed else 64
    observed = {}
    output = bytearray()
    for panel in range(0, columns, panel_columns):
        for row, values in enumerate(rows):
            for col in range(panel, min(columns, panel + panel_columns)):
                offset = len(output)
                output.extend(values[col].to_bytes(element_bytes, "little"))
                observed[(row, col)] = int.from_bytes(output[offset:offset + element_bytes], "little")
    expected = {(r, c): value for r, values in enumerate(rows) for c, value in enumerate(values)}
    if observed != expected or len(output) != len(rows) * columns * element_bytes:
        raise AssertionError("nonbijective panel repacking")
    return bytes(output)


class EngineeringModel:
    """Fixed-point network equations, independent of any RTL state machine."""

    def __init__(self, shape, seed, mode):
        self.shape, self.mode = shape, mode
        rng = random.Random(seed)
        self.tensors = {}
        self.weights = {}
        self.bias = {}
        self.history = [[] for _ in range(shape.layers)]
        self.embedding = [[self.half(rng.randrange(-12, 13)) for _ in range(shape.hidden)]
                          for _ in range(shape.vocab)]
        self.add(0, 0, 0, panel_bytes(list(map(list, zip(*self.embedding))), 2))
        self.gamma = {}
        for layer in range(shape.layers):
            for kind in (5, 6):
                self.gamma[layer, kind] = [self.half(rng.randrange(8, 17)) for _ in range(shape.hidden)]
                self.add(kind, layer, 0, self.words(self.gamma[layer, kind], 2))
            for proj in range(7):
                inputs = shape.intermediate if proj == 6 else shape.hidden
                outputs = shape.kv if proj in (1, 2) else (
                    shape.intermediate if proj in (4, 5) else shape.hidden)
                if mode == "AWQ":
                    q = [[rng.randrange(16) for _ in range(outputs)] for _ in range(inputs)]
                    z = [[rng.randrange(16) for _ in range(outputs)]
                         for _ in range(inputs // shape.group)]
                    scales = [[0x2400 + 0x400 * rng.randrange(3) for _ in range(outputs)]
                              for _ in z]
                    self.add(1, layer, proj, panel_bytes([pack_awq(row) for row in q], 4, True))
                    self.add(2, layer, proj, panel_bytes([pack_awq(row) for row in z], 4, True))
                    self.add(3, layer, proj, panel_bytes(scales, 2))
                    self.weights[layer, proj] = [
                        [(q[r][c] - z[r // shape.group][c]) *
                         fp_q16(scales[r // shape.group][c], 5, 10, True)
                         for c in range(outputs)] for r in range(inputs)]
                else:
                    bits = [[self.bfloat(rng.randrange(-8, 9)) for _ in range(outputs)]
                            for _ in range(inputs)]
                    self.add(1, layer, proj, panel_bytes(bits, 2))
                    self.weights[layer, proj] = [[bf16(x) for x in row] for row in bits]
                if proj < 3:
                    self.bias[layer, proj] = [self.half(rng.randrange(-4, 5)) for _ in range(outputs)]
                    self.add(4, layer, proj, self.words(self.bias[layer, proj], 2))
            for kind in (9, 10):
                self.add(kind, layer, 0, bytes(shape.max_seq * shape.kv * 4))
        self.gamma[0, 7] = [0x3c00] * shape.hidden
        self.add(7, 0, 0, self.words(self.gamma[0, 7], 2))
        self.add(8, 0, 0, bytes(15 * max(shape.hidden, shape.intermediate) * 4))
        # Engineering identity rotations are legal input tables, not checkpoint RoPE fixtures.
        self.rope = [[(1 << 30) if c % 2 == 0 else 0 for c in range(shape.head_dim)]
                     for _ in range(shape.max_seq)]
        self.add(11, 0, 0, self.words([v for row in self.rope for v in row], 4))
        self.image = bytearray()
        self.descriptors = []
        for (kind, layer, proj), data in sorted(self.tensors.items()):
            base = len(self.image)
            padded = data + bytes((-len(data)) % 64)
            self.descriptors.append((layer * 96 + kind * 8 + proj, kind, layer, proj,
                                     base, len(padded)))
            self.image.extend(padded)

    @staticmethod
    def half(numerator):
        return int.from_bytes(struct.pack("<e", numerator / 16), "little")

    @staticmethod
    def bfloat(numerator):
        return struct.unpack("<I", struct.pack("<f", numerator / 16))[0] >> 16

    @staticmethod
    def words(values, size):
        return b"".join((x & ((1 << (size * 8)) - 1)).to_bytes(size, "little") for x in values)

    def add(self, kind, layer, proj, data):
        self.tensors[kind, layer, proj] = data

    def projection(self, vector, layer, proj):
        weights = self.weights[layer, proj]
        bias = self.bias.get((layer, proj), [0] * len(weights[0]))
        return [sat32(round_shift(sum(a * row[c] for a, row in zip(vector, weights)) +
                                  (fp16(bias[c]) << 16), 16))
                for c in range(len(weights[0]))]

    def token(self, token_id, position, new_sequence=False):
        s = self.shape
        self.last_writes = []

        def write(kind, layer, row, vector):
            self.last_writes.extend((kind, layer, row, col, value)
                                    for col, value in enumerate(vector))

        if new_sequence:
            self.history = [[] for _ in range(s.layers)]
        x = [fp16(v) for v in self.embedding[token_id]]
        write(8, 0, 0, x)
        for layer in range(s.layers):
            a = norm(x, self.gamma[layer, 5])
            write(8, 0, 1, a)
            q, k, v = [self.projection(a, layer, p) for p in range(3)]
            for slot, vector in zip((2, 3, 4), (q, k, v)):
                write(8, 0, slot, vector)
            table = self.rope[position]
            for vector, heads in ((q, s.qheads), (k, s.kvheads)):
                for head in range(heads):
                    for pair in range(s.head_dim // 2):
                        lo = head * s.head_dim + pair
                        hi = lo + s.head_dim // 2
                        first, second = vector[lo], vector[hi]
                        cosine, sine = table[2 * pair:2 * pair + 2]
                        vector[lo] = sat32(round_shift(first * cosine - second * sine, 30))
                        vector[hi] = sat32(round_shift(second * cosine + first * sine, 30))
            write(8, 0, 2, q)
            write(8, 0, 3, k)
            write(9, layer, position, k)
            write(10, layer, position, v)
            self.history[layer].append((k, v))
            context = []
            for head in range(s.qheads):
                kvhead = head // (s.qheads // s.kvheads)
                scores = []
                for old_k, _ in self.history[layer]:
                    dot = sum(q[head * s.head_dim + dim] * old_k[kvhead * s.head_dim + dim]
                              for dim in range(s.head_dim))
                    scores.append(signed(round_div(signed(dot, 96),
                                                   math.isqrt(s.head_dim << 32)), 96))
                maximum = max(scores)
                exps = [exp_q24(score - maximum) for score in scores]
                for dim in range(s.head_dim):
                    weighted = sum(old_v[kvhead * s.head_dim + dim] * e
                                   for (_, old_v), e in zip(self.history[layer], exps))
                    context.append(sat32(round_div(signed(weighted, 96), sum(exps))))
            write(8, 0, 5, context)
            projected = self.projection(context, layer, 3)
            write(8, 0, 6, projected)
            residual = [sat32(a + b) for a, b in zip(x, projected)]
            write(8, 0, 7, residual)
            a = norm(residual, self.gamma[layer, 6])
            write(8, 0, 8, a)
            gate, up = [self.projection(a, layer, p) for p in (4, 5)]
            write(8, 0, 9, gate)
            write(8, 0, 10, up)
            product = [sat32(round_shift(silu(g) * u, 16)) for g, u in zip(gate, up)]
            write(8, 0, 11, product)
            down = self.projection(product, layer, 6)
            write(8, 0, 12, down)
            x = [sat32(a + b) for a, b in zip(residual, down)]
            write(8, 0, 0, x)
        final = norm(x, self.gamma[0, 7])
        write(8, 0, 14, final)
        return self.vocabulary(final)

    def vocabulary(self, final):
        return [sat32(round_shift(sum(a * fp16(b) for a, b in zip(final, row)), 16))
                for row in self.embedding]
