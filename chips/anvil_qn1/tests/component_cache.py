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
            validate(results)
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
