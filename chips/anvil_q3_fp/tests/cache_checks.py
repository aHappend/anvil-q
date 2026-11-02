"""Streaming cache codec public-pin comparisons, including malformed inputs."""

from fractions import Fraction
import random

from cache_reference import decode, encode
from execution import icarus, verilator
from ieee import pack


def check(evidence, seed=17, exhaustive=False):
    results = []
    rng = random.Random(seed)
    for mode, fp8, affine in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 0, 0), (2, 0, 1)):
        cases = []
        maximum = 32 if mode == 1 else 64
        for dtype, fmt in enumerate(("bf16", "fp16")):
            groups = []
            if mode == 0 and exhaustive:
                groups += [list(range(start, start + 64)) for start in range(0, 65536, 64)]
            for count in (1, 2, 7, 8, 15, 16, 31, 32, 33, 63, 64):
                if count > maximum:
                    continue
                groups += [[pack(Fraction(rng.randrange(-127, 128), 32), fmt)[0] for _ in range(count)],
                           [0, 0x8000] * (count // 2) + ([0] if count % 2 else []),
                           [pack(Fraction(3, 32), fmt)[0]] * count,
                           [pack(Fraction(-3, 32), fmt)[0]] * count]
            for values in groups:
                words = encode(values, fmt, mode, fp8, affine)
                decoded = decode(words, len(values), fmt, mode, fp8, affine)
                cases += [(0, dtype, len(values), values, words, 0),
                          (1, dtype, len(values), words, decoded, 0)]
            if mode:
                finite = [pack(Fraction(i - 3, 8), fmt)[0] for i in range(7)]
                good = encode(finite, fmt, mode, fp8, affine)
                for mask in (1 << 24, 1 << 20, 1 << 22, 1 << 21):
                    bad = list(good)
                    bad[0] ^= mask
                    cases.append((1, dtype, 7, bad, [], 1))
                bad = list(good)
                width = 8 if mode == 1 else 4
                bad[-1] |= 1 << (32 - width)
                cases.append((1, dtype, 7, bad, [], 1))
                cases.append((0, dtype, 1, [0x7c00 if dtype else 0x7f80], [], 1))
            else:
                cases.append((1, dtype, 1, [0x10000], [], 1))
        lines = []
        for decoding, dtype, count, inputs, outputs, error in cases:
            lines.append(f"{decoding} {dtype} {count} {len(inputs)} {len(outputs)} {error}\n")
            lines.extend(f"{word:08x}\n" for word in inputs + outputs)
        tb = CACHE_TB.replace("@MODE@", str(mode)).replace("@FP8@", str(fp8)).replace("@AFFINE@", str(affine))
        runner = verilator if exhaustive else icarus
        runner(evidence, f"cache-m{mode}-f{fp8}-a{affine}", tb,
               ["rtl/anvil_q3_fp_00_pkg.sv", "rtl/anvil_q3_fp_cache_codec.sv"],
               {"vectors.txt": "".join(lines)})
        results.append({"mode": mode, "fp8": fp8, "affine": affine, "commands": len(cases),
                        "compared_output_words": sum(len(case[4]) for case in cases),
                        "negative_commands": sum(case[5] for case in cases)})
    return results


CACHE_TB = """
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,cmd_valid=0,cmd_decode=0,cmd_fp16=0;
  reg [6:0] cmd_count=0;
  wire cmd_ready,done,error,in_ready,out_valid,out_last;
  reg in_valid=0,in_last=0,out_ready=0;
  reg [31:0] in_data=0;
  wire [31:0] out_data;
  anvil_q3_fp_cache_codec #(.CACHE_MODE(@MODE@),.MODE1_FP8(@FP8@),.INT4_ASYM(@AFFINE@)) dut(.*);
  integer fd,rc,decode_command,dtype,count,ninput,noutput,expected_error,ni,no,latency;
  integer commands=0,compared=0,negative=0,stalls=0,cycle=0;
  reg [31:0] inputs[0:63],expected[0:63],hold_data;
  reg hold_last,held=0;
  task reset_check;
    begin
      if ({cmd_ready,done,error,in_ready,out_valid,out_last,out_data}!==38'd0)
        $fatal(1,"RESET nonzero/X codec outputs");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check;
  initial begin
    rst_n=0;
    #0; reset_check;
    #1; reset_check;
    @(negedge clk); rst_n=1;
    fd=$fopen("vectors.txt","r");
    if (!fd) $fatal(1,"vector open");
    while (!$feof(fd)) begin
      rc=$fscanf(fd,"%d %d %d %d %d %d\\n",decode_command,dtype,count,ninput,noutput,expected_error);
      if (rc!=6) $fatal(1,"malformed cache command");
      for (ni=0;ni<ninput;ni=ni+1) begin
        rc=$fscanf(fd,"%h\\n",inputs[ni]); if (rc!=1) $fatal(1,"input vector");
      end
      for (no=0;no<noutput;no=no+1) begin
        rc=$fscanf(fd,"%h\\n",expected[no]); if (rc!=1) $fatal(1,"output vector");
      end
      while (cmd_ready!==1'b1) @(negedge clk);
      cmd_decode=decode_command; cmd_fp16=dtype; cmd_count=count; cmd_valid=1;
      @(negedge clk); cmd_valid=0;
      ni=0; no=0; latency=0; held=0;
      while (done!==1'b1 && latency<4096) begin
        in_valid=ni<ninput;
        in_data=in_valid ? inputs[ni] : 32'd0;
        in_last=ni+1==ninput;
        out_ready=cycle%7<4;
        @(posedge clk);
        if (held && (out_valid!==1'b1 || {out_last,out_data}!=={hold_last,hold_data}))
          $fatal(1,"STALL codec payload changed");
        held=out_valid && !out_ready; hold_data=out_data; hold_last=out_last;
        if (held) stalls=stalls+1;
        if (in_valid && in_ready) ni=ni+1;
        if (out_valid && out_ready) begin
          if (no>=noutput || out_data!==expected[no] || out_last!==(no+1==noutput))
            $fatal(1,"CACHE cmd=%0d decode=%d dtype=%d count=%d word=%0d expected=%h got=%h last=%b",
              commands,decode_command,dtype,count,no,expected[no],out_data,out_last);
          no=no+1; compared=compared+1;
        end
        @(negedge clk);
        latency=latency+1; cycle=cycle+1;
      end
      in_valid=0; out_ready=0;
      if (done!==1'b1 || error!==1'(expected_error) || no!=noutput)
        $fatal(1,"CACHE completion cmd=%0d expected_error=%0d done=%b error=%b outputs=%0d/%0d inputs=%0d/%0d",
          commands,expected_error,done,error,no,noutput,ni,ninput);
      negative=negative+expected_error; commands=commands+1;
      @(negedge clk);
      if (done!==1'b0) $fatal(1,"codec done not a pulse");
    end
    if (commands==0 || compared==0 || negative==0 || stalls==0) $fatal(1,"missing codec comparison coverage");
    $display("COMPARED cache commands=%0d words=%0d negative=%0d stalls=%0d",commands,compared,negative,stalls);
    $finish;
  end
endmodule
"""
