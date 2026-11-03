"""Dense HT2 mathematical decoder over the compatible public packed image.

This is an oracle component, not a DUT experiment or a coverage producer.
It models numeric values and causal sequences, never pipeline/control state.
"""

from dataclasses import dataclass
from functools import lru_cache
from math import isqrt

from reference import (causal_context, exp_q24, f32, half, kv_decode, kv_encode,
                       nearest_div, q16_to_half, saturate_q16, single,
                       single_to_q16, unpack_rows)


def signed32(bits):
    return bits - (1 << 32) if bits & (1 << 31) else bits


def scalar_half(bits):
    return saturate_q16(int(half(bits) * 65536))


def rmsnorm(values, gamma):
    mean = (sum(value * value for value in values) << 32) // len(values)
    root = isqrt(mean + 18446744073710)
    if not root:
        raise ValueError("zero RMS denominator")
    reciprocal = (1 << 64) // root
    return tuple(saturate_q16(nearest_div(value * scalar_half(g) * reciprocal, 1 << 48))
                 for value, g in zip(values, gamma, strict=True))


def silu(value):
    exponent = exp_q24(-abs(value))
    sigmoid = ((exponent << 24) if value < 0 else (1 << 48)) // (
        (1 << 24) + exponent)
    return saturate_q16(nearest_div(value * sigmoid, 1 << 24))


@lru_cache(maxsize=65536)
def add32(a, b):
    return f32(single(a) + single(b))


@lru_cache(maxsize=65536)
def product32(delta, scale, activation):
    scale_value = half(scale)
    if scale_value < 0:
        raise ValueError("negative active AWQ scale")
    decoded_weight = f32(delta * scale_value)
    return f32(single(decoded_weight) * half(activation))


@dataclass(frozen=True)
class Geometry:
    layers: int = 36
    hidden: int = 64
    intermediate: int = 8
    kv_heads: int = 2
    head_dim: int = 4
    group: int = 8
    vocabulary: int = 8
    maximum: int = 8

    def __post_init__(self):
        if (self.layers <= 0 or self.kv_heads <= 0 or self.head_dim <= 0 or
                self.head_dim % 2 or self.hidden != 8 * self.kv_heads * self.head_dim or
                self.group not in (8, 16, 32, 64, 128) or self.hidden % self.group or
                self.intermediate <= 0 or self.intermediate % self.group or
                self.vocabulary <= 0 or not 1 <= self.maximum <= 32768):
            raise ValueError("illegal reference model geometry")


class PackedImage:
    def __init__(self, path):
        fields = path.read_text().split()
        if not fields or len(fields) != 1 + 2 * int(fields[0]):
            raise ValueError("malformed image line count")
        self.lines = {}
        for index in range(int(fields[0])):
            address, data = (int(field, 16) for field in fields[1 + 2 * index:3 + 2 * index])
            if address < 0 or address >= 1 << 33 or address % 64 or data >= 1 << 512:
                raise ValueError("malformed physical image line")
            if address in self.lines or data < 0:
                raise ValueError("duplicate or negative image data")
            self.lines[address] = data.to_bytes(64, "little")

    def read(self, address, count):
        if address < 0 or count < 0 or address + count > 1 << 33:
            raise ValueError("image read overflow")
        return bytes(self.lines[(address + offset) & ~63][(address + offset) & 63]
                     for offset in range(count))

    def halves(self, address, count):
        data = self.read(address, 2 * count)
        return tuple(int.from_bytes(data[index:index + 2], "little")
                     for index in range(0, len(data), 2))


@dataclass(frozen=True)
class Matrix:
    weights: tuple
    zeros: tuple
    scales: tuple
    group: int

    def project(self, values):
        if len(values) != len(self.weights):
            raise ValueError("projection activation width")
        activations = tuple(q16_to_half(value & 0xffffffff) for value in values)
        outputs = len(self.weights[0])
        stripes = [[0] * 8 for _ in range(outputs)]
        for column, activation in enumerate(activations):
            group = column // self.group
            for row in range(outputs):
                product = product32(self.weights[column][row] - self.zeros[group][row],
                                    self.scales[group][row], activation)
                stripes[row][column % 8] = add32(stripes[row][column % 8], product)
        result = []
        for partial in stripes:
            level1 = [add32(partial[index], partial[index + 1])
                      for index in range(0, 8, 2)]
            total = add32(add32(level1[0], level1[1]), add32(level1[2], level1[3]))
            bits, error = single_to_q16(total)
            if error:
                raise ValueError("invalid completed projection")
            result.append(signed32(bits))
        return tuple(result)


@dataclass(frozen=True)
class Evaluation:
    position: int
    token: int
    logits: tuple
    records: dict
    contexts: tuple
    projections: tuple

    @property
    def argmax(self):
        return max(range(len(self.logits)), key=lambda index: (self.logits[index], -index))


class SerialModel:
    def __init__(self, image, geometry=Geometry(), mode=1):
        if mode not in (1, 2):
            raise ValueError("reference requires compressed INT8/INT4 cache")
        self.image, self.geometry, self.mode = image, geometry, mode
        self.capacity = 32 if mode == 1 else 64
        self.matrices = []
        offsets = [0, 0x60000000, 0x64000000]
        kv_width = geometry.kv_heads * geometry.head_dim
        for _ in range(geometry.layers):
            projections = []
            for inputs, outputs in (
                    (geometry.hidden, geometry.hidden), (geometry.hidden, kv_width),
                    (geometry.hidden, kv_width), (geometry.hidden, geometry.hidden),
                    (geometry.hidden, geometry.intermediate),
                    (geometry.hidden, geometry.intermediate),
                    (geometry.intermediate, geometry.hidden)):
                if outputs % 8:
                    raise ValueError("packed-image oracle requires whole AWQ row words")
                groups = inputs // geometry.group
                weights = tuple(tuple(unpack_rows(int.from_bytes(image.read(
                    offsets[0] + column * (outputs // 2), outputs // 2), "little"), outputs))
                    for column in range(inputs))
                zeros = tuple(tuple(unpack_rows(int.from_bytes(image.read(
                    offsets[1] + group * (outputs // 2), outputs // 2), "little"), outputs))
                    for group in range(groups))
                scales = tuple(image.halves(offsets[2] + group * outputs * 2, outputs)
                               for group in range(groups))
                projections.append(Matrix(weights, zeros, scales, geometry.group))
                for region, count in enumerate((inputs * outputs // 2,
                                               groups * outputs // 2,
                                               groups * outputs * 2)):
                    offsets[region] += ((count + 63) // 64) * 64
            self.matrices.append(tuple(projections))

    def rotate(self, values, position):
        dim = self.geometry.head_dim
        coefficients = [signed32(int.from_bytes(self.image.read(
            0x6e000000 + (position * dim + component) * 4, 4), "little"))
            for component in range(dim)]
        if any(abs(value) > 1 << 30 for value in coefficients):
            raise ValueError("invalid RoPE coefficient")
        result = list(values)
        for head in range(len(values) // dim):
            for pair in range(dim // 2):
                first, second = head * dim + pair, head * dim + pair + dim // 2
                cosine, sine = coefficients[2 * pair:2 * pair + 2]
                result[first] = saturate_q16(nearest_div(
                    values[first] * cosine - values[second] * sine, 1 << 30))
                result[second] = saturate_q16(nearest_div(
                    values[second] * cosine + values[first] * sine, 1 << 30))
        return tuple(result)

    def evaluate(self, token, position, prefix=(), ancestors=()):
        g = self.geometry
        if not 0 <= token < g.vocabulary or not 0 <= position < g.maximum:
            raise ValueError("token/position outside model")
        if position != len(prefix) + len(ancestors):
            raise ValueError("causal reference sequence has a position gap")
        if [item.position for item in (*prefix, *ancestors)] != list(range(position)):
            raise ValueError("unordered causal prefix")
        state = tuple(scalar_half(value) for value in self.image.halves(
            0x80000000 + token * g.hidden * 2, g.hidden))
        records, contexts, projections = {}, [], []
        groups = (g.head_dim + self.capacity - 1) // self.capacity
        for layer, matrices in enumerate(self.matrices):
            normalized = rmsnorm(state, self.image.halves(
                0x6d000000 + 2 * layer * g.hidden * 2, g.hidden))
            qkv = [matrices[projection].project(normalized) for projection in range(3)]
            kv_width = g.kv_heads * g.head_dim
            bias = self.image.halves(0x6c000000 + layer * (g.hidden + 2 * kv_width) * 2,
                                    g.hidden + 2 * kv_width)
            offset = 0
            for projection in range(3):
                count = len(qkv[projection])
                qkv[projection] = tuple(saturate_q16(value + scalar_half(bias[offset + row]))
                                        for row, value in enumerate(qkv[projection]))
                offset += count
            projections.extend(qkv)
            query, key, value = self.rotate(qkv[0], position), self.rotate(qkv[1], position), qkv[2]
            for kind, vector in enumerate((key, value)):
                for head in range(g.kv_heads):
                    for group in range(groups):
                        start = head * g.head_dim + group * self.capacity
                        count = min(self.capacity, g.head_dim - group * self.capacity)
                        records[layer, kind, head, group] = kv_encode(vector[start:start + count],
                                                                     self.mode)
            causal_records = [item.records for item in (*prefix, *ancestors)] + [records]
            context = []
            for qhead in range(8 * g.kv_heads):
                decoded = []
                for kind in (0, 1):
                    vectors = []
                    for causal in causal_records:
                        components = []
                        for group in range(groups):
                            count = min(self.capacity, g.head_dim - group * self.capacity)
                            components.extend(kv_decode(causal[layer, kind, qhead // 8, group],
                                                        count, self.mode))
                        vectors.append(components)
                    decoded.append(vectors)
                context.extend(causal_context(query[qhead * g.head_dim:(qhead + 1) * g.head_dim],
                                              decoded[0], decoded[1], g.head_dim))
            contexts.append(tuple(context))
            output = matrices[3].project(context)
            residual = tuple(saturate_q16(a + b) for a, b in zip(state, output, strict=True))
            normalized = rmsnorm(residual, self.image.halves(
                0x6d000000 + (2 * layer + 1) * g.hidden * 2, g.hidden))
            gate, up = matrices[4].project(normalized), matrices[5].project(normalized)
            intermediate = tuple(saturate_q16(nearest_div(silu(a) * b, 65536))
                                 for a, b in zip(gate, up, strict=True))
            down = matrices[6].project(intermediate)
            projections.extend((output, gate, up, down))
            state = tuple(saturate_q16(a + b) for a, b in zip(residual, down, strict=True))
        normalized = rmsnorm(state, self.image.halves(
            0x6d000000 + 2 * g.layers * g.hidden * 2, g.hidden))
        logits = tuple(saturate_q16(nearest_div(sum(a * scalar_half(b) for a, b in
            zip(normalized, self.image.halves(0xc0000000 + row * g.hidden * 2, g.hidden),
                strict=True)), 65536)) for row in range(g.vocabulary))
        return Evaluation(position, token, logits, records, tuple(contexts), tuple(projections))

    def evaluate_tree(self, mask, tokens, parents, prefix):
        if not mask or mask & ~15 or len(tokens) != 4 or len(parents) != 4:
            raise ValueError("invalid tree shape")
        results, ancestry = [None] * 4, [()] * 4
        for node in range(4):
            if not mask & (1 << node):
                if tokens[node] or parents[node]:
                    raise ValueError("nonzero inactive tree node")
                continue
            parent = parents[node]
            if parent != 4 and (parent < 0 or parent >= node or results[parent] is None):
                raise ValueError("invalid tree parent")
            if any(mask & (1 << other) and parents[other] == parent and
                   tokens[other] == tokens[node] for other in range(node)):
                raise ValueError("duplicate sibling token")
            ancestry[node] = () if parent == 4 else (*ancestry[parent], results[parent])
            results[node] = self.evaluate(tokens[node], len(prefix) + len(ancestry[node]),
                                          prefix, ancestry[node])
        return tuple(results)
