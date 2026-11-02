"""Compiled legacy modes compared against separately authored integer equations."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment
from legacy_reference import make_fixture
from system_matrix import compile_top


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--case", type=int, nargs="+")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("compatibility", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["verilator", "--version"], "version")
        binary = compile_top(experiment)
        results, index = [], 0
        experiment.receipt["cases"] = results
        for seed in (17, 29, 43):
            for mode, caches in ((1, (0,)), (2, (0, 1)), (3, (0, 1, 2, 3))):
                for cache_format in caches:
                    case = index
                    index += 1
                    if args.case is not None and case not in args.case:
                        continue
                    options = dict(seed=seed, mode=mode, cache_format=cache_format,
                                   banks=(1, 2, 4, 8)[case % 4])
                    identity = hashlib.sha256(json.dumps(options, sort_keys=True).encode()).hexdigest()[:12]
                    directory = experiment.directory / f"case-{case}-{identity}"
                    directory.mkdir()
                    geometry = make_fixture(directory, **options)
                    geometry["fixture_sha256"] = {
                        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in directory.glob("*.txt")}
                    print(f"compatibility case={case} seed={seed} mode={mode} "
                          f"cache={cache_format}", flush=True)
                    output = experiment.run([experiment.rel(binary), experiment.rel(directory)],
                                            f"simulation-{case}")
                    if "SUMMARY top tokens=4 logits=68 " not in output:
                        raise AssertionError("missing exact legacy comparisons")
                    geometry["summary"] = output[output.index("SUMMARY"):].splitlines()[0]
                    results.append(geometry)
                    experiment.save()
        if not results:
            raise AssertionError("no compatibility case executed")
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
