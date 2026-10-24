module anvil_q1_fp_compat_sqrt(
  input wire clk, rst_n, in_valid,
  output wire in_ready,
  input wire [127:0] radicand,
  output wire out_valid,
  output wire [63:0] result
);
  reg busy, valid_reg;
  reg [5:0] digit;
  reg [127:0] source;
  reg [63:0] root, result_reg;
  reg [65:0] remainder;
  wire [65:0] shifted_remainder, trial, next_remainder;
  wire subtract;
  wire [63:0] next_root;
  assign shifted_remainder=(remainder<<2) | {64'd0,source[127:126]};
  assign trial=({2'd0,root}<<2) | 66'd1;
  assign subtract=shifted_remainder>=trial;
  assign next_remainder=subtract ? shifted_remainder-trial : shifted_remainder;
  assign next_root={root[62:0],subtract};
  assign in_ready=rst_n && !busy;
  assign out_valid=rst_n && valid_reg;
  assign result=(rst_n && valid_reg) ? result_reg : 64'd0;
  always @(posedge clk) begin
    if (!rst_n) begin
      busy<=0; valid_reg<=0; digit<=0; source<=0; root<=0;
      result_reg<=0; remainder<=0;
    end else begin
      valid_reg<=0;
      if (!busy && in_valid) begin
        busy<=1; digit<=0; source<=radicand; root<=0; remainder<=0;
      end else if (busy) begin
        source<=source<<2; remainder<=next_remainder; root<=next_root;
        if (digit==63) begin busy<=0; valid_reg<=1; result_reg<=next_root; end
        else digit<=digit+1;
      end
    end
  end
endmodule
