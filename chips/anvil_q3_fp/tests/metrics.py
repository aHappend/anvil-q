"""Numerical populations, including zero and nonfinite classifications."""

import math

from ieee import bits_float, convert, float_bits


def ordered(bits, width):
    sign = 1 << (width - 1)
    return (~bits & ((1 << width) - 1)) if bits & sign else bits | sign


def compare(raw, expected, fmt):
    if not raw or len(raw) != len(expected):
        raise AssertionError("Numerical comparison has missing or unequal populations")
    actual = [bits_float(value) for value in raw]
    classifications = {"finite": 0, "zero": 0, "nan": 0, "infinity": 0}
    absolute, ulp32, ulp16 = [], [], []
    for bits, x, y in zip(raw, actual, expected):
        if math.isnan(x) or math.isnan(y):
            classifications["nan"] += 1
            if not (math.isnan(x) and math.isnan(y)):
                raise AssertionError("Unexpected NaN in numerical population")
            continue
        if math.isinf(x) or math.isinf(y):
            classifications["infinity"] += 1
            if x != y:
                raise AssertionError("Unexpected infinity in numerical population")
            continue
        classifications["zero" if x == 0 else "finite"] += 1
        absolute.append(abs(x - y))
        target = float_bits(y)
        ulp32.append(abs(ordered(bits, 32) - ordered(target, 32)))
        a = convert(bits, "fp32", fmt)[0]
        b = convert(target, "fp32", fmt)[0]
        ulp16.append(abs(ordered(a, 16) - ordered(b, 16)))
    if len(absolute) != len(raw):
        raise AssertionError("Seeded fidelity fixture unexpectedly contains nonfinite values")
    norm_actual = math.sqrt(sum(x * x for x in actual))
    norm_reference = math.sqrt(sum(x * x for x in expected))
    cosine = (1.0 if not norm_actual and not norm_reference else
              0.0 if not norm_actual or not norm_reference else
              sum(x * y for x, y in zip(actual, expected)) / (norm_actual * norm_reference))
    def distribution(values):
        values = sorted(values)
        return {"count": len(values), "maximum": max(values),
                "median": values[len(values) // 2], "p99": values[min(len(values) - 1, len(values) * 99 // 100)]}
    return {"count": len(raw), "classifications": classifications, "cosine": cosine,
            "maximum_absolute_error": max(absolute),
            "rms_absolute_error": math.sqrt(sum(x * x for x in absolute) / len(absolute)),
            "binary32_ulp": distribution(ulp32), "selected_format_ulp": distribution(ulp16)}
