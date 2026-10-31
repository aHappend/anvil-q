module anvil_q1_ht2_projection #(
  parameter HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter GROUP_SIZE = 128, VOCAB_SIZE = 151936
) (
  input wire clk, rst_n, abort_error,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [1:0] cmd_format,
  input wire [3:0] cmd_slots,
  input wire [31:0] cmd_inputs, cmd_outputs,
  input wire [32:0] cmd_weight_base, cmd_zero_base, cmd_scale_base,
  input wire [31:0] cmd_weight_length, cmd_zero_length, cmd_scale_length,
  input wire cmd_down_projection, cmd_sparse, cmd_finite_weights,
  input wire [15:0] cmd_threshold,
  input wire activation_valid,
  output wire activation_ready,
  input wire [63:0] activation_data,
  input wire [3:0] activation_nonzero,
  output wire result_valid,
  input wire result_ready,
  output wire [31:0] result_panel,
  output wire [8191:0] result_data,
  output wire [63:0] result_mask,
  output wire [3:0] result_slots,
  output wire busy, done, error,
  output wire dma_valid,
  input wire dma_ready,
  output wire [32:0] dma_address,
  output wire [7:0] dma_burstcount,
  input wire dma_data_valid,
  output wire dma_data_ready,
  input wire [511:0] dma_data,
  input wire dma_error,
  output wire stats_valid,
  output wire [31:0] stats_dense_bytes, stats_avoided_bytes, stats_replay_bytes,
  output wire stats_replay_column
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam SG = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  localparam LEGAL = HIDDEN_SIZE >= 8 && HIDDEN_SIZE <= 896 &&
    INTERMEDIATE_SIZE >= 8 && INTERMEDIATE_SIZE <= 4864 &&
    (HIDDEN_SIZE & 7) == 0 && (INTERMEDIATE_SIZE & 7) == 0 &&
    GROUP_SIZE >= 1 && GROUP_SIZE <= HIDDEN_SIZE &&
    HIDDEN_SIZE % SG == 0 && INTERMEDIATE_SIZE % SG == 0 &&
    VOCAB_SIZE >= 1 && VOCAB_SIZE <= 151936;
  localparam H = LEGAL ? HIDDEN_SIZE : 8, I = LEGAL ? INTERMEDIATE_SIZE : 8;
  localparam G = LEGAL ? GROUP_SIZE : 1, V = LEGAL ? VOCAB_SIZE : 1;
  localparam MAX_INPUTS = H > I ? H : I;
  localparam MAX_ROWS = (H > I ? H : I) > V ? (H > I ? H : I) : V;
  localparam IDLE = 5'd0, PREF_MULTIPLY = 5'd1, PREF_LENGTH = 5'd2,
    PREF_CHECK = 5'd3, INPUT_FILL = 5'd4, PANEL_BEGIN = 5'd5,
    COLUMN_READ = 5'd6, COLUMN_SETUP = 5'd7,
    ZERO_REQUEST = 5'd8, ZERO_RESPONSE = 5'd9,
    SCALE_REQUEST = 5'd10, SCALE_RESPONSE = 5'd11,
    WEIGHT_BEGIN = 5'd12, SPARSE_REQUEST = 5'd13, SPARSE_RESPONSE = 5'd14,
    WEIGHT_REQUEST = 5'd15, WEIGHT_RESPONSE = 5'd16, WEIGHT_CHECK = 5'd17,
    DEQUANT_SEND = 5'd18, DEQUANT_WAIT = 5'd19, MAC_SEND = 5'd20,
    MAC_RESPONSE = 5'd21, PANEL_RESULT = 5'd22, COMPLETE = 5'd23,
    FAIL_DRAIN = 5'd24;
  wire run_n;
  reg [4:0] state;
  reg [1:0] format;
  reg [3:0] slots;
  reg [12:0] inputs, group_count, input_index, column_index, group_offset;
  reg [17:0] outputs, panel;
  reg [11:0] panels;
  reg [24:0] weight_units, metadata_units;
  reg [31:0] weight_length, zero_length, scale_length;
  reg [31:0] required_weight, required_zero, required_scale;
  reg [32:0] weight_base, zero_base, scale_base;
  reg [32:0] weight_address, zero_address, scale_address;
  reg [63:0] mask;
  reg down_projection, sparse_enable, finite_weights, failed, cancel_workers, reader_owned;
  reg replay_column;
  reg [15:0] threshold;
  reg [1023:0] row_words, scale_words, weights;
  reg [255:0] zero_words;
  reg [8191:0] results;
  reg stats_pulse, replay_pulse;
  reg [31:0] dense_bytes, avoided_bytes, replay_bytes;
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [67:0] activation_store [0:MAX_INPUTS-1];
  reg [67:0] activation_q;
  reg input_bad, row_bad, original_nonzero;
  wire [63:0] sparse_activations;
  wire worker_rst_n = run_n && !cancel_workers;
  wire [33:0] weight_end = {1'b0, weight_base} + {2'b0, required_weight};
  wire [33:0] zero_end = {1'b0, zero_base} + {2'b0, required_zero};
  wire [33:0] scale_end = {1'b0, scale_base} + {2'b0, required_scale};
  wire [7:0] column_beats = format == 2 ? 8'd1 : 8'd2;
  wire [31:0] column_bytes = format == 2 ? 32'd64 : 32'd128;
  wire [17:0] remaining_rows = outputs - panel;
  wire final_column = column_index + 1'b1 == inputs;
  wire reader_cmd_valid, reader_cmd_ready, reader_rsp_valid, reader_rsp_ready;
  wire [32:0] reader_cmd_address;
  wire [7:0] reader_cmd_beats;
  wire [1023:0] reader_data;
  wire reader_error;
  wire reader_transfer = reader_cmd_valid && reader_cmd_ready;
  wire reader_response = reader_rsp_valid && reader_rsp_ready;
  wire sparse_ready, sparse_dma_valid, sparse_dma_ready, sparse_decision;
  wire [32:0] sparse_address;
  wire [7:0] sparse_beats;
  wire sparse_skipped, sparse_error;
  wire [63:0] dequant_ready, dequant_valid, dequant_error;
  wire [1023:0] dequant_weights;
  wire mac_ready, mac_valid, mac_error;
  wire [8191:0] mac_data;
  wire [63:0] mac_mask;
  wire [3:0] mac_slots;
  wire mac_transfer = state == MAC_SEND && mac_ready && !abort_error;
  wire vector_transfer = activation_valid && activation_ready;
  integer slot_index, row_index;
  genvar lane, token_slot;

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native projection geometry");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    input_bad = 0;
    original_nonzero = 0;
    for (slot_index = 0; slot_index < 4; slot_index = slot_index + 1) begin
      if (slots[slot_index]) begin
        if (format == 1) begin
          if (activation_data[16*slot_index+10+:5] == 5'h1f) input_bad = 1;
        end else if (activation_data[16*slot_index+7+:8] == 8'hff) input_bad = 1;
        if (activation_q[16*slot_index+:15] != 0 || activation_q[64+slot_index])
          original_nonzero = 1;
      end
    end
    row_bad = 0;
    for (row_index = 0; row_index < 64; row_index = row_index + 1) begin
      if (mask[row_index]) begin
        if (format == 1) begin
          if (row_words[16*row_index+10+:5] == 5'h1f) row_bad = 1;
        end else if (row_words[16*row_index+7+:8] == 8'hff) row_bad = 1;
      end
    end
  end
  generate
    for (token_slot = 0; token_slot < 4; token_slot = token_slot + 1) begin : g_predicate
      wire [31:0] expanded = expand16(activation_q[16*token_slot+:16], 1'b1);
      assign sparse_activations[16*token_slot+:16] = format == 1 ?
        narrow32(expanded, 1'b0) : activation_q[16*token_slot+:16];
    end
    for (lane = 0; lane < 64; lane = lane + 1) begin : g_dequant
      anvil_q1_ht2_dequant u_dequant (
        .clk(clk), .rst_n(worker_rst_n),
        .in_valid(state == DEQUANT_SEND && (&dequant_ready) && !abort_error),
        .in_ready(dequant_ready[lane]),
        .in_qweight(mask[lane] ? row_words[32*(lane >> 3)+:32] : 32'b0),
        .in_qzero(mask[lane] ? zero_words[32*(lane >> 3)+:32] : 32'b0),
        .in_lane(3'(lane & 7)),
        .in_scale(mask[lane] ? scale_words[16*lane+:16] : 16'b0),
        .out_valid(dequant_valid[lane]),
        .out_ready(state == DEQUANT_WAIT),
        .out_weight(dequant_weights[16*lane+:16]), .out_error(dequant_error[lane])
      );
    end
  endgenerate
  anvil_q1_ht2_sparse_dma u_sparse (
    .clk(clk), .rst_n(worker_rst_n),
    .req_valid(state == SPARSE_REQUEST && !abort_error), .req_ready(sparse_ready),
    .req_address(weight_address), .req_burstcount(column_beats),
    .req_activations(sparse_activations), .req_slots(slots), .req_threshold(threshold),
    .dma_valid(sparse_dma_valid), .dma_ready(sparse_dma_ready),
    .dma_address(sparse_address), .dma_burstcount(sparse_beats),
    .decision_valid(sparse_decision), .decision_ready(state == SPARSE_RESPONSE),
    .decision_skipped(sparse_skipped), .decision_error(sparse_error)
  );
  assign reader_cmd_valid = run_n && !abort_error &&
    (state == ZERO_REQUEST || state == SCALE_REQUEST || state == WEIGHT_REQUEST ||
     (state == SPARSE_RESPONSE && sparse_dma_valid));
  assign reader_cmd_address = !reader_cmd_valid ? 33'b0 :
    state == ZERO_REQUEST ? zero_address : state == SCALE_REQUEST ? scale_address :
    state == SPARSE_RESPONSE ? sparse_address : weight_address;
  assign reader_cmd_beats = !reader_cmd_valid ? 8'b0 :
    state == ZERO_REQUEST ? 8'd1 : state == SCALE_REQUEST ? 8'd2 :
    state == SPARSE_RESPONSE ? sparse_beats : column_beats;
  assign sparse_dma_ready = run_n && !abort_error &&
    state == SPARSE_RESPONSE && reader_cmd_ready;
  assign reader_rsp_ready = run_n &&
    (state == ZERO_RESPONSE || state == SCALE_RESPONSE ||
     state == WEIGHT_RESPONSE || state == FAIL_DRAIN);
  anvil_q1_ht2_burst_reader u_reader (
    .clk(clk), .rst_n(run_n), .cmd_valid(reader_cmd_valid), .cmd_ready(reader_cmd_ready),
    .cmd_address(reader_cmd_address), .cmd_burstcount(reader_cmd_beats),
    .mem_valid(dma_valid), .mem_ready(dma_ready), .mem_address(dma_address),
    .mem_burstcount(dma_burstcount), .mem_data_valid(dma_data_valid),
    .mem_data_ready(dma_data_ready), .mem_data(dma_data), .mem_error(dma_error),
    .rsp_valid(reader_rsp_valid), .rsp_ready(reader_rsp_ready),
    .rsp_data(reader_data), .rsp_error(reader_error)
  );
  anvil_q1_ht2_tile_batch_mac u_array (
    .clk(clk), .rst_n(worker_rst_n),
    .in_valid(state == MAC_SEND && !abort_error), .in_ready(mac_ready),
    .in_first(column_index == 0), .in_last(final_column), .in_fp16(format == 1),
    .in_slots(slots), .in_mask(mask), .in_activation(activation_q[63:0]), .in_weights(weights),
    .out_valid(mac_valid), .out_ready(state == MAC_RESPONSE),
    .out_data(mac_data), .out_mask(mac_mask), .out_slots(mac_slots), .out_error(mac_error)
  );
  assign cmd_ready = run_n && state == IDLE && !abort_error;
  assign activation_ready = run_n && state == INPUT_FILL && !abort_error;
  assign result_valid = run_n && state == PANEL_RESULT;
  assign result_panel = result_valid ? {14'b0, panel} : 32'b0;
  assign result_data = result_valid ? results : 8192'b0;
  assign result_mask = result_valid ? mask : 64'b0;
  assign result_slots = result_valid ? slots : 4'b0;
  assign busy = run_n && state != IDLE;
  assign done = run_n && state == COMPLETE;
  assign error = done && failed;
  assign stats_valid = run_n && stats_pulse;
  assign stats_dense_bytes = stats_valid ? dense_bytes : 32'b0;
  assign stats_avoided_bytes = stats_valid ? avoided_bytes : 32'b0;
  assign stats_replay_bytes = stats_valid ? replay_bytes : 32'b0;
  assign stats_replay_column = stats_valid && replay_pulse;

  always @(posedge clk) begin
    if (run_n) begin
      if (vector_transfer && !input_bad)
        activation_store[input_index] <= {activation_nonzero, activation_data};
      if (state == COLUMN_READ) activation_q <= activation_store[column_index];
    end
  end
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      format <= 0;
      slots <= 0;
      inputs <= 0;
      group_count <= 0;
      input_index <= 0;
      column_index <= 0;
      group_offset <= 0;
      outputs <= 0;
      panel <= 0;
      panels <= 0;
      weight_units <= 0;
      metadata_units <= 0;
      weight_length <= 0;
      zero_length <= 0;
      scale_length <= 0;
      required_weight <= 0;
      required_zero <= 0;
      required_scale <= 0;
      weight_base <= 0;
      zero_base <= 0;
      scale_base <= 0;
      weight_address <= 0;
      zero_address <= 0;
      scale_address <= 0;
      mask <= 0;
      down_projection <= 0;
      sparse_enable <= 0;
      finite_weights <= 0;
      failed <= 0;
      cancel_workers <= 0;
      reader_owned <= 0;
      replay_column <= 0;
      threshold <= 0;
      row_words <= 0;
      scale_words <= 0;
      weights <= 0;
      zero_words <= 0;
      results <= 0;
      stats_pulse <= 0;
      replay_pulse <= 0;
      dense_bytes <= 0;
      avoided_bytes <= 0;
      replay_bytes <= 0;
    end else begin
      stats_pulse <= 0;
      replay_pulse <= 0;
      dense_bytes <= 0;
      avoided_bytes <= 0;
      replay_bytes <= 0;
      if (reader_transfer) reader_owned <= 1;
      if (reader_response) reader_owned <= 0;
      if (abort_error && state != IDLE && state != COMPLETE && state != FAIL_DRAIN) begin
        failed <= 1;
        cancel_workers <= 1;
        state <= FAIL_DRAIN;
      end else case (state)
        IDLE: begin
          cancel_workers <= 0;
          if (cmd_valid && cmd_ready) begin
            format <= cmd_format;
            slots <= cmd_slots;
            inputs <= cmd_inputs[12:0];
            outputs <= cmd_outputs[17:0];
            panels <= 12'((cmd_outputs+63) >> 6);
            group_count <= cmd_inputs == I ? 13'(I/G) : 13'(H/G);
            weight_base <= cmd_weight_base;
            zero_base <= cmd_zero_base;
            scale_base <= cmd_scale_base;
            weight_length <= cmd_weight_length;
            zero_length <= cmd_zero_length;
            scale_length <= cmd_scale_length;
            weight_address <= cmd_weight_base;
            zero_address <= cmd_zero_base;
            scale_address <= cmd_scale_base;
            down_projection <= cmd_down_projection;
            sparse_enable <= cmd_sparse && cmd_down_projection;
            finite_weights <= cmd_finite_weights;
            threshold <= cmd_threshold;
            input_index <= 0;
            panel <= 0;
            failed <= 0;
            replay_column <= 0;
            if (!LEGAL || cmd_format == 3 || cmd_slots == 0 ||
                (cmd_inputs != H && cmd_inputs != I) ||
                cmd_outputs == 0 || cmd_outputs > MAX_ROWS ||
                (cmd_sparse && (cmd_threshold[14:7] == 8'hff ||
                  (cmd_threshold[15] && cmd_threshold[14:0] != 0)))) begin
              failed <= 1;
              state <= COMPLETE;
            end else state <= PREF_MULTIPLY;
          end
        end
        PREF_MULTIPLY: begin
          weight_units <= inputs * panels;
          metadata_units <= group_count * panels;
          state <= PREF_LENGTH;
        end
        PREF_LENGTH: begin
          required_weight <= format == 2 ? {1'b0, weight_units, 6'b0} :
                                                            {weight_units, 7'b0};
          required_zero <= {1'b0, metadata_units, 6'b0};
          required_scale <= {metadata_units, 7'b0};
          state <= PREF_CHECK;
        end
        PREF_CHECK: begin
          if (weight_length != required_weight || (|weight_base[5:0]) ||
              weight_end > 34'h200000000 ||
              (format == 2 && (zero_length != required_zero ||
                scale_length != required_scale || (|zero_base[5:0]) ||
                (|scale_base[5:0]) || zero_end > 34'h200000000 ||
                scale_end > 34'h200000000))) begin
            failed <= 1;
            state <= COMPLETE;
          end else state <= INPUT_FILL;
        end
        INPUT_FILL: if (vector_transfer) begin
          if (input_bad) begin failed <= 1; state <= COMPLETE; end
          else if (input_index + 1'b1 == inputs) state <= PANEL_BEGIN;
          else input_index <= input_index + 1'b1;
        end
        PANEL_BEGIN: begin
          mask <= remaining_rows >= 64 ? 64'hffffffffffffffff :
                                          64'hffffffffffffffff >> (64-remaining_rows);
          column_index <= 0;
          group_offset <= 0;
          state <= COLUMN_READ;
        end
        COLUMN_READ: state <= COLUMN_SETUP;
        COLUMN_SETUP: begin
          replay_column <= 0;
          if (down_projection) begin
            stats_pulse <= 1;
            dense_bytes <= column_bytes;
          end
          if (format == 2 && group_offset == 0) state <= ZERO_REQUEST;
          else state <= WEIGHT_BEGIN;
        end
        ZERO_REQUEST: if (reader_transfer) state <= ZERO_RESPONSE;
        ZERO_RESPONSE: if (reader_response) begin
          if (reader_error) begin
            failed <= 1;
            cancel_workers <= 1;
            state <= FAIL_DRAIN;
          end else begin
            zero_words <= reader_data[255:0];
            zero_address <= zero_address + 33'd64;
            state <= SCALE_REQUEST;
          end
        end
        SCALE_REQUEST: if (reader_transfer) state <= SCALE_RESPONSE;
        SCALE_RESPONSE: if (reader_response) begin
          if (reader_error) begin
            failed <= 1;
            cancel_workers <= 1;
            state <= FAIL_DRAIN;
          end else begin
            scale_words <= reader_data;
            scale_address <= scale_address + 33'd128;
            state <= WEIGHT_BEGIN;
          end
        end
        WEIGHT_BEGIN: begin
          if (sparse_enable) state <= SPARSE_REQUEST;
          else state <= WEIGHT_REQUEST;
        end
        SPARSE_REQUEST: if (sparse_ready) state <= SPARSE_RESPONSE;
        SPARSE_RESPONSE: if (sparse_decision) begin
          if (sparse_error) begin
            failed <= 1;
            cancel_workers <= 1;
            state <= FAIL_DRAIN;
          end else if (!sparse_skipped) state <= WEIGHT_RESPONSE;
          else if (original_nonzero || !finite_weights) begin
            replay_column <= 1;
            state <= WEIGHT_REQUEST;
          end else begin
            weights <= 0;
            stats_pulse <= 1;
            avoided_bytes <= column_bytes;
            state <= MAC_SEND;
          end
        end
        WEIGHT_REQUEST: if (reader_transfer) begin
          if (replay_column) begin
            stats_pulse <= 1;
            replay_pulse <= 1;
            replay_bytes <= column_bytes;
          end
          state <= WEIGHT_RESPONSE;
        end
        WEIGHT_RESPONSE: if (reader_response) begin
          if (reader_error) begin
            failed <= 1;
            cancel_workers <= 1;
            state <= FAIL_DRAIN;
          end else begin row_words <= reader_data; state <= WEIGHT_CHECK; end
        end
        WEIGHT_CHECK: begin
          if (format == 2) state <= DEQUANT_SEND;
          else if (row_bad) begin
            failed <= 1;
            cancel_workers <= 1;
            state <= FAIL_DRAIN;
          end else begin weights <= row_words; state <= MAC_SEND; end
        end
        DEQUANT_SEND: if (&dequant_ready) state <= DEQUANT_WAIT;
        DEQUANT_WAIT: if (&dequant_valid) begin
          if (|(dequant_error & mask)) begin
            failed <= 1;
            cancel_workers <= 1;
            state <= FAIL_DRAIN;
          end else begin weights <= dequant_weights; state <= MAC_SEND; end
        end
        MAC_SEND: if (mac_transfer) begin
          weight_address <= weight_address + {1'b0, column_bytes};
          if (final_column) state <= MAC_RESPONSE;
          else begin
            column_index <= column_index + 1'b1;
            if (group_offset + 1'b1 == G) group_offset <= 0;
            else group_offset <= group_offset + 1'b1;
            state <= COLUMN_READ;
          end
        end
        MAC_RESPONSE: if (mac_valid) begin
          if (mac_error || mac_mask != mask || mac_slots != slots) begin
            failed <= 1;
            cancel_workers <= 1;
            state <= FAIL_DRAIN;
          end else begin results <= mac_data; state <= PANEL_RESULT; end
        end
        PANEL_RESULT: if (result_valid && result_ready) begin
          if (panel + 18'd64 >= outputs) state <= COMPLETE;
          else begin panel <= panel + 18'd64; state <= PANEL_BEGIN; end
        end
        FAIL_DRAIN: if (!reader_owned || reader_response) state <= COMPLETE;
        COMPLETE: state <= IDLE;
        default: begin
          failed <= 1;
          cancel_workers <= 1;
          state <= FAIL_DRAIN;
        end
      endcase
    end
  end
endmodule
