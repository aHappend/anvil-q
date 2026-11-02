module anvil_q2_fp2_product_round2 (
  input wire clk, rst_n, flush, enable,
  input wire in_valid, in_sign, in_error,
  input wire [1:0] in_class,
  input wire [47:0] in_product,
  input wire signed [12:0] in_exponent,
  output wire out_valid,
  output wire [31:0] out_data,
  output wire out_error
);
  function automatic [5:0] leading_zeros48(input [47:0] x);
    reg [63:0] q;
    reg [5:0] n;
    begin
      q={x,16'd0};
      n[5]=!(|q[63:32]);
      if (n[5]) q=q << 32;
      n[4]=!(|q[63:48]);
      if (n[4]) q=q << 16;
      n[3]=!(|q[63:56]);
      if (n[3]) q=q << 8;
      n[2]=!(|q[63:60]);
      if (n[2]) q=q << 4;
      n[1]=!(|q[63:62]);
      if (n[1]) q=q << 2;
      n[0]=!q[63];
      leading_zeros48=n;
    end
  endfunction

  wire [5:0] leading=leading_zeros48(in_product);
  wire signed [12:0] top=13'sd47-$signed({7'd0,leading});
  wire signed [12:0] unbiased=in_exponent+top;
  wire signed [12:0] shift=(unbiased < -13'sd126) ?
    -13'sd149-in_exponent : top-13'sd23;
  wire signed [12:0] negative_shift=-shift;
  reg [47:0] truncated;
  reg guard_bit, sticky;
  always @* begin
    truncated=0;
    guard_bit=0;
    sticky=0;
    if (shift>13'sd48) sticky=|in_product;
    else if (shift>0) begin
      truncated=in_product >> shift[5:0];
      guard_bit=|(in_product & (48'd1 << (shift[5:0]-6'd1)));
      if (shift>1)
        sticky=|(in_product &
          (48'hffffffffffff >> (7'd49-{1'b0,shift[5:0]})));
    end else if (negative_shift<=13'sd47)
      truncated=in_product << negative_shift[5:0];
  end

  reg v1, v2, sign1, error1, error2, zero1, guard1, sticky1;
  reg [1:0] class1;
  reg [23:0] mantissa1;
  reg signed [12:0] exponent1;
  reg [31:0] result2;
  wire [24:0] rounded={1'b0,mantissa1}+
    {24'd0,(guard1 && (sticky1 || mantissa1[0]))};
  wire [23:0] significand=rounded[24] ? rounded[24:1] : rounded[23:0];
  wire signed [12:0] exponent_final=exponent1+
    $signed({12'd0,rounded[24]});
  wire [7:0] encoded=(exponent_final == -13'sd126 && !significand[23]) ?
    8'd0 : exponent_final[7:0]+8'd127;
  reg [31:0] packed_result;
  always @* begin
    if (class1==2) packed_result=32'h7fc00000;
    else if (class1==1 || (!zero1 && exponent_final>13'sd127))
      packed_result={sign1,8'hff,23'd0};
    else if (zero1) packed_result={sign1,31'd0};
    else packed_result={sign1,encoded,significand[22:0]};
  end

  assign out_valid=rst_n && !flush && v2;
  assign out_data=rst_n ? result2 : 32'd0;
  assign out_error=out_valid && error2;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      v1<=0; v2<=0; sign1<=0; error1<=0; error2<=0; zero1<=0;
      guard1<=0; sticky1<=0; class1<=0; mantissa1<=0; exponent1<=0;
      result2<=0;
    end else if (flush) begin
      v1<=0; v2<=0;
    end else if (enable) begin
      v1<=in_valid;
      v2<=v1;
      if (in_valid) begin
        sign1<=in_sign;
        error1<=in_error;
        zero1<=in_product==0;
        guard1<=guard_bit;
        sticky1<=sticky;
        class1<=in_class;
        mantissa1<=truncated[23:0];
        exponent1<=unbiased < -13'sd126 ? -13'sd126 : unbiased;
      end
      if (v1) begin
        result2<=packed_result;
        error2<=error1 || (&packed_result[30:23]);
      end
    end
  end
endmodule

module anvil_q2_fp2_mul3 (
  input wire clk, rst_n, flush, enable,
  input wire in_valid, in_error,
  input wire [31:0] in_a, in_b,
  output wire out_valid,
  output wire [31:0] out_data,
  output wire out_error
);
  wire [23:0] ma={|in_a[30:23],in_a[22:0]};
  wire [23:0] mb={|in_b[30:23],in_b[22:0]};
  wire signed [12:0] ea=(in_a[30:23]==0) ? -13'sd149 :
    $signed({5'd0,in_a[30:23]})-13'sd150;
  wire signed [12:0] eb=(in_b[30:23]==0) ? -13'sd149 :
    $signed({5'd0,in_b[30:23]})-13'sd150;
  wire nan_a=(&in_a[30:23]) && (|in_a[22:0]);
  wire nan_b=(&in_b[30:23]) && (|in_b[22:0]);
  wire inf_a=(&in_a[30:23]) && !(|in_a[22:0]);
  wire inf_b=(&in_b[30:23]) && !(|in_b[22:0]);
  wire invalid=nan_a || nan_b ||
    (inf_a && !(|in_b[30:0])) || (inf_b && !(|in_a[30:0]));
  reg v0, sign0, error0;
  reg [1:0] class0;
  reg [47:0] product0;
  reg signed [12:0] exponent0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      v0<=0; sign0<=0; error0<=0; class0<=0; product0<=0; exponent0<=0;
    end else if (flush) v0<=0;
    else if (enable) begin
      v0<=in_valid;
      if (in_valid) begin
        product0<=ma*mb;
        exponent0<=ea+eb;
        sign0<=in_a[31]^in_b[31];
        class0<=invalid ? 2'd2 : ((inf_a || inf_b) ? 2'd1 : 2'd0);
        error0<=in_error || (&in_a[30:23]) || (&in_b[30:23]);
      end
    end
  end
  anvil_q2_fp2_product_round2 rounding (
    .clk(clk),.rst_n(rst_n),.flush(flush),.enable(enable),
    .in_valid(v0),.in_sign(sign0),.in_error(error0),.in_class(class0),
    .in_product(product0),.in_exponent(exponent0),
    .out_valid(out_valid),.out_data(out_data),.out_error(out_error)
  );
endmodule

module anvil_q2_fp2_bfp_mul3 (
  input wire clk, rst_n, flush, enable,
  input wire in_valid, in_error, in_sign,
  input wire [7:0] in_ma, in_mb,
  input wire signed [12:0] in_group_exponent,
  input wire [7:0] in_residual_a, in_residual_b,
  output wire out_valid,
  output wire [31:0] out_data,
  output wire out_error
);
  reg v0, sign0, error0;
  reg [47:0] product0;
  reg signed [12:0] exponent0;
  wire [15:0] exact_product=in_ma*in_mb;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      v0<=0; sign0<=0; error0<=0; product0<=0; exponent0<=0;
    end else if (flush) v0<=0;
    else if (enable) begin
      v0<=in_valid;
      if (in_valid) begin
        product0<={32'd0,exact_product};
        exponent0<=in_group_exponent-
          $signed({5'd0,in_residual_a})-$signed({5'd0,in_residual_b});
        sign0<=in_sign;
        error0<=in_error;
      end
    end
  end
  anvil_q2_fp2_product_round2 rounding (
    .clk(clk),.rst_n(rst_n),.flush(flush),.enable(enable),
    .in_valid(v0),.in_sign(sign0),.in_error(error0),.in_class(2'd0),
    .in_product(product0),.in_exponent(exponent0),
    .out_valid(out_valid),.out_data(out_data),.out_error(out_error)
  );
endmodule

module anvil_q2_fp2_add4 (
  input wire clk, rst_n, flush, enable,
  input wire in_valid, in_error,
  input wire [31:0] in_a, in_b,
  output wire out_valid,
  output wire [31:0] out_data,
  output wire out_error
);
  function automatic [26:0] shift_jam27(input [26:0] x, input [7:0] shift);
    reg [26:0] q;
    begin
      q=x;
      if (shift[0]) q={1'b0,q[26:2],|q[1:0]};
      if (shift[1]) q={2'd0,q[26:3],|q[2:0]};
      if (shift[2]) q={4'd0,q[26:5],|q[4:0]};
      if (shift[3]) q={8'd0,q[26:9],|q[8:0]};
      if (shift[4]) q={16'd0,q[26:17],|q[16:0]};
      if (shift>=27) q={26'd0,|x};
      shift_jam27=q;
    end
  endfunction

  function automatic [4:0] leading_zeros27(input [26:0] x);
    reg [31:0] q;
    reg [4:0] n;
    begin
      q={x,5'd0};
      n[4]=!(|q[31:16]);
      if (n[4]) q=q << 16;
      n[3]=!(|q[31:24]);
      if (n[3]) q=q << 8;
      n[2]=!(|q[31:28]);
      if (n[2]) q=q << 4;
      n[1]=!(|q[31:30]);
      if (n[1]) q=q << 2;
      n[0]=!q[31];
      leading_zeros27=n;
    end
  endfunction

  wire a_big=in_a[30:0]>=in_b[30:0];
  wire [31:0] big=a_big ? in_a : in_b;
  wire [31:0] smaller=a_big ? in_b : in_a;
  wire [7:0] big_e=big[30:23]==0 ? 8'd1 : big[30:23];
  wire [7:0] small_e=smaller[30:23]==0 ? 8'd1 : smaller[30:23];
  wire [7:0] distance=big_e-small_e;
  wire [26:0] small_aligned=shift_jam27(
    {|smaller[30:23],smaller[22:0],3'd0},distance);
  wire nan_a=(&in_a[30:23]) && (|in_a[22:0]);
  wire nan_b=(&in_b[30:23]) && (|in_b[22:0]);
  wire inf_a=(&in_a[30:23]) && !(|in_a[22:0]);
  wire inf_b=(&in_b[30:23]) && !(|in_b[22:0]);
  wire invalid=nan_a || nan_b || (inf_a && inf_b && in_a[31]!=in_b[31]);
  wire both_zero=!(|in_a[30:0]) && !(|in_b[30:0]);
  wire special=invalid || inf_a || inf_b || both_zero;
  wire [31:0] special_value=invalid ? 32'h7fc00000 :
    (inf_a ? in_a : (inf_b ? in_b : {in_a[31]&in_b[31],31'd0}));

  reg [3:0] valid;
  reg [2:0] sign_bit, exceptional, failed;
  reg subtract0;
  reg [26:0] big0, small0, normalized2;
  reg [27:0] total1;
  reg [8:0] exponent0, exponent1, exponent2;
  reg [31:0] special0, special1, special2, result3;
  reg error3, zero2;
  wire [27:0] total=subtract0 ? {1'b0,big0}-{1'b0,small0} :
    {1'b0,big0}+{1'b0,small0};
  wire [4:0] leading=leading_zeros27(total1[26:0]);
  wire [8:0] available=exponent1-9'd1;
  wire [4:0] left_shift=available<{4'd0,leading} ? available[4:0] : leading;
  wire [26:0] normalized=total1[27] ?
    {total1[27:2],|total1[1:0]} : (total1[26:0] << left_shift);
  wire [8:0] normalized_exponent=total1[27] ?
    exponent1+9'd1 : exponent1-{4'd0,left_shift};
  wire [24:0] rounded={1'b0,normalized2[26:3]}+
    {24'd0,(normalized2[2] && ((|normalized2[1:0]) || normalized2[3]))};
  wire [8:0] packed_exponent=exponent2+{8'd0,rounded[24]};
  wire [23:0] packed_mantissa=rounded[24] ? rounded[24:1] : rounded[23:0];
  wire [7:0] encoded_exponent=(packed_exponent==1 && !packed_mantissa[23]) ?
    8'd0 : packed_exponent[7:0];
  wire [31:0] normal_value=zero2 ? 32'd0 :
    (packed_exponent>=255 ? {sign_bit[2],8'hff,23'd0} :
      {sign_bit[2],encoded_exponent,packed_mantissa[22:0]});
  wire [31:0] packed_value=exceptional[2] ? special2 : normal_value;

  assign out_valid=rst_n && !flush && valid[3];
  assign out_data=rst_n ? result3 : 32'd0;
  assign out_error=out_valid && error3;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0; sign_bit<=0; exceptional<=0; failed<=0; subtract0<=0;
      big0<=0; small0<=0; normalized2<=0; total1<=0;
      exponent0<=0; exponent1<=0; exponent2<=0;
      special0<=0; special1<=0; special2<=0; result3<=0;
      error3<=0; zero2<=0;
    end else if (flush) valid<=0;
    else if (enable) begin
      valid<={valid[2:0],in_valid};
      if (in_valid) begin
        sign_bit[0]<=big[31];
        subtract0<=big[31]^smaller[31];
        big0<={|big[30:23],big[22:0],3'd0};
        small0<=small_aligned;
        exponent0<={1'b0,big_e};
        exceptional[0]<=special;
        special0<=special_value;
        failed[0]<=in_error || (&in_a[30:23]) || (&in_b[30:23]);
      end
      if (valid[0]) begin
        total1<=total;
        exponent1<=exponent0;
        sign_bit[1]<=sign_bit[0];
        exceptional[1]<=exceptional[0];
        special1<=special0;
        failed[1]<=failed[0];
      end
      if (valid[1]) begin
        normalized2<=normalized;
        exponent2<=normalized_exponent;
        zero2<=total1==0;
        sign_bit[2]<=sign_bit[1];
        exceptional[2]<=exceptional[1];
        special2<=special1;
        failed[2]<=failed[1];
      end
      if (valid[2]) begin
        result3<=packed_value;
        error3<=failed[2] || (&packed_value[30:23]);
      end
    end
  end
endmodule
