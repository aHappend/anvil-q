"""Summarize retained project input observations without certifying runtime integrity."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment


def differences(before, after):
    return [{"path": name, "before": before.get(name), "after": after.get(name)}
            for name in sorted(before.keys() | after.keys())
            if name not in before or name not in after or before[name] != after[name]]


def summarize(directory):
    receipt = json.loads((directory / "receipt.json").read_text())

    def parsed_time(value):
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            raise ValueError("observation timestamps must include a timezone")
        return result

    run_start, run_end = (parsed_time(receipt[key]) for key in ("start", "end"))
    if run_end < run_start:
        raise ValueError("invalid receipt timestamps")
    before = json.loads((directory / "declared-inputs-before.json").read_text())
    after = json.loads((directory / "declared-inputs-after.json").read_text())
    if before != receipt["declared_inputs_before"] or after != receipt["declared_inputs_after"]:
        raise ValueError("standalone bindings differ from retained receipt")
    endpoint_changes = differences(before, after)
    observations = []
    path = directory / "declared-input-metadata.jsonl"
    if path.exists():
        with path.open() as stream:
            observations = [json.loads(line) for line in stream]
    intervals = []
    unobserved = []
    previous = None
    for row in observations:
        start, end = (parsed_time(row[key]) for key in ("start", "end"))
        if end < start or start < run_start or end > run_end:
            raise ValueError("invalid observation timestamps")
        previous_end = parsed_time(previous["end"]) if previous else run_start
        if start < previous_end:
            raise ValueError("overlapping or unordered observation intervals")
        gap = {
            "from_boundary": previous["boundary"] if previous else "receipt:start",
            "to_boundary": row["boundary"],
            "unobserved_start": previous["end"] if previous else receipt["start"],
            "unobserved_end": row["start"],
            "unobserved_seconds": (start - previous_end).total_seconds(),
        }
        unobserved.append(gap)
        if previous is not None:
            intervals.append({
                **gap,
                "observed_metadata_differences": differences(previous["files"], row["files"]),
            })
        previous = row
    unobserved.append({
        "from_boundary": previous["boundary"] if previous else "receipt:start",
        "to_boundary": "receipt:end",
        "unobserved_start": previous["end"] if previous else receipt["start"],
        "unobserved_end": receipt["end"],
        "unobserved_seconds": (
            run_end - (parsed_time(previous["end"]) if previous else run_start)
        ).total_seconds(),
    })
    return {
        "scope": "retrospective project observations only; not acceptance or restart authority",
        "recorded_command_exit": receipt["exit"],
        "selected_files_before": len(before), "selected_files_after": len(after),
        "endpoint_content_differences": endpoint_changes,
        "metadata_observation_count": len(observations),
        "first_observation_start": observations[0]["start"] if observations else None,
        "last_observation_end": observations[-1]["end"] if observations else None,
        "intervals": intervals,
        "unobserved_intervals": unobserved,
        "limitations": [
            "File observations are sequential scans, not atomic snapshots or write-event logs.",
            "Each interval is unobserved; unchanged endpoints do not exclude intervening writes.",
            "No write chronology exists before the first or after the last observation.",
            "No writer identity, runtime comparison rule or affected-path list is inferred.",
            "Capsule admission and receipt-publication readiness are not established.",
        ],
        "runtime_diagnosis": "unavailable from these project observations",
    }


def worker(root, run, output):
    # A restored endpoint must not be interpreted as a complete write history.
    before = {"a": {"mtime_ns": 1}, "removed": {}}
    after = {"a": {"mtime_ns": 2}, "added": {}}
    expected = [
        {"path": "a", "before": {"mtime_ns": 1}, "after": {"mtime_ns": 2}},
        {"path": "added", "before": None, "after": {}},
        {"path": "removed", "before": {}, "after": None},
    ]
    if differences(before, after) != expected or differences(before, before):
        raise RuntimeError("diagnostic difference self-check failed")
    print("CHECK readable_changed_added_removed_and_equal_bindings")
    report = summarize(root / run)
    with (root / output / "observations.json").open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ("intervals", "unobserved_intervals")}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    for path in (args.run, args.output):
        if path.is_absolute() or ".." in path.parts:
            parser.error("paths must be project-relative")
        if not path.parts or path.parts[0] != "evidence":
            parser.error("only project evidence directories are supported")
    if args.worker:
        worker(root, args.run, args.output)
        return 0
    names = ["tests/binding_diagnosis.py", "tests/retention.py"] + [
        str(args.run / name) for name in (
            "receipt.json", "declared-inputs-before.json", "declared-inputs-after.json")]
    metadata = args.run / "declared-input-metadata.jsonl"
    if (root / metadata).exists():
        names.append(str(metadata))
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    experiment.receipt["scope"] = "offline diagnostic; no RTL, aggregate checks or native gates"
    try:
        experiment.run([sys.executable, "--version"], "python-version")
        experiment.run([sys.executable, "-B", "tests/binding_diagnosis.py", "--worker",
                        "--run", str(args.run), "--output", str(args.output)], "diagnosis")
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1
    experiment.finish(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
