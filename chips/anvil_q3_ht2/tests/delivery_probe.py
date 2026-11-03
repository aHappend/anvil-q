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
from receipts import ROOT, execute, new_run, relative, utc
from synthesis import run_synthesis
from verify import Ledger, clean_reproduction, enter_tier


FAILED_RECEIPT = (
    "evidence/preparation/delivery-producers-20261103T024849232660Z/"
    "changed-producers-20261103T024849279956Z/receipt.json"
)


def worker(run):
    ledger = Ledger(run, "changed-delivery-producers-preparation")
    try:
        for mode in (1, 2):
            ledger.check(f"read-only-attention-synthesis-mode{mode}", run_synthesis,
                         "anvil_q3_ht2_tree_attention", mode)
            ledger.check(f"compatibility-mode{mode}", run_compatibility, mode)
        integrated = ledger.check("integrated-mode1-seed17", run_fast_integration, 1, 17)
        ledger.check("performance", run_performance, integrated)
        ledger.check("integrated-mode2-seed29", run_fast_integration, 2, 29)
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
    args = parser.parse_args()
    enter_tier()
    if args._worker_run:
        run = ROOT / args._worker_run
        if not run.resolve().is_relative_to(ROOT / "evidence/preparation"):
            parser.error("worker run must be a preparation directory")
        worker(run)
    else:
        run = new_run("delivery-producers", preparation=True, repair_of=args.repair_of)
        print(f"Preparation evidence: {relative(run)}", flush=True)
        result = execute(run, "changed-producers", [
            sys.executable, "tests/delivery_probe.py", "--_worker-run", relative(run)],
            [sys.executable, "--version"])
        print(json.dumps({"preparation_receipt": relative(result / "receipt.json"),
                          "summary": relative(run / "summary.json")}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
