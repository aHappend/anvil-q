"""Independent integer transformer model for the documented legacy equations."""

from collections import defaultdict
from decimal import Decimal, localcontext
from fractions import Fraction
from math import isqrt
import random

from ieee_reference import decode, evaluate, nearest_integer, rounded
from transformer_reference import sincos


OFFSETS = (0, 16, 4, 20, 8, 24, 12, 28)
Q = 1 << 16


def saturate(value):
    return min((1 << 31)-1, max(-(1 << 31), value))


def round_shift(value, shift):
    magnitude = abs(value)
    if shift:
        magnitude = (magnitude+(1 << (shift-1))) >> shift
    return saturate(-magnitude if value < 0 else magnitude)


def rounded_divide(numerator, denominator):
    """Signed legacy division rounds magnitude halfway away from zero."""
    value = (abs(numerator)+(abs(denominator) >> 1))//abs(denominator)
    return -value if (numerator < 0) != (denominator < 0) else value


def f16_q16(encoding):
    sign, kind, value = decode(encoding, 5, 10)
    if kind != "finite":
        raise ValueError("nonfinite legacy table")
    magnitude = abs(value)*Q
    rounded = (2*magnitude.numerator+magnitude.denominator)//(2*magnitude.denominator)
    return saturate(-rounded if sign else rounded)


def norm(vector, gamma):
    mean = (sum(x*x for x in vector) << 32)//len(vector)
    root = isqrt(mean+18446744073710)
    reciprocal = (1 << 64)//root
    return [round_shift(x*g*reciprocal, 48) for x, g in zip(vector, gamma)]


def exponential(value):
    if value < -16*Q:
        return 0
    if value >= 0:
        return 1 << 24
    shift, residue = divmod((-value) << 8, 11629080)
    term = total = 1 << 24
    for divisor in range(1, 7):
        next_term = ((abs(term)*residue) >> 24)//divisor
        term = next_term if term < 0 else -next_term
        total += term
    return max(0, total) >> shift


def silu(value):
    exp = exponential(-abs(value))
    sigmoid = ((exp << 24) if value < 0 else (1 << 48))//((1 << 24)+exp)
    magnitude = (abs(value)*sigmoid+(1 << 23)) >> 24
    return saturate(-magnitude if value < 0 else magnitude)


def cache_block(values, cache_format):
    width = 8 if cache_format == 1 else 4
    if cache_format == 3:
        for exponent in range(33):
            rounded = [round_shift_unbounded(value, exponent) for value in values]
            lower = max(-8, -8-min(rounded))
            upper = min(7, 7-max(rounded))
            if lower <= upper:
                zero = lower if lower > 0 else upper if upper < 0 else 0
                codes = [value+zero for value in rounded]
                break
        else:
            raise AssertionError("legacy asymmetric cache range")
    else:
        limit, maximum = (127, 25) if width == 8 else (7, 29)
        magnitude = max(abs(value) for value in values)
        exponent = next(e for e in range(maximum+1) if magnitude <= limit << e)
        zero = 0
        codes = [min(limit, max(-limit, round_shift_unbounded(value, exponent)))
                 for value in values]
    decoded = [saturate((code-zero) << exponent) for code in codes]
    return exponent | ((zero & 15) << 8), codes, decoded


def round_shift_unbounded(value, shift):
    magnitude = (abs(value)+(1 << (shift-1))) >> shift if shift else abs(value)
    return -magnitude if value < 0 else magnitude


def make_fixture(directory, seed=17, mode=1, cache_format=0, banks=1, tokens=4):
    rng = random.Random(seed)
    heads, kvheads, dimension = (8, 1, 2) if mode == 3 else (1, 1, 8)
    hidden, intermediate, layers, vocabulary, group = heads*dimension, 8, 3, 17, 8
    kd = kvheads*dimension
    block = 1 if not cache_format else (
        32 if mode == 3 and cache_format == 1 else 64 if mode == 3 else dimension)
    image, expected, stage_counts = {}, defaultdict(list), defaultdict(int)

    def native(key, denominator, centered=False):
        value = Fraction(rng.randrange(-7, 8) or 1, denominator)
        if centered:
            value += 1
        encoding = evaluate(8, rounded(value)[0])[0]
        image[key] = encoding
        return f16_q16(encoding)

    embeddings = [[native((0, 0, 0, row, col), 8) for col in range(hidden)]
                  for row in range(vocabulary)]
    final_gamma = [native((7, 0, 0, 0, col), 32, True) for col in range(hidden)]
    gammas, matrices, biases = {}, {}, {}
    for layer in range(layers):
        for kind in (5, 6):
            gammas[layer, kind] = [native((kind, layer, 0, 0, col), 32, True)
                                   for col in range(hidden)]
        for proj in range(7):
            inputs = intermediate if proj == 6 else hidden
            outputs = kd if proj in (1, 2) else intermediate if proj in (4, 5) else hidden
            matrix = [[0]*inputs for _ in range(outputs)]
            packed, zeros = defaultdict(int), defaultdict(int)
            for output in range(outputs):
                for start in range(0, inputs, group):
                    z = rng.randrange(16)
                    zeros[start//group, output//8] |= z << OFFSETS[output % 8]
                    scale = native((3, layer, proj, start//group, output), 512)
                    # Legacy scales are nonnegative; independently bind their FP16 bytes.
                    scale = abs(scale)
                    key = (3, layer, proj, start//group, output)
                    image[key] &= 0x7fff
                    for col in range(start, min(inputs, start+group)):
                        q = rng.randrange(16)
                        packed[col, output//8] |= q << OFFSETS[output % 8]
                        matrix[output][col] = (q-z)*scale
            for (row, col), value in packed.items():
                image[1, layer, proj, row, col] = value
            for (row, col), value in zeros.items():
                image[2, layer, proj, row, col] = value
            matrices[layer, proj] = matrix
            if proj < 3:
                biases[layer, proj] = [native((4, layer, proj, 0, col), 128)
                                       for col in range(outputs)]

    def record(slot, vector, stage):
        for col, value in enumerate(vector):
            expected[8, 0, 0, slot, col].append(value & 0xffffffff)
            stage_counts[stage] += 1

    def gemv(vector, layer, proj):
        return [round_shift(sum(w*x for w, x in zip(row, vector)) +
                            ((biases[layer, proj][n] << 16) if proj < 3 else 0), 16)
                for n, row in enumerate(matrices[layer, proj])]

    def rotate(vector, position):
        result = vector.copy()
        with localcontext() as context:
            context.prec = 70
            for base in range(0, len(vector), dimension):
                for d in range(dimension//2):
                    angle = Decimal(position)*(
                        -Decimal(2*d)/dimension*Decimal(1000000).ln()).exp()
                    sine, cosine = sincos(angle)
                    c, s = nearest_integer(Fraction(cosine)*(1 << 30)), nearest_integer(
                        Fraction(sine)*(1 << 30))
                    image[11, 0, 0, position, 2*d] = c & 0xffffffff
                    image[11, 0, 0, position, 2*d+1] = s & 0xffffffff
                    x, y = vector[base+d], vector[base+dimension//2+d]
                    result[base+d] = round_shift(x*c-y*s, 30)
                    result[base+dimension//2+d] = round_shift(y*c+x*s, 30)
        return result

    def cache(vector, layer, position, kind):
        if not cache_format:
            for col, value in enumerate(vector):
                expected[kind, layer, 0, position, col].append(value & 0xffffffff)
                stage_counts["cache"] += 1
            return vector.copy()
        decoded = []
        width = 8 if cache_format == 1 else 4
        blocks = (dimension+block-1)//block
        words = (block*width+31)//32
        for head in range(kvheads):
            for b in range(blocks):
                values = vector[head*dimension+b*block:
                                head*dimension+min(dimension, (b+1)*block)]
                metadata, codes, reconstructed = cache_block(values, cache_format)
                decoded.extend(reconstructed)
                padded = codes + [0]*(block-len(codes))
                for word in range(words):
                    payload = sum((padded[word*(32//width)+lane] & ((1 << width)-1)) <<
                                  (lane*width) for lane in range(32//width))
                    col = (head*blocks+b)*words+word
                    expected[kind+3, layer, 0, position, col].append(payload)
                    stage_counts["cache_payload"] += 1
                expected[kind+5, layer, 0, position, head*blocks+b].append(metadata)
                stage_counts["cache_metadata"] += 1
        return decoded

    history, logits = defaultdict(list), []
    token_ids = [(2+3*n) % vocabulary for n in range(tokens)]
    for position, token in enumerate(token_ids):
        residual = embeddings[token].copy()
        record(0, residual, "embedding")
        for layer in range(layers):
            normalized = norm(residual, gammas[layer, 5])
            record(1, normalized, "attention_norm")
            q, k, v = [gemv(normalized, layer, proj) for proj in range(3)]
            for slot, vector in ((2, q), (3, k), (4, v)):
                record(slot, vector, "qkv")
            q, k = rotate(q, position), rotate(k, position)
            record(2, q, "query_rope"); record(3, k, "key_rope")
            ck, cv = cache(k, layer, position, 9), cache(v, layer, position, 10)
            history[layer].append((ck, cv))
            attention = []
            root = isqrt(dimension << 32)
            for head in range(heads):
                kv = head//(heads//kvheads)
                scores = [rounded_divide(sum(q[head*dimension+d]*old_k[kv*dimension+d]
                                       for d in range(dimension)), root)
                          for old_k, old_v in history[layer]]
                maximum = max(scores)
                probabilities = [exponential(score-maximum) for score in scores]
                denominator = sum(probabilities)
                attention.extend([
                    saturate(rounded_divide(sum(p*old_v[kv*dimension+d] for p, (_, old_v) in
                                           zip(probabilities, history[layer])), denominator))
                    for d in range(dimension)])
            record(5, attention, "gqa")
            projected = gemv(attention, layer, 3)
            record(6, projected, "attention_output")
            post = [saturate(x+y) for x, y in zip(residual, projected)]
            record(7, post, "attention_residual")
            normalized = norm(post, gammas[layer, 6])
            record(8, normalized, "ffn_norm")
            gate, up = gemv(normalized, layer, 4), gemv(normalized, layer, 5)
            record(9, gate, "gate"); record(10, up, "up")
            product = [round_shift(silu(g)*u, 16) for g, u in zip(gate, up)]
            record(11, product, "swiglu")
            down = gemv(product, layer, 6)
            record(12, down, "down")
            residual = [saturate(x+y) for x, y in zip(post, down)]
            record(0, residual, "ffn_residual")
        final = norm(residual, final_gamma)
        record(14, final, "final_norm")
        logits.extend(round_shift(sum(w*x for w, x in zip(row, final)), 16)
                      for row in embeddings)
    descriptor = [1, mode, 1, 1, 0, cache_format, banks, layers, hidden, intermediate,
                  heads, kvheads, dimension, vocabulary, tokens+1, group, 1, 0x49742400,
                  0x358637bd, 1, tokens+1, 1, heads//kvheads, seed, block]+[0]*7
    (directory/"descriptor.txt").write_text("".join(f"{word:08x}\n" for word in descriptor))
    (directory/"memory.txt").write_text("".join(
        " ".join(map(str, key))+f" {value:08x}\n" for key, value in sorted(image.items())))
    (directory/"expected-writes.txt").write_text("".join(
        " ".join(map(str, key))+f" {value}\n" for key, values in sorted(expected.items())
        for value in values))
    (directory/"expected-logits.txt").write_text("".join(f"{value}\n" for value in logits))
    (directory/"tokens.txt").write_text("".join(f"{value}\n" for value in token_ids))
    (directory/"seed.txt").write_text(f"{seed}\n")
    return {"seed": seed, "mode": mode, "cache_format": cache_format, "banks": banks,
            "tokens": tokens, "layers": layers, "hidden": hidden,
            "expected_logits": len(logits), "comparison": "exact integer bits",
            "stage_comparison_counts": dict(stage_counts)}
