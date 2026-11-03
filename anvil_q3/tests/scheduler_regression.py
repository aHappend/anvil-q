"""Bounded public-pin mailbox repair regression; not aggregate acceptance."""

from datetime import datetime, timezone
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Run, write_json
from scheduler_checks import scheduler_case


FAILED_RECEIPT = (
    "evidence/check-behavior/shards/scheduler-28a4f9c293b0fbefcca8/"
    "20261031T205251Z-89bec9c92888/tool-0001/receipt.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--banks", type=int, choices=(1, 2, 4, 8), required=True)
    parser.add_argument("--depth", type=int, choices=(1, 3, 16), required=True)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = Run("evidence/preparation/scheduler-mailbox-repair-" + stamp,
              "registered response availability and handshake regression",
              repair_of=FAILED_RECEIPT)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V"),
                      ("verilator", "--version"), ("g++", "--version")])
        cases = [(args.banks, args.depth, simulator, wrap)
                 for simulator in ("iverilog", "verilator") for wrap in (0, 1, 2)]
        # Execute each complete case, retaining partial progress on the first failure.
        results = []
        for banks, depth, simulator, wrap in cases:
            results.append(scheduler_case(run, banks, depth, simulator, wrap=wrap))
            write_json(run.path / "scheduler-results.json", results)
            print(f"scheduler {len(results)}/{len(cases)} b{banks} q{depth} "
                  f"{simulator} wrap{wrap}", flush=True)
        assert len(results) == 6
        run.finish("passed", result={"cases": results, "required_cases": 6})
    except BaseException as exc:
        run.finish("failed", diagnosis=str(exc))
        raise


if __name__ == "__main__":
    main()
