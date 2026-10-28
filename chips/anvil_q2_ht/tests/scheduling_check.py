"""Bounded scheduler recovery experiments, never aggregate accelerator acceptance."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_cache import compile_verilator, create_cache
from build_reuse_check import PROBE
from retention import Experiment
from scheduling import BUDGET_ENV, HELD_ENV, create_budget, run_graph
from verify import run_observed_child
import verify


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_receipt(root, output):
    return json.loads((root / output / "receipt.json").read_text())


def worker(args, root):
    experiment = Experiment(root, args.output, sys.orig_argv, [
        "tests/scheduling_check.py", "tests/build_cache.py", "tests/build_reuse_check.py",
        "tests/retention.py"])
    try:
        if args.kind == "nested":
            rows = [{
                "check": "nested-" + str(index), "outcome": "not-executed",
                "argv": ["python3", "-B", "tests/scheduling_check.py", "--worker",
                         "--output", str(experiment.output / ("nested-" + str(index))),
                         "--kind", "hold", "--build-cache", str(args.build_cache)]}
                for index in range(3)]
            graph(experiment, rows)
            experiment.finish(0)
            return 0
        if args.kind == "hold":
            time.sleep(0.5)
        relative = Path("sources/tests/build_reuse_probe.sv")
        source = PROBE if args.kind != "compile-failure" else PROBE.replace(
            "observed=operand*7+ADDEND;", "observed=;")
        (experiment.directory / relative).write_text(source)
        experiment.receipt["generated_input"] = {
            "path": str(args.output / relative),
            "sha256": hashlib.sha256(source.encode()).hexdigest()}
        executable = compile_verilator(experiment, [
            "verilator", "--binary", "--timing", "-Wno-fatal",
            "--top-module", "build_reuse_probe", "--Mdir", str(args.output / "obj"),
            "-MAKEFLAGS", "VK_PCH_I_FAST= VK_PCH_I_SLOW=", "-o", "probe_sim",
            "-GADDEND=2", str(args.output / relative)], cache=args.build_cache)
        text = experiment.run([executable, "+operand=11",
                               "+expected=" + ("80" if args.kind == "numerical-failure" else "79")],
                              "simulate")
        require("BUILD_REUSE_CHECKED operand=11 result=79" in text, "missing fresh comparison")
        experiment.receipt["comparison_summary"] = text.strip()
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


def execute(experiment, row):
    run_observed_child(experiment, row["argv"], row["check"], timeout=14400,
                       delegated=row.get("delegated", False))


def graph(experiment, rows, workers=None, expected_failure=False):
    experiment.receipt.setdefault("graphs", []).append(rows)
    schedule_count = len(experiment.receipt.get("schedules", []))
    failed = False
    try:
        run_graph(experiment, rows, lambda row: execute(experiment, row), workers=workers)
    except RuntimeError:
        failed = True
        if not expected_failure:
            raise
    require(failed == expected_failure, "wrong graph success/failure outcome")
    schedules = experiment.receipt["schedules"]
    require(len(schedules) == schedule_count + 1, "missing scheduler record")
    schedule = schedules[-1]
    journal = experiment.root / schedule["journal"]
    events = [json.loads(line) for line in journal.read_text().splitlines()]
    require(events[0]["event"] == "created" and events[-1]["event"] == "settled",
            "missing scheduler journal boundaries")
    require([row["check"] for row in events[0]["checks"]] ==
            [row["check"] for row in rows], "journal omitted planned workloads")
    for row in rows:
        transitions = [event for event in events
                       if event.get("check", {}).get("check") == row["check"]]
        expected = ["suppressed"] if row["outcome"] == "suppressed" else ["started", "finished"]
        require([event["event"] for event in transitions] == expected,
                "wrong journal transitions: " + row["check"])
        require(transitions[-1]["check"] == row,
                "journal lost final workload outcome: " + row["check"])
    require(all(before["offset_s"] <= after["offset_s"]
                for before, after in zip(events, events[1:])),
            "scheduler journal time ordering regressed")


def contract(experiment):
    cache = experiment.output / "builds"
    create_cache(experiment.root, cache)

    def row(name, kind="normal", dependencies=(), priority=0):
        return {"check": name, "outcome": "not-executed", "depends_on": list(dependencies),
                "priority": priority,
                "delegated": kind == "nested",
                "argv": ["python3", "-B", "tests/scheduling_check.py", "--worker",
                         "--output", str(experiment.output / name), "--kind", kind,
                         "--build-cache", str(cache)]}

    initial = [row("contender-a"), row("contender-b")]
    graph(experiment, initial)
    children = [read_receipt(experiment.root, experiment.output / row["check"]) for row in initial]
    builds = [child["builds"][0] for child in children]
    require(sum(not build["cache_hit"] for build in builds) == 1, "same-key double producer")
    require(builds[0]["key"] == builds[1]["key"], "same inputs produced distinct keys")
    require(any(build["producer_lock_wait_s"] > 0.1 for build in builds),
            "same-key producer contention not observed")
    require(children[0]["comparison_summary"] == children[1]["comparison_summary"],
            "contending consumers did not freshly compare identical results")
    failed_rows = [
        row("numerical-failure", "numerical-failure", priority=10),
        row("must-not-launch", dependencies=("numerical-failure",)),
        row("independent-success")]
    graph(experiment, failed_rows, expected_failure=True)
    require([row["outcome"] for row in failed_rows] == ["failed", "suppressed", "passed"],
            "failure did not preserve independent work or suppress its dependent")
    require(not (experiment.directory / "must-not-launch").exists(), "dependent was executed")
    rejected = read_receipt(experiment.root, experiment.output / "numerical-failure")
    require(rejected["exit"] == 1, "failed child receipt not retained")
    simulated = next(command for command in rejected["commands"]
                     if command["argv"][0].endswith("probe_sim"))
    require(simulated["exit"] != 0 and not simulated["timed_out"] and
            "BUILD_REUSE_NUMERICAL" in (experiment.root / simulated["stdout"]).read_text(),
            "failure was not the intended executed numerical assertion")
    broken = [row("broken-a", "compile-failure"), row("broken-b", "compile-failure")]
    graph(experiment, broken, expected_failure=True)
    receipts = [read_receipt(experiment.root, experiment.output / row["check"]) for row in broken]
    compiles = [command for child in receipts for command in child["commands"]
                if "--binary" in command["argv"]]
    require(len(compiles) == 1 and compiles[0]["exit"] != 0,
            "failed producer was rebuilt or incorrectly reused")
    require(any("incomplete/failed build cache producer" in child.get("failure", "")
                for child in receipts), "failed producer consumer diagnosis missing")
    require(len(list((experiment.root / cache).glob("*/build-failure.json"))) == 1,
            "missing immutable failed build manifest")
    nested = [row("nested", "nested"), row("outer", "hold")]
    graph(experiment, nested)
    nested_receipt = read_receipt(experiment.root, experiment.output / "nested")
    outer_receipt = read_receipt(experiment.root, experiment.output / "outer")
    commands = [command for command in experiment.receipt["commands"]
                if command["argv"] == nested[1]["argv"]] + nested_receipt["commands"]
    events = []
    for command in commands:
        lease = command.get("resource_lease")
        require(lease is not None, "nested workload bypassed the shared budget")
        start = command["execution_start_monotonic_s"]
        events += [(start, 1), (start + command["execution_duration_s"], -1)]
    active = peak = 0
    for _, delta in sorted(events):
        active += delta
        peak = max(peak, active)
    require(peak == 2 and active == 0, "nested/outer resource lease accounting exceeded two slots")
    require(any(command["resource_lease"]["wait_s"] > 0.1 for command in commands),
            "shared nested/outer resource contention was not observed")
    require(outer_receipt["exit"] == 0, "independent outer comparison failed")
    experiment.receipt["nested_resource_observation"] = {
        "peak_leased_subtrees": peak, "budget_slots": 2,
        "maximum_lease_wait_s": max(command["resource_lease"]["wait_s"] for command in commands)}
    experiment.receipt["comparison_summary"] = (
        "same-key single producer; two fresh equal comparisons; numerical failure retained; "
        "dependent suppressed; independent success retained; failed build producer retained once")


def command(experiment, prefix, name, script, options=(), cache=None):
    output = experiment.output / prefix / name
    return {"check": prefix + "-" + name, "outcome": "not-executed",
            "child_output": str(output),
            "argv": ["python3", "-B", "tests/" + script, "--output", str(output),
                     *options, *(["--build-cache", str(cache)] if cache is not None else [])],
            "delegated": script == "system_benchmark.py"}


def semantic_benchmarks(value):
    if isinstance(value, dict):
        return {key: semantic_benchmarks(item) for key, item in value.items()
                if key not in ("receipt", "simulation_stdout")}
    if isinstance(value, list):
        return [semantic_benchmarks(item) for item in value]
    return value


def semantic_summary(text):
    lines = text.splitlines()
    provenance = [line for line in lines if re.fullmatch(
        r"- [^:\n]+:\d+: Verilog \$finish", line)]
    require(len(provenance) == 1, "missing or extra Verilator finish provenance")
    return [line for line in lines if line not in provenance]


def representative(experiment, nested=False):
    batches = []
    for prefix in ("serial", "concurrent"):
        cache = experiment.output / prefix / "builds"
        create_cache(experiment.root, cache)
        if nested:
            # Serial workers apply inside the real benchmark graph as well.
            rows = [command(experiment, prefix, "benchmark", "system_benchmark.py",
                            ["--seed", "11", "--cache", "0", "--weight-mode", "w4",
                             *(["--serial-preparation"] if prefix == "serial" else [])], cache)]
            stem = experiment.output / prefix / "benchmark" / "mode0-cache0-seed11"
            recompare = command(
                experiment, prefix, "recompare", "benchmark_check.py",
                ["--ht-receipt", str(stem.with_name(stem.name + "-ht") / "receipt.json"),
                 "--parent-receipt", str(stem.with_name(stem.name + "-parent4") / "receipt.json"),
                 "--seed", "11"])
            recompare["depends_on"] = [rows[0]["check"]]
            rows.append(recompare)
        else:
            rows = [
                command(experiment, prefix, "synthesis", "synthesis_check.py",
                        ["--top", "anvil_q2_ht_tensor_array", "--expand-packages"]),
                command(experiment, prefix, "tokens-a", "system_check.py",
                        ["--simulator", "verilator"]),
                command(experiment, prefix, "tokens-b", "system_check.py",
                        ["--simulator", "verilator"]),
                command(experiment, prefix, "persistence", "system_check.py",
                        ["--simulator", "verilator", "--scenario", "persistence",
                         "--mode", "1", "--cache", "2", "--seed", "29"], cache)]
            for row in rows[1:3]:
                row["argv"] += ["--build-cache", str(cache)]
            rows[0]["priority"] = 100
        graph(experiment, rows, workers=1 if prefix == "serial" else None)
        batches.append(rows)
    comparisons = []
    for serial, concurrent in zip(*batches):
        before = read_receipt(experiment.root, Path(serial["child_output"]))
        after = read_receipt(experiment.root, Path(concurrent["child_output"]))
        require(before["exit"] == after["exit"] == 0, "representative child failed")
        fields = (("summary", "results") if serial["check"].endswith("recompare") else
                  ("benchmarks",)) if nested else (
            ("structure",) if serial["check"].endswith("synthesis") else
            ("fixture", "comparison_summary", "readback_sha256", "readback_bytes_per_pass"))
        for field in fields:
            normalize = semantic_summary if field == "comparison_summary" else semantic_benchmarks
            require(normalize(before[field]) == normalize(after[field]),
                    "serial/concurrent semantic mismatch: " + serial["check"] + "/" + field)
        comparisons.append({"serial": serial["child_output"] + "/receipt.json",
                            "concurrent": concurrent["child_output"] + "/receipt.json",
                            "equal_fields": list(fields)})
    experiment.receipt["serial_concurrent_comparisons"] = comparisons
    if not nested:
        parallel = batches[1]
        require(parallel[0]["start_offset_s"] <= min(row["start_offset_s"] for row in parallel[1:]),
                "independent synthesis was not started first")
        receipts = [read_receipt(experiment.root, Path(row["child_output"])) for row in parallel[1:]]
        builds = [receipt["builds"][0] for receipt in receipts]
        require(len({build["key"] for build in builds}) == 1 and
                sum(not build["cache_hit"] for build in builds) == 1,
                "connected same-key compilation did not have one producer")
    experiment.receipt["comparison_summary"] = (
        "fresh serial and concurrent numerical/protocol observations identical; "
        "bounded small-model preparation, not full-model or aggregate acceptance")


def planned_l1_checks(experiment):
    captured = []
    with patch.object(verify, "create_budget"), patch.object(verify, "create_cache"), \
            patch.object(verify, "require_tools"), \
            patch.object(verify, "run_graph", side_effect=lambda _, rows, __: captured.extend(rows)):
        verify.l1(experiment)
    return captured


def critical_path(experiment):
    require(experiment.receipt["resource_budget"]["slots"] >= 2,
            "critical-path concurrency requires at least two detected resource slots")
    cache = experiment.output / "verilator-builds"
    create_cache(experiment.root, cache)
    experiment.receipt["build_cache"] = str(cache)
    planned = planned_l1_checks(experiment)
    names = ("default-synthesis", "D5-common-service-benchmark",
             "five-domain-ledger-recomparison")
    require(len(planned) == len({row["check"] for row in planned}),
            "duplicate production workload")
    by_name = {row["check"]: row for row in planned}
    rows = [by_name[name] for name in names]
    rows[1]["delegated"] = True
    experiment.receipt["critical_path_checks"] = rows
    graph(experiment, rows)

    children = []
    for row in rows:
        child = json.loads((experiment.root / row["receipt"]).read_text())
        require(child["exit"] == 0, "critical-path child did not complete: " + row["check"])
        require(all(experiment.receipt["source_hashes"].get(name) == digest
                    for name, digest in child["source_hashes"].items()),
                "critical-path child source mismatch")
        children.append(child)
    synthesis, benchmark, recompare = children
    require(synthesis["structure"]["top"] == "anvil_q2_ht_top",
  