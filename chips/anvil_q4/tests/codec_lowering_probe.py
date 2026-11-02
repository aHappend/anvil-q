"""Bounded process-lowering diagnostic for the legacy packed cache codec."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment
from synthesis_probe import expand_packages


def main():
    experiment = Experiment("codec-lowering", preparation=True, repair_of=[
        "evidence/preparation/synthesis-20261102T115751286843Z/receipt.json"])
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["yosys", "-V"], "version")
        frontend = experiment.directory / "frontend.sv"
        experiment.receipt["frontend_sha256"] = expand_packages(frontend)
        netlist = experiment.directory / "codec.json"
        experiment.run([
            "yosys", "-Q", "-T", "-p",
            f"read_verilog -sv -defer {experiment.rel(frontend)}; "
            "hierarchy -check -top anvil_q3_cache_codec; "
            "proc -ifx; opt_expr; opt_clean; check -assert; "
            "memory -nomap; opt_clean; check -assert; "
            "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod; "
            f"stat; write_json {experiment.rel(netlist)}"], "lowering")
    except (RuntimeError, ValueError, AssertionError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
