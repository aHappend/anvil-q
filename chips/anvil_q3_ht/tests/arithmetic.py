"""Exhaustive binary16 conversion and directed final-rounding comparisons."""

import random

from model import half_scale, half_signed, rounded_shift


ARITHMETIC_TB = r"""
module verify_arithmetic;
  reg [65:0] expected_half [0:65535];
  reg [127:0] round_input [0:@LAST@];
  reg [31:0] round_expected [0:@LAST@];
  reg [7:0] round_shift [0:@LAST@];
  reg [65:0] actual_half;
  reg [4:0] shifts [0:7];
  integer i;
  initial begin
    $readmemh("@HALF@",expected_half);
    $readmemh("@ROUND_INPUT@",round_input);
    $readmemh("@ROUND_EXPECTED@",round_expected);
    $readmemh("@ROUND_SHIFT@",round_shift);
    shifts[0]=0; shifts[1]=16; shifts[2]=4; shifts[3]=20;
    shifts[4]=8; shifts[5]=24; shifts[6]=12; shifts[7]=28;
    for (i=0;i<8;i=i+1)
      if (anvil_q3_pkg::awq_lane_shift(3'(i)) !== shifts[i])
        $fatal(1,"AWQ_LANE_MAPPING lane=%0d",i);
    for (i=0;i<65536;i=i+1) begin
      actual_half={anvil_q3_pkg::f16_invalid(16'(i)),
                   anvil_q3_pkg::f16_scale_invalid(16'(i)),
                   anvil_q3_pkg::f16_q16(16'(i)),anvil_q3_pkg::f16_scale(16'(i))};
      if (actual_half !== expected_half[i])
        $fatal(1,"BINARY16_CONVERSION bits=%h actual=%h expected=%h",16'(i),actual_half,expected_half[i]);
    end
    for (i=0;i<=@LAST@;i=i+1) begin
      if (anvil_q3_pkg::round_shift_sat32($signed(round_input[i]),32'(round_shift[i]))
          !== round_expected[i])
        $fatal(1,"SIGNED_ROUNDING case=%0d shift=%0d input=%0d expected=%0d",
               i,round_shift[i],$signed(round_input[i]),$signed(round_expected[i]));
      if (round_shift[i]==16 &&
          anvil_q3_pkg::round_q32_to_q16($signed(round_input[i])) !== round_expected[i])
        $fatal(1,"FINAL_Q16_ROUNDING case=%0d",i);
    end
    $display("ARITHMETIC_PASS half_patterns=65536 awq_lanes=8 rounded=@COUNT@");
    $finish;
  end
endmodule
"""


def arithmetic_bench(directory, relative):
    half = directory / "binary16-reference.hex"
    with half.open("w") as stream:
        for bits in range(65536):
            try:
                signed, invalid = half_signed(bits), False
            except ValueError:
                signed, invalid = 0, True
            try:
                scale, invalid_scale = half_scale(bits), False
            except ValueError:
                scale, invalid_scale = 0, True
            reference = (scale | ((signed & 0xFFFFFFFF) << 32)
                         | (int(invalid_scale) << 64) | (int(invalid) << 65))
            stream.write(f"{reference:017x}\n")
    vectors = []
    rng = random.Random(17)
    for shift in (0, 16, 24, 30, 48):
        half_step = (1 << (shift - 1)) if shift else 0
        for integral in (0, 1, 2, 7, (1 << 31) - 2, (1 << 31) - 1, 1 << 31):
            for delta in (-1, 0, 1):
                magnitude = max(0, (integral << shift) + half_step + delta)
                for sign in (-1, 1):
                    vectors.append((sign * magnitude, shift))
        vectors.extend((rng.randrange(-(1 << 100), 1 << 100), shift) for _ in range(256))
    bench = ARITHMETIC_TB.replace("@LAST@", str(len(vectors) - 1))
    bench = bench.replace("@COUNT@", str(len(vectors))).replace("@HALF@", relative(half))
    for name, width, values in (
            ("round_input", 128, [value for value, _ in vectors]),
            ("round_shift", 8, [shift for _, shift in vectors]),
            ("round_expected", 32, [rounded_shift(value, shift) for value, shift in vectors])):
        path = directory / f"{name}.hex"
        path.write_text("".join(f"{value & ((1 << width) - 1):0{width // 4}x}\n"
                                for value in values))
        bench = bench.replace(f"@{name.upper()}@", relative(path))
    return bench
