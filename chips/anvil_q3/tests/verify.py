#!/usr/bin/env python3
"""Project-relative retained verification entry point.

Unfinished gates are explicit failures, not skipped or accepted evidence.
The shared runtime remains responsible for engineering check execution.
Decoder dispatch and completion accounting retain the complete frozen simulator
matrix. Compact single-token smokes do not replace multi-token Icarus coverage.
Trace I/O already flushes only at DONE/SUMMARY, never per memory request.
The behavior gate preflights every frozen decoder simulator obligation before
launching tools; an incompatible execution policy fails, never skips coverage.
"""

import argparse
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder_checks import SimulationTierConflict, decoder_case, validate_simulation_tier
from execution import Run, write_json
from leaf_checks import codec_case, dot8_case
from parameters import A, behavioral_geometries
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
    """Reject simulator substitution independently of dispatch/tiering policy."""
    expected = Counter(
        (replace(A, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym), seed,
         simulator, (1, 4, 2, 6, 3, 5, 7), 4)
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
            "workloads. Compiled results do not satisfy frozen Icarus obligations; "
            "the simulator-policy conflict requires independent reconciliation.")
    return {"required": sum(expected.values()), "observed": sum(observed.values())}


def mandatory_decoder_workloads():
    """Keep actual dispatch identical to the frozen preflight obligations."""
    for label, g in behavioral_geometries():
        for seed in ((17,) if label == "C" else (17, 89, 257)):
            tokens = (1, 4, 2, 6) if label == "C" else (1, 4, 2, 6, 3, 5, 7)
            simulators = ("iverilog", "verilator") if label == "A" or seed == 17 else ("iverilog",)
            for simulator in simulators:
                yield label, g, seed, simulator, tokens, 2 if label == "C" else 4


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


def behavior_execution_preflight(run):
    """Expose frozen obligations incompatible with policy before decoder execution.

    B/C require all Icarus cases and selected Verilator cases spanning every
    bank/cache variant; seed17 supplies that selection without expanding it to
    B's entire three-seed matrix. The policy guard still blocks incompatible runs.
    """
    obligations = []
    for label, g, seed, simulator, tokens, prefill in mandatory_decoder_workloads():
        row = {"profile": label, "geometry": asdict(g), "seed": seed,
               "simulator": simulator, "tokens": list(tokens), "prefill_tokens": prefill}
        try:
            validate_simulation_tier(g, simulator, tokens)
        except SimulationTierConflict as exc:
            row["conflict"] = str(exc)
        obligations.append(row)
    supplemental = {
        "check_id": "supplemental-decoder-a-b8-int4-asymmetric-seed257",
        "profile": "A", "geometry": asdict(replace(A, BANKS=8, CACHE_MODE=2, INT4_ASYM=1)),
        "seed": 257, "simulator": "verilator", "tokens": [1, 4, 2, 6, 3, 5, 7],
        "prefill_tokens": 4,
    }
    try:
        validate_simulation_tier(
            replace(A, BANKS=8, CACHE_MODE=2, INT4_ASYM=1),
            supplemental["simulator"], supplemental["tokens"])
    except SimulationTierConflict as exc:
        supplemental["conflict"] = str(exc)
    conflicts = [row for row in obligations if "conflict" in row]
    supplemental_conflicts = int("conflict" in supplemental)
    write_json(run.path / "execution-contract.json", {
        "status": "incompatible" if conflicts or supplemental_conflicts else "compatible",
        "required_workloads": len(obligations), "conflicting_workloads": len(conflicts),
        "obligations": obligations,
        "supplemental_obligations": [supplemental],
        "conflicting_supplemental_workloads": supplemental_conflicts,
        "verilator_selection": "A: all seeds; B/C: seed17 across every bank/cache variant",
        "scope": "execution-policy preflight only; no numerical coverage"})
    if conflicts or supplemental_conflicts:
        counts = Counter(row["profile"] for row in conflicts)
        raise SimulationTierConflict(
            "frozen decoder simulator obligations conflict with the execution policy: "
            f"{len(conflicts)}/{len(obligations)} behavior workloads "
            f"({dict(sorted(counts.items()))}); {supplemental_conflicts} supplemental workload. "
            "See execution-contract.json. No behavior subtest was launched. "
            "Preserve all mandatory Icarus runs, seeds, tokens and thresholds; "
            "authoritative reconciliation and independent admission are required, "
            "not compiled-simulator substitution.")


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
    for banks in (1, 2, 4, 8):
        for depth in (1, 3, 16):
            for simulator in ("iverilog", "verilator"):
                ledger.append(scheduler_case(run, banks, depth, simulator))
                for wrap in (1, 2):
                    ledger.append(scheduler_case(run, banks, depth, simulator, wrap=wrap))
                write_json(run.path / "scheduler-matrix.json", ledger)
        for tile_k in (8, 24, 128):
            for tile_rows in (1, 3, 8):
                for simulator in ("iverilog", "verilator"):
                    ledger.append(prefetch_case(run, banks, tile_k, tile_rows, simulator))
                    write_json(run.path / "prefetch-matrix.json", ledger)
    for seed in (17, 89, 257):
        for simulator in ("iverilog", "verilator"):
            ledger.append(accumulator_case(run, simulator, seed))
            for unit in (0, 1):
                ledger.append(math_memory_case(run, unit, simulator, seed))
            for unit in range(5):
                ledger.append(scalar_case(run, simulator, unit, seed))
            ledger.append(dot8_case(run, simulator, seed))
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                ledger.append(codec_case(run, simulator, mode, asym, seed=seed))
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
            ledger.append(decoder_case(
                run, replace(A, CACHE_MODE=mode, INT4_ASYM=asym),
                seed=seed, simulator="verilator", tokens=[1, 4],
                adversarial=True, label="adversarial-full-range"))
    for workload in mandatory_decoder_workloads():
        label, g, seed, simulator, tokens, prefill = workload
        ledger.append(decoder_case(run, g, seed, simulator, tokens=list(tokens),
                                   prefill_tokens=prefill))
        decoder_coverage.append(workload)
        if label == "A":
            a_coverage.append((g, seed, simulator, tokens, prefill))
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
