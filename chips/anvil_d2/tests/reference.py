"""Independent integer/rational models of the frozen numerical boundaries."""

from bisect import bisect_left
from fractions import Fraction


def pow2(exponent):
    return Fraction(1 << exponent) if exponent >= 0 else Fraction(1, 1 << -exponent)


def ties_even(value):
    integer, remainder = divmod(value.numerator, value.denominator)
    twice = 2 * remainder
    return integer + (twice > value.denominator or
                      (twice == value.denominator and integer % 2 == 1))


def encode_ieee(magnitude, fraction_bits, exponent_bits=8, bias=127):
    """Round a nonnegative rational to IEEE bits, including gradual underflow."""
    assert magnitude >= 0
    if not magnitude:
        return 0
    exponent = magnitude.numerator.bit_length() - magnitude.denominator.bit_length()
    if magnitude < pow2(exponent):
        exponent -= 1
    minimum = 1 - bias
    quantum = pow2(max(exponent, minimum) - fraction_bits)
    significand = ties_even(magnitude / quantum)
    if exponent < minimum:
        return significand
    if significand == 1 << (fraction_bits + 1):
        significand >>= 1
        exponent += 1
    encoded_exponent = exponent + bias
    if encoded_exponent >= (1 << exponent_bits) - 1:
        return ((1 << exponent_bits) - 1) << fraction_bits
    return (encoded_exponent << fraction_bits) | (significand - (1 << fraction_bits))


def binary_value(bits, fraction_bits):
    exponent = (bits >> fraction_bits) & 255
    significand = bits & ((1 << fraction_bits) - 1)
    if exponent == 255:
        raise ValueError("nonfinite IEEE value")
    if exponent:
        significand += 1 << fraction_bits
    value = significand * pow2((exponent - 127 if exponent else -126) - fraction_bits)
    return -value if bits >> (fraction_bits + 8) else value


def fp8_value(code):
    exponent, fraction = (code >> 3) & 15, code & 7
    if exponent == 15 and fraction == 7:
        raise ValueError("E4M3FN NaN")
    value = (fraction * pow2(-9) if exponent == 0
             else (8 + fraction) * pow2(exponent - 10))
    return -value if code & 128 else value


FP8_POSITIVES = tuple(fp8_value(code) for code in range(127))


def dequantize(code, scale):
    invalid = ((code & 127) == 127 or scale >> 31 or
               (scale >> 23) == 255 or (scale & 0x7FFFFFFF) == 0)
    if invalid:
        return 0, 0, 1
    exact = abs(fp8_value(code)) * binary_value(scale, 23)
    fp32 = encode_ieee(exact, 23)
    if (fp32 >> 23) == 255:
        return 0, 0, 1
    bf16 = encode_ieee(binary_value(fp32, 23), 7)
    if (bf16 >> 7) == 255:
        return 0, 0, 1
    sign = code >> 7
    return fp32 | (sign << 31), bf16 | (sign << 15), 0


def quantize_group(values):
    assert 1 <= len(values) <= 128
    maximum = Fraction(max(abs(value) for value in values), 65536)
    scale = Fraction(1)
    if maximum:
        while maximum > 448 * scale:
            scale *= 2
        while maximum <= 448 * scale / 2:
            scale /= 2
    encoded_scale = encode_ieee(scale, 23)
    result = []
    for value in values:
        magnitude = Fraction(abs(value), 65536) / scale
        upper = bisect_left(FP8_POSITIVES, magnitude)
        if upper == 0:
            selected = 0
        elif upper >= len(FP8_POSITIVES):
            selected = 126
        else:
            lower = upper - 1
            low_error = magnitude - FP8_POSITIVES[lower]
            high_error = FP8_POSITIVES[upper] - magnitude
            selected = (lower if low_error < high_error else upper if high_error < low_error
                        else lower if lower % 2 == 0 else upper)
        result.append(selected | (128 if value < 0 else 0))
    return encoded_scale, result


def bf16_to_q16(bits):
    if (bits >> 7) & 255 == 255:
        return 0, 1
    exact = binary_value(bits, 7) * 65536
    rounded = (abs(exact).numerator * 2 + abs(exact).denominator) // (
        2 * abs(exact).denominator)
    if exact < 0:
        rounded = -rounded
    saturated = min(0x7FFFFFFF, max(-0x80000000, rounded))
    return saturated & 0xFFFFFFFF, 0
