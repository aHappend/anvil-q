module anvil_q2_ht_tensor_lane (
  input wire clk, rst_n, advance,
  input wire keep, mode,
  input wire signed [31:0] activation,
  input wire [3:0] weight4, zero4,
  input wire [15:0] scale16, weight_bf16,
  output wire signed [68:0] product,
  output wire [31:0] product_fp32,
  output wire error
);
  import anvil_q2_ht_fp_pkg::*;
  reg signed [31:0] act0, act1, act2, act3;
  reg [3:0] weight0, zero0;
  reg [15:0] scale0, bf0;
  reg mode0;
  reg signed [4:0] delta1;
  reg [31:0] scale1;
  reg signed [36:0] dequant2, dequant3;
  reg signed [35:0] partial00_4, partial01_4, partial10_4, partial11_4;
  reg signed [52:0] lower5, upper5;
  reg signed [68:0] product6;

  reg [31:0] act_magnitude1;
  reg [5:0] act_leading1;
  reg act_sign1, act_sign2, act_sign3;
  reg [8:0] act_rounded2;
  reg [7:0] act_exponent2;
  reg act_zero2;
  reg [7:0] act_significand3;
  reg signed [10:0] act_factor_exponent3;
  reg [7:0] weight_significand1, weight_significand2, weight_significand3;
  reg signed [10:0] weight_exponent1, weight_exponent2, weight_exponent3;
  reg weight_sign1, weight_sign2, weight_sign3;
  reg [15:0] fp_magnitude4;
  reg signed [10:0] fp_exponent4;
  reg fp_sign4, fp_sign5;
  reg [26:0] fp_significand5;
  reg [9:0] fp_exponent5;
  reg [31:0] fp_result6;
  reg error1, error2, error3, error4, error5, error6;

  wire [31:0] act_magnitude0 = act0[31] ? (~act0+32'd1) : act0;
  wire [31:0] normalized_act1 = act_magnitude1 << act_leading1;
  wire act_round_up1 = normalized_act1[23] &&
    ((|normalized_act1[22:0]) || normalized_act1[24]);
  wire [7:0] act_biased_exponent1 = 8'd142-{2'd0,act_leading1};
  wire [5:0] product_leading4 = leading32({fp_magnitude4,16'd0});
  wire [26:0] normalized_product4 =
    {fp_magnitude4,11'd0} << product_leading4;
  wire signed [10:0] product_biased_exponent4 =
    fp_exponent4+11'sd142-$signed({5'd0,product_leading4});
  wire signed [10:0] product_underflow_distance4 =
    11'sd1-product_biased_exponent4;
  wire [32:0] fp_packed5 = pack_fp32(fp_sign5,fp_exponent5,fp_significand5);

  wire signed [18:0] weight_low3 = $signed({1'b0,dequant3[17:0]});
  wire signed [18:0] weight_high3 = $signed(dequant3[36:18]);
  wire signed [16:0] act_low3 = $signed({1'b0,act3[15:0]});
  wire signed [16:0] act_high3 = $signed({act3[31],act3[31:16]});
  wire signed [52:0] partial00_ext4 = {{17{partial00_4[35]}},partial00_4};
  wire signed [52:0] partial01_ext4 = {{17{partial01_4[35]}},partial01_4};
  wire signed [52:0] partial10_ext4 = {{17{partial10_4[35]}},partial10_4};
  wire signed [52:0] partial11_ext4 = {{17{partial11_4[35]}},partial11_4};
  wire signed [68:0] lower_ext5 = {{16{lower5[52]}},lower5};
  wire signed [68:0] upper_ext5 = {{16{upper5[52]}},upper5};

  function automatic [31:0] finite_scale_q16(input [15:0] value);
    reg [31:0] mantissa;
    reg [4:0] left_distance, right_distance;
    begin
      mantissa = {21'd0,(|value[14:10]),value[9:0]};
      left_distance = value[14:10]-5'd9;
      right_distance = value[14:10] == 0 ? 5'd8 : 5'd9-value[14:10];
      if (value[14:10] >= 9) finite_scale_q16 = mantissa << left_distance;
      else finite_scale_q16 =
        (mantissa+(32'd1 << (right_distance-5'd1))) >> right_distance;
    end
  endfunction

  assign product = rst_n ? product6 : 69'sd0;
  assign product_fp32 = rst_n ? fp_result6 : 32'd0;
  assign error = rst_n && error6;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      act0 <= 0; act1 <= 0; act2 <= 0; act3 <= 0;
      weight0 <= 0; zero0 <= 0; scale0 <= 0; bf0 <= 0; mode0 <= 0;
      delta1 <= 0; scale1 <= 0; dequant2 <= 0; dequant3 <= 0;
      partial00_4 <= 0; partial01_4 <= 0; partial10_4 <= 0; partial11_4 <= 0;
      lower5 <= 0; upper5 <= 0; product6 <= 0;
      act_magnitude1 <= 0; act_leading1 <= 0;
      act_sign1 <= 0; act_sign2 <= 0; act_sign3 <= 0;
      act_rounded2 <= 0; act_exponent2 <= 0; act_zero2 <= 0;
      act_significand3 <= 0; act_factor_exponent3 <= 0;
      weight_significand1 <= 0; weight_significand2 <= 0; weight_significand3 <= 0;
      weight_exponent1 <= 0; weight_exponent2 <= 0; weight_exponent3 <= 0;
      weight_sign1 <= 0; weight_sign2 <= 0; weight_sign3 <= 0;
      fp_magnitude4 <= 0; fp_exponent4 <= 0; fp_sign4 <= 0;
      fp_significand5 <= 0; fp_exponent5 <= 0; fp_sign5 <= 0; fp_result6 <= 0;
      error1 <= 0; error2 <= 0; error3 <= 0;
      error4 <= 0; error5 <= 0; error6 <= 0;
    end else if (advance) begin
      act0 <= keep ? activation : 32'sd0;
      weight0 <= keep && !mode ? weight4 : 4'd0;
      zero0 <= keep && !mode ? zero4 : 4'd0;
      scale0 <= keep && !mode ? scale16 : 16'd0;
      bf0 <= keep && mode ? weight_bf16 : 16'd0;
      mode0 <= mode;

      act1 <= act0;
      delta1 <= $signed({1'b0,weight0})-$signed({1'b0,zero0});
      scale1 <= finite_scale_q16(scale0);
      act_magnitude1 <= act_magnitude0;
      act_leading1 <= leading32(act_magnitude0);
      act_sign1 <= act0[31];
      weight_significand1 <= {(|bf0[14:7]),bf0[6:0]};
      if (bf0[14:7] == 0) weight_exponent1 <= -11'sd133;
      else weight_exponent1 <= $signed({3'd0,bf0[14:7]})-11'sd134;
      weight_sign1 <= bf0[15];
      if (mode0) error1 <= bf0[14:7] == 8'hff;
      else error1 <= scale0[14:10] == 5'd31 ||
        (scale0[15] && (|scale0[14:0]));

      act2 <= act1;
      dequant2 <= $signed(delta1)*$signed({1'b0,scale1});
      act_rounded2 <= {1'b0,normalized_act1[31:24]}+{8'd0,act_round_up1};
      act_exponent2 <= act_biased_exponent1;
      act_zero2 <= act_magnitude1 == 0;
      act_sign2 <= act_sign1;
      weight_significand2 <= weight_significand1;
      weight_exponent2 <= weight_exponent1;
      weight_sign2 <= weight_sign1;
      error2 <= error1;

      act3 <= act2;
      dequant3 <= dequant2;
      if (act_zero2) begin
        act_significand3 <= 0;
        act_factor_exponent3 <= 0;
      end else if (act_rounded2[8]) begin
        act_significand3 <= 8'h80;
        act_factor_exponent3 <= $signed({3'd0,act_exponent2})-11'sd133;
      end else begin
        act_significand3 <= act_rounded2[7:0];
        act_factor_exponent3 <= $signed({3'd0,act_exponent2})-11'sd134;
      end
      act_sign3 <= act_sign2;
      weight_significand3 <= weight_significand2;
      weight_exponent3 <= weight_exponent2;
      weight_sign3 <= weight_sign2;
      error3 <= error2;

      partial00_4 <= weight_low3*act_low3;
      partial01_4 <= weight_low3*act_high3;
      partial10_4 <= weight_high3*act_low3;
      partial11_4 <= weight_high3*act_high3;
      fp_magnitude4 <= act_significand3*weight_significand3;
      fp_exponent4 <= act_factor_exponent3+weight_exponent3;
      fp_sign4 <= act_sign3 ^ weight_sign3;
      error4 <= error3;

      lower5 <= partial00_ext4+(partial10_ext4 <<< 18);
      upper5 <= partial01_ext4+(partial11_ext4 <<< 18);
      fp_sign5 <= fp_sign4;
      if (fp_magnitude4 == 0) begin
        fp_significand5 <= 0;
        fp_exponent5 <= 1;
      end else if (product_biased_exponent4 < 1) begin
        fp_significand5 <= right_jam27(
          normalized_product4,product_underflow_distance4[8:0]);
        fp_exponent5 <= 1;
      end else begin
        fp_significand5 <= normalized_product4;
        fp_exponent5 <= product_biased_exponent4[9:0];
      end
      error5 <= error4;

      product6 <= lower_ext5+(upper_ext5 <<< 16);
      fp_result6 <= fp_packed5[31:0];
      error6 <= error5 || fp_packed5[32];
    end
  end
endmodule
