"""One admitted defect diagnostic: RNE-to-truncation in a disposable RTL copy.

This is one of the ten mandatory defects, not the complete mutation suite.
Compilation failures are explicitly not counted as detections.
"""

import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, run_scalar


def main():
    parent = Probe("rne-defect")
    baseline = Probe("rne-baseline")
    mutant = None
    try:
        try:
            run_scalar(baseline, "verilator", compact=True)
            baseline_status = baseline.settle()
        except Exception as error:
            baseline.settle(f"{type(error).__name__}: {error}")
            raise
        if baseline_status:
            raise AssertionError("positive-control scalar comparison failed")
        mutant = Probe("rne-mutant")
        original = ROOT / "rtl/anvil_q2_fp2_arithmetic.sv"
        needle = "guard1 && (sticky1 || mantissa1[0])"
        text = original.read_text()
        if text.count(needle) != 1:
            raise AssertionError("mutation anchor must identify exactly one rounding operation")
        target = mutant.directory / original.name
        target.write_text(text.replace(needle, "1'b0"))
        mutant.receipt["mutation"] = {
            "source": str(original.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
            "mutant": str(target.relative_to(ROOT)),
            "mutant_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "replacement": [needle, "1'b0"],
        }
        try:
            run_scalar(mutant, "verilator", compact=True, overrides={original.name: target})
        except Exception as error:
            mutant.settle(f"{type(error).__name__}: {error}")
            raise
        mutant.settle()
        compiled = any(
            command["stdout"].endswith("/compile.stdout.txt") and command.get("exit_status") == 0
            for command in mutant.receipt["commands"]
        )
        simulated = any(
            command["stdout"].endswith("/simulation.stdout.txt") and command.get("exit_status") == 0
            for command in mutant.receipt["commands"]
        )
        observations = [row for row in mutant.summary["mismatches"] if row["check"] == "mul"]
        parent.compare("mutant-compilation", True, compiled, {})
        parent.compare("mutant-simulation", True, simulated, {})
        parent.compare("rounding-defect-genuine-mismatch", True, bool(observations), {})
        parent.summary["baseline_receipt"] = str((baseline.directory / "receipt.json").relative_to(ROOT))
        parent.summary["mutant_receipt"] = str((mutant.directory / "receipt.json").relative_to(ROOT))
        parent.summary["detection"] = observations[:3]
        parent.summary["detected_defects"] = int(compiled and simulated and bool(observations))
        return parent.settle()
    except Exception as error:
        return parent.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
