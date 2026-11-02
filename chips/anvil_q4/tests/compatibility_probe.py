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
from synthesis_probe import expand_packages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--case", type=int, nargs="+")
    parser.add_argument("--repair-of", action="append", default=[])
    parser.add_argument("--frontend-normalization", action="store_true")
    parser.add_argument("--workers", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    experiment = Experiment("compatibility", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["verilator", "--version"], "version")
        rtl_sources = None
        if args.frontend_normalization:
            frontend = experiment.directory/"frontend.sv"
            experiment.receipt["frontend_sha256"] = expand_packages(
                frontend, indexed_write_lowering=True)
            rtl_sources = [experiment.rel(frontend)]
        binary = compile_top(experiment, rtl_sources=rtl_sources)
        results, index = [], 0
        experiment.receipt["cases"] = results
        selected = []
        for seed in (17, 29, 43):
            for mode, caches in ((1, (0,)), (2, (0, 1)), (3, (0, 1, 2, 3))):
                for cache_format in caches:
                    case = index
                    index += 1
                    if args.case is not None and case not in args.case:
                        continue
                    options = dict(seed=seed, mode=mode, cache_format=cache_format,
                                   banks=(1, 2, 4, 8)[case % 4])
                    selected.append((case, options))
        experiment.receipt["case_workers"] = args.workers

        def execute(item):
            case, options = item
            identity = hashlib.sha256(json.dumps(options, sort_keys=True).encode()).hexdigest()[:12]
            directory = experiment.directory / f"case-{case}-{identity}"
            directory.mkdir()
            geometry = make_fixture(directory, **options)
            geometry["case_index"] = case
            geometry["fixture_sha256"] = {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in directory.glob("*.txt")}
            print(f"compatibility case={case} seed={options['seed']} mode={options['mode']} "
                  f"cache={options['cache_format']}", flush=True)
            output = experiment.run([experiment.rel(binary), experiment.rel(directory)],
                                    f"simulation-{case}")
            if "SUMMARY top tokens=4 logits=68 " not in output:
                raise AssertionError("missing exact legacy comparisons")
            geometry["summary"] = output[output.index("SUMMARY"):].splitlines()[0]
            return geometry

        for geometry in experiment.map(execute, selected, args.workers):
            experiment.append_result("cases", geometry)
        if len(results) != len(selected):
            raise AssertionError("missing selected compatibility cases")
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
