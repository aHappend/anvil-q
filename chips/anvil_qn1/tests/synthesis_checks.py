"""Yosys structural synthesis with lossless netlists and bounded memory retention."""

import gzip
import hashlib
import json
import re

from execution import ROOT, relative


def yosys_sources(run):
    """Expand package scope for the installed Verilog frontend, without RTL edits."""
    package = (ROOT / "rtl" / "anvil_qn1_00_pkg.sv").read_text()
    match = re.fullmatch(r"\s*package anvil_qn1_pkg;(.*)endpackage\s*", package, re.S)
    if match is None:
        raise AssertionError("native arithmetic package structure changed")
    body = match.group(1)
    output = run.path / "yosys-source"
    output.mkdir(exist_ok=False)
    sources, transformations = [], []
    for source in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv")):
        if source.name == "anvil_qn1_00_pkg.sv":
            continue
        original = source.read_text()
        text = original.replace("import anvil_qn1_pkg::*;", "")
        text = text.replace("anvil_qn1_pkg::", "")
        text, count = re.subn(r"(module\b.*?;\s*\n)", lambda m: m[1] + body + "\n",
                              text, count=1, flags=re.S)
        if count != 1:
            raise AssertionError(f"Yosys package-expansion module header: {source.name}")
        target = output / source.name
        target.write_text(text)
        sources.append(relative(target))
        transformations.append({
            "source": source.relative_to(ROOT).as_posix(),
            "original_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "expanded_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "operation": "inline unchanged package declarations; resolve package scope",
        })
    (run.path / "yosys-package-expansion.json").write_text(
        json.dumps(transformations, indent=2) + "\n")
    return sources


def retain_json(path):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    target = path.with_suffix(path.suffix + ".gz")
    with target.open("xb") as file:
        with gzip.GzipFile(fileobj=file, mode="wb", mtime=0) as compressed:
            compressed.write(raw)
    with gzip.open(target, "rb") as file:
        recovered = file.read()
    if recovered != raw:
        raise AssertionError("lossless netlist retention failed")
    data = json.loads(raw)
    path.unlink()
    return data, {"file": relative(target), "raw_bytes": len(raw), "raw_sha256": digest,
                  "compressed_bytes": target.stat().st_size,
                  "compressed_sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


def inspect_netlist(data):
    modules = data.get("modules", {})
    if "anvil_qn1_top" not in modules:
        raise AssertionError("synthesized native top missing")
    counts = {}
    for name, module in modules.items():
        if module.get("attributes", {}).get("blackbox") in (1, "00000000000000000000000000000001"):
            raise AssertionError(f"unresolved synthesized black box: {name}")
        if module.get("processes"):
            raise AssertionError(f"unlowered synthesis process: {name}")
        for cell in module.get("cells", {}).values():
            kind = cell["type"]
            counts[kind] = counts.get(kind, 0) + 1
            if "latch" in kind.lower() or kind in ("$div", "$mod", "$divfloor", "$modfloor"):
                raise AssertionError(f"forbidden synthesized cell {kind} in {name}")
            if not kind.startswith("$") and kind not in modules:
                raise AssertionError(f"unresolved synthesized cell {kind}")
    required = ("decoder", "dual_think_ctrl", "csr_perf", "bank_scheduler")
    top_cells = modules["anvil_qn1_top"].get("cells", {})
    for stem in required:
        if not any(name.split(".")[-1] == stem for name in top_cells):
            raise AssertionError(f"required live top hierarchy missing: {stem}")
    tensors = [(name, module) for name, module in modules.items()
               if "anvil_qn1_tensor_array" in name]
    if not tensors:
        raise AssertionError("live tensor synthesis missing")
    lane_cells = 0
    for _, tensor in tensors:
        for lane in range(256):
            prefix = f"lanes[{lane}]."
            cell_names = tensor["cells"]
            if not all(prefix + stem in cell_names
                       for stem in ("weight_formation", "activation_multiply")):
                raise AssertionError(f"dynamic tensor lane disconnected: {lane}")
            lane_cells += 1
        for port in ("q", "z", "scale_bf16", "activation_bf16", "weight_bf16", "lane_mask"):
            bits = tensor["ports"][port]["bits"]
            if any(isinstance(bit, str) for bit in bits):
                raise AssertionError(f"dynamic tensor input folded to constants: {port}")
    sequential = sum(count for kind, count in counts.items()
                     if "dff" in kind.lower() or kind.startswith("$mem"))
    if not sequential or not lane_cells:
        raise AssertionError("synthesis discarded connected state")
    return {"module_count": len(modules), "cell_counts": counts,
            "dynamic_lanes": lane_cells, "state_cells": sequential,
            "latches": 0, "combinational_div_mod": 0, "unresolved_blackboxes": 0}


def run_synthesis_probe(run):
    sources = yosys_sources(run)
    hierarchy = run.path / "hierarchy.json"
    netlist = run.path / "synthesized.json"
    script = run.path / "synthesis.ys"
    script.write_text(
        "read_verilog -sv " + " ".join(sources) + "\n"
        "chparam -set COMPACT 1 -set NUM_LAYERS 1 -set HIDDEN_SIZE 8 "
        "-set INTERMEDIATE_SIZE 8 -set NUM_Q_HEADS 2 -set NUM_KV_HEADS 1 "
        "-set HEAD_DIM 8 -set VOCAB_SIZE 8 -set MAX_SEQ_LEN 16 "
        "-set GROUP_SIZE 8 -set BANKS 1 -set QUEUE_DEPTH 3 anvil_qn1_top\n"
        "hierarchy -check -top anvil_qn1_top\n"
        "proc\nopt_expr\nopt_clean\ncheck -assert -noinit\n"
        f"write_json {relative(hierarchy)}\n"
        "memory -nomap\nopt_clean\ncheck -assert -noinit\nstat\n"
        f"write_json {relative(netlist)}\n")
    run.execute(["yosys", "-Q", "-T", "-s", relative(script)], "yosys-compact-structural")
    _, before = retain_json(hierarchy)
    data, after = retain_json(netlist)
    structural = inspect_netlist(data)
    run.execute(["yosys", "-Q", "-T", "-p", "help synth"], "yosys-synth-help")
    return {"geometry": "compact H8/D8/Q2/K1/B1/QD3", "hierarchy": before,
            "structural_netlist": after, "structural": structural}


def run_controller_synthesis(run):
    script = run.path / "controller.ys"
    netlist = run.path / "controller.json"
    script.write_text(
        "read_verilog -sv rtl/anvil_qn1_dual_think_ctrl.sv\n"
        "chparam -set MAX_SEQ_LEN 16 anvil_qn1_dual_think_ctrl\n"
        "hierarchy -check -top anvil_qn1_dual_think_ctrl\n"
        "proc\nopt -full\n"
        f"write_json {relative(netlist)}\n"
        "check -assert\nstat\n")
    text = run.execute(["yosys", "-Q", "-T", "-s", relative(script)],
                       "yosys-controller-optimized")
    data, artifact = retain_json(netlist)
    if "Found and reported 0 problems" not in text:
        raise AssertionError("controller structural result missing")
    return {"netlist": artifact, "modules": len(data["modules"]),
            "structural_consistency": "passed"}
