module anvil_q3_ht2_q16_to_f16 (
  input wire clk,rst_n,flush,enable,in_valid,
  input wire signed [31:0] in_q16,
  output wire out_valid,out_error,
  output wire [15:0] out_f16
);
  import anvil_q3_ht2_fp_pkg::*;
  reg [3:0] valid_pipe,error_pipe;
  reg signed [31:0] value0;
  reg sign1;
  reg [31:0] magnitude1;
  reg sign2,subnormal2;
  reg [4:0] exponent2;
  reg [13:0] significand2;
  reg [9:0] subnormal_fraction2;
  reg [15:0] result3;
  reg input_bad;
  wire [31:0] magnitude0=value0[31] ? (~value0+32'd1) : value0;
  wire [5:0] zeros1=leading_zero32(magnitude1);
  wire [31:0] normalized1=magnitude1<<zeros1;
  wire round_increment2=significand2[2] &&
    (significand2[1] || significand2[0] || significand2[3]);
  wire [11:0] rounded2={1'b0,significand2[13:3]}+12'(round_increment2);
  wire [4:0] final_exponent2=exponent2+5'(rounded2[11]);
  wire [9:0] final_fraction2=rounded2[11] ? rounded2[10:1] : rounded2[9:0];
  wire [15:0] packed2=subnormal2 ?
    (subnormal_fraction2==0 ? 16'd0 : {sign2,5'd0,subnormal_fraction2}) :
    {sign2,final_exponent2,final_fraction2};
  always @* begin
    input_bad=0;
`ifndef SYNTHESIS
    if ((^in_q16)===1'bx) input_bad=1;
`endif
  end
  assign out_valid=rst_n && !flush && valid_pipe[3];
  assign out_error=out_valid && error_pipe[3];
  assign out_f16=out_valid && !out_error ? result3 : 0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe<=0; error_pipe<=0; value0<=0;
      sign1<=0; magnitude1<=0;
      sign2<=0; subnormal2<=0; exponent2<=0;
      significand2<=0; subnormal_fraction2<=0; result3<=0;
    end else if (flush) begin
      valid_pipe<=0; error_pipe<=0; value0<=0;
      sign1<=0; magnitude1<=0;
      sign2<=0; subnormal2<=0; exponent2<=0;
      significand2<=0; subnormal_fraction2<=0; result3<=0;
    end else if (enable) begin
      valid_pipe<={valid_pipe[2:0],in_valid};
      error_pipe<={error_pipe[2:0],in_valid && input_bad};
      value0<=in_valid ? in_q16 : 0;
      sign1<=value0[31]; magnitude1<=magnitude0;
      sign2<=sign1; subnormal2<=magnitude1<4;
      exponent2<=5'(6'd30-zeros1);
      significand2<={normalized1[31:19],|normalized1[18:0]};
      subnormal_fraction2<={magnitude1[1:0],8'd0};
      result3<=packed2;
    end
  end
endmodule
