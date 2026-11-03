"""Independent integer reference and deterministic synthetic image construction."""

from dataclasses import dataclass
from hashlib import sha256
from math import cos, isqrt, sin
import random


MIN32 = -(1 << 31)
MAX32 = (1 << 31) - 1
AWQ_SHIFTS = (0, 16, 4, 20, 8, 24, 12, 28)
BASES = {
    "qweight": 0,
    "qzeros": 0x60000000,
    "scales": 0x64000000,
    "bias": 0x6C000000,
    "norm": 0x6D000000,
    "rope": 0x6E000000,
    "embedding": 0x80000000,
    "kv": 0x100000000,
}
LIMITS = {
    "qweight": 0x60000000,
    "qzeros": 0x64000000,
    "scales": 0x6C000000,
    "bias": 0x6D000000,
    "norm": 0x6E000000,
    "rope": 0x80000000,
    "embedding": 0xC0000000,
    "kv": 0x200000000,
}


def saturate(value):
    return max(MIN32, min(MAX32, value))


def rounded_ratio(numerator, denominator):
    if denominator <= 0:
        raise ValueError("nonpositive denominator")
    magnitude = (abs(numerator) + denominator // 2) // denominator
    return -magnitude if numerator < 0 else magnitude


def rounded_shift(value, shift):
    return saturate(rounded_ratio(value, 1 << shift))


def half_magnitude(bits):
    exponent, fraction = (bits >> 10) & 31, bits & 1023
    if exponent == 31:
        raise ValueError("nonfinite binary16")
    if exponent == 0:
        numerator, denominator = fraction, 256
    else:
        power = exponent - 9
        numerator = (1024 + fraction) << max(0, power)
        denominator = 1 << max(0, -power)
    return rounded_ratio(numerator, denominator)


def half_scale(bits):
    if bits & 0x8000 and bits & 0x7FFF:
        raise ValueError("negative scale")
    return half_magnitude(bits)


def half_signed(bits):
    magnitude = half_magnitude(bits)
    return saturate(-magnitude if bits & 0x8000 else magnitude)


def mac(q, z, scales, activations, mask=0xFFFF):
    total = 0
    for lane in range(16):
        if mask & (1 << lane):
            total += (q[lane] - z[lane]) * half_scale(scales[lane]) * activations[lane]
    return total


def encode_kv(values, mode):
    capacity = (16, 32, 64)[mode]
    if not 0 < len(values) <= capacity:
        raise ValueError("invalid KV count")
    record = bytearray(64)
    if mode == 0:
        for i, value in enumerate(values):
            record[i * 4:i * 4 + 4] = int(value).to_bytes(4, "little", signed=True)
        return bytes(record)
    limit, bits = (127, 8) if mode == 1 else (7, 4)
    exponent = 0
    while max(map(abs, values)) > limit * (1 << exponent):
        exponent += 1
    packed = 0
    for i, value in enumerate(values):
        code = max(-limit, min(limit, rounded_ratio(value, 1 << exponent)))
        packed |= (code & ((1 << bits) - 1)) << (i * bits)
    record[:32] = packed.to_bytes(32, "little")
    record[32:36] = exponent.to_bytes(4, "little")
    return bytes(record)


def decode_kv(record, count, mode):
    capacity = (16, 32, 64)[mode]
    if len(record) != 64 or not 0 < count <= capacity:
        raise ValueError("invalid KV record extent")
    if mode == 0:
        if any(record[count * 4:]):
            raise ValueError("nonzero unused lossless lanes")
        return [int.from_bytes(record[i * 4:i * 4 + 4], "little", signed=True)
                for i in range(count)]
    bits, maximum = (8, 25) if mode == 1 else (4, 29)
    exponent = int.from_bytes(record[32:36], "little")
    if exponent > maximum or any(record[36:]):
        raise ValueError("invalid exponent or padding")
    payload = int.from_bytes(record[:32], "little")
    codes = []
    for i in range(capacity):
        code = (payload >> (i * bits)) & ((1 << bits) - 1)
        if code & (1 << (bits - 1)):
            code -= 1 << bits
        if i >= count:
            if code:
                raise ValueError("nonzero unused compressed lane")
        else:
            if code == -(1 << (bits - 1)):
                raise ValueError("reserved compressed code")
            codes.append(code)
    if not any(codes) and exponent != 0:
        raise ValueError("noncanonical zero group")
    return [saturate(code * (1 << exponent)) for code in codes]


def quantize_vector(values, mode):
    capacity = (16, 32, 64)[mode]
    reconstructed = []
    for offset in range(0, len(values), capacity):
        group = values[offset:offset + capacity]
        reconstructed.extend(decode_kv(encode_kv(group, mode), len(group), mode))
    return reconstructed


def exponential(value):
    if value < -1048576:
        return 0
    if value >= 0:
        return 1 << 24
    quotient, remainder = divmod(-value * 256, 11629080)
    term = total = 1 << 24
    for degree in range(1, 7):
        magnitude = abs(term) * remainder // ((1 << 24) * degree)
        term = -magnitude if degree & 1 else magnitude
        total += term
    return max(0, total) >> quotient


def silu(value):
    exp = exponential(-abs(value))
    numerator = 1 << 48 if value >= 0 else exp << 24
    sigmoid = numerator // ((1 << 24) + exp)
    return rounded_shift(value * sigmoid, 24)


def rmsnorm(values, gamma):
    square_sum = sum(value * value for value in values)
    root = isqrt((square_sum << 32) // len(values) + 18446744073710)
    reciprocal = (1 << 64) // root
    return [rounded_shift(value * half_signed(weight) * reciprocal, 48)
            for value, weight in zip(values, gamma)]


@dataclass(frozen=True)
class Geometry:
    layers: int = 1
    hidden: int = 16
    intermediate: int = 16
    q_heads: int = 8
    kv_heads: int = 1
    head_dim: int = 2
    group: int = 8
    vocab: int = 3
    context: int = 3

    def __post_init__(self):
        if not (self.hidden == self.q_heads * self.head_dim
                and self.q_heads == 8 * self.kv_heads and self.head_dim > 0
                and self.head_dim % 2 == 0 and self.group in (8, 16, 32, 64, 128)
                and self.hidden % self.group == self.intermediate % self.group == 0
                and min(self.layers, self.intermediate, self.vocab, self.context) > 0
                and self.context <= 32768):
            raise ValueError("illegal reference geometry")

    @property
    def shapes(self):
        h, i, kv = self.hidden, self.intermediate, self.kv_heads * self.head_dim
        return ((h, h), (h, kv), (h, kv), (h, h), (h, i), (h, i), (i, h))

    def parameters(self):
        return dict(NUM_LAYERS=self.layers, HIDDEN_SIZE=self.hidden,
                    INTERMEDIATE_SIZE=self.intermediate, NUM_Q_HEADS=self.q_heads,
                    NUM_KV_HEADS=self.kv_heads, HEAD_DIM=self.head_dim,
                    GROUP_SIZE=self.group, VOCAB_SIZE=self.vocab, MAX_SEQ_LEN=self.context)


def align64(value):
    return (value + 63) & -64


PRODUCTION = Geometry(layers=36, hidden=2048, intermediate=11008, q_heads=16,
                      kv_heads=2, head_dim=128, group=128, vocab=151936, context=32768)


def image_layout(geometry=PRODUCTION):
    offsets = {name: BASES[name] for name in ("qweight", "qzeros", "scales")}
    matrices = {}
    useful = dict.fromkeys(offsets, 0)
    for layer in range(geometry.layers):
        for projection, (inputs, outputs) in enumerate(geometry.shapes):
            lengths = dict(qweight=inputs * ((outputs + 7) // 8) * 4,
                           qzeros=(inputs // geometry.group) * ((outputs + 7) // 8) * 4,
                           scales=(inputs // geometry.group) * outputs * 2)
            matrices[layer, projection] = dict(inputs=inputs, outputs=outputs,
                                               **{name: offsets[name] for name in offsets})
            for name, length in lengths.items():
                useful[name] += length
                offsets[name] += align64(length)
    extents = {name: offsets[name] - BASES[name] for name in offsets}
    extents.update(
        bias=geometry.layers * (geometry.hidden + 2 * geometry.kv_heads * geometry.head_dim) * 2,
        norm=(2 * geometry.layers + 1) * geometry.hidden * 2,
        rope=geometry.context * geometry.head_dim * 4,
        embedding=geometry.vocab * geometry.hidden * 2)
    for name, length in extents.items():
        if BASES[name] + length > LIMITS[name]:
            raise ValueError(f"{name} region overflow")
    kv_bytes = {}
    for mode, capacity in enumerate((16, 32, 64)):
        extent = (geometry.layers * 2 * geometry.context * geometry.kv_heads
                  * ((geometry.head_dim + capacity - 1) // capacity) * 64)
        if BASES["kv"] + extent > LIMITS["kv"]:
            raise ValueError("KV region overflow")
        kv_bytes[mode] = extent
    return dict(matrices=matrices, component_bytes=extents, useful_weight_bytes=useful,
                persistent_image_bytes=sum(extents.values()), kv_bytes=kv_bytes)


class Image:
    """A sparse byte-addressed image, not official checkpoint data."""

    def __init__(self, geometry=Geometry(), seed=17):
        self.geometry, self.seed = geometry, seed
        self.data = {}
        self.matrices = {}
        self.biases = {}
        self.norms = {}
        self.embeddings = []
        self.rope = []
        self.matrix_bases = {}
        rng = random.Random(seed)
        offsets = {name: BASES[name] for name in ("qweight", "qzeros", "scales")}
        for layer in range(geometry.layers):
            for projection, (n, m) in enumerate(geometry.shapes):
                qw, qz, sc = (offsets[name] for name in ("qweight", "qzeros", "scales"))
                self.matrix_bases[layer, projection] = qw, qz, sc
                groups, words = n // geometry.group, (m + 7) // 8
                q = [[rng.randrange(16) for _ in range(m)] for _ in range(n)]
                z = [[rng.randrange(4, 12) for _ in range(m)] for _ in range(groups)]
                scales = [[rng.choice((0x1000, 0x1400, 0x1800)) for _ in range(m)]
                          for _ in range(groups)]
                self.matrices[layer, projection] = q, z, scales
                for source in range(n):
                    for word in range(words):
                        packed = sum(q[source][out] << AWQ_SHIFTS[out % 8]
                                     for out in range(word * 8, min(m, (word + 1) * 8)))
                        self.put(qw + 4 * (source * words + word), packed, 4)
                for group in range(groups):
                    for word in range(words):
                        packed = sum(z[group][out] << AWQ_SHIFTS[out % 8]
                                     for out in range(word * 8, min(m, (word + 1) * 8)))
                        self.put(qz + 4 * (group * words + word), packed, 4)
                    for out in range(m):
                        self.put(sc + 2 * (group * m + out), scales[group][out], 2)
                for name, length in (("qweight", n * words * 4),
                                     ("qzeros", groups * words * 4),
                                     ("scales", groups * m * 2)):
                    offsets[name] += align64(length)
                if projection < 3:
                    bias = [rng.choice((0, 0x1000, 0x9000, 0x1400, 0x9400))
                            for _ in range(m)]
                    self.biases[layer, projection] = bias
                    per_layer = (geometry.hidden + 2 * geometry.kv_heads * geometry.head_dim) * 2
                    before = (0, geometry.hidden,
                              geometry.hidden + geometry.kv_heads * geometry.head_dim)[projection]
                    for out, value in enumerate(bias):
                        self.put(BASES["bias"] + layer * per_layer + 2 * (before + out),
                                 value, 2)
            for which in range(2):
                gamma = [rng.choice((0x3C00, 0x3800, 0x3A00)) for _ in range(geometry.hidden)]
                self.norms[layer, which] = gamma
                for col, value in enumerate(gamma):
                    self.put(BASES["norm"] + 2 * ((layer * 2 + which) * geometry.hidden + col),
                             value, 2)
        self.final_gamma = [0x3C00] * geometry.hidden
        for col, value in enumerate(self.final_gamma):
            self.put(BASES["norm"] + 2 * (2 * geometry.layers * geometry.hidden + col), value, 2)
        for token in range(geometry.vocab):
            row = [rng.choice((0x3000, 0xB000, 0x3400, 0xB400, 0x3800, 0xB800))
                   for _ in range(geometry.hidden)]
            self.embeddings.append(row)
            for col, value in enumerate(row):
                self.put(BASES["embedding"] + 2 * (token * geometry.hidden + col), value, 2)
        for pos in range(geometry.context):
            pairs = []
            for pair in range(geometry.head_dim // 2):
                angle = pos / (10000 ** (2 * pair / geometry.head_dim))
                cosine, sine = round(cos(angle) * (1 << 30)), round(sin(angle) * (1 << 30))
                pairs.append((cosine, sine))
                for component, value in enumerate((cosine, sine)):
                    self.put(BASES["rope"] + 4 * (pos * geometry.head_dim + pair * 2 + component),
                             value & 0xFFFFFFFF, 4)
            self.rope.append(pairs)
        self.extents = {name: offsets[name] - BASES[name] for name in offsets}
        self.extents.update(
            bias=geometry.layers * (geometry.hidden + 2 * geometry.kv_heads * geometry.head_dim) * 2,
            norm=(2 * geometry.layers + 1) * geometry.hidden * 2,
            rope=geometry.context * geometry.head_dim * 4,
            embedding=geometry.vocab * geometry.hidden * 2)
        for name, length in self.extents.items():
            if BASES[name] + length > LIMITS[name]:
                raise ValueError(f"{name} region overflow")

    def put(self, address, value, size):
        for index, byte in enumerate(value.to_bytes(size, "little")):
            if address + index in self.data:
                raise ValueError("overlapping image writes")
            self.data[address + index] = byte

    def records(self):
        addresses = sorted({address & -64 for address in self.data})
        return [(address, bytes(self.data.get(address + i, 0) for i in range(64)))
                for address in addresses]

    @property
    def digest(self):
        digest = sha256()
        for address, record in self.records():
            digest.update(address.to_bytes(8, "little") + record)
        return digest.hexdigest()

    def project(self, layer, projection, activation):
        q, z, scales = self.matrices[layer, projection]
        n, m = self.geometry.shapes[projection]
        bias = self.biases.get((layer, projection), [0] * m)
        return [rounded_shift(sum((q[source][out] - z[source // self.geometry.group][out])
                                  * half_scale(scales[source // self.geometry.group][out])
                                  * activation[source] for source in range(n))
                              + (half_signed(bias[out]) << 16), 16)
                for out in range(m)]


class Inference:
    def __init__(self, image, mode):
        self.image, self.mode = image, mode
        self.cache = [[] for _ in range(image.geometry.layers)]
        self.traces = []

    def token(self, token_id, position, new_sequence=False):
        image, g = self.image, self.image.geometry
        if new_sequence:
            self.cache = [[] for _ in range(g.layers)]
        if not 0 <= token_id < g.vocab or any(len(layer) != position for layer in self.cache):
            raise ValueError("invalid reference token sequence")
        hidden = [half_signed(value) for value in image.embeddings[token_id]]
        trace = []
        for layer in range(g.layers):
            layer_trace = dict(projections={})
            normalized = rmsnorm(hidden, image.norms[layer, 0])
            q, k, v = [image.project(layer, proj, normalized) for proj in range(3)]
            for projection, values in enumerate((q, k, v)):
                layer_trace["projections"][projection] = values[:]
            for values, heads in ((q, g.q_heads), (k, g.kv_heads)):
                for head in range(heads):
                    for pair, (cosine, sine) in enumerate(image.rope[position]):
                        a = head * g.head_dim + pair
                        b = a + g.head_dim // 2
                        x, y = values[a], values[b]
                        values[a] = rounded_shift(x * cosine - y * sine, 30)
                        values[b] = rounded_shift(y * cosine + x * sine, 30)
            k = sum((quantize_vector(k[head * g.head_dim:(head + 1) * g.head_dim], self.mode)
                     for head in range(g.kv_heads)), [])
            v = sum((quantize_vector(v[head * g.head_dim:(head + 1) * g.head_dim], self.mode)
                     for head in range(g.kv_heads)), [])
            self.cache[layer].append((k, v))
            layer_trace["keys"], layer_trace["values"] = k[:], v[:]
            context = []
            divisor = isqrt(g.head_dim << 32)
            for head in range(g.q_heads):
                kv_head = head >> 3
                scores = [rounded_ratio(sum(q[head * g.head_dim + d]
                                            * keys[kv_head * g.head_dim + d]
                                            for d in range(g.head_dim)), divisor)
                          for keys, _ in self.cache[layer]]
                weights = [exponential(score - max(scores)) for score in scores]
                for d in range(g.head_dim):
                    numerator = sum(weight * vals[kv_head * g.head_dim + d]
                                    for weight, (_, vals) in zip(weights, self.cache[layer]))
                    context.append(saturate(rounded_ratio(numerator, sum(weights))))
            attention = image.project(layer, 3, context)
            layer_trace["context"] = context[:]
            layer_trace["projections"][3] = attention[:]
            hidden = [saturate(a + b) for a, b in zip(hidden, attention)]
            normalized = rmsnorm(hidden, image.norms[layer, 1])
            gate, up = [image.project(layer, proj, normalized) for proj in (4, 5)]
            layer_trace["projections"][4], layer_trace["projections"][5] = gate[:], up[:]
            gated = [rounded_shift(silu(a) * b, 16) for a, b in zip(gate, up)]
            down = image.project(layer, 6, gated)
            layer_trace["projections"][6] = down[:]
            hidden = [saturate(a + b) for a, b in zip(hidden, down)]
            trace.append(layer_trace)
        hidden = rmsnorm(hidden, image.final_gamma)
        logits = [rounded_shift(sum(value * half_signed(weight)
                                    for value, weight in zip(hidden, row)), 16)
                  for row in image.embeddings]
        self.traces.append(dict(token=token_id, position=position, layers=trace, logits=logits))
        return logits
