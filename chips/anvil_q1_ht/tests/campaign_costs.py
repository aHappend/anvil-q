#!/usr/bin/env python3
"""Complete-case build-reuse diagnosis; never a substitute for admitted checks.

python3 -B tests/campaign_costs.py --config 1 --seeds 17
executes all tokens in both storage modes with independently generated inputs.
Historical costs are labeled diagnostic observations, never reused test results.
"""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiments import integration_matrix
from reference import MATRIX
from verify import Evidence, ROOT, file_sha256

CAMPAIGN = (
    "fixture-integrity", "checkpoint-repack", "parameters", "dequant", "tensor", "math",
    "dma", "kv", "csr-upload", "integration-matrix", "faults", "orphan-fault",
    "abort-states", "compatibility-matrix", "sensitivity", "synthesis-control",
    "synthesis", "kernel-default", "projection-default", "bf16-default",
    "vocabulary-default",
    "layer-awq", "layer-bf16", "attention-context",
)


def historical_costs(evidence):
    rows = []
    stages = {}
    gaps = evidence.record["historical_receipt_gaps"] = []
    for path in sorted((ROOT / "evidence/preparation").glob("*/receipt.json")):
        if path == evidence.folder / "receipt.json":
            continue
        # A missing or malformed historical receipt is not a successful cost sample.
        try:
            record = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            gaps.append({"receipt": evidence.relative(path), "sha256": file_sha256(path),
                         "size_bytes": path.stat().st_size, "error": str(exc),
                         "status": "malformed_historical_evidence_not_repaired",
                         "used_as_cost_or_acceptance_sample": False})
            evidence.flush()
            continue
        commands = record.get("commands", [])
        settled = [command for command in commands
                   if command.get("process_settled") and "elapsed_seconds" in command]
        if settled:
            row = {
                "receipt": evidence.relative(path), "sha256": file_sha256(path),
                "probe": record.get("probe"), "outcome": record.get("outcome", "unfinished"),
                "end_time": record.get("end_time"),
                "command_seconds": sum(command["elapsed_seconds"] for command in settled),
                "compile_seconds": sum(command["elapsed_seconds"] for command in settled
                                       if command["label"].endswith("-compile")),
                "simulation_seconds": sum(command["elapsed_seconds"] for command in settled
                                          if command["label"].endswith("-simulation")),
                "settled_commands": len(settled), "all_commands": len(commands),
                "source_sha256": record.get("source_sha256", {}),
                "rtl_and_reference_match_current": all(
                    record.get("source_sha256", {}).get(name) == digest
                    for name, digest in evidence.record["source_sha256"].items()
                    if name.startswith(("rtl/", "anvil_q1_reference/")) or
                    name == "tests/reference.py"),
            }
            if record.get("end_time"):
                row["receipt_wall_seconds"] = (
                    datetime.datetime.fromisoformat(record["end_time"]) -
                    datetime.datetime.fromisoformat(record["start_time"])).total_seconds()
            fixture = record.get("engineering_fixture")
            if fixture:
                row["case"] = {key: fixture.get(key) for key in
                               ("mode", "seed", "shape", "read_fault_beat", "write_fault_beat",
                                "orphan_response_fault", "abort_stage")}
                row["token_count"] = len(fixture.get("tokens", []))
            builds = record.get("simulation_builds", [])
            if builds:
                row["build_key"] = builds[-1]["key"]
            if commands and commands[-1].get("process_settled"):
                row["last_command_seconds"] = commands[-1].get("elapsed_seconds")
            rows.append(row)
            if (row["outcome"] == "probe_passed" and row["rtl_and_reference_match_current"] and
                    row.get("probe") and row.get("receipt_wall_seconds")):
                stages.setdefault(row["probe"], []).append({
                    "seconds": row["receipt_wall_seconds"], "receipt": evidence.relative(path),
                    "receipt_sha256": row["sha256"],
                    "measurement": "standalone_complete_probe_including_nested_children",
                })
        for stage in record.get("mandatory_campaign", []):
            if stage["outcome"] == "completed":
                elapsed = (datetime.datetime.fromisoformat(stage["end_time"]) -
                           datetime.datetime.fromisoformat(stage["start_time"])).total_seconds()
                stages.setdefault(stage["probe"], []).append({
                    "seconds": elapsed, "receipt": evidence.relative(path),
                    "receipt_sha256": file_sha256(path),
                })
    evidence.record["historical_cost_inventory"] = rows
    evidence.record["whole_campaign_cost_breakdown"] = [
        {"stage": name, "complete_stage_samples": stages.get(name, []),
         "status": "measured_historical" if name in stages else "no_complete_stage_measurement",
         "acceptance_evidence": False}
        for name in CAMPAIGN]
    evidence.record["historical_complete_stage_lower_bound_seconds"] = sum(
        min(sample["seconds"] for sample in stages[name])
        for name in CAMPAIGN if name in stages)
    evidence.record["cost_accounting_limits"] = (
        "The lower bound excludes every unmeasured campaign stage. Historical "
        "costs use their original harness/options, not a prediction of this revision. "
        "No missing, canceled or malformed execution is assigned zero cost or a pass.")
    evidence.flush()
    partition_diagnosis(evidence, rows)


def partition_diagnosis(evidence, samples):
    """Cost-only proposal: neither a new executable contract nor cached passes."""
    partitions = []
    for config, shape in enumerate(MATRIX):
        complete = [
            row for row in samples
            if row["outcome"] == "probe_passed" and row["rtl_and_reference_match_current"]
            and row.get("build_key") and row.get("case", {}).get("shape") == vars(shape)
            and row.get("token_count") == min(shape.max_seq, shape.window + 2) + 1
            and row.get("probe", "").startswith(f"matrix-{config}-")
            and row["case"].get("read_fault_beat") == -1
            and row["case"].get("write_fault_beat") == -1
            and not row["case"].get("orphan_response_fault")
            and not row["case"].get("abort_stage")
        ]
        latest = max(complete, key=lambda row: row["end_time"]) if complete else None
        matching = [row for row in complete if row["build_key"] == latest["build_key"]]
        for seed in (17, 89, 257):
            for mode in ("AWQ", "BF16"):
                candidates = [row for row in matching
                              if row["case"]["seed"] == seed and row["case"]["mode"] == mode]
                sample = max(candidates, key=lambda row: row["end_time"]) if candidates else None
                entry = {
                    "configuration": config, "seed": seed, "mode": mode,
                    "argv": ["python3", "-B", "tests/campaign_costs.py", "--config", str(config),
                             "--seeds", str(seed), "--modes", mode],
                    "measurement_status": "measured_preparation" if sample else "unmeasured",
                    "required_tokens": min(shape.max_seq, shape.window + 2) + 1,
                    "required_ordered_logits": (min(shape.max_seq, shape.window + 2) + 1) * shape.vocab,
                }
                if sample:
                    entry.update({
                        "receipt": sample["receipt"], "receipt_sha256": sample["sha256"],
                        "measured_case_wall_seconds": sample["receipt_wall_seconds"],
                        "functional_simulation_seconds": sample["last_command_seconds"],
                        "simulation_only_excess_over_2700_seconds": max(
                            0, sample["last_command_seconds"] - 2700),
                        "build_key": sample["build_key"],
                    })
                partitions.append(entry)
    evidence.record["execution_partition_proposal"] = {
        "status": "diagnosis_only_requires_Coordinator_and_independent_review",
        "original_and_supplemental_checks_remain_mandatory": True,
        "does_not_repair_or_replace_original_command": True,
        "matrix_case_commands": partitions,
        "other_stage_commands": [
            ["python3", "tests/verify.py", "--probe", name]
            for name in CAMPAIGN if name != "integration-matrix"],
        "observed_matrix_cases": sum(row["measurement_status"] == "measured_preparation"
                                     for row in partitions),
        "required_matrix_cases": len(partitions),
        "missing_case_costs_are_unknown_not_zero": True,
        "whole_campaign_total_seconds": None,
        "limitation": (
            "These commands preserve complete cases but are proposed append-only diagnostics, "
            "not admitted replacements for aggregate L1. A measured single-case simulation "
            "over 2700 seconds cannot fit unchanged patrol even without compilation. "
            "Coordinator must diagnose execution-policy reconciliation or admit a separately "
            "verified state-preserving checkpoint harness; no such harness is implemented here. "
            "Other stage costs and the complete campaign total remain partially unmeasured."),
    }
    evidence.flush()


def compare_retained(evidence):
    comparisons = []
    for row in evidence.record["integration_matrix"]:
        child = json.loads((ROOT / row["receipt"]).read_text())
        fixture = child["engineering_fixture"]
        candidates = []
        for sample in evidence.record["historical_cost_inventory"]:
            case = sample.get("case", {})
            if (sample["outcome"] == "probe_passed" and
                    case.get("shape") == fixture["shape"] and
                    case.get("mode") == fixture["mode"] and
                    case.get("seed") == fixture["seed"]):
                old = json.loads((ROOT / sample["receipt"]).read_text())
                bindings = child["source_sha256"]
                if any(old["source_sha256"].get(name) != digest for name, digest in bindings.items()
                       if name.startswith(("rtl/", "anvil_q1_reference/")) or
                       name == "tests/reference.py"):
                    continue
                if old.get("engineering_fixture") != fixture:
                    continue
                counters = old["observations"][-1]["observed_counters"]
                if counters != child["observations"][-1]["observed_counters"]:
                    raise AssertionError("complete-case counters changed: " + sample["receipt"])
                candidates.append(sample["receipt"])
        comparisons.append({
            "configuration": row["configuration"], "seed": row["seed"], "mode": row["mode"],
            "fresh_receipt": row["receipt"], "matching_complete_historical_receipts": candidates,
            "tokens": row["tokens"], "ordered_logits": row["ordered_logits"],
            "observed_counters": child["observations"][-1]["observed_counters"],
            "expectations_sha256": hashlib.sha256(
                json.dumps(fixture["tokens"], sort_keys=True).encode()).hexdigest(),
            "compile_seconds": sum(command["elapsed_seconds"] for command in child["commands"]
                                   if command["label"].endswith("-compile")),
            "simulation_seconds": sum(command["elapsed_seconds"] for command in child["commands"]
                                      if command["label"].endswith("-simulation")),
            "compiled_build_seconds": sum(
                command["elapsed_seconds"] for command in child["commands"]
                if command["label"].endswith("-compile") and command["argv"][0] == "verilator"),
            "functional_simulation_seconds": child["commands"][-1]["elapsed_seconds"],
            "simulation_child_user_seconds": sum(
                command.get("sequential_child_user_seconds", 0) for command in child["commands"]
                if command["label"].endswith("-simulation")),
            "simulation_child_system_seconds": sum(
                command.get("sequential_child_system_seconds", 0) for command in child["commands"]
                if command["label"].endswith("-simulation")),
            "reused": child["simulation_builds"][-1]["reused"],
        })
    evidence.record["complete_case_comparisons"] = comparisons
    evidence.record["cost_scope"] = (
        "All requested cases executed freshly; historical results only compare costs, "
        "expectations and counters. Missing stage costs are unknown, not zero. "
        "No whole-campaign patrol closure or accelerator performance is established.")
    evidence.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=int, choices=(0, 1, 2), default=1)
    parser.add_argument("--seeds", type=int, nargs="+", default=[17])
    parser.add_argument("--repair-of")
    parser.add_argument("--modes", choices=("AWQ", "BF16"), nargs="+", default=["AWQ", "BF16"])
    parser.add_argument("--regressions-only", action="store_true")
    parser.add_argument("--compatibility", action="store_true",
                        help="also freshly execute both parent and compatibility implementations")
    args = parser.parse_args()
    evidence = Evidence("campaign-costs", args.repair_of)
    try:
        historical_costs(evidence)
        for tool, flags in (("python3", ["--version"]), ("iverilog", ["-V"]),
                            ("vvp", ["-V"]), ("verilator", ["--version"]),
                            ("g++", ["--version"])):
            evidence.command([tool, *flags], tool.replace("+", "p") + "-version")
        for script, extra in (
                ("simulation_checks.py", ["--regression-child"]),
                ("evidence_checks.py", [])):
            evidence.command(
                ["python3", "-B", "tests/" + script, *extra, "--scratch",
                 evidence.relative(evidence.folder / (script + "-scratch"))],
                script.replace(".py", "") + "-regression")
        if args.regressions_only:
            evidence.finish("probe_passed", "Harness regressions and historical cost inventory only; "
                            "no RTL case or acceptance result is claimed.")
            return 0
        started = time.monotonic()
        integration_matrix(evidence, configurations=(args.config,), seeds=tuple(args.seeds),
                           modes=tuple(args.modes))
        evidence.record["fresh_complete_cases_elapsed_seconds"] = time.monotonic() - started
        compare_retained(evidence)
        if args.compatibility:
            from compatibility import compatibility
            for seed in args.seeds:
                trial = Evidence(
                    f"cost-compatibility-{args.config}-{seed}",
                    source_root=evidence.folder / "sources")
                trial.simulation_build_pool = evidence.simulation_build_pool
                try:
                    compatibility(trial, seed, args.config)
                    trial.finish("probe_passed", "Complete public-interface compatibility cost case.")
                except (OSError, RuntimeError, AssertionError, ValueError) as exc:
                    trial.finish("failed", str(exc))
                    raise
                evidence.record["observations"].append({
                    "compatibility_receipt": evidence.relative(trial.folder / "receipt.json"),
                    "seed": seed, "configuration": args.config})
                evidence.flush()
        evidence.finish("probe_passed", "Complete-case build reuse and cost diagnosis only; "
                        "all original acceptance requirements remain mandatory.")
        return 0
    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
        evidence.finish("failed", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
