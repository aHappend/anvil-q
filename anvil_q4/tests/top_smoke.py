"""Compact single-token, four-state Icarus numerical and public-protocol smoke."""

import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT
from transformer_reference import make_fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("token-smoke", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["geometry"] = make_fixture(
            experiment.directory, layers=1, tokens=1, heads=1, kv_heads=1,
            dimension=2, intermediate=1, vocabulary=1, banks=1, tile_k=1,
            context_capacity=1, physical_pages=1, page_base=0)
        experiment.receipt["fixture_sha256"] = {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in experiment.directory.glob("*.txt")}
        experiment.receipt["tool_version"] = experiment.run(["iverilog", "-V"], "version")
        experiment.run(["vvp", "-V"], "vvp-version")
        packages = ["rtl/anvil_q3_00_pkg.sv", "rtl/anvil_q4_00_fp_pkg.sv"]
        rtl = packages + [experiment.rel(p) for p in sorted((ROOT/"rtl").glob("*.sv"))
                          if experiment.rel(p) not in packages]
        binary = experiment.directory / "smoke.vvp"
        experiment.run(["iverilog", "-g2012", "-Wall", "-s", "top_smoke_tb",
                        "-o", experiment.rel(binary), *rtl,
                        "tests/top_smoke_tb.sv"], "compile")
        output = experiment.run(["vvp", experiment.rel(binary),
                                 "+FIXTURE="+experiment.rel(experiment.directory)], "simulation")
        if "SUMMARY smoke tokens=1 logits=1 stages=" not in output:
            raise AssertionError("missing compact Icarus numerical comparisons")
    except (RuntimeError, ValueError, AssertionError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
