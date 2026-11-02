"""Fresh, source-bound execution receipts for project-owned L1 experiments."""

import datetime
import hashlib
import json
from pathlib import Path
import shutil
import os
import signal
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]


def source_files(root=ROOT):
    files = []
    for pattern in ("rtl/*.sv", "anvil_q3_reference/rtl/*.sv", "design/*.md",
                    "tests/*.py", "README.md"):
        files.extend(root.glob(pattern))
    return sorted(set(files))


def fresh(stem, preparation=False):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parent = ROOT / "evidence"
    if preparation:
        parent /= "preparation"
    else:
        stem = f"l1-{stem}"
    path = parent / f"{stem}-{stamp}-{uuid.uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


class Run:
    def __init__(self, stem, preparation=False, repair_of=None):
        self.path = fresh(stem, preparation)
        self.start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.monotonic_start = time.monotonic()
        self.commands = []
        self.components = []
        self.hashes = {}
        snapshot = self.path / "source"
        for file in source_files():
            name = file.relative_to(ROOT)
            self.hashes[name.as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target)
        self.repair_of = repair_of

    def component(self, stem, operation):
        child = Run(stem, preparation="preparation" in self.path.parts)
        child.monotonic_start = self.monotonic_start
        child.tool_versions = getattr(self, "tool_versions", {})
        if child.hashes != self.hashes:
            raise RuntimeError("sources changed during an active verification suite")
        try:
            results = operation(child)
            child.finish("passed", results)
        except Exception as error:
            child.finish("failed", error=f"{type(error).__name__}: {error}")
            self.components.append({"receipt": relative(child.path / "receipt.json"),
                                    "status": "failed"})
            raise
        self.components.append({"receipt": relative(child.path / "receipt.json"),
                                "status": "passed"})
        return results

    def execute(self, argv, name, timeout=2700, cwd=ROOT, expected_exit=0):
        stdout = self.path / f"{name}.stdout.txt"
        stderr = self.path / f"{name}.stderr.txt"
        start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        disposition = "exited"
        timeout = min(timeout, max(0.01, 2700 - (time.monotonic() - self.monotonic_start)))
        with stdout.open("x") as out, stderr.open("x") as err:
            process = subprocess.Popen(argv, cwd=cwd, stdout=out, stderr=err,
                                       start_new_session=True)
            deadline = time.monotonic() + timeout
            try:
                while True:
                    try:
                        exit_code = process.wait(timeout=min(30, max(0.01, deadline - time.monotonic())))
                        break
                    except subprocess.TimeoutExpired:
                        if time.monotonic() >= deadline:
                            os.killpg(process.pid, signal.SIGKILL)
                            exit_code = process.wait()
                            disposition = "timeout"
                            break
                        print(f"PROGRESS {name}: tool execution active", flush=True)
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
        record = {"argv": list(map(str, argv)),
                  "cwd": Path(cwd).resolve().relative_to(ROOT).as_posix(),
                  "start": start,
                  "end": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "timeout_seconds": timeout, "disposition": disposition,
                  "exit_code": exit_code, "child_settled": process.poll() is not None,
                  "stdout": relative(stdout), "stderr": relative(stderr)}
        self.commands.append(record)
        text = stdout.read_text()
        if disposition != "exited" or exit_code != expected_exit:
            raise RuntimeError(f"{name}: {disposition}, exit {exit_code}; "
                               f"{relative(stdout)}, {relative(stderr)}\n"
                               f"{text[-2000:]}\n{stderr.read_text()[-2000:]}")
        return text

    def versions(self, tools):
        versions = {}
        flags = {"iverilog": ["-V"], "vvp": ["-V"], "yosys": ["-V"],
                 "verilator": ["--version"], "g++": ["--version"],
                 "make": ["--version"], "python3": ["--version"]}
        for tool in tools:
            if not shutil.which(tool):
                raise RuntimeError(f"missing installed prerequisite: {tool}")
            name = f"version-{tool}"
            text = self.execute([tool, *flags[tool]], name)
            versions[tool] = (text + (self.path / f"{name}.stderr.txt").read_text())[:3000]
        self.tool_versions = versions

    def finish(self, status, results=None, error=None):
        transient = {}
        for folder in self.path.glob("obj-*"):
            if folder.is_dir():
                for pattern in ("*.o", "*.a", "*.gch"):
                    for file in folder.glob(pattern):
                        file.unlink()
        image_directory = self.path / "checkpoint-images"
        if image_directory.is_dir():
            for file in image_directory.glob("*.hex"):
                transient[file.relative_to(self.path).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
                file.unlink()
            image_directory.rmdir()
        artifacts = {}
        for file in self.path.rglob("*"):
            if file.is_file() and "source" not in file.relative_to(self.path).parts:
                artifacts[file.relative_to(self.path).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
        receipt = {"kind": "independent-l1-preparation" if "preparation" in self.path.parts
                   else "independent-l1",
                   "entrypoint_argv": list(sys.orig_argv),
                   "entrypoint_cwd": Path.cwd().resolve().relative_to(ROOT).as_posix(),
                   "start": self.start,
                   "end": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "status": status, "source_sha256": self.hashes,
                   "tool_versions": getattr(self, "tool_versions", {}),
                   "commands": self.commands, "components": self.components,
                   "results": results, "error": error,
                   "repair_of": self.repair_of, "artifact_sha256": artifacts}
        receipt["transient_image_sha256"] = transient
        path = self.path / "receipt.json"
        with path.open("x") as output:
            json.dump(receipt, output, indent=2)
            output.write("\n")
        print(f"RECEIPT {relative(path)}", flush=True)
