"""Disposable source mutations with structured, real comparison failures."""

import argparse
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative, source_hashes
from numerics import vectors


def numerical_mutants(preparation=False):
    directory = new_run("numerical-defects", preparation)
    fixture = directory / "fp32-vectors.txt"
    vectors(fixture, compact=True)
    mutants = (
        ("clean", None, None, None),
        ("rounding", "anvil_q4_00_fp_pkg.sv",
         "increment = extended[2] && (extended[1] || extended[0] || extended[3]);",
         "increment = 1'b0;"),
        ("fp-flags", "anvil_q4_fp32.sv",
         "assign flags = out_valid ? result_register[36:32] : 5'd0;",
         "assign flags = 5'd0;"),
    )
    records = []
    for label, target, original, replacement in mutants:
        child = directory / f"{label}-sources"
        child.mkdir()
        inputs = []
        for name in ("anvil_q4_00_fp_pkg.sv", "anvil_q4_fp32.sv"):
            text = (ROOT / "rtl" / name).read_text()
            if name == target:
                if original not in text:
                    raise AssertionError(f"Mutation anchor absent: {label}")
                text = text.replace(original, replacement, 1)
            copy = child / name
            copy.write_text(text)
            inputs.append(relative(copy))
        obj = child / "compile-obj"
        try:
            execute(directory / f"{label}-compile", [
                "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                "--top-module", "fp32_tb", "--Mdir", relative(obj),
                *inputs, "tests/fp32_tb.sv"])
            mismatch = child / "mismatch.json"
            receipt = execute(directory / f"{label}-simulation", [
                relative(obj / "Vfp32_tb"), f"+vectors={relative(fixture)}",
                f"+mismatch={relative(mismatch)}"], expect_failure=label != "clean",
                extra_inputs=[ROOT / name for name in inputs])
            record = {"mutant": label,
                      "receipt": relative(directory / f"{label}-simulation/receipt.json")}
            if label != "clean":
                comparison = json.loads(mismatch.read_text())
                # A nonzero child exit, text match, timeout or compiler error
                # alone cannot establish defect sensitivity.
                if (comparison["kind"] != "ieee" or comparison["valid"] != 1 or
                    (comparison["expected"] == comparison["observed"] and
                     comparison["expected_flags"] == comparison["observed_flags"])):
                    raise AssertionError(f"Not an executed numerical mismatch: {label}")
                record["comparison"] = comparison
            records.append(record)
        finally:
            if obj.exists():
                shutil.rmtree(obj)
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "numerical_mutants": records,
        "scope": "rounding and FP-flags only"}, indent=2) + "\n")
    print(f"Numerical defect receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    args = parser.parse_args()
    numerical_mutants(args.preparation)
