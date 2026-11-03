#!/usr/bin/env python3
"""Bounded synthetic copy lifecycle regressions; no RTL or production execution."""

import argparse
from contextlib import ExitStack
import errno
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify


CASES = ("insufficient-bytes", "insufficient-inodes", "mid-copy-enospc",
         "success", "failed-child", "missing-log", "changed-copy")
CHILD = """import json, pathlib, sys
root = pathlib.Path('.')
p = root / 'evidence/preparation/synthetic-smoke-17'
p.mkdir(parents=True)
(p/'run.stdout').write_text('Synthetic comparison results; no RTL execution\\n')
(p/'run.stderr').write_text('')
(p/'generated-result.json').write_text('{"synthetic":true}\\n')
names = ['synthesis_anvil_q1_fp_top', 'leaf_independent_numerical'] + [
    f'minimum-mode{m}-seed17_independent_architecture_numerical' for m in (0,1,2)]
failed = pathlib.Path('tests/data/fail-child').exists()
receipt = p/'receipt.json'
receipt.write_text(json.dumps({
    'status':'failed' if failed else 'passed',
    'scope':'SYNTHETIC LIFECYCLE ONLY; NO RTL OR SYNTHESIS EXECUTION',
    'records':[{'stdout':str(p/'run.stdout'),'stderr':str(p/'run.stderr')}],
    'assertions':[{'name':n,'passed':not failed} for n in names]}))
print(json.dumps({'status':'failed' if failed else 'passed','receipt':str(receipt)}))
sys.exit(1 if failed else 0)
"""


def worker(case):
    root = verify.ROOT
    ev = verify.Evidence("portable-lifecycle-" + case)
    ev.receipt["scope"] = "Synthetic lifecycle only; not portable RTL acceptance"
    project = ev.path / "fixture-project"
    contents = {
        "rtl/fixture.sv": "module fixture; endmodule\n",
        "design/fixture.md": "Synthetic input.\n",
        "fpga/fixture.sdc": "# Synthetic constraint.\n",
        "anvil_q1_reference/rtl/fixture.sv": "module parent; endmodule\n",
        "tests/verify.py": CHILD,
        "tests/data/first.bin": bytes(range(256)) * 16,
        "tests/data/second.bin": b"independent input bytes\n" * 256,
    }
    if case == "failed-child":
        contents["tests/data/fail-child"] = b"fail\n"
    for name, value in contents.items():
        target = project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value.encode() if isinstance(value, str) else value)
    original_hashes = {name: verify.digest(project / name) for name in contents}
    real_copy, real_vfs, real_sources = shutil.copy2, os.statvfs, verify.sources
    injected = None
    caught = None
    child = None
    good = False

    def capacity(path):
        actual = real_vfs(path)
        return SimpleNamespace(
            f_frsize=actual.f_frsize, f_bsize=actual.f_bsize,
            f_bavail=0 if case == "insufficient-bytes" else 10**9,
            f_favail=0 if case == "insufficient-inodes" else 10**9)

    def copy(source, target, *args, **kwargs):
        nonlocal injected
        if case == "mid-copy-enospc" and Path(source).name == "second.bin":
            with Path(source).open("rb") as stream:
                Path(target).write_bytes(stream.read(37))
            injected = OSError(errno.ENOSPC, "injected mid-copy ENOSPC", str(target))
            raise injected
        return real_copy(source, target, *args, **kwargs)

    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(verify, "ROOT", project))
            stack.enter_context(patch.object(
                verify, "sources", side_effect=lambda root=None: real_sources(root or project)))
            stack.enter_context(patch.object(verify.os, "statvfs", side_effect=capacity))
            stack.enter_context(patch.object(verify.shutil, "copy2", side_effect=copy))
            child = verify.Evidence("portable-fixture-" + case)
            try:
                result = verify.portable_check(child)
            except OSError as error:
                caught = error
                traceback.print_exc()
                child.assertion("expected_original_copy_exception", False,
                                diagnostics=getattr(error, "verification_diagnostics", []))
                result = False
            destination = child.path / "clean-project"
            measured = child.receipt["portable_capacity"]
            checks = {
                "all_declared_inputs_planned": set(measured["declared_files"]) == set(contents),
                "capacity_recorded_before_copy": measured["snapshot_at"] <=
                    child.receipt.get("portable_copy", {}).get("started_at", verify.now()),
            }
            if case.startswith("insufficient-"):
                child.finish("failed")
                checks.update(rejected=not result, no_copy_allocation=not destination.exists(),
                              no_child_execution=not child.receipt["records"])
            elif case == "mid-copy-enospc":
                child.finish("failed")
                partial = destination / "tests/data/second.bin"
                diagnostic = child.receipt["portable_copy"]["diagnostic"]
                checks.update(
                    original_exception_identity=caught is injected and injected is not None,
                    original_errno_traceback=diagnostic["errno"] == errno.ENOSPC and
                        "copy" in diagnostic["traceback"],
                    partial_copy_retained=partial.read_bytes() == contents[
                        "tests/data/second.bin"][:37],
                    complete_prefix_retained=all((destination / name).is_file()
                        for name in child.receipt["portable_copy"]["copied_inputs"]),
                    no_child_execution=not child.receipt["records"])
            else:
                manifest = child.receipt["portable_copy"]["copied_inputs"]
                checks["independent_files_and_exact_hashes"] = (
                    set(manifest) == set(contents) and all(
                        verify.digest(destination / name) == original_hashes[name] and
                        (destination / name).stat().st_nlink == 1 and
                        (destination / name).stat().st_ino != (project / name).stat().st_ino
                        for name in contents))
                evidence_files = {str(p.relative_to(destination)): verify.digest(p)
                    for p in (destination / "evidence").rglob("*") if p.is_file()}
                if case == "missing-log":
                    missing = destination / "evidence/preparation/synthetic-smoke-17/run.stdout"
                    # Preserve original bytes while making the recorded dependency absent.
                    missing.rename(missing.with_suffix(".retained"))
                dependencies = verify.audit_evidence(child) if result else False
                passed = result and dependencies
                child.finish("passed" if passed else "failed")
                if case == "changed-copy":
                    (destination / "tests/data/first.bin").write_bytes(b"changed")
                    try:
                        verify.portable_dispose_inputs(child)
                    except ValueError as error:
                        child.assertion("expected_changed_copy_rejection", False,
                                        diagnostic=str(error))
                        child.finish("failed")
                        checks["changed_copy_rejected"] = "changed before disposal" in str(error)
                    checks["all_inputs_retained"] = all(
                        (destination / name).is_file() for name in contents)
                elif passed:
                    verify.portable_dispose_inputs(child)
                    checks.update(
                        success_committed=child.receipt["status"] == "passed",
                        only_copied_inputs_removed=all(not (destination / name).exists()
                                                      for name in contents),
                        all_results_receipts_logs_preserved=all(
                            verify.digest(destination / name) == value
                            for name, value in evidence_files.items()),
                        dependencies_survive_disposal=verify.audit_evidence(child),
                        disposed_manifest_complete=set(child.receipt["portable_copy"][
                            "disposed_inputs"]) == set(contents))
                    child.finish("passed")
                else:
                    try:
                        verify.portable_dispose_inputs(child)
                    except ValueError as error:
                        checks["failed_disposal_guard"] = (
                            case == "missing-log" and "before successful" in str(error))
                    checks.update(rejected=not passed,
                                  all_failed_inputs_retained=all(
                                      (destination / name).is_file() for name in contents))
                    if case == "missing-log":
                        checks["missing_log_rejected"] = not dependencies
                        # The negative audit is retained; restore the raw log for publication.
                        missing.with_suffix(".retained").rename(missing)
                        child.finish("failed")
            checks["original_inputs_untouched"] = all(
                verify.digest(project / name) == value for name, value in original_hashes.items())
            good = all(checks.values())
        reference = str((child.path / "receipt.json").relative_to(root))
        ev.receipt["children"] = [reference]
        ev.receipt["child_project_roots"] = {reference: str(project.relative_to(root))}
        for name, passed in checks.items():
            ev.assertion(case + "_" + name, passed)
    except Exception as error:
        traceback.print_exc()
        ev.assertion("lifecycle_regression_exception", False, diagnostic=repr(error))
    ev.finish("passed" if good else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(root))}), flush=True)
    return 0 if good else 1


def check(ev):
    ev.receipt["scope"] = "Synthetic lifecycle sensitivity and read-only capacity planning"
    original = verify.ROOT / "evidence/preparation/verifier-portable-p56b2at4/receipt.json"
    ev.receipt["repair_of"] = {
        "path": str(original.relative_to(verify.ROOT)), "sha256": verify.digest(original)}
    for name in ("kx2g0kie", "9yh8y5rf"):
        previous = verify.ROOT / (
            "evidence/preparation/verifier-portable-copy-lifecycle-" + name + "/receipt.json")
        if previous.is_file():
            ev.receipt.setdefault("diagnostic_repairs", []).append({
                "path": str(previous.relative_to(verify.ROOT)), "sha256": verify.digest(previous)})
    good = ev.run("python-version", [sys.executable, "--version"])
    for case in CASES:
        label = "lifecycle-" + case
        executed = ev.run(label, [
            sys.executable, "tests/portable_copy_checks.py", "--case", case], timeout=3600)
        output = (ev.path / (label + ".stdout")).read_text().splitlines()
        child = json.loads(output[-1]) if output else {}
        good = ev.assertion(label, executed and child.get("status") == "passed") and good
        if child.get("receipt"):
            ev.receipt.setdefault("children", []).append(child["receipt"])
    executed = ev.run("interpreter-clean-copy", [
        sys.executable, "tests/interpreter_consistency.py", "--case", "clean-copy"],
        timeout=3600)
    output = (ev.path / "interpreter-clean-copy.stdout").read_text().splitlines()
    child = json.loads(output[-1]) if output else {}
    good = ev.assertion("existing_interpreter_clean_copy_fixture",
                        executed and child.get("status") == "passed" and
                        child.get("diagnostic_expectations_met") is True) and good
    if child.get("receipt"):
        ev.receipt.setdefault("children", []).append(child["receipt"])
    # No destination or large payload is allocated by this assessment.
    verify.portable_capacity(ev, verify.sources())
    return good and verify.audit_evidence(ev)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES)
    args = parser.parse_args()
    if args.case:
        return worker(args.case)
    ev = verify.Evidence("portable-copy-lifecycle")
    good = False
    try:
        good = check(ev)
    except Exception as error:
        traceback.print_exc()
        ev.assertion("portable_lifecycle_exception", False, diagnostic=repr(error))
    ev.finish("passed" if good else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(verify.ROOT))}))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
