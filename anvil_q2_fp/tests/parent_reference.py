"""Independent integer/rational interpretation of the supplied parent's ABI.

The parent uses FP16 tensor loads, saturated Q16.16 scratch, Q2.30 RoPE,
wide exact projection sums, half-away-from-zero rounding and Q0.24 exp.
This is not floating-point bit identity and provides no native-weight baseline.
"""

from fractions import Fraction
from math import isqrt

from fp_reference import rope_real, value
from transformer_reference import Transformer, key


def half_away(x):
    x = Fraction(x)
    magnitude = abs(x)
    q, r = divmod(magnitude.numerator, magnitude.denominator)
    result = q + int(2 * r >= magnitude.denominator)
    return -result if x < 0 else result


def sat(x):
    return min(2**31 - 1, max(-2**31, x))


def q16(x):
    return sat(half_away(Fraction(x) * 65536))


def exp_q24(x):
    if x < -16 * 65536:
        return 0
    if x >= 0:
        return 2**24
    exponent, remainder = divmod(-x * 256, 11629080)
    magnitude, total = 2**24, 2**24
    for degree in range(1, 7):
        magnitude = (magnitude * remainder // 2**24) // degree
        total += magnitude if degree % 2 == 0 else -magnitude
    return max(0, total // 2**exponent)


def silu_q16(x):
    exponential = exp_q24(-abs(x))
    numerator = exponential if x < 0 else 2**24
    sigmoid = numerator * 2**24 // (2**24 + exponential)
    return sat(half_away(Fraction(x * sigmoid, 2**24)))


class ParentTransformer(Transformer):
    def __init__(self, cache_mode, seed, geometry=None):
        super().__init__("fp16", 1, cache_mode, seed, geometry)

    def _tensors(self):
        super()._tensors()
        for address, matrix in self.weights.items():
            self.weights[address] = [[q16(value(x)) for x in row] for row in matrix]
        for address, vector in self.biases.items():
            self.biases[address] = [q16(value(x)) for x in vector]
        for address, vector in self.norms.items():
            self.norms[address] = [q16(value(x)) for x in vector]
        for position in range(self.g.positions):
            for component in range(self.g.head_dim // 2):
                c, s = rope_real(position, component, self.g.head_dim)
                self.loads[key(11, row=position, col=2 * component)] = half_away(
                    Fraction(c) * 2**30) & 0xFFFFFFFF
                self.loads[key(11, row=position, col=2 * component + 1)] = half_away(
                    Fraction(s) * 2**30) & 0xFFFFFFFF

    def embedding(self, token):
        return [q16(value(self.loads[key(0, row=token, col=col)], "fp16"))
                for col in range(self.g.hidden)]

    def store(self, slot, vector, domain, layer, position):
        for col, x in enumerate(vector):
            self.writes[key(8, row=slot, col=col)].append(x & 0xFFFFFFFF)
        self.stages.append({"domain": domain, "layer": layer, "position": position,
                            "slot": slot, "q16": vector[:]})
        return vector

    def normalization(self, x, layer, kind):
        mean_q64 = (sum(v * v for v in x) << 32) // len(x) + 18446744073710
        inverse_q32 = 2**64 // isqrt(mean_q64)
        return [sat(half_away(Fraction(v * gamma * inverse_q32, 2**48)))
                for v, gamma in zip(x, self.norms[layer, kind])]

    def projection(self, vector, layer, proj):
        result = []
        for row, weights in enumerate(self.weights[layer, proj]):
            total = sum(a * b for a, b in zip(vector, weights))
            if proj < 3:
                total += self.biases[layer, proj][row] << 16
            result.append(sat(half_away(Fraction(total, 65536))))
        return result

    def rotate(self, vector, position):
        result = list(vector)
        half = self.g.head_dim // 2
        for head in range(len(vector) // self.g.head_dim):
            for component in range(half):
                i, j = head * self.g.head_dim + component, head * self.g.head_dim + component + half
                c, s = rope_real(position, component, self.g.head_dim)
                c, s = half_away(Fraction(c) * 2**30), half_away(Fraction(s) * 2**30)
                result[i] = sat(half_away(Fraction(vector[i] * c - vector[j] * s, 2**30)))
                result[j] = sat(half_away(Fraction(vector[j] * c + vector[i] * s, 2**30)))
        return result

    def commit(self, vector, layer, position, is_value):
        g = self.g
        if self.cache_mode == 0:
            for col, x in enumerate(vector):
                self.writes[key(9 + int(is_value), layer, row=position, col=col)].append(
                    x & 0xFFFFFFFF)
            reconstructed = vector[:]
        else:
            reconstructed = []
            words = (g.block + 3) // 4
            for start in range(0, len(vector), g.block):
                block = vector[start:start + g.block]
                maximum = max(map(abs, block))
                exponent = 0
                while maximum > 127 * 2**exponent:
                    exponent += 1
                assert exponent <= 25
                q = [min(127, max(-127, half_away(Fraction(v, 2**exponent)))) for v in block]
                block_index = start // g.block
                for word in range(words):
                    packed = sum((v & 255) << (8 * j)
                                 for j, v in enumerate(q[4 * word:4 * word + 4]))
                    self.writes[key(12 + int(is_value), layer, row=position,
                                    col=block_index * words + word)].append(packed)
                self.writes[key(14 + int(is_value), layer, row=position,
                                col=block_index)].append(exponent)
                reconstructed.extend(sat(v * 2**exponent) for v in q)
        self.cache[layer, position, is_value] = reconstructed

    def attention(self, query, layer, position):
        g = self.g
        result = []
        divisor = isqrt(g.head_dim << 32)
        for head in range(g.q_heads):
            offset = (head // (g.q_heads // g.kv_heads)) * g.head_dim
            q = query[head * g.head_dim:(head + 1) * g.head_dim]
            scores = []
            for t in range(position + 1):
                k = self.cache[layer, t, False][offset:offset + g.head_dim]
                scores.append(half_away(Fraction(sum(a * b for a, b in zip(q, k)), divisor)))
            maximum = max(scores)
            weights = [exp_q24(s - maximum) for s in scores]
            denominator = sum(weights)
            for component in range(g.head_dim):
                total = sum(w * self.cache[layer, t, True][offset + component]
                            for t, w in enumerate(weights))
                result.append(sat(half_away(Fraction(total, denominator))))
        return result

    def residual(self, a, b):
        return [sat(x + y) for x, y in zip(a, b)]

    def swiglu(self, gate, up):
        return [sat(half_away(Fraction(silu_q16(a) * b, 65536)))
                for a, b in zip(gate, up)]

    def output_dot(self, norm, row):
        weights = self.embedding(row)
        return sat(half_away(Fraction(sum(a * b for a, b in zip(norm, weights)), 65536))) & 0xFFFFFFFF

    def manifest(self):
        result = super().manifest()
        result.update(product="accepted-parent", fp_format="FP16-loads/Q16.16-scratch",
                      rounding="exact integer reference; parent half-away rounding",
                      native_weight_mode="not applicable: parent supports AWQ only",
                      rope_encoding="signed Q2.30, independently calculated angles")
        return result
