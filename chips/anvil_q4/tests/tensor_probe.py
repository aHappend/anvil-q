"""Exact FP32 tensor reductions, A8 scales and inactive-lane comparisons."""

import argparse
from fractions import Fraction
import hashlib
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment
from ieee_reference import decode, evaluate, nearest_integer, rounded


OFFSETS = (0, 16, 4, 20, 8, 24, 12, 28)


def vectors(lanes):
    rng = random.Random(170029 + lanes)
    for fmt in (0, 1, 2):
        for a8 in (False, True) if fmt else (False,):
            for afmt in (0, 1):
                for asymmetric in (False, True):
                    for length in (1, 3, 7):
                        mask = (1 << lanes)-1
                        if length == 3 and lanes > 1:
                            mask ^= 1 << (lanes//2)
                        activation = [rounded(Fraction(rng.randrange(-127, 128), 16))[0]
                                      for _ in range(length)]
                        accumulators = [rounded(Fraction(rng.randrange(-31, 32), 16))[0]
                                        for _ in range(lanes)]
                        if fmt == 0 and not asymmetric and length == 3:
                            activation = [0x43800000, 0x3f800000, 0xc3800000]
                            accumulators = [0]*lanes
                        expected = accumulators.copy()
                        flags = 0
                        actual = activation.copy()
                        if a8:
                            maximum = max(x & 0x7fffffff for x in activation)
                            scale, f = evaluate(3, maximum, 0x42fe0000) if maximum else (
                                0x3f800000, 0)
                            flags |= f
                            actual = []
                            for value in activation:
                                q, f = evaluate(3, value, scale)
                                flags |= f
                                q = min(127, max(-127, nearest_integer(decode(q)[2])))
                                value, f = evaluate(9, q & 0xffffffff)
                                flags |= f
                                value, f = evaluate(2, value, scale)
                                flags |= f
                                value, f = evaluate(7, value)
                                flags |= f
                                value, f = evaluate(5, value)
                                flags |= f
                                actual.append(value)
                        weights = []
                        for k in range(length):
                            row = []
                            for lane in range(lanes):
                                if not mask >> lane & 1:
                                    row.append((0xffffffff, 0xffffffff, 0x7fc00000, 7))
                                    continue
                                if not fmt:
                                    weight = (0x3c00 if afmt else 0x3f80) if (
                                        not asymmetric and length == 3) else evaluate(
                                            8 if afmt else 7,
                                            rounded(Fraction(rng.randrange(-15, 16), 8))[0])[0]
                                    payload, zero, scale, selector = weight, 0, 0, 0
                                    widened, f = evaluate(6 if afmt else 5, weight)
                                    flags |= f
                                else:
                                    width = 4 if fmt == 1 else 8
                                    selector = (k+lane) % (8 if fmt == 1 else 4)
                                    shift = OFFSETS[selector] if fmt == 1 else selector*8
                                    q = rng.randrange(1 << width)
                                    zero = rng.randrange(1 << width) if asymmetric else 0
                                    payload = q << shift
                                    scale = (0x3c800000, 0x3eaaaaab)[(k+lane) % 2]
                                    integer = q if asymmetric or q < 1 << (width-1) else q-(1 << width)
                                    widened, f = evaluate(9, (integer-zero) & 0xffffffff)
                                    flags |= f
                                    widened, f = evaluate(2, widened, scale)
                                    flags |= f
                                    widened, f = evaluate(7, widened)
                                    flags |= f
                                    widened, f = evaluate(5, widened)
                                    flags |= f
                                row.append((payload, zero, scale, selector))
                                product, f = evaluate(2, actual[k], widened)
                                flags |= f
                                expected[lane], f = evaluate(0, expected[lane], product)
                                flags |= f
                            weights.append(row)
                        yield (length, mask, a8, afmt, asymmetric, fmt,
                               accumulators, activation, weights, expected, flags)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--lanes", type=int, choices=(1, 2, 4, 8, 16), default=16)
    args = parser.parse_args()
    experiment = Experiment("tensor", args.preparation)
    error = None
    objects = experiment.directory / "compile-obj"
    try:
        fixture = experiment.directory / "vectors.txt"
        count = 0
        with fixture.open("w") as stream:
            for length, mask, a8, afmt, asym, fmt, acc, act, weights, expected, flags in vectors(args.lanes):
                stream.write(f"{length} {mask:x} {int(a8)} {afmt} {int(asym)} {fmt}\n")
                words = acc + act + [word for row in weights for lane in row for word in lane]
                words += expected + [flags]
                stream.write(" ".join(f"{word:08x}" for word in words)+"\n")
                count += 1
        experiment.receipt["fixture_sha256"] = hashlib.sha256(fixture.read_bytes()).hexdigest()
        experiment.receipt["tool_version"] = experiment.run(["verilator", "--version"], "version")
        experiment.run([
            "verilator", "--binary", "--timing", "-Wno-fatal",
            "--top-module", "tensor_tb", "--Mdir", experiment.rel(objects),
            f"-GLANES={args.lanes}", "-o", "tensor-sim",
            *("rtl/"+name+".sv" for name in (
                "anvil_q4_00_fp_pkg", "anvil_q4_fp32", "anvil_q4_dequant",
                "anvil_q4_activation_quantizer", "anvil_q4_tensor_array")),
            "tests/tensor_tb.sv"], "compile")
        output = experiment.run([experiment.rel(objects/"tensor-sim"),
                                 "+VECTORS="+experiment.rel(fixture)], "simulation")
        if f"SUMMARY tensor comparisons={count} lanes={args.lanes} " not in output:
            raise AssertionError("missing exact tensor comparisons")
        experiment.receipt["comparisons"] = {"cases": count, "lanes": args.lanes,
                                            "comparison": "exact FP32 bits and flags"}
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
