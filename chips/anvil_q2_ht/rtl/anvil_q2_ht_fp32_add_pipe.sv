module anvil_q2_ht_fp32_add_pipe (
  input wire clk, rst_n, advance,
  input wire [31:0] a, b,
  output wire [31:0] sum,
  output wire error
);
  import anvil_q2_ht_fp_pkg::*;
  reg [26:0] large1, small1;
  reg [8:0] exponent1;
  reg sign1, subtract1, error1;
  reg [27:0] magnitude2;
  reg [8:0] exponent2;
  reg sign2, error2;
  reg [26:0] significand3;
  reg [9:0] exponent3;
  reg sign3, error3;
  reg [31:0] result4;
  reg error4;

  wire invalid_a = a[30:23] == 8'hff;
  wire invalid_b = b[30:23] == 8'hff;
  wire [31:0] finite_a = invalid_a ? 32'd0 : a;
  wire [31:0] finite_b = invalid_b ? 32'd0 : b;
  wire a_larger = finite_a[30:0] >= finite_b[30:0];
  wire [31:0] large_operand = a_larger ? finite_a : finite_b;
  wire [31:0] small_operand = a_larger ? finite_b : finite_a;
  wire [8:0] large_exponent = large_operand[30:23] == 0 ?
    9'd1 : {1'b0,large_operand[30:23]};
  wire [8:0] small_exponent = small_operand[30:23] == 0 ?
    9'd1 : {1'b0,small_operand[30:23]};
  wire [26:0] large_significand =
    {(|large_operand[30:23]),large_operand[22:0],3'b0};
  wire [26:0] small_significand =
    {(|small_operand[30:23]),small_operand[22:0],3'b0};
  wire [8:0] align_distance = large_exponent-small_exponent;
  wire [5:0] leading_distance = leading32({magnitude2[26:0],5'd0});
  wire [8:0] available_shift = exponent2-9'd1;
  wire [8:0] normalize_distance = {3'd0,leading_distance} < available_shift ?
    {3'd0,leading_distance} : available_shift;
  wire [32:0] packed_result = pack_fp32(sign3,exponent3,significand3);

  assign sum = rst_n ? result4 : 32'd0;
  assign error = rst_n && error4;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      large1 <= 0; small1 <= 0; exponent1 <= 0;
      sign1 <= 0; subtract1 <= 0; error1 <= 0;
      magnitude2 <= 0; exponent2 <= 0; sign2 <= 0; error2 <= 0;
      significand3 <= 0; exponent3 <= 0; sign3 <= 0; error3 <= 0;
      result4 <= 0; error4 <= 0;
    end else if (advance) begin
      large1 <= large_significand;
      small1 <= right_jam27(small_significand,align_distance);
      exponent1 <= large_exponent;
      sign1 <= large_operand[31];
      subtract1 <= large_operand[31] != small_operand[31];
      error1 <= invalid_a || invalid_b;

      if (subtract1) magnitude2 <= {1'b0,large1}-{1'b0,small1};
      else magnitude2 <= {1'b0,large1}+{1'b0,small1};
      exponent2 <= exponent1;
      if (subtract1 && large1 == small1) sign2 <= 0;
      else sign2 <= sign1;
      error2 <= error1;

      sign3 <= sign2;
      error3 <= error2;
      if (magnitude2[27]) begin
        significand3 <= {magnitude2[27:2],|magnitude2[1:0]};
        exponent3 <= {1'b0,exponent2}+10'd1;
      end else if (magnitude2 == 0) begin
        significand3 <= 0;
        exponent3 <= 1;
      end else begin
        significand3 <= magnitude2[26:0] << normalize_distance;
        exponent3 <= {1'b0,exponent2}-{1'b0,normalize_distance};
      end

      result4 <= packed_result[31:0];
      error4 <= error3 || packed_result[32];
    end
  end
endmodule
