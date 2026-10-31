module anvil_q2_ht2_product_pipe (
  input wire clk, rst_n, advance, keep, fp16, weight_fp16,
  input wire [15:0] a, b,
  output wire [31:0] product,
  output wire error
);
  import anvil_q2_ht2_fp_pkg::*;
  reg [10:0] a1, b1;
  reg signed [11:0] ae1, be1;
  reg sign1, special1;
  reg [31:0] exceptional1;
  reg [21:0] magnitude2, magnitude3;
  reg signed [11:0] factor2, factor3;
  reg sign2, sign3;
  reg [5:0] leading3;
  reg [26:0] normalized4, significand5;
  reg signed [11:0] exponent4;
  reg [11:0] exponent5;
  reg sign4, sign5;
  reg [31:0] result6, result7;
  reg error6, error7;
  reg [3:0] special_pipe;
  reg [31:0] exceptional_pipe [0:3];
  integer i;

  wire [15:0] av=keep ? a : 16'd0;
  wire [15:0] bv=keep ? b : 16'd0;
  wire an=fp16 ? av[14:10]==5'h1f : av[14:7]==8'hff;
  wire bn=weight_fp16 ? bv[14:10]==5'h1f : bv[14:7]==8'hff;
  wire az=av[14:0]==0;
  wire bz=bv[14:0]==0;
  wire aq=an && (fp16 ? (|av[9:0]) : (|av[6:0]));
  wire bq=bn && (weight_fp16 ? (|bv[9:0]) : (|bv[6:0]));
  wire invalid=aq || bq || (an && bz) || (bn && az);
  wire [31:0] exceptional=invalid ? 32'h7fc00000 :
    {av[15]^bv[15],8'hff,23'd0};
  wire [5:0] product_leading=leading32({magnitude2,10'd0});
  wire signed [11:0] biased_exponent=
    factor3+12'sd148-$signed({6'd0,leading3});
  wire signed [11:0] underflow_distance=12'sd1-exponent4;
  wire [32:0] packed_result=pack_fp32(sign5,exponent5,significand5);

  assign product=rst_n ? result7 : 32'd0;
  assign error=rst_n && error7;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      a1<=0; b1<=0; ae1<=0; be1<=0; sign1<=0; special1<=0;
      exceptional1<=0; magnitude2<=0; magnitude3<=0;
      factor2<=0; factor3<=0; sign2<=0; sign3<=0; leading3<=0;
      normalized4<=0; significand5<=0; exponent4<=0; exponent5<=0;
      sign4<=0; sign5<=0; result6<=0; result7<=0;
      error6<=0; error7<=0; special_pipe<=0;
      for (i=0;i<4;i=i+1) exceptional_pipe[i]<=0;
    end else if (advance) begin
      if (fp16) begin
        a1<={(|av[14:10]),av[9:0]};
        ae1<=av[14:10]==0 ? -12'sd24 :
          $signed({7'd0,av[14:10]})-12'sd25;
      end else begin
        a1<={3'd0,(|av[14:7]),av[6:0]};
        ae1<=av[14:7]==0 ? -12'sd133 :
          $signed({4'd0,av[14:7]})-12'sd134;
      end
      if (weight_fp16) begin
        b1<={(|bv[14:10]),bv[9:0]};
        be1<=bv[14:10]==0 ? -12'sd24 :
          $signed({7'd0,bv[14:10]})-12'sd25;
      end else begin
        b1<={3'd0,(|bv[14:7]),bv[6:0]};
        be1<=bv[14:7]==0 ? -12'sd133 :
          $signed({4'd0,bv[14:7]})-12'sd134;
      end
      sign1<=av[15]^bv[15];
      special1<=an || bn;
      exceptional1<=exceptional;

      magnitude2<=a1*b1;
      factor2<=ae1+be1;
      sign2<=sign1;
      special_pipe[0]<=special1;
      exceptional_pipe[0]<=exceptional1;

      magnitude3<=magnitude2;
      leading3<=product_leading;
      factor3<=factor2;
      sign3<=sign2;
      special_pipe[1]<=special_pipe[0];
      exceptional_pipe[1]<=exceptional_pipe[0];

      normalized4<={magnitude3,5'd0} << leading3;
      exponent4<=magnitude3==0 ? 12'sd1 : biased_exponent;
      sign4<=sign3;
      special_pipe[2]<=special_pipe[1];
      exceptional_pipe[2]<=exceptional_pipe[1];

      if (exponent4<1) begin
        significand5<=right_jam27(normalized4,underflow_distance);
        exponent5<=1;
      end else begin
        significand5<=normalized4;
        exponent5<=exponent4;
      end
      sign5<=sign4;
      special_pipe[3]<=special_pipe[2];
      exceptional_pipe[3]<=exceptional_pipe[2];

      result6<=special_pipe[3] ? exceptional_pipe[3] : packed_result[31:0];
      error6<=special_pipe[3] || packed_result[32];
      result7<=result6;
      error7<=error6;
    end
  end
endmodule
