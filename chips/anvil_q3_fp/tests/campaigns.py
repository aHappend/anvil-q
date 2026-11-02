"""Mandatory suite dispatch; every suite generates its own inputs and tools."""

import json

import cache_checks
import integration
import nonlinear
import numerics
import synthesis
import tensor_checks
import protocol_checks
import parameter_checks
import top_control
import accumulation


REPRESENTATIONS = ((0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 0, 0), (2, 0, 1))


def numerics_suite(evidence, seed):
    results = {"conversions": numerics.conversions(evidence, seed),
               "cache": cache_checks.check(evidence, seed, exhaustive=True),
               "nonlinear": nonlinear.check(evidence, seed), "seeds": {}}
    for numeric_seed in (17, 89, 211):
        scope = evidence.scope(f"seed-{numeric_seed}")
        print(f"NUMERICS seed={numeric_seed}", flush=True)
        results["seeds"][str(numeric_seed)] = {
            "primitives": numerics.primitives(scope, numeric_seed),
            "iterative": numerics.iterative(scope, numeric_seed),
            "dots": numerics.dots(scope, numeric_seed),
            "masked_accumulation": accumulation.check(scope, numeric_seed)}
    scope = evidence.scope("tensor-accumulation")
    results["accumulation"] = []
    for banks in (1, 2, 4, 8):
        results["accumulation"] += tensor_checks.check(scope, seed, banks)
        results["accumulation"] += tensor_checks.check(scope, seed, banks, tile_rows=1,
                                                       tile_k=128, hidden=128,
                                                       intermediate=136, head_dim=16, repeats=1)
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
                                                     fmt, awq, 4, mode, fp8, affine, heads=16))
                    (evidence.path / "behavior-progress.json").write_text(json.dumps(results, indent=2) + "\n")
    if len(results) != 80 or any(len(row["tokens"]) != 4 for row in results):
        raise AssertionError("Incomplete bank/cache/dtype/AWQ matrix")
    transitions = []
    for fmt in ("bf16", "fp16"):
        transitions.append(integration.smoke(evidence, seed, "verilator", 8,
                                             fmt, False, 4, 0, heads=16,
                                             awq_transition=True))
    mode, fp8, affine = REPRESENTATIONS[{17: 0, 89: 2, 211: 4}.get(seed, 0)]
    deep = integration.smoke(evidence, seed, "verilator", 1, "bf16", False, 4,
                             mode, fp8, affine, layers=36, intermediate=8, vocab=1)
    return {"seed": seed, "one_layer_matrix": results, "native_to_awq": transitions,
            "compact_36_layer_sequencing": deep}


def protocol(evidence, seed):
    results = {"scheduler": [], "top_control": []}
    for banks in (1, 2, 4, 8):
        for depth in (1, 3, 16):
            results["scheduler"].append(protocol_checks.scheduler(evidence, banks, depth))
    results["icarus_startup"] = protocol_checks.scheduler(evidence, 1, 1, "iverilog")
    results["invalid_parameters"] = parameter_checks.check(evidence)
    for mode, fp8, affine in REPRESENTATIONS:
        results["top_control"] += top_control.check(evidence, 1, mode, fp8, affine)
    results["sequence_rejections"] = [top_control.rejected_sequence(evidence, case)
                                      for case in ("dtype", "position", "phase-reversal", "token-id")]
    results["minimal_top"] = integration.smoke(evidence, seed, "iverilog", 1,
                                              vocab=1, max_seq_len=1, tile_rows=1)
    return results


def synthesis_suite(evidence, seed):
    results = []
    for banks in (1, 2, 4, 8):
        for mode, fp8, affine in REPRESENTATIONS:
            print(f"SYNTHESIS banks={banks} mode={mode} fp8={fp8} affine={affine}", flush=True)
            results.append(synthesis.synthesize(evidence, banks, mode, fp8, affine))
    results.append(synthesis.synthesize(evidence, 8, production=True))
    return results
