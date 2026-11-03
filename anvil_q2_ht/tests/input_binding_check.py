"""Synthetic regression for aggregate input bindings and diagnostic retention."""

import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment
from invocation import invocation_experiment, run_regression
from binding_diagnosis import summarize
import verify


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def diagnosis_cases(base):
    count = 0
    for name, spans, gaps in (
            ("no-scans", [], [(0, 10)]),
            ("one-scan", [(2, 3)], [(0, 2), (3, 10)]),
            ("two-scans", [(2, 3), (6, 7)], [(0, 2), (3, 6), (7, 10)]),
            ("naive-time", [(2, 3)], None),
            ("reversed-scan", [(3, 2)], None),
            ("outside-run", [(2, 11)], None)):
        directory = base / ("diagnosis-" + name)
        directory.mkdir()

        def stamp(second):
            return f"2026-01-01T00:00:{second:02d}+00:00"

        bindings = {"synthetic": {"bytes": 1, "sha256": "synthetic-only"}}
        receipt = {"exit": 0, "start": stamp(0), "end": stamp(10),
                   "declared_inputs_before": bindings, "declared_inputs_after": bindings}
        for filename, value in (("receipt.json", receipt),
                                ("declared-inputs-before.json", bindings),
                                ("declared-inputs-after.json", bindings)):
            (directory / filename).write_text(json.dumps(value))
        observations = [
            {"boundary": f"scan-{index}", "start": stamp(start), "end": stamp(end),
             "files": {"synthetic": {"mtime_ns": index}}}
            for index, (start, end) in enumerate(spans)]
        if name == "naive-time":
            observations[0]["start"] = "2026-01-01T00:00:02"
        if observations:
            (directory / "declared-input-metadata.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in observations))
        try:
            report = summarize(directory)
        except ValueError:
            check(gaps is None, name + ": valid timeline rejected")
        else:
            check(gaps is not None, name + ": invalid timeline accepted")
            actual = report["unobserved_intervals"]
            check([(row["unobserved_start"], row["unobserved_end"],
                    row["unobserved_seconds"]) for row in actual] ==
                  [(stamp(start), stamp(end), end - start) for start, end in gaps],
                  name + ": missing or incorrect observation gaps")
            check(report["endpoint_content_differences"] == [], name)
            check(report["runtime_diagnosis"] ==
                  "unavailable from these project observations", name)
        count += 1
        print("CHECK diagnosis-" + name, "pass")
    return count


def run_cases(base):
    base.mkdir()
    count = 0
    for name in ("success", "child-failure", "changed", "failed-and-changed",
                 "added", "removed", "missing-selector"):
        root = base / name
        for directory, pattern in verify.INPUT_SELECTORS:
            target = root / directory
            target.mkdir(parents=True, exist_ok=True)
            suffix = {"*.sv": ".sv", "*.sdc": ".sdc"}.get(pattern, ".md")
            (target / ("fixture" + suffix)).write_text("synthetic original\n")
        (root / "data/model/second.json").write_text("{}\n")

        def workload(experiment):
            target = root / "data/model/second.json"
            if name in ("changed", "failed-and-changed"):
                target.write_text('{"changed":true}\n')
            elif name == "added":
                (root / "data/model/added.json").write_text("{}\n")
            elif name in ("removed", "missing-selector"):
                target.unlink()
                if name == "missing-selector":
                    (root / "data/model/fixture.md").unlink()
            if name in ("child-failure", "failed-and-changed"):
                raise RuntimeError("deliberate synthetic child failure")

        with patch.object(verify, "__file__", str(root / "tests/verify.py")), \
                patch.object(verify, "l1", workload), \
                patch.object(sys, "argv", ["verify.py", "--suite", "l1", "--output", "run"]), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            result = verify.main()
        receipt = json.loads((root / "run/receipt.json").read_text())
        before_path = root / "run/declared-inputs-before.json"
        retained = before_path.read_text()
        check(json.loads(retained) == receipt["declared_inputs_before"], name)
        check(result == (0 if name == "success" else 1), name)
        check(receipt["exit"] == result, name)
        if name != "missing-selector":
            after = json.loads((root / "run/declared-inputs-after.json").read_text())
            check(after == receipt["declared_inputs_after"], name)
            expected = {"added": [], "removed": [], "changed": []}
            if name in ("changed", "failed-and-changed"):
                expected["changed"] = ["data/model/second.json"]
            elif name == "added":
                expected["added"] = ["data/model/added.json"]
            elif name == "removed":
                expected["removed"] = ["data/model/second.json"]
            check(receipt["declared_input_changes"] == expected, name)
            recorded = type("Recorded", (), {
                "root": root, "directory": root / "run", "output": Path("run"),
                "receipt": {},
            })()
            try:
                verify.record_input_bindings(recorded, "before")
            except FileExistsError:
                pass
            else:
                raise RuntimeError("existing binding overwritten: " + name)
        else:
            check("empty declared input selector" in receipt["input_binding_failure"], name)
            check("declared_inputs_after" not in receipt, name)
        check(before_path.read_text() == retained, name)
        check(("suite_failure" in receipt) ==
              (name in ("child-failure", "failed-and-changed")), name)
        check(("input_binding_failure" in receipt) ==
              (name not in ("success", "child-failure")), name)
        if name in ("child-failure", "failed-and-changed"):
            check(receipt["failure"] == "deliberate synthetic child failure",
                  name + ": final input hashing masked original suite failure")
        count += 1
        print("CHECK", name, "pass")

    root = base / "success"
    for child_fails, observer_fails in ((False, False), (True, False),
                                        (True, True), (False, True)):
        name = f"observed-child-{int(child_fails)}-{int(observer_fails)}"
        experiment = Experiment(root, Path(name), [name], [])
        observe = verify.observe_input_metadata

        def observer(experiment, boundary):
            if observer_fails and boundary.endswith(":after"):
                raise OSError("deliberate synthetic metadata failure")
            return observe(experiment, boundary)

        failure = None
        try:
            with patch.object(verify, "observe_input_metadata", observer):
                verify.run_observed_child(
                    experiment, [sys.executable, "-B", "-c",
                                 "print('SYNTHETIC_CHILD'); raise SystemExit("
                                 + str(7 if child_fails else 0) + ")"], name)
        except (OSError, RuntimeError) as error:
            failure = error
        experiment.finish(1 if failure is not None else 0, failure)
        command = experiment.receipt["commands"][0]
        check(command["exit"] == (7 if child_fails else 0), name)
        check(not command["timed_out"], name)
        check("SYNTHETIC_CHILD" in (root / command["stdout"]).read_text(), name)
        check((failure is not None) == (child_fails or observer_fails), name)
        if child_fails:
            check(type(failure) is RuntimeError and "failed; see" in str(failure),
                  name + ": metadata failure masked original child failure")
        elif observer_fails:
            check(type(failure) is OSError, name)
        if observer_fails:
            records = experiment.receipt["input_metadata_failures"]
            check(len(records) == 1, name)
            check(records[0]["boundary"] == name + ":after", name)
            check(records[0]["error"] == "deliberate synthetic metadata failure", name)
            check(records[0]["child_failure"] ==
                  (str(failure) if child_fails else None), name)
        count += 1
        print("CHECK", name, "pass")
    name = "observed-child-before-failure"
    experiment = Experiment(root, Path(name), [name], [])
    failure = None
    with patch.object(verify, "observe_input_metadata",
                      side_effect=OSError("deliberate synthetic pre-child metadata failure")), \
            patch.object(experiment, "run") as child:
        try:
            verify.run_observed_child(experiment, [sys.executable, "-B", "-c",
                                                   "raise SystemExit('must not launch')"], name)
        except OSError as error:
            failure = error
        check(not child.called, name + ": child launched after observation failure")
    experiment.finish(1 if failure is not None else 0, failure)
    check(isinstance(failure, OSError), name)
    check(not experiment.receipt["commands"], name)
    records = experiment.receipt.get("input_metadata_failures", [])
    check(len(records) == 1, name + ": missing pre-child diagnostic")
    check(records[0] == {
        "boundary": name + ":before",
        "error": str(failure),
        "child_failure": None,
    }, name)
    count += 1
    print("CHECK", name, "pass")

    for collision in ("both", "stderr-only"):
        name = "retained-log-" + collision
        experiment = Experiment(root, Path(name), [name], [])
        stdout = experiment.directory / "child.stdout"
        stderr = experiment.directory / "child.stderr"
        if collision == "both":
            experiment.run([sys.executable, "-B", "-c",
                            "import sys; print('original stdout'); "
                            "print('original stderr', file=sys.stderr)"], "child")
        else:
            stderr.write_text("original stderr\n")
        originals = {path: path.read_bytes() for path in (stdout, stderr)
                     if path.exists()}
        failure = None
        try:
            experiment.run([sys.executable, "-B", "-c",
                            "raise SystemExit('must not launch')"], "child")
        except (OSError, RuntimeError) as error:
            failure = error
        experiment.finish(1 if failure is not None else 0, failure)
        check(all(path.read_bytes() == data for path, data in originals.items()),
              name + ": existing raw evidence overwritten")
        check(isinstance(failure, FileExistsError), name + ": collision not rejected")
        command = experiment.receipt["commands"][-1]
        check(command["exit"] is None and not command["timed_out"], name)
        check("launch_error" in command, name)
        count += 1
        print("CHECK", name, "pass")

    name = "missing-child-executable"
    experiment = Experiment(root, Path(name), [name], [])
    failure = None
    try:
        experiment.run([str(experiment.directory / "nonexistent-executable")], "child")
    except OSError as error:
        failure = error
    experiment.finish(1 if failure is not None else 0, failure)
    check(isinstance(failure, FileNotFoundError), name)
    command = experiment.receipt["commands"][0]
    check(command["exit"] is None and not command["timed_out"], name)
    check("launch_error" in command and "end" in command, name)
    check(all((root / command[key]).is_file() for key in ("stdout", "stderr")), name)
    count += 1
    print("CHECK", name, "pass")
    name = "retained-receipt"
    experiment = Experiment(root, Path(name), [name], [])
    receipt_path = experiment.directory / "receipt.json"
    original = b'{"synthetic_retained_receipt":true}\n'
    receipt_path.write_bytes(original)
    failure = None
    try:
        experiment.finish(0)
    except OSError as error:
        failure = error
    check(receipt_path.read_bytes() == original,
          name + ": existing receipt overwritten")
    check(isinstance(failure, FileExistsError),
          name + ": receipt collision not rejected")
    count += 1
    print("CHECK", name, "pass")
    for primary, collision in ((False, False), (True, False), (True, True)):
        name = f"receipt-publication-{int(primary)}-{int(collision)}"
        experiment = Experiment(root, Path(name), [name], [])
        receipt_path = experiment.directory / "receipt.json"
        original = b'{"synthetic_retained_receipt":true}\n'
        if collision:
            receipt_path.write_bytes(original)
        original_failure = RuntimeError("deliberate original workload failure") if primary else None
        publication_failure = FileNotFoundError("deliberate missing output namespace")
        actual_open = Path.open

        def publish(path, *args, **kwargs):
            if path == receipt_path and not collision:
                raise publication_failure
            return actual_open(path, *args, **kwargs)

        stdout, stderr = io.StringIO(), io.StringIO()
        caught = None
        with patch.object(Path, "open", publish), \
                patch.object(Path, "mkdir") as mkdir, \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                experiment.finish(1 if primary else 0, original_failure)
            except (OSError, RuntimeError) as error:
                caught = error
            check(not mkdir.called, name + ": attempted to recreate evidence")
        if primary:
            check(caught is original_failure, name + ": publication masked original failure")
            check(isinstance(caught.__cause__,
                             FileExistsError if collision else FileNotFoundError),
                  name + ": missing chained publication failure")
        else:
            check(caught is publication_failure, name + ": publication failure suppressed")
        diagnostic = json.loads(stderr.getvalue())
        check(diagnostic["event"] == "receipt-publication-failed" and
              diagnostic["receipt_published"] is False and
              diagnostic["receipt"] == str(experiment.output / "receipt.json") and
              diagnostic["exit"] == (1 if primary else 0) and
              diagnostic["failure"] == (str(original_failure) if primary else None) and
              diagnostic["publication_error"].startswith(
                  "FileExistsError:" if collision else "FileNotFoundError:"),
              name + ": incomplete stderr diagnostic")
        check(not stdout.getvalue(), name + ": advertised an unpublished receipt")
        if collision:
            check(receipt_path.read_bytes() == original, name + ": prior receipt changed")
        else:
            check(not receipt_path.exists(), name + ": manufactured replacement receipt")
        count += 1
        print("CHECK", name, "pass")
    count += diagnosis_cases(base)
    check(count == 25, "missing synthetic comparisons")
    print("SYNTHETIC_BINDING_CASES", count, "NO_RTL_EXECUTED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = args.output or Path("evidence/verification") / (
        "input-binding-" + uuid.uuid4().hex)
    if output.is_absolute() or ".." in output.parts:
        parser.error("output must be project-relative")
    if args.worker:
        run_cases(root / output / "cases")
        return 0
    experiment = invocation_experiment(root, output, sys.orig_argv,
                            ["tests/input_binding_check.py", "tests/verify.py",
                             "tests/retention.py", "tests/build_cache.py", "tests/binding_diagnosis.py",
                             "tests/invocation.py", "tests/invocation_check.py",
                             "tests/progress_check.py",
                             "tests/scheduling_check.py", "tests/README.md"])
    experiment.receipt["scope"] = "synthetic retention only; no RTL or aggregate suite"
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        experiment.run([sys.executable, "--version"], "python-version")
        experiment.run([sys.executable, "-B", "tests/input_binding_check.py",
                        "--worker", "--output", str(experiment.output)], "synthetic-cases")
        experiment.receipt["compared_cases"] = 25
        run_regression(experiment)
        experiment.receipt["invocation_regression"] = str(
            experiment.output / "invocation-regression/receipt.json")
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
