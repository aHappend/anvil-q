"""Source-bound subprocess retention, including unfinished child invocations.

An in-flight receipt with a null exit is not evidence of child completion or
shared-runtime persistence recovery.
Snapshot copying starts only after an incomplete receipt is retained. If later
writes fail too, that receipt remains incomplete, never a successful snapshot.
Every copied source must match its recorded hash before the snapshot is complete.
Successful finalization requires a complete snapshot and settled child records;
completed expected-negative tests may retain nonzero exit codes.
Snapshot content, raw logs and child receipts must still exist at finalization.
"""

from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parent.parent
SELECTORS = ("rtl/*.sv", "design/*.md", "design/*.json", "fpga/*",
             "tests/**", "anvil_q2_reference/rtl/*.sv")
VERILATOR_UNROLL = ("--unroll-count", "1024", "--unroll-stmts", "1000000")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sources():
    selected = set()
    for pattern in SELECTORS:
        # pathlib's trailing ** visits directories, unlike the admitted recursive selector.
        matches = {p for p in ROOT.glob(pattern + "/*" if pattern.endswith("/**") else pattern)
                   if p.is_file() and not set(p.relative_to(ROOT).parts).intersection(
                       ("__pycache__", ".vulcan", ".git", ".tooling", "VULCAN"))}
        if not matches:
            raise AssertionError("declared source selector matched no public files: " + pattern)
        selected.update(matches)
    return sorted(selected)


def write_json(path, obj):
    path = Path(path)
    payload = json.dumps(obj, indent=2, sort_keys=True) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix="." + path.name + "-", delete=False) as out:
            temporary = Path(out.name)
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink()


class Run:
    def __init__(self, output, purpose, repair_of=None):
        root = Path(output)
        if not root.is_absolute():
            root = ROOT / root
        root.relative_to(ROOT)
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") +
                            "-" + uuid.uuid4().hex[:12])
        self.path.mkdir()
        self.records = []
        self.start = time.time()
        self.purpose = purpose
        self.repair_of = repair_of
        self.hashes = {}
        self.source_snapshot_complete = False
        self.finish("running")
        try:
            for source in sources():
                relative = source.relative_to(ROOT)
                self.hashes[str(relative)] = sha256(source)
                target = self.path / "sources" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                if sha256(target) != self.hashes[str(relative)]:
                    raise OSError(errno.EIO, "source snapshot hash mismatch: " + str(relative))
        except OSError as exc:
            self.finish("failed", diagnosis="source snapshot failed: " + str(exc))
            raise
        self.source_snapshot_complete = True
        self.finish("running")

    def rel(self, path):
        return str(Path(path).relative_to(ROOT))

    def tool(self, argv, *, cwd=None, timeout=3600, expected=(0,)):
        if timeout < 3600:
            raise ValueError("functional subprocess deadlines must be >=3600 seconds")
        work = ROOT if cwd is None else Path(cwd)
        work.relative_to(ROOT)
        folder = self.path / ("tool-%04d" % len(self.records))
        folder.mkdir()
        start = time.time()
        record = {"argv": [str(a) for a in argv], "cwd": str(work.relative_to(ROOT)) or ".",
                  "cwd_base": "project root", "started_at": start, "timeout_s": timeout,
                  "stdout": self.rel(folder / "stdout.txt"), "stderr": self.rel(folder / "stderr.txt"),
                  "timeout": False, "exit_code": None}
        caught = None
        with (folder / "stdout.txt").open("wb") as out, (folder / "stderr.txt").open("wb") as err:
            write_json(folder / "receipt.json", record)
            self.records.append(record)
            self.finish("running")
            try:
                child = subprocess.run(record["argv"], cwd=work, stdout=out, stderr=err,
                                       timeout=timeout, check=False)
                record["exit_code"] = child.returncode
            except subprocess.TimeoutExpired as exc:
                record["timeout"] = True
                caught = exc
            except OSError as exc:
                record["launch_error"] = str(exc)
                caught = exc
        record["finished_at"] = time.time()
        write_json(folder / "receipt.json", record)
        self.finish("running")
        if caught is not None:
            raise RuntimeError("tool execution failed: " + self.rel(folder / "receipt.json")) from caught
        if record["exit_code"] not in expected:
            raise AssertionError("tool exit %s: %s" %
                                 (record["exit_code"], self.rel(folder / "receipt.json")))
        return (folder / "stdout.txt").read_text(errors="replace"), record

    def versions(self, tools):
        versions = dict(getattr(self, "tool_versions", {}))
        for name, flag in tools:
            if shutil.which(name) is None:
                versions[name] = {"available": False}
                continue
            text, record = self.tool([name, flag])
            versions[name] = {"available": True, "version_output": record["stdout"],
                              "version_text": text[:2000]}
        self.tool_versions = versions
        self.finish("running")
        return versions

    def finish(self, status, **details):
        if status == "passed" and (
                not self.source_snapshot_complete or
                any(record.get("exit_code") is None or record.get("timeout") or
                    "launch_error" in record for record in self.records)):
            raise AssertionError("incomplete verification execution cannot be finalized as passed")
        if status == "passed":
            for name, digest in self.hashes.items():
                snapshot = self.path / "sources" / name
                if not snapshot.is_file() or sha256(snapshot) != digest:
                    raise AssertionError("missing/changed retained verification artifact: "
                                         + self.rel(snapshot))
            for index, record in enumerate(self.records):
                folder = self.path / ("tool-%04d" % index)
                for stream in ("stdout", "stderr"):
                    path = folder / (stream + ".txt")
                    if record.get(stream) != self.rel(path) or not path.is_file():
                        raise AssertionError("missing/misbound retained verification artifact: "
                                             + self.rel(path))
                receipt = folder / "receipt.json"
                if not receipt.is_file() or json.loads(receipt.read_text()) != record:
                    raise AssertionError("missing/changed retained verification artifact: "
                                         + self.rel(receipt))
        write_json(self.path / "receipt.json",
                   {"schema": 1, "purpose": self.purpose, "status": status,
                    "started_at": self.start, "finished_at": time.time(),
                    "invocation": {"argv": ["python3", *sys.argv], "cwd": ".",
                                   "cwd_base": "project root"},
                    "repair_of": self.repair_of, "source_hashes": self.hashes,
                    "source_snapshot_complete": self.source_snapshot_complete,
                    "tool_versions": getattr(self, "tool_versions", {}),
                    "executions": self.records, **details})
