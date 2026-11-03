module anvil_q3_ht2_weight_decode (
  input wire clk,rst_n,flush,enable,in_valid,
  input wire [3:0] in_q,in_zero,
  input wire [15:0] in_scale_f16,
  output wire out_valid,out_error,
  output wire [31:0] out_weight_f32
);
  import anvil_q3_ht2_fp_pkg::*;
  reg [2:0] valid_pipe,error_pipe;
  reg [3:0] q0,z0;
  reg [15:0] scale0;
  reg sign1;
  reg [14:0] product1;
  reg signed [9:0] power1;
  reg [31:0] weight2;
  wire sign0=q0<z0;
  wire [3:0] magnitude0=sign0 ? z0-q0 : q0-z0;
  wire [10:0] mantissa0={scale0[14:10]!=0,scale0[9:0]};
  wire [14:0] multiplied0=mantissa0*magnitude0;
  wire [5:0] zeros1=leading_zero32({product1,17'd0});
  wire [23:0] normalized1={product1,9'd0}<<zeros1;
  wire signed [9:0] exponent1=power1+10'sd141-
    $signed({4'd0,zeros1});
  reg input_bad;
  always @* begin
    input_bad=in_scale_f16[14:10]==31 ||
      (in_scale_f16[15] && in_scale_f16[14:0]!=0);
`ifndef SYNTHESIS
    if ((^{in_q,in_zero,in_scale_f16})===1'bx) input_bad=1;
`endif
  end
  assign out_valid=rst_n && !flush && valid_pipe[2];
  assign out_error=out_valid && error_pipe[2];
  assign out_weight_f32=out_valid && !out_error ? weight2 : 0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe<=0; error_pipe<=0; q0<=0; z0<=0; scale0<=0;
      sign1<=0; product1<=0; power1<=0; weight2<=0;
    end else if (flush) begin
      valid_pipe<=0; error_pipe<=0; q0<=0; z0<=0; scale0<=0;
      sign1<=0; product1<=0; power1<=0; weight2<=0;
    end else if (enable) begin
      valid_pipe<={valid_pipe[1:0],in_valid};
      error_pipe<={error_pipe[1:0],in_valid && input_bad};
      q0<=in_valid ? in_q : 0;
      z0<=in_valid ? in_zero : 0;
      scale0<=in_valid ? in_scale_f16 : 0;
      sign1<=sign0;
      product1<=multiplied0;
      if (scale0[14:10]==0) power1<=-10'sd24;
      else power1<=$signed({5'd0,scale0[14:10]})-10'sd25;
      if (product1==0) weight2<=0;
      else weight2<={sign1,exponent1[7:0],normalized1[22:0]};
    end
  end
endmodule
