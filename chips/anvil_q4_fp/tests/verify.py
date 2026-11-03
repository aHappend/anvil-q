#!/usr/bin/env python3
"""Portable, self-contained L1 entry point; all comparisons execute real tools."""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import new_run, relative, source_hashes
import evidence


SUITES = ("numerics", "behavior", "compatibility", "defects", "synthesis", "delivery")


def run_suite(suite):
    start = time.monotonic()
    evidence.DEADLINE = start + 2700
    directory = new_run(f"suite-{suite}")
    records = []

    def check(label, function, *args, **kwargs):
        print(f"L1 {suite}: {label}", flush=True)
        before = time.monotonic()
        result = function(*args, **kwargs)
        records.append({"check": label, "duration_s": time.monotonic()-before,
                        "directory": relative(result)})
        if time.monotonic()-start > 2700:
            raise RuntimeError(f"L1 {suite} exceeded aggregate 2700s patrol budget")

    try:
        if suite == "numerics":
            import numerics
            import cache_decode
            import tensor
            check("IEEE-exhaustive-and-three-seeds", numerics.run)
            check("frozen-exp-and-high-precision", numerics.run_exp)
            check("all-cache-encodings", cache_decode.run)
            check("tensor-default-edges-and-mask", tensor.run)
            check("tensor-singleton", tensor.run, lanes=1, tile_k=1)
            check("tensor-nonpower", tensor.run, lanes=3, tile_k=3)
        elif suite == "behavior":
            import attention
            import behavior
            import cache_write
            import descriptor
            import integrated
            import scheduler
            import speculative
            import top_safety
            check("four-state-startup-and-illegal-parameters", top_safety.run)
            check("atomic-descriptors", descriptor.run)
            check("all-attention-dimensions", attention.run_matrix)
            check("packed-cache-pages-and-readback", cache_write.run)
            check("Icarus-cache-smoke", cache_write.run, icarus_smoke=True)
            check("scheduler-sixteen-banks", scheduler.run)
            check("scheduler-singleton-conflicts", scheduler.run, banks=1, queue=1)
            check("speculation-public-leaf", speculative.run)
            check("integrated-speculation-drain-rollback", integrated.run)
            check("48-format-cache-GQA-crosses", behavior.run_matrix)
            check("geometries-seeds-and-real-hierarchy-cohorts", behavior.run_geometries)
        elif suite == "compatibility":
            import compatibility
            check("all-four-original-parent-modes", compatibility.run)
        elif suite == "defects":
            import defects
            check("IEEE-rounding-and-flags", defects.numerical_mutants)
            check("protocol-commit-rollback-and-native-mutants", defects.protocol_mutants)
        elif suite == "synthesis":
            import synthesis
            check("three-geometries-no-latch-and-lane-connectivity", synthesis.run)
        else:
            import delivery
            check("source-only-clean-reproduction", delivery.run)
    except Exception as error:
        (directory / "result.json").write_text(json.dumps({
            "suite": suite, "status": "failed", "error": str(error),
            "source_sha256": source_hashes(), "completed": records,
            "duration_s": time.monotonic()-start}, indent=2) + "\n")
        raise
    (directory / "result.json").write_text(json.dumps({
        "suite": suite, "status": "passed", "source_sha256": source_hashes(),
        "checks": records, "duration_s": time.monotonic()-start}, indent=2) + "\n")
    print(f"L1 {suite}: passed; ledger {relative(directory / 'result.json')}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=SUITES)
    args = parser.parse_args()
    for name in (args.suite,) if args.suite else SUITES:
        run_suite(name)
