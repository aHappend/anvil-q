"""Memory-preserving generic Yosys synthesis; never physical timing/PPA."""

import json
import re

from execution import ROOT, relative


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
    result = {"parameters": parameters, "generic_cell_definitions": counts,
              "generic_memory_definition_bits": memory_bits,
              "netlist": relative(directory / "netlist.json"), "physical_ppa": False}
    (directory / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
