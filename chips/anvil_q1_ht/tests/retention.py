"""Bounded evidence-retention diagnostics, never product acceptance checks.

Run ``python3 tests/verify.py --probe retention`` before expensive recovery work.
After handoff, a fresh Verifier invocation can read the retained files with
``python3 tests/verify.py --probe retention-audit --retention-of <receipt>``.
The audit does not modify the earlier run or certify who removed missing files.
It records missing prerequisites and all observed artifact discrepancies before
failing; diagnosis also exits nonzero when artifacts or source bindings differ.
A later invocation alone does not establish a role handoff.
"""

import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
MISSING_PREDECESSORS = (
    "evidence/preparation/verifier-checkpoint-repack-20261028T034247Z-8a9fd3cd/receipt.json",
    "evidence/preparation/verifier-sensitivity-20261028T034303Z-f2bc7486/receipt.json",
    "evidence/preparation/verifier-retention-20261028T034734Z-7e929ab0/receipt.json",
    "evidence/preparation/verifier-mutation-final_logit_stall-20261028T035358Z-ff3d9921/receipt.json",
)


class RetentionFailure(AssertionError):
    def __init__(self, observation):
        self.observation = observation
        super().__init__("retention discrepancies: " +
                         json.dumps(observation["discrepancies"], sort_keys=True))


def project_file(relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"expected project-relative retention input: {relative}")
    resolved = (ROOT / path).resolve(strict=True)
    if not resolved.is_relative_to(ROOT / "evidence/preparation"):
        raise ValueError(f"retention input escapes preparation evidence: {relative}")
    return resolved


def identity(path):
    stat = path.stat()
    return {"device": stat.st_dev, "inode": stat.st_ino,
            "size": stat.st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def workspace_identity():
    directories = {}
    for relative in (".", "evidence", "evidence/preparation"):
        try:
            stat = (ROOT / relative).stat()
        except FileNotFoundError:
            directories[relative] = None
        else:
            directories[relative] = [stat.st_dev, stat.st_ino]
    return directories


def observe(baseline, phase):
    discrepancies = []
    for relative, expected in baseline["files"].items():
        try:
            actual = identity(project_file(relative))
        except FileNotFoundError:
            actual = None
        if actual != expected:
            discrepancies.append({"path": relative, "kind": "file",
                                  "expected": expected, "actual": actual})
    for relative, expected in baseline["directories"].items():
        try:
            stat = project_file(relative).stat()
            actual = [stat.st_dev, stat.st_ino]
        except FileNotFoundError:
            actual = None
        if actual != expected:
            discrepancies.append({"path": relative, "kind": "directory",
                                  "expected": expected, "actual": actual})
    for relative in baseline["live_files"]:
        try:
            present = project_file(relative).is_file()
        except FileNotFoundError:
            present = False
        if not present:
            discrepancies.append({"path": relative, "kind": "live_file",
                                  "expected": "present", "actual": None})
    if "workspace_directories" in baseline:
        actual_directories = workspace_identity()
        for relative, expected in baseline["workspace_directories"].items():
            actual = actual_directories[relative]
            if actual != expected:
                discrepancies.append({"path": relative, "kind": "workspace_directory",
                                      "expected": expected, "actual": actual})
    observation = {"phase": phase, "time_ns": time.time_ns(),
                   "files_compared": len(baseline["files"]),
                   "directories_compared": len(baseline["directories"]),
                   "live_files_observed": len(baseline["live_files"]),
                   "discrepancies": discrepancies}
    if discrepancies:
        raise RetentionFailure(observation)
    return observation


def run(evidence):
    child_prefix = f"{len(evidence.record['commands']):05d}-retention-child"
    baseline = {"files": {}, "directories": {},
                "workspace_directories": workspace_identity(), "live_files": [
        evidence.relative(evidence.folder / name)
        for name in ("receipt.json", child_prefix + "-stdout.log", child_prefix + "-stderr.log")
    ]}
    for relative in evidence.record["source_sha256"]:
        path = evidence.folder / "sources" / relative
        baseline["files"][evidence.relative(path)] = identity(path)
    for receipt in sorted((ROOT / "evidence/preparation").glob("*/receipt.json")):
        if receipt.parent != evidence.folder:
            for path in sorted(receipt.parent.rglob("*")):
                if path.is_file():
                    baseline["files"][evidence.relative(path)] = identity(
                        project_file(evidence.relative(path)))
    for path in (ROOT / "evidence/preparation", evidence.folder):
        stat = path.stat()
        baseline["directories"][evidence.relative(path)] = [stat.st_dev, stat.st_ino]
    saved = evidence.folder / "retention-baseline.json"
    saved.write_text(json.dumps(baseline, indent=2) + "\n")
    evidence.record["retention"] = {
        "baseline": evidence.relative(saved), "baseline_identity": identity(saved),
        "missing_predecessors": {name: (ROOT / name).exists() for name in MISSING_PREDECESSORS},
        "post_handoff_status": "not_observed_in_this_invocation",
        "scope": "storage_diagnostic_only_not_repaired_storage_or_product_acceptance",
    }
    evidence.flush()
    output = evidence.command(
        ["python3", "tests/retention.py", "--child", evidence.relative(saved)],
        "retention-child", timeout=60)
    observations = [json.loads(line) for line in output.splitlines()]
    if [row["phase"] for row in observations] != ["during_child_0", "during_child_1", "during_child_2"]:
        raise AssertionError("retention child did not complete all observations")
    observations.append(observe(baseline, "after_child_completion"))
    evidence.record["observations"].extend(observations)
    evidence.record["retention"]["settled_artifacts"] = {
        command[key]: identity(project_file(command[key]))
        for command in evidence.record["commands"] for key in ("stdout", "stderr")
    }
    evidence.flush()


def audit(evidence, receipt):
    try:
        previous_path = project_file(receipt)
    except FileNotFoundError:
        evidence.record["observations"].append({
            "phase": "audit_prerequisite", "time_ns": time.time_ns(),
            "earlier_receipt": receipt, "outcome": "missing",
            "retention_observed": False,
            "scope": "missing_prerequisite_not_deleting_actor_attribution",
        })
        evidence.flush()
        raise
    if previous_path == evidence.folder / "receipt.json":
        raise ValueError("retention audit requires an earlier receipt")
    previous = json.loads(previous_path.read_text())
    if previous.get("probe") != "retention" or previous.get("outcome") != "probe_passed":
        raise ValueError("earlier receipt is not a completed retention diagnostic")
    retention = previous["retention"]
    baseline_path = project_file(retention["baseline"])
    if identity(baseline_path) != retention["baseline_identity"]:
        raise AssertionError("retention baseline changed after completion")
    baseline = json.loads(baseline_path.read_text())
    try:
        observation = observe(baseline, "later_invocation")
    except RetentionFailure as exc:
        evidence.record["observations"].append({
            **exc.observation, "earlier_receipt": receipt,
        })
        evidence.flush()
        raise
    try:
        settled_observation = observe(
            {"files": retention["settled_artifacts"], "directories": {}, "live_files": []},
            "later_invocation_settled_artifacts")
    except RetentionFailure as exc:
        evidence.record["observations"].append({
            **exc.observation, "earlier_receipt": receipt,
        })
        evidence.flush()
        raise
    evidence.record["observations"].append({
        **observation, "earlier_receipt": receipt,
        "earlier_receipt_identity": identity(previous_path),
        "scope": "later_invocation_retention_only_role_boundary_requires_runtime_confirmation",
    })
    evidence.record["observations"].append(settled_observation)
    evidence.flush()


def diagnose(evidence, receipt):
    """Compare a retained failure across invocations without certifying recovery."""
    output = evidence.command(
        ["python3", "tests/retention.py", "--diagnose-child", receipt],
        "retention-diagnosis", timeout=60, expected_codes=(0, 1))
    observation = json.loads(output)
    if observation["scope"] != "diagnosis_only_not_storage_repair_or_acceptance":
        raise AssertionError("missing retention diagnosis scope")
    evidence.record["observations"].append(observation)
    evidence.flush()
    failed = (observation["outcome"] != "artifacts_match" or
              bool(observation["discrepancies"]) or
              bool(observation["source_discrepancies"]))
    expected_exit = 1 if failed else 0
    if evidence.record["commands"][-1]["exit_code"] != expected_exit:
        raise AssertionError("retention diagnosis exit disagrees with observation")
    if failed:
        raise AssertionError(
            "Retention diagnosis found missing or changed artifacts; "
            "see the retained observation and raw child logs. Storage repair "
            "and role-handoff confirmation remain unestablished.")


def missing_prerequisite(receipt, missing_path, kind):
    print(json.dumps({
        "phase": "diagnosis_prerequisite", "time_ns": time.time_ns(),
        "earlier_receipt": receipt, "outcome": "missing_prerequisite",
        "discrepancies": [{"path": missing_path, "kind": kind,
                           "expected": "present", "actual": None}],
        "source_discrepancies": [],
        "scope": "diagnosis_only_not_storage_repair_or_acceptance",
        "role_handoff_confirmation": "requires_shared_runtime_confirmation",
        "deleting_actor": "not_established",
    }), flush=True)
    return 1


def diagnose_child(receipt):
    try:
        previous_path = project_file(receipt)
        previous_identity = identity(previous_path)
        previous = json.loads(previous_path.read_text())
    except FileNotFoundError:
        return missing_prerequisite(receipt, receipt, "earlier_receipt")
    if previous.get("probe") != "retention" or previous.get("outcome") != "failed":
        raise ValueError("diagnosis requires an earlier failed retention receipt")
    baseline_relative = previous["retention"]["baseline"]
    try:
        baseline_path = project_file(baseline_relative)
        baseline_identity = identity(baseline_path)
        baseline = json.loads(baseline_path.read_text())
    except FileNotFoundError:
        return missing_prerequisite(receipt, baseline_relative, "retention_baseline")
    if baseline_identity != previous["retention"]["baseline_identity"]:
        raise AssertionError("failed retention baseline changed")
    try:
        observation = observe(baseline, "failed_run_later_invocation")
    except RetentionFailure as exc:
        observation = exc.observation
    sources = []
    for relative, expected in previous["source_sha256"].items():
        path = ROOT / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != expected:
            sources.append({"path": relative, "expected": expected, "actual": actual})
    print(json.dumps({
        **observation,
        "outcome": ("discrepancies_found" if observation["discrepancies"] or sources
                    else "artifacts_match"),
        "earlier_receipt": receipt,
        "earlier_receipt_identity": previous_identity,
        "baseline_identity": baseline_identity,
        "source_discrepancies": sources,
        "workspace_identity_now": workspace_identity(),
        "scope": "diagnosis_only_not_storage_repair_or_acceptance",
        "role_handoff_confirmation": "requires_shared_runtime_confirmation",
        "deleting_actor": "not_established",
    }), flush=True)
    return 1 if observation["discrepancies"] or sources else 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--diagnose-child":
        raise SystemExit(diagnose_child(sys.argv[2]))
    if len(sys.argv) != 3 or sys.argv[1] != "--child":
        raise SystemExit("use tests/verify.py --probe retention or retention-audit")
    baseline = json.loads(project_file(sys.argv[2]).read_text())
    for index in range(3):
        print(json.dumps(observe(baseline, f"during_child_{index}")), flush=True)
        time.sleep(1)
