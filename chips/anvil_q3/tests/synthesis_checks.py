"""Retained generic synthesis; no generic-netlist result certifies FPGA timing."""

from collections import Counter
from dataclasses import asdict, replace
import json
import re

from execution import ROOT, sha256, write_json
from parameters import A, defaults, legal
from structure_checks import sequential_lint


def lower_packages(folder):
    """Normalize package, signed-port and declaration syntax for native Yosys."""
    package = ROOT / "rtl/anvil_q3_00_pkg.sv"
    text = package.read_text()
    match = re.fullmatch(r"\s*package anvil_q3_pkg;\s*(.*?)\s*endpackage\s*", text, re.S)
    if match is None:
        raise AssertionError("unexpected package grammar; do not guess a lowering")
    functions = match.group(1)
    if re.sub(r"function\b.*?endfunction", "", functions, flags=re.S).strip():
        raise AssertionError("package contains objects other than pure functions")

    lowered = folder / "yosys-input"
    lowered.mkdir()
    paths, bindings = [], []
    for source in sorted((ROOT / "rtl").glob("*.sv")):
        if source == package:
            continue
        original = source.read_text()
        qualified = original.replace("anvil_q3_pkg::", "")
        if "::" in qualified or re.search(r"\bimport\b", qualified):
            raise AssertionError("unsupported package reference in " + source.name)
        converted, modules = re.subn(r"(\bmodule\b.*?;)", lambda m: m[1] + "\n" + functions,
                                     qualified, flags=re.S)
        if not modules:
            raise AssertionError("no module in " + source.name)
        aliases = []
        declaration_moves = []
        if source.name == "anvil_q3_rmsnorm.sv":
            # Yosys 0.33 genrtlil.cc asserts for $signed(unsigned_whole_wire) ports.
            # An explicit signed alias preserves all 128 bits and the port signedness.
            if not re.search(r"reg\s+\[127:0\]\s+square,\s*sum,\s*mean\s*;", converted):
                raise AssertionError("RMSNorm signed-port alias source declaration changed")
            for name in ("square", "mean"):
                expression = "$signed(" + name + ")"
                if converted.count(expression) != 1:
                    raise AssertionError("RMSNorm signed-port alias is not unique: " + name)
                alias = "yosys_signed_port_" + name
                converted = converted.replace(expression, alias)
                aliases.append({"source": name, "alias": alias, "width": 128, "signed": True})
            declarations = "\n".join(
                f"wire signed [127:0] {a['alias']};\nassign {a['alias']}={a['source']};"
                for a in aliases)
            converted = re.sub(r"(\bmodule\b.*?;)", lambda m: m[1] + "\n" + declarations,
                               converted, count=1, flags=re.S)
        if source.name == "anvil_q3_tensor_array.sv":
            declaration = "reg [31:0] addition_row;"
            anchor = "wire [31:0] sum_index=row_pipe[7]-output_base;"
            if converted.count(declaration) != 1 or converted.count(anchor) != 1:
                raise AssertionError("tensor generate-scope declaration source changed")
            converted = converted.replace(declaration, "")
            converted = converted.replace(anchor, declaration + "\n    " + anchor)
            declaration_moves.append({"declaration": declaration, "before": anchor,
                                      "reason": "Yosys 0.33 generate-scope forward-reference width"})
        target = lowered / source.name
        target.write_text(converted)
        paths.append(target)
        bindings.append({"source": str(source.relative_to(ROOT)), "sha256": sha256(source),
                         "lowered": str(target.relative_to(ROOT)), "lowered_sha256": sha256(target),
                         "modules": modules, "signed_port_aliases": aliases,
                         "declaration_moves": declaration_moves})
    write_json(folder / "package-lowering.json",
               {"operation": "remove package qualification; inline identical functions; "
                             "materialize bit-identical signed whole-wire port aliases; "
                             "move unchanged forward-referenced declarations before use",
                "package_sha256": sha256(package), "sources": bindings})
    return paths


def synthesis_case(run, g, label):
    if not legal(g):
        raise AssertionError("illegal synthesis geometry " + str(asdict(g)))
    folder = run.path / ("synthesis-" + label)
    folder.mkdir()
    inputs = lower_packages(folder)
    netlist = folder / "netlist.json"
    script = folder / "synthesis.ys"
    commands = ["read_verilog -sv -defer " + " ".join(run.rel(p) for p in inputs)]
    commands += ["chparam " + " ".join(f"-set {k} {v}" for k, v in asdict(g).items()) +
                 " anvil_q3_top",
                 "synth -top anvil_q3_top -run begin:fine",
                 "check -assert",
                 "select -assert-none t:$dlatch t:$adlatch t:$dlatchsr "
                 "t:$div t:$mod t:$divfloor t:$modfloor",
                 "stat", "write_json " + run.rel(netlist)]
    script.write_text("\n".join(commands) + "\n")
    _, receipt = run.tool(["yosys", "-Q", "-T", "-s", run.rel(script)], timeout=14400)
    design = json.loads(netlist.read_text())
    cells = Counter(cell["type"] for module in design["modules"].values()
                    for cell in module.get("cells", {}).values())
    prohibited = {k: v for k, v in cells.items()
                  if "latch" in k.lower() or k in ("$div", "$mod", "$divfloor", "$modfloor")}
    if prohibited:
        raise AssertionError("forbidden runtime cells: " + repr(prohibited))
    if "anvil_q3_top" not in design["modules"] or not cells:
        raise AssertionError("empty/wrong-top synthesis")
    result = {"geometry": asdict(g), "label": label, "cell_types": dict(cells),
              "latches": 0, "runtime_div_mod_cells": 0, "structural_check": "check -assert",
              "netlist_sha256": sha256(netlist), "stdout": receipt["stdout"],
              "scope": "Yosys coarse generic synthesis with memories retained; not Quartus fit/STA"}
    write_json(folder / "result.json", result)
    return result


def synthesis(run):
    run.versions([("yosys", "-V")])
    lint = sequential_lint()
    results = []
    cases = [(f"a-b{b}-m{m}-a{a}", replace(A, BANKS=b, CACHE_MODE=m, INT4_ASYM=a))
             for b in (1, 2, 4, 8) for m, a in ((0, 0), (1, 0), (2, 0), (2, 1))]
    cases += [(f"shipping-default-b8-m{m}-a{a}",
               replace(defaults(3), CACHE_MODE=m, INT4_ASYM=a))
              for m, a in ((0, 0), (1, 0), (2, 0), (2, 1))]
    write_json(run.path / "synthesis-matrix.json",
               [{"label": label, "geometry": asdict(g)} for label, g in cases])
    for label, g in cases:
        results.append(synthesis_case(run, g, label))
        write_json(run.path / "synthesis-results.json", results)
    return {"lint": lint, "synthesis": results}
