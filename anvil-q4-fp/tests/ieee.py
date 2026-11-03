"""Independent integer/rational IEEE oracle; no RTL imports or host float ALU."""

from fractions import Fraction
from math import isqrt


FORMATS = {"fp32": (8, 23), "bf16": (8, 7), "fp16": (5, 10),
           "fp8": (5, 2)}
INVALID, DIVZERO, OVERFLOW, UNDERFLOW, INEXACT = 16, 8, 4, 2, 1


def power2(exponent):
    return Fraction(1 << exponent) if exponent >= 0 else Fraction(1, 1 << -exponent)


def decode(bits, fmt="fp32"):
    eb, fb = FORMATS[fmt]
    sign = bits >> (eb + fb)
    exponent = (bits >> fb) & ((1 << eb) - 1)
    fraction = bits & ((1 << fb) - 1)
    if exponent == (1 << eb) - 1:
        return sign, "nan" if fraction else "inf", (
            bool(fraction and not fraction & (1 << (fb - 1))))
    bias = (1 << (eb - 1)) - 1
    value = Fraction(fraction if exponent == 0 else (1 << fb) + fraction)
    value *= power2((exponent or 1) - bias - fb)
    return sign, "finite", -value if sign else value


def nan(fmt="fp32"):
    eb, fb = FORMATS[fmt]
    return (((1 << eb) - 1) << fb) | (1 << (fb - 1))


def infinity(sign, fmt="fp32"):
    eb, fb = FORMATS[fmt]
    return (sign << (eb + fb)) | (((1 << eb) - 1) << fb)


def round_integer(value):
    q, remainder = divmod(value.numerator, value.denominator)
    twice = remainder * 2
    return q + int(twice > value.denominator or
                   (twice == value.denominator and q & 1))


def floor_log2(value):
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    return exponent - int(value < power2(exponent))


def pack(value, fmt="fp32", zero_sign=0):
    """Round an exact rational, testing tininess after rounding."""
    eb, fb = FORMATS[fmt]
    bias = (1 << (eb - 1)) - 1
    sign = int(value < 0) if value else zero_sign
    value = abs(value)
    if not value:
        return sign << (eb + fb), 0
    exponent = max(floor_log2(value), 1 - bias)
    unit = power2(exponent - fb)
    rounded = round_integer(value / unit)
    if rounded >= 1 << (fb + 1):
        rounded >>= 1
        exponent += 1
        unit *= 2
    if exponent > bias:
        return infinity(sign, fmt), OVERFLOW | INEXACT
    encoded = 0 if rounded < 1 << fb else exponent + bias
    bits = (sign << (eb + fb)) | (encoded << fb) | (rounded & ((1 << fb) - 1))
    flags = INEXACT if rounded * unit != value else 0
    if flags and encoded == 0:
        flags |= UNDERFLOW
    return bits, flags


def convert(bits, source, target):
    sign, kind, value = decode(bits, source)
    if kind == "nan":
        return nan(target), INVALID if value else 0
    if kind == "inf":
        return infinity(sign, target), 0
    return pack(value, target, sign)


def sqrt_round(value):
    """Integer square-root plus exact midpoint comparison, not math.sqrt."""
    exponent = floor_log2(value) // 2
    unit = power2(max(exponent, -126) - 23)
    scaled_square = value / (unit * unit)
    lower = isqrt(scaled_square.numerator // scaled_square.denominator)
    midpoint_square = Fraction((2 * lower + 1) ** 2, 4)
    upper = scaled_square > midpoint_square or (
        scaled_square == midpoint_square and lower & 1)
    rounded = lower + int(upper)
    bits, flags = pack(rounded * unit)
    if rounded * rounded != scaled_square:
        flags |= INEXACT
        if bits < 0x00800000:
            flags |= UNDERFLOW
    return bits, flags


def operation(op, a, b=0):
    if op in (5, 6):
        return convert(a & 65535, "bf16" if op == 5 else "fp16", "fp32")
    if op in (7, 8):
        return convert(a, "fp32", "bf16" if op == 7 else "fp16")
    if op == 9:
        return pack(Fraction(a - (1 << 32) if a & (1 << 31) else a))
    if op >= 10:
        return nan(), INVALID
    sa, ka, va = decode(a)
    sb, kb, vb = decode(b)
    if ka == "nan" or (op != 4 and kb == "nan"):
        signaling = (ka == "nan" and va) or (op != 4 and kb == "nan" and vb)
        return nan(), INVALID if signaling else 0
    if op in (0, 1):
        sb ^= op
        if op:
            vb = -vb
        if ka == "inf" and kb == "inf" and sa != sb:
            return nan(), INVALID
        if ka == "inf":
            return infinity(sa), 0
        if kb == "inf":
            return infinity(sb), 0
        return pack(va + vb, zero_sign=sa & sb if not va and not vb else 0)
    if op == 2:
        if (ka == "inf" and kb == "finite" and not vb or
                kb == "inf" and ka == "finite" and not va):
            return nan(), INVALID
        if ka == "inf" or kb == "inf":
            return infinity(sa ^ sb), 0
        return pack(va * vb, zero_sign=sa ^ sb)
    if op == 3:
        if ka == kb == "inf" or (ka == kb == "finite" and not va and not vb):
            return nan(), INVALID
        if ka == "inf":
            return infinity(sa ^ sb), 0
        if kb == "inf":
            return (sa ^ sb) << 31, 0
        if not vb:
            return infinity(sa ^ sb), DIVZERO
        return pack(va / vb, zero_sign=sa ^ sb)
    if sa and (ka == "inf" or va):
        return nan(), INVALID
    if ka == "inf":
        return infinity(0), 0
    if not va:
        return sa << 31, 0
    return sqrt_round(va)


def exp_frozen(bits):
    """Derive frozen Q56/Q62 algorithm from mathematical constants."""
    from decimal import Decimal, localcontext
    from math import factorial

    sign, kind, value = decode(bits)
    if kind == "nan":
        return nan(), INVALID if value else 0
    if kind == "inf":
        return (0 if sign else infinity(0)), 0
    if value > 89:
        return infinity(0), OVERFLOW | INEXACT
    if value < -104:
        return 0, UNDERFLOW | INEXACT
    with localcontext() as ctx:
        ctx.prec = 100
        ln2 = round_integer(Fraction(Decimal(2).ln()) * (1 << 56))
    magnitude = abs(value) * (1 << 56)
    fixed = magnitude.numerator // magnitude.denominator
    if sign:
        fixed = -fixed
    power, remainder = divmod(fixed, ln2)
    reduced = remainder << 6
    polynomial = round_integer(Fraction(1 << 62, factorial(16)))
    for degree in range(15, -1, -1):
        polynomial = round_integer(Fraction(polynomial * reduced, 1 << 62))
        polynomial += round_integer(Fraction(1 << 62, factorial(degree)))
    result, flags = pack(Fraction(polynomial, 1 << 62) * power2(power))
    return result, flags | (INEXACT if value else 0)


def exp_high_precision(bits):
    from decimal import Decimal, localcontext

    _, kind, value = decode(bits)
    if kind != "finite":
        return exp_frozen(bits)[0]
    with localcontext() as ctx:
        ctx.prec = 110
        x = Decimal(value.numerator) / Decimal(value.denominator)
        return pack(Fraction(x.exp()))[0]
