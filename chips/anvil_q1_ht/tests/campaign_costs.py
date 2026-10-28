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
from verify import Evidence, ROOT, file_sha256


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
    campaign = (
        "fixture-integrity", "checkpoint-repack", "parameters", "dequant", "tensor", "math",
        "dma", "kv", "csr-upload", "integration-matrix", "faults", "orphan-fault",
        "abort-states", "compatibility-matrix", "sensitivity", "synthesis-control",
        "synthesis", "kernel-default", "projection-default", "bf16-default",
        "vocabulary-default",
    )
    evidence.record["whole_campaign_cost_breakdown"] = [
        {"stage": name, "complete_stage_samples": stages.get(name, []),
         "status": "measured_historical" if name in stages else "no_complete_stage_measurement",
         "acceptance_evidence": False}
        for name in campaign]
    evidence.record["historical_complete_stage_lower_bound_seconds"] = sum(
        min(sample["seconds"] for sample in stages[name])
        for name in campaign if name in stages)
    evidence.record["cost_accounting_limits"] = (
        "The lower bound excludes every unmeasured campaign stage. Historical "
        "costs use their original harness/options, not a prediction of this revision. "
        "No missing, canceled or malformed execution is assigned zero cost or a pass.")
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
