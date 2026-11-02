"""Real Yosys memory-preserving structural synthesis checks."""

import argparse
import collections
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import execute, new_run, relative


def run_synthesis(run, top):
    inputs = {
        "anvil_q3_ht2_sparse_dma": ["rtl/anvil_q3_ht2_sparse_dma.sv"],
        "anvil_q3_ht2_ddr_arbiter": ["rtl/anvil_q3_ht2_ddr_arbiter.sv"],
    }[top]
    netlist = run / f"{top}.json"
    script = run / f"{top}.ys"
    script.write_text("\n".join([
        f"read_verilog -sv {' '.join(inputs)}",
        f"hierarchy -check -top {top}", "proc", "opt_expr", "opt_clean",
        "check -assert", "memory -nomap", "opt_clean", "check -assert",
        "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod t:$divfloor t:$modfloor",
        "stat", f"write_json {relative(netlist)}", "",
    ]))
    result = execute(run, f"synthesis-{top}", ["yosys", "-s", relative(script)],
                     ["yosys", "-V"])
    data = json.loads(netlist.read_text())
    cells = collections.Counter(cell["type"] for module in data["modules"].values()
                                for cell in module["cells"].values())
    forbidden = [name for name in cells if "latch" in name.lower() or
                 name in ("$div", "$mod", "$divfloor", "$modfloor")]
    if forbidden:
        raise AssertionError(f"forbidden synthesized cells: {forbidden}")
    state = sum(count for name, count in cells.items() if "dff" in name.lower())
    if state == 0:
        raise AssertionError("no substantive sequential state in synthesized DUT")
    memory_bits = 0
    for module in data["modules"].values():
        for cell in module["cells"].values():
            if cell["type"] == "$mem_v2":
                memory_bits += int(cell["parameters"]["WIDTH"], 2) * int(
                    cell["parameters"]["SIZE"], 2)
    if top == "anvil_q3_ht2_sparse_dma" and memory_bits < 11008 * 68:
        raise AssertionError("production scan banks were not retained as live memory")
    ports = data["modules"][top]["ports"]
    for name, port in ports.items():
        if port["direction"] == "output" and name in (
                "weight_data", "memory_req_address", "c_rsp_rdata", "avm_address"):
            if all(isinstance(bit, str) for bit in port["bits"]):
                raise AssertionError(f"functional output synthesized to constant: {name}")
    summary = {"top": top, "cell_types": dict(cells), "sequential_cells": state,
               "memory_bits": memory_bits, "latches": 0, "div_mod": 0,
               "receipt": relative(result / "receipt.json")}
    (run / "synthesis-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", choices=["anvil_q3_ht2_sparse_dma", "anvil_q3_ht2_ddr_arbiter"],
                        default="anvil_q3_ht2_sparse_dma")
    args = parser.parse_args()
    run = new_run("synthesis", preparation=True)
    print(f"synthesis evidence: {relative(run)}", flush=True)
    try:
        print(json.dumps(run_synthesis(run, args.top), sort_keys=True))
    except (RuntimeError, AssertionError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
