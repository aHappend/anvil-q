"""Independent public-interface arithmetic and streaming-lane experiments."""

import argparse
import hashlib
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp_reference import add, classify, convert, divide, multiply, square_root
from retained import ROOT, Run, require_time_zero, with_time_zero_check


SCALAR_BENCH = r"""
module tb;
  parameter COUNT=1;
  reg clk=0, rst_n, in_valid=0, out_ready=0;
  always #5 clk=~clk;
  reg [2:0] in_op=0;
  reg [31:0] in_a=0,in_b=0;
  wire in_ready,out_valid,out_error;
  wire [31:0] out_data;
  reg [98:0] vectors[0:COUNT-1];
  reg [31:0] held;
  reg held_error;
  integer i,j,cycles=0,accepted=0,retired=0;
  anvil_q2_fp_scalar dut(clk,rst_n,in_valid,in_ready,in_op,in_a,in_b,
                         out_valid,out_ready,out_data,out_error);
  initial begin
    rst_n=0;
    $readmemh("VECTORS",vectors);
    #1;
    if({in_ready,out_valid,out_data,out_error} !== 0) $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk);
    rst_n=1;
    for(i=0;i<COUNT;i=i+1) begin
      @(negedge clk);
      {in_op,in_a,in_b}=vectors[i][66:0];
      in_valid=1;
      do @(posedge clk); while(!in_ready);
      accepted=accepted+1;
      @(negedge clk);
      in_valid=0;
      do @(posedge clk); while(!out_valid);
      held=out_data; held_error=out_error;
      for(j=0;j<(i%4)+1;j=j+1) begin
        @(posedge clk);
        if(out_valid !== 1'b1 || out_data !== held || out_error !== held_error)
          $fatal(1,"SCALAR_STALL_INSTABILITY");
      end
      @(negedge clk);
      out_ready=1;
      @(posedge clk);
      if(out_data !== vectors[i][98:67] ||
         out_error !== (&vectors[i][97:90]))
        $fatal(1,"SCALAR_MISMATCH case=%0d op=%0d a=%08h b=%08h got=%08h expected=%08h",
               i,in_op,in_a,in_b,out_data,vectors[i][98:67]);
      retired=retired+1;
      @(negedge clk);
      out_ready=0;
    end
    $display("SCALAR_COMPARED %0d %0d",accepted,retired);
    $finish;
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 && {in_ready,out_valid,out_data,out_error} !== 0)
      $fatal(1,"RESET_EDGE_NONZERO_X");
  always @(posedge clk) cycles<=cycles+1;
endmodule
"""


LANE_BENCH = r"""
module tb;
  parameter FORMAT=0, COUNT=4096;
  reg clk=0,rst_n;
  always #5 clk=~clk;
  reg out_ready=0;
  wire in_ready,out_valid,out_last;
  wire [255:0] out_sum;
  reg [145:0] vectors[0:COUNT-1];
  integer index=0,cycle=0,retired=0;
  reg input_valid=0, was_stalled=0;
  reg [256:0] held;
  wire in_valid=input_valid && index<COUNT;
  wire [145:0] beat=index<COUNT ? vectors[index] : 146'd0;
  anvil_q2_fp_dot_lane #(FORMAT) dut(
    clk,rst_n,in_valid,in_ready,beat[15:0],beat[143:16],beat[144],beat[145],
    out_valid,out_ready,out_sum,out_last);
  initial begin
    rst_n=0;
    $readmemh("VECTORS",vectors);
    #1;
    if({in_ready,out_valid,out_sum,out_last} !== 0) $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk);
    rst_n=1;
  end
  always @(negedge clk) begin
    if(rst_n) begin
      // The first 64 beats are an uninterrupted latency/II experiment.
      out_ready=cycle<70 || ((cycle%11)!=3 && (cycle%11)!=4 && (cycle%11)!=5);
      if(!in_valid || in_ready)
        input_valid=cycle<70 || ((cycle%7)!=2 && (cycle%7)!=3);
    end
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 && {in_ready,out_valid,out_sum,out_last} !== 0)
      $fatal(1,"RESET_EDGE_NONZERO_X");
  always @(posedge clk) begin
    cycle<=cycle+1;
    if(rst_n) begin
      if((^{in_ready,out_valid}) === 1'bx) $fatal(1,"ACTIVE_CONTROL_X");
      if(was_stalled && {out_last,out_sum} !== held)
        $fatal(1,"LANE_STALL_INSTABILITY");
      if(was_stalled && out_valid !== 1'b1) $fatal(1,"LANE_STALL_VALID");
      was_stalled<=out_valid && !out_ready;
      held<={out_last,out_sum};
      if(in_valid && in_ready) begin
        $display("IN %0d %0d %037h",cycle,index,beat);
        index<=index+1;
      end
      if(out_valid && out_ready) begin
        if((^{out_last,out_sum}) === 1'bx) $fatal(1,"ACTIVE_OUTPUT_X");
        $display("OUT %0d %0d %064h",cycle,out_last,out_sum);
        retired<=retired+1;
        if(retired+1==COUNT) begin
          if(index!=COUNT) $fatal(1,"EARLY_COMPLETION");
          $display("LANE_COMPARED %0d %0d",index,retired+1);
          $finish;
        end
      end
    end
  end
endmodule
"""


def scalar_vectors():
    rng = random.Random(17)
    directed = [
        0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x00800000,
        0x3F800000, 0xBF800000, 0x3F800001, 0x3F7FFFFF,
        0x33800000, 0x33C00000, 0x7F7FFFFF, 0xFF7FFFFF,
        0x7F800000, 0xFF800000, 0x7FC00001, 0x7F800001,
    ]
    operations = (add, multiply, divide, lambda a, b: square_root(a))
    for op, function in enumerate(operations):
        pairs = [(a, b) for a in directed for b in directed]
        pairs += [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(512)]
        for a, b in pairs:
            yield (function(a, b) << 67) | (op << 64) | (a << 32) | b


def lane_vectors(fmt, count=4096):
    rng = random.Random(43)
    special = ([0, 0x8000, 1, 0x8001, 0x007F, 0x0080, 0x3F80, 0xBF80,
                0x7F7F, 0xFF7F, 0x7F80, 0xFF80, 0x7FC1, 0x3F81]
               if fmt == "bf16" else
               [0, 0x8000, 1, 0x8001, 0x03FF, 0x0400, 0x3C00, 0xBC00,
                0x7BFF, 0xFBFF, 0x7C00, 0xFC00, 0x7E01, 0x3C01])
    length, offset = 1, 0
    for index in range(count):
        if offset == length:
            length = [1, 1, 2, 3, 17, 64][index % 6]
            offset = 0
        first, last = offset == 0, offset + 1 == length or index + 1 == count
        a = special[index % len(special)] if index < 256 else rng.getrandbits(16)
        weights = [special[(index + 3 * j) % len(special)] if index < 256
                   else rng.getrandbits(16) for j in range(8)]
        yield a | sum(w << (16 + j * 16) for j, w in enumerate(weights)) | (
            int(first) << 144) | (int(last) << 145)
        offset += 1


def compare_lane(trace, fmt, count):
    from collections import deque
    pending = deque()
    accumulator = [0] * 8
    accepted = retired = exact_latency = consecutive_outputs = 0
    last_output_cycle = None
    for line in trace.read_text().splitlines():
        words = line.split()
        if words[0] == "IN":
            cycle, index, beat = int(words[1]), int(words[2]), int(words[3], 16)
            assert index == accepted
            if (beat >> 144) & 1:
                accumulator = [0] * 8
            a = convert(beat & 0xFFFF, fmt)
            for j in range(8):
                b = convert((beat >> (16 + 16 * j)) & 0xFFFF, fmt)
                accumulator[j] = add(accumulator[j], multiply(a, b))
            expected = sum(s << (32 * j) for j, s in enumerate(accumulator))
            pending.append((cycle, expected, (beat >> 145) & 1))
            accepted += 1
        elif words[0] == "OUT":
            assert pending, "uncommanded lane output"
            cycle, last, result = int(words[1]), int(words[2]), int(words[3], 16)
            issued, expected, expected_last = pending.popleft()
            assert result == expected and last == expected_last, (
                f"LANE_MISMATCH beat={retired} observed={result:064x} "
                f"expected={expected:064x} last={last}/{expected_last}")
            assert cycle - issued >= 3, "early lane output"
            if issued < 65:
                assert cycle - issued == 3, "three-capture latency violation"
                exact_latency += 1
                if last_output_cycle is not None:
                    assert cycle == last_output_cycle + 1, "initiation interval not one"
                    consecutive_outputs += 1
                last_output_cycle = cycle
            retired += 1
    assert accepted == retired == count and not pending, "unconsumed lane beats"
    assert exact_latency >= 32 and consecutive_outputs >= 31, "latency/II coverage absent"
    return {"accepted": accepted, "retired": retired, "scalar_results_compared": count * 8,
            "exact_latency_beats": exact_latency, "consecutive_output_pairs": consecutive_outputs}


def execute(case, fmt):
    run = Run(f"verifier-{case}-{fmt}")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        if case in ("scalar", "add"):
            vectors = [v for v in scalar_vectors()
                       if case == "scalar" or ((v >> 64) & 7) == 0]
            bench_text, width = SCALAR_BENCH, 25
            if case == "add":
                bench_text = bench_text.replace(
                    "anvil_q2_fp_scalar dut(clk,rst_n,in_valid,in_ready,in_op,in_a,in_b,",
                    "anvil_q2_fp_add dut(clk,rst_n,in_valid,in_ready,in_a,in_b,")
        else:
            vectors = list(lane_vectors(fmt))
            bench_text, width = LANE_BENCH, 37
        vector_path = run.path / "vectors.hex"
        vector_path.write_text("".join(f"{v:0{width}x}\n" for v in vectors))
        bench = run.path / "bench.sv"
        bench.write_text(with_time_zero_check(bench_text.replace("VECTORS", run.relative(vector_path))))
        run.receipt["generated_sha256"] = {
            run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (vector_path, bench)}
        binary = run.path / "bench.vvp"
        module = {"scalar": "anvil_q2_fp_scalar.sv", "add": "anvil_q2_fp_add.sv",
                  "lane": "anvil_q2_fp_dot_lane.sv"}[case]
        run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                     f"-Ptb.COUNT={len(vectors)}",
                     *([f"-Ptb.FORMAT={int(fmt == 'fp16')}"] if case == "lane" else []),
                     "-o", run.relative(binary), "rtl/anvil_q2_fp_00_pkg.sv",
                     f"rtl/{module}", run.relative(bench)], "compile")
        trace = run.command(["vvp", run.relative(binary)], "simulation")
        require_time_zero(trace)
        if case in ("scalar", "add"):
            assert f"SCALAR_COMPARED {len(vectors)} {len(vectors)}" in trace.read_text()
            metrics = {"accepted": len(vectors), "results_compared": len(vectors)}
        else:
            metrics = compare_lane(trace, fmt, len(vectors))
        run.finish("passed-focused-only", metrics=metrics)
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("scalar", "add", "lane"), required=True)
    parser.add_argument("--format", choices=("bf16", "fp16"), default="bf16")
    args = parser.parse_args()
    return execute(args.case, args.format)


if __name__ == "__main__":
    raise SystemExit(main())
