package anvil_q1_ht2_fp_pkg;
  localparam [31:0] FP32_QNAN = 32'h7fc00000;

  function automatic fp32_nonfinite(input [31:0] x);
    begin fp32_nonfinite = &x[30:23]; end
  endfunction

  function automatic fp32_nan(input [31:0] x);
    begin fp32_nan = (&x[30:23]) && (|x[22:0]); end
  endfunction

  function automatic [5:0] leading_bit64(input [63:0] x);
    reg [63:0] v;
    reg [5:0] p;
    begin
      v = x;
      p = 0;
      if (|v[63:32]) begin v = v >> 32; p = p + 32; end
      if (|v[31:16]) begin v = v >> 16; p = p + 16; end
      if (|v[15:8]) begin v = v >> 8; p = p + 8; end
      if (|v[7:4]) begin v = v >> 4; p = p + 4; end
      if (|v[3:2]) begin v = v >> 2; p = p + 2; end
      if (v[1]) p = p + 1;
      leading_bit64 = p;
    end
  endfunction

  function automatic [63:0] shift_rne64(input [63:0] x, input integer shift);
    reg [63:0] q;
    reg guard_bit, sticky_bit;
    begin
      q = 0;
      guard_bit = 0;
      sticky_bit = 0;
      if (shift <= 0) begin
        if (shift > -64) q = x << (-shift);
      end else if (shift <= 64) begin
        if (shift < 64) q = x >> shift;
        guard_bit = x[shift-1];
        if (shift > 1) sticky_bit = |(x & (64'hffffffffffffffff >> (65-shift)));
        q = q + {63'b0, guard_bit && (sticky_bit || q[0])};
      end
      shift_rne64 = q;
    end
  endfunction

  // The exact input value is (-1)^sign_bit * significand * 2^scale.
  function automatic [31:0] pack32(
    input sign_bit, input [63:0] significand, input integer scale
  );
    integer p, exponent, shift;
    reg [63:0] rounded;
    reg [7:0] encoded_exponent;
    begin
      p = {26'b0, leading_bit64(significand)};
      exponent = scale + p;
      shift = 0;
      rounded = 0;
      encoded_exponent = 0;
      if (significand == 0) pack32 = {sign_bit, 31'b0};
      else if (exponent > 127) pack32 = {sign_bit, 8'hff, 23'b0};
      else begin
        if (exponent < -126) shift = -149 - scale;
        else shift = p - 23;
        rounded = shift_rne64(significand, shift);
        if (exponent < -126) begin
          if (rounded[23]) encoded_exponent = 8'd1;
        end else begin
          if (rounded[24]) begin
            rounded = rounded >> 1;
            exponent = exponent + 1;
          end
          encoded_exponent = 8'(exponent + 127);
        end
        if (exponent > 127) pack32 = {sign_bit, 8'hff, 23'b0};
        else pack32 = {sign_bit, encoded_exponent, rounded[22:0]};
      end
    end
  endfunction

  function automatic [15:0] pack16(
    input sign_bit, input [63:0] significand, input integer scale, input fp16
  );
    integer p, exponent, shift, fraction_bits, minimum_exponent, maximum_exponent, bias;
    reg [63:0] rounded;
    reg [7:0] encoded_exponent;
    begin
      p = {26'b0, leading_bit64(significand)};
      exponent = scale + p;
      fraction_bits = fp16 ? 10 : 7;
      minimum_exponent = fp16 ? -14 : -126;
      maximum_exponent = fp16 ? 15 : 127;
      bias = fp16 ? 15 : 127;
      shift = 0;
      rounded = 0;
      encoded_exponent = 0;
      if (significand == 0) pack16 = {sign_bit, 15'b0};
      else if (exponent > maximum_exponent)
        pack16 = fp16 ? {sign_bit, 5'h1f, 10'b0} : {sign_bit, 8'hff, 7'b0};
      else begin
        if (exponent < minimum_exponent) shift = minimum_exponent - fraction_bits - scale;
        else shift = p - fraction_bits;
        rounded = shift_rne64(significand, shift);
        if (exponent < minimum_exponent) begin
          if (rounded[fraction_bits]) encoded_exponent = 1;
        end else begin
          if (rounded[fraction_bits+1]) begin
            rounded = rounded >> 1;
            exponent = exponent + 1;
          end
          encoded_exponent = 8'(exponent + bias);
        end
        if (exponent > maximum_exponent)
          pack16 = fp16 ? {sign_bit, 5'h1f, 10'b0} : {sign_bit, 8'hff, 7'b0};
        else if (fp16) pack16 = {sign_bit, encoded_exponent[4:0], rounded[9:0]};
        else pack16 = {sign_bit, encoded_exponent, rounded[6:0]};
      end
    end
  endfunction

  function automatic [31:0] expand16(input [15:0] x, input fp16);
    reg [63:0] significand;
    integer scale;
    begin
      significand = 0;
      scale = 0;
      if (!fp16) begin
        if (x[14:7] == 8'hff && x[6:0] != 0) expand16 = FP32_QNAN;
        else expand16 = {x, 16'b0};
      end else if (x[14:10] == 5'h1f) begin
        if (x[9:0] != 0) expand16 = FP32_QNAN;
        else expand16 = {x[15], 8'hff, 23'b0};
      end else begin
        significand = {53'b0, (|x[14:10]), x[9:0]};
        if (x[14:10] == 0) scale = -24;
        else scale = int'({1'b0, x[14:10]}) - 25;
        expand16 = pack32(x[15], significand, scale);
      end
    end
  endfunction

  function automatic [15:0] narrow32(input [31:0] x, input fp16);
    reg [63:0] significand;
    integer scale;
    begin
      significand = {40'b0, (|x[30:23]), x[22:0]};
      if (x[30:23] == 0) scale = -149;
      else scale = int'({1'b0, x[30:23]}) - 150;
      if (fp32_nan(x)) narrow32 = fp16 ? 16'h7e00 : 16'h7fc0;
      else if (fp32_nonfinite(x))
        narrow32 = fp16 ? {x[31], 5'h1f, 10'b0} : {x[31], 8'hff, 7'b0};
      else narrow32 = pack16(x[31], significand, scale, fp16);
    end
  endfunction

  function automatic [26:0] shift_jam27(input [26:0] x, input [8:0] shift);
    reg [26:0] shifted;
    reg sticky;
    begin
      shifted = x;
      sticky = 0;
      if (shift >= 27) begin shifted = 0; sticky = |x; end
      else if (shift != 0) begin
        shifted = x >> shift;
        sticky = |(x & (27'h7ffffff >> (27-shift)));
      end
      shift_jam27 = shifted | {26'b0, sticky};
    end
  endfunction

  function automatic [4:0] awq_shift(input [2:0] lane);
    begin awq_shift = {lane[0], lane[2:1], 2'b00}; end
  endfunction
endpackage
