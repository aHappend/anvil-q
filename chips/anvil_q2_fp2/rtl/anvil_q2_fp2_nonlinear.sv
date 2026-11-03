module anvil_q2_fp2_normalize (
  input wire [31:0] in_x,
  output wire [23:0] mantissa,
  output wire signed [9:0] exponent,
  output wire invalid
);
  reg [23:0] shifted;
  reg [4:0] distance;
  always @* begin
    shifted={1'b0,in_x[22:0]};
    distance=0;
    if (!(|shifted[23:8])) begin shifted=shifted << 16; distance=distance+16; end
    if (!(|shifted[23:16])) begin shifted=shifted << 8; distance=distance+8; end
    if (!(|shifted[23:20])) begin shifted=shifted << 4; distance=distance+4; end
    if (!(|shifted[23:22])) begin shifted=shifted << 2; distance=distance+2; end
    if (!shifted[23]) begin shifted=shifted << 1; distance=distance+1; end
  end
  assign mantissa=(|in_x[30:23]) ? {1'b1,in_x[22:0]} : shifted;
  assign exponent=(|in_x[30:23]) ?
    $signed({2'd0,in_x[30:23]})-10'sd127 : -10'sd126-$signed({5'd0,distance});
  assign invalid=in_x[31] || !(|in_x[30:0]) || (&in_x[30:23]);
endmodule

module anvil_q2_fp2_tangent_pack (
  input wire [34:0] base,
  input wire signed [23:0] correction,
  input wire [7:0] encoded_exponent,
  output wire [31:0] out_data,
  output wire out_error
);
  // Split the exact subtraction at the Q34-to-binary32 rounding boundary.
  wire [10:0] low_difference={1'b0,base[9:0]}-{1'b0,correction[9:0]};
  wire borrow=low_difference[10];
  wire odd=base[10]^correction[10]^borrow;
  wire round_up=low_difference[9] && ((|low_difference[8:0]) || odd);
  wire [1:0] carry_in={1'b0,!borrow}+{1'b0,round_up};
  wire [24:0] a=base[34:10];
  wire [24:0] b=~{{11{correction[23]}},correction[23:10]};
  wire [24:0] c={23'd0,carry_in};
  wire [24:0] sum=a^b^c;
  wire [24:0] carry=((a&b)|(a&c)|(b&c)) << 1;
  wire [24:0] rounded=sum+carry;
  assign out_error=rounded[24] || !rounded[23];
  assign out_data=out_error ? 32'h7fc00000 :
    {1'b0,encoded_exponent,rounded[22:0]};
endmodule

module anvil_q2_fp2_rsqrt2 (
  input wire clk, rst_n,
  input wire in_valid,
  output wire in_ready,
  input wire [31:0] in_x,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_data,
  output wire out_error
);
  wire [23:0] mantissa;
  wire signed [9:0] exponent;
  wire invalid;
  anvil_q2_fp2_normalize normalize(in_x,mantissa,exponent,invalid);
  wire [69:0] coefficients;
  anvil_q2_fp2_rsqrt_rom lut({exponent[0],mantissa[22:13]},coefficients);
  wire signed [12:0] delta=$signed({!mantissa[12],mantissa[11:0]});
  reg v0, v1, error0, error1;
  reg [34:0] base0;
  reg [32:0] slope0;
  reg signed [12:0] delta0;
  reg [7:0] encoded0;
  reg [31:0] result1;
  wire enable=!v1 || out_ready;
  wire signed [46:0] correction=$signed({1'b0,slope0})*delta0;
  wire signed [10:0] encoded=11'sd126-($signed(exponent) >>> 1);
  wire [31:0] packed_value;
  wire packing_error;
  anvil_q2_fp2_tangent_pack pack(base0,correction[46:23],encoded0,
    packed_value,packing_error);
  assign in_ready=rst_n && enable;
  assign out_valid=rst_n && v1;
  assign out_data=rst_n ? result1 : 32'd0;
  assign out_error=out_valid && error1;
  always @(posedge clk) begin
    if (rst_n && enable && in_valid) begin
      base0<=coefficients[69:35];
      slope0<=coefficients[32:0];
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      v0<=0; v1<=0; error0<=0; error1<=0;
      delta0<=0; encoded0<=0; result1<=0;
    end else if (enable) begin
      v0<=in_valid;
      v1<=v0;
      if (in_valid) begin
        delta0<=delta;
        encoded0<=encoded[7:0];
        error0<=invalid || encoded>=255 || encoded<=0;
      end
      if (v0) begin
        result1<=error0 ? 32'h7fc00000 : packed_value;
        error1<=error0 || packing_error;
      end
    end
  end
endmodule

module anvil_q2_fp2_reciprocal2 (
  input wire clk, rst_n, flush, enable,
  input wire in_valid, in_error,
  input wire [31:0] in_x,
  output wire out_valid,
  output wire [31:0] out_data,
  output wire out_error
);
  wire [23:0] mantissa;
  wire signed [9:0] exponent;
  wire invalid;
  anvil_q2_fp2_normalize normalize(in_x,mantissa,exponent,invalid);
  wire [69:0] coefficients;
  anvil_q2_fp2_recip_rom lut(mantissa[22:12],coefficients);
  wire signed [11:0] delta=$signed({!mantissa[11],mantissa[10:0]});
  reg v0, v1, error0, error1;
  reg [34:0] base0;
  reg [33:0] slope0;
  reg signed [11:0] delta0;
  reg [7:0] encoded0;
  reg [31:0] result1;
  wire signed [46:0] correction=$signed({1'b0,slope0})*delta0;
  wire signed [10:0] encoded=11'sd126-$signed(exponent);
  wire [31:0] packed_value;
  wire packing_error;
  anvil_q2_fp2_tangent_pack pack(base0,correction[46:23],encoded0,
    packed_value,packing_error);
  assign out_valid=rst_n && !flush && v1;
  assign out_data=rst_n ? result1 : 32'd0;
  assign out_error=out_valid && error1;
  always @(posedge clk) begin
    if (rst_n && !flush && enable && in_valid) begin
      base0<=coefficients[69:35];
      slope0<=coefficients[33:0];
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      v0<=0; v1<=0; error0<=0; error1<=0;
      delta0<=0; encoded0<=0; result1<=0;
    end else if (flush) begin
      v0<=0; v1<=0;
    end else if (enable) begin
      v0<=in_valid;
      v1<=v0;
      if (in_valid) begin
        delta0<=delta;
        encoded0<=encoded[7:0];
        error0<=in_error || invalid || encoded>=255 || encoded<=0;
      end
      if (v0) begin
        result1<=error0 ? 32'h7fc00000 : packed_value;
        error1<=error0 || packing_error;
      end
    end
  end
endmodule

module anvil_q2_fp2_exp9 (
  input wire clk, rst_n, flush, enable,
  input wire in_valid, in_error,
  input wire [31:0] in_x,
  output wire out_valid,
  output wire [31:0] out_data,
  output wire out_error
);
  // Q40 magnitude times Q48 log2(e); range reduction never uses division.
  localparam [48:0] LOG2_E=49'h171547652b830;
  wire [23:0] input_mantissa={|in_x[30:23],in_x[22:0]};
  wire signed [9:0] input_shift=$signed({2'd0,in_x[30:23]})-10'sd110;
  wire signed [9:0] right_shift=-input_shift;
  wire [46:0] fixed_input=input_shift>=0 ?
    ({23'd0,input_mantissa} << input_shift[5:0]) :
    (right_shift>=47 ? 47'd0 : {23'd0,input_mantissa} >> right_shift[5:0]);
  wire input_bad=(&in_x[30:23]) || (!in_x[31] && (|in_x[30:0]));
  wire input_zero=in_x[31] && in_x[30:0]>31'h42a00000;
  reg [8:0] valid, failed, zero;
  reg [46:0] magnitude0;
  reg [95:0] logarithm1;
  reg [6:0] exponent2, exponent3, exponent4, exponent5, exponent6;
  reg [39:0] fraction2;
  wire [122:0] coefficients;
  anvil_q2_fp2_exp_rom lut(fraction2[39:30],coefficients);
  reg [40:0] base3, slope3, quadratic3, base4, base5;
  reg signed [30:0] delta3;
  reg signed [71:0] linear4;
  reg [61:0] square4;
  reg [40:0] quadratic4;
  reg signed [42:0] linear5;
  reg [62:0] quadratic5;
  reg [42:0] sum6;
  reg [23:0] significand7;
  reg guard7, sticky7;
  reg [7:0] encoded7;
  reg [31:0] result8;
  wire signed [71:0] linear_product=$signed({1'b0,slope3})*delta3;
  wire signed [61:0] delta_squared=delta3*delta3;
  wire [62:0] quadratic_product=quadratic4*square4[61:40];
  wire signed [43:0] combined=$signed({3'd0,base5})-
    $signed({linear5[42],linear5})+$signed({21'd0,quadratic5[62:40]});
  wire [24:0] rounded={1'b0,significand7}+
    {24'd0,(guard7 && (sticky7 || significand7[0]))};
  wire [7:0] final_exponent=encoded7+{7'd0,rounded[24]};
  wire [23:0] final_mantissa=rounded[24] ? rounded[24:1] : rounded[23:0];
  assign out_valid=rst_n && !flush && valid[8];
  assign out_data=rst_n ? result8 : 32'd0;
  assign out_error=out_valid && failed[8];
  always @(posedge clk) begin
    if (rst_n && !flush && enable && valid[2]) begin
      base3<=coefficients[122:82];
      slope3<=coefficients[81:41];
      quadratic3<=coefficients[40:0];
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0; failed<=0; zero<=0; magnitude0<=0; logarithm1<=0;
      exponent2<=0; exponent3<=0; exponent4<=0; exponent5<=0; exponent6<=0;
      fraction2<=0; delta3<=0;
      base4<=0; base5<=0; linear4<=0; square4<=0; quadratic4<=0;
      linear5<=0; quadratic5<=0; sum6<=0; significand7<=0;
      guard7<=0; sticky7<=0; encoded7<=0; result8<=0;
    end else if (flush) begin
      valid<=0;
    end else if (enable) begin
      valid<={valid[7:0],in_valid};
      failed<={failed[7:0],(in_error || input_bad)};
      zero<={zero[7:0],input_zero};
      if (in_valid) magnitude0<=fixed_input;
      if (valid[0]) logarithm1<=magnitude0*LOG2_E;
      if (valid[1]) begin
        exponent2<=logarithm1[94:88];
        fraction2<=logarithm1[87:48];
      end
      if (valid[2]) begin
        delta3<=$signed({1'b0,fraction2[29:0]})-31'sd536870912;
        exponent3<=exponent2;
      end
      if (valid[3]) begin
        base4<=base3;
        linear4<=linear_product;
        square4<=delta_squared;
        quadratic4<=quadratic3;
        exponent4<=exponent3;
      end
      if (valid[4]) begin
        base5<=base4;
        linear5<=linear4 >>> 40;
        quadratic5<=quadratic_product;
        exponent5<=exponent4;
      end
      if (valid[5]) begin
        sum6<=combined[42:0];
        exponent6<=exponent5;
      end
      if (valid[6]) begin
        significand7<=sum6[40] ? sum6[40:17] : sum6[39:16];
        guard7<=sum6[40] ? sum6[16] : sum6[15];
        sticky7<=sum6[40] ? (|sum6[15:0]) : (|sum6[14:0]);
        encoded7<=8'd127-{1'b0,exponent6}-(sum6[40] ? 8'd0 : 8'd1);
      end
      if (valid[7]) begin
        if (failed[7]) result8<=32'h7fc00000;
        else if (zero[7]) result8<=32'd0;
        else result8<={1'b0,final_exponent,final_mantissa[22:0]};
      end
    end
  end
endmodule
