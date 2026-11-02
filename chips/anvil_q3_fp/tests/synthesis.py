"""Memory-preserving generic Yosys synthesis; never physical timing/PPA."""

import json
import re

from execution import ROOT, relative


def output_cone(module):
    """Conservative structural fan-in, retaining sequential and RAM dependencies."""
    drivers = {}
    cells = module.get("cells", {})
    for name, cell in cells.items():
        for port, direction in cell["port_directions"].items():
            if direction == "output":
                for bit in cell["connections"][port]:
                    if isinstance(bit, int):
                        drivers.setdefault(bit, []).append(name)
    work = [bit for port in module.get("ports", {}).values() if port["direction"] == "output"
            for bit in port["bits"] if isinstance(bit, int)]
    bits, reached = set(), set()
    while work:
        bit = work.pop()
        if bit in bits:
            continue
        bits.add(bit)
        for name in drivers.get(bit, []):
            if name in reached:
                continue
            reached.add(name)
            cell = cells[name]
            work.extend(bit for port, direction in cell["port_directions"].items()
                        if direction == "input" for bit in cell["connections"][port]
                        if isinstance(bit, int) and bit not in bits)
    return reached


def structure(modules, banks):
    paths, counts, memory_bits = [], {}, 0
    active_paths = []
    def visit(name, prefix="", active=True):
        nonlocal memory_bits
        module = modules[name]
        cone = output_cone(module)
        for instance, cell in module.get("cells", {}).items():
            path = prefix + instance
            kind = cell["type"]
            paths.append(path)
            live = active and instance in cone
            if live:
                active_paths.append(path)
            if kind in modules:
                visit(kind, path + ".", live)
            else:
                counts[kind] = counts.get(kind, 0) + 1
                if kind == "$mem_v2":
                    memory_bits += int(cell["parameters"]["WIDTH"], 2) * int(cell["parameters"]["SIZE"], 2)
    visit("anvil_q3_fp_top")
    required = ("decoder", "final_norm", "token_io", "bank_scheduler",
                "decoder.norm", "decoder.gemv", "decoder.rope", "decoder.attention",
                "decoder.mlp", "decoder.residual", "decoder.gemv.tensor_array",
                "decoder.gemv.tensor_array.weight_prefetcher")
    for path in required:
        if path not in active_paths:
            raise AssertionError(f"Required hierarchy absent from public output cone: {path}")
    base = "decoder.gemv.tensor_array."
    for bank in range(banks):
        for path in (base + f"engines[{bank}].dot8",
                     base + f"engines[{bank}].accumulator",
                     base + f"weight_prefetcher.banks[{bank}].storage"):
            if path not in active_paths:
                raise AssertionError(f"Bank arithmetic/prefetch bypassed: {path}")
        storage = base + f"weight_prefetcher.banks[{bank}].storage."
        if not any(path.startswith(storage) and "weight_storage" in path for path in active_paths):
            raise AssertionError(f"Native weight tile RAM not in output cone for bank {bank}")
    scheduler = modules[modules["anvil_q3_fp_top"]["cells"]["bank_scheduler"]["type"]]
    scheduler_cone = output_cone(scheduler)
    if not any(name in scheduler_cone and cell["type"] in ("$dff", "$adff", "$sdff", "$dffe", "$adffe")
               for name, cell in scheduler["cells"].items()):
        raise AssertionError("Scheduler state missing from output cone")
    if memory_bits == 0 or counts.get("$mul", 0) == 0:
        raise AssertionError("Synthesis lost all memories or actual multipliers")
    return {"generic_instantiated_cells": counts, "generic_instantiated_memory_bits": memory_bits,
            "active_hierarchy_paths": [path for path in active_paths if not path.split(".")[-1].startswith("$")],
            "cone_analysis": "conservative structural public-output fan-in, not functional equivalence proof"}


def adapted_sources(directory, rtl_root=None):
    """Inline only the common SV package for the installed Verilog frontend."""
    rtl_root = rtl_root or ROOT / "rtl"
    package = (rtl_root / "anvil_q3_fp_00_pkg.sv").read_text()
    body = package.split("package anvil_q3_fp_pkg;", 1)[1].rsplit("endpackage", 1)[0]
    directory.mkdir()
    outputs = []
    for path in sorted(rtl_root.glob("*.sv")):
        if path.name == "anvil_q3_fp_00_pkg.sv":
            continue
        text = path.read_text().replace("import anvil_q3_fp_pkg::*;", "")
        text = text.replace("anvil_q3_fp_pkg::", "")
        text = re.sub(r"(module\s+\w+\b[\s\S]*?\)\s*;)", lambda match: match[0] + "\n" + body, text)
        output = directory / path.name
        output.write_text(text)
        outputs.append(relative(output))
    outputs += ["anvil_q3_reference/rtl/anvil_q3_bank_scheduler.sv",
                "anvil_q3_reference/rtl/anvil_q3_mem_port.sv"]
    return outputs


def synthesize(evidence, banks=1, mode=0, fp8=0, affine=0, production=False):
    directory = evidence.path / f"synth-b{banks}-m{mode}-f{fp8}-a{affine}-p{int(production)}"
    directory.mkdir()
    inputs = adapted_sources(directory / "inputs")
    parameters = {"BANKS": banks, "CACHE_MODE": mode, "MODE1_FP8": fp8, "INT4_ASYM": affine}
    if not production:
        parameters.update(NUM_LAYERS=1, HIDDEN_SIZE=16, INTERMEDIATE_SIZE=24,
                          NUM_Q_HEADS=8, NUM_KV_HEADS=1, HEAD_DIM=2, GROUP_SIZE=8,
                          VOCAB_SIZE=1, MAX_SEQ_LEN=1, TILE_K=8, TILE_ROWS=3)
    script = "read_verilog -sv " + " ".join(inputs) + "\n"
    script += "hierarchy -check -top anvil_q3_fp_top " + " ".join(
        f"-chparam {key} {value}" for key, value in parameters.items()) + "\n"
    script += ("proc\nopt_expr\nopt_clean\ncheck -assert -noinit\n"
               "memory -nomap\nopt_clean\nwreduce\nopt_clean\ncheck -assert -noinit\n"
               "stat\nwrite_json " + relative(directory / "netlist.json") + "\n")
    (directory / "synthesis.ys").write_text(script)
    evidence.run(["yosys", "-Q", "-T", "-s", relative(directory / "synthesis.ys")])
    modules = json.loads((directory / "netlist.json").read_text())["modules"]
    forbidden, blackboxes = [], []
    counts = {}
    memory_bits = 0
    for name, module in modules.items():
        if int(module.get("attributes", {}).get("blackbox", "0"), 2):
            blackboxes.append(name)
        for cell_name, cell in module.get("cells", {}).items():
            kind = cell["type"]
            counts[kind] = counts.get(kind, 0) + 1
            if kind in ("$dlatch", "$adlatch", "$dlatchsr", "$div", "$mod", "$divfloor", "$modfloor"):
                forbidden.append((name, cell_name, kind))
            if kind == "$mem_v2":
                parameter = cell["parameters"]
                memory_bits += int(parameter["WIDTH"], 2) * int(parameter["SIZE"], 2)
    if forbidden or blackboxes:
        raise AssertionError(f"Forbidden synthesis structures: {forbidden}; blackboxes={blackboxes}")
    if memory_bits == 0:
        raise AssertionError("Lost all memory inference")
    required = {"decoder", "final_norm", "token_io", "bank_scheduler", "norm", "gemv",
                "rope", "attention", "mlp", "residual", "tensor_array", "weight_prefetcher"}
    instances = {name.split(".")[-1] for module in modules.values() for name in module.get("cells", {})}
    if required - instances:
        raise AssertionError(f"Missing required hierarchy: {sorted(required - instances)}")
    connectivity = structure(modules, banks)
    result = {"parameters": parameters, "generic_cell_definitions": counts,
              "generic_memory_definition_bits": memory_bits,
              "netlist": relative(directory / "netlist.json"), "physical_ppa": False,
              "structure": connectivity}
    (directory / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
