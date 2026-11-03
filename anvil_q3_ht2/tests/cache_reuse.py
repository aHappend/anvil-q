"""Bounded real-tool regression of compilation reuse, never of simulation results."""

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from arithmetic import run_arithmetic
from integrated_fast import run_fast_integration
from kv_atomic import run_atomic
from receipts import new_run, relative
import receipts
from verify import enter_tier


def check_binding_contract(run, binding_path):
    """Negative cache checks use disposable metadata, not changed DUT sources."""
    binding_path = receipts.ROOT / binding_path
    binding = json.loads(binding_path.read_text())
    identity = receipts.compilation_identity(binding["identity"])
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    # Use the actual cold binding, since process/retained bindings point to it.
    while binding["reused"]:
        if "retained_binding" in binding:
            binding_path = receipts.ROOT / binding["retained_binding"]
        else:
            raise AssertionError("expected retained arithmetic build provenance")
        binding = json.loads(binding_path.read_text())
    with patch.object(receipts, "retained_models",
                      return_value={key: [(binding_path, binding)]}):
        if receipts.retained_model(key, identity) is None:
            raise AssertionError("unchanged build rejected")
    comparisons = 1
    for field in ("argv", "tools", "environment_sha256", "source_sha256"):
        changed = copy.deepcopy(identity)
        if field == "argv":
            changed[field] = [*changed[field], "-DHT2_CHANGED_CONFIGURATION"]
        elif field == "environment_sha256":
            changed[field] = "changed-environment"
        elif field == "tools":
            changed[field]["verilator_bin"]["binary_sha256"] = "changed-compiler"
        else:
            name = next(name for name in changed[field] if name.startswith("rtl/"))
            changed[field][name] = "changed-rtl"
        changed_key = hashlib.sha256(json.dumps(changed, sort_keys=True).encode()).hexdigest()
        with patch.object(receipts, "retained_models",
                          return_value={key: [(binding_path, binding)]}):
            if receipts.retained_model(changed_key, changed) is not None:
                raise AssertionError(f"changed {field} reused an old build")
        comparisons += 1
    for field, value in (("executable", relative(run / "absent-executable")),
                         ("executable_sha256", "changed-binary")):
        stale = {**binding, field: value}
        with patch.object(receipts, "retained_models",
                          return_value={key: [(binding_path, stale)]}):
            if receipts.retained_model(key, identity) is not None:
                raise AssertionError(f"stale {field} reused an old build")
        comparisons += 1
    return {"comparisons": comparisons, "binding": relative(binding_path),
            "scope": "build-cache contract only, not RTL coverage"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integration-path", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    enter_tier()
    run = new_run("compiled-reuse", preparation=True, repair_of=args.repair_of)
    results = []
    cases = (
            ("arithmetic-seed17", run_arithmetic, ("verilator", 17, True), {}, False),
            ("arithmetic-seed29", run_arithmetic, ("verilator", 29, True), {}, True),
            ("arithmetic-mutant", run_arithmetic, ("verilator", 17, True),
             {"mutant": True}, False),
            ("atomic-mode1-seed17", run_atomic, (1, 17), {}, False),
            ("atomic-mode1-seed29", run_atomic, (1, 29), {}, True),
            ("atomic-mode2-seed17", run_atomic, (2, 17), {}, False))
    if args.integration_path:
        cases = tuple(
            (f"integration-path-seed{seed}", run_fast_integration, (1, seed),
             {"diagnostic": True, "diagnostic_cycles": 64}, index != 0)
            for index, seed in enumerate((17, 29)))
    for name, function, arguments, kwargs, reused in cases:
        from time import time_ns
        case = run / f"{name}-{time_ns()}"
        case.mkdir()
        observed = function(case, *arguments, **kwargs)
        bindings = list(case.glob("*-binding-*.json"))
        if len(bindings) != 1:
            raise AssertionError("each experiment must have exactly one build binding")
        binding = json.loads(bindings[0].read_text())
        if reused and binding["reuse_origin"] != "process":
            raise AssertionError(f"unexpected compile reuse for {name}")
        if not reused and binding["reuse_origin"] not in ("cold", "retained"):
            raise AssertionError(f"unexpected initial build origin for {name}")
        results.append({"name": name, "binding": relative(bindings[0]), "result": observed})
    if args.integration_path:
        if results[0]["result"]["model_sha256"] == results[1]["result"]["model_sha256"]:
            raise AssertionError("fresh integration seed did not change model bytes")
        if any(not item["result"]["diagnostic_only"] for item in results):
            raise AssertionError("cache-path experiment must remain diagnostic-only")
    elif results[0]["result"]["vector_sha256"] == results[1]["result"]["vector_sha256"]:
        raise AssertionError("arithmetic seed change did not generate fresh vectors")
    if not args.integration_path and (
            results[3]["result"]["record_sha256"] == results[4]["result"]["record_sha256"]):
        raise AssertionError("atomic seed change did not generate fresh records")
    if not args.integration_path and (
            results[0]["result"]["vector_sha256"] != results[2]["result"]["vector_sha256"]):
        raise AssertionError("mutant and unmodified arithmetic vectors differ")
    contract = check_binding_contract(run, results[0]["binding"])
    summary = run / "cache-reuse-summary.json"
    summary.write_text(json.dumps({"cases": results, "binding_contract": contract,
                                  "status": "passed"}, indent=2) + "\n")
    print(json.dumps({"summary": relative(summary), "status": "passed"}), flush=True)


if __name__ == "__main__":
    main()
