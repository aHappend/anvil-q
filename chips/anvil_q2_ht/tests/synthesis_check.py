"""Actual-width generic synthesis and retained hierarchy/storage inspection."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment


REQUIRED = {
    "prefetcher": "anvil_q2_ht_ddr_prefetcher",
    "tile_buffers": "anvil_q2_ht_tile_buffers",
    "tensor_array": "anvil_q2_ht_tensor_array",
    "kv_cache": "anvil_q2_ht_kv_cache",
    "sequencer": "anvil_q2_ht_sequencer",
}


def lower_packages(snapshots, destination):
    """Expand wildcard imports verbatim; do not modify any executable expression."""
    packages = {}
    modules = {}
    for path in snapshots:
        text = path.read_text()
        match = re.fullmatch(r"\s*package\s+(\w+)\s*;([\s\S]*?)endpackage\s*", text)
        if match:
            packages[match[1]] = match[2]
        else:
            modules[path.name] = text
    if set(packages) != {"anvil_q2_ht_fp_pkg", "anvil_q2_ht_int_pkg"}:
        raise RuntimeError("unexpected package inventory; lowering requires explicit review")
    destination.mkdir()
    manifest = {}
    for name, text in modules.items():
        def expand(match):
            package = match[1]
            if package not in packages:
                raise RuntimeError("unknown wildcard package " + package)
            return packages[package]
        lowered = re.sub(r"import\s+(\w+)::\*\s*;", expand, text)
        if re.search(r"\bimport\b|::", lowered):
            raise RuntimeError("unsupported package construct")
        path = destination / name
        path.write_text(lowered)
        manifest[name] = {"original_sha256": hashlib.sha256(text.encode()).hexdigest(),
                          "expanded_sha256": hashlib.sha256(lowered.encode()).hexdigest()}
    return manifest


def inspect_netlist(path, top):
    netlist = json.loads(path.read_text())
    modules = netlist["modules"]
    if top not in modules:
        raise RuntimeError("missing synthesized top")
    top_module = modules[top]
    if len(top_module["ports"]) < (40 if top == "anvil_q2_ht_top" else 15):
        raise RuntimeError("synthesis top ports were reduced")
    required_instances = {}
    lane_instances = 0
    state_bits = 0
    memory_bits = 0
    forbidden = []

    def base_name(module):
        return modules[module].get("attributes", {}).get("hdlname", module).split()[0].lstrip("\\")

    def visit(name, prefix):
        nonlocal lane_instances, state_bits, memory_bits
        subtree_state = 0
        if base_name(name) == "anvil_q2_ht_tensor_lane":
            lane_instances += 1
        for cell_name, cell in modules[name].get("cells", {}).items():
            kind = cell["type"]
            location = prefix + "." + cell_name
            if kind in modules:
                child_state = visit(kind, location)
                leaf = cell_name.rsplit(".", 1)[-1]
                if prefix == top and leaf in REQUIRED:
                    if base_name(kind) != REQUIRED[leaf]:
                        raise RuntimeError("wrong required module type: " + location)
                    connections = cell.get("connections", {})
                    dynamic = sum(isinstance(bit, int)
                                  for bits in connections.values() for bit in bits)
                    if dynamic == 0 or child_state == 0:
                        raise RuntimeError("decorative/disconnected required instance " + location)
                    required_instances[leaf] = {"module": base_name(kind), "state_bits": child_state,
                                                "connected_bits": dynamic}
                subtree_state += child_state
            else:
                lower = kind.lower()
                if any(token in lower for token in ("latch", "$div", "$mod")):
                    forbidden.append({"path": location, "type": kind})
                if "dff" in lower:
                    bits = len(cell.get("connections", {}).get("Q", []))
                    state_bits += bits
                    subtree_state += bits
                if kind == "$mem_v2":
                    params = cell["parameters"]
                    bits = int(params["WIDTH"], 2) * int(params["SIZE"], 2)
                    memory_bits += bits
                    subtree_state += bits
        return subtree_state

    total_state = visit(top, top)
    if forbidden:
        raise RuntimeError("forbidden synthesized cells: " + json.dumps(forbidden[:10]))
    if lane_instances != 128 or total_state == 0:
        raise RuntimeError(f"physical lane/state inventory: lanes={lane_instances} state={total_state}")
    if top == "anvil_q2_ht_top" and (set(required_instances) != set(REQUIRED) or memory_bits == 0):
        raise RuntimeError("missing retained required hierarchy/storage")
    return {"top": top, "physical_lane_instances": lane_instances,
            "register_bits": state_bits, "memory_bits": memory_bits,
            "required_instances": required_instances, "forbidden_cells": forbidden,
            "scope": "coarse generic synthesis, not FPGA mapping or timing closure"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top", choices=("anvil_q2_ht_top", "anvil_q2_ht_tensor_array"),
                        default="anvil_q2_ht_top")
    parser.add_argument("--expand-packages", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    rtl = sorted(str(path.relative_to(root)) for path in (root / "rtl").glob("*.sv"))
    experiment = Experiment(root, args.output, sys.orig_argv,
                            rtl + ["tests/synthesis_check.py", "tests/retention.py"])
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        experiment.run(["yosys", "-V"], "yosys-version")
        sources = [experiment.directory / "sources" / name for name in rtl]
        if args.top == "anvil_q2_ht_tensor_array":
            array_names = {
                "anvil_q2_ht_00_fp_pkg.sv", "anvil_q2_ht_01_int_pkg.sv",
                "anvil_q2_ht_tensor_lane.sv", "anvil_q2_ht_add128_pipe.sv",
                "anvil_q2_ht_fp32_add_pipe.sv", "anvil_q2_ht_tensor_array.sv",
            }
            sources = [path for path in sources if path.name in array_names]
        if args.expand_packages:
            destination = experiment.directory / "expanded"
            experiment.receipt["package_expansion"] = lower_packages(sources, destination)
            sources = sorted(destination.glob("*.sv"))
        names = [str(path.relative_to(root)) for path in sources]
        output = args.output
        commands = [
            "read_verilog -sv " + " ".join(names),
            "hierarchy -check -top " + args.top,
            "proc",
            "opt -nosdff -nodffe",
            "memory_dff",
            "memory_collect",
            "opt_clean",
            "check -assert",
            "select -assert-none t:$dlatch t:$adlatch t:$dlatchsr",
            "select -assert-none t:$div t:$mod t:$divfloor t:$modfloor",
            "stat",
            "write_json " + str(output / "netlist.json"),
        ]
        script = experiment.directory / "synthesis.ys"
        script.write_text("\n".join(commands) + "\n")
        experiment.run(["yosys", "-Q", "-T", "-s", str(output / "synthesis.ys")],
                       "synthesize", timeout=14400)
        result = inspect_netlist(experiment.directory / "netlist.json", args.top)
        (experiment.directory / "structure.json").write_text(json.dumps(result, indent=2) + "\n")
        experiment.receipt["structure"] = result
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
