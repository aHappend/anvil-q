"""Exercise evidence reuse and rejection without rerunning numerical failures."""

import argparse
import ast
import json
from pathlib import Path
import sys
from unittest.mock import patch
import os
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import CHECK_SECONDS, ROOT, hashes, relative, remaining, timestamp
from retention import find_result, inventory, validated_result
from verify import (OBLIGATIONS, REPRODUCTION_BUDGET, SETTLEMENT_RESERVE, TOOLS,
                    child, dependencies, schedule)
from run_synthesis import JOBS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_retention.py", *sys.argv[1:]],
                   cwd=".", start=timestamp(), timeout=remaining(),
                   source_sha256=hashes(), tool_version=sys.version)
    parsed_sources = []
    for path in sorted((ROOT / "tests").glob("*.py")):
        ast.parse(path.read_text(), filename=relative(path))
        parsed_sources.append(relative(path))
    versions = inventory(output, TOOLS)
    jobs = schedule()
    identifiers = [job[0] for job in jobs]
    required = (set(OBLIGATIONS)-{"synthesis"}) | {
        f"synthesis-{entry[0]}" for entry in JOBS}
    if not required.issubset(identifiers) or len(identifiers) != len(set(identifiers)):
        raise AssertionError("scheduling lost or duplicated a mandatory obligation")
    if (jobs[0][0] != "reproduction" or jobs[0][2] != REPRODUCTION_BUDGET
            or CHECK_SECONDS - SETTLEMENT_RESERVE < REPRODUCTION_BUDGET
            or any(not 0 < minimum <= budget <= CHECK_SECONDS
                   for _, _, budget, minimum in jobs)):
        raise AssertionError("fresh reproduction cannot receive its full cold-compile budget")
    observed = []
    for script, options, failed in (
            ("tests/run_unit.py", ["--suite", "primitive", "--simulator", "verilator",
                                  "--seed", "17"], False),
            ("tests/run_unit.py", ["--suite", "quantizer", "--simulator", "icarus",
                                  "--seed", "17"], False),
            ("tests/run_epilogue.py", ["--seed", "17"], True),
            ("tests/run_epilogue.py", ["--seed", "89"], True),
            ("tests/run_epilogue.py", ["--seed", "2026"], True)):
        argv = ["python3", script, *options]
        deps = dependencies(script)
        bound = find_result(argv, deps, versions, allow_failure=failed)
        if bound is None:
            raise AssertionError(f"complete matched result not reusable: {argv}")
        result = bound["result"]
        if result["status"] != ("failed" if failed else "passed"):
            raise AssertionError("retention changed a genuine outcome")
        if failed and len(result["failures"]) != 4:
            raise AssertionError("retention lost original numerical failures")
        stale = dict(hashes())
        stale[deps[0]] = "0" * 64
        with patch("retention.hashes", return_value=stale):
            if validated_result(ROOT / bound["result_path"], argv, deps, versions,
                                allow_failure=failed) is not None:
                raise AssertionError("stale source accepted")
        bad_versions = {**versions, "iverilog": "different-version",
                        "verilator": "different-version"}
        if validated_result(ROOT / bound["result_path"], argv, deps, bad_versions,
                            allow_failure=failed) is not None:
            raise AssertionError("different simulator version accepted")
        if validated_result(ROOT / bound["result_path"], argv + ["--unrecognized"],
                            deps, versions, allow_failure=failed) is not None:
            raise AssertionError("different argv/coverage accepted")
        with patch("retention.digest", return_value="0" * 64):
            if validated_result(ROOT / bound["result_path"], argv, deps, versions,
                                allow_failure=failed) is not None:
                raise AssertionError("corrupt raw output accepted")
        observed.append(dict(argv=argv, status=result["status"], receipt=bound["receipt"],
                             source_rejection=True, tool_rejection=True,
                             argv_rejection=True, artifact_rejection=True))
    previous_deadline = os.environ.get("HT3_CHECK_DEADLINE")
    outer_deadline = time.time() + 100
    os.environ["HT3_CHECK_DEADLINE"] = str(outer_deadline)

    def synthetic_child(argv, parent, identifier, version_argv):
        remaining_allocation = float(os.environ["HT3_CHECK_DEADLINE"]) - time.time()
        if not 39 <= remaining_allocation <= 40:
            raise AssertionError("child consumed reserved execution budget")
        directory = ROOT / argv[argv.index("--output") + 1]
        directory.mkdir()
        with (directory / "result.json").open("x") as out:
            json.dump(dict(status="passed", coverage_limits=["synthetic diagnostic only"]), out)
        return ""

    try:
        with patch("verify.execute", side_effect=synthetic_child):
            row = child("synthetic-reserve", ["tests/synthetic-not-an-rtl-run.py"], output,
                        budget=90, reserve=60)
        if row["status"] != "incomplete" or float(os.environ["HT3_CHECK_DEADLINE"]) != outer_deadline:
            raise AssertionError("coverage or outer budget changed by child scheduling")
    finally:
        if previous_deadline is None:
            os.environ.pop("HT3_CHECK_DEADLINE", None)
        else:
            os.environ["HT3_CHECK_DEADLINE"] = previous_deadline
    result = dict(status="passed", kind="retention-validator-diagnostic",
                  comparisons=len(observed) * 5 + 4, observations=observed,
                  synthetic_reserve_observation=row, parsed_sources=parsed_sources)
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=0, timed_out=False,
                   result=relative(output / "result.json"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
