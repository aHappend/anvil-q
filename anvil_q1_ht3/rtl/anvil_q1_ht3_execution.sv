module anvil_q1_ht3_execution #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2, HEAD_DIM = 64,
  parameter GROUP_SIZE = 128, VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768,
  parameter TILE_BEATS = 256, FLASH_TILE = 16
) (
  input wire clk, rst_n, new_sequence, invalidate_image, abort_error,
  input wire image_valid, finite_image,
  input wire [3:0] configuration,
  input wire [15:0] sparse_threshold,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire batch_valid,
  output wire batch_ready,
  input wire [2:0] batch_count,
  input wire [127:0] batch_token_ids,
  input wire [11:0] batch_parents,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index, logit_data,
  output wire commit_valid,
  input wire commit_ready,
  output wire [2:0] commit_count,
  output wire [127:0] commit_token_ids,
  output wire [31:0] commit_position,
  output wire commit_error,
  output wire busy, pending_results, done, error,
  output wire [2:0] accepted_tokens,
  output wire completed_batch,
  output wire [31:0] eligible_bytes, avoided_bytes,
  output wire lookup_valid,
  input wire lookup_ready,
  output wire [31:0] lookup_index,
  input wire lookup_rsp_valid,
  output wire lookup_rsp_ready,
  input wire [32:0] lookup_base,
  input wire [31:0] lookup_length,
  input wire lookup_error,
  output wire read_dma_valid,
  input wire read_dma_ready,
  output wire [32:0] read_dma_address,
  output wire [7:0] read_dma_burstcount,
  input wire read_dma_data_valid,
  output wire read_dma_data_ready,
  input wire [511:0] read_dma_data,
  input wire read_dma_error,
  output wire write_dma_valid,
  input wire write_dma_ready,
  output wire [32:0] write_dma_address,
  output wire [511:0] write_dma_data,
  output wire [63:0] write_dma_byteenable,
  input wire write_dma_rsp_valid,
  output wire write_dma_rsp_ready,
  input wire write_dma_error,
  input wire [1:0] kv_format,
  input wire int8_weights,
  input wire [32:0] extension_base,
  input wire [31:0] extension_length, image_generation
);
  import anvil_q1_ht3_layout_pkg::*;
  localparam LEGAL = geometry_legal(NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,
    NUM_Q_HEADS,NUM_KV_HEADS,HEAD_DIM,GROUP_SIZE,VOCAB_SIZE,MAX_SEQ_LEN) &&
    TILE_BEATS >= 1 && TILE_BEATS <= 256 && FLASH_TILE >= 1 && FLASH_TILE <= 128;
  initial if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 execution geometry");
  generate if (!LEGAL) begin: g_invalid
    assign token_ready = 0;
    assign batch_ready = 0;
    assign logit_valid = 0;
    assign logit_index = 0;
    assign logit_data = 0;
    assign commit_valid = 0;
    assign commit_count = 0;
    assign commit_token_ids = 0;
    assign commit_position = 0;
    assign commit_error = 0;
    assign busy = 0;
    assign pending_results = 0;
    assign done = 0;
    assign error = 0;
    assign accepted_tokens = 0;
    assign completed_batch = 0;
    assign eligible_bytes = 0;
    assign avoided_bytes = 0;
    assign lookup_valid = 0;
    assign lookup_index = 0;
    assign lookup_rsp_ready = 0;
    assign read_dma_valid = 0;
    assign read_dma_address = 0;
    assign read_dma_burstcount = 0;
    assign read_dma_data_ready = 0;
    assign write_dma_valid = 0;
    assign write_dma_address = 0;
    assign write_dma_data = 0;
    assign write_dma_byteenable = 0;
    assign write_dma_rsp_ready = 0;
  end else begin: g_legal
    localparam L = NUM_LAYERS, V = VOCAB_SIZE, S = MAX_SEQ_LEN;
    localparam C = NUM_KV_HEADS*HEAD_DIM;
    localparam NATIVE_KV_BYTES = S*((2*C+63) >> 6)*64;
    localparam INT4_KV_BYTES = S*((4*C+511) >> 9)*64;
    localparam INT8_KV_BYTES = S*((8*C+511) >> 9)*64;
    localparam IDLE = 5'd0, MASK_SEND = 5'd1, MASK_WAIT = 5'd2,
      KV_BEGIN = 5'd3, KV_SETTLE = 5'd4, DECODE_SEND = 5'd5,
      DECODE_WAIT = 5'd6, VERIFY_SEND = 5'd7, VERIFY_WAIT = 5'd8,
      COPY_SELECT = 5'd9, COPY_SEND = 5'd10, COPY_WAIT = 5'd11,
      LOGIT_READ = 5'd12, LOGIT_EMIT = 5'd13, COMMIT = 5'd14,
      FAULT = 5'd15, COMPLETE = 5'd16, DRAIN = 5'd17;
    localparam LM_IDLE = 2'd0, LM_COMMAND = 2'd1, LM_WAIT = 2'd2, LM_RESPONSE = 2'd3;
    localparam KC_IDLE = 3'd0, KC_KEY_SEND = 3'd1, KC_KEY_WAIT = 3'd2,
      KC_VALUE_SEND = 3'd3, KC_VALUE_WAIT = 3'd4;
    wire run_n;
    reg [4:0] state;
    reg is_batch, correction, need_correction, failed, prefix_valid;
    reg [31:0] prefix_length, prefix_target, reserved_length, next_target;
    reg [2:0] count, result_count;
    reg [3:0] slots, remaining_mask;
    reg [127:0] tokens, positions, node_targets, result_tokens;
    reg [15:0] ancestors;
    reg [11:0] parents;
    reg [1:0] copying_node;
    reg [4:0] copying_layer;
    reg copying_owned;
    reg [31:0] logit_write_index, emit_index, emit_word;
    reg [3:0] configuration_q;
    reg [15:0] threshold_q;
    reg [1:0] format_q;
    reg int8_q, finite_q, published_error;
    reg [32:0] extension_base_q;
    reg [31:0] extension_length_q, image_q, published_position;
    (* ramstyle = "M20K", nomem2reg *) reg [31:0] ordinary_logits [0:V-1];
    wire flush = new_sequence || invalidate_image;
    wire cancel = state == DRAIN || abort_error || flush || failed;
    wire command_accepted = (token_valid && token_ready) || (batch_valid && batch_ready);
    wire final_logit_transfer = logit_valid && logit_ready && emit_index + 1 == V;
    wire commit_transfer = commit_valid && commit_ready;
    wire [3:0] active_slots = correction ? 4'b0001 : slots;
    wire [1:0] correction_index = result_count == 0 ? 2'b0 : 2'(result_count-1'b1);
    wire [127:0] active_tokens = correction ?
      {96'b0,result_tokens[32*correction_index+:32]} : tokens;
    wire [127:0] active_positions = correction ? {96'b0,reserved_length} : positions;
    wire [15:0] active_ancestors = correction ? 16'h0001 : ancestors;
    wire [31:0] active_prefix_length = correction ? reserved_length : prefix_length;
    reg batch_bad, targets_bad, verifier_bad, selected_found;
    reg [2:0] selected_count;
    reg [1:0] selected_node;
    integer node;
    wire m_ready, m_valid, m_error;
    wire [127:0] m_positions;
    wire [15:0] m_ancestors;
    wire v_ready, v_valid, v_error;
    wire [2:0] v_count;
    wire [127:0] v_tokens;
    wire [3:0] v_mask;
    wire d_ready, d_valid, d_error, d_busy, d_done;
    wire [127:0] d_targets;
    wire d_logit_valid, d_logit_ready;
    wire [31:0] d_logit_index;
    wire [127:0] d_logit_data;
    wire [3:0] d_logit_slots;
    wire d_stats_valid;
    wire [31:0] d_dense_bytes, d_avoided_bytes;
    wire d_lookup_valid, d_lookup_ready, d_lookup_rsp_valid, d_lookup_rsp_ready;
    wire [31:0] d_lookup_index;
    wire d_read_valid, d_read_ready, d_read_data_ready;
    wire [32:0] d_read_address;
    wire [7:0] d_read_beats;
    wire d_store_valid, d_store_ready, d_store_first, d_store_last, k_store_error;
    wire [1:0] d_store_node, d_store_format;
    wire [31:0] d_store_layer, d_store_column, d_store_image;
    wire d_store_fault;
    wire [15:0] d_store_key, d_store_value;
    wire d_kv_valid, d_kv_ready, d_kv_provisional;
    wire [1:0] d_kv_node;
    wire [31:0] d_kv_layer, d_kv_position, d_kv_head, d_kv_column;
    wire [31:0] d_kv_key_scale, d_kv_value_scale, k_key_scale, k_value_scale;
    wire d_kv_rsp_valid, d_kv_rsp_ready, d_kv_error;
    wire [15:0] d_kv_key, d_kv_value;
    wire k_begin_ready, k_begin_error, k_read_ready, k_copy_ready;
    wire k_copy_valid, k_copy_rsp_valid, k_copy_rsp_error;
    wire k_read_valid, k_read_dma_ready, k_read_data_ready;
    wire [32:0] k_read_address;
    wire [7:0] k_read_beats;
    wire [3:0] read_client_ready, read_client_valid;
    wire [511:0] read_client_data;
    wire read_client_error, read_busy, read_fault;
    reg [1:0] lookup_state;
    reg lookup_owner;
    reg [31:0] held_lookup_index, held_lookup_length;
    reg [32:0] held_lookup_base;
    reg held_lookup_error;
    reg [2:0] cache_state;
    reg cache_valid, cache_error;
    reg [31:0] cache_layer;
    reg [32:0] cache_key_base, cache_value_base;
    reg [31:0] cache_key_length, cache_value_length;
    wire [31:0] wanted_layer = state == COPY_SEND ? {27'b0,copying_layer} : d_kv_layer;
    wire wants_cache = state == COPY_SEND || d_kv_valid;
    wire cache_match = cache_valid && cache_layer == wanted_layer;
    wire c_lookup_valid = run_n && !cancel &&
      (cache_state == KC_KEY_SEND || cache_state == KC_VALUE_SEND);
    wire c_lookup_ready = run_n && lookup_state == LM_IDLE && !d_lookup_valid;
    wire c_lookup_rsp_valid = run_n && lookup_state == LM_RESPONSE && lookup_owner;
    wire c_lookup_rsp_ready = cache_state == KC_KEY_WAIT || cache_state == KC_VALUE_WAIT;
    wire [31:0] c_lookup_index = cache_layer*96 +
      (cache_state == KC_KEY_SEND ? 32'd72 : 32'd80);
    wire [31:0] expected_kv_bytes = format_q == 2 ? INT4_KV_BYTES :
      format_q == 3 ? INT8_KV_BYTES : NATIVE_KV_BYTES;
    wire [33:0] cached_lookup_end = {1'b0,held_lookup_base} + {2'b0,held_lookup_length};
    wire [33:0] cache_key_end = {1'b0,cache_key_base} + {2'b0,cache_key_length};
    wire cached_lookup_bad = held_lookup_error || held_lookup_length != expected_kv_bytes ||
      (|held_lookup_base[5:0]) || cached_lookup_end > 34'h200000000 ||
      (cache_state == KC_VALUE_WAIT && {1'b0,held_lookup_base} < cache_key_end &&
       {1'b0,cache_key_base} < cached_lookup_end);
    wire lookup_completion = lookup_rsp_valid &&
      (lookup_state == LM_WAIT || (lookup_state == LM_COMMAND && lookup_ready));
    wire failure_event = abort_error || flush || k_begin_error || k_store_error ||
      cache_error || read_fault;

    anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
    always @* begin
      batch_bad = batch_count == 0 || batch_count > 4 || !configuration[2] ||
        !prefix_valid || prefix_length >= S;
      targets_bad = 0;
      verifier_bad = v_error || v_count == 0 || v_count > 4 ||
        {1'b0,prefix_length} + {30'b0,v_count} > S;
      selected_count = 0;
      selected_found = 0;
      selected_node = 0;
      for (node = 0; node < 4; node = node + 1) begin
        if (node < batch_count && batch_token_ids[32*node+:32] >= V) batch_bad = 1;
        if (active_slots[node] && d_targets[32*node+:32] >= V) targets_bad = 1;
        if (v_mask[node]) selected_count = selected_count + 1'b1;
        if (node < v_count && v_tokens[32*node+:32] >= V) verifier_bad = 1;
        if (v_mask[node] && !slots[node]) verifier_bad = 1;
        if (!selected_found && remaining_mask[node]) begin
          selected_found = 1;
          selected_node = node[1:0];
        end
      end
      if (selected_count > v_count ||
          (selected_count != v_count && selected_count + 1'b1 != v_count)) verifier_bad = 1;
    end
    anvil_q1_ht3_tree_mask #(.MAX_SEQ_LEN(S)) u_tree (
      .clk(clk), .rst_n(rst_n), .req_valid(run_n && state == MASK_SEND && !cancel),
      .req_ready(m_ready), .req_prefix_valid(prefix_valid),
      .req_prefix_position(prefix_length-1'b1), .req_count(count), .req_parents(parents),
      .rsp_valid(m_valid), .rsp_ready(state == MASK_WAIT || state == DRAIN),
      .rsp_positions(m_positions), .rsp_ancestors(m_ancestors), .rsp_error(m_error)
    );
    anvil_q1_ht3_spec_verifier u_branch_select (
      .clk(clk), .rst_n(rst_n), .in_valid(run_n && state == VERIFY_SEND && !cancel),
      .in_ready(v_ready), .in_count(count), .in_draft_tokens(tokens),
      .in_target_tokens(node_targets), .in_parents(parents), .in_prefix_target(prefix_target),
      .out_valid(v_valid), .out_ready(state == VERIFY_WAIT || state == DRAIN),
      .out_count(v_count), .out_tokens(v_tokens), .out_commit_mask(v_mask), .out_error(v_error)
    );
    anvil_q1_ht3_decoder #(
      .NUM_LAYERS(NUM_LAYERS), .HIDDEN_SIZE(HIDDEN_SIZE),
      .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE), .NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS), .HEAD_DIM(HEAD_DIM), .GROUP_SIZE(GROUP_SIZE),
      .VOCAB_SIZE(V), .MAX_SEQ_LEN(S), .TILE_BEATS(TILE_BEATS), .FLASH_TILE(FLASH_TILE)
    ) u_decoder (
      .clk(clk), .rst_n(rst_n), .abort_error(cancel),
      .cmd_valid(run_n && state == DECODE_SEND && !cancel), .cmd_ready(d_ready),
      .cmd_format(configuration_q[1:0]), .cmd_slots(active_slots), .cmd_tokens(active_tokens),
      .cmd_positions(active_positions), .cmd_ancestors(active_ancestors),
      .cmd_prefix_length(active_prefix_length), .cmd_emit_logits(!is_batch),
      .cmd_sparse(configuration_q[3]), .cmd_finite_weights(finite_q), .cmd_threshold(threshold_q),
      .cmd_kv_format(format_q), .cmd_int8_weights(int8_q),
      .cmd_extension_base(extension_base_q), .cmd_extension_length(extension_length_q),
      .cmd_image(image_q),
      .lookup_valid(d_lookup_valid), .lookup_ready(d_lookup_ready),
      .lookup_index(d_lookup_index), .lookup_rsp_valid(d_lookup_rsp_valid),
      .lookup_rsp_ready(d_lookup_rsp_ready), .lookup_base(held_lookup_base),
      .lookup_length(held_lookup_length), .lookup_error(held_lookup_error),
      .dma_valid(d_read_valid), .dma_ready(d_read_ready), .dma_address(d_read_address),
      .dma_burstcount(d_read_beats), .dma_data_valid(read_client_valid[0]),
      .dma_data_ready(d_read_data_ready), .dma_data(read_client_data), .dma_error(read_client_error),
      .kv_store_valid(d_store_valid), .kv_store_ready(d_store_ready),
      .kv_store_node(d_store_node), .kv_store_layer(d_store_layer),
      .kv_store_column(d_store_column), .kv_store_first(d_store_first), .kv_store_last(d_store_last),
      .kv_store_key(d_store_key), .kv_store_value(d_store_value), .kv_store_error(k_store_error),
      .kv_store_format(d_store_format), .kv_store_image(d_store_image), .kv_store_fault(d_store_fault),
      .kv_read_valid(d_kv_valid), .kv_read_ready(d_kv_ready),
      .kv_read_provisional(d_kv_provisional), .kv_read_node(d_kv_node),
      .kv_read_layer(d_kv_layer), .kv_read_position(d_kv_position),
      .kv_read_head(d_kv_head), .kv_read_column(d_kv_column),
      .kv_read_key_scale(d_kv_key_scale), .kv_read_value_scale(d_kv_value_scale),
      .kv_rsp_valid(d_kv_rsp_valid), .kv_rsp_ready(d_kv_rsp_ready),
      .kv_key(d_kv_key), .kv_value(d_kv_value), .kv_rsp_error(d_kv_error),
      .kv_key_scale(k_key_scale), .kv_value_scale(k_value_scale),
      .logit_valid(d_logit_valid), .logit_ready(d_logit_ready), .logit_index(d_logit_index),
      .logit_data(d_logit_data), .logit_slots(d_logit_slots),
      .rsp_valid(d_valid), .rsp_ready(state == DECODE_WAIT || state == DRAIN),
      .rsp_targets(d_targets), .rsp_error(d_error), .busy(d_busy), .done(d_done),
      .stats_valid(d_stats_valid), .stats_dense_bytes(d_dense_bytes),
      .stats_avoided_bytes(d_avoided_bytes), .stats_replay_bytes(), .stats_replay_column()
    );
    anvil_q1_ht3_kv #(
      .NUM_LAYERS(L), .NUM_KV_HEADS(NUM_KV_HEADS), .HEAD_DIM(HEAD_DIM), .MAX_SEQ_LEN(S)
    ) u_kv (
      .clk(clk), .rst_n(rst_n), .flush(flush), .abort_error(cancel),
      .cmd_valid(run_n && state == KV_BEGIN && !cancel), .cmd_ready(k_begin_ready),
      .cmd_begin(1'b1), .cmd_slots(active_slots), .cmd_error(k_begin_error),
      .cmd_kv_format(format_q), .cmd_image(image_q),
      .store_valid(d_store_valid), .store_ready(d_store_ready),
      .store_node(d_store_node), .store_layer(d_store_layer), .store_column(d_store_column),
      .store_first(d_store_first), .store_last(d_store_last),
      .store_key(d_store_key), .store_value(d_store_value), .store_error(k_store_error),
      .store_format(d_store_format), .store_image(d_store_image), .store_fault(d_store_fault),
      .read_valid(d_kv_valid && cache_match && !cancel), .read_ready(k_read_ready),
      .read_provisional(d_kv_provisional), .read_fp16(format_q == 1),
      .read_node(d_kv_node), .read_layer(d_kv_layer), .read_head(d_kv_head),
      .read_column(d_kv_column), .read_position(d_kv_position),
      .read_prefix_length(active_prefix_length), .read_kv_format(format_q), .read_image(image_q),
      .read_key_scale(d_kv_key_scale), .read_value_scale(d_kv_value_scale),
      .read_key_base(cache_key_base), .read_value_base(cache_value_base),
      .read_key_length(cache_key_length), .read_value_length(cache_value_length),
      .read_rsp_valid(d_kv_rsp_valid), .read_rsp_ready(d_kv_rsp_ready),
      .read_rsp_key(d_kv_key), .read_rsp_value(d_kv_value), .read_rsp_error(d_kv_error),
      .read_rsp_key_scale(k_key_scale), .read_rsp_value_scale(k_value_scale),
      .copy_valid(k_copy_valid), .copy_ready(k_copy_ready),
      .copy_fp16(format_q == 1), .copy_node(copying_node),
      .copy_layer({27'b0,copying_layer}), .copy_position(reserved_length),
      .copy_prefix_length(reserved_length), .copy_kv_format(format_q), .copy_image(image_q),
      .copy_key_base(cache_key_base), .copy_value_base(cache_value_base),
      .copy_key_length(cache_key_length), .copy_value_length(cache_value_length),
      .copy_rsp_valid(k_copy_rsp_valid), .copy_rsp_ready(state == COPY_WAIT || state == DRAIN),
      .copy_rsp_error(k_copy_rsp_error),
      .read_dma_valid(k_read_valid), .read_dma_ready(k_read_dma_ready),
      .read_dma_address(k_read_address), .read_dma_burstcount(k_read_beats),
      .read_dma_data_valid(read_client_valid[1]), .read_dma_data_ready(k_read_data_ready),
      .read_dma_data(read_client_data), .read_dma_error(read_client_error),
      .write_dma_valid(write_dma_valid), .write_dma_ready(write_dma_ready),
      .write_dma_address(write_dma_address), .write_dma_data(write_dma_data),
      .write_dma_byteenable(write_dma_byteenable), .write_dma_rsp_valid(write_dma_rsp_valid),
      .write_dma_rsp_ready(write_dma_rsp_ready), .write_dma_error(write_dma_error)
    );
    anvil_q1_ht3_dma_mux #(.CHECK_RESPONSE_LAST(0)) u_read_arbiter (
      .clk(clk), .rst_n(rst_n), .client_valid({2'b0,k_read_valid,d_read_valid}),
      .client_ready(read_client_ready), .client_write(4'b0),
      .client_address({66'b0,k_read_address,d_read_address}),
      .client_burstcount({16'b0,k_read_beats,d_read_beats}),
      .client_writedata(2048'b0), .client_byteenable(256'b0),
      .client_rsp_valid(read_client_valid),
      .client_rsp_ready({2'b0,k_read_data_ready,d_read_data_ready}),
      .client_rsp_data(read_client_data), .client_rsp_error(read_client_error),
      .busy(read_busy), .protocol_error(read_fault),
      .req_valid(read_dma_valid), .req_ready(read_dma_ready), .req_write(),
      .req_address(read_dma_address), .req_burstcount(read_dma_burstcount),
      .req_writedata(), .req_byteenable(), .rsp_valid(read_dma_data_valid),
      .rsp_ready(read_dma_data_ready), .rsp_write(1'b0), .rsp_last(1'b0),
      .rsp_error(read_dma_error), .rsp_data(read_dma_data)
    );
    assign d_read_ready = read_client_ready[0];
    assign k_read_dma_ready = read_client_ready[1];
    assign d_kv_ready = run_n && !cancel && cache_match && k_read_ready;
    assign k_copy_valid = run_n && state == COPY_SEND && cache_match && !cancel;
    assign d_logit_ready = run_n && (state == DECODE_WAIT || state == DRAIN);
    assign d_lookup_ready = run_n && lookup_state == LM_IDLE;
    assign d_lookup_rsp_valid = run_n && lookup_state == LM_RESPONSE && !lookup_owner;
    assign lookup_valid = run_n && lookup_state == LM_COMMAND;
    assign lookup_index = lookup_valid ? held_lookup_index : 32'b0;
    assign lookup_rsp_ready = run_n &&
      (lookup_state == LM_WAIT || (lookup_valid && lookup_ready));

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        lookup_state <= LM_IDLE;
        lookup_owner <= 0;
        held_lookup_index <= 0;
        held_lookup_base <= 0;
        held_lookup_length <= 0;
        held_lookup_error <= 0;
      end else if (run_n) case (lookup_state)
        LM_IDLE: if (d_lookup_valid || c_lookup_valid) begin
          lookup_owner <= !d_lookup_valid;
          held_lookup_index <= d_lookup_valid ? d_lookup_index : c_lookup_index;
          lookup_state <= LM_COMMAND;
        end
        LM_COMMAND: if (lookup_ready) begin
          if (lookup_completion) begin
            held_lookup_base <= lookup_base;
            held_lookup_length <= lookup_length;
            held_lookup_error <= lookup_error;
            lookup_state <= LM_RESPONSE;
          end else lookup_state <= LM_WAIT;
        end
        LM_WAIT: if (lookup_completion) begin
          held_lookup_base <= lookup_base;
          held_lookup_length <= lookup_length;
          held_lookup_error <= lookup_error;
          lookup_state <= LM_RESPONSE;
        end
        LM_RESPONSE: if (lookup_owner ? c_lookup_rsp_ready : d_lookup_rsp_ready)
          lookup_state <= LM_IDLE;
        default: lookup_state <= LM_IDLE;
      endcase
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        cache_state <= KC_IDLE;
        cache_valid <= 0;
        cache_error <= 0;
        cache_layer <= 0;
        cache_key_base <= 0;
        cache_value_base <= 0;
        cache_key_length <= 0;
        cache_value_length <= 0;
      end else if (run_n) begin
        cache_error <= 0;
        if (flush || state == IDLE || cancel) cache_valid <= 0;
        case (cache_state)
          KC_IDLE: if (wants_cache && !cache_match && !cancel) begin
            cache_layer <= wanted_layer;
            cache_valid <= 0;
            cache_state <= KC_KEY_SEND;
          end
          KC_KEY_SEND: begin
            if (cancel) cache_state <= KC_IDLE;
            else if (c_lookup_valid && c_lookup_ready) cache_state <= KC_KEY_WAIT;
          end
          KC_KEY_WAIT: if (c_lookup_rsp_valid) begin
            if (cached_lookup_bad || cancel) begin
              cache_error <= cached_lookup_bad;
              cache_state <= KC_IDLE;
            end else begin
              cache_key_base <= held_lookup_base;
              cache_key_length <= held_lookup_length;
              cache_state <= KC_VALUE_SEND;
            end
          end
          KC_VALUE_SEND: begin
            if (cancel) cache_state <= KC_IDLE;
            else if (c_lookup_valid && c_lookup_ready) cache_state <= KC_VALUE_WAIT;
          end
          KC_VALUE_WAIT: if (c_lookup_rsp_valid) begin
            cache_value_base <= held_lookup_base;
            cache_value_length <= held_lookup_length;
            cache_valid <= !cached_lookup_bad && !cancel;
            cache_error <= cached_lookup_bad;
            cache_state <= KC_IDLE;
          end
          default: begin cache_error <= 1; cache_valid <= 0; cache_state <= KC_IDLE; end
        endcase
      end
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) copying_owned <= 0;
      else if (run_n) begin
        if (k_copy_valid && k_copy_ready) copying_owned <= 1;
        if (k_copy_rsp_valid && (state == COPY_WAIT || state == DRAIN)) copying_owned <= 0;
      end
    end
    assign token_ready = run_n && state == IDLE && image_valid && !flush && !abort_error;
    assign batch_ready = token_ready;
    assign logit_valid = run_n && state == LOGIT_EMIT;
    assign logit_index = logit_valid ? emit_index : 32'b0;
    assign logit_data = logit_valid ? emit_word : 32'b0;
    assign commit_valid = run_n && (state == COMMIT || (state == FAULT && is_batch));
    assign commit_count = commit_valid && !published_error ? result_count : 3'b0;
    assign commit_token_ids = commit_valid && !published_error ? result_tokens : 128'b0;
    assign commit_position = commit_valid && !published_error ? published_position : 32'b0;
    assign commit_error = commit_valid && published_error;
    assign busy = run_n && state != IDLE;
    assign pending_results = run_n &&
      (state == LOGIT_READ || state == LOGIT_EMIT || state == COMMIT || state == FAULT);
    assign done = run_n && state == COMPLETE;
    assign error = done && failed;
    assign accepted_tokens = final_logit_transfer && !failed && !failure_event ? 3'd1 :
      commit_transfer && !published_error && !failed && !failure_event ? result_count : 3'b0;
    assign completed_batch = commit_transfer && !published_error && !failed && !failure_event;
    assign eligible_bytes = d_stats_valid ? d_dense_bytes : 32'b0;
    assign avoided_bytes = d_stats_valid ? d_avoided_bytes : 32'b0;
    always @(posedge clk) begin
      if (run_n) begin
        if (state == DECODE_WAIT && d_logit_valid && d_logit_ready && !is_batch &&
            d_logit_index == logit_write_index && d_logit_index < V && d_logit_slots == 1)
          ordinary_logits[d_logit_index] <= d_logit_data[31:0];
        if (state == LOGIT_READ) emit_word <= ordinary_logits[emit_index];
      end
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        is_batch <= 0;
        correction <= 0;
        need_correction <= 0;
        failed <= 0;
        prefix_valid <= 0;
        prefix_length <= 0;
        prefix_target <= 0;
        reserved_length <= 0;
        next_target <= 0;
        count <= 0;
        result_count <= 0;
        slots <= 0;
        remaining_mask <= 0;
        tokens <= 0;
        positions <= 0;
        node_targets <= 0;
        result_tokens <= 0;
        ancestors <= 0;
        parents <= 0;
        copying_node <= 0;
        copying_layer <= 0;
        logit_write_index <= 0;
        emit_index <= 0;
        configuration_q <= 0;
        threshold_q <= 0;
        format_q <= 0;
        int8_q <= 0;
        finite_q <= 0;
        extension_base_q <= 0;
        extension_length_q <= 0;
        image_q <= 0;
        published_error <= 0;
        published_position <= 0;
      end else if (run_n) begin
        if (flush) begin prefix_valid <= 0; prefix_length <= 0; prefix_target <= 0; end
        if (failure_event && state != IDLE && state != COMPLETE &&
            state != DRAIN && state != FAULT) begin
          failed <= 1;
          if (state == COMMIT) begin
            if (commit_ready) state <= COMPLETE;
          end else if (state != LOGIT_EMIT || logit_ready) state <= DRAIN;
        end else case (state)
          IDLE: if (command_accepted) begin
            is_batch <= batch_valid;
            correction <= 0;
            need_correction <= 0;
            failed <= 0;
            configuration_q <= configuration;
            threshold_q <= sparse_threshold;
            format_q <= kv_format;
            int8_q <= int8_weights;
            finite_q <= finite_image;
            extension_base_q <= extension_base;
            extension_length_q <= extension_length;
            image_q <= image_generation;
            reserved_length <= prefix_length;
            logit_write_index <= 0;
            emit_index <= 0;
            remaining_mask <= 0;
            result_count <= 0;
            published_error <= 0;
            published_position <= 0;
            if (token_valid && batch_valid) begin
              failed <= 1; published_error <= 1; state <= FAULT;
            end else if (batch_valid) begin
              tokens <= batch_token_ids;
              count <= batch_count;
              slots <= batch_count <= 4 ? 4'b1111 >> (4-batch_count) : 4'b0;
              parents <= batch_parents;
              if (batch_bad || configuration[1:0] == 3) begin
                failed <= 1; published_error <= 1; state <= FAULT;
              end else state <= MASK_SEND;
            end else begin
              tokens <= {96'b0,token_id};
              positions <= {96'b0,token_pos};
              ancestors <= 16'h0001;
              slots <= 1;
              count <= 1;
              result_count <= 1;
              result_tokens <= {96'b0,token_id};
              parents <= 12'h004;
              if (token_id >= V || token_pos != prefix_length || prefix_length >= S ||
                  configuration[1:0] == 3) begin
                failed <= 1; published_error <= 1; state <= FAULT;
              end else state <= KV_BEGIN;
            end
          end
          MASK_SEND: if (m_ready) state <= MASK_WAIT;
          MASK_WAIT: if (m_valid) begin
            if (m_error) begin failed <= 1; published_error <= 1; state <= FAULT; end
            else begin positions <= m_positions; ancestors <= m_ancestors; state <= KV_BEGIN; end
          end
          KV_BEGIN: if (k_begin_ready) state <= KV_SETTLE;
          KV_SETTLE: state <= DECODE_SEND;
          DECODE_SEND: if (d_ready) state <= DECODE_WAIT;
          DECODE_WAIT: begin
            if (d_logit_valid && d_logit_ready && !is_batch) begin
              if (d_logit_index != logit_write_index || d_logit_index >= V ||
                  d_logit_slots != 1) begin failed <= 1; state <= DRAIN; end
              else logit_write_index <= logit_write_index + 1'b1;
            end
            if (d_valid) begin
              if (d_error || targets_bad || (!is_batch && logit_write_index != V)) begin
                failed <= 1; state <= DRAIN;
              end else if (!is_batch || correction) begin
                node_targets <= d_targets;
                remaining_mask <= 1;
                next_target <= d_targets[31:0];
                state <= COPY_SELECT;
              end else begin node_targets <= d_targets; state <= VERIFY_SEND; end
            end
          end
          VERIFY_SEND: if (v_ready) state <= VERIFY_WAIT;
          VERIFY_WAIT: if (v_valid) begin
            if (verifier_bad) begin failed <= 1; published_error <= 1; state <= FAULT; end
            else begin
              result_count <= v_count;
              result_tokens <= v_tokens;
              remaining_mask <= v_mask;
              need_correction <= selected_count != v_count;
              state <= COPY_SELECT;
            end
          end
          COPY_SELECT: begin
            if (selected_found) begin
              if (!correction && positions[32*selected_node+:32] != reserved_length) begin
                failed <= 1; state <= DRAIN;
              end else begin copying_node <= selected_node; copying_layer <= 0; state <= COPY_SEND; end
            end else if (is_batch && need_correction && !correction) begin
              correction <= 1; state <= KV_BEGIN;
            end else if ({1'b0,reserved_length} !=
                {1'b0,prefix_length} + {30'b0,result_count}) begin
              failed <= 1; state <= DRAIN;
            end else if (is_batch) begin
              published_error <= 0;
              published_position <= prefix_length;
              state <= COMMIT;
            end else begin emit_index <= 0; state <= LOGIT_READ; end
          end
          COPY_SEND: if (k_copy_valid && k_copy_ready) state <= COPY_WAIT;
          COPY_WAIT: if (k_copy_rsp_valid) begin
            if (k_copy_rsp_error) begin failed <= 1; state <= DRAIN; end
            else if (copying_layer + 1'b1 == L) begin
              remaining_mask[copying_node] <= 0;
              reserved_length <= reserved_length + 1'b1;
              next_target <= node_targets[32*copying_node+:32];
              state <= COPY_SELECT;
            end else begin copying_layer <= copying_layer + 1'b1; state <= COPY_SEND; end
          end
          LOGIT_READ: state <= LOGIT_EMIT;
          LOGIT_EMIT: if (logit_ready) begin
            if (failed) state <= DRAIN;
            else if (final_logit_transfer) begin
              prefix_length <= reserved_length;
              prefix_target <= next_target;
              prefix_valid <= 1;
              state <= COMPLETE;
            end else begin emit_index <= emit_index + 1'b1; state <= LOGIT_READ; end
          end
          COMMIT: if (commit_transfer) begin
            if (!failed) begin
              prefix_length <= reserved_length;
              prefix_target <= next_target;
              prefix_valid <= 1;
            end
            state <= COMPLETE;
          end
          FAULT: if (!is_batch || commit_transfer) state <= COMPLETE;
          COMPLETE: state <= IDLE;
          DRAIN: if (!d_busy && !read_busy && !copying_owned &&
              lookup_state == LM_IDLE && cache_state == KC_IDLE && !m_valid && !v_valid) begin
            published_error <= 1; state <= FAULT;
          end
          default: begin failed <= 1; state <= DRAIN; end
        endcase
      end
    end
  end endgenerate
endmodule
