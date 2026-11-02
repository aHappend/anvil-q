"""Bounded diagnostics for concurrent receipt allocation and nested budgets."""

from concurrent.futures import ThreadPoolExecutor
import json

from execution import ROOT, relative
import integration


def check(evidence, seed):
    evidence.run(["python3", "-m", "py_compile",
                  *[relative(path) for path in sorted((ROOT / "tests").glob("*.py"))]])
    commands = [["python3", "-c", f"print('{label}')"] for label in ("FIRST", "SECOND")]
    with ThreadPoolExecutor(max_workers=2) as executor:
        outputs = list(executor.map(evidence.run, commands))
    if len(set(outputs)) != 2 or [path.read_text().strip() for path in outputs] != ["FIRST", "SECOND"]:
        raise AssertionError("Concurrent commands lost/collided stdout records")
    deadline = evidence.deadline
    child = evidence.run(["python3", "-c",
                          "import os,sys;sys.path.insert(0,'tests');"
                          "from execution import Evidence,relative,DEADLINE_ENV;"
                          "e=Evidence('nested-budget',preparation=True);"
                          "assert e.deadline==float(os.environ[DEADLINE_ENV]);"
                          "e.finish('passed',inherited_deadline=e.deadline);"
                          "print(relative(e.path/'receipt.json'))"])
    receipt_path = ROOT / child.read_text().strip()
    receipt = json.loads(receipt_path.read_text())
    if receipt["inherited_deadline"] != deadline:
        raise AssertionError("Nested fixture generation reset the whole-check budget")
    scopes = [evidence.scope(name) for name in ("reuse-first", "reuse-second")]
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda scope: integration.smoke(scope, seed), scopes))
    if results[0]["stdout"] != results[1]["stdout"] or results[0]["logits"] != 3:
        raise AssertionError("Identical current-invocation fixture was not checked/reused exactly")
    return {"concurrent_distinct_command_logs": [relative(path) for path in outputs],
            "nested_budget_receipt": relative(receipt_path),
            "shared_checked_fixture_stdout": results[0]["stdout"], "compared_logits": 3}
