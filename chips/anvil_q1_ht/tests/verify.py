#!/usr/bin/env python3
"""Source-bound L1 experiments. Partial probes never certify complete acceptance.

Command logs use exclusive, numbered paths even when labels repeat. Receipts bind
raw log hashes and sizes; successful finalization rechecks logs and snapshots.
These checks detect local evidence loss, not persistence across runtime handoff.
Receipt-write failures emit bounded in-memory progress to stderr for independent
runtime retention; that diagnostic never replaces missing source/log evidence.
Nested matrix cases retain their configuration and child receipt in that
diagnostic, since the parent's last command can precede the active child case.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiments import run_probe

ROOT = Path(__file__).resolve().parents[1]
SELECTORS = ("rtl/*.sv", "tests/*.py", "design/SPEC.md", "design/ARCHITECTURE.md",
             "design/anvil_q1_ht.qsf", "design/anvil_q1_ht.sdc", "anvil_q1_reference/rtl/*.sv")
NONPORTABLE_PATH = re.compile(r"(?:^|[\s\"'=(:,])/(?![/*])[A-Za-z0-9_.-]+/|[A-Za-z]:\\")


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def entry_command():
    """Portable direct-script invocation; runtime records remain authoritative."""
    argv = list(sys.orig_argv)
    script_index = argv.index(sys.argv[0], 1)
    script = Path(sys.argv[0]).resolve().relative_to(ROOT)
    argv[0] = "python3"
    argv[script_index] = str(script)
    return argv


def build_artifacts(build):
    artifacts = {**build["inputs"], build["executable"]: build["executable_sha256"]}
    command = build["compile_command"]
    for key in ("stdout", "stderr"):
        artifacts[command[key]] = command[key + "_sha256"]
    return artifacts


class Evidence:
    def __init__(self, probe, repair_of=None, source_root=None):
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.folder = ROOT / "evidence" / "preparation" / f"verifier-{probe}-{stamp}-{uuid.uuid4().hex[:8]}"
        self.folder.mkdir(parents=True, exist_ok=False)
        self.record = {"kind": "verifier_preparation", "probe": probe, "cwd": ".",
                       "entry_argv": entry_command(),
                       "start_time": utc(), "repair_of": repair_of, "source_sha256": {},
                       "commands": [], "observations": [], "acceptance_evidence": False}
        self.simulation_build_pool = {}
        self.create_receipt()
        source_root = ROOT if source_root is None else Path(source_root)
        for selector in SELECTORS:
            files = sorted(source_root.glob(selector))
            if not files:
                raise RuntimeError(f"required source selector is empty: {selector}")
            for path in files:
                relative = path.relative_to(source_root)
                snapshot = self.folder / "sources" / relative
                snapshot.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, snapshot)
                self.record["source_sha256"][str(relative)] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        self.flush()

    def relative(self, path):
        return str(Path(path).relative_to(ROOT))

    def create_receipt(self):
        with (self.folder / "receipt.json").open("x", encoding="utf-8") as stream:
            stat = os.fstat(stream.fileno())
            self.receipt_identity = (stat.st_dev, stat.st_ino)
            stream.write(json.dumps(self.record, indent=2) + "\n")

    def flush(self):
        # Never recreate a lost receipt or overwrite a replacement.
        path = self.folder / "receipt.json"
        try:
            payload = json.dumps(self.record, indent=2) + "\n"
            with path.open("r+", encoding="utf-8") as stream:
                stat = os.fstat(stream.fileno())
                if (stat.st_dev, stat.st_ino) != self.receipt_identity:
                    raise OSError("live receipt identity changed")
                stream.write(payload)
                stream.truncate()
                stream.flush()
                current = path.stat()
                if (current.st_dev, current.st_ino) != self.receipt_identity:
                    raise OSError("live receipt identity changed during update")
        except OSError as exc:
            print(json.dumps({
                "event": "receipt_update_failed",
                "receipt": self.relative(path),
                "error_type": type(exc).__name__,
                "errno": exc.errno,
                "os_error": exc.strerror,
                "expected_receipt_identity": {
                    "device": self.receipt_identity[0],
                    "inode": self.receipt_identity[1],
                },
                "progress_at_failure": {
                    "entry_argv": self.record.get("entry_argv"),
                    "probe": self.record.get("probe"),
                    "command_count": len(self.record["commands"]),
                    "last_command": (self.record["commands"][-1]
                                     if self.record["commands"] else None),
                    "campaign": [
                        {key: stage[key] for key in ("probe", "outcome", "start_time", "end_time")
                         if key in stage}
                        for stage in self.record.get("mandatory_campaign", [])
                    ],
                    "integration_matrix": [
                        {key: case[key] for key in (
                            "configuration", "seed", "mode", "outcome", "receipt",
                            "tokens", "ordered_logits", "accepted_DDR_read_beats",
                            "initial_preload_beats") if key in case}
                        for case in self.record.get("integration_matrix", [])
                    ],
                    "source_binding_count": len(self.record["source_sha256"]),
                    "source_bindings_sha256": hashlib.sha256(
                        json.dumps(self.record["source_sha256"], sort_keys=True).encode()
                    ).hexdigest(),
                },
                "evidence_recreated": False,
                "acceptance_evidence": False,
                "scope": "retention_failure_not_RTL_diagnosis_or_storage_repair",
            }), file=sys.stderr, flush=True)
            raise

    def command(self, argv, label, timeout=3600, expected_codes=(0,), cwd=None):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", label):
            raise ValueError("command labels must be plain filenames")
        workdir = ROOT if cwd is None else Path(cwd)
        if not workdir.resolve().is_relative_to(ROOT):
            raise ValueError("verification children must run within the project")
        ordinal = len(self.record["commands"])
        prefix = f"{ordinal:05d}-{label}"
        stdout = self.folder / (prefix + "-stdout.log")
        stderr = self.folder / (prefix + "-stderr.log")
        entry = {"label": label, "argv": list(map(str, argv)), "cwd": str(workdir.relative_to(ROOT)),
                 "start_time": utc(),
                 "timeout_seconds": timeout, "stdout": self.relative(stdout),
                 "stderr": self.relative(stderr), "timed_out": False}
        self.record["commands"].append(entry)
        self.flush()
        started = time.monotonic()
        child_times = os.times()
        process = None
        try:
            with stdout.open("xb") as out, stderr.open("xb") as err:
                process = subprocess.Popen(entry["argv"], cwd=workdir, stdout=out, stderr=err)
                entry["pid"] = process.pid
                try:
                    self.flush()
                    try:
                        process.wait(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        entry["timed_out"] = True
                finally:
                    # Receipt failure must not leave a launched child running.
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=30)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                    entry["process_settled"] = process.poll() is not None
                code = process.returncode
        except OSError as exc:
            code = None if process is None else process.returncode
            entry["launch_error" if process is None else "execution_error"] = str(exc)
        entry.update(exit_code=code, end_time=utc(), elapsed_seconds=time.monotonic() - started)
        settled_times = os.times()
        entry["sequential_child_user_seconds"] = settled_times.children_user - child_times.children_user
        entry["sequential_child_system_seconds"] = settled_times.children_system - child_times.children_system
        for key, path in (("stdout", stdout), ("stderr", stderr)):
            if not path.is_file():
                entry[key + "_missing"] = True
            else:
                entry[key + "_sha256"] = file_sha256(path)
                entry[key + "_bytes"] = path.stat().st_size
        self.flush()
        if entry.get("launch_error"):
            raise RuntimeError(f"{label} launch failed: {entry['launch_error']}")
        if entry.get("execution_error"):
            raise RuntimeError(f"{label} execution failed: {entry['execution_error']}")
        if entry.get("stdout_missing") or entry.get("stderr_missing"):
            raise RuntimeError(f"{label}: raw command evidence disappeared")
        text = stdout.read_text() + stderr.read_text()
        if code not in expected_codes or entry["timed_out"]:
            raise RuntimeError(f"{label} failed (exit={code}, timeout={entry['timed_out']}):\n{text[-8000:]}")
        return text

    def simulate(self, name, bench, sources=None, rtl_root=None, timeout=3600,
                 simulator=None, defines=(), cxx_optimization="-O3", flatten=False,
                 runtime_args=(), build_pool=None):
        simulator = simulator or getattr(self, "default_simulator", "iverilog")
        if cxx_optimization not in ("-Os", "-O3"):
            raise ValueError("unsupported C++ optimization")
        if shutil.which(simulator) is None:
            raise RuntimeError(f"required simulation tool unavailable: {simulator}")
        folder = self.folder / name
        folder.mkdir(exist_ok=False)
        tb = folder / "tb.sv"
        tb.write_text(bench)
        source_dir = rtl_root or getattr(self, "rtl_root", self.folder / "sources/rtl")
        if sources is None:
            sources = sorted(source_dir.glob("*.sv"))
        else:
            sources = [source_dir / source for source in sources]
        inputs = [self.relative(path) for path in sources] + [self.relative(tb)]
        if simulator == "iverilog":
            image = folder / "simulation.vvp"
            argv = ["iverilog", "-g2012", "-Wall", "-s", "tb",
                    *["-D" + value for value in defines], "-o", self.relative(image), *inputs]
            self.command(argv, name + "-compile")
            command = ["vvp", self.relative(image)]
        elif simulator == "verilator":
            version = self.command(["verilator", "--version"], name + "-tool-version")
            compiler = self.command(["g++", "--version"], name + "-compiler-version")
            build = folder / "compiled"
            options = ["--binary", "--timing", "--assert", "-Wno-fatal",
                       "-j", "2", "-CFLAGS", cxx_optimization,
                       *(["--flatten"] if flatten else []),
                       "--top-module", "tb", *["-D" + value for value in defines]]
            identity = {
                "schema": 1, "verilator": version, "compiler": compiler,
                "options": options, "bench_sha256": file_sha256(tb),
                "geometry": self.record.get("engineering_fixture", {}).get(
                    "shape", self.record.get("simulation_geometry")),
                "sources": [(path.name, file_sha256(path)) for path in sources],
            }
            key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
            cached = None if build_pool is None else build_pool.get(key)
            if cached is None:
                self.command(
                    ["verilator", *options, "--Mdir", self.relative(build), *inputs],
                    name + "-compile", timeout=3600)
                executable = build / "Vtb"
                cached = {
                    "identity": identity, "key": key,
                    "producer_receipt": self.relative(self.folder / "receipt.json"),
                    "executable": self.relative(executable),
                    "executable_sha256": file_sha256(executable),
                    "compile_command": dict(self.record["commands"][-1]),
                    "inputs": {self.relative(path): file_sha256(path)
                               for path in [*sources, tb]},
                }
                if build_pool is not None:
                    build_pool[key] = cached
                reused = False
            else:
                reused = True
            for path, digest in build_artifacts(cached).items():
                if file_sha256(ROOT / path) != digest:
                    raise RuntimeError("compiled simulation build changed: " + path)
            self.record.setdefault("simulation_builds", []).append(
                {**cached, "reused": reused, "runtime_args": list(runtime_args)})
            self.flush()
            command = [cached["executable"]]
        else:
            raise ValueError(f"unsupported simulation tool: {simulator}")
        output = self.command([*command, *runtime_args], name + "-simulation", timeout=timeout)
        if "CHECKS_PASSED " not in output:
            raise AssertionError(f"{name}: missing completed assertion ledger")
        ledgers = []
        for line in output.splitlines():
            if line.startswith(("CHECKS_PASSED ", "TOKEN_COMPARED ")):
                fields = dict(re.findall(r"([a-zA-Z_][a-zA-Z_0-9]*)=([^\s]+)", line))
                ledgers.append({key: int(value) if value.isdecimal() else value
                                for key, value in fields.items()})
        self.record["observations"].append({"name": name, "transcript": output.strip(),
                                           "observed_counters": ledgers})
        self.flush()
        return output

    def finish(self, outcome, reason):
        if outcome in ("probe_passed", "packaging_subset_passed"):
            missing_or_changed = []
            artifacts = {
                self.relative(self.folder / "sources" / name): digest
                for name, digest in self.record["source_sha256"].items()
            }
            for command in self.record["commands"]:
                for key in ("stdout", "stderr"):
                    artifacts[command[key]] = command.get(key + "_sha256")
            artifacts.update(self.record.get("runtime_input_sha256", {}))
            for build in self.record.get("simulation_builds", []):
                artifacts.update(build_artifacts(build))
            for relative, expected in artifacts.items():
                path = ROOT / relative
                if expected is None or not path.is_file() or file_sha256(path) != expected:
                    missing_or_changed.append(relative)
            if missing_or_changed:
                reason = "Missing or changed retained command/source evidence: " + ", ".join(missing_or_changed)
                self.record.update(end_time=utc(), outcome="failed_evidence_changed", reason=reason)
                self.flush()
                raise RuntimeError(reason)
            current = {
                str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for selector in SELECTORS for path in ROOT.glob(selector)
            }
            if current != self.record["source_sha256"]:
                reason = ("Declared sources changed during execution; retained observations bind "
                          "only the frozen snapshots, not the current delivery.")
                self.record.update(end_time=utc(), outcome="failed_source_changed", reason=reason)
                self.flush()
                raise RuntimeError(reason)
        self.record.update(end_time=utc(), outcome=outcome, reason=reason)
        self.flush()
        print(json.dumps({"outcome": outcome, "reason": reason,
                          "receipt": self.relative(self.folder / "receipt.json")}), flush=True)


def clean_reproduction(evidence, fixture_root, seed):
    from fixtures import FILES, PINNED, project_path

    supplied = project_path(fixture_root)
    evidence.command(["python3", "tests/fixtures.py", "--root", str(supplied)],
                     "supplied-fixture-validation")
    clone = Path(tempfile.mkdtemp(prefix="clean-project-", dir=evidence.folder))
    evidence.record["clean_reproduction"] = {
        "scope": "packaging_subset_not_full_L1_or_native_acceptance",
        "directory": evidence.relative(clone), "fixture_root": str(supplied),
        "seed": seed, "copied_sources": {}, "copied_fixtures": {},
        "completed_probes": [],
    }
    record = evidence.record["clean_reproduction"]
    for relative, expected_digest in evidence.record["source_sha256"].items():
        source = evidence.folder / "sources" / relative
        text = source.read_text()
        if NONPORTABLE_PATH.search(text):
            raise ValueError(f"nonportable private path in deliverable: {relative}")
        destination = clone / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        if digest != expected_digest:
            raise AssertionError(f"clean source copy differs: {relative}")
        record["copied_sources"][relative] = digest
    inputs = [Path("manifest.json")]
    inputs += [Path(mode.lower()) / filename for mode in PINNED for filename in FILES]
    manifest = json.loads((supplied / "manifest.json").read_text())
    inputs += [project_path(model["metadata_file"]) for model in manifest["models"].values()]
    for relative in inputs:
        source = supplied / relative
        if source.is_symlink() or not source.resolve().is_relative_to((ROOT / supplied).resolve()):
            raise ValueError(f"fixture dependency escapes supplied bundle: {source}")
        destination = clone / "fixtures/qwen2.5-0.5b" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        record["copied_fixtures"][str(relative)] = {
            "size": destination.stat().st_size,
            "sha256": file_sha256(destination),
        }
    evidence.flush()
    evidence.command(["python3", "tests/fixtures.py"], "clean-fixture-validation",
                     cwd=clone)
    for probe in ("dequant", "tensor", "top-awq", "top-bf16", "dma", "kv", "synthesis-small"):
        output = evidence.command(
            ["python3", "tests/verify.py", "--probe", probe, "--seed", str(seed), "--config", "0"],
            "clean-" + probe, timeout=14400, cwd=clone)
        results = [json.loads(line) for line in output.splitlines() if line.startswith("{")]
        if len(results) != 1 or results[0].get("outcome") != "probe_passed":
            raise AssertionError(f"clean {probe}: missing actual successful child receipt")
        child_path = project_path(results[0]["receipt"])
        receipt = json.loads((clone / child_path).read_text())
        if (receipt.get("source_sha256") != record["copied_sources"] or
                not receipt.get("observations") or not receipt.get("commands") or
                any(command.get("exit_code") != 0 or command.get("timed_out") or
                    not command.get("process_settled") for command in receipt["commands"])):
            raise AssertionError(f"clean {probe}: missing source-bound settled comparisons")
        record["completed_probes"].append({
            "probe": probe, "receipt": evidence.relative(clone / child_path),
            "outcome": receipt["outcome"],
        })
        evidence.flush()


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=("tensor", "dequant", "math", "top-awq", "top-bf16",
                                           "csr-upload", "synthesis", "kv", "parameters", "dma",
                                           "sensitivity", "dma-pipeline-sensitivity",
                                           "arithmetic-sensitivity",
                                           "faults", "orphan-fault", "abort-states",
                                           "synthesis-small", "synthesis-control", "fixture-integrity",
                                           "dma-compiled",
                                           "kernel-default", "projection-default", "projection-k",
                                           "layer-awq", "layer-bf16", "layer-sensitivity",
                                           "arithmetic-default",
                                           "integration-matrix", "matrix-config", "compatibility",
                                           "compatibility-matrix", "bf16-default", "vocabulary-default",
                                           "checkpoint-repack", "retention", "retention-audit",
                                           "retention-diagnosis"),
                        help="bounded advisory experiment")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--config", type=int, choices=(0, 1, 2), default=0)
    parser.add_argument("--repair-of")
    parser.add_argument("--retention-of", help="earlier project-relative retention receipt to audit")
    parser.add_argument("--clean-repro", action="store_true")
    parser.add_argument("--fixture-root", default="fixtures/qwen2.5-0.5b",
                        help="project-relative, hash-validated pinned checkpoint bundle")
    args = parser.parse_args()
    if args.retention_of and args.probe not in ("retention-audit", "retention-diagnosis"):
        parser.error("--retention-of requires --probe retention-audit or retention-diagnosis")
    if args.probe in ("retention-audit", "retention-diagnosis") and not args.retention_of:
        parser.error("retention audit/diagnosis requires --retention-of")
    evidence = Evidence(args.probe or ("clean-repro" if args.clean_repro else "mandatory"),
                        args.repair_of)
    evidence.record["seed"] = args.seed
    evidence.record["configuration_index"] = args.config
    evidence.flush()
    try:
        for tool, version_args in (("python3", ["--version"]), ("iverilog", ["-V"]),
                                   ("vvp", ["-V"]), ("yosys", ["-V"]),
                                   ("verilator", ["--version"])):
            if shutil.which(tool) is None:
                raise RuntimeError(f"required verification tool unavailable: {tool}")
            evidence.command([tool, *version_args], tool + "-version")
        evidence.command(["python3", "-B", "tests/retention_checks.py"],
                         "retention-harness-regression")
        evidence.command(["python3", "-B", "tests/evidence_checks.py", "--scratch",
                          evidence.relative(evidence.folder / "command-harness-scratch")],
                         "command-evidence-regression")
        evidence.command(["python3", "-B", "tests/simulation_checks.py", "--regression-child",
                          "--scratch", evidence.relative(evidence.folder / "simulation-harness-scratch")],
                         "simulation-build-reuse-regression")
        if args.probe in ("retention", "retention-audit", "retention-diagnosis"):
            from retention import audit, diagnose, run
            if args.probe == "retention":
                run(evidence)
            elif args.probe == "retention-diagnosis":
                diagnose(evidence, args.retention_of)
            else:
                audit(evidence, args.retention_of)
            evidence.finish("probe_passed", "Bounded retention diagnostic only; "
                            "no storage repair or engineering acceptance is established.")
            return 0
        if args.probe:
            run_probe(evidence, args.probe, args.seed, args.config)
            evidence.finish("probe_passed", "Only the named advisory scope completed.")
            return 0
        if args.clean_repro:
            clean_reproduction(evidence, args.fixture_root, args.seed)
            evidence.finish("packaging_subset_passed",
                            "Fresh-directory numerical, DMA/KV and synthesis subset only; "
                            "mandatory L1 and native acceptance remain separate.")
            return 0
        campaign = (
            "fixture-integrity", "checkpoint-repack", "parameters", "dequant", "tensor", "math",
            "dma", "kv", "csr-upload", "integration-matrix", "faults",
            "orphan-fault", "abort-states", "compatibility-matrix", "sensitivity", "synthesis-control",
            "synthesis", "kernel-default", "projection-default", "bf16-default",
            "vocabulary-default", "layer-awq", "layer-bf16",
        )
        ledger = [{"probe": name, "outcome": "not_run"} for name in campaign]
        evidence.record["mandatory_campaign"] = ledger
        evidence.record["unclosed_L1_requirements"] = [
            "complete observed directed-coverage ledger, including reset during active traffic",
            "parent compatibility command/error/logit comparisons",
            "D1 measured DDR service and compute-consumed bandwidth",
            "D2 matched packed-weight arithmetic baseline and compute-only measurements",
            "D2 default-dimension BF16 and vocabulary projection benchmarks",
            "D3 separately measured hot-window and full-context cold retrieval",
            "D4 complete default-dimension decoder-layer comparisons",
            "D5 checkpoint repacking, tokenizer, independent full-model reference and bridge workloads",
            "accepted-parent fixed-point versus independent software-model discrepancy report",
        ]
        evidence.flush()
        for stage in ledger:
            stage.update(outcome="running", start_time=utc())
            evidence.flush()
            try:
                run_probe(evidence, stage["probe"], args.seed, 0)
            except (OSError, RuntimeError, AssertionError, ValueError) as exc:
                stage.update(outcome="failed", end_time=utc(), reason=str(exc))
                evidence.flush()
                raise
            stage.update(outcome="completed", end_time=utc())
            evidence.flush()
        raise RuntimeError(
            "The mandatory L1 campaign is incomplete: " +
            "; ".join(evidence.record["unclosed_L1_requirements"]) +
            ". Completed stages, acquired input identity and clean reproduction "
            "cannot replace these requirements.")
    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
        evidence.finish("failed", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
