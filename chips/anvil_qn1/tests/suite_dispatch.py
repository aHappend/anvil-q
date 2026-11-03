"""Default dispatch of every admitted L1 suite under the same cumulative budget.

An exact-source complete suite may be reused after recursive source/tool/command
and artifact checks. Missing/stale work executes, never becomes a skip or pass.
The no-argument aggregate has the same 2700-second budget: a cold campaign that
does not fit fails explicitly and retains its completed children.
"""

import hashlib
import json
from pathlib import Path

from benchmark_checks import DOMAINS, run_benchmark
from behavior_suite import run_behavior
from component_cache import component
from defect_checks import run_defects
from execution import ROOT
from numerical_checks import run_numerical
from reproduction_checks import run_reproduce
from smoke_checks import run_smoke
from synthesis_checks import run_synthesis


def jobs():
    return [
        ("smoke", run_smoke), ("numerical", run_numerical), ("behavior", run_behavior),
        *[(f"benchmark-{domain}", lambda run, domain=domain: run_benchmark(run, domain))
          for domain in DOMAINS],
        ("defects", run_defects), ("synthesis", run_synthesis), ("reproduce", run_reproduce),
    ]


def require_complete(result):
    if not isinstance(result, dict) or not result:
        raise AssertionError("missing complete suite results")


def retained_artifacts(run, entry):
    """Keep raw/netlist evidence obligations when reusing an entire suite."""
    path = ROOT / entry["receipt"]
    receipt = json.loads(path.read_text())
    for name, digest in receipt.get("artifact_sha256", {}).items():
        item = Path(name)
        if item.is_absolute() or ".." in item.parts:
            raise AssertionError("nonportable suite artifact")
        # Object files are intentionally reclaimed, not comparison evidence.
        if any(part.startswith("obj-") for part in item.parts):
            continue
        artifact = path.parent / item
        if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != digest:
            raise AssertionError(f"missing/changed suite artifact: {entry['receipt']}:{name}")


def run_all(run):
    results = {}
    for name, operation in jobs():
        results[name] = component(
            run, name, operation,
            inputs=("tests/*.py", "anvil_q3_reference/rtl/*.sv"),
            parameters={}, tools=tuple(run.tool_versions), validate=require_complete)
        if run.components[-1].get("reused"):
            retained_artifacts(run, run.components[-1])
    if set(results) != {name for name, _ in jobs()} or len(results) != 11:
        raise AssertionError("default dispatch omitted a mandatory L1 suite/domain")
    return {"scope": "all mandatory L1 suites; compact regulation, not physical signoff",
            "suites": results, "suite_count": len(results)}
