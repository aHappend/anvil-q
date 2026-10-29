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
from verify import Evidence, digest


CASES = ("success", "write", "short-write", "file-fsync", "replace",
         "directory-fsync")
OLD = {"schema": 1, "status": "running", "marker": "previous-valid-receipt"}
NEW = {"schema": 1, "marker": "replacement-receipt", "payload": list(range(128))}


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
    return good


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=CASES)
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    exercise(args.case, args.directory)
