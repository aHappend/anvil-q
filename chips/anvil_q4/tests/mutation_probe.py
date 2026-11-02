"""Disposable leaf mutations; compilation failures never count as detections."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT


CASES = {
    "fp-rounding": (
        "rtl/anvil_q4_00_fp_pkg.sv",
        "increment = extended[2] && (extended[1] || extended[0] || extended[3]);\n"
        "        rounded = {1'b0, extended[26:3]}",
        "increment = extended[2] && (extended[1] || extended[0]);\n"
        "        rounded = {1'b0, extended[26:3]}",
        ["arithmetic_probe.py", "--samples", "10000"],
        "IEEE_MISMATCH"),
    "fp32-accumulation": (
        "rtl/anvil_q4_tensor_array.sv",
        "accumulators[j*32+:32]<=fp_result[j*32+:32];",
        "accumulators[j*32+:32]<={fp_result[j*32+16+:16],16'd0};",
        ["tensor_probe.py", "--preparation", "--lanes", "4"],
        "TENSOR_MISMATCH"),
    "awq-lane": (
        "rtl/anvil_q4_dequant.sv",
        "1: awq_shift = 16;",
        "1: awq_shift = 4;",
        ["numerics_probe.py", "--preparation"],
        "NUMERICS_EXACT"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--case", choices=CASES, action="append")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("leaf-mutations", args.preparation, args.repair_of)
    error = None
    try:
        results = []
        experiment.receipt["cases"] = results
        for name in args.case or CASES:
            path, before, after, command, marker = CASES[name]
            source = (ROOT/path).read_text()
            if source.count(before) != 1:
                raise AssertionError(f"mutation anchor no longer uniquely matches: {name}")
            changed = source.replace(before, after)
            identity = hashlib.sha256(changed.encode()).hexdigest()[:12]
            directory = experiment.directory / f"mutant-{identity}"
            directory.mkdir()
            for pattern in ("rtl/*.sv", "design/*.md", "tests/*"):
                for original in ROOT.glob(pattern):
                    if original.is_file():
                        destination = directory / original.relative_to(ROOT)
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(original, destination)
            (directory/path).write_text(changed)
            experiment.run(["python3", "tests/"+command[0], *command[1:]], name,
                           cwd=directory, expect_failure=True)
            receipts = list((directory/"evidence").glob("preparation/*/receipt.json"))
            if len(receipts) != 1:
                raise AssertionError(f"missing unique executed mutant receipt: {name}")
            receipt = json.loads(receipts[0].read_text())
            compiled = [item for item in receipt["commands"]
                        if Path(item["argv"][0]).name == "verilator" and
                        ("--binary" in item["argv"] or "--cc" in item["argv"])]
            simulated = [item for item in receipt["commands"]
                         if item["argv"][0].endswith("-sim")]
            if len(compiled) != 1 or compiled[0]["exit_code"] != 0 or (
                    len(simulated) != 1 or simulated[0]["exit_code"] == 0 or
                    simulated[0]["timed_out"]):
                raise AssertionError(f"not a compiled numerical mutant rejection: {name}")
            simulation = simulated[0]
            output = (directory/simulation["stdout_path"]).read_text() + (
                directory/simulation["stderr_path"]).read_text()
            if marker not in output:
                raise AssertionError(f"missing independent numerical mismatch: {name}")
            results.append({
                "mutation": name, "source": path,
                "original_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "mutant_sha256": hashlib.sha256(changed.encode()).hexdigest(),
                "receipt": experiment.rel(receipts[0]), "detection": marker,
                "compile_exit": compiled[0]["exit_code"],
                "simulation_exit": simulation["exit_code"]})
            experiment.save()
    except (RuntimeError, ValueError, AssertionError, KeyError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
