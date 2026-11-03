"""Project-local fresh evidence, raw logs, source bindings and tool execution."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
import sys
import os
import threading


ROOT = Path(__file__).resolve().parents[1]
CHECK_BUDGET_S = 2700
COMMAND_BUDGET_S = 600
DEADLINE_ENV = "ANVIL_L1_MONOTONIC_DEADLINE"
MAX_TOOL_WORKERS = 6


def timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT))


def sources():
    paths = []
    for pattern in ("rtl/*.sv", "tests/*.py", "anvil_q3_reference/rtl/*.sv",
                    "design/SPEC.md", "design/ARCHITECTURE.md"):
        paths.extend(sorted(ROOT.glob(pattern)))
    return {relative(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


class Evidence:
    def __init__(self, suite, preparation=False, repair_of=None):
        start = time.monotonic()
        self.deadline = min(start + CHECK_BUDGET_S,
                            float(os.environ.get(DEADLINE_ENV, start + CHECK_BUDGET_S)))
        self._simulators = {}
        self._tool_slots = threading.BoundedSemaphore(MAX_TOOL_WORKERS)
        self._lock = threading.RLock()
        self._build_locks = {}
        self._integration_runs = {}
        self._integration_locks = {}
        self._last_heartbeat = start
        base = ROOT / "evidence" / ("preparation" if preparation else "")
        self.path = base / f"{suite}-{timestamp()}"
        self.path.mkdir(parents=True, exist_ok=False)
        self.record = {
            "schema": 1, "suite": suite, "cwd": ".", "started_at": timestamp(),
            "argv": ["python3", *sys.argv],
            "sources": sources(), "commands": [], "repair_of": repair_of,
            "check_budget_s": CHECK_BUDGET_S,
        }
        self.write()

    def write(self):
        with self._lock:
            (self.path / "receipt.json").write_text(json.dumps(self.record, indent=2) + "\n")

    def scope(self, name):
        self.ensure_budget()
        return EvidenceScope(self, name)

    def ensure_budget(self):
        now = time.monotonic()
        if now >= self.deadline:
            raise TimeoutError("Whole-check 2700-second budget exhausted")
        with self._lock:
            if now - self._last_heartbeat >= 30:
                print(f"PREPARING suite={self.record['suite']} remaining_s={int(self.deadline - now)}",
                      flush=True)
                self._last_heartbeat = now

    def run(self, argv, cwd=None, timeout=COMMAND_BUDGET_S, expect_failure=False):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0 or not self._tool_slots.acquire(timeout=max(0, remaining)):
            raise TimeoutError("Whole-check 2700-second budget exhausted waiting for a tool slot")
        try:
            return self._run(argv, cwd, timeout, expect_failure)
        finally:
            self._tool_slots.release()

    def _run(self, argv, cwd=None, timeout=COMMAND_BUDGET_S, expect_failure=False):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Whole-check 2700-second budget exhausted")
        timeout = min(timeout, COMMAND_BUDGET_S, remaining)
        directory = Path(cwd or ROOT)
        with self._lock:
            number = len(self.record["commands"])
            stdout = self.path / f"command-{number:03d}.stdout.txt"
            stderr = self.path / f"command-{number:03d}.stderr.txt"
            command = {
                "argv": [str(arg) for arg in argv], "cwd": relative(directory),
                "started_at": timestamp(), "timeout_s": timeout,
                "stdout": relative(stdout), "stderr": relative(stderr), "timed_out": False,
            }
            self.record["commands"].append(command)
            self.write()
        start = time.monotonic()
        try:
            with stdout.open("w") as out, stderr.open("w") as err:
                environment = dict(os.environ, **{DEADLINE_ENV: str(self.deadline)})
                process = subprocess.Popen(command["argv"], cwd=directory, stdout=out, stderr=err,
                                           env=environment)
                try:
                    deadline = start + timeout
                    while True:
                        try:
                            command["exit_code"] = process.wait(timeout=min(30, max(0.001, deadline - time.monotonic())))
                            break
                        except subprocess.TimeoutExpired:
                            if time.monotonic() >= deadline:
                                raise
                            print(f"RUNNING {argv[0]} log={relative(stdout)} elapsed_s={int(time.monotonic() - start)}",
                                  flush=True)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    command["timed_out"] = True
                    command["exit_code"] = process.returncode
        except OSError as error:
            command["launch_error"] = str(error)
            raise
        finally:
            with self._lock:
                command["ended_at"] = timestamp()
                command["elapsed_s"] = time.monotonic() - start
                self.write()
        if command["timed_out"] or ((command["exit_code"] == 0) == expect_failure):
            raise AssertionError(f"Tool execution failed: {relative(stdout)}, {relative(stderr)}")
        return stdout

    def versions(self, tools):
        for argv in tools:
            output = self.run(argv)
            self.record.setdefault("tool_versions", []).append({
                "argv": argv, "stdout": relative(output),
                "stderr": self.record["commands"][-1]["stderr"],
            })
        self.write()

    def finish(self, status, **details):
        if status == "passed" and time.monotonic() > self.deadline:
            raise TimeoutError("Whole-check 2700-second budget exhausted")
        generated = {relative(path): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in self.path.rglob("*")
                     if path.is_file() and (path.suffix in (".sv", ".ys") or path.name == "vectors.txt")}
        if status == "passed":
            self.ensure_budget()
        self.record.update(status=status, ended_at=timestamp(), generated_inputs=generated, **details)
        self.write()


class EvidenceScope:
    """Namespaced fixtures share the enclosing immutable execution ledger."""

    def __init__(self, parent, name):
        self.path = parent.path / name
        self.path.mkdir()
        self.run = parent.run
        self.ensure_budget = parent.ensure_budget
        self.deadline = parent.deadline
        self._lock = parent._lock
        self._simulators = parent._simulators
        self._build_locks = parent._build_locks
        self._integration_runs = parent._integration_runs
        self._integration_locks = parent._integration_locks
        self.scope = lambda child: EvidenceScope(self, child)


def icarus(evidence, name, testbench, rtl, files=None):
    evidence.ensure_budget()
    directory = evidence.path / name
    directory.mkdir()
    (directory / "tb.sv").write_text(testbench)
    for filename, text in (files or {}).items():
        (directory / filename).write_text(text)
    evidence.run(["iverilog", "-g2012", "-Wall", "-s", "tb", "-o",
                  relative(directory / "sim.vvp"), *rtl, relative(directory / "tb.sv")])
    return evidence.run(["vvp", "sim.vvp"], cwd=directory, timeout=600)


def verilator(evidence, name, testbench, rtl, files=None):
    evidence.ensure_budget()
    directory = evidence.path / name
    directory.mkdir()
    # Icarus supplies the event-region startup check; Verilator has no #0 region.
    (directory / "tb.sv").write_text(testbench.replace("#0; reset_check;", "#1; reset_check;").replace(
        "reset_sample<=1; @(posedge reset_sample); reset_check;", "#1; reset_check;"))
    for filename, text in (files or {}).items():
        (directory / filename).write_text(text)
    objects = directory / "compile-obj"
    try:
        evidence.run(["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module", "tb",
                      "-j", "2", "--Mdir", relative(objects), "-o", "sim",
                      *rtl, relative(directory / "tb.sv")])
        output = evidence.run(["./compile-obj/sim"], cwd=directory)
    finally:
        for pattern in ("*.o", "*.a", "*.gch"):
            for path in objects.glob(pattern):
                path.unlink()
    return output


def compiled(evidence, name, testbench, rtl):
    """Build once per elaboration; each fixture still runs in a fresh process."""
    evidence.ensure_budget()
    identity = hashlib.sha256((testbench + "\n" + "\n".join(rtl)).encode()).hexdigest()
    with evidence._lock:
        lock = evidence._build_locks.setdefault(identity, threading.Lock())
    with lock:
        return _compile(evidence, name, testbench, rtl, identity)


def _compile(evidence, name, testbench, rtl, identity):
    cache = evidence._simulators
    if identity in cache:
        return cache[identity]
    directory = evidence.path / f"build-{name}-{identity[:12]}"
    directory.mkdir()
    (directory / "tb.sv").write_text(testbench.replace("#0; reset_check;", "#1; reset_check;").replace(
        "reset_sample<=1; @(posedge reset_sample); reset_check;", "#1; reset_check;"))
    objects = directory / "compile-obj"
    try:
        evidence.run(["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module", "tb",
                      "-j", "2", "--Mdir", relative(objects), "-o", "sim", *rtl,
                      relative(directory / "tb.sv")])
    finally:
        for pattern in ("*.o", "*.a", "*.gch"):
            for path in objects.glob(pattern):
                path.unlink()
    binary = objects / "sim"
    cache[identity] = binary
    evidence._simulators = cache
    return binary


def run_compiled(evidence, binary, name, files):
    evidence.ensure_budget()
    directory = evidence.path / name
    directory.mkdir()
    for filename, text in files.items():
        (directory / filename).write_text(text)
    argv = os.path.relpath(binary, directory)
    if not argv.startswith("."):
        argv = "./" + argv
    return evidence.run([argv], cwd=directory)
