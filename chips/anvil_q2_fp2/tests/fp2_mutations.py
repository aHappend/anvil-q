"""Ten successfully compiled disposable defects checked against positive controls."""

import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, run_scalar
import fp2_attention_probe as attention
import fp2_epilogue_probe as epilogue
import fp2_prefetch_probe as prefetch
import fp2_telemetry_probe as telemetry
import fp2_tensor_probe as tensor


MUTATIONS = (
    ("lane-127-omission", "tensor", "anvil_q2_fp2_bfp_tensor_array.sv",
     "in_mask[lane] ? in_a", "(in_mask[lane] && lane!=127) ? in_a"),
    ("wrong-group-exponent", "tensor", "anvil_q2_fp2_bfp_tensor_array.sv",
     "-13'sd268;", "-13'sd267;"),
    ("rne-to-truncation", "scalar", "anvil_q2_fp2_arithmetic.sv",
     "guard1 && (sticky1 || mantissa1[0])", "1'b0"),
    ("ping-pong-association", "prefetch", "anvil_q2_fp2_ping_pong_prefetch.sv",
     "data_slot[fill_slot][512*beat_count+:512]", "data_slot[!fill_slot][512*beat_count+:512]"),
    ("inverse-sqrt-coefficient", "scalar", "anvil_q2_fp2_nonlinear.sv",
     "base0<=coefficients[69:35];", "base0<=coefficients[69:35] ^ 35'h100000000;"),
    ("rope-pair-mapping", "epilogue", "anvil_q2_fp2_epilogue_fusion.sv",
     "rope_input,1'b0,in_b,in_sin,", "rope_input,1'b0,in_a,in_sin,"),
    ("swiglu-sign-branch", "epilogue", "anvil_q2_fp2_epilogue_fusion.sv",
     "(gate[31] ? exp_saved : 32'h3f800000)", "(!gate[31] ? exp_saved : 32'h3f800000)"),
    ("softmax-rescale-removal", "attention", "anvil_q2_fp2_flash_attn.sv",
     "alpha<=alpha_data;", "alpha<=32'h3f800000;"),
    ("sixth-head-broadcast", "attention", "anvil_q2_fp2_flash_attn.sv",
     "(issue_head*D+lane)*16", "((issue_head==5 ? 4 : issue_head)*D+lane)*16"),
    ("telemetry-stall-omission", "telemetry", "anvil_q2_fp2_telemetry.sv",
     "assign increments[1]={63'd0,event_mem_stall};", "assign increments[1]=64'd0;"),
)


def execute(probe, family, override=None):
    overrides = {override.name: override} if override else None
    if family == "scalar":
        run_scalar(probe, "verilator", compact=True, overrides=overrides)
    elif family == "tensor":
        tensor.run(probe, True, "verilator", overrides=overrides)
    elif family == "epilogue":
        epilogue.run(probe, True, "verilator", overrides=overrides)
    elif family == "attention":
        attention.run(probe, True, "verilator", 8, 3, overrides=overrides)
    elif family == "prefetch":
        prefetch.run(probe, "verilator", override)
    elif family == "telemetry":
        telemetry.run(probe, 64, "verilator", override)
    else:
        raise ValueError(f"unknown mutation family {family}")


def child_probe(parent, name):
    return Probe(name, output_parent=parent.directory, preparation=True)


def run(parent, selected=None):
    cases = [case for case in MUTATIONS if selected is None or case[0] in selected]
    if not cases:
        raise ValueError("no selected mutations")
    baseline_receipts = {}
    for family in dict.fromkeys(case[1] for case in cases):
        baseline = child_probe(parent, f"{family}-positive-control")
        try:
            execute(baseline, family)
        except Exception as error:
            baseline.settle(f"{type(error).__name__}: {error}")
            raise
        if baseline.settle():
            raise AssertionError(f"failed positive control {family}")
        baseline_receipts[family] = str((baseline.directory / "receipt.json").relative_to(ROOT))
    detections = []
    for name, family, filename, needle, replacement in cases:
        mutant = child_probe(parent, name)
        original = ROOT / "rtl" / filename
        text = original.read_text()
        expected_anchors = 2 if name == "inverse-sqrt-coefficient" else 1
        if text.count(needle) != expected_anchors:
            mutant.settle("mutation anchor changed")
            raise AssertionError(f"mutation anchor changed: {name}")
        disposable = mutant.directory / filename
        disposable.write_text(text.replace(needle, replacement, 1))
        mutant.receipt["mutation"] = {
            "name": name, "original": str(original.relative_to(ROOT)),
            "original_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
            "disposable": str(disposable.relative_to(ROOT)),
            "disposable_sha256": hashlib.sha256(disposable.read_bytes()).hexdigest(),
            "replacement": [needle, replacement],
        }
        try:
            execute(mutant, family, disposable)
        except Exception as error:
            mutant.settle(f"{type(error).__name__}: {error}")
            # Compiler and simulator failures alone are not numerical detections.
            raise
        mutant.settle()
        compile_records = [record for record in mutant.receipt["commands"]
                           if record["stdout"].endswith("/compile.stdout.txt")]
        simulation_records = [record for record in mutant.receipt["commands"]
                              if record["stdout"].endswith("/simulation.stdout.txt")]
        compiled = len(compile_records) == 1 and compile_records[0].get("exit_status") == 0
        simulated = len(simulation_records) == 1 and simulation_records[0].get("exit_status") == 0
        mismatches = mutant.summary["mismatch_count"]
        observations = mutant.summary["mismatches"]
        parent.compare(f"{name}-compiled", True, compiled, {})
        parent.compare(f"{name}-simulated", True, simulated, {})
        parent.compare(f"{name}-genuine-mismatch", True, mismatches > 0 and bool(observations), {})
        detections.append({
            "name": name, "compiled": compiled, "simulated": simulated,
            "mismatch_count": mismatches, "detection": observations[:2],
            "baseline_receipt": baseline_receipts[family],
            "mutant_receipt": str((mutant.directory / "receipt.json").relative_to(ROOT)),
        })
        if not (compiled and simulated and mismatches and observations):
            raise AssertionError(f"undetected compiled mutation {name}")
    parent.summary["defects"] = detections
    parent.compare("detected-defect-count", len(cases), len(detections), {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=[case[0] for case in MUTATIONS])
    args = parser.parse_args()
    parent = Probe("mutations")
    try:
        run(parent, [args.only] if args.only else None)
        return parent.settle()
    except Exception as error:
        return parent.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
