"""Bounded evaluation-cost diagnostic; never a functional acceptance result."""

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrated_fast import run_fast_integration
from receipts import ROOT, execute, new_run, relative
from verify import enter_tier


def main():
    enter_tier()
    run = new_run("integration-profile", preparation=True, repair_of=(
        "evidence/preparation/delivery-producers-20261103T044347301602Z/"
        "changed-producers-20261103T044347350047Z/receipt.json"))
    print(f"Profile evidence: {relative(run)}", flush=True)
    summary = run_fast_integration(run, 1, 17, diagnostic=True, profile=True)
    binary = next(run.glob("integrated-clock-driver-compile-binding-*.json"))
    executable = ROOT / json.loads(binary.read_text())["executable"]
    profile = execute(run, "gprof", [
        "gprof", relative(executable), relative(run / "gmon.out")],
        ["gprof", "--version"])
    print(json.dumps({"summary": summary, "profile": relative(profile / "receipt.json")}),
          flush=True)


if __name__ == "__main__":
    main()
