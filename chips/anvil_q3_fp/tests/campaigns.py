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
import attention_checks
import prefetch_checks


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
                                                     fmt, awq, 4, mode, fp8, affine))
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
    results["tail_gqa_cache"] = []
    for dimension in (34, 66):
        for mode, fp8, affine in REPRESENTATIONS:
            for fmt in ("bf16", "fp16"):
                results["tail_gqa_cache"].append(attention_checks.check(
                    evidence, dimension, mode, fp8, affine, fmt, tokens=1))
    results["default_prefetch_overlap"] = []
    for banks in (1, 2, 4, 8):
        results["default_prefetch_overlap"] += prefetch_checks.check(evidence, banks, [0])
        results["default_prefetch_overlap"] += prefetch_checks.check(
            evidence, banks, [0], row_count=1, input_counts=(128, 1))
    return results


def synthesis_suite(evidence, seed):
    results = []
    for banks in (1, 2, 4, 8):
        for mode, fp8, affine in REPRESENTATIONS:
            print(f"SYNTHESIS banks={banks} mode={mode} fp8={fp8} affine={affine}", flush=True)
            results.append(synthesis.synthesize(evidence, banks, mode, fp8, affine))
    results.append(synthesis.synthesize(evidence, 8, production=True))
    return results


def benchmark(evidence, seed):
    """Measured synthetic five-domain work; no real-checkpoint extrapolation."""
    rows = []
    for banks in (1, 2, 4, 8):
        for mode, fp8, affine in REPRESENTATIONS:
            for fmt in ("bf16", "fp16"):
                for awq in (False, True):
                    print(f"BENCHMARK banks={banks} mode={mode} fp8={fp8} affine={affine} "
                          f"fmt={fmt} awq={int(awq)}", flush=True)
                    run = integration.smoke(evidence, seed, "verilator", banks, fmt,
                                            awq, 4, mode, fp8, affine)
                    rows.append({"execution": run, "domains": domain_metrics(run)})
                    (evidence.path / "benchmark-progress.json").write_text(json.dumps(rows, indent=2) + "\n")
    if len(rows) != 80 or any(len(row["domains"]) != 5 for row in rows):
        raise AssertionError("Missing five-domain bank/cache/dtype/AWQ benchmark cells")
    tensor, parent, sampled = [], [], []
    for banks in (1, 2, 4, 8):
        scope = evidence.scope(f"projection-comparison-b{banks}")
        tensor += tensor_checks.check(scope, seed, banks, repeats=1)
        parent += tensor_checks.check(scope, seed, banks, repeats=1, parent=True)
        sampled += prefetch_checks.check(evidence, banks)
    direct = []
    for baseline in parent:
        matched = [row for row in tensor if row["banks"] == baseline["banks"] and
                   row["format"] == baseline["format"] and row["awq"] == 1]
        if len(matched) != 1:
            raise AssertionError("Missing matched represented-input INT-versus-FP projection run")
        for integer, floating in zip(baseline["measured_commands"], matched[0]["measured_commands"]):
            if integer["projection"] != floating["projection"]:
                raise AssertionError("Parent/FP projection ordering differs")
            direct.append({"banks": baseline["banks"], "format": baseline["format"],
                           "projection": integer["projection"], "integer": integer, "floating": floating,
                           "fp_minus_int_cycles": floating["command_to_done_cycles"] - integer["command_to_done_cycles"],
                           "fp_minus_int_bytes": floating["response_bytes"] - integer["response_bytes"]})
    default_attention = []
    for mode, fp8, affine in REPRESENTATIONS:
        for fmt in ("bf16", "fp16"):
            default_attention.append(attention_checks.check(evidence, 128, mode, fp8, affine, fmt, tokens=1))
    deep = integration.smoke(evidence, seed, "verilator", 1, "bf16", False, 4,
                             layers=36, intermediate=8, vocab=1)
    return {"synthetic_seed": seed, "clock_hz_for_bandwidth": 100000000,
            "matrix": rows, "projection_runs": tensor, "immutable_parent_runs": parent,
            "matched_int_fp_comparison": direct, "production_shape_selected_tiles": sampled,
            "default_head128_gqa_cache": default_attention, "compact_36_layers": deep,
            "scope": "synthetic compact full decoder and explicitly sampled default row tiles; "
                     "not a complete Qwen checkpoint, physical PPA or measured device frequency"}


def domain_metrics(run):
    traffic = run["public_transaction_traffic"]
    if not traffic:
        raise AssertionError("Benchmark has no measured public-memory traffic")
    selectors = (
        ("projection_tensor_gemv", lambda r: r["kind"] in (1, 2, 3, 4)),
        ("causal_gqa_hierarchical_kv", lambda r: r["kind"] in (9, 10, 12, 13, 14, 15) or
         r["kind"] == 8 and r["scratch_slot"] in (2, 3, 4, 5)),
        ("rmsnorm_rope_residual", lambda r: r["kind"] in (5, 6, 7, 11) or
         r["kind"] == 8 and r["scratch_slot"] in (0, 1, 2, 3, 7, 8, 14)),
        ("silu_swiglu_mlp", lambda r: r["kind"] in (1, 2, 3) and r["projection"] >= 4 or
         r["kind"] == 8 and r["scratch_slot"] in (9, 10, 11, 12)),
        ("integrated_decoder_token_logit", lambda r: True),
    )
    parameters = run["parameters"]
    h, i, d = parameters["HIDDEN_SIZE"], parameters["INTERMEDIATE_SIZE"], parameters["HEAD_DIM"]
    layers, tokens, heads = parameters["NUM_LAYERS"], len(run["tokens"]), parameters["NUM_Q_HEADS"]
    operations = [
        tokens * layers * 2 * (2 * h * h + 2 * h * (heads // 8) * d + 3 * h * i),
        layers * sum(heads * d * 4 * (t + 1) for t in range(tokens)),
        tokens * ((layers * 2 + 1) * h * 6 + layers * (h + heads // 8 * d) * 6 + layers * h * 2),
        tokens * layers * (6 * h * i + 4 * i),
    ]
    operations.append(sum(operations) - tokens * layers * 6 * h * i +
                      tokens * parameters["VOCAB_SIZE"] * h * 2)
    results = []
    banks = parameters["BANKS"]
    for index, (name, predicate) in enumerate(selectors):
        selected = [row for row in traffic if predicate(row)]
        transfers = sum(row["accepted_reads"] + row["accepted_writes"] for row in selected)
        if not selected or not transfers:
            raise AssertionError(f"Benchmark domain has no real accepted transactions: {name}")
        first = min(row["first_accepted_request_cycle"] for row in selected)
        last = max(row["last_response_cycle"] for row in selected)
        if last < first:
            raise AssertionError("Unretired benchmark memory traffic")
        cycles = last - first + 1
        total_bytes = transfers * 4
        metadata = sum(4 * (row["accepted_reads"] + row["accepted_writes"])
                       for row in selected if row["kind"] in (14, 15))
        padding = sum(row["padding_bytes"] for row in selected)
        observed = total_bytes * 100000000 / cycles
        ideal = banks * 4 * 100000000
        results.append({"domain": name, "public_traffic_span_cycles": cycles,
                        "span_definition": "first accepted request through last accepted response, includes gaps; "
                                           "overlapping domain traffic is not additive",
                        "accepted_token_to_done_cycles": [row["cycles"] for row in run["tokens"]],
                        "useful_operations": operations[index],
                        "operation_definition": "algorithmic scalar multiply/add and nonlinear calls, not DSP instruction count",
                        "transferred_bytes": total_bytes, "metadata_bytes": metadata,
                        "padding_bytes": padding,
                        "payload_bytes": total_bytes - metadata - padding,
                        "request_stalls": sum(row["request_stalls"] for row in selected),
                        "observed_bytes_per_second_at_100mhz": observed,
                        "ideal_configured_bank_bytes_per_second_at_100mhz": ideal,
                        "bandwidth_gap_bytes_per_second": ideal - observed})
    return results
