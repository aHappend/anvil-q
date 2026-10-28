"""Offline fail-closed delivery-gate sensitivity, not physical acceptance."""

import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, Run


def runtime_receipt_sensitivity(folder):
    """Runtime metadata cannot substitute for public inputs or fresh execution."""
    import hardware_checks
    import prerequisites

    original_is_file = Path.is_file
    original_read_text = Path.read_text
    phantom = {
        "status": "passed", "wns_setup_ns": 0, "wns_hold_ns": 0,
        "unconstrained_functional_endpoints": 0, "unapproved_timing_exceptions": 0,
        "deterministic_across_runs": True, "runs_executed": 3,
    }

    def is_file(path):
        if ".vulcan" in path.parts:
            return True
        return original_is_file(path)

    def read_text(path, *args, **kwargs):
        if ".vulcan" in path.parts:
            return json.dumps(phantom)
        return original_read_text(path, *args, **kwargs)

    marker = "offline fixture: unidentified physical board"
    fake = SimpleNamespace(path=folder, hashes={"rtl/fixture.sv": "0" * 64},
                           versions=lambda tools: None)
    with (patch.object(Path, "is_file", is_file),
          patch.object(Path, "read_text", read_text),
          patch.object(prerequisites, "configuration", return_value={}),
          patch.object(prerequisites, "validate_assets", return_value=[]),
          patch.object(prerequisites.shutil, "which", return_value="offline-fixture"),
          patch.object(prerequisites, "board_inputs",
                       side_effect=hardware_checks.PhysicalPrerequisiteError([marker])),
          patch.object(hardware_checks, "board_inputs",
                       side_effect=hardware_checks.PhysicalPrerequisiteError([marker]))):
        try:
            prerequisites.prerequisites(fake)
        except RuntimeError as exc:
            if not str(exc).startswith("unmet prerequisites:"):
                raise
        else:
            raise AssertionError("unidentified board accepted")
        report = json.loads((folder / "prerequisites.json").read_text())
        rows = [row for row in report["prerequisites"]
                if row["requirement"] == "identified-physical-board"]
        if len(rows) != 1 or rows[0]["met"]:
            raise AssertionError("runtime receipt existence bypassed board identification")
        for check in (hardware_checks.quartus_sta, hardware_checks.board_hil):
            try:
                check(fake)
            except hardware_checks.PhysicalPrerequisiteError as exc:
                if exc.unmet != (marker,):
                    raise
            else:
                raise AssertionError("runtime receipt bypassed physical execution: " + check.__name__)
    for name in ("quartus-results.json", "hil-results.json"):
        if (folder / name).exists():
            raise AssertionError("unexecuted physical check published " + name)
    return {"phantom_runtime_receipts_rejected": True,
            "scope": "mocked metadata only; no runtime files read or written, no physical execution"}


def delivery_gate_sensitivity(run):
    import benchmark_checks
    import hardware_checks
    import prerequisites

    folder = run.path / "delivery-gate-fixtures"
    folder.mkdir()
    runtime = folder / "runtime-receipt-fixtures"
    runtime.mkdir()
    runtime_result = runtime_receipt_sensitivity(runtime)
    fake = SimpleNamespace(path=folder, hashes={})
    with patch.object(hardware_checks, "board_inputs", return_value={"board": {}, "device": hardware_checks.DEVICE}):
        try:
            hardware_checks.board_hil(fake)
        except hardware_checks.PhysicalPrerequisiteError as exc:
            if not any("physical execution driver" in item for item in exc.unmet):
                raise AssertionError("HIL rejection does not identify missing execution") from exc
        else:
            raise AssertionError("HIL reported success without any hardware execution")
    if (folder / "hil-results.json").exists():
        raise AssertionError("unexecuted HIL published result rows")

    with (patch.object(prerequisites, "configuration", return_value={}),
          patch.object(prerequisites, "validate_assets", return_value=[]),
          patch.object(prerequisites.shutil, "which", return_value="offline-fixture"),
          patch.object(prerequisites, "board_inputs", return_value={})):
        try:
            prerequisites.prerequisites(fake)
        except RuntimeError as exc:
            if not str(exc).startswith("unmet prerequisites:"):
                raise
        else:
            raise AssertionError("missing generation baselines accepted")
    report = json.loads((folder / "prerequisites.json").read_text())
    for generation in ("Q1", "Q2"):
        for prefix in ("generation_baseline:", "generation_adapter:"):
            rows = [row for row in report["prerequisites"]
                    if row["requirement"] == prefix + generation]
            if len(rows) != 1 or rows[0]["met"]:
                raise AssertionError("missing baseline/adapter not rejected: " + prefix + generation)

    class StopBeforeWorkload(Exception):
        pass

    with (patch.object(benchmark_checks, "tensor_speedup"),
          patch.object(benchmark_checks, "validate_assets", return_value=[]),
          patch.object(benchmark_checks, "official_weight_slice", side_effect=StopBeforeWorkload)):
        try:
            benchmark_checks.benchmark(fake)
        except StopBeforeWorkload:
            pass
        else:
            raise AssertionError("offline benchmark fixture unexpectedly executed workload")
    status = json.loads((folder / "cross-generation-prerequisites.json").read_text())
    if [row["generation"] for row in status["generations"]] != ["Q1", "Q2"]:
        raise AssertionError("benchmark omits a required generation")
    if len(status["unmet"]) != 4:
        raise AssertionError("benchmark accepts missing provenance or execution adapters")
    return {"unexecuted_hil_rejected": True, "required_generations": ["Q1", "Q2"],
            "runtime_receipt_checker": runtime_result,
            "scope": "offline negative checker fixtures; no FPGA tools or hardware executed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--folder")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    if args.worker:
        folder = ROOT / args.folder
        folder.relative_to(ROOT / "evidence/preparation")
        print(json.dumps(delivery_gate_sensitivity(SimpleNamespace(path=folder))))
        return
    run = Run("evidence/preparation/independent-delivery-gates",
              "offline delivery gate fail-closed sensitivity", repair_of=args.repair_of)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("python3", "--version")])
        text, _ = run.tool(["python3", "tests/delivery_gate_checks.py", "--worker",
                            "--folder", run.rel(run.path)])
        result = json.loads(text)
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)


if __name__ == "__main__":
    main()
