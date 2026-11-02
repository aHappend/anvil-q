"""Project-relative, append-only tool receipts for bounded verifier preparation."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
SUITE_DEADLINE = None
SUITE_PATH = None


def begin_suite(path, seconds=2700):
    """One deadline shared by fixture generation, compilers and simulators."""
    global SUITE_DEADLINE, SUITE_PATH
    SUITE_DEADLINE = time.monotonic() + seconds
    SUITE_PATH = path


def remaining():
    return 2700 if SUITE_DEADLINE is None else max(0, SUITE_DEADLINE-time.monotonic())


def check_deadline():
    if remaining() <= 0:
        raise TimeoutError("aggregate 2700-second suite deadline expired")


def now():
    return datetime.now(timezone.utc).isoformat()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def sources():
    return sorted(p for pattern in ("rtl/*.sv", "tests/*.py", "design/*.md",
                                    "anvil_q3_reference/rtl/*.sv")
                  for p in ROOT.glob(pattern))


class Evidence:
    def __init__(self, stem, repair_of=None, preparation=True):
        suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
        base = ROOT / "evidence" / "preparation" if preparation else ROOT / "evidence"
        self.path = (SUITE_PATH or base) / (stem + "-" + suffix)
        self.path.mkdir(parents=True, exist_ok=False)
        self.record = dict(kind="L1 verification" if SUITE_PATH or not preparation else "verifier preparation",
                           start_time=now(), argv=["python3", *sys.argv], cwd=rel(Path.cwd()),
                           python_version=sys.version,
                           source_sha256={rel(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in sources()},
                           children=[], repair_of=repair_of)
        self.save()

    def save(self):
        # This run's receipt is live until finish; earlier run directories are immutable.
        (self.path / "receipt.json").write_text(json.dumps(self.record, indent=2) + "\n")

    def run(self, name, argv, version_argv, cwd=None, expected_exit_codes=(0,)):
        cwd = ROOT if cwd is None else Path(cwd)
        stdout = self.path / (name + ".stdout.txt")
        stderr = self.path / (name + ".stderr.txt")
        version_stdout = self.path / (name + ".version.stdout.txt")
        version_stderr = self.path / (name + ".version.stderr.txt")
        child = dict(argv=[str(x) for x in argv], cwd=rel(cwd), start_time=now(),
                     timeout_s=min(600 if Path(str(argv[0])).name == "vvp" else 2700,
                                   remaining()),
                     timed_out=False, stdout=rel(stdout), stderr=rel(stderr),
                     tool_version_argv=version_argv, tool_version_stdout=rel(version_stdout),
                     tool_version_stderr=rel(version_stderr),
                     expected_exit_codes=list(expected_exit_codes))
        generated_inputs = sorted({path for pattern in (
            "*.sv", "*.ys", "fixture.json", "*-fixtures.json", "checkpoint-images/*.hex")
            for path in self.path.glob(pattern)})
        child["generated_input_sha256"] = {
            rel(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in generated_inputs}
        self.record["children"].append(child)
        self.save()
        start = time.monotonic()
        process = None
        try:
            with version_stdout.open("w") as out, version_stderr.open("w") as err:
                version = subprocess.run(version_argv, cwd=cwd, stdout=out, stderr=err,
                                         check=False, timeout=max(0.001, min(30, remaining())))
            child["tool_version_exit_code"] = version.returncode
            check_deadline()
            deadline = min(start + child["timeout_s"], time.monotonic()+remaining())
            with stdout.open("w") as out, stderr.open("w") as err:
                process = subprocess.Popen(child["argv"], cwd=cwd, stdout=out, stderr=err)
                while True:
                    try:
                        wait = deadline-time.monotonic()
                        if wait <= 0:
                            raise TimeoutError(f"{name}: finite execution deadline expired")
                        exit_code = process.wait(timeout=min(30, wait))
                        break
                    except subprocess.TimeoutExpired:
                        # This is a progress heartbeat, not an execution
                        # timeout or a numerical acceptance threshold.
                        print(f"PROGRESS {name} elapsed_s={int(time.monotonic()-start)}",
                              flush=True)
            child["exit_code"] = exit_code
        except (subprocess.TimeoutExpired, TimeoutError) as exc:
            child["timed_out"] = True
            child["timeout_error"] = str(exc)
            if process is not None:
                # Kill only descendants of this owned child; never name-match
                # unrelated simulations or Quartus work.
                descendants = subprocess.run(
                    ["ps", "-eo", "pid=,ppid="], capture_output=True, text=True,
                    timeout=5, check=True).stdout.splitlines()
                tree = [(int(line.split()[0]), int(line.split()[1])) for line in descendants]
                owned = {process.pid}
                while True:
                    expanded = owned | {pid for pid, parent in tree if parent in owned}
                    if expanded == owned:
                        break
                    owned = expanded
                import os
                import signal
                for pid in sorted(owned, reverse=True):
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                child["exit_code"] = process.wait(timeout=5)
            raise TimeoutError(f"{name} timed out; retained {rel(self.path/'receipt.json')}") from exc
        except OSError as exc:
            child["launch_error"] = str(exc)
            raise
        finally:
            child["end_time"] = now()
            child["duration_s"] = time.monotonic() - start
            self.save()
        if exit_code not in expected_exit_codes:
            raise RuntimeError(f"{name} exited {exit_code}: {rel(stdout)}, {rel(stderr)}")
        return stdout

    def finish(self, status, **summary):
        self.record.update(end_time=now(), status=status, summary=summary)
        self.save()
