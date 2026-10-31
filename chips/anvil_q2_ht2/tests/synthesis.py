"""Whole-hierarchy, memory-preserving structural synthesis through yosys-slang."""

import collections
import hashlib
import json
import re


def expand_packages(run, root, source_paths):
    """Inline only project function/constant packages at their import sites."""
    packages = {}
    modules = []
    package_pattern = re.compile(r"\s*package\s+(\w+)\s*;(.*)\bendpackage\s*", re.S)
    for path in source_paths:
        text = path.read_text()
        match = package_pattern.fullmatch(text)
        if match:
            packages[match[1]] = match[2]
        else:
            modules.append((path, text))
    imports = re.compile(r"\bimport\s+(\w+)::\*\s*;")
    outputs = []
    bindings = []
    for path, text in modules:
        def inline(match):
            name = match[1]
            if name not in packages:
                raise RuntimeError(f"unresolved synthesis package: {name}")
            return packages[name]
        lowered = imports.sub(inline, text)
        if path.name in ("anvil_q2_ht_configuration.sv",
                         "anvil_q2_ht2_native_configuration.sv"):
            replacements = [
                ("reg [15:0] initialized [0:ENTRIES-1];",
                 "reg [16*ENTRIES-1:0] initialized;"),
                ("initialized[cfg_index][cfg_addr[5:2]]",
                 "initialized[{cfg_index,cfg_addr[5:2]}]"),
                ("initialized[index]", "initialized[{index,4'b0000}+:16]"),
            ]
            for old, new in replacements:
                if old not in lowered:
                    raise RuntimeError(f"unrecognized configuration storage syntax: {path.name}")
                lowered = lowered.replace(old, new)
            lowered, resets = re.subn(
                r"for \(i=0;\s*i<ENTRIES;\s*i=i\+1\) initialized\[i\]<=0;",
                "initialized<=0;", lowered)
            if resets != 1 or re.search(r"initialized\[(?:i|index|cfg_index)\]", lowered):
                raise RuntimeError(f"unrecognized configuration reset/index: {path.name}")
        lowered = re.sub(r"\bint'\(([^()]*)\)", r"$signed(32'(\1))", lowered)
        if re.search(r"\bint'\s*\(", lowered):
            raise RuntimeError(f"unsupported nested int cast: {path.relative_to(root)}")
        if "::" in lowered or re.search(r"\b(?:package|import)\s", lowered):
            raise RuntimeError(f"unsupported package syntax: {path.relative_to(root)}")
        destination = run.path / "lowered-sources" / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(lowered)
        outputs.append(destination)
        bindings.append({
            "source": str(path.relative_to(root)), "lowered": run.relative(destination),
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "lowered_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        })
    run.receipt["package_expansion"] = {
        "operation": ("replace wildcard imports with verbatim package bodies; omit package units; "
                      "lower int'(x) to $signed(32'(x)); flatten only the asynchronous-reset "
                      "16-bit initialized register arrays in both configuration modules, "
                      "with index {row,word} and whole-vector reset"),
        "bindings": bindings,
    }
    run.save()
    return outputs


COMPACT_PARAMETERS = {
    "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
    "NUM_Q_HEADS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8,
    "GROUP_SIZE": 1, "VOCAB_SIZE": 2, "MAX_SEQ_LEN": 5,
    "TILE_SLOTS": 2, "READ_OUTSTANDING": 1, "QUEUE_DEPTH": 3,
    "CACHE_BLOCK": 1, "HOT_BLOCKS": 1,
}


def execute(run, root, source_paths, compact=False):
    run.tool("yosys")
    record, _, stderr = run.command(
        ["yosys", "-Q", "-T", "-m", "slang", "-p", "help read_slang"],
        "systemverilog-frontend", check=False)
    if record["exit_code"] != 0:
        lowered = expand_packages(run, root, source_paths)
        frontend = []
        read_command = "read_verilog -sv -defer " + " ".join(run.relative(p) for p in lowered)
    else:
        frontend = ["-m", "slang"]
        read_command = "read_slang --top anvil_q2_ht2_top " + " ".join(
            str(p.relative_to(root)) for p in source_paths)
    netlist = run.path / "production-netlist.json"
    script = run.path / "synthesis.ys"
    parameters = COMPACT_PARAMETERS if compact else {}
    parameter_options = "".join(f" -chparam {name} {value}"
                                for name, value in parameters.items())
    script.write_text(
        read_command + "\n"
        f"hierarchy -check -top anvil_q2_ht2_top{parameter_options}\n"
        "proc\nopt_expr\nopt_clean\ncheck -noinit -assert\n"
        "memory -nomap\nopt_clean\ncheck -noinit -assert\n"
        "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod t:$divfloor t:$modfloor\n"
        f"write_json {run.relative(netlist)}\nstat\n"
    )
    run.command(["yosys", "-Q", "-T", *frontend, "-s", run.relative(script)],
                "production-synthesis")
    modules = json.loads(netlist.read_text())["modules"]
    counts = collections.Counter()
    origins = collections.Counter()
    memory_bits = 0

    def visit(name, multiplicity, ancestry):
        nonlocal memory_bits
        if name in ancestry:
            raise RuntimeError(f"recursive synthesized hierarchy: {name}")
        module = modules[name]
        attributes = module.get("attributes", {})
        if int(str(attributes.get("blackbox", "0")), 2):
            raise RuntimeError(f"unresolved black box: {name}")
        origin = str(attributes.get("hdlname", name)).split()[0].lstrip("\\")
        origins[origin] += multiplicity
        for cell in module.get("cells", {}).values():
            kind = cell["type"]
            if kind in modules:
                visit(kind, multiplicity, ancestry | {name})
            else:
                counts[kind] += multiplicity
                if kind.startswith(("$dlatch", "$adlatch", "$_DLATCH", "$div", "$mod")):
                    raise RuntimeError(f"forbidden synthesized cell {kind}")
                if kind in ("$mem", "$mem_v2"):
                    params = cell["parameters"]
                    memory_bits += (int(params["WIDTH"], 2) * int(params["SIZE"], 2)
                                    * multiplicity)

    visit("anvil_q2_ht2_top", 1, set())
    for required in ("anvil_q2_ht2_tile_batch_mac", "anvil_q2_ht2_sparse_w2w4_dma",
                     "anvil_q2_ht2_spec_verifier"):
        if origins[required] == 0:
            raise RuntimeError(f"required production hierarchy missing: {required}")
    if origins["anvil_q2_ht2_product_pipe"] < 512:
        raise RuntimeError("production hierarchy does not retain 512 physical multipliers")
    if counts["$mul"] < 512 or counts["$add"] == 0 or memory_bits == 0:
        raise RuntimeError("synthesis lacks substantive multiplier/addition/storage paths")
    if sum(count for name, count in counts.items() if "dff" in name.lower()) == 0:
        raise RuntimeError("synthesis lacks registered state")
    run.receipt["synthesis"] = {
        "configuration": "compact whole top" if compact else "production parameter defaults",
        "parameters": parameters, "cells": dict(counts),
        "hierarchy_instances": dict(origins), "memory_bits": memory_bits,
        "latches": 0, "black_boxes": 0,
        "limits": "Generic structural synthesis does not establish M20K/DSP mapping, fit or timing.",
    }
    run.save()
