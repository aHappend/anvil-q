"""Independent integer/rational IEEE and high-precision mathematical oracles."""

from decimal import Decimal, localcontext
from fractions import Fraction


QNAN = 0x7FC00000


def finite(bits, exponent_bits=8, fraction_bits=23):
    return ((bits >> fraction_bits) & ((1 << exponent_bits) - 1)) != (
        (1 << exponent_bits) - 1
    )


def exact(bits, fraction_bits=23, exponent_bits=8):
    """Decode a finite binary32 or BF16 into an exact rational."""
    exponent_max = (1 << exponent_bits) - 1
    bias = (1 << (exponent_bits - 1)) - 1
    exponent = (bits >> fraction_bits) & exponent_max
    fraction = bits & ((1 << fraction_bits) - 1)
    if exponent == exponent_max:
        raise ValueError("nonfinite operand")
    significand = fraction if exponent == 0 else (1 << fraction_bits) + fraction
    shift = (1 if exponent == 0 else exponent) - bias - fraction_bits
    value = Fraction(significand << max(shift, 0), 1 << max(-shift, 0))
    return -value if bits >> (fraction_bits + exponent_bits) else value


def nearest_even(numerator, denominator):
    quotient, remainder = divmod(numerator, denominator)
    twice = remainder * 2
    return quotient + (twice > denominator or (twice == denominator and quotient & 1))


def rounded(value, fraction_bits=23, negative_zero=False, exponent_bits=8):
    """RNE a rational to a binary format with an 8-bit exponent."""
    value = Fraction(value)
    sign = int(value < 0 or (value == 0 and negative_zero))
    bias = (1 << (exponent_bits - 1)) - 1
    minimum_exponent = 1 - bias
    sign_field = sign << (fraction_bits + exponent_bits)
    value = abs(value)
    if value == 0:
        return sign_field
    numerator, denominator = value.numerator, value.denominator
    exponent = numerator.bit_length() - denominator.bit_length()
    if exponent >= 0:
        exponent -= numerator < denominator << exponent
    else:
        exponent -= numerator << -exponent < denominator
    quantum = max(exponent, minimum_exponent) - fraction_bits
    significand = nearest_even(
        numerator << max(-quantum, 0), denominator << max(quantum, 0)
    )
    if significand == 0:
        return sign_field
    if significand >= 1 << (fraction_bits + 1):
        significand >>= 1
        exponent += 1
    if exponent > bias:
        return sign_field | (((1 << exponent_bits) - 1) << fraction_bits)
    encoded = (0 if significand < 1 << fraction_bits
               else max(exponent, minimum_exponent) + bias)
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


def mx_magnitude(payload):
    exponent, fraction = (payload >> 3) & 15, payload & 7
    if exponent == 15 and fraction == 7:
        raise ValueError("E4M3FN NaN has no finite magnitude")
    if exponent == 0:
        return Fraction(fraction, 512)
    return Fraction(8 + fraction, 8) * Fraction(2) ** (exponent - 7)


MX_MAGNITUDES = tuple(mx_magnitude(code) for code in range(127))


def mx_encode_lane(value, scale):
    if not finite(value, fraction_bits=7) or scale == 255:
        return 127, True
    magnitude = abs(exact(value, fraction_bits=7)) / Fraction(2) ** (scale - 127)
    if magnitude > 448:
        raise ValueError("encoding reference requires an accommodating group scale")
    # Exhaust the mathematical finite code space. Even payload LSB resolves ties.
    code = min(range(127), key=lambda p: (abs(MX_MAGNITUDES[p] - magnitude), p & 1))
    return code | ((value >> 15) << 7), False


def mx_encode_group(values, mask):
    active = [value if mask >> lane & 1 else 0 for lane, value in enumerate(values)]
    if any(not finite(value, fraction_bits=7) for value in active):
        raise ValueError("nonfinite group has no valid encoding")
    maximum = max(abs(exact(value, fraction_bits=7)) for value in active)
    if maximum == 0:
        scale = 127
    else:
        scale = next(s for s in range(255) if maximum <= 448 * Fraction(2) ** (s - 127))
    return [mx_encode_lane(value, scale)[0] for value in active], scale


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


def rms(values, gamma):
    total = 0
    for value in values:
        total = add(total, multiply(value, value))
    mean = multiply(total, rounded(Fraction(1, len(values))))
    inverse = transcendental(add(mean, 0x358637BD), "rsqrt")
    return [multiply(multiply(value, inverse), weight)
            for value, weight in zip(values, gamma, strict=True)]


def swiglu(gate, up):
    magnitude = gate & 0x7FFFFFFF
    exponential = 0 if magnitude > 0x42A00000 else transcendental(magnitude | 0x80000000, "exp")
    denominator = add(0x3F800000, exponential)
    inverse = rounded(1 / exact(denominator))
    sigmoid = multiply(exponential, inverse) if gate >> 31 else inverse
    return multiply(multiply(gate, sigmoid), up)


def rope(x, y, cosine, sine):
    first = add(multiply(x, cosine), multiply(y, sine) ^ 0x80000000)
    second = add(multiply(y, cosine), multiply(x, sine))
    return first, second


def rope_coefficients(position, pair_index, head_dim, mathematical=False):
    """Derive trigonometric coefficients without using the shipped generator."""
    with localcontext() as context:
        context.prec = 100
        pi = Decimal(
            "3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679"
        )
        angle = Decimal(position) * (
            -Decimal(2 * pair_index) * Decimal(1000000).ln() / Decimal(head_dim)
        ).exp()
        reduced = angle % (2 * pi)
        if reduced > pi:
            reduced -= 2 * pi
        square = reduced * reduced
        sine_term, cosine_term = reduced, Decimal(1)
        sine, cosine = sine_term, cosine_term
        for n in range(1, 200):
            sine_term *= -square / Decimal((2 * n) * (2 * n + 1))
            cosine_term *= -square / Decimal((2 * n - 1) * (2 * n))
            sine += sine_term
            cosine += cosine_term
            if abs(sine_term) < Decimal("1e-95") and abs(cosine_term) < Decimal("1e-95"):
                if mathematical:
                    return Fraction(cosine), Fraction(sine)
                return rounded(Fraction(cosine)), rounded(Fraction(sine))
        raise ArithmeticError("trigonometric reference did not converge")
