"""Strict public-pin time-zero and both-edge asynchronous-reset experiment."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("startup", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["iverilog", "-V"], "iverilog-version")
        experiment.run(["vvp", "-V"], "vvp-version")
        packages = ["rtl/anvil_q3_00_pkg.sv", "rtl/anvil_q4_00_fp_pkg.sv"]
        rtl = packages + [experiment.rel(p) for p in sorted((ROOT/"rtl").glob("*.sv"))
                          if experiment.rel(p) not in packages]
        binary = experiment.directory/"startup.vvp"
        experiment.run(["iverilog", "-g2012", "-Wall", "-s", "startup_tb",
                        "-o", experiment.rel(binary), *rtl,
                        "tests/startup_tb.sv"], "compile")
        output = experiment.run(["vvp", experiment.rel(binary)], "simulation")
        if "SUMMARY startup reset_samples=" not in output:
            raise AssertionError("missing public-reset comparisons")
    except (RuntimeError, ValueError, AssertionError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
