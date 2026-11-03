"""Bounded negative checks for aggregation and retained-component applicability.

These are checker tests, not additional RTL mutation detections or fresh
simulations. Counterexamples are in-memory copies; retained evidence is read-only.
"""

import copy
import json
from types import SimpleNamespace

from behavior_suite import (
    SPECULATION, TOOLS, run_behavior_components, validate_controller,
    validate_core, validate_faults, validate_memory, validate_speculative_cancels,
    validate_telemetry,
)
from component_cache import assess
from execution import ROOT, relative
from production_checks import measured_fusion_delta


def rejection(operation, label):
    try:
        operation()
    except AssertionError:
        return label
    raise AssertionError(f"checker accepted deliberately incomplete case: {label}")


def run_behavior_checker(run):
    complete = run_behavior_components(run)["components"]
    rejected = []
    for stem, validate in (
            ("behavior-core", validate_core), ("memory-matrix", validate_memory),
            ("fault-matrix", validate_faults),
            ("speculative-cancel", validate_speculative_cancels)):
        result = complete[stem]
        validate(result)
        for index in range(len(result["cases"])):
            broken = copy.deepcopy(result)
            del broken["cases"][index]
            rejected.append(rejection(lambda: validate(broken), f"{stem}:missing-case-{index}"))
    controller = copy.deepcopy(complete["controller"])
    for index in range(len(controller["coverage_names"])):
        broken = copy.deepcopy(controller)
        del broken["coverage_names"][index]
        rejected.append(rejection(lambda: validate_controller(broken),
                                  f"controller:missing-case-{index}"))
    for index in range(len(complete["integrated-csr"]["counts"])):
        broken = copy.deepcopy(complete["integrated-csr"])
        broken["counts"][index] += 1
        rejected.append(rejection(lambda: validate_telemetry(broken),
                                  f"telemetry:corrupt-count-{index}"))

    core = next(c for c in run.components if c["receipt"].split("/")[-2].startswith(
        ("behavior-core-", "l1-behavior-core-")))
    receipt = ROOT / core["receipt"]
    inputs = (*SPECULATION, "tests/behavior_checks.py")
    good, _ = assess(run, receipt, inputs, {}, TOOLS)
    if not good["applicable"]:
        raise AssertionError("known complete behavior component became inapplicable")
    for name in ("tests/model.py", "rtl/anvil_qn1_top.sv"):
        for missing in (False, True):
            hashes = dict(run.hashes)
            if missing:
                del hashes[name]
            else:
                hashes[name] = "0" * 64
            changed, _ = assess(SimpleNamespace(hashes=hashes, tool_versions=run.tool_versions),
                                receipt, inputs, {}, TOOLS)
            if changed["applicable"]:
                raise AssertionError(f"component accepted stale/missing source {name}")
            rejected.append(f"cache:{'missing' if missing else 'stale'}:{name}")
    for tool in TOOLS:
        versions = dict(run.tool_versions)
        versions[tool] += "\nDELIBERATE_TOOL_CHANGE"
        changed, _ = assess(SimpleNamespace(hashes=run.hashes, tool_versions=versions),
                            receipt, inputs, {}, TOOLS)
        if changed["applicable"]:
            raise AssertionError(f"component accepted changed {tool}")
        rejected.append(f"cache:changed-tool:{tool}")
    changed, _ = assess(run, receipt, inputs, {"case_count": 16}, TOOLS)
    if changed["applicable"]:
        raise AssertionError("component accepted changed parameter/coverage identity")
    rejected.append("cache:changed-case-count")

    measured = []
    candidates = sorted((ROOT / "evidence/preparation").glob("fusion-compact-*/receipt.json"))
    for path in candidates:
        receipt_data = json.loads(path.read_text())
        result = receipt_data.get("results")
        if (receipt_data.get("status") != "passed" or not isinstance(result, dict) or
                not all(name in result for name in ("fused", "without_norm"))):
            continue
        # This validates the stricter checker against recorded measurements only.
        # It deliberately does not admit those old sources as a current execution.
        fused, baseline = result["fused"], result["without_norm"]
        difference = measured_fusion_delta(fused, baseline)
        measured.append({"receipt": relative(path), "extra_cycles": difference,
                         "fused_cycles": fused["cycles"],
                         "without_norm_cycles": baseline["cycles"]})
    for compact in (False, True):
        baseline = {"cycles": 10000, "requests": 123, "normalization": False,
                    "compact_diagnostic": compact}
        fused = {**baseline, "normalization": True}
        for cycles, accepted in ((10199, True), (10200, False), (10201, False)):
            fused["cycles"] = cycles
            if accepted:
                if measured_fusion_delta(fused, baseline) != 199:
                    raise AssertionError("strict fusion integer comparison changed")
            else:
                rejected.append(rejection(
                    lambda: measured_fusion_delta(fused, baseline),
                    f"fusion:{'compact' if compact else 'production'}:{cycles}"))
        for field in ("requests", "normalization", "simulation_threads"):
            broken = {**fused, "cycles": 10000, field: -1}
            rejected.append(rejection(lambda: measured_fusion_delta(broken, baseline),
                                      f"fusion:changed-{field}:{compact}"))
    return {"scope": "checker-only negative tests; not RTL defect sensitivity or suite acceptance",
            "rejected_counterexamples": rejected, "rejected_count": len(rejected),
            "historical_measurement_rechecks": measured,
            "protocol_components": sorted(complete)}


def run_delivery_checker(run):
    """Source/aggregation diagnostics, not simulation or mandatory-suite closure."""
    import ast
    import time
    from unittest.mock import patch
    import budget
    from benchmark_checks import DOMAINS, benchmark_bench, compact_tokens, fixture_manifest
    from behavior_suite import MODEL, validate_fusion

    parsed = []
    for path in sorted((ROOT / "tests").glob("*.py")):
        ast.parse(path.read_text(), filename=relative(path))
        parsed.append(relative(path))
    benchmark_bench()
    fixtures = {domain: fixture_manifest(domain) for domain in DOMAINS}
    for domain, records in fixtures.items():
        if (len(records) != 4 or len({r["id"] for r in records}) != 4 or
                len({tuple(compact_tokens(r["description"])) for r in records}) != 4):
            raise AssertionError(f"missing distinct domain fixtures/token prompts: {domain}")
        for record in records:
            if len(record["sha256"]) != 64 or not record["attribution"]["license"]:
                raise AssertionError("missing fixture hash/license attribution")
    now = time.monotonic()
    with patch.object(budget, "START", now - 100), patch.object(budget.time, "monotonic",
                                                             return_value=now):
        if budget.remaining() != 2550 or budget.remaining(retention=True) != 2600:
            raise AssertionError("whole-check clock lost preparation/retention time")
    with patch.object(budget, "START", now - 2701), patch.object(budget.time, "monotonic",
                                                              return_value=now):
        if budget.remaining() != 0 or budget.remaining(retention=True) != 0:
            raise AssertionError("whole-check deadline renewed")
        try:
            budget.Run("must-not-create-output")
        except budget.BudgetExceeded:
            pass
        else:
            raise AssertionError("expired check created another child/output")
    candidates = sorted((ROOT / "evidence/preparation").glob("fusion-compact-*/receipt.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    applicable = None
    for path in candidates:
        assessment, result = assess(
            run, path, (*MODEL, "tests/production_checks.py"),
            {"profile": 1, "compact_diagnostic": True}, TOOLS)
        if assessment["applicable"]:
            validate_fusion(result, 1)
            applicable = assessment
            break
    if applicable is None:
        raise AssertionError("no compatible complete compact profile-1 receipt")
    rejected = []
    for field in ("cycles", "requests", "compared_writes", "key_writes", "value_writes"):
        broken = copy.deepcopy(result)
        broken["fused"][field] = 0
        rejected.append(rejection(lambda: validate_fusion(broken, 1), f"fusion:zero-{field}"))
    for record in ("fused", "without_norm"):
        for field in ("profile", "geometry", "normalization", "compact_diagnostic", "parameters"):
            broken = copy.deepcopy(result)
            broken[record][field] = None
            rejected.append(rejection(lambda: validate_fusion(broken, 1),
                                      f"fusion:{record}:changed-{field}"))
    broken = copy.deepcopy(result)
    broken["fused"]["cycles"] = broken["without_norm"]["cycles"] * 2
    broken["extra_cycles"] = broken["fused"]["cycles"] - broken["without_norm"]["cycles"]
    rejected.append(rejection(lambda: validate_fusion(broken, 1), "fusion:overhead"))
    rejected.append(rejection(lambda: validate_fusion(result, 2), "fusion:wrong-profile-cache"))
    return {"scope": "source/checker/applicability diagnostics only",
            "parsed_sources": parsed, "fixtures": fixtures,
            "compact_profile1_applicability": applicable,
            "compact_profile1_counts": {
                name: result[name] for name in ("extra_cycles", "compact_diagnostic", "profile")},
            "rejected_counterexamples": rejected, "cumulative_budget_properties": 4}
