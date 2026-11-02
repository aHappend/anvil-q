"""Yosys structural synthesis with lossless netlists and bounded memory retention."""

import gzip
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor

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


def connected_tensor_lanes(data):
    """Conservative bit-level structural reachability through real cell ports."""
    records = []
    for name, module in data["modules"].items():
        if "anvil_qn1_tensor_array" not in name:
            continue
        predecessors = {}
        for cell in module["cells"].values():
            directions = cell.get("port_directions", {})
            inputs = {bit for port, bits in cell["connections"].items()
                      if directions.get(port) == "input" and port not in
                      ("clk", "rst_n", "flush", "ce")
                      for bit in bits if isinstance(bit, int)}
            outputs = {bit for port, bits in cell["connections"].items()
                       if directions.get(port) == "output"
                       for bit in bits if isinstance(bit, int)}
            for bit in outputs:
                predecessors.setdefault(bit, set()).update(inputs)
        reachable = set(module["ports"]["out_sum"]["bits"])
        pending = list(reachable)
        while pending:
            bit = pending.pop()
            for ancestor in predecessors.get(bit, ()):
                if ancestor not in reachable:
                    reachable.add(ancestor)
                    pending.append(ancestor)
        widths = {"q": 4, "z": 4, "scale_bf16": 16,
                  "activation_bf16": 16, "weight_bf16": 16, "lane_mask": 1}
        for lane in range(256):
            for port, width in widths.items():
                bits = module["ports"][port]["bits"][lane * width:(lane + 1) * width]
                if len(bits) != width or not all(bit in reachable for bit in bits):
                    raise AssertionError(f"tensor lane {lane} {port} cannot reach out_sum")
        records.append({"module": name, "reachable_output_ancestry_bits": len(reachable),
                        "connected_lanes": 256,
                        "method": "structural cell-port reachability, not functional equivalence"})
    if not records:
        raise AssertionError("tensor dataflow reachability not checked")
    return records


def run_synthesis_case(run, profile=3, compact=False, banks=8, queue=3,
                       vocabulary=8, maximum=16, head_dim=8, q_heads=2):
    sources = yosys_sources(run)
    parameters = {"PROFILE": profile, "BANKS": banks, "QUEUE_DEPTH": queue}
    if compact:
        parameters.update({"COMPACT": 1, "NUM_LAYERS": 1, "HIDDEN_SIZE": 8,
                           "INTERMEDIATE_SIZE": 8, "NUM_Q_HEADS": q_heads,
                           "NUM_KV_HEADS": 1, "HEAD_DIM": head_dim,
                           "VOCAB_SIZE": vocabulary, "MAX_SEQ_LEN": maximum,
                           "GROUP_SIZE": 8})
    hierarchy = run.path / "hierarchy.json"
    netlist = run.path / "coarse-synthesized.json"
    script = run.path / "synthesis.ys"
    script.write_text(
        "read_verilog -sv " + " ".join(sources) + "\n"
        "chparam " + " ".join(f"-set {key} {value}" for key, value in parameters.items()) +
        " anvil_qn1_top\n"
        "hierarchy -check -top anvil_qn1_top\n"
        "proc\nopt_expr\nopt_clean\ncheck -assert\n"
        f"write_json {relative(hierarchy)}\n"
        # Stop before Yosys's fine stage: it forcibly maps external-client RAMs.
        "synth -top anvil_qn1_top -noshare -noalumacc -run coarse:coarse\n"
        "hierarchy -check -top anvil_qn1_top\ncheck -assert\nstat\n"
        f"write_json {relative(netlist)}\n"
        "select anvil_qn1_top/native.bank_scheduler\n"
        "flatten\nselect anvil_qn1_top\nopt -full\nscc -expect 0\n"
        "check -assert\n")
    output = run.execute(["yosys", "-Q", "-T", "-s", relative(script)], "yosys-coarse-synthesis")
    before_data, before = retain_json(hierarchy)
    before_structure = inspect_netlist(before_data)
    before_connections = connected_tensor_lanes(before_data)
    del before_data
    data, artifact = retain_json(netlist)
    structure = inspect_netlist(data)
    connections = connected_tensor_lanes(data)
    if not re.search(r"Found 0 SCCs", output):
        raise AssertionError("optimized cross-hierarchy zero-SCC result missing")
    return {"parameters": parameters, "production": not compact,
            "hierarchy_netlist": before, "hierarchy": before_structure,
            "hierarchy_connections": before_connections,
            "synthesized_netlist": artifact, "synthesis": structure,
            "synthesized_connections": connections,
            "top_scheduler_combinational_scc": 0,
            "scope": "Yosys coarse synthesis with unmapped memories; not physical timing"}


def run_synthesis(run):
    cases = []
    for profile in (1, 2, 3):
        cases.append((f"synthesis-profile{profile}", {"profile": profile}))
    for index, (banks, queue, vocabulary, maximum, head_dim, q_heads) in enumerate((
            (1, 1, 1, 1, 8, 2),
            (8, 3, 8, 16, 8, 4),
            (1, 16, 8, 16, 128, 4),
            (8, 16, 8, 16, 128, 2))):
        cases.append((f"synthesis-boundary{index}",
                      {"compact": True, "banks": banks, "queue": queue,
                       "vocabulary": vocabulary, "maximum": maximum,
                       "head_dim": head_dim, "q_heads": q_heads}))

    def execute_case(case):
        stem, parameters = case
        return run.component(stem, lambda child: run_synthesis_case(child, **parameters))

    # Independent Yosys processes, no shared output paths or mutable build cache.
    # Three bounded workers keep the campaign within its whole-check deadline.
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(execute_case, cases))
    return {"cases": results, "case_count": len(results),
            "production_profiles": [1, 2, 3], "compact_boundaries": 4,
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
        "proc\nopt_expr\nopt_clean\ncheck -assert\n"
        f"write_json {relative(hierarchy)}\n"
        "memory -nomap\nopt_clean\ncheck -assert\nstat\n"
        f"write_json {relative(netlist)}\n"
        "select anvil_qn1_top/native.bank_scheduler\n"
        "flatten\nselect anvil_qn1_top\nopt -full\nscc -expect 0\n")
    run.execute(["yosys", "-Q", "-T", "-s", relative(script)], "yosys-compact-structural")
    _, before = retain_json(hierarchy)
    data, after = retain_json(netlist)
    structural = inspect_netlist(data)
    run.execute(["yosys", "-Q", "-T", "-p", "help synth"], "yosys-synth-help")
    return {"geometry": "compact H8/D8/Q2/K1/B1/QD3", "hierarchy": before,
            "structural_netlist": after, "structural": structural,
            "top_scheduler_combinational_scc": 0}


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
