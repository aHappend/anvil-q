module anvil_q2_ht2_unpack_lane (
  input wire clk, rst_n, advance, required,
  input wire [1:0] format,
  input wire [15:0] word_value,
  input wire [3:0] zero,
  input wire [15:0] scale,
  output wire [15:0] weight,
  output wire error
);
  import anvil_q2_ht2_fp_pkg::*;
  reg [1:0] formats [0:8];
  reg [15:0] native [0:8];
  reg [15:0] exceptional [0:7];
  reg [8:0] errors;
  reg [3:0] q0, z0;
  reg [15:0] scale0, scale1;
  reg signed [4:0] difference1;
  reg [3:0] magnitude2;
  reg [7:0] significand2;
  reg signed [11:0] factor2, factor3, factor4;
  reg sign2, sign3, sign4, sign5, sign6, sign7;
  reg [11:0] product3, product4;
  reg [5:0] leading4;
  reg [26:0] normalized5, denormal6;
  reg signed [11:0] exponent5;
  reg [11:0] exponent6, exponent7;
  reg [8:0] rounded7;
  reg [15:0] packed8, result9;
  reg error8, error9;
  integer i;

  wire native_nonfinite=format==1 ? word_value[14:10]==5'h1f :
    word_value[14:7]==8'hff;
  wire native_nan=format==1 ? (|word_value[9:0]) : (|word_value[6:0]);
  wire [15:0] canonical_native=native_nonfinite && native_nan ?
    (format==1 ? 16'h7e00 : 16'h7fc0) : word_value;
  wire scale_nonfinite=scale[14:7]==8'hff;
  wire signed [4:0] input_difference=
    $signed({1'b0,word_value[3:0]})-$signed({1'b0,zero});
  wire [15:0] exceptional_weight=(|scale[6:0]) || input_difference==0 ?
    16'h7fc0 : {scale[15]^input_difference[4],8'hff,7'd0};
  wire signed [4:0] abs_difference=difference1[4] ? -difference1 : difference1;
  wire [5:0] count_leading=leading32({product3,20'd0});
  wire signed [11:0] biased_exponent=
    factor4+12'sd138-$signed({6'd0,leading4});
  wire signed [11:0] shift_underflow=12'sd1-exponent5;
  wire [11:0] final_exponent=exponent7+{11'd0,rounded7[8]};
  wire [7:0] final_significand=rounded7[8] ? rounded7[8:1] : rounded7[7:0];

  assign weight=rst_n ? result9 : 16'd0;
  assign error=rst_n && error9;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (i=0;i<9;i=i+1) begin formats[i]<=0; native[i]<=0; end
      for (i=0;i<8;i=i+1) exceptional[i]<=0;
      errors<=0; q0<=0; z0<=0; scale0<=0; scale1<=0; difference1<=0;
      magnitude2<=0; significand2<=0; factor2<=0; factor3<=0; factor4<=0;
      sign2<=0; sign3<=0; sign4<=0; sign5<=0; sign6<=0; sign7<=0;
      product3<=0; product4<=0; leading4<=0; normalized5<=0; denormal6<=0;
      exponent5<=0; exponent6<=0; exponent7<=0; rounded7<=0;
      packed8<=0; result9<=0; error8<=0; error9<=0;
    end else if (advance) begin
      formats[0]<=format;
      native[0]<=required ? canonical_native : 16'd0;
      errors[0]<=required && (format<2 ? native_nonfinite : scale_nonfinite);
      q0<=required ? word_value[3:0] : 4'd0;
      z0<=required ? zero : 4'd0;
      scale0<=required ? scale : 16'd0;
      exceptional[0]<=exceptional_weight;
      for (i=1;i<8;i=i+1) exceptional[i]<=exceptional[i-1];
      for (i=1;i<9;i=i+1) begin
        formats[i]<=formats[i-1];
        native[i]<=native[i-1];
        errors[i]<=errors[i-1];
      end

      difference1<=$signed({1'b0,q0})-$signed({1'b0,z0});
      scale1<=scale0;

      magnitude2<=abs_difference[3:0];
      significand2<={(|scale1[14:7]),scale1[6:0]};
      factor2<=scale1[14:7]==0 ? -12'sd133 :
        $signed({4'd0,scale1[14:7]})-12'sd134;
      sign2<=difference1[4]^scale1[15];

      product3<=magnitude2*significand2;
      factor3<=factor2;
      sign3<=sign2;

      product4<=product3;
      leading4<=count_leading;
      factor4<=factor3;
      sign4<=sign3;

      normalized5<={product4,15'd0} << leading4;
      exponent5<=product4==0 ? 12'sd1 : biased_exponent;
      sign5<=sign4;

      if (exponent5<1) begin
        denormal6<=right_jam27(normalized5,shift_underflow);
        exponent6<=1;
      end else begin
        denormal6<=normalized5;
        exponent6<=exponent5;
      end
      sign6<=sign5;

      rounded7<={1'b0,denormal6[26:19]}+
        {8'd0,(denormal6[18] && ((|denormal6[17:0]) || denormal6[19]))};
      exponent7<=exponent6;
      sign7<=sign6;

      error8<=errors[7] || (final_exponent>=255 && final_significand!=0);
      if (errors[7]) packed8<=exceptional[7];
      else if (final_exponent>=255 && final_significand!=0)
        packed8<={sign7,8'hff,7'd0};
      else if (!final_significand[7])
        packed8<={sign7,8'd0,final_significand[6:0]};
      else packed8<={sign7,final_exponent[7:0],final_significand[6:0]};

      result9<=formats[8]<2 ? native[8] : packed8;
      error9<=formats[8]<2 ? errors[8] : error8;
    end
  end
endmodule
