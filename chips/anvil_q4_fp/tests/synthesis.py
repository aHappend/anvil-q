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
    routing = inspect_routing(modules, top)
    return {"geometry": geometry, "sequential_cell_definitions": sequential,
            "memory_bits_in_module_definitions": memory_bits,
            "forbidden_cells": prohibited, "tensor_arrays": array_records,
            "native_scheduler_clients": 17, "external_banks": banks,
            "lane_connectivity": routing,
            "cell_types": dict(counts)}


def inspect_routing(modules, top):
    """Prove literal per-lane wiring, including both directions of every bundle."""
    fields = {"req_valid": 1, "req_ready": 1, "req_write": 1, "req_kind": 4,
              "req_proj": 3, "req_layer": 32, "req_row": 32, "req_col": 32,
              "req_wdata": 32, "req_stride": 32, "rsp_valid": 1, "rsp_ready": 1,
              "rsp_error": 1, "rsp_rdata": 32}
    records = []

    def cell(module, suffix):
        found = [c for name, c in module["cells"].items()
                 if name == suffix or name.endswith("." + suffix)]
        if len(found) != 1:
            raise AssertionError(f"Expected single routing instance {suffix}")
        return found[0]

    def equal(actual, expected, label):
        if actual != expected:
            raise AssertionError(f"Lane wiring mismatch: {label}")

    def edges(module, mux_name, children, label):
        mux = cell(module, mux_name)
        connections = mux["connections"]
        for field, width in fields.items():
            if field == "req_stride" and label == "top-scheduler":
                continue
            for name, client in children:
                child = cell(module, name)
                expected = connections["c_" + field][client*17*width:(client+1)*17*width]
                equal(child["connections"]["mem_" + field], expected,
                      f"{label}.{name}.{field}")
        if label != "top-scheduler":
            for field in fields:
                equal(connections["mem_" + field], module["ports"]["mem_" + field]["bits"],
                      f"{label}.parent.{field}")
        mux_module = modules[mux["type"]]
        clients = len(mux_module["ports"]["c_req_valid"]["bits"]) // 17
        for lane in range(17):
            owner = cell(mux_module, f"channels[{lane}].ownership")
            for field, width in fields.items():
                expected = [bit for client in range(clients)
                            for bit in mux_module["ports"]["c_" + field]["bits"][
                                (client*17+lane)*width:(client*17+lane+1)*width]]
                equal(owner["connections"]["c_" + field], expected,
                      f"{label}.lane{lane}.clients.{field}")
                equal(owner["connections"]["mem_" + field],
                      mux_module["ports"]["mem_" + field]["bits"][lane*width:(lane+1)*width],
                      f"{label}.lane{lane}.external.{field}")
        records.append({"stage": label, "channels": 17, "payload_and_handshake_fields": len(fields),
                        "children": [{"instance": name, "client": client} for name, client in children]})
        return mux

    decoder = cell(top, "decoder")
    io = cell(top, "token_io")
    dec_module = modules[decoder["type"]]
    io_module = modules[io["type"]]
    mlp = cell(dec_module, "mlp")
    edges(dec_module, "routing", (("gemv", 1), ("mlp", 5)), "decoder")
    edges(modules[mlp["type"]], "routing", (("gemv", 0),), "MLP")
    edges(io_module, "routing", (("lm_head", 1),), "LM-head")
    stage = edges(top, "stage_routing", (("token_io", 0), ("decoder", 1)), "top-scheduler")
    scheduler = cell(top, "bank_scheduler")
    for field in fields:
        equal(stage["connections"]["mem_" + field], scheduler["connections"]["c_" + field],
              f"scheduler.{field}")
    return records


def run(preparation=False, geometries=None, repair_of=None):
    directory = new_run("synthesis", preparation)
    lowered = directory / "package-lowered.sv"
    lower_packages(lowered)
    records = []
    minimum_netlist = None
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
        if geometry == (1, 1, 1, 1):
            minimum_netlist = destination
    import identity
    identity_directory = identity.run(preparation)
    if minimum_netlist is None:
        raise AssertionError("Synthesis requires the singleton geometry for the top control proof")
    epoch_directory = identity.top_epoch(minimum_netlist, preparation)
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "geometries": records,
        "scheduler_boundary_proofs": relative(identity_directory),
        "top_epoch_boundary_proof": relative(epoch_directory),
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
