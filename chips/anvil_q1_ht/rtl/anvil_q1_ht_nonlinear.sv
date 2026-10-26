module anvil_q1_ht_nonlinear (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  output wire in_ready,
  input wire in_silu,
  input wire signed [63:0] in_data,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_data,
  output wire out_error
);
  import anvil_q1_ht_numeric_pkg::*;
  localparam IDLE = 5'd0, RANGE_START = 5'd1, RANGE_WAIT = 5'd2,
             RANGE_MUL_START = 5'd3, RANGE_MUL_WAIT = 5'd4,
             RANGE_SUB_START = 5'd5, RANGE_SUB_WAIT = 5'd6,
             TERM_MUL_START = 5'd7, TERM_MUL_WAIT = 5'd8,
             TERM_DIV_START = 5'd9, TERM_DIV_WAIT = 5'd10,
             TOTAL_START = 5'd11, TOTAL_WAIT = 5'd12,
             EXP_FINISH = 5'd13, SIGMOID_START = 5'd14,
             SIGMOID_WAIT = 5'd15, SILU_MUL_START = 5'd16,
             SILU_MUL_WAIT = 5'd17, SILU_ROUND_START = 5'd18,
             SILU_ROUND_WAIT = 5'd19, RESULT = 5'd20;
  reg [4:0] state;
  reg silu, failed;
  reg signed [31:0] x;
  reg [63:0] u, range_quotient, range_remainder, term_divisor;
  reg signed [63:0] term, total;
  reg [31:0] exponential, result;
  reg [3:0] iteration;
  reg [127:0] temporary, sigmoid;
  reg math_valid;
  reg [3:0] math_op;
  reg [127:0] math_a, math_b;
  reg [6:0] math_shift;
  wire math_ready, math_out_valid, math_error;
  wire [127:0] math_result;
  wire [32:0] input_magnitude = in_data[31] ?
      -$signed({in_data[31], in_data[31:0]}) : {1'b0, in_data[31:0]};
  wire signed [32:0] silu_argument = -$signed(input_magnitude);
  wire signed [63:0] argument = in_silu ? {{31{silu_argument[32]}}, silu_argument} : in_data;
  wire [20:0] exp_magnitude = -argument[20:0];
  wire math_accept_result = math_out_valid;
  wire signed [24:0] negative_remainder = -$signed({1'b0, range_remainder[23:0]});
  wire [32:0] sigmoid_denominator = {1'b0, exponential} + 33'd16777216;

  assign in_ready = rst_n && state == IDLE;
  assign out_valid = rst_n && state == RESULT;
  assign out_data = out_valid && !failed ? result : 32'b0;
  assign out_error = out_valid && failed;

  anvil_q1_ht_math u_math (
    .clk(clk), .rst_n(rst_n), .in_valid(math_valid), .in_ready(math_ready),
    .in_op(math_op), .in_a(math_a), .in_b(math_b), .in_shift(math_shift),
    .out_valid(math_out_valid), .out_ready(1'b1),
    .out_data(math_result), .out_error(math_error)
  );

  always @* begin
    math_valid = 0;
    math_op = MATH_ADD;
    math_a = 0;
    math_b = 0;
    math_shift = 0;
    if (rst_n) case (state)
      RANGE_START: begin
        math_valid = 1;
        math_op = MATH_UDIV;
        math_a = {64'b0, u};
        math_b = 128'd11629080;
      end
      RANGE_MUL_START: begin
        math_valid = 1;
        math_op = MATH_MUL;
        math_a = {64'b0, range_quotient};
        math_b = 128'd11629080;
      end
      RANGE_SUB_START: begin
        math_valid = 1;
        math_op = MATH_SUB;
        math_a = {64'b0, u};
        math_b = temporary;
      end
      TERM_MUL_START: begin
        math_valid = 1;
        math_op = MATH_MUL;
        math_a = {{64{term[63]}}, term};
        math_b = {{103{negative_remainder[24]}}, negative_remainder};
      end
      TERM_DIV_START: begin
        math_valid = 1;
        math_op = MATH_TRUNC_DIV;
        math_a = {{64{temporary[63]}}, temporary[63:0]};
        math_b = {64'b0, term_divisor};
      end
      TOTAL_START: begin
        math_valid = 1;
        math_op = MATH_ADD;
        math_a = {{64{total[63]}}, total};
        math_b = {{64{term[63]}}, term};
      end
      SIGMOID_START: begin
        math_valid = 1;
        math_op = MATH_UDIV;
        math_a = x[31] ? {72'b0, exponential, 24'b0} : 128'd281474976710656;
        math_b = {95'b0, sigmoid_denominator};
      end
      SILU_MUL_START: begin
        math_valid = 1;
        math_op = MATH_MUL;
        math_a = {{96{x[31]}}, x};
        math_b = sigmoid;
      end
      SILU_ROUND_START: begin
        math_valid = 1;
        math_op = MATH_ROUND_SHIFT;
        math_a = {{63{temporary[64]}}, temporary[64:0]};
        math_shift = 24;
      end
      default: begin end
    endcase
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      silu <= 0;
      failed <= 0;
      x <= 0;
      u <= 0;
      range_quotient <= 0;
      range_remainder <= 0;
      term_divisor <= 0;
      term <= 0;
      total <= 0;
      exponential <= 0;
      result <= 0;
      iteration <= 0;
      temporary <= 0;
      sigmoid <= 0;
    end else if (math_accept_result && math_error) begin
      failed <= 1;
      state <= RESULT;
    end else case (state)
      IDLE: if (in_valid) begin
        silu <= in_silu;
        failed <= 0;
        x <= in_data[31:0];
        iteration <= 1;
        term_divisor <= 64'd16777216;
        term <= 64'sd16777216;
        total <= 64'sd16777216;
        if (in_silu && in_data != {{32{in_data[31]}}, in_data[31:0]}) begin
          failed <= 1;
          state <= RESULT;
        end else if (argument < -64'sd1048576) begin
          exponential <= 0;
          result <= 0;
          if (in_silu) state <= SIGMOID_START;
          else state <= RESULT;
        end else if (argument >= 0) begin
          exponential <= 32'd16777216;
          result <= 32'd16777216;
          if (in_silu) state <= SIGMOID_START;
          else state <= RESULT;
        end else begin
          u <= {35'b0, exp_magnitude, 8'b0};
          state <= RANGE_START;
        end
      end
      RANGE_START: if (math_ready) state <= RANGE_WAIT;
      RANGE_WAIT: if (math_accept_result) begin
        range_quotient <= math_result[63:0];
        state <= RANGE_MUL_START;
      end
      RANGE_MUL_START: if (math_ready) state <= RANGE_MUL_WAIT;
      RANGE_MUL_WAIT: if (math_accept_result) begin
        temporary <= math_result;
        state <= RANGE_SUB_START;
      end
      RANGE_SUB_START: if (math_ready) state <= RANGE_SUB_WAIT;
      RANGE_SUB_WAIT: if (math_accept_result) begin
        range_remainder <= math_result[63:0];
        state <= TERM_MUL_START;
      end
      TERM_MUL_START: if (math_ready) state <= TERM_MUL_WAIT;
      TERM_MUL_WAIT: if (math_accept_result) begin
        temporary <= math_result;
        state <= TERM_DIV_START;
      end
      TERM_DIV_START: if (math_ready) state <= TERM_DIV_WAIT;
      TERM_DIV_WAIT: if (math_accept_result) begin
        term <= math_result[63:0];
        state <= TOTAL_START;
      end
      TOTAL_START: if (math_ready) state <= TOTAL_WAIT;
      TOTAL_WAIT: if (math_accept_result) begin
        total <= math_result[63:0];
        if (iteration == 6) state <= EXP_FINISH;
        else begin
          iteration <= iteration + 4'd1;
          term_divisor <= term_divisor + 64'd16777216;
          state <= TERM_MUL_START;
        end
      end
      EXP_FINISH: begin
        if (total[63]) begin
          exponential <= 0;
          result <= 0;
        end else begin
          exponential <= total >> range_quotient;
          result <= total >> range_quotient;
        end
        if (silu) state <= SIGMOID_START;
        else state <= RESULT;
      end
      SIGMOID_START: if (math_ready) state <= SIGMOID_WAIT;
      SIGMOID_WAIT: if (math_accept_result) begin
        sigmoid <= {64'b0, math_result[63:0]};
        state <= SILU_MUL_START;
      end
      SILU_MUL_START: if (math_ready) state <= SILU_MUL_WAIT;
      SILU_MUL_WAIT: if (math_accept_result) begin
        temporary <= math_result;
        state <= SILU_ROUND_START;
      end
      SILU_ROUND_START: if (math_ready) state <= SILU_ROUND_WAIT;
      SILU_ROUND_WAIT: if (math_accept_result) begin
        result <= sat32($signed(math_result));
        state <= RESULT;
      end
      RESULT: if (out_ready) state <= IDLE;
      default: begin
        failed <= 1;
        state <= RESULT;
      end
    endcase
  end
endmodule
