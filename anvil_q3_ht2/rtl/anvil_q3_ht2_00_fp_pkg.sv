package anvil_q3_ht2_fp_pkg;
  function automatic [2:0] awq_position(input [2:0] row);
    case (row)
      0: awq_position=0;
      1: awq_position=4;
      2: awq_position=1;
      3: awq_position=5;
      4: awq_position=2;
      5: awq_position=6;
      6: awq_position=3;
      default: awq_position=7;
    endcase
  endfunction

  function automatic [3:0] leading_zero8(input [7:0] value);
    casez (value)
      8'b1???????: leading_zero8=0;
      8'b01??????: leading_zero8=1;
      8'b001?????: leading_zero8=2;
      8'b0001????: leading_zero8=3;
      8'b00001???: leading_zero8=4;
      8'b000001??: leading_zero8=5;
      8'b0000001?: leading_zero8=6;
      8'b00000001: leading_zero8=7;
      default: leading_zero8=8;
    endcase
  endfunction

  function automatic [5:0] leading_zero32(input [31:0] value);
    reg [3:0] z0,z1,z2,z3;
    begin
      z0=leading_zero8(value[31:24]);
      z1=leading_zero8(value[23:16]);
      z2=leading_zero8(value[15:8]);
      z3=leading_zero8(value[7:0]);
      if (z0!=8) leading_zero32={2'd0,z0};
      else if (z1!=8) leading_zero32=6'd8+z1;
      else if (z2!=8) leading_zero32=6'd16+z2;
      else leading_zero32=6'd24+z3;
    end
  endfunction

  function automatic [5:0] leading_zero48(input [47:0] value);
    reg [5:0] upper,lower;
    begin
      upper=leading_zero32({value[47:16]});
      lower=leading_zero32({value[15:0],16'd0});
      if (upper!=32) leading_zero48=upper;
      else if (lower==32) leading_zero48=48;
      else leading_zero48=6'd32+lower;
    end
  endfunction

  function automatic [26:0] shift_jam27(input [26:0] value,
    input [8:0] distance);
    reg [26:0] shifted,discarded;
    begin
      if (distance==0) shift_jam27=value;
      else if (distance>=27) shift_jam27={26'd0,|value};
      else begin
        shifted=value>>distance;
        discarded=value<<(9'd27-distance);
        shift_jam27=shifted | {26'd0,|discarded};
      end
    end
  endfunction

  function automatic [47:0] shift_jam48(input [47:0] value,
    input [10:0] distance);
    reg [47:0] shifted,discarded;
    begin
      if (distance==0) shift_jam48=value;
      else if (distance>=48) shift_jam48={47'd0,|value};
      else begin
        shifted=value>>distance;
        discarded=value<<(11'd48-distance);
        shift_jam48=shifted | {47'd0,|discarded};
      end
    end
  endfunction

  function automatic [31:0] expand_f16(input [15:0] value);
    reg [5:0] zeros;
    reg [23:0] mantissa;
    reg [7:0] exponent;
    begin
      zeros=leading_zero32({value[9:0],22'd0});
      mantissa={value[9:0],14'd0}<<zeros;
      exponent=8'd112-zeros;
      if (value[14:0]==0) expand_f16=0;
      else if (value[14:10]==0)
        expand_f16={value[15],exponent,mantissa[22:0]};
      else if (value[14:10]==31)
        expand_f16={value[15],8'hff,value[9:0],13'd0};
      else expand_f16={value[15],8'(value[14:10]+8'd112),
        value[9:0],13'd0};
    end
  endfunction

  // Bit 32 reports overflow; the FP datapath never silently saturates.
  function automatic [32:0] round_pack_f32(input sign,
    input signed [10:0] exponent, input [26:0] significand);
    reg [24:0] rounded;
    reg signed [10:0] adjusted;
    reg increment;
    begin
      increment=significand[2] &&
        (significand[1] || significand[0] || significand[3]);
      rounded={1'b0,significand[26:3]}+{{24{1'b0}},increment};
      adjusted=exponent;
      if (rounded[24]) begin
        rounded=rounded>>1;
        adjusted=exponent+11'sd1;
      end
      if (rounded==0) round_pack_f32=0;
      else if (adjusted>=255)
        round_pack_f32={1'b1,32'd0};
      else if (adjusted<1)
        round_pack_f32={1'b1,32'd0};
      else if (adjusted==1 && !rounded[23])
        round_pack_f32={1'b0,sign,8'd0,rounded[22:0]};
      else round_pack_f32={1'b0,sign,adjusted[7:0],rounded[22:0]};
    end
  endfunction
endpackage
