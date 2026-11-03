module anvil_d2_fp8_dequant (
  input wire clk, rst_n, flush,
  input wire in_valid,
  output wire in_ready,
  input wire [7:0] in_fp8,
  input wire [31:0] in_scale,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_fp32,
  output wire [15:0] out_bf16,
  output wire out_error
);
  reg armed;
  reg [3:0] valid;
  reg s0_sign, s0_error;
  reg [3:0] s0_fp8_sig;
  reg [23:0] s0_scale_sig;
  reg signed [10:0] s0_exponent;
  reg s1_sign, s1_error;
  reg [27:0] s1_product;
  reg signed [10:0] s1_exponent;
  reg [31:0] s2_fp32, s3_fp32;
  reg [15:0] s3_bf16;
  reg s2_error, s3_error;

  wire advance3=!valid[3] || out_ready;
  wire advance2=!valid[2] || advance3;
  wire advance1=!valid[1] || advance2;
  wire advance0=!valid[0] || advance1;
  wire enabled=rst_n && armed && !flush;
  wire input_transfer=in_valid && in_ready;
  wire [3:0] fp8_sig=in_fp8[6:3]==0 ?
    {1'b0,in_fp8[2:0]} : {1'b1,in_fp8[2:0]};
  wire [23:0] scale_sig=in_scale[30:23]==0 ?
    {1'b0,in_scale[22:0]} : {1'b1,in_scale[22:0]};
  wire signed [10:0] fp8_exponent=in_fp8[6:3]==0 ?
    -11'sd9 : $signed({7'd0,in_fp8[6:3]})-11'sd10;
  wire signed [10:0] scale_exponent=in_scale[30:23]==0 ?
    -11'sd149 : $signed({3'd0,in_scale[30:23]})-11'sd150;
  wire classification_error=(in_fp8[6:0]==7'h7f) ||
    in_scale[31] || in_scale[30:23]==8'hff || in_scale[30:0]==0;
  wire [27:0] exact_product=s0_scale_sig*s0_fp8_sig;

  function automatic [4:0] leading_bit28(input [27:0] magnitude);
    reg [31:0] value;
    reg [4:0] index;
    begin
      value={4'd0,magnitude};
      index=0;
      if (|value[31:16]) begin value=value>>16; index=index+5'd16; end
      if (|value[15:8]) begin value=value>>8; index=index+5'd8; end
      if (|value[7:4]) begin value=value>>4; index=index+5'd4; end
      if (|value[3:2]) begin value=value>>2; index=index+5'd2; end
      if (value[1]) index=index+5'd1;
      leading_bit28=index;
    end
  endfunction

  function automatic [32:0] rounded_binary32(
    input sign_bit,
    input [27:0] magnitude,
    input signed [10:0] exponent,
    input invalid
  );
    integer leading, unbiased, shift;
    reg [31:0] rounded, remainder, half, extended;
    reg [7:0] encoded_exponent;
    reg [31:0] bits;
    reg failed;
    begin
      leading={27'd0,leading_bit28(magnitude)};
      unbiased=$signed(exponent)+leading;
      shift=0;
      rounded=0;
      remainder=0;
      half=0;
      extended={4'd0,magnitude};
      encoded_exponent=0;
      bits={sign_bit,31'd0};
      failed=invalid;
      if (!invalid && magnitude!=0) begin
        if (unbiased>=-126) shift=leading-23;
        else shift=-149-$signed(exponent);
        if (shift>0) begin
          if (shift<32) begin
            rounded=extended>>shift;
            half=32'd1<<(shift-1);
            remainder=extended&((32'd1<<shift)-1'b1);
            if (remainder>half || (remainder==half && rounded[0]))
              rounded=rounded+1'b1;
          end
        end else rounded=extended<<(-shift);
        if (unbiased>=-126) begin
          if (rounded[24]) begin
            rounded=rounded>>1;
            unbiased=unbiased+1;
          end
          if (unbiased>127) failed=1;
          else begin
            encoded_exponent=unbiased+127;
            bits={sign_bit,encoded_exponent,rounded[22:0]};
          end
        end else if (rounded[23]) bits={sign_bit,8'd1,23'd0};
        else bits={sign_bit,8'd0,rounded[22:0]};
      end
      rounded_binary32={failed,failed ? 32'd0 : bits};
    end
  endfunction

  function automatic [16:0] rounded_bf16(input [31:0] bits, input invalid);
    reg [15:0] rounded;
    reg increment, failed;
    begin
      increment=bits[15] && ((|bits[14:0]) || bits[16]);
      rounded=bits[31:16]+{15'd0,increment};
      failed=invalid || rounded[14:7]==8'hff;
      rounded_bf16={failed,failed ? 16'd0 : rounded};
    end
  endfunction

  wire [32:0] binary32_result=rounded_binary32(
    s1_sign,s1_product,s1_exponent,s1_error);
  wire [16:0] bf16_result=rounded_bf16(s2_fp32,s2_error);
  assign in_ready=enabled && advance0;
  assign out_valid=enabled && valid[3];
  assign out_fp32=out_valid ? s3_fp32 : 32'd0;
  assign out_bf16=out_valid ? s3_bf16 : 16'd0;
  assign out_error=out_valid && s3_error;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      armed<=0; valid<=0;
      s0_sign<=0; s0_error<=0; s0_fp8_sig<=0; s0_scale_sig<=0; s0_exponent<=0;
      s1_sign<=0; s1_error<=0; s1_product<=0; s1_exponent<=0;
      s2_fp32<=0; s2_error<=0; s3_fp32<=0; s3_bf16<=0; s3_error<=0;
    end else begin
      armed<=1;
      if (flush) begin
        valid<=0;
        s0_sign<=0; s0_error<=0; s0_fp8_sig<=0; s0_scale_sig<=0; s0_exponent<=0;
        s1_sign<=0; s1_error<=0; s1_product<=0; s1_exponent<=0;
        s2_fp32<=0; s2_error<=0; s3_fp32<=0; s3_bf16<=0; s3_error<=0;
      end else begin
        if (advance0) begin
          valid[0]<=input_transfer;
          if (input_transfer) begin
            s0_sign<=in_fp8[7]; s0_error<=classification_error;
            s0_fp8_sig<=fp8_sig; s0_scale_sig<=scale_sig;
            s0_exponent<=fp8_exponent+scale_exponent;
          end
        end
        if (advance1) begin
          valid[1]<=valid[0];
          if (valid[0]) begin
            s1_sign<=s0_sign; s1_error<=s0_error;
            s1_product<=exact_product; s1_exponent<=s0_exponent;
          end
        end
        if (advance2) begin
          valid[2]<=valid[1];
          if (valid[1]) begin
            s2_fp32<=binary32_result[31:0]; s2_error<=binary32_result[32];
          end
        end
        if (advance3) begin
          valid[3]<=valid[2];
          if (valid[2]) begin
            s3_fp32<=bf16_result[16] ? 32'd0 : s2_fp32;
            s3_bf16<=bf16_result[15:0]; s3_error<=bf16_result[16];
          end
        end
      end
    end
  end
endmodule
