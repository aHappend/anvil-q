"""Lazy native-shape synthetic tensors and compact independent numerical models.

Repeated *mathematical tensor values* permit exact reference-row reuse. This
does not reduce DUT dimensions, requests, operations or measured hardware time.
The parent is AWQ-only and retains its different fixed-point numerical ABI.
"""

from array import array
from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
import math
import struct
import sys

from codec_checks import SHIFTS
from fp_reference import convert, rounded, rope_coefficients, rope_real, value
from parent_reference import ParentTransformer, half_away, q16, sat
from transformer_reference import Geometry, Transformer, coordinates, key


def native_geometry():
    return Geometry(layers=28, hidden=1536, intermediate=8960, q_heads=12,
                    kv_heads=2, head_dim=128, group=128, vocabulary=151936,
                    positions=8, block=16)


@lru_cache(maxsize=4096)
def tensor(numerator, denominator, fmt):
    return rounded(Fraction(numerator, denominator), fmt)


@lru_cache(maxsize=4096)
def expand_tensor(bits, fmt):
    return convert(bits, fmt)


@lru_cache(maxsize=16384)
def as_float(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def float_bits(number):
    if math.isnan(number):
        return 0x7FC00000
    try:
        return struct.unpack(">I", struct.pack(">f", number))[0]
    except OverflowError:
        return 0xFF800000 if number < 0 else 0x7F800000


def host_add(a, b):
    """Two binary32 operands: binary64 has ample precision for binary32 RNE."""
    return float_bits(as_float(a) + as_float(b))


def host_multiply(a, b):
    """A binary32 significand product has at most 48 significant bits."""
    return float_bits(as_float(a) * as_float(b))


def require_ieee_host():
    assert sys.float_info.radix == 2 and sys.float_info.mant_dig == 53, (
        "native reference requires IEEE binary64 Python floats")
    assert host_add(0x3F800000, 0x33800000) == 0x3F800000
    assert host_add(0x3F800001, 0x33800000) == 0x3F800002
    assert host_multiply(1, 0x3F000000) == 0
    assert host_multiply(3, 0x3F000000) == 2


class TensorMemory:
    """Read-only ABI service; no materialized vocabulary or projection matrix."""

    def __init__(self, fmt, weight_mode, seed, geometry, parent=False):
        self.fmt, self.weight_mode, self.seed, self.g = fmt, weight_mode, seed, geometry
        self.parent = parent
        if parent:
            assert fmt == "fp16" and weight_mode == 1, "no native-weight parent baseline"

    def shape(self, proj):
        g = self.g
        assert 0 <= proj < 7
        return (g.intermediate if proj == 6 else g.hidden,
                g.kv_heads * g.head_dim if proj in (1, 2) else
                g.intermediate if proj in (4, 5) else g.hidden)

    def delta(self, layer, proj, column, row):
        return (3 * self.seed + 5 * layer + 7 * proj + 11 * column + 13 * row) % 7 - 3

    def zero(self, layer, proj, group, row):
        return 3 + (self.seed + layer + proj + 3 * group + 5 * row) % 9

    def scale_denominator(self, layer, proj, group, row):
        return 128 << ((self.seed + layer + proj + group + row) % 2)

    def effective_weight(self, layer, proj, column, row):
        return tensor(self.delta(layer, proj, column, row),
                      self.scale_denominator(layer, proj, column // self.g.group, row), self.fmt)

    def __getitem__(self, address):
        if type(address) is not int or not 0 <= address < 2**103:
            raise KeyError("memory address is not an unsigned 103-bit coordinate")
        kind, layer, proj, row, col = coordinates(address)
        g = self.g
        if kind == 0 and layer == proj == 0 and row < g.vocabulary and col < g.hidden:
            return tensor((self.seed + 11 * row + 7 * col) % 33 - 16, 31, self.fmt)
        if kind in (1, 2, 3, 4) and layer < g.layers and proj < 7:
            inputs, outputs = self.shape(proj)
            if kind == 1 and row < inputs:
                if self.weight_mode == 0 and col < outputs:
                    return self.effective_weight(layer, proj, row, col)
                if self.weight_mode == 1 and col < (outputs + 7) // 8:
                    group = row // g.group
                    return sum((self.zero(layer, proj, group, output) +
                                self.delta(layer, proj, row, output)) << SHIFTS[j]
                               for j in range(8) if (output := 8 * col + j) < outputs)
            if self.weight_mode == 1 and row < inputs // g.group:
                if kind == 2 and col < (outputs + 7) // 8:
                    return sum(self.zero(layer, proj, row, output) << SHIFTS[j]
                               for j in range(8) if (output := 8 * col + j) < outputs)
                if kind == 3 and col < outputs:
                    return tensor(1, self.scale_denominator(layer, proj, row, col), self.fmt)
            if kind == 4 and proj < 3 and row == 0 and col < outputs:
                return tensor((self.seed + 3 * layer + 5 * proj + col) % 9 - 4, 256, self.fmt)
        if (kind in (5, 6, 7) and layer < g.layers and (kind != 7 or layer == 0) and
                proj == row == 0 and col < g.hidden):
            return tensor(64 + (self.seed + kind + layer + col) % 5 - 2, 64, self.fmt)
        if (kind == 11 and layer == proj == 0 and row < g.positions and col < g.head_dim):
            if self.parent:
                real = rope_real(row, col // 2, g.head_dim)[col % 2]
                return half_away(Fraction(real) * 2**30) & 0xFFFFFFFF
            return rope_coefficients(row, col // 2, g.head_dim)[col % 2]
        raise KeyError(f"unavailable or illegal model coordinate: {coordinates(address)}")


class CompactLogits:
    def __init__(self, vocabulary):
        self.vocabulary = vocabulary
        self.bits = array("I")

    def append(self, item):
        position, row, bits = item
        assert (position, row) == divmod(len(self.bits), self.vocabulary)
        self.bits.append(bits)

    def __len__(self):
        return len(self.bits)

    def __iter__(self):
        for index, bits in enumerate(self.bits):
            position, row = divmod(index, self.vocabulary)
            yield position, row, bits


class NativeTransformer(Transformer):
    """The same normative graph, using periodic rows and compact observations."""

    def __init__(self, fmt, weight_mode, cache_mode, seed, geometry=None):
        require_ieee_host()
        assert array("I").itemsize == 4, "compact oracle requires 32-bit unsigned array elements"
        super().__init__(fmt, weight_mode, cache_mode, seed, geometry or native_geometry())
        self.writes = defaultdict(lambda: array("I"))
        self.logits = CompactLogits(self.g.vocabulary)
        self._output_cache = {}

    def _tensors(self):
        self.loads = TensorMemory(self.fmt, self.weight_mode, self.seed, self.g)
        self.weights, self.biases, self.norms = {}, {}, {}
        for layer in range(self.g.layers):
            for kind in (5, 6, 7):
                if kind != 7 or layer == 0:
                    self.norms[layer, kind] = [
                        expand_tensor(self.loads[key(kind, layer, col=col)], self.fmt)
                        for col in range(self.g.hidden)]
            for proj in range(7):
                outputs = self.loads.shape(proj)[1]
                self.biases[layer, proj] = [
                    expand_tensor(self.loads[key(4, layer, proj, col=row)], self.fmt)
                    for row in range(outputs)] if proj < 3 else []

    def store(self, slot, vector, domain, layer, position):
        encoded = array("I", (bits & 0xFFFFFFFF for bits in vector))
        for col, bits in enumerate(encoded):
            self.writes[key(8, row=slot, col=col)].append(bits)
        self.stages.append(dict(domain=domain, layer=layer, position=position, slot=slot, bits=encoded))
        if slot == 14:
            self._output_cache.clear()
        return vector

    def projection(self, vector, layer, proj):
        inputs, outputs = self.loads.shape(proj)
        assert len(vector) == inputs
        activation = [self.a16(bits) for bits in vector]
        totals = []
        # delta has period 7 and scale parity has period 2 in the output row.
        for row in range(min(outputs, 14)):
            total = 0
            for column, a in enumerate(activation):
                b = expand_tensor(self.loads.effective_weight(layer, proj, column, row), self.fmt)
                total = host_add(total, host_multiply(a, b))
            totals.append(total)
        return [host_add(totals[row % 14], self.biases[layer, proj][row]) if proj < 3
                else totals[row % 14] for row in range(outputs)]

    def output_dot(self, norm, row):
        # Embedding/output values repeat after three vocabulary rows.
        pattern = row % 3
        if pattern not in self._output_cache:
            total = 0
            for col, x in enumerate(norm):
                w = expand_tensor(self.loads[key(0, row=pattern, col=col)], self.fmt)
                total = host_add(total, host_multiply(self.a16(x), w))
            self._output_cache[pattern] = total
        return self._output_cache[pattern]

    def manifest(self):
        result = super().manifest()
        result.update(
            shape_class="native" if self.g == native_geometry() else "reduced-for-self-check",
            reference_storage="lazy model tensors; compact uint32 write/logit observations",
            reference_row_reuse="exact period-14 projection sums and period-3 output rows",
            max_seq_len_parameter=32768 if self.g == native_geometry() else self.g.positions,
            scope="Independent synthetic numerical reference, not evidence of DUT execution.")
        return result


class NativeParentTransformer(ParentTransformer, NativeTransformer):
    """Native-size real-parent AWQ ABI, without allocating native weight matrices."""

    def _tensors(self):
        NativeTransformer._tensors(self)
        self.loads.parent = True
        self.norms = {address: [q16(value(bits)) for bits in vector]
                      for address, vector in self.norms.items()}
        self.biases = {address: [q16(value(bits)) for bits in vector]
                       for address, vector in self.biases.items()}

    store = NativeTransformer.store

    def projection(self, vector, layer, proj):
        inputs, outputs = self.loads.shape(proj)
        assert len(vector) == inputs
        totals = [
            sum(a * q16(value(self.loads.effective_weight(layer, proj, column, row), "fp16"))
                for column, a in enumerate(vector))
            for row in range(min(outputs, 14))]
        return [sat(half_away(Fraction(
            totals[row % 14] + (self.biases[layer, proj][row] << 16 if proj < 3 else 0), 65536)))
            for row in range(outputs)]

    def output_dot(self, norm, row):
        pattern = row % 3
        if pattern not in self._output_cache:
            total = sum(a * b for a, b in zip(norm, self.embedding(pattern)))
            self._output_cache[pattern] = sat(half_away(Fraction(total, 65536))) & 0xFFFFFFFF
        return self._output_cache[pattern]
