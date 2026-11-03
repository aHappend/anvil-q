"""Isolate Yosys signed function lowering using unchanged package bodies."""

import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT
from synthesis_probe import expand_packages


def main():
    experiment = Experiment("signed-frontend", preparation=True, repair_of=[
        "evidence/preparation/synthesis-20261102T115223592689Z/receipt.json"])
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["yosys", "-V"], "version").strip()
        package = (ROOT / "rtl/anvil_q3_00_pkg.sv").read_text()
        body = re.fullmatch(r"\s*package\s+\w+\s*;(.*)endpackage\s*",
                            package, re.S)[1]
        results = []
        for name, calls in (
                ("unsigned-context",
                 "assign gamma=f16_q16(h); assign rounded=round_shift_sat32(x,48);"),
                ("signed-context",
                 "assign gamma=$signed(f16_q16(h)); "
                 "assign rounded=$signed(round_shift_sat32(x,48));")):
            path = experiment.directory / (name + ".sv")
            path.write_text(
                "module diagnostic(input [15:0] h, input signed [127:0] x, "
                "output [31:0] gamma, rounded);\n" + body + "\n" + calls +
                "\nendmodule\n")
            for deferred in (False, True):
                variant = name + ("-deferred" if deferred else "-eager")
                try:
                    experiment.run([
                        "yosys", "-Q", "-T", "-p",
                        f"read_verilog -sv {'-defer ' if deferred else ''}"
                        f"{experiment.rel(path)}; "
                        "hierarchy -check -top diagnostic; proc; check -assert"],
                        variant)
                    results.append({"variant": variant, "exit_code": 0})
                except RuntimeError as exc:
                    results.append({"variant": variant, "exit_code":
                                    experiment.receipt["commands"][-1]["exit_code"],
                                    "failure": str(exc)})
        rmsnorm = (ROOT / "rtl/anvil_q3_rmsnorm.sv").read_text()
        header = re.search(r"\)\s*;", rmsnorm)
        rmsnorm = rmsnorm[:header.end()] + body + rmsnorm[header.end():]
        rmsnorm = rmsnorm.replace("anvil_q3_pkg::", "")
        for variant, text in (
                    ("rmsnorm-only", rmsnorm),
                    ("rmsnorm-cast-concat", re.sub(
                        r"\$signed\((\w+)\)", r"$signed({\1})", rmsnorm)),
                    ("rmsnorm-signed-alias", rmsnorm.replace(
                        "$signed(square)", "frontend_signed_square").replace(
                        "$signed(mean)", "frontend_signed_mean").replace(
                        "  localparam IDLE",
                        "  wire signed [127:0] frontend_signed_square=square;\n"
                        "  wire signed [127:0] frontend_signed_mean=mean;\n"
                        "  localparam IDLE"))):
            path = experiment.directory / (variant + ".sv")
            path.write_text(text)
            try:
                    experiment.run([
                        "yosys", "-Q", "-T", "-p",
                        f"read_verilog -sv {experiment.rel(path)}; "
                        "proc; opt_expr; opt_clean; check -assert"],
                        variant)
                    results.append({"variant": variant, "exit_code": 0})
            except RuntimeError as exc:
                    results.append({"variant": variant, "exit_code":
                                    experiment.receipt["commands"][-1]["exit_code"],
                                    "failure": str(exc)})
        children = list(re.finditer(
            r"^  (anvil_q3_\w+)[^\n]* \(.*?^  \);", rmsnorm, re.M | re.S))
        if not children:
            raise AssertionError("no RMSNorm child instantiations isolated")
        for selected in [None, *range(len(children))]:
            text = rmsnorm
            for index in reversed(range(len(children))):
                    if index != selected:
                        child = children[index]
                        text = text[:child.start()] + text[child.end():]
            variant = "rmsnorm-child-" + (
                    "none" if selected is None else children[selected][1])
            path = experiment.directory / (variant + ".sv")
            path.write_text(text)
            try:
                    experiment.run([
                        "yosys", "-Q", "-T", "-p",
                        f"read_verilog -sv {experiment.rel(path)}"], variant)
                    results.append({"variant": variant, "exit_code": 0})
            except RuntimeError as exc:
                    results.append({"variant": variant, "exit_code":
                                    experiment.receipt["commands"][-1]["exit_code"],
                                    "failure": str(exc)})
        frontend = experiment.directory / "localized.sv"
        experiment.receipt["frontend_sha256"] = expand_packages(frontend)
        for deferred in (False, True):
            variant = "rmsnorm-" + ("deferred" if deferred else "eager")
            try:
                experiment.run([
                    "yosys", "-Q", "-T", "-p",
                    f"read_verilog -sv {'-defer ' if deferred else ''}"
                    f"{experiment.rel(frontend)}; "
                    "hierarchy -check -top anvil_q3_rmsnorm; "
                    "proc; opt_expr; opt_clean; check -assert"],
                    variant)
                results.append({"variant": variant, "exit_code": 0})
            except RuntimeError as exc:
                results.append({"variant": variant, "exit_code":
                                experiment.receipt["commands"][-1]["exit_code"],
                                "failure": str(exc)})
        experiment.receipt["diagnostic_results"] = results
    except (RuntimeError, ValueError, AssertionError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
