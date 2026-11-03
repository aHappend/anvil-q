"""Source-bound compiled arithmetic diagnostic with an independent exact model."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ieee_reference import evaluate, self_check


ROOT = Path(__file__).resolve().parent.parent


def vectors(samples):
    directed = [
        0, 0x80000000, 1, 2, 3, 0x7FFFFF, 0x800000, 0x800001,
        0x807FFFFF, 0x80800000, 0x3F000000, 0x3F800000, 0x3F800001,
        0x3F800002, 0x33800000, 0x40000000, 0x40400000, 0xBF800000,
        0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000,
        0x7FC00000, 0x7F800001, 0xFFC00001, 0xFF800001,
    ]
    for op in range(16):
        for a in directed:
            for b in directed if op < 4 else [0]:
                yield op, a, b
    for op in (5, 6):
        for encoding in range(65536):
            yield op, encoding, 0
    for op in range(10):
        rng = random.Random(170001 + op)
        for _ in range(samples):
            if op in (5, 6):
                maximum = 0xFF if op == 5 else 0x1F
                shift = 7 if op == 5 else 10
                a = rng.getrandbits(16)
                while (a >> shift) & maximum == maximum:
                    a = rng.getrandbits(16)
            elif op == 9:
                a = rng.getrandbits(32)
            else:
                a = rng.getrandbits(32)
                while a & 0x7F800000 == 0x7F800000:
                    a = rng.getrandbits(32)
                if op == 4:
                    a &= 0x7FFFFFFF
            b = rng.getrandbits(32)
            while b & 0x7F800000 == 0x7F800000:
                b = rng.getrandbits(32)
            yield op, a, b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("samples must be positive")
    self_check()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = ROOT / "evidence" / "preparation" / ("arithmetic-" + stamp)
    directory.mkdir(parents=True, exist_ok=False)
    rel = lambda path: path.relative_to(ROOT).as_posix()
    sources = ["rtl/anvil_q4_00_fp_pkg.sv", "rtl/anvil_q4_fp32.sv",
               "tests/arithmetic_tb.sv", "tests/ieee_reference.py",
               "tests/arithmetic_probe.py"]
    receipt = {
        "argv": ["python3", "tests/arithmetic_probe.py", *sys.argv[1:]], "cwd": ".",
        "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                          for p in sources},
        "repair_of": args.repair_of, "commands": [], "samples_per_opcode": args.samples,
    }

    def run(argv, stem):
        record = {
            "argv": argv, "cwd": ".", "timeout_s": 600,
            "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "stdout_path": rel(directory / (stem + ".stdout.txt")),
            "stderr_path": rel(directory / (stem + ".stderr.txt")),
        }
        started = time.monotonic()
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
        fixture = directory / "vectors.txt"
        counts = [0] * 16
        with fixture.open("w") as stream:
            for op, a, b in vectors(args.samples):
                result, flags = evaluate(op, a, b)
                stream.write(f"{op} {a:08x} {b:08x} {result:08x} {flags:02x}\n")
                counts[op] += 1
        receipt["generated_counts"] = counts
        receipt["fixture_sha256"] = hashlib.sha256(fixture.read_bytes()).hexdigest()
        if not run(["verilator", "--version"], "version"):
            return 1
        objects = directory / "compile-obj"
        compile_argv = [
            "verilator", "--binary", "--timing", "-Wno-fatal", "--top-module",
            "arithmetic_tb", "--Mdir", rel(objects), "-o", "arithmetic-sim",
            *sources[:3],
        ]
        if run(compile_argv, "compile"):
            passed = run([rel(objects / "arithmetic-sim"),
                          "+VECTORS=" + rel(fixture)], "simulation")
            output = (directory / "simulation.stdout.txt").read_text()
            passed &= f"SUMMARY arithmetic comparisons={sum(counts)} " in output
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
