package anvil_q4_fp_pkg;
  function automatic [36:0] narrow_fp8(input [31:0] x);
    reg [35:0] unpacked;
    reg signed [11:0] exponent;
    reg [26:0] significand;
    reg [3:0] rounded;
    reg [4:0] encoded_exponent;
    reg [7:0] bits;
    reg [4:0] exceptions;
    reg inexact, increment;
    begin
      unpacked=unpack_normalized(x);
      exponent=$signed(unpacked[35:24]);
      significand={unpacked[23:0],3'd0};
      rounded=0; encoded_exponent=0; exceptions=0;
      bits={x[31],7'd0}; inexact=0; increment=0;
      if (is_nan(x)) begin bits=8'h7e; exceptions[4]=is_signaling_nan(x); end
      else if (is_infinity(x)) bits={x[31],5'h1f,2'd0};
      else if (!is_zero(x)) begin
        if (exponent < -12'sd14) begin
          significand=shift_right_jam27(significand,$unsigned(-12'sd14-exponent));
          exponent=-12'sd14;
        end
        inexact=|significand[23:0];
        increment=significand[23] && (|significand[22:0] || significand[24]);
        rounded={1'b0,significand[26:24]}+{3'd0,increment};
        if (rounded[3]) begin rounded=rounded>>1; exponent=exponent+12'sd1; end
        if (exponent>12'sd15) begin bits={x[31],5'h1f,2'd0}; exceptions=5'b00101; end
        else begin
          if (rounded[2]) encoded_exponent=5'(exponent+12'sd15);
          bits={x[31],encoded_exponent,rounded[1:0]};
          exceptions[0]=inexact;
          exceptions[1]=inexact && encoded_exponent==0;
        end
      end
      narrow_fp8={exceptions,24'd0,bits};
    end
  endfunction
  function automatic is_nan(input [31:0] x);
    is_nan = x[30:23] == 8'hff && x[22:0] != 0;
  endfunction

  function automatic is_signaling_nan(input [31:0] x);
    is_signaling_nan = is_nan(x) && !x[22];
  endfunction

  function automatic is_infinity(input [31:0] x);
    is_infinity = x[30:0] == 31'h7f800000;
  endfunction

  function automatic is_zero(input [31:0] x);
    is_zero = x[30:0] == 0;
  endfunction

  function automatic [5:0] leading_zeros32(input [31:0] value);
    reg [31:0] work;
    reg [5:0] count;
    begin
      work = value;
      count = 0;
      if (value == 0) count = 32;
      else begin
        if (work[31:16] == 0) begin count = count + 16; work = work << 16; end
        if (work[31:24] == 0) begin count = count + 8; work = work << 8; end
        if (work[31:28] == 0) begin count = count + 4; work = work << 4; end
        if (work[31:30] == 0) begin count = count + 2; work = work << 2; end
        if (!work[31]) count = count + 1;
      end
      leading_zeros32 = count;
    end
  endfunction

  function automatic [35:0] unpack_normalized(input [31:0] x);
    reg signed [11:0] exponent;
    reg [23:0] significand;
    reg [5:0] shift;
    begin
      shift = 0;
      if (x[30:23] != 0) begin
        exponent = $signed({4'b0, x[30:23]}) - 12'sd127;
        significand = {1'b1, x[22:0]};
      end else if (x[22:0] != 0) begin
        shift = leading_zeros32({9'd0, x[22:0]}) - 6'd8;
        exponent = -12'sd126 - $signed({6'd0, shift});
        significand = {1'b0, x[22:0]} << shift;
      end else begin
        exponent = -12'sd126;
        significand = 0;
      end
      unpack_normalized = {exponent, significand};
    end
  endfunction

  function automatic [26:0] shift_right_jam27(
    input [26:0] value, input [11:0] distance
  );
    reg [26:0] shifted, mask;
    begin
      shifted = value;
      mask = 0;
      if (distance >= 27) shifted = {26'd0, |value};
      else if (distance != 0) begin
        mask = (27'd1 << distance[4:0]) - 27'd1;
        shifted = value >> distance[4:0];
        shifted[0] = shifted[0] | (|(value & mask));
      end
      shift_right_jam27 = shifted;
    end
  endfunction

  // sig[26] is the hidden bit; sig[2:0] carry guard, round and sticky.
  function automatic [36:0] round_pack32(
    input sign, input signed [11:0] exponent, input [26:0] sig
  );
    reg signed [11:0] e;
    reg [26:0] extended;
    reg [24:0] rounded;
    reg increment, inexact;
    reg [7:0] encoded_exponent;
    reg [31:0] bits;
    reg [4:0] flags;
    begin
      e = exponent;
      extended = sig;
      rounded = 0;
      encoded_exponent = 0;
      increment = 0;
      inexact = 0;
      bits = {sign, 31'd0};
      flags = 0;
      if (sig != 0) begin
        if (e < -12'sd126) begin
          extended = shift_right_jam27(sig, $unsigned(-12'sd126 - e));
          e = -12'sd126;
        end
        inexact = |extended[2:0];
        increment = extended[2] && (extended[1] || extended[0] || extended[3]);
        rounded = {1'b0, extended[26:3]} + {24'd0, increment};
        if (rounded[24]) begin
          rounded = rounded >> 1;
          e = e + 12'sd1;
        end
        if (e > 12'sd127) begin
          bits = {sign, 8'hff, 23'd0};
          flags = 5'b00101;
        end else begin
          if (e == -12'sd126 && !rounded[23]) encoded_exponent = 0;
          else encoded_exponent = 8'(e + 12'sd127);
          bits = {sign, encoded_exponent, rounded[22:0]};
          flags[0] = inexact;
          flags[1] = inexact && encoded_exponent == 0;
        end
      end
      round_pack32 = {flags, bits};
    end
  endfunction

  function automatic [36:0] widen_bf16(input [15:0] x);
    reg [31:0] bits;
    reg [4:0] flags;
    begin
      bits = {x, 16'd0};
      flags = 0;
      if (x[14:7] == 8'hff && x[6:0] != 0) begin
        bits = 32'h7fc00000;
        flags[4] = !x[6];
      end
      widen_bf16 = {flags, bits};
    end
  endfunction

  function automatic [36:0] widen_fp16(input [15:0] x);
    reg [31:0] bits;
    reg [4:0] flags;
    reg [10:0] significand;
    reg [7:0] exponent;
    reg [5:0] shift;
    begin
      bits = {x[15], 31'd0};
      flags = 0;
      significand = 0;
      exponent = 0;
      shift = 0;
      if (x[14:10] == 5'd31) begin
        if (x[9:0] == 0) bits = {x[15], 8'hff, 23'd0};
        else begin
          bits = 32'h7fc00000;
          flags[4] = !x[9];
        end
      end else if (x[14:10] != 0) begin
        exponent = {3'd0, x[14:10]} + 8'd112;
        bits = {x[15], exponent, x[9:0], 13'd0};
      end else if (x[9:0] != 0) begin
        shift = leading_zeros32({22'd0, x[9:0]}) - 6'd21;
        significand = {1'b0, x[9:0]} << shift;
        exponent = 8'd113 - {2'd0, shift};
        bits = {x[15], exponent, significand[9:0], 13'd0};
      end
      widen_fp16 = {flags, bits};
    end
  endfunction

  function automatic [36:0] narrow_bf16(input [31:0] x);
    reg increment, inexact;
    reg [15:0] rounded;
    reg [4:0] flags;
    begin
      increment = x[15] && ((|x[14:0]) || x[16]);
      inexact = |x[15:0];
      rounded = x[31:16] + {15'd0, increment};
      flags = 0;
      if (is_nan(x)) begin
        rounded = 16'h7fc0;
        flags[4] = is_signaling_nan(x);
      end else if (is_infinity(x)) rounded = x[31:16];
      else begin
        flags[0] = inexact;
        flags[1] = inexact && rounded[14:7] == 0;
        if (rounded[14:7] == 8'hff) flags = 5'b00101;
      end
      narrow_bf16 = {flags, 16'd0, rounded};
    end
  endfunction

  function automatic [36:0] narrow_fp16(input [31:0] x);
    reg [35:0] unpacked;
    reg signed [11:0] e;
    reg [26:0] extended;
    reg [11:0] rounded;
    reg increment, inexact;
    reg [4:0] encoded_exponent, flags;
    reg [15:0] bits;
    begin
      unpacked = unpack_normalized(x);
      e = $signed(unpacked[35:24]);
      extended = shift_right_jam27({unpacked[23:0], 3'd0}, 12'd13);
      rounded = 0;
      increment = 0;
      inexact = 0;
      encoded_exponent = 0;
      bits = {x[31], 15'd0};
      flags = 0;
      if (is_nan(x)) begin
        bits = 16'h7e00;
        flags[4] = is_signaling_nan(x);
      end else if (is_infinity(x)) bits = {x[31], 5'h1f, 10'd0};
      else if (!is_zero(x)) begin
        if (e < -12'sd14) begin
          extended = shift_right_jam27(extended, $unsigned(-12'sd14 - e));
          e = -12'sd14;
        end
        inexact = |extended[2:0];
        increment = extended[2] && (extended[1] || extended[0] || extended[3]);
        rounded = {1'b0, extended[13:3]} + {11'd0, increment};
        if (rounded[11]) begin
          rounded = rounded >> 1;
          e = e + 12'sd1;
        end
        if (e > 12'sd15) begin
          bits = {x[31], 5'h1f, 10'd0};
          flags = 5'b00101;
        end else begin
          if (e == -12'sd14 && !rounded[10]) encoded_exponent = 0;
          else encoded_exponent = 5'(e + 12'sd15);
          bits = {x[31], encoded_exponent, rounded[9:0]};
          flags[0] = inexact;
          flags[1] = inexact && encoded_exponent == 0;
        end
      end
      narrow_fp16 = {flags, 16'd0, bits};
    end
  endfunction

  function automatic [36:0] int32_to_fp32(input [31:0] x);
    reg [31:0] magnitude;
    reg [5:0] leading, position;
    reg [26:0] sig;
    reg [31:0] shifted, mask;
    reg signed [11:0] exponent;
    begin
      magnitude = x[31] ? (~x + 32'd1) : x;
      leading = leading_zeros32(magnitude);
      position = 0;
      sig = 0;
      shifted = 0;
      mask = 0;
      exponent = 0;
      if (magnitude != 0) begin
        position = 6'd31 - leading;
        exponent = $signed({6'd0, position});
        if (position > 26) begin
          shifted = magnitude >> (position - 6'd26);
          mask = (32'd1 << (position - 6'd26)) - 32'd1;
          sig = shifted[26:0];
          sig[0] = sig[0] || (|(magnitude & mask));
        end else sig = magnitude[26:0] << (6'd26 - position);
      end
      int32_to_fp32 = round_pack32(x[31], exponent, sig);
    end
  endfunction

  function automatic ordered_less(input [31:0] a, input [31:0] b);
    begin
      if (is_nan(a) || is_nan(b) || (is_zero(a) && is_zero(b))) ordered_less = 1'b0;
      else if (a[31] != b[31]) ordered_less = a[31];
      else if (a[31]) ordered_less = a[30:0] > b[30:0];
      else ordered_less = a[30:0] < b[30:0];
    end
  endfunction

  function automatic ordered_equal(input [31:0] a, input [31:0] b);
    ordered_equal = !is_nan(a) && !is_nan(b) &&
      (a == b || (is_zero(a) && is_zero(b)));
  endfunction
endpackage
