"""Functional defect sensitivity on disposable source copies only.

All mutants must compile and fail the unchanged public-pin comparison with a
specific mismatch. Positive controls execute here without prerequisite receipts.
Compiler failure, timeout, missing SUMMARY, or an arbitrary nonzero exit never
counts as sensitivity. RTL originals and the immutable parent are not modified.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csr import csr_bench
from diagnostic import native_bench, simulate
from evidence import Evidence, ROOT, rel
from mla import mla_bench
from numerical import primitive_bench
from router import router_bench


MUTATIONS = [
    dict(name="absorption_head", source="anvil_d1_absorption.sv", bench="native",
         old="{4'd2,head,reduction[23:0]}", new="{4'd2,4'd0,reduction[23:0]}",
         mismatch="NUMERICAL_WRITE_MISMATCH"),
    dict(name="missing_rotary_score", source="anvil_d1_mla_engine.sv", bench="mla",
         old="if (component==CW-1) begin score_sum<=accumulated_score;",
         new="if (component==RK-1) begin score_sum<=accumulated_score;",
         mismatch="MLA_NUMERICAL_WRITE_MISMATCH"),
    dict(name="topk_cutoff_tie", source="anvil_d1_moe_router_dma.sv", bench="router",
         old="scores[scan_index]>best_score", new="scores[scan_index]>=best_score",
         mismatch="ROUTER_WRONG_WINNER"),
    dict(name="dropped_shared", source="anvil_d1_moe_router_dma.sv", bench="router",
         old="(!routed_phase && !second_shared ? 128'sd0 : mixture_word)",
         new="(!routed_phase ? 128'sd0 : mixture_word)",
         mismatch="ROUTER_NUMERICAL_WRITE_MISMATCH"),
    dict(name="stale_prefetch_consumption", source="anvil_d1_moe_router_dma.sv", bench="router",
         old="tile_data<=tiles[active_tile_base+expert_tile_index]",
         new="tile_data<=tiles[expert_tile_index]",
         mismatch="ROUTER_NUMERICAL_WRITE_MISMATCH"),
    dict(name="telemetry_increment", source="anvil_d1_csr_perf.sv", bench="csr",
         old="assign global_increment[5]={4'd0,cache_read_bytes};",
         new="assign global_increment[5]={4'd0,other_write_bytes};",
         mismatch="CSR_POST_EDGE_MISMATCH"),
    dict(name="negative_half_rounding", source="anvil_d1_round_sat.sv", bench="numerical",
         old="in_value[127] ? in_value[S-1:0]>HALF",
         new="in_value[127] ? in_value[S-1:0]>=HALF",
         mismatch="NUMERICAL_round"),
]


def build_bench(evidence, kind):
    if kind == "native":
        return native_bench(evidence, 17, 1)
    if kind == "mla":
        return mla_bench(evidence)
    if kind == "router":
        return router_bench(evidence)
    if kind == "csr":
        return csr_bench(evidence)
    if kind == "numerical":
        return primitive_bench(evidence)
    raise ValueError(f"unknown defect bench: {kind}")


def sensitivity(selected=None):
    mutations = [m for m in MUTATIONS if selected is None or m["name"] == selected]
    ledger = []
    for kind in sorted({m["bench"] for m in mutations}):
        evidence = Evidence("defect-positive-"+kind)
        try:
            build_bench(evidence, kind)
            observations = simulate(evidence, kind+".sv", "verilator")
            evidence.finish("passed", positive_control=kind, observations=observations)
        except Exception as exc:
            evidence.finish("failed", error=str(exc))
            raise
        ledger.append(dict(kind="positive", bench=kind, receipt=rel(evidence.path/"receipt.json")))
    for mutation in mutations:
        evidence = Evidence("defect-"+mutation["name"])
        try:
            build_bench(evidence, mutation["bench"])
            source = evidence.path / ("mutant-source-"+evidence.path.name.rsplit("-", 1)[-1])
            for folder in ("rtl", "anvil_q3_reference/rtl"):
                (source/folder).mkdir(parents=True, exist_ok=False)
                for original in ROOT.glob(folder+"/*.sv"):
                    shutil.copyfile(original, source/folder/original.name)
            target = source/"rtl"/mutation["source"]
            text = target.read_text()
            if text.count(mutation["old"]) != 1:
                raise AssertionError(f"mutation anchor not unique: {mutation['name']}")
            target.write_text(text.replace(mutation["old"], mutation["new"], 1))
            evidence.record["mutation"] = mutation
            evidence.record["experiment_source_sha256"] = {
                rel(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for pattern in ("rtl/*.sv", "anvil_q3_reference/rtl/*.sv")
                for path in source.glob(pattern)}
            evidence.save()
            try:
                simulate(evidence, mutation["bench"]+".sv", "verilator", source_root=source)
            except RuntimeError:
                child = evidence.record["children"][-1]
                if child.get("exit_code") in (None, 0) or child.get("timed_out") or "simulation.stdout.txt" not in child["stdout"]:
                    raise AssertionError("mutation failed outside a completed functional simulation")
                stdout = ROOT/child["stdout"]
                observations = stdout.read_text()
                if mutation["mismatch"] not in observations:
                    raise AssertionError(f"wrong mutation failure: expected {mutation['mismatch']}, {rel(stdout)}")
            else:
                raise AssertionError(f"mutant escaped reference comparisons: {mutation['name']}")
            evidence.finish("passed", mutant_compiled=True,
                            specific_mismatch=mutation["mismatch"], observations=observations)
            ledger.append(dict(kind="detected", name=mutation["name"],
                               mismatch=mutation["mismatch"], receipt=rel(evidence.path/"receipt.json")))
            print(f"DEFECT_DETECTED {mutation['name']} {mutation['mismatch']}", flush=True)
        except Exception as exc:
            evidence.finish("failed", error=str(exc))
            raise
    return ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=[m["name"] for m in MUTATIONS])
    args = parser.parse_args()
    evidence = Evidence("defect-matrix")
    try:
        ledger = sensitivity(args.case)
        evidence.finish("passed", runs=ledger)
        print(json.dumps(dict(positive_controls=sum(r["kind"] == "positive" for r in ledger),
                              detected_mutants=sum(r["kind"] == "detected" for r in ledger))))
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        print(str(exc), file=sys.stderr)
        print(rel(evidence.path/"receipt.json"), file=sys.stderr)
        return 1
    print(rel(evidence.path/"receipt.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
