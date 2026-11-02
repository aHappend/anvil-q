"""Memory-preserving real Yosys synthesis with strict structural assertions."""

import json
from collections import defaultdict, deque


SUBSTANTIVE = (
    "anvil_q1_fp2_bfp_tensor_array", "anvil_q1_fp2_fast_rsqrt",
    "anvil_q1_fp2_epilogue_fusion", "anvil_q1_fp2_flash_attn",
    "anvil_q1_fp2_telemetry_csr", "anvil_q1_fp2_ddr_pingpong",
    "anvil_q1_fp2_decoder_control", "anvil_q1_fp2_projection",
    "anvil_q1_fp2_gqa_group", "anvil_q1_fp2_kv_reader",
    "anvil_q1_fp2_kv_writer", "anvil_q1_fp2_ddr_read_stream",
    "anvil_q1_fp2_mx_quantize", "anvil_q1_fp2_exp",
    "anvil_q1_fp2_reciprocal", "anvil_q1_fp2_fp32_binary",
)


def assert_integrated_hierarchy(design):
    root = design["modules"]["anvil_q1_fp2_top"]
    expected = {
        "tensor_array": ("anvil_q1_fp2_bfp_tensor_array", "result"),
        "epilogue_fusion": ("anvil_q1_fp2_epilogue_fusion", "out_data"),
        "flash_attn": ("anvil_q1_fp2_flash_attn", "out_data"),
        "telemetry_csr": ("anvil_q1_fp2_telemetry_csr", "csr_rsp_rdata"),
        "ddr_pingpong": ("anvil_q1_fp2_ddr_pingpong", "out_data"),
        "decoder_control": ("anvil_q1_fp2_decoder_control", "logit_data"),
    }
    drivers = defaultdict(list)
    for name, cell in root["cells"].items():
        for port, direction in cell["port_directions"].items():
            if direction == "output":
                for bit in cell["connections"][port]:
                    if isinstance(bit, int):
                        drivers[bit].append(name)
    pending = deque(
        bit for port in root["ports"].values() if port["direction"] == "output"
        for bit in port["bits"] if isinstance(bit, int)
    )
    reachable_bits, reachable_cells = set(), set()
    while pending:
        bit = pending.popleft()
        if bit in reachable_bits:
            continue
        reachable_bits.add(bit)
        for name in drivers[bit]:
            if name in reachable_cells:
                continue
            reachable_cells.add(name)
            cell = root["cells"][name]
            pending.extend(
                source for port, direction in cell["port_directions"].items()
                if direction == "input" for source in cell["connections"][port]
                if isinstance(source, int)
            )
    identities = {}
    for instance, (module_name, data_port) in expected.items():
        cell = root["cells"].get(instance)
        if cell is None:
            raise AssertionError(f"missing literal root instance {instance}")
        module = design["modules"][cell["type"]]
        identity = module.get("attributes", {}).get("hdlname", cell["type"]).split()[0].lstrip("\\")
        if identity != module_name:
            raise AssertionError(f"{instance}: incorrect synthesized identity {identity}")
        bits = {bit for bit in cell["connections"][data_port] if isinstance(bit, int)}
        if instance not in reachable_cells or not bits.intersection(reachable_bits):
            raise AssertionError(f"{instance}.{data_port}: disconnected from architectural outputs")
        if not module.get("cells"):
            raise AssertionError(f"{instance}: empty implementation")
        identities[instance] = identity
    epilogue = design["modules"][root["cells"]["epilogue_fusion"]["type"]]
    fast = epilogue["cells"].get("fast_rsqrt")
    if fast is None or fast["type"] != "anvil_q1_fp2_fast_rsqrt":
        raise AssertionError("epilogue lacks the substantive named fast_rsqrt instance")
    return identities


def synthesize(run, root, tops=None):
    run.version("yosys")
    sources = [
        *sorted(root.glob("anvil_q1_fp_reference/rtl/*.sv")),
        *sorted(root.glob("rtl/*.sv")),
    ]
    for top in tops or ("anvil_q1_fp2_top", *SUBSTANTIVE):
        directory = run.path / top
        directory.mkdir()
        script = directory / "synthesis.ys"
        netlist = run.relative / top / "netlist.json"
        script.write_text(
            "read_verilog -defer -sv " + " ".join(str(source.relative_to(root)) for source in sources) +
            f"\nhierarchy -check -top {top}\n"
            "proc\nopt_expr\nopt_clean\ncheck -assert\n"
            # Collect memories without mapping to registers or invoking the optional
            # quadratic write-priority/SAT sharing optimizations on wide bank stores.
            "memory_dff\nmemory_collect\nopt_clean\ncheck -assert\n"
            "select -assert-none t:$dlatch t:$adlatch t:$dlatchsr "
            "t:$div t:$mod t:$divfloor t:$modfloor\n"
            f"stat\nwrite_json {netlist}\n"
        )
        run.command(["yosys", "-Q", "-T", "-s", str(script.relative_to(root))],
                    top + "-synthesis")
        design = json.loads((root / netlist).read_text())
        hierarchy = assert_integrated_hierarchy(design) if top == "anvil_q1_fp2_top" else None
        counts = {}
        for module in design["modules"].values():
            if str(module.get("attributes", {}).get("blackbox", "0")).strip("0"):
                raise AssertionError(f"{top}: unexpected blackbox")
            for cell in module.get("cells", {}).values():
                cell_type = cell["type"]
                counts[cell_type] = counts.get(cell_type, 0) + 1
                if any(marker in cell_type.lower() for marker in ("latch", "$div", "$mod")):
                    raise AssertionError(f"{top}: forbidden cell {cell_type}")
        sequential = sum(count for name, count in counts.items() if "dff" in name.lower())
        arithmetic = sum(counts.get(name, 0) for name in ("$add", "$sub", "$mul", "$macc"))
        if not sequential or not arithmetic:
            raise AssertionError(f"{top}: absent sequential/arithmetic structure: {counts}")
        run.receipt["comparisons"].append({
            "top": top, "sequential_cells": sequential, "arithmetic_cells": arithmetic,
            "cell_counts": counts, "result": "passed",
            "integrated_hierarchy": hierarchy,
        })
