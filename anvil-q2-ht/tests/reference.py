"""Independent exact mathematical oracles; no RTL arithmetic is imported."""

from fractions import Fraction
from math import isqrt


def rhaz(value, bits):
    if not bits:
        return value
    magnitude = (abs(value) + (1 << (bits - 1))) >> bits
    return -magnitude if value < 0 else magnitude


def sat32(value):
    return max(-(1 << 31), min((1 << 31) - 1, value))


def nearest_even(numerator, denominator):
    quotient, remainder = divmod(numerator, denominator)
    return quotient + (2 * remainder > denominator or
                       (2 * remainder == denominator and quotient & 1))


def ieee_value(word, exponent_bits, fraction_bits):
    exponent = (word >> fraction_bits) & ((1 << exponent_bits) - 1)
    fraction = word & ((1 << fraction_bits) - 1)
    if exponent == (1 << exponent_bits) - 1:
        raise ValueError("nonfinite IEEE operand")
    bias = (1 << (exponent_bits - 1)) - 1
    significand = fraction if exponent == 0 else (1 << fraction_bits) + fraction
    power = (1 - bias if exponent == 0 else exponent - bias) - fraction_bits
    magnitude = Fraction(significand) * Fraction(2) ** power
    return -magnitude if word >> (exponent_bits + fraction_bits) else magnitude


def ieee_round(value, exponent_bits, fraction_bits, negative_zero=False):
    """Round an exact rational directly to an IEEE encoding, including gradual underflow."""
    sign = value < 0 or (value == 0 and negative_zero)
    sign_word = int(sign) << (exponent_bits + fraction_bits)
    value = abs(value)
    if not value:
        return sign_word
    bias = (1 << (exponent_bits - 1)) - 1
    minimum_exponent = 1 - bias
    power = value.numerator.bit_length() - value.denominator.bit_length()
    if value < Fraction(2) ** power:
        power -= 1
    unit = Fraction(2) ** (max(power, minimum_exponent) - fraction_bits)
    scaled = value / unit
    significand = nearest_even(scaled.numerator, scaled.denominator)
    if significand >= (1 << (fraction_bits + 1)):
        significand >>= 1
        power += 1
    if power > bias:
        raise OverflowError("nonfinite IEEE result")
    if significand < (1 << fraction_bits):
        return sign_word | significand
    return (sign_word | ((max(power, minimum_exponent) + bias) << fraction_bits) |
            (significand - (1 << fraction_bits)))


def fp32_add(a, b):
    value = ieee_value(a, 8, 23) + ieee_value(b, 8, 23)
    return ieee_round(value, 8, 23, negative_zero=a == b == 0x80000000)


def fp32_product_q16_bf16(activation, weight):
    activation_word = ieee_round(Fraction(activation, 1 << 16), 8, 7)
    a = ieee_value(activation_word, 8, 7)
    b = ieee_value(weight, 8, 7)
    return ieee_round(a * b, 8, 23,
                      negative_zero=bool((activation_word ^ weight) & 0x8000))


def scale_q16(word):
    value = ieee_value(word, 5, 10)
    if value < 0:
        raise ValueError("negative scale")
    scaled = value * (1 << 16)
    return (2 * scaled.numerator + scaled.denominator) // (2 * scaled.denominator)


def array_result(mode, keep, activations, weights, zeros, scales, bf16):
    try:
        if not mode:
            total = sum(activations[j] * (weights[j] - zeros[j]) * scale_q16(scales[j])
                        for j in range(128) if keep >> j & 1)
            return total & ((1 << 128) - 1), 0, 0
        tree = [fp32_product_q16_bf16(activations[j], bf16[j])
                if keep >> j & 1 else 0 for j in range(128)]
        while len(tree) != 1:
            tree = [fp32_add(tree[j], tree[j + 1]) for j in range(0, len(tree), 2)]
        return 0, tree[0], 0
    except (ValueError, OverflowError):
        # Fault payload is unspecified, but transaction identity and timing are not.
        return 0, 0, 1


def pack_words(words, width):
    mask = (1 << width) - 1
    return sum((word & mask) << (index * width) for index, word in enumerate(words))


def rounded_div(value, denominator):
    magnitude = (abs(value) + denominator // 2) // denominator
    return -magnitude if value < 0 else magnitude


def fraction_q16(value):
    scaled = abs(value) * (1 << 16)
    magnitude = (2 * scaled.numerator + scaled.denominator) // (2 * scaled.denominator)
    return sat32(-magnitude if value < 0 else magnitude)


def rms_norm(values, gamma):
    mean = (sum(x * x for x in values) << 32) // len(values) + 18446744073710
    reciprocal = (1 << 64) // isqrt(mean)
    return [sat32(rhaz(x * g * reciprocal, 48)) for x, g in zip(values, gamma)]


def exp_q24(value):
    if value < -1048576:
        return 0
    if value >= 0:
        return 16777216
    power, remainder = divmod((-value) << 8, 11629080)
    term = total = 16777216
    for j in range(1, 7):
        magnitude = ((abs(term) * remainder) >> 24) // j
        term = -magnitude if term >= 0 else magnitude
        total += term
    return max(total, 0) >> power


def swiglu(gate, up):
    outputs = []
    for x, y in zip(gate, up):
        exp = exp_q24(-abs(x))
        sigmoid = ((exp << 24) if x < 0 else (1 << 48)) // (16777216 + exp)
        silu = rhaz(x * sigmoid, 24)
        outputs.append(sat32(rhaz(silu * y, 16)))
    return outputs


def cache_roundtrip(values, mode, block=1):
    if mode == 0:
        return list(values)
    if mode == 1:
        return [fraction_q16(ieee_value(
            ieee_round(Fraction(value, 1 << 16), 5, 10), 5, 10)) for value in values]
    outputs = []
    for start in range(0, len(values), block):
        group = values[start:start + block]
        maximum = max(abs(x) for x in group)
        exponent = next((e for e in range(26) if maximum <= 127 << e), 25)
        outputs += [sat32(max(-127, min(127, rhaz(x, exponent))) << exponent) for x in group]
    return outputs
