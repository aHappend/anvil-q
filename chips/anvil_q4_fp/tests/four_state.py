"""Compact complete native inference under four-state Icarus semantics."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative
from native_model import Fixture, descriptor


def run(preparation=False, repair_of=None):
    directory = new_run("native-four-state", preparation)
    fixture = Fixture(descriptor(banks=1, dimension=2, intermediate=1, vocabulary=1,
                                 context=1, page_tokens=1, bias=0), tokens=1).export(directory)
    binary = directory / "native.vvp"
    execute(directory / "compile", [
        "iverilog", "-g2012", "-Wall", "-s", "native_smoke_tb", "-o", relative(binary),
        *[relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))],
        "tests/native_smoke_tb.sv"])
    execute(directory / "simulate", [
        "vvp", relative(binary), f"+image={relative(fixture)}"],
        timeout=600, repair_of=repair_of)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run(args.preparation, args.repair_of)
