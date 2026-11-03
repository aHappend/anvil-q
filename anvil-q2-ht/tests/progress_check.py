"""Synthetic nested progress regression; no accelerator or physical-gate claims."""

import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment
import scheduling
from verify import run_observed_child


SOURCES = ["tests/progress_check.py", "tests/retention.py", "tests/scheduling.py",
           "tests/verify.py", "tests/README.md"]
LEAF = """
import sys, time
kind = sys.argv[1]
if kind == "quiet":
    time.sleep(0.7)
else:
    for index in range(6):
        sys.stdout.write("OUT-%d\\n" % index); sys.stdout.flush()
        sys.stderr.write("ERR-%d\\n" % index); sys.stderr.flush()
        time.sleep(0.12)
raise SystemExit(7 if kind == "failure" else 0)
"""


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def worker(args, root):
    # Accelerate only the observation cadence, never the child watchdog.
    scheduling.PROGRESS_INTERVAL_S = 0.1
    experiment = Experiment(root, args.output, sys.orig_argv, SOURCES)
    try:
        if args.level:
            output = experiment.output / ("nested-" + uuid.uuid4().hex)
            argv = [sys.executable, "-B", "tests/progress_check.py", "--worker",
                    "--output", str(output), "--level", str(args.level - 1),
                    "--kind", args.kind]
        else:
            argv = [sys.executable, "-B", "-c", LEAF, args.kind]
        run_observed_child(experiment, argv, "child")
    except (OSError, RuntimeError) as error:
        experiment.finish(1, error)
        return 1
    experiment.finish(0)
    return 0


def cases(experiment):
    earlier = {}
    observations = []
    for kind in ("growing", "quiet", "failure"):
        output = experiment.output / (kind + "-" + uuid.uuid4().hex)
        progress_path = experiment.directory / (kind + "-progress.jsonl")
        observed_live = []
        stop = threading.Event()
        monitor_errors = []

        def monitor():
            try:
                while not stop.wait(0.02):
                    lines = progress_path.read_text().splitlines(keepends=True)
                    # A concurrent write may leave only the final line incomplete.
                    events = [json.loads(line) for line in lines if line.endswith("\n")]
                    for event in events:
                        if event["event"] == "child-progress" and event["stdout"].endswith(
                                "/child.stdout") and sum(event["growth_bytes"]) > 0:
                            if not any(other["event"] == "child-finish" and
                                       other["pid"] == event["pid"] for other in events):
                                try:
                                    os.kill(event["pid"], 0)
                                except ProcessLookupError:
                                    continue
                                observed_live.append(event["pid"])
            except Exception as error:
                monitor_errors.append(error)

        with progress_path.open("xb") as stream, patch.dict(os.environ, {
                scheduling.PROGRESS_FD_ENV: str(stream.fileno()),
                scheduling.PROGRESS_PREFIX_ENV: "."}):
            observer = threading.Thread(target=monitor)
            observer.start()
            try:
                experiment.run([
                    sys.executable, "-B", "tests/progress_check.py", "--worker",
                    "--output", str(output), "--level", "2", "--kind", kind],
                    kind, allow_mismatch=True)
            finally:
                stop.set()
                observer.join()
        require(not monitor_errors, "live observer failed: " + str(monitor_errors))
        events = [json.loads(line) for line in progress_path.read_text().splitlines()]
        commands = []
        receipts = sorted((experiment.root / output).rglob("receipt.json"))
        require(len(receipts) == 3, kind + ": missing nested receipts")
        for path in receipts:
            receipt = json.loads(path.read_text())
            require(receipt["exit"] == (1 if kind == "failure" else 0),
                    kind + ": nested failure propagation changed")
            commands.extend(receipt["commands"])
        require(len(commands) == 3, kind + ": missing nested commands")
        leaf = next(command for command in commands if "-c" in command["argv"])
        leaf_events = [event for event in events if event["pid"] == leaf["pid"]]
        require(leaf_events[0]["event"] == "child-start" and
                leaf_events[-1]["event"] == "child-finish",
                kind + ": nested boundaries hidden from outer descriptor")
        require(leaf["timeout_s"] == 3600 and not leaf["timed_out"] and
                leaf["exit"] == (7 if kind == "failure" else 0),
                kind + ": child exit/watchdog changed")
        expected_out = b"" if kind == "quiet" else b"".join(
            f"OUT-{index}\n".encode() for index in range(6))
        expected_err = expected_out.replace(b"OUT", b"ERR")
        for key, data in (("stdout", expected_out), ("stderr", expected_err)):
            require((experiment.root / leaf[key]).read_bytes() == data,
                    kind + ": incomplete or contaminated raw log")
        require(leaf_events[-1]["bytes"] == [len(expected_out), len(expected_err)] and
                leaf_events[-1]["exit"] == leaf["exit"],
                kind + ": wrong final measured sizes/exit")
        progress = [event for event in leaf_events if event["event"] == "child-progress"]
        require(bool(progress) == (kind != "quiet"),
                kind + ": quiet child indistinguishable from measured growth")
        if kind != "quiet":
            require(leaf["pid"] in observed_live,
                    kind + ": leaf progress only appeared after settlement")
        previous = leaf_events[0]["bytes"]
        for event in progress:
            require(event["growth_bytes"] ==
                    [new - old for new, old in zip(event["bytes"], previous)] and
                    sum(event["growth_bytes"]) > 0,
                    kind + ": fabricated or incorrect log growth")
            previous = event["bytes"]
        for event in events:
            require(not Path(event["stdout"]).is_absolute() and
                    not Path(event["stderr"]).is_absolute(),
                    kind + ": private path in progress output")
        require(all((experiment.root / path).read_bytes() == data
                    for path, data in earlier.items()), "earlier evidence changed")
        for path in (experiment.root / output).rglob("*"):
            if path.is_file():
                earlier[str(path.relative_to(experiment.root))] = path.read_bytes()
        earlier[str(progress_path.relative_to(experiment.root))] = progress_path.read_bytes()
        observations.append({"case": kind, "nested_commands": len(commands),
                             "leaf_progress_events": len(progress),
                             "observed_while_alive": leaf["pid"] in observed_live,
                             "progress_log": str(progress_path.relative_to(experiment.root)),
                             "leaf_stdout": leaf["stdout"], "leaf_stderr": leaf["stderr"],
                             "leaf_exit": leaf["exit"]})
    experiment.receipt["progress_cases"] = observations
    experiment.receipt["earlier_evidence_preserved"] = len(earlier)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--repair-of")
    parser.add_argument("--level", type=int, default=2)
    parser.add_argument("--kind", choices=("growing", "quiet", "failure"), default="growing")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    if args.worker:
        return worker(args, root)
    experiment = Experiment(root, args.output, sys.orig_argv, SOURCES)
    experiment.receipt["scope"] = "synthetic nested progress; no RTL or native gates"
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        experiment.run([sys.executable, "--version"], "python-version")
        cases(experiment)
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1
    experiment.finish(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
