"""Bounded subprocess execution with immutable, source-bound project receipts."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATTERNS = ("rtl/*.sv", "design/*.md", "tests/*.py", "anvil_q1_ht_reference/rtl/*.sv")
DEADLINE = None


def set_budget(seconds):
    global DEADLINE
    DEADLINE = time.monotonic() + seconds


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bindings():
    return {
        str(path.relative_to(ROOT)): digest(path)
        for pattern in SOURCE_PATTERNS
        for path in sorted(ROOT.glob(pattern))
    }


def now():
    return datetime.now(timezone.utc).isoformat()


def fresh(stem, preparation=False):
    parent = ROOT / "evidence"
    if preparation:
        parent /= "preparation"
    name = f"{stem}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
    directory = parent / name
    directory.mkdir(parents=True, exist_ok=False)
    return directory


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT))


def write_json(path, data):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def execute(argv, directory, label, timeout=600, cwd=ROOT, inputs=()):
    """Every invocation gets its own fresh child directory and receipt."""
    if DEADLINE is not None:
        timeout = min(timeout, max(0.01, DEADLINE - time.monotonic()))
    run = directory / f"{label}-{uuid.uuid4().hex[:8]}"
    run.mkdir(exist_ok=False)
    started, monotonic = now(), time.monotonic()
    executable = shutil.which(argv[0])
    tool_version = {"available": executable is not None}
    version_argv = {
        "python3": ["python3", "--version"], "iverilog": ["iverilog", "-V"],
        "vvp": ["vvp", "-V"], "verilator": ["verilator", "--version"],
        "yosys": ["yosys", "-V"],
    }.get(Path(argv[0]).name)
    if version_argv and executable:
        with (run / "version.stdout.txt").open("w") as out, (run / "version.stderr.txt").open("w") as err:
            version = subprocess.run(version_argv, cwd=cwd, stdout=out, stderr=err, timeout=30, check=False)
        tool_version.update(argv=version_argv, exit_code=version.returncode,
                            stdout="version.stdout.txt", stderr="version.stderr.txt")
    timed_out = False
    launch_error = None
    with (run / "stdout.txt").open("w") as out, (run / "stderr.txt").open("w") as err:
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdout=out, stderr=err, start_new_session=True)
        except OSError as exc:
            launch_error = f"{type(exc).__name__}: {exc}"
            err.write(launch_error + "\n")
            code = 127
        else:
            deadline = time.monotonic() + timeout
            while True:
                try:
                    code = process.wait(timeout=min(30, max(0.01, deadline - time.monotonic())))
                    break
                except subprocess.TimeoutExpired:
                    if time.monotonic() >= deadline:
                        timed_out = True
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        code = 124
                        break
                    print(f"progress: {label} running", flush=True)
    receipt = {
        "schema_version": 1, "argv": [str(x) for x in argv],
        "cwd": relative(cwd), "start_time": started, "end_time": now(),
        "duration_s": time.monotonic() - monotonic, "timeout_s": timeout,
        "timed_out": timed_out, "exit_code": code, "launch_error": launch_error,
        "tool_version": tool_version, "source_sha256": bindings(),
        "input_sha256": {relative(p): digest(p) for p in inputs},
        "stdout": "stdout.txt", "stderr": "stderr.txt",
    }
    write_json(run / "receipt.json", receipt)
    return receipt, run


class ExecutionFailure(RuntimeError):
    def __init__(self, result):
        self.receipt, self.directory = result
        super().__init__(f"execution failed: {relative(self.directory / 'receipt.json')}")


def require_success(result):
    receipt, run = result
    if receipt["exit_code"] != 0:
        raise ExecutionFailure(result)
    return run
