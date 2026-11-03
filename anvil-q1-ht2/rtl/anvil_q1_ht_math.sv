module anvil_q1_ht_math (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  output wire in_ready,
  input wire [3:0] in_op,
  input wire [127:0] in_a,
  input wire [127:0] in_b,
  input wire [6:0] in_shift,
  output wire out_valid,
  input wire out_ready,
  output wire [127:0] out_data,
  output wire out_error
);
  import anvil_q1_ht_numeric_pkg::*;
  localparam IDLE = 5'd0, ADD = 5'd1, MUL_DIGIT = 5'd2,
             MUL_ADD = 5'd3, SHIFT_LOW = 5'd4, SHIFT_HIGH = 5'd5,
             SHIFT_ROUND = 5'd6, MAGNITUDE = 5'd7, DIV_BIAS = 5'd8,
             DIV_START = 5'd9, DIV_WAIT = 5'd10, NEGATE = 5'd11,
             SQRT_START = 5'd12, SQRT_WAIT = 5'd13, RESULT = 5'd14;
  reg [4:0] state;
  reg [3:0] op;
  reg [127:0] a, b, result, shifted;
  reg [159:0] magnitude, bias_operand;
  reg [2:0] chunk, digit_a, digit_b;
  reg [6:0] shift_bits;
  reg carry, negative, increment, failed;
  (* multstyle = "dsp" *) reg [31:0] partial_product;
  wire [6:0] partial_shift = ({4'b0, digit_a} + {4'b0, digit_b}) << 4;
  wire [127:0] partial_operand = {96'b0, partial_product} << partial_shift;
  wire [31:0] add_b = op == MATH_SUB ? ~b[32*chunk+:32] : b[32*chunk+:32];
  wire [32:0] add_sum = {1'b0, a[32*chunk+:32]} +
                        {1'b0, add_b} + {32'b0, carry};
  wire [32:0] multiply_sum = {1'b0, result[32*chunk+:32]} +
                             {1'b0, partial_operand[32*chunk+:32]} +
                             {32'b0, carry};
  wire [32:0] increment_sum = {1'b0, shifted[32*chunk+:32]} + {32'b0, carry};
  wire [31:0] mag_word = chunk == 4 ? {32{negative}} : a[32*chunk+:32];
  wire [32:0] magnitude_sum =
    {1'b0, (negative ? ~mag_word : mag_word)} + {32'b0, carry};
  wire [32:0] bias_sum = {1'b0, magnitude[32*chunk+:32]} +
                         {1'b0, bias_operand[32*chunk+:32]} + {32'b0, carry};
  wire [32:0] negate_sum = {1'b0, ~a[32*chunk+:32]} + {32'b0, carry};
  wire div_ready, div_valid, div_error;
  wire [128:0] quotient, unused_remainder;
  wire sqrt_ready, sqrt_valid;
  wire [63:0] root;
  wire [127:0] remainder_mask = ~(128'hffffffffffffffffffffffffffffffff << shift_bits);
  wire [127:0] halfway = 128'd1 << (shift_bits - 7'd1);
  wire round_bit = |(a & halfway);
  wire lower_nonzero = |(a & (remainder_mask >> 1));

  assign in_ready = rst_n && state == IDLE;
  assign out_valid = rst_n && state == RESULT;
  assign out_data = out_valid && !failed ? result : 128'b0;
  assign out_error = out_valid && failed;

  anvil_q1_ht_divide #(.WIDTH(129)) u_divide (
    .clk(clk), .rst_n(rst_n), .in_valid(state == DIV_START),
    .in_ready(div_ready), .numerator(magnitude[128:0]),
    .denominator({1'b0, b}), .out_valid(div_valid),
    .out_ready(state == DIV_WAIT), .quotient(quotient),
    .remainder(unused_remainder), .divide_by_zero(div_error)
  );
  anvil_q1_ht_isqrt u_isqrt (
    .clk(clk), .rst_n(rst_n), .in_valid(state == SQRT_START),
    .in_ready(sqrt_ready), .in_data(a), .out_valid(sqrt_valid),
    .out_ready(state == SQRT_WAIT), .out_root(root)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      op <= 0;
      a <= 0;
      b <= 0;
      result <= 0;
      shifted <= 0;
      magnitude <= 0;
      bias_operand <= 0;
      chunk <= 0;
      digit_a <= 0;
      digit_b <= 0;
      shift_bits <= 0;
      carry <= 0;
      negative <= 0;
      increment <= 0;
      failed <= 0;
      partial_product <= 0;
    end else case (state)
      IDLE: if (in_valid) begin
        op <= in_op;
        a <= in_a;
        b <= in_b;
        shift_bits <= in_shift;
        result <= 0;
        chunk <= 0;
        digit_a <= 0;
        digit_b <= 0;
        failed <= 0;
        carry <= in_op == MATH_SUB;
        negative <= in_op != MATH_UDIV && in_a[127];
        case (in_op)
          MATH_ADD, MATH_SUB: state <= ADD;
          MATH_MUL: state <= MUL_DIGIT;
          MATH_ROUND_SHIFT: state <= SHIFT_LOW;
          MATH_ROUND_DIV, MATH_TRUNC_DIV, MATH_UDIV: begin
            carry <= in_op != MATH_UDIV && in_a[127];
            state <= MAGNITUDE;
          end
          MATH_ISQRT: state <= SQRT_START;
          default: begin
            failed <= 1;
            state <= RESULT;
          end
        endcase
      end
      ADD: begin
        result[32*chunk+:32] <= add_sum[31:0];
        carry <= add_sum[32];
        if (chunk == 3) state <= RESULT;
        else chunk <= chunk + 3'd1;
      end
      MUL_DIGIT: begin
        partial_product <= a[16*digit_a+:16] * b[16*digit_b+:16];
        carry <= 0;
        chunk <= 0;
        state <= MUL_ADD;
      end
      MUL_ADD: begin
        result[32*chunk+:32] <= multiply_sum[31:0];
        carry <= multiply_sum[32];
        if (chunk != 3) chunk <= chunk + 3'd1;
        else if (digit_a + digit_b == 7) begin
          if (digit_a == 7) state <= RESULT;
          else begin
            digit_a <= digit_a + 3'd1;
            digit_b <= 0;
            state <= MUL_DIGIT;
          end
        end else begin
          digit_b <= digit_b + 3'd1;
          state <= MUL_DIGIT;
        end
      end
      SHIFT_LOW: begin
        shifted <= $signed(a) >>> shift_bits[3:0];
        if (shift_bits == 0) increment <= 0;
        else if (a[127]) increment <= round_bit && lower_nonzero;
        else increment <= round_bit;
        state <= SHIFT_HIGH;
      end
      SHIFT_HIGH: begin
        shifted <= $signed(shifted) >>> {shift_bits[6:4], 4'b0};
        carry <= increment;
        chunk <= 0;
        state <= SHIFT_ROUND;
      end
      SHIFT_ROUND: begin
        result[32*chunk+:32] <= increment_sum[31:0];
        carry <= increment_sum[32];
        if (chunk == 3) state <= RESULT;
        else chunk <= chunk + 3'd1;
      end
      MAGNITUDE: begin
        magnitude[32*chunk+:32] <= magnitude_sum[31:0];
        carry <= magnitude_sum[32];
        if (chunk == 4) begin
          chunk <= 0;
          carry <= 0;
          bias_operand <= {33'b0, b[127:1]};
          if (op == MATH_ROUND_DIV) state <= DIV_BIAS;
          else state <= DIV_START;
        end else chunk <= chunk + 3'd1;
      end
      DIV_BIAS: begin
        magnitude[32*chunk+:32] <= bias_sum[31:0];
        carry <= bias_sum[32];
        if (chunk == 4) state <= DIV_START;
        else chunk <= chunk + 3'd1;
      end
      DIV_START: if (div_ready) state <= DIV_WAIT;
      DIV_WAIT: if (div_valid) begin
        failed <= div_error;
        if (negative && !div_error) begin
          a <= quotient[127:0];
          chunk <= 0;
          carry <= 1;
          state <= NEGATE;
        end else begin
          result <= quotient[127:0];
          state <= RESULT;
        end
      end
      NEGATE: begin
        result[32*chunk+:32] <= negate_sum[31:0];
        carry <= negate_sum[32];
        if (chunk == 3) state <= RESULT;
        else chunk <= chunk + 3'd1;
      end
      SQRT_START: if (sqrt_ready) state <= SQRT_WAIT;
      SQRT_WAIT: if (sqrt_valid) begin
        result <= {64'b0, root};
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
