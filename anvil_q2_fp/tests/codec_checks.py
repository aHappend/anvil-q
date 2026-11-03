"""Independent exact-rational AWQ and block-codec public-interface checkers."""

import argparse
import hashlib
import random
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp_reference import classify, convert, multiply, rounded, rounded_integer, value
from retained import ROOT, Run, require_time_zero, with_time_zero_check


SHIFTS = (0, 16, 4, 20, 8, 24, 12, 28)


def awq_reference(qweight, qzero, scale, lane, fmt):
    if classify(scale, fmt) != "finite" or value(scale, fmt) < 0:
        return 0, True
    delta = ((qweight >> SHIFTS[lane]) & 15) - ((qzero >> SHIFTS[lane]) & 15)
    product = multiply(rounded(delta), convert(scale, fmt))
    result = convert(product, "fp32", fmt)
    return result, classify(result, fmt) != "finite"


def codec_reference(values, quantized, exponent, decode, fmt):
    lower, upper = (-139, 122) if fmt == "bf16" else (-30, 10)
    count = len(values)
    if decode:
        if not lower <= exponent <= upper:
            return [], [], exponent, True
        q = [b if b < 128 else b - 256 for b in quantized]
        if -128 in q:
            return [], [], exponent, True
    else:
        if any(classify(x, fmt) != "finite" for x in values):
            return [], [], 0, True
        x = [value(v, fmt) for v in values]
        maximum = max(map(abs, x))
        exponent = 0
        if maximum:
            exponent = lower
            while maximum > 127 * Fraction(2) ** exponent:
                exponent += 1
        if not lower <= exponent <= upper:
            return [], [], exponent, True
        q = [rounded_integer(v / Fraction(2) ** exponent) for v in x]
        assert all(-127 <= v <= 127 for v in q)
    reconstructed = [rounded(v * Fraction(2) ** exponent, fmt) for v in q]
    failed = any(classify(v, fmt) != "finite" for v in reconstructed)
    if not decode and not failed:
        # The independently rounded final-format error is not silently ignored.
        for original, quant, actual in zip(values, q, reconstructed):
            exact_reconstruction = quant * Fraction(2) ** exponent
            allowance = abs(value(actual, fmt) - exact_reconstruction)
            assert abs(value(original, fmt) - value(actual, fmt)) <= (
                Fraction(1, 2) * Fraction(2) ** exponent + allowance)
    assert len(reconstructed) == count
    return reconstructed, [v & 255 for v in q], exponent, failed


def awq_cases(fmt):
    rng = random.Random(89)
    scales = [rounded(Fraction(n, 32), fmt) for n in (0, 1, 3, 17, 127)]
    scales += [0x8000, 0xFFFF, 0x7F80 if fmt == "bf16" else 0x7C00,
               1, 0x7F7F if fmt == "bf16" else 0x7BFF]
    # Every signed delta and nibble position, including equal zero points.
    for lane in range(8):
        for q in range(16):
            for zero in range(16):
                qw, qz = rng.getrandbits(32), rng.getrandbits(32)
                mask = 15 << SHIFTS[lane]
                qw = (qw & ~mask) | (q << SHIFTS[lane])
                qz = (qz & ~mask) | (zero << SHIFTS[lane])
                scale = scales[(q + zero + lane) % len(scales)]
                result, error = awq_reference(qw, qz, scale, lane, fmt)
                yield qw, qz, scale, lane, result, int(error)


def codec_cases(fmt, block):
    rng = random.Random(17)
    samples = [
        [0] * block, [0x8000] * block, [1] * block,
        [rounded(Fraction((-1) ** j * (j + 1), 16), fmt) for j in range(block)],
        [rounded(127, fmt)] + [rounded(Fraction(1, 1024), fmt)] * (block - 1),
        [0x7F7F if fmt == "bf16" else 0x7BFF] * block,
        [0x7FC0 if fmt == "bf16" else 0x7E00] * block,
    ]
    for _ in range(128):
        samples.append([rounded(Fraction(rng.randint(-8192, 8192), 1024), fmt)
                        for _ in range(block)])
    for values in samples:
        yield False, values, [0] * block, 0, codec_reference(
            values, [0] * block, 0, False, fmt)
    # Exhaust all bytes, including the reserved -128, at every block geometry.
    for byte in range(256):
        q = [(byte + j) & 255 for j in range(block)]
        values = [0] * block
        yield True, values, q, -3, codec_reference(values, q, -3, True, fmt)
    lower, upper = (-139, 122) if fmt == "bf16" else (-30, 10)
    for exponent in (lower - 1, lower, upper, upper + 1, 0, 65535, -65536):
        for byte in (0, 1, 127, 129, 255):
            values, q = [0] * block, [byte] * block
            yield True, values, q, exponent, codec_reference(values, q, exponent, True, fmt)


AWQ_BENCH = r"""
module tb;
  parameter FORMAT=0, COUNT=1, INITIAL_LANE=0;
  reg clk=0,rst_n,in_valid=0,out_ready=0;
  always #5 clk=~clk;
  reg [31:0] qw=0,qz=0;
  reg [15:0] scale=0;
  reg [2:0] lane=INITIAL_LANE;
  wire in_ready,out_valid,out_error;
  wire [15:0] out_weight;
  reg [99:0] vectors[0:COUNT-1];
  reg [16:0] held;
  integer i,j,accepted=0,compared=0;
  anvil_q2_fp_awq_dequant #(FORMAT) dut(
    clk,rst_n,in_valid,in_ready,qw,qz,scale,lane,
    out_valid,out_ready,out_weight,out_error);
  initial begin
    rst_n=0;
    $readmemh("VECTORS",vectors);
    #1;
    if({in_ready,out_valid,out_error,out_weight} !== 0) $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk);
    rst_n=1;
    for(i=0;i<COUNT;i=i+1) begin
      @(negedge clk);
      {qw,qz,scale,lane}=vectors[i][82:0];
      in_valid=1;
      do @(posedge clk); while(!in_ready);
      $display("AWQ_INPUT %0d %08h %08h %04h %0d",i,qw,qz,scale,lane);
      accepted=accepted+1;
      @(negedge clk); in_valid=0;
      do @(posedge clk); while(!out_valid);
      held={out_error,out_weight};
      for(j=0;j<i%3+1;j=j+1) begin
        @(posedge clk);
        if(out_valid !== 1'b1 || {out_error,out_weight} !== held)
          $fatal(1,"AWQ_STALL_INSTABILITY");
      end
      @(negedge clk); out_ready=1;
      @(posedge clk);
      if(out_error !== vectors[i][99] ||
         (!vectors[i][99] && out_weight !== vectors[i][98:83]))
        $fatal(1,"AWQ_MISMATCH case=%0d got=%04h error=%b expected=%04h error=%b",
               i,out_weight,out_error,vectors[i][98:83],vectors[i][99]);
      compared=compared+1;
      @(negedge clk); out_ready=0;
    end
    $display("AWQ_COMPARED %0d %0d",accepted,compared);
    $finish;
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 && {in_ready,out_valid,out_error,out_weight} !== 0)
      $fatal(1,"RESET_EDGE_NONZERO_X");
endmodule
"""


CODEC_BENCH = r"""
module tb;
  parameter FORMAT=0,BLOCK=16,COUNT=1;
  localparam INPUT_BITS=1+BLOCK*24+32;
  localparam OUTPUT_BITS=BLOCK*24+32+1;
  localparam TOTAL=INPUT_BITS+OUTPUT_BITS;
  reg clk=0,rst_n,in_valid=0,out_ready=0;
  always #5 clk=~clk;
  reg decode=0;
  reg [BLOCK*16-1:0] values=0;
  reg [BLOCK*8-1:0] bytes_in=0;
  reg [31:0] exponent=0;
  wire in_ready,out_valid,out_error;
  wire [BLOCK*16-1:0] out_values;
  wire [BLOCK*8-1:0] out_bytes;
  wire [31:0] out_exponent;
  reg [TOTAL-1:0] vectors[0:COUNT-1];
  reg [OUTPUT_BITS-1:0] held;
  reg expected_error;
  reg [BLOCK*16-1:0] expected_values;
  reg [BLOCK*8-1:0] expected_bytes;
  reg [31:0] expected_exponent;
  integer i,j,accepted=0,compared=0,rejections=0;
  anvil_q2_fp_cache_codec #(.FP_FORMAT(FORMAT),.CACHE_BLOCK(BLOCK)) dut(
    clk,rst_n,in_valid,in_ready,decode,values,bytes_in,exponent,
    out_valid,out_ready,out_values,out_bytes,out_exponent,out_error);
  initial begin
    rst_n=0;
    $readmemh("VECTORS",vectors);
    #1;
    if({in_ready,out_valid,out_error,out_values,out_bytes,out_exponent} !== 0)
      $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk); rst_n=1;
    for(i=0;i<COUNT;i=i+1) begin
      @(negedge clk);
      {decode,values,bytes_in,exponent}=vectors[i][INPUT_BITS-1:0];
      {expected_error,expected_values,expected_bytes,expected_exponent}=
        vectors[i][TOTAL-1:INPUT_BITS];
      in_valid=1;
      do @(posedge clk); while(!in_ready);
      accepted=accepted+1;
      @(negedge clk); in_valid=0;
      do @(posedge clk); while(!out_valid);
      held={out_error,out_values,out_bytes,out_exponent};
      for(j=0;j<i%3+1;j=j+1) begin
        @(posedge clk);
        if(out_valid !== 1'b1 ||
           {out_error,out_values,out_bytes,out_exponent} !== held)
          $fatal(1,"CODEC_STALL_INSTABILITY");
      end
      @(negedge clk); out_ready=1;
      @(posedge clk);
      if(out_error !== expected_error ||
         (!expected_error && {out_values,out_bytes,out_exponent} !==
                              {expected_values,expected_bytes,expected_exponent}))
        $fatal(1,"CODEC_MISMATCH case=%0d decode=%b exponent=%08h got_error=%b expected_error=%b got_exp=%08h expected_exp=%08h got_values=%h expected_values=%h got_bytes=%h expected_bytes=%h",
          i,decode,exponent,out_error,expected_error,out_exponent,expected_exponent,
          out_values,expected_values,out_bytes,expected_bytes);
      compared=compared+1;
      if(expected_error) rejections=rejections+1;
      @(negedge clk); out_ready=0;
    end
    if(rejections==0) $fatal(1,"REJECTION_COVERAGE_MISSING");
    $display("CODEC_COMPARED %0d %0d %0d",accepted,compared,rejections);
    $finish;
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 &&
       {in_ready,out_valid,out_error,out_values,out_bytes,out_exponent} !== 0)
      $fatal(1,"RESET_EDGE_NONZERO_X");
endmodule
"""


def pack_components(values, bits):
    return sum(v << (bits * i) for i, v in enumerate(values))


def fixtures(case, fmt, block):
    if case == "awq":
        vectors = []
        for qw, qz, scale, lane, result, error in awq_cases(fmt):
            inputs = (qw << 51) | (qz << 19) | (scale << 3) | lane
            vectors.append((error << 99) | (result << 83) | inputs)
        return vectors, AWQ_BENCH, 25, ["anvil_q2_fp_scalar.sv", "anvil_q2_fp_awq_dequant.sv"]
    vectors = []
    input_bits = 1 + block * 24 + 32
    for decode, values, quantized, exponent, expected in codec_cases(fmt, block):
        result, q, e, error = expected
        inputs = ((int(decode) << (block * 24 + 32)) |
                  (pack_components(values, 16) << (block * 8 + 32)) |
                  (pack_components(quantized, 8) << 32) | (exponent & 0xFFFFFFFF))
        outputs = ((int(error) << (block * 24 + 32)) |
                   (pack_components(result, 16) << (block * 8 + 32)) |
                   (pack_components(q, 8) << 32) | (e & 0xFFFFFFFF))
        vectors.append((outputs << input_bits) | inputs)
    return vectors, CODEC_BENCH, (2 * input_bits + 3) // 4, ["anvil_q2_fp_cache_codec.sv"]


def execute(case, fmt, block, initial_lane=0, diagnosis_of=None):
    run = Run(f"verifier-{case}-{fmt}-block{block}")
    if diagnosis_of:
        run.receipt["diagnosis_of"] = diagnosis_of
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        vectors, template, width, modules = fixtures(case, fmt, block)
        vector_path = run.path / "vectors.hex"
        vector_path.write_text("".join(f"{v:0{width}x}\n" for v in vectors))
        bench = run.path / "bench.sv"
        bench.write_text(with_time_zero_check(template.replace("VECTORS", run.relative(vector_path))))
        run.receipt["generated_sha256"] = {
            run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (vector_path, bench)}
        binary = run.path / "bench.vvp"
        run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                     f"-Ptb.COUNT={len(vectors)}", f"-Ptb.FORMAT={int(fmt == 'fp16')}",
                     *([f"-Ptb.INITIAL_LANE={initial_lane}"] if case == "awq" else []),
                     *([f"-Ptb.BLOCK={block}"] if case == "codec" else []),
                     "-o", run.relative(binary), "rtl/anvil_q2_fp_00_pkg.sv",
                     *[f"rtl/{module}" for module in modules], run.relative(bench)], "compile")
        trace = run.command(["vvp", run.relative(binary)], "simulation")
        require_time_zero(trace)
        assert f"{case.upper()}_COMPARED {len(vectors)} {len(vectors)}" in trace.read_text()
        run.finish("passed-focused-only", metrics={"commands_compared": len(vectors)})
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("awq", "codec"), required=True)
    parser.add_argument("--format", choices=("bf16", "fp16"), default="bf16")
    parser.add_argument("--block", type=int, choices=(1, 2, 16), default=16)
    parser.add_argument("--initial-lane", type=int, choices=(0, 7), default=0)
    parser.add_argument("--diagnosis-of")
    args = parser.parse_args()
    return execute(args.case, args.format, args.block, args.initial_lane, args.diagnosis_of)


if __name__ == "__main__":
    raise SystemExit(main())
