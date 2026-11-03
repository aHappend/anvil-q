module anvil_qn1_fp32_mul (
  input wire clk, rst_n, flush, ce,
  input wire [31:0] a, b,
  input wire in_error,
  output wire [31:0] result,
  output wire out_error
);
  import anvil_qn1_pkg::*;
  wire [23:0] raw_a = {a[30:23] != 0, a[22:0]};
  wire [23:0] raw_b = {b[30:23] != 0, b[22:0]};
  wire [5:0] shift_a = raw_a == 0 ? 6'd0 : leading_zero32({8'd0,raw_a})-6'd8;
  wire [5:0] shift_b = raw_b == 0 ? 6'd0 : leading_zero32({8'd0,raw_b})-6'd8;
  wire signed [11:0] exponent_a =
    (a[30:23] == 0 ? -12'sd126 : $signed({4'd0,a[30:23]})-12'sd127) -
    $signed({6'd0,shift_a});
  wire signed [11:0] exponent_b =
    (b[30:23] == 0 ? -12'sd126 : $signed({4'd0,b[30:23]})-12'sd127) -
    $signed({6'd0,shift_b});
  reg [23:0] mantissa_a1, mantissa_b1;
  reg signed [11:0] exponent_a1, exponent_b1, exponent2, exponent3;
  reg [47:0] product2;
  reg [26:0] significand3;
  reg [3:0] negative, failed;
  reg [31:0] value4;
  reg error4;
  wire [32:0] packed4 = round_pack32(negative[2], exponent3, significand3);

  assign result = rst_n && !flush ? value4 : 32'd0;
  assign out_error = rst_n && !flush && error4;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mantissa_a1 <= 0; mantissa_b1 <= 0;
      exponent_a1 <= 0; exponent_b1 <= 0; exponent2 <= 0; exponent3 <= 0;
      product2 <= 0; significand3 <= 0; negative <= 0; failed <= 0;
      value4 <= 0; error4 <= 0;
    end else if (flush) begin
      mantissa_a1 <= 0; mantissa_b1 <= 0;
      exponent_a1 <= 0; exponent_b1 <= 0; exponent2 <= 0; exponent3 <= 0;
      product2 <= 0; significand3 <= 0; negative <= 0; failed <= 0;
      value4 <= 0; error4 <= 0;
    end else if (ce) begin
      mantissa_a1 <= raw_a << shift_a;
      mantissa_b1 <= raw_b << shift_b;
      exponent_a1 <= exponent_a;
      exponent_b1 <= exponent_b;
      negative <= {negative[2:0], a[31] ^ b[31]};
      failed <= {failed[2:0], in_error || fp32_invalid(a) || fp32_invalid(b)};
      product2 <= mantissa_a1 * mantissa_b1;
      exponent2 <= exponent_a1 + exponent_b1;
      if (product2[47]) begin
        significand3 <= {product2[47:22], product2[21] | (|product2[20:0])};
        exponent3 <= exponent2 + 1'b1;
      end else begin
        significand3 <= {product2[46:21], product2[20] | (|product2[19:0])};
        exponent3 <= exponent2;
      end
      value4 <= failed[2] || packed4[32] ? 32'd0 : packed4[31:0];
      error4 <= failed[2] || packed4[32];
    end
  end
endmodule
