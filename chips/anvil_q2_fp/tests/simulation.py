"""Retained compiled simulation, with a four-state Icarus startup companion.

Only generated testbench scheduling is adapted for Verilator's lack of #0
inactive-region support. The unmodified bench checks time-zero and both reset
edges in Icarus before the compiled workload runs. No DUT source is rewritten.
"""

import fcntl
from collections import Counter, deque
import hashlib
import json
import os
from pathlib import Path
import stat

from retained import ROOT, require_time_zero


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cleanup_intermediates(run, objects, protected=()):
    """Only settled, attributed build products may be discarded, never receipts."""
    objects.resolve().relative_to(run.path.resolve())
    assert objects.name.endswith("-obj") and not objects.is_symlink()
    protected = {Path(p).resolve() for p in protected}
    def references(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield from references(key)
                yield from references(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                yield from references(item)
        elif isinstance(value, str) and value.startswith("evidence/"):
            yield (ROOT / value).resolve()
    protected.update(references(run.receipt))
    removed = []
    for path in sorted(objects.iterdir()):
        if path.suffix not in (".o", ".a", ".gch"):
            continue
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid(), (
            f"unattributed build intermediate: {path}")
        assert info.st_nlink == 1 and path.resolve() not in protected, (
            f"receipt-bound or shared build artifact: {path}")
        removed.append(dict(path=run.relative(path), bytes=info.st_size,
                            sha256=digest(path), uid=info.st_uid, inode=info.st_ino))
    run.receipt.setdefault("disposable_build_intermediates", []).extend(removed)
    for row in removed:
        path = ROOT / row["path"]
        info = path.lstat()
        assert (info.st_ino, info.st_size, info.st_uid) == (
            row["inode"], row["bytes"], row["uid"]), "intermediate changed before cleanup"
        path.unlink()
    return removed


def stream_model(run, argv, checker, transaction_prefixes, record_prefixes,
                 label="simulation", timeout=21600):
    """Check each bounded pipe record before discarding transaction text.

    Reproducible inputs, summary output, full-stream hashes/counts and a bounded
    failure window are retained. This is explicitly not a raw transaction dump.
    """
    def handle(process, output):
        full, records = hashlib.sha256(), hashlib.sha256()
        counts, recent = Counter(), deque(maxlen=32)
        byte_count = line_count = record_count = 0
        record = run.receipt["commands"][-1]
        record["stdout_policy"] = "live-checked transactions; summaries and failure window retained"

        def lines():
            nonlocal byte_count, line_count, record_count
            while True:
                line = process.stdout.readline(65537)
                if not line:
                    break
                assert len(line) <= 65536, "oversized simulation record"
                raw = line.encode("utf-8")
                full.update(raw)
                byte_count += len(raw)
                line_count += 1
                recent.append(line)
                if line.startswith(record_prefixes):
                    records.update(raw)
                    record_count += 1
                if line.startswith(transaction_prefixes):
                    counts[line.split()[0]] += 1
                else:
                    output.write(line)
                yield line
        try:
            result = checker(lines())
            assert process.stdout.read(1) == "", "checker did not consume the complete stream"
            return result
        except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
            output.write(f"STREAM_COMPARISON_FAILURE {type(exc).__name__}: {exc}\n")
            output.write("STREAM_FAILURE_WINDOW_BEGIN\n" + "".join(recent)
                         + "STREAM_FAILURE_WINDOW_END\n")
            raise
        finally:
            record["checked_stream"] = dict(
                sha256=full.hexdigest(), bytes=byte_count, lines=line_count,
                protocol_sha256=records.hexdigest(), protocol_records=record_count,
                discarded_transaction_counts=dict(counts), failure_window_records=32)
            output.write("CHECKED_STREAM " + json.dumps(record["checked_stream"], sort_keys=True) + "\n")
    return run.interactive(argv, label, handle, timeout=timeout)


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
    cleanup_intermediates(run, objects, [binary, *artifact_paths])
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
