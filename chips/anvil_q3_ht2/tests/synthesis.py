"""Real Yosys memory-preserving structural synthesis checks."""

import argparse
import collections
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import execute, new_run, relative


def run_synthesis(run, top, mode=1, parameters=None):
    inputs = {
        "anvil_q3_ht2_sparse_dma": ["rtl/anvil_q3_ht2_sparse_dma.sv"],
        "anvil_q3_ht2_ddr_arbiter": ["rtl/anvil_q3_ht2_ddr_arbiter.sv"],
        "anvil_q3_ht2_private_scratch": ["rtl/anvil_q3_ht2_private_scratch.sv"],
        "anvil_q3_ht2_kv_commit_engine": [
            "anvil_q3_ht_reference/rtl/anvil_q3_ht_kv_codec.sv",
            "rtl/anvil_q3_ht2_kv_commit_engine.sv"],
        "anvil_q3_ht2_spec_verifier": [
            "anvil_q3_ht_reference/rtl/anvil_q3_ht_kv_codec.sv",
            "rtl/anvil_q3_ht2_kv_commit_engine.sv",
            "rtl/anvil_q3_ht2_spec_verifier.sv"],
    }[top]
    cached = top in ("anvil_q3_ht2_kv_commit_engine", "anvil_q3_ht2_spec_verifier")
    netlist = run / f"{top}.json"
    script = run / f"{top}.ys"
    script.write_text("\n".join([
        f"read_verilog -sv {' '.join(inputs)}",
        *([f"chparam -set CACHE_MODE {mode} {top}"] if cached else []),
        *[f"chparam -set {name} {value} {top}"
          for name, value in (parameters or {}).items()],
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
    if top == "anvil_q3_ht2_sparse_dma" and memory_bits < (
            (parameters or {}).get("MAX_COLUMNS", 11008) * 68):
        raise AssertionError("production scan banks were not retained as live memory")
    if top == "anvil_q3_ht2_private_scratch":
        memories = {name: cell for module in data["modules"].values()
                    for name, cell in module["cells"].items() if cell["type"] == "$mem_v2"}
        expected_depth = 10 * 2048 + 3 * 11008 + 2 * 2 * 128
        for bank in range(4):
            for kind, width in (("words", 32), ("initialized", 1)):
                suffix = f"token_bank[{bank}].{kind}"
                matching = [cell for name, cell in memories.items() if name.endswith(suffix)]
                if len(matching) != 1 or (
                        int(matching[0]["parameters"]["WIDTH"], 2),
                        int(matching[0]["parameters"]["SIZE"], 2)) != (width, expected_depth):
                    raise AssertionError(f"production scratch RAM not retained: {suffix}")
    ports = data["modules"][top]["ports"]
    for name, port in ports.items():
        if port["direction"] == "output" and name in (
                "weight_data", "memory_req_address", "memory_req_wdata",
                "out_tokens", "visible_count", "c_rsp_rdata", "avm_address"):
            if all(isinstance(bit, str) for bit in port["bits"]):
                raise AssertionError(f"functional output synthesized to constant: {name}")
    if top == "anvil_q3_ht2_spec_verifier":
        instances = data["modules"][top]["cells"]
        engines = [cell for name, cell in instances.items()
                   if name.endswith("kv_commit_engine")]
        if len(engines) != 1 or not engines[0]["connections"]:
            raise AssertionError("literal atomic engine hierarchy/connection missing")
        for port in ("cmd_valid", "stage_record", "commit_valid", "memory_req_address"):
            if not any(isinstance(bit, int) for bit in engines[0]["connections"][port]):
                raise AssertionError(f"atomic engine connection is constant: {port}")
    summary = {"top": top, "cache_mode": mode if cached else None,
               "parameters": parameters or {},
               "cell_types": dict(cells), "sequential_cells": state,
               "memory_bits": memory_bits, "latches": 0, "div_mod": 0,
               "receipt": relative(result / "receipt.json")}
    (run / "synthesis-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", choices=["anvil_q3_ht2_sparse_dma", "anvil_q3_ht2_ddr_arbiter",
                                        "anvil_q3_ht2_kv_commit_engine",
                                        "anvil_q3_ht2_spec_verifier",
                                        "anvil_q3_ht2_private_scratch"],
                        default="anvil_q3_ht2_sparse_dma")
    parser.add_argument("--mode", type=int, choices=(1, 2), default=1)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run = new_run("synthesis", preparation=True, repair_of=args.repair_of)
    print(f"synthesis evidence: {relative(run)}", flush=True)
    try:
        print(json.dumps(run_synthesis(run, args.top, args.mode), sort_keys=True))
    except (RuntimeError, AssertionError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
