module anvil_q1_ht2_rope #(
  parameter HEAD_DIM = 64, HEADS = 14
) (
  input wire clk, rst_n, abort_error,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [3:0] cmd_slots,
  input wire cmd_fp16,
  input wire [127:0] cmd_positions,
  input wire in_valid,
  output wire in_ready,
  input wire [127:0] in_first, in_second,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_first_index, out_second_index,
  output wire [127:0] out_first, out_second,
  output wire [63:0] out_first_encoded, out_second_encoded,
  output wire [3:0] out_slots,
  output wire busy, done, error
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam LEGAL = HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    HEADS >= 1 && HEADS <= 14 && HEADS*HEAD_DIM <= 896;
  localparam D = LEGAL ? HEAD_DIM : 8, N = LEGAL ? HEADS : 1;
  localparam IDLE = 5'd0, INPUT_PAIR = 5'd1, ANGLE_SEND = 5'd2, ANGLE_WAIT = 5'd3,
    TRIG_SEND = 5'd4, TRIG_WAIT = 5'd5,
    MUL0_SEND = 5'd6, MUL0_WAIT = 5'd7, MUL1_SEND = 5'd8, MUL1_WAIT = 5'd9,
    ADD0_SEND = 5'd10, ADD0_WAIT = 5'd11,
    MUL2_SEND = 5'd12, MUL2_WAIT = 5'd13, MUL3_SEND = 5'd14, MUL3_WAIT = 5'd15,
    ADD1_SEND = 5'd16, ADD1_WAIT = 5'd17, OUTPUT_PAIR = 5'd18, COMPLETE = 5'd19;
  wire run_n;
  reg [4:0] state, pair_index;
  reg [9:0] row_base;
  reg [3:0] slots;
  reg fp16, failed, cancel;
  reg [127:0] positions, first_input, second_input, angle, sine, cosine;
  reg [127:0] first_product, second_product, first_result, second_result;
  wire [31:0] frequency;
  wire worker_rst_n = run_n && !cancel;
  wire [3:0] multiply_valid, add_valid, trig_valid, trig_ready, trig_error;
  wire [127:0] multiply_data, add_data, trig_sin, trig_cos;
  wire [127:0] first_masked, second_masked;
  wire [63:0] first_encoded, second_encoded;
  reg command_error, input_error, multiply_error, addition_error, trig_failed, narrowing_error;
  wire multiply_send = run_n && !abort_error &&
    (state == ANGLE_SEND || state == MUL0_SEND || state == MUL1_SEND ||
     state == MUL2_SEND || state == MUL3_SEND);
  wire add_send = run_n && !abort_error && (state == ADD0_SEND || state == ADD1_SEND);
  wire trig_send = run_n && !abort_error && state == TRIG_SEND && (&trig_ready);
  wire trig_consume = state == TRIG_WAIT && (&trig_valid);
  integer token;
  genvar slot;

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native RoPE geometry");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  anvil_q1_ht2_rope_frequency #(.HEAD_DIM(D)) u_frequency (
    .rst_n(run_n), .index(pair_index), .frequency(frequency)
  );
  always @* begin
    command_error = cmd_slots == 0;
    input_error = 0;
    multiply_error = 0;
    addition_error = 0;
    trig_failed = 0;
    narrowing_error = 0;
    for (token = 0; token < 4; token = token + 1) begin
      if (cmd_slots[token] && cmd_positions[32*token+:32] >= 32768) command_error = 1;
      if (slots[token]) begin
        if (fp32_nonfinite(in_first[32*token+:32]) ||
            fp32_nonfinite(in_second[32*token+:32])) input_error = 1;
        if (fp32_nonfinite(multiply_data[32*token+:32])) multiply_error = 1;
        if (fp32_nonfinite(add_data[32*token+:32])) addition_error = 1;
        if (trig_error[token] || fp32_nonfinite(trig_sin[32*token+:32]) ||
            fp32_nonfinite(trig_cos[32*token+:32])) trig_failed = 1;
        if (fp16) begin
          if (first_encoded[16*token+10+:5] == 5'h1f ||
              second_encoded[16*token+10+:5] == 5'h1f) narrowing_error = 1;
        end else if (first_encoded[16*token+7+:8] == 8'hff ||
                     second_encoded[16*token+7+:8] == 8'hff) narrowing_error = 1;
      end
    end
  end
  generate for (slot = 0; slot < 4; slot = slot + 1) begin : g_slot
    wire [31:0] position_float = pack32(1'b0, {32'b0, positions[32*slot+:32]}, 0);
    wire [31:0] multiply_a = state == ANGLE_SEND ? position_float :
      (state == MUL0_SEND || state == MUL3_SEND) ? first_input[32*slot+:32] :
                                                               second_input[32*slot+:32];
    wire [31:0] multiply_b = state == ANGLE_SEND ? frequency :
      (state == MUL0_SEND || state == MUL2_SEND) ? cosine[32*slot+:32] : sine[32*slot+:32];
    wire [31:0] add_b = state == ADD0_SEND ?
      {~second_product[32*slot+31], second_product[32*slot+:31]} :
      second_product[32*slot+:32];
    anvil_q1_ht2_fp32_mul u_multiply (
      .clk(clk), .rst_n(worker_rst_n), .enable(1'b1), .in_valid(multiply_send),
      .in_a(slots[slot] ? multiply_a : 32'b0),
      .in_b(slots[slot] ? multiply_b : 32'b0),
      .out_valid(multiply_valid[slot]), .out_data(multiply_data[32*slot+:32])
    );
    anvil_q1_ht2_fp32_add u_add (
      .clk(clk), .rst_n(worker_rst_n), .enable(1'b1), .in_valid(add_send),
      .in_a(first_product[32*slot+:32]), .in_b(add_b),
      .out_valid(add_valid[slot]), .out_data(add_data[32*slot+:32])
    );
    anvil_q1_ht2_fp32_sincos u_sincos (
      .clk(clk), .rst_n(worker_rst_n), .enable(1'b1), .req_valid(trig_send),
      .req_ready(trig_ready[slot]), .req_data(angle[32*slot+:32]),
      .rsp_valid(trig_valid[slot]), .rsp_ready(trig_consume),
      .rsp_sin(trig_sin[32*slot+:32]), .rsp_cos(trig_cos[32*slot+:32]),
      .rsp_error(trig_error[slot])
    );
    assign first_masked[32*slot+:32] = slots[slot] ? first_result[32*slot+:32] : 32'b0;
    assign second_masked[32*slot+:32] = slots[slot] ? second_result[32*slot+:32] : 32'b0;
    assign first_encoded[16*slot+:16] = narrow32(first_masked[32*slot+:32], fp16);
    assign second_encoded[16*slot+:16] = narrow32(second_masked[32*slot+:32], fp16);
  end endgenerate
  assign cmd_ready = run_n && state == IDLE && !abort_error;
  assign in_ready = run_n && state == INPUT_PAIR && !abort_error;
  assign out_valid = run_n && state == OUTPUT_PAIR && !narrowing_error;
  assign out_first_index = out_valid ? {22'b0, row_base}+{27'b0, pair_index} : 32'b0;
  assign out_second_index = out_valid ? out_first_index+(D >> 1) : 32'b0;
  assign out_first = out_valid ? first_masked : 128'b0;
  assign out_second = out_valid ? second_masked : 128'b0;
  assign out_first_encoded = out_valid ? first_encoded : 64'b0;
  assign out_second_encoded = out_valid ? second_encoded : 64'b0;
  assign out_slots = out_valid ? slots : 4'b0;
  assign busy = run_n && state != IDLE;
  assign done = run_n && state == COMPLETE;
  assign error = done && failed;
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      pair_index <= 0;
      row_base <= 0;
      slots <= 0;
      fp16 <= 0;
      failed <= 0;
      cancel <= 0;
      positions <= 0;
      first_input <= 0;
      second_input <= 0;
      angle <= 0;
      sine <= 0;
      cosine <= 0;
      first_product <= 0;
      second_product <= 0;
      first_result <= 0;
      second_result <= 0;
    end else if (abort_error && state != IDLE && state != COMPLETE) begin
      failed <= 1;
      cancel <= 1;
      state <= COMPLETE;
    end else case (state)
      IDLE: begin
        cancel <= 0;
        if (cmd_valid && cmd_ready) begin
          slots <= cmd_slots;
          fp16 <= cmd_fp16;
          positions <= cmd_positions;
          pair_index <= 0;
          row_base <= 0;
          failed <= 0;
          if (!LEGAL || command_error) begin failed <= 1; state <= COMPLETE; end
          else state <= INPUT_PAIR;
        end
      end
      INPUT_PAIR: if (in_valid && in_ready) begin
        if (input_error) begin failed <= 1; state <= COMPLETE; end
        else begin first_input <= in_first; second_input <= in_second; state <= ANGLE_SEND; end
      end
      ANGLE_SEND: state <= ANGLE_WAIT;
      MUL0_SEND: state <= MUL0_WAIT;
      MUL1_SEND: state <= MUL1_WAIT;
      MUL2_SEND: state <= MUL2_WAIT;
      MUL3_SEND: state <= MUL3_WAIT;
      ANGLE_WAIT: if (&multiply_valid) begin
        if (multiply_error) begin failed <= 1; state <= COMPLETE; end
        else begin angle <= multiply_data; state <= TRIG_SEND; end
      end
      TRIG_SEND: if (trig_send) state <= TRIG_WAIT;
      TRIG_WAIT: if (trig_consume) begin
        if (trig_failed) begin failed <= 1; state <= COMPLETE; end
        else begin sine <= trig_sin; cosine <= trig_cos; state <= MUL0_SEND; end
      end
      MUL0_WAIT, MUL2_WAIT: if (&multiply_valid) begin
        if (multiply_error) begin failed <= 1; state <= COMPLETE; end
        else begin
          first_product <= multiply_data;
          if (state == MUL0_WAIT) state <= MUL1_SEND;
          else state <= MUL3_SEND;
        end
      end
      MUL1_WAIT, MUL3_WAIT: if (&multiply_valid) begin
        if (multiply_error) begin failed <= 1; state <= COMPLETE; end
        else begin
          second_product <= multiply_data;
          if (state == MUL1_WAIT) state <= ADD0_SEND;
          else state <= ADD1_SEND;
        end
      end
      ADD0_SEND: state <= ADD0_WAIT;
      ADD1_SEND: state <= ADD1_WAIT;
      ADD0_WAIT: if (&add_valid) begin
        if (addition_error) begin failed <= 1; state <= COMPLETE; end
        else begin first_result <= add_data; state <= MUL2_SEND; end
      end
      ADD1_WAIT: if (&add_valid) begin
        if (addition_error) begin failed <= 1; state <= COMPLETE; end
        else begin second_result <= add_data; state <= OUTPUT_PAIR; end
      end
      OUTPUT_PAIR: begin
        if (narrowing_error) begin failed <= 1; state <= COMPLETE; end
        else if (out_valid && out_ready) begin
          if ({1'b0, pair_index}+6'd1 == (D >> 1)) begin
            pair_index <= 0;
            if (row_base + D >= N*D) state <= COMPLETE;
            else begin row_base <= row_base + 10'(D); state <= INPUT_PAIR; end
          end else begin pair_index <= pair_index + 1'b1; state <= INPUT_PAIR; end
        end
      end
      COMPLETE: state <= IDLE;
      default: begin failed <= 1; cancel <= 1; state <= COMPLETE; end
    endcase
  end
endmodule
