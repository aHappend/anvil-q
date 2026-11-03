"""Authorized bounded preparation of changed delivery producers, not admission."""

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from compatibility import run_compatibility
from integrated_fast import run_fast_integration
from performance import run_performance
from performance import measure_sustained
from arithmetic import run_arithmetic
from tile import run_tile
from sparse import run_sparse
from tree_attention import run_tree
from kv_atomic import run_atomic
from synthesis import run_synthesis
from receipts import ROOT, execute, new_run, relative, utc
from verify import Ledger, bind_mutation_control, clean_reproduction, enter_tier


FAILED_RECEIPT = (
    "evidence/l1-all-20261103T042653651958Z/"
    "compatibility-mode1-1793680921796401778/"
    "compatibility-compile-20261103T044202191734Z/receipt.json"
)


def run_cache_path(run):
    result = execute(run, "integration-cached-path", [
        sys.executable, "tests/cache_reuse.py", "--integration-path"],
        [sys.executable, "--version"])
    records = [json.loads(line) for line in (result / "stdout.txt").read_text().splitlines()
               if line.startswith('{"summary":')]
    if len(records) != 1 or records[0]["status"] != "passed":
        raise AssertionError("missing exact cached-path diagnostic result")
    return {"receipt": relative(result / "receipt.json"), **records[0]}


def worker(run, focus):
    ledger = Ledger(run, "changed-delivery-producers-preparation")
    try:
        if focus == "repaired-tools":
            for name, function in (("broadcast", run_tile), ("sparse", run_sparse)):
                control = ledger.check(f"control-{name}", function, "verilator", 17, True)
                observed = ledger.check(f"mutation-{name}", function, "verilator", 17,
                                        True, mutant=True)
                bind_mutation_control(ledger, control, observed,
                                      ("seed", "simulator", "vector_sha256"))
            ledger.check("clean-reproduction", clean_reproduction)
        elif focus == "compacted":
            ledger.check("tile-portability", run_tile, "iverilog", 17, True)
            ledger.check("sparse-portability", run_sparse, "iverilog", 17, True)
            for seed in (17, 29, 43):
                ledger.check(f"tile-seed{seed}", run_tile, "verilator", seed, False)
                ledger.check(f"sparse-seed{seed}", run_sparse, "verilator", seed, False)
            ledger.check("sustained-physical-bandwidth", measure_sustained)
            ledger.check("compatibility-mode1", run_compatibility, 1)
            ledger.check("compatibility-mode2", run_compatibility, 2)
        elif focus == "residual":
            ledger.check("integration-cached-path", run_cache_path)
            ledger.check("sustained-physical-bandwidth", measure_sustained)
            for mode in (1, 2):
                for top in (("anvil_q3_ht2_top", "anvil_q3_ht2_tree_attention",
                             "anvil_q3_ht2_kv_commit_engine", "anvil_q3_ht2_spec_verifier")
                            if mode == 2 else ()):
                    ledger.check(f"synthesis-{top}-mode{mode}", run_synthesis, top, mode)
            for top in ("anvil_q3_ht2_tile_batch_mac", "anvil_q3_ht2_projection",
                        "anvil_q3_ht2_sparse_dma", "anvil_q3_ht2_ddr_arbiter",
                        "anvil_q3_ht2_private_scratch"):
                ledger.check(f"synthesis-{top}", run_synthesis, top)
            control = ledger.check("tree-control", run_tree, 1, 17, residency=3)
            for mutant in ("gqa", "sibling"):
                observed = ledger.check(f"mutation-{mutant}", run_tree, 1, 17,
                                        mutant=mutant, residency=3)
                bind_mutation_control(ledger, control, observed,
                                      ("mode", "seed", "residency", "vector_sha256"))
            control = ledger.check("atomic-control", run_atomic, 1, 17)
            observed = ledger.check("mutation-atomic", run_atomic, 1, 17, mutant=True)
            bind_mutation_control(ledger, control, observed,
                                  ("mode", "seed", "record_sha256"))
            for name, function in (("broadcast", run_tile), ("rounding", run_arithmetic),
                                   ("sparse", run_sparse)):
                control = ledger.check(f"control-{name}", function, "verilator", 17, True)
                observed = ledger.check(f"mutation-{name}", function, "verilator", 17,
                                        True, mutant=True)
                bind_mutation_control(ledger, control, observed,
                                      ("seed", "simulator", "vector_sha256"))
            ledger.check("clean-reproduction", clean_reproduction)
        elif focus == "integration-boundary":
            ledger.check("integrated-one-layer-mode1", run_fast_integration, 1, 17,
                         layers=1, compact=True)
        elif focus == "compact-closure":
            controls = {}
            for seed in (17, 29, 43):
                controls[seed] = ledger.check(
                    f"tile-seed{seed}", run_tile, "verilator", seed, True)
            mutant = ledger.check("mutation-broadcast", run_tile, "verilator",
                                  17, True, mutant=True)
            bind_mutation_control(ledger, controls[17], mutant,
                                  ("seed", "simulator", "vector_sha256"))
            ledger.check("integrated-one-layer-mode2", run_fast_integration, 2, 29,
                         layers=1, compact=True)
        elif focus == "integration":
            integrated = ledger.check("integrated-mode1-seed17", run_fast_integration, 1, 17,
                                      compact=True)
            ledger.check("performance", run_performance, integrated)
            ledger.check("integrated-mode2-seed29", run_fast_integration, 2, 29,
                         compact=True)
        elif focus == "compatibility":
            ledger.check("compatibility-mode2", run_compatibility, 2)
            ledger.check("compatibility-mode1", run_compatibility, 1)
            ledger.check("clean-reproduction", clean_reproduction)
        else:
            integrated = ledger.check("integrated-mode1-seed17", run_fast_integration, 1, 17,
                                      compact=True)
            ledger.check("compatibility-mode2", run_compatibility, 2)
            ledger.check("performance", run_performance, integrated)
            ledger.check("integrated-mode2-seed29", run_fast_integration, 2, 29,
                         compact=True)
            ledger.check("compatibility-mode1", run_compatibility, 1)
            ledger.check("clean-reproduction", clean_reproduction)
        ledger.finish()
    except Exception as error:
        ledger.data.update(status="failed", finished_at=utc(),
                           error=f"{type(error).__name__}: {error}")
        ledger.save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--_worker-run", help=argparse.SUPPRESS)
    parser.add_argument("--repair-of", default=FAILED_RECEIPT)
    parser.add_argument("--focus", choices=("all", "compatibility", "integration", "residual",
                                          "compacted", "repaired-tools",
                                          "integration-boundary", "compact-closure"),
                        default="all")
    args = parser.parse_args()
    enter_tier()
    if args._worker_run:
        run = ROOT / args._worker_run
        if not run.resolve().is_relative_to(ROOT / "evidence/preparation"):
            parser.error("worker run must be a preparation directory")
        worker(run, args.focus)
    else:
        run = new_run("delivery-producers", preparation=True, repair_of=args.repair_of)
        print(f"Preparation evidence: {relative(run)}", flush=True)
        result = execute(run, "changed-producers", [
            sys.executable, "tests/delivery_probe.py", "--_worker-run", relative(run),
            "--focus", args.focus],
            [sys.executable, "--version"])
        print(json.dumps({"preparation_receipt": relative(result / "receipt.json"),
                          "summary": relative(run / "summary.json")}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
