module anvil_q1_ht3_dequant (
  input wire clk, rst_n, in_valid,
  output wire in_ready,
  input wire in_int8,
  input wire [31:0] in_qweight, in_qzero,
  input wire [2:0] in_lane,
  input wire [15:0] in_scale,
  input wire [31:0] in_scale_fp32,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_data,
  output wire [15:0] out_weight,
  output wire out_error
);
  import anvil_q1_ht3_fp_pkg::*;
  wire run_n;
  reg [4:0] valid_pipe, error_pipe, int8_pipe;
  reg [31:0] result_q;
  reg [15:0] encoded_q;
  reg error_q;
  wire [4:0] shift = awq_shift(in_lane);
  wire [31:0] shifted_weight = in_qweight >> shift;
  wire [31:0] shifted_zero = in_qzero >> shift;
  wire signed [8:0] integer_weight = in_int8 ?
    $signed({in_qweight[7], in_qweight[7:0]}) :
    $signed({5'b0, shifted_weight[3:0]}) - $signed({5'b0, shifted_zero[3:0]});
  wire [8:0] integer_magnitude =
    integer_weight[8] ? -integer_weight : integer_weight;
  wire [31:0] integer_fp32 =
    pack32(integer_weight[8], {55'b0, integer_magnitude}, 0);
  wire [31:0] scale_fp32 =
    in_int8 ? in_scale_fp32 : expand16(in_scale, 1'b1);
  wire invalid_scale = in_int8 ?
    in_scale_fp32[31] || in_scale_fp32[30:0] == 0 || fp32_nonfinite(in_scale_fp32) :
    in_scale[14:10] == 5'h1f || (in_scale[15] && in_scale[14:0] != 0);
  wire [31:0] product_data;
  wire product_valid;
  wire [15:0] narrowed = narrow32(product_data, 1'b0);
  wire [31:0] legacy_data = expand16(narrowed, 1'b0);
  wire advance = run_n && (!valid_pipe[4] || out_ready);

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  anvil_q1_ht3_fp32_mul u_scale (
    .clk(clk), .rst_n(rst_n), .enable(advance),
    .in_valid(in_valid && in_ready),
    .in_a(integer_fp32), .in_b(scale_fp32),
    .out_valid(product_valid), .out_data(product_data)
  );
  assign in_ready = advance;
  assign out_valid = run_n && valid_pipe[4];
  assign out_data = out_valid ? result_q : 32'b0;
  assign out_weight = out_valid ? encoded_q : 16'b0;
  assign out_error = out_valid && error_q;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 0;
      error_pipe <= 0;
      int8_pipe <= 0;
      result_q <= 0;
      encoded_q <= 0;
      error_q <= 0;
    end else if (advance) begin
      valid_pipe <= {valid_pipe[3:0], in_valid && in_ready};
      error_pipe <= {error_pipe[3:0], invalid_scale};
      int8_pipe <= {int8_pipe[3:0], in_int8};
      result_q <= int8_pipe[3] ? product_data : legacy_data;
      encoded_q <= int8_pipe[3] ? 16'b0 : narrowed;
      error_q <= error_pipe[3] || (product_valid &&
        (fp32_nonfinite(product_data) || (!int8_pipe[3] && fp32_nonfinite(legacy_data))));
    end
  end
endmodule
