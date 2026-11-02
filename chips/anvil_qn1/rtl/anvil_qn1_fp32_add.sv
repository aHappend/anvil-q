module anvil_qn1_fp32_add (
  input wire clk, rst_n, flush, ce,
  input wire [31:0] a, b,
  input wire in_error,
  output wire [31:0] result,
  output wire out_error
);
  import anvil_qn1_pkg::*;
  wire a_larger = a[30:0] >= b[30:0];
  wire [31:0] large_value = a_larger ? a : b;
  wire [31:0] small_value = a_larger ? b : a;
  wire signed [11:0] large_exponent = large_value[30:23] == 0 ?
    -12'sd126 : $signed({4'd0,large_value[30:23]})-12'sd127;
  wire signed [11:0] small_exponent = small_value[30:23] == 0 ?
    -12'sd126 : $signed({4'd0,small_value[30:23]})-12'sd127;
  reg [26:0] large1, small1, large2, small2;
  reg [11:0] distance1;
  reg signed [11:0] exponent1, exponent2, exponent3, exponent4;
  reg negative1, negative2, negative3, negative4;
  reg subtract1, subtract2;
  reg [27:0] sum3;
  reg [26:0] significand4;
  reg [4:0] failed;
  reg [31:0] value5;
  reg error5;
  wire [27:0] sum_next = subtract2 ?
    {1'b0,large2}-{1'b0,small2} : {1'b0,large2}+{1'b0,small2};
  wire [5:0] left_shift = sum3 == 0 ? 6'd0 :
    leading_zero32({4'd0,sum3})-6'd5;
  wire [32:0] packed5 = round_pack32(negative4, exponent4, significand4);

  assign result = rst_n && !flush ? value5 : 32'd0;
  assign out_error = rst_n && !flush && error5;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      large1 <= 0; small1 <= 0; large2 <= 0; small2 <= 0; distance1 <= 0;
      exponent1 <= 0; exponent2 <= 0; exponent3 <= 0; exponent4 <= 0;
      negative1 <= 0; negative2 <= 0; negative3 <= 0; negative4 <= 0;
      subtract1 <= 0; subtract2 <= 0; sum3 <= 0; significand4 <= 0;
      failed <= 0; value5 <= 0; error5 <= 0;
    end else if (flush) begin
      large1 <= 0; small1 <= 0; large2 <= 0; small2 <= 0; distance1 <= 0;
      exponent1 <= 0; exponent2 <= 0; exponent3 <= 0; exponent4 <= 0;
      negative1 <= 0; negative2 <= 0; negative3 <= 0; negative4 <= 0;
      subtract1 <= 0; subtract2 <= 0; sum3 <= 0; significand4 <= 0;
      failed <= 0; value5 <= 0; error5 <= 0;
    end else if (ce) begin
      large1 <= {large_value[30:23] != 0,large_value[22:0],3'd0};
      small1 <= {small_value[30:23] != 0,small_value[22:0],3'd0};
      exponent1 <= large_exponent;
      distance1 <= $unsigned(large_exponent-small_exponent);
      negative1 <= large_value[31];
      subtract1 <= a[31] ^ b[31];
      failed <= {failed[3:0],in_error || fp32_invalid(a) || fp32_invalid(b)};
      large2 <= large1;
      small2 <= shift_jam27(small1,distance1);
      exponent2 <= exponent1; negative2 <= negative1; subtract2 <= subtract1;
      sum3 <= sum_next;
      exponent3 <= exponent2;
      negative3 <= sum_next == 0 && subtract2 ? 1'b0 : negative2;
      if (sum3[27]) begin
        significand4 <= {sum3[27:2],sum3[1] | sum3[0]};
        exponent4 <= exponent3 + 1'b1;
      end else begin
        significand4 <= sum3[26:0] << left_shift;
        exponent4 <= exponent3-$signed({6'd0,left_shift});
      end
      negative4 <= negative3;
      value5 <= failed[3] || packed5[32] ? 32'd0 : packed5[31:0];
      error5 <= failed[3] || packed5[32];
    end
  end
endmodule
