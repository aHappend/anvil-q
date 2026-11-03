#!/usr/bin/env python3
"""Public-pin mixed-dot/binary regression for the shared three-stage reducer.

The existing rational dot oracle and thresholds are unchanged. Expectations here
use decoded exact rational terms and the specified common grid, never DUT helpers.
L1 runs exhaustive/wide randomized cases on Verilator plus compact Icarus smoke.
"""

from collections import Counter
from fractions import Fraction
import argparse
import json
from pathlib import Path
import random
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from numerical import (binary32, decode, dot_reference, dot_vectors, floor_log2,
                       power_two)


def grid_reference(products, additions):
    terms, zero_signs, infinities = [], [], set()
    nan, invalid = False, False
    for operands in products:
        sign = operands[0][0] ^ operands[1][0]
        kinds = [operand[1] for operand in operands]
        invalid |= any(operand[2] for operand in operands)
        nan |= "nan" in kinds
        bad_product = "inf" in kinds and any(
            operand[1] == "finite" and operand[3] == 0 for operand in operands)
        invalid |= bad_product
        if "nan" in kinds or bad_product:
            continue
        if "inf" in kinds:
            infinities.add(sign)
        else:
            value = operands[0][3] * operands[1][3]
            terms.append(value)
            zero_signs.append(sign if value == 0 else None)
    for sign, kind, signaling, value in additions:
        nan |= kind == "nan"
        invalid |= signaling
        if kind == "inf":
            infinities.add(sign)
        elif kind == "finite":
            terms.append(value)
            zero_signs.append(sign if value == 0 else None)
    invalid |= len(infinities) > 1
    if invalid or nan:
        return 0x7fc00000, 16 if invalid else 0
    if infinities:
        return (next(iter(infinities)) << 31) | 0x7f800000, 0
    nonzero = [abs(term) for term in terms if term]
    if not nonzero:
        return binary32(Fraction(), negative_zero=all(sign == 1 for sign in zero_signs))
    step = power_two(floor_log2(max(nonzero)) - 63)
    quantized = [int(abs(term) / step) * (-1 if term < 0 else 1) for term in terms]
    aligned = sum(quantized) * step
    assert abs(sum(terms, Fraction()) - aligned) < len(terms) * step
    return binary32(aligned, alignment_lost=any(
        term != integer * step for term, integer in zip(terms, quantized)))


def mixed_reference(precision, a, b, mask, seed):
    if precision not in (1, 2):
        return 0x7fc00000, 16
    eb, fb = (8, 7) if precision == 1 else (5, 10)
    products = [(decode((a >> (32*lane)) & 0xffffffff, 8, 23),
                 decode((b >> (16*lane)) & 0xffff, eb, fb))
                for lane in range(8) if mask & (1 << lane)]
    return grid_reference(products, [decode(seed, 8, 23)])


def binary_reference(a, b, multiply):
    operands = [decode(a, 8, 23), decode(b, 8, 23)]
    return grid_reference([operands] if multiply else [], [] if multiply else operands)


def widen(bits, precision):
    sign, kind, signaling, value = decode(bits, *((8, 7) if precision == 1 else (5, 10)))
    if kind == "inf":
        return (sign << 31) | 0x7f800000
    if kind == "nan":
        return (sign << 31) | (0x7f800001 if signaling else 0x7fc00000)
    return binary32(value, negative_zero=bool(sign and value == 0))[0]


def vectors(full, coverage):
    # Every unchanged dot vector is also checked with an exactly widened input.
    for vector in dot_vectors(full):
        precision, a, b, mask, seed = vector
        wide = sum(widen((a >> (16*lane)) & 0xffff, precision) << (32*lane)
                   for lane in range(8))
        observed = mixed_reference(precision, wide, b, mask, seed)
        assert observed == dot_reference(*vector)[:2]
        coverage["dot_oracle_crosschecks"] += 1
        yield precision, wide, b, mask, seed, seed, (wide & 0xffffffff), observed
    specials = [0, 0x80000000, 1, 0x80000001, 0x7fffff, 0x800000,
                0x807fffff, 0x80800000, 0x33800000, 0x3f800000, 0xbf800000,
                0x7f7fffff, 0xff7fffff, 0x7f800000, 0xff800000,
                0x7fc00000, 0x7f800001, 0xff800001]
    for a in specials:
        for b in specials:
            coverage["binary_special_pairs"] += 1
            yield 1, a, 0x3f80, 1, 0, a, b, None
    for precision, one in ((1, 0x3f80), (2, 0x3c00)):
        # Carry chains, exact/near cancellation, all masks, alignment loss and
        # signed zeros with full binary32 (not pre-rounded sixteen-bit) inputs.
        for mask in range(256):
            for value in (0x3f800001, 0x7f7fffff, 0x800001, 1):
                a = sum((value ^ (0x80000000 if lane & 1 else 0)) << (32*lane)
                        for lane in range(8))
                b = sum(one << (16*lane) for lane in range(8))
                coverage[f"mixed_masks_precision{precision}"] += 1
                yield precision, a, b, mask, 0x80000001, value, value ^ 0x80000000, None
        for exponent in range(255):
            for offset in (-1, 0, 1):
                a = max(0, (exponent << 23) + offset)
                coverage[f"binary_exponent_boundaries_precision{precision}"] += 1
                yield precision, a, one, 1, 1, a, 0x3f800000, None
        rng = random.Random(89 + precision)
        for _ in range(100000 if full else 128):
            a, b, seed = rng.getrandbits(256), rng.getrandbits(128), rng.getrandbits(32)
            coverage[f"mixed_random_precision{precision}"] += 1
            coverage["binary_random"] += 1
            yield precision, a, b, rng.randrange(256), seed, (
                rng.getrandbits(32)), rng.getrandbits(32), None


def check(root, ev, full=True, simulator=None):
    import verify
    coverage = Counter()
    path = ev.path / "reducer-input.txt"
    expected_comparisons, rows, history = 0, 0, 0
    started = last_progress = time.monotonic()
    with path.open("x") as stream:
        def emit(reset, valid, precision=1, a=0, b=0, mask=0, seed=0,
                 x=0, y=0, expected=None):
            nonlocal rows, history, expected_comparisons
            expected = expected or mixed_reference(precision, a, b, mask, seed)
            ar, ast = binary_reference(x, y, False)
            pr, ps = binary_reference(x, y, True)
            stream.write(f"{reset} {valid} {precision} {a:064x} {b:032x} {mask:02x} "
                         f"{seed:08x} {x:08x} {y:08x} {expected[0]:08x} {expected[1]:02x} "
                         f"{ar:08x} {ast:02x} {pr:08x} {ps:02x}\n")
            history = ((history << 1) | valid) & 7 if reset else 0
            expected_comparisons += bool(history & 4)
            rows += 1

        emit(0, 0)
        for phase in (1, 2, 3):
            for _ in range(phase):
                emit(1, 1, a=0x3f800001, b=0x3f80, mask=1)
            emit(0, 0)
            for _ in range(3):
                emit(1, 0)
        for index, vector in enumerate(vectors(full, coverage)):
            emit(1, 1, *vector)
            if index % 31 == 0:
                emit(1, 0)
            if index % 4096 == 0 and time.monotonic() - last_progress >= 30:
                print(json.dumps({"role": "verifier", "execution": "reducer-reference",
                                  "phase": "stimulus", "vectors": index + 1,
                                  "elapsed_s": time.monotonic() - started}), flush=True)
                last_progress = time.monotonic()
        for _ in range(3):
            emit(1, 0)
    ev.receipt["coverage"] = dict(coverage)
    ev.elapsed("reducer-independent-reference-generation", started)
    ev.receipt["data_sha256"] = {str(path.relative_to(root)): verify.digest(path)}
    ev.assertion("independent_grid_reference_coverage", (
        coverage["dot_oracle_crosschecks"] > 0 and
        all(coverage[f"mixed_masks_precision{p}"] == 1024 for p in (1, 2)) and
        all(coverage[f"mixed_random_precision{p}"] == (100000 if full else 128)
            for p in (1, 2))), full_vectors=full, coverage=dict(coverage))
    simulator = verify.simulation_tier(
        simulator or ("verilator" if full else "iverilog"), full=full, cycles=rows)
    compiled = simulator == "verilator"
    executable = ev.path / ("reducer.sim" if compiled else "reducer.vvp")
    argv = (["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
             "--top-module", "reducer_tb", "--Mdir",
             str((ev.path / "reducer-build").relative_to(root)),
             "-o", str(executable.resolve())] if compiled else
            ["iverilog", "-g2012", "-Wall", "-DICARUS_SMOKE", "-s", "reducer_tb",
             "-o", str(executable.relative_to(root))])
    if not verify.compile_simulation(ev, "reducer-compile", [
            *argv, *[str(p.relative_to(root)) for p in sorted((root / "rtl").glob("*.sv"))],
            "tests/reducer_tb.sv"], executable):
        return ev.assertion("reducer_compile", False)
    passed = ev.run("reducer-simulate", [
        *([str(executable)] if compiled else ["vvp", str(executable.relative_to(root))]),
        "+input=" + str(path.relative_to(root))], timeout=86400)
    stdout = (ev.path / "reducer-simulate.stdout").read_text()
    match = re.search(r"REDUCER_SUMMARY cycles=(\d+) comparisons=(\d+) "
                      r"consecutive=(\d+) resets=(\d+)", stdout)
    passed = ev.assertion(
        "reducer_public_pin_numerical_latency_reset", passed and match is not None and
        list(map(int, match.groups()[:2])) == [rows, expected_comparisons] and
        int(match[3]) > 0 and int(match[4]) == 3,
        simulator=simulator, stimulus_cycles=rows,
        expected_comparisons_per_operator=expected_comparisons,
        summary=match.group(0) if match else None) and passed
    if not compiled:
        passed = ev.assertion("reducer_icarus_measured_budget",
                              ev.receipt["records"][-1]["elapsed_s"] < 60,
                              wall_clock_allowance_s=86400,
                              elapsed_s=ev.receipt["records"][-1]["elapsed_s"]) and passed
    return passed


def main():
    import verify
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--simulator", choices=("iverilog", "verilator"))
    parser.add_argument("--repair-of", type=Path)
    args = parser.parse_args()
    ev = verify.Evidence("reducer-smoke" if args.smoke else "reducer-full")
    good = False
    try:
        if args.repair_of:
            ev.receipt["repair_of"] = {
                "path": str(args.repair_of),
                "sha256": verify.digest(verify.ROOT / args.repair_of)}
        good = ev.versions() and check(
            verify.ROOT, ev, full=not args.smoke, simulator=args.simulator)
        good = good and verify.audit_evidence(ev)
    except Exception as error:
        ev.assertion("reducer_exception", False, diagnostics=verify.exception_diagnostic(
            error, "execution", ev.path))
    finally:
        good = good and all(row["passed"] for row in ev.receipt["assertions"])
        ev.finish("passed" if good else "failed")
        verify.report_failures(ev)
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(verify.ROOT))}))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
