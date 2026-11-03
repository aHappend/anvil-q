"""Physical DDR bandwidth and complete-FFN accounting from real DUT execution."""

import hashlib
import json
from time import time_ns

from integrated_fast import run_fast_integration
from receipts import ROOT, cleanup_build, compile_verilator, execute, relative
from reference import pack_rows, tile_sum


def generate(path):
    cases = []
    for mask, sparse_percent in ((1, 0), (15, 0), (15, 40), (15, 50)):
        zeros = [[(row * 3 + group * 5) & 15 for row in range(128)]
                 for group in range(5)]
        scales = [sum(0x1400 << (16 * row) for row in range(128))] * 5
        image = {}
        beats, activations = [], []
        for column in range(160):
            group = column // 32
            packed = pack_rows([(value + 1) & 15 for value in zeros[group]])
            image[0x1000 + column * 64] = packed
            skip = ((column % 5 < 2) if sparse_percent == 40 else
                    (column % 2 == 0) if sparse_percent == 50 else False)
            values = [0, 0x8000, 0, 0x8000] if skip else [
                0x3c00, 0xbc00, 0x3800, 0xb800]
            activation = sum(value << (16 * token) for token, value in enumerate(values))
            activations.append(activation)
            if not skip:
                beats.append((packed, pack_rows(zeros[group]), scales[group], activation, mask))
        for group in range(5):
            image[0x10000 + group * 320] = pack_rows(zeros[group])
            for line in range(4):
                image[0x10000 + group * 320 + 64 + line * 64] = (
                    scales[group] >> (line * 512)) & ((1 << 512) - 1)
        expected = tile_sum(beats, mask, (1 << 128) - 1)
        cases.append("\n".join([
            f"{mask} {int(sparse_percent != 0)} {len(beats)} {len(image)}",
            *(f"{address:x} {data:x}" for address, data in sorted(image.items())),
            *(f"{activation:x}" for activation in activations),
            *(f"{(expected >> (token * 4096)) & ((1 << 4096) - 1):x}"
              for token in range(4)),
        ]))
    path.write_text(str(len(cases)) + "\n" + "\n".join(cases) + "\n")


def measure_sustained(run):
    vectors = run / "bandwidth-vectors.txt"
    generate(vectors)
    obj = run / "performance-obj"
    sources = [relative(path) for directory in ("anvil_q3_ht_reference/rtl", "rtl")
               for path in sorted((ROOT / directory).glob("*.sv"))]
    executable = compile_verilator(run, "performance-compile", [
        "verilator", "--binary", "--timing", "-Wno-fatal",
        "--top-module", "performance_tb", "--Mdir", relative(obj), "-j", "2",
        "--output-split", "20000", "--output-split-cfuncs", "2000",
        "-CFLAGS", "-O3", *sources, "tests/performance_tb.sv"], obj, "Vperformance_tb")
    try:
        result = execute(run, "performance-simulate",
                         [relative(executable), f"+vectors={relative(vectors)}"],
                         ["verilator", "--version"])
    finally:
        cleanup_build(obj)
    rows = [json.loads(line.removeprefix("MEASUREMENT ")) for line in
            (result / "stdout.txt").read_text().splitlines()
            if line.startswith("MEASUREMENT ")]
    if len(rows) != 4 or [row["case"] for row in rows] != list(range(4)):
        raise AssertionError("missing measured sustained DMA/MAC fixtures")
    for row, active, retained in zip(rows, (1, 4, 4, 4), (160, 160, 96, 80), strict=True):
        if (row["cycles"] <= 0 or row["qweight_beats"] != retained or
                row["metadata_beats"] != 25 or row["operands"] != retained or
                row["candidate_consumers"] != active * retained or
                row["lane_comparisons"] != 512):
            raise AssertionError("incomplete physical-byte or numerical bandwidth evidence")
        row["physical_qweight_bytes"] = 64 * row["qweight_beats"]
        row["physical_metadata_bytes"] = 64 * row["metadata_beats"]
        row["total_physical_bytes"] = (
            row["physical_qweight_bytes"] + row["physical_metadata_bytes"])
        row["useful_candidate_weight_bytes"] = 64 * row["candidate_consumers"]
    one, four, sparse40, sparse50 = rows
    raw_reuse = four["candidate_consumers"] / four["qweight_beats"]
    effective = ((four["useful_candidate_weight_bytes"] / four["cycles"]) /
                 (one["useful_candidate_weight_bytes"] / one["cycles"]))
    reductions = [1 - row["qweight_beats"] / four["qweight_beats"]
                  for row in (sparse40, sparse50)]
    if raw_reuse != 4 or effective < 3.4 or reductions != [0.4, 0.5]:
        raise AssertionError("measured reuse/bandwidth/down-projection thresholds not met")
    return {
        "observed": rows, "raw_qweight_reuse": raw_reuse,
        "effective_bandwidth_ratio": effective, "down_qweight_reductions": reductions,
        "clock_hz_for_reporting": 100000000,
        "denominator": "same 160-column 128-row DMA/MAC traversal, including all "
                       "25 physical metadata reads, activation scan and reduction cycles",
        "scope": "sustained projection fixture, not end-to-end decoding throughput; "
                 "independent synthetic activations and resident metadata",
        "vector_sha256": hashlib.sha256(vectors.read_bytes()).hexdigest(),
        "receipt": relative(result / "receipt.json"),
    }


def complete_ffn(integration):
    if integration.get("diagnostic_only") or integration.get(
            "functional_result") != "nonzero-model-compared":
        raise AssertionError("whole-FFN measurement needs completed numerical integration")
    transactions = [dict(row) for row in integration["observed"].get("transactions", [])]
    if len(transactions) != 3:
        raise AssertionError("missing measured one-token, chain and branch transactions")
    for row, evaluated, accepted in zip(
            transactions, (1, 4, 4), (1, 4, 2), strict=True):
        if (row.get("evaluated_tokens") != evaluated or
                row.get("accepted_tokens") != accepted or row.get("cycles", 0) <= 0):
            raise AssertionError("incomplete evaluated/accepted-token accounting")
        for field in ("qweight_bytes", "metadata_bytes",
                      "ffn_qweight_bytes", "ffn_metadata_bytes"):
            if row.get(field, 0) <= 0 or row[field] % 64:
                raise AssertionError("missing physical FFN traffic category")
        row["complete_ffn_bytes"] = row["ffn_qweight_bytes"] + row["ffn_metadata_bytes"]
        row["ffn_bytes_per_evaluated_token"] = row["complete_ffn_bytes"] / evaluated
        row["ffn_bytes_per_committed_token"] = row["complete_ffn_bytes"] / accepted
    one, chain, branch = transactions
    baseline = 4 * one["complete_ffn_bytes"]
    reduction = 1 - chain["complete_ffn_bytes"] / baseline
    if reduction < 0.4:
        raise AssertionError("measured accepted-batch complete-FFN saving below 40 percent")
    return {
        "whole_ffn_reduction": reduction, "transactions": transactions,
        "dense_serial_four_token_ffn_bytes": baseline,
        "denominator": "four otherwise identical one-active-token dense HT2 FFN traversals; "
                       "gate/up/down and zero/scale physical reads across all 36 layers",
        "attribution": "batching only; sparsity disabled in complete-model workload",
        "accepted_batch": "all-four-accepted chain; rejected branching work is reported separately",
        "integration_receipt": integration["receipt"],
    }


def run_performance(run, integration=None):
    # A direct invocation owns its prerequisite rather than relying on check order.
    if integration is None:
        child = run / f"integrated-prerequisite-{time_ns()}"
        child.mkdir()
        integration = run_fast_integration(child, 1, 17)
    ffn = complete_ffn(integration)
    sustained = measure_sustained(run)
    summary = {"whole_ffn_reduction": ffn["whole_ffn_reduction"],
               "effective_bandwidth_ratio": sustained["effective_bandwidth_ratio"],
               "complete_ffn": ffn, "sustained_projection": sustained}
    (run / "performance-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
