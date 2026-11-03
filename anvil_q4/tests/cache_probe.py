"""Bounded public-pin cache diagnostic; not a substitute for the eight L1 suites.

Run: python3 tests/cache_probe.py
Every invocation retains a new preparation receipt, including failing cases.
"""

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
from cache_reference import CASES, fixture


ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=["all", *CASES], default="all")
    parser.add_argument("--mode", choices=["all", "write", "read", "order"],
                        default="all")
    parser.add_argument("--repair-of", action="append", default=[])
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="iverilog")
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = ROOT / "evidence" / "preparation" / ("cache-recovery-" + stamp)
    directory.mkdir(parents=True, exist_ok=False)
    relative = lambda path: path.relative_to(ROOT).as_posix()
    sources = [
        "rtl/anvil_q4_00_fp_pkg.sv", "rtl/anvil_q4_fp32.sv",
        "rtl/anvil_q4_mem_port.sv", "rtl/anvil_q4_kv_cache.sv",
        "tests/cache_recovery_tb.sv", "tests/cache_reference.py",
        "tests/cache_probe.py", "design/SPEC.md", "design/ARCHITECTURE.md",
    ]
    receipt = {
        "kind": "bounded-public-pin-cache-diagnostic",
        "argv": ["python3", relative(Path(sys.argv[0]).resolve()), *sys.argv[1:]],
        "cwd": ".", "repair_of": args.repair_of,
        "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                          for p in sources},
        "commands": [],
    }

    def run(argv, stem, timeout=600):
        started = time.monotonic()
        record = {"argv": argv, "cwd": ".", "timeout_s": timeout,
                  "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "stdout_path": relative(directory / (stem + ".stdout.txt")),
                  "stderr_path": relative(directory / (stem + ".stderr.txt"))}
        with (ROOT / record["stdout_path"]).open("wb") as stdout, (
                ROOT / record["stderr_path"]).open("wb") as stderr:
            try:
                child = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr,
                                       timeout=timeout, check=False)
                record.update(exit_code=child.returncode, timed_out=False)
            except subprocess.TimeoutExpired:
                record.update(exit_code=None, timed_out=True)
            except OSError as exc:
                stderr.write(str(exc).encode())
                record.update(exit_code=None, timed_out=False, launch_error=str(exc))
        record["elapsed_s"] = time.monotonic() - started
        record["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt["commands"].append(record)
        return record["exit_code"] == 0

    try:
        objects = directory/"compile-obj"
        if args.simulator == "iverilog":
            tools_ok = run(["iverilog", "-V"], "iverilog-version")
            tools_ok &= run(["vvp", "-V"], "vvp-version")
            binary = relative(directory / "cache.vvp")
            compiled = tools_ok and run(
                ["iverilog", "-g2012", "-Wall", "-s", "cache_recovery_tb", "-o",
                 binary, *sources[:5]], "compile")
            simulate = ["vvp", binary]
        else:
            tools_ok = run(["verilator", "--version"], "verilator-version")
            compiled = tools_ok and run(
                ["verilator", "--binary", "--timing", "-Wno-fatal",
                 "--top-module", "cache_recovery_tb", "--Mdir", relative(objects),
                 "-o", "cache-sim", *sources[:5]], "compile")
            simulate = [relative(objects/"cache-sim")]
        receipt["cases"] = []
        receipt["fixture_sha256"] = {}
        if compiled:
            cases = list(CASES) if args.case == "all" else [args.case]
            modes = ["write", "read", "order"] if args.mode == "all" else [args.mode]
            for name in cases:
                image = directory / (name + ".hex")
                image.write_text("".join(f"{word:08x}\n" for word in fixture(name)))
                receipt["fixture_sha256"][relative(image)] = hashlib.sha256(
                    image.read_bytes()).hexdigest()
                for mode in modes:
                    stem = name + "-" + mode
                    passed = run(
                        [*simulate, "+FIXTURE=" + relative(image),
                         "+MODE=" + str(["write", "read", "order"].index(mode))], stem)
                    record = receipt["commands"][-1]
                    summary = (ROOT / record["stdout_path"]).read_text()
                    passed = passed and "SUMMARY cache comparisons=" in summary
                    receipt["cases"].append({"case": name, "mode": mode,
                                             "passed": passed,
                                             "stdout_path": record["stdout_path"]})
                    print(f"{stem}: {'PASS' if passed else 'FAIL'}", flush=True)
        passed = compiled and bool(receipt["cases"]) and all(
            case["passed"] for case in receipt["cases"])
        receipt["exit_code"] = 0 if passed else 1
        if passed and objects.is_dir():
            shutil.rmtree(objects)
    finally:
        receipt["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (directory / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(relative(directory / "receipt.json"), flush=True)
    return receipt["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
