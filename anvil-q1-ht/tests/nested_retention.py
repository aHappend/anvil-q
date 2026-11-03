#!/usr/bin/env python3
"""Observe the actual nested configuration-0/seed-17 AWQ evidence lifecycle.

Proposed supplemental command: python3 -B tests/nested_retention.py
This is a retention diagnostic, not storage repair or accelerator acceptance.
The ordinary full matrix and all mandatory checks remain unchanged. Timestamped
JSON observations go directly to stdout for independent shared-runtime retention.
Existing receipts and snapshots are only read; missing evidence is never recreated.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiments import integration_matrix
from verify import Evidence, ROOT, file_sha256, utc


class LifecycleObserver:
    def __init__(self, parent):
        self.lock = threading.Lock()
        self.targets = []
        self.rows = []
        self.failures = []
        self.stop = threading.Event()
        self.simulation_running_observed = False
        self.watch(parent, "parent")
        self.worker = threading.Thread(target=self.monitor, name="nested-evidence-observer")

    def watch(self, evidence, role):
        with self.lock:
            files = {
                evidence.folder / "sources" / name: digest
                for name, digest in evidence.record["source_sha256"].items()
            }
            directories = {ROOT, ROOT / "evidence", ROOT / "evidence/preparation",
                           evidence.folder, evidence.folder / "sources"}
            for path in files:
                directory = path.parent
                while directory != evidence.folder:
                    directories.add(directory)
                    directory = directory.parent
            target = {"evidence": evidence, "role": role, "files": files,
                      "identities": {}, "directories": {}, "command_states": {}}
            self.targets.append(target)
            for kind, paths, reader in (
                    ("directories", sorted(directories), self.directory_identity),
                    ("identities", sorted(files), self.file_identity)):
                for path in paths:
                    try:
                        target[kind][path] = reader(path)
                    except OSError as exc:
                        target[kind][path] = None
                        failure = {"phase": "baseline_capture", "path": self.relative(path),
                                   "error_type": type(exc).__name__, "errno": exc.errno,
                                   "os_error": exc.strerror}
                        self.failures.append(failure)
                        self.emit(failure)
            # Publish the full baseline once; periodic rows contain compact bindings
            # plus every discrepancy, keeping independently retained stdout bounded.
            self.emit({"phase": "baseline", "role": role,
                       "receipt": evidence.relative(evidence.folder / "receipt.json"),
                       "receipt_identity": list(evidence.receipt_identity),
                       "directories": {self.relative(p): v for p, v in
                                       target["directories"].items()},
                       "sources": {self.relative(p): {
                           "expected_sha256": files[p], "observed": identity}
                           for p, identity in target["identities"].items()}})
            self.observe_locked("baseline_validation")

    @staticmethod
    def relative(path):
        return str(path.relative_to(ROOT))

    @staticmethod
    def directory_identity(path):
        stat = path.stat()
        return [stat.st_dev, stat.st_ino]

    @staticmethod
    def file_identity(path):
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            digest = hashlib.sha256(stream.read()).hexdigest()
            after = os.fstat(stream.fileno())
            named = path.stat()
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        versions = [dict((field, getattr(stat, field)) for field in fields)
                    for stat in (before, after, named)]
        return {"sha256": digest, "metadata": versions[-1],
                "stable_read": versions[0] == versions[1] == versions[2]}

    def emit(self, row):
        row.update(event="nested_evidence_observation", observation_time=utc(),
                   acceptance_evidence=False, evidence_recreated=False)
        print(json.dumps(row, sort_keys=True), flush=True)
        self.rows.append(row)

    def observe_locked(self, phase):
        discrepancies = []
        targets = []
        for target in self.targets:
            evidence = target["evidence"]
            receipt = evidence.folder / "receipt.json"
            checks = [(path, "directory", expected) for path, expected in
                      target["directories"].items()]
            checks += [(path, "snapshot", expected) for path, expected in
                       target["identities"].items()]
            checks.append((receipt, "receipt", list(evidence.receipt_identity)))
            source_state = {}
            receipt_state = None
            for path, kind, expected in checks:
                try:
                    actual = (self.file_identity(path) if kind in ("snapshot", "receipt")
                              else self.directory_identity(path))
                    invalid = actual != expected
                    if kind == "snapshot":
                        source_state[self.relative(path)] = actual
                        invalid |= (not actual["stable_read"] or
                                    actual["sha256"] != target["files"][path])
                    elif kind == "receipt":
                        receipt_state = actual
                        metadata = actual["metadata"]
                        # Contents legitimately change as the owner updates progress.
                        invalid = [metadata["st_dev"], metadata["st_ino"]] != expected
                    if invalid:
                        discrepancies.append({"path": self.relative(path), "kind": kind,
                                              "expected": expected, "actual": actual})
                except OSError as exc:
                    discrepancies.append({
                        "path": self.relative(path), "kind": kind,
                        "error_type": type(exc).__name__, "errno": exc.errno,
                        "os_error": exc.strerror, "expected": expected})
            running = []
            for index, original in enumerate(list(evidence.record["commands"])):
                command = original.copy()
                state = tuple(command.get(key) for key in
                              ("pid", "end_time", "exit_code", "process_settled", "timed_out"))
                if target["command_states"].get(index) != state:
                    self.emit({"phase": "command_state", "role": target["role"],
                               "receipt": self.relative(receipt), "command": command})
                    target["command_states"][index] = state
                if "pid" in command and "end_time" not in command:
                    try:
                        os.kill(command["pid"], 0)
                    except ProcessLookupError:
                        continue
                    running.append({key: command[key] for key in ("label", "pid")})
                    if (target["role"] == "child" and command["label"].endswith("-simulation")
                            and "four-state-reset" not in command["label"]):
                        self.simulation_running_observed = True
            targets.append({
                "role": target["role"], "receipt": self.relative(receipt),
                "receipt_state": receipt_state,
                "source_count": len(source_state),
                "source_state_sha256": hashlib.sha256(
                    json.dumps(source_state, sort_keys=True).encode()).hexdigest(),
                "running_commands": running,
            })
        self.emit({"phase": phase, "targets": targets, "discrepancies": discrepancies})
        if discrepancies:
            self.failures.append({"phase": phase, "discrepancies": discrepancies})

    def observe(self, phase):
        with self.lock:
            self.observe_locked(phase)

    def monitor(self):
        while not self.stop.wait(2):
            try:
                self.observe("during_child_execution")
            except Exception as exc:
                # Preserve observer errors independently; they must fail the probe.
                with self.lock:
                    failure = {"phase": "observer_error",
                               "error_type": type(exc).__name__, "reason": str(exc)}
                    self.failures.append(failure)
                    self.emit(failure)
                return

    def lifecycle(self, phase, child):
        if phase == "after_child_creation":
            self.watch(child, "child")
        self.observe(phase)
        if self.failures:
            raise RuntimeError("nested evidence disappeared or changed; see stdout observations")

    def settle(self):
        self.stop.set()
        self.worker.join()


def validate_child(parent):
    row, = parent.record["integration_matrix"]
    if (row["configuration"], row["seed"], row["mode"], row["outcome"]) != (
            0, 17, "AWQ", "compared"):
        raise AssertionError("diagnostic did not complete the exact admitted nested case")
    receipt = ROOT / row["receipt"]
    child = json.loads(receipt.read_text())
    if child.get("outcome") != "probe_passed":
        raise AssertionError("nested child did not finalize successfully")
    commands = child["commands"]
    if (not commands or any(command.get("process_settled") is not True or
                            command.get("exit_code") != 0 or command.get("timed_out")
                            for command in commands)):
        raise AssertionError("nested commands lack successful process settlement")
    simulations = [command for command in commands
                   if command["label"].endswith("-simulation")]
    if not simulations or any(command["timeout_seconds"] < 3600 for command in simulations):
        raise AssertionError("nested simulation deadline is below the admitted minimum")
    for command in commands:
        for key in ("stdout", "stderr"):
            path = ROOT / command[key]
            if (file_sha256(path) != command[key + "_sha256"] or
                    path.stat().st_size != command[key + "_bytes"]):
                raise AssertionError(f"nested command log changed: {command[key]}")
    return {"receipt": row["receipt"], "receipt_sha256": file_sha256(receipt),
            "commands": commands, "compared_case": row}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    parent = Evidence("nested-retention", args.repair_of)
    observer = LifecycleObserver(parent)
    observer.worker.start()
    failure = None
    try:
        for tool, flags in (("python3", ["--version"]), ("iverilog", ["-V"]),
                            ("vvp", ["-V"])):
            if shutil.which(tool) is None:
                raise RuntimeError(f"required diagnostic tool unavailable: {tool}")
            parent.command([tool, *flags], tool + "-version")
        integration_matrix(parent, configurations=(0,), seeds=(17,), modes=("AWQ",),
                           lifecycle=observer.lifecycle)
        parent.record["nested_child"] = validate_child(parent)
        if not observer.simulation_running_observed:
            raise AssertionError("no live child simulation observation was retained")
    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        observer.settle()
    observer.observe("before_parent_finalization")
    parent.record["nested_retention"] = {
        "scope": "nested_lifecycle_only_not_storage_repair_or_accelerator_acceptance",
        "observations": observer.rows.copy(), "failures": observer.failures.copy(),
        "simulation_running_observed": observer.simulation_running_observed,
    }
    if observer.failures and failure is None:
        failure = "nested evidence retention discrepancies; see stdout observations"
    try:
        parent.finish("failed" if failure else "probe_passed",
                      failure or "Only the actual nested case and its evidence lifecycle completed.")
    finally:
        observer.observe("after_parent_finalization")
    if observer.failures:
        raise RuntimeError("nested evidence retention failed; no evidence was recreated")
    return 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
