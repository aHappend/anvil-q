package anvil_q2_ht2_fp_pkg;
  function automatic [31:0] exp_coefficient(input integer index);
    begin
      case (index)
        0,1: exp_coefficient=32'h3f800000;
        2: exp_coefficient=32'h3f000000;
        3: exp_coefficient=32'h3e2aaaab;
        4: exp_coefficient=32'h3d2aaaab;
        5: exp_coefficient=32'h3c088889;
        6: exp_coefficient=32'h3ab60b61;
        7: exp_coefficient=32'h39500d01;
        8: exp_coefficient=32'h37d00d01;
        9: exp_coefficient=32'h3638ef1d;
        10: exp_coefficient=32'h3493f27e;
        11: exp_coefficient=32'h32d7322b;
        12: exp_coefficient=32'h310f76c7;
        default: exp_coefficient=32'h7fc00000;
      endcase
    end
  endfunction

  function automatic [5:0] leading32(input [31:0] value);
    reg [31:0] work;
    reg [5:0] count;
    begin
      work=value;
      count=0;
      if (work[31:16]==0) begin count=count+16; work=work << 16; end
      if (work[31:24]==0) begin count=count+8; work=work << 8; end
      if (work[31:28]==0) begin count=count+4; work=work << 4; end
      if (work[31:30]==0) begin count=count+2; work=work << 2; end
      if (!work[31]) count=count+1;
      leading32=value==0 ? 6'd32 : count;
    end
  endfunction

  function automatic [26:0] right_jam27(
    input [26:0] value, input [11:0] distance);
    reg [26:0] work;
    begin
      work=value;
      if (distance[0]) work={1'b0,work[26:2],|work[1:0]};
      if (distance[1]) work={2'b0,work[26:3],|work[2:0]};
      if (distance[2]) work={4'b0,work[26:5],|work[4:0]};
      if (distance[3]) work={8'b0,work[26:9],|work[8:0]};
      if (distance[4]) work={16'b0,work[26:17],|work[16:0]};
      if (|distance[11:5]) work={26'd0,|value};
      right_jam27=work;
    end
  endfunction

  // Effective biased exponent is one for subnormals. G/R/S occupy bits 2:0.
  function automatic [32:0] pack_fp32(
    input sign_bit, input [11:0] exponent, input [26:0] significand);
    reg [24:0] rounded;
    reg [11:0] result_exponent;
    reg [23:0] mantissa;
    begin
      rounded={1'b0,significand[26:3]}+
        {24'd0,(significand[2] &&
          (significand[1] || significand[0] || significand[3]))};
      result_exponent=exponent;
      mantissa=rounded[23:0];
      if (rounded[24]) begin
        mantissa=rounded[24:1];
        result_exponent=exponent+12'd1;
      end
      if (significand==0)
        pack_fp32={1'b0,sign_bit,31'd0};
      else if (result_exponent>=255)
        pack_fp32={1'b1,sign_bit,8'hff,23'd0};
      else if (!mantissa[23])
        pack_fp32={1'b0,sign_bit,8'd0,mantissa[22:0]};
      else
        pack_fp32={1'b0,sign_bit,result_exponent[7:0],mantissa[22:0]};
    end
  endfunction
endpackage
