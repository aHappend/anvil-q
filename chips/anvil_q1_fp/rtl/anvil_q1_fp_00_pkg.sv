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

  function automatic [64:0] align_magnitude(
    input [79:0] term, input signed [10:0] maximum);
    reg [63:0] mag;
    reg lost;
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
      align_magnitude={lost,mag};
    end
  endfunction

  function automatic [69:0] align_term(
    input [79:0] term, input signed [10:0] maximum);
    reg [64:0] magnitude;
    reg signed [68:0] aligned;
    begin
      magnitude=align_magnitude(term,maximum);
      aligned=$signed({5'd0,magnitude[63:0]});
      if (term[75]) aligned=-aligned;
      align_term={magnitude[64],aligned};
    end
  endfunction

  function automatic [2:0] leading8(input [7:0] x);
    reg [7:0] v;
    reg [2:0] high;
    begin
      v=x; high=0;
      if (|v[7:4]) begin v=v>>4; high[2]=1; end
      if (|v[3:2]) begin v=v>>2; high[1]=1; end
      high[0]=v[1];
      leading8=high;
    end
  endfunction

  // Return {status[4:0], binary32}; the magnitude is measured in 2^grid units.
  function automatic [36:0] pack_grid(
    input [68:0] magnitude, input sign,
    input signed [10:0] grid, input alignment_lost);
    reg [71:0] padded;
    reg [8:0] nonzero, selected;
    reg [2:0] local_high [0:8];
    reg [31:0] window [0:8];
    reg [31:0] normalized [0:8];
    reg [8:0] tail;
    reg [70:0] shifted;
    reg [24:0] normal_unrounded, normal_significand;
    reg [24:0] tiny_unrounded, tiny_significand;
    reg [31:0] value;
    reg [4:0] flags;
    reg normal_guard, normal_sticky, tiny_guard, tiny_sticky;
    reg [6:0] high, right_distance;
    reg [4:0] left_distance;
    reg signed [11:0] biased_grid, carried_grid;
    reg signed [11:0] biased_exponent, carried_exponent, distance;
    integer block_index;
    begin
      padded={3'd0,magnitude}; nonzero=0; selected=0; tail=0;
      normal_unrounded=0; normal_guard=0; normal_sticky=0; high=0;
      // Normalize each eight-bit leading window before selecting the leading block.
      for (block_index=0;block_index<9;block_index=block_index+1) begin
        nonzero[block_index]=|padded[block_index*8+:8];
        local_high[block_index]=leading8(padded[block_index*8+:8]);
        if (block_index>=3)
          window[block_index]=32'(padded >> (block_index*8-24));
        else window[block_index]=32'(padded << (24-block_index*8));
        normalized[block_index]=window[block_index] << (~local_high[block_index]);
        if (block_index>=4)
          tail[block_index]=|(padded << (72-(block_index*8-24)));
      end
      for (block_index=0;block_index<9;block_index=block_index+1) begin
        selected[block_index]=nonzero[block_index] &&
          !(|(nonzero >> (block_index+1)));
        normal_unrounded=normal_unrounded |
          ({25{selected[block_index]}} & {1'b0,normalized[block_index][31:8]});
        normal_guard=normal_guard |
          (selected[block_index] && normalized[block_index][7]);
        normal_sticky=normal_sticky |
          (selected[block_index] &&
           ((|normalized[block_index][6:0]) || tail[block_index]));
        high=high | ({7{selected[block_index]}} &
          {4'(block_index),local_high[block_index]});
      end
      normal_significand=normal_unrounded+
        {24'd0,(normal_guard && (normal_sticky || normal_unrounded[0]))};
      // The subnormal shift depends only on the grid, not on leading detection.
      distance=-12'sd149-$signed({grid[10],grid});
      right_distance=distance[6:0];
      left_distance=5'(-distance);
      shifted={magnitude,2'd0};
      if (right_distance[0]) shifted={1'd0,shifted[70:2],|shifted[1:0]};
      if (right_distance[1]) shifted={2'd0,shifted[70:3],|shifted[2:0]};
      if (right_distance[2]) shifted={4'd0,shifted[70:5],|shifted[4:0]};
      if (right_distance[3]) shifted={8'd0,shifted[70:9],|shifted[8:0]};
      if (right_distance[4]) shifted={16'd0,shifted[70:17],|shifted[16:0]};
      if (right_distance[5]) shifted={32'd0,shifted[70:33],|shifted[32:0]};
      if (right_distance[6]) shifted={64'd0,shifted[70:65],|shifted[64:0]};
      tiny_unrounded=0; tiny_guard=0; tiny_sticky=0;
      if (distance>12'sd69) tiny_sticky=1;
      else if (distance>0) begin
        tiny_unrounded=shifted[26:2];
        tiny_guard=shifted[1]; tiny_sticky=shifted[0];
      end else tiny_unrounded=magnitude[24:0] << left_distance;
      tiny_significand=tiny_unrounded+
        {24'd0,(tiny_guard && (tiny_sticky || tiny_unrounded[0]))};
      biased_grid=$signed({grid[10],grid})+12'sd127;
      carried_grid=$signed({grid[10],grid})+12'sd128;
      biased_exponent=biased_grid+$signed({5'd0,high});
      carried_exponent=carried_grid+$signed({5'd0,high});
      value={sign,31'd0}; flags={4'd0,alignment_lost};
      if (magnitude!=0) begin
        if (biased_exponent>12'sd254) begin
          value={sign,8'hff,23'd0};
          flags[2]=1; flags[0]=1;
        end else if (biased_exponent>=12'sd1) begin
          flags[0]=alignment_lost || normal_guard || normal_sticky;
          if (biased_exponent==12'sd254 && normal_significand[24]) begin
            value={sign,8'hff,23'd0};
            flags[2]=1; flags[0]=1;
          end else if (normal_significand[24])
            value={sign,carried_exponent[7:0],normal_significand[23:1]};
          else value={sign,biased_exponent[7:0],normal_significand[22:0]};
        end else begin
          value={sign,7'd0,tiny_significand[23:0]};
          flags[0]=alignment_lost || tiny_guard || tiny_sticky;
          flags[1]=flags[0] && !tiny_significand[23];
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
