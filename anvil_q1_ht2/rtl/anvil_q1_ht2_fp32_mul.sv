module anvil_q1_ht2_fp32_mul (
  input wire clk, rst_n, enable, in_valid,
  input wire [31:0] in_a, in_b,
  output wire out_valid,
  output wire [31:0] out_data
);
  import anvil_q1_ht2_fp_pkg::*;
  reg [2:0] valid_pipe;
  reg [31:0] a0, b0;
  reg sign1, special1;
  reg [31:0] special_data1, data2;
  reg [47:0] product1;
  reg signed [10:0] scale1;
  wire [23:0] mantissa_a = {(|a0[30:23]), a0[22:0]};
  wire [23:0] mantissa_b = {(|b0[30:23]), b0[22:0]};
  wire invalid_product = fp32_nan(a0) || fp32_nan(b0) ||
    (fp32_nonfinite(a0) && b0[30:0] == 0) ||
    (fp32_nonfinite(b0) && a0[30:0] == 0);
  wire signed [10:0] scale_a = a0[30:23] == 0 ? -11'sd149 :
                                             $signed({3'b0, a0[30:23]}) - 11'sd150;
  wire signed [10:0] scale_b = b0[30:23] == 0 ? -11'sd149 :
                                             $signed({3'b0, b0[30:23]}) - 11'sd150;
  wire [31:0] rounded_product = pack32(sign1, {16'b0, product1}, int'(scale1));
  assign out_valid = rst_n && valid_pipe[2];
  assign out_data = out_valid ? data2 : 32'b0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 0;
      a0 <= 0;
      b0 <= 0;
      sign1 <= 0;
      special1 <= 0;
      special_data1 <= 0;
      data2 <= 0;
      product1 <= 0;
      scale1 <= 0;
    end else if (enable) begin
      valid_pipe <= {valid_pipe[1:0], in_valid};
      a0 <= in_a;
      b0 <= in_b;
      sign1 <= a0[31] ^ b0[31];
      special1 <= invalid_product || fp32_nonfinite(a0) || fp32_nonfinite(b0);
      if (invalid_product) special_data1 <= FP32_QNAN;
      else special_data1 <= {a0[31] ^ b0[31], 8'hff, 23'b0};
      product1 <= mantissa_a * mantissa_b;
      scale1 <= scale_a + scale_b;
      if (special1) data2 <= special_data1;
      else data2 <= rounded_product;
    end
  end
endmodule
