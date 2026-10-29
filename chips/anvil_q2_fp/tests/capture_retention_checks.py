"""Bounded capture recovery: failure fixtures and unchanged reduced RTL attention."""

import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run, audit_streams


FAILED_BENCHMARK = "evidence/l1/l1-benchmark-20261029T053434Z-037abc33/receipt.json"

FIXTURE = r"""
import json, os, sys, time
from pathlib import Path
action, target, observations = sys.argv[1:]
target, observations = Path(target), Path(observations)
print("capture fixture payload " * 128, flush=True)
if action != "healthy":
    deadline = time.monotonic() + 30
    while True:
        rows = [json.loads(line) for line in observations.read_text().splitlines()]
        if any(row["phase"] == "live" and
               row["streams"][str(target)]["descriptor"]["size"] > 0 for row in rows):
            break
        assert time.monotonic() < deadline, "fixture did not observe a live checkpoint"
        time.sleep(0.05)
    if action == "missing":
        target.unlink()
    elif action == "replaced":
        target.rename(target.with_suffix(".original"))
        with target.open("x") as stream:
            stream.write("deliberate replacement fixture\n")
    elif action == "truncated":
        with target.open("r+b") as stream:
            stream.truncate(0)
    time.sleep(5)
"""


def fixtures(repair_of=None):
    run = Run("capture-retention-fixtures")
    if repair_of:
        run.receipt["repair_of"] = repair_of
    try:
        run.command(["python3", "--version"], "python-version")
        results = []
        for interactive in (False, True):
            for action in ("healthy", "missing", "replaced", "truncated"):
                child = Run(f"capture-fixture-{'interactive' if interactive else 'command'}-{action}",
                            root=run.relative(run.path / "children"))
                target = child.path / "fixture.stdout.txt"
                observations = target.with_suffix(".capture.jsonl")
                argv = ["python3", "-c", FIXTURE, action, child.relative(target),
                        child.relative(observations)]
                try:
                    if interactive:
                        def consume(process, raw):
                            for line in process.stdout:
                                raw.write(line)
                                raw.flush()
                        child.interactive(argv, "fixture", consume, timeout=3600)
                    else:
                        child.command(argv, "fixture", timeout=3600)
                    assert action == "healthy", "capture corruption was not rejected"
                    child.finish("passed-focused-only", fixture=action)
                    results.append(dict(action=action, interactive=interactive, rejected=False,
                                        receipt=child.relative(child.path / "receipt.json")))
                except RuntimeError as exc:
                    child.finish("failed", expected_fixture_rejection=action != "healthy",
                                 failure=str(exc), fixture=action)
                    assert action != "healthy", str(exc)
                    record = child.receipt["commands"][-1]
                    first = record.get("first_capture_failure")
                    assert first and first["phase"] == "live", record
                    reason = " ".join(first["errors"])
                    expected = {"missing": "FileNotFoundError", "replaced": "pathname replaced",
                                "truncated": "stream truncated"}[action]
                    assert expected in reason, reason
                    assert record["exit_code"] is not None, "child not settled"
                    assert record["capture_reopen"]["exit_code"] != 0
                    results.append(dict(action=action, interactive=interactive, rejected=True,
                                        receipt=child.relative(child.path / "receipt.json")))
        run.finish("passed-focused-only", fixtures=results,
                   limitations="Synthetic retention failure handling only; not RTL evidence.")
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError, KeyError) as exc:
        traceback.print_exc()
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        return 1


def probe():
    run = Run("attention-capture-recovery")
    run.receipt["repair_of"] = FAILED_BENCHMARK
    try:
        failed = (ROOT / FAILED_BENCHMARK).read_bytes()
        run.receipt["input_sha256"] = {FAILED_BENCHMARK: hashlib.sha256(failed).hexdigest()}
        historical = json.loads(failed)
        run.receipt["historical_failure"] = historical.get("failure")
        protected = {name: expected for name, expected in historical["source_sha256"].items()
                     if name.startswith(("rtl/", "design/", "anvil_q2_reference/rtl/"))}
        assert protected, "historical source provenance unavailable"
        assert all(run.receipt["source_sha256"].get(name) == expected
                   for name, expected in protected.items()), "protected product source changed"
        run.receipt["unchanged_product_source_count"] = len(protected)
        run.receipt["verification_source_changes"] = [
            name for name, current in run.receipt["source_sha256"].items()
            if name.startswith("tests/") and historical["source_sha256"].get(name) != current]
        assert set(run.receipt["verification_source_changes"]) == {
            "tests/retained.py", "tests/capture_retention_checks.py"}
        run.command(["python3", "--version"], "python-version")
        output = run.command(
            ["python3", "tests/attention_checks.py", "--seed", "17", "--reduced"],
            "reduced-attention", timeout=21600,
            environment={"ANVIL_EVIDENCE_ROOT": run.relative(run.path / "children"),
                         "ANVIL_SIM_CACHE": run.relative(run.path / "compiled-models")})
        names = [line for line in output.read_text().splitlines()
                 if line.endswith("/receipt.json")]
        assert len(names) == 1, names
        child_path = ROOT / names[0]
        child_path.resolve().relative_to(run.path / "children")
        child = json.loads(child_path.read_text())
        assert child["outcome"] == "passed-focused-only", child.get("failure")
        assert child["source_sha256"] == run.receipt["source_sha256"]
        simulations = [c for c in child["commands"] if c.get("live_stimulus")]
        assert len(simulations) == 2
        for command in simulations:
            assert command["exit_code"] == 0 and not command["timed_out"]
            assert not command.get("first_capture_failure"), command
            assert command["capture_reopen"]["exit_code"] == 0
            rows = [json.loads(line) for line in
                    (ROOT / command["capture_observations"]).read_text().splitlines()]
            assert rows[0]["phase"] == "creation" and rows[-1]["phase"] == "pre-close"
            assert any(row["phase"] == "live" for row in rows), "no live RTL capture observation"
            assert all(not row["errors"] for row in rows)
        for mode in ("mode0", "mode1"):
            metrics = child["metrics"][mode]
            assert metrics["frames_compared"] == 9
            assert metrics["memory_requests"] == metrics["memory_responses"] > 0
            assert metrics["attention_values_compared"] > 0
        run.command(["python3", "tests/stream_retention_checks.py", "--action", "reopen",
                     "--path", names[0]], "independent-child-reopen")
        hashes, errors = audit_streams(child["commands"])
        assert not errors, errors
        assert hashes == child["raw_stream_sha256"], "child stream audit changed"
        run.finish(
            "passed-focused-only", child_receipt=names[0], metrics=child["metrics"],
            limitations="Reduced seed-17 attention only, both cache modes, compiled Verilator "
                        "with Icarus startup. Does not explain historical loss or establish "
                        "full benchmark, timing, resources, hardware or delivery acceptance.")
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError, KeyError) as exc:
        traceback.print_exc()
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True, choices=("fixtures", "probe"))
    parser.add_argument("--repair-of", help="prior failed preparation receipt, kept unchanged")
    args = parser.parse_args()
    raise SystemExit(fixtures(args.repair_of) if args.action == "fixtures" else probe())
