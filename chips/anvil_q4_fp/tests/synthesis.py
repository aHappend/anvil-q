"""Memory-preserving generic Yosys checks, not FPGA fit or timing evidence."""

import argparse
from collections import Counter
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative, source_hashes


def lower_packages(destination):
    """Equivalent syntax lowering for Yosys 0.33, without RTL substitutions."""
    packages, modules = {}, []
    for path in sorted((ROOT / "rtl").glob("*.sv")):
        text = path.read_text()
        package = re.fullmatch(r"\s*package\s+(\w+)\s*;(.*)endpackage\s*",
                               text, flags=re.S)
        if package:
            packages[package[1]] = package[2]
        else:
            modules.append((path, text))
    result = []
    for path, text in modules:
        imports = set(re.findall(r"import\s+(\w+)::\*\s*;", text))
        qualified = set(re.findall(r"(\w+)::", text)) - imports
        text = re.sub(r"import\s+(\w+)::\*\s*;",
                      lambda m: packages[m[1]], text)
        if qualified:
            end_header = text.index(";", text.index("module ")) + 1
            text = (text[:end_header] +
                    "\n".join(packages[name] for name in sorted(qualified)) +
                    text[end_header:])
        for name in packages:
            text = text.replace(name + "::", "")
        text = re.sub(r"\binteger'\((\w+)\)", r"$signed(32'(\1))", text)
        signed_ports = []

        def signed_port(match):
            name = f"__yosys_signed_port_{len(signed_ports)}"
            expression = match[2]
            signed_ports.append(
                f"wire signed [$bits({expression})-1:0] {name};\n"
                f"assign {name}=$signed({expression});\n")
            return f".{match[1]}({name})"

        # Older Yosys returns an unsigned wire for a width-preserving $signed
        # cell argument, then asserts on its own AST signedness invariant.
        text = re.sub(r"\.(\w+)\(\$signed\(([^()]*)\)\)", signed_port, text)
        if signed_ports:
            text = text.replace("endmodule", "\n" + "".join(signed_ports) + "\nendmodule")
        result.append(f"// Source: {relative(path)}\n{text}")
    destination.write_text("\n".join(result))


def inspect(netlist, geometry):
    modules = netlist["modules"]
    top = modules["anvil_q4_fp_top"]
    counts = Counter(cell["type"] for module in modules.values()
                     for cell in module.get("cells", {}).values())
    prohibited = {name: count for name, count in counts.items()
                  if "latch" in name.lower() or name in (
                      "$div", "$mod", "$divfloor", "$modfloor")}
    if prohibited:
        raise AssertionError(f"Forbidden synthesis cells: {prohibited}")
    for name, module in modules.items():
        if int(module.get("attributes", {}).get("blackbox", "0"), 2):
            raise AssertionError(f"Unresolved black box: {name}")
        for cell in module.get("cells", {}).values():
            if not cell["type"].startswith("$") and cell["type"] not in modules:
                raise AssertionError(f"Unresolved cell: {cell['type']}")
    sequential = sum(count for name, count in counts.items()
                     if "dff" in name.lower())
    if not sequential:
        raise AssertionError("Empty sequential state")
    banks, queue, tile_k, rows = geometry
    if len(top["ports"]["mem_req_valid"]["bits"]) != banks:
        raise AssertionError("External bank count")
    paths = {}

    def walk(module_name, prefix=""):
        for name, cell in modules[module_name].get("cells", {}).items():
            path = prefix + "." + name if prefix else name
            if cell["type"] in modules:
                paths[path] = cell
                walk(cell["type"], path)

    walk("anvil_q4_fp_top")
    native = {path: cell for path, cell in paths.items() if "compatibility" not in path}
    for suffix in ("descriptor", "bank_scheduler", "speculative", "token_io",
                   "decoder", "final_norm"):
        if not any(path.endswith("." + suffix) for path in native):
            raise AssertionError(f"Missing native hierarchy: {suffix}")
    schedulers = [cell for path, cell in native.items() if path.endswith(".bank_scheduler")]
    if len(schedulers) != 1 or len(schedulers[0]["connections"]["c_req_valid"]) != 17:
        raise AssertionError("Native scheduler must have seventeen clients")
    arrays = [(path, cell) for path, cell in native.items() if path.endswith(".tensor_array")]
    if len(arrays) != 3:
        raise AssertionError(f"Expected decoder, MLP, LM-head tensor arrays, got {len(arrays)}")
    array_records = []
    for path, array in arrays:
        cells = modules[array["type"]]["cells"]
        lanes = [cell for name, cell in cells.items() if "tensor_lanes" in name
                 and name.endswith(".arithmetic")]
        if len(lanes) != rows:
            raise AssertionError(f"Tensor lane count {path}: {len(lanes)} != {rows}")
        array_records.append({"path": path, "arithmetic_lanes": len(lanes)})
    memory_bits = 0
    for module in modules.values():
        for cell in module.get("cells", {}).values():
            if cell["type"].startswith("$mem"):
                parameters = cell["parameters"]
                if "SIZE" in parameters and "WIDTH" in parameters:
                    memory_bits += int(parameters["SIZE"], 2) * int(parameters["WIDTH"], 2)
    if memory_bits < 131072 * 32:
        raise AssertionError("Large score memories were not retained as memories")
    return {"geometry": geometry, "sequential_cell_definitions": sequential,
            "memory_bits_in_module_definitions": memory_bits,
            "forbidden_cells": prohibited, "tensor_arrays": array_records,
            "native_scheduler_clients": 17, "external_banks": banks,
            "cell_types": dict(counts)}


def run(preparation=False, geometries=None, repair_of=None):
    directory = new_run("synthesis", preparation)
    lowered = directory / "package-lowered.sv"
    lower_packages(lowered)
    records = []
    for index, geometry in enumerate(geometries or (
            (16, 3, 128, 16), (1, 1, 1, 1), (4, 3, 3, 3))):
        banks, queue, tile_k, rows = geometry
        destination = directory / f"netlist-{index}.json"
        script = directory / f"script-{index}.ys"
        script.write_text(
            f"read_verilog -sv -noopt -defer {relative(lowered)}\n"
            "hierarchy -check -top anvil_q4_fp_top "
            f"-chparam BANKS {banks} -chparam QUEUE_DEPTH {queue} "
            f"-chparam TILE_K {tile_k} -chparam TILE_ROWS {rows}\n"
            "proc\nopt_expr\nopt_clean\ncheck -assert -noinit\n"
            "memory -nomap\nopt_clean\ncheck -assert -noinit\n"
            f"write_json {relative(destination)}\n")
        execute(directory / f"yosys-{index}", [
            "yosys", "-Q", "-T", "-L", relative(directory / f"yosys-{index}.log"),
            "-s", relative(script)],
                timeout=1800, repair_of=repair_of)
        records.append(inspect(json.loads(destination.read_text()), geometry))
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "geometries": records,
        "scope": "generic synthesis only, not device timing or fit"}, indent=2) + "\n")
    print(f"Synthesis receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--singleton", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run(args.preparation, [(1, 1, 1, 1)] if args.singleton else None, args.repair_of)
