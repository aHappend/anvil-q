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
  localparam LEGAL = INTERMEDIATE_SIZE >= 8 && INTERMEDIATE_SIZE <= 4864 &&
    (INTERMEDIATE_SIZE & 7) == 0;
  localparam I = LEGAL ? INTERMEDIATE_SIZE : 8;
  localparam IDLE = 3'd0, START = 3'd1, ACTIVE = 3'd2, DRAIN = 3'd3, COMPLETE = 3'd4;
  wire run_n;
  reg [2:0] state;
  reg [3:0] slots;
  reg fp16, failed;
  reg [12:0] submitted, retired;
  wire [7:0] engine_ready, input_ready, output_valid, engine_busy, engine_done, engine_error;
  wire [255:0] indices;
  wire [1023:0] results;
  wire [511:0] activations;
  wire [31:0] nonzero, output_slots;
  wire [2:0] write_engine = submitted[2:0];
  wire [2:0] read_engine = retired[2:0];
  wire cancel = failed || abort_error;
  wire selected_valid = output_valid[read_engine];
  wire selected_bad = selected_valid &&
    (indices[32*read_engine+:32] != {22'b0, retired[12:3]} ||
     output_slots[4*read_engine+:4] != slots);
  wire input_transfer = in_valid && in_ready;
  wire output_transfer = out_valid && out_ready;
  genvar engine;

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native SwiGLU intermediate size");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  generate for (engine = 0; engine < 8; engine = engine + 1) begin : g_engine
    anvil_q1_ht2_swiglu_engine #(.WORDS(I/8)) u_engine (
      .clk(clk), .rst_n(run_n), .abort_error(cancel),
      .cmd_valid(state == START && (&engine_ready) && !cancel),
      .cmd_ready(engine_ready[engine]), .cmd_slots(slots), .cmd_fp16(fp16),
      .in_valid(state == ACTIVE && submitted < I && write_engine == engine &&
        in_valid && !cancel),
      .in_ready(input_ready[engine]), .in_gate(in_gate), .in_up(in_up),
      .out_valid(output_valid[engine]),
      .out_ready(state == ACTIVE && retired < I && read_engine == engine &&
        out_ready && !cancel && !selected_bad),
      .out_index(indices[32*engine+:32]), .out_data(results[128*engine+:128]),
      .out_activation(activations[64*engine+:64]),
      .out_nonzero(nonzero[4*engine+:4]), .out_slots(output_slots[4*engine+:4]),
      .busy(engine_busy[engine]), .done(engine_done[engine]), .error(engine_error[engine])
    );
  end endgenerate
  assign cmd_ready = run_n && state == IDLE && !abort_error;
  assign in_ready = run_n && state == ACTIVE && submitted < I &&
    input_ready[write_engine] && !cancel;
  assign out_valid = run_n && state == ACTIVE && retired < I &&
    selected_valid && !selected_bad && !cancel;
  assign out_index = out_valid ? {19'b0, retired} : 32'b0;
  assign out_data = out_valid ? results[128*read_engine+:128] : 128'b0;
  assign out_activation = out_valid ? activations[64*read_engine+:64] : 64'b0;
  assign out_nonzero = out_valid ? nonzero[4*read_engine+:4] : 4'b0;
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
      submitted <= 0;
      retired <= 0;
    end else if ((abort_error || (|engine_error) ||
        (state == ACTIVE && selected_bad)) &&
        state != IDLE && state != COMPLETE && state != DRAIN) begin
      failed <= 1;
      state <= DRAIN;
    end else case (state)
      IDLE: if (cmd_valid && cmd_ready) begin
        slots <= cmd_slots;
        fp16 <= cmd_fp16;
        submitted <= 0;
        retired <= 0;
        failed <= !LEGAL || cmd_slots == 0;
        if (!LEGAL || cmd_slots == 0) state <= COMPLETE;
        else state <= START;
      end
      START: if (&engine_ready) state <= ACTIVE;
      ACTIVE: begin
        if (input_transfer) submitted <= submitted + 1'b1;
        if (output_transfer) begin
          retired <= retired + 1'b1;
          if (retired + 1'b1 == I) state <= DRAIN;
        end
      end
      DRAIN: if (!(|engine_busy)) state <= COMPLETE;
      COMPLETE: state <= IDLE;
      default: begin failed <= 1; state <= DRAIN; end
    endcase
  end
endmodule
