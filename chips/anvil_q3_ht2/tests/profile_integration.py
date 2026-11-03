"""Bounded evaluation-cost diagnostic; never a functional acceptance result."""

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrated_fast import run_fast_integration
from receipts import ROOT, execute, new_run, relative
from verify import enter_tier


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--cycles", type=int, default=262144)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--layers", type=int, default=36)
    parser.add_argument("--repair-of")
    parser.add_argument("--flat", action="store_true")
    parser.add_argument("--complete", action="store_true")
    parser.add_argument("--mode", type=int, choices=(1, 2), default=1)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    if args.cycles <= 0 or not 1 <= args.layers <= 36:
        parser.error("cycles must be positive and layers must be in 1..36")
    enter_tier()
    run = new_run("integration-profile", preparation=True, repair_of=args.repair_of)
    print(f"Profile evidence: {relative(run)}", flush=True)
    summary = run_fast_integration(run, args.mode, args.seed,
                                   diagnostic=not args.complete, profile=args.profile,
                                   diagnostic_cycles=args.cycles,
                                   layers=args.layers, compact=args.compact,
                                   flat=args.flat)
    result = {"summary": summary}
    if args.profile:
        binary = next(run.glob("integrated-clock-driver-compile-binding-*.json"))
        executable = ROOT / json.loads(binary.read_text())["executable"]
        profile = execute(run, "gprof", [
            "gprof", relative(executable), relative(run / "gmon.out")],
            ["gprof", "--version"])
        result["profile"] = relative(profile / "receipt.json")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
