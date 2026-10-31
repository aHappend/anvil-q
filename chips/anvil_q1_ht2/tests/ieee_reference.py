"""Independent exact-value IEEE reference; no RTL arithmetic is imported.

Finite values are Fractions. Rounding chooses the nearest representable value
by exact integer comparisons, including a squared-midpoint test for sqrt.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
import math
import struct


@dataclass(frozen=True)
class Format:
    exponent: int
    fraction: int

    @property
    def sign(self):
        return 1 << (self.exponent + self.fraction)

    @property
    def infinity(self):
        return ((1 << self.exponent) - 1) << self.fraction

    @property
    def nan(self):
        return self.infinity | (1 << (self.fraction - 1))

    @property
    def bias(self):
        return (1 << (self.exponent - 1)) - 1


BF16 = Format(8, 7)
FP16 = Format(5, 10)
FP32 = Format(8, 23)


def pow2(exponent):
    return Fraction(1 << exponent) if exponent >= 0 else Fraction(1, 1 << -exponent)


def kind(bits, fmt=FP32):
    magnitude = bits & (fmt.sign - 1)
    if magnitude > fmt.infinity:
        return "nan"
    if magnitude == fmt.infinity:
        return "inf"
    return "zero" if magnitude == 0 else "finite"


def value(bits, fmt=FP32):
    if kind(bits, fmt) in ("nan", "inf"):
        raise ValueError("nonfinite value has no rational representation")
    e = (bits >> fmt.fraction) & ((1 << fmt.exponent) - 1)
    f = bits & ((1 << fmt.fraction) - 1)
    if e:
        f += 1 << fmt.fraction
    result = f * pow2(max(e, 1) - fmt.bias - fmt.fraction)
    return -result if bits & fmt.sign else result


def nearest_integer(x):
    q, remainder = divmod(x.numerator, x.denominator)
    twice = 2 * remainder
    return q + (twice > x.denominator or (twice == x.denominator and q & 1))


def rounded(x, fmt=FP32, negative_zero=False):
    x = Fraction(x)
    sign = fmt.sign if x < 0 or (not x and negative_zero) else 0
    x = abs(x)
    if not x:
        return sign
    exponent = x.numerator.bit_length() - x.denominator.bit_length()
    if x < pow2(exponent):
        exponent -= 1
    exponent = max(exponent, 1 - fmt.bias)
    mantissa = nearest_integer(x / pow2(exponent - fmt.fraction))
    if mantissa == 1 << (fmt.fraction + 1):
        exponent += 1
        mantissa >>= 1
    if exponent > fmt.bias:
        return sign | fmt.infinity
    encoded = 0 if mantissa < 1 << fmt.fraction else exponent + fmt.bias
    return sign | (encoded << fmt.fraction) | (mantissa & ((1 << fmt.fraction) - 1))


def convert(bits, source, destination):
    classification = kind(bits, source)
    sign = destination.sign if bits & source.sign else 0
    if classification == "nan":
        return destination.nan
    if classification == "inf":
        return sign | destination.infinity
    return rounded(value(bits, source), destination, bool(sign))


def add(a, b):
    ka, kb = kind(a), kind(b)
    if "nan" in (ka, kb):
        return FP32.nan
    if ka == kb == "inf" and (a ^ b) & FP32.sign:
        return FP32.nan
    if ka == "inf":
        return a
    if kb == "inf":
        return b
    return rounded(value(a) + value(b), negative_zero=bool(a & b & FP32.sign))


def multiply(a, b, fmt=FP32):
    ka, kb = kind(a, fmt), kind(b, fmt)
    sign = bool((a ^ b) & fmt.sign)
    if "nan" in (ka, kb) or {ka, kb} == {"zero", "inf"}:
        return FP32.nan
    if "inf" in (ka, kb):
        return (FP32.sign if sign else 0) | FP32.infinity
    return rounded(value(a, fmt) * value(b, fmt), negative_zero=sign)


def divide(a, b):
    ka, kb = kind(a), kind(b)
    sign = FP32.sign if (a ^ b) & FP32.sign else 0
    if "nan" in (ka, kb) or ka == kb and ka in ("zero", "inf"):
        return FP32.nan
    if ka == "inf" or kb == "zero":
        return sign | FP32.infinity
    if kb == "inf":
        return sign
    return rounded(value(a) / value(b), negative_zero=bool(sign))


def sqrt(a):
    classification = kind(a)
    if classification == "nan" or a & FP32.sign and classification != "zero":
        return FP32.nan
    if classification in ("zero", "inf"):
        return a
    x = value(a)
    lo, hi = 0, FP32.infinity
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if value(mid) ** 2 <= x:
            lo = mid
        else:
            hi = mid
    midpoint = (value(lo) + value(hi)) / 2
    if x > midpoint ** 2 or x == midpoint ** 2 and lo & 1:
        return hi
    return lo


def awq(qword, zword, lane, scale):
    if kind(scale, FP16) in ("nan", "inf") or (
        scale & FP16.sign and scale & (FP16.sign - 1)
    ):
        return 0, True
    # AWQ's documented interleave is a layout permutation, not arithmetic.
    nibble = (0, 4, 1, 5, 2, 6, 3, 7)[lane]
    difference = ((qword >> (4 * nibble)) & 15) - ((zword >> (4 * nibble)) & 15)
    product = multiply(rounded(difference), convert(scale, FP16, FP32))
    return convert(product, FP32, BF16), kind(product) in ("nan", "inf")


@lru_cache(maxsize=1)
def mathematical_constants():
    with localcontext() as ctx:
        ctx.prec = 130
        # Chudnovsky computes pi independently of the RTL interval constants.
        m, l, x, k = 1, 13591409, 1, 6
        total = Decimal(l)
        for i in range(1, 12):
            m = m * (k ** 3 - 16 * k) // i ** 3
            l += 545140134
            x *= -262537412640768000
            total += Decimal(m * l) / Decimal(x)
            k += 12
        pi = 426880 * Decimal(10005).sqrt() / total
        return Fraction(pi), Fraction(Decimal(2).ln())


def exp32(a):
    if kind(a) == "nan":
        return FP32.nan
    if kind(a) == "inf":
        return 0 if a & FP32.sign else FP32.infinity
    x = value(a)
    if x <= -104:
        return 0
    if x >= 89:
        return FP32.infinity
    _, ln2 = mathematical_constants()
    n = nearest_integer(value(multiply(a, rounded(1 / ln2))))
    nf = rounded(n)
    hi = 0x3F317200
    lo = rounded(ln2 - value(hi))
    r = add(add(a, multiply(nf, hi) ^ FP32.sign), multiply(nf, lo) ^ FP32.sign)
    p = rounded(Fraction(1, math.factorial(12)))
    for degree in range(11, -1, -1):
        p = add(multiply(p, r), rounded(Fraction(1, math.factorial(degree))))
    return rounded(value(p) * pow2(n))


def sincos32(a):
    if kind(a) in ("nan", "inf") or abs(value(a)) > 32768:
        return FP32.nan, FP32.nan, True
    if kind(a) == "zero":
        return a, rounded(1), False
    pi, _ = mathematical_constants()
    x = value(a)
    q = nearest_integer(2 * x / pi)
    r = rounded(x - q * pi / 2)
    r2 = multiply(r, r)
    results = []
    for cosine in (False, True):
        coefficients = [
            rounded(Fraction((-1) ** k, math.factorial(2 * k + (not cosine))))
            for k in range(9)
        ]
        p = coefficients[-1]
        for coefficient in reversed(coefficients[:-1]):
            p = add(multiply(p, r2), coefficient)
        results.append(p if cosine else multiply(r, p))
    s, c = results
    return (
        (s, c),
        (c, s ^ FP32.sign),
        (s ^ FP32.sign, c ^ FP32.sign),
        (c ^ FP32.sign, s),
    )[q % 4] + (False,)


def as_float(bits):
    return struct.unpack(">f", bits.to_bytes(4, "big"))[0]


def fidelity(actual, reference):
    if len(actual) != len(reference) or not actual:
        raise ValueError("fidelity requires matching nonempty vectors")
    if not all(math.isfinite(x) for x in actual + reference):
        raise ValueError("nonfinite decoder observation")
    energy = math.fsum(x * x for x in reference)
    error = math.fsum((a - b) ** 2 for a, b in zip(actual, reference))
    ae = math.fsum(x * x for x in actual)
    cosine = (
        math.fsum(a * b for a, b in zip(actual, reference)) / math.sqrt(ae * energy)
        if ae and energy else float(ae == energy)
    )
    return {
        "nrmse": math.sqrt(error / len(actual)) / max(math.sqrt(energy / len(actual)), 2 ** -24),
        "cosine": cosine,
        "max_absolute_error": max(abs(a - b) for a, b in zip(actual, reference)),
    }
