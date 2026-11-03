#!/usr/bin/env python3
"""Portable source-current L1 verification and retained preparation probes."""

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import dequantize

ROOT = Path(__file__).resolve().parents[1]


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class Experiment:
    def __init__(self, stem, preparation=False):
        suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        self.directory = ROOT / "evidence" / ("preparation" if preparation else "verification") / (
            stem + "-" + suffix)
        self.directory.mkdir(parents=True)
        sources = sorted({p for pattern in (
            "rtl/*.sv", "anvil_d1_reference/rtl/*.sv", "design/*.md",
            "fpga/quartus_gate.json", "tests/*")
            for p in ROOT.glob(pattern) if p.is_file()})
        self.receipt = {
            "started_at": timestamp(),
            "entry_argv": [str(Path(sys.executable).name), "tests/verify.py", *sys.argv[1:]],
            "cwd": ".",
            "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sources},
            "commands": [], "results": {},
        }
        self.save()

    def save(self):
        (self.directory / "receipt.json").write_text(json.dumps(self.receipt, indent=2) + "\n")

    def execute(self, argv, name, timeout=600):
        relative = self.directory.relative_to(ROOT)
        record = {"argv": argv, "cwd": ".", "started_at": timestamp(),
                  "timeout_s": timeout,
                  "stdout": str(relative / (name + ".stdout.txt")),
                  "stderr": str(relative / (name + ".stderr.txt"))}
        self.receipt["commands"].append(record)
        self.save()
        start = time.monotonic()
        try:
            with (ROOT / record["stdout"]).open("w") as stdout, (
                    ROOT / record["stderr"]).open("w") as stderr:
                try:
                    result = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr,
                                            timeout=timeout, check=False)
                    record["exit_code"] = result.returncode
                    record["timed_out"] = False
                except subprocess.TimeoutExpired:
                    record["exit_code"] = None
                    record["timed_out"] = True
                    raise
        finally:
            record["ended_at"] = timestamp()
            record["duration_s"] = time.monotonic() - start
            self.save()
        if result.returncode:
            raise RuntimeError(f"{name} exited {result.returncode}; see {record['stdout']} "
                               f"and {record['stderr']}")
        return (ROOT / record["stdout"]).read_text()

    def finish(self, success, error=None):
        self.receipt.update(ended_at=timestamp(), success=success)
        if error:
            self.receipt["error"] = error
        self.save()
        print(str((self.directory / "receipt.json").relative_to(ROOT)), flush=True)


def dequant_vectors(path):
    scales = [0x00000001, 0x00000101, 0x007FFFFF, 0x00800000,
              0x00800001, 0x33800000, 0x3EAAAAAB, 0x3F000001,
              0x3F7FFFFF, 0x3F800000, 0x3F800001, 0x3FC00000,
              0x40000000, 0x477FE000, 0x7B000001, 0x7F7FFFFF]
    vectors = [(code, scale) for scale in scales for code in range(256)]
    rng = random.Random(17)
    vectors += [(rng.randrange(256), rng.randrange(1, 0x7F800000)) for _ in range(10000)]
    vectors += [(code, scale) for scale in (
        0, 0x80000000, 0xBF800000, 0x7F800000, 0x7FC00001, 0xFF800000)
        for code in (0, 1, 0x38, 0x7E, 0x7F, 0x80, 0xFF)]
    with path.open("w") as stream:
        for code, scale in vectors:
            fp32, bf16, error = dequantize(code, scale)
            stream.write(f"{code:02x} {scale:08x} {fp32:08x} {bf16:04x} {error:x}\n")
    return len(vectors)


def run_dequant(experiment, simulator):
    directory = experiment.directory.relative_to(ROOT)
    vectors = experiment.directory / "dequant-vectors.txt"
    count = dequant_vectors(vectors)
    if simulator == "icarus":
        experiment.execute(["iverilog", "-V"], "iverilog-version")
        binary = directory / "dequant.vvp"
        experiment.execute(["iverilog", "-g2012", "-Wall", "-s", "dequant_tb", "-o",
                            str(binary), "rtl/anvil_d2_fp8_dequant.sv", "tests/dequant_tb.sv"],
                           "dequant-compile")
        argv = ["vvp", str(binary)]
    else:
        experiment.execute(["verilator", "--version"], "verilator-version")
        obj = directory / "dequant-obj"
        experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                            "--top-module", "dequant_tb", "--Mdir", str(obj),
                            "-o", "dequant-sim", "rtl/anvil_d2_fp8_dequant.sv",
                            "tests/dequant_tb.sv"], "dequant-compile", 1200)
        argv = [str(obj / "dequant-sim")]
    output = experiment.execute(argv + ["+vectors=" + str(vectors.relative_to(ROOT))],
                                "dequant-simulation")
    experiment.receipt["results"]["dequant"] = {
        "simulator": simulator, "vectors": count,
        "all_codes_at_distinct_scales": 16, "seeded_random_cases": 10000,
        "public_pin_scoreboard": True, "raw_summary": output.strip(),
    }
    experiment.save()


def run_public_smoke(experiment):
    directory = experiment.directory.relative_to(ROOT)
    obj = directory / "public-obj"
    sources = [str(p.relative_to(ROOT)) for pattern in (
        "rtl/*.sv", "anvil_d1_reference/rtl/*.sv") for p in sorted(ROOT.glob(pattern))]
    experiment.execute(["verilator", "--version"], "verilator-version")
    experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                        "--top-module", "top_smoke_tb", "--Mdir", str(obj),
                        "-o", "public-sim", *sources, "tests/top_smoke_tb.sv"],
                       "public-compile", 1200)
    output = experiment.execute([str(obj / "public-sim")], "public-simulation", 1200)
    experiment.receipt["results"]["public-smoke"] = {
        "geometry": {"hidden": 8, "layers": 1, "banks": 2, "queue_depth": 3},
        "weight_fixture": "all-zero tensors; FP8 missing scales positive one",
        "oracle": "zero output projection gives zero logits and greedy token zero",
        "raw_summary": output.strip(),
        "scope": "bounded protocol smoke, not nonzero transformer numerical coverage",
    }
    experiment.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=["dequant", "public-smoke"], required=True)
    parser.add_argument("--simulator", choices=["icarus", "verilator"], default="icarus")
    parser.add_argument("--repair-of", help="Project-relative retained failed receipt")
    args = parser.parse_args()
    experiment = Experiment("d2-" + args.probe, preparation=True)
    if args.repair_of:
        prior = Path(args.repair_of)
        if prior.is_absolute() or ".." in prior.parts or not (ROOT / prior).is_file():
            raise ValueError("--repair-of must name an existing project-relative receipt")
        experiment.receipt["repair_of"] = str(prior)
        experiment.save()
    try:
        experiment.execute(["python3", "--version"], "python-version")
        if args.probe == "dequant":
            run_dequant(experiment, args.simulator)
        else:
            run_public_smoke(experiment)
    except Exception as error:
        experiment.finish(False, str(error))
        raise
    experiment.finish(True)


if __name__ == "__main__":
    main()
