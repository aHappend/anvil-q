"""Exact rational IEEE RNE model, independent of the RTL arithmetic algorithm."""

from fractions import Fraction
from math import isqrt


INVALID, DIVZERO, OVERFLOW, UNDERFLOW, INEXACT = 16, 8, 4, 2, 1


def power2(exponent):
    return Fraction(1 << exponent) if exponent >= 0 else Fraction(1, 1 << -exponent)


def decode(bits, exponent_bits=8, fraction_bits=23):
    sign = bits >> (exponent_bits + fraction_bits)
    exponent = (bits >> fraction_bits) & ((1 << exponent_bits) - 1)
    fraction = bits & ((1 << fraction_bits) - 1)
    if exponent == (1 << exponent_bits) - 1:
        return sign, "nan" if fraction else "inf", fraction
    bias = (1 << (exponent_bits - 1)) - 1
    value = Fraction(fraction + ((1 << fraction_bits) if exponent else 0))
    value *= power2((exponent if exponent else 1) - bias - fraction_bits)
    return sign, "finite", -value if sign else value


def logarithm2(value):
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    return exponent - (value < power2(exponent))


def nearest_integer(value):
    integer, remainder = divmod(value.numerator, value.denominator)
    return integer + (remainder * 2 > value.denominator or
                      (remainder * 2 == value.denominator and integer & 1))


def rounded(value, exponent_bits=8, fraction_bits=23, zero_sign=0):
    sign = int(value < 0) if value else zero_sign
    value = abs(value)
    sign_bits = sign << (exponent_bits + fraction_bits)
    if not value:
        return sign_bits, 0
    bias = (1 << (exponent_bits - 1)) - 1
    minimum, maximum = 1 - bias, bias
    exponent = max(minimum, logarithm2(value))
    step = power2(exponent - fraction_bits)
    significand = nearest_integer(value / step)
    inexact = Fraction(significand) * step != value
    if significand == 1 << (fraction_bits + 1):
        significand >>= 1
        exponent += 1
    if exponent > maximum:
        return sign_bits | (((1 << exponent_bits) - 1) << fraction_bits), 5
    encoded_exponent = exponent + bias if significand >= 1 << fraction_bits else 0
    bits = sign_bits | (encoded_exponent << fraction_bits)
    bits |= significand & ((1 << fraction_bits) - 1)
    flags = int(inexact) | (UNDERFLOW if inexact and encoded_exponent == 0 else 0)
    return bits, flags


def square_root(value):
    if not value:
        return 0, 0
    exponent = max(-126, logarithm2(value) // 2)
    step = power2(exponent - 23)
    ratio = value / (step * step)
    lower = isqrt(ratio.numerator // ratio.denominator)
    midpoint_comparison = 4 * ratio.numerator - ratio.denominator * (2 * lower + 1) ** 2
    integer = lower + (midpoint_comparison > 0 or
                       (midpoint_comparison == 0 and lower & 1))
    bits, flags = rounded(Fraction(integer) * step)
    inexact = integer * integer * ratio.denominator != ratio.numerator
    return bits, flags | int(inexact) | (UNDERFLOW if inexact and bits >> 23 == 0 else 0)


def evaluate(op, a, b=0):
    """Return (result bits, IEEE flags), with tininess detected after rounding."""
    if op in (5, 6):
        exponent_bits, fraction_bits = (8, 7) if op == 5 else (5, 10)
        sign, kind, value = decode(a & 65535, exponent_bits, fraction_bits)
        if kind == "nan":
            return 0x7FC00000, INVALID if not value & (1 << (fraction_bits - 1)) else 0
        if kind == "inf":
            return (sign << 31) | 0x7F800000, 0
        return rounded(value, zero_sign=sign)
    if op == 9:
        return rounded(Fraction(a - (1 << 32) if a & 0x80000000 else a))
    if op >= 10:
        return 0x7FC00000, INVALID
    sa, ka, va = decode(a)
    sb, kb, vb = decode(b)
    if op in (7, 8):
        eb, fb = (8, 7) if op == 7 else (5, 10)
        if ka == "nan":
            return (0x7FC0 if op == 7 else 0x7E00), INVALID if not va & 0x400000 else 0
        if ka == "inf":
            return (sa << 15) | (((1 << eb) - 1) << fb), 0
        return rounded(va, eb, fb, sa)
    if ka == "nan" or (op != 4 and kb == "nan"):
        signaling = ka == "nan" and not va & 0x400000
        signaling |= op != 4 and kb == "nan" and not vb & 0x400000
        return 0x7FC00000, INVALID if signaling else 0
    if op in (0, 1):
        sb ^= op
        if ka == kb == "inf" and sa != sb:
            return 0x7FC00000, INVALID
        if ka == "inf":
            return (sa << 31) | 0x7F800000, 0
        if kb == "inf":
            return (sb << 31) | 0x7F800000, 0
        total = va + (-vb if op else vb)
        return rounded(total, zero_sign=sa & sb if not va and not vb else 0)
    sign = sa ^ sb
    if op == 2:
        if (ka == "inf" and kb == "finite" and not vb or
                kb == "inf" and ka == "finite" and not va):
            return 0x7FC00000, INVALID
        if ka == "inf" or kb == "inf":
            return (sign << 31) | 0x7F800000, 0
        return rounded(va * vb, zero_sign=sign)
    if op == 3:
        if ka == kb == "inf" or ka == kb == "finite" and not va and not vb:
            return 0x7FC00000, INVALID
        if ka == "inf":
            return (sign << 31) | 0x7F800000, 0
        if kb == "inf":
            return sign << 31, 0
        if not vb:
            return (sign << 31) | 0x7F800000, DIVZERO
        return rounded(va / vb, zero_sign=sign)
    if op == 4:
        if sa and (ka == "inf" or va):
            return 0x7FC00000, INVALID
        if ka == "inf":
            return a, 0
        if not va:
            return a, 0
        return square_root(va)
    raise ValueError(f"unimplemented opcode {op}")


def self_check():
    assert evaluate(0, 0x3F800000, 0x33800000) == (0x3F800000, INEXACT)
    assert evaluate(0, 0x3F800001, 0x33800000) == (0x3F800002, INEXACT)
    assert evaluate(2, 1, 0x3F000000) == (0, UNDERFLOW | INEXACT)
    assert evaluate(2, 3, 0x3F000000) == (2, UNDERFLOW | INEXACT)
    assert evaluate(3, 0x3F800000, 0x40400000) == (0x3EAAAAAB, INEXACT)
    assert evaluate(4, 0x40000000) == (0x3FB504F3, INEXACT)
    assert evaluate(4, 0x40800000) == (0x40000000, 0)
    assert evaluate(5, 1) == (0x00010000, 0)
    assert evaluate(6, 1) == (0x33800000, 0)
    assert evaluate(8, 0x33800000) == (1, 0)
    assert evaluate(9, 0x80000000) == (0xCF000000, 0)
