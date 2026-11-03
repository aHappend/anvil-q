module anvil_q3_fp_add (
  input wire clk, rst_n, flush, in_valid,
  input wire [31:0] in_a, in_b,
  input wire out_ready,
  output wire in_ready, out_valid,
  output wire [31:0] out_data,
  output wire [4:0] out_flags
);
  import anvil_q3_fp_pkg::*;

  reg valid0, valid1, valid2;
  wire ready2 = !valid2 || out_ready;
  wire ready1 = !valid1 || ready2;
  wire ready0 = !valid0 || ready1;
  wire a_larger = in_a[30:0] >= in_b[30:0];
  wire [31:0] large_operand = a_larger ? in_a : in_b;
  wire [31:0] small_operand = a_larger ? in_b : in_a;
  wire [7:0] large_exponent =
    large_operand[30:23] == 0 ? 8'd1 : large_operand[30:23];
  wire [7:0] small_exponent =
    small_operand[30:23] == 0 ? 8'd1 : small_operand[30:23];
  wire [9:0] alignment = {2'd0,large_exponent}-{2'd0,small_exponent};
  wire [26:0] large_sig =
    {large_operand[30:23] != 0,large_operand[22:0],3'd0};
  wire [26:0] small_sig =
    {small_operand[30:23] != 0,small_operand[22:0],3'd0};
  wire opposite_infinities = is_inf32(in_a) && is_inf32(in_b) &&
    (in_a[31] != in_b[31]);
  wire nan_sum = is_nan32(in_a) || is_nan32(in_b) || opposite_infinities;
  wire special = nan_sum || is_inf32(in_a) || is_inf32(in_b);
  wire [31:0] special_value = nan_sum ? CANONICAL_NAN :
    (is_inf32(in_a) ? in_a : in_b);
  wire [4:0] special_flags =
    {is_snan32(in_a) || is_snan32(in_b) || opposite_infinities,4'd0};

  reg sign0, same_sign0, special0;
  reg [26:0] large0, aligned0;
  reg signed [12:0] exponent0;
  reg [31:0] special_value0;
  reg [4:0] special_flags0;
  reg sign1, same_sign1, special1;
  reg [27:0] sum1;
  reg signed [12:0] exponent1;
  reg [31:0] special_value1;
  reg [4:0] special_flags1;
  reg [31:0] data2;
  reg [4:0] flags2;
  wire [4:0] leading = clz27(sum1[26:0]);
  wire [26:0] normalized_sum = sum1[27] ?
    {sum1[27:2],(|sum1[1:0])} : (sum1[26:0] << leading);
  wire signed [12:0] normalized_exponent = sum1[27] ?
    exponent1+13'sd1 : exponent1-$signed({8'd0,leading});
  wire [36:0] rounded_sum = round32(sign1,normalized_exponent,normalized_sum);
  wire [31:0] finite_value = sum1 == 0 ?
    {sign1 && same_sign1,31'd0} : rounded_sum[31:0];

  assign in_ready = rst_n && !flush && ready0;
  assign out_valid = rst_n && !flush && valid2;
  assign out_data = out_valid ? data2 : 32'd0;
  assign out_flags = out_valid ? flags2 : 5'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid0 <= 0;
      valid1 <= 0;
      valid2 <= 0;
      sign0 <= 0;
      same_sign0 <= 0;
      special0 <= 0;
      large0 <= 0;
      aligned0 <= 0;
      exponent0 <= 0;
      special_value0 <= 0;
      special_flags0 <= 0;
      sign1 <= 0;
      same_sign1 <= 0;
      special1 <= 0;
      sum1 <= 0;
      exponent1 <= 0;
      special_value1 <= 0;
      special_flags1 <= 0;
      data2 <= 0;
      flags2 <= 0;
    end else if (flush) begin
      valid0 <= 0;
      valid1 <= 0;
      valid2 <= 0;
    end else begin
      if (ready0) begin
        valid0 <= in_valid;
        if (in_valid) begin
          sign0 <= large_operand[31];
          same_sign0 <= in_a[31] == in_b[31];
          special0 <= special;
          large0 <= large_sig;
          aligned0 <= shift_jam27(small_sig,alignment);
          exponent0 <= $signed({5'd0,large_exponent})-13'sd127;
          special_value0 <= special_value;
          special_flags0 <= special_flags;
        end
      end
      if (ready1) begin
        valid1 <= valid0;
        if (valid0) begin
          sign1 <= sign0;
          same_sign1 <= same_sign0;
          special1 <= special0;
          sum1 <= same_sign0 ? {1'b0,large0}+{1'b0,aligned0} :
            {1'b0,large0}-{1'b0,aligned0};
          exponent1 <= exponent0;
          special_value1 <= special_value0;
          special_flags1 <= special_flags0;
        end
      end
      if (ready2) begin
        valid2 <= valid1;
        if (valid1) begin
          data2 <= special1 ? special_value1 : finite_value;
          flags2 <= special1 ? special_flags1 :
            (sum1 == 0 ? 5'd0 : rounded_sum[36:32]);
        end
      end
    end
  end
endmodule
