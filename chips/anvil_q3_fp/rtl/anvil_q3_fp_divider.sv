module anvil_q3_fp_divider (
  input wire clk, rst_n, flush, start,
  input wire [31:0] numerator, denominator,
  output wire ready, done, error,
  output wire [31:0] quotient,
  output wire [4:0] flags
);
  import anvil_q3_fp_pkg::*;

  localparam [2:0] IDLE=0, ITERATE=1, ROUND=2, SPECIAL=3, COMPLETE=4;
  reg [2:0] state;
  reg sign_reg, error_reg;
  reg [24:0] remainder_reg;
  reg [23:0] divisor;
  reg [26:0] quotient_bits;
  reg [4:0] remaining;
  reg signed [12:0] exponent_reg;
  reg [31:0] value_reg, special_value_reg;
  reg [4:0] flags_reg, special_flags_reg;

  wire [23:0] raw_a = {numerator[30:23] != 0,numerator[22:0]};
  wire [23:0] raw_b = {denominator[30:23] != 0,denominator[22:0]};
  wire [4:0] leading_a = clz24(raw_a);
  wire [4:0] leading_b = clz24(raw_b);
  wire [23:0] sig_a = raw_a << leading_a;
  wire [23:0] sig_b = raw_b << leading_b;
  wire signed [12:0] exponent_a =
    $signed({5'd0,(numerator[30:23] == 0 ? 8'd1 : numerator[30:23])}) -
    13'sd127 - $signed({8'd0,leading_a});
  wire signed [12:0] exponent_b =
    $signed({5'd0,(denominator[30:23] == 0 ? 8'd1 : denominator[30:23])}) -
    13'sd127 - $signed({8'd0,leading_b});
  wire invalid_ratio =
    (is_zero32(numerator) && is_zero32(denominator)) ||
    (is_inf32(numerator) && is_inf32(denominator));
  wire nan_ratio = is_nan32(numerator) || is_nan32(denominator) || invalid_ratio;
  wire special = nan_ratio || is_inf32(numerator) || is_inf32(denominator) ||
    is_zero32(numerator) || is_zero32(denominator);
  wire negative = numerator[31]^denominator[31];
  wire divide_zero = !is_nan32(numerator) && !is_inf32(numerator) &&
    !is_zero32(numerator) && is_zero32(denominator);
  wire [31:0] special_value = nan_ratio ? CANONICAL_NAN :
    {negative,(is_inf32(numerator) || is_zero32(denominator)) ? 8'hff : 8'd0,23'd0};
  wire [4:0] special_flags =
    {is_snan32(numerator) || is_snan32(denominator) || invalid_ratio,divide_zero,3'd0};
  wire subtract = remainder_reg >= {1'b0,divisor};
  wire [24:0] difference = remainder_reg - {1'b0,divisor};
  wire [24:0] next_remainder = (subtract ? difference : remainder_reg) << 1;
  wire [26:0] rounding_sig =
    {quotient_bits[26:1],quotient_bits[0] || (|remainder_reg)};
  wire [36:0] rounded = round32(sign_reg,exponent_reg,rounding_sig);

  assign ready = rst_n && !flush && state == IDLE;
  assign done = rst_n && !flush && state == COMPLETE;
  assign error = done && error_reg;
  assign quotient = rst_n && !flush ? value_reg : 32'd0;
  assign flags = rst_n && !flush ? flags_reg : 5'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      sign_reg <= 0;
      error_reg <= 0;
      remainder_reg <= 0;
      divisor <= 0;
      quotient_bits <= 0;
      remaining <= 0;
      exponent_reg <= 0;
      value_reg <= 0;
      special_value_reg <= 0;
      flags_reg <= 0;
      special_flags_reg <= 0;
    end else if (flush) begin
      state <= IDLE;
      error_reg <= 0;
      value_reg <= 0;
      flags_reg <= 0;
    end else case (state)
      IDLE: if (start && ready) begin
        error_reg <= 0;
        sign_reg <= negative;
        if (special) begin
          special_value_reg <= special_value;
          special_flags_reg <= special_flags;
          state <= SPECIAL;
        end else begin
          remainder_reg <= sig_a < sig_b ? {sig_a,1'b0} : {1'b0,sig_a};
          divisor <= sig_b;
          quotient_bits <= 0;
          remaining <= 5'd27;
          exponent_reg <= exponent_a-exponent_b-(sig_a < sig_b ? 13'sd1 : 13'sd0);
          state <= ITERATE;
        end
      end
      ITERATE: begin
        remainder_reg <= next_remainder;
        quotient_bits <= {quotient_bits[25:0],subtract};
        remaining <= remaining-5'd1;
        if (remaining == 1) state <= ROUND;
      end
      ROUND: begin
        value_reg <= rounded[31:0];
        flags_reg <= rounded[36:32];
        state <= COMPLETE;
      end
      SPECIAL: begin
        value_reg <= special_value_reg;
        flags_reg <= special_flags_reg;
        state <= COMPLETE;
      end
      COMPLETE: state <= IDLE;
      default: begin
        value_reg <= 0;
        flags_reg <= 0;
        error_reg <= 1;
        state <= COMPLETE;
      end
    endcase
  end
endmodule
