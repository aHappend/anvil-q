package anvil_q3_fp_pkg;
  localparam [31:0] CANONICAL_NAN = 32'h7fc00000;

  function automatic is_nan32(input logic [31:0] x);
    is_nan32 = (&x[30:23]) && (|x[22:0]);
  endfunction

  function automatic is_snan32(input logic [31:0] x);
    is_snan32 = is_nan32(x) && !x[22];
  endfunction

  function automatic is_inf32(input logic [31:0] x);
    is_inf32 = x[30:0] == 31'h7f800000;
  endfunction

  function automatic is_zero32(input logic [31:0] x);
    is_zero32 = x[30:0] == 0;
  endfunction

  function automatic scale_invalid(input logic [15:0] x);
    scale_invalid = (&x[14:10]) || (x[15] && (|x[14:0]));
  endfunction

  function automatic [5:0] clz32(input logic [31:0] x);
    reg [31:0] work;
    reg [5:0] count;
    begin
      work = x;
      count = 0;
      if (work[31:16] == 0) begin
        count = count + 6'd16;
        work = work << 16;
      end
      if (work[31:24] == 0) begin
        count = count + 6'd8;
        work = work << 8;
      end
      if (work[31:28] == 0) begin
        count = count + 6'd4;
        work = work << 4;
      end
      if (work[31:30] == 0) begin
        count = count + 6'd2;
        work = work << 2;
      end
      if (!work[31]) count = count + 6'd1;
      clz32 = x == 0 ? 6'd32 : count;
    end
  endfunction

  function automatic [4:0] clz24(input logic [23:0] x);
    reg [5:0] count;
    begin
      count = clz32({x,8'd0});
      clz24 = x == 0 ? 5'd24 : count[4:0];
    end
  endfunction

  function automatic [4:0] clz27(input logic [26:0] x);
    reg [5:0] count;
    begin
      count = clz32({x,5'd0});
      clz27 = x == 0 ? 5'd27 : count[4:0];
    end
  endfunction

  function automatic [26:0] shift_jam27(
    input logic [26:0] x, input logic [9:0] distance
  );
    reg [26:0] discarded;
    begin
      discarded = 0;
      if (distance == 0) shift_jam27 = x;
      else if (distance >= 27) shift_jam27 = {26'd0,|x};
      else begin
        discarded = x << (10'd27-distance);
        shift_jam27 = (x >> distance) | {26'd0,|discarded};
      end
    end
  endfunction

  // sig[26] is the hidden bit and sig[2:0] are guard, round and sticky.
  function automatic [36:0] round32(
    input logic sign,
    input logic signed [12:0] exponent,
    input logic [26:0] sig
  );
    reg signed [12:0] e;
    reg [26:0] work;
    reg [24:0] rounded;
    reg [9:0] distance;
    reg [7:0] encoded_exponent;
    reg [4:0] flags;
    reg [31:0] value;
    begin
      e = exponent;
      work = sig;
      distance = 0;
      encoded_exponent = 0;
      flags = 0;
      if (e < -13'sd126) begin
        distance = 10'(-13'sd126-e);
        work = shift_jam27(work,distance);
        e = -13'sd126;
      end
      flags[0] = |work[2:0];
      rounded = {1'b0,work[26:3]} +
        {24'd0,(work[2] && (work[1] || work[0] || work[3]))};
      if (rounded[24]) begin
        rounded = rounded >> 1;
        e = e + 13'sd1;
      end
      if (e > 13'sd127) begin
        value = {sign,8'hff,23'd0};
        flags = 5'b00101;
      end else begin
        if (rounded[23]) encoded_exponent = 8'(e+13'sd127);
        flags[1] = flags[0] && !rounded[23];
        value = {sign,encoded_exponent,rounded[22:0]};
      end
      round32 = {flags,value};
    end
  endfunction

  function automatic [31:0] widen16(
    input logic [15:0] x, input logic fp16
  );
    reg [23:0] sig;
    reg [4:0] leading;
    reg [7:0] exponent;
    begin
      sig = 0;
      leading = 0;
      exponent = 0;
      if (!fp16) widen16 = {x,16'd0};
      else if (&x[14:10])
        widen16 = {x[15],8'hff,x[9:0],13'd0};
      else if (x[14:0] == 0)
        widen16 = {x[15],31'd0};
      else if (x[14:10] != 0) begin
        exponent = {3'd0,x[14:10]} + 8'd112;
        widen16 = {x[15],exponent,x[9:0],13'd0};
      end else begin
        sig = {1'b0,x[9:0],13'd0};
        leading = clz24(sig);
        sig = sig << leading;
        exponent = 8'd113 - {3'd0,leading};
        widen16 = {x[15],exponent,sig[22:0]};
      end
    end
  endfunction

  function automatic [20:0] narrow16(
    input logic [31:0] x, input logic fp16
  );
    reg [23:0] sig;
    reg [4:0] leading;
    reg signed [12:0] e, minimum_e, maximum_e, bias;
    reg [9:0] distance;
    reg [26:0] work;
    reg [24:0] rounded;
    reg [7:0] encoded_exponent;
    reg [4:0] flags;
    reg [15:0] value;
    reg hidden, carry;
    begin
      sig = {x[30:23] != 0,x[22:0]};
      leading = clz24(sig);
      minimum_e = fp16 ? -13'sd14 : -13'sd126;
      maximum_e = fp16 ? 13'sd15 : 13'sd127;
      bias = fp16 ? 13'sd15 : 13'sd127;
      e = $signed({5'd0,(x[30:23] == 0 ? 8'd1 : x[30:23])}) -
        13'sd127 - $signed({8'd0,leading});
      sig = sig << leading;
      distance = fp16 ? 10'd13 : 10'd16;
      if (e < minimum_e) begin
        distance = distance + 10'(minimum_e-e);
        e = minimum_e;
      end
      work = shift_jam27({sig,3'd0},distance);
      rounded = {1'b0,work[26:3]} +
        {24'd0,(work[2] && (work[1] || work[0] || work[3]))};
      carry = fp16 ? rounded[11] : rounded[8];
      if (carry) begin
        rounded = rounded >> 1;
        e = e + 13'sd1;
      end
      hidden = fp16 ? rounded[10] : rounded[7];
      encoded_exponent = hidden ? 8'(e+bias) : 8'd0;
      flags = 0;
      flags[0] = |work[2:0];
      flags[1] = flags[0] && !hidden;
      value = fp16 ? {x[31],encoded_exponent[4:0],rounded[9:0]} :
        {x[31],encoded_exponent,rounded[6:0]};
      if (is_nan32(x)) begin
        value = fp16 ? 16'h7e00 : 16'h7fc0;
        flags = {is_snan32(x),4'd0};
      end else if (is_inf32(x)) begin
        value = fp16 ? {x[31],15'h7c00} : {x[31],15'h7f80};
        flags = 0;
      end else if (is_zero32(x)) begin
        value = {x[31],15'd0};
        flags = 0;
      end else if (e > maximum_e) begin
        value = fp16 ? {x[31],15'h7c00} : {x[31],15'h7f80};
        flags = 5'b00101;
      end
      narrow16 = {flags,value};
    end
  endfunction

  function automatic [31:0] delta32(input logic signed [4:0] delta);
    reg [4:0] magnitude;
    reg [23:0] sig;
    reg [7:0] exponent;
    begin
      magnitude = delta[4] ? -delta : delta;
      sig = 0;
      exponent = 0;
      if (magnitude[4]) begin
        sig = {19'd0,magnitude} << 19;
        exponent = 8'd131;
      end else if (magnitude[3]) begin
        sig = {19'd0,magnitude} << 20;
        exponent = 8'd130;
      end else if (magnitude[2]) begin
        sig = {19'd0,magnitude} << 21;
        exponent = 8'd129;
      end else if (magnitude[1]) begin
        sig = {19'd0,magnitude} << 22;
        exponent = 8'd128;
      end else if (magnitude[0]) begin
        sig = 24'h800000;
        exponent = 8'd127;
      end
      delta32 = magnitude == 0 ? 32'd0 : {delta[4],exponent,sig[22:0]};
    end
  endfunction

  function automatic [36:0] scale32(
    input logic [31:0] x, input logic signed [12:0] power
  );
    reg [23:0] sig;
    reg [4:0] leading;
    reg signed [12:0] exponent;
    begin
      sig = {x[30:23] != 0,x[22:0]};
      leading = clz24(sig);
      exponent = $signed({5'd0,(x[30:23] == 0 ? 8'd1 : x[30:23])}) -
        13'sd127 - $signed({8'd0,leading}) + power;
      sig = sig << leading;
      if (is_nan32(x))
        scale32 = {{is_snan32(x),4'd0},CANONICAL_NAN};
      else if (is_inf32(x) || is_zero32(x))
        scale32 = {5'd0,x};
      else scale32 = round32(x[31],exponent,{sig,3'd0});
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
endpackage
