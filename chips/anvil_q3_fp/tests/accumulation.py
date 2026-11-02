"""Exact masked, arbitrary-length dot reductions followed by registered FP32 sums."""

import random

from execution import compiled, relative, run_compiled
from ieee import binary, dot


LENGTHS = (1, 7, 8, 9, 31, 32, 63, 64, 65, 128)


def check(evidence, seed):
    rng = random.Random(seed)
    lines, totals = [], []
    packed = lambda values, width: sum(value << (width * lane) for lane, value in enumerate(values))
    for dtype, fmt in enumerate(("bf16", "fp16")):
        for awq in (0, 1):
            tiles = 0
            for row in range(256):
                length = LENGTHS[row % len(LENGTHS)]
                total = 0
                for base in range(0, length, 8):
                    count = min(8, length - base)
                    mask = (1 << count) - 1
                    activations = [rng.randrange(65536) for _ in range(8)]
                    weights = [rng.randrange(65536) for _ in range(8)]
                    q, z = [rng.randrange(16) for _ in range(8)], [rng.randrange(16) for _ in range(8)]
                    scales = [rng.randrange(0x7c00) for _ in range(8)]
                    if row % 7 == 0:
                        mask &= 0x55
                    reduced, dot_flags = dot(activations, weights, mask, fmt, q if awq else None, z, scales)
                    value, add_flags = binary("add", total, reduced)
                    lines.append(f"{dtype:x} {awq:x} {row:x} {length:x} {mask:02x} "
                                 f"{packed(activations,16):032x} {packed(weights,16):032x} "
                                 f"{packed(q,4):08x} {packed(z,4):08x} {packed(scales,16):032x} "
                                 f"{total:08x} {value:08x} {dot_flags | add_flags:02x}\n")
                    total = value
                    tiles += 1
            totals.append({"format": fmt, "awq": awq, "rows": 256, "tile_comparisons": tiles,
                           "lengths": list(LENGTHS)})
    executable = compiled(evidence, "masked-accumulation", TB, [
        "rtl/anvil_q3_fp_00_pkg.sv", "rtl/anvil_q3_fp_add.sv", "rtl/anvil_q3_fp_mul.sv",
        "rtl/anvil_q3_fp_dot8.sv"])
    output = run_compiled(evidence, executable, "masked-accumulation", {"vectors.txt": "".join(lines)})
    return {"seed": seed, "populations": totals, "stdout": relative(output)}


TB = """
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,in_valid=0,in_fp16=0,in_awq=0,out_ready=0;
  wire in_ready,dot_valid,dot_ready,dot_error,out_valid,out_error;
  reg [127:0] weight16=0,activation16=0,scale_f16=0;
  reg [31:0] q_nibbles=0,z_nibbles=0,base_sum=0;
  reg [7:0] lane_mask=0;
  reg loaded_fp16,loaded_awq;
  reg [127:0] loaded_weight,loaded_activation,loaded_scale;
  reg [31:0] loaded_q,loaded_z,loaded_base;
  reg [7:0] loaded_mask;
  wire [31:0] dot_sum,out_sum;
  wire [4:0] dot_flags,out_flags;
  anvil_q3_fp_dot8 reduction(.clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(in_valid),.in_ready(in_ready),.in_fp16(in_fp16),.in_awq(in_awq),
    .weight16(weight16),.activation16(activation16),.scale_f16(scale_f16),
    .q_nibbles(q_nibbles),.z_nibbles(z_nibbles),.lane_mask(lane_mask),
    .out_valid(dot_valid),.out_ready(dot_ready),.out_error(dot_error),
    .out_dot(dot_sum),.out_flags(dot_flags));
  anvil_q3_fp_vector #(.LANES(1),.MULTIPLY(0)) accumulator(
    .clk(clk),.rst_n(rst_n),.flush(flush),.in_valid(dot_valid),.in_ready(dot_ready),
    .in_a(base_sum),.in_b(dot_sum),.in_meta(1'b0),.in_flags(dot_flags),.in_error(dot_error),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(out_sum),.out_flags(out_flags),
    .out_error(out_error),.out_meta());
  integer fd,rc,row,length,cycle=0,accepted_cycle,comparisons=0,latency;
  reg [31:0] expected;
  reg [4:0] flags;
  reg held=0;
  reg [37:0] payload;
  task reset_check;
    begin
      if ({in_ready,dot_valid,dot_ready,dot_error,dot_sum,dot_flags,
          out_valid,out_error,out_sum,out_flags}!==0) $fatal(1,"RESET accumulation outputs");
    end
  endtask
  always @(posedge clk) begin
    if (!rst_n) reset_check;
    else begin
      if (held && (out_valid!==1'b1 || {out_error,out_flags,out_sum}!==payload))
        $fatal(1,"STALL accumulation");
      held=out_valid && !out_ready; payload={out_error,out_flags,out_sum};
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check;
    else begin cycle=cycle+1; out_ready=cycle<64 || cycle%11<7; end
  end
  initial begin
    rst_n=0;
    #0; reset_check;
    #1; reset_check;
    @(negedge clk); rst_n=1;
    fd=$fopen("vectors.txt","r");
    if (!fd) $fatal(1,"accumulation vectors");
    while (!$feof(fd)) begin
      @(negedge clk);
      rc=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h\\n",
        loaded_fp16,loaded_awq,row,length,loaded_mask,loaded_activation,loaded_weight,
        loaded_q,loaded_z,loaded_scale,loaded_base,expected,flags);
      if (rc!=13) $fatal(1,"accumulation vector");
      in_fp16=loaded_fp16; in_awq=loaded_awq; lane_mask=loaded_mask;
      activation16=loaded_activation; weight16=loaded_weight; scale_f16=loaded_scale;
      q_nibbles=loaded_q; z_nibbles=loaded_z; base_sum=loaded_base;
      in_valid=1;
      @(posedge clk);
      while (in_ready!==1'b1) @(posedge clk);
      accepted_cycle=cycle;
      @(negedge clk); in_valid=0;
      latency=0;
      @(posedge clk);
      while (!(out_valid && out_ready) && latency<512) begin
        @(posedge clk); latency=latency+1;
      end
      if (out_valid!==1'b1 || out_error!==1'b0 || {out_flags,out_sum}!=={flags,expected})
        $fatal(1,"ACCUM row=%0d length=%0d base=%h expected=%h/%h got=%h/%h",
          row,length,base_sum,flags,expected,out_flags,out_sum);
      if (accepted_cycle<32 && cycle-accepted_cycle!=15)
        $fatal(1,"LATENCY accumulated native path expected 15 got=%0d",cycle-accepted_cycle);
      comparisons=comparisons+1;
      @(negedge clk);
    end
    if (comparisons==0) $fatal(1,"missing accumulation comparisons");
    $display("COMPARED accumulated tiles=%0d",comparisons);
    $finish;
  end
endmodule
"""
