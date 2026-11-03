"""Independent integer/rational IEEE references; no RTL helper imports."""

import math
import random
import struct
from fractions import Fraction

INVALID, DIVZERO, OVERFLOW, UNDERFLOW, INEXACT = 16, 8, 4, 2, 1
NAN = 0x7FC00000


def decode(bits, fraction_bits=23, exponent_bits=8, bias=127):
    sign = bits >> (fraction_bits + exponent_bits)
    fraction = bits & ((1 << fraction_bits) - 1)
    exponent = (bits >> fraction_bits) & ((1 << exponent_bits) - 1)
    if exponent == (1 << exponent_bits) - 1:
        return ("nan" if fraction else "inf", sign, fraction, 0)
    return (
        "finite",
        sign,
        fraction + ((1 << fraction_bits) if exponent else 0),
        (exponent if exponent else 1) - bias - fraction_bits,
    )


def as_fraction(bits, fraction_bits=23):
    kind, sign, n, e = decode(bits, fraction_bits)
    if kind != "finite":
        raise ValueError("nonfinite rational")
    return (-1 if sign else 1) * Fraction(n) * Fraction(2) ** e


def round_integer(n, shift):
    if shift <= 0:
        return n << -shift, False
    kept, remainder = divmod(n, 1 << shift)
    half = 1 << (shift - 1)
    return kept + (remainder > half or (remainder == half and kept & 1)), bool(remainder)


def round_dyadic(n, exponent, fraction_bits=23, negative_zero=False):
    sign = int(n < 0 or (n == 0 and negative_zero))
    n = abs(n)
    sign_bits = sign << (fraction_bits + 8)
    if not n:
        return sign_bits, 0
    high = n.bit_length() - 1 + exponent
    quantum = max(high - fraction_bits, -126 - fraction_bits)
    rounded, lost = round_integer(n, quantum - exponent)
    if rounded == 0:
        return sign_bits, (UNDERFLOW | INEXACT) if lost else 0
    high = rounded.bit_length() - 1 + quantum
    if high > 127:
        return sign_bits | (255 << fraction_bits), OVERFLOW | INEXACT
    if high < -126:
        return sign_bits | rounded, (UNDERFLOW | INEXACT) if lost else 0
    mantissa = rounded << max(0, fraction_bits - (rounded.bit_length() - 1))
    mantissa >>= max(0, rounded.bit_length() - 1 - fraction_bits)
    return (
        sign_bits | ((high + 127) << fraction_bits) | (mantissa & ((1 << fraction_bits) - 1)),
        INEXACT if lost else 0,
    )


def mx_decode(code, scale):
    if scale == 255:
        return 0x7FC0, INVALID
    if code & 127 == 127:
        return 0x7FC0, 0
    exponent, fraction = (code >> 3) & 15, code & 7
    n = fraction + (8 if exponent else 0)
    e = (exponent - 10 if exponent else -9) + scale - 127
    return round_dyadic(-n if code & 128 else n, e, 7, bool(code & 128))


def reduce_terms(terms, flags=0):
    """Each term is (kind, sign, integer significand, binary exponent)."""
    has_nan = False
    infinities = set()
    finite = []
    all_negative_zero = True
    for kind, sign, n, e in terms:
        if kind == "nan":
            has_nan = True
            all_negative_zero = False
        elif kind == "inf":
            infinities.add(sign)
            all_negative_zero = False
        else:
            all_negative_zero &= n == 0 and bool(sign)
            if n:
                finite.append((-n if sign else n, e))
    if len(infinities) == 2:
        flags |= INVALID
    if has_nan or len(infinities) == 2:
        return NAN, flags
    if infinities:
        return (next(iter(infinities)) << 31) | 0x7F800000, flags
    exponent = min((e for _, e in finite), default=0)
    n = sum(n << (e - exponent) for n, e in finite)
    value, rounded_flags = round_dyadic(n, exponent, negative_zero=all_negative_zero)
    return value, flags | rounded_flags


def signaling_nan(bits, fraction_bits=23):
    kind, _, fraction, _ = decode(bits, fraction_bits)
    return kind == "nan" and not fraction & (1 << (fraction_bits - 1))


def product(a, b, fraction_bits=23):
    ka, sa, na, ea = decode(a, fraction_bits)
    kb, sb, nb, eb = decode(b, fraction_bits)
    invalid = (
        signaling_nan(a, fraction_bits)
        or signaling_nan(b, fraction_bits)
        or (ka == "inf" and kb == "finite" and not nb)
        or (kb == "inf" and ka == "finite" and not na)
    )
    if invalid or ka == "nan" or kb == "nan":
        return ("nan", 0, 0, 0), INVALID if invalid else 0
    if ka == "inf" or kb == "inf":
        return ("inf", sa ^ sb, 0, 0), 0
    return ("finite", sa ^ sb, na * nb, ea + eb), 0


def binary(a, b, multiply):
    if multiply:
        term, flags = product(a, b)
        return reduce_terms([term], flags)
    flags = INVALID if signaling_nan(a) or signaling_nan(b) else 0
    return reduce_terms([decode(a), decode(b)], flags)


def tensor(a, b, mask, acc, mx=False, a_scale=0x7F7F, b_scale=0x7F7F):
    terms = [decode(acc)]
    flags = INVALID if signaling_nan(acc) else 0
    finite_products = []
    for lane in range(64):
        if not (mask >> lane) & 1:
            continue
        av, bv = a[lane], b[lane]
        if mx:
            av, af = mx_decode(av, (a_scale >> (8 * (lane // 32))) & 255)
            bv, bf = mx_decode(bv, (b_scale >> (8 * (lane // 32))) & 255)
            flags |= af | bf
        term, product_flags = product(av, bv, 7)
        terms.append(term)
        flags |= product_flags
        if term[0] == "finite" and term[2]:
            finite_products.append((term[2], term[3]))
    maxima = [n.bit_length() - 1 + e for n, e in finite_products]
    if terms[0][0] == "finite" and terms[0][2]:
        maxima.append(terms[0][2].bit_length() - 1 + terms[0][3])
    maximum = max(maxima, default=-512)
    events = sum(
        e + (n & -n).bit_length() - 1 < maximum - 63
        for n, e in finite_products
    )
    result, status = reduce_terms(terms, flags)
    return result, status, events


def f32(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def bits32(value):
    try:
        return struct.unpack(">I", struct.pack(">f", value))[0]
    except OverflowError:
        return 0xFF800000 if value < 0 else 0x7F800000


def ordered(bits):
    return (~bits & 0xFFFFFFFF) if bits & 0x80000000 else bits ^ 0x80000000


def approximation_interval(value, tolerance, relative_only=False):
    width = tolerance * (abs(value) if relative_only else max(1, abs(value)))
    low, high = bits32(value - width), bits32(value + width)
    while f32(low) < value - width:
        low += -1 if low & 0x80000000 else 1
    while f32(high) > value + width:
        high += 1 if high & 0x80000000 else -1
    return low, high


def reference_selftest():
    assert round_dyadic(1, 0) == (0x3F800000, 0)
    assert round_dyadic((1 << 24) + 1, -24) == (0x3F800000, INEXACT)
    assert round_dyadic((1 << 24) + 3, -24) == (0x3F800002, INEXACT)
    assert round_dyadic(1, -150) == (0, UNDERFLOW | INEXACT)
    assert round_dyadic((1 << 24) - 1, -150) == (0x00800000, INEXACT)
    assert binary(0x80000000, 0x80000000, False) == (0x80000000, 0)
    assert binary(0x7F800000, 0, True) == (NAN, INVALID)
    assert mx_decode(0x7E, 127) == (0x43E0, 0)
    assert mx_decode(0x01, 127) == (0x3B00, 0)
    rng = random.Random(17)
    for _ in range(256):
        a = rng.randrange(0x7F800000)
        assert round_dyadic(decode(a)[2], decode(a)[3]) == (a, 0)
    assert math.isfinite(f32(0x7F7FFFFF))
