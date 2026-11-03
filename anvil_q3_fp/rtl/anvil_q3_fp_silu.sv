module anvil_q3_fp_silu (
  input wire clk, rst_n, flush, start,
  input wire [31:0] x,
  output wire ready, done, error,
  output wire [31:0] value
);
  import anvil_q3_fp_pkg::*;

  localparam [3:0] IDLE=0, EXP=1, EXP_WAIT=2, ADD=3, ADD_WAIT=4,
    MULTIPLY=5, MULTIPLY_WAIT=6, DIVIDE=7, DIVIDE_WAIT=8, COMPLETE=9;
  reg [3:0] state;
  reg [31:0] operand, exponential, denominator, numerator, value_reg;
  reg error_reg;
  wire exp_ready, exp_done, exp_error;
  wire [31:0] exp_value;
  wire add_ready, add_valid;
  wire [31:0] add_value;
  wire [4:0] add_flags;
  wire multiply_ready, multiply_valid;
  wire [31:0] multiply_value;
  wire [4:0] multiply_flags;
  wire divide_ready, divide_done, divide_error;
  wire [31:0] divide_value;
  wire [4:0] divide_flags;

  assign ready = rst_n && !flush && state == IDLE;
  assign done = rst_n && !flush && state == COMPLETE;
  assign error = done && error_reg;
  assign value = rst_n && !flush ? value_reg : 32'd0;

  anvil_q3_fp_exp exp (
    .clk(clk),.rst_n(rst_n),.flush(flush),.start(state == EXP),
    .x({1'b1,operand[30:0]}),.ready(exp_ready),
    .done(exp_done),.error(exp_error),.value(exp_value)
  );
  anvil_q3_fp_add add (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state == ADD),.in_ready(add_ready),
    .in_a(32'h3f800000),.in_b(exponential),
    .out_valid(add_valid),.out_ready(state == ADD_WAIT),
    .out_data(add_value),.out_flags(add_flags)
  );
  anvil_q3_fp_mul multiply (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state == MULTIPLY),.in_ready(multiply_ready),
    .in_a(operand),.in_b(exponential),
    .out_valid(multiply_valid),.out_ready(state == MULTIPLY_WAIT),
    .out_data(multiply_value),.out_flags(multiply_flags)
  );
  anvil_q3_fp_divider divide (
    .clk(clk),.rst_n(rst_n),.flush(flush),.start(state == DIVIDE),
    .numerator(numerator),.denominator(denominator),
    .ready(divide_ready),.done(divide_done),.error(divide_error),
    .quotient(divide_value),.flags(divide_flags)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      operand <= 0;
      exponential <= 0;
      denominator <= 0;
      numerator <= 0;
      value_reg <= 0;
      error_reg <= 0;
    end else if (flush) begin
      state <= IDLE;
      value_reg <= 0;
      error_reg <= 0;
    end else case (state)
      IDLE: if (start && ready) begin
        error_reg <= 0;
        operand <= x;
        if (is_nan32(x)) begin
          value_reg <= CANONICAL_NAN;
          state <= COMPLETE;
        end else if (is_inf32(x)) begin
          value_reg <= x[31] ? 32'h80000000 : x;
          state <= COMPLETE;
        end else if (is_zero32(x)) begin
          value_reg <= x;
          state <= COMPLETE;
        end else state <= EXP;
      end
      EXP: if (exp_ready) state <= EXP_WAIT;
      EXP_WAIT: if (exp_done) begin
        if (exp_error) begin
          value_reg <= CANONICAL_NAN;
          error_reg <= 1;
          state <= COMPLETE;
        end else begin
          exponential <= exp_value;
          state <= ADD;
        end
      end
      ADD: if (add_ready) state <= ADD_WAIT;
      ADD_WAIT: if (add_valid) begin
        if (|add_flags[4:2]) begin
          value_reg <= CANONICAL_NAN;
          error_reg <= 1;
          state <= COMPLETE;
        end else begin
          denominator <= add_value;
          if (operand[31]) state <= MULTIPLY;
          else begin
            numerator <= operand;
            state <= DIVIDE;
          end
        end
      end
      MULTIPLY: if (multiply_ready) state <= MULTIPLY_WAIT;
      MULTIPLY_WAIT: if (multiply_valid) begin
        if (|multiply_flags[4:2]) begin
          value_reg <= CANONICAL_NAN;
          error_reg <= 1;
          state <= COMPLETE;
        end else begin
          numerator <= multiply_value;
          state <= DIVIDE;
        end
      end
      DIVIDE: if (divide_ready) state <= DIVIDE_WAIT;
      DIVIDE_WAIT: if (divide_done) begin
        value_reg <= divide_value;
        error_reg <= divide_error || (|divide_flags[4:2]);
        state <= COMPLETE;
      end
      COMPLETE: state <= IDLE;
      default: begin
        value_reg <= CANONICAL_NAN;
        error_reg <= 1;
        state <= COMPLETE;
      end
    endcase
  end
endmodule
