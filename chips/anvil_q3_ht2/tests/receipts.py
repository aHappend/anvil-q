"""Immutable, project-relative receipts for project-owned verification children."""

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]


def utc():
    return datetime.now(timezone.utc).isoformat()


def sources():
    return sorted(path for pattern in ("rtl/*.sv", "design/*.md", "fpga/*",
                                       "tests/*", "anvil_q3_ht_reference/rtl/*.sv")
                  for path in ROOT.glob(pattern) if path.is_file())


def hashes(paths):
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def new_run(stem, preparation=False, repair_of=None):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = ROOT / "evidence" / (
        f"preparation/{stem}-{timestamp}" if preparation else f"l1-{stem}-{timestamp}")
    path.mkdir(parents=True, exist_ok=False)
    snapshot = path / "source-snapshot"
    captured = sources()
    for source in captured:
        target = snapshot / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    (path / "source-hashes.json").write_text(json.dumps(hashes(captured), indent=2) + "\n")
    if repair_of is not None:
        prior = ROOT / repair_of
        if not prior.is_file() or not prior.is_relative_to(ROOT / "evidence"):
            raise ValueError("repair_of must identify an existing project evidence receipt")
        (path / "repair-of.json").write_text(json.dumps(
            {"receipt": repair_of, "sha256": hashlib.sha256(prior.read_bytes()).hexdigest()},
            indent=2) + "\n")
    return path


def execute(run, name, argv, version_argv, *, cwd=None, expect=0):
    cwd = ROOT if cwd is None else Path(cwd)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    location = run / f"{name}-{timestamp}"
    location.mkdir(exist_ok=False)
    inputs = []
    for argument in map(str, argv):
        if argument.startswith("+") and "=" in argument:
            argument = argument.split("=", 1)[1]
        candidate = (cwd / argument).resolve()
        if candidate.is_relative_to(ROOT) and candidate.is_file():
            inputs.append(candidate)
    input_hashes = hashes(inputs)
    receipt = {
        "argv": list(map(str, argv)),
        "cwd": str(cwd.relative_to(ROOT)),
        "source_sha256": hashes(sources()),
        "input_sha256": input_hashes,
        "tool_version_argv": version_argv,
        "tool_version_exit_code": None,
        "tool_version": None,
        "started_at": utc(), "timeout_s": None, "timed_out": False,
        "execution_started": False, "exit_code": None,
        "shared_deadline_monotonic": os.environ.get("HT2_L1_DEADLINE"),
        "stdout_path": str((location / "stdout.txt").relative_to(ROOT)),
        "stderr_path": str((location / "stderr.txt").relative_to(ROOT)),
    }
    if (run / "repair-of.json").is_file():
        receipt["repair_of"] = json.loads((run / "repair-of.json").read_text())
    started = time.monotonic()
    for filename in ("stdout.txt", "stderr.txt", "version.stdout.txt",
                     "version.stderr.txt"):
        (location / filename).touch(exist_ok=False)
    try:
        inherited = os.environ.get("HT2_L1_DEADLINE")
        if inherited is None:
            raise RuntimeError("missing inherited HT2_L1_DEADLINE; no tool launched")
        deadline = float(inherited)
        if not math.isfinite(deadline):
            raise ValueError("HT2_L1_DEADLINE must be a finite monotonic deadline")
        limit = 600 if Path(str(argv[0])).name == "vvp" else 2700
        child_deadline = min(deadline, started + limit)

        def remaining():
            left = child_deadline - time.monotonic()
            if left <= 0:
                receipt["timed_out"] = True
                raise RuntimeError("shared check execution budget exhausted")
            return left

        receipt["timeout_s"] = remaining()
        with (location / "version.stdout.txt").open("wb") as stdout, (
                location / "version.stderr.txt").open("wb") as stderr:
            try:
                version = subprocess.run(version_argv, cwd=ROOT, stdout=stdout,
                                         stderr=stderr, timeout=remaining())
            except subprocess.TimeoutExpired:
                receipt["timed_out"] = True
                raise
        receipt["tool_version_exit_code"] = version.returncode
        version_lines = ((location / "version.stdout.txt").read_text() +
                         (location / "version.stderr.txt").read_text()).splitlines()
        receipt["tool_version"] = version_lines[0] if version_lines else None
        if version.returncode != 0 or not version_lines:
            raise RuntimeError(f"version command failed ({version.returncode}) "
                               "or returned no version")
        remaining()
        with (location / "stdout.txt").open("wb") as stdout, (
                location / "stderr.txt").open("wb") as stderr:
            process = subprocess.Popen(argv, cwd=cwd, stdout=stdout, stderr=stderr)
            receipt["execution_started"] = True
            while True:
                left = child_deadline - time.monotonic()
                try:
                    if left <= 0:
                        raise subprocess.TimeoutExpired(argv, 0)
                    exit_code = process.wait(timeout=min(30, left))
                    break
                except subprocess.TimeoutExpired:
                    if child_deadline > time.monotonic():
                        print(f"{name}: tool execution active "
                              f"({int(time.monotonic() - started)}s)", flush=True)
                        continue
                    receipt["timed_out"] = True
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    exit_code = process.returncode
                    break
        receipt["exit_code"] = exit_code
        if receipt["timed_out"]:
            raise RuntimeError("execution budget timeout")
        if hashes(inputs) != input_hashes:
            raise RuntimeError("declared inputs changed during tool execution")
        if exit_code != expect:
            raise RuntimeError(f"exit {exit_code}, expected {expect}")
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        receipt["execution_error"] = f"{type(error).__name__}: {error}"
        raise RuntimeError(f"{name}: {error}; "
                           f"see {location.relative_to(ROOT)}/receipt.json") from error
    finally:
        receipt.update(finished_at=utc(), duration_s=time.monotonic() - started)
        (location / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return location


def relative(path):
    return str(path.relative_to(ROOT))


def mutation_copy(run, source, before, after, defect):
    source = ROOT / source
    original = source.read_text()
    if original.count(before) != 1:
        raise AssertionError(f"mutation target is not unique: {defect}")
    copy = run / f"mutant-{source.name}"
    copy.write_text(original.replace(before, after))
    (run / "mutation.json").write_text(json.dumps({
        "defect": defect, "source": relative(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "mutant": relative(copy),
        "mutant_sha256": hashlib.sha256(copy.read_bytes()).hexdigest(),
        "before": before, "after": after,
    }, indent=2) + "\n")
    return relative(copy)


def cleanup_build(path):
    path = path.resolve()
    if not path.is_dir() or not path.is_relative_to(ROOT / "evidence"):
        raise ValueError("cleanup requires a known project evidence build directory")
    for pattern in ("*.o", "*.a", "*.gch", "*.verilator_deplist.tmp"):
        for file in path.glob(pattern):
            if file.is_file():
                file.unlink()
