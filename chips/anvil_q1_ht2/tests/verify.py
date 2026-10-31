#!/usr/bin/env python3
"""Portable L1 entry point and bounded, retained preparation probes.

Verification is under construction. No unimplemented suite is reported as a
passing check. Physical timing/board execution belongs to the shared runtime.
"""

import argparse
import json
from pathlib import Path
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence import bindings, fresh, now, relative, set_budget, write_json
import leaf_checks


PROBES = {
    "conversions": leaf_checks.conversions,
    "pipelines": leaf_checks.pipelines,
    "sparse": leaf_checks.sparse,
    "verifier": leaf_checks.verifier,
    "awq": leaf_checks.dequant,
    "mac": leaf_checks.mac,
    "masks": leaf_checks.masks,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("behavior", "mutations", "synthesis",
                        "benchmark-contract", "reproduction", "full-model-benchmarks"))
    parser.add_argument("--probe", choices=(*PROBES, "divsqrt", "exp", "sincos", "mutations",
                                          "rmsnorm", "swiglu", "mutation-rounding", "top",
                                          "synthesis-array", "synthesis-top", "parameters", "top-startup",
                                          "cdc-fifo", "cdc-mailbox", "control", "compatibility",
                                          "logical-compatibility", "benchmark-prerequisites",
                                          "harness-selfcheck"))
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="iverilog")
    parser.add_argument("--mode", choices=("bf16", "fp16", "w4"), default="bf16")
    parser.add_argument("--geometry", choices=("singleton", "compact", "gqa", "medium"),
                        default="compact")
    parser.add_argument("--seed", type=int, choices=(17, 43, 89), default=17)
    parser.add_argument("--threshold", type=lambda x: int(x, 0), default=0)
    parser.add_argument("--compact", action="store_true",
                        help="bounded clean-reproduction matrix; not official full-model evidence")
    parser.add_argument("--repair-of", help="project-relative retained receipt")
    args = parser.parse_args()
    if bool(args.suite) == bool(args.probe):
        parser.error("select exactly one of --suite or --probe")
    suite = args.probe or args.suite
    directory = fresh(suite, preparation=bool(args.probe))
    start, monotonic = now(), time.monotonic()
    set_budget(2700)
    source_hashes = bindings()
    result = {"schema_version": 1, "suite": suite, "start_time": start,
              "argv": ["python3", "tests/verify.py", *sys.argv[1:]], "cwd": ".",
              "source_sha256": source_hashes, "repair_of": args.repair_of,
              "preparation": bool(args.probe), "checks": [],
              "python_version": sys.version}
    code = 1
    with (directory / "stdout.txt").open("x") as out, (directory / "stderr.txt").open("x") as err:
        try:
            if args.probe:
                if suite in PROBES:
                    check = PROBES[suite](directory, args.simulator)
                elif suite in ("top", "top-startup"):
                    import integration_checks
                    from decoder_reference import Geometry
                    geometries = {
                        "singleton": Geometry(vocabulary=1, sequence=1, window=1),
                        "compact": Geometry(),
                        "gqa": Geometry(2, 24, 40, 3, 1, 8, 8, 31, 9, 3, 3),
                        "medium": Geometry(2, 64, 128, 4, 2, 16, 16, 257, 17, 3, 5),
                    }
                    check = integration_checks.top(
                        directory, args.simulator, geometries[args.geometry],
                        {"bf16": 0, "fp16": 1, "w4": 2}[args.mode], args.seed,
                        batch=args.geometry != "singleton", startup=suite == "top-startup",
                        threshold=args.threshold)
                elif suite in ("synthesis-array", "synthesis-top"):
                    import synthesis_checks
                    check = {"name": suite, "results": synthesis_checks.synthesize(
                        directory, ("anvil_q1_ht2_top" if suite == "synthesis-top"
                                    else "anvil_q1_ht2_tile_batch_mac",))}
                elif suite == "parameters":
                    import parameter_checks
                    check = {"name": suite, "results": parameter_checks.run(directory)}
                elif suite in ("cdc-fifo", "cdc-mailbox", "control"):
                    import protocol_checks
                    check = (protocol_checks.control(directory, args.simulator) if suite == "control"
                             else protocol_checks.cdc(directory, "mailbox" if suite == "cdc-mailbox"
                                                      else "response_fifo", args.simulator))
                elif suite == "compatibility":
                    import compatibility_checks
                    check = compatibility_checks.run(
                        directory, {"bf16": 0, "fp16": 1, "w4": 2}[args.mode], args.seed)
                elif suite == "logical-compatibility":
                    import compatibility_checks
                    check = compatibility_checks.logical_top(directory)
                elif suite == "benchmark-prerequisites":
                    import hardware_workload
                    document, path = hardware_workload.inputs()
                    check = {"name": suite, "manifest": relative(path)}
                elif suite == "harness-selfcheck":
                    import tooling_checks
                    check = tooling_checks.run(directory)
                elif suite == "mutations":
                    import mutation_checks
                    check = {"name": "mutations", "results": mutation_checks.run(directory)}
                elif suite == "mutation-rounding":
                    import mutation_checks
                    check = {"name": suite, "results": mutation_checks.run(
                        directory, {"multiply-rounding"})}
                elif suite in ("rmsnorm", "swiglu"):
                    import operator_checks
                    check = operator_checks.vectors(directory, suite, args.simulator)
                else:
                    check = leaf_checks.scalars(directory, suite, args.simulator)
                result["checks"].append(check)
            elif suite == "mutations":
                import mutation_checks
                result["checks"] = mutation_checks.run(directory)
            elif suite == "synthesis":
                import synthesis_checks
                result["checks"] = synthesis_checks.synthesize(directory)
            elif suite == "full-model-benchmarks":
                import benchmark_checks
                result["checks"] = benchmark_checks.full_model(directory)
            elif suite == "behavior":
                import suites
                result["checks"] = suites.behavior(directory, args.compact)
            elif suite == "reproduction":
                import suites
                result["checks"] = suites.reproduction(directory)
            else:
                raise NotImplementedError(f"{suite}: mandatory verification suite not yet implemented")
            code = 0
        except Exception as exc:
            result["failure"] = f"{type(exc).__name__}: {exc}"
            traceback.print_exc(file=err)
            print(result["failure"], file=sys.stderr, flush=True)
        finally:
            result.update(exit_code=code, status="passed" if code == 0 else "failed",
                          end_time=now(), duration_s=time.monotonic() - monotonic,
                          timeout_s=2700, timed_out=False, stdout="stdout.txt", stderr="stderr.txt",
                          source_unchanged=bindings() == source_hashes,
                          tool_versions="See source-bound child receipts")
            if not result["source_unchanged"]:
                code = result["exit_code"] = 1
                result["status"] = "failed"
                result["failure"] = "verification inputs changed during execution"
            out.write(json.dumps({"status": result["status"], "checks": result["checks"]}) + "\n")
            write_json(directory / "receipt.json", result)
    print(json.dumps({"status": result["status"], "receipt": relative(directory / "receipt.json")}),
          flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
