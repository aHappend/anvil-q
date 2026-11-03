"""Portable L1 aggregate; incomplete coverage and numerical failures are nonzero.

Every required shard is accounted for. Missing/stale executable shards run rather
than being treated as receipt-only prerequisites. Native timing/HIL and the final
product report remain owned by the shared runtime.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import (CHECK_SECONDS, ROOT, execute, failure_details, hashes,
                       nested_outcomes, relative, timestamp)
from retention import find_result, inventory
from run_synthesis import JOBS, JOB_BUDGETS
from run_reproduction import REPRODUCTION_BUDGET


SEEDS = (17, 89, 2026)
OBLIGATIONS = {
    "transcendental": "IEEE exp, sin/cos, divide/sqrt; approximation and latency matrix",
    "attention_restart": "KV response fault drains; legal and immediate-invalid next commands complete",
    "attention": "online FP64 attention, formats, masks, tiles, long context and stalls",
    "attention_timing": "frozen no-stall attention edges with observed resident tile supply",
    "packed_cache": "FP32 store conversion, packed writes/readback and subsequent attention",
    "packed_top": "quantized-cache decode/publication and fault invalidation at public top",
    "compatibility": "integrated inference, CSR/loader/descriptor/batch/reset/error matrix",
    "integrated_geometry": "functional smallest/nonpower/H64, native formats and GQA",
    "parameters": "legal extrema/default elaboration and explicit illegal diagnostics",
    "mutations": "five compiling/executing disposable defects rejected by public assertions",
    "stream_checkpoint": "uninterrupted/restored RTL agreement with accepted memory debt and independent logits",
    "benchmarks": "hash-pinned official model/datasets; scored logits, PPL and legacy fixtures",
    "performance": "matched HT2/HT3 actual cycles, transition reduction >60%, bytes and TPM",
    "synthesis": "default hierarchy/256 lanes, compact mapping, new modules and zero latches",
    "reproduction": "fresh declared-source compact behavior and Yosys synthesis",
}

TOOLS = {"python3": ["python3", "--version"], "iverilog": ["iverilog", "-V"],
         "verilator": ["verilator", "--version"], "yosys": ["yosys", "-V"]}
SETTLEMENT_RESERVE = 30
SUITE_BUDGETS = {"attention": 750, "attention_timing": 180,
                 "parameters": 450, "attention_restart": 60,
                 "transcendental": 180, "packed_cache": 180, "compatibility": 420,
                 "packed_top": 480,
                 "integrated_geometry": 1500,
                 "mutations": 420, "stream_checkpoint": 360,
                 "benchmarks": 1800, "performance": 900}
MINIMUM_ALLOCATIONS = {
    "reproduction": REPRODUCTION_BUDGET, "integrated_geometry": 360,
    "parameters": 240, "mutations": 240, "stream_checkpoint": 300,
    "benchmarks": 360, "performance": 300, "compatibility": 300,
    "packed_cache": 120, "attention": 180, "attention_timing": 90,
    "packed_top": 360,
}


def dependencies(script):
    sources = [relative(p) for pattern in ("rtl/*.sv", "design/*.md")
               for p in sorted(ROOT.glob(pattern))]
    shared = ["tests/execution.py"]
    owned = {
        "tests/run_unit.py": ["tests/reference.py", "tests/primitive_tb.sv",
                              "tests/quantizer_tb.sv"],
        "tests/run_epilogue.py": ["tests/reference.py", "tests/epilogue_tb.sv"],
        "tests/run_attention.py": ["tests/reference.py", "tests/attention_tb.sv"],
        "tests/run_attention_timing.py": ["tests/attention_timing_tb.sv", "tests/retention.py"],
        "tests/run_attention_restart.py": ["tests/attention_restart_tb.sv"],
        "tests/run_transcendental.py": ["tests/reference.py", "tests/transcendental_tb.sv"],
        "tests/run_packed_cache.py": ["tests/reference.py", "tests/packed_cache_tb.sv"],
        "tests/run_packed_top.py": ["tests/reference.py", "tests/inference_tb.sv",
                                   "tests/run_compatibility.py", "tests/retention.py"],
        "tests/run_compatibility.py": ["tests/reference.py", "tests/inference_tb.sv",
                                      "tests/retention.py"],
        "tests/run_integrated_geometry.py": ["tests/reference.py", "tests/inference_tb.sv",
                                            "tests/run_compatibility.py",
                                            "tests/run_performance.py", "tests/retention.py"],
        "tests/run_performance.py": ["tests/reference.py", "tests/inference_tb.sv",
                                     "tests/performance_monitor.sv",
                                     "tests/run_compatibility.py",
                                     *[relative(p) for p in sorted(
                                         ROOT.glob("anvil_q1_ht2_reference/rtl/*.sv"))]],
        "tests/run_benchmarks.py": ["tests/official_inputs.json", "tests/official_reference.py",
                                   "tests/acquire_public.py", "tests/reference.py",
                                   "tests/run_compatibility.py", "tests/official_image.py",
                                   "tests/official_stream.py", "tests/official_stream.cpp",
                                   "tests/official_scoring.py", "tests/retention.py"],
        "tests/run_stream_checkpoint.py": ["tests/official_stream.py",
                                          "tests/official_stream.cpp", "tests/reference.py",
                                          "tests/run_compatibility.py", "tests/retention.py"],
        "tests/run_parameters.py": ["tests/top_csr_tb.sv", "tests/parameter_leaf_tb.sv",
                                    *[relative(p) for p in sorted(
                                        ROOT.glob("anvil_q1_ht2_reference/rtl/*.sv"))]],
        "tests/run_synthesis.py": ["tests/yosys_frontend.py", "tests/retention.py"],
        "tests/run_mutations.py": ["tests/run_mutation_case.py", "tests/run_packed_cache.py",
                                  "tests/packed_cache_tb.sv", "tests/run_epilogue.py",
                                  "tests/epilogue_tb.sv", "tests/run_attention.py",
                                  "tests/attention_tb.sv", "tests/reference.py",
                                  "tests/retention.py"],
    }
    if script not in owned:
        return list(hashes())
    if script in ("tests/run_compatibility.py", "tests/run_integrated_geometry.py",
                  "tests/run_performance.py"):
        owned[script] = [*owned[script], "tests/retention.py"]
    return sources + shared + [script] + owned[script]


def retained_epilogue():
    directory = ROOT / "evidence/preparation/ht3-epilogue-failure-ledger-20261102T190500-a1"
    receipt_path = directory / "receipt.json"
    if not receipt_path.is_file() or not (directory / "result.json").is_file():
        return None
    receipt = json.loads(receipt_path.read_text())
    required = [relative(p) for pat in ("rtl/*.sv", "design/*.md")
                for p in sorted(ROOT.glob(pat))]
    required += ["tests/run_epilogue.py", "tests/reference.py", "tests/epilogue_tb.sv"]
    current = hashes()
    if any(receipt.get("source_sha256", {}).get(p) != current[p] for p in required):
        return None
    result = json.loads((directory / "result.json").read_text())
    if (receipt.get("exit") == 0) != (result.get("status") == "passed"):
        raise AssertionError("retained epilogue checker receipt/result disagree")
    if result.get("commands") != 104 or result.get("vectors") != 168:
        raise AssertionError("retained epilogue has incomplete observation counts")
    for name in ("observations.txt", "vectors.txt", "simulation.stdout.txt",
                 "simulation.stderr.txt", "simulation.receipt.json"):
        if not (directory / name).is_file():
            return None
    simulation = json.loads((directory / "simulation.receipt.json").read_text())
    if simulation.get("exit") != 0:
        return None
    return dict(id="epilogue-seed17", status=result["status"],
                receipt=relative(receipt_path), reused=True, commands=result["commands"],
                vectors=result["vectors"], failures=result["failures"],
                retained_artifact_sha256={
                    relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in directory.iterdir()
                    if p.is_file() and p.suffix in (".json", ".txt")})


def child(identifier, argv, output, budget=None, versions=None, reserve=0, minimum=0):
    if versions is not None:
        cached = find_result(["python3", *argv], dependencies(argv[0]), versions,
                             allow_failure=identifier.startswith("epilogue-seed"))
        if cached is not None:
            result = cached.pop("result")
            return dict(id=identifier, status=("incomplete" if result.get("coverage_limits")
                                              else result["status"]), reused=True,
                        coverage_limits=result.get("coverage_limits", []),
                        failures=result.get("failures", []), **cached)
    directory = output / f"{identifier}-{uuid.uuid4().hex[:12]}"
    deadline = os.environ["HT3_CHECK_DEADLINE"]
    allocation = max(0, float(deadline) - time.time() - reserve)
    if budget is not None:
        allocation = min(allocation, budget)
    if allocation < minimum:
        return dict(id=identifier, status="not_started",
                    failure_kind="execution_budget_unstarted", available_s=allocation,
                    minimum_s=minimum,
                    error="insufficient useful cold-work allocation; no subprocess launched")
    os.environ["HT3_CHECK_DEADLINE"] = str(time.time() + allocation)
    try:
        execute(["python3", *argv, "--output", relative(directory)],
                output, identifier, ["python3", "--version"])
        result_path = directory / "result.json"
        if not result_path.is_file():
            raise AssertionError("zero driver exit without result.json")
        result = json.loads(result_path.read_text())
        if result.get("status") != "passed":
            raise AssertionError("zero driver exit without passing observation summary")
        if result.get("coverage_limits"):
            return dict(id=identifier, status="incomplete", result=relative(result_path),
                        coverage_limits=result["coverage_limits"],
                        receipt=relative(output / f"{identifier}.receipt.json"))
        return dict(id=identifier, status="passed", result=relative(result_path),
                    receipt=relative(output / f"{identifier}.receipt.json"))
    except (RuntimeError, AssertionError) as exc:
        receipt_path = output / f"{identifier}.receipt.json"
        nested = {}
        if receipt_path.is_file():
            record = json.loads(receipt_path.read_text())
            nested = {key: record[key] for key in
                      ("nested_timed_out", "budget_exhausted", "timed_out_receipts",
                       "unstarted_receipts") if key in record}
        return dict(id=identifier, status="failed", error=str(exc),
                    **failure_details(exc), **nested,
                    receipt=relative(output / f"{identifier}.receipt.json"),
                    result=relative(directory / "result.json"))
    finally:
        os.environ["HT3_CHECK_DEADLINE"] = deadline


def reconcile_coverage(rows):
    """Resolve cross-suite labels only from current, checked public observations."""
    current = hashes()

    def checked_result(row, script):
        if (row is None or row["status"] not in ("passed", "incomplete")
                or not row.get("receipt")):
            return None
        result_path = row.get("result_path", row.get("result"))
        if not result_path:
            return None
        receipt = json.loads((ROOT/row["receipt"]).read_text())
        if (receipt.get("timed_out") or receipt.get("exit") != 0
                or any(receipt.get("source_sha256", {}).get(path) != current[path]
                       for path in dependencies(script))):
            return None
        result = json.loads((ROOT/result_path).read_text())
        return result if result.get("status") == "passed" else None

    packed = next((r for r in rows if r["id"] == "packed_cache"), None)
    packed_top = next((r for r in rows if r["id"] == "packed_top"), None)
    packed_result = checked_result(packed, "tests/run_packed_cache.py")
    top_result = checked_result(packed_top, "tests/run_packed_top.py")
    if packed_result is not None and top_result is not None:
        expected = {(fmt, probe) for fmt in (2, 3) for probe in
                    ("success", "read_error", "write_error", "new_sequence", "reset")}
        observed = top_result.get("runs", [])
        if (len(observed) == 10 and {(r["format"], r["probe"]) for r in observed} == expected
                and all(r["status"] == "passed" for r in observed)
                and packed_result.get("faults") == dict(
                    dma_errors=4, abort_drains=4, reset_debts=4,
                    poisoned_rows=4, flush_invalidations=4)):
            label = "integrated quantized-cache prefix-publication matrix"
            if label in packed.get("coverage_limits", []):
                packed["reported_coverage_limits"] = list(packed["coverage_limits"])
                packed["coverage_limits"] = [s for s in packed["coverage_limits"] if s != label]
                packed["resolved_coverage"] = dict(label=label, check="packed_top",
                                                  receipt=packed_top["receipt"], cases=10)
                if not packed["coverage_limits"]:
                    packed["status"] = "passed"

    attention = next((r for r in rows if r["id"] == "attention"), None)
    if checked_result(attention, "tests/run_attention.py") is None:
        return
    timing = next((r for r in rows if r["id"] == "attention_timing"
                   and r["status"] == "passed"), None)
    timing_result = checked_result(timing, "tests/run_attention_timing.py")
    if timing_result is not None:
        expected = {(d, t, c, f) for d, t in
                    [(8, t) for t in (1, 3, 16, 128)] + [(64, 3)]
                    for c in (2*t, 2*t+1) for f in range(4)}
        runs = timing_result.get("runs", [])
        observed = {(r.get("dimension"), r.get("tile"),
                     r.get("context"), r.get("format")) for r in runs}
        if (len(runs) == len(expected) and observed == expected
                and all(r.get("status") == "passed"
                        and r.get("resident_handoffs") == (r["context"]-1)//r["tile"]
                        and len(r.get("output_cycles", [])) == r["dimension"]
                        for r in runs)):
            label = "resident-tile handoff edge assertions"
            if label in attention.get("coverage_limits", []):
                attention.setdefault("reported_coverage_limits",
                                     list(attention["coverage_limits"]))
                attention["coverage_limits"] = [s for s in attention["coverage_limits"]
                                                if s != label]
                attention["resident_tile_coverage"] = dict(
                    label=label, check="attention_timing", receipt=timing["receipt"],
                    result=timing.get("result_path", timing.get("result")),
                    cases=len(runs), handoffs=sum(r["resident_handoffs"] for r in runs))
    restart = next((r for r in rows if r["id"] == "attention_restart"
                    and r["status"] == "passed"), None)
    if restart is None:
        return
    result_path = restart.get("result_path", restart.get("result"))
    if not result_path:
        return
    for row, script in ((restart, "tests/run_attention_restart.py"),
                        (attention, "tests/run_attention.py")):
        if not row.get("receipt"):
            return
        receipt = json.loads((ROOT/row["receipt"]).read_text())
        if (receipt.get("timed_out") or receipt.get("exit") != 0
                or any(receipt.get("source_sha256", {}).get(path) != current[path]
                       for path in dependencies(script))):
            return
    result = json.loads((ROOT/result_path).read_text())
    expected = ("SUMMARY attention_restart accepts=9 completions=8 fault_responses=1 "
                "failures=0 abort_drains=1 reset_canceled=1 zero_responses=8")
    if result.get("status") != "passed" or expected not in result.get("observations", []):
        return
    covered = {"abort/reset during accepted KV", "zero-latency KV response"}
    limits = attention.get("coverage_limits", [])
    resolved = [label for label in limits if label in covered]
    if not resolved:
        return
    attention.setdefault("reported_coverage_limits", list(limits))
    attention["coverage_limits"] = [label for label in limits if label not in covered]
    attention["resolved_coverage"] = dict(
        labels=resolved, check="attention_restart", receipt=restart["receipt"],
        result=result_path, observations=expected)
    if attention["status"] == "incomplete" and not attention["coverage_limits"]:
        attention["status"] = "passed"


def schedule(has_retained_epilogue=False):
    jobs = [("reproduction", ["tests/run_reproduction.py"],
             REPRODUCTION_BUDGET, REPRODUCTION_BUDGET)]
    for suite in ("primitive", "quantizer"):
        for simulator, seed in [("icarus", 17), *[("verilator", s) for s in SEEDS]]:
            jobs.append((f"{suite}-{simulator}-seed{seed}",
                         ["tests/run_unit.py", "--suite", suite, "--simulator", simulator,
                          "--seed", str(seed)], 120 if simulator == "icarus" else 90, 15))
    for seed in SEEDS:
        if seed != 17 or not has_retained_epilogue:
            jobs.append((f"epilogue-seed{seed}",
                         ["tests/run_epilogue.py", "--seed", str(seed)], 90, 15))
    for identifier in OBLIGATIONS:
        if identifier in ("synthesis", "reproduction"):
            continue
        argv = [f"tests/run_{identifier}.py"]
        if identifier == "attention":
            argv.append("--compact")
        jobs.append((identifier, argv, SUITE_BUDGETS[identifier],
                     MINIMUM_ALLOCATIONS.get(identifier, 60)))
    for identifier, _, _, _ in JOBS:
        jobs.append((f"synthesis-{identifier}",
                     ["tests/run_synthesis.py", "--job", identifier],
                     JOB_BUDGETS[identifier], JOB_BUDGETS[identifier]))
    return jobs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="evidence/l1")
    args = parser.parse_args()
    start = time.time()
    os.environ["HT3_CHECK_DEADLINE"] = str(start + CHECK_SECONDS)
    parent = ROOT / args.output
    parent.resolve().relative_to(ROOT)
    parent.mkdir(parents=True, exist_ok=True)
    output = parent / f"run-{uuid.uuid4().hex}"
    output.mkdir()
    receipt = dict(argv=["python3", "tests/verify.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=CHECK_SECONDS, source_sha256=hashes(),
                   tool_version=sys.version)
    rows = []
    try:
        versions = inventory(output, TOOLS)
        old = retained_epilogue()
        if old is not None:
            rows.append(old)
        synthesis_rows = []
        jobs = schedule(old is not None)
        pending = []
        for identifier, argv, budget, minimum in jobs:
            cached = (find_result(["python3", *argv], dependencies(argv[0]), versions,
                                  allow_failure=identifier.startswith("epilogue-seed"))
                      if identifier != "reproduction" else None)
            if cached is None:
                pending.append((identifier, argv, budget, minimum))
                continue
            result = cached.pop("result")
            row = dict(id=identifier, status=("incomplete" if result.get("coverage_limits")
                                             else result["status"]), reused=True,
                       coverage_limits=result.get("coverage_limits", []),
                       failures=result.get("failures", []), **cached)
            (synthesis_rows if identifier.startswith("synthesis-") else rows).append(row)
        # Do not reserve fictional 15/30/60-second cold compilations. Reproduction
        # is always fresh; completed cases in the remaining suites resume separately.
        for identifier, argv, budget, minimum in pending:
            reserve = SETTLEMENT_RESERVE
            if not (ROOT/argv[0]).is_file():
                row = dict(id=identifier, status="not_implemented",
                           requirement=OBLIGATIONS.get(identifier, identifier))
            else:
                row = child(identifier, argv, output, budget=budget,
                            versions=versions if identifier != "reproduction" else None,
                            reserve=reserve, minimum=minimum)
            (synthesis_rows if identifier.startswith("synthesis-") else rows).append(row)
        rows.append(dict(id="synthesis", status="passed" if all(
            row["status"] == "passed" for row in synthesis_rows) else "failed",
                         jobs=synthesis_rows))
        reconcile_coverage(rows)
    except (OSError, ValueError, AssertionError) as exc:
        rows.append(dict(id="aggregate", status="failed",
                         error=f"{type(exc).__name__}: {exc}"))
    status = "passed" if rows and all(r["status"] == "passed" for r in rows) else "failed"
    summary = dict(status=status, checks=rows, seeds=list(SEEDS),
                   elapsed_s=time.time()-start, source_sha256=receipt["source_sha256"])
    with (output / "result.json").open("x") as out:
        json.dump(summary, out, indent=2)
        out.write("\n")
    receipt.update(end=timestamp(), exit=0 if status == "passed" else 1,
                   result=relative(output / "result.json"), **nested_outcomes(output))
    receipt["timed_out"] = (time.time()-start >= CHECK_SECONDS
                            or receipt["nested_timed_out"] or receipt["budget_exhausted"])
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
        out.write("\n")
    print(json.dumps(dict(status=status, result=relative(output / "result.json"),
                          checks=[dict(id=r["id"], status=r["status"]) for r in rows])),
          flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
