"""Retained compiled simulation, with a four-state Icarus startup companion.

Only generated testbench scheduling is adapted for Verilator's lack of #0
inactive-region support. The unmodified bench checks time-zero and both reset
edges in Icarus before the compiled workload runs. No DUT source is rewritten.
"""

import fcntl
import hashlib
import json
import os
from pathlib import Path

from retained import ROOT, require_time_zero


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_model(run, bench, sources, parameters, label="compile"):
    sources = list(sources)
    identity = {
        "sources": {run.relative(p): digest(p) for p in sources},
        "bench": digest(bench), "parameters": parameters,
        "frontend_sha256": digest(Path(__file__)),
        "options": ["--binary", "--timing", "--assert", "--top-module", "tb",
                    "-Wno-fatal", "-Wno-BLKANDNBLK",
                    "--unroll-count", "512", "--unroll-stmts", "1000000",
                    "-CFLAGS", "-O1", "-j", "2"],
    }
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    cache = Path(os.environ.get("ANVIL_SIM_CACHE", run.relative(run.path / "sim-cache")))
    assert not cache.is_absolute() and ".." not in cache.parts
    assert cache.parts[:1] == ("evidence",)
    index = ROOT / cache / f"{key}.json"
    index.parent.mkdir(parents=True, exist_ok=True)
    with index.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return build_model(run, bench, sources, parameters, label, identity, index)


def build_model(run, bench, sources, parameters, label, identity, index):
    if index.exists():
        recorded = json.loads(index.read_text())
        assert recorded["identity"] == identity, "compiled-model cache identity mismatch"
        binary = ROOT / recorded["binary"]
        binary.resolve().relative_to(ROOT.resolve())
        assert digest(binary) == recorded["binary_sha256"], "compiled-model binary changed"
        for name, expected in recorded["artifact_sha256"].items():
            path = ROOT / name
            path.resolve().relative_to(ROOT.resolve())
            assert digest(path) == expected, f"compiled-model evidence changed: {name}"
        run.receipt.setdefault("reused_compiled_models", []).append(recorded)
        return binary

    run.command(["verilator", "--version"], label + "-verilator-version")
    run.command(["g++", "--version"], label + "-cxx-version")
    run.command(["make", "--version"], label + "-make-version")
    run.command(["iverilog", "-V"], label + "-iverilog-version")
    run.command(["vvp", "-V"], label + "-vvp-version")
    original = bench.read_text()
    anchor = "#0; reset_sample<=1;"
    assert original.count(anchor) == 1, "missing independently observed Icarus reset"
    startup = run.path / f"{label}-startup.sv"
    startup.write_text(original.replace(
        "module tb;", 'module tb;\ninitial begin #20; '
        '$display("ICARUS_STARTUP_COMPARED"); $finish; end', 1))
    startup_binary = run.path / f"{label}-startup.vvp"
    run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                 *[f"-Ptb.{k}={v}" for k, v in parameters.items()],
                 "-o", run.relative(startup_binary),
                 *[run.relative(p) for p in sources], run.relative(startup)],
                label + "-startup-compile")
    # Startup stops before any command; fixture-load plusargs are still required.
    compiled = run.path / f"{label}-compiled.sv"
    compiled.write_text(original.replace(anchor, "reset_sample=1;", 1))
    objects = run.path / f"{label}-obj"
    binary = objects / "Vtb"
    run.command(["verilator", *identity["options"], "--Mdir", run.relative(objects),
                 *[f"-G{k}={v}" for k, v in parameters.items()],
                 *[run.relative(p) for p in sources], run.relative(compiled)],
                label, timeout=3600)
    artifact_paths = [bench, startup, startup_binary, compiled]
    for command in run.receipt["commands"]:
        if command["stdout"].startswith(run.relative(run.path / label)):
            artifact_paths.extend(ROOT / command[field] for field in ("stdout", "stderr"))
    recorded = {
        "identity": identity, "binary": run.relative(binary), "binary_sha256": digest(binary),
        "startup": run.relative(startup_binary),
        "artifact_sha256": {run.relative(p): digest(p) for p in artifact_paths},
        "build_commands": [c for c in run.receipt["commands"]
                           if c["stdout"].startswith(run.relative(run.path / label))],
    }
    run.receipt.setdefault("compiled_models", []).append(recorded)
    with index.open("x") as stream:
        json.dump(recorded, stream, indent=2)
        stream.write("\n")
    return binary


def startup_check(run, binary, arguments=(), label="startup"):
    records = run.receipt.get("compiled_models", []) + run.receipt.get("reused_compiled_models", [])
    model = next(record for record in records if record["binary"] == run.relative(binary))
    trace = run.command(["vvp", model["startup"], *arguments], label)
    require_time_zero(trace)
    assert "ICARUS_STARTUP_COMPARED" in trace.read_text(), "missing four-state startup completion"
