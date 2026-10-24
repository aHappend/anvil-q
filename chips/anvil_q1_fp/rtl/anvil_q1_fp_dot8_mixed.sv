module anvil_q1_fp_dot8_mixed(
  input wire clk, rst_n, in_valid,
  input wire [1:0] in_precision,
  input wire [255:0] a,
  input wire [127:0] b,
  input wire [7:0] lane_mask,
  input wire [31:0] acc_in,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  wire [719:0] terms;
  genvar lane;
  generate for (lane=0;lane<8;lane=lane+1) begin: products
    wire [31:0] weight;
    assign weight=anvil_q1_fp_pkg::widen16(b[lane*16+:16],in_precision);
    assign terms[lane*80+:80]=anvil_q1_fp_pkg::product32(a[lane*32+:32],weight);
  end endgenerate
  assign terms[640+:80]=anvil_q1_fp_pkg::term32(acc_in);
  anvil_q1_fp_reduce3 pipeline(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.terms(terms),
    .active({1'b1,lane_mask}),
    .force_invalid(in_precision!=2'b01 && in_precision!=2'b10),
    .out_valid(out_valid),.result(result),.status(status)
  );
endmodule
