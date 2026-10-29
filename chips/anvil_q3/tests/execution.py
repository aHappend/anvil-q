"""Source-bound subprocess retention, including unfinished child invocations.

An in-flight receipt with a null exit is not evidence of child completion or
shared-runtime persistence recovery.
Snapshot copying starts only after an incomplete receipt is retained. If later
writes fail too, that receipt remains incomplete, never a successful snapshot.
Every copied source must match its recorded hash before the snapshot is complete.
Live sources must still match that snapshot at successful finalization; source
drift fails the invocation rather than certifying a different workspace revision.
Check the same identity before each child launch, so detected drift cannot start
another tool. This guard detects changes, not their writer or shared-runtime cause.
The complete public-source inventory must match too, including added files.
Successful finalization requires a complete snapshot and settled child records;
completed expected-negative tests may retain nonzero exit codes.
Snapshot content, raw logs and child receipts must still exist at finalization.

Workload shards retain independent invocation receipts under WORKLOAD_ROOT.
Reuse requires matching public sources, tool executables/version outputs,
deterministic fixture inputs and complete workload arguments, plus intact
snapshots, generated fixtures, comparisons and raw tool evidence. The aggregate
automatically executes cases without reusable evidence and revalidates every
child at finalization. These content bindings do not adjudicate runtime-owned
identifiers, waive coverage gates or establish a cold-run time budget.
"""

from datetime import datetime, timezone
from dataclasses import asdict, dataclass, is_dataclass
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
import threading
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parent.parent
SELECTORS = ("rtl/*.sv", "design/*.md", "design/*.json", "fpga/*",
             "tests/**", "anvil_q2_reference/rtl/*.sv")
VERILATOR_UNROLL = ("--unroll-count", "1024", "--unroll-stmts", "1000000")
WORKLOAD_ROOT = "evidence/check-behavior/shards"


def canonical(value):
    if is_dataclass(value):
        return canonical(asdict(value))
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [canonical(item) for item in value]
    return value


def content_hash(value):
    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True).encode()).hexdigest()


@dataclass
class Workload:
    """One unchanged case; cost is a scheduling heuristic, never a time claim."""

    group: str
    name: str
    action: object
    run: object
    args: tuple
    kwargs: dict
    cost: int = 1

    @property
    def descriptor(self):
        return canonical({"group": self.group, "call": self.name,
                          "args": self.args, "kwargs": self.kwargs})

    @property
    def id(self):
        return self.group + "-" + content_hash(self.descriptor)[:20]

    def execute(self, run):
        return self.action(run, *self.args, **self.kwargs)

    def __call__(self):
        return self.execute(self.run)


def workload(run, group, name, action, *args, cost=1, **kwargs):
    if name == "decoder_case":
        g = args[0]
        tokens = kwargs.get("tokens", (1, 4, 2, 6, 3, 5, 7))
        cost = len(tokens) * (
            g.NUM_LAYERS * (4 * g.HIDDEN_SIZE**2 +
                            3 * g.HIDDEN_SIZE * g.INTERMEDIATE_SIZE) +
            g.VOCAB_SIZE * g.HIDDEN_SIZE)
    return Workload(group, name, action, run, args, kwargs, cost)


def execution_resources():
    cpus = len(os.sched_getaffinity(0))
    limit = Path("/sys/fs/cgroup/memory.max")
    memory = None
    if limit.is_file():
        value = limit.read_text().strip()
        memory = None if value == "max" else int(value)
    available = os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    budget = min(available, memory) if memory is not None else available
    workers = min(8, cpus, max(1, (budget - 2 * 1024**3) // (512 * 1024**2)))
    build_jobs = min(2, max(1, cpus // min(workers, 2)))
    if budget < 8 * 1024**3:
        build_jobs = 1
    return {"workers": workers, "build_jobs": build_jobs,
            "affinity_cpus": cpus, "memory_limit_bytes": memory}


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
        self.lock = threading.RLock()
        self.build_locks = {}
        self.resources = execution_resources()
        self.compiler_slots = threading.BoundedSemaphore(min(2, self.resources["workers"]))
        self.builds = {}
        self.build_reuses = []
        self.workload_results = []
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

    def validate_live_sources(self):
        if not self.source_snapshot_complete:
            raise AssertionError("incomplete verification snapshot cannot launch a tool")
        for name, digest in self.hashes.items():
            source = ROOT / name
            if not source.is_file() or sha256(source) != digest:
                raise AssertionError("live verification source changed during execution: " + name)
        selected = {str(source.relative_to(ROOT)) for source in sources()}
        recorded = set(self.hashes)
        if selected != recorded:
            raise AssertionError(
                "live verification source selection changed during execution: "
                + json.dumps({"added": sorted(selected - recorded),
                              "removed": sorted(recorded - selected)}, sort_keys=True))

    def parallel(self, jobs):
        """Submit the complete inventory longest-first, retaining inventory order."""
        jobs = list(jobs)
        order = list(range(len(jobs)))
        if any(isinstance(job, Workload) for job in jobs):
            order.sort(key=lambda i: (-getattr(jobs[i], "cost", 1),
                                      getattr(jobs[i], "id", ""), i))
            self.workload_toolchain()
            write_json(self.path / "workload-inventory.json", [
                {"id": job.id, "workload": job.descriptor, "scheduling_cost": job.cost}
                for job in jobs if isinstance(job, Workload)])
        workers = self.resources["workers"]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {}
            for index in order:
                job = jobs[index]
                futures[index] = (pool.submit(self.collect_workload, job)
                                  if isinstance(job, Workload) else pool.submit(job))
            try:
                return [futures[index].result() for index in range(len(jobs))]
            except BaseException:
                for future in futures.values():
                    future.cancel()
                raise

    def workload_toolchain(self):
        if hasattr(self, "workload_toolchain_identity"):
            return self.workload_toolchain_identity
        tools = (("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V"),
                 ("verilator", "--version"), ("g++", "--version"), ("make", "--version"))
        versions = self.versions(tools)
        identity = {}
        for name, _ in tools:
            version = versions[name]
            identity[name] = {"available": version["available"]}
            if version["available"]:
                record = next(record for record in reversed(self.records)
                              if record["stdout"] == version["version_output"])
                identity[name].update({
                    "executable_sha256": sha256(Path(shutil.which(name)).resolve()),
                    "stdout_sha256": sha256(ROOT / record["stdout"]),
                    "stderr_sha256": sha256(ROOT / record["stderr"])})
        identity["environment_sha256"] = content_hash({
            name: os.environ.get(name) for name in
            ("CC", "CXX", "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS", "MAKEFLAGS",
             "VERILATOR_ROOT", "IVERILOG_ICONFIG")})
        self.workload_toolchain_identity = identity
        return identity

    def reusable_workload(self, receipt, binding):
        """Incomplete, stale or damaged receipts trigger execution, not acceptance."""
        try:
            saved = json.loads(receipt.read_text())
            if (not isinstance(saved, dict) or saved.get("status") != "passed" or
                    saved.get("source_snapshot_complete") is not True or
                    saved.get("source_hashes") != self.hashes or
                    saved.get("workload_binding") != binding or
                    not isinstance(saved.get("finished_at"), (int, float)) or
                    "result" not in saved or not saved.get("executions") or
                    not isinstance(saved["executions"], list) or
                    not isinstance(saved.get("workload_artifacts"), dict) or
                    not saved["workload_artifacts"] or
                    not isinstance(saved.get("workload_dependencies"), dict) or
                    not saved["workload_dependencies"] or
                    saved.get("result_sha256") != content_hash(saved["result"])):
                return None, "incomplete or stale binding/result"
            for index, record in enumerate(saved["executions"]):
                if (not isinstance(record, dict) or
                        record.get("exit_code") is None or record.get("timeout") or
                        record["exit_code"] not in record.get("expected_exit_codes", ()) or
                        "launch_error" in record or "finished_at" not in record):
                    return None, "unsettled tool execution"
                folder = receipt.parent / ("tool-%04d" % index)
                child = folder / "receipt.json"
                if json.loads(child.read_text()) != record:
                    return None, "changed tool receipt"
                for stream in ("stdout", "stderr"):
                    if record.get(stream) != self.rel(folder / (stream + ".txt")):
                        return None, "misbound tool log"
            for name, digest in saved["workload_artifacts"].items():
                path = (receipt.parent / name).resolve()
                path.relative_to(receipt.parent.resolve())
                if sha256(path) != digest:
                    return None, "changed retained artifact: " + name
            for name, digest in saved["workload_dependencies"].items():
                path = (ROOT / name).resolve()
                path.relative_to(ROOT.resolve())
                if sha256(path) != digest:
                    return None, "changed retained dependency: " + name
            actual = {str(path.relative_to(receipt.parent))
                      for path in receipt.parent.rglob("*")
                      if path.is_file() and path != receipt}
            if actual != set(saved["workload_artifacts"]):
                return None, "changed retained artifact inventory"
            for name, digest in self.hashes.items():
                if sha256(receipt.parent / "sources" / name) != digest:
                    return None, "changed source snapshot: " + name
            return saved["result"], None
        except (FileNotFoundError, IsADirectoryError, json.JSONDecodeError,
                UnicodeDecodeError, KeyError, TypeError, ValueError):
            return None, "missing or malformed retained evidence"

    def collect_workload(self, job):
        self.validate_live_sources()
        binding = {"workload": job.descriptor, "source_hashes": self.hashes,
                   "toolchain": self.workload_toolchain(),
                   "fixture_inputs": "source-bound deterministic generators, seeds and assets"}
        root = ROOT / WORKLOAD_ROOT / job.id
        decisions = []
        for receipt in sorted(root.glob("*/receipt.json"), reverse=True):
            result, reason = self.reusable_workload(receipt, binding)
            decisions.append({"receipt": self.rel(receipt), "rejection": reason})
            if reason is None:
                self.validate_live_sources()
                with self.lock:
                    if not hasattr(self, "workload_reuses"):
                        self.workload_reuses = []
                    self.workload_reuses.append({"id": job.id, "receipt": self.rel(receipt)})
                    self.workload_results.append({
                        "receipt": self.rel(receipt), "binding": binding,
                        "result_sha256": content_hash(result)})
                    write_json(self.path / "workload-reuse.json", self.workload_reuses)
                return result
        child = Run(self.rel(root), "behavior-shard:" + job.id)
        child.workload_toolchain_identity = binding["toolchain"]
        child.tool_versions = self.tool_versions
        child.resources = self.resources
        child.compiler_slots = self.compiler_slots
        child.lock = self.lock
        child.build_locks = self.build_locks
        child.shared_builds = self.builds
        child.workload_binding = binding
        child.finish("running", reuse_candidates=decisions)
        try:
            if child.hashes != self.hashes:
                raise AssertionError("shard source snapshot differs from inventory snapshot")
            self.validate_live_sources()
            result = job.execute(child)
            if job.group == "portability" and result["cycles"] > 500000:
                raise AssertionError("portability smoke exceeds compact cycle tier")
            if isinstance(result, dict):
                result = {**result, "evidence_receipt": child.rel(child.path / "receipt.json")}
            child.workload_artifacts = {
                str(path.relative_to(child.path)): sha256(path)
                for path in sorted(child.path.rglob("*"))
                if path.is_file() and path != child.path / "receipt.json"}
            dependencies = set()
            for version in self.tool_versions.values():
                if version["available"]:
                    folder = (ROOT / version["version_output"]).parent
                    dependencies.update(folder / name for name in
                                        ("receipt.json", "stdout.txt", "stderr.txt"))
            with self.lock:
                builds = list(self.builds.values())
            for cached, _, record in builds:
                dependencies.update((cached, cached.parent / "build.json"))
                folder = (ROOT / record["stdout"]).parent
                dependencies.update(folder / name for name in
                                    ("receipt.json", "stdout.txt", "stderr.txt"))
            child.workload_dependencies = {self.rel(path): sha256(path)
                                           for path in sorted(dependencies)}
            child.finish("passed", result=result, result_sha256=content_hash(result),
                         reuse_candidates=decisions)
        except BaseException as exc:
            child.finish("failed", diagnosis=str(exc), reuse_candidates=decisions)
            raise
        with self.lock:
            self.workload_results.append({
                "receipt": self.rel(child.path / "receipt.json"), "binding": binding,
                "result_sha256": content_hash(result)})
        return result

    def _build(self, argv, cwd, timeout, expected):
        argv = list(argv)
        tool = str(argv[0])
        if tool == "verilator" and "-j" not in argv:
            argv[1:1] = ["-j", str(self.resources["build_jobs"])]
        output_flag = "-o"
        binary = Path(argv[argv.index(output_flag) + 1])
        if tool == "verilator":
            obj = Path(argv[argv.index("--Mdir") + 1])
            binary = obj / binary
        work = ROOT if cwd is None else Path(cwd)
        binary = work / binary
        if tool not in getattr(self, "tool_versions", {}):
            self.versions([(tool, "--version" if tool == "verilator" else "-V")])
        normalized = []
        skip = False
        for arg in map(str, argv):
            if skip:
                skip = False
                continue
            if arg in ("-o", "--Mdir"):
                skip = True
                continue
            path = work / arg
            if tool == "verilator" and arg.endswith(".cpp") and not path.is_file():
                path = work / obj / arg
            if path.is_file():
                normalized.append({"name": path.name, "sha256": sha256(path)})
            else:
                normalized.append(arg)
        identity = {"argv": normalized, "tool": self.tool_versions[tool],
                    "cwd": str(work.relative_to(ROOT)),
                    "source_inventory": self.hashes}
        if tool == "verilator" and "g++" in self.tool_versions:
            identity["cpp_toolchain"] = self.tool_versions["g++"]
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        with self.lock:
            gate = self.build_locks.setdefault(key, threading.Lock())
        with gate:
            self.validate_live_sources()
            cache_entries = getattr(self, "shared_builds", self.builds)
            if key in cache_entries:
                cached, text, record = cache_entries[key]
                manifest = json.loads((cached.parent / "build.json").read_text())
                if sha256(cached) != manifest["executable_sha256"]:
                    raise AssertionError("cached executable identity changed")
                binary.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cached, binary)
                binary.chmod(0o755)
                with self.lock:
                    self.builds[key] = cached, text, record
                    reuse = {"key": key, "executable": self.rel(binary),
                             "build_manifest": self.rel(cached.parent / "build.json"),
                             "compile_stdout": record["stdout"]}
                    self.build_reuses.append(reuse)
                    write_json(self.path / "build-reuse.json", self.build_reuses)
                return text, record
            with self.compiler_slots:
                text, record = self._tool(argv, cwd=cwd, timeout=timeout, expected=expected)
            if record["exit_code"] != 0:
                return text, record
            cache = self.path / "builds" / key
            cache.mkdir(parents=True)
            cached = cache / "executable"
            shutil.copyfile(binary, cached)
            cached.chmod(0o755)
            write_json(cache / "build.json", {
                "key": key, "identity": identity, "executable_sha256": sha256(cached),
                "compile_receipt": str(Path(record["stdout"]).parent / "receipt.json"),
                "original_executable": self.rel(binary),
                "intermediates": "removed after successful link; executable retained"})
            if tool == "verilator":
                # Only this invocation's resolved build directory is eligible.
                directory = (work / obj).resolve()
                directory.relative_to(self.path.resolve())
                for path in directory.iterdir():
                    if path != binary.resolve():
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()
            with self.lock:
                self.builds[key] = cached, text, record
                cache_entries[key] = cached, text, record
            return text, record

    def tool(self, argv, *, cwd=None, timeout=3600, expected=(0,)):
        if (str(argv[0]) == "verilator" and
                ("--binary" in argv or "--build" in argv) or
                str(argv[0]) == "iverilog" and "-o" in argv):
            return self._build(argv, cwd, timeout, expected)
        return self._tool(argv, cwd=cwd, timeout=timeout, expected=expected)

    def _tool(self, argv, *, cwd=None, timeout=3600, expected=(0,)):
        if timeout < 3600:
            raise ValueError("functional subprocess deadlines must be >=3600 seconds")
        work = ROOT if cwd is None else Path(cwd)
        work.relative_to(ROOT)
        self.validate_live_sources()
        start = time.time()
        with self.lock:
            folder = self.path / ("tool-%04d" % len(self.records))
            folder.mkdir()
            record = {}
            self.records.append(record)
        record = {"argv": [str(a) for a in argv], "cwd": str(work.relative_to(ROOT)) or ".",
                  "cwd_base": "project root", "started_at": start, "timeout_s": timeout,
                  "expected_exit_codes": list(expected),
                  "stdout": self.rel(folder / "stdout.txt"), "stderr": self.rel(folder / "stderr.txt"),
                  "timeout": False, "exit_code": None}
        caught = None
        with (folder / "stdout.txt").open("wb") as out, (folder / "stderr.txt").open("wb") as err:
            with self.lock:
                self.records[int(folder.name.split("-")[1])] = record
                write_json(folder / "receipt.json", record)
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
        with self.lock:
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
        with self.lock:
            return self._finish(status, **details)

    def _finish(self, status, **details):
        if status == "passed" and (
                not self.source_snapshot_complete or
                any(record.get("exit_code") is None or record.get("timeout") or
                    "launch_error" in record for record in self.records)):
            raise AssertionError("incomplete verification execution cannot be finalized as passed")
        if status == "passed":
            self.validate_live_sources()
            for item in self.workload_results:
                result, reason = self.reusable_workload(ROOT / item["receipt"], item["binding"])
                if reason is not None or content_hash(result) != item["result_sha256"]:
                    raise AssertionError("missing/stale workload at finalization: "
                                         + item["receipt"] + ": " + str(reason))
            for cached, _, _ in self.builds.values():
                manifest = json.loads((cached.parent / "build.json").read_text())
                if sha256(cached) != manifest["executable_sha256"]:
                    raise AssertionError("retained cached executable identity changed")
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
                    "build_manifests": [self.rel(item[0].parent / "build.json")
                                        for item in self.builds.values()],
                    "build_reuses": self.build_reuses,
                    "workload_results": self.workload_results,
                    "execution_resources": self.resources,
                    **({"workload_binding": self.workload_binding}
                       if hasattr(self, "workload_binding") else {}),
                    **({"workload_artifacts": self.workload_artifacts}
                       if hasattr(self, "workload_artifacts") else {}),
                    **({"workload_dependencies": self.workload_dependencies}
                       if hasattr(self, "workload_dependencies") else {}),
                    "executions": self.records, **details})
