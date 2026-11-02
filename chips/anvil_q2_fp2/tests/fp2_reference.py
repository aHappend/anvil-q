"""Independent integer/rational IEEE and high-precision mathematical oracles."""

from decimal import Decimal, localcontext
from fractions import Fraction


QNAN = 0x7FC00000


def finite(bits, exponent_bits=8, fraction_bits=23):
    return ((bits >> fraction_bits) & ((1 << exponent_bits) - 1)) != (
        (1 << exponent_bits) - 1
    )


def exact(bits, fraction_bits=23):
    """Decode a finite binary32 or BF16 into an exact rational."""
    exponent = (bits >> fraction_bits) & 255
    fraction = bits & ((1 << fraction_bits) - 1)
    if exponent == 255:
        raise ValueError("nonfinite operand")
    significand = fraction if exponent == 0 else (1 << fraction_bits) + fraction
    shift = (1 if exponent == 0 else exponent) - 127 - fraction_bits
    value = Fraction(significand << max(shift, 0), 1 << max(-shift, 0))
    return -value if bits >> (fraction_bits + 8) else value


def nearest_even(numerator, denominator):
    quotient, remainder = divmod(numerator, denominator)
    twice = remainder * 2
    return quotient + (twice > denominator or (twice == denominator and quotient & 1))


def rounded(value, fraction_bits=23, negative_zero=False):
    """RNE a rational to a binary format with an 8-bit exponent."""
    value = Fraction(value)
    sign = int(value < 0 or (value == 0 and negative_zero))
    sign_field = sign << (fraction_bits + 8)
    value = abs(value)
    if value == 0:
        return sign_field
    numerator, denominator = value.numerator, value.denominator
    exponent = numerator.bit_length() - denominator.bit_length()
    if exponent >= 0:
        exponent -= numerator < denominator << exponent
    else:
        exponent -= numerator << -exponent < denominator
    quantum = max(exponent, -126) - fraction_bits
    significand = nearest_even(
        numerator << max(-quantum, 0), denominator << max(quantum, 0)
    )
    if significand == 0:
        return sign_field
    if significand >= 1 << (fraction_bits + 1):
        significand >>= 1
        exponent += 1
    if exponent > 127:
        return sign_field | (255 << fraction_bits)
    encoded = 0 if significand < 1 << fraction_bits else max(exponent, -126) + 127
    return sign_field | (encoded << fraction_bits) | (significand & ((1 << fraction_bits) - 1))


def add(a, b):
    if not finite(a) or not finite(b):
        if (a & 0x7FFFFFFF) > 0x7F800000 or (b & 0x7FFFFFFF) > 0x7F800000:
            return QNAN
        if (a ^ b) == 0x80000000:
            return QNAN
        return a if not finite(a) else b
    return rounded(exact(a) + exact(b), negative_zero=a == b == 0x80000000)


def multiply(a, b):
    sign = ((a ^ b) >> 31) != 0
    if not finite(a) or not finite(b):
        if (a & 0x7FFFFFFF) > 0x7F800000 or (b & 0x7FFFFFFF) > 0x7F800000:
            return QNAN
        if (a & 0x7FFFFFFF) == 0 or (b & 0x7FFFFFFF) == 0:
            return QNAN
        return (int(sign) << 31) | 0x7F800000
    return rounded(exact(a) * exact(b), negative_zero=sign)


def tensor(a, b, mask):
    values = [
        multiply(x << 16, y << 16) if mask >> i & 1 else 0
        for i, (x, y) in enumerate(zip(a, b, strict=True))
    ]
    if len(values) != 128:
        raise ValueError("the physical reduction has exactly 128 lanes")
    failed = any(
        (not finite(x << 16) or not finite(y << 16)) and mask >> i & 1
        for i, (x, y) in enumerate(zip(a, b, strict=True))
    )
    failed |= any(not finite(x) for x in values)
    while len(values) > 1:
        values = [add(values[i], values[i + 1]) for i in range(0, len(values), 2)]
        failed |= any(not finite(x) for x in values)
    return values[0], bool(failed)


def mx_decode(payload, scale):
    exponent, fraction = (payload >> 3) & 15, payload & 7
    if scale == 255 or exponent == 15 and fraction == 7:
        return 0x7FC0, True
    if exponent == 0:
        value = Fraction(fraction, 512)
    else:
        value = Fraction(8 + fraction, 8) * Fraction(2) ** (exponent - 7)
    value *= Fraction(2) ** (scale - 127)
    if payload & 128:
        value = -value
    result = rounded(value, fraction_bits=7, negative_zero=bool(payload & 128))
    return result, not finite(result, fraction_bits=7)


def decimal_value(bits):
    rational = exact(bits)
    return Decimal(rational.numerator) / Decimal(rational.denominator)


def transcendental(bits, operation):
    with localcontext() as context:
        context.prec = 100
        value = decimal_value(bits)
        if operation == "rsqrt":
            result = Decimal(1) / value.sqrt()
        elif operation == "reciprocal":
            result = Decimal(1) / value
        elif operation == "exp":
            result = value.exp()
        else:
            raise ValueError(operation)
        return rounded(Fraction(result))


def ordered_bits(bits):
    return (~bits & 0xFFFFFFFF) if bits >> 31 else (bits | 0x80000000)


def ulp_distance(a, b):
    return abs(ordered_bits(a) - ordered_bits(b))
