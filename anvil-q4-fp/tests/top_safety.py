"""Bounded four-state top startup and safely diagnosed illegal geometries."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative


def run(preparation=False, repair_of=None):
    directory = new_run("top-safety", preparation)
    geometries = (
        ("legal-minimum", (1, 1, 1, 1)),
        ("banks-zero", (0, 1, 1, 1)), ("banks-nonpower", (3, 1, 1, 1)),
        ("banks-immediate-upper", (17, 1, 1, 1)),
        ("banks-large", (32, 1, 1, 1)), ("queue-zero", (1, 0, 1, 1)),
        ("queue-large", (1, 17, 1, 1)), ("k-zero", (1, 1, 0, 1)),
        ("k-large", (1, 1, 129, 1)), ("rows-zero", (1, 1, 1, 0)),
        ("rows-large", (1, 1, 1, 17)),
    )
    for label, values in geometries:
        binary = directory / f"{label}.vvp"
        parameters = [f"-Ptop_safety_tb.{name}={value}" for name, value in
                      zip(("BANKS", "QUEUE_DEPTH", "TILE_K", "TILE_ROWS"), values)]
        execute(directory / f"{label}-compile", [
            "iverilog", "-g2012", "-Wall", "-s", "top_safety_tb", *parameters,
            "-o", relative(binary),
            *[relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))],
            "tests/top_safety_tb.sv"], timeout=60)
        simulation = directory / f"{label}-simulation"
        execute(simulation, ["vvp", relative(binary)], timeout=60,
                expect_failure=label != "legal-minimum",
                repair_of=repair_of if label == "legal-minimum" else None)
        if label != "legal-minimum":
            raw = (simulation / "stdout.txt").read_text() + (
                simulation / "stderr.txt").read_text()
            if "PARAMETER ERROR" not in raw or "SUMMARY top_safety" in raw:
                raise AssertionError(f"Illegal geometry not diagnosed before work: {label}")
    for lanes, tile_k in ((1, 1), (3, 3), (16, 128), (0, 1), (17, 1),
                          (-1, 1), (1, 0), (1, 129), (1, -1)):
        label = f"tensor-lanes-{lanes}-k-{tile_k}"
        binary = directory / f"{label}.vvp"
        legal = 1 <= lanes <= 16 and 1 <= tile_k <= 128
        execute(directory / f"{label}-compile", [
            "iverilog", "-g2012", "-Wall", "-s", "tensor_parameter_tb",
            f"-Ptensor_parameter_tb.LANES={lanes}", f"-Ptensor_parameter_tb.TILE_K={tile_k}",
            "-o", relative(binary), "rtl/anvil_q4_00_fp_pkg.sv", "rtl/anvil_q4_fp32.sv",
            "rtl/anvil_q4_fp_tensor_array.sv", "tests/tensor_parameter_tb.sv"])
        simulation = directory / f"{label}-simulation"
        execute(simulation, ["vvp", relative(binary)], expect_failure=not legal)
        if not legal:
            raw = (simulation / "stdout.txt").read_text() + (simulation / "stderr.txt").read_text()
            if "PARAMETER ERROR" not in raw or "SUMMARY tensor_parameter" in raw:
                raise AssertionError(f"Illegal tensor geometry not diagnosed: {label}")
    print(f"Top safety receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run(args.preparation, args.repair_of)
