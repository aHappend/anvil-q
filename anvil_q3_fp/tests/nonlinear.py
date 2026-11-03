"""FP64 mathematical bounds for public exponential and stable SiLU units."""

import math
import random

from execution import relative, verilator
from ieee import binary, bits_float, canonical, classify, exact, float_bits


def check(evidence, seed=17, count=4096):
    rng = random.Random(seed)
    exp_inputs = [0, 0x80000000, 0x80000001, 0x807fffff, 0xbf800000,
                  float_bits(-80), float_bits(-80) + 1, 0xff800000,
                  0x3f800000, 0x7f800000, 0x7fc00000, 0x7f800001]
    exp_inputs += [float_bits(-80 * rng.random()) for _ in range(count)]
    silu_inputs = [0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x807fffff,
                   0x7f7fffff, 0xff7fffff, 0x7f800000, 0xff800000, 0x7fc00000, 0x7f800001]
    silu_inputs += [float_bits(160 * rng.random() - 80) for _ in range(count)]
    results = []
    for operation, values in (("exp", exp_inputs), ("silu", silu_inputs)):
        text = "".join(f"{value:08x}\n" for value in values)
        tb = NONLINEAR_TB.replace("@MODULE@", f"anvil_q3_fp_{operation}")
        rtl = ["rtl/anvil_q3_fp_00_pkg.sv", "rtl/anvil_q3_fp_add.sv", "rtl/anvil_q3_fp_mul.sv",
               "rtl/anvil_q3_fp_exp.sv", "rtl/anvil_q3_fp_divider.sv", "rtl/anvil_q3_fp_silu.sv"]
        output = verilator(evidence, operation, tb, rtl, {"vectors.txt": text})
        samples = []
        for line in (evidence.path / operation / "results.txt").read_text().splitlines():
            fields = line.split()
            if len(fields) != 4:
                raise AssertionError(f"Malformed nonlinear result: {line}")
            samples.append(tuple(int(field, 16) for field in fields))
        if len(samples) != len(values):
            raise AssertionError(f"Missing nonlinear results: {len(samples)}/{len(values)}")
        maximum_error, finite_count, special_count = 0.0, 0, 0
        for index, (source, result, error, latency) in enumerate(samples):
            if source != values[index] or latency > (1024 if operation == "exp" else 1152):
                raise AssertionError(f"{operation}: transaction/latency mismatch at {index}")
            kind, sign, _ = classify(source)
            actual = bits_float(result)
            if operation == "exp":
                domain_error = kind == "nan" or (not sign and kind != "zero")
                if error != domain_error:
                    raise AssertionError(f"exp input-domain error mismatch x={source:08x}")
                if domain_error:
                    if result != canonical():
                        raise AssertionError("exp invalid-input NaN is not canonical")
                    special_count += 1
                    continue
                if kind == "zero":
                    if result != 0x3f800000:
                        raise AssertionError("exp(+-0) is not exactly one")
                elif not math.isfinite(actual) or not 0 <= actual <= 1:
                    raise AssertionError(f"exp out of range x={source:08x} result={result:08x}")
                value = bits_float(source)
                expected = math.exp(value)
                tolerance = 2 ** -23 + 2 ** -15 * expected
                if value >= -80 and abs(actual - expected) > tolerance:
                    raise AssertionError(f"EXP_BOUND x={source:08x} expected={expected} actual={actual} bound={tolerance}")
                if value < -80 and actual != 0 and abs(actual - expected) > tolerance:
                    raise AssertionError(f"exp out-of-range mathematical result x={source:08x}")
                maximum_error = max(maximum_error, abs(actual - expected))
            else:
                if error:
                    raise AssertionError(f"SiLU unexpectedly reports protocol error x={source:08x}")
                if kind in ("nan", "inf", "zero"):
                    expected = canonical() if kind == "nan" else 0x80000000 if kind == "inf" and sign else source
                    if result != expected:
                        raise AssertionError(f"SILU_LIMIT x={source:08x} expected={expected:08x} actual={result:08x}")
                    special_count += 1
                    continue
                x = bits_float(source)
                exponential = math.exp(-abs(x))
                delta = (2 ** -23 + 2 ** -15 * exponential) if abs(x) <= 80 else 0.0
                exp_low, exp_high = max(0.0, exponential - delta), min(1.0, exponential + delta)
                e_low, e_high = float_bits(exp_low), float_bits(exp_high)
                den_low = binary("add", 0x3f800000, e_low)[0]
                den_high = binary("add", 0x3f800000, e_high)[0]
                numerators = ([source] if not sign else
                              [binary("mul", source, e)[0] for e in (e_low, e_high)])
                bounds = [exact(binary("div", n, d)[0]) for n in numerators for d in (den_low, den_high)]
                if not math.isfinite(actual) or not min(bounds) <= exact(result) <= max(bounds):
                    raise AssertionError(f"SILU_BOUND x={source:08x} actual={result:08x} interval={min(bounds)}..{max(bounds)}")
                expected = x / (1 + exponential) if x >= 0 else x * exponential / (1 + exponential)
                maximum_error = max(maximum_error, abs(actual - expected))
            finite_count += 1
        results.append({"operation": operation, "transactions": len(samples),
                        "finite_comparisons": finite_count, "special_comparisons": special_count,
                        "maximum_absolute_math_error": maximum_error, "stdout": relative(output)})
    return results


NONLINEAR_TB = """
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,start=0;
  reg [31:0] x=0;
  reg [31:0] loaded_x;
  wire ready,done,error;
  wire [31:0] value;
  @MODULE@ dut(.*);
  integer fd,outfile,rc,count=0,latency;
  task reset_check;
    begin
      if ({ready,done,error,value}!==35'd0) $fatal(1,"RESET nonlinear outputs");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check;
  initial begin
    rst_n=0;
    #0; reset_check;
    #1; reset_check;
    @(negedge clk); rst_n=1;
    fd=$fopen("vectors.txt","r"); outfile=$fopen("results.txt","w");
    if (!fd || !outfile) $fatal(1,"nonlinear files");
    while (!$feof(fd)) begin
      while (ready!==1'b1) @(negedge clk);
      rc=$fscanf(fd,"%h\\n",loaded_x);
      if (rc!=1) $fatal(1,"nonlinear input");
      // Explicit assignment keeps compiled-simulator input sensitivities live.
      x=loaded_x;
      start=1;
      @(negedge clk); start=0;
      latency=0;
      while (done!==1'b1 && latency<1152) begin @(negedge clk); latency=latency+1; end
      if (done!==1'b1) $fatal(1,"nonlinear progress bound x=%h",x);
      $fdisplay(outfile,"%h %h %h %h",x,value,error,latency);
      count=count+1;
      @(negedge clk);
      if (done!==1'b0) $fatal(1,"nonlinear done not pulse");
    end
    $fclose(outfile);
    if (count==0) $fatal(1,"no nonlinear transactions");
    $display("COMPARED nonlinear transactions=%0d",count);
    $finish;
  end
endmodule
"""
