"""Compact compiled multi-architecture numerical integration matrix."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT
from transformer_reference import make_fixture


def cases():
    for seed in (17, 29, 43):
        for index, ratio in enumerate((1, 3, 6, 7, 8)):
            yield dict(seed=seed, heads=ratio, kv_heads=1, dimension=2,
                       layers=3, tokens=4, intermediate=5, vocabulary=17,
                       activation_format=index % 2, bias=index % 2 == 0,
                       banks=(1, 2, 4, 8, 16)[index], page_tokens=2 if index % 2 else 1,
                       weight_format=(0, 1, 2, 1, 2)[index],
                       activation_a8=index >= 3, asymmetric=index % 2 == 0)
        yield dict(seed=seed, heads=4, kv_heads=4, dimension=16,
                   layers=3, tokens=4, intermediate=7, vocabulary=17,
                   activation_format=1, bias=False, banks=16, page_tokens=32)
    for ratio, theta in ((7, 1000000), (6, 10000)):
        yield dict(seed=17, heads=ratio, kv_heads=1, dimension=2,
                   layers=28, tokens=4, intermediate=5, vocabulary=17,
                   activation_format=0, bias=True, banks=16, page_tokens=2,
                   theta_value=theta)
    yield dict(seed=17, heads=1, kv_heads=1, dimension=2, layers=1,
               tokens=1, intermediate=1, vocabulary=1, activation_format=0,
               bias=False, banks=1, page_tokens=1)


def compile_top(experiment, banks=16, tile_k=7, tile_rows=3, queue_depth=3):
    objects = experiment.directory / "compile-obj"
    packages = ["rtl/anvil_q3_00_pkg.sv", "rtl/anvil_q4_00_fp_pkg.sv"]
    rtl = packages + [experiment.rel(p) for p in sorted((ROOT/"rtl").glob("*.sv"))
                      if experiment.rel(p) not in packages]
    experiment.run([
        "verilator", "--cc", "--exe", "--build", "--verilate-jobs", "1",
        "--build-jobs", "2", "-Wno-fatal",
        "--top-module", "anvil_q4_top", "--Mdir", experiment.rel(objects),
        f"-GBANKS={banks}", f"-GQUEUE_DEPTH={queue_depth}",
        f"-GTILE_K={tile_k}", f"-GTILE_ROWS={tile_rows}",
        "-CFLAGS", "-std=c++17", "-o", "top-sim", *rtl,
        str(Path("../../../../tests/top_probe.cpp") if
            experiment.directory.parent.name == "preparation" else
            Path("../../../tests/top_probe.cpp")),
    ], "compile", timeout=600)
    return objects / "top-sim"


def execute_case(experiment, binary, options, index):
    identity = hashlib.sha256(json.dumps(options, sort_keys=True).encode()).hexdigest()[:12]
    directory = experiment.directory / f"case-{index}-{identity}"
    directory.mkdir()
    geometry = make_fixture(directory, **options)
    (directory/"seed.txt").write_text(str(options["seed"])+"\n")
    geometry["fixture_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in directory.glob("*.txt")
    }
    output = experiment.run([experiment.rel(binary), experiment.rel(directory)],
                            f"simulation-{index}", timeout=600)
    expected = f"SUMMARY top tokens={geometry['tokens']} logits={geometry['expected_logits']} "
    if expected not in output:
        raise AssertionError(f"missing numerical summary for case {index}")
    geometry["summary"] = output[output.index("SUMMARY"):].splitlines()[0]
    return geometry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--case", type=int)
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("system-matrix", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(
            ["verilator", "--version"], "version").strip()
        binary = compile_top(experiment)
        results = []
        experiment.receipt["cases"] = results
        for index, options in enumerate(cases()):
            if args.case is not None and args.case != index:
                continue
            print(f"system case={index} seed={options['seed']} hidden="
                  f"{options['heads']*options['dimension']}", flush=True)
            results.append(execute_case(experiment, binary, options, index))
            experiment.save()
        if not results:
            raise AssertionError("no system cases executed")
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
