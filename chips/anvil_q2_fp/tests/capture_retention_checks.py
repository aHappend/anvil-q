"""Bounded capture recovery: failure fixtures and unchanged reduced RTL attention."""

import argparse
import datetime
import hashlib
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run, audit_streams


FAILED_BENCHMARK = "evidence/l1/l1-benchmark-20261029T053434Z-037abc33/receipt.json"
FAILED_BENCHMARK_SHA256 = "659015c5be09b925d359301cb11731959673b90e74249b10f40c768ef3f33f4f"
ADMITTED_DESIGNER = (
    "evidence/preparation/designer-attention-request-static-20261029T062619Z-54e76ddf/"
    "receipt.json")
ADMITTED_DESIGNER_SHA256 = "4a563731c49577f61fc910500c167c9676b9374939f9cf27ce35b2371eff4fce"
ADMITTED_TRANSITION = {
    "rtl/anvil_q2_fp_gqa_attention.sv": (
        "0d144e671dd14580ccb86a96210d3b2adfcbb2dbe238b91f51f7d6a731bdcf22",
        "57efcd7438cfd5b3ff597c3a7a4cc2ac496f44d8d21f46574f0e6dc00cd1d181"),
    "design/SPEC.md": (
        "fc7b8c1a30f2e6da37eb839ab4d05f29e82b8eb5b1b88848429aeac2d43bf9e0",
        "66c19ac4cc97712a4fdddf72990c889992e47b82f1f0066d54c3a1f627151bf2"),
    "design/ARCHITECTURE.md": (
        "5e15d80b09e0edc1449f8a51d04c34fa14a2bc61be65aff0c445c9a4d1db68ce",
        "1db03d55d8a46919c961bd8fa5ce0cbf36327495a5b6edf6eab5028147b93f8e"),
    "design/INTEGRATION.md": (
        "d28f45de29bb54c1e6f1d18d8840585cdeb11617a588daaa8cc8cd9e4550da4a",
        "c0cbbff5ebd17679705ed8b992b1c6df38993cd21e7ffce4cebf4b2b66c3292f"),
}

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


def existing_root_fixture(run):
    root = run.relative(run.path / "root-reuse")
    children = []
    intervals = []
    preserved = {}
    compared_files = 0

    def launch(index):
        return run.command(
            ["python3", "-c",
             "import sys; sys.path.insert(0, 'tests'); "
             "from retained import Run; "
             "run = Run('same-name'); "
             "output = run.command("
             f"['python3', '-c', \"print('root-reuse-{index}')\"], 'payload'); "
             f"assert output.read_text() == 'root-reuse-{index}\\n'; "
             f"run.finish('passed-focused-only', fixture='existing-root', invocation={index})"],
            f"root-reuse-fresh-process-{index}",
            environment={"ANVIL_EVIDENCE_ROOT": root})

    concurrent_outputs = []
    for index in range(4):
        if index < 2:
            output = launch(index)
        else:
            if index == 2:
                with ThreadPoolExecutor(max_workers=2) as pool:
                    concurrent_outputs = list(pool.map(launch, range(2, 4)))
            output = concurrent_outputs[index - 2]
        names = [line for line in output.read_text().splitlines()
                 if line.endswith("/receipt.json")]
        assert len(names) == 1, names
        path = ROOT / names[0]
        path.resolve().relative_to((ROOT / root).resolve())
        child = json.loads(path.read_text())
        assert child["evidence_root"] == root
        assert child["source_sha256"] == run.receipt["source_sha256"]
        assert child["outcome"] == "passed-focused-only"
        assert child["invocation"] == index
        intervals.append({
            "started_at": child["started_at"], "ended_at": child["ended_at"]})
        assert path.parent not in children, "reused a prior run directory"
        for name, expected in preserved.items():
            assert (ROOT / name).read_bytes() == expected, (
                f"executing a new run changed prior evidence: {name}")
        compared_files += len(preserved)
        children.append(path.parent)
        for target in path.parent.rglob("*"):
            if target.is_file():
                preserved[run.relative(target)] = target.read_bytes()
    reopened = []
    for index, path in enumerate(children):
        name = run.relative(path / "receipt.json")
        output = run.command(
            ["python3", "tests/stream_retention_checks.py", "--action", "reopen",
             "--path", name], f"root-reuse-independent-reopen-{index}")
        result = json.loads(output.read_text())
        assert result["receipt"] == name
        assert result["outcome"] == "passed-focused-only"
        assert result["raw_streams_compared"] > 0
        reopened.append(result)
    for name, expected in preserved.items():
        assert (ROOT / name).read_bytes() == expected, (
            f"independent reopening changed prior evidence: {name}")
    assert len(children) == len(reopened) == 4 and compared_files > 0
    overlap = (
        min(datetime.datetime.fromisoformat(row["ended_at"]) for row in intervals[2:])
        - max(datetime.datetime.fromisoformat(row["started_at"]) for row in intervals[2:])
    ).total_seconds()
    assert overlap > 0, "concurrent root-reuse invocations did not overlap"
    return dict(
        root=root, receipts=[run.relative(path / "receipt.json") for path in children],
        invocations_compared=len(children), preserved_files_compared=compared_files,
        concurrent_invocations=2,
        concurrent_overlap_s=overlap, invocation_intervals=intervals,
        allocation="fresh Python processes with ANVIL_EVIDENCE_ROOT",
        independent_reopens=reopened,
        preserved_sha256={name: hashlib.sha256(data).hexdigest()
                          for name, data in preserved.items()})


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
        root_reuse = existing_root_fixture(run)
        run.finish("passed-focused-only", fixtures=results, root_reuse=root_reuse,
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
        admitted = {}
        run.receipt["input_sha256"] = {}
        for name, expected in ((FAILED_BENCHMARK, FAILED_BENCHMARK_SHA256),
                               (ADMITTED_DESIGNER, ADMITTED_DESIGNER_SHA256)):
            data = (ROOT / name).read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            run.receipt["input_sha256"][name] = digest
            assert digest == expected, f"admitted provenance receipt changed: {name}"
            admitted[name] = json.loads(data)
        historical = admitted[FAILED_BENCHMARK]
        revised = admitted[ADMITTED_DESIGNER]["source_sha256"]
        run.receipt["historical_failure"] = historical.get("failure")
        protected = {name: expected for name, expected in historical["source_sha256"].items()
                     if name.startswith(("rtl/", "design/", "anvil_q2_reference/rtl/"))}
        assert protected, "historical source provenance unavailable"
        for name, (before, after) in ADMITTED_TRANSITION.items():
            assert protected.get(name) == before, f"historical transition mismatch: {name}"
            assert revised.get(name) == after, f"revised transition mismatch: {name}"
        expected_product = dict(protected)
        expected_product.update({name: pair[1] for name, pair in ADMITTED_TRANSITION.items()})
        revised_product = {name: digest for name, digest in revised.items()
                           if name.startswith(("rtl/", "design/", "anvil_q2_reference/rtl/"))}
        current_product = {
            name: digest for name, digest in run.receipt["source_sha256"].items()
            if name.startswith(("rtl/", "design/", "anvil_q2_reference/rtl/"))}
        assert revised_product == expected_product, "unadmitted Designer product transition"
        assert current_product == expected_product, "protected product source changed"
        run.receipt["admitted_product_transition"] = {
            "admission": "call-0036",
            "description": "Registered non-fall-through attention request buffer and its "
                           "SPEC, ARCHITECTURE and INTEGRATION documentation; "
                           "no numerical or transaction assertion change.",
            "sources": {name: dict(historical=pair[0], revised=pair[1])
                        for name, pair in ADMITTED_TRANSITION.items()}}
        run.receipt["unchanged_product_source_count"] = len(protected) - len(ADMITTED_TRANSITION)
        run.receipt["verification_source_changes"] = [
            name for name, current in run.receipt["source_sha256"].items()
            if name.startswith("tests/") and historical["source_sha256"].get(name) != current]
        assert set(run.receipt["verification_source_changes"]) == {
            "tests/retained.py", "tests/capture_retention_checks.py"}
        revised_tests = {name: digest for name, digest in revised.items()
                         if name.startswith("tests/") and
                         name != "tests/capture_retention_checks.py"}
        current_tests = {name: digest for name, digest in run.receipt["source_sha256"].items()
                         if name.startswith("tests/") and
                         name != "tests/capture_retention_checks.py"}
        assert current_tests == revised_tests, "unadmitted verification source changed"
        run.command(["python3", "--version"], "python-version")
        run.receipt["root_reuse"] = existing_root_fixture(run)
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
