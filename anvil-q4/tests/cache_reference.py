"""Independent rational model of the admitted Q4 cache representation."""

from fractions import Fraction


MARKER = 0x7FC00000


def rne(value):
    """Round a nonnegative rational to an integer, ties to even."""
    quotient, remainder = divmod(value.numerator, value.denominator)
    return quotient + (2 * remainder > value.denominator or
                       (2 * remainder == value.denominator and quotient & 1))


def finite_value(bits):
    exponent = (bits >> 23) & 255
    if exponent == 255:
        raise ValueError("nonfinite FP32")
    significand = bits & 0x7FFFFF
    power = -149
    if exponent:
        significand |= 1 << 23
        power = exponent - 150
    value = Fraction(significand) * Fraction(2) ** power
    return -value if bits >> 31 else value


def fp32(value):
    sign = 0x80000000 if value < 0 else 0
    value = abs(value)
    if not value:
        return sign
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    if value < Fraction(2) ** exponent:
        exponent -= 1
    if exponent < -126:
        return sign | rne(value * (1 << 149))
    rounded = rne(value / Fraction(2) ** (exponent - 23))
    if rounded == 1 << 24:
        rounded >>= 1
        exponent += 1
    if exponent > 127:
        return sign | 0x7F800000
    return sign | ((exponent + 127) << 23) | (rounded & 0x7FFFFF)


def canonical(bits):
    if bits & 0x7F800000 == 0x7F800000 and bits & 0x7FFFFF:
        return MARKER
    return bits


def encode_head(values):
    escape = any((bits & 0x7F800000) == 0x7F800000 or
                 bits == 0x80000000 for bits in values)
    if not escape:
        maximum = max(abs(finite_value(bits)) for bits in values)
        scale = fp32(maximum / 127) if maximum else 0x3F800000
        escape = scale == 0
    if escape:
        return MARKER, [0] * len(values), [canonical(v) for v in values]
    codes = []
    reconstructed = []
    for bits in values:
        ratio = finite_value(fp32(finite_value(bits) / finite_value(scale)))
        code = min(127, rne(abs(ratio)))
        code = -code if ratio < 0 else code
        codes.append(code & 255)
        reconstructed.append(fp32(Fraction(code) * finite_value(scale)))
    return scale, codes, reconstructed


CASES = {
    "ordinary": [0x3F800000, 0xBF800000, 0x40000000, 0xBF000000],
    "subnormal63": [63, 0, 0x3F800000, 0xBF800000],
    "subnormal64": [64, 0, 0x3F800000, 0xBF800000],
    "signed_zero": [0x80000000, 0, 0, 0x80000000],
    "infinity": [0x7F800000, 0xFF800000, 0x3F800000, 0],
    "nan": [0x7FA00001, 0xFFC12345, 0x3F800000, 0xBF800000],
    "adjacent_escape": [0x3F800000, 0xBF800000, 1, 0x80000000],
    "positive_zero": [0, 0, 0, 0],
}


def fixture(name):
    # Two heads of dimension two share one packed word. K and V are distinct.
    inputs = CASES[name] + list(reversed(CASES[name]))
    scales, codes, decoded = [], [], []
    for start in range(0, 8, 2):
        scale, byte_codes, reconstruction = encode_head(inputs[start:start + 2])
        scales.append(scale)
        codes.extend(byte_codes)
        decoded.extend(reconstruction)
    words = [sum(codes[base + lane] << (8 * lane) for lane in range(4))
             for base in (0, 4)]
    # Layout is intentionally a test fixture ABI, not a copy of DUT state.
    return inputs + scales + decoded + words
