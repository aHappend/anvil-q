module anvil_q3_ht2_fp32_add (
  input wire clk,rst_n,flush,enable,in_valid,
  input wire [31:0] in_a,in_b,
  output wire out_valid,out_error,
  output wire [31:0] out_result,
  output wire retire_valid,retire_error,
  output wire [31:0] retire_result
);
  import anvil_q3_ht2_fp_pkg::*;
  reg [5:0] valid_pipe;
  reg [5:0] error_pipe;
  reg [31:0] a0,b0;
  reg sign1,subtract1;
  reg [8:0] exponent1,distance1;
  reg [26:0] large1,small1;
  reg sign2,subtract2;
  reg [8:0] exponent2;
  reg [26:0] large2,small2;
  reg sign3;
  reg [8:0] exponent3;
  reg [27:0] sum3;
  reg sign4;
  reg signed [10:0] exponent4;
  reg [26:0] normalized4;
  reg [31:0] result5;
  wire b_larger=b0[30:0]>a0[30:0];
  wire [31:0] large0=b_larger ? b0 : a0;
  wire [31:0] small0=b_larger ? a0 : b0;
  wire [8:0] large_exp0=large0[30:23]==0 ?
    9'd1 : {1'b0,large0[30:23]};
  wire [8:0] small_exp0=small0[30:23]==0 ?
    9'd1 : {1'b0,small0[30:23]};
  wire [26:0] aligned1=shift_jam27(small1,distance1);
  wire [5:0] zeros3=leading_zero32({sum3[26:0],5'd0});
  wire [8:0] available_shift3=exponent3-9'd1;
  wire [8:0] left_shift3=available_shift3<{3'd0,zeros3} ?
    available_shift3 : {3'd0,zeros3};
  wire [32:0] rounded4=round_pack_f32(sign4,exponent4,normalized4);
  wire running=rst_n && !flush;
  reg input_bad;
  always @* begin
    input_bad=in_a[30:23]==255 || in_b[30:23]==255;
`ifndef SYNTHESIS
    if ((^{in_a,in_b})===1'bx) input_bad=1;
`endif
  end
  assign retire_valid=running && enable && valid_pipe[4];
  assign retire_error=retire_valid && (error_pipe[4] || rounded4[32]);
  assign retire_result=retire_valid && !retire_error ? rounded4[31:0] : 0;
  assign out_valid=running && valid_pipe[5];
  assign out_error=out_valid && error_pipe[5];
  assign out_result=out_valid && !out_error ? result5 : 0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe<=0;
      error_pipe<=0;
      a0<=0; b0<=0;
      sign1<=0; subtract1<=0; exponent1<=0; distance1<=0;
      large1<=0; small1<=0;
      sign2<=0; subtract2<=0; exponent2<=0; large2<=0; small2<=0;
      sign3<=0; exponent3<=0; sum3<=0;
      sign4<=0; exponent4<=0; normalized4<=0; result5<=0;
    end else if (flush) begin
      valid_pipe<=0;
      error_pipe<=0;
      a0<=0; b0<=0;
      sign1<=0; subtract1<=0; exponent1<=0; distance1<=0;
      large1<=0; small1<=0;
      sign2<=0; subtract2<=0; exponent2<=0; large2<=0; small2<=0;
      sign3<=0; exponent3<=0; sum3<=0;
      sign4<=0; exponent4<=0; normalized4<=0; result5<=0;
    end else if (enable) begin
      valid_pipe<={valid_pipe[4:0],in_valid};
      error_pipe<={error_pipe[4] || rounded4[32],error_pipe[3:0],
        in_valid && input_bad};
      a0<=in_valid ? in_a : 0;
      b0<=in_valid ? in_b : 0;
      sign1<=large0[31];
      subtract1<=large0[31]^small0[31];
      exponent1<=large_exp0;
      distance1<=large_exp0-small_exp0;
      large1<={large0[30:23]!=0,large0[22:0],3'd0};
      small1<={small0[30:23]!=0,small0[22:0],3'd0};
      sign2<=sign1;
      subtract2<=subtract1;
      exponent2<=exponent1;
      large2<=large1;
      small2<=aligned1;
      sign3<=sign2;
      exponent3<=exponent2;
      if (subtract2) sum3<={1'b0,large2}-{1'b0,small2};
      else sum3<={1'b0,large2}+{1'b0,small2};
      sign4<=sign3;
      if (sum3[27]) begin
        normalized4<={sum3[27:2],sum3[1] || sum3[0]};
        exponent4<=$signed({2'd0,exponent3})+11'sd1;
      end else begin
        normalized4<=sum3[26:0]<<left_shift3;
        exponent4<=$signed({2'd0,exponent3})-
          $signed({2'd0,left_shift3});
      end
      result5<=rounded4[32] || error_pipe[4] ? 0 : rounded4[31:0];
    end
  end
endmodule
