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


def stream_stat(stat):
    return dict(device=stat.st_dev, inode=stat.st_ino, links=stat.st_nlink,
                size=stat.st_size, mtime_ns=stat.st_mtime_ns, ctime_ns=stat.st_ctime_ns)


def reopen_capture(name):
    path = Path(name)
    assert not path.is_absolute() and ".." not in path.parts
    (ROOT / path).resolve().relative_to(ROOT / "evidence")
    observations = [json.loads(line) for line in (ROOT / path).read_text().splitlines()]
    failures = [row for row in observations if row["errors"]]
    assert not failures, f"capture previously failed: {failures[0] if failures else ''}"
    final = next(row for row in reversed(observations) if row["phase"] == "pre-close")
    assert not final["errors"], final["errors"]
    results = {}
    for name, expected in final["streams"].items():
        target = ROOT / name
        target.resolve().relative_to(ROOT / "evidence")
        with target.open("rb") as stream:
            before = stream_stat(os.fstat(stream.fileno()))
            pathname = stream_stat(target.stat())
            assert before == expected["descriptor"] == pathname, (
                f"reopened stream identity/size changed: {name}")
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
            after = stream_stat(os.fstat(stream.fileno()))
            assert before == after == stream_stat(target.stat()), (
                f"stream changed during separate-process reopening: {name}")
        results[name] = dict(descriptor=after, pathname=pathname, sha256=digest.hexdigest())
    print(json.dumps(dict(phase="separate-process-reopen", timestamp=now(), streams=results)))


class Capture:
    """Observe retained pathname/descriptor identity throughout child execution."""

    def __init__(self, run, record, out, err, text=False):
        self.run, self.record = run, record
        self.paths = (out, err)
        self.text = text
        self.stop = threading.Event()
        self.process = None
        self.failure = None
        self.previous = {}

    def checkpoint(self, phase):
        row = dict(phase=phase, timestamp=now(), monotonic_s=time.monotonic(),
                   streams={}, errors=[])
        for path, stream in zip(self.paths, self.streams):
            name = self.run.relative(path)
            try:
                stream.flush()
                os.fsync(stream.fileno())
                descriptor = stream_stat(os.fstat(stream.fileno()))
                observed = dict(descriptor=descriptor)
                row["streams"][name] = observed
                pathname = stream_stat(path.stat())
                observed["pathname"] = pathname
                if (descriptor["device"], descriptor["inode"]) != (
                        pathname["device"], pathname["inode"]):
                    row["errors"].append(f"pathname replaced: {name}")
                if descriptor["links"] == 0:
                    row["errors"].append(f"open descriptor unlinked: {name}")
                if descriptor["size"] < self.previous.get(name, 0):
                    row["errors"].append(f"stream truncated: {name}")
                self.previous[name] = descriptor["size"]
            except OSError as exc:
                row["errors"].append(f"{name}: {type(exc).__name__}: {exc}")
        if row["errors"] and self.failure is None:
            self.failure = row
            self.record["first_capture_failure"] = row
        self.observations.write(json.dumps(row) + "\n")
        self.observations.flush()
        os.fsync(self.observations.fileno())
        return row

    def monitor(self):
        while not self.stop.wait(0.25):
            try:
                self.checkpoint("live")
            except OSError as exc:
                self.failure = self.failure or dict(
                    phase="live", timestamp=now(), errors=[f"observation write failed: {exc}"])
                self.record.setdefault("first_capture_failure", self.failure)
            if self.failure:
                if self.process is not None and self.process.poll() is None:
                    self.process.kill()
                return

    def __enter__(self):
        observation_path = self.paths[0].with_suffix(".capture.jsonl")
        self.record["capture_observations"] = self.run.relative(observation_path)
        self.observations = observation_path.open("x")
        self.streams = []
        try:
            for path in self.paths:
                self.streams.append(path.open("x" if self.text else "xb"))
            self.checkpoint("creation")
            if self.failure:
                raise RuntimeError(f"capture creation failed: {self.failure['errors']}")
        except BaseException:
            for stream in self.streams:
                stream.close()
            self.observations.close()
            raise
        self.thread = threading.Thread(target=self.monitor, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, kind, value, traceback):
        self.stop.set()
        self.thread.join()
        try:
            self.checkpoint("pre-close")
        finally:
            for stream in self.streams:
                stream.close()
            self.observations.close()
        stdout = self.paths[0].with_suffix(".reopen.stdout.txt")
        stderr = self.paths[0].with_suffix(".reopen.stderr.txt")
        argv = ["python3", "tests/retained.py", "--reopen-capture",
                self.record["capture_observations"]]
        reopening = dict(argv=argv, cwd=".", started_at=now(), timeout_s=3600)
        self.record["capture_reopen"] = reopening
        self.record["capture_reopen_stdout"] = self.run.relative(stdout)
        self.record["capture_reopen_stderr"] = self.run.relative(stderr)
        with stdout.open("xb") as out, stderr.open("xb") as err:
            try:
                result = subprocess.run(argv, cwd=ROOT, stdout=out, stderr=err,
                                        timeout=3600, check=False)
                reopening.update(exit_code=result.returncode, timed_out=False)
            except subprocess.TimeoutExpired:
                reopening.update(exit_code=None, timed_out=True)
            out.flush()
            err.flush()
            os.fsync(out.fileno())
            os.fsync(err.fileno())
        reopening["ended_at"] = now()
        if self.failure or reopening["exit_code"] != 0:
            raise RuntimeError(
                f"raw stream retention failure; see {self.record['capture_observations']} "
                f"and {self.record['capture_reopen_stderr']}") from value


def audit_streams(commands):
    hashes, errors = {}, {}
    for command in commands:
        for field in ("stdout", "stderr", "capture_observations",
                      "capture_reopen_stdout", "capture_reopen_stderr"):
            if field not in command:
                continue
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
        try:
            with Capture(self, record, out, err) as capture:
                process = subprocess.Popen(
                    argv, cwd=ROOT, stdout=capture.streams[0], stderr=capture.streams[1],
                    env=(os.environ | environment) if environment else None)
                capture.process = process
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    record["timed_out"] = True
                finally:
                    if process.poll() is None:
                        process.kill()
                    process.wait()
                    record["exit_code"] = process.returncode
        finally:
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
        with Capture(self, record, out, err, text=True) as capture:
            stdout, stderr = capture.streams
            process = subprocess.Popen(
                argv, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=stderr, text=True, bufsize=1)
            capture.process = process

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
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--audit-preparation-receipt",
                        help="read-only audit of a project-relative advisory receipt")
    group.add_argument("--reopen-capture", help="separate-process capture identity/size audit")
    args = parser.parse_args()
    if args.reopen_capture:
        reopen_capture(args.reopen_capture)
    else:
        raise SystemExit(audit_preparation_receipt(args.audit_preparation_receipt))
