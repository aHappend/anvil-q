"""Project-relative, append-only tool receipts for bounded verifier preparation."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def sources():
    return sorted(p for pattern in ("rtl/*.sv", "tests/*.py", "design/*.md",
                                    "anvil_q3_reference/rtl/*.sv")
                  for p in ROOT.glob(pattern))


class Evidence:
    def __init__(self, stem, repair_of=None):
        suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
        self.path = ROOT / "evidence" / "preparation" / (stem + "-" + suffix)
        self.path.mkdir(parents=True, exist_ok=False)
        self.record = dict(kind="verifier preparation", start_time=now(),
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
                     timeout_s=None, timed_out=False, stdout=rel(stdout), stderr=rel(stderr),
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
        try:
            with version_stdout.open("w") as out, version_stderr.open("w") as err:
                version = subprocess.run(version_argv, cwd=cwd, stdout=out, stderr=err, check=False)
            child["tool_version_exit_code"] = version.returncode
            with stdout.open("w") as out, stderr.open("w") as err:
                process = subprocess.Popen(child["argv"], cwd=cwd, stdout=out, stderr=err)
                while True:
                    try:
                        exit_code = process.wait(timeout=30)
                        break
                    except subprocess.TimeoutExpired:
                        # This is a progress heartbeat, not an execution
                        # timeout or a numerical acceptance threshold.
                        print(f"PROGRESS {name} elapsed_s={int(time.monotonic()-start)}",
                              flush=True)
            child["exit_code"] = exit_code
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
