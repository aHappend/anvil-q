#!/usr/bin/env python3
"""Read-only workflow discovery and retention diagnosis, not product acceptance.

Run python3 -B tests/platform_checks.py. A successful diagnostic invocation does
not authorize longer stages, alter patrol limits, or certify engineering gates.
"""

import argparse
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


def supervision_records(attempt=309):
    """Report recorded enforcement, not permission inferred from narrative text."""
    if attempt < 1:
        raise ValueError("attempt must be positive")
    folder = f".vulcan/engineering/run-0001/attempt-{attempt:04d}"
    paths = (
        ".vulcan/engineering/run-0001/state.json",
        folder + "/result.json",
        folder + "/patrol.json",
        folder + "/settled.json",
    )
    records = {name: json.loads((ROOT / name).read_text()) for name in paths}
    state, result, patrol, settled = (records[name] for name in paths)
    config = state["config"]
    logs = {}
    for name in ("stdout.log", "stderr.log"):
        relative = folder + "/" + name
        path = ROOT / relative
        logs[relative] = {"sha256": file_sha256(path), "bytes": path.stat().st_size}
    return {
        "attempt": attempt,
        "record_sha256": {name: file_sha256(ROOT / name) for name in paths},
        "raw_logs": logs,
        "runtime_state_keys": sorted(state),
        "runtime_config_keys": sorted(config),
        "recorded_role_limits": config.get("role_limits"),
        "failed_command": result["argv"],
        "failed_exit_code": result["exit_code"],
        "failed_duration_seconds": result["duration_s"],
        "recorded_interception": patrol["interception"],
        "process_scope_settled": settled["process_scope_settled"],
        "supervision_confirmation": "not_established",
        "scope": (
            "These records describe the existing execution and cancellation. "
            "Role limits are not an override of the observed patrol. No separately "
            "supervised-stage contract, effective patrol accommodation, original "
            "absolute-deadline reconciliation or durable-retention confirmation "
            "is established by this audit."
        ),
    }


def audit_supervision(attempt=309):
    evidence = Evidence(
        "supervision-record-audit",
        repair_of=(
            "evidence/preparation/"
            "verifier-workflow-platform-diagnosis-20261029T032417Z-dd670a9d/receipt.json"
        ),
    )
    try:
        evidence.command(["python3", "--version"], "python-version")
        text = evidence.command(
            ["python3", "-B", "tests/platform_checks.py",
             "--inspect-supervision-records", "--attempt", str(attempt)],
            "retained-supervision-records")
        observation = json.loads(text)
        evidence.record["diagnostic_input_sha256"] = {
            **observation["record_sha256"],
            **{name: row["sha256"] for name, row in observation["raw_logs"].items()},
        }
        evidence.record["observations"].append(observation)
        evidence.finish(
            "diagnostic_completed",
            "Audited actual retained enforcement records without CLI discovery, "
            "runtime changes or simulation. Stage accommodation remains "
            "unestablished; this is not a passing engineering check.")
        print(evidence.relative(evidence.folder / "receipt.json"))
        return 0
    except Exception as exc:
        evidence.finish("diagnostic_failed", f"{type(exc).__name__}: {exc}")
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--audit-supervision", action="store_true",
                      help="retain a read-only audit of actual enforcement records")
    mode.add_argument("--inspect-supervision-records", action="store_true",
                      help=argparse.SUPPRESS)
    parser.add_argument("--attempt", type=int, default=309,
                        help="retained attempt to inspect with --audit-supervision")
    args = parser.parse_args()
    if args.attempt < 1:
        parser.error("--attempt must be positive")
    if args.attempt != 309 and not (
            args.audit_supervision or args.inspect_supervision_records):
        parser.error("--attempt requires --audit-supervision")
    if args.inspect_supervision_records:
        print(json.dumps(supervision_records(args.attempt), indent=2))
        return 0
    if args.audit_supervision:
        return audit_supervision(args.attempt)
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
