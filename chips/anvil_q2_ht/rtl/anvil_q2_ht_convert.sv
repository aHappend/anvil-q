module anvil_q2_ht_convert (
  input wire clk, rst_n,
  input wire s_valid,
  output wire s_ready,
  input wire [3:0] s_op,
  input wire [31:0] s_data,
  output wire m_valid,
  input wire m_ready,
  output wire [31:0] m_data,
  output wire m_error
);
  import anvil_q2_ht_fp_pkg::*;
  reg [2:0] valid;
  reg [3:0] op0, op1;
  reg [31:0] data0, original1;
  reg sign1, error1, error2;
  reg [31:0] magnitude1, result2;
  reg signed [9:0] shift1;
  reg decoded_sign, decoded_error;
  reg [31:0] decoded_magnitude;
  reg signed [9:0] decoded_shift;
  wire advance=rst_n && (!valid[2] || m_ready);

  function automatic [31:0] to_q16(
    input sign_bit, input [31:0] magnitude, input signed [9:0] shift);
    reg [63:0] rounded;
    begin
      rounded=0;
      if (magnitude!=0) begin
        if (shift>31) rounded=64'hffffffffffffffff;
        else if (shift>=0) rounded={32'd0,magnitude} << shift;
        else if (shift>=-32)
          rounded=({32'd0,magnitude}+(64'd1 << (-shift-1))) >> (-shift);
      end
      if (!sign_bit && rounded>64'd2147483647) to_q16=32'h7fffffff;
      else if (sign_bit && rounded>=64'd2147483648) to_q16=32'h80000000;
      else to_q16=sign_bit ? (~rounded[31:0]+32'd1) : rounded[31:0];
    end
  endfunction

  function automatic [31:0] from_q16(
    input [3:0] operation, input sign_bit, input [31:0] magnitude);
    reg [5:0] bit_index, precision_bits, distance;
    reg [8:0] exponent;
    reg [63:0] retained, remainder, midpoint;
    begin
      bit_index=6'd31-leading32(magnitude);
      if (operation==3) precision_bits=11;
      else if (operation==4) precision_bits=8;
      else precision_bits=24;
      retained=0; remainder=0; midpoint=0; distance=0;
      exponent={3'd0,bit_index}+9'd111;
      if (bit_index>=precision_bits) begin
        distance=bit_index-(precision_bits-6'd1);
        retained={32'd0,magnitude} >> distance;
        remainder={32'd0,magnitude} & ((64'd1 << distance)-64'd1);
        midpoint=64'd1 << (distance-6'd1);
        if (remainder>midpoint || (remainder==midpoint && retained[0]))
          retained=retained+64'd1;
      end else retained={32'd0,magnitude} << (precision_bits-6'd1-bit_index);
      if (retained[precision_bits]) begin
        retained=retained >> 1;
        exponent=exponent+9'd1;
      end
      if (magnitude==0) from_q16=0;
      else if (operation==3) begin
        if (bit_index<2) from_q16={16'd0,sign_bit,5'd0,10'(magnitude << 8)};
        else from_q16={16'd0,sign_bit,5'(exponent-9'd112),retained[9:0]};
      end else if (operation==4)
        from_q16={16'd0,sign_bit,exponent[7:0],retained[6:0]};
      else from_q16={sign_bit,exponent[7:0],retained[22:0]};
    end
  endfunction

  function automatic [31:0] f16_to_fp32(input [15:0] value);
    reg [5:0] bit_index;
    reg [7:0] exponent;
    reg [31:0] significand;
    begin
      bit_index=6'd31-leading32({22'd0,value[9:0]});
      exponent=8'd103+{2'd0,bit_index};
      significand={22'd0,value[9:0]} << (6'd23-bit_index);
      if (value[14:10]!=0)
        f16_to_fp32={value[15],(value[14:10]+8'd112),value[9:0],13'd0};
      else if (value[9:0]==0) f16_to_fp32={value[15],31'd0};
      else f16_to_fp32={value[15],exponent,significand[22:0]};
    end
  endfunction

  always @* begin
    decoded_sign=data0[31];
    decoded_magnitude=0;
    decoded_shift=0;
    decoded_error=0;
    case (op0)
      0,6: begin
        decoded_sign=data0[15];
        decoded_magnitude={21'd0,(|data0[14:10]),data0[9:0]};
        if (data0[14:10]==0) decoded_shift=-10'sd8;
        else decoded_shift=$signed({5'd0,data0[14:10]})-10'sd9;
        decoded_error=data0[14:10]==31;
      end
      1,7: begin
        decoded_sign=data0[15];
        decoded_magnitude={24'd0,(|data0[14:7]),data0[6:0]};
        if (data0[14:7]==0) decoded_shift=-10'sd117;
        else decoded_shift=$signed({2'd0,data0[14:7]})-10'sd118;
        decoded_error=data0[14:7]==255;
      end
      2: begin
        decoded_magnitude={8'd0,(|data0[30:23]),data0[22:0]};
        if (data0[30:23]==0) decoded_shift=-10'sd133;
        else decoded_shift=$signed({2'd0,data0[30:23]})-10'sd134;
        decoded_error=data0[30:23]==255;
      end
      3,4,5: decoded_magnitude=data0[31] ? (~data0+32'd1) : data0;
      default: decoded_error=1;
    endcase
  end

  assign s_ready=advance;
  assign m_valid=rst_n && valid[2];
  assign m_data=m_valid ? result2 : 32'd0;
  assign m_error=m_valid && error2;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0; op0<=0; op1<=0; data0<=0; original1<=0;
      sign1<=0; error1<=0; error2<=0;
      magnitude1<=0; result2<=0; shift1<=0;
    end else if (advance) begin
      valid<={valid[1:0],s_valid};
      op0<=s_valid ? s_op : 4'd0;
      data0<=s_valid ? s_data : 32'd0;
      op1<=op0; original1<=data0;
      sign1<=decoded_sign; error1<=decoded_error;
      magnitude1<=decoded_magnitude; shift1<=decoded_shift;
      error2<=error1;
      if (error1) result2<=0;
      else case (op1)
        0,1,2: result2<=to_q16(sign1,magnitude1,shift1);
        3,4,5: result2<=from_q16(op1,sign1,magnitude1);
        6: result2<=f16_to_fp32(original1[15:0]);
        7: result2<={original1[15:0],16'd0};
        default: result2<=0;
      endcase
    end
  end
endmodule
