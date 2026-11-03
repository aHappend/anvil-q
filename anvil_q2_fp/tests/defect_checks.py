"""Disposable compiled RTL mutants rejected by unchanged public-pin checkers.

Each case first compiles and executes a pristine copy with the same fixture.
Compilation failures, missing comparisons and timeouts do not count as kills.
"""

import argparse
import difflib
import hashlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from codec_checks import fixtures
from numerical_checks import LANE_BENCH, compare_lane
from retained import ROOT, Run, require_time_zero, with_time_zero_check
from simulation import compile_model, startup_check
from scheduler_checks import BENCH as SCHEDULER_BENCH, compare as compare_scheduler


MUTATIONS = {
    "accumulation": (
        "anvil_q2_fp_dot_lane.sv",
        "accumulator[j]<=next_sum;",
        "accumulator[j]<=FP_ZERO;",
        "LANE_MISMATCH",
    ),
    "awq-nibbles": (
        "anvil_q2_fp_awq_dequant.sv",
        "{in_lane[0],in_lane[2],in_lane[1],2'b00}",
        "{in_lane[2],in_lane[1],in_lane[0],2'b00}",
        "AWQ_MISMATCH",
    ),
    "int8-exponent": (
        "anvil_q2_fp_cache_codec.sv",
        "exponent<=in_exponent[12:0];",
        "exponent<=in_exponent[12:0]+13'sd1;",
        "CODEC_MISMATCH",
    ),
    "held-request": (
        "anvil_q2_bank_scheduler.sv",
        "mem_req_wdata[b*32+:32]=wdata[held_slot[b]];",
        "mem_req_wdata[b*32+:32]=wdata[held_slot[b]]^next_tag[31:0];",
        "HELD_REQUEST_INSTABILITY",
    ),
}


def fixture(case, run):
    if case == "held-request":
        return SCHEDULER_BENCH, {"BANKS": 1, "DEPTH": 16}, None
    if case == "accumulation":
        one = 0x3F80
        payload = one | sum(one << (16 + j * 16) for j in range(8))
        vectors = [payload | ((index % 4 == 0) << 144) | ((index % 4 == 3) << 145)
                   for index in range(128)]
        template, width = LANE_BENCH, 37
        parameters = {"FORMAT": 0, "COUNT": len(vectors)}
    else:
        vectors, template, width, _ = fixtures(
            "awq" if case == "awq-nibbles" else "codec", "bf16", 16)
        parameters = {"FORMAT": 0, "COUNT": len(vectors)}
        if case == "int8-exponent":
            parameters["BLOCK"] = 16
    path = run.path / "vectors.hex"
    path.write_text("".join(f"{v:0{width}x}\n" for v in vectors))
    return template.replace("VECTORS", run.relative(path)), parameters, path


def pristine_check(case, trace):
    if case == "accumulation":
        return compare_lane(trace, "bf16", 128)
    if case == "held-request":
        return compare_scheduler(trace, 1)
    marker = "AWQ_COMPARED 2048 2048" if case == "awq-nibbles" else "CODEC_COMPARED"
    assert marker in trace.read_text(), "pristine fixture did not reach comparisons"
    return {"normal_checker_summary": marker}


def execute(case):
    run = Run(f"verifier-defect-{case}")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        pristine = run.path / "pristine" / "rtl"
        mutant = run.path / "mutant" / "rtl"
        shutil.copytree(ROOT / "rtl", pristine)
        shutil.copytree(ROOT / "rtl", mutant)
        module, original, replacement, marker = MUTATIONS[case]
        path = mutant / module
        text = path.read_text()
        assert text.count(original) == 1, "mutation anchor must be unique"
        changed = text.replace(original, replacement)
        path.write_text(changed)
        diff = run.path / "mutation.diff"
        diff.write_text("".join(difflib.unified_diff(
            text.splitlines(keepends=True), changed.splitlines(keepends=True),
            fromfile=f"pristine/rtl/{module}", tofile=f"mutant/rtl/{module}")))
        template, parameters, vector = fixture(case, run)
        bench = run.path / "bench.sv"
        bench.write_text(with_time_zero_check(template))
        artifacts = [diff, bench] + ([vector] if vector else [])
        artifacts.extend(pristine.glob("*.sv"))
        artifacts.extend(mutant.glob("*.sv"))
        run.receipt["generated_sha256"] = {
            run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}
        run.receipt["mutation"] = {
            "module": module, "original": original, "replacement": replacement,
            "expected_functional_rejection": marker, "diff": run.relative(diff),
        }
        outcomes = {}
        for label, sources in (("pristine", pristine), ("mutant", mutant)):
            binary = compile_model(run, bench, sorted(sources.glob("*.sv")), parameters,
                                   label=f"{label}-compile")
            startup_check(run, binary, label=f"{label}-startup")
            trace = run.command([run.relative(binary)], f"{label}-simulation",
                                expected_codes=(0,) if label == "pristine" else (0, 1, -6))
            exit_code = run.receipt["commands"][-1]["exit_code"]
            if label == "pristine":
                outcomes[label] = {"exit_code": exit_code, "metrics": pristine_check(case, trace)}
            elif case == "accumulation":
                assert exit_code == 0, "mutant must finish simulation before numerical comparison"
                try:
                    pristine_check(case, trace)
                except AssertionError as exc:
                    assert marker in str(exc), f"wrong mutant failure: {exc}"
                    outcomes[label] = {"exit_code": exit_code, "functional_rejection": str(exc)}
                else:
                    raise AssertionError("accumulation defect escaped the normal checker")
            else:
                assert exit_code in (1, -6) and marker in trace.read_text(), (
                    f"mutant did not reach its targeted functional rejection: {marker}")
                outcomes[label] = {"exit_code": exit_code, "functional_rejection": marker}
        run.finish("passed-focused-only", metrics=outcomes,
                   limitations="One targeted defect case, not complete admitted sensitivity coverage.")
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple(MUTATIONS), required=True)
    raise SystemExit(execute(parser.parse_args().case))
