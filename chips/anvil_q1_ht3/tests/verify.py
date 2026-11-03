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
from execution import CHECK_SECONDS, ROOT, execute, hashes, relative, timestamp
from retention import find_result, inventory
from run_synthesis import JOBS, JOB_BUDGETS


SEEDS = (17, 89, 2026)
OBLIGATIONS = {
    "transcendental": "IEEE exp, sin/cos, divide/sqrt; approximation and latency matrix",
    "attention_restart": "KV response fault drains; legal and immediate-invalid next commands complete",
    "attention": "online FP64 attention, formats, masks, tiles, long context and stalls",
    "packed_cache": "FP32 store conversion, packed writes/readback and subsequent attention",
    "compatibility": "integrated inference, CSR/loader/descriptor/batch/reset/error matrix",
    "parameters": "legal extrema/default elaboration and explicit illegal diagnostics",
    "mutations": "five compiling/executing disposable defects rejected by public assertions",
    "benchmarks": "hash-pinned official model/datasets; scored logits, PPL and legacy fixtures",
    "performance": "matched HT2/HT3 actual cycles, transition reduction >60%, bytes and TPM",
    "synthesis": "default hierarchy/256 lanes, compact mapping, new modules and zero latches",
    "reproduction": "fresh declared-source compact behavior and Yosys synthesis",
}

TOOLS = {"python3": ["python3", "--version"], "iverilog": ["iverilog", "-V"],
         "verilator": ["verilator", "--version"], "yosys": ["yosys", "-V"]}
REPRODUCTION_RESERVE = 360
SETTLEMENT_RESERVE = 30
SUITE_BUDGETS = {"attention": 750, "parameters": 260, "attention_restart": 60,
                 "transcendental": 180, "packed_cache": 180, "compatibility": 420,
                 "mutations": 420, "benchmarks": 300, "performance": 480}


def dependencies(script):
    sources = [relative(p) for pattern in ("rtl/*.sv", "design/*.md")
               for p in sorted(ROOT.glob(pattern))]
    shared = ["tests/execution.py"]
    owned = {
        "tests/run_unit.py": ["tests/reference.py", "tests/primitive_tb.sv",
                              "tests/quantizer_tb.sv"],
        "tests/run_epilogue.py": ["tests/reference.py", "tests/epilogue_tb.sv"],
        "tests/run_attention.py": ["tests/reference.py", "tests/attention_tb.sv"],
        "tests/run_attention_restart.py": ["tests/attention_restart_tb.sv"],
        "tests/run_transcendental.py": ["tests/reference.py", "tests/transcendental_tb.sv"],
        "tests/run_packed_cache.py": ["tests/reference.py", "tests/packed_cache_tb.sv"],
        "tests/run_compatibility.py": ["tests/reference.py", "tests/inference_tb.sv"],
        "tests/run_performance.py": ["tests/reference.py", "tests/inference_tb.sv",
                                     "tests/run_compatibility.py",
                                     *[relative(p) for p in sorted(
                                         ROOT.glob("anvil_q1_ht2_reference/rtl/*.sv"))]],
        "tests/run_benchmarks.py": ["tests/official_inputs.json", "tests/official_reference.py",
                                   "tests/acquire_public.py", "tests/reference.py",
                                   "tests/run_compatibility.py", "tests/official_image.py"],
    }
    if script not in owned:
        return list(hashes())
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


def child(identifier, argv, output, budget=None, versions=None, reserve=0):
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
        return dict(id=identifier, status="failed", error=str(exc),
                    receipt=relative(output / f"{identifier}.receipt.json"),
                    result=relative(directory / "result.json"))
    finally:
        os.environ["HT3_CHECK_DEADLINE"] = deadline


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
        for suite in ("primitive", "quantizer"):
            rows.append(child(f"{suite}-icarus-seed17",
                              ["tests/run_unit.py", "--suite", suite,
                               "--simulator", "icarus", "--seed", "17"], output,
                              budget=120, versions=versions,
                              reserve=REPRODUCTION_RESERVE + SETTLEMENT_RESERVE))
            for seed in SEEDS:
                rows.append(child(f"{suite}-verilator-seed{seed}",
                                  ["tests/run_unit.py", "--suite", suite,
                                   "--simulator", "verilator", "--seed", str(seed)], output,
                                  budget=90, versions=versions,
                                  reserve=REPRODUCTION_RESERVE + SETTLEMENT_RESERVE))
        for seed in SEEDS:
            if seed == 17 and old is not None:
                continue
            rows.append(child(f"epilogue-seed{seed}",
                              ["tests/run_epilogue.py", "--seed", str(seed)], output,
                              budget=90, versions=versions,
                              reserve=REPRODUCTION_RESERVE + SETTLEMENT_RESERVE))
        for identifier, requirement in OBLIGATIONS.items():
            if identifier in ("synthesis", "reproduction"):
                continue
            script = f"tests/run_{identifier}.py"
            if (ROOT / script).is_file():
                rows.append(child(identifier, [script, "--compact"] if identifier == "attention"
                                  else [script], output,
                                  budget=SUITE_BUDGETS[identifier], versions=versions,
                                  reserve=REPRODUCTION_RESERVE + SETTLEMENT_RESERVE))
            else:
                rows.append(dict(id=identifier, status="not_implemented",
                                 requirement=requirement))
        synthesis_rows = []
        for index, (identifier, _, _, _) in enumerate(JOBS):
            later_reserve = sum(min(JOB_BUDGETS[name], 60)
                                for name, _, _, _ in JOBS[index + 1:])
            synthesis_rows.append(child(
                f"synthesis-{identifier}", ["tests/run_synthesis.py", "--job", identifier],
                output, budget=JOB_BUDGETS[identifier], versions=versions,
                reserve=REPRODUCTION_RESERVE + SETTLEMENT_RESERVE + later_reserve))
        rows.append(dict(id="synthesis", status="passed" if all(
            row["status"] == "passed" for row in synthesis_rows) else "failed",
                         jobs=synthesis_rows))
        rows.append(child("reproduction", ["tests/run_reproduction.py"], output,
                          budget=REPRODUCTION_RESERVE, reserve=SETTLEMENT_RESERVE))
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
                   timed_out=time.time()-start >= CHECK_SECONDS or any(
                       json.loads(p.read_text()).get("timed_out", False)
                       for p in output.rglob("*.json")
                       if p.name == "receipt.json" or p.name.endswith(".receipt.json")),
                   result=relative(output / "result.json"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
        out.write("\n")
    print(json.dumps(dict(status=status, result=relative(output / "result.json"),
                          checks=[dict(id=r["id"], status=r["status"]) for r in rows])),
          flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
