"""Bounded single-job startup diagnostic, not structure/functional acceptance."""

from dataclasses import asdict, replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compiler_admission_checks import admission_sensitivity
from execution import ROOT, Run, VERILATOR_UNROLL, write_json
from parameters import A, B
from structure_checks import sv_literal


FAILED_RECEIPT = (
    "evidence/check-structure/20261030T132122Z-8483d693b413/tool-0107/receipt.json")


def startup_builds(run):
    results = []
    affected = replace(B, BANKS=4, CACHE_MODE=1, TILE_K=24, TILE_ROWS=3)
    rtl = [run.rel(p) for p in sorted((ROOT / "rtl").glob("*.sv"))]
    # Distinct constant labels force actual cold builds instead of cache reuse.
    cases = [affected] * 4 + [replace(A, BANKS=1), replace(A, BANKS=8, CACHE_MODE=2)]
    for number, geometry in enumerate(cases):
        folder = run.path / f"startup-{number:04d}"
        folder.mkdir()
        overrides = ",".join(f".{key}({sv_literal(value)})"
                             for key, value in asdict(geometry).items())
        tb = folder / "startup.sv"
        marker = f"STARTUP_COMPLETE_{number}"
        tb.write_text(
            "`timescale 1ns/1ps\nmodule parameter_startup;\n"
            f"anvil_q3_top #({overrides}) accelerator "
            "(.clk(1'b0),.rst_n(1'b0),.cancel(1'b0),.token_valid(1'b0));\n"
            f'initial begin #10; $display("{marker}"); $finish; end\nendmodule\n')
        obj = folder / "obj"
        _, compile_record = run.tool([
            "verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
            *VERILATOR_UNROLL, "--top-module", "parameter_startup",
            "--Mdir", run.rel(obj), "-o", "startup", *rtl, run.rel(tb)],
            build_class="verilator-startup")
        assert compile_record["argv"][1:3] == ["-j", "1"]
        assert "--threads" not in compile_record["argv"]
        assert compile_record["exit_code"] == 0
        text, simulation = run.tool([run.rel(obj / "startup")])
        assert text.count(marker) == 1 and "PARAMETER ERROR" not in text
        assert not run.compiler_admissions
        results.append({
            "parameters": asdict(geometry),
            "compile_receipt": str(Path(compile_record["stdout"]).parent / "receipt.json"),
            "startup_receipt": str(Path(simulation["stdout"]).parent / "receipt.json"),
            "scope": "constant-input parameter startup only",
        })
        write_json(run.path / "startup-results.json", results)
    assert not run.build_reuses and len(run.builds) == len(cases)
    return results


def main():
    run = Run("evidence/preparation/startup-single-job",
              "single-job compiler teardown mitigation", repair_of=FAILED_RECEIPT)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("python3", "--version"), ("verilator", "--version"),
                      ("g++", "--version"), ("make", "--version")])
        result = {"regressions": admission_sensitivity(), "startups": startup_builds(run),
                  "original_failure": FAILED_RECEIPT}
        run.finish("passed", result=result)
    except BaseException as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
