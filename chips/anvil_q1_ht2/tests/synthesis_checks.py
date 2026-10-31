"""Real Yosys lowering with memories retained and package-import expansion.

The installed Verilog frontend has no package-import support. For synthesis
only, package declarations are lexically inserted at each import site. Functions,
constants, modules and attributes are otherwise byte-for-byte unchanged.
"""

import json
import re
import uuid

from evidence import ROOT, execute, relative, require_success, write_json


def integer_casts(text):
    """Yosys spelling of the SV signed, 32-bit int cast."""
    while "int'(" in text:
        start = text.index("int'(")
        end, depth = start + 5, 1
        while depth:
            if text[end] == "(":
                depth += 1
            elif text[end] == ")":
                depth -= 1
            end += 1
        expression = text[start + 5:end - 1]
        text = text[:start] + "$signed(32'(" + expression + "))" + text[end:]
    return text


def expanded_sources(directory):
    packages, modules = {}, []
    for source in sorted((ROOT / "rtl").glob("*.sv")):
        text = source.read_text()
        match = re.fullmatch(r"\s*package\s+(\w+)\s*;(.*)endpackage\s*", text, re.S)
        if match:
            packages[match[1]] = match[2]
        else:
            modules.append((source, text))
    result = directory / "expanded.sv"
    text = ""
    for source, body in modules:
        body = re.sub(r"import\s+(\w+)::\*\s*;", lambda m: packages[m[1]], body)
        for package, declarations in packages.items():
            if package + "::" in body:
                body = body.replace(");", ");\n" + declarations, 1)
                body = body.replace(package + "::", "")
        if "import " in body or "::" in body:
            raise AssertionError(f"unhandled synthesis package reference: {relative(source)}")
        text += f"\n// Lexically expanded {relative(source)}\n" + integer_casts(body)
    result.write_text(text)
    write_json(directory / "expansion.json", {
        "operation": "replace import declaration with exact package body",
        "packages": sorted(packages), "sources": [relative(s) for s, _ in modules],
        "generated_source": relative(result), "arithmetic_rewrites": 0,
        "frontend_cast_spelling": "int'(x) -> $signed(32'(x))",
    })
    return result


def module_name(module, fallback):
    return module.get("attributes", {}).get("hdlname", fallback).split()[0].lstrip("\\")


def inspect(netlist, top, default_geometry):
    modules = netlist["modules"]
    if top not in modules:
        raise AssertionError("synthesis top absent")
    leaves = {}
    instances = {}
    memory_bits = 0
    initial_state = []

    def visit(name, ancestors=()):
        nonlocal memory_bits
        if name in ancestors:
            raise AssertionError("recursive synthesis hierarchy")
        definition = modules[name]
        logical = module_name(definition, name)
        instances[logical] = instances.get(logical, 0) + 1
        for wire, net in definition.get("netnames", {}).items():
            if "init" in net.get("attributes", {}):
                initial_state.append({"module": logical, "wire": wire,
                                      "init": net["attributes"]["init"]})
        for cell in definition.get("cells", {}).values():
            kind = cell["type"]
            if kind in modules:
                if not any(cell["connections"].values()):
                    raise AssertionError("disconnected hierarchy cell")
                visit(kind, (*ancestors, name))
            else:
                leaves[kind] = leaves.get(kind, 0) + 1
                if kind.startswith("$mem"):
                    params = cell["parameters"]
                    memory_bits += int(params.get("WIDTH", "0"), 2) * int(params.get("SIZE", "0"), 2)

    visit(top)
    forbidden = [kind for kind in leaves if any(item in kind.lower()
                 for item in ("dlatch", "div", "mod"))]
    if forbidden:
        raise AssertionError(f"latch or runtime combinational divide/remainder: {forbidden}")
    registers = sum(count for kind, count in leaves.items() if "dff" in kind.lower())
    if not registers:
        raise AssertionError("no synthesized registered state")
    if top in ("anvil_q1_ht2_top", "anvil_q1_ht2_decoder", "anvil_q1_ht2_tile_batch_mac"):
        if instances.get("anvil_q1_ht2_mac_lane") != 256:
            raise AssertionError(f"256 live array paths absent: {instances}")
        if instances.get("anvil_q1_ht2_fp16_mul", 0) < 256:
            raise AssertionError("native array multipliers absent")
    if top == "anvil_q1_ht2_top":
        for name in ("anvil_q1_ht2_decoder", "anvil_q1_ht2_sparse_dma",
                     "anvil_q1_ht2_spec_verifier", "anvil_q1_ht2_transport"):
            if instances.get(name, 0) != 1:
                raise AssertionError(f"connected top module missing: {name}")
        if memory_bits == 0:
            raise AssertionError("model/KV memory inference missing")
        if not any(any(isinstance(bit, int) for bit in port["bits"])
                   for name, port in modules[top]["ports"].items()
                   if name in ("commit_token_ids", "logit_data", "avm_address")):
            raise AssertionError("top output connectivity reduced to constants")
    return {"top": top, "default_geometry": default_geometry,
            "registered_cells": registers, "memory_bits": memory_bits,
            "initial_state": initial_state,
            "hierarchical_instances": instances, "leaf_cells": leaves,
            "zero_latches": True, "zero_runtime_div_mod": True,
            "scope": "generic synthesis, not FPGA resource mapping or timing"}


def synthesize(directory, selected=None):
    expanded = expanded_sources(directory)
    targets = selected or (
        "anvil_q1_ht2_fp16_mul", "anvil_q1_ht2_fp32_add",
        "anvil_q1_ht2_fp32_mul", "anvil_q1_ht2_fp32_divsqrt",
        "anvil_q1_ht2_fp32_exp", "anvil_q1_ht2_fp32_sincos",
        "anvil_q1_ht2_tile_batch_mac", "anvil_q1_ht2_sparse_dma",
        "anvil_q1_ht2_spec_verifier", "anvil_q1_ht2_top", "anvil_q1_ht_top", "anvil_q1_top",
    )
    results = []
    for top in targets:
        work = directory / f"{top}-{uuid.uuid4().hex[:8]}"
        work.mkdir()
        netlist, script = work / "netlist.json", work / "synthesis.ys"
        script.write_text(
            f"read_verilog -sv {relative(expanded)}\n"
            f"hierarchy -check -top {top}\n"
            "proc\nopt_expr\nopt_clean\ncheck\n"
            "memory -nomap\nopt_clean\ncheck -assert\n"
            "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod t:$divfloor t:$modfloor\n"
            "stat\n"
            f"write_json {relative(netlist)}\n")
        run = require_success(execute(
            ["yosys", "-Q", "-T", "-s", relative(script)], directory, top + "-synthesis",
            timeout=1800, inputs=[expanded, script]))
        data = inspect(json.loads(netlist.read_text()), top, True)
        data["receipt"] = relative(run / "receipt.json")
        data["netlist"] = relative(netlist)
        write_json(work / "statistics.json", data)
        results.append(data)
    return results
