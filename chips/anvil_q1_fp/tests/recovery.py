"""Bounded recovery diagnostics; retained evidence never becomes a runtime pass."""

import json
from pathlib import Path
import shutil

from architecture import CONFIGURATIONS
from benchmark import sha


def facilities(root, ev, python_facilities=()):
    names = ("python3", "python", "iverilog", "vvp", "yosys", "verilator",
             "quartus_sh", "vulcan", "docker", "podman", "bwrap", "firejail")
    tools = {name: shutil.which(name) for name in names}
    ev.receipt["facility_discovery"] = tools
    interpreters = sorted(
        {str(Path(path).absolute()) for name, path in tools.items()
         if name in ("python3", "python") and path} |
        {str(path.absolute()) for path in python_facilities})
    script = (
        "import importlib.util,json,sys; print(json.dumps({'version':sys.version,"
        "'dependencies':{name:importlib.util.find_spec(name) is not None for name in "
        "('numpy','torch','transformers','tokenizers','safetensors','datasets','mpmath')}}))")
    ok = True
    for index, interpreter in enumerate(interpreters):
        ok = ev.run(f"existing-python-{index}", [interpreter, "-c", script], timeout=30) and ok
    for name in ("quartus_sh", "docker", "bwrap"):
        if tools[name]:
            observed = ev.run("existing-version-" + name, [tools[name], "--version"], timeout=30)
            ok = ev.assertion("facility_version_" + name, observed) and ok
    ev.receipt["facility_scope"] = (
        "Existing PATH tools and explicitly supplied authorized Python interpreters only; no installation, "
        "container launch, network request, other account/session search or hardware execution")
    required = ("model_manifest.json", "benchmark_manifest.json", "full_model_results.json")
    ev.receipt["missing_inputs"] = [
        "tests/data/" + name for name in required if not (root / "tests/data" / name).is_file()]
    ev.receipt["unestablished_facilities"] = [
        "Authorized complete checkpoint/derived native and AWQ streams and pinned corpus",
        "Independent production FP64 inference implementation with dependencies",
        "Suitably isolated HumanEval evaluator with case-bound execution evidence",
        "Source/data-bound hardware bridge, accepted bitstream and physical benchmark adapter",
    ]
    return ev.assertion("existing_facility_inventory_completed", ok,
                        scope="Discovery is not prerequisite satisfaction")


def reconcile_integration(root, ev, interrupted, accelerated):
    original = json.loads(interrupted.read_text())
    retained = json.loads(accelerated.read_text())
    ev.receipt["reconciled_with"] = dict(path=str(accelerated.relative_to(root)),
                                        sha256=sha(accelerated))
    dependencies = [*root.glob("rtl/*.sv"), *root.glob("anvil_q1_reference/rtl/*.sv")]
    dependencies += [root / "tests" / name for name in
                     ("integration_tb.sv", "architecture.py", "numerical.py")]
    for path in dependencies:
        name = str(path.relative_to(root))
        # Only reuse the completed accelerated run. The interrupted run may
        # predate transactor/oracle repairs and is retained, not certified.
        inputs = (original, retained) if path.suffix == ".sv" and "tests" not in path.parts else (retained,)
        if any(data["source_sha256"].get(name) != sha(path) for data in inputs):
            return ev.assertion("reconciliation_input_binding", False, changed=name)
    records = {item["label"]: item for item in retained["records"]}
    assertions = {item["name"]: item for item in retained["assertions"]}
    failures, covered = [], []
    for name in CONFIGURATIONS:
        for mode in (0, 1, 2):
            for seed in (17, 53, 89):
                label = f"{name}-mode{mode}-seed{seed}"
                for suffix in (("-revised", "-parent") if mode == 0 else ("-revised",)):
                    record = records.get(label + suffix, {})
                    if record.get("exit_code") != 0 or record.get("timed_out", True):
                        failures.append(label + suffix + ": incomplete execution")
                    for key in ("stdout", "stderr"):
                        path = root / record.get(key, "missing-raw-log")
                        if not path.is_file():
                            failures.append(label + suffix + ": missing " + key)
                        else:
                            ev.receipt.setdefault("reused_raw_sha256", {})[
                                str(path.relative_to(root))] = sha(path)
                assertion = assertions.get(label + "_independent_architecture_numerical", {})
                path = root / assertion.get("report", "missing-report")
                if not assertion.get("passed") or not path.is_file():
                    failures.append(label + ": missing successful comparisons")
                else:
                    report = json.loads(path.read_text())
                    if (not report.get("passed") or report.get("events_compared", 0) <= 0 or
                            (mode != 0 and not report.get("groups")) or not all(
                            item["passed"] and item["comparisons"] > 0
                            for item in report["groups"].values())):
                        failures.append(label + ": incomplete numerical report")
                    ev.receipt.setdefault("reused_reports", {})[
                        str(path.relative_to(root))] = sha(path)
                if mode == 0 and not assertions.get(
                        label + "_parent_differential", {}).get("passed"):
                    failures.append(label + ": missing compatibility differential")
                covered.append(label)
    unresolved = [record["label"] for record in original["records"]
                  if "exit_code" not in record]
    ev.receipt["interrupted_test_source_differences"] = {
        name: dict(interrupted=hashed, current=sha(root / name))
        for name, hashed in original["source_sha256"].items()
        if name.startswith("tests/") and (root / name).is_file() and
        sha(root / name) != hashed}
    return ev.assertion("interrupted_matrix_reconciled_by_existing_execution",
                        not failures, failures=failures, covered=covered,
                        interrupted_children_still_incomplete=unresolved,
                        scope="Verilator full matrix already executed; original Icarus "
                              "children remain incomplete, not passes or timeouts. "
                              "No replacement of admitted checks.")
