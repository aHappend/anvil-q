"""Asynchronous reset at every public three-stage lane occupancy."""

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run, require_time_zero, with_time_zero_check


BENCH = r"""
module tb;
  parameter FORMAT=0;
  reg clk=0,rst_n,in_valid=0,out_ready=0,first=0,last=0;
  always #5 clk=~clk;
  wire in_ready,out_valid,out_last;
  wire [255:0] out_sum;
  wire [15:0] one=FORMAT==0 ? 16'h3f80 : 16'h3c00;
  integer fill,j,cycle=0,issued=0,accepted=0,retired=0,aborted=0,compared=0;
  anvil_q2_fp_dot_lane #(FORMAT) dut(
    clk,rst_n,in_valid,in_ready,one,{8{one}},first,last,
    out_valid,out_ready,out_sum,out_last);
  initial begin
    rst_n=0;
    #1;
    if({in_ready,out_valid,out_sum,out_last} !== 0) $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk); rst_n=1;
    for(fill=0;fill<=3;fill=fill+1) begin
      for(j=0;j<fill;j=j+1) begin
        @(negedge clk); in_valid=1; first=j==0; last=0;
        @(posedge clk);
        if(in_ready !== 1'b1) $fatal(1,"LANE_OCCUPANCY_NOT_REACHED");
      end
      @(negedge clk); in_valid=0;
      if((fill==3 && (out_valid !== 1'b1 || out_sum !== {8{32'h3f800000}})) ||
         (fill<3 && out_valid !== 1'b0)) $fatal(1,"LANE_PUBLIC_OCCUPANCY_MISMATCH");
      #1; rst_n=0; aborted=aborted+fill;
      #1;
      if({in_ready,out_valid,out_sum,out_last} !== 0) $fatal(1,"OCCUPIED_ASYNC_RESET_X");
      repeat(2) @(negedge clk); rst_n=1;
      @(negedge clk); in_valid=1; first=1; last=1;
      @(posedge clk);
      if(in_ready !== 1'b1) $fatal(1,"RESET_RECOVERY_NOT_READY");
      issued=cycle;
      @(negedge clk); in_valid=0;
      do @(posedge clk); while(!out_valid);
      if(cycle-issued!=3 || out_last !== 1'b1 || out_sum !== {8{32'h3f800000}})
        $fatal(1,"LANE_RESET_RECOVERY_NUMERICAL_OR_LATENCY");
      repeat(3) begin
        @(posedge clk);
        if(out_valid !== 1'b1 || out_last !== 1'b1 || out_sum !== {8{32'h3f800000}})
          $fatal(1,"RESET_RECOVERY_STALL_INSTABILITY");
      end
      @(negedge clk); out_ready=1;
      @(posedge clk);
      if(out_valid !== 1'b1 || out_sum !== {8{32'h3f800000}})
        $fatal(1,"RESET_RECOVERY_HANDSHAKE");
      compared=compared+1;
      @(negedge clk);
      repeat(8) begin
        @(posedge clk);
        if(out_valid !== 1'b0) $fatal(1,"STALE_LANE_OUTPUT_AFTER_RESET");
      end
      @(negedge clk); out_ready=0;
    end
    #1;
    if(accepted!=retired+aborted || retired!=4 || aborted!=6 || compared!=4)
      $fatal(1,"LANE_RESET_EPOCH_ACCOUNTING");
    $display("LANE_LIFECYCLE_COMPARED %0d %0d %0d %0d",accepted,retired,aborted,compared);
    $finish;
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 && {in_ready,out_valid,out_sum,out_last} !== 0)
      $fatal(1,"RESET_EDGE_NONZERO_X");
  always @(posedge clk) begin
    cycle<=cycle+1;
    if(rst_n) begin
      if((^{in_ready,out_valid}) === 1'bx) $fatal(1,"LANE_LIFECYCLE_CONTROL_X");
      if(in_valid && in_ready) accepted=accepted+1;
      if(out_valid && out_ready) retired=retired+1;
    end
  end
endmodule
"""


def execute(fmt):
    run = Run(f"verifier-lane-lifecycle-{fmt}")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        bench = run.path / "bench.sv"
        bench.write_text(with_time_zero_check(BENCH))
        run.receipt["generated_sha256"] = {
            run.relative(bench): hashlib.sha256(bench.read_bytes()).hexdigest()}
        binary = run.path / "bench.vvp"
        run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                     f"-Ptb.FORMAT={int(fmt=='fp16')}", "-o", run.relative(binary),
                     "rtl/anvil_q2_fp_00_pkg.sv", "rtl/anvil_q2_fp_dot_lane.sv",
                     run.relative(bench)], "compile")
        trace = run.command(["vvp", run.relative(binary)], "simulation")
        require_time_zero(trace)
        assert "LANE_LIFECYCLE_COMPARED 10 4 6 4" in trace.read_text()
        run.finish("passed-focused-only", metrics={
            "occupancies_checked": [0, 1, 2, 3], "accepted": 10,
            "retired_and_compared": 4, "explicitly_reset_abandoned": 6})
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("bf16", "fp16"), default="bf16")
    raise SystemExit(execute(parser.parse_args().format))
