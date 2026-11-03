module anvil_q1_ht3_fp32_divsqrt (
  input wire clk, rst_n, enable, req_valid,
  output wire req_ready,
  input wire req_sqrt,
  input wire [31:0] req_a, req_b,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_data
);
  import anvil_q1_ht3_fp_pkg::*;
  localparam IDLE = 4'd0, NORMALIZE = 4'd1, SETUP = 4'd2,
    DIVIDE = 4'd3, SQRT = 4'd4, ROUND = 4'd5,
    WAIT_RELEASE = 4'd6, RESPONSE = 4'd7;
  wire run_n;
  reg [3:0] state;
  reg [5:0] elapsed;
  reg [4:0] iteration;
  reg sqrt_q, sign_q, special_q;
  reg [31:0] a_q, b_q, special_data, response_data;
  reg [23:0] normalized_a, normalized_b, divisor;
  reg signed [10:0] exponent_a, exponent_b, result_scale;
  reg [24:0] div_remainder;
  reg [26:0] quotient;
  reg [53:0] radicand;
  reg [28:0] sqrt_remainder;
  reg [26:0] root;
  reg [27:0] round_significand;
  wire [23:0] raw_a = {(|a_q[30:23]), a_q[22:0]};
  wire [23:0] raw_b = {(|b_q[30:23]), b_q[22:0]};
  wire [5:0] leading_a = leading_bit64({40'b0, raw_a});
  wire [5:0] leading_b = leading_bit64({40'b0, raw_b});
  wire [5:0] shift_a = 6'd23 - leading_a;
  wire [5:0] shift_b = 6'd23 - leading_b;
  wire signed [10:0] decoded_exponent_a =
    (a_q[30:23] == 0 ? -11'sd126 :
     $signed({3'b0, a_q[30:23]}) - 11'sd127) - $signed({5'b0, shift_a});
  wire signed [10:0] decoded_exponent_b =
    (b_q[30:23] == 0 ? -11'sd126 :
     $signed({3'b0, b_q[30:23]}) - 11'sd127) - $signed({5'b0, shift_b});
  wire signed [10:0] even_exponent =
    exponent_a[0] ? exponent_a - 11'sd1 : exponent_a;
  wire [24:0] sqrt_mantissa =
    exponent_a[0] ? {normalized_a, 1'b0} : {1'b0, normalized_a};
  wire a_zero = a_q[30:0] == 0;
  wire b_zero = b_q[30:0] == 0;
  wire a_inf = a_q[30:23] == 8'hff && a_q[22:0] == 0;
  wire b_inf = b_q[30:23] == 8'hff && b_q[22:0] == 0;
  wire div_special =
    fp32_nonfinite(a_q) || fp32_nonfinite(b_q) || a_zero || b_zero;
  wire sqrt_special = fp32_nonfinite(a_q) || a_zero || a_q[31];
  wire [25:0] div_difference = {1'b0, div_remainder} - {2'b0, divisor};
  wire div_bit = !div_difference[25];
  wire [24:0] div_residue =
    div_bit ? div_difference[24:0] : div_remainder;
  wire [26:0] next_quotient = {quotient[25:0], div_bit};
  wire [28:0] shifted_sqrt_remainder =
    {sqrt_remainder[26:0], radicand[53:52]};
  wire [28:0] sqrt_trial = {root, 2'b01};
  wire [29:0] sqrt_difference =
    {1'b0, shifted_sqrt_remainder} - {1'b0, sqrt_trial};
  wire sqrt_bit = !sqrt_difference[29];
  wire [28:0] next_sqrt_remainder =
    sqrt_bit ? sqrt_difference[28:0] : shifted_sqrt_remainder;
  wire [26:0] next_root = {root[25:0], sqrt_bit};
  wire [31:0] rounded =
    pack32(sign_q, {36'b0, round_significand}, int'(result_scale));
  reg [31:0] exceptional;

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  assign req_ready = run_n && enable && state == IDLE;
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_data = rsp_valid ? response_data : 32'b0;

  always @* begin
    exceptional = FP32_QNAN;
    if (sqrt_q) begin
      if (fp32_nan(a_q) || (a_q[31] && !a_zero)) exceptional = FP32_QNAN;
      else exceptional = a_q;
    end else begin
      if (fp32_nan(a_q) || fp32_nan(b_q) ||
          (a_zero && b_zero) || (a_inf && b_inf))
        exceptional = FP32_QNAN;
      else if (a_inf || b_zero)
        exceptional = {a_q[31] ^ b_q[31], 8'hff, 23'b0};
      else exceptional = {a_q[31] ^ b_q[31], 31'b0};
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      elapsed <= 0;
      iteration <= 0;
      sqrt_q <= 0;
      sign_q <= 0;
      special_q <= 0;
      a_q <= 0;
      b_q <= 0;
      special_data <= 0;
      response_data <= 0;
      normalized_a <= 0;
      normalized_b <= 0;
      divisor <= 0;
      exponent_a <= 0;
      exponent_b <= 0;
      result_scale <= 0;
      div_remainder <= 0;
      quotient <= 0;
      radicand <= 0;
      sqrt_remainder <= 0;
      root <= 0;
      round_significand <= 0;
    end else if (run_n) begin
      case (state)
        IDLE: if (req_valid && req_ready) begin
          a_q <= req_a;
          b_q <= req_b;
          sqrt_q <= req_sqrt;
          elapsed <= 0;
          iteration <= 0;
          state <= NORMALIZE;
        end
        NORMALIZE: begin
          normalized_a <= raw_a << shift_a;
          normalized_b <= raw_b << shift_b;
          exponent_a <= decoded_exponent_a;
          exponent_b <= decoded_exponent_b;
          special_q <= sqrt_q ? sqrt_special : div_special;
          special_data <= exceptional;
          state <= SETUP;
        end
        SETUP: begin
          quotient <= 0;
          root <= 0;
          sqrt_remainder <= 0;
          if (special_q) begin
            response_data <= special_data;
            state <= WAIT_RELEASE;
          end else if (sqrt_q) begin
            sign_q <= 0;
            result_scale <= (even_exponent >>> 1) - 11'sd26;
            radicand <= {sqrt_mantissa, 29'b0};
            state <= SQRT;
          end else begin
            sign_q <= a_q[31] ^ b_q[31];
            result_scale <= exponent_a - exponent_b - 11'sd26;
            divisor <= normalized_b;
            div_remainder <= {1'b0, normalized_a};
            state <= DIVIDE;
          end
        end
        DIVIDE: begin
          quotient <= next_quotient;
          div_remainder <= div_residue << 1;
          if (iteration == 5'd26) begin
            round_significand <= {1'b0, next_quotient[26:1],
                                   next_quotient[0] || (|div_residue)};
            state <= ROUND;
          end else iteration <= iteration + 1'b1;
        end
        SQRT: begin
          root <= next_root;
          sqrt_remainder <= next_sqrt_remainder;
          radicand <= radicand << 2;
          if (iteration == 5'd26) begin
            round_significand <= {1'b0, next_root[26:1],
                                   next_root[0] || (|next_sqrt_remainder)};
            state <= ROUND;
          end else iteration <= iteration + 1'b1;
        end
        ROUND: begin
          response_data <= rounded;
          state <= WAIT_RELEASE;
        end
        WAIT_RELEASE: begin end
        RESPONSE: if (rsp_valid && rsp_ready) state <= IDLE;
        default: begin
          response_data <= FP32_QNAN;
          state <= WAIT_RELEASE;
        end
      endcase
      if (state != IDLE && state != RESPONSE) begin
        elapsed <= elapsed + 1'b1;
        if (elapsed == 6'd63) state <= RESPONSE;
      end
    end
  end
endmodule
