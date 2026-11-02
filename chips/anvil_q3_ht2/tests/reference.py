"""Independent exact-number and compatible-image reference operations.

No DUT helper, host floating-point rounding, or RTL state is used.
"""

from fractions import Fraction


class Nonfinite(ValueError):
    pass


def binary_value(bits, exponent_bits, fraction_bits):
    sign = -1 if bits >> (exponent_bits + fraction_bits) else 1
    exponent = (bits >> fraction_bits) & ((1 << exponent_bits) - 1)
    fraction = bits & ((1 << fraction_bits) - 1)
    bias = (1 << (exponent_bits - 1)) - 1
    if exponent == (1 << exponent_bits) - 1:
        raise Nonfinite(f"nonfinite binary encoding {bits:x}")
    mantissa = fraction if exponent == 0 else (1 << fraction_bits) + fraction
    power = (1 - bias if exponent == 0 else exponent - bias) - fraction_bits
    return sign * Fraction(mantissa) * Fraction(2) ** power


def half(bits):
    return binary_value(bits, 5, 10)


def single(bits):
    return binary_value(bits, 8, 23)


def nearest_even(value):
    quotient, remainder = divmod(value.numerator, value.denominator)
    double = 2 * remainder
    return quotient + int(double > value.denominator or
                          (double == value.denominator and quotient & 1))


def binary_round(value, exponent_bits, fraction_bits):
    value = Fraction(value)
    if not value:
        return 0
    sign = int(value < 0)
    value = abs(value)
    bias = (1 << (exponent_bits - 1)) - 1
    power = value.numerator.bit_length() - value.denominator.bit_length()
    if value < Fraction(2) ** power:
        power -= 1
    power = max(power, 1 - bias)
    significand = nearest_even(value / (Fraction(2) ** (power - fraction_bits)))
    if significand >= (1 << (fraction_bits + 1)):
        significand >>= 1
        power += 1
    exponent = 0 if significand < (1 << fraction_bits) else power + bias
    if exponent >= (1 << exponent_bits) - 1:
        raise OverflowError("binary rounding overflow")
    if significand == 0:
        return 0
    return ((sign << (exponent_bits + fraction_bits)) |
            (exponent << fraction_bits) |
            (significand & ((1 << fraction_bits) - 1)))


def f32(value):
    return binary_round(value, 8, 23)


def fp_operation(a, b, multiply):
    try:
        value = single(a) * single(b) if multiply else single(a) + single(b)
        return f32(value), 0
    except (Nonfinite, OverflowError):
        return 0, 1


def q16_to_half(bits):
    signed = bits if bits < (1 << 31) else bits - (1 << 32)
    return binary_round(Fraction(signed, 65536), 5, 10)


def single_to_q16(bits):
    try:
        value = single(bits) * 65536
    except Nonfinite:
        return 0, 1
    magnitude = abs(value)
    rounded = (magnitude.numerator * 2 + magnitude.denominator) // (
        magnitude.denominator * 2)
    result = -rounded if value < 0 else rounded
    return min((1 << 31) - 1, max(-(1 << 31), result)) & 0xffffffff, 0


def weight(q, z, scale):
    try:
        value = half(scale)
        if value < 0:
            return 0, 1
        return f32((q - z) * value), 0
    except Nonfinite:
        return 0, 1


AWQ_POSITIONS = (0, 4, 1, 5, 2, 6, 3, 7)


def pack_rows(rows):
    result = 0
    for row, value in enumerate(rows):
        shift = 32 * (row // 8) + 4 * AWQ_POSITIONS[row % 8]
        result |= value << shift
    return result


def unpack_rows(bits, count):
    return [(bits >> (32 * (row // 8) + 4 * AWQ_POSITIONS[row % 8])) & 15
            for row in range(count)]


def tile_sum(beats, token_mask, row_mask):
    stripes = [[[0] * 8 for _ in range(128)] for _ in range(4)]
    for ordinal, (q, z, scales, activations, keep) in enumerate(beats):
        q = unpack_rows(q, 128)
        z = unpack_rows(z, 128)
        for token in range(4):
            if not (token_mask & keep & (1 << token)):
                continue
            a = half((activations >> (token * 16)) & 0xffff)
            for row in range(128):
                if not row_mask & (1 << row):
                    continue
                scale = (scales >> (row * 16)) & 0xffff
                w, error = weight(q[row], z[row], scale)
                if error:
                    raise ValueError("invalid active weight")
                product = f32(single(w) * a)
                stripe = ordinal & 7
                stripes[token][row][stripe] = f32(
                    single(stripes[token][row][stripe]) + single(product))
    result = 0
    for token in range(4):
        for row in range(128):
            values = stripes[token][row]
            while len(values) > 1:
                values = [f32(single(values[i]) + single(values[i + 1]))
                          for i in range(0, len(values), 2)]
            result |= values[0] << (32 * (token * 128 + row))
    return result


def packed_image(output_count, columns, seed):
    """Unique per-column/per-row AWQ bytes; padding is deliberately nonzero."""
    import random

    randomizer = random.Random(seed)
    packed = bytearray()
    logical = []
    for _ in range(columns):
        rows = [randomizer.randrange(16) for _ in range(output_count)]
        logical.append(rows)
        packed.extend(pack_rows(rows).to_bytes(output_count // 2, "little"))
    useful_bytes = len(packed)
    packed.extend(bytes([0xa7]) * ((-useful_bytes) % 64))
    return packed, logical


def sparse_expected(base, output_count, row_base, activations, mask,
                    sparse, threshold, projection, image, logical):
    threshold_value = half(threshold)
    if threshold_value < 0:
        raise ValueError("negative sparse threshold")
    rows = min(128, output_count - row_base)
    expected = []
    requests = []
    for column, act in enumerate(activations):
        keep = 0
        visible = 0
        for token in range(4):
            if mask & (1 << token):
                bits = (act >> (16 * token)) & 0xffff
                value = half(bits)
                visible |= bits << (16 * token)
                if not sparse or projection != 6 or abs(value) > threshold_value:
                    keep |= 1 << token
        if not keep:
            continue
        start = column * (output_count // 2) + (row_base // 8) * 4
        size = ((row_base + rows - 1) // 8 - row_base // 8 + 1) * 4
        aligned = start & ~63
        lines = [aligned]
        if start % 64 + size > 64:
            lines.append(aligned + 64)
        for offset in lines:
            if offset + 64 > len(image):
                raise ValueError("source span exceeds rounded matrix allocation")
            requests.append((base + offset,
                             int.from_bytes(image[offset:offset + 64], "little")))
        expected.append((column, pack_rows(logical[column][row_base:row_base + rows]),
                         visible, keep, int(column == len(activations) - 1), len(lines)))
    if expected:
        expected = [entry[:4] + (int(i == len(expected) - 1), entry[5])
                    for i, entry in enumerate(expected)]
    return requests, expected, (1 << rows) - 1
