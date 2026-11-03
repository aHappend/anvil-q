"""Portable L1 check dispatcher; the shared runtime owns engineering admission.

Run from the project root:
  python3 tests/verify.py --check behavior|synthesis|defects|benchmark|portability

Prerequisites: Python 3, Icarus/vvp, Verilator with a C++ compiler and make, Yosys.
Missing prerequisites, comparisons,
sources, coverage rows or native vector support are failures, never skipped
passes. Each invocation retains a source-bound plan, raw child streams and an
accounted run ledger under a unique evidence/l1/ directory. Native timing,
physical resources, full-token performance and report approval are separate
mandatory shared-runtime gates, not local-device operations in this script.

Large/token/mutation workloads use compiled Verilator with hash-bound,
check-local model reuse; seeds and fixture paths are run-time testbench inputs,
not changes to DUT parameters. Icarus retains full compact leaf tests and
four-state time-zero/edge startup checks for each compiled configuration.
Behavior dispatches same-configuration seeds/scenarios in one worker so cache
lock waiters never consume the other workers. Native-row jobs start first.
Behavior and benchmark dispatch at most eight jobs, bounded
by current storage, memory and CPU capacity, with cross-process compiler admission
and two compiler jobs per build. Native synthesis dispatches at most four jobs,
bounded by available CPU/memory, and retains memory -nomap in every child.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from itertools import product
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from defect_checks import MUTATIONS
from retained import ROOT, Run
from suite_manifest import SEEDS, configurations, manifest
from synthesis_dispatch import policy as synthesis_policy, resources as synthesis_resources
from simulation import build_policy
from top_lifecycle_checks import SCENARIOS


def behavior_jobs():
    yield "fp32-scalar", ["tests/numerical_checks.py", "--case", "scalar"], "IEEE FP32 arithmetic"
    yield "fp32-bias-add", ["tests/numerical_checks.py", "--case", "add"], (
        "registered GEMV bias adder: IEEE FP32, special values, RNE and output stalls")
    yield "exp", ["tests/exp_checks.py"], "normative exp, high-precision <=1e-5"
    yield "parameters", ["tests/parameter_checks.py"], "native/legal elaboration and illegal diagnostics"
    for fmt in ("bf16", "fp16"):
        yield f"native-lane-{fmt}", [
            "tests/numerical_checks.py", "--case", "lane", "--format", fmt
        ], "4096 native beats, exact three-stage latency, II=1 and stalls"
        yield f"awq-lane-{fmt}", [
            "tests/awq_lane_checks.py", "--format", fmt
        ], "4096 actual AWQ-fed beats, separate dequant and accumulator comparison"
        yield f"lane-reset-{fmt}", [
            "tests/lane_lifecycle_checks.py", "--format", fmt
        ], "reset at all pipeline occupancies, conservation and numerical recovery"
        yield f"awq-{fmt}", [
            "tests/codec_checks.py", "--case", "awq", "--format", fmt
        ], "all AWQ nibbles/deltas, special scales and signed zero"
        for block in (1, 2, 16):
            yield f"codec-{fmt}-block{block}", [
                "tests/codec_checks.py", "--case", "codec", "--format", fmt, "--block", str(block)
            ], "all 256 bytes, RNE error bounds, exponent extremes and errors"
    for banks, depth, seed in product((1, 2, 4), (1, 3, 16), SEEDS):
        yield f"scheduler-b{banks}-q{depth}-s{seed}", [
            "tests/scheduler_checks.py", "--banks", str(banks), "--depth", str(depth),
            "--seed", str(seed)
        ], "contention, queue boundaries, reverse responses, bank/result stalls and tagged errors"
    for banks, depth in product((1, 2, 4), (1, 3, 16)):
        yield f"scheduler-lifecycle-b{banks}-q{depth}", [
            "tests/scheduler_lifecycle_checks.py", "--banks", str(banks), "--depth", str(depth)
        ], "flush-edge accepted transfers, unknown/duplicate/wrong-bank tags, reset and recovery"
    for fmt, cache, block, seed in product(("bf16", "fp16"), (0, 1), (1, 2, 16), SEEDS):
        yield f"cache-{fmt}-c{cache}-block{block}-s{seed}", [
            "tests/cache_protocol_checks.py", "--format", fmt, "--cache", str(cache),
            "--block", str(block), "--seed", str(seed)
        ], "all component/head/layer boundaries; commit acknowledgement, corruption and invalidation"
    for config in configurations():
        banks, cache, fmt, weights, seed = (
            config[k] for k in ("banks", "cache_mode", "fp_format", "weight_mode", "seed"))
        label = f"token-{fmt}-w{weights}-c{cache}-b{banks}-s{seed}"
        yield label, [
            "tests/token_checks.py", "--format", fmt, "--weights", str(weights),
            "--cache", str(cache), "--banks", str(banks), "--seed", str(seed)
        ], "nonzero two-layer three-position GQA6:1 decoder; every write/logit/transaction compared"
    for banks, fmt, weights, cache in product((1, 2, 4), ("bf16", "fp16"), (0, 1), (0, 1)):
        for scenario in SCENARIOS:
            yield f"top-{scenario}-{fmt}-w{weights}-c{cache}-b{banks}", [
                "tests/top_lifecycle_checks.py", "--case", scenario, "--format", fmt,
                "--weights", str(weights), "--cache", str(cache), "--banks", str(banks)
            ], "public token cancellation/fault, drain, failed-sequence rejection and numerical recovery"
        for depth in (1, 3, 16):
            yield f"singleton-{fmt}-w{weights}-c{cache}-b{banks}-q{depth}", [
                "tests/token_checks.py", "--singleton", "--format", fmt, "--weights", str(weights),
                "--cache", str(cache), "--banks", str(banks), "--seed", "89", "--depth", str(depth)
            ], "single position/vocabulary, non-power-of-two GROUP_SIZE=3, CACHE_BLOCK=1"
    for banks, fmt, weights, projection, seed in product(
            (1, 2, 4), ("bf16", "fp16"), (0, 1), (0, 6), SEEDS):
        yield f"native-row-{fmt}-w{weights}-b{banks}-p{projection}-s{seed}", [
            "tests/projection_row_checks.py", "--format", fmt, "--weights", str(weights),
            "--banks", str(banks), "--projection", str(projection), "--seed", str(seed)
        ], "full 1536/8960-column native-geometry first row groups, not full projection timing"
    for seed in SEEDS:
        yield f"attention-adversarial-s{seed}", [
            "tests/attention_checks.py", "--reduced", "--adversarial", "--seed", str(seed)
        ], "separately reported adversarial causal attention with actual-output feedback"
    for fmt in ("bf16", "fp16"):
        yield f"expanded-fp-{fmt}", [
            "tests/token_checks.py", "--format", fmt, "--weights", "1", "--cache", "1",
            "--banks", "4", "--seed", "17", "--expanded-packages"
        ], "lossless synthesis frontend retains independently checked FP token behavior"
    for cache in (0, 1):
        yield f"expanded-parent-c{cache}", [
            "tests/token_checks.py", "--product", "parent", "--weights", "1",
            "--cache", str(cache), "--banks", "2", "--seed", "43", "--expanded-packages"
        ], "qualified-package frontend repair retains actual parent token behavior"


def synthesis_jobs():
    for banks, cache, fmt, weights in product((1, 2, 4), (0, 1), ("bf16", "fp16"), (0, 1)):
        yield f"fp-native-b{banks}-c{cache}-{fmt}-w{weights}", [
            "tests/synthesis_checks.py", "--top", "anvil_q2_fp_top",
            "--banks", str(banks), "--cache", str(cache), "--format", fmt, "--weights", str(weights)
        ], "native dimensions; literal bank hierarchy, substantive state, zero latches/dividers/loops"
    for banks, cache in product((1, 2, 4), (0, 1)):
        yield f"parent-native-b{banks}-c{cache}", [
            "tests/synthesis_checks.py", "--top", "anvil_q2_top", "--product", "parent",
            "--banks", str(banks), "--cache", str(cache)
        ], "real parent's native-dimensional generic cell/state/memory comparison"


def jobs(check):
    if check == "behavior":
        return list(behavior_jobs())
    if check == "synthesis":
        return list(synthesis_jobs())
    if check == "defects":
        return [(case, ["tests/defect_checks.py", "--case", case],
                 "pristine and mutant compile; normal checker rejects the targeted functional defect")
                for case in MUTATIONS]
    if check == "benchmark":
        return [
            ("five-domain-matrix", ["tests/benchmark_checks.py"],
             "complete reduced matrix and real parent/high-precision comparisons"),
            *[(f"full-head-drift-s{seed}", ["tests/attention_checks.py", "--seed", str(seed)],
               "28 layers, 12/2 heads, D=128, eight causal positions; actual-output feedback")
              for seed in SEEDS],
            ("native-vector-interface", ["tests/hardware_vectors.py", "--self-check"],
             "portable native-shape vector generation and independent bridge comparison entrypoints"),
        ]
    return [("fresh-declared-sources", ["tests/portability_checks.py"],
             "fresh source-only copy, real representative compile/simulation/reference and synthesis")]


def source_contract():
    result = {}
    for name in ("anvil_q2_bank_scheduler.sv", "anvil_q2_bus_mux.sv",
                 "anvil_q2_scalar_arbiter.sv", "anvil_q2_mem_port.sv"):
        current, parent = ROOT / "rtl" / name, ROOT / "anvil_q2_reference/rtl" / name
        assert current.read_bytes() == parent.read_bytes(), f"parent control substrate changed: {name}"
        result[name] = hashlib.sha256(current.read_bytes()).hexdigest()
    for pattern in ("rtl/*.sv", "design/*", "tests/*.py", "anvil_q2_reference/rtl/*.sv"):
        assert any(p.is_file() for p in ROOT.glob(pattern)), f"unmatched source selector: {pattern}"
    return result


def execute_job(run, record):
    try:
        execute_record(run, record)
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError, KeyError) as exc:
        record.update(outcome="failed", failure=f"{type(exc).__name__}: {exc}")
        raise


def configuration_groups(records):
    """Keep same-model seeds/scenarios in one worker, without dropping runs."""
    groups = {}
    for record in records:
        argv = record["argv"]
        key = argv[:2]
        i = 2
        while i < len(argv):
            if argv[i] == "--seed" or (
                    argv[1] == "tests/top_lifecycle_checks.py" and argv[i] == "--case"):
                i += 2
            else:
                key.append(argv[i])
                i += 1
        groups.setdefault(tuple(key), []).append(record)
    priority = {"tests/projection_row_checks.py": 0, "tests/token_checks.py": 1,
                "tests/top_lifecycle_checks.py": 2}
    return sorted(groups.values(), key=lambda rows: priority.get(rows[0]["argv"][1], 3))


def execute_group(run, records):
    for record in records:
        execute_job(run, record)


def execute_record(run, record):
    label = record["id"]
    record["outcome"] = "running"
    output = run.command(
        record["argv"], label, timeout=86400, expected_codes=(0, 1),
        environment={"ANVIL_EVIDENCE_ROOT": run.relative(run.path / "children"),
                     "ANVIL_SIM_CACHE": run.relative(run.path / "compiled-models")})
    command = next(c for c in run.receipt["commands"] if c["stdout"] == run.relative(output))
    receipts = [line for line in output.read_text().splitlines() if line.endswith("/receipt.json")]
    if len(receipts) != 1:
        record["outcome"] = "missing-or-ambiguous-receipt"
        raise AssertionError(f"{label}: missing/ambiguous child receipt")
    child_path = ROOT / receipts[0]
    child_path.resolve().relative_to((run.path / "children").resolve())
    child = json.loads(child_path.read_text())
    record.update(receipt=receipts[0], child_outcome=child["outcome"],
                  exit_code=command["exit_code"], metrics=child.get("metrics"))
    assert child["source_sha256"] == run.receipt["source_sha256"], (
        f"{label}: source identity changed")
    if record["exit_code"] != 0 or child["outcome"] != "passed-focused-only":
        record["outcome"] = "failed"
        raise AssertionError(f"{label}: failed: {receipts[0]}: {child.get('failure')}")
    record["outcome"] = "compared"


def execute(check):
    run = Run(f"l1-{check}", root="evidence/l1")
    records = []
    try:
        required = {"python3"}
        if check in ("behavior", "defects", "benchmark", "portability"):
            required.update(("iverilog", "vvp"))
        if check in ("behavior", "defects", "benchmark"):
            required.update(("verilator", "g++", "make"))
        if check in ("synthesis", "portability"):
            required.add("yosys")
        for executable in sorted(required):
            if shutil.which(executable) is None:
                raise RuntimeError(f"missing required executable: {executable}")
        preserved = source_contract()
        planned = jobs(check)
        assert planned and len({label for label, _, _ in planned}) == len(planned)
        records = [dict(id=label, argv=["python3", *arguments], requirement=requirement,
                        outcome="not-executed") for label, arguments, requirement in planned]
        definition = dict(manifest(), check=check, jobs=records, preserved_parent_control=preserved)
        definition_path = run.path / "check-manifest.json"
        definition_path.write_text(json.dumps(definition, indent=2) + "\n")
        run.receipt["generated_sha256"] = {
            run.relative(definition_path): hashlib.sha256(definition_path.read_bytes()).hexdigest()}
        for record in records:
            if not (ROOT / record["argv"][1]).is_file():
                record["outcome"] = "missing-verification-source"
                raise RuntimeError(f"required verification entrypoint missing: {record['argv'][1]}")
        workers = 4 if check in ("behavior", "benchmark") else 1
        if check in ("behavior", "benchmark"):
            dispatch = build_policy()
            workers = dispatch["maximum_concurrent_jobs"]
            run.receipt["simulation_dispatch"] = dispatch
        if check == "synthesis":
            dispatch = synthesis_policy(synthesis_resources())
            workers = dispatch["maximum_concurrent_jobs"]
            run.receipt["synthesis_dispatch"] = dispatch
        run.receipt["maximum_concurrent_jobs"] = workers
        groups = configuration_groups(records) if check == "behavior" else [[r] for r in records]
        run.receipt["dispatch_groups"] = [[r["id"] for r in group] for group in groups]
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(execute_group, run, group) for group in groups]
            try:
                for future in as_completed(futures):
                    future.result()
            except BaseException:
                for future in futures:
                    future.cancel()
                raise
        assert all(row["outcome"] == "compared" for row in records), "coverage denominator incomplete"
        ledger = run.path / "ledger.json"
        ledger.write_text(json.dumps(records, indent=2) + "\n")
        run.finish("passed", check=check, metrics={
            "required_runs": len(records), "compared_runs": len(records),
            "ledger": run.relative(ledger)}, native_hardware_acceptance=False)
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
        ledger = run.path / "failed-ledger.json"
        ledger.write_text(json.dumps(records, indent=2) + "\n")
        run.finish("failed", check=check, failure=f"{type(exc).__name__}: {exc}",
                   ledger=run.relative(ledger))
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", required=True, choices=(
        "behavior", "synthesis", "defects", "benchmark", "portability"))
    raise SystemExit(execute(parser.parse_args().check))
