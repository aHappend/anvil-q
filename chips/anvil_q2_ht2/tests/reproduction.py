"""Fresh-source reproduction, with no imported build products or runtime metadata."""

import hashlib
import json
import shutil
import time


def execute(run):
    from verify import ROOT, hashes
    workspace = run.path / "clean-project"
    workspace.mkdir()
    bindings = hashes()
    for relative, expected in bindings.items():
        source = ROOT / relative
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if hashlib.sha256(destination.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"clean-copy hash mismatch: {relative}")
    run.receipt["clean_reproduction"] = {
        "source_manifest": bindings,
        "copied_files": len(bindings),
        "workspace": run.relative(workspace),
        "inputs": "declared RTL, reference RTL, design Markdown and verification sources only",
    }
    run.save()
    remaining = run.budget_s - (time.monotonic() - run.started) - 30
    if remaining <= 0:
        raise RuntimeError("no execution budget remains for fresh-directory reproduction")
    _, stdout, _ = run.command(
        ["python3", "tests/verify.py", "reproduce", "--reproduction-child",
         *(["--preparation"] if run.receipt["kind"] == "advisory-preparation" else [])],
        "clean-project-reproduction", cwd=workspace,
        environment={"PYTHONPATH": "", "PYTHONSAFEPATH": "1",
                     "ANVIL_L1_BUDGET_SECONDS": str(remaining)})
    try:
        outcome = json.loads(stdout.splitlines()[-1])
        receipt_path = workspace / outcome["receipt"]
        receipt_path.resolve().relative_to(workspace.resolve())
        receipt = json.loads(receipt_path.read_text())
    except (ValueError, KeyError, IndexError, OSError) as exc:
        raise RuntimeError("clean child produced no readable execution receipt") from exc
    if (outcome["exit_code"] != 0 or receipt["exit_code"] != 0 or
            not receipt["source_hashes_unchanged"] or
            receipt["source_hashes"] != bindings):
        raise RuntimeError("clean child did not pass with the exact copied sources")
    run.receipt["clean_reproduction"]["receipt"] = run.relative(receipt_path)
    run.receipt["clean_reproduction"]["comparisons"] = receipt["reproduction_comparisons"]
    run.save()


def child(run):
    from verify import ROOT, numerics, top_behavior, sources
    from synthesis import execute
    numerics(run, range(5), "iverilog", True)
    top_behavior(run, "verilator")
    execute(run, ROOT, sources(), compact=True)
    # The fallback's exact expanded files must also preserve numerical behavior.
    lowered = run.path / "lowered-sources"
    if lowered.exists():
        run.design_root = lowered
        numerics(run, range(5), "iverilog", True, vector_prefix="lowered-numerics")
        top_behavior(run, "verilator", stem="lowered-compact-model",
                     result_key="lowered_top_smoke")
    run.receipt["reproduction_comparisons"] = {
        "numerics": run.receipt["numerics"],
        "top": run.receipt["top_smoke"],
        "lowered_top": run.receipt.get("lowered_top_smoke"),
        "synthesis": run.receipt["synthesis"],
        "scope": "independent compact checks; not official model, physical fit or benchmark proof",
    }
    run.save()
