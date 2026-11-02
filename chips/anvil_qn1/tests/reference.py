"""Independent exact-rational implementation of the admitted numerical contract."""

from fractions import Fraction
from math import isqrt
import math
import struct


class ArithmeticFault(ValueError):
    pass


def decode(bits, width=32):
    fraction_bits = 23 if width == 32 else 7
    exponent = (bits >> fraction_bits) & 255
    fraction = bits & ((1 << fraction_bits) - 1)
    if exponent == 255:
        raise ArithmeticFault("nonfinite input")
    significand = fraction + ((1 << fraction_bits) if exponent else 0)
    power = (exponent - 127 if exponent else -126) - fraction_bits
    magnitude = Fraction(significand) * pow2(power)
    return -magnitude if bits >> (width - 1) else magnitude


def pow2(power):
    return Fraction(1 << power) if power >= 0 else Fraction(1, 1 << -power)


def nearest_integer(value):
    quotient, remainder = divmod(value.numerator, value.denominator)
    twice = 2 * remainder
    return quotient + (twice > value.denominator or
                       (twice == value.denominator and quotient & 1))


def floor_log2(value):
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    return exponent - (value < pow2(exponent))


def encode(value, width=32, negative_zero=False):
    value = Fraction(value)
    fraction_bits = 23 if width == 32 else 7
    negative = value < 0 or (not value and negative_zero)
    magnitude = abs(value)
    if not magnitude:
        return int(negative) << (width - 1)
    exponent = max(-126, floor_log2(magnitude))
    significand = nearest_integer(magnitude / pow2(exponent - fraction_bits))
    if significand == 1 << (fraction_bits + 1):
        significand >>= 1
        exponent += 1
    if exponent > 127:
        raise ArithmeticFault("finite-operation overflow")
    biased = exponent + 127 if significand >= (1 << fraction_bits) else 0
    return ((int(negative) << (width - 1)) | (biased << fraction_bits) |
            (significand & ((1 << fraction_bits) - 1)))


def add(a, b):
    value = decode(a) + decode(b)
    return encode(value, negative_zero=(a == 0x80000000 and b == 0x80000000))


def subtract(a, b):
    return add(a, b ^ 0x80000000)


def multiply(a, b):
    return encode(decode(a) * decode(b), negative_zero=bool((a ^ b) >> 31))


def divide(a, b):
    denominator = decode(b)
    if not denominator:
        raise ArithmeticFault("division by zero")
    return encode(decode(a) / denominator, negative_zero=bool((a ^ b) >> 31))


def sqrt32(bits):
    value = decode(bits)
    if value < 0:
        raise ArithmeticFault("negative square root")
    if not value:
        return bits
    exponent = floor_log2(value) // 2
    unit = pow2(exponent - 23)
    scaled_square = value / (unit * unit)
    lower = isqrt(scaled_square.numerator // scaled_square.denominator)
    midpoint_square = Fraction((2 * lower + 1) ** 2, 4)
    rounded = lower + (scaled_square > midpoint_square or
                       (scaled_square == midpoint_square and lower & 1))
    return encode(rounded * unit)


def bf16(bits):
    return encode(decode(bits), 16, negative_zero=bool(bits >> 31))


def balanced_sum(values):
    values = list(values)
    if not values:
        return 0
    values += [0] * ((1 << (len(values) - 1).bit_length()) - len(values))
    while len(values) > 1:
        values = [add(values[i], values[i + 1]) for i in range(0, len(values), 2)]
    return values[0]


def tensor(q, z, scales, activations, weights, mask, w4):
    products = []
    for lane in range(256):
        if not (mask >> lane) & 1:
            products.append(0)
            continue
        activation = activations[lane] << 16
        if w4:
            scale = decode(scales[lane], 16)
            if scale < 0:
                raise ArithmeticFault("negative AWQ scale")
            weight = multiply(encode(q[lane] - z[lane]), scales[lane] << 16)
        else:
            weight = weights[lane] << 16
        products.append(multiply(weight, activation))
    return balanced_sum(products)


def coefficients(dimension, position):
    cosines, sines = [], []
    for index in range(dimension // 2):
        angle = position * math.pow(1000000, -2 * index / dimension)
        cosines.append(encode(Fraction.from_float(math.cos(angle)), 16))
        sines.append(encode(Fraction.from_float(math.sin(angle)), 16))
    return cosines, sines


def qknorm(data, gamma, cosine, sine, position):
    dimension = len(data)
    squares = [multiply(value << 16, value << 16) for value in data]
    mean = divide(balanced_sum(squares), encode(dimension))
    reciprocal = divide(0x3F800000, sqrt32(add(mean, 0x358637BD)))
    unit = [bf16(multiply(value << 16, reciprocal)) for value in data]
    normalized = [bf16(multiply(u << 16, g << 16)) for u, g in zip(unit, gamma)]
    output = [0] * dimension
    half = dimension // 2
    for index in range(half):
        c = 0x3F80 if position == 0 else cosine[index]
        s = 0 if position == 0 else sine[index]
        x, y = normalized[index] << 16, normalized[index + half] << 16
        output[index] = bf16(subtract(multiply(x, c << 16), multiply(y, s << 16)))
        output[index + half] = bf16(add(multiply(x, s << 16), multiply(y, c << 16)))
    return output


def exp32(bits):
    value = decode(bits)
    if value > 0:
        raise ArithmeticFault("E requires nonpositive input")
    if value < -16:
        return 0
    if not value:
        return 0x3F800000
    logarithm = decode(0x3F317218)
    m = int((-value) // logarithm)
    remainder = add(bits, multiply(encode(m), 0x3F317218))
    term, total = 0x3F800000, 0x3F800000
    for k in range(1, 7):
        term = divide(multiply(term, remainder), encode(k))
        total = add(total, term)
    clamped = min(Fraction(1), max(Fraction(0), decode(total)))
    return encode(clamped * pow2(-m))


def silu32(bits):
    value = decode(bits)
    exponential = exp32(bits ^ 0x80000000 if value >= 0 else bits)
    numerator = bits if value >= 0 else multiply(bits, exponential)
    return divide(numerator, add(0x3F800000, exponential))


def pack(values, width):
    return sum(value << (index * width) for index, value in enumerate(values))


def self_check():
    for value, expected in [(Fraction(1), 0x3F800000),
                            (Fraction(-2), 0xC0000000),
                            (pow2(-149), 1),
                            (pow2(-150), 0),
                            (3 * pow2(-150), 2)]:
        assert encode(value) == expected
    assert add(0x80000000, 0x80000000) == 0x80000000
    assert add(0x3F800000, 0xBF800000) == 0
    assert multiply(0, 0xBF800000) == 0x80000000
    assert sqrt32(0x40800000) == 0x40000000
    assert divide(0x3F800000, 0x40000000) == 0x3F000000
    for value in [1, 2, 3, 17, 128, 65537]:
        native = struct.unpack(">I", struct.pack(">f", math.sqrt(value)))[0]
        assert sqrt32(encode(value)) == native
