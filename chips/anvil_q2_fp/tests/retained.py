"""Append-only project-local receipts with audited, hash-bound raw tool streams."""

import argparse
import datetime
import hashlib
import json
import os
import re
import resource
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def with_time_zero_check(bench):
    """Observe time-zero reset after reset NBAs, without a prior 1->0 toggle."""
    match = re.search(r"if\s*\(\s*(\{[^}]+\})\s*!==\s*0\s*\)", bench)
    assert match, "testbench must declare its complete public reset-output comparison"
    anchor = "initial begin\n    rst_n=0;\n"
    assert bench.count(anchor) == 1, "testbench must drive reset procedurally at time zero"
    bench = bench.replace("module tb;", "module tb;\n  reg reset_sample=0;", 1)
    bench = bench.replace(anchor, anchor + "    #0; reset_sample<=1;\n", 1)
    check = (
        "\n  always @(posedge reset_sample) begin\n"
        '    if($time !== 0) $fatal(1,"RESET_OBSERVATION_NOT_TIME_ZERO");\n'
        f'    if({match[1]} !== 0) $fatal(1,"TIME_ZERO_RESET_NONZERO_X");\n'
        '    $display("RESET_TIME_ZERO_COMPARED");\n'
        "  end\n"
    )
    before, after = bench.rsplit("endmodule", 1)
    return before + check + "endmodule" + after


def require_time_zero(trace):
    assert "RESET_TIME_ZERO_COMPARED" in trace.read_text(), "missing time-zero reset comparison"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def audit_streams(commands):
    hashes, errors = {}, {}
    for command in commands:
        for field in ("stdout", "stderr"):
            name = command[field]
            path = Path(name)
            if path.is_absolute() or ".." in path.parts:
                errors[name] = "raw stream path is not project-relative"
                continue
            try:
                resolved = (ROOT / path).resolve()
                relative = resolved.relative_to(ROOT)
                if {".git", ".vulcan", ".tooling", "VULCAN"} & set(relative.parts):
                    errors[name] = "raw stream points into excluded metadata"
                    continue
                digest = hashlib.sha256()
                with resolved.open("rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
                hashes[name] = digest.hexdigest()
            except OSError as exc:
                errors[name] = f"{type(exc).__name__}: {exc.strerror}"
            except ValueError:
                errors[name] = "raw stream resolves outside the project"
    return hashes, errors


class Run:
    def __init__(self, name, root=None):
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        root = root or os.environ.get("ANVIL_EVIDENCE_ROOT", "evidence/preparation")
        relative_root = Path(root)
        assert not relative_root.is_absolute() and ".." not in relative_root.parts
        assert relative_root.parts[:1] == ("evidence",), "receipts must be project-local evidence"
        assert not {".vulcan", ".git", ".tooling", "VULCAN"} & set(relative_root.parts)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.path = ROOT / root / f"{name}-{stamp}-{uuid.uuid4().hex[:8]}"
        self.path.mkdir(parents=True, exist_ok=False)
        self.receipt = {
            "schema": 1, "purpose": name, "acceptance_evidence": False,
            "cwd": ".", "started_at": now(), "commands": [], "source_sha256": {},
            "evidence_root": root,
            "argv": ["python3", str(Path(sys.argv[0]).resolve().relative_to(ROOT)), *sys.argv[1:]],
            "python_version": sys.version,
        }
        for pattern in ("rtl/*.sv", "design/*", "tests/*.py",
                        "anvil_q2_reference/rtl/*.sv"):
            for source in sorted(ROOT.glob(pattern)):
                if source.is_file():
                    self.receipt["source_sha256"][str(source.relative_to(ROOT))] = (
                        hashlib.sha256(source.read_bytes()).hexdigest())

    def relative(self, path):
        return str(Path(path).relative_to(ROOT))

    def command(self, argv, label, timeout=3600, expected_codes=(0,), environment=None):
        if shutil.which(argv[0]) is None:
            raise RuntimeError(f"missing required executable: {argv[0]}")
        out, err = self.path / f"{label}.stdout.txt", self.path / f"{label}.stderr.txt"
        record = {
            "argv": list(map(str, argv)), "cwd": ".", "started_at": now(),
            "timeout_s": timeout, "stdout": self.relative(out), "stderr": self.relative(err),
            "timed_out": False,
            "expected_exit_codes": list(expected_codes),
        }
        if environment:
            record["environment_overrides"] = environment
        self.receipt["commands"].append(record)
        start = time.monotonic()
        with out.open("xb") as stdout, err.open("xb") as stderr:
            try:
                completed = subprocess.run(
                    argv, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=timeout, check=False,
                    env=(os.environ | environment) if environment else None)
                record["exit_code"] = completed.returncode
            except subprocess.TimeoutExpired:
                record["exit_code"] = None
                record["timed_out"] = True
        record["ended_at"] = now()
        record["duration_s"] = time.monotonic() - start
        if record["timed_out"] or record["exit_code"] not in expected_codes:
            raise RuntimeError(f"{label}: tool failure; see {self.relative(err)}")
        return out

    def finish(self, outcome, **details):
        hashes, errors = audit_streams(self.receipt["commands"])
        self.receipt["raw_stream_sha256"] = hashes
        if errors:
            self.receipt["raw_stream_retention_errors"] = errors
            if outcome != "failed":
                self.receipt["unadmitted_result_before_retention_failure"] = {
                    "outcome": outcome, "details": details}
                raise RuntimeError("retained raw streams are unavailable: " + ", ".join(errors))
        self.receipt.update(outcome=outcome, ended_at=now(), **details)
        receipt = self.path / "receipt.json"
        with receipt.open("x") as stream:
            json.dump(self.receipt, stream, indent=2)
            stream.write("\n")
        print(self.relative(receipt), flush=True)

    def interactive(self, argv, label, handler, timeout=21600):
        """Bound a live public-pin transactor and retain both raw tool streams."""
        if shutil.which(argv[0]) is None:
            raise RuntimeError(f"missing required executable: {argv[0]}")
        out, err = self.path / f"{label}.stdout.txt", self.path / f"{label}.stderr.txt"
        record = {
            "argv": list(map(str, argv)), "cwd": ".", "started_at": now(),
            "timeout_s": timeout, "stdout": self.relative(out), "stderr": self.relative(err),
            "timed_out": False, "expected_exit_codes": [0], "live_stimulus": True,
        }
        self.receipt["commands"].append(record)
        start = time.monotonic()
        with out.open("x") as stdout, err.open("x") as stderr:
            process = subprocess.Popen(
                argv, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=stderr, text=True, bufsize=1)

            def expire():
                record["timed_out"] = True
                process.kill()

            timer = threading.Timer(timeout, expire)
            timer.start()
            try:
                result = handler(process, stdout)
                process.stdin.close()
                for line in process.stdout:
                    stdout.write(line)
                process.wait()
            finally:
                timer.cancel()
                if process.poll() is None:
                    process.kill()
                process.wait()
                process.stdout.close()
                if not process.stdin.closed:
                    process.stdin.close()
                record.update(exit_code=process.returncode, ended_at=now(),
                              duration_s=time.monotonic() - start)
        if record["timed_out"] or record["exit_code"] != 0:
            raise RuntimeError(f"{label}: tool failure; see {self.relative(out)} and {self.relative(err)}")
        return result


def audit_preparation_receipt(name):
    """Read-only integrity audit; never repair or relabel the original receipt."""
    run = Run("verifier-preparation-retention-audit")
    try:
        run.command(["python3", "--version"], "python-version")
        path = Path(name)
        assert not path.is_absolute() and ".." not in path.parts
        assert path.parts[:2] == ("evidence", "preparation") and path.name == "receipt.json"
        resolved = (ROOT / path).resolve()
        resolved.relative_to(ROOT / "evidence/preparation")
        data = resolved.read_bytes()
        original = json.loads(data)
        hashes, errors = audit_streams(original["commands"])
        for stream, expected in original.get("raw_stream_sha256", {}).items():
            if stream in hashes and hashes[stream] != expected:
                errors[stream] = "raw stream hash differs from its immutable receipt"
        run.receipt["audited_preparation_receipt"] = name
        run.receipt["input_sha256"] = {name: hashlib.sha256(data).hexdigest()}
        run.receipt["audited_stream_sha256"] = hashes
        run.receipt["audited_stream_errors"] = errors
        if errors:
            raise RuntimeError("advisory raw-stream integrity failure: " + ", ".join(errors))
        run.finish("passed-focused-only", metrics={"raw_streams_checked": len(hashes)},
                   limitations="Read-only raw-stream integrity audit, not reexecution or engineering acceptance.")
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError, KeyError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-preparation-receipt", required=True,
                        help="read-only audit of a project-relative advisory receipt")
    raise SystemExit(audit_preparation_receipt(parser.parse_args().audit_preparation_receipt))
