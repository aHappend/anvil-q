package anvil_q2_pkg;
  function automatic [128:0] reciprocal_div(
    input [128:0] dividend, input [63:0] divisor);
    reg [383:0] normalized, reciprocal, residual, product, quotient;
    integer shift, i;
    begin
      normalized = {320'd0,divisor};
      shift = 0;
      for (i=0; i<63; i=i+1)
        if (!normalized[63]) begin normalized = normalized << 1; shift = shift+1; end
      reciprocal = 384'd1 << 128;
      // Underestimating Newton reciprocal, followed by exact remainder correction.
      for (i=0; i<9; i=i+1) begin
        residual = (384'd1 << 192)-normalized*reciprocal;
        reciprocal = reciprocal+((reciprocal*residual) >> 192);
      end
      residual = (384'd1 << 192)-normalized*reciprocal;
      if (residual >= normalized) reciprocal = reciprocal+1;
      product = {255'd0,dividend}*reciprocal;
      quotient = product >> (192-shift);
      residual = {255'd0,dividend}-quotient*{320'd0,divisor};
      if (residual >= {320'd0,divisor}) quotient = quotient+1;
      reciprocal_div = divisor == 0 ? {129{1'bx}} : quotient[128:0];
    end
  endfunction
  function automatic [63:0] constant_div64(
    input [63:0] dividend, divisor, reciprocal);
    reg [127:0] product;
    reg [63:0] quotient, remainder;
    begin
      product = dividend*reciprocal;
      quotient = product[127:64];
      remainder = dividend-quotient*divisor;
      constant_div64 = quotient+(remainder >= divisor ? 64'd1 : 64'd0);
    end
  endfunction
  function automatic signed [31:0] sat32(input signed [127:0] x);
    begin
      if (x > 128'sd2147483647) sat32 = 32'sh7fffffff;
      else if (x < -128'sd2147483648) sat32 = 32'sh80000000;
      else sat32 = x[31:0];
    end
  endfunction
  function automatic signed [127:0] round_shift(
    input signed [127:0] x, input integer bits);
    reg [128:0] mag;
    begin
      mag = x < 0 ? -$signed({x[127],x}) : {1'b0,x};
      if (bits > 0) mag = (mag + (129'd1 << (bits-1))) >> bits;
      round_shift = x < 0 ? -$signed(mag) : $signed(mag);
    end
  endfunction
  function automatic signed [127:0] round_div(
    input signed [127:0] x, input [63:0] divisor);
    reg [128:0] mag;
    begin
      mag = x < 0 ? -$signed({x[127],x}) : {1'b0,x};
      mag = reciprocal_div(mag + ({65'd0,divisor} >> 1),divisor);
      round_div = x < 0 ? -$signed(mag) : $signed(mag);
    end
  endfunction
  function automatic f16_invalid(input [15:0] h);
    begin f16_invalid = h[14:10] == 5'd31; end
  endfunction
  function automatic signed [31:0] f16_q16(input [15:0] h);
    reg [127:0] mag;
    reg signed [127:0] val;
    integer shift;
    begin
      mag = h[14:10] == 0 ? {118'd0,h[9:0]} : {117'd0,1'b1,h[9:0]};
      shift = h[14:10] == 0 ? -8 : $signed({27'd0,h[14:10]})-9;
      if (shift >= 0) mag = mag << shift;
      else mag = (mag + (128'd1 << (-shift-1))) >> (-shift);
      val = h[15] ? -$signed(mag) : $signed(mag);
      f16_q16 = sat32(val);
    end
  endfunction
  function automatic [31:0] f16_scale(input [15:0] h);
    reg [63:0] mag;
    integer shift;
    begin
      mag = h[14:10] == 0 ? {54'd0,h[9:0]} : {53'd0,1'b1,h[9:0]};
      shift = h[14:10] == 0 ? -8 : $signed({27'd0,h[14:10]})-9;
      if (shift >= 0) mag = mag << shift;
      else mag = (mag + (64'd1 << (-shift-1))) >> (-shift);
      f16_scale = mag[31:0];
    end
  endfunction
  function automatic [63:0] isqrt128(input [127:0] x);
    reg [63:0] root;
    reg [129:0] remainder, trial;
    integer i;
    begin
      root = 0;
      remainder = 0;
      for (i=63; i>=0; i=i-1) begin
        remainder = (remainder << 2) | {128'd0,x[i*2+:2]};
        trial = ({66'd0,root} << 2) | 130'd1;
        if (remainder >= trial) begin
          remainder = remainder-trial;
          root = (root << 1) | 64'd1;
        end else root = root << 1;
      end
      isqrt128 = root;
    end
  endfunction
  function automatic [31:0] exp_q24(input signed [63:0] x);
    reg [63:0] u, n, r, magnitude, quotient;
    reg signed [63:0] term, total, numerator;
    integer j;
    begin
      if (x < -64'sd1048576) exp_q24 = 0;
      else if (x >= 0) exp_q24 = 32'd16777216;
      else begin
        u = (-x) << 8;
        n = constant_div64(u,64'd11629080,64'd1586259968433);
        r = u-n*64'd11629080;
        term = 64'sd16777216;
        total = term;
        for (j=1; j<=6; j=j+1) begin
          numerator = -term * $signed(r);
          magnitude = (numerator < 0 ? -numerator : numerator) >> 24;
          case (j)
            1: quotient = magnitude;
            2: quotient = magnitude >> 1;
            3: quotient = constant_div64(magnitude,64'd3,64'h5555555555555555);
            4: quotient = magnitude >> 2;
            5: quotient = constant_div64(magnitude,64'd5,64'h3333333333333333);
            default: quotient = constant_div64(magnitude,64'd3,64'h5555555555555555) >> 1;
          endcase
          term = numerator < 0 ? -$signed(quotient) : $signed(quotient);
          total = total + term;
        end
        exp_q24 = total < 0 ? 0 : (total >> n);
      end
    end
  endfunction
  function automatic signed [31:0] silu_q16(input signed [31:0] x);
    reg [31:0] e;
    reg [63:0] sigmoid, magnitude;
    reg signed [64:0] prod;
    begin
      magnitude = x < 0 ? -$signed({{32{x[31]}},x}) : {32'd0,x};
      e = exp_q24(-$signed(magnitude));
      if (x >= 0) sigmoid = 64'(reciprocal_div(129'd281474976710656,64'd16777216+e));
      else sigmoid = 64'(reciprocal_div({73'd0,e,24'd0},64'd16777216+e));
      prod = $signed({{33{x[31]}},x}) * $signed({1'b0,sigmoid});
      silu_q16 = sat32(round_shift({{63{prod[64]}},prod},24));
    end
  endfunction
endpackage
