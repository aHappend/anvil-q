"""Explicit Qwen split-half RoPE input table, with independent coefficient checks."""

from decimal import Decimal, ROUND_HALF_UP, localcontext
import math
import struct


PI = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286")


def sincos(value):
    value = (value + PI) % (2 * PI) - PI
    if value < -PI:
        value += 2 * PI
    sine = sine_term = value
    cosine = cosine_term = Decimal(1)
    for index in range(1, 160):
        sine_term *= -value * value / ((2 * index) * (2 * index + 1))
        cosine_term *= -value * value / ((2 * index - 1) * (2 * index))
        sine += sine_term
        cosine += cosine_term
        if abs(sine_term) < Decimal("1e-75") and abs(cosine_term) < Decimal("1e-75"):
            return sine, cosine
    raise ArithmeticError("high-precision RoPE series did not converge")


def quantize(value):
    return int((value * (1 << 30)).to_integral_value(rounding=ROUND_HALF_UP))


def write_table(path, base):
    comparisons = 0
    libm_disagreements = 0
    with localcontext() as context, path.open("r+b") as stream:
        context.prec = 80
        inverse = [(-Decimal(1000000).ln() * Decimal(2 * index) / 128).exp()
                   for index in range(64)]
        deltas = [sincos(frequency) for frequency in inverse]
        phases = [(Decimal(0), Decimal(1)) for _ in inverse]
        stream.seek(base)
        for position in range(32768):
            row = []
            for index, frequency in enumerate(inverse):
                sine, cosine = phases[index]
                actual = (quantize(cosine), quantize(sine))
                angle = position * (1000000.0 ** (-2 * index / 128))
                approximate = (round(math.cos(angle) * (1 << 30)),
                               round(math.sin(angle) * (1 << 30)))
                if any(abs(a - b) > 1 for a, b in zip(actual, approximate)):
                    raise ArithmeticError("RoPE convention differs from independent libm evaluation")
                comparisons += 2
                libm_disagreements += sum(a != b for a, b in zip(actual, approximate))
                if position in (0, 1, 2, 32767):
                    direct_sine, direct_cosine = sincos(Decimal(position) * frequency)
                    if actual != (quantize(direct_cosine), quantize(direct_sine)):
                        raise ArithmeticError("RoPE recurrence differs from direct high-precision series")
                row.extend(actual)
                delta_sine, delta_cosine = deltas[index]
                phases[index] = (sine * delta_cosine + cosine * delta_sine,
                                 cosine * delta_cosine - sine * delta_sine)
            stream.write(struct.pack("<128i", *row))
    return {"convention": "theta=1000000; angle=position*theta**(-2*i/128); split-half pairs",
            "encoding": "little-endian interleaved cos,sin signed Q2.30; nearest ties away",
            "generator_precision_decimal_digits": 80, "coefficient_comparisons": comparisons,
            "direct_series_checked_positions": [0, 1, 2, 32767],
            "libm_one_lsb_disagreements": libm_disagreements,
            "note": "libm checks the input convention, not a framework FP32 parity claim"}
