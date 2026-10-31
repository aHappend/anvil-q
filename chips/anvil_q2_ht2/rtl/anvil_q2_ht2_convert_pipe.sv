module anvil_q2_ht2_convert_pipe (
  input wire clk, rst_n, annul, s_valid, m_ready,
  input wire s_to_fp32, s_fp16,
  input wire [31:0] s_data,
  input wire [63:0] s_tag,
  output wire s_ready, m_valid, m_error,
  output wire [31:0] m_data,
  output wire [63:0] m_tag
);
  import anvil_q2_ht2_fp_pkg::*;
  reg [3:0] valid;
  reg [63:0] tags [0:3];
  reg sign1, sign2, sign3;
  reg expand1, expand2, expand3, half1, half2, half3;
  reg special1, special2, special3;
  reg nan1, nan2, nan3;
  reg [26:0] significand1, significand2;
  reg signed [11:0] exponent1;
  reg [11:0] exponent2, exponent3;
  reg [24:0] rounded3;
  reg [31:0] data4;
  reg error4;
  integer i;

  wire advance=!valid[3] || m_ready;
  wire [23:0] source_significand=s_to_fp32 ?
    (s_fp16 ? {(|s_data[14:10]),s_data[9:0],13'd0} :
      {(|s_data[14:7]),s_data[6:0],16'd0}) :
    {(|s_data[30:23]),s_data[22:0]};
  wire [5:0] leading=leading32({source_significand,8'd0});
  wire [7:0] source_exponent=s_to_fp32 ?
    (s_fp16 ? {3'd0,s_data[14:10]} : s_data[14:7]) : s_data[30:23];
  wire source_special=s_to_fp32 ?
    (s_fp16 ? (&s_data[14:10]) : (&s_data[14:7])) : (&s_data[30:23]);
  wire source_nan=s_to_fp32 ?
    (s_fp16 ? (|s_data[9:0]) : (|s_data[6:0])) : (|s_data[22:0]);
  wire signed [11:0] effective_source=source_exponent==0 ?
    12'sd1 : $signed({4'd0,source_exponent});
  wire signed [11:0] bias_adjust=s_fp16 ?
    (s_to_fp32 ? 12'sd112 : -12'sd112) : 12'sd0;
  wire signed [11:0] normalized_exponent=
    effective_source+bias_adjust-$signed({6'd0,leading});
  wire [11:0] shift_distance=12'sd1-exponent1;
  wire [11:0] result_exponent=exponent3+
    (expand3 ? {11'd0,rounded3[24]} :
      (half3 ? {11'd0,rounded3[11]} : {11'd0,rounded3[8]}));
  wire [23:0] result_significand=expand3 ?
    (rounded3[24] ? rounded3[24:1] : rounded3[23:0]) :
    (half3 ? {13'd0,(rounded3[11] ? rounded3[11:1] : rounded3[10:0])} :
      {16'd0,(rounded3[8] ? rounded3[8:1] : rounded3[7:0])});
  wire result_overflow=expand3 ? result_exponent>=255 :
    (half3 ? result_exponent>=31 : result_exponent>=255);

  assign s_ready=rst_n && !annul && advance;
  assign m_valid=rst_n && !annul && valid[3];
  assign m_data=m_valid ? data4 : 32'd0;
  assign m_tag=m_valid ? tags[3] : 64'd0;
  assign m_error=m_valid && error4;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0;
      sign1<=0; sign2<=0; sign3<=0;
      expand1<=0; expand2<=0; expand3<=0;
      half1<=0; half2<=0; half3<=0;
      special1<=0; special2<=0; special3<=0;
      nan1<=0; nan2<=0; nan3<=0;
      significand1<=0; significand2<=0;
      exponent1<=0; exponent2<=0; exponent3<=0;
      rounded3<=0; data4<=0; error4<=0;
      for (i=0;i<4;i=i+1) tags[i]<=0;
    end else if (annul) begin
      valid<=0;
    end else if (advance) begin
      valid<={valid[2:0],s_valid};
      tags[0]<=s_tag;
      for (i=1;i<4;i=i+1) tags[i]<=tags[i-1];
      sign1<=s_to_fp32 ? s_data[15] : s_data[31];
      expand1<=s_to_fp32; half1<=s_fp16;
      special1<=source_special; nan1<=source_nan;
      significand1<={source_significand,3'd0} << leading;
      exponent1<=source_significand==0 ? 12'sd1 : normalized_exponent;

      sign2<=sign1; expand2<=expand1; half2<=half1;
      special2<=special1; nan2<=nan1;
      if (exponent1<1) begin
        significand2<=right_jam27(significand1,shift_distance);
        exponent2<=1;
      end else begin
        significand2<=significand1;
        exponent2<=exponent1;
      end

      sign3<=sign2; expand3<=expand2; half3<=half2;
      special3<=special2; nan3<=nan2; exponent3<=exponent2;
      if (expand2)
        rounded3<={1'b0,significand2[26:3]}+
          {24'd0,(significand2[2] &&
            (significand2[1] || significand2[0] || significand2[3]))};
      else if (half2)
        rounded3<={14'd0,significand2[26:16]}+
          {24'd0,(significand2[15] &&
            ((|significand2[14:0]) || significand2[16]))};
      else
        rounded3<={17'd0,significand2[26:19]}+
          {24'd0,(significand2[18] &&
            ((|significand2[17:0]) || significand2[19]))};

      error4<=special3 || (result_overflow && result_significand!=0);
      if (expand3) begin
        if (special3)
          data4<=nan3 ? 32'h7fc00000 : {sign3,8'hff,23'd0};
        else if (result_overflow && result_significand!=0)
          data4<={sign3,8'hff,23'd0};
        else if (!result_significand[23])
          data4<={sign3,8'd0,result_significand[22:0]};
        else data4<={sign3,result_exponent[7:0],result_significand[22:0]};
      end else if (half3) begin
        if (special3)
          data4<=nan3 ? 32'h00007e00 : {16'd0,sign3,5'h1f,10'd0};
        else if (result_overflow && result_significand!=0)
          data4<={16'd0,sign3,5'h1f,10'd0};
        else if (!result_significand[10])
          data4<={16'd0,sign3,5'd0,result_significand[9:0]};
        else data4<={16'd0,sign3,result_exponent[4:0],result_significand[9:0]};
      end else begin
        if (special3)
          data4<=nan3 ? 32'h00007fc0 : {16'd0,sign3,8'hff,7'd0};
        else if (result_overflow && result_significand!=0)
          data4<={16'd0,sign3,8'hff,7'd0};
        else if (!result_significand[7])
          data4<={16'd0,sign3,8'd0,result_significand[6:0]};
        else data4<={16'd0,sign3,result_exponent[7:0],result_significand[6:0]};
      end
    end
  end
endmodule
