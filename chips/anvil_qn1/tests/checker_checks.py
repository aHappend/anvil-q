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
