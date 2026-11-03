"""Scheduler ownership, per-client holds, cancellation and malformed responses."""

import argparse
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative


def run(preparation=False, banks=16, queue=3):
    directory = new_run("scheduler", preparation)
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile", [
            "verilator", "--cc", "--exe", "--build", "-Wno-fatal", "-j", "2",
            "--top-module", "anvil_q4_fp_bank_scheduler", "--Mdir", relative(obj),
            f"-GBANKS={banks}", f"-GQUEUE_DEPTH={queue}",
            "-CFLAGS", f"-std=c++17 -DBANKS={banks}",
            "rtl/anvil_q4_fp_bank_scheduler.sv",
            os.path.relpath(ROOT / "tests/scheduler_sim.cpp", obj)])
        execute(directory / "verilator-scheduler", [
            relative(obj / "Vanvil_q4_fp_bank_scheduler")])
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Scheduler receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--banks", type=int, default=16)
    parser.add_argument("--queue", type=int, default=3)
    args = parser.parse_args()
    run(args.preparation, args.banks, args.queue)
