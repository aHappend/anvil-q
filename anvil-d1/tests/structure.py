"""Memory-preserving Yosys checks, with public ports left unconstrained."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import Evidence, ROOT, rel
from frontend import adapted_sources


COMPACT = dict(NUM_LAYERS=2, HIDDEN_SIZE=16, INTERMEDIATE_SIZE=16,
               NUM_Q_HEADS=2, KV_LORA_RANK=3, QK_NOPE_HEAD_DIM=2,
               QK_ROPE_HEAD_DIM=2, V_HEAD_DIM=2, ROUTED_EXPERTS=7,
               TOP_K=6, SHARED_EXPERTS=2, MOE_INTERMEDIATE_SIZE=8,
               FIRST_DENSE_LAYERS=1, VOCAB_SIZE=8, MAX_SEQ_LEN=5,
               BANKS=2, QUEUE_DEPTH=3, TILE_K=8, TILE_ROWS=3)


def synthesize(evidence, top="anvil_d1_top", parameters=None, frontend_noopt=False,
               frontend_adapter=False):
    sources = (adapted_sources(evidence) if frontend_adapter else
               sorted(ROOT.glob("anvil_q3_reference/rtl/*.sv")) + sorted(ROOT.glob("rtl/*.sv")))
    params = "".join(f" -chparam {name} {value}" for name, value in (parameters or {}).items())
    output = evidence.path / "netlist.json"
    script = (
        "read_verilog -defer -sv " + ("-noopt " if frontend_noopt else "") +
        " ".join(rel(p) for p in sources) + ";\n"
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
    if not registers or not active_ports or len(modules) < 2:
        raise AssertionError("synthesis lost state, ports, or hierarchy")
    instance_cells = {}
    instance_memories = 0
    instance_registers = 0

    def walk(name, ancestors=()):
        nonlocal instance_memories, instance_registers
        if name in ancestors:
            raise AssertionError(f"recursive synthesis hierarchy: {name}")
        for cell in modules[name].get("cells", {}).values():
            kind = cell["type"]
            if kind in modules:
                walk(kind, ancestors+(name,))
            else:
                instance_cells[kind] = instance_cells.get(kind, 0)+1
                if "dff" in kind.lower():
                    instance_registers += 1
                if kind == "$mem_v2":
                    instance_memories += (int(cell["parameters"]["SIZE"], 2) *
                                          int(cell["parameters"]["WIDTH"], 2))

    walk(top)
    identities = {module.get("attributes", {}).get("hdlname", name).split()[0].lstrip("\\")
                  for name, module in modules.items()}
    if top == "anvil_d1_top":
        required = ({"anvil_q3_top"} if (parameters or {}).get("MODEL_MODE") == 1 else
                    {"anvil_d1_decoder_layer", "anvil_d1_mla_engine",
                     "anvil_d1_moe_router_dma", "anvil_d1_csr_perf"})
        if not required <= identities:
            raise AssertionError(f"required synthesis hierarchy missing: {sorted(required-identities)}")
    summary = dict(top=top, parameters=parameters or {}, module_definitions=len(modules),
                   cell_types=counts, memory_bits_in_module_definitions=memory_bits,
                   register_cells_in_module_definitions=registers,
                   instantiated_cell_types=instance_cells,
                   instantiated_register_cells=instance_registers,
                   instantiated_memory_bits=instance_memories,
                   top_port_bits=active_ports, prohibited_cells=prohibited)
    (evidence.path / "structure.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of")
    parser.add_argument("--top", choices=["anvil_d1_top", "anvil_d1_exp", "anvil_d1_silu",
                                         "anvil_d1_mla_engine", "anvil_d1_moe_router_dma",
                                         "anvil_d1_csr_perf", "anvil_q3_top"],
                        default="anvil_d1_top")
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--legacy-profile", type=int, choices=(1, 2, 3))
    parser.add_argument("--frontend-noopt", action="store_true",
                        help="diagnose AST simplification compatibility without changing RTL")
    parser.add_argument("--frontend-adapter", action="store_true")
    args = parser.parse_args()
    stem = ("production-synthesis" if args.production else "compact-synthesis") if args.top == "anvil_d1_top" else (
        args.top.removeprefix("anvil_d1_") + "-synthesis")
    if args.legacy_profile:
        stem += f"-legacy{args.legacy_profile}"
    evidence = Evidence(stem, args.repair_of)
    try:
        parameters = COMPACT.copy() if args.top == "anvil_d1_top" and not args.production else {}
        if args.legacy_profile:
            if args.top not in ("anvil_d1_top", "anvil_q3_top"):
                raise ValueError("--legacy-profile requires a native or parent top")
            parameters = dict(PROFILE=args.legacy_profile, NUM_LAYERS=1,
                              HIDDEN_SIZE=16, INTERMEDIATE_SIZE=16,
                              NUM_Q_HEADS=8 if args.legacy_profile == 3 else 2,
                              NUM_KV_HEADS=1, HEAD_DIM=2 if args.legacy_profile == 3 else 8,
                              GROUP_SIZE=8, AWQ_BITS=4,
                              VOCAB_SIZE=8, MAX_SEQ_LEN=5, BANKS=2, QUEUE_DEPTH=3,
                              TILE_K=8, TILE_ROWS=3)
            if args.top == "anvil_d1_top":
                parameters["MODEL_MODE"] = 1
        summary = synthesize(evidence, top=args.top, parameters=parameters,
                             frontend_noopt=args.frontend_noopt,
                             frontend_adapter=args.frontend_adapter)
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
