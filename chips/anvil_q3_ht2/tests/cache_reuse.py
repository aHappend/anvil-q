"""Bounded real-tool regression of compilation reuse, never of simulation results."""

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from arithmetic import run_arithmetic
from integrated_fast import run_fast_integration
from kv_atomic import run_atomic
from receipts import new_run, relative
from verify import enter_tier


FAILURE = (
    "evidence/l1-all-20261102T234418357483Z/"
    "integrated-mode1-1793664874027319183/"
    "integrated-clock-driver-simulate-20261103T002158905077Z/receipt.json"
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integration-path", action="store_true")
    args = parser.parse_args()
    enter_tier()
    run = new_run("compiled-reuse", preparation=True, repair_of=FAILURE)
    results = []
    cases = (
            ("arithmetic-seed17", run_arithmetic, ("verilator", 17, True), {}, False),
            ("arithmetic-seed29", run_arithmetic, ("verilator", 29, True), {}, True),
            ("arithmetic-mutant", run_arithmetic, ("verilator", 17, True),
             {"mutant": True}, False),
            ("atomic-mode1-seed17", run_atomic, (1, 17), {}, False),
            ("atomic-mode1-seed29", run_atomic, (1, 29), {}, True),
            ("atomic-mode2-seed17", run_atomic, (2, 17), {}, False))
    if args.integration_path:
        cases = tuple(
            (f"integration-path-seed{seed}", run_fast_integration, (1, seed),
             {"diagnostic": True, "diagnostic_cycles": 64}, index != 0)
            for index, seed in enumerate((17, 29)))
    for name, function, arguments, kwargs, reused in cases:
        from time import time_ns
        case = run / f"{name}-{time_ns()}"
        case.mkdir()
        observed = function(case, *arguments, **kwargs)
        bindings = list(case.glob("*-binding-*.json"))
        if len(bindings) != 1:
            raise AssertionError("each experiment must have exactly one build binding")
        binding = json.loads(bindings[0].read_text())
        if binding["reused"] is not reused:
            raise AssertionError(f"unexpected compile reuse for {name}")
        results.append({"name": name, "binding": relative(bindings[0]), "result": observed})
    if args.integration_path:
        if results[0]["result"]["model_sha256"] == results[1]["result"]["model_sha256"]:
            raise AssertionError("fresh integration seed did not change model bytes")
        if any(not item["result"]["diagnostic_only"] for item in results):
            raise AssertionError("cache-path experiment must remain diagnostic-only")
    elif results[0]["result"]["vector_sha256"] == results[1]["result"]["vector_sha256"]:
        raise AssertionError("arithmetic seed change did not generate fresh vectors")
    if not args.integration_path and (
            results[3]["result"]["record_sha256"] == results[4]["result"]["record_sha256"]):
        raise AssertionError("atomic seed change did not generate fresh records")
    if not args.integration_path and (
            results[0]["result"]["vector_sha256"] != results[2]["result"]["vector_sha256"]):
        raise AssertionError("mutant and unmodified arithmetic vectors differ")
    summary = run / "cache-reuse-summary.json"
    summary.write_text(json.dumps({"cases": results, "status": "passed"}, indent=2) + "\n")
    print(json.dumps({"summary": relative(summary), "status": "passed"}), flush=True)


if __name__ == "__main__":
    main()
