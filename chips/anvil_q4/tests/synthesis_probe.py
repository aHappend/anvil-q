"""Bounded Yosys lowering and structural checks, without physical timing claims."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT


def lower_codec_writes(text):
    """Express indexed nonblocking writes as exact whole-vector masked writes.

    The index expression and 8192-bit destination width are unchanged. This
    avoids Yosys 0.33's pathological PROC_MUX expansion of multiple dynamic
    part-select assignments. The standalone codec equivalence test compares
    original and localized outputs every cycle and against integer equations.
    """
    def replace(match):
        name, width, value = match.groups()
        mask = (1 << int(width))-1
        return (f"{name}<=({name} & ~(8192'd{mask} << (index*{width}))) | "
                f"((8192'({value}) & 8192'd{mask}) << (index*{width}));")

    result, count = re.subn(
        r"(result_payload|result_values)\[index\*(4|8|32)\+:\2\]<=([^;]+);",
        replace, text)
    if count != 7:
        raise AssertionError(f"codec frontend expected seven indexed writes, found {count}")
    return result


def lower_legacy_cache_writes(text):
    """Apply the same exact indexed-write lowering to the packed cache buffers."""
    for name, index in (("values", "lane"), ("payload", "word_index")):
        before = f"{name}[{index}*32+:32]<=rdata;"
        after = (f"{name}<=({name} & ~(8192'd4294967295 << ({index}*32))) | "
                 f"(8192'(rdata) << ({index}*32));")
        if text.count(before) != 1:
            raise AssertionError("legacy cache packed-write frontend anchor changed")
        text = text.replace(before, after)
    return text


def expand_packages(destination, indexed_write_lowering=False):
    """Localize function-only packages for the Yosys 0.33 Verilog frontend.

    Package bodies are copied byte-for-byte. Two same-width signed port casts
    in legacy RMSNorm use explicitly signed aliases to avoid a Yosys 0.33 AST
    assertion on unsigned wire aliases. The aliases preserve all 128 bits;
    no arithmetic, port width, hierarchy or sequential logic changes.
    Indexed packed-buffer writes can also use exact masked-vector expressions;
    codec cycle comparisons and independent legacy integer tests cover this
    frontend treatment. Original and generated inputs are both hash-bound.
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
        if indexed_write_lowering and path.name == "anvil_q3_cache_codec.sv":
            text = lower_codec_writes(text)
        if indexed_write_lowering and path.name == "anvil_q3_kv_cache.sv":
            text = lower_legacy_cache_writes(text)
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


def structural(netlist, top_name="anvil_q4_top"):
    modules = netlist["modules"]
    top = modules[top_name]
    required = {
        "anvil_q4_descriptor", "anvil_q4_token_io", "anvil_q4_decoder_layer",
        "anvil_q4_rmsnorm", "anvil_q4_bank_scheduler", "anvil_q4_speculative",
        "anvil_q4_compat", "anvil_q4_gemv", "anvil_q4_rope",
        "anvil_q4_gqa_attention", "anvil_q4_kv_cache", "anvil_q4_swiglu_mlp",
        "anvil_q4_elementwise", "anvil_q4_tensor_array",
        "anvil_q4_dequant", "anvil_q4_fp32",
    }
    if top_name == "compat_synthesis_top":
        required = {
            "anvil_q4_compat", "anvil_q4_legacy_gemv", "anvil_q3_rmsnorm",
            "anvil_q3_rope", "anvil_q3_gqa_attention", "anvil_q3_kv_cache",
            "anvil_q3_cache_codec", "anvil_q3_elementwise", "anvil_q3_token_io",
        }
    found = set()
    memo = {}
    visiting = set()

    def visit(name):
        if name in memo:
            return memo[name]
        if name in visiting:
            raise AssertionError("recursive synthesis hierarchy")
        visiting.add(name)
        module = modules[name]
        hdlname = module.get("attributes", {}).get("hdlname", name).split()[0].lstrip("\\")
        found.add(hdlname)
        state_bits = memory_bits = cells = registered_buffer_bits = 0
        q_bits = set()
        for cell in module.get("cells", {}).values():
            kind = cell["type"]
            cells += 1
            if kind in modules:
                child_state, child_memory, child_cells, child_buffers = visit(kind)
                state_bits += child_state
                memory_bits += child_memory
                cells += child_cells
                registered_buffer_bits += child_buffers
            elif "latch" in kind.lower() or kind in ("$div", "$mod", "$divfloor", "$modfloor"):
                raise AssertionError(f"forbidden synthesis cell {kind}")
            elif "dff" in kind.lower():
                state_bits += len(cell["connections"]["Q"])
                q_bits.update(bit for bit in cell["connections"]["Q"] if isinstance(bit, int))
            elif kind.startswith("$mem"):
                parameters = cell["parameters"]
                memory_bits += int(parameters["WIDTH"], 2) * int(parameters["SIZE"], 2)
        buffers = {
            "anvil_q3_cache_codec": ("source_values", "source_payload",
                                     "result_values", "result_payload"),
            "anvil_q3_kv_cache": ("values", "payload"),
        }.get(hdlname, ())
        for buffer in buffers:
            bits = set(module.get("netnames", {}).get(buffer, {}).get("bits", [])) & q_bits
            if len(bits) < 32:
                raise AssertionError(f"missing register-backed cache storage: {hdlname}.{buffer}")
            registered_buffer_bits += len(bits)
        if hdlname in required:
            if not module.get("cells") or not state_bits+memory_bits:
                raise AssertionError(f"stateless/empty required function: {hdlname}")
            status = [port["bits"] for key, port in module.get("ports", {}).items()
                      if key in ("done", "out_valid", "result_valid", "cfg_done",
                                 "verify_valid", "mem_req_valid") and port["direction"] == "output"]
            if status and not any(isinstance(bit, int) for bits in status for bit in bits):
                raise AssertionError(f"constant functional status: {hdlname}")
        visiting.remove(name)
        memo[name] = state_bits, memory_bits, cells, registered_buffer_bits
        return memo[name]

    state_bits, memory_bits, cells, registered_buffer_bits = visit(top_name)
    if required - found:
        raise AssertionError(f"missing functional hierarchy: {sorted(required - found)}")
    if state_bits < 1024 or memory_bits+registered_buffer_bits < 32:
        raise AssertionError(f"missing state/storage: {state_bits}/{memory_bits}/{registered_buffer_bits}")
    ports = ["mem_req_valid", "mem_req_row", "mem_req_col", "mem_req_wdata",
             "mem_rsp_ready", "logit_data", "logit_valid"]
    if top_name == "anvil_q4_top":
        ports.append("mem_req_tag")
    for name in ports:
        if not any(isinstance(bit, int) for bit in top["ports"][name]["bits"]):
            raise AssertionError(f"constant/disconnected top output: {name}")
    return {"state_bits": state_bits, "memory_bits": memory_bits,
            "registered_cache_buffer_bits": registered_buffer_bits,
            "cells": cells, "counting": "hierarchical instance-expanded generic cells/storage",
            "required_functions": sorted(required)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--banks", type=int, choices=(1, 16))
    parser.add_argument("--compat-only", action="store_true")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    if args.compat_only and args.banks is not None:
        parser.error("--banks and --compat-only are mutually exclusive")
    experiment = Experiment("synthesis", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["yosys", "-V"], "version").strip()
        frontend = experiment.directory / "frontend.sv"
        experiment.receipt["frontend_sha256"] = expand_packages(
            frontend, indexed_write_lowering=True)
        results = []
        configurations = (["compat"] if args.compat_only else
                          [args.banks] if args.banks else [16, 1, "compat"])
        for banks in configurations:
            root = "compat_synthesis_top" if banks == "compat" else "anvil_q4_top"
            extra = " tests/compat_synthesis_top.sv" if banks == "compat" else ""
            netlist = experiment.directory / f"top-{banks}.json"
            commands = (
                f"read_verilog -sv -defer {experiment.rel(frontend)}{extra}; "
                + (f"chparam -set BANKS {banks} anvil_q4_top; " if banks != "compat" else "")
                + f"hierarchy -check -top {root}; "
                "proc; opt_expr; opt_clean; check -assert; "
                "memory -nomap; opt_clean; check -assert; "
                "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod "
                "t:$divfloor t:$modfloor; stat; "
                f"write_json {experiment.rel(netlist)}"
            )
            experiment.run(["yosys", "-Q", "-T", "-p", commands],
                           f"synthesis-{banks}", timeout=1200)
            results.append({"configuration": banks, "top": root,
                            **structural(json.loads(netlist.read_text()), root)})
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
