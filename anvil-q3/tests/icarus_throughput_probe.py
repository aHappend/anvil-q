"""Actual-Icarus throughput diagnostic; NOT an admitted coverage collector.

Implementation only until shared-runtime simulator/deadline reconciliation and
independent append-only command admission. No compact/compiled substitution is
made here: a bounded prefix retains the complete original fixture and schedule.
Exit 2 and receipt status incomplete mean the workload did not finish. Even a
completed diagnostic never contributes to the original coverage ledger.
"""

import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

from decoder_checks import allocate, compare_trace, trace_records
from execution import ROOT, Run, sha256, write_json
from parameters import A, B, C
from reference import Fixture


@contextmanager
def heartbeat(folder, stage):
    stop = threading.Event()

    def report():
        while not stop.wait(30):
            path = folder / "progress.jsonl"
            progress = "no cycle sample yet"
            if path.is_file():
                lines = path.read_text().splitlines()
                if lines:
                    progress = lines[-1]
            print(f"Icarus diagnostic {folder.name} {stage}: {progress}", flush=True)

    worker = threading.Thread(target=report, daemon=True)
    worker.start()
    try:
        yield
    finally:
        stop.set()
        worker.join()


def prepare(folder, g, seed, tokens, prefill):
    model = Fixture(g, seed)
    expected = model.oracle(tokens)
    words = allocate(model, folder, tokens)
    write_json(folder / "expected.json", expected)
    mapping = {}
    for line in (folder / "map.tsv").read_text().splitlines():
        kind, layer, proj, base, rows, cols = map(int, line.split())
        mapping[kind, layer, proj] = base, cols
    with (folder / "expected-writes.txt").open("w") as out:
        out.write(str(len(expected["writes"])) + "\n")
        for token, kind, layer, proj, row, col, value in expected["writes"]:
            base, cols = mapping[kind, layer, proj]
            out.write(f"{base + row * cols + col} {token} {value:08x}\n")
    write_json(folder / "fixture.json", {
        "geometry": asdict(g), "seed": seed, "tokens": tokens,
        "prefill_tokens": prefill, "fixture_sha256": model.digest(),
        "classification": "unchanged synthetic structural/numerical workload",
        "files": {p.name: sha256(p) for p in folder.iterdir() if p.is_file()}})
    return expected, words


def compare_prefix(folder, expected, tokens, progress):
    """Compare observed logits; writes were checked online by the original TB."""
    starts, done, streamed = {}, [], {}
    logits = [[] for _ in tokens]
    logit_count = 0
    for fields in trace_records(folder / "trace.tsv"):
        kind = fields[0]
        if kind == "TOKEN":
            token, identifier, cycle = map(int, fields[1:])
            if (token != len(starts) or token >= len(tokens) or
                    identifier != tokens[token] or cycle < 0):
                raise AssertionError("prefix accepted token differs from original workload")
            starts[token] = cycle
        elif kind == "LOGIT":
            token, index, value, cycle = map(int, fields[1:])
            if (token not in starts or index != len(logits[token]) or
                    index >= len(expected["logits"][token]) or
                    cycle <= starts[token] or value != expected["logits"][token][index]):
                raise AssertionError("prefix logit differs from independent oracle/order")
            logits[token].append(value)
            logit_count += 1
        elif kind == "COMPARED":
            token, writes, requests, weights, cache = map(int, fields[1:])
            required = sum(row[0] == token for row in expected["writes"])
            if (token not in starts or token in streamed or writes != required or
                    requests < writes or min(weights, cache) < 0):
                raise AssertionError("prefix completed-token write comparison incomplete")
            streamed[token] = writes
        elif kind == "DONE":
            token, cycle = map(int, fields[1:])
            if (token != len(done) or token not in streamed or
                    logits[token] != expected["logits"][token] or cycle <= starts[token]):
                raise AssertionError("prefix completed token lacks full numerical comparison")
            done.append(token)
        else:
            raise AssertionError("unexpected record in incomplete normal workload: " + kind)
    if (len(starts) != progress["commands"] or len(done) != progress["completed"] or
            progress["remaining_writes"] + progress["compared_writes"] != len(expected["writes"]) or
            not sum(streamed.values()) <= progress["compared_writes"] <= len(expected["writes"]) or
            not 0 <= progress["responses"] <= progress["requests"]):
        raise AssertionError("prefix trace/progress conservation mismatch")
    return {
        "scope": "incomplete prefix only; online exact writes and observed logits",
        "completed_tokens": len(done), "compared_logits": logit_count,
        "compared_bits": 32 * (progress["compared_writes"] + logit_count),
        "bit_mismatches": 0, "missing_writes": progress["remaining_writes"],
        "missing_logits": sum(map(len, expected["logits"])) - logit_count}


def sample(run, args, label):
    folder = run.path / label
    folder.mkdir()
    g = replace({"A": A, "B": B, "C": C}[label], BANKS=args.banks,
                CACHE_MODE=args.mode, INT4_ASYM=args.asymmetric)
    tokens = [1, 4, 2, 6] if label == "C" else [1, 4, 2, 6, 3, 5, 7]
    prefill = 2 if label == "C" else 4
    measurement = {
        "status": "incomplete", "profile": label, "geometry": asdict(g),
        "seed": args.seed, "tokens": tokens, "prefill_tokens": prefill,
        "simulator": "iverilog/vvp", "driver": "original SystemVerilog top_tb",
        "coverage_credit": False, "original_obligations_discharged": 0,
        "cycle_budget": args.cycles, "timeout_s": args.timeout,
        "stage_seconds": {}, "receipts": {}, "progress": []}
    stage = "fixture"
    started = time.monotonic()
    try:
        with heartbeat(folder, stage):
            expected, words = prepare(folder, g, args.seed, tokens, prefill)
        measurement["stage_seconds"][stage] = time.monotonic() - started
        stage, started = "compilation", time.monotonic()
        binary = folder / "decoder.vvp"
        parameters = {**asdict(g), "WORDS": words,
                      "ICARUS_DIAGNOSTIC_CYCLES": args.cycles,
                      "ICARUS_DIAGNOSTIC_STRIDE": args.progress_cycles}
        command = ["iverilog", "-g2012", "-Wall", "-s", "top_tb",
                   "-o", run.rel(binary)]
        command += [f"-Ptop_tb.{key}={value}" for key, value in parameters.items()]
        command += [run.rel(p) for p in sorted((ROOT / "rtl").glob("*.sv"))]
        command += ["tests/top_tb.sv"]
        with heartbeat(folder, stage):
            _, record = run.tool(command, timeout=args.timeout)
        measurement["receipts"][stage] = str(Path(record["stdout"]).parent / "receipt.json")
        measurement["stage_seconds"][stage] = time.monotonic() - started
        measurement["executable_sha256"] = sha256(binary)
        stage, started = "simulation", time.monotonic()
        with heartbeat(folder, stage):
            _, record = run.tool([
                "vvp", run.rel(binary), "+directory=" + run.rel(folder),
                f"+tokens={len(tokens)}", "+first_new=1", f"+prefill={prefill}",
                "+prelude=0", "+fault=0", "+boundary=0", "+restart=-1",
                "+stream_compare=1", "+sparse_scan=1"],
                timeout=args.timeout, expected=(0, 2))
        measurement["receipts"][stage] = str(Path(record["stdout"]).parent / "receipt.json")
        measurement["stage_seconds"][stage] = time.monotonic() - started
        measurement["simulator_exit_code"] = record["exit_code"]
        stage, started = "comparison", time.monotonic()
        progress = [json.loads(line) for line in (folder / "progress.jsonl").read_text().splitlines()]
        measurement["progress"] = progress
        if not progress or progress[-1]["cycles"] <= 0 or any(
                b["cycles"] < a["cycles"] for a, b in zip(progress, progress[1:])):
            raise AssertionError("missing or nonmonotonic actual simulator cycle progress")
        with heartbeat(folder, stage):
            if record["exit_code"] == 0:
                comparison = compare_trace(folder, expected, g, expected_tokens=tokens)
                measurement["status"] = "completed-diagnostic-only"
            else:
                comparison = compare_prefix(folder, expected, tokens, progress[-1])
                if progress[-1]["completed"] >= len(tokens):
                    raise AssertionError("incomplete exit claimed a complete workload")
        measurement["comparison"] = comparison
        measurement["stage_seconds"][stage] = time.monotonic() - started
        measurement["cycles_per_simulation_second"] = (
            progress[-1]["cycles"] / measurement["stage_seconds"]["simulation"])
        measurement["trace_sha256"] = sha256(folder / "trace.tsv")
    except Exception as exc:
        measurement["stage_seconds"][stage] = time.monotonic() - started
        measurement["status"] = "failed"
        measurement["failed_stage"] = stage
        measurement["diagnosis"] = str(exc)
        raise
    finally:
        progress_path = folder / "progress.jsonl"
        if progress_path.is_file():
            measurement["raw_progress"] = run.rel(progress_path)
        measurement["tool_receipts"] = [
            str(Path(record["stdout"]).parent / "receipt.json") for record in run.records]
        write_json(folder / "measurement.json", measurement)
    return measurement


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles", nargs="+", choices=("A", "B", "C"), default=["A", "B", "C"])
    parser.add_argument("--banks", type=int, choices=(1, 2, 4, 8), default=8)
    parser.add_argument("--mode", type=int, choices=(0, 1, 2), default=2)
    parser.add_argument("--asymmetric", type=int, choices=(0, 1), default=0)
    parser.add_argument("--seed", type=int, choices=(17, 89, 257), default=17)
    parser.add_argument("--cycles", type=int, default=10000)
    parser.add_argument("--progress-cycles", type=int, default=1000)
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    if (not 1000 <= args.cycles <= 500000 or
            not 1000 <= args.progress_cycles <= args.cycles or args.timeout != 3600 or
            len(set(args.profiles)) != len(args.profiles) or
            (args.asymmetric and args.mode != 2) or (args.seed != 17 and "C" in args.profiles)):
        parser.error("require unique original cases, 1000..500000 cycles, valid progress stride, "
                     "3600s deadline, asymmetric INT4 only, and seed17 for C")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run = Run("evidence/preparation/icarus-throughput-" + stamp,
              "actual-Icarus bounded diagnostic; no original matrix coverage credit",
              repair_of="evidence/check-behavior/20261031T060147Z-3eb7a4049470/receipt.json")
    print(run.rel(run.path / "receipt.json"), flush=True)
    measurements = []
    try:
        versions = run.versions([("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V")])
        if any(not entry["available"] for entry in versions.values()):
            raise RuntimeError("actual Icarus tools are required; no simulator substitution")
        for label in args.profiles:
            measurements.append(sample(run, args, label))
        write_json(run.path / "measurements.json", measurements)
        incomplete = any(row["status"] == "incomplete" for row in measurements)
        run.finish("incomplete" if incomplete else "passed", result={
            "scope": "diagnostic only; no matrix acceptance",
            "measurements": run.rel(run.path / "measurements.json"),
            "original_obligations_discharged": 0,
            "complete_workload_comparisons": Counter(row["status"] for row in measurements)})
        return 2 if incomplete else 0
    except Exception as exc:
        write_json(run.path / "measurements.json", measurements)
        run.finish("failed", diagnosis=str(exc))
        raise


if __name__ == "__main__":
    sys.exit(main())
