"""4096 real AWQ-dequantized eight-row lane beats per selected format.

Public AWQ outputs fill a stimulus buffer before the independent lane latency,
II, stall and FP32 recurrence experiment. No expected weight is driven back
into the DUT; every captured AWQ weight is separately compared to rational RNE.
"""

import argparse
import hashlib
import random
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from codec_checks import awq_reference
from fp_reference import rounded
from numerical_checks import LANE_BENCH, compare_lane
from retained import ROOT, Run, require_time_zero, with_time_zero_check


DECLARATIONS = r"""
  reg stream_active=0,awq_input=0,awq_output_ready=0;
  reg [209:0] awq_sources[0:COUNT-1];
  reg [31:0] awq_qw=0,awq_qz=0;
  reg [127:0] awq_scales=0;
  wire [7:0] awq_ready,awq_valid,awq_error;
  wire [127:0] awq_weights;
  integer prefill,j;
  genvar weight_lane;
  generate for(weight_lane=0;weight_lane<8;weight_lane=weight_lane+1) begin: frontends
    anvil_q2_fp_awq_dequant #(FORMAT) dequant(
      clk,rst_n,awq_input,awq_ready[weight_lane],awq_qw,awq_qz,
      awq_scales[weight_lane*16+:16],3'(weight_lane),
      awq_valid[weight_lane],awq_output_ready,
      awq_weights[weight_lane*16+:16],awq_error[weight_lane]);
  end endgenerate
"""

PREFILL = r"""
    for(prefill=0;prefill<COUNT;prefill=prefill+1) begin
      @(negedge clk);
      awq_qw=awq_sources[prefill][47:16]; awq_qz=awq_sources[prefill][79:48];
      awq_scales=awq_sources[prefill][207:80]; awq_input=1;
      @(posedge clk);
      if(awq_ready !== 8'hff) $fatal(1,"AWQ_FRONTENDS_NOT_READY");
      @(negedge clk); awq_input=0;
      do @(posedge clk); while(awq_valid!=8'hff);
      if(awq_valid !== 8'hff || awq_error !== 0) $fatal(1,"AWQ_FRONTEND_OUTPUT_ERROR_X");
      vectors[prefill]={awq_sources[prefill][209:208],awq_weights,awq_sources[prefill][15:0]};
      for(j=0;j<8;j=j+1)
        $display("AWQ_CAPTURE %0d %0d %04h",prefill,j,awq_weights[j*16+:16]);
      @(negedge clk); awq_output_ready=1;
      @(posedge clk);
      @(negedge clk); awq_output_ready=0;
    end
    stream_active=1;
"""


def sources(fmt):
    rng = random.Random(89)
    length, offset = 1, 0
    for index in range(4096):
        if offset == length:
            length, offset = (1, 1, 2, 3, 17, 64)[index % 6], 0
        a = rng.getrandbits(16)
        qw, qz = rng.getrandbits(32), rng.getrandbits(32)
        scales = [rounded(Fraction((index + 3 * j) % 65, 128), fmt) for j in range(8)]
        if index % 37 == 0:
            scales[index % 8] = 0x8000
        yield (a | (qw << 16) | (qz << 48) |
               sum(scale << (80 + j * 16) for j, scale in enumerate(scales)) |
               (int(offset == 0) << 208) | (int(offset + 1 == length or index == 4095) << 209))
        offset += 1


def execute(fmt, repair_of=None):
    run = Run(f"verifier-awq-lane-{fmt}")
    if repair_of:
        run.receipt["repair_of"] = repair_of
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        vectors = list(sources(fmt))
        vector_file = run.path / "awq-sources.hex"
        vector_file.write_text("".join(f"{x:053x}\n" for x in vectors))
        text = LANE_BENCH.replace("  always #5 clk=~clk;",
                                 "  always #5 clk=~clk;\n" + DECLARATIONS)
        text = text.replace('$readmemh("VECTORS",vectors);',
                            f'$readmemh("{run.relative(vector_file)}",awq_sources);')
        text = text.replace("    rst_n=1;\n", "    rst_n=1;\n" + PREFILL)
        text = text.replace("if(rst_n) begin", "if(rst_n && stream_active) begin")
        text = text.replace("    cycle<=cycle+1;", "    if(stream_active) cycle<=cycle+1;")
        text = text.replace("{in_ready,out_valid,out_sum,out_last}",
                            "{in_ready,out_valid,out_sum,out_last,awq_ready,awq_valid,awq_error,awq_weights}")
        bench = run.path / "bench.sv"
        bench.write_text(with_time_zero_check(text))
        run.receipt["generated_sha256"] = {
            run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (vector_file, bench)}
        binary = run.path / "bench.vvp"
        run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                     f"-Ptb.FORMAT={int(fmt=='fp16')}", "-Ptb.COUNT=4096", "-o", run.relative(binary),
                     "rtl/anvil_q2_fp_00_pkg.sv", "rtl/anvil_q2_fp_awq_dequant.sv",
                     "rtl/anvil_q2_fp_scalar.sv", "rtl/anvil_q2_fp_dot_lane.sv",
                     run.relative(bench)], "compile")
        trace = run.command(["vvp", run.relative(binary)], "simulation")
        require_time_zero(trace)
        captured = set()
        for line in trace.read_text().splitlines():
            fields = line.split()
            if fields and fields[0] == "AWQ_CAPTURE":
                index, lane, bits = int(fields[1]), int(fields[2]), int(fields[3], 16)
                assert (index, lane) not in captured
                source = vectors[index]
                qw, qz = (source >> 16) & 0xFFFFFFFF, (source >> 48) & 0xFFFFFFFF
                scale = (source >> (80 + 16 * lane)) & 0xFFFF
                expected, error = awq_reference(qw, qz, scale, lane, fmt)
                assert not error and bits == expected, (
                    f"AWQ_LANE_WEIGHT_MISMATCH beat={index} lane={lane} "
                    f"got={bits:04x} expected={expected:04x}")
                captured.add((index, lane))
        assert len(captured) == 32768, "AWQ-fed lane coverage missing"
        metrics = compare_lane(trace, fmt, 4096)
        metrics.update(weight_mode="actual AWQ frontend outputs", dequantized_weights_compared=32768)
        run.finish("passed-focused-only", metrics=metrics)
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("bf16", "fp16"), default="bf16")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    raise SystemExit(execute(args.format, args.repair_of))
