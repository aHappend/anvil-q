"""Fresh declared-source-only reproduction with real numerical RTL and synthesis."""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run, audit_streams


DECLARED = ("rtl/*.sv", "design/*", "tests/*.py", "anvil_q2_reference/rtl/*.sv")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute():
    run = Run("verifier-clean-reproduction")
    try:
        version = run.command(["python3", "--version"], "python-version")
        absent = run.relative(run.path / "deliberately-absent-stream.txt")
        assert not (ROOT / absent).exists()
        hashes, errors = audit_streams([{"stdout": run.relative(version), "stderr": absent}])
        assert set(hashes) == {run.relative(version)} and set(errors) == {absent}, (
            "raw-stream audit failed to identify a synthetic absent-path fixture")
        bundle = run.path / "bundle"
        bundle.mkdir()
        sources = {}
        for pattern in DECLARED:
            matches = [p for p in sorted(ROOT.glob(pattern)) if p.is_file()]
            assert matches, f"unmatched declared source pattern: {pattern}"
            for source in matches:
                relative = source.relative_to(ROOT)
                destination = bundle / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                assert digest(source) == digest(destination), f"copy mismatch: {relative}"
                sources[str(relative)] = digest(destination)
        assert not (bundle / ".vulcan").exists() and not (bundle / "evidence").exists()
        assert not any(p.suffix == ".vvp" for p in bundle.rglob("*") if p.is_file())
        help_output = run.command(
            ["python3", run.relative(bundle / "tests/verify.py"), "--help"], "copied-dispatcher-help")
        for check in ("behavior", "synthesis", "defects", "benchmark", "portability"):
            assert check in help_output.read_text(), f"copied dispatcher lost {check}"
        inspection = run.command([
            "python3", "-c",
            "import sys,json; "
            f"sys.path.insert(0,{run.relative(bundle / 'tests')!r}); "
            "import verify; "
            "assert verify.source_contract(); "
            "print(json.dumps({k:len(verify.jobs(k)) for k in "
            "('behavior','synthesis','defects','benchmark','portability')}))",
        ], "copied-dispatcher-contract")
        planned_runs = json.loads(inspection.read_text())
        assert all(number > 0 for number in planned_runs.values()), "empty declared checks"
        children = {}
        for label, arguments in (
            ("numerical", ["tests/numerical_checks.py", "--case", "lane", "--format", "bf16"]),
            ("synthesis", ["tests/synthesis_checks.py", "--top", "anvil_q2_fp_dot_lane"]),
        ):
            output = run.command(
                ["python3", run.relative(bundle / arguments[0]), *arguments[1:]], label)
            receipts = [line.strip() for line in output.read_text().splitlines()
                        if line.strip().endswith("/receipt.json")]
            assert len(receipts) == 1, f"{label}: absent or ambiguous child receipt"
            receipt_path = bundle / receipts[0]
            receipt_path.resolve().relative_to(bundle.resolve())
            receipt = json.loads(receipt_path.read_text())
            assert receipt["outcome"] == "passed-focused-only", f"{label}: child did not pass"
            assert receipt["commands"], f"{label}: no execution"
            assert all(c["exit_code"] == 0 and not c["timed_out"] for c in receipt["commands"])
            if label == "numerical":
                assert receipt["metrics"]["scalar_results_compared"] == 32768
            else:
                assert receipt["metrics"]["state_bits"] > 0 and receipt["metrics"]["cells"] > 0
            assert receipt["source_sha256"] == sources, f"{label}: copied source binding mismatch"
            children[label] = {"receipt": run.relative(receipt_path), "metrics": receipt["metrics"]}
        for relative, expected in sources.items():
            assert digest(bundle / relative) == expected, f"reproduction changed source: {relative}"
        run.finish("passed-focused-only", copied_source_sha256=sources,
                   metrics={"fresh_output_directory": run.relative(bundle), "children": children,
                            "dispatcher_planned_runs_not_executed": planned_runs},
                   limitations="Representative portability, not whole-matrix or native hardware acceptance.")
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    raise SystemExit(execute())
