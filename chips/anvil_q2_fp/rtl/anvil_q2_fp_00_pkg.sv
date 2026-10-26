package anvil_q2_fp_pkg;
  localparam [31:0] FP_ZERO = 32'h00000000;
  localparam [31:0] FP_ONE = 32'h3f800000;
  localparam [31:0] FP_NAN = 32'h7fc00000;
  localparam [31:0] FP_EPS = 32'h358637bd;

  // Product record: {class[1:0], sign, binary_exponent[12:0], significand[47:0]}.
  localparam PRODUCT_BITS = 64;
  localparam [1:0] CLASS_FINITE=0, CLASS_INF=1, CLASS_NAN=2;

  function automatic fp_is_nan(input [31:0] x);
    fp_is_nan = (&x[30:23]) && (|x[22:0]);
  endfunction

  function automatic fp_is_inf(input [31:0] x);
    fp_is_inf = (&x[30:23]) && !(|x[22:0]);
  endfunction

  function automatic fp_is_finite(input [31:0] x);
    fp_is_finite = !(&x[30:23]);
  endfunction

  function automatic fp_is_zero(input [31:0] x);
    fp_is_zero = !(|x[30:0]);
  endfunction

  function automatic [23:0] fp_sig(input [31:0] x);
    fp_sig = {(|x[30:23]),x[22:0]};
  endfunction

  function automatic signed [12:0] fp_exp2(input [31:0] x);
    begin
      if (x[30:23]==0) fp_exp2=-13'sd149;
      else fp_exp2=$signed({5'd0,x[30:23]})-13'sd150;
    end
  endfunction

  function automatic [31:0] expand16(input [15:0] h, input integer format);
    reg [10:0] m;
    reg [7:0] e;
    integer k, shift;
    begin
      if (format==0) begin
        expand16={h,16'd0};
        if ((&h[14:7]) && (|h[6:0])) expand16=FP_NAN;
      end else begin
        if (h[14:10]==31)
          expand16=(|h[9:0]) ? FP_NAN : {h[15],8'hff,23'd0};
        else if (h[14:10]!=0) begin
          e={3'd0,h[14:10]}+8'd112;
          expand16={h[15],e,h[9:0],13'd0};
        end else if (h[9:0]==0) expand16={h[15],31'd0};
        else begin
          shift=0;
          for (k=0;k<10;k=k+1)
            if (h[k]) shift=10-k;
          // Later set bits replace earlier ones, selecting the highest bit.
          m={1'b0,h[9:0]} << shift;
          e=8'd113-shift;
          expand16={h[15],e,m[9:0],13'd0};
        end
      end
    end
  endfunction

  function automatic [47:0] rshift_rne48(input [47:0] x, input integer shift);
    reg [47:0] q;
    reg guard_bit, sticky;
    integer i;
    begin
      q=0; guard_bit=0; sticky=0;
      if (shift<=0) q=x << (-shift);
      else begin
        q=x >> shift;
        for (i=0;i<48;i=i+1) begin
          if (i==shift-1) guard_bit=x[i];
          if (i<shift-1) sticky=sticky|x[i];
        end
        if (guard_bit && (sticky || q[0])) q=q+48'd1;
      end
      rshift_rne48=q;
    end
  endfunction

  function automatic [31:0] pack48(
    input sign_bit, input [47:0] significand, input signed [12:0] exponent);
    integer i, top, unbiased, shift;
    reg [47:0] rounded;
    reg [7:0] encoded_exp;
    begin
      top=-1;
      for (i=0;i<48;i=i+1) if (significand[i]) top=i;
      rounded=0; encoded_exp=0;
      unbiased=top+$signed(exponent);
      pack48={sign_bit,31'd0};
      if (top>=0) begin
        if (unbiased>127) pack48={sign_bit,8'hff,23'd0};
        else if (unbiased>=-126) begin
          shift=top-23;
          rounded=rshift_rne48(significand,shift);
          if (rounded[24]) begin rounded=rounded >> 1; unbiased=unbiased+1; end
          if (unbiased>127) pack48={sign_bit,8'hff,23'd0};
          else begin
            encoded_exp=unbiased+127;
            pack48={sign_bit,encoded_exp,rounded[22:0]};
          end
        end else begin
          shift=-149-$signed(exponent);
          rounded=rshift_rne48(significand,shift);
          if (rounded[23]) pack48={sign_bit,8'd1,23'd0};
          else pack48={sign_bit,8'd0,rounded[22:0]};
        end
      end
    end
  endfunction

  function automatic [15:0] narrow16(input [31:0] x, input integer format);
    reg [16:0] bf;
    reg [47:0] m, rounded;
    reg [4:0] encoded_exp;
    integer i, top, unbiased, shift, exponent;
    begin
      bf=0; m={24'd0,fp_sig(x)}; rounded=0; encoded_exp=0;
      top=-1; unbiased=0; shift=0; exponent=$signed(fp_exp2(x));
      for (i=0;i<24;i=i+1) if (m[i]) top=i;
      narrow16={x[31],15'd0};
      if (fp_is_nan(x)) narrow16=format==0 ? 16'h7fc0 : 16'h7e00;
      else if (fp_is_inf(x)) narrow16=format==0 ?
        {x[31],8'hff,7'd0} : {x[31],5'h1f,10'd0};
      else if (format==0) begin
        bf={1'b0,x[31:16]}+
          ((x[15] && ((|x[14:0]) || x[16])) ? 17'd1 : 17'd0);
        narrow16=bf[15:0];
      end else if (top>=0) begin
        unbiased=top+exponent;
        if (unbiased>15) narrow16={x[31],5'h1f,10'd0};
        else if (unbiased>=-14) begin
          shift=top-10;
          rounded=rshift_rne48(m,shift);
          if (rounded[11]) begin rounded=rounded >> 1; unbiased=unbiased+1; end
          if (unbiased>15) narrow16={x[31],5'h1f,10'd0};
          else begin
            encoded_exp=unbiased+15;
            narrow16={x[31],encoded_exp,rounded[9:0]};
          end
        end else begin
          rounded=rshift_rne48(m,-24-exponent);
          if (rounded[10]) narrow16={x[31],5'd1,10'd0};
          else narrow16={x[31],5'd0,rounded[9:0]};
        end
      end
    end
  endfunction

  function automatic [63:0] exact_product(input [31:0] a,b);
    reg [1:0] classification;
    reg signed [12:0] exponent;
    reg [47:0] product;
    begin
      classification=CLASS_FINITE;
      if (fp_is_nan(a) || fp_is_nan(b) ||
          (fp_is_inf(a) && fp_is_zero(b)) ||
          (fp_is_inf(b) && fp_is_zero(a))) classification=CLASS_NAN;
      else if (fp_is_inf(a) || fp_is_inf(b)) classification=CLASS_INF;
      exponent=fp_exp2(a)+fp_exp2(b);
      product={24'd0,fp_sig(a)}*{24'd0,fp_sig(b)};
      exact_product={classification,a[31]^b[31],exponent,product};
    end
  endfunction

  function automatic [31:0] round_product(input [63:0] p);
    begin
      case (p[63:62])
        CLASS_NAN: round_product=FP_NAN;
        CLASS_INF: round_product={p[61],8'hff,23'd0};
        default: round_product=pack48(p[61],p[47:0],$signed(p[60:48]));
      endcase
    end
  endfunction

  function automatic [26:0] shift_jam27(input [26:0] x, input integer shift);
    reg [26:0] q;
    reg sticky;
    integer i;
    begin
      q=x >> shift; sticky=0;
      for (i=0;i<27;i=i+1) if (i<shift) sticky=sticky|x[i];
      q[0]=q[0]|sticky;
      shift_jam27=q;
    end
  endfunction

  function automatic [31:0] fp_add(input [31:0] a,b);
    reg [31:0] big, smaller;
    reg [26:0] bm, sm, normalized;
    reg [27:0] total;
    reg [24:0] rounded;
    reg sign_bit;
    reg [7:0] encoded_exp;
    integer be, se, exponent, i, top, shift;
    begin
      big=0; smaller=0; bm=0; sm=0; normalized=0; total=0; rounded=0;
      sign_bit=0; encoded_exp=0; be=0; se=0; exponent=0; top=-1; shift=0;
      fp_add=FP_ZERO;
      if (fp_is_nan(a) || fp_is_nan(b)) fp_add=FP_NAN;
      else if (fp_is_inf(a) && fp_is_inf(b) && (a[31]!=b[31])) fp_add=FP_NAN;
      else if (fp_is_inf(a)) fp_add=a;
      else if (fp_is_inf(b)) fp_add=b;
      else if (fp_is_zero(a) && fp_is_zero(b)) fp_add={a[31]&b[31],31'd0};
      else begin
        if (a[30:0]>=b[30:0]) begin big=a; smaller=b; end
        else begin big=b; smaller=a; end
        sign_bit=big[31];
        be=big[30:23]==0 ? 1 : {24'd0,big[30:23]};
        se=smaller[30:23]==0 ? 1 : {24'd0,smaller[30:23]};
        exponent=be;
        bm={fp_sig(big),3'd0};
        sm=shift_jam27({fp_sig(smaller),3'd0},be-se);
        if (big[31]==smaller[31]) total={1'b0,bm}+{1'b0,sm};
        else total={1'b0,bm}-{1'b0,sm};
        if (total!=0) begin
          if (total[27]) begin
            normalized=total[27:1];
            normalized[0]=total[1]|total[0];
            exponent=exponent+1;
          end else begin
            for (i=0;i<27;i=i+1) if (total[i]) top=i;
            shift=26-top;
            if (shift>exponent-1) shift=exponent-1;
            normalized=total[26:0] << shift;
            exponent=exponent-shift;
          end
          rounded={1'b0,normalized[26:3]}+
            ((normalized[2] && ((|normalized[1:0]) || normalized[3])) ? 25'd1 : 25'd0);
          if (rounded[24]) begin rounded=rounded >> 1; exponent=exponent+1; end
          if (exponent>=255) fp_add={sign_bit,8'hff,23'd0};
          else begin
            encoded_exp=(exponent==1 && !rounded[23]) ? 8'd0 : exponent;
            fp_add={sign_bit,encoded_exp,rounded[22:0]};
          end
        end
      end
    end
  endfunction

  function automatic [31:0] fp_scale2(input [31:0] a, input signed [12:0] n);
    begin
      if (fp_is_nan(a)) fp_scale2=FP_NAN;
      else if (fp_is_inf(a)) fp_scale2=a;
      else if (fp_is_zero(a)) fp_scale2=a;
      else if (n>13'sd511) fp_scale2={a[31],8'hff,23'd0};
      else if (n < -13'sd511) fp_scale2={a[31],31'd0};
      else fp_scale2=pack48(a[31],{24'd0,fp_sig(a)},fp_exp2(a)+n);
    end
  endfunction

  function automatic [31:0] fp_from_int(input signed [31:0] x);
    reg [31:0] magnitude;
    begin
      magnitude=x[31] ? (~x+32'd1) : x;
      fp_from_int=pack48(x[31],{16'd0,magnitude},13'sd0);
    end
  endfunction

  // Only bounded finite operands are passed by the exponential/codec controllers.
  function automatic signed [31:0] fp_to_int_rne(input [31:0] x);
    reg [47:0] rounded;
    begin
      rounded=rshift_rne48({24'd0,fp_sig(x)},-$signed(fp_exp2(x)));
      fp_to_int_rne=x[31] ? -$signed(rounded[31:0]) : $signed(rounded[31:0]);
    end
  endfunction

  function automatic fp_less(input [31:0] a,b);
    begin
      if (fp_is_nan(a) || fp_is_nan(b) || (fp_is_zero(a) && fp_is_zero(b)))
        fp_less=0;
      else if (a[31]!=b[31]) fp_less=a[31];
      else if (a[31]) fp_less=a[30:0]>b[30:0];
      else fp_less=a[30:0]<b[30:0];
    end
  endfunction
endpackage
