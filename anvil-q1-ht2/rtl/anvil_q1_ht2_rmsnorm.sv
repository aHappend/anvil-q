module anvil_q1_ht2_rmsnorm #(
  parameter HIDDEN_SIZE = 896
) (
  input wire clk, rst_n, abort_error,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [3:0] cmd_slots,
  input wire cmd_fp16,
  input wire in_valid,
  output wire in_ready,
  input wire [127:0] in_data,
  input wire [15:0] in_gamma,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_index,
  output wire [127:0] out_data,
  output wire [3:0] out_slots,
  output wire busy, done, error
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam LEGAL = HIDDEN_SIZE >= 8 && HIDDEN_SIZE <= 896 && (HIDDEN_SIZE & 7) == 0;
  localparam H = LEGAL ? HIDDEN_SIZE : 8;
  localparam [31:0] H_FLOAT = pack32(1'b0, 64'(H), 0);
  localparam IDLE = 5'd0, INPUT_WORD = 5'd1, SQUARE_SEND = 5'd2,
    SQUARE_WAIT = 5'd3, SUM_SEND = 5'd4, SUM_WAIT = 5'd5,
    MEAN_SEND = 5'd6, DIV_WAIT = 5'd7, EPS_SEND = 5'd8,
    EPS_WAIT = 5'd9, SQRT_SEND = 5'd10, INV_SEND = 5'd11,
    COMPLETE = 5'd18, SCALE_STREAM = 5'd19;
  wire run_n;
  reg [4:0] state;
  reg [3:0] slots;
  reg fp16, failed, cancel;
  reg [9:0] index;
  reg [1:0] divide_phase;
  reg [127:0] current, square, sums, mean, radicand, root, inverse;
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [143:0] vectors [0:H-1];
  reg [143:0] vector_q;
  wire worker_rst_n = run_n && !cancel;
  wire [31:0] gamma = expand16(vector_q[143:128], fp16);
  wire [31:0] input_gamma = expand16(in_gamma, fp16);
  wire [3:0] multiply_valid, add_valid, divide_valid, divide_ready, gamma_valid;
  wire [127:0] multiply_data, add_data, divide_data, gamma_data, masked_result;
  reg input_error, multiply_error, add_error, divide_error, gamma_error;
  reg scale_input_valid;
  reg [9:0] scale_read, scale_index;
  reg [41:0] scale_tags [0:5];
  wire scale_phase = state == SCALE_STREAM;
  wire scale_advance = !(&gamma_valid) || out_ready;
  wire scale_fetch = scale_phase && scale_advance && scale_read < H && !abort_error;
  wire multiply_send = run_n && !abort_error &&
    (state == SQUARE_SEND || (scale_phase && scale_input_valid));
  wire add_send = run_n && !abort_error && (state == SUM_SEND || state == EPS_SEND);
  wire divide_send = run_n && !abort_error && (&divide_ready) &&
    (state == MEAN_SEND || state == SQRT_SEND || state == INV_SEND);
  wire divide_consume = state == DIV_WAIT && (&divide_valid);
  integer token;
  genvar slot;

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native RMSNorm hidden size");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    input_error = fp32_nonfinite(input_gamma);
    multiply_error = 0;
    add_error = 0;
    divide_error = 0;
    gamma_error = 0;
    for (token = 0; token < 4; token = token + 1) begin
      if (slots[token]) begin
        if (fp32_nonfinite(in_data[32*token+:32])) input_error = 1;
        if (fp32_nonfinite(multiply_data[32*token+:32])) multiply_error = 1;
        if (fp32_nonfinite(add_data[32*token+:32])) add_error = 1;
        if (fp32_nonfinite(divide_data[32*token+:32])) divide_error = 1;
        if (fp32_nonfinite(gamma_data[32*token+:32])) gamma_error = 1;
      end
    end
  end
  generate for (slot = 0; slot < 4; slot = slot + 1) begin : g_slot
    wire [31:0] multiply_a = state == SQUARE_SEND ? current[32*slot+:32] :
      vector_q[32*slot+:32];
    wire [31:0] multiply_b = state == SQUARE_SEND ? current[32*slot+:32] :
      inverse[32*slot+:32];
    wire [31:0] add_a = state == SUM_SEND ? sums[32*slot+:32] : mean[32*slot+:32];
    wire [31:0] add_b = state == SUM_SEND ? square[32*slot+:32] : 32'h358637bd;
    wire [31:0] divide_a = state == MEAN_SEND ? sums[32*slot+:32] :
      state == SQRT_SEND ? radicand[32*slot+:32] : 32'h3f800000;
    wire [31:0] divide_b = state == MEAN_SEND ? H_FLOAT : root[32*slot+:32];
    anvil_q1_ht2_fp32_mul u_multiply (
      .clk(clk), .rst_n(worker_rst_n), .enable(!scale_phase || scale_advance),
      .in_valid(multiply_send),
      .in_a(slots[slot] ? multiply_a : 32'b0),
      .in_b(slots[slot] ? multiply_b : 32'b0),
      .out_valid(multiply_valid[slot]), .out_data(multiply_data[32*slot+:32])
    );
    anvil_q1_ht2_fp32_mul u_gamma (
      .clk(clk), .rst_n(worker_rst_n), .enable(scale_advance),
      .in_valid(scale_phase && (&multiply_valid) && !abort_error),
      .in_a(slots[slot] ? multiply_data[32*slot+:32] : 32'b0),
      .in_b(slots[slot] ? scale_tags[2][41:10] : 32'b0),
      .out_valid(gamma_valid[slot]), .out_data(gamma_data[32*slot+:32])
    );
    anvil_q1_ht2_fp32_add u_add (
      .clk(clk), .rst_n(worker_rst_n), .enable(1'b1), .in_valid(add_send),
      .in_a(add_a), .in_b(add_b),
      .out_valid(add_valid[slot]), .out_data(add_data[32*slot+:32])
    );
    anvil_q1_ht2_fp32_divsqrt u_divide (
      .clk(clk), .rst_n(worker_rst_n), .enable(1'b1),
      .req_valid(divide_send), .req_ready(divide_ready[slot]),
      .req_sqrt(state == SQRT_SEND), .req_a(divide_a), .req_b(divide_b),
      .rsp_valid(divide_valid[slot]), .rsp_ready(divide_consume),
      .rsp_data(divide_data[32*slot+:32])
    );
    assign masked_result[32*slot+:32] = slots[slot] ? gamma_data[32*slot+:32] : 32'b0;
  end endgenerate
  assign cmd_ready = run_n && state == IDLE && !abort_error;
  assign in_ready = run_n && state == INPUT_WORD && !abort_error;
  assign out_valid = run_n && scale_phase && (&gamma_valid) && !gamma_error && !abort_error;
  assign out_index = out_valid ? {22'b0, scale_tags[5][9:0]} : 32'b0;
  assign out_data = out_valid ? masked_result : 128'b0;
  assign out_slots = out_valid ? slots : 4'b0;
  assign busy = run_n && state != IDLE;
  assign done = run_n && state == COMPLETE;
  assign error = done && failed;
  always @(posedge clk) begin
    if (run_n) begin
      if (in_valid && in_ready && !input_error) vectors[index] <= {in_gamma, in_data};
      if (scale_fetch) vector_q <= vectors[scale_read];
      if (scale_phase && scale_advance) begin
        scale_tags[0] <= {gamma, scale_index};
        scale_tags[1] <= scale_tags[0];
        scale_tags[2] <= scale_tags[1];
        scale_tags[3] <= scale_tags[2];
        scale_tags[4] <= scale_tags[3];
        scale_tags[5] <= scale_tags[4];
      end
    end
  end
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      slots <= 0;
      fp16 <= 0;
      failed <= 0;
      cancel <= 0;
      index <= 0;
      divide_phase <= 0;
      current <= 0;
      square <= 0;
      sums <= 0;
      mean <= 0;
      radicand <= 0;
      root <= 0;
      inverse <= 0;
      scale_input_valid <= 0;
      scale_read <= 0;
      scale_index <= 0;
    end else if ((abort_error || (scale_phase &&
        (((&multiply_valid) && multiply_error) || ((&gamma_valid) && gamma_error)))) &&
        state != IDLE && state != COMPLETE) begin
      failed <= 1;
      cancel <= 1;
      state <= COMPLETE;
    end else case (state)
      IDLE: begin
        cancel <= 0;
        if (cmd_valid && cmd_ready) begin
          slots <= cmd_slots;
          fp16 <= cmd_fp16;
          failed <= 0;
          sums <= 0;
          index <= 0;
          if (!LEGAL || cmd_slots == 0) begin failed <= 1; state <= COMPLETE; end
          else state <= INPUT_WORD;
        end
      end
      INPUT_WORD: if (in_valid && in_ready) begin
        if (input_error) begin failed <= 1; state <= COMPLETE; end
        else begin current <= in_data; state <= SQUARE_SEND; end
      end
      SQUARE_SEND: state <= SQUARE_WAIT;
      SQUARE_WAIT: if (&multiply_valid) begin
        if (multiply_error) begin failed <= 1; state <= COMPLETE; end
        else begin square <= multiply_data; state <= SUM_SEND; end
      end
      SUM_SEND: state <= SUM_WAIT;
      SUM_WAIT: if (&add_valid) begin
        if (add_error) begin failed <= 1; state <= COMPLETE; end
        else begin
          sums <= add_data;
          if (index + 1'b1 == H) state <= MEAN_SEND;
          else begin index <= index + 1'b1; state <= INPUT_WORD; end
        end
      end
      MEAN_SEND: if (divide_send) begin divide_phase <= 0; state <= DIV_WAIT; end
      SQRT_SEND: if (divide_send) begin divide_phase <= 1; state <= DIV_WAIT; end
      INV_SEND: if (divide_send) begin divide_phase <= 2; state <= DIV_WAIT; end
      DIV_WAIT: if (divide_consume) begin
        if (divide_error) begin failed <= 1; state <= COMPLETE; end
        else case (divide_phase)
          0: begin mean <= divide_data; state <= EPS_SEND; end
          1: begin root <= divide_data; state <= INV_SEND; end
          2: begin
            inverse <= divide_data;
            scale_read <= 0;
            scale_input_valid <= 0;
            state <= SCALE_STREAM;
          end
          default: begin failed <= 1; state <= COMPLETE; end
        endcase
      end
      EPS_SEND: state <= EPS_WAIT;
      EPS_WAIT: if (&add_valid) begin
        if (add_error) begin failed <= 1; state <= COMPLETE; end
        else begin radicand <= add_data; state <= SQRT_SEND; end
      end
      SCALE_STREAM: begin
        if (scale_advance) begin
          scale_input_valid <= scale_fetch;
          if (scale_fetch) begin
            scale_index <= scale_read;
            scale_read <= scale_read + 1'b1;
          end
        end
        if (out_valid && out_ready && scale_tags[5][9:0] + 1'b1 == H)
          state <= COMPLETE;
      end
      COMPLETE: state <= IDLE;
      default: begin failed <= 1; cancel <= 1; state <= COMPLETE; end
    endcase
  end
endmodule
