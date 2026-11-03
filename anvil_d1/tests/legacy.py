"""Independent dense Anvil-Q arithmetic and packed-memory generated fixtures.

Fixtures are synthetic, not checkpoint/accuracy claims. FP16 conversion uses
Python's binary16 codec and exact power-of-two scaling. AWQ rows are packed in
the published lane order 0,16,4,20,8,24,12,28. Full dense inference uses
uncompressed or block-quantized GQA, split-half Q30 RoPE, the historical epsilon,
and nearest/ties-away signed attention division. Native equations are not substituted.
"""

from collections import defaultdict
from math import isqrt
import random
import struct

from reference import Q16, Q24, exp_q24, sat32


def signed_round_div(numerator, denominator):
    magnitude = (abs(numerator)+denominator//2)//denominator
    return -magnitude if numerator < 0 else magnitude


def fp16_word(value):
    return int.from_bytes(struct.pack("<e", value), "little")


def fp16_q16(word):
    value = struct.unpack("<e", int(word).to_bytes(2, "little"))[0]
    scaled = value*Q16
    magnitude = int(abs(scaled)+0.5)
    return sat32(-magnitude if scaled < 0 else magnitude)


def legacy_round(value, shift):
    if shift == 0:
        return sat32(value)
    half = 1 << (shift-1)
    threshold = ((1 << 31)-1)*(1 << shift)+half
    if value >= threshold:
        return (1 << 31)-1
    if value <= -threshold:
        return -(1 << 31)
    magnitude = (abs(value)+half) >> shift
    return -magnitude if value < 0 else magnitude


def legacy_norm(values, gamma):
    mean = (sum(v*v for v in values) << 32)//len(values)
    root = isqrt(mean+18446744073710)
    reciprocal = (1 << 64)//root
    return [legacy_round(x*fp16_q16(g)*reciprocal, 48)
            for x, g in zip(values, gamma, strict=True)]


def legacy_silu(value):
    e = exp_q24(-abs(value))
    sigmoid = ((1 << 48) if value >= 0 else e*Q24)//(Q24+e)
    return legacy_round(value*sigmoid, 24)


def encode_cache(values, mode, capacity, asymmetric):
    if mode == 0:
        return [values[0] & 0xffffffff], 0, values[:]
    bits, limit = (4, 7) if mode == 2 else (8, 127)
    zero = 0
    exponent = 0
    if mode == 2 and asymmetric:
        while True:
            extrema = [legacy_round(min(values), exponent),
                       legacy_round(max(values), exponent)]
            lower, upper = max(-8, -8-extrema[0]), min(7, 7-extrema[1])
            if lower <= upper:
                zero = lower if lower > 0 else upper if upper < 0 else 0
                break
            exponent += 1
    else:
        while max(abs(v) for v in values) > limit*(1 << exponent):
            exponent += 1
    codes = [max(-8 if asymmetric and mode == 2 else -limit,
                 min(limit, legacy_round(v, exponent)+zero)) for v in values]
    payload = sum((code & ((1 << bits)-1)) << (bits*i) for i, code in enumerate(codes))
    words = [(payload >> (32*i)) & 0xffffffff for i in range((capacity*bits+31)//32)]
    return words, exponent | (zero & 15) << 8, [sat32((code-zero) << exponent) for code in codes]


class LegacyFixture:
    def __init__(self, seed=17, profile=3, mode=0, asymmetric=0):
        self.seed, self.profile, self.mode, self.asymmetric = seed, profile, mode, asymmetric
        self.hidden, self.intermediate, self.heads, self.kv_heads = 16, 16, 8 if profile == 3 else 2, 1
        self.dim = self.hidden//self.heads
        self.vocab, self.layers, self.maxseq = 8, 1, 5
        self.initial, self.writes = {}, defaultdict(list)
        self.cache, self.matrices = {}, {}
        rng = random.Random(seed)
        for token in range(self.vocab):
            for col in range(self.hidden):
                self.initial[0, 0, 0, token, col] = fp16_word(rng.choice(
                    (-0.75, -0.375, -0.125, 0.125, 0.375, 0.75)))
        for kind in (5, 6, 7):
            for col in range(self.hidden):
                self.initial[kind, 0, 0, 0, col] = fp16_word(rng.choice((0.75, 1., 1.25)))
        for pos in range(self.maxseq):
            for pair in range(self.dim//2):
                self.initial[11, 0, 0, pos, 2*pair] = (1 << 30)-pos*(1 << 24)
                self.initial[11, 0, 0, pos, 2*pair+1] = (1 << 27)+pos*(1 << 24)
        for projection in range(7):
            rows = self.kv_heads*self.dim if projection in (1, 2) else self.intermediate if projection in (4, 5) else self.hidden
            cols = self.intermediate if projection == 6 else self.hidden
            matrix = [[rng.randrange(3, 13) for _ in range(cols)] for _ in range(rows)]
            scales = [[fp16_word(rng.choice((0.03125, 0.0625, 0.125)))
                       for _ in range(rows)] for group in range((cols+7)//8)]
            zeros = [[rng.randrange(6, 10) for _ in range(rows)] for _ in scales]
            self.matrices[projection] = [[
                (matrix[row][col]-zeros[col//8][row])*fp16_q16(scales[col//8][row])
                for col in range(cols)] for row in range(rows)]
            shifts = (0, 16, 4, 20, 8, 24, 12, 28)
            for col in range(cols):
                for block in range((rows+7)//8):
                    word = sum(matrix[row][col] << shifts[row % 8]
                               for row in range(block*8, min(rows, (block+1)*8)))
                    self.initial[1, 0, projection, col, block] = word
            for group in range((cols+7)//8):
                for block in range((rows+7)//8):
                    self.initial[2, 0, projection, group, block] = sum(
                        zeros[group][row] << shifts[row % 8]
                        for row in range(block*8, min(rows, (block+1)*8)))
                for row in range(rows):
                    self.initial[3, 0, projection, group, row] = scales[group][row]
            if projection < 3:
                for row in range(rows):
                    self.initial[4, 0, projection, 0, row] = fp16_word(rng.choice((-0.125, 0., 0.125)))

    def write(self, key, value):
        self.writes[key].append(value & 0xffffffff)

    def vector(self, slot, values):
        for col, value in enumerate(values):
            self.write((8, 0, 0, slot, col), value)

    def project(self, projection, values, slot):
        outputs = [legacy_round(sum(a*b for a, b in zip(row, values, strict=True)) +
                   (fp16_q16(self.initial[4, 0, projection, 0, i]) << 16
                    if projection < 3 else 0), 16)
                   for i, row in enumerate(self.matrices[projection])]
        self.vector(slot, outputs)
        return outputs

    def rotary(self, values, heads, pos, slot):
        result = values[:]
        half = self.dim//2
        for head in range(heads):
            for pair in range(half):
                a, b = values[head*self.dim+pair], values[head*self.dim+pair+half]
                c, s = self.initial[11, 0, 0, pos, 2*pair], self.initial[11, 0, 0, pos, 2*pair+1]
                result[head*self.dim+pair] = legacy_round(a*c-b*s, 30)
                result[head*self.dim+pair+half] = legacy_round(a*s+b*c, 30)
                self.write((8, 0, 0, slot, head*self.dim+pair), result[head*self.dim+pair])
                self.write((8, 0, 0, slot, head*self.dim+pair+half), result[head*self.dim+pair+half])
        return result

    def commit(self, key, value, pos):
        capacity = 1 if self.mode == 0 else (64 if self.mode == 2 else 32) if self.profile == 3 else 2
        decoded = []
        for values, is_value in ((key, False), (value, True)):
            restored = []
            blocks = (self.dim+capacity-1)//capacity
            for head in range(self.kv_heads):
                for block in range(blocks):
                    start = head*self.dim+block*capacity
                    words, metadata, items = encode_cache(
                        values[start:min((head+1)*self.dim, start+capacity)],
                        self.mode, capacity, self.asymmetric)
                    restored.extend(items)
                    for word, payload in enumerate(words):
                        kind = (10 if is_value else 9) if self.mode == 0 else (13 if is_value else 12)
                        col = start if self.mode == 0 else (head*blocks+block)*len(words)+word
                        self.write((kind, 0, 0, pos, col), payload)
                    if self.mode:
                        self.write((15 if is_value else 14, 0, 0, pos, head*blocks+block), metadata)
            decoded.append(restored)
        self.cache[pos] = decoded

    def token(self, token, pos):
        x = [fp16_q16(self.initial[0, 0, 0, token, col]) for col in range(self.hidden)]
        self.vector(0, x)
        norm = legacy_norm(x, [self.initial[5, 0, 0, 0, col] for col in range(self.hidden)])
        self.vector(1, norm)
        q, k, v = self.project(0, norm, 2), self.project(1, norm, 3), self.project(2, norm, 4)
        q = self.rotary(q, self.heads, pos, 2)
        k = self.rotary(k, self.kv_heads, pos, 3)
        self.commit(k, v, pos)
        context = []
        for head in range(self.heads):
            kv = head//(self.heads//self.kv_heads)
            scores = [signed_round_div(sum(q[head*self.dim+d]*self.cache[t][0][kv*self.dim+d]
                                   for d in range(self.dim)), isqrt(self.dim << 32))
                      for t in range(pos+1)]
            exponentials = [exp_q24(z-max(scores)) for z in scores]
            context.extend(sat32(signed_round_div(sum(e*self.cache[t][1][kv*self.dim+d]
                                              for t, e in enumerate(exponentials)),
                                          sum(exponentials))) for d in range(self.dim))
        self.vector(5, context)
        branch = self.project(3, context, 6)
        residual = [sat32(a+b) for a, b in zip(x, branch, strict=True)]
        self.vector(7, residual)
        norm = legacy_norm(residual, [self.initial[6, 0, 0, 0, col] for col in range(self.hidden)])
        self.vector(8, norm)
        gate, up = self.project(4, norm, 9), self.project(5, norm, 10)
        intermediate = [legacy_round(legacy_silu(g)*u, 16) for g, u in zip(gate, up, strict=True)]
        self.vector(11, intermediate)
        branch = self.project(6, intermediate, 12)
        x = [sat32(a+b) for a, b in zip(residual, branch, strict=True)]
        self.vector(0, x)
        norm = legacy_norm(x, [self.initial[7, 0, 0, 0, col] for col in range(self.hidden)])
        self.vector(14, norm)
        return [legacy_round(sum(fp16_q16(self.initial[0, 0, 0, token, col])*norm[col]
                                  for col in range(self.hidden)), 16) for token in range(self.vocab)]
