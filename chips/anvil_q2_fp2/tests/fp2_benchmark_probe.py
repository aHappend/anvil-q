"""Matched five-domain synthetic workloads; never an official Qwen quality test."""

from collections import Counter
from fractions import Fraction
import hashlib
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import ROOT
import fp2_parent_probe as parent
import fp2_top_probe as top
import fp2_kv_traffic_probe as kv_traffic
from fp2_reference import exact, finite, rounded, ulp_distance


DOMAINS = (
    ("language", 13, ((3, 0, 1, 0), (5, 1, 0, 0), (7, 2, 0, 1))),
    ("mathematics", 19, ((2, 0, 1, 0), (6, 1, 0, 1))),
    ("coding", 23, ((11, 0, 1, 0), (12, 1, 0, 0), (15, 2, 0, 1))),
    ("reasoning", 29, ((1, 0, 1, 0), (4, 1, 0, 1), (9, 0, 1, 0), (10, 1, 0, 1))),
    ("knowledge", 31, ((0, 0, 1, 0), (8, 1, 0, 0), (14, 2, 0, 1))),
)


def fixture(salt):
    def embedding(row, column):
        return rounded(Fraction(((row * salt + column * 7 + salt) % 23) - 11, 32),
                       fraction_bits=7)
    return embedding


def traffic_tb(text, wide):
    declarations = """
  integer traffic_reads[0:15],traffic_writes[0:15],traffic_i;
"""
    text = text.replace("module tb;", "module tb;" + declarations, 1)
    text = text.replace("    rst_n=0;", """
    for(traffic_i=0;traffic_i<16;traffic_i=traffic_i+1) begin
      traffic_reads[traffic_i]=0; traffic_writes[traffic_i]=0;
    end
    rst_n=0;""", 1)
    request = "ddr_req" if wide else "req"
    anchor = f"      if ({request}_valid && {request}_ready) begin" if wide else \
             "      if(req_valid && req_ready) begin"
    if text.count(anchor) != 1:
        raise ValueError("traffic instrumentation request anchor changed")
    text = text.replace(anchor, anchor + f"""
        if({request}_write) traffic_writes[{request}_kind]=traffic_writes[{request}_kind]+1;
        else traffic_reads[{request}_kind]=traffic_reads[{request}_kind]+1;
""", 1)
    text = text.replace("          $finish;", """
          for(traffic_i=0;traffic_i<16;traffic_i=traffic_i+1)
            $display("TRAFFIC %0d %0d %0d",traffic_i,traffic_reads[traffic_i],traffic_writes[traffic_i]);
          $finish;""", 1)
    return text


CSR_TASK = r"""
  reg bench_csr_valid=0,bench_csr_write=0,bench_csr_ready=0;
  reg [15:0] bench_csr_addr=0;
  reg [31:0] bench_csr_data=0,bench_csr_observation;
  integer bench_counter,bench_hold;
  task automatic bench_csr(input [15:0] address,input write_,input [31:0] data_);
    begin
      @(negedge clk);
      bench_csr_valid=1; bench_csr_write=write_;
      bench_csr_addr=address; bench_csr_data=data_; bench_csr_ready=0;
      @(posedge clk);
      if(csr_req_ready !== 1'b1) $fatal(1,"BENCH_CSR_NOT_READY");
      #1;
      if(csr_rsp_valid !== 1'b0) $fatal(1,"BENCH_CSR_EARLY");
      @(negedge clk); bench_csr_valid=0;
      @(posedge clk); #1;
      if(csr_rsp_valid !== 1'b1 || csr_rsp_error !== 1'b0 ||
         (^csr_rsp_rdata) === 1'bx) $fatal(1,"BENCH_CSR_RESPONSE");
      bench_csr_observation=csr_rsp_rdata;
      for(bench_hold=0;bench_hold<3;bench_hold=bench_hold+1) begin
        @(posedge clk); #1;
        if(csr_rsp_valid !== 1'b1 || csr_rsp_rdata !== bench_csr_observation ||
           csr_rsp_error !== 1'b0) $fatal(1,"BENCH_CSR_STABILITY");
      end
      @(negedge clk); bench_csr_ready=1;
      @(posedge clk); #1;
      if(csr_rsp_valid !== 1'b0) $fatal(1,"BENCH_CSR_DUPLICATION");
    end
  endtask
"""


def instrument_top():
    text = traffic_tb(top.TOP_TB, True)
    text = text.replace("module tb;", "module tb;" + CSR_TASK, 1)
    for needle, replacement in (
        (".csr_req_valid(1'b0)", ".csr_req_valid(bench_csr_valid)"),
        (".csr_req_write(1'b0)", ".csr_req_write(bench_csr_write)"),
        (".csr_req_addr(16'd0)", ".csr_req_addr(bench_csr_addr)"),
        (".csr_req_wdata(32'd0)", ".csr_req_wdata(bench_csr_data)"),
        (".csr_req_wstrb(4'd0)", ".csr_req_wstrb(4'hf)"),
        (".csr_rsp_ready(1'b1)", ".csr_rsp_ready(bench_csr_ready)"),
    ):
        if text.count(needle) != 1:
            raise ValueError(f"CSR instrumentation anchor changed: {needle}")
        text = text.replace(needle, replacement, 1)
    text = text.replace("          $finish;", """
          bench_csr(16'h0008,1,32'd2);
          for(bench_counter=0;bench_counter<12;bench_counter=bench_counter+1) begin
            bench_csr(16'h0010+bench_counter*8,0,0);
            $display("TELEMETRY %0d low %08h",bench_counter,bench_csr_observation);
            bench_csr(16'h0014+bench_counter*8,0,0);
            $display("TELEMETRY %0d high %08h",bench_counter,bench_csr_observation);
          end
          $finish;""", 1)
    return text


def observations(probe, wide):
    reads, writes, telemetry = {}, {}, {}
    output = probe.directory / "simulation.stdout.txt"
    with output.open() as stream:
        for line in stream:
            words = line.split()
            if words[:1] == ["TRAFFIC"]:
                kind, read, write = map(int, words[1:])
                if kind in reads or not 0 <= kind < 16:
                    raise AssertionError("duplicate/out-of-range traffic row")
                reads[kind], writes[kind] = read, write
            elif words[:1] == ["TELEMETRY"]:
                key = (int(words[1]), words[2])
                if key in telemetry:
                    raise AssertionError("duplicate telemetry response")
                telemetry[key] = int(words[3], 16)
    if len(reads) != 16:
        raise AssertionError("missing accepted-transfer accounting")
    summary = probe.summary["transactions"]
    probe.compare("traffic-read-conservation", summary["read_beats" if wide else "read_words"],
                  sum(reads.values()), {})
    probe.compare("traffic-write-conservation", summary["write_beats" if wide else "write_words"],
                  sum(writes.values()), {})
    width = 64 if wide else 4
    result = {
        "read_bytes": width * sum(reads.values()), "write_bytes": width * sum(writes.values()),
        "reads_by_kind": reads, "writes_by_kind": writes,
        "kv_read_bytes": width * sum(reads[kind] for kind in (9, 10, 12, 13, 14, 15)),
        "intermediate_architectural_write_bytes": width * writes[8],
    }
    if wide:
        if len(telemetry) != 24:
            raise AssertionError("missing coherent CSR snapshot words")
        counters = {index: telemetry[index, "low"] | (telemetry[index, "high"] << 32)
                    for index in range(12)}
        expected = {
            1: summary["request_stalls"],
            5: 64 * sum(reads[kind] + writes[kind] for kind in (9, 10, 12, 13, 14, 15)),
            6: sum(reads.values()), 7: sum(writes.values()),
            8: 10 * sum(command[1] + 1 for command in probe.summary["commands"]),
            9: len(probe.summary["commands"]), 10: 0, 11: 0,
        }
        for index, value in expected.items():
            probe.compare("integrated-telemetry", value, counters[index], {"counter": index})
        probe.compare("zero-fused-intermediate-writebacks", 0, writes[8], {})
        result["telemetry_snapshot"] = counters
    probe.summary["external_accounting"] = result
    return result


def numerical_distribution(probe):
    rows = probe.summary["numerical_metrics"]
    if not rows or any(row["absolute"] is None for row in rows):
        raise AssertionError("missing finite independent benchmark comparisons")
    return {
        "compared_logits": len(rows), "ulp_histogram": dict(sorted(Counter(
            row["ulp"] for row in rows).items())),
        "maximum_absolute_error": max(row["absolute"] for row in rows),
        "maximum_relative_error": max((row["relative"] for row in rows
                                       if row["relative"] is not None), default=0),
    }


def run(suite, execute):
    records = []
    for name, salt, commands in DOMAINS:
        embedding = fixture(salt)
        fixture_hash = hashlib.sha256(bytes.fromhex("".join(
            f"{embedding(row, column):04x}" for row in range(16) for column in range(48)))).hexdigest()
        for seed in (17, 89, 203):
            def parent_case(probe):
                parent.run(probe, commands=commands, seed=seed, embedding_fn=embedding,
                           tb_template=traffic_tb(parent.PARENT_TB, False))
                observations(probe, False)
            baseline = execute(f"{name}-parent-seed{seed}", parent_case)
            parent_accounting = baseline.summary["external_accounting"]
            for mode in (0, 2):
                def fp2_case(probe):
                    top.run(probe, "verilator", commands=commands, seed=seed, weight_mode=mode,
                            cache_mode=mode, embedding_fn=embedding, tb_template=instrument_top())
                    observations(probe, True)
                accelerated = execute(f"{name}-fp2-mode{mode}-seed{seed}", fp2_case)
                accounting = accelerated.summary["external_accounting"]
                reference_run = execute(f"{name}-six-query-reference-mode{mode}-seed{seed}",
                                        lambda p: kv_traffic.run(p, commands, mode, seed))
                reference_accounting = reference_run.summary["nonbroadcast_external_accounting"]
                suite.compare("at-least-83.333-percent-kv-read-reduction", True,
                              6 * accounting["kv_read_bytes"] <= reference_accounting["kv_read_bytes"],
                              {"domain": name, "seed": seed, "mode": mode,
                               "broadcast_bytes": accounting["kv_read_bytes"],
                               "nonbroadcast_bytes": reference_accounting["kv_read_bytes"]})
                # Both graphs use the identical logical BF16 fixture. The zero branches
                # are exactly representable in native and MX storage.
                original = {(command, index): bits for command, index, bits
                            in baseline.summary["logit_bits"]}
                for command, index, bits in accelerated.summary["logit_bits"]:
                    reference = original[command, index]
                    difference = abs(exact(bits) - exact(reference)) if finite(bits) else None
                    suite.compare("matched-parent-fp2-logits", True,
                                  difference is not None and difference <=
                                  Fraction(5, 10000) * (1 + abs(exact(reference))),
                                  {"domain": name, "seed": seed, "mode": mode,
                                   "command": command, "index": index,
                                   "ulp": ulp_distance(reference, bits)})
                records.append({
                    "domain": name, "seed": seed, "mode": mode, "fixture_sha256": fixture_hash,
                    "geometry": [1, 48, 64, 6, 1, 8, 16, 3],
                    "parent_cycles": baseline.summary["transactions"]["cycles"],
                    "fp2_cycles": accelerated.summary["transactions"]["cycles"],
                    "speedup": baseline.summary["transactions"]["cycles"] /
                               accelerated.summary["transactions"]["cycles"],
                    "parent_traffic": parent_accounting, "fp2_traffic": accounting,
                    "nonbroadcast_traffic": reference_accounting,
                    "observed_kv_read_reduction": 1 - accounting["kv_read_bytes"] /
                                                   reference_accounting["kv_read_bytes"],
                    "parent_precision": numerical_distribution(baseline),
                    "fp2_precision": numerical_distribution(accelerated),
                    "recommendation": (
                        "Increase memory service/prefetch availability" if
                        accounting["telemetry_snapshot"][1] else
                        "Inspect tensor/epilogue occupancy before changing scheduling"),
                    "parent_receipt": str((baseline.directory / "receipt.json").relative_to(ROOT)),
                    "fp2_receipt": str((accelerated.directory / "receipt.json").relative_to(ROOT)),
                    "nonbroadcast_receipt": str((reference_run.directory / "receipt.json").relative_to(ROOT)),
                })
    suite.compare("benchmark-run-count", 30, len(records), {})
    geometric_mean = math.exp(sum(math.log(row["speedup"]) for row in records) / len(records))
    suite.compare("measured-geometric-mean-speedup", True, geometric_mean > 1,
                  {"observed": geometric_mean, "required": ">1"})
    suite.summary["benchmark"] = {
        "fixtures": "deterministic domain-labelled synthetic embeddings/tokens; zero branch weights/biases",
        "official_checkpoint_data": False, "qwen_task_accuracy_claim": False,
        "memory_service": "same xorshift seeds, readiness bits, 2..17 cycle latency and newest-due-first reordering",
        "beat_accounting": "actual accepted 64-byte DDR beats versus actual accepted 4-byte parent words",
        "physical_lane_count": 128,
        "per_domain": records, "geometric_mean_cycle_speedup": geometric_mean,
        "physical_comparison": "requires genuine comparable source-bound parent and FP2 Quartus results",
        "power_claim": "none",
    }


def main():
    from fp2_probe import SuiteDeadline
    from verify import Suite
    suite = Suite("benchmark-smoke", preparation=True)
    error = None
    try:
        with SuiteDeadline():
            for mode in (0, 2):
                def smoke(probe):
                    top.run(probe, "verilator", weight_mode=mode, cache_mode=mode,
                            tb_template=instrument_top())
                    observations(probe, True)
                suite.execute(f"instrumented-top-mode{mode}", smoke)
            def baseline(probe):
                parent.run(probe, tb_template=traffic_tb(parent.PARENT_TB, False))
                observations(probe, False)
            suite.execute("instrumented-parent", baseline)
    except Exception as failure:
        error = f"{type(failure).__name__}: {failure}"
    return suite.probe.settle(error)


if __name__ == "__main__":
    raise SystemExit(main())
