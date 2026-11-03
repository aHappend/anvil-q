"""Independent high-precision nonlinear and exact quantization comparisons."""

import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment
from ieee_reference import decode, evaluate, nearest_integer, rounded


def bits(value):
    return rounded(Fraction(value))[0]


def interval(reference, tolerance):
    lo, hi = reference - tolerance, reference + tolerance
    lower, upper = bits(lo), bits(hi)
    if decode(lower)[2] < Fraction(lo):
        lower += -1 if lower >> 31 else 1
    if decode(upper)[2] > Fraction(hi):
        upper += 1 if upper >> 31 else -1
    return lower, upper


def vectors(points=2049):
    with localcontext() as context:
        context.prec = 80
        for unit, start, end in ((0, -80, 0), (1, -32, 32)):
            for n in range(points):
                a = bits(Decimal(start) + Decimal(end-start)*n/(points-1))
                value = decode(a)[2]
                x = Decimal(value.numerator)/Decimal(value.denominator)
                expected = x.exp() if unit == 0 else x/(1+(-x).exp())
                tolerance = Decimal("2e-6") * abs(expected)
                if unit == 1:
                    tolerance += Decimal("2e-6")
                lo, hi = interval(expected, tolerance)
                yield (unit, 0, 0, 0, 0, 1, a, 0, 0, lo, hi, 0, 0, 0)
        for unit in (0, 1):
            for a in (0, 0x80000000, 1, 0x80000001, 0x7f800000,
                      0xff800000, 0x7fc00000, 0x7f800001):
                sign, kind, value = decode(a)
                if kind == "nan" or kind == "inf" and sign and unit == 1:
                    expected = 0x7fc00000
                    flags = 16 if kind == "inf" or not value & 0x400000 else 0
                elif kind == "inf":
                    expected, flags = (0 if sign else 0x7f800000), 0
                elif unit == 0:
                    reference = (Decimal(value.numerator)/value.denominator).exp()
                    expected = bits(reference)
                    flags = 0
                else:
                    x = Decimal(value.numerator)/value.denominator
                    reference = x/(1+(-x).exp())
                    expected = rounded(Fraction(reference), zero_sign=sign)[0]
                    flags = 0
                if kind == "finite" and value:
                    tolerance = Decimal("2e-6") * abs(reference)
                    if unit == 1:
                        tolerance += Decimal("2e-6")
                    lo, hi = interval(reference, tolerance)
                else:
                    lo = hi = expected
                yield (unit, 0, 0, 0, 0, 1, a, 0, 0,
                       lo, hi, flags, 16, 0)

    offsets = (0, 16, 4, 20, 8, 24, 12, 28)
    scales = (0x3c800000, 0x3eaaaaab, 1, 0x7f000000)
    for fmt in (1, 2):
        width, lanes = (4, 8) if fmt == 1 else (8, 4)
        for asymmetric in (0, 1):
            for q in range(1 << width):
                for z in range(1 << width) if asymmetric and fmt == 1 else (
                        (0, 1, 127, 255) if asymmetric else (0,)):
                    for lane in range(lanes):
                        scale = scales[(q+z+lane) % len(scales)]
                        shift = offsets[lane] if fmt == 1 else lane*8
                        payload = (0x76543210 & ~(((1 << width)-1) << shift)) | q << shift
                        integer = q if asymmetric or q < (1 << (width-1)) else q-(1 << width)
                        integer -= z
                        value, flags = evaluate(9, integer & 0xffffffff)
                        value, f = evaluate(2, value, scale)
                        flags |= f
                        value, f = evaluate(7, value)
                        flags |= f
                        value, f = evaluate(5, value)
                        flags |= f
                        yield (2, fmt, 0, asymmetric, lane, 1, payload, z, scale,
                               value, value, flags, 31, 0)
    for fmt, lane, payload, zero, scale in (
            (3, 0, 0, 0, 0x3f800000), (2, 4, 0, 0, 0x3f800000),
            (0, 0, 0x10000, 0, 0x3f800000), (1, 0, 0, 16, 0x3f800000),
            (2, 0, 0, 256, 0x3f800000),
            *((1, 0, 0, 0, s) for s in (0, 0x80000000, 0xbf800000, 0x7f800000, 0x7fc00000))):
        yield (2, fmt, 0, 1, lane, 1, payload, zero, scale, 0, 0, 0, 31, 1)
        yield (2, fmt, 0, 1, lane, 0, payload, zero, scale, 0, 0, 0, 31, 0)
    for activation_format in (0, 1):
        for value in (0, 1, 0x3c00, 0x3f80, 0x7f80, 0x7c00, 0x8000, 0xffff):
            expected, flags = evaluate(6 if activation_format else 5, value)
            yield (2, 0, activation_format, 0, 0, 1, value, 0, 0,
                   expected, expected, flags, 31, 0)
    for scale in (0x3f800000, 0x3c800000, 0x3eaaaaab):
        for n in range(-260, 261):
            # Halfway integers and either neighboring FP32 input exercise RNE.
            base = bits(Fraction(n, 2) * decode(scale)[2])
            for a in (base, (base-1) & 0xffffffff, (base+1) & 0xffffffff):
                if decode(a)[1] != "finite":
                    continue
                quotient, flags = evaluate(3, a, scale)
                integer = min(127, max(-127, nearest_integer(decode(quotient)[2])))
                value, f = evaluate(9, integer & 0xffffffff)
                flags |= f
                value, f = evaluate(2, value, scale)
                flags |= f
                value, f = evaluate(7, value)
                flags |= f
                value, f = evaluate(5, value)
                flags |= f
                yield (3, 0, 0, 0, 0, 1, a, scale, 0,
                       value, value, flags, 31, 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("numerics", args.preparation, args.repair_of)
    error = None
    objects = experiment.directory / "compile-obj"
    try:
        fixture = experiment.directory / "vectors.txt"
        counts = [0]*4
        with fixture.open("w") as stream:
            for vector in vectors():
                counts[vector[0]] += 1
                stream.write(" ".join(str(x) for x in vector[:6]) + " " +
                             " ".join(f"{x:08x}" for x in vector[6:13]) +
                             f" {vector[13]}\n")
        experiment.receipt["fixture_sha256"] = hashlib.sha256(fixture.read_bytes()).hexdigest()
        experiment.receipt["generated_counts"] = counts
        experiment.receipt["tool_version"] = experiment.run(
            ["verilator", "--version"], "version").strip()
        sources = ["anvil_q4_00_fp_pkg", "anvil_q4_fp32", "anvil_q4_umul64",
                   "anvil_q4_exp", "anvil_q4_silu", "anvil_q4_dequant",
                   "anvil_q4_activation_quantizer"]
        experiment.run([
            "verilator", "--binary", "--timing", "-Wno-fatal",
            "--top-module", "numerics_tb", "--Mdir", experiment.rel(objects),
            "-o", "numerics-sim", *("rtl/"+name+".sv" for name in sources),
            "tests/numerics_tb.sv"], "compile")
        output = experiment.run([experiment.rel(objects/"numerics-sim"),
                                 "+VECTORS="+experiment.rel(fixture)], "simulation")
        if f"SUMMARY numerics comparisons={sum(counts)} " not in output:
            raise AssertionError("missing numerical comparison summary")
        experiment.receipt["comparisons"] = dict(zip(("exp", "silu", "dequant", "a8"), counts))
        experiment.prune_objects(objects)
    except (RuntimeError, ValueError, AssertionError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
