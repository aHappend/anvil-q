"""Memory-preserving real Yosys synthesis with strict structural assertions."""

import json


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
        })
