package anvil_q1_ht_numeric_pkg;
  localparam [3:0] MATH_ADD = 0, MATH_SUB = 1, MATH_MUL = 2,
                   MATH_ROUND_SHIFT = 3, MATH_ROUND_DIV = 4,
                   MATH_TRUNC_DIV = 5, MATH_UDIV = 6, MATH_ISQRT = 7;

  function automatic signed [31:0] sat32(input signed [127:0] value);
    begin
      if (value > 128'sd2147483647) sat32 = 32'sh7fffffff;
      else if (value < -128'sd2147483648) sat32 = 32'sh80000000;
      else sat32 = value[31:0];
    end
  endfunction

  function automatic fp16_invalid(input [15:0] value);
    begin fp16_invalid = value[14:10] == 5'd31; end
  endfunction

  function automatic scale_invalid(input [15:0] value);
    begin
      scale_invalid = fp16_invalid(value) || (value[15] && value[14:0] != 0);
    end
  endfunction

  function automatic [31:0] fp16_scale(input [15:0] value);
    reg [31:0] magnitude;
    integer shift;
    begin
      magnitude = value[14:10] == 0 ? {22'd0, value[9:0]} :
                                     {21'd0, 1'b1, value[9:0]};
      shift = value[14:10] == 0 ? -8 : int'({1'b0, value[14:10]}) - 9;
      if (shift >= 0) magnitude = magnitude << shift;
      else magnitude = (magnitude + (32'd1 << (-shift-1))) >> (-shift);
      fp16_scale = magnitude;
    end
  endfunction

  function automatic signed [31:0] fp16_q16(input [15:0] value);
    reg [31:0] magnitude;
    begin
      magnitude = fp16_scale(value);
      if (value[15]) begin
        if (magnitude >= 32'h80000000) fp16_q16 = 32'sh80000000;
        else fp16_q16 = -$signed(magnitude);
      end else begin
        if (magnitude > 32'h7fffffff) fp16_q16 = 32'sh7fffffff;
        else fp16_q16 = $signed(magnitude);
      end
    end
  endfunction

  function automatic bf16_invalid(input [15:0] value);
    begin bf16_invalid = value[14:7] == 8'hff; end
  endfunction

  function automatic signed [31:0] bf16_q16(input [15:0] value);
    reg [31:0] magnitude;
    integer shift;
    begin
      magnitude = value[14:7] == 0 ? {25'd0, value[6:0]} :
                                    {24'd0, 1'b1, value[6:0]};
      shift = value[14:7] == 0 ? -117 : int'({1'b0, value[14:7]}) - 118;
      if (shift > 23) begin
        bf16_q16 = value[15] ? 32'sh80000000 : 32'sh7fffffff;
      end else begin
        if (shift >= 0) magnitude = magnitude << shift;
        else if (shift < -8) magnitude = 0;
        else magnitude = (magnitude + (32'd1 << (-shift-1))) >> (-shift);
        if (value[15]) begin
          if (magnitude >= 32'h80000000) bf16_q16 = 32'sh80000000;
          else bf16_q16 = -$signed(magnitude);
        end else begin
          if (magnitude > 32'h7fffffff) bf16_q16 = 32'sh7fffffff;
          else bf16_q16 = $signed(magnitude);
        end
      end
    end
  endfunction

  function automatic [4:0] awq_shift(input [2:0] lane);
    begin awq_shift = {lane[0], lane[2:1], 2'b00}; end
  endfunction
endpackage
