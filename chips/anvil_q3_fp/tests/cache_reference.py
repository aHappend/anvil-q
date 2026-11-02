"""Exact independent group-cache ABI, exponent selection and payload oracle."""

from fractions import Fraction

from ieee import classify, convert, exact, pack, power2, round_integer


def fp8_value(code):
    sign = -1 if code & 0x80 else 1
    exponent, fraction = (code >> 3) & 15, code & 7
    if exponent == 15 and fraction == 7:
        raise ValueError("forbidden E4M3FN NaN payload")
    return sign * (Fraction(fraction, 8) * power2(-6) if not exponent else
                   Fraction(8 + fraction, 8) * power2(exponent - 7))


FP8_POSITIVES = [fp8_value(code) for code in range(127)]


def encode(values, fmt, mode, fp8=0, affine=0):
    if mode == 0:
        return [values[index] | ((values[index + 1] if index + 1 < len(values) else 0) << 16)
                for index in range(0, len(values), 2)]
    if any(classify(value, fmt)[0] in ("nan", "inf") for value in values):
        raise ValueError("nonfinite lossy-cache source")
    represented = [exact(value, fmt) for value in values]
    zero_point = 0
    if not any(represented):
        exponent = 0
    else:
        for exponent in range(-256, 257):
            step = power2(exponent)
            if mode == 2 and affine:
                minimum, maximum = round_integer(min(represented) / step), round_integer(max(represented) / step)
                low, high = max(-8, -8 - minimum), min(7, 7 - maximum)
                if low <= high:
                    zero_point = max(low, min(0, high))
                    break
            elif max(map(abs, represented)) <= (448 if mode == 1 and fp8 else 127 if mode == 1 else 7) * step:
                break
        else:
            raise ValueError("no representable shared exponent")
    metadata = ((exponent & 0xffff) | ((zero_point & 15) << 16) |
                (int(fmt == "fp16") << 20) | (int(mode == 1 and fp8) << 21) | (mode << 22))
    payload = [0] * 8
    width = 8 if mode == 1 else 4
    for index, (raw, value) in enumerate(zip(values, represented)):
        if mode == 1 and fp8:
            magnitude = abs(value / power2(exponent))
            code = min(range(127), key=lambda code: (abs(FP8_POSITIVES[code] - magnitude), code % 2))
            code |= (raw >> 15) << 7
            bound = max((FP8_POSITIVES[min(126, code & 127) + 1] - FP8_POSITIVES[code & 127]) / 2
                        if (code & 127) < 126 else Fraction(16),
                        (FP8_POSITIVES[code & 127] - FP8_POSITIVES[max(0, (code & 127) - 1)]) / 2)
            if abs(abs(value / power2(exponent)) - FP8_POSITIVES[code & 127]) > bound:
                raise AssertionError("FP8 rounding error exceeds local half-spacing")
        else:
            lower = -127 if mode == 1 else -8 if affine else -7
            upper = 127 if mode == 1 else 7
            integer = max(lower, min(upper, round_integer(value / power2(exponent)) + zero_point))
            if abs(value - (integer - zero_point) * power2(exponent)) > power2(exponent) / 2:
                raise AssertionError("integer quantization exceeds half-step")
            code = integer & ((1 << width) - 1)
        per_word = 32 // width
        payload[index // per_word] |= code << (width * (index % per_word))
    return [metadata] + payload


def decode(words, count, fmt, mode, fp8=0, affine=0):
    if mode == 0:
        if len(words) != (count + 1) // 2 or (count % 2 and words[-1] >> 16):
            raise ValueError("bad Mode-0 padding/count")
        return [(words[index // 2] >> (16 * (index % 2))) & 0xffff for index in range(count)]
    if len(words) != 9:
        raise ValueError("bad lossy-cache word count")
    metadata = words[0]
    exponent = metadata & 0xffff
    exponent -= 65536 if exponent & 32768 else 0
    zero_point = (metadata >> 16) & 15
    zero_point -= 16 if zero_point & 8 else 0
    if (metadata >> 24 or (metadata >> 22) & 3 != mode or
            (metadata >> 21) & 1 != bool(mode == 1 and fp8) or
            (metadata >> 20) & 1 != bool(fmt == "fp16") or
            not -256 <= exponent <= 256 or
            (zero_point and not (mode == 2 and affine))):
        raise ValueError("malformed quantization metadata")
    width = 8 if mode == 1 else 4
    result = []
    for index in range(32 if mode == 1 else 64):
        per_word = 32 // width
        code = (words[1 + index // per_word] >> (width * (index % per_word))) & ((1 << width) - 1)
        if index >= count:
            if code:
                raise ValueError("nonzero quantized padding")
            continue
        sign = 0
        if mode == 1 and fp8:
            value = fp8_value(code)
            sign = code >> 7
        else:
            integer = code - (1 << width) if code >> (width - 1) else code
            if (mode == 1 and integer == -128) or (mode == 2 and not affine and integer == -8):
                raise ValueError("forbidden signed code")
            value = integer - zero_point
        wide = pack(value * power2(exponent), zero_sign=sign)[0]
        result.append(convert(wide, "fp32", fmt)[0])
    return result
