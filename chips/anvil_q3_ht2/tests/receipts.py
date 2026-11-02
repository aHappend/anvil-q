"""Immutable, project-relative receipts for project-owned verification children."""

import hashlib
import json
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
    version = subprocess.run(version_argv, cwd=ROOT, capture_output=True, text=True)
    (location / "version.stdout.txt").write_text(version.stdout)
    (location / "version.stderr.txt").write_text(version.stderr)
    inputs = []
    for argument in map(str, argv):
        argument = argument.removeprefix("+vectors=")
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
        "tool_version_exit_code": version.returncode,
        "tool_version": (version.stdout + version.stderr).splitlines()[0],
        "started_at": utc(), "timeout_s": None, "timed_out": False,
        "stdout_path": str((location / "stdout.txt").relative_to(ROOT)),
        "stderr_path": str((location / "stderr.txt").relative_to(ROOT)),
    }
    if (run / "repair-of.json").is_file():
        receipt["repair_of"] = json.loads((run / "repair-of.json").read_text())
    started = time.monotonic()
    with (location / "stdout.txt").open("wb") as stdout, (
            location / "stderr.txt").open("wb") as stderr:
        process = subprocess.Popen(argv, cwd=cwd, stdout=stdout, stderr=stderr)
        while True:
            try:
                exit_code = process.wait(timeout=30)
                break
            except subprocess.TimeoutExpired:
                print(f"{name}: tool execution active ({int(time.monotonic() - started)}s)",
                      flush=True)
    receipt.update(finished_at=utc(), duration_s=time.monotonic() - started,
                   exit_code=exit_code)
    (location / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if version.returncode != 0:
        raise RuntimeError(f"{name}: version command failed ({version.returncode})")
    if hashes(inputs) != input_hashes:
        raise RuntimeError(f"{name}: declared inputs changed during tool execution")
    if exit_code != expect:
        raise RuntimeError(f"{name}: exit {exit_code}, expected {expect}; "
                           f"see {location.relative_to(ROOT)}/receipt.json")
    return location


def relative(path):
    return str(path.relative_to(ROOT))


def cleanup_build(path):
    path = path.resolve()
    if not path.is_dir() or not path.is_relative_to(ROOT / "evidence"):
        raise ValueError("cleanup requires a known project evidence build directory")
    for pattern in ("*.o", "*.a", "*.gch", "*.verilator_deplist.tmp"):
        for file in path.glob(pattern):
            if file.is_file():
                file.unlink()
