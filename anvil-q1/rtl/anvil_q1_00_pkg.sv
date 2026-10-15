package anvil_q1_pkg;
  function automatic signed [15:0] sat16(input signed [95:0] x);
    begin
      if (x > 96'sd32767) sat16 = 16'sh7fff;
      else if (x < -96'sd32768) sat16 = 16'sh8000;
      else sat16 = x[15:0];
    end
  endfunction
  function automatic signed [31:0] sat32(input signed [95:0] x);
    begin
      if (x > 96'sd2147483647) sat32 = 32'sh7fffffff;
      else if (x < -96'sd2147483648) sat32 = 32'sh80000000;
      else sat32 = x[31:0];
    end
  endfunction
  function automatic signed [95:0] round_shift(
    input signed [95:0] x, input integer bits);
    reg [95:0] mag;
    begin
      mag = x < 0 ? -x : x;
      if (bits > 0) mag = (mag + (96'd1 << (bits-1))) >> bits;
      round_shift = x < 0 ? -$signed(mag) : $signed(mag);
    end
  endfunction
  function automatic signed [95:0] round_div(
    input signed [95:0] x, input [63:0] divisor);
    reg [95:0] mag;
    begin
      mag = x < 0 ? -x : x;
      if (divisor == 0) round_div = 0;
      else begin
        mag = (mag + (divisor >> 1)) / divisor;
        round_div = x < 0 ? -$signed(mag) : $signed(mag);
      end
    end
  endfunction
  function automatic f16_invalid(input [15:0] h);
    begin f16_invalid = h[14:10] == 5'd31; end
  endfunction
  function automatic signed [15:0] f16_q8(input [15:0] h);
    reg [95:0] mag;
    reg signed [95:0] val;
    integer shift;
    begin
      mag = h[14:10] == 0 ? {86'd0,h[9:0]} : {85'd0,1'b1,h[9:0]};
      shift = h[14:10] == 0 ? -16 : integer'(h[14:10])-17;
      if (shift >= 0) mag = mag << shift;
      else mag = (mag + (96'd1 << (-shift-1))) >> (-shift);
      val = h[15] ? -$signed(mag) : $signed(mag);
      f16_q8 = sat16(val);
    end
  endfunction
  function automatic [31:0] f16_scale(input [15:0] h);
    reg [63:0] mag;
    integer shift;
    begin
      mag = h[14:10] == 0 ? {54'd0,h[9:0]} : {53'd0,1'b1,h[9:0]};
      shift = h[14:10] == 0 ? -8 : integer'(h[14:10])-9;
      if (shift >= 0) mag = mag << shift;
      else mag = (mag + (64'd1 << (-shift-1))) >> (-shift);
      f16_scale = mag[31:0];
    end
  endfunction
  function automatic [47:0] isqrt96(input [95:0] x);
    reg [47:0] root, candidate;
    reg [95:0] square;
    integer i;
    begin
      root = 0;
      for (i=47; i>=0; i=i-1) begin
        candidate = root | (48'd1 << i);
        square = {48'd0,candidate} * {48'd0,candidate};
        if (square <= x) root = candidate;
      end
      isqrt96 = root;
    end
  endfunction
  function automatic [31:0] exp_q24(input signed [63:0] x);
    reg [63:0] u, n, r;
    reg signed [63:0] term, total;
    integer j;
    begin
      if (x < -64'sd1048576) exp_q24 = 0;
      else if (x >= 0) exp_q24 = 32'd16777216;
      else begin
        u = (-x) << 8;
        n = u / 64'd11629080;
        r = u % 64'd11629080;
        term = 64'sd16777216;
        total = term;
        for (j=1; j<=6; j=j+1) begin
          term = (-term * $signed(r)) / (64'sd16777216*j);
          total = total + term;
        end
        exp_q24 = total < 0 ? 0 : (total >> n);
      end
    end
  endfunction
  function automatic signed [15:0] silu_q8(input signed [15:0] x);
    reg [31:0] e;
    reg [63:0] sigmoid, magnitude;
    reg signed [95:0] prod;
    begin
      magnitude = x < 0 ? -$signed({{48{x[15]}},x}) : x;
      e = exp_q24(-$signed(magnitude << 8));
      if (x >= 0) sigmoid = 64'd281474976710656 / (64'd16777216+e);
      else sigmoid = ({32'd0,e} << 24) / (64'd16777216+e);
      prod = $signed(x) * $signed({1'b0,sigmoid});
      silu_q8 = sat16(round_shift(prod,24));
    end
  endfunction
endpackage
