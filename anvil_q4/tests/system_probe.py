"""Bounded compact full-decoder diagnostic with independently expected tensors."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transformer_reference import make_fixture


ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = ROOT / "evidence" / "preparation" / ("system-compact-" + stamp)
    directory.mkdir(parents=True, exist_ok=False)
    rel = lambda path: path.relative_to(ROOT).as_posix()
    rtl = [ROOT / "rtl" / name for name in
           ("anvil_q3_00_pkg.sv", "anvil_q4_00_fp_pkg.sv")]
    rtl += sorted(p for p in (ROOT / "rtl").glob("*.sv") if p not in rtl)
    sources = rtl + [ROOT / "tests" / name for name in (
        "top_probe.cpp", "transformer_reference.py", "ieee_reference.py", "system_probe.py")]
    receipt = {
        "argv": ["python3", "tests/system_probe.py", *sys.argv[1:]], "cwd": ".",
        "repair_of": args.repair_of,
        "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_sha256": {rel(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "commands": [],
    }

    def run(argv, stem):
        started = time.monotonic()
        record = {"argv": argv, "cwd": ".", "timeout_s": 600,
                  "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "stdout_path": rel(directory / (stem + ".stdout.txt")),
                  "stderr_path": rel(directory / (stem + ".stderr.txt"))}
        with (ROOT / record["stdout_path"]).open("wb") as out, (
                ROOT / record["stderr_path"]).open("wb") as err:
            try:
                child = subprocess.run(argv, cwd=ROOT, stdout=out, stderr=err,
                                       timeout=600, check=False)
                record.update(exit_code=child.returncode, timed_out=False)
            except subprocess.TimeoutExpired:
                record.update(exit_code=124, timed_out=True)
            except OSError as exc:
                err.write(str(exc).encode())
                record.update(exit_code=127, timed_out=False)
        record["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record["elapsed_s"] = time.monotonic() - started
        receipt["commands"].append(record)
        return record["exit_code"] == 0

    passed = False
    try:
        receipt["geometry"] = make_fixture(directory)
        receipt["fixture_sha256"] = {
            rel(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in directory.glob("*.txt")
        }
        objects = directory / "compile-obj"
        if run(["verilator", "--version"], "version") and run([
            "verilator", "--cc", "--exe", "--build", "--verilate-jobs", "1",
            "--build-jobs", "2", "-Wno-fatal",
            "--top-module", "anvil_q4_top", "--Mdir", rel(objects),
            "-CFLAGS", "-std=c++17", "-o", "top-sim", *map(rel, rtl),
            # make executes inside Mdir, so the input is relative to that directory.
            "../../../../tests/top_probe.cpp",
        ], "compile"):
            passed = run([rel(objects / "top-sim"), rel(directory)], "simulation")
            if passed:
                passed = "SUMMARY top tokens=4 logits=68 " in (
                    directory / "simulation.stdout.txt").read_text()
            if passed:
                shutil.rmtree(objects)
    finally:
        receipt["exit_code"] = 0 if passed else 1
        receipt["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (directory / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(rel(directory / "receipt.json"), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
