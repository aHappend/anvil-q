"""Bounded discrimination of a Yosys 0.33 signed-function frontend assertion."""

import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative
from synthesis import lower_packages


if __name__ == "__main__":
    directory = new_run("yosys-frontend", preparation=True)
    lowered = directory / "lowered.sv"
    lower_packages(lowered)
    module = re.search(r"module anvil_q3_parent_rmsnorm\b.*?endmodule",
                       lowered.read_text(), flags=re.S)[0]
    original = "round_shift_sat32(scaled_result,48)"
    package_body = re.fullmatch(r"\s*package\s+\w+\s*;(.*)endpackage\s*",
        (ROOT / "rtl/anvil_q3_parent_00_pkg.sv").read_text(), flags=re.S)[1]
    variants = (
        ("original", module),
        ("expression", module.replace(original,
            "round_shift_sat32($signed(scaled_result ^ 128'd0),48)")),
        ("explicit-wire", module.replace(original,
            "round_shift_sat32($signed({scaled_result}),32'sd48)")),
        ("f16-only", "module probe(input [15:0] h, output [31:0] y);\n" +
         package_body + "\nassign y=f16_q16(h);\nendmodule\n"),
        ("round-only", "module probe(input signed [127:0] x, output [31:0] y);\n" +
         package_body + "\nassign y=round_shift_sat32(x,48);\nendmodule\n"),
    )
    results = []
    for label, text in variants:
        source = directory / f"{label}.sv"
        source.write_text(text)
        try:
            receipt = execute(directory / label, [
                "yosys", "-Q", "-T", "-p",
                f"read_verilog -sv {relative(source)}; proc; opt_expr; check -noinit"],
                repair_of="evidence/preparation/synthesis-20261103T024127235905Z/yosys-0/receipt.json")
            status = "completed"
        except RuntimeError:
            status = "tool-failure"
        results.append({"variant": label, "status": status,
                        "receipt": relative(directory / label / "receipt.json")})
    (directory / "observed.json").write_text(json.dumps(results, indent=2) + "\n")
    print(relative(directory), flush=True)
