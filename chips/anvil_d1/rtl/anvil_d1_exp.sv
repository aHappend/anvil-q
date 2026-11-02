module anvil_d1_exp (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire signed [32:0] in_x,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire [24:0] out_value
);
  localparam IDLE=0, REDUCE=1, REDUCE_WAIT=2, MULTIPLY=3, MULTIPLY_WAIT=4;
  localparam DIVIDE=5, DIVIDE_WAIT=6, ACCUMULATE=7;
  reg [2:0] state;
  reg armed, valid, failed;
  reg [2:0] iteration;
  reg [31:0] argument, reduction_remainder, exponent;
  reg signed [31:0] term, total;
  reg signed [63:0] numerator;
  reg [24:0] result;
  wire [32:0] negative_x;
  wire [31:0] negative_term;
  wire signed [31:0] multiplier_term=negative_term;
  wire signed [31:0] multiplier_remainder=reduction_remainder;
  wire unused_x_borrow, unused_term_borrow;
  wire reduce_ready, reduce_valid, reduce_error;
  wire [31:0] reduce_q, reduce_r;
  wire multiply_ready, multiply_valid;
  wire signed [63:0] product;
  wire divide_ready, divide_valid, divide_error;
  wire signed [64:0] quotient;
  wire [31:0] division_remainder;
  wire signed [32:0] next_total=$signed({total[31],total})+$signed({term[31],term});
  wire [32:0] nonnegative_total=next_total[32] ? 33'd0 : $unsigned(next_total);
  wire [32:0] shifted_total=nonnegative_total>>exponent;
  wire [31:0] taylor_denominator={5'd0,iteration,24'd0};
  anvil_d1_sub_unsigned #(.WIDTH(33)) negate_x (
    .a(33'd0),.b(in_x),.difference(negative_x),.borrow(unused_x_borrow)
  );
  anvil_d1_sub_unsigned #(.WIDTH(32)) negate_term (
    .a(32'd0),.b(term),.difference(negative_term),.borrow(unused_term_borrow)
  );
  anvil_d1_udiv #(.NUM_W(32),.DEN_W(32)) reduction (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==REDUCE),.in_ready(reduce_ready),
    .numerator(argument),.denominator(32'd11629080),
    .out_valid(reduce_valid),.out_ready(1'b1),.out_error(reduce_error),
    .quotient(reduce_q),.remainder(reduce_r)
  );
  anvil_d1_mul32 multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MULTIPLY),.in_ready(multiply_ready),
    .in_a(multiplier_term),.in_b(multiplier_remainder),
    .out_valid(multiply_valid),.out_ready(1'b1),.out_product(product)
  );
  anvil_d1_sdiv #(.NUM_W(64),.DEN_W(32)) divider (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==DIVIDE),.in_ready(divide_ready),
    .numerator(numerator),.denominator(taylor_denominator),
    .out_valid(divide_valid),.out_ready(1'b1),.out_error(divide_error),
    .quotient(quotient),.remainder(division_remainder)
  );
  assign in_ready=rst_n && armed && !flush && state==IDLE && !valid;
  assign out_valid=rst_n && !flush && valid;
  assign out_error=out_valid && failed;
  assign out_value=rst_n && !flush ? result : 25'd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; valid<=0; failed<=0; iteration<=0;
      argument<=0; reduction_remainder<=0; exponent<=0; term<=0; total<=0;
      numerator<=0; result<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; valid<=0; failed<=0; result<=0; end
      else if ((reduce_valid && reduce_error) || (divide_valid && divide_error)) begin
        state<=IDLE; valid<=1; failed<=1;
      end else begin
        if (out_valid && out_ready) valid<=0;
        case (state)
          IDLE: if (in_valid && in_ready) begin
            failed<=0;
            if (in_x>=0) begin result<=25'd16777216; valid<=1; end
            else if (in_x< -33'sd1048576) begin result<=0; valid<=1; end
            else begin
              argument<=negative_x[31:0]<<8; state<=REDUCE;
              term<=32'sd16777216; total<=32'sd16777216; iteration<=1;
            end
          end
          REDUCE: if (reduce_ready) state<=REDUCE_WAIT;
          REDUCE_WAIT: if (reduce_valid) begin
            exponent<=reduce_q; reduction_remainder<=reduce_r; state<=MULTIPLY;
          end
          MULTIPLY: if (multiply_ready) state<=MULTIPLY_WAIT;
          MULTIPLY_WAIT: if (multiply_valid) begin numerator<=product; state<=DIVIDE; end
          DIVIDE: if (divide_ready) state<=DIVIDE_WAIT;
          DIVIDE_WAIT: if (divide_valid) begin
            if (quotient[64:32]!={33{quotient[31]}}) begin
              failed<=1; valid<=1; state<=IDLE;
            end else begin term<=quotient[31:0]; state<=ACCUMULATE; end
          end
          ACCUMULATE: begin
            if (next_total[32]!=next_total[31]) begin
              failed<=1; valid<=1; state<=IDLE;
            end else begin
              total<=next_total[31:0];
              if (iteration==6) begin result<=shifted_total[24:0]; valid<=1; state<=IDLE; end
              else begin iteration<=iteration+1'b1; state<=MULTIPLY; end
            end
          end
          default: begin state<=IDLE; valid<=1; failed<=1; end
        endcase
      end
    end
  end
endmodule
