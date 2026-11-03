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
DEFAULT_DEADLINE = time.time() + CHECK_SECONDS


class ExecutionFailure(RuntimeError):
    def __init__(self, message, record):
        super().__init__(message)
        self.timed_out = record["timed_out"]
        self.record = record


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
    deadline = float(os.environ.get("HT3_CHECK_DEADLINE", DEFAULT_DEADLINE))
    return max(0.0, min(CHECK_SECONDS, deadline - time.time()))


def nested_outcomes(directory):
    timed_out, unstarted = [], []
    for path in directory.rglob("*.receipt.json"):
        record = json.loads(path.read_text())
        launched = record.get("launched", record.get("exit") is not None
                              or record.get("timeout", 0) > 0)
        if not launched and record.get("budget_exhausted"):
            unstarted.append(relative(path))
        elif record.get("timed_out") and launched:
            timed_out.append(relative(path))
    return dict(nested_timed_out=bool(timed_out), budget_exhausted=bool(unstarted),
                timed_out_receipts=timed_out, unstarted_receipts=unstarted)


def failure_details(exc):
    if not isinstance(exc, ExecutionFailure):
        return dict(failure_kind=("numerical_or_protocol_assertion"
                                  if isinstance(exc, AssertionError)
                                  else "verification_or_input_failure"))
    record = exc.record
    launched = record.get("launched", record.get("exit") is not None
                          or record.get("timeout", 0) > 0)
    return dict(failure_kind=("execution_budget_unstarted" if not launched
                              else "execution_timeout" if exc.timed_out
                              else "nested_execution_budget" if (
                                  record.get("nested_timed_out")
                                  or record.get("budget_exhausted"))
                              else "simulation_or_tool_failure"),
                process_timed_out=bool(exc.timed_out and launched), launched=launched)


def execute(argv, output, stem, version_argv, root=ROOT):
    requested_argv = list(argv)
    if root == ROOT and argv[0].startswith("evidence/"):
        from campaign import artifact
        executable = artifact(ROOT/argv[0])
        argv = [relative(executable), *argv[1:]]
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
                  timeout=limit, tool_version_argv=version_argv, launched=False,
                  budget_exhausted=False)
    if argv != requested_argv:
        record["requested_argv"] = requested_argv
        record["executable_relocation"] = dict(
            original=requested_argv[0], restored=argv[0],
            sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
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
            limit = min(limit, remaining())
            if limit <= 5:
                record.update(timeout=0, settlement_timeout=limit, budget_exhausted=True)
                err.write("Complete-check execution budget exhausted before launch.\n")
            else:
                settlement_seconds = min(5, limit)
                execution_seconds = max(0, min(limit, remaining())-settlement_seconds)
                record.update(timeout=execution_seconds,
                              settlement_timeout=settlement_seconds)
                end = start + execution_seconds
                environment = dict(os.environ)
                environment["HT3_CHECK_DEADLINE"] = str(
                    time.time() + max(0, end-time.monotonic()))
                process = subprocess.Popen(argv, cwd=root, stdout=out, stderr=err,
                                           start_new_session=True, env=environment)
                record["launched"] = True
                previous_handler = signal.getsignal(signal.SIGTERM)
                ancestor_timeout = False

                def cancel_child(signum, frame):
                    nonlocal ancestor_timeout
                    ancestor_timeout = True
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGTERM)

                signal.signal(signal.SIGTERM, cancel_child)
                try:
                    while True:
                        wait = end - time.monotonic()
                        if wait <= 0 or ancestor_timeout:
                            timed_out = True
                            if process.poll() is None:
                                os.killpg(process.pid, signal.SIGTERM)
                            try:
                                exit_code = process.wait(timeout=settlement_seconds)
                            except subprocess.TimeoutExpired:
                                os.killpg(process.pid, signal.SIGKILL)
                                exit_code = process.wait()
                            break
                        try:
                            exit_code = process.wait(timeout=min(30, wait))
                            timed_out = ancestor_timeout
                            break
                        except subprocess.TimeoutExpired:
                            print(f"PROGRESS {stem} elapsed_s={time.monotonic()-start:.0f}",
                                  flush=True)
                finally:
                    signal.signal(signal.SIGTERM, previous_handler)
    except OSError as exc:
        record["launch_error"] = f"{type(exc).__name__}: {exc}"
        if not stdout.exists():
            stdout.write_text("")
        if not stderr.exists():
            stderr.write_text(record["launch_error"] + "\n")
    record.update(exit=exit_code, timed_out=timed_out,
                  process_timed_out=timed_out and record["launched"], end=timestamp(),
                  duration_s=time.monotonic()-start,
                  artifact_sha256={relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in (stdout, stderr)})
    if "--output" in argv:
        nested_directory = root/argv[argv.index("--output")+1]
        if nested_directory.is_dir():
            outcomes = nested_outcomes(nested_directory)
            outcomes["budget_exhausted"] |= record["budget_exhausted"]
            record.update(outcomes)
    with receipt.open("x") as out:
        json.dump(record, out, indent=2)
        out.write("\n")
    if Path(argv[0]).parent.name == "compile-obj" and exit_code is not None:
        clean_objects(root / Path(argv[0]).parent)
    if timed_out or exit_code != 0:
        raise ExecutionFailure(f"{stem}: exit={exit_code}, timed_out={timed_out}; "
                               f"{relative(receipt)}", record)
    return stdout.read_text()
