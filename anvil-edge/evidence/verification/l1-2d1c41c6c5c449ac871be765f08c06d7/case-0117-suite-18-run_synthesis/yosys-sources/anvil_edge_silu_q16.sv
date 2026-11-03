module anvil_edge_silu_q16 (
  input wire clk, rst_n,
  input wire in_valid,
  output wire in_ready,
  input wire signed [31:0] x,
  output wire out_valid,
  input wire out_ready,
  output wire signed [31:0] value,
  output wire arithmetic_error
);
  function automatic signed [31:0] sat32(input signed [127:0] x);
    begin
      if (x>128'sd2147483647) sat32=32'sh7fffffff;
      else if (x< -128'sd2147483648) sat32=32'sh80000000;
      else sat32=x[31:0];
    end
  endfunction

  function automatic signed [127:0] round_shift(
    input signed [127:0] x, input integer bits);
    reg [128:0] magnitude;
    begin
      magnitude=x<0 ? -$signed({x[127],x}) : {1'b0,x};
      if (bits>0) magnitude=(magnitude+(129'd1 << (bits-1))) >> bits;
      round_shift=x<0 ? -$signed(magnitude) : $signed(magnitude);
    end
  endfunction

  function automatic f16_invalid(input [15:0] h);
    begin f16_invalid=h[14:10]==5'd31; end
  endfunction

  function automatic [31:0] f16_scale(input [15:0] h);
    reg [31:0] magnitude;
    integer shift;
    begin
      magnitude=h[14:10]==0 ? {22'd0,h[9:0]} : {21'd0,1'b1,h[9:0]};
      shift=h[14:10]==0 ? -8 : $signed({27'd0,h[14:10]})-9;
      if (shift>=0) magnitude=magnitude << shift;
      else magnitude=(magnitude+(32'd1 << (-shift-1))) >> (-shift);
      f16_scale=magnitude;
    end
  endfunction

  function automatic signed [31:0] f16_q16(input [15:0] h);
    reg [31:0] magnitude;
    reg signed [32:0] signed_value;
    begin
      magnitude=f16_scale(h);
      signed_value=h[15] ? -$signed({1'b0,magnitude}) : $signed({1'b0,magnitude});
      f16_q16=sat32({{95{signed_value[32]}},signed_value});
    end
  endfunction

  localparam [3:0] IDLE=0, EXP=1, EXP_WAIT=2, DIVIDE=3, DIVIDE_WAIT=4,
    MULTIPLY=5, MULTIPLY_WAIT=6, ROUND=7, RETURN=8;
  reg [3:0] state;
  reg signed [31:0] operand, result;
  reg [63:0] magnitude, numerator, denominator, sigmoid;
  reg signed [64:0] truncated_product;
  reg failed;
  wire exp_ready, exp_valid, exp_error;
  wire [31:0] exponential;
  wire divider_ready, divider_valid, divide_by_zero;
  wire [63:0] quotient, remainder;
  wire multiplier_ready, multiplier_valid;
  wire signed [127:0] product;

  wire signed [63:0] yosys_signed_sigmoid=sigmoid;

  wire signed [63:0] yosys_extended_operand={{32{operand[31]}},operand};
  anvil_edge_exp_q24 exp_unit(
    .clk(clk),.rst_n(rst_n),.in_valid(state==EXP),.in_ready(exp_ready),
    .x(-$signed(magnitude)),.out_valid(exp_valid),.out_ready(state==EXP_WAIT),
    .value(exponential),.arithmetic_error(exp_error)
  );
  anvil_edge_unsigned_divider #(.WIDTH(64)) divider(
    .clk(clk),.rst_n(rst_n),.in_valid(state==DIVIDE),.in_ready(divider_ready),
    .numerator(numerator),.denominator(denominator),.out_valid(divider_valid),
    .out_ready(state==DIVIDE_WAIT),.quotient(quotient),.remainder(remainder),
    .divide_by_zero(divide_by_zero)
  );
  anvil_edge_signed_multiplier #(.WIDTH(64)) multiplier(
    .clk(clk),.rst_n(rst_n),.in_valid(state==MULTIPLY),.in_ready(multiplier_ready),
    .operand_a(yosys_extended_operand),.operand_b(yosys_signed_sigmoid),
    .out_valid(multiplier_valid),.out_ready(state==MULTIPLY_WAIT),.product(product)
  );
  assign in_ready=rst_n && state==IDLE;
  assign out_valid=rst_n && state==RETURN;
  assign value=rst_n ? result : 0;
  assign arithmetic_error=rst_n && failed;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; operand<=0; result<=0; magnitude<=0; numerator<=0;
      denominator<=0; sigmoid<=0; truncated_product<=0; failed<=0;
    end else case (state)
      IDLE: if (in_valid && in_ready) begin
        operand<=x;
        magnitude<=x<0 ? -$signed({{32{x[31]}},x}) : {32'd0,x};
        result<=0;
        failed<=0;
        state<=EXP;
      end
      EXP: if (exp_ready) state<=EXP_WAIT;
      EXP_WAIT: if (exp_valid) begin
        if (exp_error) begin failed<=1; state<=RETURN; end
        else begin
          numerator<=operand>=0 ? 64'd281474976710656 : {8'd0,exponential,24'd0};
          denominator<=64'd16777216+{32'd0,exponential};
          state<=DIVIDE;
        end
      end
      DIVIDE: if (divider_ready) state<=DIVIDE_WAIT;
      DIVIDE_WAIT: if (divider_valid) begin
        if (divide_by_zero) begin failed<=1; state<=RETURN; end
        else begin sigmoid<=quotient; state<=MULTIPLY; end
      end
      MULTIPLY: if (multiplier_ready) state<=MULTIPLY_WAIT;
      MULTIPLY_WAIT: if (multiplier_valid) begin
        truncated_product<=product[64:0];
        state<=ROUND;
      end
      ROUND: begin
        result<=sat32(round_shift(
          {{63{truncated_product[64]}},truncated_product},24));
        state<=RETURN;
      end
      RETURN: if (out_valid && out_ready) state<=IDLE;
      default: begin failed<=1; result<=0; state<=RETURN; end
    endcase
  end
endmodule
