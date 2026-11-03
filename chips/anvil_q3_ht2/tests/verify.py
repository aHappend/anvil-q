#!/usr/bin/env python3
"""Source-bound L1 orchestration and fresh-directory portable reproduction."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from receipts import ROOT, execute, hashes, new_run, relative, sources, utc
from arithmetic import run_arithmetic
from compatibility import run_compatibility
from integrated_fast import run_fast_integration
from kv_atomic import run_atomic
from parameters import run_parameters
from performance import run_performance
from projection_boundary import run_projection_boundary
from projection_layout import compact_parameters, run_projection_layout
from sparse import run_sparse
from speculative import run_spec
from synthesis import run_synthesis
from tile import run_tile
from tree_attention import run_tree


SEEDS = (17, 29, 43)
INTEGRATION_SAMPLES = ((1, 17), (2, 29))


def enter_tier():
    """Only the outer entry establishes an allowance; children inherit it."""
    entered = time.monotonic()
    if "HT2_L1_DEADLINE" not in os.environ:
        os.environ["HT2_L1_DEADLINE"] = repr(entered + 2700)
    deadline = float(os.environ["HT2_L1_DEADLINE"])
    if not math.isfinite(deadline) or deadline <= entered:
        raise RuntimeError("inherited L1 execution allowance is invalid or exhausted")
    return entered, deadline


def case_directory(run, name):
    timestamp = time.time_ns()
    path = run / f"{name}-{timestamp}"
    path.mkdir(exist_ok=False)
    return path


class Ledger:
    def __init__(self, run, suite):
        self.run = run
        self.data = {
            "suite": suite, "started_at": utc(), "status": "running",
            "source_sha256": hashes(sources()), "cases": [],
            "shared_deadline_monotonic": os.environ["HT2_L1_DEADLINE"],
        }
        self.save()

    def save(self):
        (self.run / "summary.json").write_text(json.dumps(self.data, indent=2) + "\n")

    def check(self, name, function, *args, **kwargs):
        directory = case_directory(self.run, name)
        started = time.monotonic()
        row = {"name": name, "directory": relative(directory), "status": "running",
               "started_at": utc()}
        self.data["cases"].append(row)
        self.save()
        print(f"L1 {name}: {relative(directory)}", flush=True)
        try:
            row["result"] = function(directory, *args, **kwargs)
            row["status"] = "passed"
        except Exception as error:
            row.update(status="failed", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            row.update(finished_at=utc(), duration_s=time.monotonic() - started)
            self.save()
        return row["result"]

    def finish(self):
        if hashes(sources()) != self.data["source_sha256"]:
            raise AssertionError("verification sources changed during this suite")
        if not self.data["cases"] or any(
                row["status"] != "passed" for row in self.data["cases"]):
            raise AssertionError("suite contains missing or unsuccessful observations")
        self.data.update(status="passed", finished_at=utc())
        self.save()


def compact_reproduction(ledger):
    ledger.check("minimum-gqa-projection", run_projection_boundary)
    ledger.check("arithmetic-portability", run_arithmetic, "iverilog", 17, True)
    ledger.check("aligned-public-ddr", run_sparse, "iverilog", 17, True)
    for mode in (1, 2):
        ledger.check(f"atomic-int{8 if mode == 1 else 4}", run_atomic, mode, 17)
    ledger.check("compact-dma-synthesis", run_synthesis,
                 "anvil_q3_ht2_sparse_dma", parameters={"MAX_COLUMNS": 17})


def copy_public_sources(run):
    tree = run / "clean-source"
    tree.mkdir()
    captured = sources()
    for source in captured:
        destination = tree / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    expected = hashes(captured)
    actual = {name: hashlib.sha256((tree / name).read_bytes()).hexdigest()
              for name in expected}
    if actual != expected:
        raise AssertionError("clean reproduction source copy differs")
    (run / "copied-inputs.json").write_text(json.dumps(expected, indent=2) + "\n")
    return tree, expected


def clean_reproduction(run):
    tree, expected = copy_public_sources(run)
    launch = run / "unrelated-launch"
    launch.mkdir()
    entry = os.path.relpath(tree / "tests/verify.py", launch)
    result = execute(run, "clean-reproduction", [
        sys.executable, entry, "--suite", "clean-repro", "--_repro-worker"],
        [sys.executable, "--version"], cwd=launch)
    summaries = list((tree / "evidence").glob("l1-clean-repro-*/summary.json"))
    if len(summaries) != 1:
        raise AssertionError("fresh reproduction did not create exactly one result")
    observed = json.loads(summaries[0].read_text())
    if observed["status"] != "passed" or observed["source_sha256"] != expected:
        raise AssertionError("clean reproduction is unsuccessful or not source-bound")
    return {"receipt": relative(result / "receipt.json"),
            "summary": relative(summaries[0]), "copied_files": len(expected),
            "observed": observed}


def require_complete_coverage(ledger):
    """Check measured product requirements, not only child return codes."""
    rows = {row["name"]: row["result"] for row in ledger.data["cases"]}
    required_mutations = {"broadcast", "rounding", "sparse", "sibling", "gqa", "atomic"}
    observed_mutations = {
        name.removeprefix("mutation-") for name, result in rows.items()
        if name.startswith("mutation-") and (
            result.get("discrimination") or result.get("observed", {}).get("discrimination"))
    }
    requirements = {
        "six_compiled_mutation_classes": required_mutations <= observed_mutations,
        "production_top_both_cache_modes": all(
            any(result.get("top") == "anvil_q3_ht2_top" and
                result.get("cache_mode") == mode for result in rows.values())
            for mode in (1, 2)),
        "legacy_public_pin_compatibility_both_modes": all(
            rows.get(f"compatibility-mode{mode}", {}).get("compared_transactions", 0) > 0
            for mode in (1, 2)),
        "measured_whole_ffn_reduction_at_least_40_percent":
            rows.get("performance", {}).get("whole_ffn_reduction", -1) >= 0.4,
        "measured_effective_bandwidth_at_least_3_4":
            rows.get("performance", {}).get("effective_bandwidth_ratio", -1) >= 3.4,
        "production_arithmetic_beats_each_seed": all(
            rows.get(f"tile-seed{seed}", {}).get("weight_lanes") == 128 and
            rows.get(f"tile-seed{seed}", {}).get("observed", {}).get("inputs", 0) ==
            rows.get(f"tile-seed{seed}", {}).get("expected_inputs") and
            rows.get(f"tile-seed{seed}", {}).get("observed", {}).get("inputs", 0) >= (
                239 if rows.get(f"tile-seed{seed}", {}).get("compact") else 1024)
            for seed in SEEDS),
        "consecutive_dense_beats_each_seed": all(
            rows.get(f"tile-seed{seed}", {}).get("observed", {}).get(
                "max_consecutive_beats", 0) >= 64 for seed in SEEDS),
        "complete_nonzero_36_layer_chain_and_branch_both_modes": all(
            rows.get(f"integrated-mode{mode}-seed{seed}", {}).get("layers") == 36 and
            rows.get(f"integrated-mode{mode}-seed{seed}", {}).get(
                "nonzero_projection_comparisons", 0) > 0 and
            rows.get(f"integrated-mode{mode}-seed{seed}", {}).get(
                "compared_tree_shapes", []) == ["chain", "branch"]
            for mode, seed in INTEGRATION_SAMPLES),
    }
    ledger.data["coverage_requirements"] = requirements
    ledger.save()
    missing = [name for name, satisfied in requirements.items() if not satisfied]
    if missing:
        raise AssertionError("missing mandatory measured coverage: " + ", ".join(missing))


def bind_mutation_control(ledger, control, mutant, fields):
    for field in fields:
        if field not in control or field not in mutant or control[field] != mutant[field]:
            raise AssertionError(f"mutation/control mismatch: {field}")
    if not (mutant.get("discrimination") or
            mutant.get("observed", {}).get("discrimination")):
        raise AssertionError("mutation did not discriminate the targeted defect")
    if "receipt" not in control:
        raise AssertionError("mutation control lacks an execution receipt")
    mutant["control_receipt"] = control["receipt"]
    mutant["control_matched_fields"] = list(fields)
    ledger.save()


def all_checks(ledger):
    performance_integration = None
    ledger.check("parameter-boundaries", run_parameters)
    ledger.check("minimum-gqa-projection", run_projection_boundary)
    for heads in (1, 2, 3):
        ledger.check(f"packed-projection-kvheads{heads}", run_projection_layout, heads)
    ledger.check("arithmetic-portability", run_arithmetic, "iverilog", 17, True)
    ledger.check("tile-portability", run_tile, "iverilog", 17, True)
    ledger.check("aligned-ddr-portability", run_sparse, "iverilog", 17, True)
    for seed in SEEDS:
        ledger.check(f"arithmetic-seed{seed}", run_arithmetic, "verilator", seed, False)
        ledger.check(f"tile-seed{seed}", run_tile, "verilator", seed, True)
        ledger.check(f"sparse-seed{seed}", run_sparse, "verilator", seed, seed != 43)
        for mode in (1, 2):
            ledger.check(f"tree-mode{mode}-seed{seed}", run_tree, mode, seed,
                         residency=1 if (seed + mode) % 2 else 3)
            ledger.check(f"greedy-mode{mode}-seed{seed}", run_spec, mode, seed)
            ledger.check(f"atomic-mode{mode}-seed{seed}", run_atomic, mode, seed)
    for mode in (1, 2):
        ledger.check(f"synthesis-minimum-gqa-mode{mode}", run_synthesis,
                     "anvil_q3_ht2_top", mode, compact_parameters())
        ledger.check(f"compatibility-mode{mode}", run_compatibility, mode)
        for top in ("anvil_q3_ht2_top", "anvil_q3_ht2_tree_attention",
                    "anvil_q3_ht2_kv_commit_engine", "anvil_q3_ht2_spec_verifier"):
            ledger.check(f"synthesis-{top}-mode{mode}", run_synthesis, top, mode)
    for mode, seed in INTEGRATION_SAMPLES:
        result = ledger.check(
            f"integrated-mode{mode}-seed{seed}", run_fast_integration, mode, seed,
            compact=True)
        if (mode, seed) == (1, 17):
            performance_integration = result
    for top in ("anvil_q3_ht2_tile_batch_mac", "anvil_q3_ht2_projection",
                "anvil_q3_ht2_sparse_dma", "anvil_q3_ht2_ddr_arbiter",
                "anvil_q3_ht2_private_scratch"):
        ledger.check(f"synthesis-{top}", run_synthesis, top)
    ledger.check("performance", run_performance, performance_integration)
    controls = {row["name"]: row["result"] for row in ledger.data["cases"]}
    tree_control = controls["tree-mode1-seed17"]
    for mutant in ("gqa", "sibling"):
        result = ledger.check(f"mutation-{mutant}", run_tree, 1, 17, mutant=mutant,
                              residency=tree_control["residency"])
        bind_mutation_control(ledger, tree_control, result,
                              ("mode", "seed", "residency", "vector_sha256"))
    atomic_mutant = ledger.check("mutation-atomic", run_atomic, 1, 17, mutant=True)
    bind_mutation_control(ledger, controls["atomic-mode1-seed17"], atomic_mutant,
                          ("mode", "seed", "record_sha256"))
    for name, function in (("broadcast", run_tile), ("rounding", run_arithmetic),
                           ("sparse", run_sparse)):
        control = ledger.check(f"control-{name}", function, "verilator", 17, True)
        mutant = ledger.check(f"mutation-{name}", function, "verilator", 17, True,
                              mutant=True)
        bind_mutation_control(ledger, control, mutant,
                              ("seed", "simulator", "vector_sha256"))
    ledger.check("clean-reproduction", clean_reproduction)
    require_complete_coverage(ledger)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("all", "clean-repro"), required=True)
    parser.add_argument("--_repro-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    enter_tier()
    run = new_run(args.suite)
    print(f"L1 evidence: {relative(run)}", flush=True)
    ledger = Ledger(run, args.suite)
    try:
        if args.suite == "all":
            if args._repro_worker:
                parser.error("reproduction worker requires --suite clean-repro")
            all_checks(ledger)
        elif args._repro_worker:
            compact_reproduction(ledger)
        else:
            ledger.check("fresh-source-reproduction", clean_reproduction)
        ledger.finish()
    except Exception as error:
        ledger.data.update(status="failed", finished_at=utc(),
                           error=f"{type(error).__name__}: {error}")
        ledger.save()
        print(f"{error}; see {relative(run)}/summary.json", file=sys.stderr)
        return 1
    print(json.dumps({"suite": args.suite, "status": "passed",
                      "summary": relative(run / "summary.json")}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
