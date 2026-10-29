"""Checkpoint-backed fixed-point network oracle, independent of RTL execution.

The existing Python network equations consume the pinned original safetensors,
not the DUT's repacked image. An owned C++ integer GEMV evaluator accelerates
exact signed-128 accumulation without an installed numerical package. It is
qualified against Python arbitrary-precision arithmetic before checkpoint use.
This produces expected ordered logits, not measured FPGA results or published
floating-point Qwen equivalence. Run through the checkpoint-reference L1 probe;
``python3 -B tests/checkpoint_reference.py --smoke`` prepares just one full
24-layer token per storage mode, explicitly not the five-domain acceptance run.
"""

import argparse
import ctypes
import hashlib
import json
import math
import mmap
from pathlib import Path
import random
import struct
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import project_path, validate
from prompts import FrozenTokenizer, PROMPTS, canonical_chat, merge_heap, merge_scan
from reference import (AWQ_SHIFTS, EngineeringModel, Shape, bf16, fp16, fp_q16,
                       pack_awq, round_shift, sat32)
from repack import PROJECTIONS, fp16_storage, words


CPP = r"""
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <exception>
#include <limits>
#include <stdexcept>
#include <vector>

namespace {
uint64_t away(uint64_t x, unsigned shift) {
    if (shift >= 64) return 0;
    return shift == 0 ? x : (x + (uint64_t(1) << (shift - 1))) >> shift;
}
uint16_t half_storage(uint16_t x, int format) {
    if (format == 0) {
        if ((x & 0x7c00) == 0x7c00) throw std::runtime_error("nonfinite FP16 storage");
        return x;
    }
    unsigned e = (x >> 7) & 255, f = x & 127;
    if (e == 255) throw std::runtime_error("nonfinite BF16 storage");
    if (e >= 143) throw std::runtime_error("BF16 overflows FP16 storage");
    uint16_t sign = x & 0x8000;
    if (e >= 113) return sign | ((e - 112) << 10) | (f << 3);
    uint64_t m = e == 0 ? f : 128 + f;
    int shift = int(e == 0 ? 1 : e) - 110;
    if (shift >= 0) return sign | uint16_t(m << shift);
    unsigned right = unsigned(-shift);
    if (right >= 64) return sign;
    uint64_t q = m >> right, rem = m - (q << right);
    uint64_t tie = uint64_t(1) << (right - 1);
    q += rem > tie || (rem == tie && (q & 1));
    return sign | uint16_t(q);
}
int64_t q16(uint16_t x, bool bfloat, bool scale = false) {
    unsigned fraction_bits = bfloat ? 7 : 10, limit = bfloat ? 255 : 31;
    unsigned e = (x >> fraction_bits) & limit;
    unsigned f = x & ((1u << fraction_bits) - 1);
    if (e == limit) throw std::runtime_error("nonfinite fixed-point input");
    bool negative = (x & 0x8000) != 0;
    if (scale && negative && (e || f)) throw std::runtime_error("negative scale");
    uint64_t m = e == 0 ? f : (1u << fraction_bits) + f;
    int shift = int(e == 0 ? 1 : e) - (bfloat ? 127 : 15) - fraction_bits + 16;
    uint64_t magnitude;
    if (m == 0) magnitude = 0;
    else if (shift >= 0) {
        if (shift >= 32 || m > (uint64_t(0xffffffff) >> shift))
            magnitude = uint64_t(0x100000000);
        else magnitude = m << shift;
    } else magnitude = away(m, unsigned(-shift));
    if (scale) {
        if (magnitude > 0xffffffff) throw std::runtime_error("scale overflows Q16");
        return int64_t(magnitude);
    }
    if (negative) return -int64_t(std::min(magnitude, uint64_t(0x80000000)));
    return int64_t(std::min(magnitude, uint64_t(0x7fffffff)));
}
struct DenseConversions {
    int64_t values[3][65536];
    bool valid[3][65536];
    DenseConversions() {
        for (unsigned format = 1; format <= 3; ++format) {
            for (unsigned bits = 0; bits < 65536; ++bits) {
                unsigned exponent = (bits >> 7) & 255;
                bool finite = format == 2 ? (bits & 0x7c00) != 0x7c00 :
                    exponent != 255 && (format != 3 || exponent < 143);
                valid[format - 1][bits] = finite;
                if (finite)
                    values[format - 1][bits] = format == 1 ? q16(bits, true) :
                        q16(half_storage(bits, format == 3 ? 1 : 0), false);
            }
        }
    }
};
void span(uint64_t size, uint64_t offset, uint64_t bytes) {
    if (offset > size || bytes > size - offset) throw std::runtime_error("tensor bounds");
}
uint16_t little16(const uint8_t* data) {
    return uint16_t(data[0]) | (uint16_t(data[1]) << 8);
}
uint32_t little32(const uint8_t* data) {
    return uint32_t(little16(data)) | (uint32_t(little16(data + 2)) << 16);
}
uint64_t word(const uint8_t* data, uint64_t size, uint64_t offset, unsigned width) {
    if (offset > size || width > size - offset) throw std::runtime_error("tensor bounds");
    uint64_t value = 0;
    for (unsigned i = 0; i < width; ++i) value |= uint64_t(data[offset + i]) << (8 * i);
    return value;
}
int32_t rounded(__int128 value) {
    bool negative = value < 0;
    unsigned __int128 magnitude = negative ? -value : value;
    magnitude = (magnitude + 32768) >> 16;
    if (negative) return -int64_t(std::min(magnitude, (unsigned __int128)0x80000000));
    return int32_t(std::min(magnitude, (unsigned __int128)0x7fffffff));
}
}

extern "C" int convert(uint16_t x, int format, int64_t* result,
                      char* error, size_t capacity) {
    try {
        if (format == 0) *result = q16(x, false);
        else if (format == 1) *result = q16(x, true);
        else if (format == 2) *result = q16(x, false, true);
        else if (format == 3) *result = half_storage(x, 1);
        else throw std::runtime_error("unknown conversion");
        return 0;
    } catch (const std::exception& e) {
        if (capacity) { std::strncpy(error, e.what(), capacity - 1); error[capacity - 1] = 0; }
        return 1;
    }
}

extern "C" int gemv(const uint8_t* data, uint64_t size, int format,
                    unsigned inputs, unsigned outputs, unsigned group,
                    uint64_t w, uint64_t z, uint64_t s, uint64_t bias, int bias_format,
                    const int32_t* activation, int32_t* result,
                    uint64_t* low, int64_t* high, char* error, size_t capacity) {
    try {
        if (!inputs || !outputs || inputs > 4864 || outputs > 151936 ||
            format < 0 || format > 3 || !group || inputs % group)
            throw std::runtime_error("invalid reference GEMV geometry");
        if (format == 0 && outputs % 8) throw std::runtime_error("AWQ packed width");
        span(size, w, uint64_t(inputs) * outputs * (format == 0 ? 1 : 4) / 2);
        if (format == 0) {
            span(size, z, uint64_t(inputs / group) * outputs / 2);
            span(size, s, uint64_t(inputs / group) * outputs * 2);
        }
        if (bias_format >= 0) span(size, bias, uint64_t(outputs) * 2);
        const unsigned shifts[] = {0, 16, 4, 20, 8, 24, 12, 28};
        std::vector<__int128> sums(outputs, 0);
        if (bias_format >= 0) {
            for (unsigned c = 0; c < outputs; ++c) {
                uint16_t bits = word(data, size, bias + 2 * c, 2);
                sums[c] = (__int128)q16(half_storage(bits, bias_format), false) * 65536;
            }
        }
        if (format == 0) {
            std::vector<int64_t> scales(outputs);
            std::vector<unsigned> zeros(outputs);
            std::vector<int64_t> group_sums(outputs);
            for (unsigned begin = 0; begin < inputs; begin += group) {
                for (unsigned c = 0; c < outputs; ++c) {
                    uint64_t packed_index = uint64_t(begin / group) * (outputs / 8) + c / 8;
                    zeros[c] = (little32(data + z + 4 * packed_index)
                                >> shifts[c % 8]) & 15;
                    scales[c] = q16(little16(data +
                                         s + 2 * (uint64_t(begin / group) * outputs + c)),
                                    false, true);
                }
                std::fill(group_sums.begin(), group_sums.end(), 0);
                // At most 4864 * 2^31 * 15: exact in int64, with no rounding.
                for (unsigned r = begin; r < begin + group; ++r) {
                    for (unsigned c = 0; c < outputs; c += 8) {
                        uint32_t packed = little32(data +
                                              w + 4 * (uint64_t(r) * (outputs / 8) + c / 8));
                        for (unsigned lane = 0; lane < 8; ++lane)
                            group_sums[c + lane] += int64_t(activation[r]) *
                                (int((packed >> shifts[lane]) & 15) - int(zeros[c + lane]));
                    }
                }
                for (unsigned c = 0; c < outputs; ++c)
                    sums[c] += (__int128)group_sums[c] * scales[c];
            }
        } else {
            static const DenseConversions table;
            uint64_t maximum = 0;
            for (unsigned r = 0; r < inputs; ++r) {
                int64_t value = activation[r];
                maximum = std::max(maximum, uint64_t(value < 0 ? -value : value));
            }
            // Every converted dense weight has magnitude <= 2^31.
            unsigned block = maximum == 0 ? inputs : unsigned(std::min(
                uint64_t(inputs), uint64_t(0x7fffffffffffffff) / (maximum << 31)));
            for (unsigned c = 0; c < outputs; ++c) {
                for (unsigned begin = 0; begin < inputs; begin += block) {
                    int64_t partial = 0;
                    unsigned end = std::min(inputs, begin + block);
                    for (unsigned r = begin; r < end; ++r) {
                        uint16_t bits = little16(data + w + 2 * (uint64_t(c) * inputs + r));
                        if (!table.valid[format - 1][bits])
                            throw std::runtime_error("invalid dense checkpoint weight");
                        partial += int64_t(activation[r]) * table.values[format - 1][bits];
                    }
                    sums[c] += partial;
                }
            }
        }
        for (unsigned c = 0; c < outputs; ++c) {
            result[c] = rounded(sums[c]);
            low[c] = uint64_t(sums[c]);
            high[c] = int64_t(sums[c] >> 64);
        }
        return 0;
    } catch (const std::exception& e) {
        if (capacity) { std::strncpy(error, e.what(), capacity - 1); error[capacity - 1] = 0; }
        return 1;
    }
}
"""


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


class IntegerGEMV:
    def __init__(self, evidence):
        source = evidence.folder / "integer-gemv.cpp"
        library = evidence.folder / "integer-gemv.so"
        source.write_text(CPP)
        evidence.command(["g++", "--version"], "reference-compiler-version")
        evidence.command(
            ["g++", "-std=c++17", "-O3", "-Wall", "-Wextra", "-Werror",
             "-shared", "-fPIC", evidence.relative(source), "-o", evidence.relative(library)],
            "reference-compiler")
        evidence.record.setdefault("runtime_input_sha256", {}).update({
            evidence.relative(path): sha(path) for path in (source, library)
        })
        self.library = ctypes.CDLL(str(library))
        self.library.gemv.restype = ctypes.c_int
        self.library.gemv.argtypes = [
            ctypes.c_void_p, ctypes.c_uint64, ctypes.c_int, ctypes.c_uint,
            ctypes.c_uint, ctypes.c_uint, *([ctypes.c_uint64] * 4), ctypes.c_int,
            ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_int32),
            ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_int64),
            ctypes.c_char_p, ctypes.c_size_t,
        ]
        self.library.convert.restype = ctypes.c_int
        self.library.convert.argtypes = [
            ctypes.c_uint16, ctypes.c_int, ctypes.POINTER(ctypes.c_int64),
            ctypes.c_char_p, ctypes.c_size_t,
        ]

    def conversion(self, bits, format_id):
        result, error = ctypes.c_int64(), ctypes.create_string_buffer(256)
        status = self.library.convert(bits, format_id, ctypes.byref(result), error, len(error))
        if status:
            raise ValueError(error.value.decode())
        return result.value

    def evaluate(self, data, size, format_id, activation, outputs, group, offsets,
                 bias_format=-1):
        if any(not -(1 << 31) <= value < (1 << 31) for value in activation):
            raise ValueError("activation exceeds signed int32")
        vector = (ctypes.c_int32 * len(activation))(*activation)
        result = (ctypes.c_int32 * outputs)()
        low, high = (ctypes.c_uint64 * outputs)(), (ctypes.c_int64 * outputs)()
        error = ctypes.create_string_buffer(256)
        status = self.library.gemv(
            data, size, format_id, len(activation), outputs, group, *offsets,
            bias_format, vector, result, low, high, error, len(error))
        if status:
            raise ValueError(error.value.decode())
        exact = [(upper << 64) + lower for upper, lower in zip(high, low)]
        return list(result), exact


def qualify(engine, seed):
    compared, rejected = 0, 0
    dense_encodings = {format_id: [] for format_id in (1, 2, 3)}
    dense_expected = {format_id: [] for format_id in (1, 2, 3)}
    dense_invalid = {format_id: [] for format_id in (1, 2, 3)}
    for bits in range(65536):
        for format_id, conversion in (
                (0, fp16), (1, bf16),
                (2, lambda x: fp_q16(x, 5, 10, True)),
                (3, lambda x: fp16_storage(words(x.to_bytes(2, "little"), 2), "BF16")[0][0])):
            dense_format = {0: 2, 1: 1, 3: 3}.get(format_id)
            try:
                expected = conversion(bits)
            except ValueError:
                if dense_format is not None:
                    dense_invalid[dense_format].append(bits)
                try:
                    engine.conversion(bits, format_id)
                except ValueError:
                    rejected += 1
                else:
                    raise AssertionError(f"reference conversion accepted invalid {format_id}/{bits:04x}")
            else:
                if engine.conversion(bits, format_id) != expected:
                    raise AssertionError(f"reference conversion mismatch {format_id}/{bits:04x}")
                compared += 1
                if dense_format is not None:
                    dense_encodings[dense_format].append(bits)
                    dense_expected[dense_format].append(
                        fp16(expected) if format_id == 3 else expected)
    dense_compared = dense_rejected = 0
    for format_id, encodings in dense_encodings.items():
        payload = struct.pack(f"<{len(encodings)}H", *encodings)
        storage = ctypes.create_string_buffer(payload)
        actual, exact = engine.evaluate(
            storage, len(payload), format_id, [65536], len(encodings), 1, (0, 0, 0, 0))
        expected = dense_expected[format_id]
        if actual != expected or exact != [value * 65536 for value in expected]:
            raise AssertionError("dense conversion table differs from exhaustive Python values")
        dense_compared += len(encodings)
        for encoding in dense_invalid[format_id]:
            storage = ctypes.create_string_buffer(struct.pack("<H", encoding))
            try:
                engine.evaluate(storage, 2, format_id, [65536], 1, 1, (0, 0, 0, 0))
            except ValueError:
                dense_rejected += 1
            else:
                raise AssertionError("dense conversion table accepts invalid encoding")
    rng = random.Random(seed)
    coordinates = accumulators = 0
    for inputs, outputs, group in (
            (8, 8, 1), (24, 72, 8), (256, 64, 32), (4864, 8, 4864)):
        activation = [rng.randrange(-(1 << 31), 1 << 31) for _ in range(inputs)]
        activation[:4] = [1, -1, -(1 << 31), (1 << 31) - 1]
        bias_bits = [0x8000, 0x3c00, 0xbc00, 1] * (outputs // 4)
        bias = b"".join(struct.pack("<H", bits) for bits in bias_bits)
        for format_id in range(4):
            if format_id == 0:
                q = [[rng.randrange(16) for _ in range(outputs)] for _ in activation]
                z = [[rng.randrange(16) for _ in range(outputs)] for _ in range(inputs // group)]
                scale = [[rng.choice((0x8000, 1, 0x3c00, 0x7bff)) for _ in range(outputs)]
                         for _ in z]
                weight = [[(q[r][c] - z[r // group][c]) *
                           fp_q16(scale[r // group][c], 5, 10, True)
                           for c in range(outputs)] for r in range(inputs)]
                chunks = [b"".join(struct.pack("<I", word) for row in matrix for word in pack_awq(row))
                          for matrix in (q, z)]
                chunks.append(b"".join(struct.pack("<H", bit) for row in scale for bit in row))
                offsets = (0, len(chunks[0]), len(chunks[0]) + len(chunks[1]),
                           sum(map(len, chunks)))
                data = b"".join(chunks) + bias
            else:
                encodings = ((0, 0x8000, 1, 0x007f, 0x3f80, 0xbf80, 0x7f7f)
                             if format_id == 1 else
                             (0, 0x8000, 1, 0x03ff, 0x3c00, 0xbc00, 0x7bff)
                             if format_id == 2 else
                             (0, 0x8000, 0x3300, 0x3380, 0x3881, 0x3f80, 0xbf80))
                bits = [[rng.choice(encodings) for _ in activation] for _ in range(outputs)]
                conversion = bf16 if format_id == 1 else fp16 if format_id == 2 else (
                    lambda value: fp16(fp16_storage(words(struct.pack("<H", value), 2), "BF16")[0][0]))
                weight = [[conversion(bits[c][r]) for c in range(outputs)] for r in range(inputs)]
                payload = b"".join(struct.pack("<H", value) for row in bits for value in row)
                offsets = (0, 0, 0, len(payload))
                data = payload + bias
            storage = ctypes.create_string_buffer(data)
            for biased in (False, True):
                result, exact = engine.evaluate(
                    storage, len(data), format_id, activation, outputs, group,
                    offsets, 0 if biased else -1)
                expected = [sum(a * row[c] for a, row in zip(activation, weight)) +
                            (fp16(bias_bits[c]) << 16 if biased else 0) for c in range(outputs)]
                if exact != expected or result != [sat32(round_shift(x, 16)) for x in expected]:
                    raise AssertionError("C++ reference differs from independent exact Python dot")
                coordinates += inputs * outputs
                accumulators += outputs
            try:
                engine.evaluate(storage, 0, format_id, activation, outputs, group, offsets)
            except ValueError:
                rejected += 1
            else:
                raise AssertionError("reference evaluator accepted out-of-range tensor")
    return {"finite_conversion_comparisons": compared, "invalid_inputs_rejected": rejected,
            "mathematical_weight_coordinates": coordinates, "exact_accumulators_compared": accumulators,
            "dense_table_conversion_comparisons": dense_compared,
            "dense_table_invalid_encodings_rejected": dense_rejected}


class Embedding:
    def __init__(self, model):
        self.model = model

    def __getitem__(self, index):
        if not 0 <= index < self.model.shape.vocab:
            raise IndexError("embedding token")
        return self.model.half_values("model.embed_tokens.weight", index * 896, 896)


class Rope:
    def __init__(self, theta):
        self.frequencies = [theta ** (-2 * pair / 64) for pair in range(32)]

    def __getitem__(self, position):
        values = []
        for frequency in self.frequencies:
            for value in (math.cos(position * frequency), math.sin(position * frequency)):
                magnitude = math.floor(abs(value) * (1 << 30) + 0.5)
                values.append(-magnitude if value < 0 else magnitude)
        return values


class CheckpointModel(EngineeringModel):
    def __init__(self, root, metadata, mode, engine):
        self.shape = Shape(24, 896, 4864, 14, 2, 64, 128, 151936, 32768, 256, 128)
        self.mode, self.engine, self.metadata = mode, engine, metadata
        self.folder = root / mode.lower()
        self.source = (self.folder / "model.safetensors").open("rb")
        self.mapping = mmap.mmap(self.source.fileno(), 0, access=mmap.ACCESS_COPY)
        self.pointer = ctypes.addressof(ctypes.c_ubyte.from_buffer(self.mapping))
        self.embedding, self.gamma = Embedding(self), {}
        self.history = [[] for _ in range(24)]
        self.rope = Rope(json.loads((self.folder / "config.json").read_text())["rope_theta"])
        self.gemv_calls, self.sample_comparisons = 0, 0
        for layer in range(24):
            for kind, suffix in ((5, "input_layernorm.weight"), (6, "post_attention_layernorm.weight")):
                self.gamma[layer, kind] = self.half_values(f"model.layers.{layer}.{suffix}", 0, 896)
        self.gamma[0, 7] = self.half_values("model.norm.weight", 0, 896)

    def close(self):
        self.mapping.close()
        self.source.close()

    def tensor(self, name):
        return self.metadata["inventory"]["tensors"][name]

    def offset(self, name):
        return 8 + self.metadata["inventory"]["header_bytes"] + self.tensor(name)["data_offsets"][0]

    def half_values(self, name, start, count):
        offset = self.offset(name) + 2 * start
        item = self.tensor(name)
        if start < 0 or count < 0 or 2 * (start + count) > item["data_offsets"][1] - item["data_offsets"][0]:
            raise ValueError("checkpoint half-value bounds")
        return list(fp16_storage(words(self.mapping[offset:offset + 2 * count], 2), item["dtype"])[0])

    def projection(self, vector, layer, proj):
        prefix = f"model.layers.{layer}.{PROJECTIONS[proj]}."
        inputs = self.shape.intermediate if proj == 6 else self.shape.hidden
        outputs = (self.shape.kv if proj in (1, 2) else self.shape.intermediate
                   if proj in (4, 5) else self.shape.hidden)
        if len(vector) != inputs:
            raise ValueError("checkpoint projection activation shape mismatch")
        offsets = ((self.offset(prefix + "qweight"), self.offset(prefix + "qzeros"),
                    self.offset(prefix + "scales")) if self.mode == "AWQ" else
                   (self.offset(prefix + "weight"), 0, 0))
        bias_format = -1
        bias_offset = 0
        if proj < 3:
            bias_offset = self.offset(prefix + "bias")
            bias_format = int(self.tensor(prefix + "bias")["dtype"] == "BF16")
        result, exact = self.engine.evaluate(
            self.pointer, len(self.mapping), int(self.mode == "BF16"), vector, outputs, 128,
            (*offsets, bias_offset), bias_format)
        # Direct original-checkpoint coordinate checks bind the accelerated path
        # independently of the physical panel repacker and its addressing.
        if self.gemv_calls < 168:
            columns = sorted({0, 1, 7, 8, outputs // 2, outputs - 1})
            for col in columns:
                total = 0
                for row, activation in enumerate(vector):
                    if self.mode == "AWQ":
                        qword = struct.unpack_from("<I", self.mapping,
                                                  offsets[0] + 4 * (row * (outputs // 8) + col // 8))[0]
                        zword = struct.unpack_from("<I", self.mapping,
                                                  offsets[1] + 4 * ((row // 128) * (outputs // 8) + col // 8))[0]
                        scale = struct.unpack_from("<H", self.mapping,
                                                   offsets[2] + 2 * ((row // 128) * outputs + col))[0]
                        weight = ((qword >> AWQ_SHIFTS[col % 8] & 15) -
                                  (zword >> AWQ_SHIFTS[col % 8] & 15)) * fp_q16(scale, 5, 10, True)
                    else:
                        bits = struct.unpack_from("<H", self.mapping,
                                                  offsets[0] + 2 * (col * inputs + row))[0]
                        weight = bf16(bits)
                    total += activation * weight
                if proj < 3:
                    total += fp16(self.half_values(prefix + "bias", col, 1)[0]) << 16
                if exact[col] != total or result[col] != sat32(round_shift(total, 16)):
                    raise AssertionError("checkpoint GEMV differs from original-coordinate Python reference")
                self.sample_comparisons += 1
        self.gemv_calls += 1
        return result

    def vocabulary(self, final):
        name = "model.embed_tokens.weight"
        format_id = 3 if self.tensor(name)["dtype"] == "BF16" else 2
        result, exact = self.engine.evaluate(
            self.pointer, len(self.mapping), format_id, final, 151936, 128,
            (self.offset(name), 0, 0, 0))
        for token in (0, 1, 7, 63, 64, 65535, 151935):
            total = sum(a * fp16(b) for a, b in zip(final, self.embedding[token]))
            if exact[token] != total or result[token] != sat32(round_shift(total, 16)):
                raise AssertionError("checkpoint tied-embedding logit reference mismatch")
            self.sample_comparisons += 1
        return result


def prepare(evidence, smoke=False, seed=17, modes=("AWQ", "BF16")):
    evidence.command(["python3", "--version"], "reference-python-version")
    evidence.command(["python3", "tests/fixtures.py"], "reference-fixture-validation")
    root = project_path("fixtures/qwen2.5-0.5b")
    metadata = validate(root)
    evidence.record.setdefault("runtime_input_sha256", {}).update({
        str(root / "manifest.json"): sha(root / "manifest.json"),
    })
    for mode in modes:
        model = metadata["models"][mode]
        evidence.record["runtime_input_sha256"].update({
            str(root / mode.lower() / name): record["sha256"]
            for name, record in model["files"].items()
        })
        evidence.record["runtime_input_sha256"][str(root / model["metadata_file"])] = (
            model["metadata_sha256"])
    engine = IntegerGEMV(evidence)
    evidence.record["reference_qualification"] = qualify(engine, seed)
    evidence.flush()
    transcript = {"schema": 1, "scope": "checkpoint_fixed_point_reference_not_RTL_or_board",
                  "smoke_only": smoke, "rows": [], "ordered_logit_vectors": 0,
                  "physical_board_runs": 0, "FPGA_cycles_measured": 0,
                  "floating_point_software_discrepancy": "not_yet_measured"}
    for mode in modes:
        model = CheckpointModel(root, metadata["models"][mode], mode, engine)
        folder = root / mode.lower()
        tokenizer = FrozenTokenizer(json.loads((folder / "tokenizer.json").read_text()),
                                    json.loads((folder / "tokenizer_config.json").read_text()))
        prompts = PROMPTS[:1] if smoke else PROMPTS
        try:
            for prompt_index, prompt in enumerate(prompts):
                starting_calls, starting_compares = model.gemv_calls, model.sample_comparisons
                text = canonical_chat(prompt)
                prefill = tokenizer.encode(text, merge_heap)
                if prefill != tokenizer.encode(text, merge_scan):
                    raise AssertionError("independent prompt tokenizer mismatch")
                if smoke:
                    prefill = prefill[:1]
                row = {"mode": mode, "repository": metadata["models"][mode]["repository"],
                       "revision": metadata["models"][mode]["revision"],
                       "checkpoint_sha256": metadata["models"][mode]["tensor_sha256"],
                       "prompt_index": prompt_index, "prompt": prompt,
                       "prefill_token_ids": prefill, "decode_token_ids": [], "steps": []}
                transcript["rows"].append(row)
                total = len(prefill) + (0 if smoke else 15)
                token = prefill[0]
                for position in range(total):
                    if position < len(prefill):
                        token = prefill[position]
                    started = time.monotonic()
                    logits = model.token(token, position, position == 0)
                    if len(logits) != 151936:
                        raise AssertionError("incomplete ordered vocabulary reference")
                    selected = max(range(151936), key=lambda index: (logits[index], -index))
                    output = evidence.folder / f"{mode.lower()}-prompt{prompt_index}-pos{position}-logits.bin"
                    payload = struct.pack("<151936i", *logits)
                    with output.open("xb") as stream:
                        stream.write(payload)
                    relative = evidence.relative(output)
                    evidence.record["runtime_input_sha256"][relative] = hashlib.sha256(payload).hexdigest()
                    row["steps"].append({
                        "position": position, "input_token": token, "selected_token": selected,
                        "phase": "prefill" if position < len(prefill) else "decode",
                        "ordered_logits": relative, "logits_sha256": hashlib.sha256(payload).hexdigest(),
                        "ordered_logit_count": len(logits),
                        "reference_wall_seconds_not_FPGA_performance": time.monotonic() - started,
                    })
                    if position >= len(prefill) - 1:
                        row["decode_token_ids"].append(selected)
                    token = selected
                    transcript["ordered_logit_vectors"] += 1
                    print(json.dumps({"reference_mode": mode, "prompt": prompt_index,
                                      "position": position, "greedy_token": selected,
                                      "ordered_logits": len(logits)}), flush=True)
                    progress = evidence.folder / f"reference-progress-{mode.lower()}-{prompt_index}-{position}.json"
                    with progress.open("x") as stream:
                        json.dump(row["steps"][-1], stream, indent=2)
                    evidence.flush()
                if not smoke and len(row["decode_token_ids"]) != 16:
                    raise AssertionError("reference did not produce sixteen consecutive greedy tokens")
                row.update(exact_projection_calls=model.gemv_calls - starting_calls,
                           python_checkpoint_coordinate_comparisons=(
                               model.sample_comparisons - starting_compares))
        finally:
            model.close()
    output = evidence.folder / "checkpoint-reference.json"
    with output.open("x") as stream:
        json.dump(transcript, stream, indent=2)
        stream.write("\n")
    evidence.record["runtime_input_sha256"][evidence.relative(output)] = sha(output)
    evidence.record["observations"].append({
        "scope": transcript["scope"], "manifest": evidence.relative(output),
        "smoke_only": smoke, "modes": list(modes),
        "ordered_logit_vectors": transcript["ordered_logit_vectors"],
        "complete_default_model_layers": 24, "full_model_acceptance": False,
        "limitations": ["Reference outputs have not been compared to FPGA execution.",
                        "Published floating-point model discrepancy remains unmeasured.",
                        "No DDR service, timing, physical resources or throughput measured."],
    })
    evidence.flush()


def main():
    from verify import Evidence
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--mode", choices=("AWQ", "BF16"),
                        help="bounded reference preparation for one mode; L1 still requires both")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    evidence = Evidence("checkpoint-reference-smoke" if args.smoke else "checkpoint-reference",
                        repair_of=args.repair_of)
    try:
        prepare(evidence, args.smoke, modes=(args.mode,) if args.mode else ("AWQ", "BF16"))
        evidence.finish("probe_passed", "Checkpoint mathematical reference only, not RTL acceptance.")
        return 0
    except Exception as exc:
        evidence.finish("probe_failed", f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
