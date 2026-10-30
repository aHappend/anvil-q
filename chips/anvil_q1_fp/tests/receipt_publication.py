#!/usr/bin/env python3
"""Bounded synthetic publication failures; no RTL or collection execution."""

import argparse
from contextlib import ExitStack
import errno
import json
import os
from pathlib import Path
import stat
import sys
import threading
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify import Evidence, ROOT, digest, parallel_components


CASES = ("success", "write", "short-write", "file-fsync", "replace",
         "directory-fsync")
OLD = {"schema": 1, "status": "running", "marker": "previous-valid-receipt"}
NEW = {"schema": 1, "marker": "replacement-receipt", "payload": list(range(128))}
LIFECYCLE_CASES = ("pristine", "allocation", "initialization", "initial-publication",
                   "execution", "execution-spawn", "disappearance", "execution-disappearance",
                   "final-disappearance", "initialization-publication",
                   "execution-parent-publication")


def lifecycle(case):
    """Run real aggregation against fresh fixtures; retain moved bytes, never delete."""
    ev = Evidence("receipt-lifecycle-" + case)
    ev.receipt["scope"] = "synthetic lifecycle failure, not RTL acceptance"
    ev.receipt["source_failure_fixture"] = str(
        (ev.path / "missing-source-a").relative_to(ROOT))
    missing = ev.receipt["source_failure_fixture"]
    missing2 = str((ev.path / "missing-source-b").relative_to(ROOT))
    real_inventory = __import__("verify").source_inventory
    real_allocate = __import__("verify").tempfile.mkdtemp
    real_finish = Evidence._finish
    parent_failure_injected = False

    def fail_source():
        raise FileNotFoundError(errno.ENOENT, "injected source inventory failure",
                                missing, None, missing2)

    def allocate(*args, **kwargs):
        if case == "allocation":
            raise PermissionError(errno.EACCES, "injected allocation failure", missing)
        return real_allocate(*args, **kwargs)

    def finish(holder, status):
        nonlocal parent_failure_injected
        if (case == "execution-parent-publication" and holder is ev
                and not parent_failure_injected
                and any(a["name"] == "component_fixture" for a in holder.receipt["assertions"])):
            parent_failure_injected = True
            raise OSError(errno.ENOSPC, "injected parent publication", missing2)
        if holder is not ev:
            if case == "final-disappearance" and status == "passed":
                moved = ev.path / ("retained-child-" + holder.path.name.rsplit("-", 1)[-1])
                holder.path.rename(moved)
                ev.receipt["retained_moved_child"] = str(moved.relative_to(ROOT))
            if case == "initial-publication" and holder.phase == "initial-publication":
                raise OSError(errno.ENOSPC, "injected initial publication", missing)
            if case == "initialization-publication":
                raise OSError(errno.ENOSPC, "injected secondary publication", missing2)
        return real_finish(holder, status)

    def inventory():
        return fail_source() if case in ("initialization", "initialization-publication") else real_inventory()

    def fixture(child):
        child.assertion("fixture_pristine_assertion", True)
        if case == "execution-spawn":
            return child.run("missing-executable", [missing])
        if case in ("disappearance", "execution-disappearance"):
            moved = ev.path / ("retained-child-" + child.path.name.rsplit("-", 1)[-1])
            child.path.rename(moved)
            ev.receipt["retained_moved_child"] = str(moved.relative_to(ROOT))
        if case in ("execution", "execution-disappearance", "execution-parent-publication"):
            fail_source()
        return True

    with ExitStack() as stack:
        stack.enter_context(patch("verify.source_inventory", side_effect=inventory))
        stack.enter_context(patch("verify.tempfile.mkdtemp", side_effect=allocate))
        stack.enter_context(patch.object(Evidence, "_finish", finish))
        results = parallel_components(ev, [("fixture", fixture, (), {})])
    passed = all(results.values()) and all(a["passed"] for a in ev.receipt["assertions"])
    ev.finish("passed" if passed else "failed")
    print(json.dumps({"receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                      "status": ev.receipt["status"]}), flush=True)
    return 0 if passed else 1


def exercise(case, directory):
    directory = directory.resolve()
    directory.mkdir()
    holder = Evidence.__new__(Evidence)
    holder.lock = threading.RLock()
    holder.path = directory
    holder.receipt = OLD.copy()
    holder.finish("running")
    previous = (directory / "receipt.json").read_bytes()
    with (directory / "previous-receipt.json").open("xb") as stream:
        stream.write(previous)
    holder.receipt = NEW.copy()
    events = []
    real_fdopen, real_fsync, real_replace = os.fdopen, os.fsync, os.replace

    def failure(operation):
        print(json.dumps({"injected_failure": operation, "events": events}),
              file=sys.stderr, flush=True)
        raise OSError(errno.ENOSPC, "injected receipt publication " + operation)

    class BrokenWriter:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, text):
            events.append("write")
            count = self.stream.write(text[:len(text) // 2])
            self.stream.flush()
            if case == "short-write":
                print("injected short receipt write", file=sys.stderr, flush=True)
                return count
            failure("write")

    def fdopen(fd, *args, **kwargs):
        stream = real_fdopen(fd, *args, **kwargs)
        return BrokenWriter(stream) if case in ("write", "short-write") else stream

    def fsync(fd):
        kind = ("directory-fsync" if stat.S_ISDIR(os.fstat(fd).st_mode)
                else "file-fsync")
        events.append(kind)
        if case == kind:
            failure(kind)
        return real_fsync(fd)

    def replace(source, target):
        events.append("replace")
        source, target = Path(source), Path(target)
        assert source.parent == target.parent == directory
        assert source != target and source.stat().st_ino != target.stat().st_ino
        assert target.read_bytes() == previous
        staged = json.loads(source.read_text())
        assert staged["marker"] == NEW["marker"] and staged["status"] == "passed"
        assert events == ["file-fsync", "replace"]
        if case == "replace":
            failure("replace")
        return real_replace(source, target)

    with ExitStack() as stack:
        stack.enter_context(patch("verify.os.fdopen", side_effect=fdopen))
        stack.enter_context(patch("verify.os.fsync", side_effect=fsync))
        stack.enter_context(patch("verify.os.replace", side_effect=replace))
        holder.finish("passed")
    assert case == "success", "injected publication failure was swallowed"
    assert events == ["file-fsync", "replace", "directory-fsync"]
    print(json.dumps({"events": events, "published": True}))


def check(root, ev):
    version_ok = ev.run("publication-python-version",
                        [sys.executable, "--version"], timeout=3600)
    good = ev.assertion("publication_python_version", version_ok)
    ev.receipt["scope"] = (
        "Synthetic receipt-publication regression only; no engineering acceptance")
    for case in CASES:
        directory = ev.path / ("fixture-" + case)
        label = "publication-" + case
        succeeded = ev.run(
            label, [sys.executable, "tests/receipt_publication.py",
                    "--case", case, "--directory", str(directory.relative_to(root))],
            timeout=3600)
        record = ev.receipt["records"][-1]
        installed = directory / "receipt.json"
        previous = directory / "previous-receipt.json"
        if not ev.assertion("publication_artifacts_" + case,
                            installed.is_file() and previous.is_file(),
                            child_exit_code=record["exit_code"]):
            good = False
            continue
        observed = json.loads(installed.read_text())
        after_replace = case in ("success", "directory-fsync")
        expected = NEW if after_replace else OLD
        correct_content = all(observed.get(key) == value
                              for key, value in expected.items())
        correct_content = correct_content and observed["status"] == (
            "passed" if after_replace else "running")
        previous_intact = installed.read_bytes() == previous.read_bytes()
        correct_content = correct_content and (after_replace or previous_intact)
        stderr = (root / record["stderr"]).read_text()
        exit_ok = (succeeded and record["exit_code"] == 0 if case == "success"
                   else not succeeded and record["exit_code"] == 1
                   and ("injected receipt publication " + case in stderr
                        or case == "short-write"
                        and "incomplete receipt write" in stderr))
        temporaries = sorted(directory.glob(".receipt-*.tmp"))
        temp_ok = len(temporaries) == (0 if after_replace else 1)
        good = ev.assertion(
            "publication_" + case,
            exit_ok and not record["timed_out"] and correct_content and temp_ok,
            expected_child_failure=case != "success",
            installed_receipt=str(installed.relative_to(root)),
            installed_sha256=digest(installed),
            installed_parseable=True, content_matches=correct_content,
            previous_bytes_intact=previous_intact,
            retained_temporaries=[str(p.relative_to(root)) for p in temporaries],
            durability_claimed=False if case == "directory-fsync" else None,
        ) and good
        ev.receipt.setdefault("data_sha256", {}).update({
            str(p.relative_to(root)): digest(p)
            for p in [installed, previous, *temporaries]
        })
    for case in LIFECYCLE_CASES:
        label = "lifecycle-" + case
        succeeded = ev.run(
            label, [sys.executable, "tests/receipt_publication.py", "--lifecycle", case],
            timeout=3600)
        record = ev.receipt["records"][-1]
        result = json.loads((root / record["stdout"]).read_text())
        path = root / result["receipt"]
        receipt = json.loads(path.read_text())
        row = receipt["shards"][0]
        assertion = next(a for a in receipt["assertions"] if a["name"] == "component_fixture")
        diagnostics = assertion["diagnostics"]
        expected = case == "pristine"
        correct = (succeeded == expected and record["exit_code"] == (0 if expected else 1)
                   and not record["timed_out"] and assertion["passed"] == expected
                   and row["status"] == ("completed" if expected else "failed")
                   and row["passed"] == expected
                   and receipt["shard_counts"]["failed"] == (0 if expected else 1)
                   and receipt["status"] == ("passed" if expected else "failed"))
        if not expected:
            correct = correct and bool(diagnostics) and row["diagnostics"] == diagnostics
            correct = correct and all(
                d["traceback"].startswith("Traceback") and d["phase"]
                and "filename" in d and "filename2" in d
                and "allocated_child_path" in d for d in diagnostics)
            primary = diagnostics[0]
            expected_phase = {"allocation": "allocation", "initialization": "initialization",
                              "initial-publication": "initial-publication",
                              "initialization-publication": "initialization",
                              "final-disappearance": "final-publication",
                              "disappearance": "profile-publication"}.get(case, "execution")
            correct = correct and primary["phase"] == expected_phase
            correct = correct and primary["errno"] == (
                errno.EACCES if case == "allocation" else
                errno.ENOSPC if case == "initial-publication" else errno.ENOENT)
            correct = correct and ((primary["allocated_child_path"] is None)
                                   == (case == "allocation"))
            if case not in ("allocation", "initial-publication", "disappearance",
                            "final-disappearance"):
                correct = correct and primary["filename"] == receipt["source_failure_fixture"]
                correct = correct and (primary["filename2"] is None if case == "execution-spawn"
                                       else primary["filename2"].endswith("missing-source-b"))
            if case in ("disappearance", "execution-disappearance", "final-disappearance"):
                correct = correct and assertion["child_receipt"] is None
                correct = correct and (root / receipt["retained_moved_child"]).is_dir()
                correct = correct and any(d["phase"] == "final-publication" for d in diagnostics)
            if case == "initialization-publication":
                correct = correct and len(diagnostics) == 2
                correct = correct and diagnostics[1]["errno"] == errno.ENOSPC
            if case == "execution-parent-publication":
                correct = correct and diagnostics[-1]["phase"] == "parent-publication"
                correct = correct and diagnostics[-1]["errno"] == errno.ENOSPC
            stderr = (root / record["stderr"]).read_text()
            correct = correct and (primary == json.loads(stderr.splitlines()[0])["diagnostics"][0])
        good = ev.assertion("lifecycle_" + case, correct, expected_child_failure=not expected,
                            child_receipt=result["receipt"], child_exit_code=record["exit_code"],
                            diagnostics=diagnostics) and good
        ev.receipt.setdefault("data_sha256", {})[result["receipt"]] = digest(path)
    return good


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--case", choices=CASES)
    group.add_argument("--lifecycle", choices=LIFECYCLE_CASES)
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    if args.lifecycle:
        sys.exit(lifecycle(args.lifecycle))
    if args.directory is None:
        parser.error("--case requires --directory")
    exercise(args.case, args.directory)
