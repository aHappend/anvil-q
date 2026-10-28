"""Independent exact-rational IEEE rounding, with no DUT arithmetic imports."""

from fractions import Fraction
from decimal import Decimal, localcontext
from functools import lru_cache
from math import factorial


FORMATS = {"bf16": (8, 7), "fp16": (5, 10), "fp32": (8, 23)}


@lru_cache(maxsize=65536)
def classify(bits, fmt="fp32"):
    eb, fb = FORMATS[fmt]
    exp = (bits >> fb) & ((1 << eb) - 1)
    frac = bits & ((1 << fb) - 1)
    if exp == (1 << eb) - 1:
        return "nan" if frac else "inf"
    return "finite"


def infinity(sign=0):
    return (sign << 31) | 0x7F800000


@lru_cache(maxsize=65536)
def convert(bits, source="fp32", target="fp32"):
    eb, fb = FORMATS[target]
    sign = bits >> sum(FORMATS[source])
    kind = classify(bits, source)
    if kind == "nan":
        return (((1 << eb) - 1) << fb) | (1 << (fb - 1))
    if kind == "inf":
        return (sign << (eb + fb)) | (((1 << eb) - 1) << fb)
    return rounded(value(bits, source), target, negative_zero=bool(sign))


@lru_cache(maxsize=65536)
def value(bits, fmt="fp32"):
    eb, fb = FORMATS[fmt]
    sign = -1 if bits >> (eb + fb) else 1
    exp = (bits >> fb) & ((1 << eb) - 1)
    frac = bits & ((1 << fb) - 1)
    if exp == (1 << eb) - 1:
        raise ValueError("nonfinite encoding has no rational value")
    bias = (1 << (eb - 1)) - 1
    if exp:
        frac += 1 << fb
    power = (exp - bias if exp else 1 - bias) - fb
    return sign * Fraction(frac) * Fraction(2) ** power


def rounded_integer(x):
    q, r = divmod(x.numerator, x.denominator)
    return q + (2 * r > x.denominator or (2 * r == x.denominator and q & 1))


def rounded(x, fmt="fp32", negative_zero=False):
    x = Fraction(x)
    eb, fb = FORMATS[fmt]
    bias = (1 << (eb - 1)) - 1
    sign = int(x < 0 or (not x and negative_zero)) << (eb + fb)
    x = abs(x)
    if not x:
        return sign
    exponent = x.numerator.bit_length() - x.denominator.bit_length()
    if x < Fraction(2) ** exponent:
        exponent -= 1
    quantum = max(exponent, 1 - bias) - fb
    mantissa = rounded_integer(x / Fraction(2) ** quantum)
    if mantissa == 1 << (fb + 1):
        mantissa >>= 1
        exponent += 1
    if exponent > bias:
        return sign | (((1 << eb) - 1) << fb)
    if mantissa < (1 << fb):
        return sign | mantissa
    return sign | ((max(exponent, 1 - bias) + bias) << fb) | (mantissa - (1 << fb))


@lru_cache(maxsize=65536)
def add(a, b):
    ca, cb = classify(a), classify(b)
    if ca == "nan" or cb == "nan":
        return 0x7FC00000
    if ca == cb == "inf" and (a ^ b) >> 31:
        return 0x7FC00000
    if ca == "inf":
        return a
    if cb == "inf":
        return b
    return rounded(value(a) + value(b),
                   negative_zero=(a == 0x80000000 and b == 0x80000000))


@lru_cache(maxsize=65536)
def multiply(a, b):
    ca, cb = classify(a), classify(b)
    if ca == "nan" or cb == "nan":
        return 0x7FC00000
    if ca == "inf" or cb == "inf":
        finite = b if ca == "inf" else a
        if classify(finite) == "finite" and value(finite) == 0:
            return 0x7FC00000
        return infinity((a ^ b) >> 31)
    return rounded(value(a) * value(b), negative_zero=bool((a ^ b) >> 31))


@lru_cache(maxsize=65536)
def divide(a, b):
    ca, cb = classify(a), classify(b)
    sign = (a ^ b) >> 31
    if ca == "nan" or cb == "nan" or ca == cb == "inf":
        return 0x7FC00000
    if ca == "inf":
        return infinity(sign)
    if cb == "inf":
        return sign << 31
    if not value(b):
        return infinity(sign) if value(a) else 0x7FC00000
    return rounded(value(a) / value(b), negative_zero=bool((a ^ b) >> 31))


@lru_cache(maxsize=65536)
def square_root(a):
    """Locate adjacent binary32 values and compare the exact squared midpoint."""
    if classify(a) == "nan":
        return 0x7FC00000
    if classify(a) == "inf":
        return 0x7FC00000 if a >> 31 else a
    x = value(a)
    if x < 0:
        return 0x7FC00000
    if not x:
        return a
    low, high = 0, 0x7F7FFFFF
    while low < high:
        mid = (low + high + 1) // 2
        if value(mid) ** 2 <= x:
            low = mid
        else:
            high = mid - 1
    midpoint = (value(low) + value(low + 1)) / 2
    return low + int(x > midpoint ** 2 or (x == midpoint ** 2 and low & 1))


def unit_impulse_norm(size):
    mean = divide(0x3F800000, rounded(size))
    root = square_root(add(mean, rounded(Fraction(1, 1000000))))
    return divide(0x3F800000, root)


def negate(bits):
    return bits ^ 0x80000000


@lru_cache(maxsize=65536)
def exp_nonpositive(bits):
    """The specified non-fused polynomial, evaluated using rational rounding."""
    if classify(bits) != "finite" or value(bits) > 0:
        return 0x7FC00000
    x = value(bits)
    if not x:
        return 0x3F800000
    if x < -80:
        return 0
    with localcontext() as ctx:
        ctx.prec = 100
        ln2 = rounded(Fraction(Decimal(2).ln()))
        log2e = rounded(Fraction(1 / Decimal(2).ln()))
    n = rounded_integer(value(multiply(bits, log2e)))
    residual = add(bits, negate(multiply(rounded(n), ln2)))
    result = rounded(Fraction(1, factorial(7)))
    for k in reversed(range(7)):
        result = add(multiply(result, residual), rounded(Fraction(1, factorial(k))))
    return rounded(value(result) * Fraction(2) ** n)


def rmsnorm(components, gamma):
    total = 0
    for x in components:
        total = add(total, multiply(x, x))
    mean = divide(total, rounded(len(components)))
    root = square_root(add(mean, rounded(Fraction(1, 1000000))))
    inverse = divide(0x3F800000, root)
    return [multiply(multiply(x, inverse), w) for x, w in zip(components, gamma)]


def silu(bits):
    exponential = exp_nonpositive(bits | 0x80000000)
    denominator = add(0x3F800000, exponential)
    numerator = exponential if bits >> 31 else 0x3F800000
    return multiply(bits, divide(numerator, denominator))


@lru_cache(maxsize=None)
def rope_real(position, component, head_dim):
    """100-digit angle and Taylor sin/cos; no DUT table or host libm oracle."""
    with localcontext() as ctx:
        ctx.prec = 100
        angle = Decimal(position) * (
            -Decimal(2 * component) / Decimal(head_dim) * Decimal(1000000).ln()).exp()
        square = angle * angle
        cosine, sine = Decimal(1), angle
        ct, st = cosine, sine
        for k in range(1, 256):
            ct *= -square / Decimal((2 * k - 1) * (2 * k))
            st *= -square / Decimal((2 * k) * (2 * k + 1))
            cosine += ct
            sine += st
            if abs(ct) < Decimal("1e-95") and abs(st) < Decimal("1e-95"):
                return cosine, sine
        raise ArithmeticError("independent RoPE series did not converge")


@lru_cache(maxsize=None)
def rope_coefficients(position, component, head_dim):
    cosine, sine = rope_real(position, component, head_dim)
    return rounded(Fraction(cosine)), rounded(Fraction(sine))
