"""Project-local fresh evidence, raw logs, source bindings and tool execution."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
import sys
import os


ROOT = Path(__file__).resolve().parents[1]


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
        base = ROOT / "evidence" / ("preparation" if preparation else "")
        self.path = base / f"{suite}-{timestamp()}"
        self.path.mkdir(parents=True, exist_ok=False)
        self.record = {
            "schema": 1, "suite": suite, "cwd": ".", "started_at": timestamp(),
            "argv": ["python3", *sys.argv],
            "sources": sources(), "commands": [], "repair_of": repair_of,
        }
        self.write()

    def write(self):
        (self.path / "receipt.json").write_text(json.dumps(self.record, indent=2) + "\n")

    def run(self, argv, cwd=None, timeout=3600, expect_failure=False):
        directory = Path(cwd or ROOT)
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
                process = subprocess.Popen(command["argv"], cwd=directory, stdout=out, stderr=err)
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
        generated = {relative(path): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in self.path.rglob("*")
                     if path.is_file() and (path.suffix in (".sv", ".ys") or path.name == "vectors.txt")}
        self.record.update(status=status, ended_at=timestamp(), generated_inputs=generated, **details)
        self.write()


def icarus(evidence, name, testbench, rtl, files=None):
    directory = evidence.path / name
    directory.mkdir()
    (directory / "tb.sv").write_text(testbench)
    for filename, text in (files or {}).items():
        (directory / filename).write_text(text)
    evidence.run(["iverilog", "-g2012", "-Wall", "-s", "tb", "-o",
                  relative(directory / "sim.vvp"), *rtl, relative(directory / "tb.sv")])
    return evidence.run(["vvp", "sim.vvp"], cwd=directory, timeout=600)


def verilator(evidence, name, testbench, rtl, files=None):
    directory = evidence.path / name
    directory.mkdir()
    # Icarus supplies the event-region startup check; Verilator has no #0 region.
    (directory / "tb.sv").write_text(testbench.replace("#0; reset_check;", "#1; reset_check;").replace(
        "reset_sample<=1; @(posedge reset_sample); reset_check;", "#1; reset_check;"))
    for filename, text in (files or {}).items():
        (directory / filename).write_text(text)
    objects = directory / "compile-obj"
    evidence.run(["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module", "tb",
                  "-j", "2", "--Mdir", relative(objects), "-o", "sim",
                  *rtl, relative(directory / "tb.sv")])
    output = evidence.run(["./compile-obj/sim"], cwd=directory)
    for pattern in ("*.o", "*.a", "*.gch"):
        for path in objects.glob(pattern):
            path.unlink()
    return output


def compiled(evidence, name, testbench, rtl):
    """Build once per elaboration; each fixture still runs in a fresh process."""
    cache = getattr(evidence, "_simulators", {})
    identity = hashlib.sha256((testbench + "\n" + "\n".join(rtl)).encode()).hexdigest()
    if identity in cache:
        return cache[identity]
    directory = evidence.path / f"build-{name}-{identity[:12]}"
    directory.mkdir()
    (directory / "tb.sv").write_text(testbench.replace("#0; reset_check;", "#1; reset_check;").replace(
        "reset_sample<=1; @(posedge reset_sample); reset_check;", "#1; reset_check;"))
    objects = directory / "compile-obj"
    evidence.run(["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module", "tb",
                  "-j", "2", "--Mdir", relative(objects), "-o", "sim", *rtl,
                  relative(directory / "tb.sv")])
    binary = objects / "sim"
    for pattern in ("*.o", "*.a", "*.gch"):
        for path in objects.glob(pattern):
            path.unlink()
    cache[identity] = binary
    evidence._simulators = cache
    return binary


def run_compiled(evidence, binary, name, files):
    directory = evidence.path / name
    directory.mkdir()
    for filename, text in files.items():
        (directory / filename).write_text(text)
    argv = os.path.relpath(binary, directory)
    if not argv.startswith("."):
        argv = "./" + argv
    return evidence.run([argv], cwd=directory)
