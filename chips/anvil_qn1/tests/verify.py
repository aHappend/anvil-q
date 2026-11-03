#!/usr/bin/env python3
"""Anvil-QN1 independent L1 verification entry point.

Executable coverage:
  scalar: exact-rational add/subtract/multiply/divide/sqrt, signed zero,
          subnormals, overflow/nonfinite rejection, and output stalls.
  qk-compact / qk-production: per-element numerical parity, five RoPE positions,
          invalid heads, metadata, 133-edge latency, reset/flush and stalls.
  tensor-compact / tensor-full: both weight formats, dynamic 256-lane reductions,
          masks, per-lane isolation, tags, 48 enabled-edge latency and global stalls.
  elementary: deterministic E parity/error bound and BF16 SiLU parity/error bound.
  top-compiled / top-continuation: seven projections, both residuals, final norm,
          every logit, external scratch/KV payloads and direct deferred continuation.
  csr: independent pre-edge/post-edge register/event oracle on both simulators.
  controller: tree prefixes 0..4, branching, markers, malformed trees and cancellation.
  speculation: real four-draft-plus-bonus, complete frames/KV and deferred continuation.
  behavior-core: target prefixes 0..4, branching, capacity/terminal rows,
          second transactions, six logical steps and invalid resubmissions.
  banked-top / memory-matrix: six-step complete direct frames/KV with banked
          request stalls, bank/tag associations and observed response reordering.
  fault-case / fault-matrix: read/write errors, malformed payloads, unknown/
          duplicate/wrong-bank/stale tags, cancellation in projection/QK/attention
          and around publication, reset in work, and compared fresh-sequence recovery.
  synthesis-frontend: compact hierarchy/connectivity checks and optimized
          top/scheduler cross-boundary zero-combinational-SCC assertion.
  integrated-csr: real speculative handshakes, deferred continuation, complete
          frames/KV, busy-write errors, pre-commit mode token classification,
          observed cycle counts, snapshot/clear and independent score maximum.
  speculative-cancel: root, accepted-draft projection/attention and before/after
          five-token publication, drained responses and no-reset fresh recovery.
  attention-context: D128 attention consuming every initialized position in
          a 40960-position external cache with independently calculated context.
  parent-reference: unchanged compact parent execution, nonuniform FP16 embedding,
          zero-dequantized affine fixture, every legacy scratch/KV write and logit.
  isolation-smoke: source-only clean directory, no copied reference tree/build
          products, and actual independent compact QK simulation in the copy.
  integrated-marker: actual IDs 151667/151668, complete 151936-word frames,
          marker cutoff, deferred resubmission opposing an idle mode override,
          held commits, exact scratch/KV payloads and generated-token counters.
  prefill-marker: actual input markers, complete frames, no commit/draft transfer
          and no generated-token accounting.
  production-layer / fusion-profile: authored full-extent first-layer comparison
          and normalization-only experimental clone; production execution remains
          incomplete after a retained timeout, not a demonstrated overhead result.
  fusion-compact / layer-parallel-compact: complete independent compact-layer
          numerical comparisons and measured simulator scheduling diagnostics.
  component-applicability: explicit source/tool/parameter/artifact assessment of
          historical long-context and D128 synthesis components, not fresh execution.
  saved-behavior-applicability: recursively assess retained behavior components,
          including descendant executions; this does not certify coverage closure.
  smoke: production/legacy elaboration, illegal diagnostics, compact startup boundary
          matrix and dual-simulator scalar/QK/tensor/CSR checks.
  numerical: full tensor/head vectors, analytic score bounds, independent Decimal
          coefficient comparisons and deterministic E/SiLU checks.

Behavior, benchmark, defect and no-argument suite dispatchers remain
incomplete; no whole-product acceptance is claimed. Production/boundary
coarse-synthesis and compact isolated-reproduction dispatch are authored but
their complete campaigns are not yet demonstrated.
The original controller
structural-loop counterexample is retained; the repaired controller has a fresh
successful structural receipt. No-argument dispatch remains
incomplete until every mandatory suite has been authored.
The scheduler/top boundary SCC failure is retained, and the repaired source has
a successful independent zero-SCC probe; this is not physical timing proof.
"""

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from execution import Run
from leaf_checks import run_qk, run_scalar, run_tensor, run_tensor_cpp, run_elementary
from integration import run_top
from control_checks import run_csr, run_controller
from smoke_checks import run_startup, run_elaboration, run_smoke
from speculation_checks import run_speculation
from numerical_checks import run_numerical
from synthesis_checks import (run_synthesis_probe, run_controller_synthesis,
                              run_synthesis_case, run_synthesis)
from behavior_checks import run_behavior_core
from memory_checks import run_banked_top, run_memory_matrix
from fault_checks import run_fault_case, run_fault_matrix, FAULT_CASES
from telemetry_checks import run_telemetry
from context_checks import run_context
from speculative_fault_checks import run_speculative_cancel_matrix, run_speculative_cancel
from parent_checks import run_parent
from reproduction_checks import run_reproduce, run_reproduction_child
from production_checks import run_layer, run_fusion_profile
from marker_checks import run_markers
from component_cache import (historical_applicability, latest_marker_build,
                             saved_behavior_applicability)
from prefill_marker_checks import run_prefill_marker
from model import Geometry
import reference


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("smoke", "numerical", "behavior", "benchmark",
                                           "defects", "synthesis", "reproduce"))
    parser.add_argument("--domain", choices=("gsm8k", "humaneval", "mmlu", "boolq", "hellaswag"))
    parser.add_argument("--probe", choices=("qk-compact", "qk-production", "scalar",
                                          "top-compact", "top-compiled", "top-continuation",
                                          "tensor-compact", "tensor-full", "tensor-cpp", "tensor-sv",
                                          "elementary", "csr", "controller", "startup", "elaboration",
                                          "speculation", "qk-stress", "analytic",
                                          "startup-matrix", "scalar-compiled", "synthesis-frontend",
                                          "controller-synthesis", "behavior-core", "banked-top",
                                          "memory-matrix", "banked-boundary", "fault-case",
                                          "fault-matrix", "integrated-csr",
                                          "attention-context", "attention-context-short",
                                          "speculative-cancel", "synthesis-production",
                                          "parent-reference", "synthesis-boundary",
                                          "attention-context-sv-short", "reproduce-child",
                                          "isolation-smoke", "speculative-cancel-case",
                                          "production-layer", "fusion-profile",
                                          "fusion-compact", "integrated-marker",
                                          "component-applicability",
                                          "layer-parallel-compact", "prefill-marker",
                                          "saved-behavior-applicability"))
    parser.add_argument("--profile", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--sim-threads", type=int, choices=(1, 2, 4, 8), default=1,
                        help="Verilator threads for layer/fusion/marker probes, not RTL geometry")
    parser.add_argument("--marker", choices=("open", "close"), default="open")
    parser.add_argument("--fault", type=int, choices=tuple(FAULT_CASES), default=1)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run = Run(args.probe or args.suite or "all", preparation=bool(args.probe),
              repair_of=args.repair_of)
    try:
        reference.self_check()
        if args.probe == "saved-behavior-applicability":
            run.versions(("python3", "verilator", "g++", "make"))
            results = saved_behavior_applicability(run)
        elif args.probe == "prefill-marker":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_prefill_marker(run, opening=args.marker == "open",
                                         threads=args.sim_threads)
        elif args.probe == "layer-parallel-compact":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_layer(run, compact=True, threads=args.sim_threads)
        elif args.probe == "component-applicability":
            run.versions(("python3", "verilator", "g++", "make", "yosys"))
            results = historical_applicability(run)
        elif args.probe == "integrated-marker":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_markers(run, opening=args.marker == "open",
                                  threads=args.sim_threads, compiled=latest_marker_build())
        elif args.probe in ("production-layer", "fusion-profile", "fusion-compact"):
            run.versions(("python3", "verilator", "g++", "make"))
            results = (run_layer(run, args.profile, threads=args.sim_threads)
                       if args.probe == "production-layer"
                       else run_fusion_profile(run, args.profile,
                                               compact=args.probe == "fusion-compact",
                                               threads=args.sim_threads))
        elif args.probe == "speculative-cancel-case":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_speculative_cancel(run, args.fault)
        elif args.probe == "isolation-smoke":
            run.versions(("python3", "iverilog", "vvp"))
            results = run_reproduce(run, child_probe="qk-compact")
        elif args.probe == "reproduce-child":
            run.versions(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
            results = run_reproduction_child(run)
        elif args.probe == "attention-context-sv-short":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_context(run, positions=64, driver="sv")
        elif args.probe == "synthesis-boundary":
            run.versions(("python3", "yosys"))
            results = run_synthesis_case(run, compact=True, banks=8, queue=16,
                                         head_dim=128, q_heads=4)
        elif args.probe == "parent-reference":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_parent(run)
        elif args.probe == "synthesis-production":
            run.versions(("python3", "yosys"))
            results = run_synthesis_case(run, profile=1)
        elif args.probe == "speculative-cancel":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_speculative_cancel_matrix(run)
        elif args.probe in ("attention-context", "attention-context-short"):
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_context(run, positions=40960 if args.probe == "attention-context" else 64)
        elif args.probe == "integrated-csr":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_telemetry(run)
        elif args.probe == "fault-case":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_fault_case(run, args.fault)
        elif args.probe == "fault-matrix":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_fault_matrix(run)
        elif args.probe == "banked-boundary":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_banked_top(run, geometry=Geometry(q_heads=4), seed=203,
                                    banks=8, queue=16)
        elif args.probe == "memory-matrix":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_memory_matrix(run)
        elif args.probe == "banked-top":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_banked_top(run)
        elif args.probe == "behavior-core":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_behavior_core(run)
        elif args.probe == "controller-synthesis":
            run.versions(("python3", "yosys"))
            results = run_controller_synthesis(run)
        elif args.probe == "synthesis-frontend":
            run.versions(("python3", "yosys"))
            results = run_synthesis_probe(run)
        elif args.probe == "startup-matrix":
            run.versions(("python3", "iverilog", "vvp"))
            results = [run_startup(run, banks=b, queue=q)
                       for b in (1, 8) for q in (1, 3, 16)]
            results.extend([run_startup(run, queue=1, q_heads=4, vocabulary=1, max_sequence=1),
                            run_startup(run, banks=8, head_dim=128, q_heads=4)])
        elif args.probe == "scalar-compiled":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_scalar(run, "verilator")
        elif args.probe == "analytic":
            from numerical_checks import analytic_coefficients
            run.versions(("python3",))
            results = analytic_coefficients()
        elif args.probe == "qk-stress":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_qk(run, "verilator", 128, True, stress=True)
        elif args.probe == "speculation":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_speculation(run)
        elif args.probe == "startup":
            run.versions(("python3", "iverilog", "vvp"))
            results = run_startup(run)
        elif args.probe == "elaboration":
            run.versions(("python3", "iverilog", "vvp"))
            results = run_elaboration(run)
        elif args.probe == "controller":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_controller(run)
        elif args.probe == "csr":
            run.versions(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
            results = [run_csr(run), run_csr(run, "verilator")]
        elif args.probe == "elementary":
            run.versions(("python3", "iverilog", "vvp"))
            results = run_elementary(run)
        elif args.probe == "tensor-sv":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_tensor(run, "verilator", True, sv_driver=True)
        elif args.probe == "tensor-cpp":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_tensor_cpp(run)
        elif args.probe in ("tensor-compact", "tensor-full"):
            compiled = args.probe == "tensor-full"
            run.versions(("python3", "verilator", "g++", "make") if compiled else
                         ("python3", "iverilog", "vvp"))
            results = run_tensor(run, "verilator" if compiled else "icarus", compiled)
        elif args.probe in ("top-compact", "top-compiled", "top-continuation"):
            compiled = args.probe != "top-compact"
            run.versions(("python3", "verilator", "g++", "make") if compiled else
                         ("python3", "iverilog", "vvp"))
            results = (run_top(run, "verilator",
                               cases=6 if args.probe == "top-continuation" else 1)
                       if compiled else run_startup(run))
        elif args.probe == "scalar":
            run.versions(("python3", "iverilog", "vvp"))
            results = run_scalar(run)
        elif args.probe == "qk-compact":
            run.versions(("python3", "iverilog", "vvp"))
            results = run_qk(run)
        elif args.probe == "qk-production":
            run.versions(("python3", "verilator", "g++", "make"))
            results = run_qk(run, "verilator", 128, True)
        elif args.suite == "smoke":
            run.versions(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
            results = run_smoke(run)
        elif args.suite == "numerical":
            run.versions(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
            results = run_numerical(run)
        elif args.suite == "synthesis":
            run.versions(("python3", "yosys"))
            results = run_synthesis(run)
        elif args.suite == "reproduce":
            run.versions(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
            results = run_reproduce(run)
        else:
            raise NotImplementedError("L1 suite authoring is in progress; no passing result claimed")
        run.finish("passed", results)
        return 0
    except Exception as error:
        run.finish("failed", error=f"{type(error).__name__}: {error}")
        print(f"FAIL {error}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
