"""Bounded Yosys lowering and structural checks, without physical timing claims."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT


def expand_packages(destination):
    """Localize function-only packages for the Yosys 0.33 Verilog frontend.

    Package bodies are copied byte-for-byte. Two same-width signed port casts
    in legacy RMSNorm use explicitly signed aliases to avoid a Yosys 0.33 AST
    assertion on unsigned wire aliases. The aliases preserve all 128 bits;
    no arithmetic, port width, hierarchy or sequential logic changes.
    Original inputs and generated frontend input are both hash-bound.
    """
    packages = {}
    modules = []
    for path in sorted((ROOT / "rtl").glob("*.sv")):
        text = path.read_text()
        match = re.fullmatch(r"\s*package\s+(\w+)\s*;(.*)endpackage\s*",
                            text, re.S)
        if match:
            packages[match[1]] = match[2]
        else:
            modules.append((path, text))
    for name, body in packages.items():
        remainder = re.sub(r"function\b.*?endfunction", "", body, flags=re.S)
        remainder = re.sub(r"//[^\n]*|/\*.*?\*/", "", remainder, flags=re.S)
        if remainder.strip():
            raise RuntimeError(f"unsupported non-function package contents: {name}")
    output = []
    for path, text in modules:
        if path.name == "anvil_q3_rmsnorm.sv":
            header = re.search(r"\)\s*;", text)
            aliases = (
                "\n  wire signed [127:0] frontend_signed_square=square;\n"
                "  wire signed [127:0] frontend_signed_mean=mean;\n")
            for name in ("square", "mean"):
                old = "$signed(" + name + ")"
                if text.count(old) != 1:
                    raise AssertionError("legacy signed-cast adaptation no longer matches")
                text = text.replace(old, "frontend_signed_" + name)
            text = text[:header.end()] + aliases + text[header.end():]
        for name, body in packages.items():
            imported = re.search(r"\bimport\s+" + name + r"::\*\s*;", text)
            qualified = name + "::" in text
            if imported:
                text = text[:imported.start()] + body + text[imported.end():]
            elif qualified:
                header = re.search(r"\)\s*;", text)
                if not header:
                    raise RuntimeError(f"cannot identify module port boundary: {path.name}")
                text = text[:header.end()] + body + text[header.end():]
            text = text.replace(name + "::", "")
        output.append("// Input: rtl/" + path.name + "\n" + text)
    destination.write_text("\n".join(output))
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def structural(netlist):
    modules = netlist["modules"]
    top = modules["anvil_q4_top"]
    required = {
        "anvil_q4_descriptor", "anvil_q4_token_io", "anvil_q4_decoder_layer",
        "anvil_q4_rmsnorm", "anvil_q4_bank_scheduler", "anvil_q4_speculative",
        "anvil_q4_compat", "anvil_q4_gemv", "anvil_q4_rope",
        "anvil_q4_gqa_attention", "anvil_q4_kv_cache", "anvil_q4_swiglu_mlp",
        "anvil_q4_elementwise", "anvil_q4_tensor_array",
        "anvil_q4_dequant", "anvil_q4_fp32",
    }
    found = set()
    state_bits = memory_bits = cells = 0
    visited = set()

    def visit(name):
        nonlocal state_bits, memory_bits, cells
        if name in visited:
            return
        visited.add(name)
        module = modules[name]
        hdlname = module.get("attributes", {}).get("hdlname", name).split()[0].lstrip("\\")
        found.add(hdlname)
        for cell in module.get("cells", {}).values():
            kind = cell["type"]
            cells += 1
            if kind in modules:
                visit(kind)
            elif "latch" in kind.lower() or kind in ("$div", "$mod", "$divfloor", "$modfloor"):
                raise AssertionError(f"forbidden synthesis cell {kind}")
            elif "dff" in kind.lower():
                state_bits += len(cell["connections"]["Q"])
            elif kind.startswith("$mem"):
                parameters = cell["parameters"]
                memory_bits += int(parameters["WIDTH"], 2) * int(parameters["SIZE"], 2)

    visit("anvil_q4_top")
    if required - found:
        raise AssertionError(f"missing functional hierarchy: {sorted(required - found)}")
    if state_bits < 1024 or memory_bits < 32:
        raise AssertionError(f"missing state/storage: {state_bits}/{memory_bits}")
    for name in ("mem_req_valid", "mem_req_row", "mem_req_col", "mem_req_wdata",
                 "mem_req_tag", "mem_rsp_ready", "logit_data", "logit_valid"):
        if not any(isinstance(bit, int) for bit in top["ports"][name]["bits"]):
            raise AssertionError(f"constant/disconnected top output: {name}")
    return {"state_bits": state_bits, "memory_bits": memory_bits,
            "cells": cells, "required_functions": sorted(required)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--banks", type=int, choices=(1, 16))
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("synthesis", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["yosys", "-V"], "version").strip()
        frontend = experiment.directory / "frontend.sv"
        experiment.receipt["frontend_sha256"] = expand_packages(frontend)
        results = []
        for banks in ([args.banks] if args.banks else [16, 1]):
            netlist = experiment.directory / f"top-{banks}.json"
            commands = (
                f"read_verilog -sv -defer {experiment.rel(frontend)}; "
                f"chparam -set BANKS {banks} anvil_q4_top; "
                "hierarchy -check -top anvil_q4_top; "
                "proc; opt_expr; opt_clean; check -assert; "
                "memory -nomap; opt_clean; check -assert; "
                "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod "
                "t:$divfloor t:$modfloor; stat; "
                f"write_json {experiment.rel(netlist)}"
            )
            experiment.run(["yosys", "-Q", "-T", "-p", commands],
                           f"synthesis-{banks}", timeout=1200)
            results.append({"banks": banks, **structural(json.loads(netlist.read_text()))})
        experiment.receipt["comparisons"] = results
    except (RuntimeError, ValueError, AssertionError, KeyError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
