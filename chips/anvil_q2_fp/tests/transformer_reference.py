"""Independent mathematical decoder and external-memory numerical ABI.

This model consumes deterministic rational tensors, not RTL functions or state.
Expected writes are ordered only per address, allowing real bank concurrency.
"""

from collections import defaultdict
from dataclasses import asdict, dataclass
from fractions import Fraction

from codec_checks import SHIFTS, codec_reference
from fp_reference import (
    add, convert, divide, exp_nonpositive, multiply, negate, rmsnorm,
    rope_coefficients, rounded, silu, square_root, value,
)


@dataclass(frozen=True)
class Geometry:
    layers: int = 2
    hidden: int = 48
    intermediate: int = 48
    q_heads: int = 6
    kv_heads: int = 1
    head_dim: int = 8
    group: int = 12
    vocabulary: int = 3
    positions: int = 3
    block: int = 2


def key(kind, layer=0, proj=0, row=0, col=0):
    assert 0 <= kind < 16 and 0 <= proj < 8
    assert all(0 <= x < 2**32 for x in (layer, row, col))
    return (kind << 99) | (layer << 67) | (proj << 64) | (row << 32) | col


def coordinates(address):
    return ((address >> 99) & 15, (address >> 67) & 0xFFFFFFFF,
            (address >> 64) & 7, (address >> 32) & 0xFFFFFFFF,
            address & 0xFFFFFFFF)


class Transformer:
    def __init__(self, fmt, weight_mode, cache_mode, seed, geometry=None):
        self.g = geometry or Geometry()
        self.fmt = fmt
        self.weight_mode = weight_mode
        self.cache_mode = cache_mode
        self.seed = seed
        self.loads = {}
        self.writes = defaultdict(list)
        self.stages = []
        self.logits = []
        self.cache = {}
        self._tensors()

    def a16(self, bits):
        return convert(convert(bits, "fp32", self.fmt), self.fmt)

    def tensor(self, rational):
        return rounded(rational, self.fmt)

    def _tensors(self):
        g, seed = self.g, self.seed
        self.weights, self.biases, self.norms = {}, {}, {}
        for row in range(g.vocabulary):
            for col in range(g.hidden):
                rational = Fraction((seed + row * 11 + col * 7) % 33 - 16, 31)
                self.loads[key(0, row=row, col=col)] = self.tensor(rational)
        for layer in range(g.layers):
            for kind in (5, 6, 7):
                if kind == 7 and layer != 0:
                    continue
                gamma = []
                for col in range(g.hidden):
                    bits = self.tensor(1 + Fraction((seed + kind + layer + col) % 5 - 2, 64))
                    self.loads[key(kind, layer, col=col)] = bits
                    gamma.append(convert(bits, self.fmt))
                self.norms[layer, kind] = gamma
            for proj in range(7):
                inputs = g.intermediate if proj == 6 else g.hidden
                outputs = (g.kv_heads * g.head_dim if proj in (1, 2) else
                           g.intermediate if proj in (4, 5) else g.hidden)
                matrix = [[0] * inputs for _ in range(outputs)]
                for column in range(inputs):
                    group = column // g.group
                    packed_weights, packed_zeros = {}, {}
                    for row in range(outputs):
                        zero = 3 + (seed + layer + proj + group * 3 + row * 5) % 9
                        delta = (seed * 3 + layer * 5 + proj * 7 + column * 11 + row * 13) % 7 - 3
                        scale = Fraction(1, 128 << ((seed + layer + proj + group + row) % 2))
                        effective = self.tensor(delta * scale)
                        matrix[row][column] = convert(effective, self.fmt)
                        if self.weight_mode == 0:
                            self.loads[key(1, layer, proj, column, row)] = effective
                        else:
                            packed_weights[row // 8] = packed_weights.get(row // 8, 0) | (
                                (zero + delta) << SHIFTS[row % 8])
                            packed_zeros[row // 8] = packed_zeros.get(row // 8, 0) | (
                                zero << SHIFTS[row % 8])
                            self.loads[key(3, layer, proj, group, row)] = self.tensor(scale)
                    if self.weight_mode:
                        for packed_col, bits in packed_weights.items():
                            self.loads[key(1, layer, proj, column, packed_col)] = bits
                            self.loads[key(2, layer, proj, group, packed_col)] = packed_zeros[packed_col]
                self.weights[layer, proj] = matrix
                bias = []
                if proj < 3:
                    for row in range(outputs):
                        bits = self.tensor(Fraction((seed + layer * 3 + proj * 5 + row) % 9 - 4, 256))
                        self.loads[key(4, layer, proj, col=row)] = bits
                        bias.append(convert(bits, self.fmt))
                self.biases[layer, proj] = bias
        for position in range(g.positions):
            for component in range(g.head_dim // 2):
                cosine, sine = rope_coefficients(position, component, g.head_dim)
                self.loads[key(11, row=position, col=2 * component)] = cosine
                self.loads[key(11, row=position, col=2 * component + 1)] = sine

    def store(self, slot, vector, domain, layer, position):
        for col, bits in enumerate(vector):
            self.writes[key(8, row=slot, col=col)].append(bits)
        self.stages.append({
            "domain": domain, "layer": layer, "position": position,
            "slot": slot, "fp32": [f"{bits:08x}" for bits in vector],
        })
        return vector

    def projection(self, vector, layer, proj):
        activation = list(map(self.a16, vector))
        result = []
        for row, weights in enumerate(self.weights[layer, proj]):
            total = 0
            for a, b in zip(activation, weights):
                total = add(total, multiply(a, b))
            if proj < 3:
                total = add(total, self.biases[layer, proj][row])
            result.append(total)
        return result

    def rotate(self, vector, position):
        result = list(vector)
        half = self.g.head_dim // 2
        for head in range(len(vector) // self.g.head_dim):
            for component in range(half):
                i = head * self.g.head_dim + component
                j = i + half
                c, s = rope_coefficients(position, component, self.g.head_dim)
                result[i] = add(multiply(vector[i], c), negate(multiply(vector[j], s)))
                result[j] = add(multiply(vector[j], c), multiply(vector[i], s))
        return result

    def commit(self, vector, layer, position, is_value):
        g = self.g
        selected = [convert(v, "fp32", self.fmt) for v in vector]
        reconstructed = []
        if self.cache_mode == 0:
            for offset in range(0, len(selected), 2):
                self.writes[key(9 + int(is_value), layer, row=position, col=offset // 2)].append(
                    selected[offset] | (selected[offset + 1] << 16))
            reconstructed = [convert(v, self.fmt) for v in selected]
        else:
            words = (g.block + 3) // 4
            for start in range(0, len(selected), g.block):
                values = selected[start:start + g.block]
                rebuilt, q, exponent, failed = codec_reference(
                    values, [0] * g.block, 0, False, self.fmt)
                assert not failed, "bounded fixture produced cache overflow"
                block_index = start // g.block
                for word in range(words):
                    packed = sum(b << (8 * j) for j, b in enumerate(q[word * 4:word * 4 + 4]))
                    self.writes[key(12 + int(is_value), layer, row=position,
                                    col=block_index * words + word)].append(packed)
                self.writes[key(14 + int(is_value), layer, row=position,
                                col=block_index)].append(exponent & 0xFFFFFFFF)
                reconstructed.extend(convert(v, self.fmt) for v in rebuilt)
        self.cache[layer, position, is_value] = reconstructed

    def attention(self, query, layer, position):
        g = self.g
        result = []
        divisor = square_root(rounded(g.head_dim))
        for head in range(g.q_heads):
            kv_head = head // (g.q_heads // g.kv_heads)
            offset = kv_head * g.head_dim
            q = list(map(self.a16, query[head * g.head_dim:(head + 1) * g.head_dim]))
            scores = []
            for t in range(position + 1):
                k = self.cache[layer, t, False][offset:offset + g.head_dim]
                dot = 0
                for a, b in zip(q, k):
                    dot = add(dot, multiply(a, b))
                scores.append(divide(dot, divisor))
            maximum = max(scores, key=value)
            weights = [exp_nonpositive(add(s, negate(maximum))) for s in scores]
            denominator = 0
            for weight in weights:
                denominator = add(denominator, weight)
            for component in range(g.head_dim):
                total = 0
                for t, weight in enumerate(weights):
                    v = self.cache[layer, t, True][offset + component]
                    total = add(total, multiply(weight, v))
                result.append(divide(total, denominator))
        return result

    def embedding(self, token):
        return [convert(self.loads[key(0, row=token, col=col)], self.fmt)
                for col in range(self.g.hidden)]

    def normalization(self, x, layer, kind):
        return rmsnorm(x, self.norms[layer, kind])

    def residual(self, a, b):
        return list(map(add, a, b))

    def swiglu(self, gate, up):
        return [multiply(silu(a), b) for a, b in zip(gate, up)]

    def output_dot(self, norm, row):
        total = 0
        for col in range(self.g.hidden):
            w = convert(self.loads[key(0, row=row, col=col)], self.fmt)
            total = add(total, multiply(self.a16(norm[col]), w))
        return total

    def execute(self):
        g = self.g
        for pos in range(g.positions):
            token = pos % g.vocabulary
            x = self.embedding(token)
            self.store(0, x, "embedding", 0, pos)
            for layer in range(g.layers):
                norm = self.store(1, self.normalization(x, layer, 5), "rmsnorm", layer, pos)
                q, k, v = [self.store(2 + proj, self.projection(norm, layer, proj),
                                      "projection", layer, pos) for proj in range(3)]
                q = self.store(2, self.rotate(q, pos), "rope", layer, pos)
                k = self.store(3, self.rotate(k, pos), "rope", layer, pos)
                self.commit(k, layer, pos, False)
                self.commit(v, layer, pos, True)
                context = self.store(5, self.attention(q, layer, pos), "attention", layer, pos)
                output = self.store(6, self.projection(context, layer, 3), "projection", layer, pos)
                residual = self.store(7, self.residual(x, output), "residual", layer, pos)
                norm = self.store(8, self.normalization(residual, layer, 6), "rmsnorm", layer, pos)
                gate = self.store(9, self.projection(norm, layer, 4), "projection", layer, pos)
                up = self.store(10, self.projection(norm, layer, 5), "projection", layer, pos)
                product = self.store(11, self.swiglu(gate, up),
                                     "swiglu", layer, pos)
                down = self.store(12, self.projection(product, layer, 6), "projection", layer, pos)
                x = self.store(0, self.residual(residual, down), "residual", layer, pos)
            norm = self.store(14, self.normalization(x, 0, 7), "rmsnorm", 0, pos)
            for row in range(g.vocabulary):
                self.logits.append((pos, row, self.output_dot(norm, row)))
        assert self.logits and self.writes and self.stages
        return self

    def manifest(self):
        return {
            "schema": 1, "suite": "anvil-q2-fp-five-domain-v1",
            "geometry": asdict(self.g), "shape_class": "reduced",
            "seed": self.seed, "fp_format": self.fmt, "weight_mode": self.weight_mode,
            "cache_mode": self.cache_mode, "inputs": "bounded rational tensors, not a checkpoint",
            "rounding": "independent exact rational RNE after each normative FP32 operation",
            "generation": "tests/transformer_reference.py:Transformer._tensors",
            "operations": "tests/transformer_reference.py:Transformer.execute",
            "domains": ["native/AWQ projections and logits", "RMSNorm and residual",
                        "split-half RoPE", "causal GQA and KV storage", "SwiGLU and token"],
            "scope": "No native throughput, trained-model accuracy or hardware claim.",
        }
