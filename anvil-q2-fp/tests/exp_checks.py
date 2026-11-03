"""Public-pin bit-exact exponential checks and independent 100-digit error bound."""

import argparse
import hashlib
import random
import sys
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp_reference import exp_nonpositive, rounded, value
from retained import Run, require_time_zero, with_time_zero_check


BENCH = r"""
module tb;
  parameter COUNT=1;
  reg clk=0,rst_n,in_valid=0,out_ready=0;
  always #5 clk=~clk;
  reg [31:0] in_x=0;
  wire in_ready,out_valid,out_error;
  wire [31:0] out_data;
  reg [64:0] vectors[0:COUNT-1];
  reg [32:0] held;
  integer i,j,compared=0;
  anvil_q2_fp_exp dut(
    clk,rst_n,in_valid,in_ready,in_x,out_valid,out_ready,out_data,out_error);
  initial begin
    rst_n=0;
    $readmemh("VECTORS",vectors);
    #1;
    if({in_ready,out_valid,out_data,out_error} !== 0)
      $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk);
    rst_n=1;
    for(i=0;i<COUNT;i=i+1) begin
      @(negedge clk); in_x=vectors[i][31:0]; in_valid=1;
      do @(posedge clk); while(!in_ready);
      @(negedge clk); in_valid=0;
      do @(posedge clk); while(!out_valid);
      held={out_error,out_data};
      for(j=0;j<i%4+1;j=j+1) begin
        @(posedge clk);
        if(out_valid !== 1'b1 || {out_error,out_data} !== held)
          $fatal(1,"EXP_STALL_INSTABILITY");
      end
      @(negedge clk); out_ready=1;
      @(posedge clk);
      if({out_error,out_data} !== vectors[i][64:32])
        $fatal(1,"EXP_MISMATCH case=%0d x=%08h got=%08h error=%b expected=%08h error=%b",
          i,in_x,out_data,out_error,vectors[i][63:32],vectors[i][64]);
      $display("EXP %08h %08h %0d",in_x,out_data,out_error);
      compared=compared+1;
      @(negedge clk); out_ready=0;
    end
    $display("EXP_COMPARED %0d",compared);
    $finish;
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 && {in_ready,out_valid,out_data,out_error} !== 0)
      $fatal(1,"RESET_EDGE_NONZERO_X");
endmodule
"""


def cases():
    inputs = {0, 0x80000000, 0x80000001, 0x807FFFFF, 0x80800000,
              0xC2A00000, 0xC2A00001, 0xC29FFFFF}
    inputs.update(rounded(-Fraction(k, 32)) for k in range(2561))
    with localcontext() as ctx:
        ctx.prec = 100
        for n in range(116):
            transition = rounded(-Fraction((Decimal(n) + Decimal("0.5")) * Decimal(2).ln()))
            inputs.update((transition - 1, transition, transition + 1))
    for seed in (17, 43, 89):
        rng = random.Random(seed)
        inputs.update(rounded(-Fraction(rng.randrange(8000001), 100000))
                      for _ in range(128))
    for bits in sorted(inputs):
        yield bits, exp_nonpositive(bits), 0
    for bits in (0x3F800000, 0x00000001, 0x7F800000, 0xFF800000, 0x7FC00001):
        yield bits, 0x7FC00000, 1


def check_accuracy(trace):
    compared, bounded, rejected = 0, 0, 0
    maximum = Decimal(0)
    worst = None
    with localcontext() as ctx:
        ctx.prec = 100
        for line in trace.read_text().splitlines():
            parts = line.split()
            if not parts or parts[0] != "EXP":
                continue
            x, result, error = int(parts[1], 16), int(parts[2], 16), int(parts[3])
            compared += 1
            if error:
                rejected += 1
                continue
            rational = value(x)
            if not -80 <= rational <= 0:
                assert result == 0, "below-range exponential not zero"
                continue
            exact = (Decimal(rational.numerator) / Decimal(rational.denominator)).exp()
            actual = value(result)
            delta = abs(Decimal(actual.numerator) / Decimal(actual.denominator) - exact)
            assert delta <= Decimal("0.00001"), f"EXP_ACCURACY x={x:08x}: {delta}"
            if delta > maximum:
                maximum, worst = delta, f"{x:08x}"
            bounded += 1
    assert compared == len(list(cases())), "missing exponential comparisons"
    assert bounded > 2560 and rejected == 5, "exponential coverage absent"
    return {"bit_exact_compared": compared, "high_precision_compared": bounded,
            "rejections": rejected, "max_absolute_error": str(maximum),
            "worst_input": worst, "absolute_error_limit": "1e-5"}


def execute():
    run = Run("verifier-exp")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        vectors = list(cases())
        vector_path = run.path / "vectors.hex"
        vector_path.write_text("".join(
            f"{(error << 64) | (result << 32) | bits:017x}\n"
            for bits, result, error in vectors))
        bench = run.path / "bench.sv"
        bench.write_text(with_time_zero_check(BENCH.replace("VECTORS", run.relative(vector_path))))
        run.receipt["generated_sha256"] = {
            run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (vector_path, bench)}
        binary = run.path / "bench.vvp"
        run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                     f"-Ptb.COUNT={len(vectors)}", "-o", run.relative(binary),
                     "rtl/anvil_q2_fp_00_pkg.sv", "rtl/anvil_q2_fp_scalar.sv",
                     "rtl/anvil_q2_fp_exp.sv", run.relative(bench)], "compile")
        trace = run.command(["vvp", run.relative(binary)], "simulation")
        require_time_zero(trace)
        run.finish("passed-focused-only", metrics=check_accuracy(trace))
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    raise SystemExit(execute())
