"""Independent exact-rational IEEE reference; no dependency on RTL arithmetic."""

from fractions import Fraction
import math
import struct


FORMATS = {"bf16": (8, 7), "fp16": (5, 10), "fp32": (8, 23)}
INVALID, DIVZERO, OVERFLOW, UNDERFLOW, INEXACT = 16, 8, 4, 2, 1


def power2(exponent):
    return Fraction(1 << exponent) if exponent >= 0 else Fraction(1, 1 << -exponent)


def classify(bits, fmt="fp32"):
    eb, fb = FORMATS[fmt]
    sign = bits >> (eb + fb)
    exponent = (bits >> fb) & ((1 << eb) - 1)
    fraction = bits & ((1 << fb) - 1)
    if exponent == (1 << eb) - 1:
        return ("nan" if fraction else "inf", sign, bool(fraction and not fraction >> (fb - 1)))
    if exponent == 0 and fraction == 0:
        return "zero", sign, False
    return "finite", sign, False


def exact(bits, fmt="fp32"):
    eb, fb = FORMATS[fmt]
    kind, sign, _ = classify(bits, fmt)
    if kind not in ("finite", "zero"):
        raise ValueError(f"{kind} has no rational value")
    exponent = (bits >> fb) & ((1 << eb) - 1)
    fraction = bits & ((1 << fb) - 1)
    significand = fraction + ((1 << fb) if exponent else 0)
    value = significand * power2((exponent or 1) - ((1 << (eb - 1)) - 1) - fb)
    return -value if sign else value


def round_integer(value):
    lower, remainder = divmod(value.numerator, value.denominator)
    twice = remainder * 2
    return lower + (twice > value.denominator or
                    (twice == value.denominator and lower % 2 != 0))


def log2_floor(value):
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    return exponent - (value < power2(exponent))


def pack(value, fmt="fp32", zero_sign=0):
    """RNE with after-rounding tininess; returns bits and IEEE exception flags."""
    eb, fb = FORMATS[fmt]
    sign = int(value < 0) if value else zero_sign
    sign_bit = sign << (eb + fb)
    if not value:
        return sign_bit, 0
    value = abs(value)
    bias = (1 << (eb - 1)) - 1
    exponent = max(1 - bias, log2_floor(value))
    quantum = power2(exponent - fb)
    significand = round_integer(value / quantum)
    if significand == 1 << (fb + 1):
        significand >>= 1
        exponent += 1
        quantum *= 2
    if exponent > bias:
        return sign_bit | (((1 << eb) - 1) << fb), OVERFLOW | INEXACT
    inexact = value != significand * quantum
    subnormal = significand < 1 << fb
    bits = sign_bit | (significand if subnormal else
                       ((exponent + bias) << fb) | (significand - (1 << fb)))
    return bits, int(inexact) | (UNDERFLOW if subnormal and inexact else 0)


def canonical(fmt="fp32"):
    eb, fb = FORMATS[fmt]
    return (((1 << eb) - 1) << fb) | (1 << (fb - 1))


def convert(bits, source, target, preserve_nan=False):
    kind, sign, snan = classify(bits, source)
    eb, fb = FORMATS[target]
    if kind == "nan":
        if preserve_nan:
            seb, sfb = FORMATS[source]
            fraction = bits & ((1 << sfb) - 1)
            return (sign << (eb + fb)) | (((1 << eb) - 1) << fb) | (fraction << (fb - sfb)), 0
        return canonical(target), INVALID if snan else 0
    if kind == "inf":
        return (sign << (eb + fb)) | (((1 << eb) - 1) << fb), 0
    return pack(exact(bits, source), target, sign)


def binary(operation, a, b):
    ka, sa, na = classify(a)
    kb, sb, nb = classify(b)
    invalid = ((operation == "add" and ka == kb == "inf" and sa != sb) or
               (operation == "mul" and {ka, kb} == {"inf", "zero"}) or
               (operation == "div" and ka == kb and ka in ("inf", "zero")))
    if ka == "nan" or kb == "nan" or invalid:
        return canonical(), INVALID if na or nb or invalid else 0
    if operation == "add":
        if ka == "inf" or kb == "inf":
            return (a if ka == "inf" else b), 0
        return pack(exact(a) + exact(b), zero_sign=int(sa == sb == 1))
    sign = sa ^ sb
    if operation == "mul":
        if ka == "inf" or kb == "inf":
            return (sign << 31) | 0x7f800000, 0
        return pack(exact(a) * exact(b), zero_sign=sign)
    if operation != "div":
        raise ValueError(operation)
    if ka == "inf" or kb == "zero":
        return (sign << 31) | 0x7f800000, DIVZERO if kb == "zero" and ka != "inf" else 0
    if kb == "inf":
        return sign << 31, 0
    return pack(exact(a) / exact(b), zero_sign=sign)


def sqrt(bits):
    kind, sign, snan = classify(bits)
    if kind == "nan" or (sign and kind != "zero"):
        return canonical(), INVALID if snan or kind != "nan" else 0
    if kind in ("inf", "zero"):
        return bits, 0
    value = exact(bits)
    exponent = log2_floor(value) // 2
    quantum = power2(max(-126, exponent) - 23)
    scaled_square = value / (quantum * quantum)
    lower = math.isqrt(scaled_square.numerator // scaled_square.denominator)
    midpoint_square = Fraction((2 * lower + 1) ** 2, 4)
    rounded = lower + (scaled_square > midpoint_square or
                       (scaled_square == midpoint_square and lower % 2 != 0))
    result, _ = pack(rounded * quantum)
    return result, INEXACT if exact(result) ** 2 != value else 0


def float_bits(value):
    return struct.unpack(">I", struct.pack(">f", value))[0]


def bits_float(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def dot(activations, weights, mask, fmt, q=None, z=None, scales=None):
    flags = 0
    products = []
    for lane, (activation, weight) in enumerate(zip(activations, weights)):
        if not (mask >> lane) & 1:
            products.append(0)
            continue
        a = convert(activation, fmt, "fp32", preserve_nan=True)[0]
        if q is None:
            w = convert(weight, fmt, "fp32", preserve_nan=True)[0]
        else:
            delta = pack(Fraction(q[lane] - z[lane]))[0]
            scale = convert(scales[lane], "fp16", "fp32", preserve_nan=True)[0]
            w, exception = binary("mul", delta, scale)
            flags |= exception
        product, exception = binary("mul", a, w)
        flags |= exception
        products.append(product)
    while len(products) > 1:
        reduced = []
        for lane in range(0, len(products), 2):
            value, exception = binary("add", products[lane], products[lane + 1])
            flags |= exception
            reduced.append(value)
        products = reduced
    return products[0], flags
