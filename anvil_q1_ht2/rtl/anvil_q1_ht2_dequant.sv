module anvil_q1_ht2_dequant (
  input wire clk, rst_n, in_valid,
  output wire in_ready,
  input wire [31:0] in_qweight, in_qzero,
  input wire [2:0] in_lane,
  input wire [15:0] in_scale,
  output wire out_valid,
  input wire out_ready,
  output wire [15:0] out_weight,
  output wire out_error
);
  import anvil_q1_ht2_fp_pkg::*;
  wire run_n;
  wire [4:0] shift = awq_shift(in_lane);
  wire [31:0] shifted_q = in_qweight >> shift;
  wire [31:0] shifted_z = in_qzero >> shift;
  wire signed [4:0] difference =
    $signed({1'b0, shifted_q[3:0]}) - $signed({1'b0, shifted_z[3:0]});
  wire [4:0] magnitude = difference[4] ? -difference : difference;
  wire [31:0] difference_fp32 = pack32(difference[4], {59'b0, magnitude}, 0);
  wire [31:0] scale_fp32 = expand16(in_scale, 1'b1);
  wire invalid_scale = in_scale[14:10] == 5'h1f ||
                                           (in_scale[15] && in_scale[14:0] != 0);
  reg [3:0] valid_pipe, error_pipe;
  reg [15:0] weight;
  reg failed;
  wire product_valid;
  wire [31:0] product;
  wire advance = run_n && (!valid_pipe[3] || out_ready);
  wire [15:0] narrowed = narrow32(product, 1'b0);
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  anvil_q1_ht2_fp32_mul u_scale (
    .clk(clk), .rst_n(run_n), .enable(advance), .in_valid(in_valid && in_ready),
    .in_a(difference_fp32), .in_b(scale_fp32),
    .out_valid(product_valid), .out_data(product)
  );
  assign in_ready = advance;
  assign out_valid = run_n && valid_pipe[3];
  assign out_weight = out_valid && !failed ? weight : 16'b0;
  assign out_error = out_valid && failed;
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      valid_pipe <= 0;
      error_pipe <= 0;
      weight <= 0;
      failed <= 0;
    end else if (advance) begin
      valid_pipe <= {valid_pipe[2:0], in_valid && in_ready};
      error_pipe <= {error_pipe[2:0], invalid_scale};
      weight <= narrowed;
      failed <= error_pipe[2] || (product_valid && fp32_nonfinite(product));
    end
  end
endmodule
