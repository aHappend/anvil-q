"""Retained bounded compiler/dispatch measurements and complete repair evidence.

Run --action probe --workers 4|8 --mode aggregate|split before choosing a
production policy. --action full executes the unchanged self-contained behavior
command in a fresh namespace; historical focused results are never substituted.
"""

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
from retained import ROOT, Run, audit_streams
from simulation import (BUILD_MEMORY, BUILD_RESERVE, MAXIMUM_BUILDS, STORAGE_HEADROOM,
                        build_model, build_policy)
from types import SimpleNamespace
from verify import configuration_groups, execute_group, jobs


PRIOR = Path("evidence/l1/l1-behavior-20261030T015154Z-c3231bb6")
MISSING = (
    "evidence/preparation/generated-build-recovery-20261030T014610Z-178337f1/receipt.json",
    "evidence/preparation/generated-build-recovery-audit-20261030T014806Z-bad627ad/receipt.json",
)
INTERRUPTED_PREPARATION = (
    "evidence/preparation/behavior-dispatch-probe-4-aggregate-20261030T024006Z-5017838e",
    "evidence/preparation/behavior-dispatch-probe-4-split-20261030T024255Z-48651b32",
    "evidence/preparation/behavior-dispatch-probe-8-split-20261030T024540Z-b00af57d",
    "evidence/preparation/behavior-dispatch-full-4-aggregate-20261030T024739Z-aa672d75",
)
INTERRUPTED_PARENT = Path("evidence/l1/l1-behavior-20261030T024740Z-9d75b4e1")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixtures():
    planned = jobs("behavior")
    original = json.loads((ROOT / PRIOR / "check-manifest.json").read_text())["jobs"]
    assert [(a, ["python3", *b], c) for a, b, c in planned] == [
        (r["id"], r["argv"], r["requirement"]) for r in original]
    rows = [dict(id=a, argv=["python3", *b]) for a, b, _ in planned]
    groups = configuration_groups(rows)
    assert len(rows) == 673
    flattened = [r for g in groups for r in g]
    assert len(flattened) == len(rows) and {id(r) for r in flattened} == {id(r) for r in rows}
    for group in groups:
        assert len({tuple(r["argv"]) for r in group}) == len(group)
    with_limit = int(os.environ.get("ANVIL_SIM_BUILD_LIMIT", MAXIMUM_BUILDS))
    for storage, cpus, memory, expected in (
            (STORAGE_HEADROOM + BUILD_RESERVE, 256, 64 * BUILD_MEMORY, 1),
            (STORAGE_HEADROOM + 32 * BUILD_RESERVE, 2, 64 * BUILD_MEMORY, 1),
            (STORAGE_HEADROOM + 32 * BUILD_RESERVE, 256, 2 * BUILD_MEMORY, 1),
            (STORAGE_HEADROOM + 32 * BUILD_RESERVE, 256, 64 * BUILD_MEMORY, with_limit)):
        assert build_policy(storage, cpus, memory)["maximum_concurrent_jobs"] == expected
    print(json.dumps(dict(unchanged_jobs=len(rows), configuration_groups=len(groups),
                         resource_fixtures=4)))


def cache_fixtures(run):
    directory = run.path / "cache-fixtures"
    directory.mkdir()
    binary, artifact, index = [directory / name for name in ("model", "generated.cpp", "index.json")]
    binary.write_bytes(b"synthetic executable identity fixture")
    artifact.write_bytes(b"synthetic generated source\n")
    identity = {"parameters": {"BANKS": 2}, "sources": {"fixture": "source-hash"}}
    entry = dict(identity=identity, binary=run.relative(binary), binary_sha256=sha(binary),
                 artifact_sha256={run.relative(artifact): sha(artifact)})
    index.write_text(json.dumps(entry))
    fake = SimpleNamespace(receipt={})
    assert build_model(fake, None, [], {}, "fixture", identity, index) == binary
    rejected = []
    for kind in ("identity", "binary", "artifact"):
        changed = dict(identity, parameters={"BANKS": 4}) if kind == "identity" else identity
        if kind == "binary":
            binary.write_bytes(b"corrupted binary")
        if kind == "artifact":
            artifact.write_bytes(b"corrupted generated source\n")
        try:
            build_model(fake, None, [], {}, "fixture", changed, index)
        except AssertionError as exc:
            assert {"identity": "identity mismatch", "binary": "binary changed",
                    "artifact": "evidence changed"}[kind] in str(exc)
            rejected.append(dict(case=kind, diagnostic=str(exc)))
        else:
            raise AssertionError(f"cache accepted corrupt {kind}")
        binary.write_bytes(b"synthetic executable identity fixture")
    run.receipt["cache_integrity_fixtures"] = rejected


def descendants_rss(pid):
    total, pending, seen = 0, [pid], set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        try:
            base = Path("/proc") / str(current)
            total += int((base / "statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE")
            for task in (base / "task").iterdir():
                pending.extend(map(int, (task / "children").read_text().split()))
        except (FileNotFoundError, ProcessLookupError):
            continue
    return total


def probe_rows():
    # Eight distinct real configurations: two tensor paths, singleton, lifecycle
    # and native rows, repeated in both formats. No shared historical binary.
    selected = {
        f"token-{fmt}-w1-c1-b1-s17" for fmt in ("bf16", "fp16")
    } | {
        f"singleton-{fmt}-w0-c0-b2-q3" for fmt in ("bf16", "fp16")
    } | {
        f"top-cancel-held-{fmt}-w1-c1-b4" for fmt in ("bf16", "fp16")
    } | {
        f"native-row-{fmt}-w1-b2-p6-s17" for fmt in ("bf16", "fp16")
    }
    rows = [dict(id=a, argv=["python3", *b], requirement=c, outcome="not-executed")
            for a, b, c in jobs("behavior") if a in selected]
    assert len(rows) == 8
    return rows


def execute(action, workers, mode):
    run = Run(f"behavior-dispatch-{action}-{workers}-{mode}", root="evidence/preparation")
    stop = threading.Event()
    samples, errors = [], []

    def monitor():
        while not stop.is_set():
            try:
                samples.append(dict(monotonic_s=time.monotonic(),
                                    descendant_rss_bytes=descendants_rss(os.getpid()),
                                    **build_policy()))
            except OSError as exc:
                errors.append(str(exc))
            stop.wait(1)

    thread = threading.Thread(target=monitor)
    thread.start()
    started = time.monotonic()
    def retain_samples():
        stop.set()
        thread.join()
        path = run.path / "resource-samples.json"
        with path.open("x") as stream:
            json.dump(samples, stream, indent=2)
            stream.write("\n")
        run.receipt["resource_samples_sha256"] = {run.relative(path): sha(path)}

    try:
        run.receipt["repair_of"] = dict(runtime_attempt=997, parent_receipt_absent=True,
                                         canceled_campaign=str(PRIOR))
        run.receipt["unavailable_historical_receipts"] = [p for p in MISSING if not (ROOT / p).is_file()]
        run.receipt["historical_claims_relied_upon"] = False
        cache_fixtures(run)
        run.command(["python3", "--version"], "python-version")
        for tool in ("verilator", "g++", "make"):
            run.command([tool, "--version"], tool + "-version")
        env = {"ANVIL_SIM_BUILD_LIMIT": str(workers), "ANVIL_SIM_BUILD_MODE": mode}
        run.command(["python3", "tests/behavior_dispatch_checks.py", "--action", "fixtures"],
                    "fixtures", environment=env)
        if action == "probe":
            rows = probe_rows()
            # execute_record retains its normal child/source validation.
            previous = {k: os.environ.get(k) for k in env}
            os.environ.update(env)
            try:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    list(executor.map(lambda group: execute_group(run, group),
                                      configuration_groups(rows)))
                assert all(row["outcome"] == "compared" for row in rows)
                children = [json.loads((ROOT / row["receipt"]).read_text()) for row in rows]
                assert sum(len(c.get("compiled_models", [])) for c in children) == 8
                # Reuse must still execute fresh independent comparison/startup.
                replay = dict(rows[0], id="reuse-" + rows[0]["id"], outcome="not-executed")
                execute_group(run, [replay])
                reused = json.loads((ROOT / replay["receipt"]).read_text())
                assert len(reused["reused_compiled_models"]) == 1
                assert replay["metrics"] == rows[0]["metrics"]
                rows.append(replay)
            finally:
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key)
                    else:
                        os.environ[key] = value
            ledger = run.path / "ledger.json"
            ledger.write_text(json.dumps(rows, indent=2) + "\n")
            run.receipt["metrics"] = dict(compared_jobs=len(rows), fresh_builds=8,
                                           ledger=run.relative(ledger))
        else:
            output = run.command(["python3", "tests/verify.py", "--check", "behavior"],
                                 "complete-behavior", timeout=86400)
            names = [s for s in output.read_text().splitlines() if s.endswith("/receipt.json")]
            assert len(names) == 1
            parent = ROOT / names[0]
            data = json.loads(parent.read_text())
            assert data["outcome"] == "passed" and data["source_sha256"] == run.receipt["source_sha256"]
            ledger = ROOT / data["metrics"]["ledger"]
            rows = json.loads(ledger.read_text())
            assert len(rows) == 673 and all(r["outcome"] == "compared" for r in rows)
            assert data["metrics"]["required_runs"] == data["metrics"]["compared_runs"] == 673
            checked = 0
            for row in rows:
                child = json.loads((ROOT / row["receipt"]).read_text())
                assert child["source_sha256"] == data["source_sha256"]
                hashes, failures = audit_streams(child["commands"])
                assert not failures and hashes == child["raw_stream_sha256"]
                checked += len(hashes)
            duration = run.receipt["commands"][-1]["duration_s"]
            assert duration < 2700, f"behavior exceeded unchanged patrol budget: {duration}"
            run.receipt.update(parent_receipt=names[0], input_sha256={
                names[0]: sha(parent), run.relative(ledger): sha(ledger)})
            run.receipt["metrics"] = dict(complete_behavior_s=duration, compared_jobs=673,
                                           audited_child_streams=checked)
        assert not errors, errors
        retain_samples()
        run.finish("passed-focused-only", elapsed_s=time.monotonic() - started,
                   limitations="Preparation execution, not shared-runtime admission or hardware closure.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError, KeyError) as exc:
        if not stop.is_set():
            retain_samples()
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        stop.set()
        thread.join()


def retention_inventory():
    absent = [name for name in (*MISSING, *INTERRUPTED_PREPARATION)
              if not (ROOT / name).exists()]
    children = list((ROOT / INTERRUPTED_PARENT / "children").glob("*/receipt.json"))
    outcomes = {}
    hashes = {}
    for path in children:
        row = json.loads(path.read_text())
        outcomes[row["outcome"]] = outcomes.get(row["outcome"], 0) + 1
        hashes[str(path.relative_to(ROOT))] = sha(path)
    print(json.dumps(dict(
        inspected_missing_paths=absent, incomplete_parent=str(INTERRUPTED_PARENT),
        parent_receipt_exists=(ROOT / INTERRUPTED_PARENT / "receipt.json").is_file(),
        required_jobs=673, retained_child_receipts=len(children), child_outcomes=outcomes,
        child_receipt_sha256=hashes,
        limitation="Read-only inventory; no absent receipt reconstructed, no writer attributed.")))


def retention_diagnostic():
    run = Run("behavior-dispatch-retention-failure", root="evidence/preparation")
    try:
        run.command(["python3", "--version"], "python-version")
        output = run.command(
            ["python3", "tests/behavior_dispatch_checks.py", "--action", "retention-inventory"],
            "missing-evidence-inventory")
        data = json.loads(output.read_text())
        run.finish(
            "failed", failure="Live preparation capture directory disappeared; "
            "full behavior command interrupted without a parent receipt.",
            observed=data,
            interrupted_capture_path=INTERRUPTED_PREPARATION[-1] +
            "/complete-behavior.stdout.reopen.stdout.txt",
            reported_tool_failure="FileNotFoundError opening the independent capture-reopen "
            "stream, followed by FileNotFoundError writing resource-samples.json.",
            original_raw_traceback_retained=False,
            scope="Retention failure, not a demonstrated numerical failure. "
            "New timing/concurrency results require fresh retained measurement. "
            "Shared runtime must diagnose evidence removal before another full execution.")
        return 1
    except (OSError, RuntimeError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=(
        "fixtures", "probe", "full", "retention", "retention-inventory"), required=True)
    parser.add_argument("--workers", type=int, choices=(4, 8), default=MAXIMUM_BUILDS)
    parser.add_argument("--mode", choices=("aggregate", "split"), default="split")
    args = parser.parse_args()
    if args.action == "fixtures":
        fixtures()
    elif args.action == "retention-inventory":
        retention_inventory()
    elif args.action == "retention":
        raise SystemExit(retention_diagnostic())
    else:
        raise SystemExit(execute(args.action, args.workers, args.mode))
