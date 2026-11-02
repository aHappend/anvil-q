"""Incremental public-pin behavior coverage; not yet the complete admitted suite.

The core matrix compares every decoder frame, scratch write and causal KV value
against independent sequential decoding, then exercises the deferred continuation.
Coverage closure still requires the bank/fault/cancel matrix, marker integration,
production transactions, measured fusion comparison and executed parent reference.
"""

from pathlib import Path

from model import Geometry
from speculation_checks import run_speculation


def run_behavior_core(run):
    results = []
    compiled = {}
    scenarios = []
    for ratio in (2, 4):
        geometry = Geometry(q_heads=ratio)
        for prefix in range(5):
            scenarios.append((geometry, (17, 89, 203)[prefix % 3],
                              prefix, False, prefix % 3 + 1))
        scenarios.append((geometry, 203, 2, True, 1))
    for maximum in (3, 6, 7):
        scenarios.append((Geometry(max_sequence=maximum), 89,
                          min(4, maximum - 2), False, 4))
    for index, (geometry, seed, prefix, branching, fault) in enumerate(scenarios):
        key = geometry

        def operation(child, geometry=geometry, seed=seed, prefix=prefix,
                      branching=branching, fault=fault, key=key):
            result = run_speculation(
                child, prefix=prefix, geometry=geometry, seed=seed,
                branching=branching, compiled=compiled.get(key),
                storage_evaluations=8, continuation_fault=fault)
            if key not in compiled:
                compiled[key] = Path(result["compiled_binary"])
            return result

        results.append(run.component(f"behavior-core-case{index:02d}", operation))
    shapes = {(r["geometry"]["q_heads"], r["prefix"], r["branching"])
              for r in results}
    for ratio in (2, 4):
        if not all((ratio, prefix, False) in shapes for prefix in range(5)):
            raise AssertionError("missing real target accepted-prefix comparisons")
        if (ratio, 2, True) not in shapes:
            raise AssertionError("missing branching target/KV comparison")
    if {r["seed"] for r in results} != {17, 89, 203}:
        raise AssertionError("missing deterministic behavior seeds")
    return {"scope": "incremental behavior core, not full behavior closure",
            "cases": results, "case_count": len(results),
            "compilations": len(compiled),
            "compared_frames": sum(len(r["evaluations"]) for r in results),
            "compared_logit_words": sum(
                len(r["evaluations"]) * r["geometry"]["vocabulary"] for r in results),
            "remaining": [
                "direct multi-token geometry matrix and new-sequence recovery",
                "BANKS 1/8 and QUEUE_DEPTH 1/3/16 with reordered tagged responses",
                "memory faults and cancellation in all required pipeline phases",
                "integrated markers and no-double-observation",
                "production-shaped transactions and 40960-position attention leaf",
                "measured strict per-profile fusion overhead",
                "executed unchanged-parent generational reference"]}
