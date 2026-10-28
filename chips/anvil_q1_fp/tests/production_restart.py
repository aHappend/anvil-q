#!/usr/bin/env python3
"""Preflight the unchanged full workload without consuming broken ancestry.

This performs input/build validation only, not RTL inference or benchmark
acceptance. The printed collection command requires independent admission.
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import artifact_path, load_json, require
from benchmark_inputs import write_json
from production_sim import MODES, checked, compile_simulator, descriptor, identity
from verify import Evidence, ROOT


COLLECTION_ARGV = [
    "python3", "tests/production_sim.py", "--case-start", "0",
    "--case-count", "50", "--modes", *MODES, "--timeout", "86400",
]


def schedule(ev, suite):
    jobs = []
    for case_number, (domain, case) in enumerate(
            (domain, case) for domain, group in suite["domains"].items()
            for case in group["cases"]):
        token_inputs = {}
        for workload, field in (("teacher", "teacher_tokens"),
                                ("greedy", "prompt_tokens")):
            path = checked(ev, case[field])
            tokens = load_json(path)
            require(isinstance(tokens, list) and 0 < len(tokens) <= 32768 and
                    all(type(token) is int and 0 <= token < 151936 for token in tokens),
                    "invalid full-workload token input")
            require(workload != "greedy" or len(tokens) + 128 <= 32768,
                    "full greedy context exceeds production sequence capacity")
            token_inputs[workload] = {
                "tokens": descriptor(path), "input_positions": len(tokens)}
        for mode in MODES:
            for workload in ("teacher", "greedy"):
                for repeat in range(2):
                    jobs.append({
                        "case_index": case_number, "case": domain + "/" + case["id"],
                        "mode": mode, "workload": workload, "repeat": repeat,
                        "origin": "reset", "resume": None,
                        "max_new_tokens": 128 if workload == "greedy" else 0,
                        **token_inputs[workload],
                    })
    require(len(jobs) == 600 and
            len({(job["case"], job["mode"], job["workload"], job["repeat"])
                 for job in jobs}) == 600,
            "incomplete or duplicate full-workload recovery schedule")
    return jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-receipt", type=Path)
    parser.add_argument("--repair-of", type=Path)
    args = parser.parse_args()
    ev = Evidence("production-restart")
    passed = False
    try:
        from teacher_reference import validate_inputs

        if args.repair_of:
            previous = artifact_path(ROOT, str(args.repair_of))
            require(load_json(previous)["status"] == "failed",
                    "repair receipt did not fail")
            ev.receipt["repair_of"] = descriptor(previous)
        model, suite, _, _ = validate_inputs(ev)
        jobs = schedule(ev, suite)
        executable = compile_simulator(ev, args.build_receipt)
        write_json(ev.path / "reset-origin-preflight.json", {
            "schema": 1, "acceptance_evidence": False, "complete_benchmark": False,
            "collection_executed": False, "historical_ancestry_consumed": False,
            "build_sources": identity(), "executable": descriptor(executable),
            "model_manifest": descriptor(ROOT / "tests/data/model_manifest.json"),
            "benchmark_manifest": descriptor(ROOT / "tests/data/benchmark_manifest.json"),
            "jobs": jobs, "collection_argv": COLLECTION_ARGV,
            "limitations": "Preflight only. Fresh collection requires independent "
            "admission; old checkpoints remain unusable. Runtime accounting repair, "
            "full result assembly and task evaluation, all admitted checks, Quartus "
            "timing/resources and physical HIL remain separate obligations.",
        })
        ev.assertion("full_workload_reset_origin_preflight", True,
                     scheduled_jobs=len(jobs), cases=50, modes=3,
                     independent_repeats=2, workloads=2, executed_jobs=0,
                     historical_ancestry_consumed=False, complete_benchmark=False)
        passed = True
    except (ValueError, OSError, KeyError, ImportError) as error:
        ev.assertion("reset_origin_preflight_failure", False, diagnostic=str(error))
    finally:
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                          "complete_benchmark": False}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
