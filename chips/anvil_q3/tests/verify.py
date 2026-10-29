#!/usr/bin/env python3
"""Project-relative retained verification entry point.

Unfinished gates are explicit failures, not skipped or accepted evidence.
The shared runtime remains responsible for engineering check execution.
Compact Icarus portability and complete compiled workloads are accounted
separately. execution-contract.json explicitly retains the discrepancy from
the originally admitted full Icarus matrix for independent review.

Planning only (prints exact, self-contained argv for every shard):
  python3 tests/verify.py --check behavior --list-shards --output evidence/check-behavior/shards
Shard collection requires independent append-only admission first. The unchanged
behavior command collects missing/stale cases automatically, then retains its
original full-Icarus coverage gate. A shard success is not a behavior-matrix pass.
"""

import argparse
from collections import Counter
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder_checks import decoder_case
from execution import Run, WORKLOAD_ROOT, workload, write_json
from leaf_checks import codec_case, dot8_case
from parameters import A, A_PORTABILITY, behavioral_geometries, defaults, legal, startup_geometry
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
from boundary_checks import boundaries as _boundaries, integration_faults as _integration_faults
from boundary_checks import singleton_case
from math_memory_checks import math_memory_case
from accumulator_checks import accumulator_case
from map_checks import memory_maps as _memory_maps, map_case
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


def memory_maps(run, plan=False):
    if not plan:
        return _memory_maps(run)
    jobs = []
    for simulator in ("iverilog", "verilator"):
        for mode in (0, 1, 2):
            jobs.append(workload(run, "memory-map", "map_case", map_case,
                                 replace(A, CACHE_MODE=mode), simulator))
            jobs.append(workload(run, "memory-map", "map_case", map_case,
                                 replace(defaults(3), CACHE_MODE=mode), simulator, "official"))
        for profile in (1, 2):
            for mode in ((0,) if profile == 1 else (0, 1)):
                jobs.append(workload(run, "memory-map", "map_case", map_case,
                                     replace(defaults(profile), CACHE_MODE=mode),
                                     simulator, "official"))
    return jobs


def boundaries(run, plan=False):
    if not plan:
        return _boundaries(run)
    jobs = []
    for banks in (1, 2, 4, 8):
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
            jobs.append(workload(run, "boundary", "singleton_case", singleton_case,
                                 banks, mode, asym, "verilator"))
    g = replace(A, BANKS=8, CACHE_MODE=2, INT4_ASYM=1,
                QUEUE_DEPTH=16, TILE_K=128, TILE_ROWS=8)
    if not legal(g):
        raise AssertionError("maximum queue/tile geometry must remain legal")
    jobs.append(workload(
        run, "boundary", "decoder_case", decoder_case, g, simulator="verilator",
        tokens=[1, 4, 2, 6, 3, 5, 7], prefill_tokens=4, label="queue-tile-maxima"))
    for profile in (1, 2, 3):
        g = startup_geometry(profile)
        for boundary in (1, 2, 3, 4):
            if boundary == 2 and profile == 1:
                continue
            prefix = g.MAX_SEQ_LEN if boundary == 1 else 2 if boundary == 2 else 1
            tokens = [1, 4, 2, 6, 3, 5, 7, 8, 9][:prefix] + [2]
            jobs.append(workload(
                run, "boundary", "decoder_case", decoder_case, g, simulator="verilator",
                tokens=tokens, prefill_tokens=1 if boundary == 2 else g.MAX_SEQ_LEN,
                boundary=boundary, restart_at=prefix, label=f"boundary-{boundary}"))
    return jobs


def integration_faults(run, plan=False):
    if not plan:
        return _integration_faults(run)
    jobs = []
    for profile in (1, 2, 3):
        for scenario in range(1, 10):
            if profile == 1 and scenario == 9:
                continue
            g = startup_geometry(profile)
            if scenario == 9:
                g = replace(g, CACHE_MODE=1 if profile == 2 else 2,
                            INT4_ASYM=int(profile == 3))
            jobs.append(workload(
                run, "integration-fault", "decoder_case", decoder_case,
                g, simulator="verilator", tokens=[1, 4],
                fault_scenario=scenario, label=f"integration-fault-{scenario}"))
    return jobs


def behavior_inventory(run=None):
    """Plan every existing case before submitting any work; no phase barriers."""
    jobs = memory_maps(run, plan=True)
    for simulator in ("iverilog", "verilator"):
        jobs.append(workload(run, "host", "host_case", host_case, simulator))
        for banks in (1, 2, 4, 8):
            for mode in (0, 1, 2):
                jobs.append(workload(run, "bridge", "bridge_case", bridge_case,
                                     banks, mode, simulator))
    jobs.extend(compatibility(run, plan=True))
    jobs.extend(boundaries(run, plan=True))
    jobs.extend(integration_faults(run, plan=True))
    for banks in (1, 2, 4, 8):
        for depth in (1, 3, 16):
            for simulator in ("iverilog", "verilator"):
                jobs.append(workload(run, "scheduler", "scheduler_case", scheduler_case,
                                     banks, depth, simulator))
                for wrap in (1, 2):
                    jobs.append(workload(run, "scheduler", "scheduler_case", scheduler_case,
                                         banks, depth, simulator, wrap=wrap))
        for tile_k in (8, 24, 128):
            for tile_rows in (1, 3, 8):
                for simulator in ("iverilog", "verilator"):
                    jobs.append(workload(run, "prefetch", "prefetch_case", prefetch_case,
                                         banks, tile_k, tile_rows, simulator))
    for seed in (17, 89, 257):
        for simulator in ("iverilog", "verilator"):
            jobs.append(workload(run, "accumulator", "accumulator_case",
                                 accumulator_case, simulator, seed))
            for unit in (0, 1):
                jobs.append(workload(run, "math-memory", "math_memory_case",
                                     math_memory_case, unit, simulator, seed))
            for unit in range(5):
                jobs.append(workload(run, "scalar", "scalar_case", scalar_case,
                                     simulator, unit, seed))
            jobs.append(workload(run, "dot8", "dot8_case", dot8_case, simulator, seed))
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                jobs.append(workload(run, "codec", "codec_case", codec_case,
                                     simulator, mode, asym, seed=seed))
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
            jobs.append(workload(
                run, "adversarial", "decoder_case", decoder_case,
                replace(A, CACHE_MODE=mode, INT4_ASYM=asym),
                seed=seed, simulator="verilator", tokens=[1, 4],
                compiled_host=True, adversarial=True, label="adversarial-full-range"))
    for row in mandatory_decoder_workloads():
        label, g, seed, simulator, tokens, prefill = row
        jobs.append(workload_case(run, g, seed, simulator, tokens, prefill))
    for simulator in ("iverilog", "verilator"):
        for banks in (1, 2, 4, 8):
            jobs.append(workload(
                run, "activation", "activation_case", activation_case, banks, simulator,
                capacity=11008 if banks == 8 and simulator == "verilator" else
                8 if banks == 1 else 120))
    jobs.append(workload(run, "activation", "activation_case", activation_case,
                         8, "verilator", capacity=120))
    ids = [job.id for job in jobs]
    if len(set(ids)) != len(ids):
        raise AssertionError("duplicate behavior shard identity")
    return jobs


def workload_case(run, g, seed, simulator, tokens, prefill):
    return workload(run, "decoder", "decoder_case", decoder_case,
                    g, seed, simulator, tokens=list(tokens), prefill_tokens=prefill,
                    compiled_host=simulator == "verilator")


def shard_inventory(output=WORKLOAD_ROOT):
    jobs = behavior_inventory()
    ordered = sorted(jobs, key=lambda job: (-job.cost, job.id))
    return {
        "schema": 1, "scope": "planning only; no simulation or acceptance",
        "original_full_icarus_obligations": 112,
        "ambiguous_objective": "unresolved; these shards do not waive original coverage",
        "required_shards": len(jobs),
        "scheduling": "descending analytical work estimate, then deterministic shard id",
        "cold_budget_feasibility": "unestablished",
        "aggregate_argv": ["python3", "tests/verify.py", "--check", "behavior",
                           "--output", "evidence/check-behavior"],
        "shards": [
            {"id": job.id, "workload": job.descriptor, "scheduling_cost": job.cost,
             "argv": ["python3", "tests/verify.py", "--check", "behavior",
                      "--behavior-shard", job.id, "--output", str(Path(output) / job.id)],
             "outputs": sorted({str(Path(output) / job.id), WORKLOAD_ROOT + "/" + job.id}),
             "requires": ["python3", "iverilog", "vvp", "verilator", "g++", "make"],
             "evidence_requirements": [
                 "settled source/toolchain/workload-bound receipt and raw logs",
                 "unchanged independent comparison and generated fixture artifacts"],
             "retained_root": WORKLOAD_ROOT + "/" + job.id}
            for job in ordered]}


def numerical_matrix(run):
    behavior_execution_preflight(run)
    jobs = behavior_inventory(run)
    ledger = run.parallel(jobs)
    if len(ledger) != len(jobs):
        raise AssertionError("behavior inventory/result count mismatch")
    for job, result in zip(jobs, ledger):
        if job.group == "portability" and result["cycles"] > 500000:
            raise AssertionError("portability smoke exceeds compact cycle tier")
    for filename, groups in (
            ("memory-map-results.json", {"memory-map"}),
            ("compatibility-results.json", {"compatibility", "portability"}),
            ("boundary-results.json", {"boundary"}),
            ("integration-faults.json", {"integration-fault"}),
            ("scheduler-prefetch-matrix.json", {"scheduler", "prefetch"}),
            ("activation-matrix.json", {"activation"})):
        write_json(run.path / filename, [result for job, result in zip(jobs, ledger)
                                         if job.group in groups])
    write_json(run.path / "numerical-matrix.json", ledger)
    labels = {row[1:]: row[0] for row in mandatory_decoder_workloads()}
    decoder_coverage = []
    for job in jobs:
        if job.group == "decoder":
            requested = (*job.args, tuple(job.kwargs["tokens"]), job.kwargs["prefill_tokens"])
            decoder_coverage.append((labels.get(requested, "unknown"), *requested))
    a_coverage = [row[1:] for row in decoder_coverage if row[0] == "A"]
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
    parser.add_argument("--list-shards", action="store_true",
                        help="print exact workload/command inventory without executing tools")
    parser.add_argument("--behavior-shard",
                        help="execute one inventory case; not aggregate behavior acceptance")
    args = parser.parse_args()
    if (args.list_shards or args.behavior_shard) and args.check != "behavior":
        parser.error("shard options require --check behavior")
    if args.list_shards:
        print(json.dumps(shard_inventory(args.output), indent=2, sort_keys=True))
        return 0
    selected = None
    if args.behavior_shard:
        selected = next((job for job in behavior_inventory()
                         if job.id == args.behavior_shard), None)
        if selected is None:
            parser.error("unknown behavior shard; use --list-shards")
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
            if selected is None:
                result = numerical_matrix(run)
            else:
                result = {"scope": "single shard only; original coverage remains unresolved",
                          "id": selected.id, "result": run.parallel([selected])[0]}
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
