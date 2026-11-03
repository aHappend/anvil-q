"""Public-pin numerical tests. Full sweeps use compiled Verilator."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative, source_hashes
from ieee import convert, decode, exp_frozen, exp_high_precision, operation, pack


DIRECTED = (0, 0x80000000, 1, 2, 0x007fffff, 0x00800000, 0x00800001,
            0x3f000000, 0x3f800000, 0x3f800001, 0x3fffffff, 0x40000000,
            0x40400000, 0xbf800000, 0x7f7fffff, 0xff7fffff, 0x7f800000,
            0xff800000, 0x7fc00000, 0x7f800001, 0xff800001, 0x33800000,
            0x33000000, 0x3f7fffff, 0x80800000)


def cases(compact=False):
    for op in range(16):
        for a in DIRECTED:
            for b in DIRECTED if op < 4 else (0,):
                yield op, a, b
    for seed in (17, 89, 2026):
        rng = random.Random(seed)
        for op in range(10):
            for _ in range(32 if compact else 4096):
                yield op, rng.getrandbits(32), rng.getrandbits(32)
    for op in (5, 6):
        for a in range(0, 65536, 257 if compact else 1):
            yield op, a, 0
    # Every adjacent nonnegative finite pair: exact midpoint and its
    # immediate FP32 neighbors, mirrored to the negative half-space.
    for fmt, op, maximum in (("bf16", 7, 0x7f7f), ("fp16", 8, 0x7bff)):
        for lower in range(0, maximum, 257 if compact else 1):
            midpoint = (decode(lower, fmt)[2] + decode(lower + 1, fmt)[2]) / 2
            center, flags = pack(midpoint)
            if flags:
                raise AssertionError("native midpoint not representable in FP32")
            for bits in (center - 1, center, center + 1):
                for sign in (0, 1 << 31):
                    yield op, bits | sign, 0
        # Include the finite-to-infinity rounding threshold.
        last = decode(maximum, fmt)[2]
        previous = decode(maximum - 1, fmt)[2]
        threshold, _ = pack(last + (last - previous) / 2)
        for bits in (threshold - 1, threshold, threshold + 1):
            for sign in (0, 1 << 31):
                yield op, bits | sign, 0


def vectors(path, compact=False):
    counts = {}
    with path.open("w") as stream:
        for op, a, b in cases(compact):
            result, flags = operation(op, a, b)
            stream.write(f"{op:x} {a:08x} {b:08x} {result:08x} {flags:02x}\n")
            counts[str(op)] = counts.get(str(op), 0) + 1
    return {"counts": counts, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def oracle_self_test():
    assert operation(0, 0x3f800000, 0x3f800000) == (0x40000000, 0)
    assert operation(1, 0x3f800000, 0x3f800000) == (0, 0)
    assert operation(3, 0x3f800000, 0x40400000) == (0x3eaaaaab, 1)
    assert operation(4, 0x40000000) == (0x3fb504f3, 1)
    assert operation(2, 1, 0x3f000000) == (0, 3)
    assert operation(0, 0x80000000, 0x80000000) == (0x80000000, 0)
    assert convert(0x0001, "fp16", "fp32") == (0x33800000, 0)
    assert pack(Fraction(1, 1 << 150)) == (0, 3)
    assert pack(Fraction((1 << 24) - 1, 1 << 150)) == (0x00800000, 1)


def exponential_vectors(path, compact=False):
    samples = list(DIRECTED)
    for boundary in (Fraction(-104), Fraction(89), Fraction(-100), Fraction(-87),
                     Fraction(88), Fraction(0), Fraction(1), Fraction(-1)):
        center = pack(boundary)[0]
        samples.extend(x for x in (center - 1, center, center + 1) if 0 <= x < 1 << 32)
    for seed in (17, 89, 2026):
        rng = random.Random(seed)
        for _ in range(32 if compact else 1400):
            samples.append(pack(Fraction(rng.randrange(-104000000, 89000001),
                                         1000000))[0])
    max_ulp = 0
    with path.open("w") as stream:
        for bits in samples:
            result, flags = exp_frozen(bits)
            if decode(bits)[1] == "finite" and result != 0x7f800000:
                reference = exp_high_precision(bits)
                distance = abs(result - reference)
                if distance > 1:
                    raise AssertionError(f"frozen exp error >1 ULP x={bits:08x} "
                                         f"frozen={result:08x} high={reference:08x}")
                max_ulp = max(max_ulp, distance)
            stream.write(f"{bits:08x} {result:08x} {flags:02x}\n")
    return {"count": len(samples), "max_frozen_high_precision_ulp": max_ulp,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def run(compact=False, preparation=False):
    oracle_self_test()
    directory = new_run("numerics-compact" if compact else "numerics", preparation)
    vector_path = directory / "fp32-vectors.txt"
    manifest = vectors(vector_path, compact)
    manifest["source_sha256"] = source_hashes()
    (directory / "vectors.json").write_text(json.dumps(manifest, indent=2) + "\n")
    inputs = ["rtl/anvil_q4_00_fp_pkg.sv", "rtl/anvil_q4_fp32.sv", "tests/fp32_tb.sv"]
    # Four-state startup and bounded leaf behavior, not an interpreted full sweep.
    vvp = relative(directory / "fp32.vvp")
    execute(directory / "icarus-compile",
            ["iverilog", "-g2012", "-Wall", "-s", "fp32_tb", "-o", vvp] + inputs)
    execute(directory / "icarus-smoke",
            ["vvp", vvp, f"+vectors={relative(vector_path)}", "+limit=128"])
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile",
                ["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                 "--top-module", "fp32_tb", "--Mdir", relative(obj)] + inputs)
        execute(directory / "verilator-numerics",
                [relative(obj / "Vfp32_tb"), f"+vectors={relative(vector_path)}"],
                timeout=1800)
    finally:
        # Retain sources/receipts/vectors, not transient objects or binaries.
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Numerical probe receipts: {relative(directory)}", flush=True)
    return directory


def run_exp(compact=False, preparation=False):
    directory = new_run("exp-compact" if compact else "exp", preparation)
    vector_path = directory / "exp-vectors.txt"
    manifest = exponential_vectors(vector_path, compact)
    manifest["source_sha256"] = source_hashes()
    (directory / "vectors.json").write_text(json.dumps(manifest, indent=2) + "\n")
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile",
                ["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                 "--top-module", "exp_tb", "--Mdir", relative(obj),
                 "rtl/anvil_q4_00_fp_pkg.sv", "rtl/anvil_q4_fp_umul64.sv",
                 "rtl/anvil_q4_fp_exp.sv", "tests/exp_tb.sv"])
        execute(directory / "verilator-exp",
                [relative(obj / "Vexp_tb"), f"+vectors={relative(vector_path)}"],
                timeout=1800)
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Exponential probe receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--exp", action="store_true")
    args = parser.parse_args()
    (run_exp if args.exp else run)(args.compact, args.preparation)
