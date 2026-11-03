"""Explicit source/tool/parameter applicability for completed component results.

Only complete, source-bound comparisons are reused. Missing/stale work executes
normally. Reused receipts are never edited; each new parent records why unrelated
source changes do not affect that component.
"""

import ast
import hashlib
import json
from pathlib import Path

from execution import ROOT, relative


COMMON = ("rtl/*.sv", "design/SPEC.md", "design/ARCHITECTURE.md", "README.md",
          "tests/execution.py")


def artifact_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for data in iter(lambda: file.read(1048576), b""):
            digest.update(data)
    return digest.hexdigest()


def assess(run, path, inputs, parameters, tools, ancestors=(), equivalence=None):
    path = Path(path).resolve()
    if path in ancestors or len(ancestors) >= 32:
        raise ValueError(f"cyclic/excessively nested component receipt: {relative(path)}")
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
    equivalent = {}
    if equivalence is not None:
        for name in sorted(selected & changed.keys()):
            record = equivalence(run, path, receipt, name)
            if record is not None:
                equivalent[name] = record
    missing = {name for name in selected if
               name not in recorded or name not in run.hashes}
    if missing:
        reasons.append("missing component source bindings: " + ",".join(sorted(missing)))
    changed_dependencies = (selected & changed.keys()) - equivalent.keys()
    if changed_dependencies:
        reasons.append("changed component dependencies: " +
                       ",".join(sorted(changed_dependencies)))
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
    for command in commands:
        if (command.get("exit_code") != command.get("expected_exit", 0) or
                command.get("disposition") != "exited" or
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
    for name, digest in receipt.get("artifact_sha256", {}).items():
        item = Path(name)
        if item.is_absolute() or ".." in item.parts:
            reasons.append("nonportable retained component artifact")
            continue
        if any(part.startswith("obj-") for part in item.parts):
            continue
        artifact = path.parent / item
        if not artifact.is_file() or artifact_digest(artifact) != digest:
            reasons.append(f"missing/changed retained component artifact {name}")
    children = []
    for child in receipt.get("components", []):
        name = Path(child.get("receipt", ""))
        if (name.is_absolute() or ".." in name.parts or
                not name.parts or name.parts[0] != "evidence"):
            reasons.append("nonportable/out-of-scope child component receipt")
            continue
        child_path = ROOT / name
        if child.get("status") != "passed" or not child_path.is_file():
            reasons.append(f"failed/missing child component {name.as_posix()}")
            continue
        assessment, _ = assess(run, child_path, inputs, {}, tools, (*ancestors, path),
                               equivalence=equivalence)
        children.append(assessment)
        if not assessment["applicable"]:
            reasons.append(f"inapplicable child component {name.as_posix()}")
    executed = len(work) + sum(child["executed_work_commands"] for child in children)
    if not executed:
        reasons.append("no executed component tools, including descendants")
    return {"receipt": relative(path), "applicable": not reasons,
            "reasons": reasons, "declared_dependencies": sorted(selected),
            "parameters": parameters, "tools": list(tools),
            "executed_work_commands": executed, "children": children,
            "equivalent_sources": equivalent,
            "changed_unrelated_sources": {
                name: value for name, value in sorted(changed.items()) if name not in selected},
            "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}, results


def saved_behavior_applicability(run):
    """Assess existing behavior evidence without treating partial coverage as closure."""
    groups = {
        "behavior-core": ("tests/behavior_checks.py", "tests/speculation_checks.py",
                          "tests/integration.py", "tests/model.py", "tests/reference.py"),
        "memory-matrix": ("tests/memory_checks.py", "tests/integration.py",
                          "tests/model.py", "tests/reference.py"),
        "fault-matrix": ("tests/fault_checks.py", "tests/memory_checks.py",
                         "tests/speculation_checks.py", "tests/integration.py",
                         "tests/model.py", "tests/reference.py"),
        "speculative-cancel": ("tests/speculative_fault_checks.py",
                               "tests/speculation_checks.py", "tests/integration.py",
                               "tests/model.py", "tests/reference.py"),
        "integrated-csr": ("tests/telemetry_checks.py", "tests/speculation_checks.py",
                           "tests/integration.py", "tests/model.py", "tests/reference.py"),
        "parent-reference": ("anvil_q3_reference/rtl/*.sv", "tests/parent_checks.py"),
    }
    results = {}
    for stem, inputs in groups.items():
        candidates = []
        for parent in (ROOT / "evidence/preparation", ROOT / "evidence"):
            candidates.extend(parent.glob(f"{stem}-*/receipt.json"))
            candidates.extend(parent.glob(f"l1-{stem}-*/receipt.json"))
        assessments = []
        for path in sorted(set(candidates), key=lambda p: p.stat().st_mtime, reverse=True):
            receipt = json.loads(path.read_text())
            expected = receipt.get("results")
            if not isinstance(expected, dict):
                continue
            if stem in ("behavior-core", "memory-matrix", "fault-matrix",
                        "speculative-cancel") and not isinstance(expected.get("cases"), list):
                continue
            assessment, _ = assess(
                run, path, inputs, {}, ("python3", "verilator", "g++", "make"))
            assessments.append(assessment)
            if assessment["applicable"]:
                break
        results[stem] = assessments
    return {"scope": "historical applicability only, not behavior coverage closure",
            "components": results,
            "applicable_groups": [name for name, items in results.items()
                                  if items and items[-1]["applicable"]],
            "unavailable_groups": [name for name, items in results.items()
                                    if not items or not items[-1]["applicable"]]}


def component(run, stem, operation, *, inputs, parameters, tools, validate,
              equivalence=None, validate_retained=None):
    candidates = []
    for parent in (ROOT / "evidence/preparation", ROOT / "evidence"):
        if parent.is_dir():
            candidates.extend(parent.glob(f"{stem}-*/receipt.json"))
            candidates.extend(parent.glob(f"l1-{stem}-*/receipt.json"))
    assessments = []
    for path in sorted(set(candidates), key=lambda p: p.stat().st_mtime, reverse=True):
        assessment, results = assess(run, path, inputs, parameters, tools,
                                     equivalence=equivalence)
        assessments.append(assessment)
        if assessment["applicable"]:
            try:
                validate(results)
                if validate_retained is not None:
                    validate_retained(run, path, json.loads(path.read_text()), results)
            except (AssertionError, KeyError, TypeError, ValueError) as error:
                assessment["applicable"] = False
                assessment["reasons"].append(f"retained comparison/artifact invalid: {error}")
                print(f"COMPONENT_STALE {relative(path)}: {error}", flush=True)
            else:
                run.components.append({"receipt": relative(path), "status": "passed",
                                       "reused": True, "applicability": assessment})
                return results
    def checked(child):
        result = operation(child)
        validate(result)
        return result

    result = run.component(stem, checked)
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


def latest_marker_build():
    paths = []
    for parent in (ROOT / "evidence/preparation", ROOT / "evidence"):
        if parent.is_dir():
            paths.extend(parent.glob("*integrated-marker-*/receipt.json"))
    for path in sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True):
        receipt = json.loads(path.read_text())
        if receipt.get("status") == "passed":
            result = receipt.get("results", {})
            if isinstance(result, dict) and result.get("compiled"):
                return result["compiled"]
    return None


def marker_source_equivalence(run, path, receipt, name):
    """Bind the original completed driver, not a later optional clock recipe."""
    if name != "tests/marker_checks.py":
        return None
    old = path.parent / "source" / name
    if (not old.is_file() or hashlib.sha256(old.read_bytes()).hexdigest() !=
            receipt.get("source_sha256", {}).get(name)):
        return None

    def definitions(source):
        nodes = ast.parse(source).body
        return [ast.dump(node, include_attributes=False) for node in nodes
                if not isinstance(node, ast.FunctionDef) or node.name != "run_markers"]

    if definitions(old.read_text()) != definitions((ROOT / name).read_text()):
        return None
    result = receipt.get("results")
    if not isinstance(result, dict):
        return None
    binding = result.get("compiled", {}).get("binding", {})
    from marker_checks import MARKER_DRIVER
    prefill = "input_marker" in result
    if prefill:
        from prefill_marker_checks import prefill_driver
        text = prefill_driver()
        driver_name = "prefill_marker_driver.cpp"
        simulation_name = "prefill-marker-simulation.stdout.txt"
        summary_pattern = (
            r"^PREFILL_MARKER_SUMMARY opening=(\d+) frames=1 logits=(\d+) commits=(\d+) "
            r"drafts=(\d+) compared_writes=(\d+) requests=(\d+) cycles=(\d+)$")
    else:
        text = MARKER_DRIVER
        driver_name = "marker_driver.cpp"
        simulation_name = "marker-simulation.stdout.txt"
        summary_pattern = (
            r"^MARKER_SUMMARY opening=(\d+) frames=2 logits=(\d+) commits=(\d+) "
            r"drafts=(\d+) compared_writes=(\d+) requests=(\d+) cycles=(\d+)$")
    driver = path.parent / driver_name
    expected = hashlib.sha256(text.encode()).hexdigest()
    if (not driver.is_file() or hashlib.sha256(driver.read_bytes()).hexdigest() != expected or
            receipt.get("artifact_sha256", {}).get(driver_name) != expected or
            binding.get("driver_sha256") != expected):
        return None
    expected_parameters = {
        "COMPACT": 1, "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 2, "NUM_KV_HEADS": 1, "HEAD_DIM": 8, "VOCAB_SIZE": 151936,
        "MAX_SEQ_LEN": 4, "GROUP_SIZE": 8, "BANKS": 8, "QUEUE_DEPTH": 3}
    rtl = {name: digest for name, digest in run.hashes.items()
           if name.startswith("rtl/anvil_qn1_") and name.endswith(".sv")}
    if (binding.get("parameters") != expected_parameters or
            binding.get("rtl_sha256") != rtl or
            binding.get("simulation_threads") != result.get("simulation_threads") or
            binding.get("tool_versions") != {
                tool: run.tool_versions[tool] for tool in ("verilator", "g++", "make")}):
        return None
    simulation = [c for c in receipt.get("commands", [])
                  if Path(c.get("stdout", "")).name == simulation_name]
    expected_argv = [result["compiled"]["binary"],
                     relative(path.parent / "checkpoint-images"),
                     str(int(result["opening"])), str(result["simulation_threads"])]
    if len(simulation) != 1 or simulation[0].get("argv") != expected_argv:
        return None
    output = ROOT / simulation[0]["stdout"]
    if not output.is_file():
        return None
    import re
    matches = re.findall(summary_pattern, output.read_text(), re.M)
    if len(matches) != 1 or list(map(int, matches[0])) != result.get("counts"):
        return None
    return {"basis": "identical module definitions except run_markers wrapper; "
                     "exact original C++ driver, RTL, parameters, tools and raw summary",
            "snapshot_sha256": receipt["source_sha256"][name],
            "current_sha256": run.hashes[name], "driver_sha256": expected,
            "simulation_argv": expected_argv}


def marker_case(run, opening):
    from marker_checks import run_markers

    def validate(result):
        if result.get("counts", [])[:5] != [
                int(opening), 303872, 2, 0 if opening else 2, 304]:
            raise AssertionError("incomplete marker frames/commits/KV/counter comparisons")

    return component(
        run, "integrated-marker",
        lambda child: run_markers(child, opening=opening, threads=8,
                                  compiled=latest_marker_build(), clock_optimized=True),
        inputs=("tests/reference.py", "tests/model.py", "tests/marker_checks.py"),
        parameters={"opening": opening, "target": 151667 if opening else 151668,
                    "vocabulary": 151936, "simulation_threads": 8},
        tools=("python3", "verilator", "g++", "make"), validate=validate,
        equivalence=marker_source_equivalence)


def marker_applicability(run, opening):
    result = marker_case(run, opening)
    return {"scope": "source-bound marker component reuse, not whole-product acceptance",
            "opening": opening, "counts": result["counts"]}
