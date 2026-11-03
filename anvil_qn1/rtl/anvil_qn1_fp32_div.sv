module anvil_qn1_fp32_div (
  input wire clk, rst_n, flush, start,
  input wire [31:0] numerator, denominator,
  input wire in_error,
  output wire ready, done,
  output wire [31:0] result,
  output wire out_error
);
  import anvil_qn1_pkg::*;
  wire [23:0] raw_a = {numerator[30:23] != 0,numerator[22:0]};
  wire [23:0] raw_b = {denominator[30:23] != 0,denominator[22:0]};
  wire [5:0] shift_a = raw_a == 0 ? 6'd0 : leading_zero32({8'd0,raw_a})-6'd8;
  wire [5:0] shift_b = raw_b == 0 ? 6'd0 : leading_zero32({8'd0,raw_b})-6'd8;
  wire [23:0] normalized_a = raw_a << shift_a;
  wire [23:0] normalized_b = raw_b << shift_b;
  wire below_one = normalized_a < normalized_b;
  wire [24:0] initial_numerator = below_one ?
    {normalized_a,1'b0} : {1'b0,normalized_a};
  wire signed [11:0] exponent_a =
    (numerator[30:23] == 0 ? -12'sd126 :
     $signed({4'd0,numerator[30:23]})-12'sd127)-$signed({6'd0,shift_a});
  wire signed [11:0] exponent_b =
    (denominator[30:23] == 0 ? -12'sd126 :
     $signed({4'd0,denominator[30:23]})-12'sd127)-$signed({6'd0,shift_b});
  reg active, done_reg, negative, failed, zero;
  reg [5:0] cycle;
  reg [23:0] divisor;
  reg [24:0] remainder;
  reg [26:0] quotient;
  reg signed [11:0] exponent;
  reg [31:0] value, rounded_value;
  reg result_failed, rounded_failed;
  wire [25:0] trial = {remainder,1'b0};
  wire take_bit = trial >= {2'd0,divisor};
  wire [25:0] next_remainder = take_bit ? trial-{2'd0,divisor} : trial;
  wire [26:0] sticky_quotient = {quotient[26:1],quotient[0] | (|remainder)};
  wire [32:0] packed_result = round_pack32(negative,exponent,
    zero ? 27'd0 : sticky_quotient);
  assign ready = rst_n && !flush && !active;
  assign done = rst_n && !flush && done_reg;
  assign result = rst_n && !flush ? value : 32'd0;
  assign out_error = rst_n && !flush && result_failed;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active <= 0; done_reg <= 0; negative <= 0; failed <= 0; zero <= 0;
      cycle <= 0; divisor <= 0; remainder <= 0; quotient <= 0; exponent <= 0;
      value <= 0; result_failed <= 0; rounded_value <= 0; rounded_failed <= 0;
    end else if (flush) begin
      active <= 0; done_reg <= 0; value <= 0; result_failed <= 0;
    end else begin
      done_reg <= 0;
      if (start && ready) begin
        active <= 1; cycle <= 1;
        divisor <= normalized_b;
        remainder <= initial_numerator-{1'b0,normalized_b};
        quotient <= 27'd1;
        exponent <= exponent_a-exponent_b-(below_one ? 12'sd1 : 12'sd0);
        negative <= numerator[31] ^ denominator[31];
        zero <= raw_a == 0;
        failed <= in_error || fp32_invalid(numerator) ||
          fp32_invalid(denominator) || raw_b == 0;
      end else if (active) begin
        cycle <= cycle+1'b1;
        if (cycle <= 26) begin
          remainder <= next_remainder[24:0];
          quotient <= {quotient[25:0],take_bit};
        end else if (cycle == 27) begin
          rounded_value <= failed || packed_result[32] ? 32'd0 : packed_result[31:0];
          rounded_failed <= failed || packed_result[32];
        end else if (cycle == 33) begin
          value <= rounded_value; result_failed <= rounded_failed;
          active <= 0; done_reg <= 1;
        end
      end
    end
  end
endmodule
