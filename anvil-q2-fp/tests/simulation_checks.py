"""Bounded backend-repair diagnostics, not substitutes for admitted L1 checks."""

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run


CASES = {
    "token": [
        ("icarus", ["tests/token_checks.py", "--singleton", "--format", "fp16",
                    "--weights", "1", "--cache", "1", "--banks", "2",
                    "--simulator", "iverilog"]),
        ("compiled", ["tests/token_checks.py", "--singleton", "--format", "fp16",
                      "--weights", "1", "--cache", "1", "--banks", "2"]),
        ("cached", ["tests/token_checks.py", "--singleton", "--format", "fp16",
                    "--weights", "1", "--cache", "1", "--banks", "2", "--seed", "43"]),
        ("parent", ["tests/token_checks.py", "--product", "parent", "--format", "fp16",
                    "--weights", "1", "--cache", "1", "--banks", "2"]),
    ],
    "attention": [("attention", ["tests/attention_checks.py", "--reduced"])],
    "lifecycle": [
        (case, ["tests/top_lifecycle_checks.py", "--case", case, "--format", "fp16",
                "--weights", "1", "--cache", "1", "--banks", "2"])
        for case in ("cancel-held", "cancel-response", "activation-overflow")
    ],
    "row": [("row", ["tests/projection_row_checks.py", "--projection", "6",
                     "--format", "fp16", "--weights", "1", "--banks", "2", "--seed", "89"])],
    "attention-cache": [("attention", ["tests/attention_checks.py", "--seed", "17"])],
    "dispatch": [
        (f"seed{seed}", ["tests/token_checks.py", "--singleton", "--format", "fp16",
                       "--weights", "1", "--cache", "1", "--banks", "2", "--seed", str(seed)])
        for seed in (17, 43)
    ],
    "contract": [],
    "defects": [(case, ["tests/defect_checks.py", "--case", case])
                for case in ("accumulation", "awq-nibbles", "int8-exponent", "held-request")],
}


def execute(case):
    run = Run(f"verifier-simulator-repair-{case}")
    records = {}
    try:
        run.receipt["repair_of"] = [
            {"receipt": "evidence/preparation/verifier-simulator-launcher-import-failure-"
                        "20261028T144035Z-109e4ab3/receipt.json",
             "observed_failure": "diagnostic launcher local import path; explicit script directory"},
            {"runtime_attempt": 17, "check": "five-domain-l1-benchmark",
             "observed_failure": "cancelled by elapsed-time patrol, not a numerical rejection"},
            {"receipt": "evidence/preparation/verifier-token-fp-fp16-w1-c1-b2-s17-"
                        "20261028T143440Z-ce175630/receipt.json",
             "observed_failure": "Verilator BLKLOOPINIT; raise tool unroll allowance, no RTL edits"},
        ]
        if case == "contract":
            from verify import jobs, source_contract
            source_contract()
            counts, bindings = {}, {}
            for check, directory in (
                ("behavior", "l1-behavior-20261028T051835Z-43cf3a13"),
                ("synthesis", "l1-synthesis-20261028T113500Z-0489c3f1"),
                ("defects", "l1-defects-20261028T125611Z-67beace7"),
                ("benchmark", "l1-benchmark-20261028T125622Z-e87b665f"),
            ):
                path = ROOT / "evidence/l1" / directory / "check-manifest.json"
                raw = path.read_bytes()
                before = json.loads(raw)["jobs"]
                actual = [(label, ["python3", *arguments], requirement)
                          for label, arguments, requirement in jobs(check)]
                assert actual == [(r["id"], r["argv"], r["requirement"]) for r in before], (
                    f"{check}: original coverage denominator/commands changed")
                counts[check] = len(actual)
                bindings[run.relative(path)] = hashlib.sha256(raw).hexdigest()
            files = sorted((ROOT / "tests").glob("*.py"))
            for path in files:
                ast.parse(path.read_text(), filename=run.relative(path))
            baseline_path = ROOT / (
                "evidence/preparation/verifier-token-fp-fp16-w1-c1-b2-s17-"
                "20261028T143440Z-ce175630/receipt.json")
            raw = baseline_path.read_bytes()
            baseline = json.loads(raw)
            for path, expected in baseline["source_sha256"].items():
                if path.startswith(("rtl/", "design/", "anvil_q2_reference/rtl/")):
                    assert run.receipt["source_sha256"][path] == expected, "nonowned source changed"
            bindings[run.relative(baseline_path)] = hashlib.sha256(raw).hexdigest()
            run.finish("passed-focused-only", input_sha256=bindings,
                       metrics={"unchanged_job_counts": counts, "python_sources_parsed": len(files)},
                       limitations="Source/denominator audit, not functional or hardware acceptance.")
            return 0
        if case == "dispatch":
            from verify import execute_job, source_contract
            source_contract()
            planned = [dict(id=name, argv=["python3", *arguments], outcome="not-executed")
                       for name, arguments in CASES[case]]
            with ThreadPoolExecutor(max_workers=2) as executor:
                list(executor.map(lambda record: execute_job(run, record), planned))
            models = [json.loads((ROOT / row["receipt"]).read_text()) for row in planned]
            assert all(row["outcome"] == "compared" for row in planned)
            assert sum(len(m.get("compiled_models", [])) for m in models) == 1
            assert sum(len(m.get("reused_compiled_models", [])) for m in models) == 1
            run.finish("passed-focused-only", metrics={"parallel_jobs": planned},
                       limitations="Two concurrent same-configuration seeds, not full check execution.")
            return 0
        for label, arguments in CASES[case]:
            output = run.command(
                ["python3", *arguments], label, expected_codes=(0, 1),
                environment={"ANVIL_EVIDENCE_ROOT": run.relative(run.path / "children"),
                             "ANVIL_SIM_CACHE": run.relative(run.path / "compiled-models")})
            names = [line for line in output.read_text().splitlines() if line.endswith("/receipt.json")]
            assert len(names) == 1, f"{label}: missing child receipt"
            path = ROOT / names[0]
            path.resolve().relative_to(run.path.resolve())
            child = json.loads(path.read_text())
            records[label] = {"receipt": names[0], "metrics": child.get("metrics")}
            assert child["source_sha256"] == run.receipt["source_sha256"], "sources changed"
            assert run.receipt["commands"][-1]["exit_code"] == 0, f"{label}: execution failed"
            assert child["outcome"] == "passed-focused-only", f"{label}: comparisons failed"
        if case == "token":
            a, b = [ROOT / records[name]["receipt"] for name in ("icarus", "compiled")]
            streams = [next(c["checked_stream"] for c in json.loads(p.read_text())["commands"]
                            if "checked_stream" in c) for p in (a, b)]
            assert streams[0]["protocol_sha256"] == streams[1]["protocol_sha256"], (
                "Icarus/Verilator public transaction/cycle traces differ")
            assert streams[0]["protocol_records"] == streams[1]["protocol_records"] > 0
            cached = json.loads((ROOT / records["cached"]["receipt"]).read_text())
            assert len(cached.get("reused_compiled_models", [])) == 1, "cache reuse not exercised"
            records["equivalence"] = {"identical_public_trace_records": streams[0]["protocol_records"],
                                      "cached_seed": 43}
        if case == "lifecycle":
            final = json.loads((ROOT / records["activation-overflow"]["receipt"]).read_text())
            assert len(final.get("reused_compiled_models", [])) == 1, "scenario cache reuse absent"
        if case == "attention-cache":
            baseline = ROOT / (
                "evidence/preparation/verifier-attention-drift-native-heads-s17-bounded-"
                "20261028T144755Z-a5c5152f/receipt.json")
            original = json.loads(baseline.read_text())
            current = json.loads((ROOT / records["attention"]["receipt"]).read_text())
            assert original["outcome"] == current["outcome"] == "passed-focused-only"
            for name, expected in original["source_sha256"].items():
                if name.startswith(("rtl/", "design/", "anvil_q2_reference/rtl/")):
                    assert current["source_sha256"][name] == expected, "design source changed"
            compared = {}
            for name in ("drift.json", "mode0-stimulus.jsonl", "mode1-stimulus.jsonl",
                         "mode0-observations.jsonl", "mode1-observations.jsonl"):
                old = baseline.parent / name
                new = (ROOT / records["attention"]["receipt"]).parent / name
                previous = hashlib.sha256(old.read_bytes()).hexdigest()
                assert hashlib.sha256(new.read_bytes()).hexdigest() == previous, (
                    f"memoization changed full-head result/stimulus/cycles: {name}")
                compared[name] = previous
            records["equivalence"] = {
                "baseline_receipt": run.relative(baseline), "identical_artifact_sha256": compared}
        run.finish("passed-focused-only", metrics=records,
                   limitations="Bounded backend repair diagnostics; original mandatory checks still required.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}", completed=records)
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, required=True)
    raise SystemExit(execute(parser.parse_args().case))
