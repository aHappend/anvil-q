#!/usr/bin/env python3
"""Portable L1 entrypoint. Each selected suite has a 2700-second whole-check budget."""

import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT


SUITES = {
    "smoke": [
        ["startup_probe.py"], ["parameter_probe.py"], ["descriptor_probe.py"],
        ["top_smoke.py"]],
    "arithmetic": [
        ["arithmetic_probe.py", "--samples", "10000"],
        ["numerics_probe.py"],
        *[["tensor_probe.py", "--lanes", str(lanes)] for lanes in (1, 2, 4, 8, 16)]],
    "system": [
        ["system_matrix.py"], ["cache_probe.py", "--simulator", "verilator"],
        ["protocol_probe.py"], ["speculative_probe.py"], ["scheduler_probe.py"],
        ["full_shape_probe.py"]],
    "compatibility": [
        ["codec_equivalence.py"], ["compatibility_probe.py"], ["switching_probe.py"],
        ["compatibility_probe.py", "--frontend-normalization", "--case", "0", "2", "6"]],
    "benchmarks": [["benchmarks.py"]],
    "mutations": [["mutation_probe.py"]],
    "synthesis": [["synthesis_probe.py"]],
    "portable": [["portable.py"]],
}


def execute(suite):
    experiment = Experiment("l1-"+suite)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["python3", "--version"], "version")
        children = []
        experiment.receipt["subchecks"] = children
        for index, command in enumerate(SUITES[suite]):
            print(f"L1 {suite}: {command[0]}", flush=True)
            output = experiment.run(["python3", "tests/"+command[0], *command[1:]],
                                    f"check-{index}", timeout=2700)
            paths = re.findall(r"^evidence/(?:preparation/)?[^\s]+/receipt\.json$", output, re.M)
            if len(paths) != 1:
                raise AssertionError("subcheck did not retain exactly one execution receipt")
            receipt = json.loads((ROOT/paths[0]).read_text())
            if receipt["exit_code"] != 0:
                raise AssertionError("subcheck receipt contradicts child exit")
            children.append({"command": command, "receipt": paths[0]})
            experiment.save()
    except (RuntimeError, ValueError, AssertionError, KeyError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=SUITES)
    args = parser.parse_args()
    failures = 0
    for suite in ([args.suite] if args.suite else SUITES):
        failures += execute(suite)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
