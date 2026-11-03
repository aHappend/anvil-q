"""Public-pin speculation acceptance, backpressure, errors and cancellation."""

import argparse
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import execute, new_run, relative


def run(preparation=False):
    directory = new_run("speculation", preparation)
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile", [
            "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
            "--top-module", "speculative_tb", "--Mdir", relative(obj),
            "rtl/anvil_q4_fp_speculative.sv", "tests/speculative_tb.sv"])
        execute(directory / "verilator-speculation", [
            relative(obj / "Vspeculative_tb")])
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Speculation receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    args = parser.parse_args()
    run(args.preparation)
