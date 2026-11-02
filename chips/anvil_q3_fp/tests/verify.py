#!/usr/bin/env python3
"""Independent L1 entry point. Verification implementation is incremental."""

import argparse
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))

from execution import Evidence, relative
import numerics
import integration
import synthesis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["numerics", "protocol", "behavior", "benchmark",
                                           "synthesis", "defects", "portability"])
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--probe", choices=["conversions", "primitives", "iterative", "dots", "top", "synthesis"])
    parser.add_argument("--repair-of")
    parser.add_argument("--simulator", choices=["iverilog", "verilator"], default="verilator")
    parser.add_argument("--banks", type=int, choices=[1, 2, 4, 8], default=1)
    parser.add_argument("--dtype", choices=["bf16", "fp16"], default="bf16")
    parser.add_argument("--awq", action="store_true")
    parser.add_argument("--tokens", type=int, choices=[1, 4], default=1)
    args = parser.parse_args()
    evidence = Evidence(args.probe or args.suite or "aggregate",
                        preparation=bool(args.probe), repair_of=args.repair_of)
    try:
        if args.probe:
            evidence.versions([["python3", "--version"], ["iverilog", "-V"], ["vvp", "-V"]])
            if args.probe == "synthesis":
                evidence.versions([["yosys", "-V"]])
                result = synthesis.synthesize(evidence, args.banks)
            elif args.probe == "top":
                evidence.versions([["verilator", "--version"]])
                result = integration.smoke(evidence, args.seed, args.simulator, args.banks,
                                           args.dtype, args.awq, args.tokens)
            else:
                result = getattr(numerics, args.probe)(evidence)
        else:
            raise NotImplementedError("Full L1 suites are not yet authored; this is not a ready handoff")
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
