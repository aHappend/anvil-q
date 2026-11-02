module anvil_q3_ht2_f32_to_q16 (
  input wire clk,rst_n,flush,enable,in_valid,
  input wire [31:0] in_f32,
  output wire out_valid,out_error,
  output wire signed [31:0] out_q16
);
  reg [3:0] valid_pipe,error_pipe;
  reg [31:0] value0;
  reg sign1,saturate1,increment1;
  reg [31:0] magnitude1;
  reg sign2,saturate2,increment2;
  reg signed [31:0] signed_value2,result3;
  reg input_bad;
  wire [7:0] exponent0=value0[30:23]==0 ? 8'd1 : value0[30:23];
  wire [31:0] significand0={8'd0,value0[30:23]!=0,value0[22:0]};
  wire [7:0] right_distance0=8'd134-exponent0;
  wire [7:0] left_distance0=exponent0-8'd134;
  wire [31:0] shifted0=exponent0>=134 ?
    (significand0<<left_distance0) : (significand0>>right_distance0);
  wire [31:0] discarded0=right_distance0>0 && right_distance0<32 ?
    (significand0<<(8'd32-right_distance0)) : 0;
  wire guard0=exponent0<134 && right_distance0<32 && discarded0[31];
  wire signed [31:0] signed_magnitude1=sign1 ?
    $signed(~magnitude1+32'd1) : $signed(magnitude1);
  wire signed [31:0] rounded2=sign2 ?
    signed_value2-$signed({31'd0,increment2}) :
    signed_value2+$signed({31'd0,increment2});
  always @* begin
    input_bad=in_f32[30:23]==255;
`ifndef SYNTHESIS
    if ((^in_f32)===1'bx) input_bad=1;
`endif
  end
  assign out_valid=rst_n && !flush && valid_pipe[3];
  assign out_error=out_valid && error_pipe[3];
  assign out_q16=out_valid && !out_error ? result3 : 0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe<=0; error_pipe<=0; value0<=0;
      sign1<=0; saturate1<=0; increment1<=0; magnitude1<=0;
      sign2<=0; saturate2<=0; increment2<=0;
      signed_value2<=0; result3<=0;
    end else if (flush) begin
      valid_pipe<=0; error_pipe<=0; value0<=0;
      sign1<=0; saturate1<=0; increment1<=0; magnitude1<=0;
      sign2<=0; saturate2<=0; increment2<=0;
      signed_value2<=0; result3<=0;
    end else if (enable) begin
      valid_pipe<={valid_pipe[2:0],in_valid};
      error_pipe<={error_pipe[2:0],in_valid && input_bad};
      value0<=in_valid ? in_f32 : 0;
      sign1<=value0[31]; saturate1<=exponent0>=142;
      increment1<=guard0; magnitude1<=shifted0;
      sign2<=sign1; saturate2<=saturate1; increment2<=increment1;
      signed_value2<=signed_magnitude1;
      if (saturate2) begin
        if (sign2) result3<=32'sh80000000;
        else result3<=32'sh7fffffff;
      end else if (!sign2 && signed_value2==32'sh7fffffff && increment2)
        result3<=32'sh7fffffff;
      else result3<=rounded2;
    end
  end
endmodule
