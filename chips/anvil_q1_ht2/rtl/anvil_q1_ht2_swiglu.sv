module anvil_q1_ht2_swiglu #(
  parameter INTERMEDIATE_SIZE = 4864
) (
  input wire clk, rst_n, abort_error,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [3:0] cmd_slots,
  input wire cmd_fp16,
  input wire in_valid,
  output wire in_ready,
  input wire [127:0] in_gate, in_up,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_index,
  output wire [127:0] out_data,
  output wire [63:0] out_activation,
  output wire [3:0] out_nonzero, out_slots,
  output wire busy, done, error
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam LEGAL = INTERMEDIATE_SIZE >= 8 && INTERMEDIATE_SIZE <= 4864 &&
    (INTERMEDIATE_SIZE & 7) == 0;
  localparam I = LEGAL ? INTERMEDIATE_SIZE : 8;
  localparam IDLE = 4'd0, INPUT_WORD = 4'd1, EXP_SEND = 4'd2,
    EXP_WAIT = 4'd3, ADD_SEND = 4'd4, ADD_WAIT = 4'd5,
    DIV_SEND = 4'd6, DIV_WAIT = 4'd7, SILU_SEND = 4'd8, SILU_WAIT = 4'd9,
    PRODUCT_SEND = 4'd10, PRODUCT_WAIT = 4'd11, OUTPUT_WORD = 4'd12, COMPLETE = 4'd13;
  wire run_n;
  reg [3:0] state, slots;
  reg fp16, failed, cancel;
  reg [12:0] index;
  reg [127:0] gate, up, exponential, denominator, sigmoid, silu, result;
  wire worker_rst_n = run_n && !cancel;
  wire [3:0] exp_ready, exp_valid, add_valid, div_ready, div_valid, mul_valid;
  wire [127:0] exp_data, add_data, div_data, mul_data, masked_result;
  wire [63:0] narrowed_result;
  wire [3:0] nonzero;
  wire exp_send = run_n && !abort_error && state == EXP_SEND && (&exp_ready);
  wire exp_consume = state == EXP_WAIT && (&exp_valid);
  wire div_send = run_n && !abort_error && state == DIV_SEND && (&div_ready);
  wire div_consume = state == DIV_WAIT && (&div_valid);
  reg input_error, exponential_error, addition_error, division_error, multiplication_error;
  reg narrowing_error;
  integer token;
  genvar slot;

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native SwiGLU intermediate size");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    input_error = 0;
    exponential_error = 0;
    addition_error = 0;
    division_error = 0;
    multiplication_error = 0;
    narrowing_error = 0;
    for (token = 0; token < 4; token = token + 1) begin
      if (slots[token]) begin
        if (fp32_nonfinite(in_gate[32*token+:32]) ||
            fp32_nonfinite(in_up[32*token+:32])) input_error = 1;
        if (fp32_nonfinite(exp_data[32*token+:32])) exponential_error = 1;
        if (fp32_nonfinite(add_data[32*token+:32])) addition_error = 1;
        if (fp32_nonfinite(div_data[32*token+:32])) division_error = 1;
        if (fp32_nonfinite(mul_data[32*token+:32])) multiplication_error = 1;
        if (fp16) begin
          if (narrowed_result[16*token+10+:5] == 5'h1f) narrowing_error = 1;
        end else if (narrowed_result[16*token+7+:8] == 8'hff) narrowing_error = 1;
      end
    end
  end
  generate for (slot = 0; slot < 4; slot = slot + 1) begin : g_slot
    wire negative_gate = gate[32*slot+31] && (|gate[32*slot+:31]);
    wire [31:0] exp_argument = slots[slot] ? {1'b1, gate[32*slot+:31]} : 32'b0;
    wire [31:0] numerator = negative_gate ? exponential[32*slot+:32] : 32'h3f800000;
    wire [31:0] multiply_a = state == SILU_SEND ? gate[32*slot+:32] : silu[32*slot+:32];
    wire [31:0] multiply_b = state == SILU_SEND ? sigmoid[32*slot+:32] : up[32*slot+:32];
    anvil_q1_ht2_fp32_exp u_exp (
      .clk(clk), .rst_n(worker_rst_n), .enable(1'b1),
      .req_valid(exp_send), .req_ready(exp_ready[slot]), .req_data(exp_argument),
      .rsp_valid(exp_valid[slot]), .rsp_ready(exp_consume), .rsp_data(exp_data[32*slot+:32])
    );
    anvil_q1_ht2_fp32_add u_add (
      .clk(clk), .rst_n(worker_rst_n), .enable(1'b1),
      .in_valid(run_n && !abort_error && state == ADD_SEND),
      .in_a(32'h3f800000), .in_b(exponential[32*slot+:32]),
      .out_valid(add_valid[slot]), .out_data(add_data[32*slot+:32])
    );
    anvil_q1_ht2_fp32_divsqrt u_divide (
      .clk(clk), .rst_n(worker_rst_n), .enable(1'b1),
      .req_valid(div_send), .req_ready(div_ready[slot]), .req_sqrt(1'b0),
      .req_a(numerator), .req_b(denominator[32*slot+:32]),
      .rsp_valid(div_valid[slot]), .rsp_ready(div_consume), .rsp_data(div_data[32*slot+:32])
    );
    anvil_q1_ht2_fp32_mul u_multiply (
      .clk(clk), .rst_n(worker_rst_n), .enable(1'b1),
      .in_valid(run_n && !abort_error && (state == SILU_SEND || state == PRODUCT_SEND)),
      .in_a(slots[slot] ? multiply_a : 32'b0),
      .in_b(slots[slot] ? multiply_b : 32'b0),
      .out_valid(mul_valid[slot]), .out_data(mul_data[32*slot+:32])
    );
    assign masked_result[32*slot+:32] = slots[slot] ? result[32*slot+:32] : 32'b0;
    assign narrowed_result[16*slot+:16] = narrow32(masked_result[32*slot+:32], fp16);
    assign nonzero[slot] = slots[slot] && (|result[32*slot+:31]);
  end endgenerate
  assign cmd_ready = run_n && state == IDLE && !abort_error;
  assign in_ready = run_n && state == INPUT_WORD && !abort_error;
  assign out_valid = run_n && state == OUTPUT_WORD && !narrowing_error;
  assign out_index = out_valid ? {19'b0, index} : 32'b0;
  assign out_data = out_valid ? masked_result : 128'b0;
  assign out_activation = out_valid ? narrowed_result : 64'b0;
  assign out_nonzero = out_valid ? nonzero : 4'b0;
  assign out_slots = out_valid ? slots : 4'b0;
  assign busy = run_n && state != IDLE;
  assign done = run_n && state == COMPLETE;
  assign error = done && failed;
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      slots <= 0;
      fp16 <= 0;
      failed <= 0;
      cancel <= 0;
      index <= 0;
      gate <= 0;
      up <= 0;
      exponential <= 0;
      denominator <= 0;
      sigmoid <= 0;
      silu <= 0;
      result <= 0;
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
          index <= 0;
          failed <= 0;
          if (!LEGAL || cmd_slots == 0) begin failed <= 1; state <= COMPLETE; end
          else state <= INPUT_WORD;
        end
      end
      INPUT_WORD: if (in_valid && in_ready) begin
        if (input_error) begin failed <= 1; state <= COMPLETE; end
        else begin gate <= in_gate; up <= in_up; state <= EXP_SEND; end
      end
      EXP_SEND: if (exp_send) state <= EXP_WAIT;
      EXP_WAIT: if (exp_consume) begin
        if (exponential_error) begin failed <= 1; state <= COMPLETE; end
        else begin exponential <= exp_data; state <= ADD_SEND; end
      end
      ADD_SEND: state <= ADD_WAIT;
      ADD_WAIT: if (&add_valid) begin
        if (addition_error) begin failed <= 1; state <= COMPLETE; end
        else begin denominator <= add_data; state <= DIV_SEND; end
      end
      DIV_SEND: if (div_send) state <= DIV_WAIT;
      DIV_WAIT: if (div_consume) begin
        if (division_error) begin failed <= 1; state <= COMPLETE; end
        else begin sigmoid <= div_data; state <= SILU_SEND; end
      end
      SILU_SEND: state <= SILU_WAIT;
      SILU_WAIT: if (&mul_valid) begin
        if (multiplication_error) begin failed <= 1; state <= COMPLETE; end
        else begin silu <= mul_data; state <= PRODUCT_SEND; end
      end
      PRODUCT_SEND: state <= PRODUCT_WAIT;
      PRODUCT_WAIT: if (&mul_valid) begin
        if (multiplication_error) begin failed <= 1; state <= COMPLETE; end
        else begin result <= mul_data; state <= OUTPUT_WORD; end
      end
      OUTPUT_WORD: begin
        if (narrowing_error) begin failed <= 1; state <= COMPLETE; end
        else if (out_valid && out_ready) begin
          if (index + 1'b1 == I) state <= COMPLETE;
          else begin index <= index + 1'b1; state <= INPUT_WORD; end
        end
      end
      COMPLETE: state <= IDLE;
      default: begin failed <= 1; cancel <= 1; state <= COMPLETE; end
    endcase
  end
endmodule
