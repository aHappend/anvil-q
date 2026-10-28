#!/usr/bin/env python3
"""Synthetic launcher regression; no RTL build, inference or acceptance claim."""

import argparse
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify
from benchmark import require, sha


CASES = ("available", "failed-import", "benchmark-fixtures", "clean-copy")


def clean_copy_fixture(ev):
    """Exercise the real copy/launcher, not the prohibited RTL clean-smoke build."""
    project = ev.path / "synthetic-project"
    script = project / "tests/verify.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "import json,os,pathlib,sys\n"
        "assert sys.executable == os.environ['ANVIL_TEST_INTERPRETER']\n"
        "assert sys.argv[1:] == ['--probe','clean-smoke']\n"
        "assert pathlib.Path.cwd() == pathlib.Path(__file__).resolve().parents[1]\n"
        "names = ['synthesis_anvil_q1_fp_top','leaf_independent_numerical'] + "
        "[f'minimum-mode{m}-seed17_independent_architecture_numerical' for m in (0,1,2)]\n"
        "p = pathlib.Path('evidence/synthetic-child/receipt.json')\n"
        "p.parent.mkdir(parents=True)\n"
        "p.write_text(json.dumps({'status':'passed','scope':'SYNTHETIC LAUNCH FIXTURE; "
        "NO RTL OR SYNTHESIS EXECUTION','assertions':[{'name':n,'passed':True} for n in names]}))\n"
        "print(json.dumps({'status':'passed','receipt':str(p),'executable':sys.executable}))\n")
    selected = lambda root=None: [((root or project) / "tests/verify.py")]
    with patch.object(verify, "ROOT", project), patch.object(verify, "sources", selected):
        child = verify.Evidence("synthetic-clean-launch")
        passed = verify.portable_check(child)
        child.finish("passed" if passed else "failed")
    ev.receipt.setdefault("children", []).append(
        str((child.path / "receipt.json").relative_to(verify.ROOT)))
    record = child.receipt["records"][0]
    return ev.assertion(
        "actual_clean_copy_launcher_uses_parent_interpreter",
        passed and record["argv"] == [
            sys.executable, "tests/verify.py", "--probe", "clean-smoke"],
        scope="Synthetic child only; actual portable behavior/synthesis check remains mandatory",
        fixture_source_sha256=sha(script), rtl_builds=0)


def worker(case):
    ev = verify.Evidence("interpreter-" + case)
    good = False
    try:
        ev.receipt["tool_versions"] = {"python": sys.version}
        shim = ev.path / "path-shim"
        shim.mkdir()
        sentinel = shim / "python3"
        sentinel.write_text("#!/bin/sh\nprintf 'WRONG_PATH_PYTHON\\n' >&2\nexit 91\n")
        sentinel.chmod(0o755)
        os.environ["PATH"] = str(shim) + os.pathsep + os.environ.get("PATH", "")
        os.environ["ANVIL_TEST_INTERPRETER"] = sys.executable
        if case == "failed-import":
            shadow = ev.path / "import-shadow"
            shadow.mkdir()
            (shadow / "numpy.py").write_text(
                "raise ModuleNotFoundError('injected NumPy import failure')\n")
            os.environ["PYTHONPATH"] = str(shadow)
        if case in ("available", "failed-import"):
            result = verify.prerequisites(ev)
            records = {row["label"]: row for row in ev.receipt["records"]}
            required = {
                "version-python3": [sys.executable, "--version"],
                "reference-numpy-import": [
                    sys.executable, "-c", "import numpy; print(numpy.__version__)"],
            }
            require(all(records[name]["argv"] == argv for name, argv in required.items()),
                    "Python version/import child changed interpreters")
            require(records["reference-dependency-discovery"]["argv"][0] == sys.executable,
                    "dependency discovery changed interpreter")
            require(records["version-python3"]["exit_code"] == 0 and
                    records["reference-dependency-discovery"]["exit_code"] == 0,
                    "version or discovery child failed")
            imported = records["reference-numpy-import"]["exit_code"] == 0
            require(imported is (case == "available"), "unexpected real NumPy import result")
            if not imported:
                require("injected NumPy import failure" in
                        (verify.ROOT / records["reference-numpy-import"]["stderr"]).read_text(),
                        "wrong NumPy failure diagnostic")
            require(not result and any(
                row["name"] == "full_model_inputs_and_execution" and not row["passed"] and
                "tests/data/full_model_results.json" in row.get("missing", [])
                for row in ev.receipt["assertions"]), "missing results did not fail closed")
            expected_failures = {"full_model_inputs_and_execution"}
            if case == "failed-import":
                expected_failures.add("reference_numpy_import")
            require({row["name"] for row in ev.receipt["assertions"] if not row["passed"]}
                    == expected_failures, "unexpected prerequisite failure")
            require(all(row["exit_code"] == 0 and not row["timed_out"]
                        for label, row in records.items()
                        if label != "reference-numpy-import"),
                    "unexpected version/discovery child failure")
            ev.assertion("real_children_consistent_missing_results_still_fail", True,
                         numpy_imported=imported, divergent_path_python_exit=91)
            # The prerequisite receipt intentionally remains failed.
            good = True
        elif case == "benchmark-fixtures":
            from benchmark_fixtures import check
            good = check(verify.ROOT, ev)
        else:
            good = clean_copy_fixture(ev)
        require(all("WRONG_PATH_PYTHON" not in (verify.ROOT / row["stderr"]).read_text()
                    for row in ev.receipt["records"]), "PATH sentinel executed")
    except (ValueError, KeyError, OSError, ImportError) as error:
        good = False
        ev.assertion("interpreter_regression_exception", False, diagnostic=repr(error))
    finally:
        passed = good and all(row["passed"] for row in ev.receipt["assertions"])
        ev.receipt["scope"] = "Bounded interpreter diagnostic only; not product acceptance"
        ev.receipt["outputs"] = {
            str(path.relative_to(verify.ROOT)): sha(path)
            for path in ev.path.rglob("*") if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if passed else "failed")
        verify.report_failures(ev)
        print(json.dumps({"receipt": str((ev.path / "receipt.json").relative_to(verify.ROOT)),
                          "diagnostic_expectations_met": good, "status": ev.receipt["status"]}))
    return 0 if good else 1


def check(root, ev):
    ev.receipt["scope"] = (
        "Actual Python child launch paths under divergent PATH; synthetic clean-copy child. "
        "No collection, reference inference, RTL build or synthesis.")
    ev.receipt["tool_versions"] = {"python": sys.version}
    previous = root / "evidence/preparation/verifier-prerequisites-mt_603j_/receipt.json"
    ev.receipt["repair_of"] = {"path": str(previous.relative_to(root)), "sha256": sha(previous)}
    failed = root / "evidence/preparation/verifier-interpreter-consistency-k95o_6ol/receipt.json"
    if failed.is_file():
        ev.receipt["diagnostic_repair_of"] = {
            "path": str(failed.relative_to(root)), "sha256": sha(failed)}
    good = True
    for case in CASES:
        label = "interpreter-" + case
        completed = ev.run(label, [
            sys.executable, "tests/interpreter_consistency.py", "--case", case], timeout=3600)
        stdout = (ev.path / (label + ".stdout")).read_text().splitlines()
        child = json.loads(stdout[-1]) if stdout else {}
        good = ev.assertion(
            label, completed and child.get("diagnostic_expectations_met") is True and
            child.get("status") == ("failed" if case in ("available", "failed-import")
                                   else "passed"),
            child_receipt=child.get("receipt"), expected_prerequisite_failure=case in (
                "available", "failed-import")) and good
        if child.get("receipt"):
            ev.receipt.setdefault("children", []).append(child["receipt"])
    return good


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=CASES)
    raise SystemExit(worker(parser.parse_args().case))
