"""Append-only, project-local advisory experiment receipts."""

from datetime import datetime, timezone
import hashlib
import json
import threading
import time

from scheduling import run_process


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class Experiment:
    def __init__(self, root, output, argv, source_names):
        self.root = root
        self.output = output
        if output.is_absolute() or ".." in output.parts:
            raise ValueError("output must be project-relative")
        self.directory = root / output
        self.directory.mkdir(parents=True, exist_ok=False)
        self.receipt = {"schema": 1, "advisory": True, "argv": argv,
                        "cwd": ".", "start": timestamp(), "timeout_s": 3600,
                        "source_hashes": {}, "commands": [], "exit": None}
        self.lock = threading.RLock()
        source_names = list(source_names)
        if "tests/retention.py" in source_names and "tests/scheduling.py" not in source_names:
            source_names.append("tests/scheduling.py")
        for name in source_names:
            data = (root / name).read_bytes()
            self.receipt["source_hashes"][name] = hashlib.sha256(data).hexdigest()
            path = self.directory / "sources" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def run(self, argv, label, timeout=3600, allow_mismatch=False, cwd=None,
            delegated=False):
        if timeout < 3600:
            raise ValueError("functional tool watchdog must be at least 3600 seconds")
        if cwd is not None and (cwd.is_absolute() or ".." in cwd.parts):
            raise ValueError("child cwd must be project-relative")
        command = {"argv": argv, "cwd": str(cwd) if cwd is not None else ".",
                   "start": timestamp(), "timeout_s": timeout,
                   "stdout": str(self.output / (label + ".stdout")),
                   "stderr": str(self.output / (label + ".stderr")),
                   "exit": None, "timed_out": False}
        with self.lock:
            self.receipt["commands"].append(command)
        start = time.monotonic()
        try:
            with (self.root / command["stdout"]).open("xb") as stdout, \
                    (self.root / command["stderr"]).open("xb") as stderr:
                run_process(self.root, argv, command, stdout, stderr, timeout,
                            cwd=cwd, delegated=delegated)
        except OSError as error:
            command["launch_error"] = str(error)
            raise
        finally:
            command["end"] = timestamp()
            command["duration_s"] = time.monotonic() - start
        if command["timed_out"] or (command["exit"] != 0 and not allow_mismatch):
            raise RuntimeError(f"{label} failed; see {command['stdout']} and {command['stderr']}")
        return (self.root / command["stdout"]).read_text()

    def finish(self, code, failure=None):
        self.receipt["end"] = timestamp()
        self.receipt["exit"] = code
        if failure is not None:
            self.receipt["failure"] = str(failure)
        with (self.directory / "receipt.json").open("x") as stream:
            stream.write(json.dumps(self.receipt, indent=2) + "\n")
        print(self.output / "receipt.json")
