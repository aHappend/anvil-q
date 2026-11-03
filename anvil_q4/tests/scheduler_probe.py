"""Concurrent bank/tag ownership with stalls, reordering and same-edge responses."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--depth", type=int, choices=(1, 3, 16), nargs="+")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("scheduler", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["verilator", "--version"], "version")
        results = []
        experiment.receipt["cases"] = results
        for depth in args.depth or (1, 3, 16):
            objects = experiment.directory/"compile-obj"
            prefix = "../../../../tests/" if args.preparation else "../../../tests/"
            experiment.run([
                "verilator", "--cc", "--exe", "--build", "--verilate-jobs", "1",
                "--build-jobs", "2", "-Wno-fatal",
                "--top-module", "anvil_q4_bank_scheduler", "--Mdir", experiment.rel(objects),
                "-GBANKS=16", "-GCLIENTS=24", f"-GQUEUE_DEPTH={depth}",
                "-CFLAGS", "-std=c++17", "-o", "scheduler-sim",
                "rtl/anvil_q4_bank_scheduler.sv", prefix+"scheduler_probe.cpp"],
                f"compile-{depth}")
            output = experiment.run([experiment.rel(objects/"scheduler-sim"), str(depth)],
                                    f"simulation-{depth}")
            marker = f"SUMMARY scheduler queue_depth={depth} transactions=480 "
            if marker not in output:
                raise AssertionError("missing public scheduler comparison/coverage summary")
            results.append({"queue_depth": depth, "summary": output.strip()})
            experiment.save()
            experiment.prune_objects(objects)
    except (RuntimeError, ValueError, AssertionError, KeyError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
