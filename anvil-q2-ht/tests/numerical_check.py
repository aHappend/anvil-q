"""Exact independent scalar conversion, integer and exponential experiments."""

import argparse
from fractions import Fraction
from math import isqrt
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import (exp_q24, fraction_q16, ieee_round, ieee_value, rhaz, rounded_div)
from retention import Experiment


def vectors(path, unit):
    rows = []
    mask = (1 << 128) - 1
    result_mask = mask if unit == "integer" else (1 << 32) - 1
    coverage = {"operations": {}, "annulled": 0, "errors": 0, "seeds": [11, 29, 101]}

    def add(op, a, b, expected, error=0, annul=0):
        rows.append(f"{op} {a & mask:x} {b & mask:x} {expected & result_mask:x} {error} {annul}\n")
        coverage["operations"][str(op)] = coverage["operations"].get(str(op), 0) + 1
        coverage["errors"] += error
        coverage["annulled"] += annul

    if unit == "convert":
        for word in range(65536):
            for op, exponent, fraction in ((0, 5, 10), (1, 8, 7), (6, 5, 10), (7, 8, 7)):
                try:
                    value = ieee_value(word, exponent, fraction)
                    expected = (fraction_q16(value) if op < 2 else
                                ieee_round(value, 8, 23, negative_zero=bool(word & 0x8000)))
                    add(op, word, 0, expected)
                except ValueError:
                    add(op, word, 0, 0, error=1)
        cases = {0, -1, 1, -(1 << 31), (1 << 31) - 1}
        for power in range(31):
            for offset in (-1, 0, 1):
                for sign in (-1, 1):
                    value = sign * ((1 << power) + offset)
                    if -(1 << 31) <= value < 1 << 31:
                        cases.add(value)
        for seed in coverage["seeds"]:
            rng = random.Random(seed)
            cases.update(rng.randint(-(1 << 31), (1 << 31) - 1) for _ in range(1000))
        for value in sorted(cases):
            for op, exponent, fraction in ((3, 5, 10), (4, 8, 7), (5, 8, 23)):
                add(op, value & 0xffffffff, 0,
                    ieee_round(Fraction(value, 1 << 16), exponent, fraction))
        for op in (8, 9, 15):
            add(op, 0, 0, 0, error=1)
        for word in (0, 1, 0x80000000, 0x7fffffff, 0x3f800000, 0x7f7fffff,
                     0xff7fffff, 0x7fc00000, 0xff800000, 0x80000001):
            try:
                add(2, word, 0, fraction_q16(ieee_value(word, 8, 23)))
            except ValueError:
                add(2, word, 0, 0, error=1)
    elif unit == "integer":
        for seed in coverage["seeds"]:
            rng = random.Random(seed)
            for index in range(128):
                a = rng.randrange(-(1 << 127), 1 << 127)
                b = rng.randrange(-(1 << 127), 1 << 127)
                add(0, a, b, a + b)
                add(7, a, b, a - b)
                for op, bits in ((1, 64), (6, 32)):
                    x = rng.randrange(-(1 << (bits - 1)), 1 << (bits - 1))
                    y = rng.randrange(-(1 << (bits - 1)), 1 << (bits - 1))
                    add(op, x, y, x * y)
                unsigned = rng.getrandbits(128)
                denominator = rng.randrange(1, 1 << 64)
                add(2, unsigned, denominator, unsigned // denominator)
                add(3, a, denominator, rounded_div(a, denominator))
                add(4, unsigned, 0, isqrt(unsigned))
                add(5, a, index, rhaz(a, index))
            for a in (0, 1, (1 << 128) - 1, 1 << 127, 1 << 64):
                add(4, a, 0, isqrt(a))
                for denominator in (1, 2, 3, (1 << 64) - 1):
                    add(2, a, denominator, a // denominator)
            for a in (0, 1, -1, -(1 << 127), (1 << 127) - 1):
                for bits in (0, 1, 31, 32, 63, 64, 126, 127):
                    add(5, a, bits, rhaz(a, bits))
            for bits, op in ((32, 6), (64, 1)):
                for a in (-(1 << (bits - 1)), (1 << (bits - 1)) - 1, -1, 0, 1):
                    for b in (-(1 << (bits - 1)), (1 << (bits - 1)) - 1, -1, 0, 1):
                        add(op, a, b, a * b)
        for op in (2, 3):
            for denominator in (0, -1, 1 << 64):
                add(op, 1, denominator, 0, error=1)
        for distance in (-1, 128, 256):
            add(5, 1, distance, 0, error=1)
        add(15, 0, 0, 0, error=1)
        for op in range(8):
            add(op, -123456789, 41, 0, annul=1)
    else:
        cases = {-(1 << 127), (1 << 127) - 1, -1048577, -1048576, -1048575,
                 -1, 0, 1, 1048576}
        for power in range(24):
            boundary = power * 11629080 // 256
            cases.update(-boundary + offset for offset in (-1, 0, 1))
        for seed in coverage["seeds"]:
            rng = random.Random(seed)
            cases.update(rng.randint(-1100000, 10000) for _ in range(128))
        for value in sorted(cases):
            add(0, value, 0, exp_q24(value))
        for value in (-1048576, -65536, -1):
            add(0, value, 0, 0, annul=1)
    path.write_text("".join(rows))
    coverage["vectors"] = len(rows)
    return coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--unit", choices=("convert", "integer", "exp"), required=True)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    names = ["rtl/anvil_q2_ht_00_fp_pkg.sv", "rtl/anvil_q2_ht_01_int_pkg.sv",
             "rtl/anvil_q2_ht_convert.sv", "rtl/anvil_q2_ht_integer_math.sv",
             "rtl/anvil_q2_ht_exp.sv", "tests/numerical_tb.sv",
             "tests/numerical_check.py", "tests/reference.py", "tests/retention.py"]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        for tool, flag in (("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V")):
            experiment.run([tool, flag], tool + "-version")
        coverage = vectors(experiment.directory / "vectors.txt", args.unit)
        experiment.receipt["vectors"] = coverage
        unit = ("convert", "integer", "exp").index(args.unit)
        binary = str(args.output / "numerical.vvp")
        experiment.run(["iverilog", "-g2012", "-Wall", "-s", "numerical_tb",
                        f"-Pnumerical_tb.UNIT={unit}", "-o", binary]
                       + [str(args.output / "sources" / name) for name in names[:6]], "compile")
        text = experiment.run(["vvp", binary, "+vectors=" + str(args.output / "vectors.txt")],
                              "simulate", timeout=14400)
        expected = coverage["vectors"] - coverage["annulled"]
        if f"NUMERICAL_CHECKED vectors={coverage['vectors']} compared={expected} " not in text:
            raise RuntimeError("missing executed scalar comparisons")
        experiment.receipt["comparison_summary"] = text.strip()
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
