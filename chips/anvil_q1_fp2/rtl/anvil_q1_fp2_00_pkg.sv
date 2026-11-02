package anvil_q1_fp2_pkg;
  function automatic [3:0] leading16(input [15:0] x);
    reg [15:0] v;
    reg [3:0] n;
    begin
      v=x; n=0;
      if (|v[15:8]) begin v=v>>8; n=n+8; end
      if (|v[7:4]) begin v=v>>4; n=n+4; end
      if (|v[3:2]) begin v=v>>2; n=n+2; end
      if (v[1]) n=n+1;
      leading16=n;
    end
  endfunction

  function automatic [3:0] trailing16(input [15:0] x);
    reg [15:0] v;
    reg [3:0] n;
    begin
      v=x; n=0;
      if (!(|v[7:0])) begin v=v>>8; n=n+8; end
      if (!(|v[3:0])) begin v=v>>4; n=n+4; end
      if (!(|v[1:0])) begin v=v>>2; n=n+2; end
      if (!v[0]) n=n+1;
      trailing16=n;
    end
  endfunction

  function automatic [4:0] leading24(input [23:0] x);
    reg [31:0] v;
    reg [4:0] n;
    begin
      v={8'd0,x}; n=0;
      if (|v[31:16]) begin v=v>>16; n=n+16; end
      if (|v[15:8]) begin v=v>>8; n=n+8; end
      if (|v[7:4]) begin v=v>>4; n=n+4; end
      if (|v[3:2]) begin v=v>>2; n=n+2; end
      if (v[1]) n=n+1;
      leading24=n;
    end
  endfunction

  function automatic [9:0] leading1024(input [1023:0] x);
    reg [1023:0] v;
    reg [9:0] n;
    begin
      v=x; n=0;
      if (|v[1023:512]) begin v=v>>512; n=n+512; end
      if (|v[511:256]) begin v=v>>256; n=n+256; end
      if (|v[255:128]) begin v=v>>128; n=n+128; end
      if (|v[127:64]) begin v=v>>64; n=n+64; end
      if (|v[63:32]) begin v=v>>32; n=n+32; end
      if (|v[31:16]) begin v=v>>16; n=n+16; end
      if (|v[15:8]) begin v=v>>8; n=n+8; end
      if (|v[7:4]) begin v=v>>4; n=n+4; end
      if (|v[3:2]) begin v=v>>2; n=n+2; end
      if (v[1]) n=n+1;
      leading1024=n;
    end
  endfunction

  function automatic [9:0] leading544(input [543:0] x);
    begin leading544=leading1024({480'd0,x}); end
  endfunction

  function automatic [9:0] leading576(input [575:0] x);
    begin leading576=leading1024({448'd0,x}); end
  endfunction

  function automatic [36:0] pack_fp32(
    input [8:0] metadata,
    input sign_bit, zero, normal,
    input signed [11:0] biased_exponent,
    input [23:0] kept,
    input guard_bit, sticky_bit
  );
    reg [31:0] value;
    reg [4:0] flags;
    reg [24:0] rounded;
    begin
      value=0; flags=metadata[8:4];
      rounded={1'b0,kept}+{24'd0,guard_bit && (sticky_bit || kept[0])};
      if (metadata[3] || (metadata[2] && metadata[1])) begin
        value=32'h7fc00000;
        flags[4]=flags[4] || (metadata[2] && metadata[1]);
      end else if (metadata[2] || metadata[1]) value={metadata[1],8'hff,23'd0};
      else if (zero) value={metadata[0],31'd0};
      else begin
        flags[0]=flags[0] || guard_bit || sticky_bit;
        if (normal) begin
          if (biased_exponent>=255 || (biased_exponent==254 && rounded[24])) begin
            value={sign_bit,8'hff,23'd0}; flags[2]=1; flags[0]=1;
          end else if (rounded[24])
            value={sign_bit,8'(biased_exponent+12'sd1),rounded[23:1]};
          else value={sign_bit,biased_exponent[7:0],rounded[22:0]};
        end else begin
          value={sign_bit,7'd0,rounded[23:0]};
          flags[1]=flags[1] || ((guard_bit || sticky_bit) && !rounded[23]);
        end
      end
      pack_fp32={flags,value};
    end
  endfunction

  // Return {status, BF16}. Scaling is exact until this single BF16 rounding.
  function automatic [20:0] mx_to_bf16(input [7:0] code, scale);
    reg [15:0] sig, kept, rounded;
    reg [15:0] value;
    reg [4:0] flags;
    reg guard_bit, sticky_bit;
    integer base, high, exponent, distance;
    begin
      sig={12'd0,code[6:3]!=0,code[2:0]};
      base=(code[6:3]==0 ? -9 : integer'({1'b0,code[6:3]})-10)
        +integer'({1'b0,scale})-127;
      high=integer'(leading16(sig));
      exponent=base+high;
      value={code[7],15'd0}; flags=0;
      kept=0; rounded=0; guard_bit=0; sticky_bit=0; distance=0;
      if (scale==255) begin value=16'h7fc0; flags[4]=1; end
      else if (code[6:0]==7'h7f) value=16'h7fc0;
      else if (sig!=0) begin
        if (exponent>127) begin
          value={code[7],8'hff,7'd0}; flags=5'b00101;
        end else if (exponent>=-126) begin
          kept=sig << (7-high);
          value={code[7],8'(exponent+127),kept[6:0]};
        end else begin
          distance=-133-base;
          if (distance>0) begin
            if (distance<=16) begin
              kept=sig >> distance;
              guard_bit=|(sig & (16'd1 << (distance-1)));
              sticky_bit=|(sig & ((16'd1 << (distance-1))-1));
            end else sticky_bit=1;
          end else kept=sig << (-distance);
          rounded=kept+{15'd0,guard_bit && (sticky_bit || kept[0])};
          value={code[7],7'd0,rounded[7:0]};
          flags[0]=guard_bit || sticky_bit;
          flags[1]=flags[0] && !rounded[7];
        end
      end
      mx_to_bf16={flags,value};
    end
  endfunction

  // {flags[4:0], NaN, +infinity, -infinity, all-negative-zero}.
  function automatic [8:0] merge_meta(input [8:0] a, b);
    begin merge_meta={(a[8:1] | b[8:1]),a[0] && b[0]}; end
  endfunction

  // Product record: {metadata, unbiased leading exponent, grid shift, sign, magnitude}.
  function automatic [45:0] bf16_product(
    input [15:0] a, b, input [4:0] conversion_status, input active);
    reg [7:0] sa, sb;
    reg [15:0] magnitude;
    reg [8:0] metadata;
    reg signed [10:0] high;
    reg [8:0] shift;
    reg ai, bi, an, bn, az, bz, sign_bit, invalid;
    integer base;
    begin
      sa={a[14:7]!=0,a[6:0]}; sb={b[14:7]!=0,b[6:0]};
      ai=a[14:7]==255 && a[6:0]==0;
      bi=b[14:7]==255 && b[6:0]==0;
      an=a[14:7]==255 && a[6:0]!=0;
      bn=b[14:7]==255 && b[6:0]!=0;
      az=a[14:0]==0; bz=b[14:0]==0; sign_bit=a[15]^b[15];
      invalid=(an && !a[6]) || (bn && !b[6]) || (ai && bz) || (bi && az);
      metadata={conversion_status,4'd0};
      metadata[8]=metadata[8] || invalid;
      metadata[3]=an || bn || invalid;
      metadata[2]=!metadata[3] && (ai || bi) && !sign_bit;
      metadata[1]=!metadata[3] && (ai || bi) && sign_bit;
      metadata[0]=!metadata[3] && !(ai || bi) && (az || bz) && sign_bit;
      magnitude=0; shift=0; high=-11'sd512;
      base=(a[14:7]==0 ? -133 : integer'({1'b0,a[14:7]})-134)
        +(b[14:7]==0 ? -133 : integer'({1'b0,b[14:7]})-134);
      if (!metadata[3] && !(ai || bi) && !az && !bz) begin
        magnitude=sa*sb;
        shift=9'(base+266);
        high=11'(base+integer'(leading16(magnitude)));
      end
      if (!active) begin
        metadata=9'b000000001; magnitude=0; shift=0;
        high=-11'sd512; sign_bit=0;
      end
      bf16_product={metadata,high,shift,sign_bit,magnitude};
    end
  endfunction

  function automatic [8:0] fp32_meta(input [31:0] x);
    reg [8:0] m;
    begin
      m=0;
      m[3]=x[30:23]==255 && x[22:0]!=0;
      m[8]=m[3] && !x[22];
      m[2]=x[30:23]==255 && x[22:0]==0 && !x[31];
      m[1]=x[30:23]==255 && x[22:0]==0 && x[31];
      m[0]=x==32'h80000000;
      fp32_meta=m;
    end
  endfunction

  function automatic signed [10:0] fp32_high(input [31:0] x);
    reg [23:0] sig;
    integer base;
    begin
      sig={x[30:23]!=0,x[22:0]};
      base=x[30:23]==0 ? -149 : integer'({1'b0,x[30:23]})-150;
      if (sig==0 || x[30:23]==255) fp32_high=-11'sd512;
      else fp32_high=11'(base+integer'(leading24(sig)));
    end
  endfunction

  function automatic [8:0] fp32_grid_shift(input [31:0] x);
    begin
      fp32_grid_shift=x[30:23]==0 ? 9'd117 :
        9'({1'b0,x[30:23]})+9'd116;
    end
  endfunction

  function automatic signed [10:0] max_exp(input signed [10:0] a, b);
    begin max_exp=a>b ? a : b; end
  endfunction

  function automatic [31:0] uint32_to_fp32(input [31:0] x);
    reg [4:0] high;
    reg [31:0] shifted;
    reg [24:0] rounded;
    reg guard_bit, sticky_bit;
    integer distance;
    begin
      high=5'(leading1024({992'd0,x}));
      shifted=0; rounded=0; guard_bit=0; sticky_bit=0; distance=0;
      if (high<=23) shifted=x << (23-high);
      else begin
        distance=integer'({1'b0,high})-23;
        shifted=x >> distance;
        guard_bit=|(x & (32'd1 << (distance-1)));
        sticky_bit=|(x & ((32'd1 << (distance-1))-1));
      end
      rounded={1'b0,shifted[23:0]}+
        {24'd0,guard_bit && (sticky_bit || shifted[0])};
      if (x==0) uint32_to_fp32=0;
      else if (rounded[24]) uint32_to_fp32={1'b0,8'(128+high),23'd0};
      else uint32_to_fp32={1'b0,8'(127+high),rounded[22:0]};
    end
  endfunction

  function automatic [20:0] fp32_to_bf16(input [31:0] x);
    reg [16:0] rounded;
    reg [4:0] flags;
    reg lost;
    begin
      flags=0; lost=|x[15:0];
      rounded={1'b0,x[31:16]}+
        {16'd0,x[15] && ((|x[14:0]) || x[16])};
      if (x[30:23]==255 && x[22:0]!=0) begin
        fp32_to_bf16={!x[22],4'd0,16'h7fc0};
      end else if (x[30:23]==255) fp32_to_bf16={5'd0,x[31:16]};
      else begin
        flags[0]=lost;
        flags[2]=rounded[14:7]==255;
        flags[1]=lost && rounded[14:7]==0;
        fp32_to_bf16={flags,rounded[15:0]};
      end
    end
  endfunction
endpackage
