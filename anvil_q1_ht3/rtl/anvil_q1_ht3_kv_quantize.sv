module anvil_q1_ht3_kv_quantize (
  input wire clk, rst_n,
  input wire in_valid,
  output wire in_ready,
  input wire [31:0] in_data, in_scale,
  input wire in_int8,
  output wire out_valid,
  input wire out_ready,
  output wire [15:0] out_code,
  output wire out_error
);
  import anvil_q1_ht3_fp_pkg::*;
  localparam IDLE = 3'd0, NORMALIZE = 3'd1, ALIGN = 3'd2,
    PRODUCT = 3'd3, COMPARE = 3'd4, ENCODE = 3'd5, RESPONSE = 3'd6;
  wire run_n;
  reg [2:0] state, iteration;
  reg sign_q, int8_q, error_q;
  reg [23:0] raw_x, raw_scale, normalized_x, normalized_scale;
  reg signed [10:0] scale_x, scale_s, exponent_difference;
  reg [32:0] numerator, threshold_product;
  reg [7:0] lower, upper, midpoint_q;
  reg [15:0] response_code;
  reg response_error;
  wire [5:0] leading_x = leading_bit64({40'b0, raw_x});
  wire [5:0] leading_s = leading_bit64({40'b0, raw_scale});
  wire signed [10:0] exponent_x =
    scale_x + $signed({5'b0, leading_x});
  wire signed [10:0] exponent_s =
    scale_s + $signed({5'b0, leading_s});
  wire [7:0] limit = int8_q ? (sign_q ? 8'd128 : 8'd127) :
                                            (sign_q ? 8'd8 : 8'd7);
  wire [8:0] bound_sum = {1'b0, lower} + {1'b0, upper};
  wire [7:0] midpoint = bound_sum[8:1];
  wire [8:0] odd_threshold = {midpoint, 1'b1};
  wire [32:0] product = normalized_scale * odd_threshold;
  wire choose_upper = numerator > threshold_product ||
    (numerator == threshold_product && midpoint_q[0]);
  wire [7:0] signed_code = sign_q ? (8'd0 - lower) : lower;
  wire input_bad = fp32_nonfinite(in_data) || fp32_nonfinite(in_scale) ||
                   in_scale[31] || in_scale[30:0] == 0;

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  assign in_ready = run_n && state == IDLE;
  assign out_valid = run_n && state == RESPONSE;
  assign out_code = out_valid ? response_code : 16'b0;
  assign out_error = out_valid && response_error;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      iteration <= 0;
      sign_q <= 0;
      int8_q <= 0;
      error_q <= 0;
      raw_x <= 0;
      raw_scale <= 0;
      normalized_x <= 0;
      normalized_scale <= 0;
      scale_x <= 0;
      scale_s <= 0;
      exponent_difference <= 0;
      numerator <= 0;
      threshold_product <= 0;
      lower <= 0;
      upper <= 0;
      midpoint_q <= 0;
      response_code <= 0;
      response_error <= 0;
    end else if (run_n) case (state)
      IDLE: if (in_valid && in_ready) begin
        sign_q <= in_data[31];
        int8_q <= in_int8;
        error_q <= input_bad;
        raw_x <= {(|in_data[30:23]), in_data[22:0]};
        raw_scale <= {(|in_scale[30:23]), in_scale[22:0]};
        if (in_data[30:23] == 0) scale_x <= -11'sd149;
        else scale_x <= $signed({3'b0, in_data[30:23]}) - 11'sd150;
        if (in_scale[30:23] == 0) scale_s <= -11'sd149;
        else scale_s <= $signed({3'b0, in_scale[30:23]}) - 11'sd150;
        iteration <= 0;
        state <= NORMALIZE;
      end
      NORMALIZE: begin
        normalized_x <= raw_x << (6'd23 - leading_x);
        normalized_scale <= raw_scale << (6'd23 - leading_s);
        exponent_difference <= exponent_x - exponent_s;
        state <= ALIGN;
      end
      ALIGN: begin
        numerator <= 0;
        lower <= 0;
        upper <= limit;
        if (error_q || raw_x == 0 || exponent_difference <= -11'sd2) begin
          lower <= 0;
          upper <= 0;
        end else if (exponent_difference >= 11'sd8) begin
          lower <= limit;
          upper <= limit;
        end else begin
          numerator <= {9'b0, normalized_x} <<
                       (exponent_difference + 11'sd1);
        end
        state <= PRODUCT;
      end
      PRODUCT: begin
        midpoint_q <= midpoint;
        threshold_product <= product;
        state <= COMPARE;
      end
      COMPARE: begin
        // Tie at mid+1/2 selects the upper integer only when mid is odd.
        if (lower < upper) begin
          if (choose_upper) lower <= midpoint_q + 1'b1;
          else upper <= midpoint_q;
        end
        if (iteration == 3'd7) state <= ENCODE;
        else begin
          iteration <= iteration + 1'b1;
          state <= PRODUCT;
        end
      end
      ENCODE: begin
        if (error_q) response_code <= 0;
        else if (int8_q) response_code <= {8'b0, signed_code};
        else response_code <= {12'b0, signed_code[3:0]};
        response_error <= error_q;
        state <= RESPONSE;
      end
      RESPONSE: if (out_valid && out_ready) state <= IDLE;
      default: begin
        response_code <= 0;
        response_error <= 1;
        state <= RESPONSE;
      end
    endcase
  end
endmodule
