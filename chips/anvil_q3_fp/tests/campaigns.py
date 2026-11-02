"""Mandatory suite dispatch; every suite generates its own inputs and tools."""

import json

import cache_checks
import integration
import nonlinear
import numerics
import synthesis


REPRESENTATIONS = ((0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 0, 0), (2, 0, 1))


def numerics_suite(evidence, seed):
    results = {"conversions": numerics.conversions(evidence, seed),
               "primitives": numerics.primitives(evidence, seed),
               "iterative": numerics.iterative(evidence, seed),
               "dots": numerics.dots(evidence, seed),
               "cache": cache_checks.check(evidence, seed, exhaustive=True),
               "nonlinear": nonlinear.check(evidence, seed)}
    return results


def behavior(evidence, seed):
    results = []
    for banks in (1, 2, 4, 8):
        for mode, fp8, affine in REPRESENTATIONS:
            for fmt in ("bf16", "fp16"):
                for awq in (False, True):
                    print(f"BEHAVIOR seed={seed} banks={banks} mode={mode} fp8={fp8} "
                          f"affine={affine} fmt={fmt} awq={int(awq)}", flush=True)
                    results.append(integration.smoke(evidence, seed, "verilator", banks,
                                                     fmt, awq, 4, mode, fp8, affine))
                    (evidence.path / "behavior-progress.json").write_text(json.dumps(results, indent=2) + "\n")
    if len(results) != 80 or any(len(row["tokens"]) != 4 for row in results):
        raise AssertionError("Incomplete bank/cache/dtype/AWQ matrix")
    return {"seed": seed, "one_layer_matrix": results}


def synthesis_suite(evidence, seed):
    results = []
    for banks in (1, 2, 4, 8):
        for mode, fp8, affine in REPRESENTATIONS:
            print(f"SYNTHESIS banks={banks} mode={mode} fp8={fp8} affine={affine}", flush=True)
            results.append(synthesis.synthesize(evidence, banks, mode, fp8, affine))
    results.append(synthesis.synthesize(evidence, 8, production=True))
    return results
