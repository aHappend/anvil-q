module anvil_q1_fp_binary #(parameter MULTIPLY=0)(
  input wire clk, rst_n, in_valid,
  input wire [31:0] a, b,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  wire [719:0] terms;
  generate if (MULTIPLY) begin: multiply
    assign terms={640'd0,anvil_q1_fp_pkg::product32(a,b)};
  end else begin: add
    assign terms={560'd0,anvil_q1_fp_pkg::term32(b),anvil_q1_fp_pkg::term32(a)};
  end endgenerate
  anvil_q1_fp_reduce3 pipeline(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.terms(terms),
    .active(MULTIPLY ? 9'b000000001 : 9'b000000011),.force_invalid(1'b0),
    .out_valid(out_valid),.result(result),.status(status)
  );
endmodule

module anvil_q1_fp_add(
  input wire clk, rst_n, in_valid,
  input wire [31:0] a, b,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  anvil_q1_fp_binary #(0) pipeline(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.a(a),.b(b),
    .out_valid(out_valid),.result(result),.status(status)
  );
endmodule

module anvil_q1_fp_mul(
  input wire clk, rst_n, in_valid,
  input wire [31:0] a, b,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  anvil_q1_fp_binary #(1) pipeline(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.a(a),.b(b),
    .out_valid(out_valid),.result(result),.status(status)
  );
endmodule
