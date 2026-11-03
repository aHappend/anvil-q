module anvil_q1_ht2_fp32_divsqrt (
  input wire clk, rst_n, enable, req_valid,
  output wire req_ready,
  input wire req_sqrt,
  input wire [31:0] req_a, req_b,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_data
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam IDLE = 3'd0, DIVIDE = 3'd1, SQRT = 3'd2,
             ROUND = 3'd3, SPECIAL = 3'd4, RESPONSE = 3'd5;
  wire run_n;
  reg [2:0] state;
  reg [4:0] iteration;
  reg sign_bit;
  reg signed [10:0] result_scale;
  reg [23:0] divisor;
  reg [24:0] div_remainder;
  reg [26:0] quotient;
  reg [53:0] radicand;
  reg [28:0] sqrt_remainder;
  reg [26:0] root;
  reg [27:0] round_significand;
  reg [31:0] response_data, special_data;
  wire [23:0] raw_a = {(|req_a[30:23]), req_a[22:0]};
  wire [23:0] raw_b = {(|req_b[30:23]), req_b[22:0]};
  wire [5:0] leading_a = leading_bit64({40'b0, raw_a});
  wire [5:0] leading_b = leading_bit64({40'b0, raw_b});
  wire [5:0] shift_a = 6'd23 - leading_a;
  wire [5:0] shift_b = 6'd23 - leading_b;
  wire [23:0] normalized_a = raw_a << shift_a;
  wire [23:0] normalized_b = raw_b << shift_b;
  wire signed [10:0] exponent_a =
    (req_a[30:23] == 0 ? -11'sd126 : $signed({3'b0, req_a[30:23]})-11'sd127) -
    $signed({5'b0, shift_a});
  wire signed [10:0] exponent_b =
    (req_b[30:23] == 0 ? -11'sd126 : $signed({3'b0, req_b[30:23]})-11'sd127) -
    $signed({5'b0, shift_b});
  wire signed [10:0] even_exponent =
    exponent_a[0] ? exponent_a - 11'sd1 : exponent_a;
  wire [24:0] sqrt_mantissa =
    exponent_a[0] ? {normalized_a, 1'b0} : {1'b0, normalized_a};
  wire a_zero = req_a[30:0] == 0;
  wire b_zero = req_b[30:0] == 0;
  wire a_inf = req_a[30:23] == 8'hff && req_a[22:0] == 0;
  wire b_inf = req_b[30:23] == 8'hff && req_b[22:0] == 0;
  wire div_special = fp32_nonfinite(req_a) || fp32_nonfinite(req_b) || a_zero || b_zero;
  wire sqrt_special = fp32_nonfinite(req_a) || a_zero || req_a[31];
  wire [25:0] div_difference = {1'b0, div_remainder} - {2'b0, divisor};
  wire div_bit = !div_difference[25];
  wire [24:0] div_residue = div_bit ? div_difference[24:0] : div_remainder;
  wire [26:0] next_quotient = {quotient[25:0], div_bit};
  wire [28:0] shifted_sqrt_remainder = {sqrt_remainder[26:0], radicand[53:52]};
  wire [28:0] sqrt_trial = {root, 2'b01};
  wire [29:0] sqrt_difference = {1'b0, shifted_sqrt_remainder} - {1'b0, sqrt_trial};
  wire sqrt_bit = !sqrt_difference[29];
  wire [28:0] next_sqrt_remainder =
    sqrt_bit ? sqrt_difference[28:0] : shifted_sqrt_remainder;
  wire [26:0] next_root = {root[25:0], sqrt_bit};
  wire [31:0] rounded = pack32(sign_bit, {36'b0, round_significand}, int'(result_scale));
  reg [31:0] exceptional;

  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    exceptional = FP32_QNAN;
    if (req_sqrt) begin
      if (fp32_nan(req_a) || (req_a[31] && !a_zero)) exceptional = FP32_QNAN;
      else exceptional = req_a;
    end else begin
      if (fp32_nan(req_a) || fp32_nan(req_b) || (a_zero && b_zero) || (a_inf && b_inf))
        exceptional = FP32_QNAN;
      else if (a_inf || b_zero) exceptional = {req_a[31] ^ req_b[31], 8'hff, 23'b0};
      else exceptional = {req_a[31] ^ req_b[31], 31'b0};
    end
  end
  assign req_ready = run_n && enable && state == IDLE;
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_data = rsp_valid ? response_data : 32'b0;

  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      iteration <= 0;
      sign_bit <= 0;
      result_scale <= 0;
      divisor <= 0;
      div_remainder <= 0;
      quotient <= 0;
      radicand <= 0;
      sqrt_remainder <= 0;
      root <= 0;
      round_significand <= 0;
      response_data <= 0;
      special_data <= 0;
    end else if (state == RESPONSE) begin
      if (rsp_valid && rsp_ready) state <= IDLE;
    end else if (enable) case (state)
      IDLE: if (req_valid && req_ready) begin
        iteration <= 0;
        special_data <= exceptional;
        quotient <= 0;
        root <= 0;
        sqrt_remainder <= 0;
        if (req_sqrt) begin
          sign_bit <= 0;
          result_scale <= (even_exponent >>> 1) - 11'sd26;
          radicand <= {sqrt_mantissa, 29'b0};
          if (sqrt_special) state <= SPECIAL;
          else state <= SQRT;
        end else begin
          sign_bit <= req_a[31] ^ req_b[31];
          result_scale <= exponent_a - exponent_b - 11'sd26;
          divisor <= normalized_b;
          div_remainder <= {1'b0, normalized_a};
          if (div_special) state <= SPECIAL;
          else state <= DIVIDE;
        end
      end
      DIVIDE: begin
        quotient <= next_quotient;
        div_remainder <= div_residue << 1;
        if (iteration == 26) begin
          round_significand <= {1'b0, next_quotient[26:1],
                                           next_quotient[0] || (|div_residue)};
          state <= ROUND;
        end else iteration <= iteration + 1'b1;
      end
      SQRT: begin
        root <= next_root;
        sqrt_remainder <= next_sqrt_remainder;
        radicand <= radicand << 2;
        if (iteration == 26) begin
          round_significand <= {1'b0, next_root[26:1],
                                           next_root[0] || (|next_sqrt_remainder)};
          state <= ROUND;
        end else iteration <= iteration + 1'b1;
      end
      ROUND: begin
        response_data <= rounded;
        state <= RESPONSE;
      end
      SPECIAL: begin
        response_data <= special_data;
        state <= RESPONSE;
      end
      default: begin
        response_data <= FP32_QNAN;
        state <= RESPONSE;
      end
    endcase
  end
endmodule
