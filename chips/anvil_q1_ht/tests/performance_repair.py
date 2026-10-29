#!/usr/bin/env python3
"""Bounded performance diagnostics; unchanged complete cases, never acceptance.

python3 -B tests/performance_repair.py --integration-profile
profiles a complete configuration-1 AWQ case using gprof instrumentation.
--integration-compare compares complete AWQ/BF16 cases with module inlining
disabled and enabled, including every public comparison and cycle counter.
--kv-build-compare compares complete KV service workloads under -O3 and -Os.
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiments import top_probe
from kv_faults import kv_fault_case
from reference import MATRIX
from verify import Evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--integration-profile", action="store_true")
    modes.add_argument("--integration-compare", action="store_true")
    modes.add_argument("--kv-build-compare", action="store_true")
    parser.add_argument("--config", type=int, choices=(0, 1), default=1)
    parser.add_argument("--repair-of", default=(
        "evidence/preparation/verifier-mandatory-20261029T214526Z-e7ab7728/receipt.json"))
    args = parser.parse_args()
    evidence = Evidence("kv-build-costs" if args.kv_build_compare else
                        "integration-hotpaths" if args.integration_profile else
                        "integration-inlining", repair_of=args.repair_of)
    try:
        if args.kv_build_compare:
            results = evidence.record["complete_KV_cases"] = []
            for depth in (1, 3, 128):
                baseline = None
                for optimization in ("-O3", "-Os"):
                    trial = Evidence(
                        f"kv-build-{depth}-{optimization[1:]}",
                        repair_of=evidence.relative(evidence.folder / "receipt.json"),
                        source_root=evidence.folder / "sources")
                    try:
                        started = time.monotonic()
                        kv_fault_case(trial, depth, 17, "verilator", optimization)
                        counters = trial.record["kv_service_checks"][-1]["observed"]
                        if baseline is not None and counters != baseline["counters"]:
                            raise AssertionError("KV compiler optimization changed comparisons or cycles")
                        result = {
                            "window": depth, "cxx_optimization": optimization,
                            "counters": counters,
                            "receipt": evidence.relative(trial.folder / "receipt.json"),
                            "wall_seconds_including_build": time.monotonic() - started,
                            "compile_seconds": sum(row["elapsed_seconds"]
                                                   for row in trial.record["commands"]
                                                   if row["label"].endswith("-compile")),
                            "simulation_seconds": sum(row["elapsed_seconds"]
                                                      for row in trial.record["commands"]
                                                      if row["label"].endswith("-simulation")),
                        }
                        trial.finish("probe_passed", "Complete KV service cost comparison only.")
                    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
                        trial.finish("failed", str(exc))
                        raise
                    results.append(result)
                    baseline = result
                    evidence.flush()
            evidence.finish("probe_passed", "Identical complete KV service cases; not aggregate acceptance.")
            return 0
        pool = {}
        results = evidence.record["complete_cases"] = []
        for mode in (("AWQ",) if args.integration_profile else ("AWQ", "BF16")):
            baseline = None
            for flatten in ((False,) if args.integration_profile else (False, True)):
                trial = Evidence(
                    f"inlining-{mode.lower()}-{int(flatten)}",
                    repair_of=evidence.relative(evidence.folder / "receipt.json"),
                    source_root=evidence.folder / "sources")
                trial.native_profile = args.integration_profile
                trial.simulation_build_pool = pool
                try:
                    started = time.monotonic()
                    top_probe(trial, mode, 17, config=args.config, flatten=flatten)
                    counters = trial.record["observations"][-1]["observed_counters"]
                    tokens = [row for row in counters if "position" in row]
                    shape = MATRIX[args.config]
                    required = min(shape.max_seq, shape.window + 2) + 1
                    if len(tokens) != required or any(row["logits"] != shape.vocab for row in tokens):
                        raise AssertionError("performance diagnostic omitted complete-case comparisons")
                    if baseline is not None and (
                            counters != baseline["counters"] or
                            trial.record["engineering_fixture"] != baseline["fixture"]):
                        raise AssertionError("inlining changed workload, comparisons or cycle counters")
                    simulations = [row for row in trial.record["commands"]
                                   if row["label"] == "top-" + mode.lower() + "-simulation"]
                    simulation, = simulations
                    result = {
                        "configuration": args.config, "mode": mode, "seed": 17, "flatten": flatten,
                        "tokens": len(tokens), "ordered_logits": sum(row["logits"] for row in tokens),
                        "receipt": evidence.relative(trial.folder / "receipt.json"),
                        "simulation_seconds": simulation["elapsed_seconds"],
                        "wall_seconds_including_build": time.monotonic() - started,
                        "counters": counters, "fixture": trial.record["engineering_fixture"],
                        "scope": "host simulator diagnosis, not accelerator throughput or full L1",
                    }
                    trial.finish("probe_passed", result["scope"])
                except (OSError, RuntimeError, AssertionError, ValueError) as exc:
                    trial.finish("failed", str(exc))
                    raise
                results.append(result)
                baseline = result
                evidence.flush()
        evidence.finish("probe_passed", "Bounded complete-case performance diagnosis only.")
        return 0
    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
        evidence.finish("failed", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
