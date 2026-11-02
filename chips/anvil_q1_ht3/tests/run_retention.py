"""Exercise evidence reuse and rejection without rerunning numerical failures."""

import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp
from retention import find_result, inventory, validated_result
from verify import TOOLS, dependencies


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_retention.py", *sys.argv[1:]],
                   cwd=".", start=timestamp(), timeout=remaining(),
                   source_sha256=hashes(), tool_version=sys.version)
    versions = inventory(output, TOOLS)
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
        observed.append(dict(argv=argv, status=result["status"], receipt=bound["receipt"],
                             source_rejection=True, tool_rejection=True,
                             argv_rejection=True))
    result = dict(status="passed", kind="retention-validator-diagnostic",
                  comparisons=len(observed) * 4, observations=observed)
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
