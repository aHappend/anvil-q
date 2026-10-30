#!/usr/bin/env python3
"""Portable, fail-closed independent verification entrypoint.

Reproduce from the project root:
  python3 tests/verify.py --check prerequisites
  python3 tests/verify.py --check l1
  python3 tests/verify.py --check benchmark-contract
  python3 tests/verify.py --check portable

L1 combines rational IEEE leaf references, FP64 transformer/operator models,
public-pin transaction scoreboards, read-only parent differentials, disposable
defects, parameter diagnostics, source rules and generic Yosys synthesis.
Icarus/vvp remains mandatory for compact four-state smoke; compiled Verilator
executes the full matrices. Neither establishes device timing or physical results.
The portable entrypoint compiles and runs an exact fresh declared-source copy
on the minimum legal configuration, all modes, and synthesizes its hierarchy.
It is bounded clean-copy reproduction, not a full-model benchmark.

Every invocation allocates exclusive project-local preparation evidence. Child
logs are exclusive too: reusing a label fails instead of overwriting a run.
Missing full-model artifacts or unimplemented mandatory coverage fail closed.
Explicit benchmark replay arrays rerun actual RTL and independent FP64 inference
into fresh bounded windows before numerical validation; no saved metric is evidence.
The shared runtime, not this script, owns Arria timing and physical gates.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import threading
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))
from numerical import (binary32, check_scalar, dot_reference, dot_vectors,
                       bits32, float32, power_two, scalar_vectors)
from architecture import Architecture, CONFIGURATIONS, PARAMETERS, compare_trace, metrics
from operators import OPERATOR_IDS, PRODUCTION, OperatorReference, compare_operator
from operator_storage import (RequestWriter, REQUEST_MAGIC, REQUEST_RECORD, publication,
                              request_count, storage_limit)
from preservation import audit as audit_preservation, parser_selftest
from rtl_rules import inspect as inspect_rtl, matched, tokens
from benchmark import FORBIDDEN, artifact_path, check as check_benchmark, validate_input_manifests

ROOT = Path(__file__).resolve().parents[1]
SELECTORS = ("rtl/*.sv", "design/*.md", "fpga/*", "tests/**",
             "anvil_q1_reference/rtl/*.sv")
REQUIRED_COVERAGE = (
    "integration_all_legal_modes_seeds", "24_layer_integration",
    "production_individual_operators", "production_addresses_schedule",
    "protocol_reset_fault_mode_recovery", "parent_differential",
    "preservation_independent_inventory", "nine_mechanism_defect_sensitivity",
    "illegal_parameter_diagnostics", "complete_hierarchy_synthesis",
    "static_arithmetic_assignment_rules",
)
_INVENTORY = {}
_INVENTORY_LOCK = threading.RLock()
_BUILDS = None


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            value.update(chunk)
    return value.hexdigest()


def sources(root=ROOT):
    selected = {p for selector in SELECTORS
                for p in root.glob(selector + "/*" if selector.endswith("/**") else selector)
                if p.is_file() and not FORBIDDEN.intersection(p.relative_to(root).parts)}
    for path in selected:
        artifact_path(root, str(path.relative_to(root)))
    return sorted(selected)


def source_inventory():
    # Hash unchanged large model inputs once per invocation, never across runs.
    with _INVENTORY_LOCK:
        inventory = {}
        for path in sources():
            stat = path.stat()
            identity = (stat.st_dev, stat.st_ino, stat.st_size,
                        stat.st_mtime_ns, stat.st_ctime_ns)
            cached = _INVENTORY.get(path)
            if cached is None or cached[0] != identity:
                cached = (identity, digest(path))
                _INVENTORY[path] = cached
            inventory[str(path.relative_to(ROOT))] = cached[1]
        return inventory


def exception_diagnostic(error, phase, path=None):
    return {
        "phase": phase, "error": repr(error),
        "exception_type": type(error).__name__,
        "traceback": "".join(traceback.format_exception(error)),
        "errno": getattr(error, "errno", None),
        "filename": os.fsdecode(error.filename) if getattr(error, "filename", None) is not None else None,
        "filename2": os.fsdecode(error.filename2) if getattr(error, "filename2", None) is not None else None,
        "allocated_child_path": str(path.relative_to(ROOT)) if path is not None else None,
    }


def retain_exception(error, phase, path=None):
    diagnostic = exception_diagnostic(error, phase, path)
    error.verification_diagnostics = [
        *getattr(error, "verification_diagnostics", []), diagnostic]
    return diagnostic


class Evidence:
    def __init__(self, name):
        self.path = None
        self.lock = threading.RLock()
        self.receipt = {
            "schema": 1, "acceptance_evidence": False,
            "argv": [sys.executable, *sys.argv], "cwd": ".",
            "python_version": sys.version,
            "started_at": now(), "records": [], "assertions": [],
        }
        self.phase = "allocation"
        try:
            parent = ROOT / "evidence" / "preparation"
            parent.mkdir(parents=True, exist_ok=True)
            self.path = Path(tempfile.mkdtemp(prefix="verifier-" + name + "-", dir=parent))
            self.phase = "initialization"
            self.receipt["source_sha256"] = source_inventory()
            self.phase = "initial-publication"
            self.finish("running")
            self.phase = "execution"
        except Exception as error:
            retain_exception(error, self.phase, self.path)
            raise

    def finish(self, status):
        with self.lock:
            self._finish(status)

    def _finish(self, status):
        self.receipt["status"] = status
        self.receipt["ended_at"] = now()
        serialized = json.dumps(self.receipt, indent=2) + "\n"
        fd, temporary = tempfile.mkstemp(prefix=".receipt-", suffix=".tmp",
                                         dir=self.path)
        # Failed staged files are retained for diagnosis, never installed.
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            if stream.write(serialized) != len(serialized):
                raise OSError("incomplete receipt write")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path / "receipt.json")
        directory = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def assertion(self, name, passed, **detail):
        with self.lock:
            self.receipt["assertions"].append(
                {"name": name, "passed": bool(passed), **detail})
            self.finish("running")
        return passed

    @contextmanager
    def profile(self, name):
        started = time.monotonic()
        record = {"name": name, "started_at": now()}
        original = None
        try:
            yield
        except Exception as error:
            original = error
            retain_exception(error, "execution", self.path)
            raise
        finally:
            record.update(ended_at=now(), elapsed_s=time.monotonic()-started)
            with self.lock:
                self.receipt.setdefault("profiles", []).append(record)
                try:
                    self.finish("running")
                except Exception as error:
                    if original is None:
                        retain_exception(error, "profile-publication", self.path)
                        raise
                    original.verification_diagnostics.append(
                        exception_diagnostic(error, "profile-publication", self.path))

    def elapsed(self, name, started):
        self.receipt.setdefault("profiles", []).append(
            {"name": name, "ended_at": now(),
             "elapsed_s": time.monotonic()-started})
        self.finish("running")

    def run(self, label, argv, timeout=3600, cwd=ROOT):
        stdout = self.path / (label + ".stdout")
        stderr = self.path / (label + ".stderr")
        record = {
            "label": label, "argv": list(map(str, argv)),
            "cwd": str(cwd.relative_to(ROOT)), "started_at": now(),
            "timeout_s": timeout, "stdout": str(stdout.relative_to(ROOT)),
            "stderr": str(stderr.relative_to(ROOT)), "timed_out": False,
        }
        with self.lock:
            self.receipt["records"].append(record)
            self.finish("running")
        started = time.monotonic()
        original = None
        try:
            with stdout.open("xb") as out, stderr.open("xb") as err:
                try:
                    completed = subprocess.run(
                        argv, cwd=cwd, stdout=out, stderr=err, timeout=timeout,
                        check=False,
                    )
                    record["exit_code"] = completed.returncode
                except subprocess.TimeoutExpired:
                    record["timed_out"] = True
                    record["exit_code"] = None
        except OSError as error:
            original = error
            record["exit_code"] = None
            record["error"] = str(error)
            record["diagnostic"] = retain_exception(error, "execution", self.path)
        record["ended_at"] = now()
        record["elapsed_s"] = time.monotonic() - started
        try:
            self.finish("running")
        except Exception as error:
            if original is None:
                retain_exception(error, "execution-publication", self.path)
                raise
            original.verification_diagnostics.append(
                exception_diagnostic(error, "execution-publication", self.path))
        if original is not None:
            raise original.with_traceback(original.__traceback__)
        return record["exit_code"] == 0 and not record["timed_out"]

    def versions(self):
        result = True
        for name, args in (
            ("python3", [sys.executable, "--version"]),
            ("iverilog", ["iverilog", "-V"]),
            ("vvp", ["vvp", "-V"]), ("yosys", ["yosys", "-V"]),
        ):
            available = shutil.which(name) is not None
            self.assertion("tool_" + name, available)
            if available:
                result = self.run("version-" + name, args, timeout=30) and result
            else:
                result = False
        self.receipt["optional_tools"] = {
            name: bool(shutil.which(name)) for name in ("verilator", "quartus_sh")
        }
        if self.receipt["optional_tools"]["verilator"]:
            result = self.run("version-verilator", ["verilator", "--version"],
                              timeout=30) and result
        return result


def simulation_tier(requested, *, hidden=0, tokens=1, seeds=1, cycles=0,
                    full=False, mutation=False, protocol=False):
    if requested not in ("iverilog", "verilator"):
        raise ValueError("Unsupported simulator: " + requested)
    compiled = (requested == "verilator" or hidden > 32 or cycles > 500000 or tokens > 1 or
                seeds > 1 or full or mutation or protocol)
    return "verilator" if compiled else "iverilog"


class BuildCache:
    """Source/parameter-bound single-flight builds, scoped to this invocation."""

    def __init__(self):
        self.lock = threading.Lock()
        self.entries = {}
        self.slots = threading.BoundedSemaphore(2)

    def compile(self, ev, label, argv, executable):
        normalized = []
        index = 0
        while index < len(argv):
            argument = str(argv[index])
            if argument in ("-o", "--Mdir"):
                index += 2
                continue
            path = ROOT / argument
            normalized.append((argument, digest(path)) if path.is_file() else argument)
            index += 1
        tool = Path(shutil.which(str(argv[0])) or str(argv[0]))
        if not tool.is_file():
            return ev.run(label, argv)
        key = hashlib.sha256(json.dumps(
            [normalized, str(tool.resolve()), digest(tool)], sort_keys=True).encode()).hexdigest()
        with self.lock:
            entry = self.entries.get(key)
            if entry is not None and entry["event"].is_set() and entry["passed"] and (
                    not entry["binary"].is_file() or
                    digest(entry["binary"]) != entry["binary_sha256"]):
                entry = None
            owner = entry is None
            if owner:
                entry = {"event": threading.Event(), "passed": False}
                self.entries[key] = entry
        if owner:
            child = None
            original = None
            try:
                child = Evidence("build-" + key[:12])
                child.receipt["tool_versions_receipt"] = ev.receipt.get(
                    "tool_versions_receipt", str((ev.path / "receipt.json").relative_to(ROOT)))
                entry["receipt"] = str((child.path / "receipt.json").relative_to(ROOT))
                entry["binary"] = child.path / executable.name
                child.receipt["compile_inputs"] = {}
                for argument in map(str, argv):
                    source = ROOT / argument
                    if source.is_file() and source.suffix in (".sv", ".cpp"):
                        snapshot = child.path / "compile-inputs" / source.relative_to(ROOT)
                        snapshot.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, snapshot)
                        child.receipt["compile_inputs"][str(source.relative_to(ROOT))] = {
                            "sha256": digest(source),
                            "snapshot": str(snapshot.relative_to(ROOT))}
                command = list(map(str, argv))
                for flag, value in (("-o", str(entry["binary"].resolve())),
                                    ("--Mdir", str((child.path / "compile-obj").relative_to(ROOT)))):
                    if flag in command:
                        command[command.index(flag)+1] = value
                with self.slots, child.profile("build"):
                    entry["passed"] = child.run("compile", command)
                entry["passed"] = child.assertion(
                    "compiled_binary_present", entry["passed"] and entry["binary"].is_file())
                if entry["passed"]:
                    entry["binary_sha256"] = digest(entry["binary"])
                    child.receipt["binary_sha256"] = entry["binary_sha256"]
                    # Preserve executable, generated sources and logs, not compiler scratch.
                    removed = []
                    for path in (child.path / "compile-obj").glob("*"):
                        if path.is_file() and path.suffix in (".o", ".a", ".gch"):
                            path.unlink()
                            removed.append(path.name)
                    child.receipt["removed_completed_intermediates"] = removed
            except Exception as error:
                entry["passed"] = False
                if child is not None:
                    child.receipt["assertions"].append({
                        "name": "build_exception", "passed": False,
                        "diagnostics": [retain_exception(error, "build-execution", child.path)]})
                original = error
                raise
            finally:
                try:
                    if child is not None:
                        try:
                            child.finish("passed" if entry["passed"] else "failed")
                        except Exception as error:
                            entry["passed"] = False
                            if original is None:
                                retain_exception(error, "build-final-publication", child.path)
                                raise
                            original.verification_diagnostics.append(
                                exception_diagnostic(error, "build-final-publication", child.path))
                finally:
                    entry["event"].set()
        else:
            with ev.profile(label + "-build-wait"):
                entry["event"].wait()
        if "receipt" not in entry:
            raise OSError("build receipt allocation failed for " + key)
        with ev.lock:
            ev.receipt.setdefault("builds", []).append({
                "label": label, "key": key, "reused": not owner,
                "receipt": entry["receipt"],
            })
        if entry["passed"]:
            shutil.copy2(entry["binary"], executable)
        return entry["passed"]


def compile_simulation(ev, label, argv, executable):
    global _BUILDS
    if _BUILDS is None:
        _BUILDS = BuildCache()
    if str(argv[0]) == "verilator" and "--binary" in argv and "-MAKEFLAGS" not in argv:
        argv = [*argv, "-MAKEFLAGS", "OPT_FAST=-O3"]
    return _BUILDS.compile(ev, label, argv, executable)


def component(ev, name, check, *args, **kwargs):
    child = Evidence.__new__(Evidence)
    passed = False
    original = None
    diagnostics = []
    phase = "allocation"
    try:
        child.__init__(name)
        child.receipt["tool_versions_receipt"] = str((ev.path / "receipt.json").relative_to(ROOT))
        phase = "execution"
        with child.profile("component"):
            result = bool(check(child, *args, **kwargs))
        if not child.receipt["assertions"]:
            child.assertion("component_assertions_present", False,
                            error="component returned without recording an assertion")
        elif not result and all(
                assertion["passed"] for assertion in child.receipt["assertions"]):
            child.assertion("component_return_value", False,
                            error="component returned false despite passing assertions")
        passed = result and all(
            assertion["passed"] for assertion in child.receipt["assertions"])
    except Exception as error:
        original = error
        diagnostics = list(getattr(error, "verification_diagnostics", []))
        if not diagnostics:
            diagnostics.append(exception_diagnostic(
                error, phase, getattr(child, "path", None)))
        child.receipt["assertions"].append({
            "name": "verification_exception", "passed": False,
            "diagnostics": diagnostics})
        passed = False
    path = getattr(child, "path", None)
    receipt = str((path / "receipt.json").relative_to(ROOT)) if path is not None else None
    try:
        child.finish("passed" if passed else "failed")
    except Exception as error:
        diagnostics.append(exception_diagnostic(error, "final-publication", path))
        passed = False
        if original is None:
            original = error
    published = receipt if receipt is not None and (ROOT / receipt).is_file() else None
    with ev.lock:
        if published is not None:
            ev.receipt.setdefault("children", []).append(receipt)
        assertion = {
            "name": "component_" + name, "passed": passed,
            "child_receipt": published,
            "allocated_child_path": str(path.relative_to(ROOT)) if path is not None else None,
            "diagnostics": diagnostics,
        }
        # Append before publication: an unavailable child cannot hide its failure.
        ev.receipt["assertions"].append(assertion)
        try:
            ev.finish("running")
        except Exception as error:
            diagnostics.append(exception_diagnostic(error, "parent-publication", path))
            assertion["passed"] = passed = False
            if original is None:
                original = error
        if not passed:
            print(json.dumps(assertion), file=sys.stderr, flush=True)
    if original is not None:
        original.verification_diagnostics = diagnostics
        raise original.with_traceback(original.__traceback__)
    return passed


def parallel_components(ev, jobs, serial=()):
    """Run all obligations; each owns its receipt, traces and output names."""
    jobs = list(jobs)
    if len({job[0] for job in jobs}) != len(jobs):
        raise ValueError("duplicate component shard")
    if not set(serial).issubset({job[0] for job in jobs}):
        raise ValueError("unknown serial component shard")
    inventory = {name: {
        "name": name, "check": check.__name__, "args": list(args), "options": kwargs,
        "status": "planned", "history": [{"status": "planned", "at": now()}],
    } for name, check, args, kwargs in jobs}
    ev.receipt["shards"] = list(inventory.values())
    ev.receipt["scheduling"] = {"component_workers": 4, "compiler_slots": 2,
                               "compiler_jobs_per_slot": 2,
                               "reuse_scope": "this invocation only",
                               "inventory_complete_before_launch": True}
    ev.finish("running")

    def transition(name, status, **detail):
        with ev.lock:
            row = inventory[name]
            row.update(status=status, **detail)
            row["history"].append({"status": status, "at": now()})
            ev.receipt["shard_counts"] = {
                state: sum(row["status"] == state for row in inventory.values())
                for state in ("planned", "queued", "running", "completed", "failed")}
            ev.finish("running")

    launch = threading.Event()

    def execute(job):
        name, check, args, kwargs = job
        launch.wait()
        passed = False
        original = None
        try:
            transition(name, "running")
            passed = component(ev, name, check, *args, **kwargs)
            return passed
        except Exception as error:
            original = error
            with ev.lock:
                inventory[name]["error"] = repr(error)
                inventory[name]["diagnostics"] = getattr(
                    error, "verification_diagnostics",
                    [exception_diagnostic(error, "shard-execution")])
                if not any(row["name"] == "component_" + name
                           and not row["passed"] for row in ev.receipt["assertions"]):
                    ev.receipt["assertions"].append({
                        "name": "component_" + name, "passed": False,
                        "child_receipt": None,
                        "diagnostics": inventory[name]["diagnostics"]})
            return False
        finally:
            with ev.lock:
                receipts = [row["child_receipt"] for row in ev.receipt["assertions"]
                            if row["name"] == "component_" + name]
            try:
                transition(name, "completed" if passed else "failed",
                           passed=passed, child_receipt=receipts[-1] if receipts else None)
            except Exception as error:
                diagnostic = exception_diagnostic(error, "shard-publication")
                with ev.lock:
                    inventory[name].update(status="failed", passed=False)
                    inventory[name].setdefault("diagnostics", []).append(diagnostic)
                    ev.receipt["shard_counts"] = {
                        state: sum(row["status"] == state for row in inventory.values())
                        for state in ("planned", "queued", "running", "completed", "failed")}
                    ev.receipt["assertions"].append({
                        "name": "shard_publication_" + name, "passed": False,
                        "diagnostics": [diagnostic]})
                print(json.dumps(inventory[name]), file=sys.stderr, flush=True)
                if original is not None:
                    original.verification_diagnostics = inventory[name]["diagnostics"]
                    raise original.with_traceback(original.__traceback__)
                raise

    with ev.profile("parallel-components"):
        for name in inventory:
            transition(name, "queued")
        launch.set()
        results = {job[0]: execute(job) for job in jobs if job[0] in serial}
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {name: pool.submit(execute, (name, check, args, kwargs))
                       for name, check, args, kwargs in jobs if name not in serial}
            results.update((name, future.result()) for name, future in futures.items())
        return results


def report_failures(ev):
    for assertion in ev.receipt["assertions"]:
        if not assertion["passed"]:
            print(json.dumps({
                "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                **assertion,
            }), file=sys.stderr)


def reference_selftest(ev):
    cases = [
        (1, 0x3f80, 0x4000, 1, 0, 0x40000000, 0),
        (2, 0x3c00, 0x4000, 1, 0, 0x40000000, 0),
        (2, 1, 0x3c00, 1, 0, 0x33800000, 0),
        (1, 1, 0x3f80, 1, 0, 0x10000, 0),
        (1, 0x7f80, 0, 1, 0, 0x7fc00000, 16),
        (2, 0x7c01, 0, 0, 0x80000000, 0x80000000, 0),
        (1, 0x3f80bf80, 0x3f803f80, 3, 0, 0, 0),
    ]
    for precision, a, b, mask, seed, result, status in cases:
        assert dot_reference(precision, a, b, mask, seed)[:2] == (result, status)
    assert binary32(power_two(-150)) == (0, 3)
    assert binary32(3 * power_two(-150)) == (2, 3)
    assert binary32(1 + power_two(-24)) == (0x3f800000, 1)
    assert binary32(1 + 3 * power_two(-24)) == (0x3f800002, 1)
    ev.assertion("independent_reference_known_answers", True, comparisons=len(cases) + 4)


def leaf_check(ev, full, rtl_directory=None, simulator="iverilog"):
    simulator = simulation_tier(simulator, full=full, mutation=rtl_directory is not None)
    generated_at = time.monotonic()
    reference_selftest(ev)
    stimulus = ev.path / "leaf-input.txt"
    expected = ev.path / "leaf-expected.jsonl"
    trace = ev.path / "leaf-output.txt"
    count = 0
    with stimulus.open("w") as out, expected.open("w") as exp:
        def emit(reset, valid, vector, x):
            nonlocal count
            precision, a, b, mask, seed = vector
            result, status, bound = dot_reference(*vector)
            out.write(f"{reset} {valid} {precision} {a:032x} {b:032x} "
                      f"{mask:02x} {seed:08x} {x:08x}\n")
            exp.write(json.dumps({
                "rst_n": reset, "valid": valid, "x": x,
                "dot": [result, status], "grid_bound": bound,
                "precision": precision,
            }, separators=(",", ":")) + "\n")
            count += 1

        idle = (1, 0, 0, 0, 0)
        emit(0, 0, idle, 0)
        # Reset with every possible in-flight scalar age and dot stage.
        for phase in range(25):
            for age in range(phase):
                emit(1, 1, (1, 0x3f80, 0x3f80, 1, 0), 0x3f800000)
            emit(0, 0, idle, 0)
            for _ in range(25):
                emit(1, 0, idle, 0)
        for index, (vector, x) in enumerate(itertools.zip_longest(
            dot_vectors(full), scalar_vectors(full)
        )):
            emit(1, 1, vector or idle, 0x3f800000 if x is None else x)
            if index % 31 == 0:
                emit(1, 0, idle, 0)
        for _ in range(24):
            emit(1, 0, idle, 0)
    for path in (stimulus, expected):
        ev.receipt.setdefault("data_sha256", {})[str(path.relative_to(ROOT))] = digest(path)
    ev.elapsed("leaf-reference-generation", generated_at)
    simulator = simulation_tier(simulator, cycles=count)
    ev.assertion("leaf_simulation_tier", simulator == "verilator" or count <= 500000,
                 simulator=simulator, stimulus_cycles=count, full_vectors=full)
    rtl = sorted((rtl_directory or ROOT / "rtl").glob("*.sv"))
    executable = ev.path / ("leaf.vvp" if simulator == "iverilog" else "leaf.sim")
    argv = (["iverilog", "-g2012", "-Wall", "-s", "leaf_tb",
             "-DICARUS_SMOKE", "-o", str(executable.relative_to(ROOT))]
            if simulator == "iverilog" else [
                "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                "--top-module", "leaf_tb", "--Mdir",
                str((ev.path / "leaf-build").relative_to(ROOT)),
                "-o", str(executable.resolve())])
    compile_ok = compile_simulation(ev, "leaf-compile", [
        *argv, *[str(p.relative_to(ROOT)) for p in rtl], "tests/leaf_tb.sv",
    ], executable)
    if not ev.assertion("leaf_compile", compile_ok):
        return False
    run_ok = ev.run("leaf-simulate", [
        *(["vvp", str(executable.relative_to(ROOT))]
          if simulator == "iverilog" else [str(executable)]),
        "+input=" + str(stimulus.relative_to(ROOT)),
        "+output=" + str(trace.relative_to(ROOT)),
    ], timeout=86400)
    if not ev.assertion("leaf_behavior_latency_bubbles_reset_xz", run_ok):
        return False
    budget_ok = True
    if simulator == "iverilog":
        budget_ok = ev.assertion("leaf_icarus_measured_budget",
                                 ev.receipt["records"][-1]["elapsed_s"] < 60,
                                 elapsed_s=ev.receipt["records"][-1]["elapsed_s"],
                                 cycles=count, wall_clock_allowance_s=86400)
    compared_at = time.monotonic()
    pending = {}
    failures = []
    mismatch_counts = dict.fromkeys(("dot", "exp", "reciprocal", "rsqrt"), 0)
    comparisons = dict.fromkeys(mismatch_counts, 0)
    rows = 0
    with expected.open() as inputs, trace.open() as outputs:
        for cycle, (input_line, output_line) in enumerate(
            itertools.zip_longest(inputs, outputs)
        ):
            if input_line is None or output_line is None:
                raise ValueError(f"trace length mismatch at cycle {cycle}")
            row = json.loads(input_line)
            fields = output_line.split()
            if len(fields) != 13 or int(fields[0]) != cycle:
                raise ValueError(f"malformed simulator trace at cycle {cycle}")
            if not row["rst_n"]:
                pending.clear()
            elif row["valid"]:
                for name, latency in (("dot", 3), ("exp", 8),
                                      ("reciprocal", 16), ("rsqrt", 24)):
                    pending[cycle + latency - 1, name] = (cycle, row)
            for offset, name in enumerate(comparisons):
                valid = int(fields[1 + 3 * offset], 2)
                result = int(fields[2 + 3 * offset], 16)
                status = int(fields[3 + 3 * offset], 16)
                wanted = pending.pop((cycle, name), None)
                if valid != int(wanted is not None):
                    raise ValueError(f"reference valid mismatch {name} cycle {cycle}")
                if wanted is None:
                    if result or status:
                        raise ValueError(f"nonzero invalid output {name} cycle {cycle}")
                    continue
                launch, case = wanted
                comparisons[name] += 1
                passed = ([result, status] == case["dot"] if name == "dot" else
                          check_scalar(name, case["x"], result, status))
                if not passed:
                    mismatch_counts[name] += 1
                    if len(failures) < 32:
                        failures.append({
                            "operator": name, "launch_cycle": launch,
                            "observed_cycle": cycle, "input": case,
                            "result_hex": f"{result:08x}", "status": status,
                        })
            rows += 1
    assert rows == count and not pending
    ev.elapsed("leaf-reference-comparison", compared_at)
    (ev.path / "leaf-mismatches.json").write_text(json.dumps({
        "comparisons": comparisons, "mismatch_counts": mismatch_counts,
        "first_failures": failures, "full_vectors": full,
    }, indent=2) + "\n")
    return ev.assertion("leaf_independent_numerical", not any(mismatch_counts.values()),
                        comparisons=comparisons, mismatch_counts=mismatch_counts,
                        diagnostics=str((ev.path / "leaf-mismatches.json").relative_to(ROOT))) and budget_ok


def benchmark_contract(ev):
    return check_benchmark(ROOT, ev)


def synthesis_check(ev, top="anvil_q1_fp_top"):
    netlist = ev.path / (top + ".json")
    script = ev.path / (top + ".ys")
    commands = ["read_verilog -sv " + " ".join(
        str(p.relative_to(ROOT)) for p in sorted(ROOT.glob("rtl/*.sv")))]
    if top == "anvil_q1_fp_top":
        parameters = dict(NUM_LAYERS=1, HIDDEN_SIZE=8, INTERMEDIATE_SIZE=8,
                          NUM_Q_HEADS=1, NUM_KV_HEADS=1, HEAD_DIM=8,
                          GROUP_SIZE=1, VOCAB_SIZE=1, MAX_SEQ_LEN=1)
        commands.append("chparam " + " ".join(
            f"-set {key} {value}" for key, value in parameters.items()) + " " + top)
    commands += [
        f"hierarchy -check -top {top}", "proc", "opt", "check -assert",
        f"synth -top {top} -noabc", "check -assert", "stat",
        "write_json " + str(netlist.relative_to(ROOT)),
    ]
    script.write_text("\n".join(commands) + "\n")
    ev.receipt.setdefault("data_sha256", {})[str(script.relative_to(ROOT))] = digest(script)
    if not ev.run("yosys-" + top, ["yosys", "-Q", "-T", "-s",
                                  str(script.relative_to(ROOT))], timeout=86400):
        return ev.assertion("synthesis_" + top, False,
                            reason="Yosys command failed; raw tool diagnostics retained")
    data = json.loads(netlist.read_text())
    modules = data["modules"]
    visited = set()
    stack = [top]
    sequential = 0
    forbidden = []
    hierarchy = set()
    while stack:
        name = stack.pop()
        if name in visited:
            continue
        visited.add(name)
        module = modules[name]
        attributes = module.get("attributes", {})
        hierarchy.add(attributes.get("hdlname", name).split()[0].lstrip("\\"))
        if int(str(attributes.get("blackbox", "0")), 2):
            forbidden.append([name, "blackbox"])
        for cell_name, cell in module.get("cells", {}).items():
            cell_type = cell["type"]
            if cell_type in modules:
                stack.append(cell_type)
            elif "latch" in cell_type.lower() or cell_type in (
                    "$div", "$mod", "$divfloor", "$modfloor"):
                forbidden.append([name, cell_name, cell_type])
            elif "dff" in cell_type.lower():
                sequential += 1
            elif not cell_type.startswith("$"):
                forbidden.append([name, cell_name, "unknown cell " + cell_type])
    required = ({"anvil_q1_fp_decoder_layer", "anvil_q1_fp_rmsnorm",
                 "anvil_q1_fp_gemv", "anvil_q1_fp_rope",
                 "anvil_q1_fp_gqa_attention", "anvil_q1_fp_swiglu_mlp",
                 "anvil_q1_fp_elementwise", "anvil_q1_fp_exp",
                 "anvil_q1_fp_reciprocal", "anvil_q1_fp_rsqrt",
                 "anvil_q1_fp_dot8_mixed"} if top == "anvil_q1_fp_top" else
                {"anvil_q1_fp_reduce3"})
    missing = sorted(required - hierarchy)
    literal_missing = []
    if top == "anvil_q1_fp_top":
        expected_paths = (
            "memory_port", "decoder", "final_norm", "bus",
            "decoder.norm", "decoder.gemv", "decoder.rope",
            "decoder.attention", "decoder.mlp", "decoder.residual", "decoder.bus",
            "decoder.mlp.gemv", "decoder.mlp.silu_product", "decoder.mlp.bus",
        )
        for path in expected_paths:
            module = modules[top]
            for instance in path.split("."):
                cell = module.get("cells", {}).get(instance)
                if cell is None or cell["type"] not in modules:
                    literal_missing.append(path)
                    break
                module = modules[cell["type"]]
    return ev.assertion("synthesis_" + top,
                        not forbidden and sequential >= 100 and not missing and not literal_missing,
                        forbidden=forbidden, sequential_cells=sequential,
                        required_modules_missing=missing,
                        literal_hierarchy_missing=literal_missing,
                        netlist=str(netlist.relative_to(ROOT)))


def prerequisites(ev):
    tool_ok = ev.versions()
    dependency_ok = ev.run("reference-dependency-discovery", [
        sys.executable, "-c",
        "import importlib.util,json; "
        "print(json.dumps({name: importlib.util.find_spec(name) is not None "
        "for name in ('numpy','torch','transformers','tokenizers','safetensors','datasets','mpmath')}))",
    ], timeout=30)
    numpy_ok = ev.run("reference-numpy-import", [
        sys.executable, "-c", "import numpy; print(numpy.__version__)",
    ], timeout=30)
    ev.assertion("reference_numpy_import", numpy_ok,
                 reason="Production FP64 references require an importable NumPy; "
                        "dependency discovery alone is not availability validation")
    try:
        _, _, cases, _ = validate_input_manifests(ROOT, ev)
        files_ok = ev.assertion("prerequisite_input_manifests", True, cases=len(cases))
    except Exception as exc:
        files_ok = ev.assertion("prerequisite_input_manifests", False, reason=f"{type(exc).__name__}: {exc}")
    return tool_ok and dependency_ok and numpy_ok and files_ok


def compare_startup(model, trace, report):
    observed = [line.split() for line in trace.read_text().splitlines()]
    wanted_count = 2*model.config["H"]+1
    expected = model.events[:wanted_count]
    if not observed or observed[-1] != [
            "S", str(wanted_count), str(wanted_count), str(model.mode), str(model.seed)]:
        raise ValueError("missing acknowledged startup coverage")
    events = observed[:-1]
    if len(events) != wanted_count:
        raise ValueError("startup trace length mismatch")
    writes = 0
    for index, (actual, wanted) in enumerate(zip(events, expected)):
        if actual[0] != "M" or wanted[0] != "M" or len(actual) != 9:
            raise ValueError("malformed startup memory event")
        if tuple(map(int, actual[1:7])) != wanted[1:7]:
            raise ValueError("startup request address/order event " + str(index))
        if wanted[1]:
            raw = bits32(wanted[7]) if model.mode else round(wanted[7]*65536) & 0xffffffff
            if int(actual[7], 16) != raw:
                raise ValueError("startup embedding write mismatch")
            writes += 1
    passed = writes == model.config["H"]
    report.write_text(json.dumps({"passed": passed, "requests_compared": len(events),
                                  "exact_embedding_writes": writes,
                                  "scope": "Startup prefix only; no completed token"}, indent=2)+"\n")
    return passed


def startup_check(ev):
    return integration_check(ev, simulator="iverilog", startup=True)


def integration_check(ev, full=False, configurations=None, modes=None, seeds=None,
                      rtl_directory=None, simulator="verilator", startup=False):
    if configurations is None:
        configurations = CONFIGURATIONS if full else {"minimum": CONFIGURATIONS["minimum"]}
    if modes is None:
        modes = (0, 1, 2) if full else (1, 2, 0)
    if seeds is None:
        seeds = (17, 53, 89) if full else (17,)
    result = True
    for name, config in configurations.items():
        selected_simulator = simulation_tier(
            simulator, hidden=config[1], tokens=config[-1], seeds=len(seeds),
            full=full or not startup,
            mutation=rtl_directory is not None)
        ev.receipt.setdefault("simulation_routes", []).append({
            "configuration": name, "requested": simulator, "selected": selected_simulator,
            "tokens": config[-1], "seeds": list(seeds), "hidden": config[1]})
        # All subsequent choices use the selected tier, including probe entrypoints.
        requested_simulator = simulator
        simulator = selected_simulator
        binaries = {}
        for parent in ((False, True) if 0 in modes else (False,)):
            label = name + ("-parent" if parent else "-revised")
            executable = ev.path / (label + (".vvp" if simulator == "iverilog" else ".sim"))
            directory = ROOT / "anvil_q1_reference/rtl" if parent else rtl_directory or ROOT / "rtl"
            rtl = sorted(directory.glob("*.sv"))
            if simulator == "iverilog":
                argv = ["iverilog", "-g2012", "-Wall", "-s", "integration_tb",
                        "-DICARUS_SMOKE", "-o", str(executable.relative_to(ROOT))]
            elif simulator == "verilator":
                argv = [
                    "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                    "--top-module", "integration_tb", "--Mdir",
                    str((ev.path / (label + "-build")).relative_to(ROOT)),
                    "-o", str(executable.resolve()),
                ]
            else:
                raise ValueError("Unsupported simulator: " + simulator)
            if parent:
                argv.append("-DPARENT")
            parameter_prefix = "-Pintegration_tb." if simulator == "iverilog" else "-G"
            argv += [f"{parameter_prefix}{key}={value}"
                     for key, value in zip(PARAMETERS, config)]
            argv += [str(p.relative_to(ROOT)) for p in rtl] + ["tests/integration_tb.sv"]
            compiled = compile_simulation(ev, label + "-compile", argv, executable)
            result = ev.assertion(label + "_compile", compiled) and result
            if compiled:
                binaries[parent] = executable
        for mode in modes:
            for seed in seeds:
                label = f"{name}-mode{mode}-seed{seed}"
                fixture = ev.path / (label + ".hex")
                with ev.profile(label + "-reference-generation"):
                    model = Architecture(config, mode, seed)
                    model.write_fixture(fixture)
                    model.execute()
                ev.receipt.setdefault("data_sha256", {})[str(fixture.relative_to(ROOT))] = digest(fixture)
                traces = {}
                for parent in ((False, True) if mode == 0 else (False,)):
                    if parent not in binaries:
                        result = False
                        continue
                    suffix = "-parent" if parent else "-revised"
                    trace = ev.path / (label + suffix + ".trace")
                    command = (["vvp", str(binaries[parent].relative_to(ROOT))]
                               if simulator == "iverilog" else [str(binaries[parent])])
                    executed = ev.run(label + suffix, [
                        *command,
                        "+fixture=" + str(fixture.relative_to(ROOT)),
                        "+trace=" + str(trace.relative_to(ROOT)),
                        f"+mode={mode}", f"+seed={seed}",
                        f"+startup={int(startup)}",
                    ], timeout=86400)
                    result = ev.assertion(label + suffix + "_protocol", executed) and result
                    if executed and simulator == "iverilog":
                        record = ev.receipt["records"][-1]
                        result = ev.assertion(
                            label + suffix + "_icarus_measured_budget",
                            record["elapsed_s"] < 60, elapsed_s=record["elapsed_s"],
                            cycle_limit=500000, wall_clock_allowance_s=86400) and result
                    if executed:
                        traces[parent] = trace
                if False in traces:
                    report = ev.path / (label + "-reference.json")
                    with ev.profile(label + "-reference-comparison"):
                        compared = (compare_startup(model, traces[False], report) if startup else
                                    compare_trace(model, traces[False], report))
                    result = ev.assertion(
                        label + ("_startup_addresses_embedding" if startup else
                                 "_independent_architecture_numerical"), compared,
                        report=str(report.relative_to(ROOT))) and result
                if mode == 0 and len(traces) == 2:
                    def logical_trace(path):
                        return [line.split()[:-1] for line in path.read_text().splitlines()
                                if line.startswith(("M ", "O "))]
                    revised, parent = logical_trace(traces[False]), logical_trace(traces[True])
                    equal = revised == parent
                    result = ev.assertion(label + "_parent_differential", equal,
                                          events=len(revised),
                                          parent_events=len(parent)) and result
        simulator = requested_simulator
    return result


def static_check(ev):
    records = []
    for path in sorted(ROOT.glob("rtl/*.sv")):
        record = inspect_rtl(path)
        record["file"] = str(path.relative_to(ROOT))
        records.append(record)
    report = ev.path / "rtl-rules.json"
    report.write_text(json.dumps(records, indent=2) + "\n")
    rules_ok = ev.assertion("static_arithmetic_assignment_rules",
                            not any(r["violations"] for r in records),
                            report=str(report.relative_to(ROOT)))
    interfaces_ok = interface_check(ev)
    return rules_ok and interfaces_ok


def interface_check(ev):
    def header(path):
        ts = tokens(path.read_text())
        if ts[0] != "module":
            raise ValueError("expected module declaration: " + str(path))
        index = 2
        parameters = []
        if ts[index] == "#":
            end = matched(ts, index+1, "(", ")")
            parameters = ts[index+2:end]
            index = end+1
        if ts[index] != "(":
            raise ValueError("expected ANSI port list: " + str(path))
        end = matched(ts, index, "(", ")")
        return parameters, ts[index+1:end]

    pairs = (
        ("top", "fp_top"), ("decoder_layer", "fp_decoder_layer"),
        ("swiglu_mlp", "fp_swiglu_mlp"), ("w4a16_gemv", "fp_gemv"),
        ("gqa_attention", "fp_gqa_attention"), ("rope", "fp_rope"),
        ("rmsnorm", "fp_rmsnorm"), ("elementwise", "fp_elementwise"),
        ("mem_port", "mem_port"), ("bus_mux", "bus_mux"),
    )
    result = True
    for parent, revised in pairs:
        pp, ports = header(ROOT / f"anvil_q1_reference/rtl/anvil_q1_{parent}.sv")
        rp, revised_ports = header(ROOT / f"rtl/anvil_q1_{revised}.sv")
        if parent not in ("mem_port", "bus_mux"):
            ports += [",", "input", "wire", "[", "1", ":", "0", "]",
                      "precision_mode" if parent == "top" else "cmd_precision"]
        result = ev.assertion("parent_interface_" + parent,
                              pp == rp and ports == revised_ports,
                              parameters_equal=pp == rp,
                              ports_equal=ports == revised_ports) and result
    return result


def protocol_check(ev, simulator="verilator", modes=(0, 1, 2)):
    simulator = simulation_tier(simulator, protocol=True)
    config = (1, 8, 8, 1, 1, 8, 1, 3, 3)
    executable = ev.path / ("protocol.vvp" if simulator == "iverilog" else "protocol.sim")
    if simulator == "iverilog":
        argv = ["iverilog", "-g2012", "-Wall", "-s", "protocol_tb", "-o",
                str(executable.relative_to(ROOT))]
    elif simulator == "verilator":
        argv = [
            "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
            "--top-module", "protocol_tb", "--Mdir",
            str((ev.path / "protocol-build").relative_to(ROOT)),
            "-o", str(executable.resolve()),
        ]
    else:
        raise ValueError("Unsupported simulator: " + simulator)
    compiled = compile_simulation(ev, "protocol-compile", [
        *argv,
        *[str(p.relative_to(ROOT)) for p in sorted(ROOT.glob("rtl/*.sv"))],
        "tests/protocol_tb.sv",
    ], executable)
    if not ev.assertion("protocol_compile", compiled):
        return False
    result = True
    native_reference = {}
    for precision in (1, 2):
        model = Architecture(config, precision, 17)
        model.execute()
        native_reference[precision] = [
            event[2] for event in model.events
            if event[0] == "O" and event[3] == "position0/layer0/logits"]
    for mode in modes:
        fixture = ev.path / f"protocol-mode{mode}.hex"
        Architecture(config, mode, 17).write_fixture(fixture)
        ev.receipt.setdefault("data_sha256", {})[str(fixture.relative_to(ROOT))] = digest(fixture)
        alternate = ev.path / f"protocol-mode{mode}-alternate.hex"
        Architecture(config, (mode+1)%3, 17).write_fixture(alternate)
        ev.receipt["data_sha256"][str(alternate.relative_to(ROOT))] = digest(alternate)
        label = f"protocol-mode{mode}"
        command = (["vvp", str(executable.relative_to(ROOT))]
                   if simulator == "iverilog" else [str(executable)])
        executed = ev.run(label, [
            *command,
            "+fixture=" + str(fixture.relative_to(ROOT)),
            "+alternate_fixture=" + str(alternate.relative_to(ROOT)), f"+mode={mode}",
        ], timeout=86400)
        output = (ev.path / (label + ".stdout")).read_text()
        result = ev.assertion(label, executed and f"PROTOCOL_COVERAGE mode={mode} " in output,
                              coverage=[s for s in output.splitlines()
                                        if s.startswith("PROTOCOL_COVERAGE ")]) and result
        if executed:
            groups = {}
            for line in output.splitlines():
                if not line.startswith("RECOVERY_RESULT "):
                    continue
                _, recovery, precision, index, bits = line.split()
                key = int(recovery), int(precision)
                vector = groups.setdefault(key, [])
                if int(index) != len(vector):
                    raise ValueError("protocol recovery logit order mismatch")
                vector.append(float32(int(bits, 16)) if key[1] else int(bits, 16))
            numerical = {}
            for (recovery, precision), values in groups.items():
                if len(values) != config[-2]:
                    raise ValueError("protocol recovery logit count mismatch")
                if precision:
                    measurement = metrics(values, native_reference[precision])
                    measurement["passed"] = (
                        measurement["normalized_max_absolute_error"] <= 0.002 and (
                            measurement["reference_all_zero"] or
                            measurement["cosine"] is not None and measurement["cosine"] >= 0.9999))
                    numerical[f"recovery{recovery}/mode{precision}"] = measurement
            resets = [line for line in output.splitlines() if line.startswith("PUBLIC_RESPONSE_RESET ")]
            report = ev.path / (label+"-recovery-reference.json")
            report.write_text(json.dumps({"numerical": numerical,
                                          "public_response_resets": resets}, indent=2)+"\n")
            result = ev.assertion(
                label+"_recovery_fp64_and_public_response_resets",
                bool(numerical) and all(m["passed"] for m in numerical.values()) and len(resets) == 125,
                report=str(report.relative_to(ROOT))) and result
    return result


def portable_check(ev):
    destination = ev.path / "clean-project"
    destination.mkdir()
    selected = sources()
    for source in selected:
        target = destination / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    copied = {str(p.relative_to(destination)): digest(p) for p in sources(destination)}
    expected = {str(p.relative_to(ROOT)): digest(p) for p in selected}
    if not ev.assertion("clean_copy_exact_declared_inputs", copied == expected,
                        copied_sha256=copied):
        return False
    executed = ev.run("clean-copy-smoke", [
        sys.executable, "tests/verify.py", "--probe", "clean-smoke",
    ], timeout=86400, cwd=destination)
    output = (ev.path / "clean-copy-smoke.stdout").read_text().splitlines()
    if not output:
        return ev.assertion("clean_copy_all_modes_behavior_synthesis", False,
                            reason="No child receipt produced")
    child = json.loads(output[-1])
    receipt = destination / child["receipt"]
    if not receipt.resolve().is_relative_to(destination.resolve()):
        raise ValueError("clean-copy receipt escaped clean project")
    retained = json.loads(receipt.read_text())
    ev.receipt.setdefault("children", []).append(str(receipt.relative_to(ROOT)))
    assertions = {a["name"]: a["passed"] for a in retained["assertions"]}
    mandatory = ["synthesis_anvil_q1_fp_top", "leaf_independent_numerical"] + [
        f"minimum-mode{mode}-seed17_independent_architecture_numerical"
        for mode in (0, 1, 2)]
    return ev.assertion("clean_copy_all_modes_behavior_synthesis",
                        executed and child["status"] == "passed" and
                        all(assertions.get(name, False) for name in mandatory),
                        required_assertions=mandatory,
                        scope="Smallest legal configuration; not full-model reproduction")


def parameter_check(ev):
    names = ("NUM_LAYERS", "HIDDEN_SIZE", "INTERMEDIATE_SIZE",
             "NUM_Q_HEADS", "NUM_KV_HEADS", "HEAD_DIM", "GROUP_SIZE",
             "VOCAB_SIZE", "MAX_SEQ_LEN")
    minimum = dict(zip(names, CONFIGURATIONS["minimum"]))
    # The tuple order in CONFIGURATIONS places vocabulary and depth after G.
    minimum["AWQ_BITS"] = 4
    rtl = [str(p.relative_to(ROOT)) for p in sorted(ROOT.glob("rtl/*.sv"))]
    result = True
    for label, values in [("production", {})] + [
        (name, dict(zip(names, config))) for name, config in CONFIGURATIONS.items()
    ]:
        argv = ["iverilog", "-g2012", "-Wall", "-t", "null", "-s", "anvil_q1_fp_top"]
        argv += [f"-Panvil_q1_fp_top.{key}={value}" for key, value in values.items()]
        result = ev.assertion("legal_elaboration_" + label,
                              ev.run("elaborate-" + label, argv + rtl)) and result
    illegal = [(name.lower()+"_zero", {name: 0}) for name in names]
    illegal += [
        ("head_grouping", {"HIDDEN_SIZE": 24, "NUM_Q_HEADS": 3, "NUM_KV_HEADS": 2}),
        ("odd_head_dim", {"HIDDEN_SIZE": 56, "NUM_Q_HEADS": 8, "NUM_KV_HEADS": 8,
                          "HEAD_DIM": 7}),
        ("awq_bits", {"AWQ_BITS": 8}), ("group_divisibility", {"GROUP_SIZE": 3}),
        ("lane_divisibility", {"HIDDEN_SIZE": 10, "HEAD_DIM": 10, "INTERMEDIATE_SIZE": 10}),
        ("embedding_address_overflow", {"VOCAB_SIZE": 536870912}),
        ("sequence_limit", {"MAX_SEQ_LEN": 16777216}),
        ("cache_address_overflow", {"NUM_LAYERS": 536870912, "MAX_SEQ_LEN": 3}),
        ("matrix_address_overflow", {"HIDDEN_SIZE": 65536, "NUM_Q_HEADS": 8192}),
    ]
    for label, changes in illegal:
        values = {**minimum, **changes}
        executable = ev.path / ("illegal-" + label + ".vvp")
        argv = ["iverilog", "-g2012", "-Wall", "-s", "anvil_q1_fp_top",
                "-o", str(executable.relative_to(ROOT))]
        argv += [f"-Panvil_q1_fp_top.{key}={value}" for key, value in values.items()]
        compiled = ev.run("illegal-" + label + "-compile", argv + rtl)
        if not ev.assertion("illegal_" + label + "_diagnostic_elaborates", compiled):
            result = False
            continue
        ev.run("illegal-" + label + "-execute", ["vvp", str(executable.relative_to(ROOT))])
        record = ev.receipt["records"][-1]
        output = (ROOT / record["stdout"]).read_text() + (ROOT / record["stderr"]).read_text()
        rejected = (record["exit_code"] is not None and record["exit_code"] != 0 and
                    not record["timed_out"] and "ANVIL_Q1 PARAMETER ERROR" in output)
        result = ev.assertion("illegal_" + label + "_explicit_diagnostic", rejected,
                              exit_code=record["exit_code"]) and result
    return result


def preservation_check(ev):
    fixture = ev.path / "control-inventory-fixture.sv"
    checks = parser_selftest(fixture)
    ev.receipt.setdefault("data_sha256", {})[str(fixture.relative_to(ROOT))] = digest(fixture)
    parser_ok = True
    for name, passed in checks.items():
        parser_ok = ev.assertion("preservation_parser_" + name, passed) and parser_ok
    report = ev.path / "preservation-inventory.json"
    result = audit_preservation(ROOT, report, digest)
    audit_ok = ev.assertion(
        "preservation_independent_inventory", result["passed"],
        original_items=result["complete_original_denominator"],
        classification_counts=result["classification_counts"],
        unclassified_items=len(result["unclassified"]),
        threshold_percent=85, report=str(report.relative_to(ROOT)),
        diagnostics=result["failures"])
    from preservation_review import manual_audit
    binding_ok = True
    hashes = result["source_sha256"]
    cases = []
    for path in sorted(hashes):
        changed = dict(hashes, **{path: "0" * 64})
        cases.append(("changed_" + path, result["modules"], changed, "source audit"))
    removed = dict(hashes)
    removed.pop("rtl/anvil_q1_fp_top.sv")
    cases.append(("removed_source", result["modules"], removed, "source audit"))
    added = dict(hashes, **{"rtl/unreviewed.sv": "0" * 64})
    cases.append(("added_source", result["modules"], added, "source audit"))
    changed_inventory = json.loads(json.dumps(result["modules"]))
    changed_inventory["top"]["items"][0]["text"] += " changed"
    cases.append(("changed_inventory", changed_inventory, hashes, "inventory audit"))
    omitted_inventory = json.loads(json.dumps(result["modules"]))
    omitted_inventory["top"]["items"].pop()
    cases.append(("omitted_inventory_item", omitted_inventory, hashes, "inventory audit"))
    for name, modules, source_hashes, diagnostic in cases:
        rejected = False
        error_text = ""
        try:
           manual_audit(ROOT, modules, source_hashes)
        except ValueError as error:
           error_text = str(error)
           rejected = "requires renewed " + diagnostic in error_text
        binding_ok = ev.assertion(
           "preservation_binding_" + name, rejected,
           diagnostic=error_text) and binding_ok
    return parser_ok and audit_ok and binding_ok


def operator_check(ev, production=False, config=None, operations=None, cases=None):
    if config is None:
        config = PRODUCTION if production else CONFIGURATIONS["nonpower"]
    simulator = "verilator"
    result = True
    for name, op in OPERATOR_IDS.items():
        if operations is not None and name not in operations:
            continue
        binaries = {}
        selected_modes = {mode for operator, _, mode in cases if operator == name} if cases else {0, 1, 2}
        for parent in ((False, True) if 0 in selected_modes else (False,)):
            label = name + ("-parent" if parent else "-revised")
            executable = ev.path / (label + (".sim" if simulator == "verilator" else ".vvp"))
            if simulator == "verilator":
                argv = [
                    "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                    "--top-module", "operator_tb", "--Mdir",
                    str((ev.path / (label+"-build")).relative_to(ROOT)),
                    "-o", str(executable.resolve()),
                ]
                prefix = "-G"
            else:
                argv = ["iverilog", "-g2012", "-Wall", "-s", "operator_tb",
                        "-o", str(executable.relative_to(ROOT))]
                prefix = "-Poperator_tb."
            if parent:
                argv.append("-DPARENT")
            values = {"OP": op, **dict(zip(PARAMETERS, config))}
            argv += [f"{prefix}{key}={value}" for key, value in values.items()]
            rtl = ROOT / ("anvil_q1_reference/rtl" if parent else "rtl")
            argv += [str(p.relative_to(ROOT)) for p in sorted(rtl.glob("*.sv"))]
            argv.append("tests/operator_tb.sv")
            if simulator == "verilator":
                argv.append(str((ROOT / "tests/operator_input.cpp").resolve()))
                argv += ["-LDFLAGS", "-lz"]
            compiled = compile_simulation(ev, label+"-compile", argv, executable)
            result = ev.assertion(label+"_compile", compiled) and result
            if compiled:
                binaries[parent] = executable
        selectors = range(7) if name == "gemv" else (
            range(3) if name in ("norm", "elementwise") else (0,))
        if operations is not None:
            selectors = operations[name]
        for selector in selectors:
            for mode in (0, 1, 2):
                if cases is not None and (name, selector, mode) not in cases:
                    continue
                label = f"{name}-selector{selector}-mode{mode}"
                binary_oracle = ev.path / (label + ".requests.bin.gz")
                position = config[-1]-1 if name == "rope" else (
                    min(2, config[-1]-1) if name == "attention" else 0)
                budget = request_count(config, name, selector, mode, position)
                with ev.profile(label+"-reference-generation"), RequestWriter(
                        binary_oracle, limit=storage_limit(budget)) as stream:
                    reference = OperatorReference(config, mode, 17, stream)
                    reference.execute_operator(name, selector, position, config[0]-1)
                result = ev.assertion(label+"_independent_request_count",
                                      reference.count == budget,
                                      expected=budget, observed=reference.count) and result
                ev.receipt.setdefault("operator_inputs", {})[label] = stream.metadata
                ev.receipt.setdefault("data_sha256", {})[
                    str(binary_oracle.relative_to(ROOT))] = digest(binary_oracle)
                manifest = binary_oracle.with_suffix(".gz.json")
                ev.receipt["data_sha256"][str(manifest.relative_to(ROOT))] = digest(manifest)
                traces = {}
                for parent in ((False, True) if mode == 0 else (False,)):
                    if parent not in binaries:
                        result = False
                        continue
                    suffix = "-parent" if parent else "-revised"
                    trace = ev.path / (label+suffix+".trace")
                    command = (["vvp", str(binaries[parent].relative_to(ROOT))]
                               if simulator == "iverilog" else [str(binaries[parent])])
                    executed = ev.run(label+suffix, [
                        *command, "+oracle="+str(binary_oracle.relative_to(ROOT)),
                        "+oracle_binary="+str(binary_oracle.relative_to(ROOT)),
                        "+trace="+str(trace.relative_to(ROOT)),
                        f"+mode={mode}", "+seed=17", f"+selector={selector}",
                        f"+position={position}", f"+layer={config[0]-1}",
                    ], timeout=86400)
                    result = ev.assertion(label+suffix+"_architecture_protocol", executed) and result
                    if executed:
                        unchanged_input = digest(binary_oracle) == stream.metadata["compressed_sha256"]
                        result = ev.assertion(label+suffix+"_input_bytes_retained",
                                              unchanged_input) and result
                        published = publication(trace, ev.path / (label+suffix+".stdout"))
                        ev.receipt.setdefault("operator_traces", {})[label+suffix] = published
                        report = ev.path / (label+suffix+"-reference.json")
                        with ev.profile(label+suffix+"-reference-comparison"):
                            passed = compare_operator(reference, trace, report)
                        result = ev.assertion(label+suffix+"_reference", passed,
                                              report=str(report.relative_to(ROOT))) and result
                        traces[parent] = trace
                if mode == 0 and len(traces) == 2:
                    def writes(path):
                        return [line.split()[:-1] for line in path.read_text().splitlines()
                                if line.startswith("W ")]
                    revised, parent = writes(traces[False]), writes(traces[True])
                    result = ev.assertion(label+"_parent_differential",
                                          revised == parent and len(revised) > 0,
                                          writes=len(revised), parent_writes=len(parent)) and result
    assertion = ("production_operator_subset" if cases is not None or operations is not None else
                 "production_individual_operators" if production else "operator_smoke")
    return ev.assertion(assertion,
                        result, configuration=dict(zip(PARAMETERS, config)),
                        selected_cases=cases, selected_operations=operations,
                        scope="Synthetic isolated-operator engineering coverage, not benchmark") and result


def production_recovery(ev, prior):
    retained = json.loads(prior.read_text())
    dependencies = [p for p in sources()
                    if p.relative_to(ROOT).parts[0] in ("rtl", "anvil_q1_reference")]
    dependencies += [ROOT / "tests" / name for name in (
        "operator_tb.sv", "operator_input.cpp", "operators.py", "architecture.py",
        "numerical.py", "verify.py", "operator_storage.py")]
    changed = [str(path.relative_to(ROOT)) for path in dependencies
               if retained["source_sha256"].get(str(path.relative_to(ROOT))) != digest(path)]
    if changed:
        ev.assertion("stale_recovery_regenerates_all_cases", True, changed=changed)
        return operator_check(ev, production=True)
    assertions = {item["name"]: item for item in retained["assertions"]}
    records = {item["label"]: item for item in retained["records"]}
    class HashWriter:
        def __init__(self):
            self.hash = hashlib.sha256(REQUEST_MAGIC)

        def emit(self, write, key, raw):
            self.hash.update(REQUEST_RECORD.pack(write, *key, raw))

    unresolved, reused = [], []
    for name in OPERATOR_IDS:
        selectors = range(7) if name == "gemv" else (
            range(3) if name in ("norm", "elementwise") else (0,))
        for selector in selectors:
            for mode in (0, 1, 2):
                label = f"{name}-selector{selector}-mode{mode}"
                completed = True
                for suffix in (("-revised", "-parent") if mode == 0 else ("-revised",)):
                    record = records.get(label + suffix, {})
                    assertion = assertions.get(label + suffix + "_reference", {})
                    report = ROOT / assertion.get("report", "missing-reference-report")
                    complete = (record.get("exit_code") == 0 and
                                not record.get("timed_out", True) and
                                assertion.get("passed") is True and report.is_file())
                    if complete:
                        complete = all((ROOT / record[key]).is_file()
                                       for key in ("stdout", "stderr"))
                        ev.receipt.setdefault("reused_reports", {})[
                            str(report.relative_to(ROOT))] = digest(report)
                    completed = completed and complete
                if mode == 0:
                    completed = completed and assertions.get(
                        label + "_parent_differential", {}).get("passed") is True
                if completed:
                    stream = HashWriter()
                    position = PRODUCTION[-1]-1 if name == "rope" else (
                        min(2, PRODUCTION[-1]-1) if name == "attention" else 0)
                    reference = OperatorReference(PRODUCTION, mode, 17, stream)
                    reference.execute_operator(name, selector, position, PRODUCTION[0]-1)
                    oracle = prior.parent / (label + ".requests.bin.gz")
                    from operator_storage import inspect_requests
                    try:
                        completed = (oracle.is_file() and
                                     inspect_requests(oracle) == (reference.count, stream.hash.hexdigest()) and
                                     retained["data_sha256"].get(
                                         str(oracle.relative_to(ROOT))) == digest(oracle))
                        for suffix in (("-revised", "-parent") if mode == 0 else ("-revised",)):
                            trace = prior.parent / (label + suffix + ".trace")
                            published = publication(
                                trace, ROOT / records[label+suffix]["stdout"])
                            completed = (completed and published == retained.get(
                                "operator_traces", {}).get(label+suffix))
                            report = ev.path / (label + suffix + "-rechecked.json")
                            compared = compare_operator(reference, trace, report)
                            ev.receipt.setdefault("reused_raw_sha256", {})[
                                str(trace.relative_to(ROOT))] = digest(trace)
                            completed = compared and completed
                    except (OSError, ValueError) as error:
                        completed = False
                        ev.receipt.setdefault("recovery_rejected_raw", []).append(
                            {"case": label, "diagnostic": repr(error),
                             "action": "regenerate with unchanged assertions"})
                (reused if completed else unresolved).append((name, selector, mode))
    ev.assertion("completed_children_not_reclassified", True, reused=reused,
                 unresolved=unresolved, prior_status=retained["status"])
    operations = {name: sorted({selector for op, selector, _ in unresolved if op == name})
                  for name in OPERATOR_IDS if any(op == name for op, _, _ in unresolved)}
    if not unresolved:
        return True
    return operator_check(ev, production=True, operations=operations, cases=unresolved)


def top_address_check(ev):
    simulator = "verilator"
    result = True
    binaries = {}
    for parent in (False, True):
        label = "production-prefix-" + ("parent" if parent else "revised")
        executable = ev.path / (label + (".sim" if simulator == "verilator" else ".vvp"))
        if simulator == "verilator":
            argv = [
                "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                "--top-module", "top_address_tb", "--Mdir",
                str((ev.path / (label+"-build")).relative_to(ROOT)),
                "-o", str(executable.resolve()),
            ]
        else:
            argv = ["iverilog", "-g2012", "-Wall", "-s", "top_address_tb",
                    "-o", str(executable.relative_to(ROOT))]
        if parent:
            argv.append("-DPARENT")
        rtl = ROOT / ("anvil_q1_reference/rtl" if parent else "rtl")
        argv += [str(p.relative_to(ROOT)) for p in sorted(rtl.glob("*.sv"))]
        argv.append("tests/top_address_tb.sv")
        compiled = compile_simulation(ev, label+"-compile", argv, executable)
        result = ev.assertion(label+"_compile", compiled) and result
        if compiled:
            binaries[parent] = executable
    for mode in (0, 1, 2):
        label = f"production-prefix-mode{mode}"
        oracle = ev.path / (label+".requests")
        with oracle.open("w") as stream:
            reference = OperatorReference(PRODUCTION, mode, 17, stream)
            reference.group = "production/embedding-last-token"
            for col in range(PRODUCTION[1]):
                x = reference.read(0, row=PRODUCTION[-2]-1, col=col)
                reference.write(8, x, col=col)
            reference.read(8, row=0, col=0)
        ev.receipt.setdefault("data_sha256", {})[str(oracle.relative_to(ROOT))] = digest(oracle)
        for parent in ((False, True) if mode == 0 else (False,)):
            if parent not in binaries:
                result = False
                continue
            suffix = "-parent" if parent else "-revised"
            trace = ev.path / (label+suffix+".trace")
            command = (["vvp", str(binaries[parent].relative_to(ROOT))]
                       if simulator == "iverilog" else [str(binaries[parent])])
            executed = ev.run(label+suffix, [
                *command, "+oracle="+str(oracle.relative_to(ROOT)),
                "+trace="+str(trace.relative_to(ROOT)), f"+mode={mode}", "+seed=17",
            ], timeout=86400)
            result = ev.assertion(label+suffix+"_architecture_protocol", executed) and result
            if executed:
                report = ev.path / (label+suffix+"-reference.json")
                result = ev.assertion(
                    label+suffix+"_exact_embedding_and_addresses",
                    compare_operator(reference, trace, report, prefix_only=True),
                    report=str(report.relative_to(ROOT))) and result
    return ev.assertion("production_top_address_prefix", result,
                        token_id=PRODUCTION[-2]-1, embedding_words=PRODUCTION[1],
                        scope="Reset after embedding and first decoder request; not full inference") and result


def leaf_defect_check(ev):
    baseline = Evidence("leaf-defect-pristine")
    baseline.receipt["tool_versions_receipt"] = str((ev.path / "receipt.json").relative_to(ROOT))
    pristine = leaf_check(baseline, full=False, simulator="verilator")
    baseline.finish("passed" if pristine else "failed")
    ev.receipt.setdefault("children", []).append(str((baseline.path / "receipt.json").relative_to(ROOT)))
    if not ev.assertion("leaf_defect_pristine", pristine):
        return False
    recipes = (
        ("bf16_exponent_bias", "anvil_q1_fp_00_pkg.sv",
         "ea=(a[14:7]==0 ? -126 : $signed(32'({1'b0,a[14:7]}))-127)-10;",
         "ea=(a[14:7]==0 ? -126 : $signed(32'({1'b0,a[14:7]}))-126)-10;"),
        ("fp16_subnormal_hidden_bit", "anvil_q1_fp_00_pkg.sv",
         "sa={a[14:10]!=0,a[9:0]};", "sa={1'b1,a[9:0]};"),
        ("dot_valid_latency", "anvil_q1_fp_reduce3.sv",
         "assign out_valid=rst_n && valid3;", "assign out_valid=rst_n && valid2;"),
        ("wide_accumulator_cancellation", "anvil_q1_fp_00_pkg.sv",
         "aligned=$signed({5'd0,mag});", "aligned=$signed({5'd0,mag[63:40],40'd0});"),
    )
    passed = True
    for name, filename, before, after in recipes:
        child = Evidence("mutant-" + name)
        child.receipt["tool_versions_receipt"] = str((ev.path / "receipt.json").relative_to(ROOT))
        directory = child.path / "rtl"
        directory.mkdir()
        for path in sorted(ROOT.glob("rtl/*.sv")):
            shutil.copy2(path, directory / path.name)
        path = directory / filename
        source = path.read_text()
        if source.count(before) != 1:
            child.assertion("unique_mutation_site", False, mechanism=name)
            child.finish("failed")
            raise ValueError("mutation recipe no longer applies: " + name)
        path.write_text(source.replace(before, after))
        child.receipt["mutation"] = {
            "mechanism": name, "file": filename, "before": before, "after": after,
            "pristine_receipt": str((baseline.path / "receipt.json").relative_to(ROOT)),
            "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in directory.glob("*.sv")},
        }
        mutant_passed = False
        try:
            mutant_passed = leaf_check(child, full=False, rtl_directory=directory)
        finally:
            child.finish("passed" if mutant_passed else "failed")
        assertions = {a["name"]: a for a in child.receipt["assertions"]}
        numerical = assertions.get("leaf_independent_numerical", {}).get("mismatch_counts", {})
        simulator_stdout = child.path / "leaf-simulate.stdout"
        latency_rejection = name == "dot_valid_latency" and simulator_stdout.is_file() and any(
            message in simulator_stdout.read_text() for message in ("LATENCY", "DOT_BUBBLE_OR_X"))
        detected = assertions.get("leaf_compile", {}).get("passed", False) and (
            numerical.get("dot", 0) > 0 or latency_rejection) and not mutant_passed
        receipt = str((child.path / "receipt.json").relative_to(ROOT))
        ev.receipt.setdefault("children", []).append(receipt)
        passed = ev.assertion("defect_" + name, detected, receipt=receipt,
                              numerical_mismatches=numerical,
                              latency_rejection=latency_rejection) and passed
    return passed


def integration_defect_check(ev):
    recipes = (
        ("awq_nibble_permutation", "anvil_q1_fp_awq_dequant.sv",
         "0: shift=0; 1: shift=16; 2: shift=4; 3: shift=20;",
         "0: shift=0; 1: shift=4; 2: shift=16; 3: shift=20;",
         "minimum", 0),
        ("gqa7_kv_head_mapping", "anvil_q1_fp_gqa_attention.sv",
         "if(group_offset+1==RATIO)", "if(group_offset+1==RATIO+1)",
         "gqa14", 1),
        ("split_half_rope_mapping", "anvil_q1_fp_rope.sv",
         "? HEAD_DIM/2 : 0);", "? 1 : 0);", "minimum", 1),
        ("precision_latching", "anvil_q1_fp_top.sv",
         "1: if(issue) state<=2;",
         "1: if(issue) begin precision<=precision_mode; state<=2; end",
         "minimum", 1),
        ("stalled_logit_stability", "anvil_q1_fp_top.sv",
         "15: if(logit_ready) begin",
         "15: if(!logit_ready) native_sum<=native_sum^32'h00000001; else begin",
         "minimum", 1),
    )
    result = True
    for name, filename, before, after, configuration, mode in recipes:
        pristine = Evidence("integration-pristine-" + name)
        pristine.receipt["tool_versions_receipt"] = str((ev.path / "receipt.json").relative_to(ROOT))
        configurations = {configuration: (
            (1, 112, 8, 14, 2, 8, 8, 1, 1) if configuration == "gqa14"
            else CONFIGURATIONS[configuration])}
        simulator = "verilator"
        passed = integration_check(pristine, configurations=configurations,
                                   modes=(mode,), seeds=(17,), simulator=simulator)
        pristine.finish("passed" if passed else "failed")
        pristine_receipt = str((pristine.path / "receipt.json").relative_to(ROOT))
        ev.receipt.setdefault("children", []).append(pristine_receipt)
        if not ev.assertion("pristine_" + name, passed, receipt=pristine_receipt):
            result = False
            continue
        child = Evidence("mutant-" + name)
        child.receipt["tool_versions_receipt"] = str((ev.path / "receipt.json").relative_to(ROOT))
        directory = child.path / "rtl"
        directory.mkdir()
        for path in sorted(ROOT.glob("rtl/*.sv")):
            shutil.copy2(path, directory / path.name)
        path = directory / filename
        source = path.read_text()
        if source.count(before) != 1:
            raise ValueError("mutation recipe no longer unique: " + name)
        path.write_text(source.replace(before, after))
        child.receipt["mutation"] = {
            "mechanism": name, "file": filename, "before": before, "after": after,
            "pristine_receipt": pristine_receipt,
            "source_sha256": {str(p.relative_to(ROOT)): digest(p)
                              for p in directory.glob("*.sv")},
        }
        mutant_passed = False
        rejection = None
        try:
            mutant_passed = integration_check(
                child, configurations=configurations, modes=(mode,), seeds=(17,),
                rtl_directory=directory, simulator=simulator)
        except ValueError as error:
            rejection = str(error)
            child.assertion("architectural_reference_rejection", False,
                            diagnostic=rejection)
        finally:
            child.finish("passed" if mutant_passed else "failed")
        assertions = {a["name"]: a for a in child.receipt["assertions"]}
        compiled = assertions.get(configuration+"-revised_compile", {}).get("passed", False)
        comparison_failure = any(
            not a["passed"] and a["name"].endswith(
                ("_parent_differential", "_independent_architecture_numerical"))
            for a in child.receipt["assertions"])
        protocol_log = child.path / f"{configuration}-mode{mode}-seed17-revised.stdout"
        logit_rejected = (name == "stalled_logit_stability" and protocol_log.is_file()
                          and "LOGIT_STABILITY" in protocol_log.read_text())
        address_rejected = rejection is not None and rejection.startswith(
            ("request address/order event ", "event "))
        receipt = str((child.path / "receipt.json").relative_to(ROOT))
        ev.receipt.setdefault("children", []).append(receipt)
        result = ev.assertion("defect_" + name,
                              compiled and not mutant_passed and (
                                  comparison_failure or address_rejected or logit_rejected),
                              receipt=receipt, diagnostic=rejection,
                              comparison_rejection=comparison_failure,
                              stalled_logit_rejection=logit_rejected) and result
    return result


def scheduling_check(ev):
    from scheduling_checks import check
    return check(ROOT, ev)


def benchmark_fixture_check(ev):
    from benchmark_fixtures import check
    return check(ROOT, ev)


def operator_storage_check(ev):
    from operator_storage_checks import check
    return check(ev)


def critical_path_check(ev):
    results = parallel_components(ev, [
        ("production-gemv6-mode2", operator_check, (), {
            "production": True, "operations": {"gemv": (6,)},
            "cases": (("gemv", 6, 2),)}),
        ("integration-defects", integration_defect_check, (), {}),
        ("production-gemv4-mode0", operator_check, (), {
            "production": True, "operations": {"gemv": (4,)},
            "cases": (("gemv", 4, 0),)}),
        ("integration-gqa7-mode0-seed89", integration_check, (), {
            "full": True, "configurations": {"gqa7": CONFIGURATIONS["gqa7"]},
            "modes": (0,), "seeds": (89,)}),
        ("integration-layers24-mode2-seed89", integration_check, (), {
            "full": True, "configurations": {"layers24": CONFIGURATIONS["layers24"]},
            "modes": (2,), "seeds": (89,)}),
        ("leaves-full", leaf_check, (), {"full": True}),
        ("leaf-defects", leaf_defect_check, (), {}),
    ])
    return ev.assertion("bounded_critical_path_subset", all(results.values()),
                        results=results, full_l1_executed=False)


def protocol_shard_check(ev):
    results = parallel_components(ev, [
        (f"protocol-mode{mode}", protocol_check, (), {"modes": (mode,)})
        for mode in (0, 1, 2)])
    return all(results.values())


def l1_jobs():
    jobs = [
        ("benchmark-validator", benchmark_fixture_check, (), {}),
        ("operator-storage", operator_storage_check, (), {}),
        ("integration-defects", integration_defect_check, (), {}),
        ("synthesis-top", synthesis_check, (), {}),
    ]
    for mode in (1, 2, 0):
        for projection in (4, 6, 5, 0, 3, 1, 2):
            jobs.append((f"production-gemv{projection}-mode{mode}", operator_check, (), {
                "production": True, "operations": {"gemv": (projection,)},
                "cases": (("gemv", projection, mode),)}))
    for name in ("gqa7", "layers24", "nonpower", "minimum"):
        for mode in (0, 1, 2):
            for seed in (17, 53, 89):
                jobs.append((f"integration-{name}-mode{mode}-seed{seed}", integration_check, (), {
                    "full": True, "configurations": {name: CONFIGURATIONS[name]},
                    "modes": (mode,), "seeds": (seed,)}))
    for name in OPERATOR_IDS:
        if name != "gemv":
            selectors = (0, 1, 2) if name in ("norm", "elementwise") else (0,)
            for selector in selectors:
                for mode in (0, 1, 2):
                    jobs.append((f"production-{name}{selector}-mode{mode}", operator_check, (), {
                        "production": True, "operations": {name: (selector,)},
                        "cases": ((name, selector, mode),)}))
    jobs += [
        ("leaves-full", leaf_check, (), {"full": True}),
        *[(f"protocol-mode{mode}", protocol_check, (), {"modes": (mode,)})
          for mode in (0, 1, 2)],
        ("icarus-integration", startup_check, (), {}),
        ("icarus-leaves", leaf_check, (), {"full": False}),
        ("leaf-defects", leaf_defect_check, (), {}),
        ("synthesis-dot", synthesis_check, ("anvil_q1_fp_dot8",), {}),
        ("maximum-position", operator_check, (), {
            "config": (1, 8, 8, 1, 1, 8, 1, 1, 16777215),
            "operations": {"rope": (0,)}}),
        ("production-top-addresses", top_address_check, (), {}),
        ("parameters", parameter_check, (), {}),
        ("static", static_check, (), {}),
        ("preservation", preservation_check, (), {}),
        ("scheduling", scheduling_check, (), {}),
    ]
    return jobs


def main():
    global _BUILDS
    _BUILDS = BuildCache()
    parser = argparse.ArgumentParser()
    entry = parser.add_mutually_exclusive_group(required=True)
    entry.add_argument("--check", choices=(
        "prerequisites", "l1", "benchmark-contract", "portable"))
    entry.add_argument("--probe", choices=(
        "leaves", "synthesis-dot", "synthesis-top", "integration", "static", "parameters",
        "defects-leaves", "integration-matrix", "protocol", "clean-smoke",
        "leaves-full", "defects-integration", "integration-accelerated",
        "protocol-accelerated", "portable-smoke", "operators", "production-operators",
        "maximum-position", "production-top-addresses", "preservation", "input-inventory",
        "production-recovery", "benchmark-fixtures", "facilities", "integration-reconciliation",
        "receipt-publication", "interpreter-consistency", "scheduling", "critical-path",
        "protocol-shards"))
    parser.add_argument("--repair-of", type=Path)
    parser.add_argument("--diagnostic-repair-of", type=Path, action="append", default=[])
    parser.add_argument("--python-facility", type=Path, action="append", default=[])
    parser.add_argument("--reconciled-with", type=Path)
    args = parser.parse_args()
    try:
        ev = Evidence(args.check or args.probe)
    except Exception as error:
        print(json.dumps({"status": "failed", "receipt": None,
                          "diagnostics": getattr(error, "verification_diagnostics", [
                              exception_diagnostic(error, "initialization")])}),
              file=sys.stderr, flush=True)
        return 1
    ok = False
    try:
        if args.repair_of:
            prior = ROOT / args.repair_of
            ev.receipt["repair_of"] = {
                "path": str(prior.relative_to(ROOT)), "sha256": digest(prior),
            }
        for path in args.diagnostic_repair_of:
            previous = ROOT / path
            ev.receipt.setdefault("diagnostic_repairs", []).append(
                {"path": str(previous.relative_to(ROOT)), "sha256": digest(previous)})
        if args.probe == "leaves":
            ok = ev.versions() and leaf_check(ev, full=False)
        elif args.probe == "leaves-full":
            ok = ev.versions() and leaf_check(ev, full=True)
        elif args.probe == "synthesis-dot":
            ok = ev.versions() and synthesis_check(ev, "anvil_q1_fp_dot8")
        elif args.probe == "synthesis-top":
            ok = ev.versions() and component(ev, "synthesis-top-check", synthesis_check)
        elif args.probe == "static":
            ok = static_check(ev)
        elif args.probe == "parameters":
            ok = ev.versions() and parameter_check(ev)
        elif args.probe == "defects-leaves":
            ok = ev.versions() and leaf_defect_check(ev)
        elif args.probe == "defects-integration":
            ok = ev.versions() and integration_defect_check(ev)
        elif args.probe == "integration":
            ok = ev.versions() and integration_check(ev)
        elif args.probe == "integration-matrix":
            ok = ev.versions() and integration_check(ev, full=True)
        elif args.probe == "protocol":
            ok = ev.versions() and protocol_check(ev)
        elif args.probe == "protocol-accelerated":
            ok = ev.versions() and protocol_check(ev, simulator="verilator")
        elif args.probe == "integration-accelerated":
            ok = ev.versions() and integration_check(ev, full=True, simulator="verilator")
        elif args.probe == "clean-smoke":
            tools_ok = ev.versions()
            if tools_ok:
                leaves_ok = leaf_check(ev, full=False)
                startup_ok = component(ev, "clean-icarus-startup", startup_check)
                integration_ok = integration_check(ev, simulator="verilator")
                synthesis_ok = synthesis_check(ev)
                preservation_ok = preservation_check(ev)
                ok = leaves_ok and startup_ok and integration_ok and synthesis_ok and preservation_ok
        elif args.probe == "portable-smoke":
            ok = ev.versions() and portable_check(ev)
        elif args.probe in ("operators", "production-operators"):
            ok = ev.versions() and operator_check(
                ev, production=args.probe == "production-operators")
        elif args.probe == "maximum-position":
            ok = ev.versions() and operator_check(
                ev, config=(1, 8, 8, 1, 1, 8, 1, 1, 16777215),
                operations={"rope": (0,)})
        elif args.probe == "production-top-addresses":
            ok = ev.versions() and top_address_check(ev)
        elif args.probe == "preservation":
            ok = preservation_check(ev)
        elif args.probe == "input-inventory":
            ok = prerequisites(ev)
        elif args.probe == "production-recovery":
            if not args.repair_of:
                raise ValueError("production-recovery requires --repair-of receipt")
            ok = ev.versions() and production_recovery(ev, prior)
        elif args.probe == "benchmark-fixtures":
            from benchmark_fixtures import check as check_fixtures
            ok = check_fixtures(ROOT, ev)
        elif args.probe == "receipt-publication":
            from receipt_publication import check as check_publication
            ok = check_publication(ROOT, ev)
        elif args.probe == "interpreter-consistency":
            from interpreter_consistency import check as check_interpreter
            ok = check_interpreter(ROOT, ev)
        elif args.probe == "scheduling":
            ok = ev.versions() and scheduling_check(ev)
        elif args.probe == "critical-path":
            ok = ev.versions() and critical_path_check(ev)
        elif args.probe == "protocol-shards":
            ok = ev.versions() and protocol_shard_check(ev)
        elif args.probe == "facilities":
            from recovery import facilities
            ok = facilities(ROOT, ev, args.python_facility)
        elif args.probe == "integration-reconciliation":
            from recovery import reconcile_integration
            if not args.repair_of or not args.reconciled_with:
                raise ValueError("integration-reconciliation requires --repair-of and "
                                 "--reconciled-with receipts")
            ok = reconcile_integration(ROOT, ev, prior, ROOT / args.reconciled_with)
        elif args.check == "prerequisites":
            ok = prerequisites(ev)
        elif args.check == "benchmark-contract":
            ok = benchmark_contract(ev)
        elif args.check == "l1":
            tools_ok = ev.versions()
            if tools_ok:
                jobs = l1_jobs()
                # Its synthetic monkeypatches finish before concurrent work.
                results = parallel_components(ev, jobs, serial=("benchmark-validator",))
                benchmark_validator_ok = results["benchmark-validator"]
                static_ok = results["static"]
                parameters_ok = results["parameters"]
                synthesis_ok = results["synthesis-top"]
                dot_synthesis_ok = results["synthesis-dot"]
                leaves_ok = results["leaves-full"] and results["icarus-leaves"]
                defects_ok = results["leaf-defects"]
                integration_defects_ok = results["integration-defects"]
                protocol_ok = all(results[f"protocol-mode{mode}"] for mode in (0, 1, 2))
                icarus_ok = results["icarus-integration"]
                integration_ok = all(
                    results[f"integration-{name}-mode{mode}-seed{seed}"]
                    for name in CONFIGURATIONS for mode in (0, 1, 2) for seed in (17, 53, 89))
                operators_ok = all(
                    results[f"production-{name}{selector}-mode{mode}"]
                    for name in OPERATOR_IDS
                    for selector in (range(7) if name == "gemv" else
                                     range(3) if name in ("norm", "elementwise") else (0,))
                    for mode in (0, 1, 2))
                maximum_position_ok = results["maximum-position"]
                top_address_ok = results["production-top-addresses"]
                preservation_ok = results["preservation"]
                ok = (results["operator-storage"] and benchmark_validator_ok and static_ok and parameters_ok and synthesis_ok and
                      dot_synthesis_ok and leaves_ok and defects_ok and
                      integration_defects_ok and protocol_ok and icarus_ok and
                      integration_ok and operators_ok and maximum_position_ok and
                      top_address_ok and preservation_ok and results["scheduling"])
                covered = {
                    "integration_all_legal_modes_seeds": integration_ok,
                    "24_layer_integration": integration_ok,
                    "protocol_reset_fault_mode_recovery": protocol_ok,
                    "parent_differential": integration_ok and icarus_ok,
                    "nine_mechanism_defect_sensitivity": defects_ok and integration_defects_ok,
                    "illegal_parameter_diagnostics": parameters_ok,
                    "complete_hierarchy_synthesis": synthesis_ok and dot_synthesis_ok,
                    "static_arithmetic_assignment_rules": static_ok,
                    "production_individual_operators": operators_ok,
                    "production_addresses_schedule": (
                        operators_ok and maximum_position_ok and top_address_ok and integration_ok),
                    "preservation_independent_inventory": preservation_ok,
                }
                for name in REQUIRED_COVERAGE:
                    covered_ok = covered.get(name, False)
                    ev.assertion(name, covered_ok, reason=(
                        "Executed required checks" if name in covered else
                        "Required coverage not implemented yet"))
                    ok = covered_ok and ok
        elif args.check == "portable":
            ok = ev.versions() and portable_check(ev)
    except Exception as error:
        ev.receipt["assertions"].append({
            "name": "verification_exception", "passed": False,
            "diagnostics": getattr(error, "verification_diagnostics", [
                exception_diagnostic(error, "execution", ev.path)])})
        ok = False
    finally:
        ok = ok and all(a["passed"] for a in ev.receipt["assertions"])
        try:
            ev.finish("passed" if ok else "failed")
        except Exception as error:
            ok = False
            ev.receipt["status"] = "failed"
            ev.receipt["assertions"].append({
                "name": "final_publication", "passed": False,
                "diagnostics": [exception_diagnostic(error, "final-publication", ev.path)]})
    if not ok:
        report_failures(ev)
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
