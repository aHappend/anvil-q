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
from integrated import run_integrated
from kv_atomic import run_atomic
from sparse import run_sparse
from speculative import run_spec
from synthesis import run_synthesis
from tile import run_tile
from tree_attention import run_tree


SEEDS = (17, 29, 43)


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
        row = {"name": name, "directory": relative(directory), "status": "running"}
        self.data["cases"].append(row)
        self.save()
        print(f"L1 {name}: {relative(directory)}", flush=True)
        try:
            row["result"] = function(directory, *args, **kwargs)
            row["status"] = "passed"
        except Exception as error:
            row.update(status="failed", error=f"{type(error).__name__}: {error}")
            self.save()
            raise
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
    ledger.check("arithmetic-portability", run_arithmetic, "iverilog", 17, True)
    ledger.check("aligned-public-ddr", run_sparse, "iverilog", 17, True)
    for mode in (1, 2):
        ledger.check(f"atomic-int{8 if mode == 1 else 4}", run_atomic, mode, 17)
    ledger.check("compact-dma-synthesis", run_synthesis,
                 "anvil_q3_ht2_sparse_dma", parameters={"MAX_COLUMNS": 17})


def clean_reproduction(run):
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
    }
    ledger.data["coverage_requirements"] = requirements
    ledger.save()
    missing = [name for name, satisfied in requirements.items() if not satisfied]
    if missing:
        raise AssertionError("missing mandatory measured coverage: " + ", ".join(missing))


def all_checks(ledger):
    ledger.check("integration-profile", run_integrated, 1, True)
    ledger.check("arithmetic-portability", run_arithmetic, "iverilog", 17, True)
    ledger.check("tile-portability", run_tile, "iverilog", 17, True)
    ledger.check("aligned-ddr-portability", run_sparse, "iverilog", 17, True)
    for seed in SEEDS:
        ledger.check(f"arithmetic-seed{seed}", run_arithmetic, "verilator", seed, False)
        ledger.check(f"tile-seed{seed}", run_tile, "verilator", seed, False)
        ledger.check(f"sparse-seed{seed}", run_sparse, "verilator", seed, False)
        for mode in (1, 2):
            ledger.check(f"tree-mode{mode}-seed{seed}", run_tree, mode, seed,
                         residency=1 if (seed + mode) % 2 else 3)
            ledger.check(f"greedy-mode{mode}-seed{seed}", run_spec, mode, seed)
            ledger.check(f"atomic-mode{mode}-seed{seed}", run_atomic, mode, seed)
    for mode in (1, 2):
        ledger.check(f"integrated-mode{mode}", run_integrated, mode)
        for top in ("anvil_q3_ht2_kv_commit_engine", "anvil_q3_ht2_spec_verifier"):
            ledger.check(f"synthesis-{top}-mode{mode}", run_synthesis, top, mode)
    for top in ("anvil_q3_ht2_sparse_dma", "anvil_q3_ht2_ddr_arbiter",
                "anvil_q3_ht2_private_scratch"):
        ledger.check(f"synthesis-{top}", run_synthesis, top)
    for mutant in ("gqa", "sibling"):
        ledger.check(f"mutation-{mutant}", run_tree, 1, 17, mutant=mutant)
    ledger.check("mutation-atomic", run_atomic, 1, 17, mutant=True)
    for name, function in (("broadcast", run_tile), ("rounding", run_arithmetic),
                           ("sparse", run_sparse)):
        control = ledger.check(f"control-{name}", function, "verilator", 17, True)
        mutant = ledger.check(f"mutation-{name}", function, "verilator", 17, True,
                              mutant=True)
        if control["vector_sha256"] != mutant["vector_sha256"]:
            raise AssertionError(f"mutation/control vectors differ: {name}")
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
