"""High-precision mathematical compact decoder, not a parent-RTL oracle.

The generated memory contains only external tables. Expected intermediates and
logits are a separate comparison input and are never returned on the DUT bus.
"""

from collections import defaultdict
from decimal import Decimal, localcontext
from fractions import Fraction
import random

from ieee_reference import decode, evaluate, nearest_integer, rounded


PI = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286")


def decimal_bits(bits):
    sign, kind, value = decode(bits)
    if kind != "finite":
        raise ValueError(f"nonfinite reference input {bits:08x}")
    return Decimal(value.numerator) / Decimal(value.denominator)


def bits(value):
    return rounded(Fraction(value))[0]


def sincos(angle):
    angle = (angle + PI) % (2 * PI) - PI
    sine, cosine = angle, Decimal(1)
    st, ct = angle, Decimal(1)
    for n in range(1, 100):
        st *= -angle * angle / ((2 * n) * (2 * n + 1))
        ct *= -angle * angle / ((2 * n - 1) * (2 * n))
        sine += st
        cosine += ct
        if abs(st) + abs(ct) < Decimal("1e-65"):
            break
    return sine, cosine


def make_fixture(directory, seed=17, layers=3, tokens=4, heads=3,
                 kv_heads=1, dimension=2, intermediate=5, vocabulary=17,
                 activation_format=0, bias=True, banks=16, page_tokens=1,
                 theta_value=10000, weight_format=0, activation_a8=False,
                 asymmetric=True, group_size=3, tile_k=7):
    with localcontext() as context:
        context.prec = 70
        return _make_fixture(directory, seed, layers, tokens, heads, kv_heads,
                             dimension, intermediate, vocabulary,
                             activation_format, bias, banks, page_tokens, theta_value,
                             weight_format, activation_a8, asymmetric, group_size, tile_k)


def _make_fixture(directory, seed, layers, tokens, heads, kv_heads, dimension,
                  intermediate, vocabulary, activation_format, bias,
                  banks, page_tokens, theta_value, weight_format, activation_a8,
                  asymmetric, group_size, tile_k):
    hidden = heads * dimension
    ratio = heads // kv_heads
    if heads != ratio * kv_heads or ratio not in (1, 3, 6, 7, 8):
        raise ValueError("invalid test geometry")
    rng = random.Random(seed)
    image = {}
    expected = defaultdict(list)
    stage_counts = defaultdict(int)
    logits = []

    def native(key, value):
        encoding = evaluate(8 if activation_format else 7, bits(value))[0]
        image[key] = encoding
        return decimal_bits(evaluate(6 if activation_format else 5, encoding)[0])

    def sample(denominator):
        value = rng.randrange(-7, 8)
        if value == 0:
            value = 1
        return Decimal(value) / denominator

    def record(slot, vector, stage):
        for col, value in enumerate(vector):
            expected[(8, 0, 0, slot, col)].append(value)
            stage_counts[stage] += 1

    def weight_matrix(layer, proj, inputs, outputs):
        if weight_format == 0:
            return [[native((1, layer, proj, row, col), sample(64))
                     for col in range(inputs)] for row in range(outputs)]
        width, packing = (4, 8) if weight_format == 1 else (8, 4)
        offsets = (0, 16, 4, 20, 8, 24, 12, 28)
        matrix = []
        for row in range(outputs):
            vector = []
            packed = [0]*((inputs+packing-1)//packing)
            for col in range(inputs):
                group = col//group_size
                if col % group_size == 0:
                    zero = rng.randrange(1 << width) if asymmetric else 0
                    scale = bits(Decimal(rng.randrange(1, 8))/256)
                    image[(2, layer, proj, row, group)] = zero
                    image[(3, layer, proj, row, group)] = scale
                q = rng.randrange(1 << width)
                shift = offsets[col % packing] if weight_format == 1 else 8*(col % packing)
                packed[col//packing] |= q << shift
                integer = q if asymmetric or q < (1 << (width-1)) else q-(1 << width)
                value = evaluate(9, (integer-zero) & 0xffffffff)[0]
                value = evaluate(2, value, scale)[0]
                value = evaluate(7, value)[0]
                vector.append(decimal_bits(evaluate(5, value)[0]))
            for col, value in enumerate(packed):
                image[(1, layer, proj, row, col)] = value
            matrix.append(vector)
        return matrix

    embeddings = [
        [native((0, 0, 0, row, col), sample(8)) for col in range(hidden)]
        for row in range(vocabulary)
    ]
    lmhead = [
        [native((0, 0, 1, row, col), sample(32)) for col in range(hidden)]
        for row in range(vocabulary)
    ]
    weights, biases, gammas = {}, {}, {}
    kd = kv_heads * dimension
    for layer in range(layers):
        for kind in (5, 6):
            gammas[layer, kind] = [
                native((kind, layer, 0, 0, col), Decimal(1) + sample(32))
                for col in range(hidden)
            ]
        for proj in range(7):
            inputs = intermediate if proj == 6 else hidden
            outputs = kd if proj in (1, 2) else intermediate if proj in (4, 5) else hidden
            weights[layer, proj] = weight_matrix(layer, proj, inputs, outputs)
            if proj < 3 and bias:
                biases[layer, proj] = [
                    native((4, layer, proj, 0, col), sample(128))
                    for col in range(outputs)
                ]
    final_gamma = [native((7, 0, 0, 0, col), Decimal(1) + sample(32))
                   for col in range(hidden)]
    epsilon = decimal_bits(0x358637BD)
    theta = Decimal(theta_value)

    def norm(vector, gamma):
        root = (sum(x * x for x in vector) / len(vector) + epsilon).sqrt()
        return [g * x / root for x, g in zip(vector, gamma)]

    def gemv(vector, layer, proj):
        if activation_a8:
            quantized = []
            for start in range(0, len(vector), tile_k):
                tile = [bits(value) for value in vector[start:start+tile_k]]
                maximum = max(value & 0x7fffffff for value in tile)
                scale = evaluate(3, maximum, 0x42fe0000)[0] if maximum else 0x3f800000
                for value in tile:
                    quotient = evaluate(3, value, scale)[0]
                    integer = min(127, max(-127, nearest_integer(decode(quotient)[2])))
                    value = evaluate(9, integer & 0xffffffff)[0]
                    value = evaluate(2, value, scale)[0]
                    value = evaluate(7, value)[0]
                    quantized.append(decimal_bits(evaluate(5, value)[0]))
            vector = quantized
        result = [sum(w * x for w, x in zip(row, vector))
                  for row in weights[layer, proj]]
        if proj < 3 and bias:
            result = [x + offset for x, offset in zip(result, biases[layer, proj])]
        return result

    def rotate(vector, position):
        result = vector.copy()
        half = dimension // 2
        for head in range(len(vector) // dimension):
            base = head * dimension
            for d in range(half):
                angle = Decimal(position) * (-Decimal(2 * d) / dimension * theta.ln()).exp()
                sine, cosine = sincos(angle)
                # Generation one is the first successful descriptor activation.
                image[(11, 1, 0, position, 2 * d)] = bits(cosine)
                image[(11, 1, 0, position, 2 * d + 1)] = bits(sine)
                x, y = vector[base + d], vector[base + half + d]
                result[base + d] = x * cosine - y * sine
                result[base + half + d] = x * sine + y * cosine
        return result

    history = defaultdict(list)
    token_ids = [(2 + 3 * n) % vocabulary for n in range(tokens)]
    for position, token in enumerate(token_ids):
        # Epoch zero labels a host mapping template. The bridge binds it to
        # the first public epoch observed, without assuming an RTL counter.
        page = position // page_tokens
        image[(15, 0, 0, page, 0)] = 0x80000000 | (page + 1)
        residual = embeddings[token].copy()
        record(0, residual, "embedding")
        for layer in range(layers):
            normalized = norm(residual, gammas[layer, 5])
            record(1, normalized, "attention_norm")
            q, k, v = [gemv(normalized, layer, proj) for proj in range(3)]
            record(2, q, "query")
            record(3, k, "key")
            record(4, v, "value")
            q, k = rotate(q, position), rotate(k, position)
            record(2, q, "query_rope")
            record(3, k, "key_rope")
            cache_k, cache_v = [], []
            physical_row = (page + 1) * page_tokens + position % page_tokens
            for kind, vector, target in ((9, k, cache_k), (10, v, cache_v)):
                for col, value in enumerate(vector):
                    encoding = evaluate(7, bits(value))[0]
                    widened = decimal_bits(evaluate(5, encoding)[0])
                    target.append(widened)
                    expected[(kind, layer, 0, physical_row, col)].append(widened)
                    stage_counts["cache"] += 1
            history[layer].append((cache_k, cache_v))
            attention = []
            for head in range(heads):
                kv_head = head // ratio
                scores = [
                    sum(q[head * dimension + d] * ck[kv_head * dimension + d]
                        for d in range(dimension)) / Decimal(dimension).sqrt()
                    for ck, cv in history[layer]
                ]
                maximum = max(scores)
                exponentials = [(score - maximum).exp() for score in scores]
                probabilities = [e / sum(exponentials) for e in exponentials]
                attention.extend([
                    sum(p * cv[kv_head * dimension + d]
                        for p, (ck, cv) in zip(probabilities, history[layer]))
                    for d in range(dimension)
                ])
            record(5, attention, "gqa")
            projected = gemv(attention, layer, 3)
            record(6, projected, "attention_output")
            post = [x + y for x, y in zip(residual, projected)]
            record(7, post, "attention_residual")
            normalized = norm(post, gammas[layer, 6])
            record(8, normalized, "ffn_norm")
            gate, up = gemv(normalized, layer, 4), gemv(normalized, layer, 5)
            record(9, gate, "gate")
            record(10, up, "up")
            product = [g / (1 + (-g).exp()) * u for g, u in zip(gate, up)]
            record(11, product, "swiglu")
            down = gemv(product, layer, 6)
            record(12, down, "down")
            residual = [x + y for x, y in zip(post, down)]
            record(0, residual, "ffn_residual")
        final = norm(residual, final_gamma)
        record(14, final, "final_norm")
        logits.extend(sum(w * x for w, x in zip(row, final)) for row in lmhead)

    descriptor = [
        1, 4, activation_format, weight_format, int(activation_a8), 0,
        banks, layers, hidden, intermediate, heads, kv_heads,
        dimension, vocabulary, tokens + 1, group_size, int(bias), bits(theta), 0x358637BD,
        page_tokens, tokens + 1, int(asymmetric), ratio, 1700 + seed,
    ] + [0] * 8
    (directory / "descriptor.txt").write_text("".join(f"{word:08x}\n" for word in descriptor))
    (directory / "memory.txt").write_text("".join(
        " ".join(str(x) for x in key) + f" {value:08x}\n"
        for key, value in sorted(image.items())))
    (directory / "expected-writes.txt").write_text("".join(
        " ".join(str(x) for x in key) + f" {value:.45E}\n"
        for key, values in sorted(expected.items()) for value in values))
    (directory / "expected-logits.txt").write_text("".join(f"{value:.45E}\n" for value in logits))
    (directory / "tokens.txt").write_text("".join(f"{token}\n" for token in token_ids))
    return {
        "seed": seed, "layers": layers, "tokens": tokens, "hidden": hidden,
        "intermediate": intermediate, "query_heads": heads, "kv_heads": kv_heads,
        "head_dim": dimension, "vocabulary": vocabulary,
        "activation_format": activation_format, "bias": bias, "banks": banks,
        "page_tokens": page_tokens, "theta": theta_value,
        "weight_format": weight_format, "activation_a8": activation_a8,
        "asymmetric": asymmetric, "group_size": group_size, "tile_k": tile_k,
        "stage_comparison_counts": dict(stage_counts),
        "expected_writes": sum(len(values) for values in expected.values()),
        "expected_logits": len(logits), "reference": "70-digit mathematical Decimal",
        "stage_tolerance": "2e-4+2e-4*abs(reference)",
        "logit_tolerance": "2e-3+2e-3*abs(reference)", "cosine_minimum": 0.9999,
        "scope": "compact native/W4/W8 external weights with BF16 cache",
    }
