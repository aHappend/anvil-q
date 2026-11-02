"""Real Yosys structural diagnostic without flattening or mapping large memories."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT


TOPS = (
    "anvil_q2_fp2_bfp_tensor_array", "anvil_q2_fp2_epilogue_fusion",
    "anvil_q2_fp2_flash_attn", "anvil_q2_fp2_telemetry", "anvil_q2_fp2_top",
)


def expand_parent(directory):
    """Only substitute exact package declarations at exact import sites."""
    directory.mkdir()
    parent = ROOT / "anvil_q2_fp_reference/rtl"
    package = (parent / "anvil_q2_fp_00_pkg.sv").read_text()
    prefix, suffix = "package anvil_q2_fp_pkg;", "endpackage"
    if not package.startswith(prefix) or not package.rstrip().endswith(suffix):
        raise ValueError("unexpected parent package delimiters")
    declarations = package[len(prefix):package.rfind(suffix)]
    generated = []
    bindings = {}
    for path in sorted(parent.glob("*.sv")):
        if path.name == "anvil_q2_fp_00_pkg.sv":
            continue
        original = path.read_text()
        expanded = original.replace("import anvil_q2_fp_pkg::*;", declarations)
        target = directory / path.name
        target.write_text(expanded)
        generated.append(target)
        bindings[path.name] = {
            "original_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "expanded_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "replacements": original.count("import anvil_q2_fp_pkg::*;"),
        }
    (directory / "expansion.json").write_text(json.dumps({
        "operation": "literal exact-package-body substitution only",
        "package_sha256": hashlib.sha256(package.encode()).hexdigest(),
        "files": bindings,
    }, indent=2) + "\n")
    return generated


def number(value):
    return int(value, 2) if isinstance(value, str) else value


def structural_summary(netlist, top):
    modules = netlist["modules"]
    if top not in modules:
        raise AssertionError(f"missing top {top}")
    leaves = Counter()
    hierarchy = Counter()
    state_bits = memory_bits = 0
    functional_engines = {}

    def visit(name, stack):
        nonlocal state_bits, memory_bits
        if name in stack:
            raise AssertionError(f"recursive hierarchy {name}")
        module = modules[name]
        attributes = module.get("attributes", {})
        if any(number(attributes.get(key, 0)) for key in ("blackbox", "whitebox")):
            raise AssertionError(f"unresolved/blackbox engine {name}")
        hdlname = str(attributes.get("hdlname", name)).split()[0].lstrip("\\")
        hierarchy[hdlname] += 1
        initial_state = state_bits
        initial_arithmetic = leaves["$add"] + leaves["$mul"] + leaves["$sub"]
        for cell_name, cell in module.get("cells", {}).items():
            kind = cell["type"]
            if kind in modules:
                visit(kind, (*stack, name))
                continue
            if not kind.startswith("$"):
                raise AssertionError(f"unresolved cell {name}.{cell_name}: {kind}")
            lowered = kind.lower()
            if "latch" in lowered or lowered in ("$div", "$mod", "$divfloor", "$modfloor"):
                raise AssertionError(f"forbidden structural cell {name}.{cell_name}: {kind}")
            leaves[kind] += 1
            parameters = cell.get("parameters", {})
            if "dff" in lowered:
                state_bits += number(parameters.get("WIDTH", 1))
            if kind in ("$mem", "$mem_v2"):
                memory_bits += number(parameters["WIDTH"]) * number(parameters["SIZE"])
        for memory in module.get("memories", {}).values():
            memory_bits += memory["width"] * memory["size"]
        if hdlname in (*TOPS, "anvil_q2_fp2_ping_pong_prefetch", "anvil_q2_fp2_rsqrt2"):
            engine_state = state_bits - initial_state
            engine_arithmetic = leaves["$add"] + leaves["$mul"] + leaves["$sub"] - initial_arithmetic
            if engine_state == 0 or engine_arithmetic == 0:
                raise AssertionError(f"empty functional engine {hdlname}")
            functional_engines[hdlname] = {
                "recursive_state_bits": engine_state,
                "recursive_arithmetic_cells": engine_arithmetic,
            }

    visit(top, ())
    if state_bits == 0:
        raise AssertionError("functional engine has no retained state")
    if not leaves.get("$add") and not leaves.get("$mul"):
        raise AssertionError("functional engine has no retained arithmetic")
    expected = {
        "anvil_q2_fp2_top": (
            "anvil_q2_fp2_bfp_tensor_array", "anvil_q2_fp2_epilogue_fusion",
            "anvil_q2_fp2_flash_attn", "anvil_q2_fp2_telemetry",
            "anvil_q2_fp2_ping_pong_prefetch", "anvil_q2_fp2_rsqrt2",
        ),
        "anvil_q2_fp2_bfp_tensor_array": ("anvil_q2_fp2_ping_pong_prefetch",),
        "anvil_q2_fp2_epilogue_fusion": ("anvil_q2_fp2_rsqrt2",),
    }.get(top, ())
    for name in expected:
        if hierarchy[name] == 0:
            raise AssertionError(f"required functional hierarchy removed: {name}")
    return {
        "top": top, "state_bits": state_bits, "memory_bits": memory_bits,
        "hierarchical_cell_counts": dict(sorted(leaves.items())),
        "retained_instances": dict(sorted(hierarchy.items())),
        "functional_engines": functional_engines,
        "resource_units": "generic logical cells/bits, not target ALMs, DSPs, or watts",
    }


COMPACT_TOP = {
    "NUM_LAYERS": 1, "HIDDEN_SIZE": 48, "INTERMEDIATE_SIZE": 64,
    "NUM_Q_HEADS": 6, "NUM_KV_HEADS": 1, "HEAD_DIM": 8,
    "GROUP_SIZE": 8, "VOCAB_SIZE": 16, "MAX_SEQ_LEN": 3,
    "BANKS": 1, "CACHE_BLOCK": 8, "QUEUE_DEPTH": 3,
}


def run(probe, top, parameters=None):
    probe.version("yosys", "-V")
    sources = sorted((ROOT / "rtl").glob("*.sv"))
    if top == "anvil_q2_fp2_top":
        sources = expand_parent(probe.directory / "parent-expanded") + sources
    script = probe.directory / "synthesis.ys"
    netlist = probe.directory / "netlist.json"
    deferred_names = {
        "anvil_q2_fp2_top.sv", "anvil_q2_fp2_controller.sv", "anvil_q2_fp2_flash_attn.sv"
    }
    eager_sources = [str(path.relative_to(ROOT)) for path in sources
                     if path.name not in deferred_names]
    deferred_sources = [str(path.relative_to(ROOT)) for path in sources
                        if path.name in deferred_names]
    parameters = parameters or {}
    overrides = "".join(f" -chparam {key} {value}" for key, value in parameters.items())
    probe.summary["parameters"] = parameters
    script.write_text(
        "read_verilog -sv " + " ".join(eager_sources) + "\n"
        + ("read_verilog -sv -defer " + " ".join(deferred_sources) + "\n"
           if deferred_sources else "")
        +
        f"hierarchy -check -top {top}{overrides}\n"
        "proc\nopt_expr\nopt_clean\ncheck -assert\n"
        "memory -nomap\nopt_clean\ncheck -assert\n"
        "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod t:$divfloor t:$modfloor\n"
        "stat\n"
        f"write_json {netlist.relative_to(ROOT)}\n"
    )
    probe.command(["yosys", "-Q", "-T", "-s", str(script.relative_to(ROOT))], "yosys")
    summary = structural_summary(json.loads(netlist.read_text()), top)
    probe.summary["synthesis"] = summary
    probe.compare("retained-state", True, summary["state_bits"] > 0, {})
    probe.compare("zero-latch-div-mod", 0, sum(
        count for kind, count in summary["hierarchical_cell_counts"].items()
        if "latch" in kind.lower() or kind in ("$div", "$mod", "$divfloor", "$modfloor")
    ), {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", choices=TOPS, default=TOPS[0])
    parser.add_argument("--repair-of")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    probe = Probe("synthesis", args.repair_of)
    try:
        parameters = COMPACT_TOP if args.compact and args.top == TOPS[-1] else {}
        if args.compact and args.top == "anvil_q2_fp2_flash_attn":
            parameters = {"HEAD_DIM": 8, "TILE_TOKENS": 3, "MAX_SEQ_LEN": 17}
        run(probe, args.top, parameters)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
