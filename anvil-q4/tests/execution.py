"""Source-bound, append-only execution records for independent L1 checks."""

import datetime
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import shutil
import subprocess
import sys
import threading
import time


ROOT = Path(__file__).resolve().parent.parent


class Experiment:
    def __init__(self, suite, preparation=False, repair_of=()):
        self._record_lock = threading.RLock()
        self._running_records = []
        self.deadline = time.monotonic() + 2700
        if "ANVIL_CHECK_DEADLINE" in os.environ:
            self.deadline = min(self.deadline, float(os.environ["ANVIL_CHECK_DEADLINE"]))
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        base = ROOT / "evidence"
        if preparation:
            base /= "preparation"
        self.directory = base / (suite + "-" + stamp)
        self.directory.mkdir(parents=True, exist_ok=False)
        paths = sorted(p for pattern in ("rtl/*.sv", "design/*.md", "tests/*",
                                        "anvil_q3_reference/rtl/*.sv")
                       for p in ROOT.glob(pattern) if p.is_file())
        self.receipt = {
            "suite": suite, "cwd": ".", "start_time": self.now(),
            "argv": [sys.executable, *sys.argv],
            "whole_check_timeout_s": 2700,
            "repair_of": list(repair_of),
            "source_sha256": {self.rel(p): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in paths},
            "commands": [], "comparisons": {},
        }
        self.save()

    @staticmethod
    def now():
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    @staticmethod
    def rel(path):
        return Path(path).relative_to(ROOT).as_posix()

    def save(self):
        with self._record_lock:
            (self.directory / "receipt.json").write_text(
                json.dumps(self.receipt, indent=2) + "\n")

    def append_result(self, key, result):
        with self._record_lock:
            self.receipt[key].append(result)
            self.save()

    def map(self, function, items, workers=2):
        """Run independent cases with bounded concurrency and ordered results."""
        if workers not in (1, 2, 3):
            raise ValueError("case concurrency must be one, two or three")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(function, item) for item in items]
            try:
                for future in futures:
                    yield future.result()
            finally:
                for future in futures:
                    future.cancel()

    def run(self, argv, stem, timeout=600, cwd=ROOT, expect_failure=False):
        timeout = min(timeout, self.deadline - time.monotonic())
        if timeout <= 0:
            raise RuntimeError("whole-check 2700-second execution budget exhausted")
        record = {
            "argv": list(map(str, argv)), "cwd": self.rel(cwd),
            "start_time": self.now(), "timeout_s": timeout,
            "stdout_path": self.rel(self.directory / (stem + ".stdout.txt")),
            "stderr_path": self.rel(self.directory / (stem + ".stderr.txt")),
        }
        start = time.monotonic()
        with self._record_lock:
            usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
            record["concurrent_commands"] = bool(self._running_records)
            for running in self._running_records:
                running["concurrent_commands"] = True
            self._running_records.append(record)
        with (ROOT / record["stdout_path"]).open("wb") as out, (
                ROOT / record["stderr_path"]).open("wb") as err:
            try:
                with subprocess.Popen(record["argv"], cwd=cwd, stdout=out,
                                      stderr=err, start_new_session=True,
                                      env={**os.environ,
                                           "ANVIL_CHECK_DEADLINE": str(self.deadline)}) as child:
                    child_deadline = time.monotonic() + timeout
                    while True:
                        remaining = child_deadline - time.monotonic()
                        try:
                            child.wait(timeout=max(0, min(30, remaining)))
                            record.update(exit_code=child.returncode, timed_out=False)
                            break
                        except subprocess.TimeoutExpired:
                            if time.monotonic() < child_deadline:
                                print(f"{self.receipt['suite']}: {stem} running "
                                      f"{int(time.monotonic()-start)}s", flush=True)
                                continue
                            os.killpg(child.pid, signal.SIGTERM)
                            try:
                                child.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                os.killpg(child.pid, signal.SIGKILL)
                                child.wait()
                            record.update(exit_code=124, timed_out=True)
                            break
            except subprocess.TimeoutExpired:
                record.update(exit_code=124, timed_out=True)
            except OSError as exc:
                err.write(str(exc).encode())
                record.update(exit_code=127, timed_out=False)
        record.update(end_time=self.now(), elapsed_s=time.monotonic() - start)
        with self._record_lock:
            usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
            if not record["concurrent_commands"]:
                record.update(user_cpu_s=usage_end.ru_utime-usage_start.ru_utime,
                              system_cpu_s=usage_end.ru_stime-usage_start.ru_stime)
            self._running_records.remove(record)
            self.receipt["commands"].append(record)
            self.save()
        if record["timed_out"] or (
                record["exit_code"] == 0 if expect_failure else record["exit_code"] != 0):
            raise RuntimeError(f"{stem}: exit={record['exit_code']} "
                               f"timeout={record['timed_out']}; {record['stderr_path']}")
        return (ROOT / record["stdout_path"]).read_text()

    def finish(self, error=None):
        self.receipt.update(exit_code=int(error is not None), end_time=self.now())
        if error is not None:
            self.receipt["failure"] = str(error)
        self.save()
        print(self.rel(self.directory / "receipt.json"), flush=True)

    def prune_objects(self, path):
        path = Path(path)
        if path.parent != self.directory or path.name != "compile-obj":
            raise ValueError("refusing cleanup outside this experiment's compile-obj")
        if path.exists():
            shutil.rmtree(path)
