"""Read-only, project-scoped build-capacity diagnostic with retained receipts."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run


FAILED = ("evidence/l1/l1-behavior-20261029T003431Z-3f57e4ba/children/"
          "verifier-token-fp-fp16-w0-c0-b1-s17-20261029T003603Z-167c8adb")
REPAIR_OF = "evidence/preparation/build-storage-capacity-20261029T032819Z-2466bfed/receipt.json"


def capacity_summary(references, checks, available):
    missing = sorted(set(checks) - set(references))
    raw = sum(r.get("raw_stream_bytes", 0) for r in references.values())
    full = sum(r["allocated_bytes"] for r in references.values())
    return dict(
        available_bytes=available,
        historical_reference_status="incomplete" if missing else "complete",
        missing_historical_checks=missing,
        observed_partial_reference_raw_stream_bytes=raw,
        observed_partial_reference_artifact_bytes=full,
        observed_raw_stream_bytes=None if missing else raw,
        raw_stream_shortfall_bytes=None if missing else max(0, raw - available),
        observed_complete_artifact_bytes=None if missing else full,
        complete_artifact_shortfall_bytes=None if missing else max(0, full - available),
        future_capacity_sufficiency="unknown",
        user_quota_sufficiency="unknown")


def self_check():
    checks = ("behavior", "synthesis")
    row = dict(raw_stream_bytes=5, allocated_bytes=12)
    absent = capacity_summary({}, checks, 100)
    partial = capacity_summary({"synthesis": row}, checks, 100)
    complete = capacity_summary(dict.fromkeys(checks, row), checks, 7)
    for result in (absent, partial):
        assert result["historical_reference_status"] == "incomplete"
        for field in ("observed_raw_stream_bytes", "raw_stream_shortfall_bytes",
                      "observed_complete_artifact_bytes", "complete_artifact_shortfall_bytes"):
            assert result[field] is None, f"missing history must remain unknown: {field}"
    assert absent["missing_historical_checks"] == ["behavior", "synthesis"]
    assert partial["missing_historical_checks"] == ["behavior"]
    assert partial["observed_partial_reference_raw_stream_bytes"] == 5
    assert partial["observed_partial_reference_artifact_bytes"] == 12
    assert complete["historical_reference_status"] == "complete"
    assert complete["observed_raw_stream_bytes"] == 10
    assert complete["raw_stream_shortfall_bytes"] == 3
    assert complete["observed_complete_artifact_bytes"] == 24
    assert complete["complete_artifact_shortfall_bytes"] == 17
    for result in (absent, partial, complete):
        assert result["future_capacity_sufficiency"] == "unknown"
        assert result["user_quota_sufficiency"] == "unknown"
    print(json.dumps(dict(compared_cases=3, scope="capacity reporting fixtures only")))


def inventory():
    totals = Counter()
    builds = defaultdict(Counter)
    campaigns = defaultdict(Counter)
    errors = []
    for base in ("evidence/l1", "evidence/preparation"):
        root = ROOT / base
        if not root.exists():
            continue
        for directory, children, files in os.walk(root, followlinks=False):
            children[:] = sorted(n for n in children
                                 if not (Path(directory) / n).is_symlink())
            for name in sorted(files):
                path = Path(directory) / name
                if path.is_symlink():
                    continue
                try:
                    stat = path.stat()
                except OSError as exc:
                    errors.append(dict(path=str(path.relative_to(ROOT)), errno=exc.errno))
                    continue
                relative = path.relative_to(ROOT)
                parts = relative.parts
                allocated = stat.st_blocks * 512
                totals["files"] += 1
                totals["logical_bytes"] += stat.st_size
                totals["allocated_bytes"] += allocated
                campaign = str(Path(*parts[:3]))
                campaigns[campaign]["allocated_bytes"] += allocated
                campaigns[campaign]["files"] += 1
                category = ("raw_stream" if name.endswith((".stdout.txt", ".stderr.txt")) else
                            "binary" if name == "Vtb" or path.suffix == ".vvp" else
                            "fixture_or_other")
                campaigns[campaign][category + "_bytes"] += allocated
                object_index = next((i for i, p in enumerate(parts)
                                     if p.endswith("-obj")), None)
                if object_index is not None:
                    campaigns[campaign]["compiler_directory_bytes"] += allocated
                    build = str(Path(*parts[:object_index + 1]))
                    row = builds[build]
                    row["allocated_bytes"] += allocated
                    row["logical_bytes"] += stat.st_size
                    row["files"] += 1
                    category = ("binary" if name == "Vtb" else
                                path.suffix if path.suffix else "other")
                    row[category + "_bytes"] += allocated
    fs = os.statvfs(ROOT)
    result = dict(
        scope=["evidence/l1", "evidence/preparation"],
        excludes="symlinks, runtime metadata, source trees and all other projects",
        filesystem=dict(device=ROOT.stat().st_dev, available_bytes=fs.f_bavail * fs.f_frsize,
                        free_bytes=fs.f_bfree * fs.f_frsize,
                        available_inodes=fs.f_favail, free_inodes=fs.f_ffree),
        totals=dict(totals), errors=errors,
        campaigns=dict(sorted(campaigns.items())),
        builds=dict(sorted(builds.items())),
        limitations=[
            "Read-only retained sizes; compiler transient peak is not inferred as measured.",
            "No historical evidence deletion, stress allocation or filesystem-wide scan.",
            "Available filesystem bytes do not establish an unknown user quota.",
        ])
    print(json.dumps(result, indent=2))
    if errors:
        raise RuntimeError("size accounting encountered inaccessible paths")


def assessment(name):
    source = ROOT / name
    source.resolve().relative_to(ROOT / "evidence/preparation")
    data = json.loads(source.read_text())
    from verify import jobs
    checks = ("behavior", "synthesis", "defects", "benchmark", "portability")
    job_counts = {check: len(jobs(check)) for check in checks}
    campaigns = []
    for path, sizes in data["campaigns"].items():
        if not path.startswith("evidence/l1/"):
            continue
        receipt = ROOT / path / "receipt.json"
        if receipt.is_file():
            record = json.loads(receipt.read_text())
            campaigns.append(dict(
                path=path, outcome=record["outcome"], check=record.get("check"),
                metrics=record.get("metrics"), **sizes))
    comparable_builds = []
    for path, sizes in data["builds"].items():
        if "/verifier-token-fp-fp16-w0-c0-b1-s17-" in path:
            comparable_builds.append(dict(
                path=path, **sizes,
                retained_build_to_binary_ratio=(
                    sizes["allocated_bytes"] / sizes["binary_bytes"]
                    if sizes.get("binary_bytes") else None)))
    lower_bounds = {}
    for check in checks:
        rows = [r for r in campaigns if r["check"] == check
                and r["outcome"] == "passed"
                and (r["metrics"] or {}).get("required_runs") == job_counts[check]]
        if rows:
            # Use the latest retained campaign, not an older smaller checkout
            # or a historical directory with fewer surviving artifacts.
            lower_bounds[check] = max(rows, key=lambda r: r["path"])
    available = data["filesystem"]["available_bytes"]
    capacity = capacity_summary(lower_bounds, checks, available)
    failed_receipt = json.loads((ROOT / FAILED / "receipt.json").read_text())
    nonowned = {p: h for p, h in failed_receipt["source_sha256"].items()
                if p.startswith(("rtl/", "design/", "anvil_q2_reference/rtl/"))}
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
               for p, h in nonowned.items()), "accepted source differs from failed attempt"
    failure = (ROOT / FAILED / "compile.stderr.txt").read_text()
    assert "No space left on device" in failure, "missing original compiler-storage diagnostic"
    print(json.dumps(dict(
        inventory=name, unchanged_mandatory_job_counts=job_counts,
        historical_campaigns=campaigns, comparable_fp16_builds=comparable_builds,
        reference_campaigns=lower_bounds,
        capacity=capacity,
        preserved_nonowned_sources=len(nonowned),
        original_failure=FAILED + "/receipt.json",
        limitations=[
            "Historical sizes are measured, future allocation estimates are not executions.",
            "Historical outcomes are recorded labels, not current acceptance or integrity audits.",
            "Raw-stream lower estimate excludes all binaries, fixtures and compiler scratch.",
            "Retained compiler-directory amplification is measured, transient peak is unknown.",
            "Hardware/Quartus storage is additional and is not included.",
            "Missing historical checks make complete estimates and shortfalls unknown (null).",
            "Partial-reference sums describe retained observations only, not required capacity.",
            "Available bytes and historical observations do not establish future capacity or quota.",
        ]), indent=2))


def execute():
    run = Run("build-storage-capacity", root="evidence/preparation")
    run.receipt["repair_of"] = REPAIR_OF
    try:
        run.command(["python3", "--version"], "python-version")
        run.command(["python3", "tests/build_storage_checks.py", "--self-check"],
                    "capacity-reporting-fixtures")
        for tool, args in (
                ("df", ["-P", "-B1", "."]), ("df", ["-Pi", "."]),
                ("findmnt", ["--json", "-T", ".", "-o", "TARGET,SOURCE,FSTYPE,OPTIONS"])):
            if shutil.which(tool):
                label = tool + ("-inodes" if args == ["-Pi", "."] else "")
                run.command([tool, "--version"], label + "-version")
                run.command([tool, *args], label)
        limitations = []
        if shutil.which("quota"):
            run.command(["quota", "--version"], "quota-version", expected_codes=(0, 1))
            run.command(["quota", "-s"], "quota", expected_codes=(0, 1))
            limitations.append("An empty/unsupported quota query does not prove capacity.")
        else:
            limitations.append("quota executable unavailable; applicable user quota unknown.")
        output = run.command(["python3", "tests/build_storage_checks.py", "--inventory"],
                             "generated-artifact-accounting")
        data = json.loads(output.read_text())
        analysis = run.command(
            ["python3", "tests/build_storage_checks.py", "--assessment", run.relative(output)],
            "capacity-assessment")
        for tool in ("verilator", "g++", "make"):
            run.command([tool, "--version"], tool + "-version")
        run.receipt["input_sha256"] = {
            run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / FAILED / "receipt.json", ROOT / FAILED / "compile.stderr.txt",
                      ROOT / FAILED / "compile.stdout.txt", output)}
        measured = json.loads(analysis.read_text())
        run.finish("passed-focused-only", metrics=data["filesystem"],
                   accounting=run.relative(output), assessment=run.relative(analysis),
                   capacity=measured["capacity"],
                   limitations=limitations,
                   scope="Storage diagnostic only, not functional or engineering acceptance.")
        return 0
    except (OSError, AssertionError, RuntimeError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--assessment")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
    elif args.inventory:
        inventory()
    elif args.assessment:
        assessment(args.assessment)
    else:
        raise SystemExit(execute())
