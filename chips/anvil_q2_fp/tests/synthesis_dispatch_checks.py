"""Retained advisory dispatch measurements; not a replacement admitted check."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run
from synthesis_dispatch import GIB, policy, resources
from verify import execute_job, synthesis_jobs


def policy_fixtures():
    cases = [(32, 32, 4), (8, 32, 3), (4, 32, 1), (32, 2, 2), (3, 1, 1)]
    for memory, cpus, expected in cases:
        actual = policy(dict(available_bytes=memory * GIB, cpu_capacity=cpus))
        assert actual["maximum_concurrent_jobs"] == expected
    try:
        policy(dict(available_bytes=2 * GIB, cpu_capacity=8))
    except RuntimeError as exc:
        assert "insufficient available memory" in str(exc)
    else:
        raise AssertionError("insufficient memory did not fail explicitly")
    print(json.dumps(dict(compared_policy_fixtures=6, current_policy=policy(resources()))))


def tree_rss_kib(pid):
    """Sample only this probe's process tree, never unrelated processes."""
    try:
        fields = Path(f"/proc/{pid}/statm").read_text().split()
        own = int(fields[1]) * os.sysconf("SC_PAGE_SIZE") // 1024
        children = set()
        for task in Path(f"/proc/{pid}/task").iterdir():
            try:
                children.update((task / "children").read_text().split())
            except (FileNotFoundError, ProcessLookupError):
                continue
    except (FileNotFoundError, ProcessLookupError):
        return 0
    return own + sum(tree_rss_kib(int(child)) for child in children)


def execute(full=False):
    run = Run("synthesis-dispatch-full" if full else "synthesis-dispatch-probe")
    stop = threading.Event()
    samples = []

    def monitor():
        while not stop.is_set():
            samples.append((time.monotonic(), tree_rss_kib(os.getpid())))
            stop.wait(0.1)

    thread = threading.Thread(target=monitor)
    started = time.monotonic()
    try:
        run.receipt["repair_of_attempt"] = "attempt-0022"
        run.receipt["original_failure"] = (
            "Serial native synthesis dispatch exceeded the 2700-second aggregate patrol; "
            "14 completed children, configuration 15 interrupted, no child timeout.")
        run.command(["python3", "--version"], "python-version")
        run.command(["yosys", "-V"], "yosys-version")
        run.command(["/usr/bin/time", "--version"], "measurement-tool-version")
        run.command(["cat", "/proc/meminfo", "/proc/self/cgroup",
                     "/sys/fs/cgroup/cpuset.cpus.effective"], "resource-environment")
        fixtures = run.command(
            ["python3", "tests/synthesis_dispatch_checks.py", "--policy-fixtures"],
            "dispatch-policy-fixtures")
        compared_fixtures = json.loads(fixtures.read_text())["compared_policy_fixtures"]
        assert compared_fixtures == 6
        thread.start()
        if full:
            output = run.command(
                ["/usr/bin/time", "-f", "%e %M", "-o",
                 run.relative(run.path / "full.resources.txt"),
                 "python3", "tests/verify.py", "--check", "synthesis"],
                "unchanged-synthesis-command", timeout=21600)
            receipts = [line for line in output.read_text().splitlines()
                        if line.endswith("/receipt.json")]
            assert len(receipts) == 1, "missing aggregate synthesis receipt"
            receipt = json.loads((ROOT / receipts[0]).read_text())
            assert receipt["outcome"] == "passed"
            assert receipt["source_sha256"] == run.receipt["source_sha256"]
            assert receipt["metrics"]["required_runs"] == 30
            assert receipt["metrics"]["compared_runs"] == 30
            metrics = dict(aggregate_receipt=receipts[0], **receipt["metrics"])
            seconds, peak = (run.path / "full.resources.txt").read_text().split()
            metrics.update(command_wall_s=float(seconds), command_peak_rss_kib=int(peak),
                           within_2700s_patrol=float(seconds) < 2700)
        else:
            labels = {
                "fp-native-b4-c1-bf16-w0", "fp-native-b4-c1-fp16-w1",
                "parent-native-b4-c0", "parent-native-b4-c1",
            }
            records = []
            for label, arguments, requirement in synthesis_jobs():
                if label in labels:
                    records.append(dict(
                        id=label, requirement=requirement, outcome="not-executed",
                        argv=["/usr/bin/time", "-f", "%e %M", "-o",
                              run.relative(run.path / f"{label}.resources.txt"),
                              "python3", *arguments]))
            assert len(records) == 4
            with ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(lambda record: execute_job(run, record), records))
            for record in records:
                seconds, peak = (run.path / f"{record['id']}.resources.txt").read_text().split()
                record.update(wall_s=float(seconds), peak_rss_kib=int(peak))
            metrics = dict(
                compared_runs=len(records), maximum_concurrent_jobs=4, records=records,
                sum_individual_peak_rss_kib=sum(r["peak_rss_kib"] for r in records))
        stop.set()
        thread.join()
        metrics.update(wall_s=time.monotonic() - started,
                       compared_policy_fixtures=compared_fixtures,
                       sampled_tree_peak_rss_kib=max(rss for _, rss in samples),
                       sample_interval_s=0.1, resource_samples=len(samples))
        with (run.path / "resources.json").open("x") as stream:
            json.dump(dict(metrics=metrics, samples=samples), stream, indent=2)
            stream.write("\n")
        run.receipt["generated_sha256"] = {
            run.relative(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [run.path / "resources.json", *run.path.glob("*.resources.txt")]}
        run.finish("passed-focused-only", metrics=metrics,
                   limitations="Preparation only; shared-runtime checks and hardware gates remain mandatory.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError, KeyError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        stop.set()
        if thread.is_alive():
            thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-check", action="store_true")
    parser.add_argument("--policy-fixtures", action="store_true")
    args = parser.parse_args()
    if args.policy_fixtures:
        policy_fixtures()
    else:
        raise SystemExit(execute(args.full_check))
