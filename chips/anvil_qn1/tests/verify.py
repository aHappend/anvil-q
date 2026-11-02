#!/usr/bin/env python3
"""Anvil-QN1 independent L1 verification entry point.

Current executable preparation coverage:
  scalar: exact-rational add/subtract/multiply/divide/sqrt, signed zero,
          subnormals, overflow/nonfinite rejection, and output stalls.
  qk-compact / qk-production: per-element numerical parity, five RoPE positions,
          invalid heads, metadata, 133-edge latency, reset/flush and stalls.
  tensor-compact / tensor-full: both weight formats, dynamic 256-lane reductions,
          masks, per-lane isolation, tags, 48 enabled-edge latency and global stalls.
  elementary: deterministic E parity/error bound and BF16 SiLU parity/error bound.
  top-compiled / top-continuation: seven projections, both residuals, final norm,
          every logit, external scratch/KV payloads and direct deferred continuation.

The mandatory suite dispatchers are not yet complete. Preparation results are
not engineering acceptance and do not assert controller, CSR, benchmark,
mutation, synthesis, production overhead or portable-reproduction closure.
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
                                          "speculation"))
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run = Run(args.probe or args.suite or "all", preparation=bool(args.probe),
              repair_of=args.repair_of)
    try:
        reference.self_check()
        if args.probe == "speculation":
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
