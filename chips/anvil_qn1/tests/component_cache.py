"""Explicit source/tool/parameter applicability for completed component results.

Only complete, source-bound comparisons are reused. Missing/stale work executes
normally. Reused receipts are never edited; each new parent records why unrelated
source changes do not affect that component.
"""

import hashlib
import json
from pathlib import Path

from execution import ROOT, relative


COMMON = ("rtl/*.sv", "design/SPEC.md", "design/ARCHITECTURE.md", "README.md",
          "tests/execution.py")


def assess(run, path, inputs, parameters, tools):
    receipt = json.loads(path.read_text())
    reasons = []
    if receipt.get("status") != "passed":
        reasons.append("component did not pass")
    selected = {relative(p) for pattern in (*COMMON, *inputs) for p in ROOT.glob(pattern)}
    for pattern in (*COMMON, *inputs):
        if not any(ROOT.glob(pattern)):
            reasons.append(f"missing declared dependency {pattern}")
    recorded = receipt.get("source_sha256", {})
    changed = {name: {"recorded": recorded.get(name), "current": run.hashes.get(name)}
               for name in set(recorded) | set(run.hashes)
               if recorded.get(name) != run.hashes.get(name)}
    if selected & changed.keys():
        reasons.append("changed component dependencies: " +
                       ",".join(sorted(selected & changed.keys())))
    for tool in tools:
        old = receipt.get("tool_versions", {}).get(tool)
        new = getattr(run, "tool_versions", {}).get(tool)
        if old is None or old != new:
            reasons.append(f"missing/different tool version {tool}")
    results = receipt.get("results")
    if not isinstance(results, dict):
        reasons.append("component results are not structured")
        results = {}
    for name, value in parameters.items():
        if results.get(name) != value:
            reasons.append(f"parameter/result identity mismatch: {name}")
    commands = receipt.get("commands", [])
    work = [c for c in commands if not Path(c.get("stdout", "")).name.startswith("version-")]
    if not work:
        reasons.append("no executed component tools")
    for command in commands:
        if (command.get("exit_code") != 0 or command.get("disposition") != "exited" or
                not command.get("child_settled")):
            reasons.append("unsuccessful/unsettled component command")
        for field in ("stdout", "stderr"):
            name = Path(command.get(field, ""))
            if name.is_absolute() or ".." in name.parts:
                reasons.append("nonportable command artifact")
                continue
            artifact = ROOT / name
            try:
                key = artifact.relative_to(path.parent).as_posix()
            except ValueError:
                reasons.append("command artifact outside its run")
                continue
            digest = receipt.get("artifact_sha256", {}).get(key)
            if not artifact.is_file() or digest is None:
                reasons.append(f"missing retained {field}")
            elif hashlib.sha256(artifact.read_bytes()).hexdigest() != digest:
                reasons.append(f"changed retained {field}")
    return {"receipt": relative(path), "applicable": not reasons,
            "reasons": reasons, "declared_dependencies": sorted(selected),
            "parameters": parameters, "tools": list(tools),
            "changed_unrelated_sources": {
                name: value for name, value in sorted(changed.items()) if name not in selected},
            "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}, results


def component(run, stem, operation, *, inputs, parameters, tools, validate):
    candidates = []
    for parent in (ROOT / "evidence/preparation", ROOT / "evidence"):
        if parent.is_dir():
            candidates.extend(parent.glob(f"{stem}-*/receipt.json"))
            candidates.extend(parent.glob(f"l1-{stem}-*/receipt.json"))
    assessments = []
    for path in sorted(set(candidates), key=lambda p: p.stat().st_mtime, reverse=True):
        assessment, results = assess(run, path, inputs, parameters, tools)
        assessments.append(assessment)
        if assessment["applicable"]:
            try:
                validate(results)
            except AssertionError as error:
                assessment["applicable"] = False
                assessment["reasons"].append(f"retained comparison/artifact invalid: {error}")
                print(f"COMPONENT_STALE {relative(path)}: {error}", flush=True)
            else:
                run.components.append({"receipt": relative(path), "status": "passed",
                                       "reused": True, "applicability": assessment})
                return results
    result = run.component(stem, operation)
    validate(result)
    run.components[-1]["reused"] = False
    run.components[-1]["prior_applicability"] = assessments
    return result


def long_context(run):
    from context_checks import run_context

    def validate(result):
        if result.get("counts", [])[:5] != [40960, 31, 15728640, 81920, 128]:
            raise AssertionError("incomplete 40960-position attention comparisons")
        if len(result.get("context", [])) != 128:
            raise AssertionError("missing context coordinates")

    return component(
        run, "attention-context", lambda child: run_context(child),
        inputs=("tests/reference.py", "tests/context_checks.py"),
        parameters={"positions": 40960, "head": 31, "q_heads": 32, "kv_heads": 8,
                    "head_dimension": 128, "driver": "cpp"},
        tools=("python3", "verilator", "g++", "make"), validate=validate)


def historical_applicability(run):
    from synthesis_checks import run_synthesis_case

    context = long_context(run)
    parameters = {
        "PROFILE": 3, "BANKS": 8, "QUEUE_DEPTH": 16, "COMPACT": 1,
        "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 4, "NUM_KV_HEADS": 1, "HEAD_DIM": 128,
        "VOCAB_SIZE": 8, "MAX_SEQ_LEN": 16, "GROUP_SIZE": 8}

    def validate(result):
        if result.get("top_scheduler_combinational_scc") != 0:
            raise AssertionError("missing cross-boundary zero-SCC assertion")
        for stage in ("hierarchy", "synthesis"):
            record = result[stage]
            if (record["dynamic_lanes"] != 256 or not record["state_cells"] or
                    any(record[name] != 0 for name in
                        ("latches", "combinational_div_mod", "unresolved_blackboxes"))):
                raise AssertionError("missing live-lane/state/no-latch synthesis comparisons")
        for name in ("hierarchy_netlist", "synthesized_netlist"):
            record = result[name]
            path = Path(record["file"])
            if path.is_absolute() or ".." in path.parts:
                raise AssertionError("nonportable retained synthesis netlist")
            file = ROOT / path
            if (not file.is_file() or
                    hashlib.sha256(file.read_bytes()).hexdigest() != record["compressed_sha256"]):
                raise AssertionError("missing/changed retained synthesis netlist")

    synthesis = component(
        run, "synthesis-boundary",
        lambda child: run_synthesis_case(child, compact=True, banks=8, queue=16,
                                         head_dim=128, q_heads=4),
        inputs=("tests/synthesis_checks.py",),
        parameters={"parameters": parameters, "production": False},
        tools=("python3", "yosys"), validate=validate)
    return {"attention_positions": context["positions"],
            "attention_reads": context["counts"][2],
            "synthesis_parameters": synthesis["parameters"],
            "scope": "explicit historical component applicability, not whole-product acceptance"}
