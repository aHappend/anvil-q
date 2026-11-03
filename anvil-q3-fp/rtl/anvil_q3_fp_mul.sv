module anvil_q3_fp_mul (
  input wire clk, rst_n, flush, in_valid,
  input wire [31:0] in_a, in_b,
  input wire out_ready,
  output wire in_ready, out_valid,
  output wire [31:0] out_data,
  output wire [4:0] out_flags
);
  import anvil_q3_fp_pkg::*;

  reg valid0, valid1, valid2;
  wire ready2 = !valid2 || out_ready;
  wire ready1 = !valid1 || ready2;
  wire ready0 = !valid0 || ready1;
  wire [23:0] raw_a = {in_a[30:23] != 0,in_a[22:0]};
  wire [23:0] raw_b = {in_b[30:23] != 0,in_b[22:0]};
  wire [4:0] leading_a = clz24(raw_a);
  wire [4:0] leading_b = clz24(raw_b);
  wire signed [12:0] exponent_a =
    $signed({5'd0,(in_a[30:23] == 0 ? 8'd1 : in_a[30:23])}) -
    13'sd127 - $signed({8'd0,leading_a});
  wire signed [12:0] exponent_b =
    $signed({5'd0,(in_b[30:23] == 0 ? 8'd1 : in_b[30:23])}) -
    13'sd127 - $signed({8'd0,leading_b});
  wire invalid_product = (is_inf32(in_a) && is_zero32(in_b)) ||
    (is_inf32(in_b) && is_zero32(in_a));
  wire nan_product = is_nan32(in_a) || is_nan32(in_b) || invalid_product;
  wire special = nan_product || is_inf32(in_a) || is_inf32(in_b) ||
    is_zero32(in_a) || is_zero32(in_b);
  wire [31:0] special_value = nan_product ? CANONICAL_NAN :
    {in_a[31]^in_b[31],
     (is_inf32(in_a) || is_inf32(in_b)) ? 8'hff : 8'd0,23'd0};
  wire [4:0] special_flags =
    {is_snan32(in_a) || is_snan32(in_b) || invalid_product,4'd0};

  reg sign0, special0;
  reg [23:0] sig_a0, sig_b0;
  reg signed [12:0] exponent_a0, exponent_b0;
  reg [31:0] special_value0;
  reg [4:0] special_flags0;
  reg sign1, special1;
  reg [47:0] product1;
  reg signed [12:0] exponent1;
  reg [31:0] special_value1;
  reg [4:0] special_flags1;
  reg [31:0] data2;
  reg [4:0] flags2;

  wire [26:0] normalized_product = product1[47] ?
    {product1[47:22],(|product1[21:0])} :
    {product1[46:21],(|product1[20:0])};
  wire signed [12:0] normalized_exponent =
    exponent1 + (product1[47] ? 13'sd1 : 13'sd0);
  wire [36:0] rounded_product = round32(sign1,normalized_exponent,normalized_product);

  assign in_ready = rst_n && !flush && ready0;
  assign out_valid = rst_n && !flush && valid2;
  assign out_data = out_valid ? data2 : 32'd0;
  assign out_flags = out_valid ? flags2 : 5'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid0 <= 0;
      valid1 <= 0;
      valid2 <= 0;
      sign0 <= 0;
      special0 <= 0;
      sig_a0 <= 0;
      sig_b0 <= 0;
      exponent_a0 <= 0;
      exponent_b0 <= 0;
      special_value0 <= 0;
      special_flags0 <= 0;
      sign1 <= 0;
      special1 <= 0;
      product1 <= 0;
      exponent1 <= 0;
      special_value1 <= 0;
      special_flags1 <= 0;
      data2 <= 0;
      flags2 <= 0;
    end else if (flush) begin
      valid0 <= 0;
      valid1 <= 0;
      valid2 <= 0;
    end else begin
      if (ready0) begin
        valid0 <= in_valid;
        if (in_valid) begin
          sign0 <= in_a[31]^in_b[31];
          special0 <= special;
          sig_a0 <= raw_a << leading_a;
          sig_b0 <= raw_b << leading_b;
          exponent_a0 <= exponent_a;
          exponent_b0 <= exponent_b;
          special_value0 <= special_value;
          special_flags0 <= special_flags;
        end
      end
      if (ready1) begin
        valid1 <= valid0;
        if (valid0) begin
          sign1 <= sign0;
          special1 <= special0;
          product1 <= sig_a0*sig_b0;
          exponent1 <= exponent_a0+exponent_b0;
          special_value1 <= special_value0;
          special_flags1 <= special_flags0;
        end
      end
      if (ready2) begin
        valid2 <= valid1;
        if (valid1) begin
          data2 <= special1 ? special_value1 : rounded_product[31:0];
          flags2 <= special1 ? special_flags1 : rounded_product[36:32];
        end
      end
    end
  end
endmodule
