package anvil_q1_fp_compat_pkg;
  function automatic signed [31:0] sat32(input signed [127:0] x);
    begin
      if (x>128'sd2147483647) sat32=32'sh7fffffff;
      else if (x< -128'sd2147483648) sat32=32'sh80000000;
      else sat32=x[31:0];
    end
  endfunction

  function automatic signed [127:0] round_shift(
    input signed [127:0] x, input integer bits);
    reg [128:0] mag;
    begin
      mag=x<0 ? -$signed({x[127],x}) : {1'b0,x};
      if (bits>0) mag=(mag+(129'd1 << (bits-1))) >> bits;
      round_shift=x<0 ? -$signed(mag) : $signed(mag);
    end
  endfunction

  function automatic f16_invalid(input [15:0] h);
    begin f16_invalid=h[14:10]==5'd31; end
  endfunction

  function automatic signed [31:0] f16_q16(input [15:0] h);
    reg [127:0] mag;
    reg signed [127:0] val;
    integer shift;
    begin
      mag=h[14:10]==0 ? {118'd0,h[9:0]} : {117'd0,1'b1,h[9:0]};
      shift=h[14:10]==0 ? -8 : $signed({27'd0,h[14:10]})-9;
      if (shift>=0) mag=mag << shift;
      else mag=(mag+(128'd1 << (-shift-1))) >> (-shift);
      val=h[15] ? -$signed(mag) : $signed(mag);
      f16_q16=sat32(val);
    end
  endfunction

  function automatic [31:0] f16_scale(input [15:0] h);
    reg [63:0] mag;
    integer shift;
    begin
      mag=h[14:10]==0 ? {54'd0,h[9:0]} : {53'd0,1'b1,h[9:0]};
      shift=h[14:10]==0 ? -8 : $signed({27'd0,h[14:10]})-9;
      if (shift>=0) mag=mag << shift;
      else mag=(mag+(64'd1 << (-shift-1))) >> (-shift);
      f16_scale=mag[31:0];
    end
  endfunction
endpackage
