module anvil_q2_ht2_fp32_mul_pipe (
  input wire clk, rst_n, advance,
  input wire [31:0] a, b,
  output wire [31:0] product,
  output wire error
);
  import anvil_q2_ht2_fp_pkg::*;
  reg [23:0] a1, b1;
  reg [47:0] product2, product3;
  reg [5:0] leading3;
  reg signed [11:0] exponent1, exponent2, exponent3, exponent4;
  reg [11:0] exponent5;
  reg sign1, sign2, sign3, sign4, sign5;
  reg [26:0] significand4, significand5;
  reg [31:0] result6, result7;
  reg error6, error7;
  reg [4:0] special;
  reg [31:0] special_value [0:4];
  integer i;

  function automatic [5:0] leading48(input [47:0] value);
    reg [47:0] work;
    reg [5:0] count;
    begin
      work=value; count=0;
      if (work[47:16]==0) begin count=count+32; work=work << 32; end
      if (work[47:32]==0) begin count=count+16; work=work << 16; end
      if (work[47:40]==0) begin count=count+8; work=work << 8; end
      if (work[47:44]==0) begin count=count+4; work=work << 4; end
      if (work[47:46]==0) begin count=count+2; work=work << 2; end
      if (!work[47]) count=count+1;
      leading48=value==0 ? 6'd48 : count;
    end
  endfunction

  wire nonfinite_a=&a[30:23];
  wire nonfinite_b=&b[30:23];
  wire invalid=(nonfinite_a && (|a[22:0])) ||
    (nonfinite_b && (|b[22:0])) ||
    (nonfinite_a && b[30:0]==0) || (nonfinite_b && a[30:0]==0);
  wire [31:0] exceptional=invalid ? 32'h7fc00000 :
    {a[31]^b[31],8'hff,23'd0};
  wire [11:0] a_exponent=a[30:23]==0 ? 12'd1 : {4'd0,a[30:23]};
  wire [11:0] b_exponent=b[30:23]==0 ? 12'd1 : {4'd0,b[30:23]};
  wire [47:0] normalized=product3 << leading3;
  wire [5:0] leading_distance=leading48(product2);
  wire [11:0] underflow_distance=12'sd1-exponent4;
  wire [32:0] packed_result=pack_fp32(sign5,exponent5,significand5);

  assign product=rst_n ? result7 : 32'd0;
  assign error=rst_n && error7;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      a1<=0; b1<=0; product2<=0; product3<=0; leading3<=0;
      exponent1<=0; exponent2<=0; exponent3<=0; exponent4<=0; exponent5<=0;
      sign1<=0; sign2<=0; sign3<=0; sign4<=0; sign5<=0;
      significand4<=0; significand5<=0; result6<=0; result7<=0;
      error6<=0; error7<=0; special<=0;
      for (i=0;i<5;i=i+1) special_value[i]<=0;
    end else if (advance) begin
      a1<={(|a[30:23]),a[22:0]};
      b1<={(|b[30:23]),b[22:0]};
      exponent1<=$signed(a_exponent)+$signed(b_exponent)-12'sd126;
      sign1<=a[31]^b[31];
      special[0]<=nonfinite_a || nonfinite_b;
      special_value[0]<=exceptional;

      product2<=a1*b1; exponent2<=exponent1; sign2<=sign1;
      product3<=product2; leading3<=leading_distance;
      exponent3<=exponent2; sign3<=sign2;

      significand4<={normalized[47:22],(|normalized[21:0])};
      exponent4<=product3==0 ? 12'sd1 : exponent3-$signed({6'd0,leading3});
      sign4<=sign3;
      if (exponent4<1) begin
        significand5<=right_jam27(significand4,underflow_distance);
        exponent5<=1;
      end else begin
        significand5<=significand4;
        exponent5<=exponent4;
      end
      sign5<=sign4;

      for (i=1;i<5;i=i+1) begin
        special[i]<=special[i-1];
        special_value[i]<=special_value[i-1];
      end
      result6<=special[4] ? special_value[4] : packed_result[31:0];
      error6<=special[4] || packed_result[32];
      result7<=result6; error7<=error6;
    end
  end
endmodule
