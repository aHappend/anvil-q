#!/usr/bin/env python3
"""Project-relative retained verification entry point.

Unfinished gates are explicit failures, not skipped or accepted evidence.
The shared runtime remains responsible for engineering check execution.
Compact Icarus portability and complete compiled workloads are accounted
separately. execution-contract.json explicitly retains the discrepancy from
the originally admitted full Icarus matrix for independent review.
"""

import argparse
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder_checks import decoder_case
from execution import Run, write_json
from leaf_checks import codec_case, dot8_case
from parameters import A, A_PORTABILITY, behavioral_geometries
from prerequisites import prerequisites
from structure_checks import structure
from synthesis_checks import synthesis
from reproduce import reproduce
from compatibility_checks import compatibility
from scalar_checks import scalar_case
from mutation_checks import mutations
from benchmark_checks import benchmark
from hardware_checks import board_hil, quartus_sta
from scheduler_checks import scheduler_case
from prefetch_checks import prefetch_case
from boundary_checks import boundaries, integration_faults
from math_memory_checks import math_memory_case
from accumulator_checks import accumulator_case
from map_checks import memory_maps
from fpga_checks import host_case, bridge_case
from tensor_checks import activation_case


CHECKS = ("prerequisites", "structure", "behavior", "benchmark", "mutations", "synthesis",
          "quartus-sta", "board-hil", "reproduce")


def mandatory_a_coverage(records):
    """Verify requested A dispatch, not actual/original simulator coverage."""
    expected = Counter(
        (replace(A_PORTABILITY if simulator == "iverilog" else A,
                 BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym), seed,
         simulator, (0,) if simulator == "iverilog" else (1, 4, 2, 6, 3, 5, 7),
         1 if simulator == "iverilog" else 4)
        for banks in (1, 2, 4, 8)
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1))
        for seed in (17, 89, 257)
        for simulator in ("iverilog", "verilator"))
    observed = Counter(records)
    if observed != expected:
        missing, extra = expected - observed, observed - expected
        raise AssertionError(
            "mandatory A dual-simulator coverage incomplete: "
            f"{sum(missing.values())} missing, {sum(extra.values())} unexpected/duplicate "
            "workloads.")
    return {"required": sum(expected.values()), "observed": sum(observed.values())}


def mandatory_decoder_workloads():
    """Keep requested dispatch identical to the recorded preflight obligations."""
    for label, g in behavioral_geometries():
        for seed in ((17,) if label == "C" else (17, 89, 257)):
            simulators = ("iverilog", "verilator") if label == "A" else ("verilator",)
            for simulator in simulators:
                if simulator == "iverilog":
                    actual = replace(g, INTERMEDIATE_SIZE=8, VOCAB_SIZE=1)
                    tokens = (0,)
                    prefill = 1
                else:
                    actual = g
                    tokens = (1, 4, 2, 6) if label == "C" else (1, 4, 2, 6, 3, 5, 7)
                    prefill = 2 if label == "C" else 4
                yield label, actual, seed, simulator, tokens, prefill


def mandatory_decoder_coverage(records):
    expected = Counter(mandatory_decoder_workloads())
    observed = Counter(records)
    if observed != expected:
        missing, extra = expected - observed, observed - expected
        raise AssertionError(
            "mandatory decoder coverage incomplete: "
            f"{sum(missing.values())} missing, {sum(extra.values())} unexpected/duplicate "
            "workloads; each profile, geometry, seed, simulator, token and phase must match")
    return {"required": sum(expected.values()), "observed": sum(observed.values())}


def original_icarus_coverage(records):
    """Count completed numerical results, never requested dispatch or smoke labels."""
    required = {}
    for label, g in behavioral_geometries():
        for seed in ((17,) if label == "C" else (17, 89, 257)):
            tokens = (1, 4, 2, 6) if label == "C" else (1, 4, 2, 6, 3, 5, 7)
            prefill = 2 if label == "C" else 4
            key = (tuple(sorted(asdict(g).items())), seed, tokens, prefill)
            required[key] = {"profile": label, "geometry": asdict(g), "seed": seed,
                             "tokens": list(tokens), "prefill_tokens": prefill}
    observed = set()
    pending = list(records)
    while pending:
        result = pending.pop()
        if not isinstance(result, dict):
            continue
        tier = result.get("tier_dispatch", {})
        if tier:
            pending.append(tier["compact_smoke"])
        if result.get("simulator") != "iverilog" or "workload" not in result:
            continue
        workload = result["workload"]
        key = (tuple(sorted(result["geometry"].items())), workload["seed"],
               tuple(workload["tokens"]), workload["prefill_tokens"])
        if key not in required:
            continue
        if (result.get("bit_mismatches") != 0 or result.get("compared_bits", 0) <= 0 or
                result.get("tokens") != len(workload["tokens"])):
            raise AssertionError("original Icarus coverage has no complete numerical comparison")
        observed.add(key)
    missing = [row for key, row in required.items() if key not in observed]
    report = {"required": len(required), "observed": len(observed), "missing": missing,
              "status": "passed" if not missing else "unestablished",
              "scope": "completed original full-workload Icarus results only; "
                       "compact and compiled results do not discharge these obligations"}
    return report


def behavior_execution_preflight(run):
    """Record actual dispatch without certifying the original simulator matrix."""
    obligations = []
    for label, g, seed, simulator, tokens, prefill in mandatory_decoder_workloads():
        row = {"profile": label, "geometry": asdict(g), "seed": seed,
               "simulator": simulator, "tokens": list(tokens), "prefill_tokens": prefill}
        obligations.append(row)
    supplemental = {
        "check_id": "supplemental-decoder-a-b8-int4-asymmetric-seed257",
        "profile": "A", "geometry": asdict(replace(A, BANKS=8, CACHE_MODE=2, INT4_ASYM=1)),
        "seed": 257, "simulator": "verilator", "tokens": [1, 4, 2, 6, 3, 5, 7],
        "prefill_tokens": 4,
    }
    write_json(run.path / "execution-contract.json", {
        "status": "tiered-dispatch-original-coverage-unresolved",
        "required_workloads": len(obligations),
        "obligations": obligations,
        "supplemental_obligations": [supplemental],
        "portability_dispatch": {
            "requested": 48, "direct_single_bank": 12,
            "automatic_minimum_single_bank": 36,
            "additional_compiled_requested_geometries": 36,
            "original_coverage_discharged": False},
        "verilator_selection": "A/B: all three seeds; C: seed17; every bank/cache variant",
        "original_coverage": {
            "required_full_icarus": {"A": 48, "B": 48, "C": 16},
            "discharged_by_compact_smoke": False,
            "status": "112 original full-workload Icarus obligations remain unestablished",
            "review_required": True},
        "scope": "requested dispatch inventory only; nested tier_dispatch records actual "
                 "single-bank Icarus and unchanged compiled geometries; "
                 "not numerical or engineering acceptance"})


def numerical_matrix(run):
    behavior_execution_preflight(run)
    a_coverage = []
    decoder_coverage = []
    ledger = memory_maps(run)
    for simulator in ("iverilog", "verilator"):
        ledger.append(host_case(run, simulator))
        for banks in (1, 2, 4, 8):
            for mode in (0, 1, 2):
                ledger.append(bridge_case(run, banks, mode, simulator))
    ledger.extend(compatibility(run))
    ledger.extend(boundaries(run))
    ledger.extend(integration_faults(run))
    jobs = []
    for banks in (1, 2, 4, 8):
        for depth in (1, 3, 16):
            for simulator in ("iverilog", "verilator"):
                jobs.append(lambda b=banks, d=depth, s=simulator: scheduler_case(run, b, d, s))
                for wrap in (1, 2):
                    jobs.append(lambda b=banks, d=depth, s=simulator, w=wrap:
                                scheduler_case(run, b, d, s, wrap=w))
        for tile_k in (8, 24, 128):
            for tile_rows in (1, 3, 8):
                for simulator in ("iverilog", "verilator"):
                    jobs.append(lambda b=banks, k=tile_k, r=tile_rows, s=simulator:
                                prefetch_case(run, b, k, r, s))
    ledger.extend(run.parallel(jobs))
    write_json(run.path / "scheduler-prefetch-matrix.json", ledger)
    jobs = []
    for seed in (17, 89, 257):
        for simulator in ("iverilog", "verilator"):
            jobs.append(lambda s=simulator, n=seed: accumulator_case(run, s, n))
            for unit in (0, 1):
                jobs.append(lambda u=unit, s=simulator, n=seed: math_memory_case(run, u, s, n))
            for unit in range(5):
                jobs.append(lambda u=unit, s=simulator, n=seed: scalar_case(run, s, u, n))
            jobs.append(lambda s=simulator, n=seed: dot8_case(run, s, n))
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                jobs.append(lambda m=mode, a=asym, s=simulator, n=seed:
                            codec_case(run, s, m, a, seed=n))
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
            jobs.append(lambda m=mode, a=asym, n=seed: decoder_case(
                run, replace(A, CACHE_MODE=m, INT4_ASYM=a),
                seed=n, simulator="verilator", tokens=[1, 4],
                compiled_host=True, adversarial=True, label="adversarial-full-range"))
    ledger.extend(run.parallel(jobs))
    jobs = []
    for workload in mandatory_decoder_workloads():
        label, g, seed, simulator, tokens, prefill = workload
        jobs.append(lambda g=g, n=seed, s=simulator, t=tokens, p=prefill:
                    decoder_case(run, g, n, s, tokens=list(t), prefill_tokens=p,
                                 compiled_host=s == "verilator"))
        decoder_coverage.append(workload)
        if label == "A":
            a_coverage.append((g, seed, simulator, tokens, prefill))
    ledger.extend(run.parallel(jobs))
    write_json(run.path / "numerical-matrix.json", ledger)
    for simulator in ("iverilog", "verilator"):
        for banks in (1, 2, 4, 8):
            ledger.append(activation_case(run, banks, simulator,
                                         capacity=11008 if banks == 8 and simulator == "verilator" else
                                         8 if banks == 1 else 120))
            write_json(run.path / "activation-matrix.json", ledger)
    ledger.append(activation_case(run, 8, "verilator", capacity=120))
    write_json(run.path / "activation-matrix.json", ledger)
    mandatory_a_coverage(a_coverage)
    mandatory_decoder_coverage(decoder_coverage)
    original = original_icarus_coverage(ledger)
    write_json(run.path / "original-icarus-coverage.json", original)
    if original["status"] != "passed":
        raise AssertionError(
            f"{len(original['missing'])} original full-workload Icarus obligations remain "
            "unestablished; successful tiered execution is not equivalent acceptance")
    write_json(run.path / "behavior-results.json", ledger)
    return ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", required=True, choices=CHECKS)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run = Run(args.output, args.check)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        if args.check == "prerequisites":
            result = prerequisites(run)
        elif args.check == "structure":
            run.versions([("iverilog", "-V"), ("vvp", "-V"), ("verilator", "--version")])
            result = structure(run)
        elif args.check == "behavior":
            run.versions([("iverilog", "-V"), ("vvp", "-V"), ("verilator", "--version")])
            result = numerical_matrix(run)
        elif args.check == "synthesis":
            result = synthesis(run)
        elif args.check == "reproduce":
            result = reproduce(run)
        elif args.check == "mutations":
            result = mutations(run)
        elif args.check == "benchmark":
            result = benchmark(run)
        elif args.check == "quartus-sta":
            result = quartus_sta(run)
        elif args.check == "board-hil":
            result = board_hil(run)
        else:
            raise AssertionError("unrouted selector " + args.check)
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        print(f"{args.check}: {exc}", file=sys.stderr)
        return 1
    run.finish("passed", result=result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
