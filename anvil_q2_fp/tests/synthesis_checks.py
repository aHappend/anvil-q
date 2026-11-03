"""Yosys synthesis of real RTL with lossless package-scope expansion.

The bundled frontend supports module-local functions but may not support
SystemVerilog packages. Wildcard imports and qualified package-function calls
receive the exact package body in module scope; qualified calls become local
calls. No arithmetic, parameters, processes or ports are rewritten.
Original and expanded sources are hash-bound in each run. This is not a stub
model, and no black boxes, latches, division/modulo cells or cycles are allowed.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run


def expand_packages(sources):
    packages = {}
    for source in sources:
        text = source.read_text()
        for match in re.finditer(r"\bpackage\s+(\w+)\s*;(.*?)\bendpackage\b", text, re.S):
            assert match[1] not in packages, "duplicate package"
            packages[match[1]] = match[2]
    chunks = []
    for source in sources:
        text = source.read_text()
        text = re.sub(r"\bpackage\s+\w+\s*;.*?\bendpackage\b", "", text, flags=re.S)

        def replace(match):
            name = match[1]
            if name not in packages:
                raise ValueError(f"unresolved package import: {name}")
            return packages[name]

        text = re.sub(r"\bimport\s+(\w+)::\*\s*;", replace, text)

        def qualified(module):
            contents = module[0]
            bodies = []
            for name in sorted(set(re.findall(r"\b(\w+)::\w+", contents))):
                if name not in packages:
                    raise ValueError(f"unresolved qualified package: {name}")
                body = packages[name]
                functions = set(re.findall(
                    r"\bfunction\s+automatic(?:\s+signed)?(?:\s*\[[^]]+\])?\s+(\w+)\s*\(",
                    body))
                called = set(re.findall(rf"\b{re.escape(name)}::(\w+)", contents))
                assert called <= functions, f"unsupported qualified nonfunction member: {name}"
                local_functions = set(re.findall(
                    r"\bfunction\s+automatic(?:\s+signed)?(?:\s*\[[^]]+\])?\s+(\w+)\s*\(",
                    contents))
                assert not functions & local_functions, "package/local function collision"
                contents = re.sub(rf"\b{re.escape(name)}::(\w+)", r"\1", contents)
                bodies.append(body)
            if bodies:
                header = re.search(r"\)\s*;", contents)
                assert header, "module with qualified calls has no port-list boundary"
                contents = contents[:header.end()] + "\n" + "\n".join(bodies) + contents[header.end():]
            return contents

        text = re.sub(r"\bmodule\b.*?\bendmodule\b", qualified, text, flags=re.S)
        assert not re.search(r"\b(?:package|import)\s+\w+", text)
        assert not re.search(r"\b\w+::\w+", text), "unexpanded package scope"
        chunks.append(f"\n// Source: {source.relative_to(ROOT)}\n{text}\n")
    return "".join(chunks)


def analyze(path, top):
    modules = json.loads(path.read_text())["modules"]
    assert top in modules, f"missing top {top}"
    forbidden = {"$dlatch", "$adlatch", "$dlatchsr", "$div", "$mod", "$divfloor", "$modfloor"}
    counts = {"cells": 0, "state_bits": 0, "memory_bits": 0}
    memories = []
    instances = {}

    def visit(name, ancestry):
        module = modules[name]
        assert not module.get("attributes", {}).get("blackbox"), f"black box: {name}"
        assert name not in ancestry, "recursive hierarchy"
        for cell_name, cell in module.get("cells", {}).items():
            kind = cell["type"]
            assert kind not in forbidden and not kind.startswith("$_DLATCH"), (
                f"forbidden synthesized cell: {kind}")
            if kind in modules:
                origin = str(modules[kind].get("attributes", {}).get("hdlname", kind))
                origin = origin.split()[0].lstrip("\\")
                instances[origin] = instances.get(origin, 0) + 1
                visit(kind, ancestry + [name])
            else:
                assert kind.startswith("$"), f"unresolved black box: {kind}"
                counts["cells"] += 1
                if "dff" in kind.lower() or kind.startswith("$_DFF"):
                    counts["state_bits"] += len(cell.get("connections", {}).get("Q", []))
                if kind.startswith("$mem"):
                    parameters = cell.get("parameters", {})
                    if "SIZE" in parameters and "WIDTH" in parameters:
                        size = int(parameters["SIZE"], 2)
                        width = int(parameters["WIDTH"], 2)
                        counts["memory_bits"] += size * width
                        origin = str(module.get("attributes", {}).get("hdlname", name))
                        memories.append(dict(module=origin.split()[0].lstrip("\\"),
                                             cell=cell_name, size=size, width=width))

    visit(top, [])
    assert counts["cells"] > 0 and counts["state_bits"] > 0, "design synthesized away"
    return dict(counts, instances=instances, memories=memories)


def check_fp_hierarchy(path, banks):
    modules = json.loads(path.read_text())["modules"]
    checked = []

    def child(parent, instance, expected):
        assert instance in parent["cells"], f"missing literal instance: {instance}"
        cell = parent["cells"][instance]
        assert cell["type"] in modules, f"unresolved required module: {instance}"
        module = modules[cell["type"]]
        origin = str(module.get("attributes", {}).get("hdlname", cell["type"]))
        origin = origin.split()[0].lstrip("\\")
        assert origin == expected, f"{instance}: {origin} != {expected}"
        checked.append({"instance": instance, "module": origin})
        return module

    top = modules["anvil_q2_fp_top"]
    scheduler = child(top, "bank_scheduler", "anvil_q2_bank_scheduler")
    assert len(scheduler["ports"]["mem_req_valid"]["bits"]) == banks
    decoder = child(top, "decoder", "anvil_q2_fp_decoder_layer")
    child(top, "final_norm", "anvil_q2_fp_rmsnorm")
    gemv = child(decoder, "gemv", "anvil_q2_fp_gemv")
    child(decoder, "rope", "anvil_q2_fp_rope")
    attention = child(decoder, "attention", "anvil_q2_fp_gqa_attention")
    mlp = child(decoder, "mlp", "anvil_q2_fp_swiglu_mlp")
    child(decoder, "residual", "anvil_q2_fp_elementwise")
    cache = child(attention, "kv_cache", "anvil_q2_fp_kv_cache")
    child(cache, "codec", "anvil_q2_fp_cache_codec")
    mlp_gemv = child(mlp, "gemv", "anvil_q2_fp_gemv")
    for compute in (gemv, mlp_gemv):
        for bank in range(banks):
            lane = child(compute, f"banks[{bank}].lane", "anvil_q2_fp_dot_lane")
            for port, width in (("in_a", 16), ("in_b", 128), ("out_sum", 256)):
                assert len(lane["ports"][port]["bits"]) == width, f"wrong lane {port} width"
                assert not lane["ports"][port].get("signed", 0), f"signed encoding port {port}"
    return checked


def execute(top="anvil_q2_fp_dot_lane", parameters=None, product="fp", repair_of=None):
    run = Run(f"verifier-synthesis-{top}")
    try:
        if repair_of:
            path = Path(repair_of)
            assert not path.is_absolute() and ".." not in path.parts
            assert path.parts[0] == "evidence" and path.name == "receipt.json"
            assert json.loads((ROOT / path).read_text())["outcome"] == "failed"
            run.receipt["repair_of"] = repair_of
            run.receipt["repair_of_sha256"] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        run.command(["yosys", "-V"], "yosys-version")
        source_root = ROOT / ("rtl" if product == "fp" else "anvil_q2_reference/rtl")
        sources = sorted(source_root.glob("*.sv"))
        expanded = run.path / "expanded.sv"
        expanded.write_text(expand_packages(sources))
        netlist = run.path / "netlist.json"
        script = run.path / "synthesis.ys"
        configuration = ""
        if parameters:
            configuration = "chparam " + " ".join(
                f"-set {name} {number}" for name, number in parameters.items()) + f" {top}\n"
        script.write_text(
            f"read_verilog -sv {run.relative(expanded)}\n"
            f"{configuration}"
            f"hierarchy -check -top {top}\n"
            "proc\n"
            "opt_expr\n"
            "opt_clean\n"
            "memory -nomap\n"
            "opt_clean\n"
            "check -assert\n"
            "select -assert-none t:$dlatch t:$adlatch t:$dlatchsr "
            "t:$div t:$mod t:$divfloor t:$modfloor\n"
            "scc -expect 0\n"
            "stat\n"
            f"write_json {run.relative(netlist)}\n")
        run.receipt["generated_sha256"] = {
            run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (expanded, script)}
        run.command(["yosys", "-Q", "-T", "-s", run.relative(script)], "synthesis", timeout=21600)
        metrics = analyze(netlist, top)
        metrics["parameters"] = parameters or {}
        metrics["product"] = product
        metrics["synthesis_flow"] = "proc; opt_expr; opt_clean; memory -nomap; opt_clean"
        if top == "anvil_q2_fp_top":
            banks = (parameters or {}).get("BANKS", 4)
            metrics["literal_hierarchy"] = check_fp_hierarchy(netlist, banks)
            assert metrics["instances"].get("anvil_q2_fp_dot_lane") == 2 * banks, (
                "lost decoder or MLP compute banks")
            for module in ("anvil_q2_bank_scheduler", "anvil_q2_fp_scalar",
                           "anvil_q2_fp_kv_cache", "anvil_q2_fp_cache_codec"):
                assert metrics["instances"].get(module, 0) > 0, f"lost {module}"
            sequence_length = (parameters or {}).get("MAX_SEQ_LEN", 32768)
            if sequence_length * 32 >= 4096:
                assert any(memory["module"] == "anvil_q2_fp_gqa_attention"
                           and memory["width"] == 32 and memory["size"] == sequence_length
                           for memory in metrics["memories"]), (
                    "attention score memory was lost or expanded into discrete registers")
        changed = [name for name, expected in run.receipt["source_sha256"].items()
                   if not (ROOT / name).is_file()
                   or hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected]
        assert not changed, f"sources changed during synthesis: {', '.join(changed)}"
        run.finish("passed-focused-only", metrics=metrics,
                   limitations="generic Yosys only; no target resource or timing claim")
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", default="anvil_q2_fp_dot_lane")
    parser.add_argument("--product", choices=("fp", "parent"), default="fp")
    parser.add_argument("--banks", type=int, choices=(1, 2, 4))
    parser.add_argument("--cache", type=int, choices=(0, 1))
    parser.add_argument("--format", choices=("bf16", "fp16"))
    parser.add_argument("--weights", type=int, choices=(0, 1))
    parser.add_argument("--repair-of", help="project-relative retained failed receipt")
    parser.add_argument("--reduced", action="store_true",
                        help="reduced top geometry; not native implementability evidence")
    args = parser.parse_args()
    parameters = {}
    if args.reduced:
        parameters.update(NUM_LAYERS=1, HIDDEN_SIZE=48, INTERMEDIATE_SIZE=48,
                          NUM_Q_HEADS=6, NUM_KV_HEADS=1, HEAD_DIM=8, GROUP_SIZE=12,
                          VOCAB_SIZE=1, MAX_SEQ_LEN=1)
        if args.product == "fp":
            parameters["CACHE_BLOCK"] = 2
    if args.banks:
        parameters["BANKS"] = args.banks
    if args.cache is not None:
        parameters["CACHE_MODE"] = args.cache
    if args.format is not None:
        assert args.product == "fp", "parent precision is its fixed FP16/Q16.16 ABI"
        parameters["FP_FORMAT"] = int(args.format == "fp16")
    if args.weights is not None:
        assert args.product == "fp", "parent supports AWQ only"
        parameters["WEIGHT_MODE"] = args.weights
    return execute(args.top, parameters, args.product, args.repair_of)


if __name__ == "__main__":
    raise SystemExit(main())
