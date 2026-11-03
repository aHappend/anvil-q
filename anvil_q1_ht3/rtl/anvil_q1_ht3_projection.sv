module anvil_q1_ht3_projection #(
  parameter HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter GROUP_SIZE = 128, VOCAB_SIZE = 151936, TILE_BEATS = 256
) (
  input wire clk, rst_n, abort_error, cmd_valid,
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
  output wire stats_replay_column,
  input wire cmd_int8_weights,
  input wire [32:0] cmd_int8_scale_base,
  input wire [31:0] cmd_int8_scale_length
);
  import anvil_q1_ht3_fp_pkg::*;
  function automatic integer constant_groups(input integer extent, input integer group_size);
    reg [32:0] remainder_value;
    reg [31:0] quotient;
    integer bit_index;
    begin
      remainder_value = 0;
      quotient = 0;
      if (extent > 0 && group_size > 0) begin
        for (bit_index = 31; bit_index >= 0; bit_index = bit_index - 1) begin
          remainder_value = {remainder_value[31:0], extent[bit_index]};
          if (remainder_value >= group_size) begin
            remainder_value = remainder_value - group_size;
            quotient[bit_index] = 1;
          end
        end
      end
      constant_groups = quotient;
    end
  endfunction
  localparam HG = constant_groups(HIDDEN_SIZE, GROUP_SIZE);
  localparam IG = constant_groups(INTERMEDIATE_SIZE, GROUP_SIZE);
  localparam LEGAL = HIDDEN_SIZE >= 8 && HIDDEN_SIZE <= 896 &&
    INTERMEDIATE_SIZE >= 8 && INTERMEDIATE_SIZE <= 4864 &&
    (HIDDEN_SIZE & 7) == 0 && (INTERMEDIATE_SIZE & 7) == 0 &&
    GROUP_SIZE >= 1 && GROUP_SIZE <= HIDDEN_SIZE &&
    HG*GROUP_SIZE == HIDDEN_SIZE && IG*GROUP_SIZE == INTERMEDIATE_SIZE &&
    VOCAB_SIZE >= 1 && VOCAB_SIZE <= 151936 &&
    TILE_BEATS >= 1 && TILE_BEATS <= 256;
  initial if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 projection geometry");
  generate if (!LEGAL) begin: g_invalid
    assign cmd_ready = 0;
    assign activation_ready = 0;
    assign result_valid = 0;
    assign result_panel = 0;
    assign result_data = 0;
    assign result_mask = 0;
    assign result_slots = 0;
    assign busy = 0;
    assign done = 0;
    assign error = 0;
    assign dma_valid = 0;
    assign dma_address = 0;
    assign dma_burstcount = 0;
    assign dma_data_ready = 0;
    assign stats_valid = 0;
    assign stats_dense_bytes = 0;
    assign stats_avoided_bytes = 0;
    assign stats_replay_bytes = 0;
    assign stats_replay_column = 0;
  end else begin: g_legal
    localparam MAX_INPUTS = HIDDEN_SIZE > INTERMEDIATE_SIZE ?
      HIDDEN_SIZE : INTERMEDIATE_SIZE;
    localparam MAX_ROWS = MAX_INPUTS > VOCAB_SIZE ? MAX_INPUTS : VOCAB_SIZE;
    localparam IDLE = 5'd0, PREF_MULTIPLY = 5'd1, PREF_LENGTH = 5'd2,
      PREF_CHECK = 5'd3, INPUT_FILL = 5'd4, PANEL_BEGIN = 5'd5,
      PREFETCH_BEGIN = 5'd6, META_BEGIN = 5'd7, ZERO_SEND = 5'd8,
      ZERO_WAIT = 5'd9, SCALE_SEND = 5'd10, SCALE_WAIT = 5'd11,
      INT8_BEGIN = 5'd12, INT8_ADDRESS = 5'd13, INT8_SEND = 5'd14,
      INT8_WAIT = 5'd15, INT8_WORD = 5'd16,
      SPARSE_READ = 5'd17, SPARSE_CLASSIFY = 5'd18,
      WEIGHT_SEND = 5'd19, WEIGHT_WAIT = 5'd20, STREAM = 5'd21,
      FLUSH = 5'd22, MAC_WAIT = 5'd23, PANEL_RESULT = 5'd24,
      FAIL_DRAIN = 5'd25, COMPLETE = 5'd26;
    wire run_n;
    reg [4:0] state;
    reg [1:0] format;
    reg [3:0] slots;
    reg int8_weights, sparse, down_projection, finite_weights;
    reg failed, cancel_workers, reader_owned;
    reg [12:0] inputs, input_index, column, received_column, group_offset, group_index;
    reg [12:0] groups;
    reg [17:0] outputs, panel;
    reg [11:0] panels;
    reg [24:0] weight_units, metadata_units;
    reg [31:0] int8_entries;
    reg [31:0] weight_length, zero_length, scale_length, int8_scale_length;
    reg [31:0] required_weight, required_zero, required_scale, required_int8;
    reg [32:0] weight_base, zero_base, scale_base, int8_scale_base;
    reg [32:0] weight_address, zero_address, scale_address, panel_scale_base;
    reg [32:0] entry_address;
    reg [6:0] scale_row;
    reg [63:0] mask;
    reg [15:0] threshold;
    reg [255:0] zeros;
    reg [1023:0] scales;
    reg [2047:0] scales32;
    reg [8191:0] result_q;
    reg scale_cache_valid;
    reg [32:0] scale_cache_address;
    reg [511:0] scale_cache_data;
    (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
    reg [67:0] activations [0:MAX_INPUTS-1];
    reg [67:0] activation_q;
    reg raw_valid, raw_error, raw_skip, replay;
    reg [12:0] raw_column;
    reg [1023:0] raw_weights;
    reg [4:0] tag_valid;
    reg [76:0] tags [0:4];
    reg stats_pulse, replay_pulse;
    reg [31:0] dense_bytes, avoided_bytes, replay_bytes;
    reg input_bad, raw_bad, predicate_skip, original_nonzero, metadata_bad;
    integer slot_index, row_index, tag_index;
    wire quantized = int8_weights || format == 2;
    wire compact = quantized;
    wire fp16 = format == 1;
    wire [31:0] column_bytes = compact ? 32'd64 : 32'd128;
    wire [7:0] column_beats = compact ? 8'd1 : 8'd2;
    wire [17:0] remaining_rows = outputs - panel;
    wire [6:0] rows = remaining_rows >= 64 ? 7'd64 : remaining_rows[6:0];
    wire worker_rst_n = rst_n && !cancel_workers;
    wire final_column = raw_column + 1'b1 == inputs;
    wire group_end = group_offset + 1'b1 == GROUP_SIZE;
    wire [33:0] weight_end = {1'b0, weight_base} + {2'b0, required_weight};
    wire [33:0] zero_end = {1'b0, zero_base} + {2'b0, required_zero};
    wire [33:0] scale_end = {1'b0, scale_base} + {2'b0, required_scale};
    wire [33:0] int8_end = {1'b0, int8_scale_base} + {2'b0, required_int8};
    wire [31:0] cache_word = scale_cache_data[32*entry_address[5:2]+:32];
    wire cache_word_bad = cache_word[31] || cache_word[30:0] == 0 ||
      fp32_nonfinite(cache_word);
    wire cache_hit = scale_cache_valid &&
      scale_cache_address == {entry_address[32:6], 6'b0};
    wire [63:0] predicate_activation;
    wire r_ready, r_valid, r_error, r_dma_valid, r_dma_data_ready;
    wire [1023:0] r_data;
    wire [32:0] r_address;
    wire [7:0] r_beats;
    wire pf_ready, pf_valid, pf_out_ready, pf_busy, pf_error, pf_data_error;
    wire [1023:0] pf_data;
    wire [12:0] pf_column;
    wire pf_dma_valid, pf_dma_data_ready;
    wire [32:0] pf_address;
    wire [7:0] pf_beats;
    wire [3:0] local_ready, local_rsp_valid;
    wire [511:0] local_rsp_data;
    wire local_rsp_error, local_busy, local_fault;
    wire [63:0] dq_ready, dq_valid, dq_error;
    wire [1023:0] dq_weights;
    wire [2047:0] dq_native;
    wire mac_ready, mac_valid, mac_error;
    wire [8191:0] mac_data;
    wire [63:0] mac_mask;
    wire [3:0] mac_slots;
    wire raw_sink_ready = quantized ? (&dq_ready) : mac_ready;
    wire raw_transfer = state == STREAM && raw_valid && raw_sink_ready &&
      !raw_bad && !abort_error;
    wire dq_result = quantized && (&dq_valid) && tag_valid[4];
    wire dq_bad = dq_result && (|(dq_error & mask));
    wire mac_input_valid = run_n && !abort_error && !cancel_workers &&
      (quantized ? dq_result && !dq_bad : state == STREAM && raw_valid && !raw_bad);
    wire mac_input_transfer = mac_input_valid && mac_ready;
    wire [12:0] mac_column = quantized ? tags[4][76:64] : raw_column;
    wire pf_transfer = pf_valid && pf_out_ready;
    wire reader_command = run_n && !abort_error &&
      (state == ZERO_SEND || state == SCALE_SEND || state == INT8_SEND ||
       state == WEIGHT_SEND);
    wire reader_transfer = reader_command && r_ready;
    wire reader_response = r_valid && (state == ZERO_WAIT || state == SCALE_WAIT ||
      state == INT8_WAIT || state == WEIGHT_WAIT || state == FAIL_DRAIN);
    wire [32:0] reader_address = state == ZERO_SEND ? zero_address :
      state == SCALE_SEND ? scale_address : state == INT8_SEND ?
      {entry_address[32:6], 6'b0} : weight_address;
    wire [7:0] reader_beats = state == SCALE_SEND ? 8'd2 :
      state == WEIGHT_SEND ? column_beats : 8'd1;
    wire input_transfer = activation_valid && activation_ready;

    anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
    assign cmd_ready = run_n && state == IDLE && !abort_error;
    assign activation_ready = run_n && state == INPUT_FILL && !abort_error;
    assign result_valid = run_n && state == PANEL_RESULT;
    assign result_panel = result_valid ? {14'b0, panel} : 32'b0;
    assign result_data = result_valid ? result_q : 8192'b0;
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
    assign pf_out_ready = run_n && ((state == STREAM && !sparse &&
      (!raw_valid || raw_sink_ready) &&
      !(raw_valid && (final_column || (quantized && group_end))) &&
      !raw_bad && !abort_error) || state == FAIL_DRAIN);

    always @* begin
      input_bad = 0;
      raw_bad = raw_error;
      predicate_skip = 1;
      original_nonzero = 0;
      metadata_bad = 0;
      for (slot_index = 0; slot_index < 4; slot_index = slot_index + 1) begin
        if (slots[slot_index]) begin
          if ((fp16 && activation_data[16*slot_index+10+:5] == 5'h1f) ||
              (!fp16 && activation_data[16*slot_index+7+:8] == 8'hff)) input_bad = 1;
          if (predicate_activation[16*slot_index+:15] > threshold[14:0])
            predicate_skip = 0;
          if (activation_q[16*slot_index+:15] != 0 ||
              activation_q[64+slot_index]) original_nonzero = 1;
        end
      end
      for (row_index = 0; row_index < 64; row_index = row_index + 1) begin
        if (mask[row_index]) begin
          if (!quantized && !raw_skip &&
              ((fp16 && raw_weights[16*row_index+10+:5] == 5'h1f) ||
               (!fp16 && raw_weights[16*row_index+7+:8] == 8'hff))) raw_bad = 1;
          if (!int8_weights && format == 2 &&
              (scales[16*row_index+10+:5] == 5'h1f ||
               (scales[16*row_index+15] && scales[16*row_index+:15] != 0)))
            metadata_bad = 1;
        end
      end
    end
    for (genvar s = 0; s < 4; s = s + 1) begin: g_predicate
      wire [31:0] expanded = expand16(activation_q[16*s+:16], 1'b1);
      assign predicate_activation[16*s+:16] = fp16 ?
        narrow32(expanded, 1'b0) : activation_q[16*s+:16];
    end
    for (genvar lane = 0; lane < 64; lane = lane + 1) begin: g_dequant
      wire participating = mask[lane] && !raw_skip;
      anvil_q1_ht3_dequant u_dequant (
        .clk(clk), .rst_n(worker_rst_n),
        .in_valid(quantized && raw_transfer), .in_ready(dq_ready[lane]),
        .in_int8(int8_weights),
        .in_qweight(!participating ? 32'b0 : int8_weights ?
          {24'b0, raw_weights[8*lane+:8]} : raw_weights[32*(lane >> 3)+:32]),
        .in_qzero(participating ? zeros[32*(lane >> 3)+:32] : 32'b0),
        .in_lane(3'(lane & 7)),
        .in_scale(participating ? scales[16*lane+:16] : 16'b0),
        .in_scale_fp32(participating ? scales32[32*lane+:32] : 32'h3f800000),
        .out_valid(dq_valid[lane]), .out_ready(mac_ready && !cancel_workers),
        .out_data(dq_native[32*lane+:32]), .out_weight(dq_weights[16*lane+:16]),
        .out_error(dq_error[lane])
      );
    end
    anvil_q1_ht3_tensor_array u_tensor_array (
      .clk(clk), .rst_n(worker_rst_n), .in_valid(mac_input_valid), .in_ready(mac_ready),
      .in_first(mac_column == 0), .in_last(mac_column + 1'b1 == inputs),
      .in_fp16(fp16), .in_slots(slots), .in_mask(mask),
      .in_activation(quantized ? tags[4][63:0] : activation_q[63:0]),
      .in_weights(quantized ? dq_weights : raw_skip ? 1024'b0 : raw_weights),
      .in_weight_fp32(int8_weights), .in_weights_fp32(dq_native),
      .out_valid(mac_valid), .out_ready(state == MAC_WAIT),
      .out_data(mac_data), .out_mask(mac_mask), .out_slots(mac_slots),
      .out_error(mac_error)
    );
    anvil_q1_ht3_panel_prefetch #(.TILE_BEATS(TILE_BEATS)) u_prefetch (
      .clk(clk), .rst_n(rst_n),
      .abort_error(abort_error || state == FAIL_DRAIN),
      .cmd_valid(state == PREFETCH_BEGIN && !abort_error), .cmd_ready(pf_ready),
      .cmd_address(weight_address), .cmd_columns(inputs), .cmd_compact(compact),
      .out_valid(pf_valid), .out_ready(pf_out_ready), .out_data(pf_data),
      .out_column(pf_column), .out_error(pf_data_error), .busy(pf_busy),
      .done(), .error(pf_error),
      .mem_valid(pf_dma_valid), .mem_ready(local_ready[1]),
      .mem_address(pf_address), .mem_burstcount(pf_beats),
      .mem_data_valid(local_rsp_valid[1]), .mem_data_ready(pf_dma_data_ready),
      .mem_data(local_rsp_data), .mem_error(local_rsp_error)
    );
    anvil_q1_ht3_burst_reader u_reader (
      .clk(clk), .rst_n(rst_n), .cmd_valid(reader_command), .cmd_ready(r_ready),
      .cmd_address(reader_address), .cmd_burstcount(reader_beats),
      .mem_valid(r_dma_valid), .mem_ready(local_ready[0]),
      .mem_address(r_address), .mem_burstcount(r_beats),
      .mem_data_valid(local_rsp_valid[0]), .mem_data_ready(r_dma_data_ready),
      .mem_data(local_rsp_data), .mem_error(local_rsp_error),
      .rsp_valid(r_valid), .rsp_ready(state == ZERO_WAIT || state == SCALE_WAIT ||
        state == INT8_WAIT || state == WEIGHT_WAIT || state == FAIL_DRAIN),
      .rsp_data(r_data), .rsp_error(r_error)
    );
    anvil_q1_ht3_dma_mux #(.CHECK_RESPONSE_LAST(0)) u_memory (
      .clk(clk), .rst_n(rst_n), .client_valid({2'b0, pf_dma_valid, r_dma_valid}),
      .client_ready(local_ready), .client_write(4'b0),
      .client_address({66'b0, pf_address, r_address}),
      .client_burstcount({16'b0, pf_beats, r_beats}),
      .client_writedata(2048'b0), .client_byteenable(256'b0),
      .client_rsp_valid(local_rsp_valid),
      .client_rsp_ready({2'b0, pf_dma_data_ready, r_dma_data_ready}),
      .client_rsp_data(local_rsp_data), .client_rsp_error(local_rsp_error),
      .busy(local_busy), .protocol_error(local_fault),
      .req_valid(dma_valid), .req_ready(dma_ready), .req_write(),
      .req_address(dma_address), .req_burstcount(dma_burstcount),
      .req_writedata(), .req_byteenable(),
      .rsp_valid(dma_data_valid), .rsp_ready(dma_data_ready),
      .rsp_write(1'b0), .rsp_last(1'b0), .rsp_error(dma_error), .rsp_data(dma_data)
    );
    always @(posedge clk) begin
      if (run_n) begin
        if (input_transfer && !input_bad)
          activations[input_index] <= {activation_nonzero, activation_data};
        if (pf_transfer) activation_q <= activations[pf_column];
        if (state == SPARSE_READ) activation_q <= activations[column];
        if (quantized && (&dq_ready)) begin
          tags[0] <= {raw_column, activation_q[63:0]};
          for (tag_index = 1; tag_index < 5; tag_index = tag_index + 1)
            tags[tag_index] <= tags[tag_index-1];
        end
      end
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) tag_valid <= 0;
      else if (cancel_workers) tag_valid <= 0;
      else if (run_n && quantized && (&dq_ready))
        tag_valid <= {tag_valid[3:0], raw_transfer};
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        format <= 0;
        slots <= 0;
        int8_weights <= 0;
        sparse <= 0;
        down_projection <= 0;
        finite_weights <= 0;
        failed <= 0;
        cancel_workers <= 0;
        reader_owned <= 0;
        inputs <= 0;
        input_index <= 0;
        column <= 0;
        received_column <= 0;
        group_offset <= 0;
        group_index <= 0;
        groups <= 0;
        outputs <= 0;
        panel <= 0;
        panels <= 0;
        weight_units <= 0;
        metadata_units <= 0;
        int8_entries <= 0;
        weight_length <= 0;
        zero_length <= 0;
        scale_length <= 0;
        int8_scale_length <= 0;
        required_weight <= 0;
        required_zero <= 0;
        required_scale <= 0;
        required_int8 <= 0;
        weight_base <= 0;
        zero_base <= 0;
        scale_base <= 0;
        int8_scale_base <= 0;
        weight_address <= 0;
        zero_address <= 0;
        scale_address <= 0;
        panel_scale_base <= 0;
        entry_address <= 0;
        scale_row <= 0;
        mask <= 0;
        threshold <= 0;
        zeros <= 0;
        scales <= 0;
        scales32 <= 0;
        result_q <= 0;
        scale_cache_valid <= 0;
        scale_cache_address <= 0;
        scale_cache_data <= 0;
        raw_valid <= 0;
        raw_error <= 0;
        raw_skip <= 0;
        replay <= 0;
        raw_column <= 0;
        raw_weights <= 0;
        stats_pulse <= 0;
        replay_pulse <= 0;
        dense_bytes <= 0;
        avoided_bytes <= 0;
        replay_bytes <= 0;
      end else if (run_n) begin
        stats_pulse <= 0;
        replay_pulse <= 0;
        dense_bytes <= 0;
        avoided_bytes <= 0;
        replay_bytes <= 0;
        if (reader_transfer) reader_owned <= 1;
        if (reader_response) reader_owned <= 0;
        if ((abort_error || local_fault || dq_bad || pf_error) &&
            state != IDLE && state != COMPLETE && state != FAIL_DRAIN &&
            state != PANEL_RESULT) begin
          failed <= 1;
          cancel_workers <= 1;
          raw_valid <= 0;
          state <= FAIL_DRAIN;
        end else case (state)
          IDLE: begin
            cancel_workers <= 0;
            if (cmd_valid && cmd_ready) begin
              format <= cmd_format;
              slots <= cmd_slots;
              int8_weights <= cmd_int8_weights;
              sparse <= cmd_sparse && cmd_down_projection;
              down_projection <= cmd_down_projection;
              finite_weights <= cmd_finite_weights;
              threshold <= cmd_threshold;
              inputs <= cmd_inputs[12:0];
              outputs <= cmd_outputs[17:0];
              panels <= 12'((cmd_outputs + 63) >> 6);
              groups <= cmd_inputs == INTERMEDIATE_SIZE ? 13'(IG) : 13'(HG);
              weight_base <= cmd_weight_base;
              zero_base <= cmd_zero_base;
              scale_base <= cmd_scale_base;
              int8_scale_base <= cmd_int8_scale_base;
              weight_address <= cmd_weight_base;
              zero_address <= cmd_zero_base;
              scale_address <= cmd_scale_base;
              panel_scale_base <= cmd_int8_scale_base;
              weight_length <= cmd_weight_length;
              zero_length <= cmd_zero_length;
              scale_length <= cmd_scale_length;
              int8_scale_length <= cmd_int8_scale_length;
              input_index <= 0;
              panel <= 0;
              scale_cache_valid <= 0;
              raw_valid <= 0;
              failed <= 0;
              if (cmd_format == 3 || cmd_slots == 0 ||
                  (cmd_inputs != HIDDEN_SIZE && cmd_inputs != INTERMEDIATE_SIZE) ||
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
            metadata_units <= groups * panels;
            int8_entries <= outputs * groups;
            state <= PREF_LENGTH;
          end
          PREF_LENGTH: begin
            required_weight <= compact ? {1'b0, weight_units, 6'b0} :
              {weight_units, 7'b0};
            required_zero <= {1'b0, metadata_units, 6'b0};
            required_scale <= {metadata_units, 7'b0};
            required_int8 <= int8_entries << 2;
            state <= PREF_CHECK;
          end
          PREF_CHECK: begin
            if (weight_length != required_weight || (|weight_base[5:0]) ||
                weight_end > 34'h200000000 ||
                (int8_weights && (int8_scale_length != required_int8 ||
                 (|int8_scale_base[1:0]) || int8_end > 34'h200000000)) ||
                (!int8_weights && format == 2 &&
                 (zero_length != required_zero || scale_length != required_scale ||
                  (|zero_base[5:0]) || (|scale_base[5:0]) ||
                  zero_end > 34'h200000000 || scale_end > 34'h200000000))) begin
              failed <= 1;
              state <= COMPLETE;
            end else state <= INPUT_FILL;
          end
          INPUT_FILL: if (input_transfer) begin
            if (input_bad) begin failed <= 1; state <= COMPLETE; end
            else if (input_index + 1'b1 == inputs) state <= PANEL_BEGIN;
            else input_index <= input_index + 1'b1;
          end
          PANEL_BEGIN: begin
            mask <= remaining_rows >= 64 ? 64'hffffffffffffffff :
              64'hffffffffffffffff >> (64-remaining_rows);
            column <= 0;
            received_column <= 0;
            group_offset <= 0;
            group_index <= 0;
            raw_valid <= 0;
            if (sparse) state <= META_BEGIN;
            else state <= PREFETCH_BEGIN;
          end
          PREFETCH_BEGIN: if (pf_ready) state <= META_BEGIN;
          META_BEGIN: begin
            if (int8_weights) state <= INT8_BEGIN;
            else if (format == 2) state <= ZERO_SEND;
            else if (sparse) state <= SPARSE_READ;
            else state <= STREAM;
          end
          ZERO_SEND: if (reader_transfer) state <= ZERO_WAIT;
          ZERO_WAIT: if (reader_response) begin
            if (r_error) begin failed <= 1; cancel_workers <= 1; state <= FAIL_DRAIN; end
            else begin
              zeros <= r_data[255:0];
              zero_address <= zero_address + 33'd64;
              state <= SCALE_SEND;
            end
          end
          SCALE_SEND: if (reader_transfer) state <= SCALE_WAIT;
          SCALE_WAIT: if (reader_response) begin
            if (r_error) begin failed <= 1; cancel_workers <= 1; state <= FAIL_DRAIN; end
            else begin
              scales <= r_data;
              scale_address <= scale_address + 33'd128;
              state <= INT8_ADDRESS;
            end
          end
          INT8_BEGIN: begin
            scale_row <= 0;
            entry_address <= panel_scale_base + {18'b0, group_index, 2'b0};
            state <= INT8_ADDRESS;
          end
          INT8_ADDRESS: begin
            if (!int8_weights) begin
              if (metadata_bad) begin
                failed <= 1; cancel_workers <= 1; state <= FAIL_DRAIN;
              end else if (sparse) state <= SPARSE_READ;
              else state <= STREAM;
            end else if (cache_hit) state <= INT8_WORD;
            else state <= INT8_SEND;
          end
          INT8_SEND: if (reader_transfer) state <= INT8_WAIT;
          INT8_WAIT: if (reader_response) begin
            if (r_error) begin failed <= 1; cancel_workers <= 1; state <= FAIL_DRAIN; end
            else begin
              scale_cache_valid <= 1;
              scale_cache_address <= {entry_address[32:6], 6'b0};
              scale_cache_data <= r_data[511:0];
              state <= INT8_WORD;
            end
          end
          INT8_WORD: begin
            if (cache_word_bad) begin
              failed <= 1; cancel_workers <= 1; state <= FAIL_DRAIN;
            end else begin
              scales32[32*scale_row+:32] <= cache_word;
              if (scale_row + 1'b1 == rows) begin
                if (sparse) state <= SPARSE_READ;
                else state <= STREAM;
              end else begin
                scale_row <= scale_row + 1'b1;
                entry_address <= entry_address + {18'b0, groups, 2'b0};
                state <= INT8_ADDRESS;
              end
            end
          end
          SPARSE_READ: state <= SPARSE_CLASSIFY;
          SPARSE_CLASSIFY: begin
            replay <= predicate_skip && (original_nonzero || !finite_weights);
            raw_column <= column;
            raw_error <= 0;
            stats_pulse <= down_projection;
            dense_bytes <= column_bytes;
            if (predicate_skip && !original_nonzero && finite_weights) begin
              raw_weights <= 0;
              raw_skip <= 1;
              raw_valid <= 1;
              avoided_bytes <= column_bytes;
              state <= STREAM;
            end else begin raw_skip <= 0; state <= WEIGHT_SEND; end
          end
          WEIGHT_SEND: if (reader_transfer) begin
            if (replay) begin
              stats_pulse <= down_projection;
              replay_pulse <= 1;
              replay_bytes <= column_bytes;
            end
            state <= WEIGHT_WAIT;
          end
          WEIGHT_WAIT: if (reader_response) begin
            if (r_error) begin failed <= 1; cancel_workers <= 1; state <= FAIL_DRAIN; end
            else begin
              raw_weights <= r_data;
              raw_valid <= 1;
              state <= STREAM;
            end
          end
          STREAM: begin
            if (raw_valid && raw_bad) begin
              failed <= 1;
              cancel_workers <= 1;
              raw_valid <= 0;
              state <= FAIL_DRAIN;
            end else begin
              if (raw_transfer) begin
                raw_valid <= 0;
                weight_address <= weight_address + {1'b0, column_bytes};
                column <= column + 1'b1;
                if (!sparse && down_projection) begin
                  stats_pulse <= 1;
                  dense_bytes <= column_bytes;
                end
                if (final_column) begin
                  if (quantized) state <= FLUSH;
                  else state <= MAC_WAIT;
                end else if (group_end) begin
                  group_offset <= 0;
                  group_index <= group_index + 1'b1;
                  if (quantized) state <= META_BEGIN;
                  else if (sparse) state <= SPARSE_READ;
                end else begin
                  group_offset <= group_offset + 1'b1;
                  if (sparse) state <= SPARSE_READ;
                end
              end
              if (pf_transfer) begin
                raw_weights <= pf_data;
                raw_column <= pf_column;
                raw_error <= pf_data_error || pf_column != received_column;
                raw_skip <= 0;
                raw_valid <= 1;
                received_column <= received_column + 1'b1;
              end
            end
          end
          FLUSH: if (mac_input_transfer && mac_column + 1'b1 == inputs) state <= MAC_WAIT;
          MAC_WAIT: if (mac_valid) begin
            if (mac_error || mac_slots != slots || mac_mask != mask) begin
              failed <= 1; cancel_workers <= 1; state <= FAIL_DRAIN;
            end else begin result_q <= mac_data; state <= PANEL_RESULT; end
          end
          PANEL_RESULT: begin
            if (abort_error || local_fault) failed <= 1;
            if (result_ready) begin
              if (failed || abort_error || local_fault) begin
                cancel_workers <= 1;
                state <= FAIL_DRAIN;
              end else if (panel + 18'd64 >= outputs) state <= COMPLETE;
              else begin
                panel <= panel + 18'd64;
                panel_scale_base <= panel_scale_base + {12'b0, groups, 8'b0};
                state <= PANEL_BEGIN;
              end
            end
          end
          FAIL_DRAIN: if ((!reader_owned || reader_response) && !pf_busy && !local_busy)
            state <= COMPLETE;
          COMPLETE: state <= IDLE;
          default: begin failed <= 1; cancel_workers <= 1; state <= FAIL_DRAIN; end
        endcase
      end
    end
  end endgenerate
endmodule
