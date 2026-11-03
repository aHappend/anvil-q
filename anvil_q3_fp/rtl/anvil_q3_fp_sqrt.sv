module anvil_q3_fp_sqrt (
  input wire clk, rst_n, flush, start,
  input wire [31:0] radicand,
  output wire ready, done, error,
  output wire [31:0] value,
  output wire [4:0] flags
);
  import anvil_q3_fp_pkg::*;

  localparam [2:0] IDLE=0, ITERATE=1, ROUND=2, SPECIAL=3, COMPLETE=4;
  reg [2:0] state;
  reg error_reg;
  reg [53:0] radicand_bits;
  reg [29:0] remainder_reg;
  reg [26:0] root_bits;
  reg [4:0] remaining;
  reg signed [12:0] exponent_reg;
  reg [31:0] value_reg, special_value_reg;
  reg [4:0] flags_reg, special_flags_reg;

  wire [23:0] raw_sig = {radicand[30:23] != 0,radicand[22:0]};
  wire [4:0] leading = clz24(raw_sig);
  wire [23:0] sig = raw_sig << leading;
  wire signed [12:0] exponent =
    $signed({5'd0,(radicand[30:23] == 0 ? 8'd1 : radicand[30:23])}) -
    13'sd127 - $signed({8'd0,leading});
  wire [24:0] even_sig = exponent[0] ? {sig,1'b0} : {1'b0,sig};
  wire invalid_root = radicand[31] && !is_zero32(radicand) && !is_nan32(radicand);
  wire nan_root = is_nan32(radicand) || invalid_root;
  wire special = nan_root || is_inf32(radicand) || is_zero32(radicand);
  wire [31:0] special_value = nan_root ? CANONICAL_NAN : radicand;
  wire [4:0] special_flags = {is_snan32(radicand) || invalid_root,4'd0};
  wire [29:0] partial_remainder = {remainder_reg[27:0],radicand_bits[53:52]};
  wire [29:0] trial = {1'b0,root_bits,2'b01};
  wire subtract = partial_remainder >= trial;
  wire [29:0] difference = partial_remainder-trial;
  wire [26:0] rounding_sig = {root_bits[26:1],root_bits[0] || (|remainder_reg)};
  wire [36:0] rounded = round32(1'b0,exponent_reg,rounding_sig);

  assign ready = rst_n && !flush && state == IDLE;
  assign done = rst_n && !flush && state == COMPLETE;
  assign error = done && error_reg;
  assign value = rst_n && !flush ? value_reg : 32'd0;
  assign flags = rst_n && !flush ? flags_reg : 5'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      error_reg <= 0;
      radicand_bits <= 0;
      remainder_reg <= 0;
      root_bits <= 0;
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
        if (special) begin
          special_value_reg <= special_value;
          special_flags_reg <= special_flags;
          state <= SPECIAL;
        end else begin
          radicand_bits <= {even_sig,29'd0};
          remainder_reg <= 0;
          root_bits <= 0;
          remaining <= 5'd27;
          exponent_reg <= exponent >>> 1;
          state <= ITERATE;
        end
      end
      ITERATE: begin
        radicand_bits <= radicand_bits << 2;
        remainder_reg <= subtract ? difference : partial_remainder;
        root_bits <= {root_bits[25:0],subtract};
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
