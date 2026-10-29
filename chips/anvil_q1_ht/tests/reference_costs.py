"""Bounded checkpoint cost diagnosis; never a reduced acceptance campaign.

Run ``python3 -B tests/reference_costs.py``. Two consecutive real default-model
prompt-prefix tokens per mode expose initial sampling and steady-state costs.
All mandatory prompts, logits and decode lengths remain in the L1 entrypoint.
"""

import argparse
import ast
import copy
import cProfile
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import pstats
import random
import struct
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint_reference import CheckpointModel, IntegerGEMV, qualify, sha
from fixtures import project_path, validate
from prompts import FrozenTokenizer, PROMPTS, canonical_chat, merge_heap, merge_scan
from software_discrepancy import FloatingGEMV, FloatingModel, compare
from software_discrepancy import qualify as qualify_floating
from reference import exp_q24, fp_q16


PREDECESSOR = (
    "evidence/preparation/verifier-checkpoint-reference-input-"
    "20261029T102107Z-b8de9733/receipt.json"
)


def profiled(evidence, label, operation):
    profile = cProfile.Profile()
    started = time.monotonic()
    result = profile.runcall(operation)
    elapsed = time.monotonic() - started
    path = evidence.folder / (label + ".prof")
    profile.dump_stats(path)
    rows = []
    for (filename, line, function), values in pstats.Stats(profile).stats.items():
        primitive, calls, own, cumulative, _ = values
        # Do not publish host paths from profiler internals.
        rows.append({"file": Path(filename).name, "line": line, "function": function,
                     "primitive_calls": primitive, "calls": calls,
                     "own_seconds": own, "cumulative_seconds": cumulative})
    rows.sort(key=lambda row: row["cumulative_seconds"], reverse=True)
    report = {"label": label, "wall_seconds": elapsed, "functions": rows}
    output = evidence.folder / (label + ".json")
    with output.open("x") as stream:
        json.dump(report, stream, indent=2)
    evidence.record.setdefault("runtime_input_sha256", {}).update({
        evidence.relative(output): sha(output), evidence.relative(path): sha(path)})
    evidence.record["observations"].append({
        "label": label, "wall_seconds": elapsed, "profile": evidence.relative(output)})
    evidence.flush()
    print(json.dumps({"cost_phase": label, "wall_seconds": elapsed}), flush=True)
    return result, report


def qualify_caches(seed):
    rng = random.Random(seed)
    compared = rejected = 0
    for bits in range(65536):
        for exponent, fraction, scale in ((5, 10, False), (8, 7, False), (5, 10, True)):
            args = bits, exponent, fraction, scale
            try:
                expected = fp_q16.__wrapped__(*args)
            except ValueError:
                try:
                    fp_q16(*args)
                except ValueError:
                    rejected += 1
                else:
                    raise AssertionError("memoized conversion swallowed invalid input")
            else:
                for _ in range(2):
                    if fp_q16(*args) != expected:
                        raise AssertionError("memoized conversion changed exact value")
                    compared += 1
    values = [-1048577, -1048576, -1048575, -1, 0, 1, -(1 << 31), (1 << 31) - 1]
    values += [rng.randrange(-1048577, 2) for _ in range(100000)]
    for value in values:
        expected = exp_q24.__wrapped__(value)
        for _ in range(2):
            if exp_q24(value) != expected:
                raise AssertionError("memoized integer exponential changed recurrence")
            compared += 1
    if fp_q16.cache_info().currsize > 131072 or exp_q24.cache_info().currsize > 65536:
        raise AssertionError("unbounded numerical memoization")
    return {"exact_scalar_comparisons": compared, "invalid_conversions_rejected": rejected}


def baseline_engine(engine, receipt, library_name, symbol):
    record = json.loads(receipt.read_text())
    if record.get("outcome") != "probe_passed":
        raise ValueError("baseline library requires a completed diagnostic receipt")
    library = receipt.parent / library_name
    if record["runtime_input_sha256"].get(str(library)) != sha(library):
        raise ValueError("baseline numerical library is not bound to retained receipt")
    result = copy.copy(engine)
    result.library = ctypes.CDLL(str(library.resolve()))
    original = getattr(engine.library, symbol)
    function = getattr(result.library, symbol)
    function.argtypes, function.restype = original.argtypes, original.restype
    return result


def original_module(receipt, filename):
    record = json.loads(receipt.read_text())
    snapshot = (project_path(record["original_evaluator_snapshots"][filename])
                if "original_evaluator_snapshots" in record else
                receipt.parent / "sources" / "tests" / filename)
    if sha(snapshot) != record.get("original_source_sha256", record["source_sha256"])[
            "tests/" + filename]:
        raise ValueError("original evaluator snapshot has changed")
    spec = importlib.util.spec_from_file_location("cost_original_" + filename[:-3], snapshot)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_original(evidence, source_receipt, metadata, root):
    """Rebuild missing diagnostic prerequisites from bound original test sources."""
    from verify import Evidence
    source_path = project_path(source_receipt)
    record = json.loads(source_path.read_text())
    baseline = Evidence("reference-original-baseline", repair_of=str(source_path))
    evidence.record["original_baseline_child"] = baseline.relative(baseline.folder / "receipt.json")
    evidence.flush()
    try:
        baseline.record["original_source_sha256"] = record["source_sha256"]
        baseline.record["original_source_receipt_sha256"] = sha(source_path)
        baseline.record["original_evaluator_snapshots"] = {}
        for name in ("checkpoint_reference.py", "software_discrepancy.py"):
            path = source_path.parent / "sources/tests" / name
            payload = path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != record["source_sha256"]["tests/" + name]:
                raise ValueError("original evaluator source snapshot changed")
            output = baseline.folder / ("original-" + name)
            with output.open("xb") as stream:
                stream.write(payload)
            baseline.record["original_evaluator_snapshots"][name] = baseline.relative(output)
        for name in ("reference.py", "fixtures.py", "repack.py", "prompts.py"):
            if record["source_sha256"]["tests/" + name] != sha(Path("tests") / name):
                raise ValueError("original evaluator dependency changed")
        for mode, model in metadata["models"].items():
            baseline.record.setdefault("runtime_input_sha256", {}).update({
                str(root / mode.lower() / name): item["sha256"]
                for name, item in model["files"].items()})
        baseline.flush()
        receipt = baseline.folder / "receipt.json"
        integer_module = original_module(receipt, "checkpoint_reference.py")
        # Resolve the original floating evaluator's sibling import to its bound
        # original integer module while loading, not to the optimized CPP string.
        current = sys.modules["checkpoint_reference"]
        try:
            sys.modules["checkpoint_reference"] = integer_module
            float_module = original_module(receipt, "software_discrepancy.py")
        finally:
            sys.modules["checkpoint_reference"] = current
        integer = integer_module.IntegerGEMV(baseline)
        floating = float_module.FloatingGEMV(baseline)
        baseline.record["integer_qualification"] = integer_module.qualify(integer, 17)
        baseline.record["floating_qualification"] = float_module.qualify(floating, 17)
        baseline.finish("probe_passed", "Fresh original evaluator prerequisite only; "
                        "does not restore missing historical evidence or accept the product.")
        return baseline.relative(receipt)
    except Exception as exc:
        baseline.finish("probe_failed", f"{type(exc).__name__}: {exc}")
        raise


def audit_reference(evidence, receipt_path, baseline, metadata, root):
    """Bind earlier completed vectors for diagnosis, never reuse them as a pass."""
    path = project_path(receipt_path)
    record = json.loads(path.read_text())
    if record.get("outcome") != "probe_passed":
        raise ValueError("diagnostic reference producer did not complete")
    for name in ("checkpoint_reference.py", "reference.py", "fixtures.py",
                 "repack.py", "prompts.py"):
        key = "tests/" + name
        if record["source_sha256"].get(key) != baseline.get(
                "original_source_sha256", baseline["source_sha256"]).get(key):
            raise ValueError("earlier reference is not bound to the original evaluator")
    bindings = record["runtime_input_sha256"]
    for mode, model in metadata["models"].items():
        for name, item in model["files"].items():
            if bindings.get(str(root / mode.lower() / name)) != item["sha256"]:
                raise ValueError("earlier reference checkpoint differs from validated fixture")
    manifest_path = path.parent / "checkpoint-reference.json"
    if bindings.get(str(manifest_path)) != sha(manifest_path):
        raise ValueError("earlier reference manifest hash changed")
    transcript = json.loads(manifest_path.read_text())
    from software_discrepancy import validate_trajectory
    validate_trajectory(transcript)
    counts = {}
    seconds = []
    for row in transcript["rows"]:
        counts[row["mode"]] = counts.get(row["mode"], 0) + len(row["steps"])
        for step in row["steps"]:
            vector_path = project_path(step["ordered_logits"])
            payload = vector_path.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            if (len(payload) != 151936 * 4 or digest != step["logits_sha256"] or
                    bindings.get(str(vector_path)) != digest):
                raise ValueError("earlier complete reference vector binding changed")
            values = struct.unpack("<151936i", payload)
            if max(range(len(values)), key=lambda i: (values[i], -i)) != step["selected_token"]:
                raise ValueError("earlier reference selected token differs from ordered logits")
            seconds.append(step["reference_wall_seconds_not_FPGA_performance"])
    evidence.record["earlier_reference_diagnosis"] = {
        "receipt": str(path), "receipt_sha256": sha(path),
        "source_and_fixture_bindings_checked_against_original": True,
        "ordered_vectors_hash_and_argmax_checked": counts,
        "sum_recorded_token_wall_seconds": sum(seconds),
        "scope": "historical_cost_diagnosis_only_not_current_reference_reuse_or_campaign_success"}
    evidence.flush()


class RecordedGEMV:
    """Compare every transient dot result without retaining tensor dumps."""

    def __init__(self, engine):
        self.engine, self.calls = engine, []

    def evaluate(self, pointer, size, format_id, activation, outputs, group, offsets,
                 bias_format=-1):
        result = self.engine.evaluate(pointer, size, format_id, activation, outputs,
                                      group, offsets, bias_format)
        integer = isinstance(result, tuple)
        payload = struct.pack(f"<{len(activation)}{'i' if integer else 'd'}", *activation)
        if integer:
            rounded, exact = result
            payload += struct.pack(f"<{len(rounded)}i", *rounded)
            payload += b"".join(value.to_bytes(16, "little", signed=True) for value in exact)
        else:
            payload += struct.pack(f"<{len(result)}d", *result)
        self.calls.append((format_id, outputs, group, tuple(offsets), bias_format,
                           hashlib.sha256(payload).hexdigest()))
        return result


def dispatch_audit(evidence):
    rows = []
    for path in sorted(Path("tests").glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "simulate"):
                simulator = next((ast.unparse(item.value) for item in node.keywords
                                  if item.arg == "simulator"), "evidence default")
                rows.append({"file": str(path), "line": node.lineno,
                             "simulator": simulator})
    flushing = []
    for name in ("experiments.py", "compatibility.py"):
        lines = (Path("tests") / name).read_text().splitlines()
        for index, line in enumerate(lines):
            if "$fflush" in line:
                context = "\n".join(lines[max(0, index - 3):index + 1])
                if "TOKEN_COMPARED" not in context:
                    raise AssertionError("request/cycle-level flushing in integration bench")
                flushing.append({"file": "tests/" + name, "line": index + 1,
                                 "event": "completed_token"})
    evidence.record["simulator_dispatch_audit"] = {
        "call_sites": rows, "integration_flush_sites": flushing,
        "manual_trace": {
            "integration_matrix": "top_probe defaults to Verilator for every configuration/seed/mode",
            "compatibility_matrix": "both implementations explicitly select Verilator",
            "mutations": "trial.default_simulator=verilator; no interpreted functional fallback",
            "full_dimension_benchmarks": "explicit Verilator",
            "Icarus": "bounded leaves, illegal-parameter diagnostics and RESET_ONLY startup",
            "dequant_interpreted_batches": "65537/65535/6144 vectors; each below 500k cycles",
        },
        "scope": "static dispatch audit, not a new simulation result or exhaustive timing proof"}
    evidence.flush()


def worker(evidence, compare_to=None, measure_smoke=False, reference_diagnosis=None,
           original_source_receipt=None):
    dispatch_audit(evidence)
    root = project_path("fixtures/qwen2.5-0.5b")
    metadata, _ = profiled(evidence, "fixture-validation", lambda: validate(root))
    if original_source_receipt:
        compare_to = generate_original(evidence, original_source_receipt, metadata, root)
    workload = []
    for mode in ("AWQ", "BF16"):
        folder = root / mode.lower()
        tokenizer = FrozenTokenizer(json.loads((folder / "tokenizer.json").read_text()),
                                    json.loads((folder / "tokenizer_config.json").read_text()))
        for index, prompt in enumerate(PROMPTS):
            text = canonical_chat(prompt)
            tokens = tokenizer.encode(text, merge_heap)
            if tokens != tokenizer.encode(text, merge_scan):
                raise AssertionError("cost inventory tokenizers disagree")
            workload.append({"mode": mode, "prompt_index": index,
                             "prefill_tokens": len(tokens),
                             "required_reference_vectors": len(tokens) + 15,
                             "required_greedy_tokens": 16})
    evidence.record["unchanged_checkpoint_workload"] = workload
    for mode, model in metadata["models"].items():
        evidence.record.setdefault("runtime_input_sha256", {}).update({
            str(root / mode.lower() / name): item["sha256"]
            for name, item in model["files"].items()})
    integer = IntegerGEMV(evidence)
    evidence.record["integer_qualification"], _ = profiled(
        evidence, "integer-qualification", lambda: qualify(integer, 17))
    floating = FloatingGEMV(evidence)
    evidence.record["floating_qualification"], _ = profiled(
        evidence, "floating-qualification", lambda: qualify_floating(floating, 17))
    evidence.record["cache_qualification"], _ = profiled(
        evidence, "cache-qualification", lambda: qualify_caches(17))
    baseline = None
    if compare_to:
        baseline = project_path(compare_to)
        record = json.loads(baseline.read_text())
        if record.get("child_receipt"):
            baseline = project_path(record["child_receipt"])
            record = json.loads(baseline.read_text())
        evidence.record["baseline_receipt"] = str(baseline)
        evidence.record["runtime_input_sha256"][str(baseline)] = sha(baseline)
        old_integer = baseline_engine(integer, baseline, "integer-gemv.so", "gemv")
        old_float = baseline_engine(floating, baseline, "floating-gemv.so", "floating_gemv")
        original_sources = record.get("original_source_sha256", record["source_sha256"])
        for mode, model in metadata["models"].items():
            for name, item in model["files"].items():
                if record["runtime_input_sha256"].get(str(root / mode.lower() / name)) != item["sha256"]:
                    raise ValueError("original evaluator used a different checkpoint")
        for name in ("reference.py", "fixtures.py", "repack.py", "prompts.py"):
            if original_sources["tests/" + name] != sha(Path("tests") / name):
                raise ValueError("baseline numerical dependency changed")
        original_integer = original_module(baseline, "checkpoint_reference.py")
        original_float = original_module(baseline, "software_discrepancy.py")
        evidence.record["original_implementation_comparison"] = {
            "receipt": str(baseline), "fixture_bindings_checked": True,
            "snapshot_modules_checked": ["checkpoint_reference.py", "software_discrepancy.py"],
            "scope": "original Python model classes and original compiled numerical libraries"}
        if reference_diagnosis:
            audit_reference(evidence, reference_diagnosis, record, metadata, root)
    elif reference_diagnosis:
        raise ValueError("earlier reference diagnosis requires the original evaluator receipt")
    rows = []
    for mode in ("AWQ", "BF16"):
        folder = root / mode.lower()
        tokenizer = FrozenTokenizer(json.loads((folder / "tokenizer.json").read_text()),
                                    json.loads((folder / "tokenizer_config.json").read_text()))
        prefix = tokenizer.encode(canonical_chat(PROMPTS[0]), merge_heap)[:2]
        if len(prefix) != 2:
            raise AssertionError("checkpoint cost probe requires two real prompt-prefix tokens")
        new_int, new_float = RecordedGEMV(integer), RecordedGEMV(floating)
        old_int = RecordedGEMV(old_integer) if baseline else None
        old_floating_engine = RecordedGEMV(old_float) if baseline else None
        fixed_model = CheckpointModel(root, metadata["models"][mode], mode, new_int)
        float_model = FloatingModel(root, metadata["models"][mode], mode, new_float)
        old_fixed_model = (original_integer.CheckpointModel(
                           root, metadata["models"][mode], mode, old_int)
                           if baseline else None)
        old_float_model = (original_float.FloatingModel(
                           root, metadata["models"][mode], mode, old_floating_engine)
                           if baseline else None)
        try:
            for position, input_token in enumerate(prefix):
                fixed, integer_profile = profiled(
                    evidence, f"{mode.lower()}-integer-{position}",
                    lambda: fixed_model.token(input_token, position, position == 0))
                floating_values, float_profile = profiled(
                    evidence, f"{mode.lower()}-floating-{position}",
                    lambda: float_model.token(input_token, position))
                if baseline:
                    old_fixed, old_integer_profile = profiled(
                        evidence, f"{mode.lower()}-baseline-integer-{position}",
                        lambda: old_fixed_model.token(input_token, position, position == 0))
                    old_floating, old_float_profile = profiled(
                        evidence, f"{mode.lower()}-baseline-floating-{position}",
                        lambda: old_float_model.token(input_token, position))
                    if (fixed != old_fixed or fixed_model.last_writes != old_fixed_model.last_writes
                            or fixed_model.history != old_fixed_model.history or
                            struct.pack("<151936d", *floating_values) !=
                            struct.pack("<151936d", *old_floating) or
                            float_model.history != old_float_model.history or
                            new_int.calls != old_int.calls or
                            new_float.calls != old_floating_engine.calls):
                        raise AssertionError("conversion repair changed logits, scratch writes or KV")
                    if compare(fixed, floating_values) != original_float.compare(old_fixed, old_floating):
                        raise AssertionError("optimization changed software discrepancy metrics")
                    evidence.record["observations"].append({
                        "mode": mode, "position": position, "input_token": input_token,
                        "ordered_integer_and_FP64_logits_compared_each": len(fixed),
                        "scratch_writes_compared": len(fixed_model.last_writes),
                        "all_layer_KV_history_equal": True,
                        "all_ordered_GEMV_inputs_results_and_exact_accumulators_equal": True,
                        "integer_GEMV_calls_compared": len(new_int.calls),
                        "floating_GEMV_calls_compared": len(new_float.calls),
                        "baseline_integer_seconds": old_integer_profile["wall_seconds"],
                        "baseline_floating_seconds": old_float_profile["wall_seconds"],
                        "scope": "original snapshot equations and original libraries; "
                                 "memoized scalars separately qualified against uncached equations"})
                metrics, metrics_profile = profiled(
                    evidence, f"{mode.lower()}-discrepancy-{position}",
                    lambda: compare(fixed, floating_values))
                payload = struct.pack("<151936i", *fixed)
                output = evidence.folder / f"{mode.lower()}-{position}-logits.bin"

                def retain():
                    with output.open("xb") as stream:
                        stream.write(payload)
                    digest = sha(output)
                    if digest != hashlib.sha256(payload).hexdigest():
                        raise AssertionError("diagnostic logit evidence changed")
                    evidence.record["runtime_input_sha256"][evidence.relative(output)] = digest
                    evidence.flush()
                    return digest

                digest, io_profile = profiled(
                    evidence, f"{mode.lower()}-evidence-io-{position}", retain)
                # The earlier cost diagnostic used token151644 twice; only its
                # first saved fingerprint has this same prompt-prefix identity.
                if baseline and position == 0 and "cost_diagnosis" in record:
                    previous = [row for row in record["cost_diagnosis"]["rows"]
                                if row["mode"] == mode and row["position"] == position]
                    if len(previous) != 1 or previous[0]["logits_sha256"] != digest:
                        raise AssertionError("fresh logits differ from original uncached baseline")
                functions = integer_profile["functions"]
                rows.append({
                    "mode": mode, "position": position, "input_token": input_token,
                    "logits_sha256": digest,
                    "integer_token_seconds": integer_profile["wall_seconds"],
                    "floating_token_seconds": float_profile["wall_seconds"],
                    "discrepancy_metrics_seconds": metrics_profile["wall_seconds"],
                    "evidence_io_seconds": io_profile["wall_seconds"],
                    "integer_GEMV_and_conversion_seconds": sum(
                        row["cumulative_seconds"] for row in functions
                        if row["file"] == "checkpoint_reference.py" and row["function"] == "evaluate"),
                    "checkpoint_projection_sampling_self_seconds": sum(
                        row["own_seconds"] for row in functions
                        if row["file"] == "checkpoint_reference.py" and row["function"] == "projection"),
                    "python_numerical_kernel_self_seconds": sum(
                        row["own_seconds"] for row in functions if row["file"] == "reference.py"),
                    "checkpoint_coordinate_comparisons": fixed_model.sample_comparisons,
                    "metrics": metrics})
                new_int.calls.clear()
                new_float.calls.clear()
                if baseline:
                    old_int.calls.clear()
                    old_floating_engine.calls.clear()
        finally:
            fixed_model.close()
            float_model.close()
            if baseline:
                old_fixed_model.close()
                old_float_model.close()
    evidence.record["cost_diagnosis"] = {
        "scope": "two_token_cost_probe_not_full_prompt_or_RTL_acceptance",
        "profile_overhead_included": True, "rows": rows,
        "categories": "profiles retain inclusive and self times; categories are not additive"}
    evidence.flush()
    if measure_smoke:
        from software_discrepancy import prepare_and_measure
        _, profile = profiled(
            evidence, "fresh-reference-and-measure-smoke",
            lambda: prepare_and_measure(evidence, smoke=True))
        report_path = evidence.folder / "software-discrepancy.json"
        report = json.loads(report_path.read_text())
        if report["summary"]["vectors_compared"] != 2:
            raise AssertionError("measurement smoke omitted a checkpoint mode")
        for row in report["rows"]:
            step, = row["steps"]
            original, = [item for item in rows
                         if item["mode"] == row["mode"] and item["position"] == 0]
            if any(step[key] != value for key, value in original["metrics"].items()):
                raise AssertionError("streamed measurement changed complete-vector metrics")
        if list(evidence.folder.glob("*-fp64.bin")):
            raise AssertionError("measurement unnecessarily dumped transient floating vectors")
        evidence.record["measurement_streaming_diagnosis"] = {
            "wall_seconds": profile["wall_seconds"], "complete_vectors_compared": 2,
            "original_metric_comparisons_equal": True, "transient_FP64_dumps": 0,
            "report": evidence.relative(report_path)}
        evidence.flush()


def main():
    from verify import Evidence
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--repair-of", default=PREDECESSOR)
    parser.add_argument("--compare-to", help="completed project-relative pre-repair cost receipt")
    parser.add_argument("--original-source-receipt",
                        help="generate original evaluator prerequisites from bound source snapshots")
    parser.add_argument("--simulation-checks", action="store_true",
                        help="also retain compact dual-simulator and numerical-leaf checks")
    parser.add_argument("--measure-smoke", action="store_true",
                        help="also profile fresh-reference/measurement plumbing in both modes")
    parser.add_argument("--reference-diagnosis",
                        help="bind a completed original reference receipt for cost diagnosis only")
    args = parser.parse_args()
    if args.compare_to and args.original_source_receipt:
        parser.error("select an original cost receipt or original source receipt, not both")
    evidence = Evidence("reference-costs-worker" if args.worker else "reference-costs",
                        repair_of=args.repair_of)
    try:
        if args.worker:
            worker(evidence, args.compare_to, args.measure_smoke, args.reference_diagnosis,
                   args.original_source_receipt)
        else:
            options = ["--compare-to", args.compare_to] if args.compare_to else []
            if args.measure_smoke:
                options.append("--measure-smoke")
            if args.reference_diagnosis:
                options += ["--reference-diagnosis", args.reference_diagnosis]
            if args.original_source_receipt:
                options += ["--original-source-receipt", args.original_source_receipt]
            text = evidence.command(
                ["python3", "-B", "tests/reference_costs.py", "--worker",
                 "--repair-of", args.repair_of, *options], "bounded-reference-costs", timeout=3600)
            final = json.loads(text.splitlines()[-1])
            receipt = project_path(final["receipt"])
            child = json.loads(receipt.read_text())
            if child.get("outcome") != "probe_passed":
                raise AssertionError("checkpoint cost worker did not complete")
            evidence.record["child_receipt"] = str(receipt)
            evidence.record["cost_diagnosis"] = child["cost_diagnosis"]
            if args.simulation_checks:
                for label, argv in (
                    ("compact-simulator-parity",
                     ["python3", "-B", "tests/simulation_checks.py", "--compact"]),
                    ("integer-math-leaves",
                     ["python3", "-B", "tests/verify.py", "--probe", "math", "--seed", "17"]),
                    ("dequant-leaves",
                     ["python3", "-B", "tests/verify.py", "--probe", "dequant", "--seed", "17"]),
                ):
                    evidence.command(argv, label, timeout=3600)
        evidence.finish("probe_passed", "Bounded checkpoint cost diagnosis only; not acceptance.")
        print(json.dumps({"receipt": evidence.relative(evidence.folder / "receipt.json")}), flush=True)
        return 0
    except Exception as exc:
        evidence.finish("probe_failed", f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
