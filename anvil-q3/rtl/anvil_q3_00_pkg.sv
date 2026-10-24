package anvil_q3_pkg;
  function automatic f16_invalid(input logic [15:0] h);
    f16_invalid = h[14:10] == 5'd31;
  endfunction

  function automatic f16_scale_invalid(input logic [15:0] h);
    f16_scale_invalid = f16_invalid(h) || (h[15] && h[14:0] != 15'd0);
  endfunction

  function automatic [31:0] f16_magnitude(input logic [15:0] h);
    reg [11:0] significand, rounded;
    reg [4:0] shift;
    begin
      significand = h[14:10] == 0 ? {2'b00,h[9:0]} : {1'b0,1'b1,h[9:0]};
      rounded = 0;
      shift = 0;
      if (f16_invalid(h)) f16_magnitude = 0;
      else if (h[14:10] >= 5'd9)
        f16_magnitude = {20'd0,significand} << (h[14:10]-5'd9);
      else begin
        shift = h[14:10] == 0 ? 5'd8 : 5'd9-h[14:10];
        rounded = (significand + (12'd1 << (shift-1'b1))) >> shift;
        f16_magnitude = {20'd0,rounded};
      end
    end
  endfunction

  function automatic [31:0] f16_scale(input logic [15:0] h);
    f16_scale = f16_scale_invalid(h) ? 32'd0 : f16_magnitude(h);
  endfunction

  function automatic signed [31:0] f16_q16(input logic [15:0] h);
    reg [31:0] magnitude;
    begin
      magnitude = f16_magnitude(h);
      if (f16_invalid(h)) f16_q16 = 0;
      else if (h[15]) begin
        if (magnitude >= 32'h80000000) f16_q16 = 32'sh80000000;
        else f16_q16 = -$signed(magnitude);
      end else begin
        if (magnitude[31]) f16_q16 = 32'sh7fffffff;
        else f16_q16 = $signed(magnitude);
      end
    end
  endfunction

  function automatic [4:0] awq_lane_shift(input logic [2:0] lane);
    begin
      case (lane)
        3'd0: awq_lane_shift = 5'd0;
        3'd1: awq_lane_shift = 5'd16;
        3'd2: awq_lane_shift = 5'd4;
        3'd3: awq_lane_shift = 5'd20;
        3'd4: awq_lane_shift = 5'd8;
        3'd5: awq_lane_shift = 5'd24;
        3'd6: awq_lane_shift = 5'd12;
        default: awq_lane_shift = 5'd28;
      endcase
    end
  endfunction

  function automatic signed [31:0] round_q32_to_q16(input logic signed [127:0] x);
    reg [47:0] magnitude, rounded;
    begin
      if (x>=128'sd140737488322560) round_q32_to_q16=32'sh7fffffff;
      else if (x<= -128'sd140737488322560) round_q32_to_q16=32'sh80000000;
      else begin
        magnitude=x[127] ? -x[47:0] : x[47:0];
        rounded=(magnitude+48'd32768)>>16;
        round_q32_to_q16=x[127] ? -$signed(rounded[31:0]) : $signed(rounded[31:0]);
      end
    end
  endfunction

  function automatic signed [31:0] round_shift_sat32(
    input logic signed [127:0] x, input integer shift
  );
    reg signed [127:0] threshold;
    reg [127:0] half, fraction;
    reg signed [32:0] integral, rounded;
    begin
      half=shift==0 ? 128'd0 : (128'd1 << (shift-1));
      threshold=(128'sd2147483647 << shift)+$signed(half);
      integral=$signed(x >>> shift);
      fraction=$unsigned(x)&((128'd1 << shift)-1'b1);
      rounded=integral;
      if (shift==0) begin
        if (x>128'sd2147483647) round_shift_sat32=32'sh7fffffff;
        else if (x< -128'sd2147483648) round_shift_sat32=32'sh80000000;
        else round_shift_sat32=x[31:0];
      end else if (x>=threshold) round_shift_sat32=32'sh7fffffff;
      else if (x<= -threshold) round_shift_sat32=32'sh80000000;
      else begin
        if ((!x[127] && fraction>=half) || (x[127] && fraction>half))
          rounded=integral+33'sd1;
        round_shift_sat32=rounded[31:0];
      end
    end
  endfunction
endpackage
