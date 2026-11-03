"""Synthetic reclamation/allocation/retry checks, not hardware acceptance."""

import argparse
import ast
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp
from retention import artifacts_intact, digest, execution_logs_intact
from run_mutations import trial
from verify import MINIMUM_ALLOCATIONS, child, schedule


def run(output):
    assertions = 0
    names = ("netlist.json", "synthesis.stdout.txt", "synthesis.stderr.txt",
             "executable", "driver.cpp")
    artifacts = {}
    for name in names:
        path = output / name
        path.write_text(f"synthetic {name}\n")
        artifacts[relative(path)] = digest(path)
    record = dict(stdout=relative(output/names[1]), stderr=relative(output/names[2]),
                  artifact_sha256=artifacts)
    if not artifacts_intact(artifacts) or not execution_logs_intact(record):
        raise AssertionError("complete synthetic artifacts rejected")
    assertions += 1
    for name in names:
        path = output/name
        original = path.read_bytes()
        # Synthetic candidates only; never remove retained execution evidence.
        path.unlink()
        if artifacts_intact(artifacts):
            raise AssertionError(f"reclaimed {name} accepted")
        if "stderr" in name or "stdout" in name:
            if execution_logs_intact(record):
                raise AssertionError("reclaimed raw log accepted")
        path.write_bytes(original)
        assertions += 1
    omitted = {p: sha for p, sha in artifacts.items() if not p.endswith("driver.cpp")}
    if artifacts_intact(omitted, artifacts):
        raise AssertionError("omitted required driver accepted")
    assertions += 1
    previous = os.environ.get("HT3_CHECK_DEADLINE")
    try:
        deadline = time.time()+70
        os.environ["HT3_CHECK_DEADLINE"] = str(deadline)
        for identifier in ("integrated_geometry", "parameters", "mutations",
                           "stream_checkpoint", "benchmarks"):
            with patch("verify.execute", side_effect=AssertionError("must not launch")):
                row = child(identifier, [f"tests/run_{identifier}.py"], output,
                            budget=1800, reserve=30,
                            minimum=MINIMUM_ALLOCATIONS[identifier])
            if (row["status"] != "not_started"
                    or row["failure_kind"] != "execution_budget_unstarted"
                    or float(os.environ["HT3_CHECK_DEADLINE"]) != deadline):
                raise AssertionError("insufficient allocation launched or reset the deadline")
            assertions += 1
        os.environ["HT3_CHECK_DEADLINE"] = str(time.time()+600)

        def sufficient(argv, parent, identifier, version):
            allocation = float(os.environ["HT3_CHECK_DEADLINE"])-time.time()
            if not 350 < allocation <= 360:
                raise AssertionError("useful cold compilation allocation not preserved")
            directory = ROOT/argv[argv.index("--output")+1]
            directory.mkdir()
            (directory/"result.json").write_text(json.dumps(dict(status="passed")))

        with patch("verify.execute", side_effect=sufficient):
            row = child("synthetic-useful", ["tests/not-hardware.py"], output,
                        budget=360, reserve=30, minimum=300)
        if row["status"] != "passed":
            raise AssertionError("useful allocation rejected")
        assertions += 1
    finally:
        if previous is None:
            os.environ.pop("HT3_CHECK_DEADLINE", None)
        else:
            os.environ["HT3_CHECK_DEADLINE"] = previous
    seen = []

    def failed_baseline(argv, parent, stem, version, root):
        if stem in seen:
            raise AssertionError("retry would collide with immutable prior outputs")
        seen.append(stem)
        directory = root/argv[argv.index("--output")+1]
        directory.mkdir(parents=True)
        (directory/"case-result.json").write_text(json.dumps(dict(status="failed")))
        (directory/"case.receipt.json").write_text(json.dumps(dict(timed_out=False)))
        raise RuntimeError("deliberate synthetic baseline rejection")

    disposable = output/"synthetic-bundle"
    disposable.mkdir()
    with patch("run_mutations.execute", side_effect=failed_baseline):
        for _ in range(2):
            _, result, error = trial(output, disposable, "baseline-epilogue", "epilogue")
            if result["status"] != "failed" or error is None:
                raise AssertionError("failed baseline became success")
            assertions += 1
    if len(set(seen)) != 2:
        raise AssertionError("failed baseline retry names not unique")
    assertions += 1
    if len({j[0] for j in schedule()}) != len(schedule()):
        raise AssertionError("duplicate mandatory job")
    assertions += 1
    for path in (ROOT/"tests").glob("*.py"):
        ast.parse(path.read_text(), filename=relative(path))
    return dict(status="passed", kind="synthetic-harness-regression",
                assertions=assertions, cases=list(names),
                scope="cache rejection, launch allocation and immutable retry naming only")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_harness_regression.py", *sys.argv[1:]],
                   cwd=".", start=timestamp(), timeout=remaining(),
                   source_sha256=hashes(), tool_version=sys.version)
    result = run(output)
    (output/"result.json").write_text(json.dumps(result, indent=2))
    receipt.update(exit=0, timed_out=False, end=timestamp(),
                   result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
