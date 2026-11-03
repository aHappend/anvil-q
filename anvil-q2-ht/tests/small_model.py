"""Independent deterministic small-geometry models, never official checkpoints."""

from fractions import Fraction
from math import cos, sin, isqrt
import random
import struct

from reference import (array_result, cache_roundtrip, exp_q24, fp32_add, fraction_q16,
                       ieee_round, ieee_value, rhaz, rms_norm, rounded_div, sat32, swiglu)

CELLS = {
    "small": dict(layers=1, hidden=8, intermediate=8, query_heads=1, kv_heads=1,
                  head_dim=8, group=1, cache_block=1, vocabulary=3, sequence=3,
                  hot_blocks=3, queue=3, slots=4, outstanding=8, image_bytes=32768),
    "phase": dict(layers=1, hidden=8, intermediate=8, query_heads=1, kv_heads=1,
                  head_dim=8, group=1, cache_block=1, vocabulary=3, sequence=4,
                  hot_blocks=3, queue=3, slots=4, outstanding=8, image_bytes=32768),
    "singleton": dict(layers=1, hidden=8, intermediate=8, query_heads=1, kv_heads=1,
                      head_dim=8, group=1, cache_block=1, vocabulary=1, sequence=1,
                      hot_blocks=1, queue=1, slots=2, outstanding=1, image_bytes=32768),
    "nonpower": dict(layers=2, hidden=24, intermediate=24, query_heads=3, kv_heads=1,
                     head_dim=8, group=1, cache_block=1, vocabulary=3, sequence=3,
                     hot_blocks=3, queue=3, slots=4, outstanding=8, image_bytes=131072),
    "block16": dict(layers=1, hidden=128, intermediate=128, query_heads=1, kv_heads=1,
                    head_dim=128, group=128, cache_block=16, vocabulary=1, sequence=1,
                    hot_blocks=1, queue=1, slots=4, outstanding=8, image_bytes=262144),
}


def fixture(weight_mode, cache_mode, seed=11, cell="small", bias_stress=False,
            tied_head=False, bias_boundary=False, observations=None):
    if bias_boundary and (weight_mode != 1 or cell != "small" or bias_stress or tied_head):
        raise ValueError("direct BF16 bias boundary requires the untied small BF16 fixture")
    geometry = CELLS[cell]
    if observations is not None:
        observations.update(vectors=[], cache=[])
    hidden = geometry["hidden"]
    intermediate = geometry["intermediate"]
    vocabulary = geometry["vocabulary"]
    sequence = geometry["sequence"]
    dimension = geometry["head_dim"]
    kv_width = geometry["kv_heads"] * dimension
    group = geometry["group"]
    layers = geometry["layers"]
    cache_block = geometry["cache_block"]
    rng = random.Random(seed)
    memory = bytearray(geometry["image_bytes"])
    descriptors = [[0] * 16 for _ in range(16 + 16 * layers)]
    plain_words = {}
    cursor = 0

    def allocate(data):
        nonlocal cursor
        cursor = (cursor + 63) & ~63
        base = cursor
        memory[base:base + len(data)] = data
        cursor += len(data)
        if cursor > len(memory):
            raise ValueError("fixture capacity exceeded")
        return base

    def descriptor(index, base, length, rows, cols, stride, fmt,
                   zeros=0, scales=0, zero_stride=0, scale_stride=0):
        raw = struct.pack("<QQQQIIIIIIQ", base, length, zeros, scales, rows, cols,
                          stride, zero_stride, scale_stride, 0x100 | fmt, 0)
        descriptors[index] = list(struct.unpack("<16I", raw))

    def plain(index, rows, cols, values, fmt=None):
        fmt = (2 if weight_mode else 1) if fmt is None else fmt
        words = [ieee_round(value, 8, 7) if fmt == 2 else ieee_round(value, 5, 10)
                 for value in values]
        plain_words[index] = words
        raw = struct.pack("<" + "H" * len(words), *words)
        base = allocate(raw)
        descriptor(index, base, len(raw), rows, cols, cols * 2, fmt)
        return [fraction_q16(ieee_value(word, 8, 7) if fmt == 2 else ieee_value(word, 5, 10))
                for word in words]

    embedding_values = [Fraction(rng.randint(-8, 8), 8) for _ in range(vocabulary * hidden)]
    head_values = [Fraction(rng.randint(-4, 4), 8) for _ in range(vocabulary * hidden)]
    if bias_boundary:
        embedding_values = [Fraction(1, 65536) if i % hidden == 0 else Fraction(0)
                            for i in range(vocabulary * hidden)]
        head_values = [Fraction(1) if i % hidden == 0 else Fraction(0)
                       for i in range(vocabulary * hidden)]
    embeddings = plain(0, vocabulary, hidden, embedding_values)
    head = plain(1, vocabulary, hidden, head_values)
    if tied_head:
        head = embeddings
        descriptors[1] = list(descriptors[0])
    gamma_value = Fraction(1, 1024) if bias_boundary else Fraction(1)
    gamma = plain(2, 1, hidden, [gamma_value] * hidden)
    rope = []
    for position in range(sequence):
        row = []
        for i in range(dimension // 2):
            angle = position * (1000000 ** (-2 * i / dimension))
            row.extend((round(cos(angle) * (1 << 30)), round(sin(angle) * (1 << 30))))
        rope.append(row)
    raw_rope = struct.pack("<" + "i" * (sequence * dimension),
                           *(word for row in rope for word in row))
    base = allocate(raw_rope)
    descriptor(3, base, len(raw_rope), sequence, dimension, dimension * 4, 3)
    matrices = []
    biases = []
    for layer in range(layers):
        layer_matrices = []
        shapes = ((hidden, hidden), (kv_width, hidden), (kv_width, hidden),
                  (hidden, hidden), (intermediate, hidden), (intermediate, hidden),
                  (hidden, intermediate))
        for projection_number, (rows, cols) in enumerate(shapes):
            signed_weights = [[rng.randint(-3, 3) for _ in range(cols)] for _ in range(rows)]
            if bias_boundary:
                signed_weights = [[0] * cols for _ in range(rows)]
                if projection_number == 2:
                    signed_weights[0][0] = 4
                elif projection_number == 3:
                    for i in range(min(rows, cols)):
                        signed_weights[i][i] = 16
            layer_matrices.append(signed_weights)
            input_tiles = (cols + 127) // 128
            tiles = ((rows + 15) // 16) * input_tiles
            tile_bytes = 4096 if weight_mode else 1024
            raw = bytearray(tiles * tile_bytes)
            for row in range(rows):
                for col in range(cols):
                    element = (((row // 16) * input_tiles + col // 128) * 2048
                               + (row % 16) * 128 + col % 128)
                    if weight_mode:
                        word = ieee_round(Fraction(signed_weights[row][col], 16), 8, 7)
                        struct.pack_into("<H", raw, element * 2, word)
                    else:
                        raw[element // 2] |= ((signed_weights[row][col] + 8)
                                             << (4 * (element & 1)))
            base = allocate(raw)
            index = 16 + 16 * layer + projection_number
            if weight_mode:
                descriptor(index, base, len(raw), rows, cols, tile_bytes, 2)
            else:
                groups = cols // group
                zero_stride = (groups + 1) // 2
                zero_base = allocate(bytes([0x88] * (rows * zero_stride)))
                scale_word = ieee_round(Fraction(1, 16), 5, 10)
                scales = rows * groups
                scale_base = allocate(struct.pack("<" + "H" * scales,
                                                   *([scale_word] * scales)))
                descriptor(index, base, len(raw), rows, cols, tile_bytes, 0,
                           zero_base, scale_base, zero_stride, groups * 2)
        matrices.append(layer_matrices)
        plain(23 + 16 * layer, 1, hidden, [gamma_value] * hidden)
        plain(24 + 16 * layer, 1, hidden, [gamma_value] * hidden)
        layer_biases = []
        for number, width in enumerate((hidden, kv_width, kv_width)):
            data = [Fraction(rng.randint(-2, 2), 16) for _ in range(width)]
            if bias_boundary:
                data = [Fraction(1, 262144) if number == 2 and i == 0 else Fraction(0)
                        for i in range(width)]
            elif bias_stress:
                data = [Fraction((i + number) % 7 - 3, 1 << (17 + i % 4)) for i in range(width)]
            layer_biases.append(plain(25 + 16 * layer + number, 1, width, data))
        biases.append(layer_biases)

    def projection(x, layer, number):
        outputs = []
        for row, weights in enumerate(matrices[layer][number]):
            if weight_mode:
                chunks = []
                for start in range(0, len(x), 128):
                    count = min(128, len(x) - start)
                    weights_bf = [ieee_round(Fraction(w, 16), 8, 7)
                                  for w in weights[start:start + count]] + [0] * (128 - count)
                    _, chunk, error = array_result(
                        1, (1 << count) - 1, x[start:start + count] + [0] * (128 - count),
                        [0] * 128, [0] * 128, [0] * 128, weights_bf)
                    if error:
                        raise ArithmeticError("nonfinite synthetic projection")
                    chunks.append(chunk)
                result = chunks[0]
                for chunk in chunks[1:]:
                    result = fp32_add(result, chunk)
                if number < 3:
                    bias_word = plain_words[25 + 16 * layer + number][row] << 16
                    result = fp32_add(result, bias_word)
                outputs.append(fraction_q16(ieee_value(result, 8, 23)))
            else:
                total = sum(a * w * 4096 for a, w in zip(x, weights))
                if number < 3:
                    total += biases[layer][number][row] << 16
                outputs.append(sat32(rhaz(total, 16)))
        return outputs

    def rotate(values, position):
        output = list(values)
        for start in range(0, len(values), dimension):
            for i in range(dimension // 2):
                c, s = rope[position][i * 2:i * 2 + 2]
                a, b = values[start + i], values[start + i + dimension // 2]
                output[start + i] = sat32(rhaz(a * c - b * s, 30))
                output[start + i + dimension // 2] = sat32(rhaz(b * c + a * s, 30))
        return output

    keys, values = [[] for _ in range(layers)], [[] for _ in range(layers)]
    logits = []

    def observe(name, domain, ht_vector, parent_vector, data, position, layer):
        if observations is not None:
            observations["vectors"].append({
                "name": name, "domain": domain, "ht_vector": ht_vector,
                "parent_vector": parent_vector, "values": list(data),
                "position": position, "layer": layer})

    for position in range(min(3, sequence)):
        token = position % vocabulary
        x = embeddings[token * hidden:(token + 1) * hidden]
        observe("embedding", "D5", 0, 0, x, position, 0)
        for layer in range(layers):
            norm = rms_norm(x, gamma)
            observe("attention-norm", "D2", 1, 1, norm, position, layer)
            q, k, v = [projection(norm, layer, number) for number in range(3)]
            for number, data in enumerate((q, k, v)):
                observe(("Q", "K", "V")[number], "D1", number + 2, number + 2,
                        data, position, layer)
            q, k = rotate(q, position), rotate(k, position)
            observe("Q-RoPE", "D2", 2, 2, q, position, layer)
            observe("K-RoPE", "D2", 3, 3, k, position, layer)
            keys[layer].append(cache_roundtrip(k, cache_mode, cache_block))
            values[layer].append(cache_roundtrip(v, cache_mode, cache_block))
            if observations is not None:
                observations["cache"].append({
                    "layer": layer, "position": position, "raw_key": k, "raw_value": v,
                    "key": keys[layer][-1], "value": values[layer][-1]})
            attention = []
            for query in range(geometry["query_heads"]):
                kv_head = query // (geometry["query_heads"] // geometry["kv_heads"])
                query_values = q[query * dimension:(query + 1) * dimension]
                scores = [rounded_div(
                    sum(a * b for a, b in zip(query_values,
                        key[kv_head * dimension:(kv_head + 1) * dimension])),
                    isqrt(dimension << 32)) for key in keys[layer]]
                exps = [exp_q24(score - max(scores)) for score in scores]
                attention += [sat32(rounded_div(
                    sum(exp * value[kv_head * dimension + i]
                        for exp, value in zip(exps, values[layer])), sum(exps)))
                    for i in range(dimension)]
            observe("attention", "D3", 5, 5, attention, position, layer)
            projected = projection(attention, layer, 3)
            observe("O", "D1", 6, 6, projected, position, layer)
            x = [sat32(a + b) for a, b in zip(x, projected)]
            observe("attention-residual", "D2", 0, 7, x, position, layer)
            norm = rms_norm(x, gamma)
            observe("mlp-norm", "D2", 1, 8, norm, position, layer)
            gate, up = projection(norm, layer, 4), projection(norm, layer, 5)
            observe("gate", "D1", 7, 9, gate, position, layer)
            observe("up", "D1", 8, 10, up, position, layer)
            activated = swiglu(gate, up)
            observe("SwiGLU", "D2", 9, 11, activated, position, layer)
            mlp = projection(activated, layer, 6)
            observe("down", "D1", 6, 12, mlp, position, layer)
            x = [sat32(a + b) for a, b in zip(x, mlp)]
            observe("mlp-residual", "D2", 0, 0, x, position, layer)
        x = rms_norm(x, gamma)
        observe("final-norm", "D2", 1, 14, x, position, layers - 1)
        for row in range(vocabulary):
            weights = head[row * hidden:(row + 1) * hidden]
            if weight_mode:
                chunks = []
                for start in range(0, hidden, 128):
                    count = min(128, hidden - start)
                    words = [ieee_round(Fraction(w, 1 << 16), 8, 7)
                             for w in weights[start:start + count]] + [0] * (128 - count)
                    _, total, error = array_result(
                        1, (1 << count) - 1, x[start:start + count] + [0] * (128 - count),
                        [0] * 128, [0] * 128, [0] * 128, words)
                    if error:
                        raise ArithmeticError("nonfinite synthetic head")
                    chunks.append(total)
                total = chunks[0]
                for chunk in chunks[1:]:
                    total = fp32_add(total, chunk)
                logits.append(fraction_q16(ieee_value(total, 8, 23)))
            else:
                logits.append(sat32(rhaz(sum(a * b for a, b in zip(x, weights)), 16)))
    return bytes(memory), descriptors, logits
