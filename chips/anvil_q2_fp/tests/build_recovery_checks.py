"""Focused generated-build recovery; advisory evidence, not admitted L1 acceptance."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run, audit_streams
from simulation import (BUILD_RESERVE, STORAGE_HEADROOM, build_model, build_policy,
                        cleanup_intermediates, generated_artifacts)


FAILED = Path(
    "evidence/l1/l1-behavior-20261030T012949Z-ccab19e9/children/"
    "verifier-token-fp-bf16-w1-c1-b1-s17-20261030T013252Z-cfce9851/receipt.json")
PRIOR_PROBE = Path("evidence/preparation/generated-build-recovery-20261030T013802Z-a2600d67")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def publish(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def cleanup_failed(run):
    path = ROOT / FAILED
    old = json.loads(path.read_text())
    assert old["outcome"] == "failed"
    commands = old["commands"]
    assert all(c.get("ended_at") and c.get("exit_code") is not None
               and not c["timed_out"] for c in commands)
    compile_command = next(c for c in commands if c["stdout"].endswith("/compile.stdout.txt"))
    assert compile_command["exit_code"] == 2
    stderr = (ROOT / compile_command["stderr"]).read_text()
    assert "expected" in stderr and "at end of input" in stderr
    assert "make" in stderr and "exited with 2" in stderr
    objects = path.parent / "compile-obj"
    stdout = (ROOT / compile_command["stdout"]).read_text()
    assert f"Entering directory '{objects}'" in stdout, "missing build attribution"
    # The supplied shared-runtime diagnosis establishes attempt-0993 settlement.
    # The Verilator make error also follows make's wait for its compiler jobs.
    run.receipt["cleanup_settlement_basis"] = dict(
        runtime_attempt=993, supplied_process_scope_settled=True,
        command_exit_code=2, command_ended_at=compile_command["ended_at"],
        compile_stdout=compile_command["stdout"], compile_stderr=compile_command["stderr"])
    hashes, errors = audit_streams(commands)
    assert not errors and hashes == old["raw_stream_sha256"], "failed raw evidence changed"
    if not objects.exists():
        run.receipt["failed_build_cleanup"] = dict(
            removed=[], original_artifacts_available=False,
            limitation="Original compile-obj disappeared after the first recovery probe; "
                       "writer unknown. No deletion by this probe; do not recreate evidence.",
            earlier_preservation_manifest=str(
                PRIOR_PROBE / "failed-build-preserved.json"))
        return
    candidates = [p for p in objects.iterdir() if p.suffix in (".o", ".a", ".gch")]
    assert (len(candidates), sum(p.stat().st_size for p in candidates)) in (
        (7, 142598264), (0, 0)), "unexpected failed-build cleanup inventory"
    keep = {str(p.relative_to(ROOT)): sha(p) for p in path.parent.rglob("*")
            if p.is_file() and p not in candidates}
    publish(run.path / "failed-build-preserved.json", keep)
    old_run = SimpleNamespace(path=path.parent, receipt=old,
                              relative=lambda p: str(p.relative_to(ROOT)))
    before = build_policy()
    removed = cleanup_intermediates(old_run, objects)
    assert all(sha(ROOT / name) == expected for name, expected in keep.items()), (
        "cleanup changed retained failed source, log, receipt or executable")
    try:
        generated_artifacts(objects)
    except AssertionError as exc:
        assert "incomplete generated artifacts" in str(exc)
        incomplete = str(exc)
    else:
        raise AssertionError("original truncated/empty generated sources were accepted")
    run.receipt["failed_build_cleanup"] = dict(
        removed=removed, preserved_files=len(keep),
        preserved_sha256_manifest=run.relative(run.path / "failed-build-preserved.json"),
        original_artifact_diagnostic=incomplete, before=before, after=build_policy())


def fixtures(directory):
    from storage_hygiene_checks import fixtures as cleanup_fixtures
    cleanup_dir = directory / "cleanup-fixtures-1"
    cleanup_dir.mkdir()
    cleanup_fixtures(cleanup_dir)
    policy_rows = []
    for available, cpus, expected in (
            (STORAGE_HEADROOM + BUILD_RESERVE - 1, 16, 1),
            (STORAGE_HEADROOM + BUILD_RESERVE, 16, 1),
            (STORAGE_HEADROOM + 2 * BUILD_RESERVE, 16, 2),
            (STORAGE_HEADROOM + 10 * BUILD_RESERVE, 16, 4),
            (STORAGE_HEADROOM + 10 * BUILD_RESERVE, 2, 1)):
        row = build_policy(available, cpus)
        assert row["maximum_concurrent_jobs"] == expected
        policy_rows.append(row)
    unsettled_dir = directory / "unsettled-fixture-obj"
    unsettled_dir.mkdir()
    guarded = unsettled_dir / "keep.o"
    guarded.write_bytes(b"not settled")
    unsettled = SimpleNamespace(path=directory, receipt={"commands": [{"timed_out": True}]},
                                relative=lambda p: str(p.relative_to(ROOT)))
    try:
        cleanup_intermediates(unsettled, unsettled_dir)
    except AssertionError as exc:
        assert "settled" in str(exc)
    else:
        raise AssertionError("cleanup admitted an unsettled tool")
    assert guarded.read_bytes() == b"not settled"

    objects = directory / "incomplete-fixture-obj"
    objects.mkdir()
    bench = directory / "fixture.sv"
    bench.write_text("module tb;\n#0; reset_sample<=1;\nendmodule\n")
    index = directory / "must-not-publish.json"
    generated = objects / "Vtb.cpp"
    manifest = objects / "Vtb__verFiles.dat"
    diagnostics = []
    for case, data, declared in (("empty", b"", 0),
                                  ("truncated", b"void eval() { identifier", 100),
                                  ("partial-line", b"void eval() { identifier", 23)):
        generated.write_bytes(data)
        manifest.write_text(
            f'T {declared} 0 0 0 0 0 "{generated.relative_to(ROOT)}"\n')
        try:
            generated_artifacts(objects)
        except AssertionError as exc:
            assert "incomplete generated artifacts" in str(exc)
            diagnostics.append(dict(case=case, diagnostic=str(exc)))
        else:
            raise AssertionError(f"incomplete {case} fixture accepted")

    fake = SimpleNamespace(path=directory, receipt={"commands": []},
                           relative=lambda p: str(p.relative_to(ROOT)))
    def command(argv, label, **kwargs):
        if label == "fixture-generate":
            # Deliberately incomplete generator output, not a simulator pass.
            target = directory / "fixture-obj"
            target.mkdir()
            source = target / "Vtb.cpp"
            source.write_bytes(b"void eval() { truncated")
            (target / "Vtb__verFiles.dat").write_text(
                f'T 100 0 0 0 0 0 "{source.relative_to(ROOT)}"\n')
    fake.command = command
    # Synthetic admission removes host capacity from this negative unit fixture.
    from contextlib import nullcontext
    with patch("simulation.build_slot", lambda run: nullcontext()):
        try:
            build_model(fake, bench, [], {}, "fixture", {"options": []}, index)
        except AssertionError as exc:
            assert "incomplete generated artifacts" in str(exc)
        else:
            raise AssertionError("incomplete generator published a cache entry")
    assert not index.exists() and fake.receipt["incomplete_builds"][0]["cache_published"] is False
    publish(directory / "build-fixture-results.json", dict(
        policy_rows=policy_rows, rejected_generated_artifacts=diagnostics,
        cache_not_published=True, unsettled_cleanup_rejected=True,
        cleanup_exclusion_results=str((cleanup_dir / "fixture-results.json").relative_to(ROOT))))
    print("BUILD_STORAGE_FIXTURES_COMPARED", len(policy_rows) + len(diagnostics) + 2)


def execute():
    run = Run("generated-build-recovery", root="evidence/preparation")
    run.receipt["repair_of"] = [str(FAILED), *[
        str(p.relative_to(ROOT)) for p in sorted(
            (ROOT / "evidence/preparation").glob("generated-build-recovery-*/receipt.json"))
        if p.parent != run.path]]
    children = []
    reserve = run.path / "receipt-reserve.bin"
    try:
        with reserve.open("xb") as stream:
            os.posix_fallocate(stream.fileno(), 0, 4 * 1024 * 1024)
        run.receipt["input_sha256"] = {str(FAILED): sha(ROOT / FAILED)}
        if (ROOT / PRIOR_PROBE).is_dir():
            run.receipt["prior_probe_sha256"] = {
                str(p.relative_to(ROOT)): sha(p) for p in (ROOT / PRIOR_PROBE).rglob("*")
                if p.is_file()}
            run.receipt["prior_probe_limitation"] = (
                "ENOSPC interrupted receipt/capture writes; partial records remain unchanged. "
                "A child explicitly denied insufficient storage; no functional pass claimed.")
        for name, expected in json.loads((ROOT / FAILED).read_text())["source_sha256"].items():
            if name.startswith(("rtl/", "design/", "anvil_q2_reference/rtl/")):
                assert sha(ROOT / name) == expected, f"nonowned sources changed: {name}"
        run.command(["python3", "--version"], "python-version")
        cleanup_failed(run)
        run.command(["python3", "tests/build_recovery_checks.py", "--fixtures",
                     run.relative(run.path)], "fixtures")
        from verify import execute_job
        from concurrent.futures import ThreadPoolExecutor
        # Both invocations are the exact failed seed and configuration.
        jobs = [dict(id=label, argv=[
            "python3", "tests/token_checks.py", "--format", "bf16", "--weights", "1",
            "--cache", "1", "--banks", "1", "--seed", "17"], outcome="not-executed")
                for label in ("exact-seed17", "reuse-exact-seed17")]
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda row: execute_job(run, row), jobs))
        children = [json.loads((ROOT / row["receipt"]).read_text()) for row in jobs]
        assert all(row["outcome"] == "compared" for row in jobs)
        built = [c for c in children if c.get("compiled_models")]
        reused = [c for c in children if c.get("reused_compiled_models")]
        assert len(built) == len(reused) == 1, "one build and one cache reuse required"
        assert children[0]["metrics"] == children[1]["metrics"], "cached numerical/protocol metrics differ"
        streams = [next(c["checked_stream"] for c in child["commands"]
                        if "checked_stream" in c) for child in children]
        assert streams[0] == streams[1] and streams[0]["protocol_records"] > 0
        previous = json.loads((ROOT / FAILED).read_text())
        failed_parameters = next(c["argv"] for c in previous["commands"]
                                 if c["stdout"].endswith("/compile.stdout.txt"))
        parameters = built[0]["compiled_models"][0]["identity"]["parameters"]
        assert all(f"-G{k}={v}" in failed_parameters for k, v in parameters.items())
        assert children[0]["metrics"]["seed"] == children[1]["metrics"]["seed"] == 17
        assert children[0]["metrics"]["logits_compared"] == 9
        assert built[0]["disposable_build_intermediates"], "successful compiler cleanup not exercised"
        models = built[0]["compiled_models"] + reused[0]["reused_compiled_models"]
        for model in models:
            assert sha(ROOT / model["binary"]) == model["binary_sha256"]
            assert all(sha(ROOT / p) == h for p, h in model["artifact_sha256"].items())
        for row in built[0]["disposable_build_intermediates"]:
            assert not (ROOT / row["path"]).exists()
        reserve.unlink()
        run.finish("passed-focused-only", metrics=dict(
            jobs=jobs, identical_checked_stream=streams[0],
            successful_cleanup_files=len(built[0]["disposable_build_intermediates"]),
            successful_cleanup_bytes=sum(r["bytes"] for r in built[0]["disposable_build_intermediates"])),
            limitations="Exact failed-case repair and cache/cleanup fixtures only; "
                        "all six mandatory checks and native hardware gates remain required.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
        if reserve.exists():
            reserve.unlink()
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}",
                   children_compared=len(children))
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures")
    args = parser.parse_args()
    if args.fixtures:
        directory = ROOT / args.fixtures
        directory.resolve().relative_to(ROOT / "evidence/preparation")
        fixtures(directory)
    else:
        raise SystemExit(execute())