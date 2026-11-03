"""Retained, bounded child execution without modifying shared-runtime evidence."""

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
SELECTORS = ("rtl/*.sv", "design/*.md", "tests/*",
             "anvil_q4_reference/rtl/*.sv")


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def source_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for pattern in SELECTORS for p in sorted(ROOT.glob(pattern))
            if p.is_file()}


def new_run(stem, preparation=False):
    parent = ROOT / "evidence" / ("preparation" if preparation else "verification")
    suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = parent / f"{stem}-{suffix}"
    directory.mkdir(parents=True, exist_ok=False)
    return directory


def relative(path):
    return str(Path(path).relative_to(ROOT))


def execute(directory, argv, timeout=600, repair_of=None):
    """Every invocation has its own immutable receipt and raw log pair."""
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise FileExistsError(f"Refusing to overwrite retained evidence: {relative(directory)}")
    versions = {"python3": ["python3", "--version"],
                "iverilog": ["iverilog", "-V"], "vvp": ["vvp", "-V"],
                "verilator": ["verilator", "--version"],
                "yosys": ["yosys", "-V"], "make": ["make", "--version"],
                "g++": ["g++", "--version"]}
    tool = Path(argv[0]).name
    version_argv = versions.get(tool, ["verilator", "--version"])
    with (directory / "tool-version.stdout.txt").open("w") as out, (
            directory / "tool-version.stderr.txt").open("w") as err:
        version = subprocess.run(version_argv, cwd=ROOT, stdout=out, stderr=err,
                                 timeout=30, check=False)
    receipt = {"schema": 1, "argv": list(map(str, argv)), "cwd": ".",
               "source_sha256": source_hashes(), "start_time": timestamp(),
               "timeout_s": timeout, "timed_out": False,
               "stdout": relative(directory / "stdout.txt"),
               "stderr": relative(directory / "stderr.txt"),
               "tool_version": {"argv": version_argv, "exit_code": version.returncode,
                                "stdout": relative(directory / "tool-version.stdout.txt"),
                                "stderr": relative(directory / "tool-version.stderr.txt")}}
    if repair_of:
        receipt["repair_of"] = repair_of
    start = time.monotonic()
    with (directory / "stdout.txt").open("w") as out, (
            directory / "stderr.txt").open("w") as err:
        process = subprocess.Popen(argv, cwd=ROOT, stdout=out, stderr=err,
                                   start_new_session=True)
        try:
            while True:
                try:
                    process.wait(timeout=min(30, max(0.01, timeout -
                                                    (time.monotonic() - start))))
                    break
                except subprocess.TimeoutExpired:
                    elapsed = time.monotonic() - start
                    if elapsed >= timeout:
                        receipt["timed_out"] = True
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        break
                    print(f"progress: {tool} running {elapsed:.0f}s", flush=True)
        finally:
            receipt.update(end_time=timestamp(), duration_s=time.monotonic() - start,
                           exit_code=process.returncode)
            (directory / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if process.returncode or receipt["timed_out"]:
        raise RuntimeError(f"Child failed; receipt: {relative(directory / 'receipt.json')}")
    return receipt
