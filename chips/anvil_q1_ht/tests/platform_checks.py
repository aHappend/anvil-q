#!/usr/bin/env python3
"""Read-only workflow discovery and retention diagnosis, not product acceptance.

Run python3 -B tests/platform_checks.py. A successful diagnostic invocation does
not authorize longer stages, alter patrol limits, or certify engineering gates.
"""

import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify import Evidence, ROOT, file_sha256


PREDECESSOR = (
    "evidence/preparation/"
    "verifier-platform-recheck-20261029T010903Z-55e459ad/receipt.json"
)


def main():
    evidence = Evidence("workflow-platform-diagnosis", repair_of=PREDECESSOR)
    evidence.record["scope"] = "read_only_prerequisites_not_acceptance"
    evidence.flush()
    try:
        evidence.command(["python3", "--version"], "python-version")
        evidence.command(["vulcan", "hardware", "--version"], "runtime-version")
        evidence.command(["df", "-k", "."], "storage-capacity")
        evidence.command(
            ["vulcan", "hardware", "workflow", "status", "--help"],
            "workflow-status-interface")
        status = evidence.command(
            ["vulcan", "hardware", "workflow", "status", "--project", "."],
            "workflow-status", expected_codes=(0, 1, 2))
        evidence.command(
            ["vulcan", "hardware", "status", "--project", ".", "--run", "run-0001"],
            "legacy-run-status", expected_codes=(0, 1, 2))
        evidence.command(
            ["vulcan", "hardware", "doctor", "--project", "."],
            "project-doctor", expected_codes=(0, 1, 2))
        predecessor_path = ROOT / PREDECESSOR
        previous = json.loads(predecessor_path.read_text())
        differences = [
            {"path": relative, "previous": expected,
             "current": evidence.record["source_sha256"].get(relative)}
            for relative, expected in previous["source_sha256"].items()
            if evidence.record["source_sha256"].get(relative) != expected
        ]
        failure = ROOT / ".vulcan/engineering/run-0001/attempt-0309"
        retained = {
            name: json.loads((failure / name).read_text())
            for name in ("result.json", "patrol.json", "settled.json")
        }
        inputs = [predecessor_path] + [
            failure / name for name in
            ("result.json", "patrol.json", "settled.json", "stdout.log", "stderr.log")
        ]
        evidence.record["diagnostic_input_sha256"] = {
            evidence.relative(path): file_sha256(path) for path in inputs
        }
        storage = os.statvfs(ROOT)
        observation = {
            "retained_failure": retained,
            "predecessor_source_count": len(previous["source_sha256"]),
            "predecessor_source_differences": differences,
            "new_sources": sorted(set(evidence.record["source_sha256"]) -
                                  set(previous["source_sha256"])),
            "available_bytes": storage.f_bavail * storage.f_frsize,
            "storage_scope": "instantaneous_capacity_not_durable_retention_confirmation",
            "workflow_status_command_exit": next(
                row["exit_code"] for row in evidence.record["commands"]
                if row["label"] == "workflow-status"),
            "workflow_status_output_bytes": len(status.encode()),
            "supervision_confirmation": "not_established_by_this_diagnostic",
            "runtime_state_modified": False,
            "simulations_launched": False,
        }
        evidence.record["observations"].append(observation)
        evidence.flush()
        if differences:
            raise AssertionError("previously bound sources differ; inspect receipt")
        evidence.finish(
            "diagnostic_completed",
            "Read-only commands and source comparisons retained. Workflow discovery "
            "is distinct from legacy hardware run discovery. This diagnostic does "
            "not confirm stage supervision, patrol accommodation, durable capacity "
            "or accelerator acceptance.")
        return 0
    except Exception as exc:
        evidence.finish("diagnostic_failed", f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
