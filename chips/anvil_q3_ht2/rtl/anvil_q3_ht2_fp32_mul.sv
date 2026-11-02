module anvil_q3_ht2_fp32_mul (
  input wire clk,rst_n,flush,enable,in_valid,
  input wire [31:0] in_a,in_b,
  output wire out_valid,out_error,
  output wire [31:0] out_result
);
  import anvil_q3_ht2_fp_pkg::*;
  reg [5:0] valid_pipe,error_pipe;
  reg [31:0] a0,b0;
  reg sign1,zero1;
  reg [23:0] mantissa_a1,mantissa_b1;
  reg signed [10:0] exponent1;
  reg sign2,zero2;
  reg signed [10:0] exponent2;
  reg [47:0] product2;
  reg sign3,zero3;
  reg signed [10:0] exponent3;
  reg [5:0] zeros3;
  reg [47:0] product3;
  reg sign4;
  reg signed [10:0] exponent4;
  reg [26:0] normalized4;
  reg [31:0] result5;
  wire [5:0] zeros_a0=leading_zero32({a0[22:0],9'd0});
  wire [5:0] zeros_b0=leading_zero32({b0[22:0],9'd0});
  wire [23:0] mantissa_a0=a0[30:23]==0 ?
    ({1'b0,a0[22:0]}<<(zeros_a0+6'd1)) : {1'b1,a0[22:0]};
  wire [23:0] mantissa_b0=b0[30:23]==0 ?
    ({1'b0,b0[22:0]}<<(zeros_b0+6'd1)) : {1'b1,b0[22:0]};
  wire signed [10:0] exponent_a0=a0[30:23]==0 ?
    -$signed({5'd0,zeros_a0}) : $signed({3'd0,a0[30:23]});
  wire signed [10:0] exponent_b0=b0[30:23]==0 ?
    -$signed({5'd0,zeros_b0}) : $signed({3'd0,b0[30:23]});
  wire [47:0] multiplied1=mantissa_a1*mantissa_b1;
  wire [5:0] product_zeros2=leading_zero48(product2);
  wire signed [10:0] normalized_exponent3=exponent3-
    $signed({5'd0,zeros3})+11'sd1;
  wire [47:0] shifted3=product3<<zeros3;
  wire [10:0] underflow_shift3=normalized_exponent3<1 ?
    11'(11'sd1-normalized_exponent3) : 11'd0;
  wire [47:0] denormalized3=shift_jam48(shifted3,underflow_shift3);
  wire [26:0] significand3={denormalized3[47:22],|denormalized3[21:0]};
  wire [32:0] rounded4=round_pack_f32(sign4,exponent4,normalized4);
  assign out_valid=rst_n && !flush && valid_pipe[5];
  assign out_error=out_valid && error_pipe[5];
  assign out_result=out_valid && !out_error ? result5 : 0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe<=0; error_pipe<=0; a0<=0; b0<=0;
      sign1<=0; zero1<=0; mantissa_a1<=0; mantissa_b1<=0; exponent1<=0;
      sign2<=0; zero2<=0; exponent2<=0; product2<=0;
      sign3<=0; zero3<=0; exponent3<=0; zeros3<=0; product3<=0;
      sign4<=0; exponent4<=0; normalized4<=0; result5<=0;
    end else if (flush) begin
      valid_pipe<=0; error_pipe<=0; a0<=0; b0<=0;
      sign1<=0; zero1<=0; mantissa_a1<=0; mantissa_b1<=0; exponent1<=0;
      sign2<=0; zero2<=0; exponent2<=0; product2<=0;
      sign3<=0; zero3<=0; exponent3<=0; zeros3<=0; product3<=0;
      sign4<=0; exponent4<=0; normalized4<=0; result5<=0;
    end else if (enable) begin
      valid_pipe<={valid_pipe[4:0],in_valid};
      error_pipe<={error_pipe[4] || rounded4[32],error_pipe[3:0],
        in_valid && (in_a[30:23]==255 || in_b[30:23]==255)};
      a0<=in_valid ? in_a : 0;
      b0<=in_valid ? in_b : 0;
      sign1<=a0[31]^b0[31];
      zero1<=a0[30:0]==0 || b0[30:0]==0;
      mantissa_a1<=mantissa_a0;
      mantissa_b1<=mantissa_b0;
      exponent1<=exponent_a0+exponent_b0-11'sd127;
      sign2<=sign1; zero2<=zero1; exponent2<=exponent1;
      product2<=multiplied1;
      sign3<=sign2; zero3<=zero2; exponent3<=exponent2;
      zeros3<=product_zeros2; product3<=product2;
      sign4<=sign3;
      if (normalized_exponent3<1) exponent4<=11'sd1;
      else exponent4<=normalized_exponent3;
      normalized4<=zero3 ? 27'd0 : significand3;
      result5<=rounded4[32] || error_pipe[4] ? 0 : rounded4[31:0];
    end
  end
endmodule
