"""Bounded native-Yosys frontend diagnosis; altered variants are never acceptance."""

import re

from execution import ROOT, sha256, write_json
from synthesis_checks import lower_packages


def frontend_probe(run):
    run.versions([("yosys", "-V")])
    folder = run.path / "frontend"
    folder.mkdir()
    lowered = lower_packages(folder)
    rms = next(p for p in lowered if p.name == "anvil_q3_rmsnorm.sv")
    lowered_text = rms.read_text()
    # Retain the original failing cast form as well as the explicit-alias adaptation.
    text = lowered_text
    for name in ("square", "mean"):
        alias = "yosys_signed_port_" + name
        text = text.replace(f"wire signed [127:0] {alias};\nassign {alias}={name};", "")
        text = text.replace(alias, "$signed(" + name + ")")
    package = (ROOT / "rtl/anvil_q3_00_pkg.sv").read_text()
    functions = re.fullmatch(r"\s*package anvil_q3_pkg;\s*(.*?)\s*endpackage\s*",
                             package, re.S)[1]
    variants = {
        "original-rms": text,
        "signed-port-alias-rms": lowered_text,
        "without-invalid-call": text.replace("f16_invalid(rdata[15:0])", "1'b0"),
        "without-f16-conversion": text.replace("f16_q16(rdata[15:0])", "32'sd0"),
        "without-output-rounding": text.replace("round_shift_sat32(scaled_result,48)", "32'sd0"),
    }
    results = []
    for label, variant in variants.items():
        target = folder / (label + ".sv")
        target.write_text(variant)
        out, receipt = run.tool(["yosys", "-Q", "-T", "-p",
                                "read_verilog -sv " + run.rel(target)],
                               expected=(0, 1, -6))
        results.append({"label": label, "exit_code": receipt["exit_code"],
                        "source_sha256": sha256(target), "stdout": receipt["stdout"],
                        "stderr": receipt["stderr"],
                        "altered_diagnostic_only": label != "original-rms"})
    for function, inputs, invocation in (
            ("f16_q16", "input [15:0] h", "h"),
            ("round_shift_sat32", "input signed [127:0] x", "x,48")):
        target = folder / (function + "-leaf.sv")
        target.write_text("module function_probe(" + inputs + ",output signed [31:0] y);\n" +
                          functions + "\nassign y=" + function + "(" + invocation + ");\nendmodule\n")
        out, receipt = run.tool(["yosys", "-Q", "-T", "-p",
                                "read_verilog -sv " + run.rel(target)], expected=(0, 1, -6))
        results.append({"label": function + "-leaf", "exit_code": receipt["exit_code"],
                        "source_sha256": sha256(target), "stdout": receipt["stdout"],
                        "stderr": receipt["stderr"], "altered_diagnostic_only": True})
    write_json(folder / "frontend-results.json", results)
    return {"diagnostics": results, "scope": "frontend localization only, never synthesis acceptance"}
