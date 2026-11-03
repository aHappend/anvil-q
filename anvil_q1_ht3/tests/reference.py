"""Independent exact-rational IEEE and cache-write reference calculations."""

from fractions import Fraction
import math
import random
import struct


def decode(bits, ebits=8, fbits=23):
    sign = bits >> (ebits + fbits)
    exp = (bits >> fbits) & ((1 << ebits) - 1)
    frac = bits & ((1 << fbits) - 1)
    if exp == (1 << ebits) - 1:
        return ("nan" if frac else "inf"), sign, None
    bias = (1 << (ebits - 1)) - 1
    power = (exp - bias if exp else 1 - bias) - fbits
    sig = frac + ((1 << fbits) if exp else 0)
    value = Fraction(sig << max(0, power), 1 << max(0, -power))
    return "finite", sign, -value if sign else value


def nearest_even(value):
    q, r = divmod(value.numerator, value.denominator)
    return q + (2 * r > value.denominator or
                (2 * r == value.denominator and q & 1))


def encode(value, ebits=8, fbits=23, zero_sign=0):
    sign = int(value < 0) if value else zero_sign
    value = abs(value)
    sign_field = sign << (ebits + fbits)
    if not value:
        return sign_field
    bias = (1 << (ebits - 1)) - 1
    emin, emax = 1 - bias, bias
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    power = Fraction(1 << max(exponent, 0), 1 << max(-exponent, 0))
    if value < power:
        exponent -= 1
    spacing = max(exponent, emin) - fbits
    unit = Fraction(1 << max(spacing, 0), 1 << max(-spacing, 0))
    integer = nearest_even(value / unit)
    if integer >= (1 << (fbits + 1)):
        integer >>= 1
        exponent += 1
    if exponent > emax:
        return sign_field | (((1 << ebits) - 1) << fbits)
    if exponent < emin:
        encoded_exp = int(integer >= (1 << fbits))
    else:
        encoded_exp = exponent + bias
    return sign_field | (encoded_exp << fbits) | (integer & ((1 << fbits) - 1))


def binary(op, a, b):
    ca, sa, va = decode(a)
    cb, sb, vb = decode(b)
    if ca == "nan" or cb == "nan":
        return 0x7FC00000
    if op == 0:
        if ca == cb == "inf" and sa != sb:
            return 0x7FC00000
        if ca == "inf":
            return (sa << 31) | 0x7F800000
        if cb == "inf":
            return (sb << 31) | 0x7F800000
        return encode(va + vb, zero_sign=sa & sb)
    if ca == "inf" or cb == "inf":
        if (ca == "finite" and va == 0) or (cb == "finite" and vb == 0):
            return 0x7FC00000
        return ((sa ^ sb) << 31) | 0x7F800000
    return encode(va * vb, zero_sign=sa ^ sb)


def convert(bits, fp16, expand=False):
    ebits, fbits = (5, 10) if fp16 else (8, 7)
    kind, sign, value = decode(bits, ebits, fbits) if expand else decode(bits)
    out_e, out_f = (8, 23) if expand else (ebits, fbits)
    if kind == "nan":
        return (((1 << out_e) - 1) << out_f) | (1 << (out_f - 1))
    if kind == "inf":
        return (sign << (out_e + out_f)) | (((1 << out_e) - 1) << out_f)
    return encode(value, out_e, out_f, sign)


def quantize(x, scale, int8):
    cx, _, vx = decode(x)
    cs, _, vs = decode(scale)
    if cx != "finite" or cs != "finite" or vs <= 0:
        return 0, 1
    width = 8 if int8 else 4
    code = max(-(1 << (width - 1)),
               min((1 << (width - 1)) - 1, nearest_even(vx / vs)))
    return code & ((1 << width) - 1), 0


def float_bits(value):
    return struct.unpack("<I", struct.pack("<f", value))[0]


def float_value(bits):
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def vector_check(actual, reference):
    if not actual or len(actual) != len(reference):
        raise AssertionError("missing or wrong-length vector")
    if not all(math.isfinite(x) for x in actual + reference):
        raise AssertionError("nonfinite active vector")
    aa = sum(x * x for x in actual)
    rr = sum(x * x for x in reference)
    max_ref = max(abs(x) for x in reference)
    error = max(abs(a - r) for a, r in zip(actual, reference))
    if not aa or not rr:
        if aa != rr or any(x != 0 for x in actual):
            raise AssertionError("zero-vector mismatch")
        else:
            cosine = 1.0
    else:
        cosine = sum(a * r for a, r in zip(actual, reference)) / math.sqrt(aa * rr)
    limit = 2e-4 * max(1, max_ref)
    if cosine < 0.9999 or error > limit:
        raise AssertionError(f"vector cosine={cosine}, error={error}, limit={limit}")
    return cosine, error


def primitive_vectors(seed, compact=False):
    rng = random.Random(seed)
    special = [0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x00800000,
               0x00800001, 0x3F000000, 0x3F800000, 0xBF800000, 0x3F800001,
               0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000,
               0x7FC00000, 0x7F800001, 0xFFC01234]
    for op in (0, 1):
        for a in special:
            for b in special:
                yield op, a, b, 0, binary(op, a, b)
        for _ in range(4096):
            a, b = rng.getrandbits(32), rng.getrandbits(32)
            while (a >> 23) & 255 == 255:
                a = rng.getrandbits(32)
            while (b >> 23) & 255 == 255:
                b = rng.getrandbits(32)
            yield op, a, b, 0, binary(op, a, b)
    for fp16 in (0, 1):
        for a in special + [rng.getrandbits(32) for _ in range(4096)]:
            yield 2, a, 0, fp16, convert(a, fp16)
        values = range(65536) if not compact else (
            list(range(32)) + [0x7C00, 0xFC00, 0x7E00, 0x8000, 0x7F80, 0x7FC0] +
            [rng.getrandbits(16) for _ in range(4096)])
        for a in values:
            yield 3, a, 0, fp16, convert(a, fp16, True)


def quantizer_vectors(seed):
    rng = random.Random(seed)
    scales = [1, 2, 0x007FFFFF, 0x00800000, 0x00800001, 0x3EAAAAAB,
              0x3F000000, 0x3F800000, 0x3FC00000, 0x40000000, 0x7F7FFFFF]
    for int8 in (0, 1):
        width = 8 if int8 else 4
        low, high = -(1 << (width - 1)), (1 << (width - 1)) - 1
        pairs = [(x, s) for x in [0, 0x80000000, 1, 0x80000001,
                                 0x007FFFFF, 0x807FFFFF, 0x00800000,
                                 0x80800000, 0x7F7FFFFF, 0xFF7FFFFF]
                 for s in scales]
        for s in scales:
            vs = decode(s)[2]
            for q in range(low - 2, high + 3):
                for value in (Fraction(q), Fraction(2 * q + 1, 2)):
                    x = encode(value * vs)
                    if decode(x)[0] == "finite":
                        pairs.append((x, s))
                        if x & 0x7FFFFFFF:
                            pairs.extend([(x - 1, s), (x + 1, s)])
        for _ in range(4096):
            x, s = rng.getrandbits(32), rng.randrange(1, 0x7F800000)
            if decode(x)[0] == "finite":
                pairs.append((x, s))
        pairs.extend((x, s) for x in (0x7F800000, 0xFF800000, 0x7FC00000)
                     for s in scales)
        pairs.extend((float_bits(1.5), s) for s in
                     (0, 0x80000000, 0xBF800000, 0x7F800000, 0x7FC00000))
        for x, s in pairs:
            code, error = quantize(x, s, int8)
            yield x, s, int8, code, error
