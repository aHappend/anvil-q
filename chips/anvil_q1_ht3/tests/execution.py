"""Bounded, source-bound tool execution with immutable raw diagnostics."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


ROOT = Path(__file__).resolve().parent.parent
CHECK_SECONDS = 2700
INTERPRETED_SECONDS = 600


def relative(path, root=ROOT):
    return Path(path).resolve().relative_to(root.resolve()).as_posix()


def hashes(root=ROOT):
    return {relative(p, root): hashlib.sha256(p.read_bytes()).hexdigest()
            for pattern in ("rtl/*.sv", "design/*.md", "tests/*",
                            "anvil_q1_ht2_reference/rtl/*.sv")
            for p in sorted(root.glob(pattern)) if p.is_file()}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def clean_objects(directory):
    directory.resolve().relative_to(ROOT)
    if directory.name != "compile-obj":
        raise ValueError("cleanup is restricted to a named compile-obj directory")
    if directory.is_dir():
        for path in directory.iterdir():
            if path.is_file() and path.suffix in (".o", ".a", ".gch"):
                path.unlink()


def remaining():
    deadline = float(os.environ.get("HT3_CHECK_DEADLINE", time.time() + CHECK_SECONDS))
    return max(0.0, min(CHECK_SECONDS, deadline - time.time()))


def execute(argv, output, stem, version_argv, root=ROOT):
    stdout = output / f"{stem}.stdout.txt"
    stderr = output / f"{stem}.stderr.txt"
    receipt = output / f"{stem}.receipt.json"
    if any(p.exists() for p in (stdout, stderr, receipt)):
        raise FileExistsError(f"immutable execution output already exists: {stem}")
    limit = min(remaining(), INTERPRETED_SECONDS if Path(argv[0]).name == "vvp"
                else CHECK_SECONDS)
    record = dict(argv=argv, cwd="." if root == ROOT else relative(root),
                  start=timestamp(), source_sha256=hashes(root),
                  stdout=relative(stdout), stderr=relative(stderr),
                  timeout=limit, tool_version_argv=version_argv)
    try:
        version = subprocess.run(version_argv, cwd=root, capture_output=True,
                                 text=True, timeout=min(INTERPRETED_SECONDS, remaining()))
        record.update(tool_version_exit=version.returncode,
                      tool_version=version.stdout + version.stderr)
    except (OSError, subprocess.TimeoutExpired) as exc:
        record.update(tool_version_exit=None, tool_version_error=str(exc))
    start = time.monotonic()
    timed_out = False
    exit_code = None
    try:
        with stdout.open("x") as out, stderr.open("x") as err:
            if limit <= 0:
                timed_out = True
                err.write("Complete-check budget exhausted before launch.\n")
            else:
                process = subprocess.Popen(argv, cwd=root, stdout=out, stderr=err,
                                           start_new_session=True)
                end = start + min(limit, remaining())
                while True:
                    wait = end - time.monotonic()
                    if wait <= 0:
                        timed_out = True
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                        break
                    try:
                        exit_code = process.wait(timeout=min(30, wait))
                        break
                    except subprocess.TimeoutExpired:
                        print(f"PROGRESS {stem} elapsed_s={time.monotonic()-start:.0f}",
                              flush=True)
    except OSError as exc:
        record["launch_error"] = f"{type(exc).__name__}: {exc}"
        if not stdout.exists():
            stdout.write_text("")
        if not stderr.exists():
            stderr.write_text(record["launch_error"] + "\n")
    record.update(exit=exit_code, timed_out=timed_out, end=timestamp(),
                  duration_s=time.monotonic()-start,
                  artifact_sha256={relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in (stdout, stderr)})
    with receipt.open("x") as out:
        json.dump(record, out, indent=2)
        out.write("\n")
    if Path(argv[0]).parent.name == "compile-obj" and exit_code is not None:
        clean_objects(root / Path(argv[0]).parent)
    if timed_out or exit_code != 0:
        raise RuntimeError(f"{stem}: exit={exit_code}, timed_out={timed_out}; "
                           f"{relative(receipt)}")
    return stdout.read_text()
