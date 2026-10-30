"""Retained compiled simulation with four-state Icarus startup coverage.

Generated testbench scheduling alone is adapted for Verilator's lack of #0
inactive-region support. DUT sources are never rewritten. Builds use bounded
CPU/memory/storage-aware admission and two parallel C++ compiler jobs.
Generated sources are checked before C++ compilation.
Only settled, owned, unreferenced .o/.a/.gch files are disposable.

Reserve 2 GiB memory and 512 MiB disk per build, plus shared headroom; these
budgets are conservative admission bounds, not guarantees against external use.
ANVIL_SIM_BUILD_LIMIT can reduce concurrency to reproduce bounded measurements.
Preparation measurements must remain inspectable before this policy is admitted;
missing receipts are not passing performance or retention evidence.
"""

import fcntl
from collections import Counter, deque
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

from retained import ROOT, require_time_zero
from synthesis_dispatch import resources


MIB = 1024 ** 2
BUILD_RESERVE = 512 * MIB
STORAGE_HEADROOM = 1024 * MIB
MAXIMUM_BUILDS = 8
BUILD_MEMORY = 2 * 1024 ** 3


def build_policy(available=None, cpus=None, memory=None):
    if available is None:
        fs = os.statvfs(ROOT)
        available = fs.f_bavail * fs.f_frsize
    snapshot = resources() if cpus is None or memory is None else {}
    if cpus is None:
        cpus = snapshot["cpu_capacity"]
    if memory is None:
        memory = snapshot["available_bytes"]
    assert cpus and cpus > 0, "cannot determine compiler CPU capacity"
    limit = int(os.environ.get("ANVIL_SIM_BUILD_LIMIT", MAXIMUM_BUILDS))
    assert 1 <= limit <= MAXIMUM_BUILDS, "compiler limit must be in 1..8"
    memory_headroom = max(1024 ** 3, memory // 4)
    workers = min(limit, max(1, cpus // 2),
                  max(1, (available - STORAGE_HEADROOM) // BUILD_RESERVE),
                  max(1, (memory - memory_headroom) // BUILD_MEMORY))
    return dict(available_bytes=available, cpu_capacity=cpus,
                maximum_concurrent_jobs=workers, per_build_reserved_bytes=BUILD_RESERVE,
                available_memory_bytes=memory, memory_headroom_bytes=memory_headroom,
                per_build_reserved_memory_bytes=BUILD_MEMORY,
                headroom_bytes=STORAGE_HEADROOM,
                limitation="Admission budget, not a quota or guarantee against external disk use.")


@contextmanager
def build_slot(run, timeout=3600):
    """Reserve bounded project-wide compiler capacity, released on process exit."""
    started = time.monotonic()
    waiting = None
    gate = ROOT / "evidence/compiler-storage.lock"
    with gate.open("a") as admission:
        while True:
            acquired = None
            unlocked = []
            fcntl.flock(admission, fcntl.LOCK_EX)
            try:
                busy = 0
                for slot in range(MAXIMUM_BUILDS):
                    handle = (gate.parent / f"compiler-slot-{slot}.lock").open("a")
                    try:
                        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        unlocked.append(handle)
                    except BlockingIOError:
                        busy += 1
                        handle.close()
                snapshot = build_policy()
                required = STORAGE_HEADROOM + (busy + 1) * BUILD_RESERVE
                if (unlocked and busy < snapshot["maximum_concurrent_jobs"]
                        and snapshot["available_bytes"] >= required
                        and snapshot["available_memory_bytes"] >=
                        snapshot["memory_headroom_bytes"] + (busy + 1) * BUILD_MEMORY):
                    acquired = unlocked.pop()
                    run.receipt.setdefault("compiler_storage_admission", []).append(
                        dict(snapshot, active_other_builds=busy, required_bytes=required,
                             wait_s=time.monotonic() - started))
                else:
                    if waiting is None:
                        waiting = dict(initial=snapshot, minimum_available_bytes=snapshot["available_bytes"])
                        run.receipt.setdefault("compiler_storage_waits", []).append(waiting)
                    waiting.update(last=snapshot, required_bytes=required, active_other_builds=busy,
                                   waited_s=time.monotonic() - started,
                                   minimum_available_bytes=min(waiting["minimum_available_bytes"],
                                                               snapshot["available_bytes"]))
            finally:
                for handle in unlocked:
                    handle.close()
                fcntl.flock(admission, fcntl.LOCK_UN)
            if acquired is not None:
                break
            if time.monotonic() - started >= timeout:
                raise RuntimeError(
                    f"compiler storage admission deadline exceeded: "
                    f"{snapshot['available_bytes']} bytes available; {required} required; "
                    "no build started or cache entry published")
            time.sleep(0.25)
        try:
            yield
        finally:
            acquired.close()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cleanup_intermediates(run, objects, protected=()):
    """Only settled, attributed build products may be discarded, never receipts."""
    objects.resolve().relative_to(run.path.resolve())
    assert objects.name.endswith("-obj") and not objects.is_symlink()
    assert objects.parent == run.path and objects.stat().st_uid == os.getuid()
    assert all(c.get("ended_at") and c.get("exit_code") is not None
               and not c.get("timed_out") for c in run.receipt.get("commands", [])), (
                   "build tools have not settled; cleanup forbidden")
    protected = {Path(p).resolve() for p in protected}

    def references(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield from references(key)
                yield from references(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                yield from references(item)
        elif isinstance(value, str) and (value.startswith("evidence/") or value.startswith("/")):
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


def generated_artifacts(objects):
    """Check Verilator's target inventory before compiling or publishing it."""
    manifest = objects / "Vtb__verFiles.dat"
    assert manifest.is_file(), f"incomplete generated artifacts: missing {manifest.name}"
    targets = {}
    errors = []
    for line in manifest.read_text().splitlines():
        if not line.startswith("T "):
            continue
        match = re.fullmatch(r'T\s+(\d+)(?:\s+\d+){5}\s+"([^"]+)"', line)
        assert match, f"incomplete generated artifacts: malformed target record: {line}"
        size, name = int(match[1]), match[2]
        path = ROOT / name
        assert path.parent.resolve() == objects.resolve(), "generated target escapes owned build"
        assert not path.is_symlink(), "generated target is a symlink"
        # Verilator writes a zero-sized self-record before closing this manifest.
        if path == manifest:
            assert size == 0, "unexpected generated-manifest self-record"
            continue
        if not path.is_file():
            errors.append(f"{path.name}: missing")
            continue
        data = path.read_bytes()
        if len(data) != size or not data or not data.endswith(b"\n"):
            errors.append(f"{path.name}: manifest={size}, actual={len(data)}, "
                          f"nonempty={bool(data)}, newline={data.endswith(bytes([10]))}")
        targets[name] = hashlib.sha256(data).hexdigest()
    assert targets and any(name.endswith(".cpp") for name in targets), (
        "incomplete generated artifacts: no C++ targets")
    assert not errors, "incomplete generated artifacts: " + "; ".join(errors)
    return {**targets, str(manifest.relative_to(ROOT)): digest(manifest)}


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
    mode = os.environ.get("ANVIL_SIM_BUILD_MODE", "split")
    assert mode in ("aggregate", "split"), "unknown compiler build mode"
    identity = {
        "sources": {run.relative(p): digest(p) for p in sources},
        "bench": digest(bench), "parameters": parameters,
        "frontend_sha256": digest(Path(__file__)),
        "options": ["--cc", "--exe", "--main", "--timing", "--assert", "--top-module", "tb",
                    "-Wno-fatal", "-Wno-BLKANDNBLK",
                    "--unroll-count", "512", "--unroll-stmts", "1000000",
                    "-CFLAGS", "-O1", "-j", "2"],
        "make_options": [f"VM_PARALLEL_BUILDS={int(mode == 'split')}"],
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
    with build_slot(run):
        return build_uncached_model(run, bench, sources, parameters, label, identity, index)


def build_uncached_model(run, bench, sources, parameters, label, identity, index):
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
    try:
        run.command(["verilator", *identity["options"], "--Mdir", run.relative(objects),
                     *[f"-G{k}={v}" for k, v in parameters.items()],
                     *[run.relative(p) for p in sources], run.relative(compiled)],
                    label + "-generate", timeout=3600)
        generated = generated_artifacts(objects)
    except (AssertionError, OSError, RuntimeError) as exc:
        run.receipt.setdefault("incomplete_builds", []).append(
            dict(objects=run.relative(objects), phase="generation", diagnostic=str(exc),
                 cache_published=False, storage=build_policy()))
        raise
    run.receipt.setdefault("generated_model_sha256", {}).update(generated)
    try:
        run.command(["make", "-C", run.relative(objects), "-f", "Vtb.mk", "-j", "2",
                     *identity["make_options"]], label, timeout=3600)
        assert generated_artifacts(objects) == generated, "generated sources changed during build"
        assert binary.is_file() and binary.stat().st_size and os.access(binary, os.X_OK), (
            "incomplete compiled artifact: executable missing or not executable")
    except (AssertionError, OSError, RuntimeError) as exc:
        run.receipt.setdefault("incomplete_builds", []).append(
            dict(objects=run.relative(objects), phase="compilation", diagnostic=str(exc),
                 cache_published=False, storage=build_policy()))
        raise
    artifact_paths = [bench, startup, startup_binary, compiled, *sorted(objects.glob("*.cpp"))]
    for command in run.receipt["commands"]:
        if command["stdout"].startswith(run.relative(run.path / label)):
            artifact_paths.extend(ROOT / command[field] for field in ("stdout", "stderr"))
    recorded = {
        "identity": identity, "binary": run.relative(binary), "binary_sha256": digest(binary),
        "startup": run.relative(startup_binary),
        "artifact_sha256": {**generated,
                            **{run.relative(p): digest(p) for p in artifact_paths}},
        "build_commands": [c for c in run.receipt["commands"]
                           if c["stdout"].startswith(run.relative(run.path / label))],
    }
    run.receipt.setdefault("compiled_models", []).append(recorded)
    run.receipt.setdefault("completed_build_storage", []).append(dict(
        objects=run.relative(objects),
        allocated_bytes=sum(p.stat().st_blocks * 512 for p in objects.iterdir() if p.is_file()),
        logical_bytes=sum(p.stat().st_size for p in objects.iterdir() if p.is_file())))
    cleanup_intermediates(run, objects, [binary, *artifact_paths])
    pending = run.path / f"{label}-cache-entry.json"
    with pending.open("x") as stream:
        json.dump(recorded, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    # Only a complete, fsynced entry becomes visible to another seed.
    os.link(pending, index)
    return binary


def startup_check(run, binary, arguments=(), label="startup"):
    records = run.receipt.get("compiled_models", []) + run.receipt.get("reused_compiled_models", [])
    model = next(record for record in records if record["binary"] == run.relative(binary))
    trace = run.command(["vvp", model["startup"], *arguments], label)
    require_time_zero(trace)
    assert "ICARUS_STARTUP_COMPARED" in trace.read_text(), "missing four-state startup completion"