#!/usr/bin/env python3
"""Independent L1 arithmetic, protocol, decoder, benchmark and synthesis checks."""

import argparse
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))

from execution import Evidence, relative
import numerics
import integration
import synthesis
import cache_checks
import nonlinear
import campaigns
import tensor_checks
import protocol_checks
import parameter_checks
import top_control
import portability
import defects
import accumulation
import attention_checks
import prefetch_checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["numerics", "protocol", "behavior", "benchmark",
                                           "synthesis", "defects", "portability"])
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--probe", choices=["conversions", "primitives", "iterative", "dots", "top", "synthesis", "cache", "nonlinear", "tensor", "scheduler", "parameters", "control", "sequence", "defect", "accumulation", "attention", "prefetch"])
    parser.add_argument("--repair-of")
    parser.add_argument("--simulator", choices=["iverilog", "verilator"], default="verilator")
    parser.add_argument("--banks", type=int, choices=[1, 2, 4, 8], default=1)
    parser.add_argument("--dtype", choices=["bf16", "fp16"], default="bf16")
    parser.add_argument("--awq", action="store_true")
    parser.add_argument("--parent", action="store_true")
    parser.add_argument("--awq-transition", action="store_true")
    parser.add_argument("--tokens", type=int, choices=[1, 4], default=1)
    parser.add_argument("--cache-mode", type=int, choices=[0, 1, 2], default=0)
    parser.add_argument("--fp8", type=int, choices=[0, 1], default=0)
    parser.add_argument("--affine", type=int, choices=[0, 1], default=0)
    parser.add_argument("--layers", type=int, choices=[1, 36], default=1)
    parser.add_argument("--queue-depth", type=int, choices=[1, 3, 16], default=3)
    parser.add_argument("--heads", type=int, default=8)
    parser.add_argument("--head-dim", type=int, default=2)
    parser.add_argument("--mutant", choices=[mutation[0] for mutation in defects.MUTATIONS], default="rounding")
    args = parser.parse_args()
    evidence = Evidence(args.probe or args.suite or "aggregate",
                        preparation=bool(args.probe), repair_of=args.repair_of)
    try:
        if args.probe:
            evidence.versions([["python3", "--version"], ["iverilog", "-V"], ["vvp", "-V"]])
            if args.probe == "prefetch":
                evidence.versions([["verilator", "--version"]])
                result = prefetch_checks.check(evidence, args.banks)
            elif args.probe == "attention":
                evidence.versions([["verilator", "--version"]])
                result = attention_checks.check(evidence, args.head_dim, args.cache_mode,
                                                args.fp8, args.affine, args.dtype, args.tokens)
            elif args.probe == "accumulation":
                evidence.versions([["verilator", "--version"]])
                result = accumulation.check(evidence, args.seed)
            elif args.probe == "defect":
                evidence.versions([["verilator", "--version"]])
                result = defects.check(evidence, args.seed, [args.mutant])
            elif args.probe == "sequence":
                evidence.versions([["verilator", "--version"]])
                result = top_control.rejected_sequence(evidence, "dtype", args.banks)
            elif args.probe == "control":
                evidence.versions([["verilator", "--version"]])
                result = top_control.check(evidence, args.banks, args.cache_mode, args.fp8, args.affine)
            elif args.probe == "parameters":
                result = parameter_checks.check(evidence, ["hidden", "group_zero", "banks_three",
                                                         "layer_address_overflow"])
            elif args.probe == "scheduler":
                evidence.versions([["verilator", "--version"]])
                result = protocol_checks.scheduler(evidence, args.banks, args.queue_depth,
                                                  args.simulator)
            elif args.probe == "tensor":
                evidence.versions([["verilator", "--version"]])
                result = tensor_checks.check(evidence, args.seed, args.banks, parent=args.parent)
            elif args.probe == "nonlinear":
                evidence.versions([["verilator", "--version"]])
                result = nonlinear.check(evidence, args.seed)
            elif args.probe == "cache":
                result = cache_checks.check(evidence, args.seed, simulator=args.simulator)
            elif args.probe == "synthesis":
                evidence.versions([["yosys", "-V"]])
                result = synthesis.synthesize(evidence, args.banks)
            elif args.probe == "top":
                evidence.versions([["verilator", "--version"]])
                result = integration.smoke(evidence, args.seed, args.simulator, args.banks,
                                           args.dtype, args.awq, args.tokens, args.cache_mode,
                                           args.fp8, args.affine, args.layers,
                                           heads=args.heads, head_dim=args.head_dim,
                                           awq_transition=args.awq_transition)
                if "tokens" in result:
                    result["benchmark_domains"] = campaigns.domain_metrics(result)
            elif args.probe in ("primitives", "dots"):
                result = getattr(numerics, args.probe)(evidence, args.seed, simulator=args.simulator)
            else:
                result = getattr(numerics, args.probe)(evidence, args.seed)
        else:
            tools = [["python3", "--version"]]
            if args.suite in ("numerics", "protocol", "portability", None):
                tools += [["iverilog", "-V"], ["vvp", "-V"]]
            if args.suite != "synthesis":
                tools.append(["verilator", "--version"])
            if args.suite in ("synthesis", "portability", None):
                tools.append(["yosys", "-V"])
            evidence.versions(tools)
            dispatch = {"numerics": campaigns.numerics_suite,
                        "protocol": campaigns.protocol,
                        "behavior": campaigns.behavior,
                        "benchmark": campaigns.benchmark,
                        "synthesis": campaigns.synthesis_suite,
                        "portability": portability.check,
                        "defects": defects.check}
            if args.suite is None:
                result = {}
                for suite, check in dispatch.items():
                    if suite == "behavior":
                        result[suite] = {str(seed): check(evidence.scope(f"behavior-seed{seed}"), seed)
                                         for seed in (17, 89, 211)}
                    else:
                        result[suite] = check(evidence.scope(suite), args.seed)
            else:
                result = dispatch[args.suite](evidence, args.seed)
        evidence.finish("passed", comparisons=result)
        print(f"PASS {relative(evidence.path / 'receipt.json')}")
        return 0
    except Exception as error:
        evidence.finish("failed", error=f"{type(error).__name__}: {error}")
        traceback.print_exc()
        print(f"FAIL {relative(evidence.path / 'receipt.json')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
