"""Directed public command errors, cancellation phases and transaction drain."""

import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment
from system_matrix import compile_top
from transformer_reference import make_fixture


CASES = ("invalid-token", "invalid-position", "memory-error", "cancel-idle",
         "cancel-issuing", "cancel-waiting", "cancel-output", "cancel-verifying")
CASES += ("normal-priority", "reset-outstanding")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--case", choices=CASES, action="append")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("protocol", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["verilator", "--version"], "version")
        binary = compile_top(experiment, driver="protocol_probe.cpp")
        identity = hashlib.sha256(b"protocol-compact17").hexdigest()[:12]
        directory = experiment.directory/f"fixture-{identity}"
        directory.mkdir()
        experiment.receipt["geometry"] = make_fixture(
            directory, seed=17, heads=3, kv_heads=1, dimension=2,
            layers=3, tokens=4, intermediate=5, vocabulary=17, page_tokens=1)
        experiment.receipt["fixture_sha256"] = {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.glob("*.txt")}
        results = []
        experiment.receipt["cases"] = results
        for case in args.case or CASES:
            output = experiment.run([experiment.rel(binary), experiment.rel(directory), case],
                                    "simulation-"+case)
            marker = "SUMMARY protocol scenario="+case+" "
            if marker not in output:
                raise AssertionError("missing protocol conservation/error comparisons")
            results.append({"case": case, "summary": output[output.index(marker):].splitlines()[0]})
            experiment.save()
        experiment.prune_objects(binary.parent)
    except (RuntimeError, ValueError, AssertionError, KeyError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
