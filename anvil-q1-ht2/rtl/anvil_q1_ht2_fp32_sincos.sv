module anvil_q1_ht2_fp32_sincos (
  input wire clk, rst_n, enable, req_valid,
  output wire req_ready,
  input wire [31:0] req_data,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_sin, rsp_cos,
  output wire rsp_error
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam [351:0] HALF_PI_LO =
    352'h00000001921fb54442d18469898cc51701b839a252049c1114cf98e804177d4c76273644a29410f31c6809bb;
  localparam IDLE = 5'd0, CLEAR = 5'd1, BUILD = 5'd2,
    DIV_SUB = 5'd3, DIV_COPY = 5'd4, HALF_SUB = 5'd5,
    SELECT_Q = 5'd6, BOUND_SUB = 5'd7, BOUND_ADD = 5'd8,
    SCAN_INIT = 5'd9, SCAN = 5'd10, ROUND_CHECK = 5'd11,
    MUL_SEND = 5'd12, MUL_WAIT = 5'd13, ADD_SEND = 5'd14,
    ADD_WAIT = 5'd15, MAP = 5'd16, RESPONSE = 5'd17;
  wire run_n;
  reg [4:0] state;
  reg [3:0] word_index, quotient_bit, degree;
  reg [4:0] input_bit;
  reg [8:0] input_scale, scan_index, lower_lead, upper_lead;
  reg [23:0] input_significand;
  reg [351:0] remainder_bits, trial_bits, lower_bits, upper_bits;
  reg [15:0] quotient;
  reg borrow, carry, difference_high, round_up, input_negative, failed;
  reg [31:0] difference_low;
  reg lower_found, upper_found, lower_sticky, upper_sticky;
  reg [4:0] lower_count, upper_count;
  reg [26:0] lower_significand, upper_significand;
  reg [1:0] phase;
  reg [31:0] reduced, square, polynomial, temporary, sine, cosine;
  reg [31:0] sin_result, cos_result;
  reg [31:0] subtract_a, subtract_b, shifted_pi, multiply_a, multiply_b;
  reg [31:0] mapped_sin, mapped_cos;
  wire [8:0] deposit_index = input_scale + {4'b0, input_bit};
  wire [32:0] subtraction =
    {1'b0, subtract_a} - {1'b0, subtract_b} - {32'b0, borrow};
  wire [32:0] bound_sum =
    {1'b0, lower_bits[32*word_index+:32]} + {32'b0, carry} +
    (word_index == 0 ? {17'b0, quotient} : 33'b0);
  wire [26:0] lower_aligned =
    lower_count < 27 ? lower_significand << (27-lower_count) : lower_significand;
  wire [26:0] upper_aligned =
    upper_count < 27 ? upper_significand << (27-upper_count) : upper_significand;
  wire [31:0] lower_rounded = pack32(round_up,
    {37'b0, lower_aligned | {26'b0, lower_sticky}}, int'({1'b0, lower_lead})-346);
  wire [31:0] upper_rounded = pack32(round_up,
    {37'b0, upper_aligned | {26'b0, upper_sticky}}, int'({1'b0, upper_lead})-346);
  wire multiply_valid, add_valid;
  wire [31:0] multiply_data, add_data;

  function automatic [31:0] pi_word(input [3:0] index);
    begin
      if (index <= 10) pi_word = HALF_PI_LO[32*index+:32];
      else pi_word = 0;
    end
  endfunction

  function automatic [31:0] coefficient(input cosine_polynomial, input [3:0] index);
    begin
      if (cosine_polynomial) case (index)
        0: coefficient = 32'h3f800000;
        1: coefficient = 32'hbf000000;
        2: coefficient = 32'h3d2aaaab;
        3: coefficient = 32'hbab60b61;
        4: coefficient = 32'h37d00d01;
        5: coefficient = 32'hb493f27e;
        6: coefficient = 32'h310f76c7;
        7: coefficient = 32'had49cba5;
        8: coefficient = 32'h29573f9f;
        default: coefficient = FP32_QNAN;
      endcase
      else case (index)
        0: coefficient = 32'h3f800000;
        1: coefficient = 32'hbe2aaaab;
        2: coefficient = 32'h3c088889;
        3: coefficient = 32'hb9500d01;
        4: coefficient = 32'h3638ef1d;
        5: coefficient = 32'hb2d7322b;
        6: coefficient = 32'h2f309231;
        7: coefficient = 32'hab573f9f;
        8: coefficient = 32'h274a963c;
        default: coefficient = FP32_QNAN;
      endcase
    end
  endfunction

  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    shifted_pi = pi_word(word_index) << quotient_bit;
    if (word_index != 0 && quotient_bit != 0)
      shifted_pi = shifted_pi |
        (pi_word(word_index-1'b1) >> (32-quotient_bit));
    subtract_a = 0;
    subtract_b = 0;
    case (state)
      DIV_SUB: begin
        subtract_a = remainder_bits[32*word_index+:32];
        subtract_b = shifted_pi;
      end
      HALF_SUB: begin
        subtract_a = remainder_bits[32*word_index+:32] << 1;
        if (word_index != 0)
          subtract_a[0] = remainder_bits[32*word_index-1];
        subtract_b = pi_word(word_index);
      end
      BOUND_SUB: begin
        if (round_up) begin
          subtract_a = pi_word(word_index);
          subtract_b = remainder_bits[32*word_index+:32];
        end else begin
          subtract_a = remainder_bits[32*word_index+:32];
          subtract_b = word_index == 0 ? {16'b0, quotient} : 32'b0;
        end
      end
      default: begin end
    endcase
  end
  always @* begin
    multiply_a = polynomial;
    multiply_b = square;
    if (phase == 0) begin multiply_a = reduced; multiply_b = reduced; end
    if (phase == 2) begin multiply_a = reduced; multiply_b = polynomial; end
    case (quotient[1:0])
      0: begin mapped_sin = sine; mapped_cos = cosine; end
      1: begin mapped_sin = cosine; mapped_cos = {~sine[31], sine[30:0]}; end
      2: begin
        mapped_sin = {~sine[31], sine[30:0]};
        mapped_cos = {~cosine[31], cosine[30:0]};
      end
      3: begin mapped_sin = {~cosine[31], cosine[30:0]}; mapped_cos = sine; end
    endcase
  end
  anvil_q1_ht2_fp32_mul u_multiply (
    .clk(clk), .rst_n(run_n), .enable(enable),
    .in_valid(run_n && state == MUL_SEND), .in_a(multiply_a), .in_b(multiply_b),
    .out_valid(multiply_valid), .out_data(multiply_data)
  );
  anvil_q1_ht2_fp32_add u_add (
    .clk(clk), .rst_n(run_n), .enable(enable),
    .in_valid(run_n && state == ADD_SEND), .in_a(temporary),
    .in_b(coefficient(phase == 3, degree)), .out_valid(add_valid), .out_data(add_data)
  );
  assign req_ready = run_n && enable && state == IDLE;
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_sin = rsp_valid ? sin_result : 32'b0;
  assign rsp_cos = rsp_valid ? cos_result : 32'b0;
  assign rsp_error = rsp_valid && failed;

  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      word_index <= 0;
      quotient_bit <= 0;
      degree <= 0;
      input_bit <= 0;
      input_scale <= 0;
      scan_index <= 0;
      lower_lead <= 0;
      upper_lead <= 0;
      input_significand <= 0;
      remainder_bits <= 0;
      trial_bits <= 0;
      lower_bits <= 0;
      upper_bits <= 0;
      quotient <= 0;
      borrow <= 0;
      carry <= 0;
      difference_high <= 0;
      round_up <= 0;
      input_negative <= 0;
      failed <= 0;
      difference_low <= 0;
      lower_found <= 0;
      upper_found <= 0;
      lower_sticky <= 0;
      upper_sticky <= 0;
      lower_count <= 0;
      upper_count <= 0;
      lower_significand <= 0;
      upper_significand <= 0;
      phase <= 0;
      reduced <= 0;
      square <= 0;
      polynomial <= 0;
      temporary <= 0;
      sine <= 0;
      cosine <= 0;
      sin_result <= 0;
      cos_result <= 0;
    end else if (state == RESPONSE) begin
      if (rsp_valid && rsp_ready) state <= IDLE;
    end else if (enable) case (state)
      IDLE: if (req_valid && req_ready) begin
        failed <= 0;
        input_negative <= req_data[31];
        quotient <= 0;
        word_index <= 0;
        input_bit <= 0;
        round_up <= 0;
        input_significand <= {(|req_data[30:23]), req_data[22:0]};
        input_scale <= req_data[30:23] == 0 ? 9'd171 :
                                              {1'b0, req_data[30:23]} + 9'd170;
        if (fp32_nonfinite(req_data) || req_data[30:0] > 31'h47000000) begin
          failed <= 1;
          sin_result <= FP32_QNAN;
          cos_result <= FP32_QNAN;
          state <= RESPONSE;
        end else if (req_data[30:0] == 0) begin
          sin_result <= req_data;
          cos_result <= 32'h3f800000;
          state <= RESPONSE;
        end else state <= CLEAR;
      end
      CLEAR: begin
        remainder_bits[32*word_index+:32] <= 0;
        if (word_index == 10) begin word_index <= 0; state <= BUILD; end
        else word_index <= word_index + 1'b1;
      end
      BUILD: begin
        if (input_significand[input_bit])
          remainder_bits[32*deposit_index[8:5]+:32] <=
            remainder_bits[32*deposit_index[8:5]+:32] | (32'b1 << deposit_index[4:0]);
        if (input_bit == 23) begin
          word_index <= 0;
          quotient_bit <= 15;
          borrow <= 0;
          state <= DIV_SUB;
        end else input_bit <= input_bit + 1'b1;
      end
      DIV_SUB: begin
        trial_bits[32*word_index+:32] <= subtraction[31:0];
        borrow <= subtraction[32];
        if (word_index == 10) begin word_index <= 0; state <= DIV_COPY; end
        else word_index <= word_index + 1'b1;
      end
      DIV_COPY: begin
        if (!borrow) remainder_bits[32*word_index+:32] <= trial_bits[32*word_index+:32];
        if (word_index == 10) begin
          if (!borrow) quotient[quotient_bit] <= 1;
          word_index <= 0;
          borrow <= 0;
          if (quotient_bit == 0) begin
            difference_high <= 0;
            difference_low <= 0;
            state <= HALF_SUB;
          end else begin
            quotient_bit <= quotient_bit - 1'b1;
            state <= DIV_SUB;
          end
        end else word_index <= word_index + 1'b1;
      end
      HALF_SUB: begin
        borrow <= subtraction[32];
        if (word_index == 0) difference_low <= subtraction[31:0];
        else difference_high <= difference_high || (|subtraction[31:0]);
        if (word_index == 10) begin word_index <= 0; state <= SELECT_Q; end
        else word_index <= word_index + 1'b1;
      end
      SELECT_Q: begin
        borrow <= 0;
        carry <= 0;
        if (borrow || (!difference_high && difference_low == 0)) begin
          round_up <= 0;
          state <= BOUND_SUB;
        end else if (difference_high || difference_low > ({16'b0, quotient} << 1)+1) begin
          quotient <= quotient + 1'b1;
          round_up <= 1;
          state <= BOUND_SUB;
        end else begin
          failed <= 1;
          sin_result <= FP32_QNAN;
          cos_result <= FP32_QNAN;
          state <= RESPONSE;
        end
      end
      BOUND_SUB: begin
        lower_bits[32*word_index+:32] <= subtraction[31:0];
        upper_bits[32*word_index+:32] <= remainder_bits[32*word_index+:32];
        borrow <= subtraction[32];
        if (word_index == 10) begin
          word_index <= 0;
          if (subtraction[32]) begin
            failed <= 1;
            sin_result <= FP32_QNAN;
            cos_result <= FP32_QNAN;
            state <= RESPONSE;
          end else if (round_up) state <= BOUND_ADD;
          else state <= SCAN_INIT;
        end else word_index <= word_index + 1'b1;
      end
      BOUND_ADD: begin
        upper_bits[32*word_index+:32] <= bound_sum[31:0];
        carry <= bound_sum[32];
        if (word_index == 10) begin word_index <= 0; state <= SCAN_INIT; end
        else word_index <= word_index + 1'b1;
      end
      SCAN_INIT: begin
        scan_index <= 351;
        lower_found <= 0;
        upper_found <= 0;
        lower_sticky <= 0;
        upper_sticky <= 0;
        lower_count <= 0;
        upper_count <= 0;
        lower_significand <= 0;
        upper_significand <= 0;
        lower_lead <= 0;
        upper_lead <= 0;
        state <= SCAN;
      end
      SCAN: begin
        if (!lower_found) begin
          if (lower_bits[scan_index]) begin
            lower_found <= 1;
            lower_lead <= scan_index;
            lower_significand <= 1;
            lower_count <= 1;
          end
        end else if (lower_count < 27) begin
          lower_significand <= {lower_significand[25:0], lower_bits[scan_index]};
          lower_count <= lower_count + 1'b1;
        end else lower_sticky <= lower_sticky || lower_bits[scan_index];
        if (!upper_found) begin
          if (upper_bits[scan_index]) begin
            upper_found <= 1;
            upper_lead <= scan_index;
            upper_significand <= 1;
            upper_count <= 1;
          end
        end else if (upper_count < 27) begin
          upper_significand <= {upper_significand[25:0], upper_bits[scan_index]};
          upper_count <= upper_count + 1'b1;
        end else upper_sticky <= upper_sticky || upper_bits[scan_index];
        if (scan_index == 0) state <= ROUND_CHECK;
        else scan_index <= scan_index - 1'b1;
      end
      ROUND_CHECK: begin
        if (lower_rounded != upper_rounded) begin
          failed <= 1;
          sin_result <= FP32_QNAN;
          cos_result <= FP32_QNAN;
          state <= RESPONSE;
        end else begin
          reduced <= lower_rounded;
          phase <= 0;
          state <= MUL_SEND;
        end
      end
      MUL_SEND: state <= MUL_WAIT;
      MUL_WAIT: if (multiply_valid) case (phase)
        0: begin
          square <= multiply_data;
          polynomial <= coefficient(0, 8);
          degree <= 7;
          phase <= 1;
          state <= MUL_SEND;
        end
        1, 3: begin temporary <= multiply_data; state <= ADD_SEND; end
        2: begin
          sine <= multiply_data;
          polynomial <= coefficient(1, 8);
          degree <= 7;
          phase <= 3;
          state <= MUL_SEND;
        end
      endcase
      ADD_SEND: state <= ADD_WAIT;
      ADD_WAIT: if (add_valid) begin
        polynomial <= add_data;
        if (degree != 0) begin
          degree <= degree - 1'b1;
          state <= MUL_SEND;
        end else if (phase == 1) begin phase <= 2; state <= MUL_SEND; end
        else begin cosine <= add_data; state <= MAP; end
      end
      MAP: begin
        sin_result <= {mapped_sin[31] ^ input_negative, mapped_sin[30:0]};
        cos_result <= mapped_cos;
        state <= RESPONSE;
      end
      default: begin
        failed <= 1;
        sin_result <= FP32_QNAN;
        cos_result <= FP32_QNAN;
        state <= RESPONSE;
      end
    endcase
  end
endmodule
