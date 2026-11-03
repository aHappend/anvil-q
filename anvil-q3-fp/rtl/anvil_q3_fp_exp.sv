module anvil_q3_fp_exp (
  input wire clk, rst_n, flush, start,
  input wire [31:0] x,
  output wire ready, done, error,
  output wire [31:0] value
);
  import anvil_q3_fp_pkg::*;

  localparam [3:0] IDLE=0, MULTIPLY=1, MULTIPLY_WAIT=2,
    ADD=3, ADD_WAIT=4, SQUARE=5, SQUARE_WAIT=6, COMPLETE=7;
  reg [3:0] state;
  reg [31:0] reduced_x, accumulator, product, value_reg;
  reg [3:0] remaining_squares;
  reg [2:0] coefficient_index;
  reg error_reg;
  wire [3:0] input_squares =
    x[30:0] > 31'h3d800000 ? 4'(x[30:23]-8'd122) : 4'd0;
  wire [36:0] scaled_input =
    scale32(x,-$signed({9'd0,input_squares}));
  reg [31:0] coefficient;
  wire multiply_ready, multiply_valid;
  wire [31:0] multiply_value;
  wire [4:0] multiply_flags;
  wire add_ready, add_valid;
  wire [31:0] add_value;
  wire [4:0] add_flags;

  always @* begin
    case (coefficient_index)
      3'd4: coefficient = 32'h3d2aaaab;
      3'd3: coefficient = 32'h3e2aaaab;
      3'd2: coefficient = 32'h3f000000;
      default: coefficient = 32'h3f800000;
    endcase
  end

  assign ready = rst_n && !flush && state == IDLE;
  assign done = rst_n && !flush && state == COMPLETE;
  assign error = done && error_reg;
  assign value = rst_n && !flush ? value_reg : 32'd0;

  anvil_q3_fp_mul multiply (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state == MULTIPLY || state == SQUARE),.in_ready(multiply_ready),
    .in_a(accumulator),.in_b(state == SQUARE ? accumulator : reduced_x),
    .out_valid(multiply_valid),.out_ready(state == MULTIPLY_WAIT || state == SQUARE_WAIT),
    .out_data(multiply_value),.out_flags(multiply_flags)
  );
  anvil_q3_fp_add add (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state == ADD),.in_ready(add_ready),
    .in_a(product),.in_b(coefficient),
    .out_valid(add_valid),.out_ready(state == ADD_WAIT),
    .out_data(add_value),.out_flags(add_flags)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      reduced_x <= 0;
      accumulator <= 0;
      product <= 0;
      value_reg <= 0;
      remaining_squares <= 0;
      coefficient_index <= 0;
      error_reg <= 0;
    end else if (flush) begin
      state <= IDLE;
      value_reg <= 0;
      error_reg <= 0;
    end else case (state)
      IDLE: if (start && ready) begin
        error_reg <= 0;
        if (is_nan32(x) || (!x[31] && !is_zero32(x))) begin
          value_reg <= CANONICAL_NAN;
          error_reg <= 1;
          state <= COMPLETE;
        end else if (is_zero32(x)) begin
          value_reg <= 32'h3f800000;
          state <= COMPLETE;
        end else if (x[30:0] > 31'h42a00000) begin
          value_reg <= 0;
          state <= COMPLETE;
        end else begin
          reduced_x <= scaled_input[31:0];
          remaining_squares <= input_squares;
          accumulator <= 32'h3c088889;
          coefficient_index <= 3'd4;
          state <= MULTIPLY;
        end
      end
      MULTIPLY: if (multiply_ready) state <= MULTIPLY_WAIT;
      MULTIPLY_WAIT: if (multiply_valid) begin
        if (|multiply_flags[4:2]) begin
          value_reg <= CANONICAL_NAN;
          error_reg <= 1;
          state <= COMPLETE;
        end else begin
          product <= multiply_value;
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
          accumulator <= add_value;
          if (coefficient_index == 0) begin
            if (remaining_squares == 0) begin
              value_reg <= add_value;
              state <= COMPLETE;
            end else state <= SQUARE;
          end else begin
            coefficient_index <= coefficient_index-3'd1;
            state <= MULTIPLY;
          end
        end
      end
      SQUARE: if (multiply_ready) state <= SQUARE_WAIT;
      SQUARE_WAIT: if (multiply_valid) begin
        if (|multiply_flags[4:2]) begin
          value_reg <= CANONICAL_NAN;
          error_reg <= 1;
          state <= COMPLETE;
        end else begin
          accumulator <= multiply_value;
          remaining_squares <= remaining_squares-4'd1;
          if (remaining_squares == 1) begin
            value_reg <= multiply_value;
            state <= COMPLETE;
          end else state <= SQUARE;
        end
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
