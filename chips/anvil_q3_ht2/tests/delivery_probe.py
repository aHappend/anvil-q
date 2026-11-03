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
from verify import Ledger, clean_reproduction, enter_tier


FAILED_RECEIPT = (
    "evidence/l1-all-20261103T033553896046Z/"
    "compatibility-mode2-1793679078565125390/"
    "compatibility-simulate-20261103T041832481330Z/receipt.json"
)


def worker(run):
    ledger = Ledger(run, "changed-delivery-producers-preparation")
    try:
        integrated = ledger.check("integrated-mode1-seed17", run_fast_integration, 1, 17)
        ledger.check("compatibility-mode2", run_compatibility, 2)
        ledger.check("performance", run_performance, integrated)
        ledger.check("integrated-mode2-seed29", run_fast_integration, 2, 29)
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
