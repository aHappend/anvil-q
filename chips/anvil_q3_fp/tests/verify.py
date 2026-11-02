#!/usr/bin/env python3
"""Self-contained synthetic L1 verification, without checkpoint or board access.

Reproduce with ``python3 tests/verify.py --suite <name>`` from a directory
containing rtl/*.sv, tests/*.py, anvil_q3_reference/rtl/*.sv and the two design
documents. No arguments execute every mandatory suite and behavior seed.
Each invocation retains fresh source hashes, generated vectors and raw tool logs.

Numerics: exhaustive BF16/FP16 conversion and lossless cache encodings, exact
integer/Fraction IEEE arithmetic, masked reductions/accumulation, nonlinear
FP64 bounds and reset/flush discard. Protocol: external tag/transaction
scoreboards, stalls, faults/cancellation/restart, illegal parameters and GQA
tail groups. Behavior: every bank/cache representation/dtype/native-AWQ cell
for seeds 17/89/211, four-token sequencing, transitions and compact 36 layers.
Benchmark: five public-transaction domains, seven projection shapes, matched
independently checked parent AWQ runs and explicitly sampled production tiles.
Synthesis: real memory-preserving Yosys checks at every bank/cache representation
and the default hierarchy. Defects: six disposable observable mutations.
Portability: real compact simulation and synthesis in a fresh declared-source copy.

The aggregate uses two bounded workers and may share identical, already checked
fixtures within that invocation; it never loads past receipts to manufacture a
pass. One monotonic 2700-second budget includes fixture generation, compilation
and nested checks; every child command is capped at 600 seconds or remaining
budget. Process watchdog failures never become numerical/protocol successes.
Generic Yosys cells are not ALMs/DSPs. Physical timing/PPA, HIL, authentic parent
physical evidence and the independently approved PDF remain separate obligations.
"""

import argparse
from pathlib import Path
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor

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
import execution_checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["numerics", "protocol", "behavior", "benchmark",
                                           "synthesis", "defects", "portability"])
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--probe", choices=["conversions", "primitives", "iterative", "dots", "top", "synthesis", "cache", "nonlinear", "tensor", "scheduler", "parameters", "control", "sequence", "defect", "accumulation", "attention", "prefetch", "execution"])
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
    parser.add_argument("--compact", action="store_true",
                        help="Use the minimal top fixture while preserving requested layers and token count")
    parser.add_argument("--mutant", choices=[mutation[0] for mutation in defects.MUTATIONS], default="rounding")
    args = parser.parse_args()
    evidence = Evidence(args.probe or args.suite or "aggregate",
                        preparation=bool(args.probe), repair_of=args.repair_of)
    try:
        if args.probe:
            evidence.versions([["python3", "--version"], ["iverilog", "-V"], ["vvp", "-V"]])
            if args.probe == "execution":
                evidence.versions([["verilator", "--version"], ["g++", "--version"], ["make", "--version"]])
                result = execution_checks.check(evidence, args.seed)
            elif args.probe == "prefetch":
                evidence.versions([["verilator", "--version"]])
                result = prefetch_checks.check(evidence, args.banks, row_count=1 if args.compact else 3,
                                               input_counts=(128, 1) if args.compact else (128, 125))
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
                result = synthesis.synthesize(evidence, args.banks, args.cache_mode,
                                               args.fp8, args.affine)
            elif args.probe == "top":
                evidence.versions([["verilator", "--version"]])
                result = integration.smoke(evidence, args.seed, args.simulator, args.banks,
                                           args.dtype, args.awq, args.tokens, args.cache_mode,
                                           args.fp8, args.affine, args.layers,
                                           heads=8 if args.compact else args.heads,
                                           head_dim=2 if args.compact else args.head_dim,
                                           intermediate=8 if args.compact else 24,
                                           vocab=1 if args.compact else 3,
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
                tools += [["verilator", "--version"], ["g++", "--version"], ["make", "--version"]]
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
                def run_suite(suite, check):
                    if suite == "behavior":
                        return {str(seed): check(evidence.scope(f"behavior-seed{seed}"), seed)
                                for seed in (17, 89, 211)}
                    return check(evidence.scope(suite), args.seed)
                with ThreadPoolExecutor(max_workers=2) as executor:
                    jobs = {suite: executor.submit(run_suite, suite, check)
                            for suite, check in dispatch.items()}
                    result = {suite: job.result() for suite, job in jobs.items()}
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
