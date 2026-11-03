"""Independent libm/exact-rational references and public primitive latency checks."""

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, clean_objects, execute, hashes, relative, remaining, timestamp
from reference import decode, encode, float_bits, float_value


SPECIAL = (0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x807fffff,
           0x00800000, 0x80800000, 0x3f800000, 0xbf800000, 0x7f7fffff,
           0xff7fffff, 0x7f800000, 0xff800000, 0x7fc00000, 0x7f800001)


def vectors(seed, compact):
    rng = random.Random(seed)
    n = 32 if compact else 4096
    for a in SPECIAL:
        yield 0, a, 0
        yield 1, a, 0
    for value in (-104, -103.97208, -103, -100, -90, -87.33655, -80, -20,
                  -1, -0.5, 0.5, 1, 20, 80, 88, 88.72284, 89):
        bits = float_bits(value)
        for a in (bits - 1, bits, bits + 1):
            yield 0, a, 0
    for position in (0, 1, 32767):
        for pair in range(32):
            yield 1, float_bits(position * 1e6 ** (-2 * pair / 64)), 0
    for value in (-32768, 32768, -32769, 32769, -math.pi, math.pi, math.pi/2):
        yield 1, float_bits(value), 0
    for _ in range(n):
        yield 0, float_bits(rng.uniform(-105, 89)), 0
        yield 1, float_bits(rng.uniform(-32768, 32768)), 0
    pairs = [(a, b) for a in SPECIAL for b in SPECIAL]
    for _ in range(n):
        a, b = rng.getrandbits(32), rng.getrandbits(32)
        while decode(a)[0] != "finite":
            a = rng.getrandbits(32)
        while decode(b)[0] != "finite":
            b = rng.getrandbits(32)
        pairs.append((a, b))
    for a, b in pairs:
        yield 2, a, b
    for a in [*SPECIAL, *[rng.randrange(0x7f800000) for _ in range(n)]]:
        yield 3, a, 0


def division(a, b):
    ca, sa, va = decode(a)
    cb, sb, vb = decode(b)
    sign = (sa ^ sb) << 31
    if ca == "nan" or cb == "nan" or ca == cb == "inf" or (
            ca == cb == "finite" and va == vb == 0):
        return 0x7fc00000
    if ca == "inf" or cb == "finite" and vb == 0:
        return sign | 0x7f800000
    if cb == "inf" or ca == "finite" and va == 0:
        return sign
    return encode(va / vb, zero_sign=sa ^ sb)


def square_root(a):
    kind, sign, value = decode(a)
    if kind == "nan" or sign and (kind == "inf" or value != 0):
        return 0x7fc00000
    if kind == "inf" or value == 0:
        return a
    return encode(Fraction(math.sqrt(float(value))))


def check(op, a, b, data, auxiliary, error):
    x = float_value(a)
    if op in (2, 3):
        expected = division(a, b) if op == 2 else square_root(a)
        kind, sign, value = decode(expected)
        if error or auxiliary:
            raise AssertionError("unexpected div/sqrt auxiliary/error")
        if kind != "finite" or value == 0:
            if data != expected:
                raise AssertionError(f"IEEE special/zero expected={expected:08x} actual={data:08x}")
            return dict(category=kind if value is None else "zero", ulp=0)
        actual_kind, actual_sign, _ = decode(data)
        ulp = abs((data & 0x7fffffff) - (expected & 0x7fffffff))
        if actual_kind != "finite" or actual_sign != sign or ulp > 2:
            raise AssertionError(f"div/sqrt expected={expected:08x} actual={data:08x} ULP={ulp}")
        return dict(category="subnormal" if expected & 0x7f800000 == 0 else "ordinary",
                    ulp=ulp)
    if op == 1:
        invalid = not math.isfinite(x) or abs(x) > 32768
        if invalid:
            if (data, auxiliary, error) != (0x7fc00000, 0x7fc00000, 1):
                raise AssertionError("trig invalid-domain/nonfinite result")
            return dict(category="invalid", max_abs_error=0)
        if error:
            raise AssertionError("trig errored on supported finite angle")
        if x == 0 and (data != a or auxiliary != 0x3f800000):
            raise AssertionError("trig signed-zero rules")
        actual = (float_value(data), float_value(auxiliary))
        expected = (math.sin(x), math.cos(x))
        discrepancy = max(abs(y-z) for y, z in zip(actual, expected))
        if not all(math.isfinite(y) for y in actual) or discrepancy > 2e-5:
            raise AssertionError(f"trig abs_error={discrepancy}")
        return dict(category="subnormal" if a & 0x7fffffff < 0x00800000 and x else "ordinary",
                    max_abs_error=discrepancy)
    if error or auxiliary:
        raise AssertionError("unexpected exp auxiliary/error")
    if math.isnan(x) or x == math.inf or x == -math.inf:
        expected = 0x7fc00000 if math.isnan(x) else (0x7f800000 if x > 0 else 0)
        if data != expected:
            raise AssertionError(f"exp IEEE expected={expected:08x} actual={data:08x}")
        return dict(category="special", max_relative_error=0)
    if x > 89:
        expected = 0x7f800000
    elif x < -105:
        expected = 0
    else:
        expected = encode(Fraction(math.exp(x)))
    if expected in (0, 0x7f800000):
        if data != expected:
            raise AssertionError(f"exp under/overflow expected={expected:08x} actual={data:08x}")
        return dict(category="underflow" if expected == 0 else "overflow",
                    max_relative_error=0)
    exact = math.exp(x)
    actual = float_value(data)
    discrepancy = abs(actual-exact)
    near_underflow = exact < 1e-7
    bound = 1e-7 if near_underflow else 2e-5 * exact
    if not math.isfinite(actual) or actual < 0 or discrepancy > bound:
        raise AssertionError(f"exp abs_error={discrepancy} limit={bound}")
    return dict(category="subnormal" if expected & 0x7f800000 == 0 else "ordinary",
                **({"underflow_absolute_error": discrepancy} if near_underflow else
                   {"ordinary_relative_error": discrepancy/exact}))


def run(output, simulator, seed):
    compact = simulator == "icarus"
    cases = list(vectors(seed, compact))
    vectors_path = output / "vectors.txt"
    observations = output / "observations.txt"
    with vectors_path.open("x") as out:
        for op, a, b in cases:
            out.write(f"{op} {a:08x} {b:08x}\n")
    sources = [f"rtl/anvil_q1_ht3_{name}.sv" for name in
               ("00_fp_pkg", "reset_sync", "fp32_exp", "fp32_sincos", "fp32_divsqrt")]
    sources += ["tests/transcendental_tb.sv"]
    if compact:
        binary = output / "simulation.vvp"
        execute(["iverilog", "-g2012", "-Wall", "-s", "transcendental_tb",
                 "-o", relative(binary), *sources], output, "compile", ["iverilog", "-V"])
        argv = ["vvp", relative(binary)]
        version = ["iverilog", "-V"]
    else:
        objects = output / "compile-obj"
        execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                 "--top-module", "transcendental_tb", "--Mdir", relative(objects),
                 *sources], output, "compile", ["verilator", "--version"])
        argv = [relative(objects / "Vtranscendental_tb")]
        version = ["verilator", "--version"]
    failures = []
    try:
        text = execute([*argv, f"+vectors={relative(vectors_path)}",
                        f"+observations={relative(observations)}", f"+seed={seed}"],
                       output, "simulation", version)
    except RuntimeError as exc:
        failures.append(dict(kind="tool_or_protocol", message=str(exc)))
        text = (output / "simulation.stdout.txt").read_text()
    finally:
        if not compact:
            clean_objects(objects)
    summary = re.search(r"SUMMARY transcendental comparisons=(\d+) stalls=(\d+) "
                        r"holds=(\d+) bubbles=(\d+) reset_canceled=3", text)
    counts = Counter()
    maximum = {}
    observed = 0
    if observations.is_file():
        for line in observations.read_text().splitlines():
            row = line.split()
            if len(row) != 5 or int(row[0]) != observed or observed >= len(cases):
                raise AssertionError("missing/duplicate/malformed primitive observation")
            op, a, b = cases[observed]
            if int(row[1]) != op:
                raise AssertionError("primitive operation association")
            data, auxiliary, error = int(row[2], 16), int(row[3], 16), int(row[4])
            try:
                comparison = check(op, a, b, data, auxiliary, error)
                counts[f"{op}:{comparison['category']}"] += 1
                for key, value in comparison.items():
                    if key != "category":
                        maximum[f"{op}:{key}"] = max(maximum.get(f"{op}:{key}", 0), value)
            except AssertionError as exc:
                failures.append(dict(kind="numerical", index=observed, op=op,
                                     a=f"{a:08x}", b=f"{b:08x}", actual=f"{data:08x}",
                                     auxiliary=f"{auxiliary:08x}", error=error, message=str(exc)))
            observed += 1
    if (not summary or int(summary[1]) != len(cases)
            or observed != len(cases) or min(map(int, summary.groups()[1:])) <= 0):
        failures.append(dict(kind="coverage", message="incomplete primitive observations",
                             observed=observed, required=len(cases), raw_tail=text[-2000:]))
    result = dict(status="failed" if failures else "passed", simulator=simulator,
                  seed=seed, compared=observed, required=len(cases), categories=dict(counts),
                  maxima=maximum, failures=failures, raw_summary=summary[0] if summary else None,
                  vector_sha256=hashlib.sha256(vectors_path.read_bytes()).hexdigest(),
                  interpreted_cycle_bound=len(cases)*150+100 if compact else None)
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--simulator", choices=("icarus", "verilator"))
    parser.add_argument("--seed", type=int, choices=(17, 89, 2026), default=17)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_transcendental.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    jobs = ([(args.simulator, args.seed)] if args.simulator else
            [("icarus", 17), *[("verilator", seed) for seed in (17, 89, 2026)]])
    rows = []
    for simulator, seed in jobs:
        directory = output / f"{simulator}-seed{seed}-{uuid.uuid4().hex[:12]}"
        directory.mkdir()
        try:
            child = run(directory, simulator, seed)
            rows.append(dict(simulator=simulator, seed=seed, status=child["status"],
                             result=relative(directory / "result.json")))
        except (RuntimeError, AssertionError) as exc:
            rows.append(dict(simulator=simulator, seed=seed, status="failed",
                             error=str(exc), path=relative(directory)))
    result = dict(status="passed" if all(row["status"] == "passed" for row in rows) else "failed",
                  runs=rows, thresholds=dict(exp_relative=2e-5, exp_underflow_absolute=1e-7,
                                            sincos_absolute=2e-5, divsqrt_ulp=2))
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=any(json.loads(p.read_text()).get("timed_out", False)
                                 for p in output.rglob("*.receipt.json")),
                   result=relative(output / "result.json"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
