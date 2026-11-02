"""Memory-preserving Yosys checks, with public ports left unconstrained."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import Evidence, ROOT, rel


COMPACT = dict(NUM_LAYERS=2, HIDDEN_SIZE=16, INTERMEDIATE_SIZE=16,
               NUM_Q_HEADS=2, KV_LORA_RANK=3, QK_NOPE_HEAD_DIM=2,
               QK_ROPE_HEAD_DIM=2, V_HEAD_DIM=2, ROUTED_EXPERTS=7,
               TOP_K=6, SHARED_EXPERTS=2, MOE_INTERMEDIATE_SIZE=8,
               FIRST_DENSE_LAYERS=1, VOCAB_SIZE=8, MAX_SEQ_LEN=5,
               BANKS=2, QUEUE_DEPTH=3, TILE_K=8, TILE_ROWS=3)


def synthesize(evidence, top="anvil_d1_top", parameters=None):
    sources = sorted(ROOT.glob("anvil_q3_reference/rtl/*.sv")) + sorted(ROOT.glob("rtl/*.sv"))
    params = "".join(f" -chparam {name} {value}" for name, value in (parameters or {}).items())
    output = evidence.path / "netlist.json"
    script = (
        "read_verilog -defer -sv " + " ".join(rel(p) for p in sources) + ";\n"
        f"hierarchy -check -top {top}{params};\n"
        "proc; opt_expr; opt_clean; check -assert -noinit;\n"
        "memory -nomap; opt_clean; check -assert -noinit; stat;\n"
        f"write_json {rel(output)};\n"
    )
    script_path = evidence.path / "synthesis.ys"
    script_path.write_text(script)
    evidence.run("synthesis", ["yosys", "-Q", "-T", "-s", rel(script_path)], ["yosys", "-V"])
    netlist = json.loads(output.read_text())
    modules = netlist["modules"]
    prohibited = []
    counts = {}
    memory_bits = 0
    active_ports = sum(len(p["bits"]) for p in modules[top]["ports"].values())
    for name, module in modules.items():
        for cell_name, cell in module.get("cells", {}).items():
            kind = cell["type"]
            counts[kind] = counts.get(kind, 0) + 1
            lower = kind.lower()
            if "latch" in lower or kind in ("$div", "$mod", "$divfloor", "$modfloor"):
                prohibited.append([name, cell_name, kind])
            if kind not in modules and not kind.startswith("$"):
                prohibited.append([name, cell_name, "unresolved:" + kind])
            if kind == "$mem_v2":
                memory_parameters = cell["parameters"]
                memory_bits += (int(memory_parameters["SIZE"], 2) *
                                int(memory_parameters["WIDTH"], 2))
    if prohibited:
        raise AssertionError(f"prohibited synthesis cells: {prohibited[:10]}")
    registers = sum(v for k, v in counts.items() if "dff" in k.lower())
    if not registers or not active_ports or len(modules) < 3:
        raise AssertionError("synthesis lost state, ports, or hierarchy")
    summary = dict(top=top, parameters=parameters or {}, module_definitions=len(modules),
                   cell_types=counts, memory_bits_in_module_definitions=memory_bits,
                   register_cells_in_module_definitions=registers,
                   top_port_bits=active_ports, prohibited_cells=prohibited)
    (evidence.path / "structure.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of")
    parser.add_argument("--top", choices=["anvil_d1_top", "anvil_d1_exp", "anvil_d1_silu"],
                        default="anvil_d1_top")
    args = parser.parse_args()
    stem = "compact-synthesis" if args.top == "anvil_d1_top" else (
        args.top.removeprefix("anvil_d1_") + "-synthesis")
    evidence = Evidence(stem, args.repair_of)
    try:
        summary = synthesize(evidence, top=args.top,
                             parameters=COMPACT if args.top == "anvil_d1_top" else {})
        evidence.finish("passed", **summary)
        print(json.dumps({k: v for k, v in summary.items() if k != "cell_types"}))
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        print(str(exc), file=sys.stderr)
        print(rel(evidence.path / "receipt.json"), file=sys.stderr)
        return 1
    print(rel(evidence.path / "receipt.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
