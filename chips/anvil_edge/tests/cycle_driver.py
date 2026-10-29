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
from pathlib import Path

from deepseek_shell import measure
from official import ROOT
from qwen_integration import save
from qwen_shell import shell_case
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
