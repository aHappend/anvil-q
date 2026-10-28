#!/usr/bin/env python3
"""Remeasure project-local capacity against retained predictor projections."""

import argparse
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import load_json, require, sha
from verify import Evidence, ROOT


def measurement(required, free):
    require(type(required) is int and required > 0 and
            type(free) is int and free >= 0, "invalid capacity quantities")
    reserve = max(1024 ** 3, free // 10)
    return {
        "projected_required_bytes": required,
        "available_bytes": free,
        "reserve_bytes": reserve,
        "projected_shortfall_bytes": max(0, required + reserve - free),
        "projection_fits": required + reserve <= free,
    }


def measurement_selftest():
    gib = 1024 ** 3
    for required, free, reserve, shortfall, fits in (
        (gib, 0, gib, 2 * gib, False),
        (gib, 2 * gib - 1, gib, 1, False),
        (gib, 2 * gib, gib, 0, True),
        (gib, 2 * gib + 1, gib, 0, True),
        (9 * gib, 10 * gib, gib, 0, True),
        (18 * gib + 1, 20 * gib, 2 * gib, 1, False),
    ):
        row = measurement(required, free)
        require((row["reserve_bytes"], row["projected_shortfall_bytes"],
                 row["projection_fits"]) == (reserve, shortfall, fits),
                "capacity boundary known-answer comparison failed")
    for required, free in ((True, gib), (0, gib), (gib, -1), (gib, True)):
        try:
            measurement(required, free)
        except ValueError:
            continue
        raise ValueError("invalid capacity quantity was accepted")


def retained_projection(relative):
    require(not relative.is_absolute() and ".." not in relative.parts and
            (ROOT / relative).resolve().is_relative_to(ROOT),
            "capacity receipt must be project-relative")
    record = load_json(ROOT / relative)
    require(record["status"] == "failed" and any(
        row["name"] == "projected_complete_reference_capacity" and not row["passed"]
        for row in record["assertions"]), "missing retained capacity failure")
    for name in ("tests/reference_predictor.py", "tests/reference_storage.py",
                 "tests/teacher_reference.py", "tests/fp64_reference.py",
                 "tests/awq_prepare.py", "tests/data/model_manifest.json",
                 "tests/data/benchmark_manifest.json"):
        require(record["source_sha256"][name] == sha(ROOT / name),
                "retained projection input changed: " + name)
    reports = [name for name in record["outputs"]
               if name.endswith("/qualified-prediction/qualification.json")]
    require(len(reports) == 1, "retained predictor report missing or ambiguous")
    relative_report = Path(reports[0])
    require(not relative_report.is_absolute() and ".." not in relative_report.parts and
            (ROOT / relative_report).resolve().is_relative_to(ROOT),
            "retained report escapes project")
    require(sha(ROOT / relative_report) == record["outputs"][reports[0]],
            "retained projection report hash differs")
    report = load_json(ROOT / relative_report)
    require(report["purpose"] == "axis-prediction-storage-qualification" and
            report["acceptance_evidence"] is False and
            report["capacity"] == record["capacity"],
            "retained projection report identity differs")
    require(len(record["records"]) == 5 and all(
        row["exit_code"] == 0 and row["timed_out"] is False
        for row in record["records"]), "retained predictor execution incomplete")
    for codec, row in report["capacity"].items():
        components = [row[name] for name in (
            "projected_payload_bytes", "index_budget_bytes", "peak_raw_staging_bytes")]
        require(all(type(value) is int and value > 0 for value in components) and
                sum(components) == row["projected_required_bytes"],
                "retained projection accounting differs: " + codec)
    return report


def worker(relative):
    report = retained_projection(relative)
    usage = shutil.disk_usage(ROOT)
    print(json.dumps({
        "purpose": "project-local-reference-capacity-remeasurement",
        "acceptance_evidence": False,
        "storage_root": ".",
        "filesystem_total_bytes": usage.total,
        "filesystem_used_bytes": usage.used,
        "capacity": {
            codec: {**measurement(row["projected_required_bytes"], usage.free),
                    "limitation": row["limitation"]}
            for codec, row in report["capacity"].items()},
        "storage_provisioned_by_probe": False,
        "full_reference_launched": False,
        "complete_collector_qualified": False,
        "full_model_results_present": (ROOT / "tests/data/full_model_results.json").is_file(),
        "scope": "Fresh free-space observation; retained three-position projections only. "
                 "No deletion, allocation reservation, mount, installation, recompression, "
                 "inference, hardware execution or runtime-state change.",
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-receipt", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker(args.projection_receipt)
        return 0
    ev = Evidence("reference-capacity")
    ok = False
    try:
        measurement_selftest()
        ev.assertion("capacity_boundary_known_answers", True,
                     comparisons=6, rejected_invalid_quantities=4)
        retained_projection(args.projection_receipt)
        ev.receipt["repair_of"] = {
            "path": str(args.projection_receipt),
            "sha256": sha(ROOT / args.projection_receipt)}
        ev.receipt["tool_versions"] = {"python": sys.version}
        ok = ev.run("capacity-remeasurement", [
            sys.executable, "tests/reference_capacity.py", "--worker",
            "--projection-receipt", str(args.projection_receipt)], timeout=3600)
        ev.assertion("capacity_remeasurement_completed", ok)
        if ok:
            report = load_json(ev.path / "capacity-remeasurement.stdout")
            ev.receipt["capacity"] = report["capacity"]
            ok = any(row["projection_fits"] for row in report["capacity"].values())
            ev.assertion("projected_complete_reference_capacity", ok,
                         full_launch_attempted=False, full_suite_capacity_proven=False,
                         complete_collector_qualified=False)
    except (ValueError, KeyError, OSError) as error:
        ok = False
        ev.assertion("capacity_exception", False, error=repr(error))
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path)
            for path in ev.path.iterdir() if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
