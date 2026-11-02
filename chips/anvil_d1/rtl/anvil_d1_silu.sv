module anvil_d1_silu (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire signed [31:0] in_x,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire signed [31:0] out_value
);
  localparam IDLE=0, EXPONENTIAL=1, EXPONENTIAL_WAIT=2, DIVIDE=3, DIVIDE_WAIT=4;
  localparam MULTIPLY=5, MULTIPLY_WAIT=6, ROUND=7, ROUND_WAIT=8;
  reg [3:0] state;
  reg armed, valid, failed;
  reg signed [31:0] x;
  reg [24:0] exponential;
  reg [31:0] sigmoid;
  reg signed [63:0] product;
  reg signed [31:0] result;
  wire [32:0] negated_x, negative_absolute;
  wire [32:0] absolute=x[31] ? negated_x : {1'b0,x};
  wire unused_x_borrow, unused_abs_borrow;
  wire exp_ready, exp_valid, exp_error;
  wire [24:0] exp_result;
  wire divide_ready, divide_valid, divide_error;
  wire [48:0] quotient;
  wire [25:0] remainder;
  wire multiply_ready, multiply_valid;
  wire signed [63:0] multiply_result;
  wire round_ready, round_valid;
  wire signed [31:0] round_result;
  anvil_d1_sub_unsigned #(.WIDTH(33)) negate_x (
    .a(33'd0),.b({x[31],x}),.difference(negated_x),.borrow(unused_x_borrow)
  );
  anvil_d1_sub_unsigned #(.WIDTH(33)) negate_absolute (
    .a(33'd0),.b(absolute),.difference(negative_absolute),.borrow(unused_abs_borrow)
  );
  anvil_d1_exp exponential_unit (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==EXPONENTIAL),.in_ready(exp_ready),.in_x($signed(negative_absolute)),
    .out_valid(exp_valid),.out_ready(1'b1),.out_error(exp_error),.out_value(exp_result)
  );
  anvil_d1_udiv #(.NUM_W(49),.DEN_W(26)) divider (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==DIVIDE),.in_ready(divide_ready),
    .numerator(x[31] ? {exponential,24'd0} : (49'd1<<48)),
    .denominator(26'd16777216+{1'b0,exponential}),
    .out_valid(divide_valid),.out_ready(1'b1),.out_error(divide_error),
    .quotient(quotient),.remainder(remainder)
  );
  anvil_d1_mul32 multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MULTIPLY),.in_ready(multiply_ready),
    .in_a(x),.in_b($signed(sigmoid)),
    .out_valid(multiply_valid),.out_ready(1'b1),.out_product(multiply_result)
  );
  anvil_d1_round_sat #(.SHIFT(24)) boundary (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ROUND),.in_ready(round_ready),
    .in_value({{64{product[63]}},product}),
    .out_valid(round_valid),.out_ready(1'b1),.out_value(round_result)
  );
  assign in_ready=rst_n && armed && !flush && state==IDLE && !valid;
  assign out_valid=rst_n && !flush && valid;
  assign out_error=out_valid && failed;
  assign out_value=rst_n && !flush ? result : 32'sd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; valid<=0; failed<=0; x<=0;
      exponential<=0; sigmoid<=0; product<=0; result<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; valid<=0; failed<=0; result<=0; end
      else if ((exp_valid && exp_error) || (divide_valid && divide_error)) begin
        failed<=1; valid<=1; state<=IDLE;
      end else begin
        if (out_valid && out_ready) valid<=0;
        case (state)
          IDLE: if (in_valid && in_ready) begin x<=in_x; failed<=0; state<=EXPONENTIAL; end
          EXPONENTIAL: if (exp_ready) state<=EXPONENTIAL_WAIT;
          EXPONENTIAL_WAIT: if (exp_valid) begin exponential<=exp_result; state<=DIVIDE; end
          DIVIDE: if (divide_ready) state<=DIVIDE_WAIT;
          DIVIDE_WAIT: if (divide_valid) begin
            if (quotient>49'd16777216) begin failed<=1; valid<=1; state<=IDLE; end
            else begin sigmoid<=quotient[31:0]; state<=MULTIPLY; end
          end
          MULTIPLY: if (multiply_ready) state<=MULTIPLY_WAIT;
          MULTIPLY_WAIT: if (multiply_valid) begin product<=multiply_result; state<=ROUND; end
          ROUND: if (round_ready) state<=ROUND_WAIT;
          ROUND_WAIT: if (round_valid) begin result<=round_result; valid<=1; state<=IDLE; end
          default: begin state<=IDLE; failed<=1; valid<=1; end
        endcase
      end
    end
  end
endmodule
