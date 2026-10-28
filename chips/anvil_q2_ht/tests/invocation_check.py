"""Synthetic entrypoint namespace regression; no accelerator acceptance claims."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
from uuid import UUID

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from invocation import invocation_experiment
from retention import Experiment


BINDING_ENTRY = """
import sys
from unittest.mock import patch
sys.path.insert(0, "tests")
import input_binding_check as entry
fail = sys.argv.pop(1) == "fail"
def regression(experiment):
    if fail:
        raise RuntimeError("deliberate invocation failure")
# Prevent only this regression's recursion; execute the real 22-case worker.
with patch.object(entry, "run_regression", regression):
    raise SystemExit(entry.main())
"""

SCHEDULING_ENTRY = """
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, "tests")
import scheduling_check as entry
fail = sys.argv.pop(1) == "fail"
def workload(experiment):
    output = experiment.output
    cache = output / "verilator-builds"
    entry.create_cache(experiment.root, cache)
    rows = entry.planned_l1_checks(experiment)
    for row in rows:
        assert Path(row["receipt"]).is_relative_to(output)
        if "--output" in row["argv"]:
            assert Path(row["argv"][row["argv"].index("--output") + 1]).is_relative_to(output)
        if "--build-cache" in row["argv"]:
            assert row["argv"][row["argv"].index("--build-cache") + 1] == str(cache)
    names = {row["check"] for row in rows}
    assert {"default-synthesis", "D5-common-service-benchmark",
            "five-domain-ledger-recomparison"} <= names
    data = output / "fresh-work.json"
    experiment.run([sys.executable, "-B", "-c",
                    "from pathlib import Path; import sys; "
                    "Path(sys.argv[1]).open('x').write('17'); print('FRESH_WORK')",
                    str(data)], "fresh-worker")
    text = experiment.run([sys.executable, "-B", "-c",
                           "from pathlib import Path; import sys; "
                           "assert Path(sys.argv[1]).read_text() == '17'; "
                           "print('DEPENDENT_COMPARED'); "
                           "raise SystemExit(int(sys.argv[2]))",
                           str(data), "7" if fail else "0"], "dependent-reader")
    assert "DEPENDENT_COMPARED" in text
    experiment.receipt["synthetic_namespace_comparison"] = {
        "data": str(data), "build_cache": str(cache),
        "matrix_rows": len(rows), "compared_value": 17}
# Exercise actual critical-path dispatch, not expensive RTL/synthesis workloads.
with patch.object(entry, "critical_path", workload):
    raise SystemExit(entry.main())
"""


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def contents(directory):
    return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob("*") if path.is_file()}


def entrypoint_cases(experiment):
    count = 0
    for name, script, options in (
            ("binding", BINDING_ENTRY, []),
            ("critical-path", SCHEDULING_ENTRY, ["--scope", "critical-path"])):
        parent = experiment.output / name
        directory = experiment.root / parent
        directory.mkdir()
        for filename, data in (
                ("receipt.json", b'{"retained_original":true}\n'),
                ("original.stdout", b"retained stdout\n"),
                ("original.stderr", b"retained stderr\n")):
            with (directory / filename).open("xb") as stream:
                stream.write(data)
        original_hash = hashlib.sha256((directory / "receipt.json").read_bytes()).hexdigest()
        seen = set()
        for index, fail in enumerate((False, False, True, False)):
            before = contents(directory)
            label = name + "-" + str(index)
            text = experiment.run(
                [sys.executable, "-B", "-c", script, "fail" if fail else "pass",
                 "--output", str(parent), *options],
                label, allow_mismatch=True)
            command = experiment.receipt["commands"][-1]
            require(command["exit"] == (1 if fail else 0) and not command["timed_out"],
                    label + ": wrong entrypoint result")
            after = contents(directory)
            require(all(after.get(path) == digest for path, digest in before.items()),
                    label + ": earlier evidence changed")
            added = set(after) - set(before)
            children = {Path(path).parts[0] for path in added}
            require(len(children) == 1, label + ": not exactly one fresh invocation")
            child = children.pop()
            require(child.startswith("invocation-") and child not in seen,
                    label + ": reused invocation")
            seen.add(child)
            resolved = parent / child
            receipt_path = resolved / "receipt.json"
            require(str(receipt_path) in text.splitlines(),
                    label + ": result reader cannot discover exact receipt")
            receipt = json.loads((experiment.root / receipt_path).read_text())
            require(receipt["exit"] == (1 if fail else 0), label + ": receipt exit")
            require(receipt["invocation"] == {
                "parent_output": str(parent), "output": str(resolved),
                "original_receipt": {"path": str(parent / "receipt.json"),
                                     "sha256": original_hash},
            }, label + ": parent/original relationship")
            require(bool(receipt["commands"]), label + ": no fresh execution")
            for child_command in receipt["commands"]:
                for key in ("stdout", "stderr"):
                    require(Path(child_command[key]).is_relative_to(resolved),
                            label + ": logs escaped resolved output")
                    require((experiment.root / child_command[key]).is_file(),
                            label + ": missing raw log")
            if name == "binding":
                worker = next(row for row in receipt["commands"]
                              if "--worker" in row["argv"])
                require(worker["argv"][worker["argv"].index("--output") + 1] == str(resolved),
                        label + ": worker received old parent")
                require(worker["exit"] == 0 and receipt["compared_cases"] == 22,
                        label + ": original comparisons did not execute")
                require("SYNTHETIC_BINDING_CASES 22 NO_RTL_EXECUTED" in
                        (experiment.root / worker["stdout"]).read_text(),
                        label + ": missing original comparison counter")
                if fail:
                    require(receipt["failure"] == "deliberate invocation failure",
                            label + ": injected failure not retained")
            else:
                require((experiment.root / resolved / "fresh-work.json").read_text() == "17",
                        label + ": worker did not produce fresh data")
                dependent = receipt["commands"][-1]
                require(dependent["exit"] == (7 if fail else 0) and
                        "DEPENDENT_COMPARED" in
                        (experiment.root / dependent["stdout"]).read_text(),
                        label + ": dependent comparison/failure not executed")
                if fail:
                    require("dependent-reader failed; see" in receipt["failure"],
                            label + ": child failure not retained")
                else:
                    comparison = receipt["synthetic_namespace_comparison"]
                    require(comparison["data"] == str(resolved / "fresh-work.json") and
                            comparison["build_cache"] == str(resolved / "verilator-builds") and
                            comparison["matrix_rows"] > 0,
                            label + ": stale dependent/cache/matrix path")
            experiment.receipt.setdefault("entrypoint_cases", []).append({
                "entrypoint": name, "outcome": "expected-failure" if fail else "passed",
                "receipt": str(receipt_path), "prior_files_unchanged": len(before),
            })
            count += 1
            print("CHECK", label, "pass")

    parent = experiment.output / "collision"
    with patch("invocation.uuid.uuid4", return_value=UUID(int=0)):
        first = invocation_experiment(experiment.root, parent, ["synthetic"], [])
        require(first.receipt["invocation"]["original_receipt"] is None,
                "new parent invented an original receipt")
        first.finish(0)
        before = contents(first.directory)
        try:
            invocation_experiment(experiment.root, parent, ["must-not-reuse"], [])
        except FileExistsError:
            pass
        else:
            raise RuntimeError("exclusive invocation collision accepted")
        require(contents(first.directory) == before, "collision changed original invocation")
    count += 1
    require(count == 9, "missing invocation regression cases")
    experiment.receipt["compared_cases"] = count
    experiment.receipt["scope"] = (
        "synthetic namespace/retention only; real entrypoint dispatch and binding workers; "
        "critical-path RTL/synthesis workload replaced by explicit synthetic work")
    print("INVOCATION_CASES", count, "NO_RTL_EXECUTED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    experiment = Experiment(root, args.output, sys.orig_argv, [
        "tests/invocation_check.py", "tests/invocation.py", "tests/input_binding_check.py",
        "tests/scheduling_check.py", "tests/retention.py", "tests/scheduling.py",
        "tests/verify.py", "tests/build_cache.py", "tests/binding_diagnosis.py",
        "tests/README.md"])
    try:
        experiment.run([sys.executable, "--version"], "python-version")
        entrypoint_cases(experiment)
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, AssertionError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
