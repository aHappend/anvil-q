module anvil_q1_ht3_fp32_mul (
  input wire clk, rst_n, enable, in_valid,
  input wire [31:0] in_a, in_b,
  output wire out_valid,
  output wire [31:0] out_data
);
  import anvil_q1_ht3_fp_pkg::*;
  wire run_n;
  reg [3:0] valid_pipe;
  reg [31:0] a0, b0;
  reg sign1, special1, sign2, special2;
  reg [31:0] special_data1, special_data2, data3;
  reg [47:0] product1;
  reg signed [10:0] scale1, exponent2;
  reg [24:0] rounded2;
  wire [23:0] mantissa_a = {(|a0[30:23]), a0[22:0]};
  wire [23:0] mantissa_b = {(|b0[30:23]), b0[22:0]};
  wire invalid_product = fp32_nan(a0) || fp32_nan(b0) ||
    (fp32_nonfinite(a0) && b0[30:0] == 0) ||
    (fp32_nonfinite(b0) && a0[30:0] == 0);
  wire signed [10:0] scale_a = a0[30:23] == 0 ? -11'sd149 :
    $signed({3'b0, a0[30:23]}) - 11'sd150;
  wire signed [10:0] scale_b = b0[30:23] == 0 ? -11'sd149 :
    $signed({3'b0, b0[30:23]}) - 11'sd150;
  wire [5:0] product_leading = leading_bit64({16'b0, product1});
  wire signed [10:0] product_exponent =
    scale1 + $signed({5'b0, product_leading});
  wire signed [10:0] rounding_shift = product_exponent < -11'sd126 ?
    -11'sd149 - scale1 : $signed({5'b0, product_leading}) - 11'sd23;
  wire [63:0] rounded_product =
    shift_rne64({16'b0, product1}, int'(rounding_shift));
  wire signed [10:0] adjusted_exponent =
    exponent2 + (rounded2[24] ? 11'sd1 : 11'sd0);
  wire [24:0] adjusted_fraction =
    rounded2[24] ? rounded2 >> 1 : rounded2;
  wire [7:0] normal_exponent = 8'(adjusted_exponent + 11'sd127);
  reg [31:0] encoded_product;

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  assign out_valid = run_n && valid_pipe[3];
  assign out_data = out_valid ? data3 : 32'b0;

  always @* begin
    encoded_product = {sign2, 31'b0};
    if (special2) encoded_product = special_data2;
    else if (exponent2 > 11'sd127)
      encoded_product = {sign2, 8'hff, 23'b0};
    else if (rounded2 != 0) begin
      if (exponent2 < -11'sd126)
        encoded_product = {sign2, 7'b0, rounded2[23], rounded2[22:0]};
      else if (adjusted_exponent > 11'sd127)
        encoded_product = {sign2, 8'hff, 23'b0};
      else
        encoded_product = {sign2, normal_exponent, adjusted_fraction[22:0]};
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 0;
      a0 <= 0;
      b0 <= 0;
      sign1 <= 0;
      special1 <= 0;
      special_data1 <= 0;
      product1 <= 0;
      scale1 <= 0;
      sign2 <= 0;
      special2 <= 0;
      special_data2 <= 0;
      exponent2 <= 0;
      rounded2 <= 0;
      data3 <= 0;
    end else if (run_n && enable) begin
      valid_pipe <= {valid_pipe[2:0], in_valid};
      a0 <= in_a;
      b0 <= in_b;
      sign1 <= a0[31] ^ b0[31];
      special1 <= invalid_product || fp32_nonfinite(a0) || fp32_nonfinite(b0);
      if (invalid_product) special_data1 <= FP32_QNAN;
      else special_data1 <= {a0[31] ^ b0[31], 8'hff, 23'b0};
      product1 <= mantissa_a * mantissa_b;
      scale1 <= scale_a + scale_b;
      sign2 <= sign1;
      special2 <= special1;
      special_data2 <= special_data1;
      exponent2 <= product_exponent;
      rounded2 <= rounded_product[24:0];
      data3 <= encoded_product;
    end
  end
endmodule
