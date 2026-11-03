"""Independent integer/rational IEEE reference; no DUT helper imports."""

import math
import random
import struct
from fractions import Fraction


def decode(bits, exponent_bits, fraction_bits):
    sign = bits >> (exponent_bits + fraction_bits)
    exponent = (bits >> fraction_bits) & ((1 << exponent_bits) - 1)
    fraction = bits & ((1 << fraction_bits) - 1)
    if exponent == (1 << exponent_bits) - 1:
        return sign, "nan" if fraction else "inf", bool(
            fraction and not fraction & (1 << (fraction_bits - 1))
        ), None
    bias = (1 << (exponent_bits - 1)) - 1
    significand = fraction + ((1 << fraction_bits) if exponent else 0)
    power = (exponent - bias if exponent else 1 - bias) - fraction_bits
    value = Fraction(significand) * power_two(power)
    return sign, "finite", False, -value if sign else value


def power_two(exponent):
    return Fraction(1 << exponent) if exponent >= 0 else Fraction(1, 1 << -exponent)


def floor_log2(value):
    assert value > 0
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    return exponent - (value < power_two(exponent))


def round_even(value):
    quotient, remainder = divmod(value.numerator, value.denominator)
    twice = remainder * 2
    return quotient + (twice > value.denominator or (
        twice == value.denominator and quotient & 1
    ))


def binary32(value, negative_zero=False, alignment_lost=False):
    """Round a signed exact rational, with tininess after rounding."""
    sign = int(value < 0 or (value == 0 and negative_zero))
    magnitude = abs(value)
    if not magnitude:
        return sign << 31, int(alignment_lost)
    exponent = floor_log2(magnitude)
    unit = power_two(max(exponent - 23, -149))
    quantized = round_even(magnitude / unit)
    inexact = magnitude != quantized * unit or alignment_lost
    if quantized >= (1 << 24):
        quantized >>= 1
        exponent += 1
    if exponent > 127:
        return (sign << 31) | 0x7f800000, 5
    if exponent < -126:
        bits = quantized
    else:
        bits = ((exponent + 127) << 23) | (quantized & 0x7fffff)
    underflow = bool(inexact and bits < 0x800000)
    return (sign << 31) | bits, int(inexact) | (int(underflow) << 1)


def dot_reference(precision, a, b, mask, seed):
    if precision not in (1, 2):
        return 0x7fc00000, 16, None
    eb, fb = (8, 7) if precision == 1 else (5, 10)
    terms = []
    zero_signs = []
    infinities = set()
    nan = False
    invalid = False
    ss, sk, sn, sv = decode(seed, 8, 23)
    nan |= sk == "nan"
    invalid |= sn
    if sk == "inf":
        infinities.add(ss)
    elif sk == "finite":
        terms.append(sv)
        zero_signs.append(ss if sv == 0 else None)
    for lane in range(8):
        if not mask & (1 << lane):
            continue
        sa, ka, na, va = decode((a >> (16 * lane)) & 65535, eb, fb)
        sb, kb, nb, vb = decode((b >> (16 * lane)) & 65535, eb, fb)
        invalid |= na or nb
        nan |= ka == "nan" or kb == "nan"
        if (ka == "inf" and kb == "finite" and vb == 0) or (
            kb == "inf" and ka == "finite" and va == 0
        ):
            invalid = True
        if ka == "nan" or kb == "nan":
            continue
        if ka == "inf" or kb == "inf":
            infinities.add(sa ^ sb)
        else:
            terms.append(va * vb)
            zero_signs.append(sa ^ sb if va * vb == 0 else None)
    invalid |= len(infinities) > 1
    if invalid or nan:
        return 0x7fc00000, 16 if invalid else 0, None
    if infinities:
        return (next(iter(infinities)) << 31) | 0x7f800000, 0, None
    nonzero = [abs(x) for x in terms if x]
    exact = sum(terms, Fraction())
    if not nonzero:
        return binary32(Fraction(), all(s == 1 for s in zero_signs)) + (None,)
    step = power_two(floor_log2(max(nonzero)) - 63)
    aligned = sum(
        (int(abs(x) / step) * (-1 if x < 0 else 1) for x in terms), 0
    ) * step
    loss = abs(exact - aligned)
    assert loss < 9 * step
    lost = any(abs(x) % step != 0 for x in terms)
    result, status = binary32(aligned, alignment_lost=lost)
    return result, status, {"loss": str(loss), "step": str(step)}


def bits32(value):
    try:
        return struct.unpack(">I", struct.pack(">f", value))[0]
    except OverflowError:
        return 0xff800000 if value < 0 else 0x7f800000


def float32(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def dot_vectors(full=True):
    rng = random.Random(17)
    for precision in (1, 2):
        one = 0x3f80 if precision == 1 else 0x3c00
        special = ([0, 0x8000, 1, 0x7f, 0x80, 0x3f00, one, 0x7f7f,
                    0x7f80, 0xff80, 0x7fc0, 0x7f81] if precision == 1 else
                   [0, 0x8000, 1, 0x3ff, 0x400, 0x3800, one, 0x7bff,
                    0x7c00, 0xfc00, 0x7e00, 0x7c01])
        for mask in range(256):
            a = sum(special[i % len(special)] << (16 * i) for i in range(8))
            b = sum(one << (16 * i) for i in range(8))
            yield precision, a, b, mask, 0x80000000
        for a in special:
            for b in special:
                for seed in (0, 0x80000000, 0x3f800000, 0x7f800001):
                    yield precision, a, b, 1, seed
        for exponent in range(1, 255 if precision == 1 else 31):
            shift = 7 if precision == 1 else 10
            for offset in (-1, 0, 1):
                value = (exponent << shift) + offset
                yield precision, value, one, 1, 0
        # Equal-and-opposite products around a much smaller FP32 seed.
        for seed in (1, 0x80000001, 0x33800000, 0xb3800000, 0x3f800000):
            for value in special[:-4]:
                yield precision, value | ((value ^ 0x8000) << 16), (
                    one | (one << 16)), 3, seed
        if full:
            for encoding in range(65536):
                yield precision, encoding, one, 1, 0
                yield precision, one, encoding, 1, 0x33800000
        for _ in range(100000 if full else 128):
            yield precision, rng.getrandbits(128), rng.getrandbits(128), (
                rng.randrange(256)), rng.getrandbits(32)
    for precision in (0, 3):
        yield precision, 0, 0, 0, 0


def scalar_vectors(full=True):
    special = [0, 0x80000000, 1, 0x800000, 0x3f800000, 0x40000000,
               0x40800000, 0x7f7fffff, 0x7f800000, 0xff800000,
               0x7fc00000, 0x7f800001, 0xbf800000, bits32(-80),
               bits32(-80) + 1, bits32(88.72), bits32(89)]
    for bits in special:
        yield bits
    for exponent in range(255):
        for fraction in (0, 1, 0x3fffff, 0x7fffff):
            yield (exponent << 23) | fraction
    # Exp range-reduction boundaries, on both sides of n*ln(2).
    for n in range(-115, 129):
        center = bits32(n * math.log(2))
        for delta in (-1, 0, 1):
            yield (center + delta) & 0xffffffff
    rng = random.Random(53)
    for index in range(100000 if full else 128):
        if index & 1:
            yield bits32(rng.uniform(-80, 0))
        else:
            yield rng.randrange(1, 0x7f800000)


def check_scalar(name, xbits, result, status):
    sign, kind, signaling, value = decode(xbits, 8, 23)
    if kind == "nan":
        return result == 0x7fc00000 and status == (16 if signaling else 0)
    if name == "exp":
        if kind == "inf":
            return result == (0 if sign else 0x7f800000) and status == 0
        x = float(value)
        if x < -80:
            return result == 0 and status == 1
        if not value:
            return result == 0x3f800000 and status == 0
        if x > 90:
            return result == 0x7f800000 and status == 5
        reference = math.exp(x)
        relative = 2e-5
    elif name == "reciprocal":
        if kind == "inf":
            return result == (sign << 31) and status == 0
        if value == 0:
            return result == ((sign << 31) | 0x7f800000) and status == 8
        reference = 1.0 / float(value)
        relative = 2e-6
    else:
        if kind == "finite" and value == 0:
            return result == ((sign << 31) | 0x7f800000) and status == 8
        if sign:
            return result == 0x7fc00000 and status == 16
        if kind == "inf":
            return result == 0 and status == 0
        reference = 1.0 / math.sqrt(float(value))
        relative = 2e-6
    rounded = bits32(reference)
    if rounded & 0x7fffffff == 0x7f800000:
        return result == rounded and status == 5
    actual = float32(result)
    if not math.isfinite(actual) or status & 28:
        return False
    ulp = 2.0 ** (max(math.frexp(abs(reference))[1] - 1, -126) - 23)
    bound = (2 * ulp if abs(reference) < 2.0 ** -126 else
             relative * abs(reference) + ulp)
    return abs(actual - reference) <= bound
