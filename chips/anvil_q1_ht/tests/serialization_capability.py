#!/usr/bin/env python3
"""Capability-only probe; never executes or certifies a segmented campaign.

Reproduce with python3 -B tests/serialization_capability.py. The existing
Coordinator/Reviewer append-only check interface is the scheduling boundary.
Help inspection is read-only and does not schedule checks or change budgets.
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiments import top_probe
from verify import Evidence, file_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of", help="Project-relative predecessor receipt, retained unchanged")
    args = parser.parse_args()
    evidence = Evidence("serialization-capability", repair_of=args.repair_of)
    try:
        evidence.record["scheduling_boundary"] = {
            "interface": "Coordinator-proposed, independently admitted execution.checks additions",
            "basis": "Caller-supplied admitted check_extensions and Verifier checks response protocol",
            "separately_bounded_commands_supported_by_contract": True,
            "new_segment_commands_admitted": False,
            "dynamic_scheduler_or_campaign_restoration_demonstrated": False,
            "runtime_state_modified": False,
            "permission": (
                "Only bounded preparation here. Return implemented commands for append-only "
                "admission before a segmented campaign; never invoke workflow run recursively."),
        }
        evidence.flush()
        for label, argv in (
            ("runtime-version", ["vulcan", "hardware", "--version"]),
            ("workflow-run-help", ["vulcan", "hardware", "workflow", "run", "--help"]),
            ("workflow-resume-help", ["vulcan", "hardware", "workflow", "resume", "--help"]),
            ("simulator-version", ["verilator", "--version"]),
            ("compiler-version", ["g++", "--version"]),
        ):
            evidence.command(argv, label)

        captured = []

        def capture(name, bench, **options):
            if options.get("simulator") == "verilator":
                captured.append((name, bench, options))

        # Generate, but do not execute or shorten, the existing independent
        # matrix stimulus, expected logits, two clocks and DDR model.
        evidence.simulate = capture
        top_probe(evidence, "AWQ", 17, config=0)
        if len(captured) != 1:
            raise RuntimeError("expected exactly one actual compiled integration harness")
        name, bench, options = captured[0]
        folder = evidence.folder / "actual-harness"
        folder.mkdir(exist_ok=False)
        tb = folder / "tb.sv"
        tb.write_text(bench)
        sources = sorted((evidence.folder / "sources/rtl").glob("*.sv"))
        evidence.record["serialization_trial"] = {
            "harness": evidence.relative(tb),
            "harness_sha256": file_sha256(tb),
            "original_simulation_name": name,
            "original_runtime_args": list(options["runtime_args"]),
            "inputs": {evidence.relative(path): file_sha256(path) for path in sources},
            "scope": "Actual unchanged timed integration harness save/restore build capability",
            "state_restoration_executed": False,
            "functional_comparisons_executed": 0,
            "parity_demonstrated": False,
        }
        evidence.flush()
        text = evidence.command(
            ["verilator", "--cc", "--build", "-j", "2", "--timing", "--savable",
             "--assert", "-Wno-fatal",
             "--top-module", "tb", "--Mdir", evidence.relative(folder / "compiled"),
             *[evidence.relative(path) for path in sources], evidence.relative(tb)],
            "actual-harness-timing-savable", expected_codes=(0, 1, 2))
        command = evidence.record["commands"][-1]
        evidence.record["serialization_trial"]["translation_exit_code"] = command["exit_code"]
        evidence.record["serialization_trial"]["translation_stdout_sha256"] = command["stdout_sha256"]
        evidence.record["serialization_trial"]["translation_stderr_sha256"] = command["stderr_sha256"]
        if command["exit_code"] != 0:
            reason = (
                "Actual harness serialization build failed; inspect retained diagnostics. "
                "No save/restore, continuation parity or invalid-segment rejection was "
                "demonstrated. Segmented execution is not adoptable.")
            if "VlDelayScheduler" in text and "operator" in text:
                reason += " Compiler diagnostics identify unsupported delay-scheduler serialization."
            evidence.finish("capability_unavailable", reason)
            return 1
        evidence.finish(
            "translation_only_not_restoration",
            "Translation succeeded, but state restoration and uninterrupted-versus-restored parity "
            "remain unproven. No segmented campaign or acceptance is authorized.")
        return 1
    except Exception as exc:
        evidence.finish("capability_probe_failed", f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
