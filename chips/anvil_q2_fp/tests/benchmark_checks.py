"""Five-domain reduced RTL benchmark against mathematical and real parent baselines.

The complete matrix is run by tests/verify.py --check benchmark. --sample is a
bounded diagnostic using one seed/bank/cache entry, never matrix acceptance.
"""

import argparse
from collections import Counter, defaultdict, deque
import hashlib
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp_reference import value
from high_precision_reference import MathematicalTransformer
from retained import ROOT, Run
from suite_manifest import DOMAINS, SEEDS, configurations, manifest
from transformer_reference import coordinates, key


def error_metrics(observed, reference):
    assert len(observed) == len(reference) and observed, "empty/mismatched precision comparison"
    errors = [a - b for a, b in zip(observed, reference)]
    assert all(math.isfinite(x) for x in observed + reference + errors)
    square_error = math.fsum(x * x for x in errors)
    square_reference = math.fsum(x * x for x in reference)
    square_observed = math.fsum(x * x for x in observed)
    denominator = math.sqrt(square_observed * square_reference)
    return {
        "values_compared": len(errors), "max_absolute_error": max(map(abs, errors)),
        "mean_absolute_error": math.fsum(map(abs, errors)) / len(errors),
        "rms_error": math.sqrt(square_error / len(errors)),
        "normalized_rmse": math.sqrt(square_error / max(square_reference, 1e-30)),
        "cosine_similarity": (math.fsum(a * b for a, b in zip(observed, reference)) /
                              denominator if denominator else None),
    }


def domain_indices(stage):
    return [index for index, names in enumerate((
        {"projection"}, {"rmsnorm", "residual"}, {"rope"}, {"attention"},
        {"rmsnorm", "residual", "projection", "rope", "attention", "swiglu"},
    )) if stage["domain"] in names]


def precision(reference_record, mathematical, product):
    actual = reference_record["stages"]
    assert len(actual) == len(mathematical.stages), "stage count differs from mathematical workload"
    observations, expected = defaultdict(list), defaultdict(list)
    for stage, ideal in zip(actual, mathematical.stages):
        for field in ("domain", "layer", "position", "slot"):
            assert stage[field] == ideal[field], "stage identity/order differs"
        numbers = ([x / 65536 for x in stage["q16"]] if product == "parent" else
                   [float(value(int(x, 16))) for x in stage["fp32"]])
        ideals = [float(Decimal(x)) for x in ideal["real"]]
        assert len(numbers) == len(ideals)
        for domain in domain_indices(stage):
            observations[domain].extend(numbers)
            expected[domain].extend(ideals)
    for observed, ideal in zip(reference_record["logits"], mathematical.logits):
        assert observed[:2] == list(ideal[:2])
        bits = observed[2]
        number = ((bits if bits < 2**31 else bits - 2**32) / 65536 if product == "parent" else
                  float(value(bits)))
        for domain in (0, 4):
            observations[domain].append(number)
            expected[domain].append(float(ideal[2]))
    assert len(reference_record["logits"]) == len(mathematical.logits)
    return {DOMAINS[i]: error_metrics(observations[i], expected[i]) for i in range(5)}


def stage_intervals(trace, reference_record):
    stages = reference_record["stages"]
    queues = defaultdict(deque)
    for index, stage in enumerate(stages):
        length = len(stage.get("fp32", stage.get("q16", [])))
        assert length > 0
        for col in range(length):
            queues[key(8, row=stage["slot"], col=col)].append(index)
    sizes = [len(s.get("fp32", s.get("q16", []))) for s in stages]
    acknowledged = Counter()
    pending, ends, commands = {}, {}, {}
    for line in trace.read_text().splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "COMMAND":
            commands[int(fields[2])] = int(fields[1])
        elif fields[0] == "REQ" and fields[3] == "1":
            address, tag = int(fields[4], 16), int(fields[6], 16)
            if coordinates(address)[0] == 8:
                assert queues[address], "unmapped stage write"
                pending[tag] = (queues[address].popleft(), int(fields[1]))
        elif fields[0] == "RSP":
            tag = int(fields[3], 16)
            if tag in pending:
                index, accepted_cycle = pending.pop(tag)
                assert int(fields[1]) > accepted_cycle
                acknowledged[index] += 1
                if acknowledged[index] == sizes[index]:
                    ends[index] = int(fields[1])
    assert not pending and all(not q for q in queues.values())
    assert len(ends) == len(stages), "missing observed stage completions"
    totals = Counter()
    for index, stage in enumerate(stages):
        start = commands[stage["position"]] if stage["domain"] == "embedding" else ends[index - 1]
        assert ends[index] > start, "overlapping/unordered stage interval"
        for domain in domain_indices(stage):
            totals[DOMAINS[domain]] += ends[index] - start
    return dict(totals)


def child(run, label, arguments):
    output = run.command(["python3", *arguments], label, timeout=86400, expected_codes=(0, 1))
    receipts = [line for line in output.read_text().splitlines() if line.endswith("/receipt.json")]
    assert len(receipts) == 1, f"{label}: missing/ambiguous retained child receipt"
    path = ROOT / receipts[0]
    path.resolve().relative_to(ROOT.resolve())
    result = json.loads(path.read_text())
    assert result["source_sha256"] == run.receipt["source_sha256"], (
        f"{label}: sources changed during execution")
    if run.receipt["commands"][-1]["exit_code"] != 0 or result["outcome"] != "passed-focused-only":
        raise AssertionError(f"{label}: child failed: {receipts[0]}: {result.get('failure')}")
    return path, result


def execute(sample=False):
    run = Run("verifier-five-domain-sample" if sample else "verifier-five-domain-matrix")
    rows = []
    try:
        seeds = (17,) if sample else SEEDS
        matrix = configurations(seeds)
        if sample:
            matrix = [c for c in matrix if c["banks"] == 4 and c["cache_mode"] == 0 and
                      c["fp_format"] == "fp16" and c["weight_mode"] == 1]
        definition = manifest(seeds=seeds)
        definition.update(execution_scope="bounded diagnostic" if sample else "complete reduced matrix",
                          executed_matrix=matrix)
        definition_path = run.path / "suite-manifest.json"
        definition_path.write_text(json.dumps(definition, indent=2) + "\n")
        run.receipt["generated_sha256"] = {
            run.relative(definition_path): hashlib.sha256(definition_path.read_bytes()).hexdigest()}
        parent_runs, math_models = {}, {}
        for config in matrix:
            banks, cache, fmt, weights, seed = (
                config[k] for k in ("banks", "cache_mode", "fp_format", "weight_mode", "seed"))
            if seed not in math_models:
                mathematical = MathematicalTransformer(seed).execute()
                mathematical_path = run.path / f"mathematical-s{seed}.json"
                mathematical_path.write_text(json.dumps({
                    "precision_digits": 70, "seed": seed, "stages": mathematical.stages,
                    "logits": [[p, r, str(v)] for p, r, v in mathematical.logits],
                }, indent=2) + "\n")
                run.receipt["generated_sha256"][run.relative(mathematical_path)] = (
                    hashlib.sha256(mathematical_path.read_bytes()).hexdigest())
                math_models[seed] = mathematical
            label = f"fp-b{banks}-c{cache}-{fmt}-w{weights}-s{seed}"
            path, measured = child(run, label, [
                "tests/token_checks.py", "--format", fmt, "--weights", str(weights),
                "--cache", str(cache), "--banks", str(banks), "--seed", str(seed)])
            record = json.loads((path.parent / "reference.json").read_text())
            metrics = precision(record, math_models[seed], "fp")
            intervals = stage_intervals(path.parent / "simulation.stdout.txt", record)
            fp_cycles = measured["metrics"]["accepted_command_to_final_accepted_logit_cycles"]
            if weights:
                parent_key = banks, cache, seed
                if parent_key not in parent_runs:
                    parent_path, parent_measured = child(run, f"parent-b{banks}-c{cache}-s{seed}", [
                        "tests/token_checks.py", "--product", "parent", "--weights", "1",
                        "--cache", str(cache), "--banks", str(banks), "--seed", str(seed)])
                    parent_record = json.loads((parent_path.parent / "reference.json").read_text())
                    parent_runs[parent_key] = dict(
                        receipt=run.relative(parent_path), measured=parent_measured["metrics"],
                        precision=precision(parent_record, math_models[seed], "parent"),
                        domain_intervals=stage_intervals(
                            parent_path.parent / "simulation.stdout.txt", parent_record))
                parent = parent_runs[parent_key]
                parent_cycles = parent["measured"]["accepted_command_to_final_accepted_logit_cycles"]
                speedup = sum(parent_cycles) / sum(fp_cycles)
            else:
                parent = {"status": "not applicable", "reason": "parent has no native decoder weights"}
                speedup = None
            cache_writes = sum(len(values) for address, values in record["writes"].items()
                               if 9 <= coordinates(int(address, 16))[0] <= 15)
            for domain in DOMAINS:
                rows.append({
                    "domain": domain, "configuration": config, "outcome": "compared",
                    "fp_receipt": run.relative(path), "precision": metrics[domain],
                    "stage_final_ack_interval_cycles": intervals[domain],
                    "integrated_token_cycles": fp_cycles, "integrated_speedup": speedup,
                    "integrated_bank_metrics": measured["metrics"]["bank_metrics"],
                    "integrated_bank_outstanding_cycles":
                        measured["metrics"]["external_bank_occupied_cycles"],
                    "cache_stored_bytes_including_metadata_padding": 4 * cache_writes,
                    "cache_write_request_count": cache_writes,
                    "integrated_memory_request_response_count": measured["metrics"]["responses_compared"],
                    "parent": parent,
                })
        assert len(rows) == 5 * len(matrix), "benchmark denominator mismatch"
        result_path = run.path / "benchmark.json"
        result_path.write_text(json.dumps({
            "suite": definition["suite"], "rows": rows,
            "scope": "Reduced real RTL; FPGA resources, native timing and full-token hardware unmeasured.",
            "domain_cycles": "Public final-write-ack intervals, not standalone command latencies.",
        }, indent=2) + "\n")
        run.finish("passed-focused-only", metrics={
            "domain_matrix_rows_compared": len(rows), "fp_token_runs": len(matrix),
            "parent_token_runs": len(parent_runs), "results": run.relative(result_path)},
            limitations="Sample only." if sample else "Reduced L1, not native hardware acceptance.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}", completed_rows=rows)
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", action="store_true")
    raise SystemExit(execute(parser.parse_args().sample))
