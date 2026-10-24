module anvil_q1_fp_compat_round_div(
  input wire clk, rst_n, in_valid,
  output wire in_ready,
  input wire signed [127:0] numerator,
  input wire [63:0] denominator,
  output wire out_valid,
  output wire signed [127:0] result,
  output wire divide_by_zero
);
  reg negative;
  wire [127:0] magnitude, quotient;
  wire [63:0] remainder;
  assign magnitude=numerator<0 ? -numerator : numerator;
  anvil_q1_fp_compat_div divider(
    clk,rst_n,in_valid,in_ready,magnitude+{65'd0,denominator[63:1]},
    denominator,out_valid,quotient,remainder,divide_by_zero);
  assign result=out_valid ? (negative ? -$signed(quotient) : $signed(quotient)) : 128'sd0;
  always @(posedge clk) begin
    if(!rst_n) negative<=0;
    else if(in_valid && in_ready) negative<=numerator[127];
  end
endmodule
