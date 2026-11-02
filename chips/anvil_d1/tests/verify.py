"""Portable self-contained L1 verification for Anvil-D1.

Run python3 tests/verify.py, or --suite behavior|compatibility|defects|synthesis|portable.
Dependencies: Python3 standard library, Icarus/vvp, Verilator with a C++ compiler
and make, Yosys. No installation, checkpoint download or local hardware access.
Each suite has a shared 2700-second budget starting before fixture generation;
vvp is restricted to compact <=500000-cycle smoke and a 600-second child budget.
Time limits are execution failures, never functional acceptance thresholds.

Requirement map:
behavior: exact arithmetic/latency, native RMS, absorption and causal context,
complete inference seeds17/89/203, production-width streaming cache transactions,
64-expert routing/retained prefetch, CSR and fault/epoch recovery.
compatibility: every legal profile/cache-mode class, immutable parent public-pin
differential plus independent dense arithmetic, five matched synthetic domains.
defects: unchanged public-pin numerical/counter comparisons detect seven
successfully compiled disposable mutants; positive controls run here.
synthesis: native compact/default production, legacy profiles, literal engines,
legal boundary synthesis and explicit illegal diagnostics; zero latches/div/mod,
resolved hierarchy, meaningful state and memories. Generic area is not PPA.
portable: declared sources only, fresh compact native/legacy/synthesis execution.

Source/evidence index: reference.py and legacy.py are numerical models;
floating.py characterizes real-valued error; each generated fixture and child
receipt binds inputs/RTL/verification hashes, exact tool argv, version, logs and
outcomes. No earlier preparation receipt is a prerequisite or passing baseline.
"""

import argparse
import json
from pathlib import Path
from fractions import Fraction
import re
import shutil
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from counter import counter_bench
from csr import csr_bench
from defects import sensitivity
from diagnostic import native_bench, simulate
from elaboration import MINIMUM, elaborate
from evidence import Evidence, ROOT, begin_suite, check_deadline, rel
from faults import faults_bench, reset_bench
from floating import characterize
from frontend import adapted_sources
from inference import DOMAINS, inference_bench
from mla import mla_bench
from numerical import primitive_bench
from reference import Shape
from rms import rms_bench
from router import router_bench
from scheduler import scheduler_bench
from structure import COMPACT, synthesize
from wide_mla import wide_bench


def observations(text):
    return {name: int(value) for name, value in re.findall(r"\b(\w+)=(\d+)\b", text)}


def ratio(numerator, denominator, units):
    return dict(numerator=numerator, denominator=denominator, units=units,
                exact=str(Fraction(numerator, denominator)) if denominator else "undefined")


class Suite:
    def __init__(self, name):
        self.start = time.monotonic()
        self.evidence = Evidence(name, preparation=False)
        begin_suite(self.evidence.path, 2700-(time.monotonic()-self.start))
        self.runs = []

    def experiment(self, name, builder, bench, simulator="verilator", **kwargs):
        check_deadline()
        evidence = Evidence(name)
        try:
            fixture = builder(evidence, **kwargs)
            text = simulate(evidence, bench+".sv", simulator)
            actual = observations(text)
            metrics = []
            for line in text.splitlines():
                if line.startswith("METRIC "):
                    values = observations(line)
                    values["active_parameter_saving"] = ratio(
                        values["dense_expert_bytes"]-values["expert_bytes"],
                        values["dense_expert_bytes"], "expert bytes saved / dense expert bytes")
                    values["prefetch_overlap_efficiency"] = ratio(
                        values["overlap_cycles"], values["shared_cycles"],
                        "overlap cycles / shared arithmetic-active cycles")
                    metrics.append(values)
            evidence.finish("passed", fixture=fixture, observations=text, actual=actual,
                            ratio_metrics=metrics)
        except Exception as exc:
            evidence.finish("failed", error=str(exc))
            self.runs.append(dict(case=name, status="failed", receipt=rel(evidence.path/"receipt.json")))
            raise
        entry = dict(case=name, status="passed", receipt=rel(evidence.path/"receipt.json"),
                     simulator=simulator, actual=actual, fixture=fixture, ratio_metrics=metrics)
        self.runs.append(entry)
        print(f"CHECK {name} {json.dumps(actual, sort_keys=True)}", flush=True)
        return entry

    def synthesis(self, name, **kwargs):
        check_deadline()
        evidence = Evidence(name)
        try:
            result = synthesize(evidence, **kwargs)
            evidence.finish("passed", **result)
        except Exception as exc:
            evidence.finish("failed", error=str(exc))
            self.runs.append(dict(case=name, status="failed", receipt=rel(evidence.path/"receipt.json")))
            raise
        self.runs.append(dict(case=name, status="passed", receipt=rel(evidence.path/"receipt.json"),
                              actual=result))
        print(f"CHECK {name} instantiated_register_cells={result['instantiated_register_cells']} "
              f"instantiated_memory_bits={result['instantiated_memory_bits']}", flush=True)
        return result


def behavior(suite):
    suite.experiment("arithmetic-ieee-smoke", primitive_bench, "numerical", "icarus")
    suite.experiment("arithmetic-compiled", primitive_bench, "numerical")
    suite.experiment("native-rms", rms_bench, "rms")
    suite.experiment("native-mla-ieee", mla_bench, "mla", "icarus")
    suite.experiment("native-mla-discriminators", mla_bench, "mla")
    suite.experiment("mla-nonsquare-scale", mla_bench, "mla", nope=1)
    for seed in (17, 89, 203):
        suite.experiment(f"complete-inference-seed{seed}", inference_bench, "native", seed=seed)
    cross = suite.experiment("complete-ieee-one-token", native_bench, "native", "icarus", seed=17, tokens=1)
    compiled = suite.experiment("complete-compiled-one-token", native_bench, "native", seed=17, tokens=1)
    for name in ("writes", "logits", "tokens"):
        if cross["actual"][name] != compiled["actual"][name]:
            raise AssertionError(f"cross-simulator mismatch: {name}")
    suite.experiment("singleton-route-ieee", router_bench, "router", "icarus",
                     experts=1, topk=1, hidden=8, tile_rows=1)
    suite.experiment("full64-top6", router_bench, "router")
    suite.experiment("topk-equals-experts", router_bench, "router",
                     experts=6, topk=6, hidden=8, tile_rows=1)
    suite.experiment("csr-protocol", csr_bench, "csr", "icarus")
    suite.experiment("counter-saturation", counter_bench, "counter")
    suite.experiment("fault-cancel-recovery", faults_bench, "native")
    suite.experiment("reset-mid-work-restart", reset_bench, "native")
    suite.experiment("bank-tag-reorder-ieee", scheduler_bench, "scheduler", "icarus")
    for banks, queue in ((1, 1), (4, 16), (8, 1)):
        suite.experiment(f"bank-tag-b{banks}-q{queue}", scheduler_bench, "scheduler",
                         banks=banks, queue=queue)
    minimum = Shape(hidden=8, intermediate=8, moe_intermediate=8, heads=1, rank=1,
                    nope=1, rope=2, value=1, layers=1, first_dense=0,
                    experts=1, topk=1, vocab=4, maxseq=1)
    suite.experiment("minimum-routed-banks1-queue1", inference_bench, "native",
                     tokens=1, shape=minimum, banks=1, queue=1, tile_rows=1)
    from dataclasses import replace
    suite.experiment("minimum-all-dense", inference_bench, "native", tokens=1,
                     shape=replace(minimum, first_dense=1), banks=1, queue=1, tile_rows=1)
    suite.experiment("last-position-banks4-queue16", inference_bench, "native",
                     tokens=5, banks=4, queue=16)
    suite.experiment("banks8-queue1", inference_bench, "native", tokens=1, banks=8, queue=1)
    wide = suite.experiment("mla-production-widths", wide_bench, "wide")
    actual = wide["actual"]
    cache = actual["cache_read_bytes"]+actual["cache_write_bytes"]
    dense = actual["cache_dense_equiv_bytes"]
    if dense == 0 or (dense-cache)*100 <= dense*82:
        raise AssertionError("observed production-width cache traffic does not exceed 82% reduction")
    suite.experiment("mla-full-hidden-contractions", wide_bench, "wide", full_hidden=True)
    characterization = [characterize(seed) for seed in (17, 89, 203)]
    check_deadline()
    (suite.evidence.path/"floating-characterization.json").write_text(
        json.dumps(characterization, indent=2)+"\n")
    return dict(cache_reduction=ratio(dense-cache, dense,
                                     "accepted cache bytes saved / identical-pass MHA cache bytes"),
                floating_characterized_scalars=sum(r["compared_scalars"]
                    for c in characterization for r in c["records"]))


def compatibility(suite):
    matrix = [(1, 0, 0), (2, 0, 0), (2, 1, 0),
              (3, 0, 0), (3, 1, 0), (3, 2, 0), (3, 2, 1)]
    for profile, mode, asymmetric in matrix:
        suite.experiment(f"legacy-profile{profile}-cache{mode}-asym{asymmetric}",
                         inference_bench, "native", legacy=(profile, mode, asymmetric))
    suite.experiment("legacy-fault-cancel-differential", faults_bench, "native",
                     legacy=(3, 0, 0))
    benchmarks = []
    # Identical generated workload geometry/service, not identical models.
    for domain, name in enumerate(DOMAINS):
        native = suite.experiment("domain-"+name+"-d1", inference_bench, "native",
                                  domain=domain, seed=17+domain, sequences=2)
        dense = suite.experiment("domain-"+name+"-dense", inference_bench, "native",
                                 domain=domain, seed=17+domain, sequences=2, legacy=(3, 0, 0))
        benchmarks.append(dict(domain=name, d1=native, dense=dense,
                               architecture_difference="native Q16 MLA/MoE versus dense FP16/AWQ GQA",
                               equal_model_or_accuracy_claim=False))
    # The signed-alias/declaration-order adapter must also execute unchanged
    # public comparisons against the original parent and integer model.
    evidence = Evidence("frontend-semantic-differential")
    try:
        frozen = inference_bench(evidence, legacy=(3, 2, 1), tokens=4)
        generated = adapted_sources(evidence)
        directory = generated[0].parents[2]
        text = (evidence.path/"native.sv").read_text()
        original_sources = sorted(ROOT.glob("anvil_q3_reference/rtl/*.sv"))
        original_directory = evidence.path/("original-source-"+evidence.path.name.rsplit("-", 1)[-1])
        original_directory.mkdir()
        extra = []
        for source in original_sources:
            target = original_directory/source.name
            target.write_text(source.read_text().replace("anvil_q3_", "original_q3_"))
            extra.append(target)
        text = text.replace("anvil_q3_top #(", "original_q3_top #(")
        (evidence.path/"native.sv").write_text(text)
        result = simulate(evidence, "native.sv", "verilator", source_root=directory,
                          extra_sources=extra)
        evidence.finish("passed", fixture=frozen, observations=result)
        suite.runs.append(dict(case="frontend-semantic-differential", status="passed",
                               receipt=rel(evidence.path/"receipt.json"), actual=observations(result)))
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        raise
    (suite.evidence.path/"domain-benchmarks.json").write_text(json.dumps(benchmarks, indent=2)+"\n")
    return dict(legacy_configurations=len(matrix), domains=5, sequences_per_architecture_per_domain=2)


def defects(suite):
    ledger = sensitivity()
    if sum(r["kind"] == "detected" for r in ledger) != 7:
        raise AssertionError("all seven functional mutants are mandatory")
    suite.runs.extend(ledger)
    return dict(detected_mutants=7)


def synthesis(suite):
    suite.synthesis("compact-native", parameters=COMPACT)
    suite.synthesis("production-native")
    for top in ("anvil_d1_mla_engine", "anvil_d1_moe_router_dma", "anvil_d1_csr_perf"):
        suite.synthesis("production-"+top, top=top)
    for profile in (1, 2, 3):
        parameters = dict(MODEL_MODE=1, PROFILE=profile, NUM_LAYERS=1,
                          HIDDEN_SIZE=16, INTERMEDIATE_SIZE=16, NUM_Q_HEADS=8 if profile == 3 else 2,
                          NUM_KV_HEADS=1, HEAD_DIM=2 if profile == 3 else 8,
                          GROUP_SIZE=8, VOCAB_SIZE=8, MAX_SEQ_LEN=5, BANKS=2,
                          QUEUE_DEPTH=3, TILE_K=8, TILE_ROWS=3)
        suite.synthesis(f"legacy-profile{profile}", parameters=parameters, frontend_adapter=True)
    for name, parameters in (
            ("minimum", MINIMUM), ("minimum-all-dense", MINIMUM | dict(FIRST_DENSE_LAYERS=1)),
            ("banks4-queue16", COMPACT | dict(BANKS=4, QUEUE_DEPTH=16)),
            ("banks8-queue1", COMPACT | dict(BANKS=8, QUEUE_DEPTH=1))):
        suite.synthesis(name, parameters=parameters)
    evidence = Evidence("parameter-diagnostics")
    try:
        result = elaborate(evidence)
        evidence.finish("passed", **result)
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        raise
    suite.runs.append(dict(case="parameter-diagnostics", status="passed",
                           receipt=rel(evidence.path/"receipt.json"), actual=result))
    return dict(generic_area_not_physical_ppa=True, legal_elaborations=result["legal_elaborations"],
                illegal_diagnostics=result["explicit_illegal_rejections"])


def portable(suite):
    directory = suite.evidence.path/("clean-project-"+suite.evidence.path.name.rsplit("-", 1)[-1])
    patterns = ("rtl/*.sv", "tests/*.py", "design/*.md", "anvil_q3_reference/rtl/*.sv")
    copied = []
    for pattern in patterns:
        paths = sorted(ROOT.glob(pattern))
        if not paths:
            raise AssertionError(f"empty deliverable selector: {pattern}")
        for source in paths:
            target = directory/source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied.append(source.relative_to(ROOT).as_posix())
            if re.search(r"(?<![\w])/(?:data|home|root|tmp)/", source.read_text()):
                raise AssertionError(f"nonportable private absolute path in shipped input: {rel(source)}")
    # A fresh process imports only the clean-copy siblings. It executes missing
    # work rather than requiring receipts or recursively running this suite.
    output = suite.evidence.run("clean-reproduction",
                               ["python3", "tests/verify.py", "--clean-reproduction"],
                               ["python3", "--version"], cwd=directory)
    result = json.loads((directory/"evidence"/"clean-result.json").read_text())
    if result.get("status") != "passed" or result.get("completed_experiments") != 3:
        raise AssertionError("clean-copy reproduction missing actual experiments")
    suite.runs.append(dict(case="clean-copy", status="passed", actual=result,
                           stdout=rel(output), source_files=copied))
    return dict(copied_source_files=len(copied), clean_experiments=3)


def clean_reproduction():
    suite = Suite("clean-reproduction")
    try:
        suite.experiment("native", native_bench, "native", "icarus", seed=17, tokens=1)
        suite.experiment("legacy", inference_bench, "native", legacy=(1, 0, 0), tokens=1)
        suite.synthesis("compact-native", parameters=COMPACT)
        suite.evidence.finish("passed", runs=suite.runs)
        result = dict(status="passed", completed_experiments=3, runs=suite.runs,
                      receipt=rel(suite.evidence.path/"receipt.json"))
        (ROOT/"evidence"/"clean-result.json").write_text(json.dumps(result, indent=2)+"\n")
    except Exception as exc:
        suite.evidence.finish("failed", error=str(exc), runs=suite.runs)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("behavior", "compatibility", "defects", "synthesis", "portable"))
    parser.add_argument("--clean-reproduction", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.clean_reproduction:
        clean_reproduction()
        return 0
    functions = dict(behavior=behavior, compatibility=compatibility, defects=defects,
                     synthesis=synthesis, portable=portable)
    for name in ([args.suite] if args.suite else functions):
        suite = Suite(name)
        try:
            result = functions[name](suite)
            check_deadline()
            suite.evidence.finish("passed", runs=suite.runs, **result)
            print(f"SUITE {name} passed {rel(suite.evidence.path/'receipt.json')}", flush=True)
        except Exception as exc:
            suite.evidence.finish("failed", runs=suite.runs,
                                  timed_out=isinstance(exc, TimeoutError), error=str(exc))
            print(f"SUITE {name} failed: {exc}; {rel(suite.evidence.path/'receipt.json')}", file=sys.stderr)
            return 1
        finally:
            import evidence
            evidence.SUITE_PATH = evidence.SUITE_DEADLINE = None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
