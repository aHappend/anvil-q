"""Bound every small-integer FP32 output direction for retained subnormal RoPE.

For inputs of magnitude u=2**-149, a separately RNE-rounded product
with a sine/cosine satisfying the admitted absolute error is in {-u,0,u}.
The following RNE add/subtract is therefore in {-2u,-u,0,u,2u}.
This diagnostic optimizes over that entire Cartesian superset, not merely
over the DUT output or the final-rounded mathematical answer.
"""

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import decode
from run_epilogue import cases, expected
from run_unit import ROOT, hashes, relative


def fraction_text(value):
    return f"{value.numerator}/{value.denominator}"


def maximum_squared_cosine(reference, bound):
    """Exact optimization over all integer vectors with |coordinate| <= bound.

    For r.k >= 0, (r.k)**2/(k.k) = max(t>=0) 2*t*r.k-t*t*k.k.
    At fixed t>0, each maximizing integer k_i is nearest to r_i/t,
    with saturation. Enumerate intervals separated by all rounding ties.
    At a tie, tied vectors have the same quadratic value; an optimum at
    a tie is also attained by an adjacent interval's vector.
    """
    if bound < 1 or not reference or not any(reference):
        raise ValueError("nonzero reference and positive bound required")
    magnitudes = [abs(x) for x in reference]
    norm = sum(x*x for x in magnitudes)
    boundaries = sorted({2*x / (2*j+1)
                         for x in magnitudes if x
                         for j in range(bound)})
    samples = [boundaries[0] / 2]
    samples.extend((a+b)/2 for a, b in zip(boundaries, boundaries[1:]))
    samples.append(boundaries[-1]*2)
    best, best_vector, candidates = Fraction(0), None, set()
    for t in samples:
        vector = tuple(min(bound, (x/t + Fraction(1, 2)).numerator //
                           (x/t + Fraction(1, 2)).denominator)
                       for x in magnitudes)
        if vector in candidates or not any(vector):
            continue
        candidates.add(vector)
        dot = sum(x*k for x, k in zip(magnitudes, vector))
        squared = dot*dot / (norm * sum(k*k for k in vector))
        if squared > best:
            best = squared
            best_vector = [k if x >= 0 else -k
                           for x, k in zip(reference, vector)]
    return best, best_vector, len(candidates)


def check_optimizer():
    from itertools import product

    count = 0
    for reference in ([1, 2], [1, -3, 2], [0, 1, 1], [3, 7, -2]):
        r = [Fraction(x) for x in reference]
        for bound in (1, 2, 3):
            actual, _, _ = maximum_squared_cosine(r, bound)
            norm = sum(x*x for x in r)
            brute = max(
                sum(x*k for x, k in zip(r, vector))**2 /
                (norm * sum(k*k for k in vector))
                for vector in product(range(-bound, bound+1), repeat=len(r))
                if any(vector))
            if actual != brute:
                raise AssertionError("lattice optimizer differs from exhaustive search")
            count += 1
    return count


def diagnose(ledger):
    fixtures = cases(ledger["seed"])
    unit = Fraction(1, 1 << 149)
    threshold = Fraction(9999, 10000)
    rows = []
    for failure in ledger["failures"]:
        c = fixtures[failure["command"]]
        if c["op"] != 2:
            continue
        slot = failure["slot"]
        if any(abs(decode(x)[2]) != unit for x in c["x"][slot]):
            raise AssertionError("RoPE lattice premise requires +/- minimum subnormal")
        ref = expected(c, slot)
        if ref != failure["reference"]:
            raise AssertionError("retained reference differs from regenerated FP64 formula")
        represented = [Fraction.from_float(x) / unit for x in ref]
        squared, vector, count = maximum_squared_cosine(represented, 2)
        if squared >= threshold*threshold:
            raise AssertionError("output lattice does not exclude a passing alternative")
        rows.append(dict(
            command=failure["command"], slot=slot, fp16=c["fp16"],
            position=c["positions"][slot], dimension=len(ref),
            input_bits=[f"{x:08x}" for x in c["x"][slot]],
            reference_in_subnormal_units=[fraction_text(x) for x in represented],
            output_coordinate_superset=[-2, -1, 0, 1, 2],
            optimum_integer_vector=vector,
            exact_maximum_cosine_squared=fraction_text(squared),
            exact_required_cosine_squared=fraction_text(threshold*threshold),
            maximum_cosine=math.sqrt(float(squared)), required_cosine=float(threshold),
            candidate_directions=count,
            scope="separately RNE FP32 RoPE products/adds satisfying trig bounds",
            conclusion="no output in this superset meets the retained FP64 cosine"))
    if not rows:
        raise AssertionError("missing applicable retained RoPE failures")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = ROOT / args.input
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(
        kind="independent-rope-output-lattice-diagnosis",
        argv=["python3", "tests/diagnose_output_lattice.py", *sys.argv[1:]],
        cwd=".", start=datetime.now(timezone.utc).isoformat(), timeout=None,
        source_sha256=hashes(), tool_version=sys.version,
        input_sha256={args.input: hashlib.sha256(source.read_bytes()).hexdigest()},
        diagnostic_of=args.input,
        stdout=relative(output / "stdout.txt"),
        stderr=relative(output / "stderr.txt"))
    try:
        self_checks = check_optimizer()
        rows = diagnose(json.loads(source.read_text()))
        result = dict(kind="analytical diagnosis, not RTL acceptance",
                      exhaustive_optimizer_self_checks=self_checks, rows=rows)
        with (output / "diagnosis.json").open("x") as out:
            json.dump(result, out, indent=2)
            out.write("\n")
        summary = json.dumps(dict(
            exhaustive_optimizer_self_checks=self_checks,
            retained_vectors=len(rows),
            maximum_cosines=[row["maximum_cosine"] for row in rows],
            required_cosine=0.9999)) + "\n"
        (output / "stdout.txt").write_text(summary)
        (output / "stderr.txt").write_text("")
        print(summary, end="", flush=True)
        receipt["exit"] = 0
    except Exception as exc:
        (output / "stdout.txt").write_text("")
        (output / "stderr.txt").write_text(f"{type(exc).__name__}: {exc}\n")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        receipt["exit"] = 1
    receipt["end"] = datetime.now(timezone.utc).isoformat()
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
        out.write("\n")
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
