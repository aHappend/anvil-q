"""Independent exact-integer IEEE oracle; no RTL or parent tables are imported."""

from dataclasses import dataclass
from decimal import Decimal, localcontext


@dataclass(frozen=True)
class Format:
    exponent: int
    fraction: int

    @property
    def bias(self):
        return (1 << (self.exponent - 1)) - 1

    @property
    def infinity(self):
        return ((1 << self.exponent) - 1) << self.fraction

    @property
    def nan(self):
        return self.infinity | (1 << (self.fraction - 1))

    @property
    def sign(self):
        return 1 << (self.exponent + self.fraction)


BF16 = Format(8, 7)
FP16 = Format(5, 10)
FP32 = Format(8, 23)


def decode(bits, fmt):
    """Return sign, unsigned integer significand, binary power, special class."""
    sign = bool(bits & fmt.sign)
    fraction = bits & ((1 << fmt.fraction) - 1)
    exponent = (bits >> fmt.fraction) & ((1 << fmt.exponent) - 1)
    if exponent == (1 << fmt.exponent) - 1:
        return sign, 0, 0, "nan" if fraction else "inf"
    significand = fraction if exponent == 0 else (1 << fmt.fraction) | fraction
    power = (exponent or 1) - fmt.bias - fmt.fraction
    return sign, significand, power, "finite"


def round_integer(value, shift):
    if shift <= 0:
        return value << -shift
    quotient, remainder = divmod(value, 1 << shift)
    midpoint = 1 << (shift - 1)
    return quotient + (remainder > midpoint or (remainder == midpoint and quotient & 1))


def encode(sign, magnitude, power, fmt):
    """Round an exact dyadic once, including gradual underflow and overflow."""
    sign_bit = fmt.sign if sign else 0
    if magnitude == 0:
        return sign_bit, False
    top_exponent = magnitude.bit_length() - 1 + power
    quantum = max(top_exponent - fmt.fraction, 1 - fmt.bias - fmt.fraction)
    rounded = round_integer(magnitude, quantum - power)
    if rounded == 0:
        return sign_bit, False
    if rounded >= 1 << (fmt.fraction + 1):
        rounded >>= 1
        quantum += 1
    exponent = quantum + fmt.fraction + fmt.bias
    if exponent >= (1 << fmt.exponent) - 1:
        return sign_bit | fmt.infinity, True
    if rounded < 1 << fmt.fraction:
        return sign_bit | rounded, False
    return sign_bit | (exponent << fmt.fraction) | (rounded - (1 << fmt.fraction)), False


def encode_ratio(sign, numerator, denominator, power, fmt):
    if numerator == 0:
        return fmt.sign if sign else 0, False
    top = numerator.bit_length() - denominator.bit_length()
    below = numerator < (denominator << top) if top >= 0 else (numerator << -top) < denominator
    if below:
        top -= 1
    quantum = max(top + power - fmt.fraction, 1 - fmt.bias - fmt.fraction)
    shift = power - quantum
    n, d = (numerator << shift, denominator) if shift >= 0 else (numerator, denominator << -shift)
    quotient, remainder = divmod(n, d)
    rounded = quotient + (2 * remainder > d or (2 * remainder == d and quotient & 1))
    return encode(sign, rounded, quantum, fmt)


def convert(bits, source, destination):
    sign, magnitude, power, special = decode(bits, source)
    if special != "finite":
        return (destination.nan if special == "nan" else
                (destination.sign if sign else 0) | destination.infinity), True
    return encode(sign, magnitude, power, destination)


def multiply(a, b, afmt=FP32, bfmt=FP32, destination=FP32, keep=True):
    if not keep:
        return 0, False
    sa, ma, ea, ca = decode(a, afmt)
    sb, mb, eb, cb = decode(b, bfmt)
    if ca == "nan" or cb == "nan" or (
        ca == "inf" and cb == "finite" and mb == 0
    ) or (cb == "inf" and ca == "finite" and ma == 0):
        return destination.nan, True
    if ca == "inf" or cb == "inf":
        return (destination.sign if sa != sb else 0) | destination.infinity, True
    return encode(sa != sb, ma * mb, ea + eb, destination)


def add(a, b):
    sa, ma, ea, ca = decode(a, FP32)
    sb, mb, eb, cb = decode(b, FP32)
    if ca == "nan" or cb == "nan" or (ca == cb == "inf" and sa != sb):
        return FP32.nan, True
    if ca == "inf" or cb == "inf":
        sign = sa if ca == "inf" else sb
        return (FP32.sign if sign else 0) | FP32.infinity, True
    quantum = min(ea, eb)
    total = (-1 if sa else 1) * (ma << (ea - quantum))
    total += (-1 if sb else 1) * (mb << (eb - quantum))
    sign = total < 0 or (ma == mb == 0 and sa and sb)
    return encode(sign, abs(total), quantum, FP32)


def dequant(code, zero, scale, required=True):
    if not required:
        return 0, False
    sign, magnitude, power, special = decode(scale, BF16)
    difference = code - zero
    if special != "finite":
        if special == "nan" or difference == 0:
            return BF16.nan, True
        return (BF16.sign if sign != (difference < 0) else 0) | BF16.infinity, True
    return encode(sign != (difference < 0), abs(difference) * magnitude, power, BF16)


def dot(activations, weights, keep, afmt, bfmt, bias=0):
    products = [multiply(a, b, afmt, bfmt, keep=k)
                for a, b, k in zip(activations, weights, keep)]
    while len(products) > 1:
        reduced = []
        for (a, ae), (b, be) in zip(products[0::2], products[1::2]):
            value, error = add(a, b)
            reduced.append((value, error or ae or be))
        products = reduced
    value, error = add(products[0][0], bias)
    return value, error or products[0][1]


def tree(count, ids, parents, targets, position, pointer, complete, errors,
         layers=28, maximum=32768, new_sequence=False):
    bad = count not in (1, 2, 4) or parents[0] != 0
    bad |= not new_sequence and position != pointer
    bad |= position >= maximum
    for node in range(min(count, 4)):
        bad |= node > 0 and parents[node] >= node
        bad |= bool(errors & (1 << node))
        bad |= ((complete >> (28 * node)) & ((1 << layers) - 1)) != (1 << layers) - 1
    path = [0]
    if not bad:
        while len(path) < count:
            children = [i for i in range(1, count)
                        if parents[i] == path[-1] and ids[i] == targets[path[-1]]]
            if not children:
                break
            path.append(min(children))
    bad |= position + len(path) > maximum
    if bad:
        return 0, 0, 0, 0, True
    return len(path), sum(1 << i for i in path), targets[path[-1]], position + len(path), False


def decimal_value(bits, fmt=FP32):
    sign, magnitude, power, special = decode(bits, fmt)
    if special != "finite":
        return Decimal("NaN" if special == "nan" else "-Infinity" if sign else "Infinity")
    with localcontext() as context:
        context.prec = 100
        return Decimal(-magnitude if sign else magnitude) * (Decimal(2) ** power)


def transcendental(operation, bits):
    with localcontext() as context:
        context.prec = 100
        value = decimal_value(bits)
        if operation == 2:
            return 1 / value
        if operation == 3:
            return 1 / value.sqrt()
        if operation == 4:
            return value.exp()
        if operation == 5:
            return 1 / (1 + (-value).exp())
        raise ValueError(f"not a transcendental operation: {operation}")


def kv_encode(values, int8):
    if any(decode(v, BF16)[3] != "finite" for v in values):
        return 0, [0] * len(values), True
    if not int8:
        return sum(v << (16*i) for i, v in enumerate(values)), values, False
    maximum = max(v & 0x7fff for v in values)
    if maximum == 0:
        scale = 0x3f80
    else:
        _, magnitude, power, _ = decode(maximum, BF16)
        scale = max(1, encode_ratio(False, magnitude, 127, power, BF16)[0])
    _, sm, se, _ = decode(scale, BF16)
    codes, decoded = [], []
    for value in values:
        sign, magnitude, power, _ = decode(value, BF16)
        gap = power - se
        n, d = (magnitude << gap, sm) if gap >= 0 else (magnitude, sm << -gap)
        q, r = divmod(n, d)
        q = min(127, q + (2*r > d or (2*r == d and q & 1)))
        q = -q if sign else q
        codes.append(q & 255)
        reconstructed, error = encode(q < 0, abs(q)*sm, se, BF16)
        if error:
            return 0, [0] * len(values), True
        decoded.append(reconstructed)
    record = scale | sum(q << (16+8*i) for i, q in enumerate(codes))
    return record, decoded, False


def kv_decode(record, words, int8):
    if not int8:
        values = [(record >> (16*i)) & 65535 for i in range(words)]
        error = any(decode(v, BF16)[3] != "finite" for v in values)
        return [0]*words if error else values, error
    scale = record & 65535
    sign, magnitude, power, special = decode(scale, BF16)
    if sign or magnitude == 0 or special != "finite":
        return [0]*words, True
    values = []
    for i in range(words):
        q = (record >> (16+8*i)) & 255
        q = q - 256 if q >= 128 else q
        if q == -128:
            return [0]*words, True
        value, error = encode(q < 0, abs(q)*magnitude, power, BF16)
        if error:
            return [0]*words, True
        values.append(value)
    return values, False
