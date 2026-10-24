package anvil_q1_fp_pkg;
  // Term bits: invalid, NaN, infinity, zero, sign, exponent[10:0], magnitude[63:0].
  function automatic [6:0] leading64(input [63:0] x);
    reg [63:0] v;
    reg [6:0] n;
    begin
      v=x; n=0;
      if (|v[63:32]) begin v=v>>32; n=n+32; end
      if (|v[31:16]) begin v=v>>16; n=n+16; end
      if (|v[15:8]) begin v=v>>8; n=n+8; end
      if (|v[7:4]) begin v=v>>4; n=n+4; end
      if (|v[3:2]) begin v=v>>2; n=n+2; end
      if (v[1]) n=n+1;
      leading64=n;
    end
  endfunction

  function automatic [79:0] term32(input [31:0] x);
    reg [23:0] sig;
    reg [63:0] mag;
    reg signed [10:0] exponent;
    integer high, base;
    reg infinity, nan, invalid, zero;
    begin
      infinity=(x[30:23]==255) && (x[22:0]==0);
      nan=(x[30:23]==255) && (x[22:0]!=0);
      invalid=nan && !x[22];
      sig={x[30:23]!=0,x[22:0]};
      zero=(x[30:0]==0);
      mag=0; exponent=0;
      if (!infinity && !nan && !zero) begin
        base=x[30:23]==0 ? -149 : $signed(32'({1'b0,x[30:23]}))-150;
        high=$signed(32'(leading64({40'd0,sig})));
        mag={40'd0,sig} << (63-high);
        exponent=11'(base+high);
      end
      term32={invalid,nan,infinity,zero,x[31],exponent,mag};
    end
  endfunction

  function automatic [79:0] product16(
    input [15:0] a, b, input [1:0] precision);
    reg [10:0] sa, sb;
    reg [21:0] product;
    reg [63:0] mag;
    reg signed [10:0] exponent;
    reg ai, bi, an, bn, asn, bsn, az, bz;
    reg infinity, nan, invalid, zero;
    integer ea, eb, high;
    begin
      sa=0; sb=0; ea=0; eb=0;
      ai=0; bi=0; an=0; bn=0; asn=0; bsn=0; az=0; bz=0;
      if (precision==2'b01) begin
        sa={a[14:7]!=0,a[6:0],3'd0};
        sb={b[14:7]!=0,b[6:0],3'd0};
        ea=(a[14:7]==0 ? -126 : $signed(32'({1'b0,a[14:7]}))-127)-10;
        eb=(b[14:7]==0 ? -126 : $signed(32'({1'b0,b[14:7]}))-127)-10;
        ai=(a[14:7]==255) && (a[6:0]==0);
        bi=(b[14:7]==255) && (b[6:0]==0);
        an=(a[14:7]==255) && (a[6:0]!=0);
        bn=(b[14:7]==255) && (b[6:0]!=0);
        asn=an && !a[6]; bsn=bn && !b[6];
        az=a[14:0]==0; bz=b[14:0]==0;
      end else if (precision==2'b10) begin
        sa={a[14:10]!=0,a[9:0]};
        sb={b[14:10]!=0,b[9:0]};
        ea=(a[14:10]==0 ? -14 : $signed(32'({1'b0,a[14:10]}))-15)-10;
        eb=(b[14:10]==0 ? -14 : $signed(32'({1'b0,b[14:10]}))-15)-10;
        ai=(a[14:10]==31) && (a[9:0]==0);
        bi=(b[14:10]==31) && (b[9:0]==0);
        an=(a[14:10]==31) && (a[9:0]!=0);
        bn=(b[14:10]==31) && (b[9:0]!=0);
        asn=an && !a[9]; bsn=bn && !b[9];
        az=a[14:0]==0; bz=b[14:0]==0;
      end
      invalid=asn || bsn || (ai && bz) || (bi && az) ||
              (precision!=2'b01 && precision!=2'b10);
      nan=an || bn || invalid;
      infinity=(ai || bi) && !nan;
      zero=(az || bz) && !nan && !infinity;
      product=sa*sb;
      mag=0; exponent=0;
      if (!nan && !infinity && !zero) begin
        high=$signed(32'(leading64({42'd0,product})));
        mag={42'd0,product} << (63-high);
        exponent=11'(ea+eb+high);
      end
      product16={invalid,nan,infinity,zero,a[15]^b[15],exponent,mag};
    end
  endfunction

  function automatic [79:0] product32(input [31:0] a, b);
    reg [23:0] sa, sb;
    reg [47:0] product;
    reg [63:0] mag;
    reg signed [10:0] exponent;
    reg ai, bi, an, bn, az, bz;
    reg infinity, nan, invalid, zero;
    integer ea, eb, high;
    begin
      sa={a[30:23]!=0,a[22:0]}; sb={b[30:23]!=0,b[22:0]};
      ea=a[30:23]==0 ? -149 : $signed(32'({1'b0,a[30:23]}))-150;
      eb=b[30:23]==0 ? -149 : $signed(32'({1'b0,b[30:23]}))-150;
      ai=(a[30:23]==255) && (a[22:0]==0);
      bi=(b[30:23]==255) && (b[22:0]==0);
      an=(a[30:23]==255) && (a[22:0]!=0);
      bn=(b[30:23]==255) && (b[22:0]!=0);
      az=a[30:0]==0; bz=b[30:0]==0;
      invalid=(an && !a[22]) || (bn && !b[22]) ||
              (ai && bz) || (bi && az);
      nan=an || bn || invalid;
      infinity=(ai || bi) && !nan;
      zero=(az || bz) && !nan && !infinity;
      product=sa*sb;
      mag=0; exponent=0;
      if (!nan && !infinity && !zero) begin
        high=$signed(32'(leading64({16'd0,product})));
        mag={16'd0,product} << (63-high);
        exponent=11'(ea+eb+high);
      end
      product32={invalid,nan,infinity,zero,a[31]^b[31],exponent,mag};
    end
  endfunction

  function automatic [69:0] align_term(
    input [79:0] term, input signed [10:0] maximum);
    reg [63:0] mag;
    reg lost;
    reg signed [68:0] aligned;
    integer distance;
    begin
      distance=$signed(32'(maximum))-$signed(32'($signed(term[74:64])));
      mag=0; lost=0;
      if (term[63:0]!=0) begin
        if (distance>=64) lost=1;
        else if (distance>0) begin
          mag=term[63:0] >> distance;
          lost=(term[63:0] & ((64'd1 << distance)-1))!=0;
        end else mag=term[63:0];
      end
      aligned=$signed({5'd0,mag});
      if (term[75]) aligned=-aligned;
      align_term={lost,aligned};
    end
  endfunction

  // Return {status[4:0], binary32}; the magnitude is measured in 2^grid units.
  function automatic [36:0] pack_grid(
    input [68:0] magnitude, input sign,
    input signed [10:0] grid, input alignment_lost);
    reg [68:0] shifted, discarded;
    reg [24:0] significand;
    reg [31:0] value;
    reg [4:0] flags;
    reg guard_bit, sticky_bit, increment;
    reg [7:0] encoded_exponent;
    integer high, exponent, unit_exponent, distance;
    begin
      shifted=0; discarded=0; significand=0;
      value={sign,31'd0}; flags={4'd0,alignment_lost};
      guard_bit=0; sticky_bit=0; increment=0; encoded_exponent=0;
      high=0; exponent=0; unit_exponent=0; distance=0;
      if (magnitude!=0) begin
        if (|magnitude[68:64])
          high=64+$signed(32'(leading64({59'd0,magnitude[68:64]})));
        else high=$signed(32'(leading64(magnitude[63:0])));
        exponent=$signed(32'(grid))+high;
        if (exponent>127) begin
          value={sign,8'hff,23'd0};
          flags[2]=1; flags[0]=1;
        end else begin
          unit_exponent=exponent>=-126 ? exponent-23 : -149;
          distance=unit_exponent-$signed(32'(grid));
          if (distance>69) begin
            shifted=0; sticky_bit=1;
          end else if (distance>0) begin
            shifted=magnitude >> distance;
            discarded=magnitude & ((69'd1 << distance)-1);
            guard_bit=magnitude[distance-1];
            sticky_bit=(discarded & ((69'd1 << (distance-1))-1))!=0;
          end else shifted=magnitude << (-distance);
          increment=guard_bit && (sticky_bit || shifted[0]);
          significand=shifted[24:0]+{24'd0,increment};
          flags[0]=alignment_lost || guard_bit || sticky_bit;
          if (exponent>=-126) begin
            if (significand[24]) begin
              significand=significand>>1;
              exponent=exponent+1;
            end
            if (exponent>127) begin
              value={sign,8'hff,23'd0};
              flags[2]=1; flags[0]=1;
            end else begin
              encoded_exponent=8'(exponent+127);
              value={sign,encoded_exponent,significand[22:0]};
            end
          end else begin
            value={sign,7'd0,significand[23:0]};
            flags[1]=flags[0] && !significand[23];
          end
        end
      end
      pack_grid={flags,value};
    end
  endfunction

  function automatic [31:0] widen16(
    input [15:0] x, input [1:0] precision);
    reg [23:0] sig;
    reg [7:0] exponent;
    integer high;
    begin
      sig=0; exponent=0; high=0;
      if (precision==2'b01) widen16={x,16'd0};
      else if (precision==2'b10) begin
        if (x[14:10]==31) widen16={x[15],8'hff,x[9:0],13'd0};
        else if (x[14:10]!=0) begin
          exponent={3'd0,x[14:10]}+8'd112;
          widen16={x[15],exponent,x[9:0],13'd0};
        end else if (x[9:0]==0) widen16={x[15],31'd0};
        else begin
          high=$signed(32'(leading64({54'd0,x[9:0]})));
          sig={14'd0,x[9:0]} << (23-high);
          exponent=8'(high+103);
          widen16={x[15],exponent,sig[22:0]};
        end
      end else widen16=32'h7fc00000;
    end
  endfunction

  function automatic [55:0] divide_steps(
    input [23:0] denominator, input [24:0] remainder_in,
    input [30:0] quotient_in, input [1:0] count);
    reg [24:0] remainder_next;
    reg [30:0] quotient_next;
    integer i;
    begin
      remainder_next=remainder_in; quotient_next=quotient_in;
      for (i=0;i<3;i=i+1) begin
        if (i<$signed(32'({1'b0,count}))) begin
          remainder_next=remainder_next << 1;
          quotient_next=quotient_next << 1;
          if (remainder_next>={1'b0,denominator}) begin
            remainder_next=remainder_next-{1'b0,denominator};
            quotient_next[0]=1;
          end
        end
      end
      divide_steps={remainder_next,quotient_next};
    end
  endfunction

  function automatic [97:0] sqrt_two_digits(
    input [47:0] radicand_in, input [23:0] root_in,
    input [25:0] remainder_in);
    reg [47:0] radicand_next;
    reg [23:0] root_next;
    reg [25:0] remainder_next, trial;
    integer i;
    begin
      radicand_next=radicand_in; root_next=root_in; remainder_next=remainder_in;
      for (i=0;i<2;i=i+1) begin
        remainder_next=(remainder_next<<2) | {24'd0,radicand_next[47:46]};
        radicand_next=radicand_next<<2;
        trial=({2'd0,root_next}<<2) | 26'd1;
        root_next=root_next<<1;
        if (remainder_next>=trial) begin
          remainder_next=remainder_next-trial;
          root_next[0]=1;
        end
      end
      sqrt_two_digits={radicand_next,root_next,remainder_next};
    end
  endfunction
endpackage
