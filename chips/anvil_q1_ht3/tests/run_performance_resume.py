"""Harness-only negative checks on disposable copies of executed observations."""

import argparse
import copy
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, ExecutionFailure, hashes, relative, remaining, timestamp
from retention import digest
from run_compatibility import compiled, fixture
from run_performance import failure_classification, performance_case, validated_simulation


def run(output):
    binary, binding = compiled()
    baseline = performance_case(output, "ht3", binary, binding, 0, 17)
    case = json.loads((ROOT/baseline["case"]).read_text())
    source = ROOT/case["simulation_receipt"]
    original = json.loads(source.read_text())
    rows = []
    mutations = ("none", "timeout", "exit", "source", "tool", "seed", "fixture",
                 "raw_hash", "missing_summary", "missing_completion", "nonfinite")
    for mutation in mutations:
        directory = output/f"copy-{mutation}-{uuid.uuid4().hex[:12]}"
        directory.mkdir()
        vectors, expected = fixture(directory, 0, 17)
        observation = directory/"observations.txt"
        observation.write_bytes((source.parent/"observations.txt").read_bytes())
        record = copy.deepcopy(original)
        record["argv"] = [relative(binary), f"+vectors={relative(vectors)}",
                          f"+observations={relative(observation)}", "+seed=17"]
        record["artifact_sha256"] = {}
        for key in ("stdout", "stderr"):
            target = directory/f"simulation.{key}.txt"
            target.write_bytes((ROOT/original[key]).read_bytes())
            record[key] = relative(target)
            record["artifact_sha256"][relative(target)] = digest(target)
        if mutation == "timeout":
            record["timed_out"] = True
        elif mutation == "exit":
            record["exit"] = 1
        elif mutation == "source":
            record["source_sha256"]["tests/inference_tb.sv"] = "0"*64
        elif mutation == "tool":
            record["tool_version"] = "not the executed tool"
        elif mutation == "seed":
            record["argv"][-1] = "+seed=89"
        elif mutation == "fixture":
            vectors.write_text(vectors.read_text()+"unexpected trailing input\n")
        elif mutation == "raw_hash":
            (ROOT/record["stdout"]).write_text("corrupted diagnostics\n")
        elif mutation == "missing_summary":
            target = ROOT/record["stdout"]
            target.write_text("\n".join(line for line in target.read_text().splitlines()
                                       if not line.startswith("SUMMARY"))+"\n")
            record["artifact_sha256"][relative(target)] = digest(target)
        elif mutation == "missing_completion":
            observation.write_text("\n".join(line for line in observation.read_text().splitlines()
                                            if not line.startswith("T 2 "))+"\n")
        elif mutation == "nonfinite":
            lines = observation.read_text().splitlines()
            index = next(i for i, line in enumerate(lines) if line.startswith("L "))
            parts = lines[index].split()
            parts[-1] = "7fc00000"
            lines[index] = " ".join(parts)
            observation.write_text("\n".join(lines)+"\n")
        path = directory/"synthetic-receipt.json"
        record["diagnostic_copy_only"] = True
        with path.open("x") as out:
            json.dump(record, out, indent=2)
        # Compare with an unmodified regenerated fixture, not the mutated file.
        check_dir = output/f"expected-{mutation}-{uuid.uuid4().hex[:12]}"
        check_dir.mkdir()
        valid_vectors, _ = fixture(check_dir, 0, 17)
        rejection = None
        try:
            accepted = validated_simulation(path, binary, binding, valid_vectors,
                                            0, 17, expected, "ht3") is not None
        except AssertionError as exc:
            accepted, rejection = False, str(exc)
        if accepted != (mutation == "none"):
            raise AssertionError(f"performance retention sensitivity failed: {mutation}")
        rows.append(dict(case=mutation, accepted=accepted, rejection=rejection))
    for launched, category in ((True, "execution_budget_timeout"),
                               (False, "execution_budget_unstarted")):
        error = ExecutionFailure("synthetic budget classification",
                                 dict(timed_out=True, launched=launched))
        if failure_classification(error, "ht3") != category:
            raise AssertionError("budget failure was classified as a DUT failure")
        rows.append(dict(case=category, classification=category))
    return dict(status="passed", scope="retention harness only, not RTL mutation coverage",
                baseline_case=baseline["case"], checks=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_performance_resume.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = run(output)
    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=remaining() <= 0, result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
