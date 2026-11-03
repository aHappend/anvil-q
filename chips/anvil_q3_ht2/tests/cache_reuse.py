"""Bounded real-tool regression of compilation reuse, never of simulation results."""

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from arithmetic import run_arithmetic
from kv_atomic import run_atomic
from receipts import new_run, relative


FAILURE = (
    "evidence/l1-all-20261102T234418357483Z/"
    "integrated-mode1-1793664874027319183/"
    "integrated-clock-driver-simulate-20261103T002158905077Z/receipt.json"
)


def main():
    run = new_run("compiled-reuse", preparation=True, repair_of=FAILURE)
    results = []
    for name, function, args, kwargs, reused in (
            ("arithmetic-seed17", run_arithmetic, ("verilator", 17, True), {}, False),
            ("arithmetic-seed29", run_arithmetic, ("verilator", 29, True), {}, True),
            ("arithmetic-mutant", run_arithmetic, ("verilator", 17, True),
             {"mutant": True}, False),
            ("atomic-mode1-seed17", run_atomic, (1, 17), {}, False),
            ("atomic-mode1-seed29", run_atomic, (1, 29), {}, True),
            ("atomic-mode2-seed17", run_atomic, (2, 17), {}, False)):
        from time import time_ns
        case = run / f"{name}-{time_ns()}"
        case.mkdir()
        observed = function(case, *args, **kwargs)
        bindings = list(case.glob("*-binding-*.json"))
        if len(bindings) != 1:
            raise AssertionError("each experiment must have exactly one build binding")
        binding = json.loads(bindings[0].read_text())
        if binding["reused"] is not reused:
            raise AssertionError(f"unexpected compile reuse for {name}")
        results.append({"name": name, "binding": relative(bindings[0]), "result": observed})
    if results[0]["result"]["vector_sha256"] == results[1]["result"]["vector_sha256"]:
        raise AssertionError("arithmetic seed change did not generate fresh vectors")
    if results[3]["result"]["record_sha256"] == results[4]["result"]["record_sha256"]:
        raise AssertionError("atomic seed change did not generate fresh records")
    if results[0]["result"]["vector_sha256"] != results[2]["result"]["vector_sha256"]:
        raise AssertionError("mutant and unmodified arithmetic vectors differ")
    summary = run / "cache-reuse-summary.json"
    summary.write_text(json.dumps({"cases": results, "status": "passed"}, indent=2) + "\n")
    print(json.dumps({"summary": relative(summary), "status": "passed"}), flush=True)


if __name__ == "__main__":
    main()
