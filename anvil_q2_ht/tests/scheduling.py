"""Run-local resource leases and dependency-aware verification scheduling."""

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import contextmanager
import fcntl
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


BUDGET_ENV = "ANVIL_VERIFICATION_BUDGET"
HELD_ENV = "ANVIL_VERIFICATION_LEASE_HELD"
GIB = 1024 ** 3
PROGRESS_FD_ENV = "ANVIL_VERIFICATION_PROGRESS_FD"
PROGRESS_PREFIX_ENV = "ANVIL_VERIFICATION_PROGRESS_PREFIX"
PROGRESS_INTERVAL_S = 30.0


@contextmanager
def progress_channel():
    """Keep the original outer stream reachable through nested raw-log captures."""
    inherited = os.environ.get(PROGRESS_FD_ENV)
    if inherited is not None:
        descriptor = int(inherited)
        os.fstat(descriptor)
        yield descriptor
        return
    try:
        descriptor = os.dup(sys.stdout.fileno())
    except io.UnsupportedOperation:
        yield None
        return
    try:
        yield descriptor
    finally:
        os.close(descriptor)


def report_progress(descriptor, event, command, sizes, previous=None):
    prefix = Path(os.environ.get(PROGRESS_PREFIX_ENV, "."))
    record = {
        "event": "child-" + event, "pid": command["pid"],
        "stdout": str(prefix / command["stdout"]),
        "stderr": str(prefix / command["stderr"]),
        "bytes": sizes,
    }
    if previous is not None:
        record["growth_bytes"] = [size - old for size, old in zip(sizes, previous)]
    if event == "finish":
        record.update(exit=command["exit"], timed_out=command["timed_out"])
    line = json.dumps(record, separators=(",", ":")) + "\n"
    if descriptor is None:
        print(line, end="", flush=True)
    else:
        data = line.encode()
        if os.write(descriptor, data) != len(data):
            raise OSError("incomplete child progress write")


def effective_resources():
    affinity = len(os.sched_getaffinity(0))
    available = None
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            available = int(line.split()[1]) * 1024
    if available is None:
        raise RuntimeError("cannot determine available memory")
    memberships = Path("/proc/self/cgroup").read_text().splitlines()
    unified = [line.split(":", 2)[2] for line in memberships if line.startswith("0::")]
    if len(unified) != 1:
        raise RuntimeError("resource detection requires the Linux unified cgroup controller")
    mount = Path("/sys/fs/cgroup")
    group = mount / unified[0].lstrip("/")
    if not group.is_dir():
        raise RuntimeError("cannot inspect effective cgroup membership")
    cpu = float(affinity)
    memory = available
    observations = []
    while True:
        record = {"cgroup": "/" + str(group.relative_to(mount)).strip(".")}
        for name in ("cpu.max", "memory.max", "memory.high", "memory.current"):
            path = group / name
            if path.exists():
                record[name] = path.read_text().strip()
        if "cpu.max" in record:
            quota, period = record["cpu.max"].split()
            if quota != "max":
                cpu = min(cpu, int(quota) / int(period))
        for name in ("memory.max", "memory.high"):
            if name in record and record[name] != "max":
                memory = min(memory, max(0, int(record[name]) -
                                         int(record["memory.current"])))
        observations.append(record)
        if group == mount:
            break
        group = group.parent
    # Cap our shared-host footprint even when the host exposes hundreds of CPUs.
    # Each leased subtree uses one make job and reserves 4 GiB of headroom.
    slots = min(8, max(1, math.floor(cpu)), memory // (4 * GIB))
    if slots < 1:
        raise RuntimeError("less than 4 GiB of effective memory headroom for verification")
    return {"affinity_cpus": affinity, "effective_cpu_capacity": cpu,
            "mem_available_bytes": available, "effective_memory_headroom_bytes": memory,
            "cgroups": observations, "memory_reservation_per_slot_bytes": 4 * GIB,
            "shared_host_slot_cap": 8, "slots": slots}


def budget_info(root):
    value = os.environ.get(BUDGET_ENV)
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("verification budget must be project-relative")
    info = json.loads((root / path / "budget.json").read_text())
    if info["schema"] != 1 or info["directory"] != str(path) or info["slots"] < 1:
        raise RuntimeError("invalid verification resource budget")
    return path, info


def create_budget(experiment, slots=None):
    if budget_info(experiment.root) is not None:
        raise RuntimeError("cannot replace an inherited verification resource budget")
    resources = effective_resources()
    if slots is not None:
        if not 1 <= slots <= resources["slots"]:
            raise ValueError("diagnostic concurrency exceeds detected resource budget")
        resources["slots"] = slots
    path = experiment.output / "resources"
    directory = experiment.root / path
    directory.mkdir()
    info = {"schema": 1, "directory": str(path), **resources}
    with (directory / "budget.json").open("x") as stream:
        json.dump(info, stream, indent=2)
        stream.write("\n")
    for slot in range(info["slots"]):
        (directory / f"slot-{slot}.lock").touch(exist_ok=False)
    os.environ[BUDGET_ENV] = str(path)
    experiment.receipt["resource_budget"] = info
    return info


@contextmanager
def resource_lease(root, command, delegated=False):
    if delegated or os.environ.get(HELD_ENV) == "1":
        yield None
        return
    budget = budget_info(root)
    if budget is None:
        yield None
        return
    path, info = budget
    started = time.monotonic()
    while True:
        for slot in range(info["slots"]):
            stream = (root / path / f"slot-{slot}.lock").open("r")
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                stream.close()
                continue
            command["resource_lease"] = {
                "budget": str(path), "slot": slot, "wait_s": time.monotonic() - started}
            try:
                yield slot
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)
                stream.close()
            return
        time.sleep(0.05)


def run_process(root, argv, command, stdout, stderr, timeout, cwd=None, delegated=False):
    """Keep actual argv and per-child wait4 costs, including failed children."""
    with resource_lease(root, command, delegated) as slot, progress_channel() as progress:
        env = dict(os.environ)
        if slot is not None:
            env[HELD_ENV] = "1"
        if progress is not None:
            env[PROGRESS_FD_ENV] = str(progress)
        prefix = Path(env.get(PROGRESS_PREFIX_ENV, "."))
        env[PROGRESS_PREFIX_ENV] = str(prefix / cwd if cwd is not None else prefix)
        started = time.monotonic()
        process = subprocess.Popen(argv, cwd=root / cwd if cwd is not None else root,
                                   stdout=stdout, stderr=stderr, env=env,
                                   pass_fds=() if progress is None else (progress,))
        command["execution_start_monotonic_s"] = started
        command["pid"] = process.pid
        sizes = [os.fstat(stream.fileno()).st_size for stream in (stdout, stderr)]
        progress_errors = []

        def report(event, current, previous=None):
            try:
                report_progress(progress, event, command, current, previous)
            except OSError as error:
                progress_errors.append(f"{type(error).__name__}: {error}")
                command["progress_errors"] = progress_errors

        report("start", sizes)
        next_progress = started + PROGRESS_INTERVAL_S
        observations = 0
        timed_out = False
        while True:
            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                break
            if time.monotonic() - started >= timeout:
                timed_out = True
                process.kill()
                _, status, usage = os.wait4(process.pid, 0)
                break
            if time.monotonic() >= next_progress:
                current = [os.fstat(stream.fileno()).st_size for stream in (stdout, stderr)]
                if current != sizes:
                    report("progress", current, sizes)
                    sizes = current
                    observations += 1
                next_progress = time.monotonic() + PROGRESS_INTERVAL_S
            time.sleep(0.02)
        process.returncode = os.waitstatus_to_exitcode(status)
        command.update(
            exit=None if timed_out else process.returncode, timed_out=timed_out,
            execution_duration_s=time.monotonic() - started,
            user_cpu_s=usage.ru_utime, system_cpu_s=usage.ru_stime,
            max_rss_kib=usage.ru_maxrss)
        # ru_maxrss is the maximum individual process RSS in this waited subtree,
        # not a simultaneous sum across compiler/simulator processes.
        command["rss_scope"] = "wait4 maximum individual process in child subtree"
        command["progress_observations"] = observations
        command["log_bytes"] = [os.fstat(stream.fileno()).st_size
                                for stream in (stdout, stderr)]
        report("finish", command["log_bytes"])
        if progress_errors and not timed_out and process.returncode == 0:
            raise RuntimeError("child progress reporting failed: " + "; ".join(progress_errors))


def run_graph(experiment, ledger, execute, workers=None):
    """Retain every result; suppress only transitive dependents of failed nodes."""
    names = {row["check"] for row in ledger}
    if len(names) != len(ledger):
        raise ValueError("duplicate verification check name")
    for row in ledger:
        if not set(row.get("depends_on", ())) <= names or row["check"] in row.get("depends_on", ()):
            raise ValueError("invalid verification dependency")
    pending = list(ledger)
    completed = set()
    while pending:
        ready = [row for row in pending if set(row.get("depends_on", ())) <= completed]
        if not ready:
            raise ValueError("cyclic verification dependencies")
        completed.update(row["check"] for row in ready)
        pending = [row for row in pending if row not in ready]
    budget = budget_info(experiment.root)
    limit = budget[1]["slots"] if budget is not None else 1
    if workers is not None:
        limit = min(limit, workers)
    if limit < 1:
        raise ValueError("scheduler needs at least one worker")
    pending = sorted(ledger, key=lambda row: row.get("priority", 0), reverse=True)
    running = {}
    outcomes = {}
    started = time.monotonic()
    schedules = experiment.receipt.setdefault("schedules", [])
    journal = experiment.directory / f"schedule-{len(schedules):03d}.jsonl"
    schedule = {
        "workers": limit, "checks": [row["check"] for row in ledger],
        "journal": str(experiment.output / journal.name), "outcomes": outcomes}
    with journal.open("x") as stream:
        stream.write(json.dumps({
            "event": "created", "offset_s": 0, "workers": limit,
            "checks": ledger}, sort_keys=True) + "\n")
    schedules.append(schedule)

    def record(event, row=None):
        with experiment.lock:
            entry = {"event": event, "offset_s": time.monotonic() - started}
            if row is not None:
                entry["check"] = dict(row)
            with journal.open("a") as stream:
                stream.write(json.dumps(entry, sort_keys=True) + "\n")

    def invoke(row):
        row.update(outcome="running", start_offset_s=time.monotonic() - started)
        record("started", row)
        try:
            execute(row)
        except Exception as error:
            row.update(outcome="failed", failure=f"{type(error).__name__}: {error}")
        else:
            row["outcome"] = "passed"
        finally:
            row["end_offset_s"] = time.monotonic() - started
            record("finished", row)

    with ThreadPoolExecutor(max_workers=limit) as pool:
        while pending or running:
            for row in list(pending):
                dependencies = row.get("depends_on", ())
                failed = [name for name in dependencies if
                          outcomes.get(name) in ("failed", "suppressed")]
                if failed:
                    row.update(outcome="suppressed", failed_dependencies=failed)
                    record("suppressed", row)
                    outcomes[row["check"]] = "suppressed"
                    pending.remove(row)
                elif len(running) < limit and all(outcomes.get(name) == "passed"
                                                 for name in dependencies):
                    pending.remove(row)
                    running[pool.submit(invoke, row)] = row
            if running:
                done, _ = wait(running, return_when=FIRST_COMPLETED)
                for future in done:
                    row = running.pop(future)
                    future.result()
                    outcomes[row["check"]] = row["outcome"]
    schedule["elapsed_s"] = time.monotonic() - started
    record("settled")
    failures = [row["check"] for row in ledger if row["outcome"] != "passed"]
    if failures:
        raise RuntimeError("verification checks failed or suppressed: " + ", ".join(failures))
