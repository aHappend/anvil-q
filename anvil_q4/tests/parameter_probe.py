"""Parameter-boundary elaboration, reset and explicit diagnostic comparisons."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT


LEGAL = ((1, 1, 1, 1), (2, 3, 7, 3), (4, 16, 128, 8),
         (8, 1, 7, 8), (16, 16, 128, 1), (16, 3, 7, 3))
ILLEGAL = ((0, 3, 7, 3), (3, 3, 7, 3), (32, 3, 7, 3),
           (1, 0, 7, 3), (1, 17, 7, 3), (1, 3, 0, 3),
           (1, 3, 129, 3), (1, 3, 7, 0), (1, 3, 7, 9))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    args = parser.parse_args()
    experiment = Experiment("parameters", args.preparation)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["iverilog", "-V"], "version")
        experiment.run(["vvp", "-V"], "vvp-version")
        packages = ["rtl/anvil_q3_00_pkg.sv", "rtl/anvil_q4_00_fp_pkg.sv"]
        rtl = packages + [experiment.rel(p) for p in sorted((ROOT/"rtl").glob("*.sv"))
                          if experiment.rel(p) not in packages]
        results = []
        experiment.receipt["comparisons"] = results
        for index, values in enumerate(LEGAL + ILLEGAL):
            legal = index < len(LEGAL)
            parameters = dict(zip(("BANKS", "QUEUE_DEPTH", "TILE_K", "TILE_ROWS"), values))
            binary = experiment.directory / f"parameters-{index}.vvp"
            experiment.run([
                "iverilog", "-g2012", "-Wall", "-s", "startup_tb",
                *[f"-Pstartup_tb.{key}={value}" for key, value in parameters.items()],
                "-o", experiment.rel(binary), *rtl, "tests/startup_tb.sv"],
                f"compile-{index}")
            output = experiment.run(["vvp", experiment.rel(binary)],
                                    f"simulation-{index}", expect_failure=not legal)
            marker = "SUMMARY startup reset_samples=" if legal else "PARAMETER ERROR"
            if marker not in output:
                raise AssertionError(f"missing expected parameter response: {parameters}")
            results.append({"parameters": parameters, "legal": legal,
                            "observation": "reset comparisons" if legal else
                            "explicit nonzero PARAMETER ERROR"})
            experiment.save()
    except (RuntimeError, ValueError, AssertionError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
