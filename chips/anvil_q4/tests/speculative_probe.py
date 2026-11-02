"""Numerical two-token greedy verification through public top-level pins."""

import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment
from system_matrix import compile_top
from transformer_reference import make_fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--accepted", type=int, choices=(0, 1, 2), nargs="+")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("speculative", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["verilator", "--version"], "version")
        binary = compile_top(experiment, driver="speculative_probe.cpp")
        results = []
        experiment.receipt["cases"] = results
        for accepted in args.accepted or (0, 1, 2):
            options = dict(seed=17, heads=3, kv_heads=1, dimension=2,
                           layers=3, tokens=4, vocabulary=17, intermediate=5,
                           page_tokens=1, banks=16, cache_format=accepted % 2,
                           token_ids=[2, None, None, None])
            identity = hashlib.sha256(str((accepted, options)).encode()).hexdigest()[:12]
            directory = experiment.directory / f"case-{identity}"
            directory.mkdir()
            geometry = make_fixture(directory, **options)
            geometry["fixture_sha256"] = {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in directory.glob("*.txt")}
            output = experiment.run([experiment.rel(binary), experiment.rel(directory),
                                     str(accepted)], f"simulation-{accepted}")
            marker = f"SUMMARY speculative accepted={accepted} committed_tokens=4 "
            if marker not in output:
                raise AssertionError("missing numerical speculative comparison summary")
            results.append({**geometry, "accepted": accepted,
                            "summary": output[output.index(marker):].splitlines()[0]})
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
