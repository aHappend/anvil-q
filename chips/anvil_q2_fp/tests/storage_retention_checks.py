"""Bounded advisory storage/retention diagnostic; never an engineering pass."""

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run, audit_streams, now


SENTINEL = b"Anvil-Q2-FP exclusive retention sentinel\n" * 64


def publish(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def local_path(name):
    path = Path(name)
    assert not path.is_absolute() and ".." not in path.parts
    resolved = (ROOT / path).resolve()
    resolved.relative_to(ROOT / "evidence/preparation")
    return resolved


def child(action, name):
    path = local_path(name)
    if action == "inspect":
        rows = []
        for directory in (ROOT, ROOT / "evidence/preparation", path):
            stat = directory.stat()
            fs = os.statvfs(directory)
            rows.append(dict(
                path=str(directory.relative_to(ROOT)), uid=stat.st_uid,
                gid=stat.st_gid, mode=oct(stat.st_mode), device=stat.st_dev,
                writable=os.access(directory, os.W_OK),
                available_bytes=fs.f_bavail * fs.f_frsize,
                free_bytes=fs.f_bfree * fs.f_frsize,
                available_inodes=fs.f_favail, free_inodes=fs.f_ffree))
        print(json.dumps(dict(uid=os.getuid(), gid=os.getgid(), paths=rows), indent=2))
    elif action == "write":
        with path.open("xb") as stream:
            stream.write(SENTINEL)
            stream.flush()
            os.fsync(stream.fileno())
        print(json.dumps(dict(path=name, bytes=len(SENTINEL),
                              sha256=hashlib.sha256(SENTINEL).hexdigest())))
    elif action == "compare":
        actual = path.read_bytes()
        assert actual == SENTINEL, "separate-process sentinel byte mismatch"
        print(json.dumps(dict(path=name, compared_bytes=len(actual),
                              sha256=hashlib.sha256(actual).hexdigest())))
    else:
        data = path.read_bytes()
        receipt = json.loads(data)
        hashes, errors = audit_streams(receipt["commands"])
        assert not errors, f"unavailable raw streams: {errors}"
        assert hashes == receipt["raw_stream_sha256"], "raw-stream hash mismatch"
        sentinel = local_path(receipt["sentinel"])
        assert sentinel.read_bytes() == SENTINEL, "reopened sentinel byte mismatch"
        assert receipt["outcome"] == "passed-focused-only"
        print(json.dumps(dict(
            receipt=name, receipt_sha256=hashlib.sha256(data).hexdigest(),
            raw_streams_compared=len(hashes), sentinel_bytes_compared=len(SENTINEL))))


def execute():
    run = Run("storage-retention", root="evidence/preparation")
    limitations = []
    try:
        run.command(["python3", "--version"], "python-version")
        run.command(["python3", "tests/storage_retention_checks.py",
                     "--action", "inspect", "--path", run.relative(run.path)], "filesystem-stat")
        for tool, arguments in (
                ("df", ["-P", "-B1", "."]), ("df", ["-Pi", "."]),
                ("findmnt", ["--json", "-T", ".", "-o", "TARGET,SOURCE,FSTYPE,OPTIONS"])):
            label = "inodes" if arguments == ["-Pi", "."] else tool
            if shutil.which(tool):
                run.command([tool, "--version"], label + "-version")
                run.command([tool, *arguments], label)
            else:
                limitations.append(f"{tool} unavailable; no conclusion from this query")
        if shutil.which("quota"):
            run.command(["quota", "--version"], "quota-version", expected_codes=(0, 1))
            output = run.command(["quota", "-s"], "quota", expected_codes=(0, 1))
            limitations.append(
                "quota query retained; unsupported/empty output does not establish available quota")
        else:
            limitations.append("quota executable unavailable; applicable per-user quota is unknown")
        sentinel = run.relative(run.path / "sentinel.bin")
        run.receipt["sentinel"] = sentinel
        for action in ("write", "compare"):
            run.command(["python3", "tests/storage_retention_checks.py",
                         "--action", action, "--path", sentinel], "sentinel-" + action)
        run.finish("passed-focused-only", limitations=limitations,
                   scope="small exclusive write/fsync and separate-process read; not synthesis acceptance")
        receipt = run.path / "receipt.json"
        with receipt.open("rb") as stream:
            os.fsync(stream.fileno())
        command_count = len(run.receipt["commands"])
        output = run.command(["python3", "tests/storage_retention_checks.py",
                              "--action", "reopen", "--path", run.relative(receipt)],
                             "independent-reopen")
        commands = run.receipt["commands"][command_count:]
        hashes, errors = audit_streams(commands)
        assert not errors, errors
        publish(run.path / "reopen-receipt.json", dict(
            schema=1, acceptance_evidence=False, cwd=".",
            argv=run.receipt["argv"], python_version=sys.version,
            source_sha256=run.receipt["source_sha256"], commands=commands,
            raw_stream_sha256=hashes, outcome="passed-focused-only", ended_at=now(),
            independently_reopened=json.loads(output.read_text())))
        return 0
    except (OSError, AssertionError, RuntimeError, ValueError) as exc:
        detail = dict(failure=f"{type(exc).__name__}: {exc}")
        if isinstance(exc, OSError):
            detail.update(errno=exc.errno, filename=exc.filename, filename2=exc.filename2)
        if not (run.path / "receipt.json").exists():
            run.finish("failed", **detail)
        else:
            publish(run.path / "reopen-failure.json", dict(ended_at=now(), **detail))
        print(json.dumps(detail), file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("inspect", "write", "compare", "reopen"))
    parser.add_argument("--path")
    args = parser.parse_args()
    if args.action:
        try:
            child(args.action, args.path)
        except OSError as exc:
            print(json.dumps(dict(error=type(exc).__name__, errno=exc.errno,
                                  path=exc.filename, message=exc.strerror)), file=sys.stderr)
            raise SystemExit(1)
    else:
        raise SystemExit(execute())
