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


def child(identifier, argv, output, budget=None):
    directory = output / f"{identifier}-{uuid.uuid4().hex[:12]}"
    deadline = os.environ["HT3_CHECK_DEADLINE"]
    if budget is not None:
        os.environ["HT3_CHECK_DEADLINE"] = str(min(float(deadline), time.time()+budget))
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
        old = retained_epilogue()
        if old is not None:
            rows.append(old)
        for suite in ("primitive", "quantizer"):
            rows.append(child(f"{suite}-icarus-seed17",
                              ["tests/run_unit.py", "--suite", suite,
                               "--simulator", "icarus", "--seed", "17"], output))
            for seed in SEEDS:
                rows.append(child(f"{suite}-verilator-seed{seed}",
                                  ["tests/run_unit.py", "--suite", suite,
                                   "--simulator", "verilator", "--seed", str(seed)], output))
        for seed in SEEDS:
            if seed == 17 and old is not None:
                continue
            rows.append(child(f"epilogue-seed{seed}",
                              ["tests/run_epilogue.py", "--seed", str(seed)], output))
        for identifier, requirement in OBLIGATIONS.items():
            script = f"tests/run_{identifier}.py"
            if (ROOT / script).is_file():
                rows.append(child(identifier, [script, "--compact"] if identifier == "attention"
                                  else [script], output,
                                  budget=750 if identifier == "attention" else None))
            else:
                rows.append(dict(id=identifier, status="not_implemented",
                                 requirement=requirement))
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
                       for p in output.rglob("*.receipt.json")),
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
