module anvil_q1_ht3_fp32_add (
  input wire clk, rst_n, enable, in_valid,
  input wire [31:0] in_a, in_b,
  output wire out_valid,
  output wire [31:0] out_data
);
  import anvil_q1_ht3_fp_pkg::*;
  wire run_n;
  reg [3:0] valid_pipe;
  reg [31:0] a0, b0;
  reg [26:0] large1, small1;
  reg [8:0] exponent1;
  reg sign1, subtract1, special1, negative_zero1;
  reg [31:0] special_data1;
  reg [27:0] magnitude2;
  reg [8:0] exponent2;
  reg sign2, special2;
  reg [31:0] special_data2, data3;
  wire a_larger = a0[30:0] >= b0[30:0];
  wire [31:0] larger_operand = a_larger ? a0 : b0;
  wire [31:0] smaller_operand = a_larger ? b0 : a0;
  wire [8:0] large_exponent =
    larger_operand[30:23] == 0 ? 9'd1 : {1'b0, larger_operand[30:23]};
  wire [8:0] small_exponent =
    smaller_operand[30:23] == 0 ? 9'd1 : {1'b0, smaller_operand[30:23]};
  wire [26:0] aligned_small = shift_jam27(
    {(|smaller_operand[30:23]), smaller_operand[22:0], 3'b0},
    large_exponent-small_exponent);
  wire invalid_sum = fp32_nan(a0) || fp32_nan(b0) ||
    (fp32_nonfinite(a0) && fp32_nonfinite(b0) && (a0[31] != b0[31]));
  wire [27:0] sum = subtract1 ? {1'b0, large1} - {1'b0, small1} :
                                               {1'b0, large1} + {1'b0, small1};
  wire [31:0] rounded_sum = pack32(
    sign2, {36'b0, magnitude2}, int'({1'b0, exponent2})-153);

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  assign out_valid = run_n && valid_pipe[3];
  assign out_data = out_valid ? data3 : 32'b0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 0;
      a0 <= 0;
      b0 <= 0;
      large1 <= 0;
      small1 <= 0;
      exponent1 <= 0;
      sign1 <= 0;
      subtract1 <= 0;
      special1 <= 0;
      negative_zero1 <= 0;
      special_data1 <= 0;
      magnitude2 <= 0;
      exponent2 <= 0;
      sign2 <= 0;
      special2 <= 0;
      special_data2 <= 0;
      data3 <= 0;
    end else if (run_n && enable) begin
      valid_pipe <= {valid_pipe[2:0], in_valid};
      a0 <= in_a;
      b0 <= in_b;
      large1 <= {(|larger_operand[30:23]), larger_operand[22:0], 3'b0};
      small1 <= aligned_small;
      exponent1 <= large_exponent;
      sign1 <= larger_operand[31];
      subtract1 <= larger_operand[31] != smaller_operand[31];
      negative_zero1 <= a0[31] && b0[31];
      special1 <= invalid_sum || fp32_nonfinite(a0) || fp32_nonfinite(b0);
      if (invalid_sum) special_data1 <= FP32_QNAN;
      else if (fp32_nonfinite(a0)) special_data1 <= a0;
      else special_data1 <= b0;
      magnitude2 <= sum;
      exponent2 <= exponent1;
      if (sum == 0) sign2 <= negative_zero1;
      else sign2 <= sign1;
      special2 <= special1;
      special_data2 <= special_data1;
      if (special2) data3 <= special_data2;
      else data3 <= rounded_sum;
    end
  end
endmodule
