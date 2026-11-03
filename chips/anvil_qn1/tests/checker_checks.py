"""Bounded negative checks for aggregation and retained-component applicability.

These are checker tests, not additional RTL mutation detections or fresh
simulations. Counterexamples are in-memory copies; retained evidence is read-only.
"""

import copy
import hashlib
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
    """Source/aggregation diagnostics plus a complete compact fusion component.

    A missing/stale fusion component executes automatically; this is not the
    complete mandatory behavior suite.
    """
    import ast
    import time
    from unittest.mock import patch
    import budget
    from benchmark_checks import (DOMAINS, benchmark_bench, compact_tokens,
                                  check_fixture_manifest)
    from behavior_suite import MODEL, validate_fusion
    from component_cache import component
    from production_checks import run_fusion_profile
    from defect_checks import MUTANTS
    from speculation_checks import replace_once
    from suite_dispatch import jobs, require_complete, tools_for

    parsed = []
    for path in sorted((ROOT / "tests").glob("*.py")):
        ast.parse(path.read_text(), filename=relative(path))
        parsed.append(relative(path))
    benchmark_bench()
    dispatch_names = [name for name, _ in jobs()]
    if len(dispatch_names) != 11 or len(set(dispatch_names)) != 11:
        raise AssertionError("default dispatch omitted/duplicated a suite")
    dispatch_rejections = [
        rejection(lambda name=name: require_complete({}, name), f"dispatch:empty-{name}")
        for name in dispatch_names
    ]
    for domain in DOMAINS:
        dispatch_rejections.append(rejection(
            lambda domain=domain: require_complete({"domain": domain}, f"benchmark-{domain}"),
            f"dispatch:single-case-is-not-suite-{domain}"))
    if any(not tools_for(name) for name in dispatch_names):
        raise AssertionError("missing per-suite prerequisite tools")
    mutation_recipes = {}
    for name, (source, kind, substitutions, diagnostics) in MUTANTS.items():
        original = (ROOT / source).read_text()
        changed = original
        for before, after in substitutions:
            changed = replace_once(changed, before, after)
        if changed == original or not diagnostics:
            raise AssertionError(f"empty mutation recipe: {name}")
        mutation_recipes[name] = {"source": source, "oracle": kind}
    fixtures = check_fixture_manifest()
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
    from concurrent.futures import ThreadPoolExecutor
    component_method = budget.Run.component
    parent = SimpleNamespace(path=run.path, hashes={}, tool_versions={}, components=[])
    child = SimpleNamespace(path=run.path / "checker-only-child", hashes={},
                            finish=lambda *args, **kwargs: "failed")
    with patch.object(budget, "Run", return_value=child):
        try:
            component_method(parent, "checker-only-child", lambda child: {})
        except budget.BudgetExceeded:
            pass
        else:
            raise AssertionError("deadline-failed child was reported as a passing component")
    if parent.components[0]["status"] != "failed":
        raise AssertionError("component status disagrees with child retention status")
    worker = budget.Run.__new__(budget.Run)
    worker.commands = []
    with patch.object(budget.BaseRun, "execute", return_value="thread-clock-checked"), \
            patch.object(budget.signal, "setitimer",
                         side_effect=AssertionError("worker altered the process alarm")):
        with ThreadPoolExecutor(max_workers=1) as executor:
            answer = executor.submit(worker.execute, ["python3", "--version"], "thread-clock").result()
        if answer != "thread-clock-checked":
            raise AssertionError("worker lost cumulative-budget execution")
    candidates = sorted((ROOT / "evidence/preparation").glob("fusion-compact-*/receipt.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    applicable = None
    fusion_assessments = []
    for path in candidates:
        assessment, result = assess(
            run, path, (*MODEL, "tests/production_checks.py"),
            {"profile": 1, "compact_diagnostic": True}, TOOLS)
        fusion_assessments.append(assessment)
        if assessment["applicable"]:
            validate_fusion(result, 1)
            applicable = assessment
            break
    (run.path / "fusion-applicability.json").write_text(
        json.dumps(fusion_assessments, indent=2) + "\n")
    if applicable is None:
        result = component(
            run, "fusion-compact", lambda child: run_fusion_profile(child, 1, compact=True),
            inputs=(*MODEL, "tests/production_checks.py"),
            parameters={"profile": 1, "compact_diagnostic": True}, tools=TOOLS,
            validate=lambda value: validate_fusion(value, 1))
        applicable = run.components[-1]
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
    return {"scope": "source/checker diagnostics and compact fusion component, not full behavior",
            "parsed_sources": parsed, "fixtures": fixtures,
            "default_dispatch": dispatch_names, "mutation_recipes": mutation_recipes,
            "dispatch_counterexamples": dispatch_rejections,
            "fixture_manifest_sha256": hashlib.sha256(json.dumps(
                fixtures, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "compact_profile1_applicability": applicable,
            "compact_profile1_counts": {
                name: result[name] for name in ("extra_cycles", "compact_diagnostic", "profile")},
            "rejected_counterexamples": rejected, "cumulative_budget_properties": 6}
