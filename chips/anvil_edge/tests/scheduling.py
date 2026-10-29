"""Bounded execution policy and advisory scheduling diagnostics."""

import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import threading


def resource_limits(root):
    cpu = len(os.sched_getaffinity(0))
    available = int(next(line.split()[1] for line in
                         Path("/proc/meminfo").read_text().splitlines()
                         if line.startswith("MemAvailable:"))) * 1024
    cgroup = Path("/sys/fs/cgroup")
    group = next((line.split("::", 1)[1] for line in
                  Path("/proc/self/cgroup").read_text().splitlines()
                  if line.startswith("0::")), "/")
    current = cgroup / group.lstrip("/")
    constraints = []
    while current == cgroup or cgroup in current.parents:
        for filename in ("cpu.max", "memory.max"):
            path = current / filename
            if not path.exists():
                continue
            value = path.read_text().strip()
            constraints.append({"path": str(path.relative_to(cgroup)), "value": value})
            if filename == "cpu.max" and not value.startswith("max"):
                quota, period = map(int, value.split())
                cpu = min(cpu, max(1, quota // period))
            elif filename == "memory.max" and value != "max":
                used = int((current / "memory.current").read_text())
                available = min(available, max(0, int(value) - used))
        if current == cgroup:
            break
        current = current.parent
    disk = shutil.disk_usage(root).free
    workers = max(1, min(8, cpu // 3, available // (2 << 30), disk // (2 << 30)))
    return {
        "workers": workers, "cpu_capacity": cpu, "available_memory_bytes": available,
        "available_disk_bytes": disk, "cgroup_constraints": constraints,
        "policy": "At most eight tool children; reserve three CPU slots and 2 GiB "
                  "memory/disk per child. Verilator compilation uses -j 2. "
                  "Nested case batches share the same child semaphore.",
    }


def source_contract():
    root = Path(__file__).resolve().parent.parent
    trees = {path.stem: ast.parse(path.read_text(), filename=str(path))
             for path in sorted((root / "tests").glob("*.py"))}
    definitions = {}
    for tree in trees.values():
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definitions[node.name] = node
    graph = {
        name: {call.func.id for call in ast.walk(node)
               if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
               and call.func.id in definitions}
        for name, node in definitions.items()
    }
    entry = next(node for node in trees["verify"].body
                 if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == "L1_SUITES"
                         for target in node.targets))
    roots = [node.id for node in ast.walk(entry.value)
             if isinstance(node, ast.Name) and node.id in definitions
             and node.id.startswith("run_")]
    required_roots = {
        "run_arithmetic", "run_fifo", "run_controller", "run_uart",
        "run_detokenizer", "run_boot", "run_config", "run_mapper", "run_bpe",
        "run_normalization", "run_dfa", "run_tokenizer", "run_numerical",
        "run_parameters", "run_adapters", "run_memory", "run_top", "run_top_resets",
        "run_synthesis", "run_mutations", "run_metadata", "run_mapper_cache",
        "run_head_row_reuse",
    }
    assert len(roots) == len(set(roots)) and set(roots) == required_roots
    l1 = [node for node in ast.walk(trees["verify"]) if isinstance(node, ast.If)
          and isinstance(node.test, ast.Compare)
          and isinstance(node.test.left, ast.Attribute)
          and node.test.left.attr == "check"
          and any(isinstance(value, ast.Constant) and value.value == "l1"
                  for value in node.test.comparators)]
    assert len(l1) == 1
    scheduled = [node for statement in l1[0].body for node in ast.walk(statement)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                 and node.func.attr == "run_cases"]
    assert len(scheduled) == 1
    assert any(isinstance(node, ast.Name) and node.id == "L1_SUITES"
               for node in ast.walk(scheduled[0]))
    stages = next(node for node in trees["verify"].body
                  if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == "OFFICIAL_STAGES"
                          for target in node.targets))
    stage_names = [node.id for node in stages.value.elts]
    direct = [statement.value.func.id for statement in l1[0].body
              if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
              and isinstance(statement.value.func, ast.Name)]
    assert direct == ["run_stages"]
    assert stage_names == ["run_qwen_fragments", "run_qwen_regex",
                           "run_unicode_rtl", "run_official_checkpoint",
                           "run_deepseek_reference", "run_deepseek_dfa",
                           "run_deepseek_integration", "run_deepseek_boot",
                           "run_deepseek_bos",
                           "run_qwen_integration", "run_qwen_boot", "run_qwen_shell"]
    stage_call, = [node for node in ast.walk(l1[0])
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == "run_stages"]
    assert [node.id for node in stage_call.args] == ["evidence", "OFFICIAL_STAGES"]
    scoped, = [node for node in ast.walk(definitions["run_stages"]) if isinstance(node, ast.Call)
               and isinstance(node.func, ast.Attribute) and node.func.attr == "run_cases"]
    assert any(item.arg == "workers" and isinstance(item.value, ast.Name)
               and item.value.id == "workers" for item in scoped.keywords)
    assert any(isinstance(node, ast.comprehension) and isinstance(node.iter, ast.Name)
               and node.iter.id == "stages" for node in ast.walk(scoped))
    incomplete = l1[0].body[-1]
    assert isinstance(incomplete, ast.Raise) and isinstance(incomplete.exc, ast.Call)
    assert isinstance(incomplete.exc.args[0], ast.Constant)
    assert incomplete.exc.args[0].value.startswith("L1 incomplete:")
    reached = set(roots)
    while True:
        expanded = reached | set().union(*(graph[name] for name in reached))
        if expanded == reached:
            break
        reached = expanded
    required_nested = {
        "run_top_profiles", "run_top_errors", "run_top_reload",
        "run_top_profile_uart", "run_top_profile_reload",
        "run_storage_faults", "run_large_images", "run_storage_edges",
        "run_image_upper", "run_watchdog_width", "run_uart_controls",
        "run_numerical_errors", "run_tokenizer_capacity",
        "run_top_interactions",
        "run_top_token_capacity",
    }
    assert required_nested <= reached, sorted(required_nested - reached)
    requirements = json.loads((root / "tests/data/requirements.json").read_text())
    assets = json.loads((root / "tests/data/assets.json").read_text())
    assert requirements["seeds"] == [1, 17, 89]
    assert requirements["max_new_tokens"] == 8
    assert requirements["prompts"] == [
        "What is the capital of France?", "Compute 17 + 25.",
        "Write a Python function that adds two integers.",
        "All robins are birds. Are robins animals? Explain briefly.",
        "Translate hello into Chinese.",
    ]
    assert [entry["family_id"] for entry in assets["official_tokenizers"]] == [1, 2, 3]
    assert isinstance(requirements["remaining_required_checks"], list)
    print(json.dumps({
        "scope": "Static transitive wiring, not executed functional coverage",
        "sources": len(trees), "entrypoints": sorted(roots),
        "reachable_functions": sorted(reached),
        "call_graph": {name: sorted(graph[name]) for name in sorted(reached)},
        "required_nested_suites": sorted(required_nested),
        "official_checkpoint_wired_and_l1_incomplete_rejection_retained": True,
        "available_official_tokenizers": [
            entry["family"] for entry in assets["official_tokenizers"] if entry["available"]],
    }, indent=2))


def scheduling_probe(evidence):
    from storage import top_test
    from protocol import UART
    cases = []
    for seed in (1, 17, 89):
        cases.append((f"top-seed-{seed}",
                      lambda scope, seed=seed: top_test(scope, seed)))
        cases.append((f"reload-seed-{seed}",
                      lambda scope, seed=seed: top_test(scope, seed, reload_profile=True)))
    bench = UART.replace("DIVISOR", "4").replace("@DEPTH@", "1").replace("SEED", "1")
    for simulator in ("iverilog", "verilator"):
        cases.append(("compact-" + simulator,
                      lambda scope, simulator=simulator: scope.simulate(
                          "scheduling-uart-" + simulator, bench,
                          ["rtl/anvil_edge_fifo.sv", "rtl/anvil_edge_uart_io.sv"],
                          78, simulator=simulator)))
    evidence.run_cases(cases)
    rows = list(evidence.record["coverage"])
    assert len(rows) == len(cases) and all(row["status"] == "passed" for row in rows)
    reloads = [row for row in rows if "nfc-bos-to-nfd-reload" in row["name"]]
    assert len(reloads) == 3
    assert len({row["compile_cache_key"] for row in reloads}) == 1
    assert sum(not row["compile_cache_hit"] for row in reloads) == 1
    evidence.record["scheduling_measurement"] = {
        "scope": "Six real production-top transactions plus compact dual-simulator UART",
        "comparisons": sum(row["actual_comparisons"] for row in rows),
        "compile_children": [row for row in evidence.record["children"]
                             if "--binary" in row["argv"] or "-g2012" in row["argv"]],
        "simulation_children": [row["simulation_receipt"] for row in rows],
        "cache_hits": sum(row.get("compile_cache_hit", False) for row in rows),
        "limits": "Measured submatrix only; not full L1 or official-model acceptance",
    }


def cache_recovery(evidence, failure):
    """Rebuild absent cache outputs; reject changed identities without editing evidence.

    Run with tests/verify.py --probe compile-cache-recovery. The absent output
    is an in-memory cache fixture, not removal of a historical artifact.
    """
    from protocol import UART
    bench = UART.replace("DIVISOR", "4").replace("@DEPTH@", "1").replace("SEED", "1")
    sources = ["rtl/anvil_edge_fifo.sv", "rtl/anvil_edge_uart_io.sv"]
    first = evidence.simulate("cache-original", bench, sources, 78, simulator="verilator")
    key = first["compile_cache_key"]
    original = evidence.compiled_simulations[key]
    missing = evidence.path / "intentionally-absent-cache-output"
    assert not missing.exists()
    evidence.compiled_simulations[key] = (missing, *original[1:])
    evidence.record["compile_cache_recovery"] = {
        "scope": "Harness recovery fixture, not full product acceptance",
        "fault": "In-memory cache points to an absent output; retained files unchanged",
        "absent_output": evidence.relative(missing),
        "original_compile_receipt": first["compile_receipt"],
    }
    rebuilt = evidence.simulate("cache-rebuilt", bench, sources, 78, simulator="verilator")
    assert not rebuilt["compile_cache_hit"]
    assert rebuilt["compile_cache_recovery"]["reason"] == "cached executable absent"
    assert rebuilt["compile_receipt"] != first["compile_receipt"]
    reused = evidence.simulate("cache-reused", bench, sources, 78, simulator="verilator")
    assert reused["compile_cache_hit"]
    assert reused["compile_receipt"] == rebuilt["compile_receipt"]
    cached = evidence.compiled_simulations[key]
    evidence.compiled_simulations[key] = (*cached[:2], "invalid-fixture-hash", cached[3])
    before = len(evidence.record["children"])
    try:
        evidence.simulate("cache-identity-rejected", bench, sources, 78, simulator="verilator")
    except failure as error:
        assert str(error) == "Compiled simulation changed before reuse"
    else:
        raise AssertionError("Changed cached executable identity was accepted")
    finally:
        evidence.compiled_simulations[key] = cached
    assert len(evidence.record["children"]) == before
    rejected = evidence.record["coverage"][-1]
    rejected["status"] = "expected-harness-rejection"
    rejected["expected_rejection"] = "Compiled simulation changed before reuse"
    evidence.record["compile_cache_recovery"].update(
        rebuilt_compile_receipt=rebuilt["compile_receipt"],
        compared_uart_transactions=sum(row["actual_comparisons"]
                                      for row in (first, rebuilt, reused)),
        unchanged_cache_reused=True,
        changed_identity_rejected_before_execution=True,
    )


def scheduling_controls(evidence):
    """Actual failure/peer settlement and concurrent cache/isolation checks."""
    from protocol import UART
    gate = threading.Barrier(evidence._limits["workers"])

    def command(scope, index):
        scope.source_overrides["unused-isolation-check"] = str(index)
        scope.name_prefix = str(index)
        gate.wait(timeout=60)
        assert scope.source_overrides["unused-isolation-check"] == str(index)
        result = scope.child(
            ["python3", "-c", f"print('CASE {index}'); raise SystemExit({7 if index == 0 else 0})"],
            "same-child-name")
        assert (Path(__file__).resolve().parent.parent / result["stdout"]).read_text() == f"CASE {index}\n"

    expected_error = None
    first_child = len(evidence.record["children"])
    try:
        evidence.run_cases([
            (f"command-{index}", lambda scope, index=index: command(scope, index))
            for index in range(evidence._limits["workers"])
        ])
    except Exception as error:
        expected_error = error
    batch = evidence.record["case_batches"][-1]
    children = evidence.record["children"][first_child:]
    assert expected_error is not None and batch["status"] == "failed"
    assert len(batch["results"]) == evidence._limits["workers"]
    assert sum(row["status"] == "failed" for row in batch["results"]) == 1
    assert len(children) == evidence._limits["workers"]
    assert sum(row["exit_code"] == 7 for row in children) == 1
    assert all(row["child_settled"] and row["process_group_settled"] for row in children)
    assert len({row["stdout"] for row in children}) == len(children)
    assert evidence.source_overrides == {} and evidence.name_prefix == ""

    bench = UART.replace("DIVISOR", "4").replace("@DEPTH@", "1").replace("SEED", "1")

    def simulation(scope, index):
        scope.simulator_override = "verilator"
        scope.name_prefix = f"copy-{index}-"
        scope.source_overrides["unused-isolation-check"] = str(index)
        return scope.simulate("uart", bench, [
            "rtl/anvil_edge_fifo.sv", "rtl/anvil_edge_uart_io.sv"], 78)

    evidence.run_cases([
        (f"cache-copy-{index}", lambda scope, index=index: simulation(scope, index))
        for index in range(3)
    ])
    rows = list(evidence.record["coverage"])
    assert len(rows) == 3 and all(row["status"] == "passed" for row in rows)
    assert len({row["compile_cache_key"] for row in rows}) == 1
    assert sum(not row["compile_cache_hit"] for row in rows) == 1
    assert evidence.source_overrides == {} and evidence.name_prefix == ""
    assert evidence.simulator_override is None
    expected_error = None
    try:
        evidence.simulate(
            "infrastructure-zero-comparison-rejection",
            'module bench; initial begin $display("COMPARED 0"); $finish; end endmodule\n',
            [], 1, simulator="iverilog")
    except Exception as error:
        expected_error = error
    rejected = evidence.record["coverage"][-1]
    assert expected_error is not None and "invalid comparison count [0]" in str(expected_error)
    assert rejected["status"] == "failed"
    assert rejected["failure_stage"] == "comparison-accounting"
    assert rejected["simulation_receipt"]["exit_code"] == 0
    assert rejected["simulation_receipt"]["process_group_settled"]
    rejected.update(status="expected-harness-rejection",
                    reason="Successful child exit with zero comparisons is not verification")
    attempt_controls(evidence)
    evidence.record["scheduling_controls"] = {
        "expected_child_exit": 7, "expected_batch_rejections": 1,
        "settled_children": len(children), "distinct_log_paths": len(children),
        "concurrent_identical_simulations": 3, "actual_compilations": 1,
        "passed_simulation_comparisons": sum(row["actual_comparisons"] for row in rows),
        "expected_zero_comparison_rejections": 1,
        "scope": "Harness diagnostic; deliberate child rejection is not an RTL mutation kill",
    }


def attempt_controls(evidence):
    """Distinguish executed compiler/assertion failures from unstarted simulation."""
    root = Path(__file__).resolve().parent.parent
    results = []
    for name, bench, stage, diagnostic in (
        ("compiler", "module bench; initial begin syntax deliberately invalid; end endmodule\n",
         "compile", "syntax error"),
        ("assertion", 'module bench; initial $fatal(1,"ACCOUNTING_FUNCTIONAL_CONTROL"); endmodule\n',
         "simulate", "ACCOUNTING_FUNCTIONAL_CONTROL"),
        ("count", 'module bench; initial begin $display("COMPARED 2"); $finish; end endmodule\n',
         "comparison-accounting", "COMPARED 2"),
    ):
        start = len(evidence.record["children"])
        error = None
        try:
            evidence.simulate("accounting-control-" + name, bench, [], 1,
                              simulator="iverilog")
        except Exception as failure:
            error = failure
        row = evidence.record["coverage"][-1]
        children = evidence.record["children"][start:]
        assert error is not None and row["status"] == "failed"
        assert row["failure_stage"] == row["stage"] == stage
        assert row["diagnostic"] == f"{type(error).__name__}: {error}"
        assert children and all(child["child_settled"] and
                                child["process_group_settled"] and
                                not child["timed_out"] for child in children)
        compiles = [child for child in children if child["argv"][0] == "iverilog"
                    and "-g2012" in child["argv"]]
        simulations = [child for child in children if child["argv"][0] == "vvp"]
        assert len(compiles) == 1
        if stage == "compile":
            assert compiles[0]["exit_code"] != 0 and not simulations
            assert "simulation_receipt" not in row
            observed = compiles[0]
        else:
            assert compiles[0]["exit_code"] == 0 and len(simulations) == 1
            observed = simulations[0]
            assert observed == row["simulation_receipt"]
            assert (observed["exit_code"] == 0) == (stage == "comparison-accounting")
        output = "".join((root / observed[key]).read_text() for key in ("stdout", "stderr"))
        assert diagnostic in output
        row.update(status="expected-harness-rejection",
                   reason="Deliberate synthetic accounting control, not a production RTL mutant")
        results.append({"case": name, "failure_stage": stage,
                        "observed_diagnostic": diagnostic,
                        "child_receipt": str(Path(observed["stdout"]).parent / "receipt.json")})
    evidence.record["attempt_accounting_controls"] = {
        "scope": "Real compact Icarus compiler and runtime controls; no product acceptance",
        "results": results,
    }


def main():
    if sys.argv[1:] == ["--source-contract"]:
        source_contract()
        return
    root = Path(__file__).resolve().parent.parent
    inputs, simulations = [], []
    for argument in sys.argv[1:]:
        path = Path(argument)
        if (path.is_absolute() or ".." in path.parts or path.name != "receipt.json"
                or path.parts[:2] != ("evidence", "preparation")):
            raise ValueError("Scheduling inputs must be project preparation receipts")
        raw = (root / path).read_bytes()
        receipt = json.loads(raw)
        if receipt["exit_code"] != 0 or not receipt["sources_unchanged"]:
            raise ValueError(f"Unsettled or changed-source scheduling input: {path}")
        for source, expected in receipt["source_sha256"].items():
            if source.startswith("rtl/"):
                actual = hashlib.sha256((root / source).read_bytes()).hexdigest()
                if actual != expected:
                    raise ValueError(f"Design changed since measured execution: {source}")
        inputs.append({"receipt": argument, "sha256": hashlib.sha256(raw).hexdigest(),
                       "source_sha256": receipt["source_sha256"]})
        for row in receipt["coverage"]:
            if row["status"] != "passed":
                raise ValueError(f"Incomplete scheduling input: {row['name']}")
            child = row["simulation_receipt"]
            if (child["exit_code"] != 0 or child["timed_out"]
                    or not child["child_settled"]):
                raise ValueError("Unsettled simulation in scheduling input")
            simulations.append({
                "name": row["name"], "duration_s": child["duration_s"],
                "argv": child["argv"], "stdout": child["stdout"],
                "actual_comparisons": row["actual_comparisons"],
            })
    if not simulations or len({row["name"] for row in simulations}) != len(simulations):
        raise ValueError("Scheduling inputs must contain distinct measured cases")
    total = sum(row["duration_s"] for row in simulations)
    print(json.dumps({
        "scope": "Observed sequential submatrix, excluding all compilation and other L1 suites",
        "acceptance_evidence": False,
        "inputs": inputs, "simulations": simulations, "simulation_seconds": total,
        "patrol_check_seconds": 2700,
        "observed_submatrix_exceeds_patrol": total > 2700,
        "limits": "Historical measurements, not an irreducible runtime lower bound. "
                  "Parallel execution or further source-bound compilation/simulation "
                  "optimization has not been measured. No admitted command, watchdog, "
                  "seed, assertion or coverage requirement is changed.",
    }, indent=2))


if __name__ == "__main__":
    main()
