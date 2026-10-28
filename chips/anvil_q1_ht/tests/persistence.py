"""Readable bounded persistence observation, never accelerator acceptance.

Run python3 -B tests/persistence.py to observe a bounded writer and its settled
output. After an actual runtime role handoff, the fresh Verifier runs
python3 -B tests/persistence.py --audit <project-relative-receipt>.
A later process alone does not establish that a role handoff occurred.
Observations reject file replacement or metadata changes during a read rather
than pairing contents from one file with another file's modification time.
Comparisons also require unchanged file identity across observations, not just
identical contents and a restorable modification timestamp.
Unavailable audit inputs retain the precise path and OS failure, without
reconstructing evidence or attributing historical removal.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify import Evidence, ROOT, SELECTORS, utc
from retention import project_file


MESSAGE = "Anvil-Q1-HT persistence observation; not accelerator acceptance"
PREDECESSOR = (
    "evidence/preparation/verifier-command-evidence-regression-"
    "20261028T043118Z-ff0c9200/receipt.json"
)


def observe(relative, phase):
    row = {"phase": phase, "observation_time": utc(), "path": relative}
    try:
        path = project_file(relative)
        with path.open(encoding="utf-8") as stream:
            before = os.fstat(stream.fileno())
            row["contents"] = stream.read()
            after = os.fstat(stream.fileno())
            named = path.stat()
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        versions = [dict((field, getattr(stat, field)) for field in fields)
                    for stat in (before, after, named)]
        row["read_versions"] = dict(zip(("before", "after", "named"), versions))
        row["mtime_ns"] = after.st_mtime_ns
        row["mtime_utc"] = datetime.datetime.fromtimestamp(
            after.st_mtime, datetime.timezone.utc).isoformat()
        row["outcome"] = ("readable" if versions[0] == versions[1] == versions[2]
                          else "changed_during_read")
    except OSError as exc:
        row.update(
            outcome="missing" if isinstance(exc, FileNotFoundError) else "unavailable",
            error_type=type(exc).__name__, errno=exc.errno, os_error=exc.strerror,
            evidence_recreated=False,
        )
    print(json.dumps(row), flush=True)
    return row


def writer(relative):
    path = ROOT / relative
    if path.is_absolute() and not path.resolve().is_relative_to(ROOT / "evidence/preparation"):
        raise ValueError("writer output must remain in preparation evidence")
    path.parent.mkdir(exist_ok=False)
    created = utc()
    pending = path.with_name(path.name + ".pending")
    with pending.open("x", encoding="utf-8") as stream:
        stream.write(MESSAGE + "\nCreation timestamp (UTC): " + created + "\n")
        stream.flush()
    # Publish only a closed, complete file; never replace an existing observation.
    path.hardlink_to(pending)
    pending.unlink()
    print(json.dumps({"event": "created", "path": relative,
                      "creation_time": created}), flush=True)
    time.sleep(5)
    print(json.dumps({"event": "writer_finished", "time": utc()}), flush=True)


def same_file(first, second):
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    identities = []
    for row in (first, second):
        if row["outcome"] != "readable":
            return False
        versions = row.get("read_versions", {})
        named = versions.get("named", {})
        if (any(field not in named for field in fields)
                or any(versions.get(phase) != named for phase in ("before", "after"))
                or row["mtime_ns"] != named["st_mtime_ns"]):
            return False
        identities.append(named)
    return (identities[0] == identities[1]
            and all(first[key] == second[key] for key in ("path", "contents", "mtime_ns")))


def run(evidence):
    relative = evidence.relative(evidence.folder / "observed/message.txt")
    observations = []
    failures = []

    def during_writer():
        try:
            deadline = time.monotonic() + 10
            while not (ROOT / relative).is_file():
                if time.monotonic() >= deadline:
                    raise TimeoutError("writer did not create its message")
                time.sleep(0.01)
            observations.append(observe(relative, "while_writer_running"))
        except Exception as exc:
            failures.append(f"{type(exc).__name__}: {exc}")

    observer = threading.Thread(target=during_writer)
    observer.start()
    try:
        output = evidence.command(
            ["python3", "-B", "tests/persistence.py", "--writer", relative],
            "bounded-writer", timeout=30)
    finally:
        observer.join(timeout=15)
        evidence.record["observations"].extend(observations)
        evidence.record["observer_errors"] = failures
        evidence.flush()
    if observer.is_alive() or failures or len(observations) != 1:
        raise AssertionError("bounded observer failed; inspect retained observations")
    command = evidence.record["commands"][-1]
    events = [json.loads(line) for line in output.splitlines()]
    if ([event["event"] for event in events] != ["created", "writer_finished"]
            or not command["process_settled"] or command["exit_code"] != 0):
        raise AssertionError("writer did not finish and settle successfully")
    if not (events[0]["creation_time"] <= observations[0]["observation_time"]
            < events[1]["time"]):
        raise AssertionError("first observation was not during bounded writer execution")
    settled = observe(relative, "after_writer_completion_and_settlement")
    evidence.record["observations"].append(settled)
    evidence.record["persistence"] = {
        "message_path": relative,
        "role_handoff_observed": False,
        "scope": "bounded_persistence_only_not_historical_cause_or_accelerator_acceptance",
    }
    evidence.flush()
    if not same_file(observations[0], settled):
        raise AssertionError("message disappeared or changed; original observations retained")
    if settled["contents"] != (
            MESSAGE + "\nCreation timestamp (UTC): " + events[0]["creation_time"] + "\n"):
        raise AssertionError("message differs from actual writer creation record")


def audit(evidence, receipt):
    evidence.record["predecessor_receipt"] = receipt
    evidence.record["role_boundary"] = "requires_independent_shared_runtime_confirmation"
    evidence.flush()
    try:
        receipt_bytes = project_file(receipt).read_bytes()
    except OSError as exc:
        evidence.record["observations"].append({
            "phase": "audit_prerequisite",
            "observation_time": utc(),
            "path": receipt,
            "outcome": "missing" if isinstance(exc, FileNotFoundError) else "unavailable",
            "error_type": type(exc).__name__,
            "errno": exc.errno,
            "os_error": exc.strerror,
            "evidence_recreated": False,
            "scope": "unavailable_input_not_historical_cause_or_storage_repair",
        })
        evidence.flush()
        raise
    previous = json.loads(receipt_bytes)
    if previous.get("probe") != "persistence-observation" or previous.get("outcome") != "probe_passed":
        raise ValueError("audit requires a completed bounded persistence observation")
    evidence.record["predecessor_receipt_sha256"] = hashlib.sha256(receipt_bytes).hexdigest()
    evidence.flush()
    validate_predecessor(previous, receipt)
    baseline = previous["observations"][-1]
    current = observe(previous["persistence"]["message_path"], "later_verifier_invocation")
    evidence.record["observations"].append(current)
    evidence.flush()
    if not same_file(baseline, current):
        raise AssertionError("later observation differs; predecessor remains untouched")


def validate_predecessor(previous, receipt):
    """Audit retained execution, not just a success-shaped receipt field."""
    if (previous.get("entry_argv") != ["python3", "-B", "tests/persistence.py"]
            or previous.get("cwd") != "."):
        raise AssertionError("predecessor invocation differs from the admitted observation command")
    folder = Path(receipt).parent
    observations = previous["observations"]
    if ([row["phase"] for row in observations] != [
            "while_writer_running", "after_writer_completion_and_settlement"]
            or not same_file(*observations)):
        raise AssertionError("predecessor lacks consistent running and settled observations")
    message = str(folder / "observed/message.txt")
    if previous["persistence"]["message_path"] != message or observations[-1]["path"] != message:
        raise AssertionError("predecessor message is outside its observation directory")
    if previous.get("observer_errors") != []:
        raise AssertionError("predecessor observer did not complete successfully")
    commands = previous["commands"]
    if ([row["label"] for row in commands] != ["python-version", "bounded-writer"]
            or any(row.get("exit_code") != 0 or row.get("timed_out") is not False
                   or row.get("process_settled") is not True
                   or row.get("cwd") != "." for row in commands)):
        raise AssertionError("predecessor commands did not finish and settle successfully")
    if commands[0]["argv"] != ["python3", "--version"]:
        raise AssertionError("predecessor tool-version command differs from the bounded protocol")
    writer_command = commands[-1]
    if writer_command["argv"] != [
            "python3", "-B", "tests/persistence.py", "--writer", message]:
        raise AssertionError("predecessor writer command differs from the bounded protocol")
    artifacts = {}
    if not previous["source_sha256"]:
        raise AssertionError("predecessor source bindings are missing")
    bindings = previous["source_sha256"]

    def matches_selector(relative, selector):
        path = Path(relative)
        return path.parent == Path(selector).parent and path.match(selector)

    for selector in SELECTORS:
        if not any(matches_selector(relative, selector) for relative in bindings):
            raise AssertionError(f"predecessor source selector is missing: {selector}")
    for relative, digest in previous["source_sha256"].items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("predecessor source binding must be project-relative")
        if not any(matches_selector(relative, selector) for selector in SELECTORS):
            raise ValueError(f"predecessor source binding is outside deliverable selectors: {relative}")
        artifacts[str(folder / "sources" / path)] = (digest, None)
    for command in commands:
        for key in ("stdout", "stderr"):
            path = Path(command[key])
            if path.parent != folder:
                raise ValueError("predecessor command log escapes its evidence directory")
            artifacts[str(path)] = (command[key + "_sha256"], command[key + "_bytes"])
    for relative, (digest, size) in artifacts.items():
        raw = project_file(relative).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest or (size is not None and len(raw) != size):
            raise AssertionError(f"predecessor artifact changed: {relative}")
    events = [json.loads(line) for line in
              project_file(writer_command["stdout"]).read_text().splitlines()]
    if ([row["event"] for row in events] != ["created", "writer_finished"]
            or events[0]["path"] != message
            or not (events[0]["creation_time"] <= observations[0]["observation_time"]
                    < events[1]["time"] <= observations[-1]["observation_time"])
            or observations[-1]["contents"] != (
                MESSAGE + "\nCreation timestamp (UTC): " + events[0]["creation_time"] + "\n")):
        raise AssertionError("predecessor raw writer trace disagrees with observations")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--writer")
    group.add_argument("--audit")
    args = parser.parse_args()
    if args.writer:
        relative = Path(args.writer)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("writer requires a project-relative path")
        writer(args.writer)
        return
    evidence = Evidence("persistence-audit" if args.audit else "persistence-observation",
                        repair_of=args.audit or PREDECESSOR)
    try:
        evidence.command(["python3", "--version"], "python-version")
        if args.audit:
            audit(evidence, args.audit)
        else:
            run(evidence)
        evidence.finish("probe_passed", "Bounded readable persistence observation only; "
                        "role-handoff confirmation and all accelerator checks remain outstanding.")
    except Exception as exc:
        evidence.finish("failed", f"{type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    main()
