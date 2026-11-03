module anvil_q1_ht3_narrow32 (
  input wire clk, rst_n, enable, in_valid,
  input wire [31:0] in_data,
  input wire in_fp16,
  output wire out_valid,
  output wire [15:0] out_data
);
  import anvil_q1_ht3_fp_pkg::*;
  wire run_n;
  reg valid_q;
  reg [15:0] data_q;
  wire [15:0] narrowed = narrow32(in_data, in_fp16);

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  assign out_valid = run_n && valid_q;
  assign out_data = out_valid ? data_q : 16'b0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_q <= 0;
      data_q <= 0;
    end else if (run_n && enable) begin
      valid_q <= in_valid;
      data_q <= narrowed;
    end
  end
endmodule
