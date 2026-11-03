module anvil_q4_parent_fp32 (
  input wire clk, rst_n, flush,
  input wire in_valid,
  output wire in_ready,
  input wire [3:0] op,
  input wire [31:0] a, b,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] result,
  output wire [4:0] flags
);
  import anvil_q4_parent_fp_pkg::*;

  reg busy, valid;
  reg [6:0] cycle;
  reg [3:0] operation;
  reg [31:0] operand_a, operand_b;
  reg [36:0] result_register, conversion_register, rounded_register;
  reg special;
  reg [36:0] special_result;
  reg [23:0] significand_a, significand_b;
  reg signed [11:0] exponent_a, exponent_b;
  reg [26:0] aligned_large, aligned_small;
  reg aligned_large_sign, aligned_small_sign;
  reg signed [11:0] aligned_exponent;
  reg [27:0] addition;
  reg addition_sign;
  reg [47:0] product;
  reg common_sign;
  reg signed [11:0] common_exponent;
  reg [26:0] common_significand;
  reg [25:0] division_remainder, division_divisor;
  reg [26:0] quotient;
  reg [53:0] square_radicand;
  reg [29:0] square_remainder;
  reg [26:0] square_root;

  wire [35:0] unpacked_a = unpack_normalized(operand_a);
  wire [35:0] unpacked_b = unpack_normalized(operand_b);
  wire effective_b_sign = operand_b[31] ^ (operation == 1);
  wire larger_a = exponent_a > exponent_b ||
    (exponent_a == exponent_b && significand_a >= significand_b);
  wire [11:0] exponent_distance = larger_a ?
    $unsigned(exponent_a - exponent_b) : $unsigned(exponent_b - exponent_a);
  wire [26:0] smaller_extended = larger_a ?
    {significand_b, 3'd0} : {significand_a, 3'd0};
  wire [26:0] smaller_aligned = shift_right_jam27(smaller_extended, exponent_distance);
  wire [5:0] addition_shift = leading_zeros32({4'd0, addition}) - 6'd5;
  wire [26:0] normalized_addition = addition[27] ?
    {addition[27:2], addition[1] | addition[0]} :
    (addition[26:0] << addition_shift);
  wire signed [11:0] normalized_addition_exponent = addition[27] ?
    aligned_exponent + 12'sd1 : aligned_exponent - $signed({6'd0, addition_shift});
  wire [36:0] rounded_common =
    round_pack32(common_sign, common_exponent, common_significand);

  wire division_bit = division_remainder >= division_divisor;
  wire [25:0] division_difference = division_bit ?
    division_remainder - division_divisor : division_remainder;
  wire [26:0] next_quotient = {quotient[25:0], division_bit};
  wire [29:0] square_extended_remainder = {square_remainder[27:0], square_radicand[53:52]};
  wire [29:0] square_trial = {1'b0, square_root, 2'b01};
  wire square_bit = square_extended_remainder >= square_trial;
  wire [29:0] next_square_remainder = square_bit ?
    square_extended_remainder - square_trial : square_extended_remainder;
  wire [26:0] next_square_root = {square_root[25:0], square_bit};

  reg special_wire;
  reg [36:0] special_result_wire;
  reg [36:0] conversion_wire;
  wire invalid_nan = is_signaling_nan(operand_a) ||
    (operation != 4 && is_signaling_nan(operand_b));
  wire product_sign = operand_a[31] ^ operand_b[31];

  always @* begin
    special_wire = 1'b0;
    special_result_wire = 37'd0;
    conversion_wire = {5'b10000, 32'h7fc00000};
    case (operation)
      0, 1: begin
        if (is_nan(operand_a) || is_nan(operand_b)) begin
          special_wire = 1'b1;
          special_result_wire = {invalid_nan, 4'd0, 32'h7fc00000};
        end else if (is_infinity(operand_a) && is_infinity(operand_b) &&
            operand_a[31] != effective_b_sign) begin
          special_wire = 1'b1;
          special_result_wire = {5'b10000, 32'h7fc00000};
        end else if (is_infinity(operand_a)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, operand_a};
        end else if (is_infinity(operand_b)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, effective_b_sign, operand_b[30:0]};
        end else if (is_zero(operand_a) && is_zero(operand_b)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, operand_a[31] & effective_b_sign, 31'd0};
        end else if (is_zero(operand_a)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, effective_b_sign, operand_b[30:0]};
        end else if (is_zero(operand_b)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, operand_a};
        end
      end
      2: begin
        if (is_nan(operand_a) || is_nan(operand_b)) begin
          special_wire = 1'b1;
          special_result_wire = {invalid_nan, 4'd0, 32'h7fc00000};
        end else if ((is_infinity(operand_a) && is_zero(operand_b)) ||
            (is_infinity(operand_b) && is_zero(operand_a))) begin
          special_wire = 1'b1;
          special_result_wire = {5'b10000, 32'h7fc00000};
        end else if (is_infinity(operand_a) || is_infinity(operand_b)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, product_sign, 8'hff, 23'd0};
        end else if (is_zero(operand_a) || is_zero(operand_b)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, product_sign, 31'd0};
        end
      end
      3: begin
        if (is_nan(operand_a) || is_nan(operand_b)) begin
          special_wire = 1'b1;
          special_result_wire = {invalid_nan, 4'd0, 32'h7fc00000};
        end else if ((is_zero(operand_a) && is_zero(operand_b)) ||
            (is_infinity(operand_a) && is_infinity(operand_b))) begin
          special_wire = 1'b1;
          special_result_wire = {5'b10000, 32'h7fc00000};
        end else if (is_infinity(operand_a)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, product_sign, 8'hff, 23'd0};
        end else if (is_infinity(operand_b)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, product_sign, 31'd0};
        end else if (is_zero(operand_b)) begin
          special_wire = 1'b1;
          special_result_wire = {5'b01000, product_sign, 8'hff, 23'd0};
        end else if (is_zero(operand_a)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, product_sign, 31'd0};
        end
      end
      4: begin
        if (is_nan(operand_a)) begin
          special_wire = 1'b1;
          special_result_wire = {is_signaling_nan(operand_a), 4'd0, 32'h7fc00000};
        end else if (operand_a[31] && !is_zero(operand_a)) begin
          special_wire = 1'b1;
          special_result_wire = {5'b10000, 32'h7fc00000};
        end else if (is_zero(operand_a) || is_infinity(operand_a)) begin
          special_wire = 1'b1;
          special_result_wire = {5'd0, operand_a};
        end
      end
      5: conversion_wire = widen_bf16(operand_a[15:0]);
      6: conversion_wire = widen_fp16(operand_a[15:0]);
      7: conversion_wire = narrow_bf16(operand_a);
      8: conversion_wire = narrow_fp16(operand_a);
      9: conversion_wire = int32_to_fp32(operand_a);
      default: conversion_wire = {5'b10000, 32'h7fc00000};
    endcase
  end

  assign in_ready = rst_n && !flush && !busy && !valid;
  assign out_valid = rst_n && !flush && valid;
  assign result = rst_n && !flush ? result_register[31:0] : 32'd0;
  assign flags = rst_n && !flush ? result_register[36:32] : 5'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy <= 1'b0;
      valid <= 1'b0;
      cycle <= 0;
      operation <= 0;
      operand_a <= 0;
      operand_b <= 0;
      result_register <= 0;
      conversion_register <= 0;
      rounded_register <= 0;
      special <= 1'b0;
      special_result <= 0;
      significand_a <= 0;
      significand_b <= 0;
      exponent_a <= 0;
      exponent_b <= 0;
      aligned_large <= 0;
      aligned_small <= 0;
      aligned_large_sign <= 0;
      aligned_small_sign <= 0;
      aligned_exponent <= 0;
      addition <= 0;
      addition_sign <= 0;
      product <= 0;
      common_sign <= 0;
      common_exponent <= 0;
      common_significand <= 0;
      division_remainder <= 0;
      division_divisor <= 0;
      quotient <= 0;
      square_radicand <= 0;
      square_remainder <= 0;
      square_root <= 0;
    end else if (flush) begin
      busy <= 1'b0;
      valid <= 1'b0;
      cycle <= 0;
      result_register <= 0;
    end else begin
      if (valid && out_ready) valid <= 1'b0;
      if (in_valid && in_ready) begin
        operand_a <= a;
        operand_b <= b;
        operation <= op;
        busy <= 1'b1;
        cycle <= 0;
      end else if (busy) begin
        cycle <= cycle + 1'b1;
        if (cycle == 0) begin
          significand_a <= unpacked_a[23:0];
          significand_b <= unpacked_b[23:0];
          exponent_a <= $signed(unpacked_a[35:24]);
          exponent_b <= $signed(unpacked_b[35:24]);
          special <= special_wire;
          special_result <= special_result_wire;
          conversion_register <= conversion_wire;
        end

        if (operation <= 1) begin
          case (cycle)
            1: begin
              aligned_large <= larger_a ? {significand_a, 3'd0} : {significand_b, 3'd0};
              aligned_small <= smaller_aligned;
              aligned_large_sign <= larger_a ? operand_a[31] : effective_b_sign;
              aligned_small_sign <= larger_a ? effective_b_sign : operand_a[31];
              aligned_exponent <= larger_a ? exponent_a : exponent_b;
            end
            2: begin
              if (aligned_large_sign == aligned_small_sign)
                addition <= {1'b0, aligned_large} + {1'b0, aligned_small};
              else addition <= {1'b0, aligned_large} - {1'b0, aligned_small};
              addition_sign <= aligned_large_sign;
            end
            3: begin
              common_sign <= addition == 0 ? 1'b0 : addition_sign;
              common_exponent <= normalized_addition_exponent;
              common_significand <= normalized_addition;
            end
            4: rounded_register <= rounded_common;
            7: begin
              result_register <= special ? special_result : rounded_register;
              valid <= 1'b1;
              busy <= 1'b0;
            end
            default: begin end
          endcase
        end else if (operation == 2) begin
          case (cycle)
            1: product <= significand_a * significand_b;
            2: begin
              common_sign <= product_sign;
              if (product[47]) begin
                common_exponent <= exponent_a + exponent_b + 12'sd1;
                common_significand <= {product[47:22], product[21] | (|product[20:0])};
              end else begin
                common_exponent <= exponent_a + exponent_b;
                common_significand <= {product[46:21], product[20] | (|product[19:0])};
              end
            end
            4: rounded_register <= rounded_common;
            7: begin
              result_register <= special ? special_result : rounded_register;
              valid <= 1'b1;
              busy <= 1'b0;
            end
            default: begin end
          endcase
        end else if (operation == 3) begin
          if (cycle == 1) begin
            division_divisor <= {2'd0, significand_b};
            quotient <= 0;
            common_sign <= product_sign;
            if (significand_a < significand_b) begin
              division_remainder <= {1'b0, significand_a, 1'b0};
              common_exponent <= exponent_a - exponent_b - 12'sd1;
            end else begin
              division_remainder <= {2'd0, significand_a};
              common_exponent <= exponent_a - exponent_b;
            end
          end else if (cycle >= 2 && cycle <= 28) begin
            division_remainder <= {division_difference[24:0], 1'b0};
            quotient <= next_quotient;
            if (cycle == 28)
              common_significand <= {next_quotient[26:1],
                next_quotient[0] | (|division_difference)};
          end else if (cycle == 29) rounded_register <= rounded_common;
          else if (cycle == 63) begin
            result_register <= special ? special_result : rounded_register;
            valid <= 1'b1;
            busy <= 1'b0;
          end
        end else if (operation == 4) begin
          if (cycle == 1) begin
            common_sign <= 1'b0;
            common_exponent <= exponent_a >>> 1;
            square_root <= 0;
            square_remainder <= 0;
            if (exponent_a[0]) square_radicand <= {significand_a, 30'd0};
            else square_radicand <= {1'b0, significand_a, 29'd0};
          end else if (cycle >= 2 && cycle <= 28) begin
            square_radicand <= {square_radicand[51:0], 2'd0};
            square_remainder <= next_square_remainder;
            square_root <= next_square_root;
            if (cycle == 28)
              common_significand <= {next_square_root[26:1],
                next_square_root[0] | (|next_square_remainder)};
          end else if (cycle == 29) rounded_register <= rounded_common;
          else if (cycle == 63) begin
            result_register <= special ? special_result : rounded_register;
            valid <= 1'b1;
            busy <= 1'b0;
          end
        end else if (cycle == 1) begin
          result_register <= conversion_register;
          valid <= 1'b1;
          busy <= 1'b0;
        end
      end
    end
  end
endmodule
