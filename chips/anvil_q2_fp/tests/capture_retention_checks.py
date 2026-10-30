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
# Canonical sorted source-hash map from the hash-pinned failed benchmark above.
PARENT_MANIFEST_SHA256 = "7d98c610c5a74959af8ced2c640e3331580f2ebedcea9a4982783b908eeb654c"
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


def source_lineage(historical, revised, current):
    prefixes = ("rtl/", "design/", "anvil_q2_reference/rtl/")
    protected = {name: digest for name, digest in historical.items()
                 if name.startswith(prefixes)}
    assert protected, "historical source provenance unavailable"
    expected_revision = dict(protected)
    for name, (before, after) in ADMITTED_TRANSITION.items():
        assert protected.get(name) == before, f"historical transition mismatch: {name}"
        assert revised.get(name) == after, f"revised transition mismatch: {name}"
        expected_revision[name] = after
    revised_product = {name: digest for name, digest in revised.items()
                       if name.startswith(prefixes)}
    assert revised_product == expected_revision, "historical Designer transition mismatch"
    reference = {name: digest for name, digest in historical.items()
                 if name.startswith("anvil_q2_reference/rtl/")}
    current_reference = {name: digest for name, digest in current.items()
                         if name.startswith("anvil_q2_reference/rtl/")}
    assert reference and current_reference == reference, "accepted parent RTL changed"

    def changes(before, after):
        return {name: dict(historical=before.get(name), current=after.get(name))
                for name in sorted(before.keys() | after.keys())
                if before.get(name) != after.get(name)}

    return dict(
        historical_transition_source_count=len(ADMITTED_TRANSITION),
        unchanged_reference_source_count=len(reference),
        product_changes_since_historical_transition=changes(
            revised_product, {name: digest for name, digest in current.items()
                              if name.startswith(prefixes)}),
        verification_changes_since_failure=changes(
            {name: digest for name, digest in historical.items() if name.startswith("tests/")},
            {name: digest for name, digest in current.items() if name.startswith("tests/")}))


def parent_identity(current):
    reference = {name: digest for name, digest in current.items()
                 if name.startswith("anvil_q2_reference/rtl/")}
    digest = hashlib.sha256(json.dumps(
        reference, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == PARENT_MANIFEST_SHA256, "accepted parent RTL changed"
    return dict(source_count=len(reference), manifest_sha256=digest)


def historical_receipt(path, expected):
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return None, dict(status="unverified", reason="historical receipt unavailable",
                          expected_sha256=expected)
    digest = hashlib.sha256(data).hexdigest()
    assert digest == expected, f"admitted provenance receipt changed: {path.name}"
    return json.loads(data), dict(status="integrity-verified", sha256=digest,
                                 functional_acceptance=False)


def historical_provenance(run):
    run.receipt["unchanged_parent"] = parent_identity(run.receipt["source_sha256"])
    admitted = {}
    audit = run.receipt["historical_provenance"] = {}
    for name, expected, endpoint in (
            (FAILED_BENCHMARK, FAILED_BENCHMARK_SHA256, 0),
            (ADMITTED_DESIGNER, ADMITTED_DESIGNER_SHA256, 1)):
        record, audit[name] = historical_receipt(ROOT / name, expected)
        if record is None:
            continue
        run.receipt["input_sha256"][name] = audit[name]["sha256"]
        sources = record["source_sha256"]
        parent_identity(sources)
        for source, pair in ADMITTED_TRANSITION.items():
            assert sources.get(source) == pair[endpoint], (
                f"historical transition mismatch: {source}")
        admitted[name] = record
    if FAILED_BENCHMARK in admitted:
        run.receipt["historical_failure"] = admitted[FAILED_BENCHMARK].get("failure")
    if len(admitted) == 2:
        run.receipt["source_lineage"] = source_lineage(
            admitted[FAILED_BENCHMARK]["source_sha256"],
            admitted[ADMITTED_DESIGNER]["source_sha256"], run.receipt["source_sha256"])
    else:
        run.receipt["source_lineage"] = dict(
            status="unverified", reason="historical transition inputs unavailable",
            missing_receipts=[name for name, row in audit.items()
                              if row["status"] == "unverified"])


def historical_fixtures(run):
    path = run.path / "historical-fixture.json"
    path.write_text('{"source_sha256": {}}\n')
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    record, audit = historical_receipt(path, expected)
    assert record == {"source_sha256": {}} and audit["status"] == "integrity-verified"
    missing, audit = historical_receipt(run.path / "unavailable-history.json", expected)
    assert missing is None and audit["status"] == "unverified"
    rejected = []
    for label, check in (
        ("receipt-corruption", lambda: historical_receipt(path, "0" * 64)),
        ("parent-change", lambda: parent_identity(
            run.receipt["source_sha256"] | {
                "anvil_q2_reference/rtl/anvil_q2_top.sv": "changed"})),
        ("parent-removal", lambda: parent_identity({
            name: digest for name, digest in run.receipt["source_sha256"].items()
            if name != "anvil_q2_reference/rtl/anvil_q2_top.sv"})),
    ):
        try:
            check()
        except AssertionError as exc:
            expected_error = ("admitted provenance receipt changed" if label == "receipt-corruption"
                              else "accepted parent RTL changed")
            assert expected_error in str(exc), str(exc)
            rejected.append(label)
        else:
            raise AssertionError(f"provenance corruption was not rejected: {label}")
    return dict(available_integrity_compared=True, missing_history_unverified=True,
                unchanged_parent=parent_identity(run.receipt["source_sha256"]),
                rejected_corruptions=rejected)


def lineage_fixtures():
    historical = {name: pair[0] for name, pair in ADMITTED_TRANSITION.items()}
    historical.update({"anvil_q2_reference/rtl/parent.sv": "parent",
                       "rtl/unchanged.sv": "unchanged", "tests/check.py": "old-check"})
    revised = historical | {name: pair[1] for name, pair in ADMITTED_TRANSITION.items()}
    current = revised | {"rtl/new_adder.sv": "adder", "tests/check.py": "new-check"}
    current.pop("rtl/unchanged.sv")
    lineage = source_lineage(historical, revised, current)
    assert lineage["product_changes_since_historical_transition"] == {
        "rtl/new_adder.sv": dict(historical=None, current="adder"),
        "rtl/unchanged.sv": dict(historical="unchanged", current=None)}
    assert lineage["verification_changes_since_failure"] == {
        "tests/check.py": dict(historical="old-check", current="new-check")}
    assert not source_lineage(historical, revised, revised)[
        "product_changes_since_historical_transition"]
    rejected = []
    for label, old, revision, present, expected in (
        ("historical-transition", historical | {"design/SPEC.md": "corrupted"},
         revised, current, "historical transition mismatch"),
        ("historical-revision", historical, revised | {"rtl/unrecorded.sv": "unexpected"},
         current, "historical Designer transition mismatch"),
        ("parent-change", historical, revised,
         current | {"anvil_q2_reference/rtl/parent.sv": "changed"}, "accepted parent RTL changed"),
        ("parent-removal", historical, revised,
         {name: digest for name, digest in current.items()
          if not name.startswith("anvil_q2_reference/rtl/")}, "accepted parent RTL changed"),
    ):
        try:
            source_lineage(old, revision, present)
        except AssertionError as exc:
            assert expected in str(exc), str(exc)
            rejected.append(label)
        else:
            raise AssertionError(f"lineage corruption was not rejected: {label}")
    return dict(revision_deltas_compared=3, unchanged_revision_compared=True,
                rejected_corruptions=rejected)


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
        lineage = lineage_fixtures()
        history = historical_fixtures(run)
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
                   source_lineage_fixtures=lineage, historical_provenance_fixtures=history,
                   limitations="Synthetic retention failure handling only; not RTL evidence.")
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError, KeyError) as exc:
        traceback.print_exc()
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        return 1


def probe(repair_of=None):
    run = Run("attention-capture-recovery")
    run.receipt["repair_of"] = repair_of or FAILED_BENCHMARK
    run.receipt["historical_benchmark_receipt"] = FAILED_BENCHMARK
    try:
        run.receipt["input_sha256"] = {}
        historical_provenance(run)
        run.receipt["historical_admitted_product_transition"] = {
            "admission": "call-0036",
            "description": "Registered non-fall-through attention request buffer and its "
                           "SPEC, ARCHITECTURE and INTEGRATION documentation; "
                           "no numerical or transaction assertion change.",
            "sources": {name: dict(historical=pair[0], revised=pair[1])
                        for name, pair in ADMITTED_TRANSITION.items()}}
        run.receipt["source_binding_policy"] = (
            "Available historical receipts are integrity checked, not functional prerequisites "
            "or a passing baseline. Missing history remains explicitly unverified. "
            "The pinned parent source manifest is enforced independently of historical files. "
            "The current source_sha256 binds this invocation; "
            "child execution must match it exactly. Accepted parent RTL remains unchanged.")
        run.command(["python3", "--version"], "python-version")
        run.command(["python3", "tests/attention_stream_checks.py"], "bounded-stream-fixtures",
                    environment={"ANVIL_EVIDENCE_ROOT": run.relative(run.path / "children")})
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
        for mode, command in enumerate(simulations):
            checked = command["checked_stream"]
            metrics = child["metrics"][f"mode{mode}"]
            assert checked["discarded_transaction_counts"] == {
                "MEM_REQ": metrics["memory_requests"], "MEM_RSP": metrics["memory_responses"]}
            assert checked["protocol_records"] == (
                metrics["memory_requests"] + metrics["memory_responses"]
                + 3 * metrics["frames_compared"] + 1)
            text = (ROOT / command["stdout"]).read_text()
            assert "\nMEM_REQ " not in text and "\nMEM_RSP " not in text
            assert len(text.encode()) < 16384
        assert child["mode0_retention_after_mode1"]
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
    raise SystemExit(fixtures(args.repair_of) if args.action == "fixtures"
                     else probe(args.repair_of))
