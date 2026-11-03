module anvil_q1_ht2_fp16_mul (
  input wire clk, rst_n, enable, in_valid, in_fp16,
  input wire [15:0] in_a, in_b,
  output wire out_valid,
  output wire [31:0] out_data
);
  import anvil_q1_ht2_fp_pkg::*;
  reg [2:0] valid_pipe;
  reg [15:0] a0, b0;
  reg fp16_0;
  reg sign1, special1;
  reg [31:0] special_data1;
  reg [21:0] product1;
  reg signed [10:0] scale1;
  reg [31:0] data2;
  wire [10:0] mantissa_a = fp16_0 ?
    {(|a0[14:10]), a0[9:0]} : {3'b0, (|a0[14:7]), a0[6:0]};
  wire [10:0] mantissa_b = fp16_0 ?
    {(|b0[14:10]), b0[9:0]} : {3'b0, (|b0[14:7]), b0[6:0]};
  wire a_inf = fp16_0 ? a0[14:10] == 5'h1f && a0[9:0] == 0 :
                                       a0[14:7] == 8'hff && a0[6:0] == 0;
  wire b_inf = fp16_0 ? b0[14:10] == 5'h1f && b0[9:0] == 0 :
                                       b0[14:7] == 8'hff && b0[6:0] == 0;
  wire a_nan = fp16_0 ? a0[14:10] == 5'h1f && a0[9:0] != 0 :
                                       a0[14:7] == 8'hff && a0[6:0] != 0;
  wire b_nan = fp16_0 ? b0[14:10] == 5'h1f && b0[9:0] != 0 :
                                       b0[14:7] == 8'hff && b0[6:0] != 0;
  wire invalid_product = a_nan || b_nan ||
    (a_inf && b0[14:0] == 0) || (b_inf && a0[14:0] == 0);
  wire signed [10:0] scale_a = fp16_0 ?
    (a0[14:10] == 0 ? -11'sd24 : $signed({6'b0,a0[14:10]}) - 11'sd25) :
    (a0[14:7] == 0 ? -11'sd133 : $signed({3'b0,a0[14:7]}) - 11'sd134);
  wire signed [10:0] scale_b = fp16_0 ?
    (b0[14:10] == 0 ? -11'sd24 : $signed({6'b0,b0[14:10]}) - 11'sd25) :
    (b0[14:7] == 0 ? -11'sd133 : $signed({3'b0,b0[14:7]}) - 11'sd134);
  wire [31:0] rounded_product =
    pack32(sign1, {42'b0, product1}, int'(scale1));

  assign out_valid = rst_n && valid_pipe[2];
  assign out_data = out_valid ? data2 : 32'b0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 0;
      a0 <= 0;
      b0 <= 0;
      fp16_0 <= 0;
      sign1 <= 0;
      special1 <= 0;
      special_data1 <= 0;
      product1 <= 0;
      scale1 <= 0;
      data2 <= 0;
    end else if (enable) begin
      valid_pipe <= {valid_pipe[1:0], in_valid};
      a0 <= in_a;
      b0 <= in_b;
      fp16_0 <= in_fp16;
      sign1 <= a0[15] ^ b0[15];
      special1 <= invalid_product || a_inf || b_inf;
      if (invalid_product) special_data1 <= FP32_QNAN;
      else special_data1 <= {a0[15] ^ b0[15], 8'hff, 23'b0};
      product1 <= mantissa_a * mantissa_b;
      scale1 <= scale_a + scale_b;
      if (special1) data2 <= special_data1;
      else data2 <= rounded_product;
    end
  end
endmodule
