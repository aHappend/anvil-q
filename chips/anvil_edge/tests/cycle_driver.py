"""Explicit shell/boot clock driver and bounded paired feasibility experiments.

The candidate removes only the recurring SV clock-delay coroutine. Verilator
timing support remains for the original edge waits and post-edge stimulus delays;
removing those would change the experiment rather than measure the clock driver.
Only the exact shell and boot clock templates support this driver. Other benches
retain their existing driver; the timed SV driver remains for paired probes.
"""

import copy
import hashlib
import json
import re
import time
from pathlib import Path

from deepseek_shell import measure
from official import ROOT
from qwen_integration import save
from qwen_shell import shell_case, shell_workers
from qwen_tables import require


EXPLICIT_CLOCK = r"""#include "Vbench.h"
#include "verilated.h"
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <memory>

int main(int argc, char** argv) {
    auto context = std::make_unique<VerilatedContext>();
    context->commandArgs(argc, argv);
    auto bench = std::make_unique<Vbench>(context.get());
    bench->clk = 0;
    bench->eval();
    uint64_t edge = 5000;  // 1 ns / 1 ps timescale: first rising edge at 5 ns.
    uint64_t edges = 0;
    while (!context->gotFinish()) {
        uint64_t next = edge;
        if (bench->eventsPending()) next = std::min(next, bench->nextTimeSlot());
        if (next <= context->time()) {
            std::fprintf(stderr, "EXPLICIT_CLOCK_NONPROGRESS time=%llu\n",
                         static_cast<unsigned long long>(context->time()));
            return 2;
        }
        context->time(next);
        if (next == edge) {
            bench->clk = !bench->clk;
            edge += 5000;
            ++edges;
        }
        bench->eval();
    }
    bench->final();
    std::printf("EXPLICIT_CLOCK edges=%llu time_ps=%llu\n",
                static_cast<unsigned long long>(edges),
                static_cast<unsigned long long>(context->time()));
    return 0;
}
"""


def observable_trace(child, prefix):
    log = (ROOT / child["stdout"]).read_text()
    return [line for line in log.splitlines()
            if line.startswith((prefix + "_", "COMPARED ", "SCOREBOARD_INJECT "))]


def run_execution_cost(evidence):
    """Fresh, bounded compact profiling, retaining the original public oracle."""
    evidence.tools(("python3", "verilator", "g++", "make", "gprof"))
    interrupted = ROOT / (
        "evidence/verification/l1-da9a33ef8bca4a49b6b71c31de9288f0/"
        "case-0221-run_qwen_shell/case-0225-qwen-shell-b0-s1/"
        "1228-qwen-shell-b0-s1-simulate/stdout.log")
    evidence.record["execution_cost_predecessor"] = {
        "path": str(interrupted.relative_to(ROOT)),
        "available": interrupted.is_file(),
        "sha256": hashlib.sha256(interrupted.read_bytes()).hexdigest()
                  if interrupted.is_file() else None,
        "scope": "Interrupted complete-table simulation; no completed inference inferred",
    }
    directory = evidence.path / "compact-inputs"
    directory.mkdir()
    evidence.child(
        ["python3", "tests/qwen_shell.py", evidence.relative(directory), "--compact"],
        "execution-cost-inputs")
    info = json.loads((directory / "shell-reference.json").read_bytes())
    rows = []
    for label, profile in (("baseline", False), ("profile", True)):
        scope = copy.copy(evidence)
        scope.name_prefix = label + "-"
        scope.compiler_profile = profile
        row = shell_case(scope, info, 17, 1, True)
        rows.append(row)
        if profile:
            samples = sorted((scope.path / row["name"]).glob("gmon.*"))
            require(len(samples) == 1, "Expected exactly one settled gprof sample")
            executable = row["compile_receipt"]["argv"]
            binary = ROOT / executable[executable.index("--Mdir") + 1] / "simulation"
            evidence.child(
                ["gprof", "-b", evidence.relative(binary), evidence.relative(samples[0])],
                "execution-cost-profile")
    require(rows[0]["actual_comparisons"] == rows[1]["actual_comparisons"] and
            observable_trace(rows[0]["simulation_receipt"], "QWEN_SHELL") ==
            observable_trace(rows[1]["simulation_receipt"], "QWEN_SHELL"),
            "Profiling changed original public transaction/cycle/byte observations")
    evidence.record["execution_cost"] = [{
        "variant": label, "simulation_seconds": row["simulation_receipt"]["duration_s"],
        "compile_seconds": row["compile_receipt"]["duration_s"],
        "resources": row["simulation_receipt"]["resources"],
        "actual_comparisons": row["actual_comparisons"],
        "raw_stdout": row["simulation_receipt"]["stdout"],
    } for label, row in zip(("baseline", "profile"), rows)]
    save(evidence.path / "execution-cost.json", evidence.record["execution_cost"])


def run_execution_acceleration(evidence):
    """Measure compiler changes and concurrency, never extrapolate a passing L1."""
    evidence.tools(("python3", "verilator", "g++", "make"))
    run_execution_cost(evidence)
    evidence.record["execution_acceleration_scope"] = (
        "Paired synthetic capacities 257/4097 and compact six-cell schedules. "
        "All original physical head rows, SPI bytes, DDR acknowledgements, "
        "numerical writes, prompts, reload and drain assertions remain active. "
        "No complete-table or aggregate execution is authorized by this diagnostic.")
    pairs = []
    compact = None
    for capacity in (257, 4097):
        directory = evidence.path / f"capacity-{capacity}"
        directory.mkdir()
        evidence.child(
            ["python3", "tests/qwen_shell.py", evidence.relative(directory),
             "--compact", str(capacity)], f"acceleration-inputs-{capacity}")
        info = json.loads((directory / "shell-reference.json").read_bytes())
        if capacity == 257:
            compact = info
            evidence.child(
                ["python3", "tests/test_shell_execution.py", evidence.relative(evidence.path),
                 evidence.relative(directory)], "execution-policy-regressions")
        rows = []
        for label, lto, bind in (("literal", False, False),
                                 ("runtime", False, True),
                                 ("lto", True, True)):
            scope = copy.copy(evidence)
            scope.name_prefix = f"{label}-{capacity}-"
            scope.compiler_lto = lto
            rows.append(shell_case(scope, info, 17, 1, True, bind_transport=bind))
        for row in rows[1:]:
            require(rows[0]["actual_comparisons"] == row["actual_comparisons"] and
                    rows[0]["source_sha256"] == row["source_sha256"] and
                    rows[0]["input_files"] == row["input_files"] and
                    observable_trace(rows[0]["simulation_receipt"], "QWEN_SHELL") ==
                    observable_trace(row["simulation_receipt"], "QWEN_SHELL"),
                    "Compiler/input acceleration changed public observations")
        pairs.append({
            "capacity": capacity, "identical_public_trace": True,
            "comparisons": rows[0]["actual_comparisons"],
            "variants": [{
                "variant": label, "simulation_seconds": row["simulation_receipt"]["duration_s"],
                "compile_seconds": row["compile_receipt"]["duration_s"],
                "resources": row["simulation_receipt"]["resources"],
                "simulation_receipt": str(Path(row["simulation_receipt"]["stdout"]).parent /
                                          "receipt.json"),
            } for label, row in zip(("literal", "runtime", "lto"), rows)],
        })
        save(evidence.path / f"acceleration-{capacity}.json", pairs[-1])
    evidence.record["execution_acceleration_pairs"] = pairs
    literal = copy.copy(evidence)
    literal.name_prefix = "literal-control-"
    before = len(evidence.record["coverage"])
    literal.run_cases([
        (f"literal-s{seed}-b{bypass}",
         lambda case, seed=seed, bypass=bypass:
         shell_case(case, compact, seed, bypass, False, bind_transport=False))
        for seed in (1, 17, 89) for bypass in (0, 1)
    ], workers=shell_workers(evidence))
    original_rows = evidence.record["coverage"][before:]
    require(len(original_rows) == 6 and
            all(row["status"] == "passed" for row in original_rows),
            "All original literal-transport controls must complete")
    original_traces = {
        row["name"].removeprefix("literal-control-"):
        observable_trace(row["simulation_receipt"], "QWEN_SHELL") for row in original_rows}
    # Warm the exact two-frame program once, outside BOTH timed schedules.
    # Transport, image paths and seed are runtime inputs, not compile identities.
    warmup = copy.copy(evidence)
    warmup.name_prefix = "schedule-warmup-"
    started = time.monotonic()
    warm = shell_case(warmup, compact, 17, 0, False)
    evidence.record["execution_schedule_warmup"] = {
        "wall_seconds": time.monotonic() - started,
        "compile_seconds": warm["compile_receipt"]["duration_s"],
        "simulation_seconds": warm["simulation_receipt"]["duration_s"],
        "compile_cache_key": warm["compile_cache_key"],
        "scope": "Excluded equally from both schedules; full cold build remains measured",
    }
    schedules = []
    baseline = None
    for workers in dict.fromkeys((1, shell_workers(evidence))):
        scope = copy.copy(evidence)
        scope.name_prefix = f"schedule-w{workers}-"
        before = len(evidence.record["coverage"])
        start = time.monotonic()
        scope.run_cases([
            (f"compact-s{seed}-b{bypass}",
             lambda case, seed=seed, bypass=bypass:
             shell_case(case, compact, seed, bypass, False))
            for seed in (1, 17, 89) for bypass in (0, 1)
        ], workers=workers)
        rows = evidence.record["coverage"][before:]
        require(len(rows) == 6 and all(row["status"] == "passed" for row in rows),
                "Every compact scheduling cell must complete")
        require(all(row["compile_cache_hit"] and
                    row["compile_cache_key"] == warm["compile_cache_key"] for row in rows),
                "Scheduling must compare equally warmed, identical production executables")
        if baseline is None:
            baseline = next(row for row in rows if row["name"].endswith("-b1-s17"))
        schedules.append({
            "workers": workers, "wall_seconds": time.monotonic() - start,
            "actual_comparisons": sum(row["actual_comparisons"] for row in rows),
            "simulation_seconds": [row["simulation_receipt"]["duration_s"] for row in rows],
            "max_rss_kib": [row["simulation_receipt"]["resources"]["max_rss_kib"] for row in rows],
            "traces": {re.sub(r"^schedule-w\d+-", "", row["name"]):
                       observable_trace(row["simulation_receipt"], "QWEN_SHELL") for row in rows},
            "source_sha256": rows[0]["source_sha256"],
            "actual_builds_in_timed_region": sum(not row["compile_cache_hit"] for row in rows),
        })
        require(schedules[-1]["traces"] == original_traces and
                schedules[-1]["actual_comparisons"] ==
                sum(row["actual_comparisons"] for row in original_rows),
                "Runtime transport binding changed an original functional observation")
        save(evidence.path / f"schedule-{workers}.json", schedules[-1])
    if len(schedules) == 2:
        require(schedules[0]["traces"] == schedules[1]["traces"] and
                schedules[0]["actual_comparisons"] == schedules[1]["actual_comparisons"],
                "Concurrency changed public transaction/cycle/byte observations")
    evidence.record["execution_schedules"] = schedules
    evidence.record["execution_monitor_controls"] = controls(evidence, baseline, "qwen")
    command = baseline["simulation_receipt"]["argv"]
    rejected = []
    for name, value in (("missing", None), ("negative", -1), ("oversized", 2)):
        arguments = [arg for arg in command if not arg.startswith("+verification_bypass=")]
        if value is not None:
            arguments.append(f"+verification_bypass={value}")
        child = evidence.child(arguments, "transport-input-" + name, allow_failure=True)
        output = (ROOT / child["stdout"]).read_text() + (ROOT / child["stderr"]).read_text()
        require(child["exit_code"] not in (0, None) and not child["timed_out"] and
                child["child_settled"] and child["process_group_settled"] and
                "QWEN_SHELL_INVALID_TRANSPORT" in output and "%Error:" in output,
                "Transport runtime input must fail explicitly before inference")
        rejected.append(child)
    evidence.record["execution_transport_controls"] = rejected
    execution_sizing(evidence, pairs)


def execution_sizing(evidence, pairs):
    """Conditional workload projection, never a claimed complete-table result."""
    relative = Path(
        "evidence/verification/l1-da9a33ef8bca4a49b6b71c31de9288f0/"
        "case-0221-run_qwen_shell/shell-reference.json")
    path = ROOT / relative
    launch_path = ROOT / Path(*relative.parts[:3]) / "launch.json"
    boot_log = path.parent / (
        "case-0225-qwen-shell-b0-s1/1228-qwen-shell-b0-s1-simulate/stdout.log")
    missing = [str(item.relative_to(ROOT)) for item in (path, launch_path, boot_log)
               if not item.is_file()]
    if missing:
        evidence.record["execution_sizing"] = {
            "available": False, "path": str(relative), "missing": missing,
            "complete_table_retry_authorized": False,
            "limitation": "Optional historical sizing is unavailable, not passed. "
                          "No projection or missing evidence reconstructed. "
                          "All current functional measurements execute independently."}
        return
    prior = json.loads(path.read_bytes())
    launch = json.loads(launch_path.read_bytes())
    require(all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value
                for name, value in launch["source_sha256"].items()
                if name.startswith(("rtl/", "anvil_q1_reference/rtl/"))),
            "Historical workload no longer describes the current design")
    points = []
    for pair_result in pairs:
        result = next(row for row in pair_result["variants"] if row["variant"] == "runtime")
        child = json.loads((ROOT / result["simulation_receipt"]).read_bytes())
        text = (ROOT / child["stdout"]).read_text()
        boot = re.findall(r"^QWEN_SHELL_BOOT .* cycles=(\d+)$", text, re.MULTILINE)
        frame = re.findall(r"^QWEN_SHELL_FRAME .* operations=(\d+).* cycles=(\d+)$",
                           text, re.MULTILINE)
        require(len(boot) == len(frame) == 1, "Sizing requires completed compact frames")
        operations, cycles = map(int, frame[0])
        points.append({
            "capacity": pair_result["capacity"], "boot_cycles": int(boot[0]),
            "frame_cycles": cycles, "operations": operations,
            "cycles_per_second": cycles / child["duration_s"],
        })
    require(points[0]["operations"] == points[1]["operations"] == 9,
            "Both scaling points must execute all nine operations")
    row_cycles = (
        (points[1]["frame_cycles"] - points[1]["boot_cycles"]) -
        (points[0]["frame_cycles"] - points[0]["boot_cycles"])
    ) / ((points[1]["capacity"] - points[0]["capacity"]) * points[0]["operations"])
    capacity = prior["physical_capacity"]
    operations = [len(case["core_operation_ids"]) for case in prior["cases"]]
    require(len(operations) == 5 and prior["max_new_tokens"] == 8 and
            all(len(case["generated_ids"]) == 8 for case in prior["cases"]),
            "Historical sizing must preserve the five eight-token workloads")
    # This is the actual last observed boot in the interrupted run, not a
    # reconstructed completion or an assumed fresh full-table execution.
    boots = re.findall(r"^QWEN_SHELL_BOOT .* cycles=(\d+)$",
                       boot_log.read_text(), re.MULTILINE)
    require(len(boots) == 1, "Expected the authentic interrupted boot observation")
    boot_cycles = int(boots[0])
    estimated = 2 * boot_cycles + row_cycles * capacity * sum(operations)
    rates = [point["cycles_per_second"] for point in points]
    evidence.record["execution_sizing"] = {
        "available": True, "historical_workload": str(relative),
        "historical_workload_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "historical_launch_sha256": hashlib.sha256(launch_path.read_bytes()).hexdigest(),
        "historical_boot_log": str(boot_log.relative_to(ROOT)),
        "historical_boot_log_sha256": hashlib.sha256(boot_log.read_bytes()).hexdigest(),
        "points": points, "cycles_per_physical_row_per_operation_fit": row_cycles,
        "physical_capacity": capacity, "operations_per_prompt": operations,
        "observed_historical_boot_cycles": boot_cycles,
        "boots_per_cell": 2, "cells": 6,
        "conditional_cell_seconds_range": [estimated / max(rates), estimated / min(rates)],
        "conditional_three_worker_seconds_range": [
            2 * estimated / max(rates), 2 * estimated / min(rates)],
        "complete_table_retry_authorized": False,
        "limitation": "Far-range synthetic-capacity linear extrapolation, not a measured "
                      "full-table runtime, proven bound or acceptance. Assumes compact "
                      "throughput extends to full tables. Adds two observed boot cycle "
                      "counts but omits full-table tokenization, other non-head work, "
                      "fresh generation/compilation and other mandatory suites. "
                      "Concurrency cannot shorten the critical path of a single cell.",
    }
    save(evidence.path / "execution-sizing.json", evidence.record["execution_sizing"])


def controls(evidence, baseline, family):
    prefix = family.upper().replace("-", "_") + "_SHELL"
    results = []
    for mode, name, suffix in (
        (1, "wrong-value", "NUMERICAL_WRITE"),
        (2, "duplicate", "UNEXPECTED_WRITE"),
        (3, "missing", "DRAIN"),
    ):
        child = evidence.child(
            [*baseline["simulation_receipt"]["argv"], f"+scoreboard_fault={mode}"],
            family + "-scoreboard-" + name, allow_failure=True)
        output = (ROOT / child["stdout"]).read_text() + (ROOT / child["stderr"]).read_text()
        assertion = prefix + "_" + suffix
        require(child["exit_code"] not in (0, None) and not child["timed_out"] and
                child["child_settled"] and child["process_group_settled"] and
                f"SCOREBOARD_INJECT {name}" in output and assertion in output and
                "%Error:" in output,
                f"Clock-driver monitor did not reject {family}/{name}")
        mismatches = [line[line.index(assertion):] for line in output.splitlines()
                      if "Assertion failed" in line and assertion in line]
        require(len(mismatches) == 1, "Expected exactly one original rejection assertion")
        results.append({"fault": name, "assertion": assertion, "mismatch": mismatches[0],
                        "trace": observable_trace(child, prefix), "simulation": child,
                        "scope": "Scoreboard rejection, not an RTL mutation kill"})
    return results


def pair(evidence, info, family, seeds, transports, general_only, reject):
    observations = {}
    for driver in ("timed-SV", "explicit-cycle"):
        scope = copy.copy(evidence)
        scope.explicit_clock = driver == "explicit-cycle"
        scope.name_prefix = driver + "-"
        before = len(evidence.record["coverage"])
        scope.run_cases([
            (f"{driver}-{family}-b{bypass}-s{seed}",
             lambda case, seed=seed, bypass=bypass:
             shell_case(case, info, seed, bypass, general_only, family=family))
            for seed in seeds for bypass in transports
        ], workers=1)
        rows = evidence.record["coverage"][before:]
        require(len(rows) == len(seeds) * len(transports) and
                all(row["status"] == "passed" for row in rows),
                "Both drivers must complete the whole admitted compact cell")
        prefix = family.upper().replace("-", "_") + "_SHELL"
        if general_only:
            measurements = []
            for row in rows:
                trace = observable_trace(row["simulation_receipt"], prefix)
                operations = [line for line in trace if line.startswith(prefix + "_OPERATION ")]
                frames = [line for line in trace if line.startswith(prefix + "_FRAME ")]
                boots = [line for line in trace if line.startswith(prefix + "_BOOT ")]
                require(len(frames) == len(boots) == 1 and
                        len(operations) == len(info["cases"][0]["core_operation_ids"]),
                        "Scaling must retain full physical-head and eight-token generation")
                values = {key: int(value) for key, value in
                          re.findall(r"(\w+)=(\d+)", frames[0])}
                expected = info["cases"][0]
                require(values["embedding_reads"] ==
                        values["operations"] * (8 * info["physical_capacity"] + 8) and
                        values["activation_writes"] == expected["activation_write_count"] and
                        values["output_bytes"] == len(bytes.fromhex(expected["output_utf8_hex"])),
                        "Scaling obligations differ from independent references")
                measurements.append({
                    "name": row["name"], "frames": [values],
                    "simulation_seconds": row["simulation_receipt"]["duration_s"],
                    "compile_seconds": row["compile_receipt"]["duration_s"],
                    "actual_comparisons": row["actual_comparisons"],
                    "raw_stdout": row["simulation_receipt"]["stdout"],
                })
        else:
            measurements = measure(evidence, info, rows, prefix)
        baseline = next((row for row in rows if row["name"].endswith("-b1-s17")), None)
        if reject:
            require(baseline is not None, "Rejection controls require seed17/bypass baseline")
        rejected = controls(scope, baseline, family) if reject else []
        observations[driver] = {"measurements": measurements, "controls": rejected,
                                "rows": rows}
        save(evidence.path /
             f"{family}-{info['physical_capacity']}-{driver}-measurements.json",
             {"measurements": measurements, "controls": rejected})
    a, b = (observations[key] for key in ("timed-SV", "explicit-cycle"))
    comparisons = []
    for old, new in zip(a["rows"], b["rows"]):
        require(old["runtime_arguments"] == new["runtime_arguments"] and
                old["input_files"] == new["input_files"] and
                old["source_sha256"] == new["source_sha256"] and
                old["actual_comparisons"] == new["actual_comparisons"] and
                observable_trace(old["simulation_receipt"], prefix) ==
                observable_trace(new["simulation_receipt"], prefix),
                "Explicit clock changed public transaction/cycle/byte observations")
        old_seconds = old["simulation_receipt"]["duration_s"]
        new_seconds = new["simulation_receipt"]["duration_s"]
        comparisons.append({
            "baseline": old["name"], "candidate": new["name"],
            "identical_public_trace": True,
            "comparisons": old["actual_comparisons"],
            "baseline_seconds": old_seconds, "candidate_seconds": new_seconds,
            "speed_ratio": old_seconds / new_seconds,
        })
    for old, new in zip(a["controls"], b["controls"]):
        require(old["assertion"] == new["assertion"] and
                old["mismatch"] == new["mismatch"] and old["trace"] == new["trace"],
                "Explicit clock changed a monitor rejection or its public trace")
    return {"family": family, "capacity": info["physical_capacity"],
            "comparisons": comparisons,
            "drivers": {key: {k: v for k, v in value.items() if k != "rows"}
                        for key, value in observations.items()}}


def run_driver_comparison(evidence):
    evidence.tools(("python3", "verilator", "g++", "make"))
    evidence.record["driver_experiment_scope"] = (
        "Synthetic compact inputs only; no complete-table retry or delivery acceptance. "
        "External C++ clock removes the timed SV clock process, not delayed stimulus "
        "scheduling. Both drivers keep identical production RTL and original assertions.")
    results = []
    evidence.record["driver_comparison"] = results
    for policy in ("raw", "bos"):
        directory = evidence.path / ("fixture-" + policy)
        directory.mkdir()
        evidence.child(
            ["./.venv/bin/python", "tests/deepseek_shell.py",
             evidence.relative(directory), policy], "driver-inputs-" + policy)
        info = json.loads((directory / "shell-reference.json").read_bytes())
        results.append(pair(evidence, info, "deepseek-" + policy, (1, 17, 89), (0, 1),
                            general_only=False, reject=True))
        save(evidence.path / ("driver-comparison-" + policy + ".json"), results[-1])


def run_driver_scaling(evidence, receipts):
    require(len(receipts) == 1, "Scaling requires the completed compact driver comparison")
    relative = Path(receipts[0])
    require(not relative.is_absolute() and ".." not in relative.parts and
            relative.parts[:2] == ("evidence", "preparation") and
            relative.name == "receipt.json", "Expected project preparation receipt")
    raw = (ROOT / relative).read_bytes()
    prior = json.loads(raw)
    require(prior["exit_code"] == 0 and prior["child_settled"] and
            prior["sources_unchanged"] and len(prior["driver_comparison"]) == 2,
            "Both compact policies must have completed before scaling")
    for name, value in prior["source_sha256"].items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value,
                "Sources changed after driver comparison: " + name)
    evidence.record["driver_scaling_parent"] = {
        "path": str(relative), "sha256": hashlib.sha256(raw).hexdigest()}
    results = []
    evidence.record["driver_scaling"] = results
    for capacity in (257, 1025, 4097):
        directory = evidence.path / f"capacity-{capacity}"
        directory.mkdir()
        evidence.child(
            ["./.venv/bin/python", "tests/qwen_shell.py", evidence.relative(directory),
             "--compact", str(capacity)], f"driver-scaling-inputs-{capacity}")
        info = json.loads((directory / "shell-reference.json").read_bytes())
        results.append(pair(evidence, info, "qwen", (17,), (1,),
                            general_only=True, reject=False))
        save(evidence.path / f"driver-scaling-{capacity}.json", results[-1])
    evidence.record["driver_scaling_limit"] = (
        "Measured supported synthetic capacities only; complete-table execution, "
        "large working-set behavior and full-model/hardware acceptance remain unproven.")
    ratios = [row["speed_ratio"] for point in results for row in point["comparisons"]]
    summary = {
        "capacities": [point["capacity"] for point in results],
        "measured_speed_ratio_range": [min(ratios), max(ratios)],
        "ratios_are": "baseline simulation seconds / candidate simulation seconds; "
                      "single serial pairs on shared tool execution, not a timing guarantee",
        "measurements": [{
            "capacity": point["capacity"], "driver": driver,
            "cycles": row["frames"][-1]["cycles"],
            "simulation_seconds": row["simulation_seconds"],
            "compile_seconds": row["compile_seconds"],
            "compared_transactions": row["actual_comparisons"],
            "cycles_per_second": row["frames"][-1]["cycles"] / row["simulation_seconds"],
        } for point in results for driver, data in point["drivers"].items()
            for row in data["measurements"]],
        "complete_table_retry_authorized": False,
        "limitation": "Clock scheduling for delayed stimulus remains enabled. Removing "
                      "the SV clock coroutine is not proof of eliminating scheduling cost. "
                      "No measured capacity reaches the official complete-table extent.",
    }
    save(evidence.path / "driver-scaling-summary.json", summary)
    evidence.record["driver_scaling_summary"] = summary


def run_driver_capacity(evidence, receipts):
    """One admitted synthetic capacity cell, never a complete-table retry."""
    expected = (
        "evidence/preparation/shell-driver-comparison-"
        "90b7b32df583442187a2cd9bc10a8663/receipt.json",
        "evidence/preparation/shell-driver-scaling-"
        "4e63b60753ea4ae1a749fe0b83adbdee/receipt.json",
        "evidence/preparation/shell-driver-capacity-"
        "e54e1e48aac34acea26cdf6598f5bb4c/receipt.json",
    )
    require(tuple(receipts) == expected, "Capacity probe requires all three admitted parents")
    parents = []
    for name in receipts:
        raw = (ROOT / name).read_bytes()
        prior = json.loads(raw)
        require(prior["exit_code"] == 0 and prior["child_settled"] and
                prior["sources_unchanged"], "Parent experiment did not settle successfully")
        require(all(child["child_settled"] and
                    child.get("process_group_settled", True) and not child["timed_out"]
                    for child in prior["children"]),
                "Parent experiment contains an unsettled or timed-out child")
        if name == expected[-1]:
            ancestor = (
                "evidence/preparation/shell-driver-capacity-"
                "37feda994948418a8f5ea7f292b74203/receipt.json"
            )
            require(prior["driver_capacity"]["capacity"] == 32769 and
                    prior["driver_capacity"]["comparisons"][0]["identical_public_trace"] and
                    [entry["path"] for entry in prior["driver_capacity_parents"]] ==
                    [*expected[:2], ancestor],
                    "Capacity-32769 must retain its paired comparison and historical parents")
            for path in prior["source_sha256"]:
                if path not in ("tests/qwen_shell.py", "tests/cycle_driver.py"):
                    snapshot = ROOT / Path(name).parent / "sources" / path
                    require((ROOT / path).read_bytes() == snapshot.read_bytes(),
                            "Source changed after capacity-32769: " + path)
            for present, recorded in zip(parents, prior["driver_capacity_parents"][:2]):
                require(present == recorded, "Retained measurement parent changed")
            evidence.record["unavailable_historical_ancestors"] = [{
                **prior["driver_capacity_parents"][-1],
                "reported_by": name,
                "available": (ROOT / ancestor).exists(),
                "validated": False,
                "interpretation": "Unavailable historical ancestor reported by the "
                                  "retained capacity-32769 parent; not reconstructed "
                                  "or newly validated.",
            }]
            require(not (ROOT / ancestor).exists(),
                    "Historical ancestor availability differs from admitted recovery")
        for path, value in prior["source_sha256"].items():
            if not path.startswith("tests/"):
                require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == value,
                        "Non-verification source changed after admitted parents: " + path)
        parents.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest()})
    evidence.record["driver_capacity_parents"] = parents
    evidence.record["driver_experiment_scope"] = (
        "One serial synthetic capacity-65537, seed17/bypass pair, general-only; "
        "eight selected tokens and all physical head rows. Supplemental diagnostic, "
        "not official complete tables, pretrained weights or delivery acceptance.")
    evidence.tools(("python3", "verilator", "g++", "make"))
    directory = evidence.path / "capacity-65537"
    directory.mkdir()
    generation = evidence.child(
        ["./.venv/bin/python", "tests/qwen_shell.py", evidence.relative(directory),
         "--compact", "65537"], "driver-capacity-inputs-65537")
    info = json.loads((directory / "shell-reference.json").read_bytes())
    require(info["physical_capacity"] == 65537 and
            info["active_vocabulary"] == 257 and
            len(info["cases"][0]["generated_ids"]) == 8,
            "Capacity probe must retain all eight generated tokens")
    result = pair(evidence, info, "qwen", (17,), (1,),
                  general_only=True, reject=False)
    evidence.record["driver_capacity"] = result
    save(evidence.path / "driver-capacity-65537.json", result)
    summary = {
        "capacity": 65537, "seed": 17, "bypass": True,
        "generation_seconds": generation["duration_s"],
        "measurements": [{
            "driver": driver, "cycles": row["frames"][-1]["cycles"],
            "operations": row["frames"][-1]["operations"],
            "output_bytes": row["frames"][-1]["output_bytes"],
            "simulation_seconds": row["simulation_seconds"],
            "compile_seconds": row["compile_seconds"],
            "compared_transactions": row["actual_comparisons"],
            "cycles_per_second": row["frames"][-1]["cycles"] / row["simulation_seconds"],
            "raw_stdout": row["raw_stdout"],
        } for driver, data in result["drivers"].items() for row in data["measurements"]],
        "comparisons": result["comparisons"],
        "complete_table_retry_authorized": False,
        "limitation": "Single shared-execution pair, not a timing guarantee. Synthetic "
                      "active vocabulary remains 257; full-model/table/hardware "
                      "acceptance and all mandatory checks remain outstanding.",
    }
    save(evidence.path / "driver-capacity-summary.json", summary)
    evidence.record["driver_capacity_summary"] = summary
