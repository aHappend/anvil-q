module anvil_q1_ht2_execution #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2, HEAD_DIM = 64,
  parameter GROUP_SIZE = 128, VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768
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
  input wire write_dma_error
);
  localparam SK = NUM_KV_HEADS > 0 ? NUM_KV_HEADS : 1;
  localparam SG = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  localparam LEGAL = NUM_LAYERS >= 1 && NUM_LAYERS <= 24 &&
    HIDDEN_SIZE >= 8 && HIDDEN_SIZE <= 896 && (HIDDEN_SIZE & 7) == 0 &&
    INTERMEDIATE_SIZE >= 8 && INTERMEDIATE_SIZE <= 4864 &&
    (INTERMEDIATE_SIZE & 7) == 0 &&
    NUM_Q_HEADS >= 1 && NUM_Q_HEADS <= 14 &&
    NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 && NUM_Q_HEADS % SK == 0 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    HIDDEN_SIZE == NUM_Q_HEADS*HEAD_DIM && ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
    GROUP_SIZE >= 1 && GROUP_SIZE <= HIDDEN_SIZE &&
    HIDDEN_SIZE % SG == 0 && INTERMEDIATE_SIZE % SG == 0 &&
    VOCAB_SIZE >= 1 && VOCAB_SIZE <= 151936 &&
    MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768;
  localparam L = LEGAL ? NUM_LAYERS : 1, H = LEGAL ? HIDDEN_SIZE : 8;
  localparam I = LEGAL ? INTERMEDIATE_SIZE : 8, Q = LEGAL ? NUM_Q_HEADS : 1;
  localparam K = LEGAL ? NUM_KV_HEADS : 1, D = LEGAL ? HEAD_DIM : 8;
  localparam G = LEGAL ? GROUP_SIZE : 1, V = LEGAL ? VOCAB_SIZE : 1;
  localparam S = LEGAL ? MAX_SEQ_LEN : 1;
  localparam [31:0] KV_BYTES = S*((2*K*D+63)/64)*64;
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
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [31:0] ordinary_logits [0:V-1];
  wire flush = new_sequence || invalidate_image;
  wire cancel = state == DRAIN || abort_error || flush;
  wire command_accepted = (token_valid && token_ready) || (batch_valid && batch_ready);
  wire final_logit_transfer = logit_valid && logit_ready && emit_index + 1 == V;
  wire commit_transfer = commit_valid && commit_ready;
  reg batch_bad, targets_bad, verifier_bad;
  reg [2:0] selected_count;
  reg selected_found;
  reg [1:0] selected_node;
  integer token, child;
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
  wire [7:0] d_read_burstcount;
  wire d_store_valid, d_store_ready, d_store_first, d_store_last, k_store_error;
  wire [1:0] d_store_node;
  wire [31:0] d_store_layer, d_store_column;
  wire [15:0] d_store_key, d_store_value;
  wire d_kv_valid, d_kv_ready, d_kv_provisional;
  wire [1:0] d_kv_node;
  wire [31:0] d_kv_layer, d_kv_position, d_kv_head, d_kv_column;
  wire d_kv_rsp_valid, d_kv_rsp_ready, d_kv_error;
  wire [15:0] d_kv_key, d_kv_value;
  wire k_begin_ready, k_begin_error, k_read_ready, k_copy_ready;
  wire k_copy_valid, k_copy_rsp_valid, k_copy_rsp_error;
  wire k_read_valid, k_read_dma_ready, k_read_data_ready;
  wire [32:0] k_read_address;
  wire [7:0] k_read_burstcount;
  reg read_owned, read_kv;
  reg [7:0] read_remaining;
  wire read_command = read_dma_valid && read_dma_ready;
  wire read_response = read_dma_data_valid && read_dma_data_ready;
  wire read_response_owned = read_owned || read_command;
  wire read_response_kv = read_owned ? read_kv : k_read_valid;
  wire [3:0] active_slots = correction ? 4'b0001 : slots;
  wire [1:0] correction_index = result_count == 0 ? 2'b0 : 2'(result_count-1'b1);
  wire [127:0] active_tokens = correction ?
    {96'b0, result_tokens[32*correction_index+:32]} : tokens;
  wire [127:0] active_positions = correction ? {96'b0, reserved_length} : positions;
  wire [15:0] active_ancestors = correction ? 16'h0001 : ancestors;
  wire [31:0] active_prefix_length = correction ? reserved_length : prefix_length;

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
  wire [31:0] wanted_layer = state == COPY_SEND ? {27'b0, copying_layer} : d_kv_layer;
  wire wants_cache = state == COPY_SEND || d_kv_valid;
  wire cache_match = cache_valid && cache_layer == wanted_layer;
  wire c_lookup_valid = run_n &&
    (cache_state == KC_KEY_SEND || cache_state == KC_VALUE_SEND);
  wire c_lookup_ready = run_n && lookup_state == LM_IDLE && !d_lookup_valid;
  wire c_lookup_rsp_valid = run_n && lookup_state == LM_RESPONSE && lookup_owner;
  wire c_lookup_rsp_ready = cache_state == KC_KEY_WAIT || cache_state == KC_VALUE_WAIT;
  wire [31:0] c_lookup_index = (cache_layer << 6) + (cache_layer << 5) +
    (cache_state == KC_KEY_SEND ? 32'd72 : 32'd80);
  wire [33:0] cached_lookup_end = {1'b0, held_lookup_base} + {2'b0, held_lookup_length};
  wire cached_lookup_bad = held_lookup_error || held_lookup_length != KV_BYTES ||
    (|held_lookup_base[5:0]) || cached_lookup_end > 34'h200000000;
  wire lookup_completion = lookup_rsp_valid &&
    (lookup_state == LM_WAIT || (lookup_state == LM_COMMAND && lookup_ready));

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native execution geometry");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    batch_bad = batch_count == 0 || batch_count > 4 || !configuration[2] ||
      !prefix_valid || prefix_length >= S;
    targets_bad = 0;
    verifier_bad = v_error || v_count == 0 || v_count > 4 ||
      {1'b0, prefix_length} + {30'b0, v_count} > S;
    selected_count = 0;
    selected_found = 0;
    selected_node = 0;
    for (token = 0; token < 4; token = token + 1) begin
      if (token < batch_count && batch_token_ids[32*token+:32] >= V) batch_bad = 1;
      if (active_slots[token] && d_targets[32*token+:32] >= V) targets_bad = 1;
      if (v_mask[token]) selected_count = selected_count + 1'b1;
      if (token < v_count && v_tokens[32*token+:32] >= V) verifier_bad = 1;
      if (v_mask[token] && !slots[token]) verifier_bad = 1;
    end
    if (selected_count > v_count ||
        (selected_count != v_count && selected_count + 1'b1 != v_count)) verifier_bad = 1;
    for (child = 0; child < 4; child = child + 1) begin
      if (!selected_found && remaining_mask[child]) begin
        selected_found = 1;
        selected_node = child[1:0];
      end
    end
  end

  anvil_q1_ht2_tree_mask #(.MAX_SEQ_LEN(S)) u_tree (
    .clk(clk), .rst_n(run_n), .req_valid(state == MASK_SEND && !cancel),
    .req_ready(m_ready), .req_prefix_valid(prefix_valid),
    .req_prefix_position(prefix_length-1'b1), .req_count(count), .req_parents(parents),
    .rsp_valid(m_valid), .rsp_ready(state == MASK_WAIT || state == DRAIN),
    .rsp_positions(m_positions), .rsp_ancestors(m_ancestors), .rsp_error(m_error)
  );
  anvil_q1_ht2_spec_verifier u_verifier (
    .clk(clk), .rst_n(run_n), .in_valid(state == VERIFY_SEND && !cancel),
    .in_ready(v_ready), .in_count(count), .in_draft_tokens(tokens),
    .in_target_tokens(node_targets), .in_parents(parents), .in_prefix_target(prefix_target),
    .out_valid(v_valid), .out_ready(state == VERIFY_WAIT || state == DRAIN),
    .out_count(v_count), .out_tokens(v_tokens), .out_commit_mask(v_mask), .out_error(v_error)
  );
  anvil_q1_ht2_decoder #(
    .NUM_LAYERS(L), .HIDDEN_SIZE(H), .INTERMEDIATE_SIZE(I),
    .NUM_Q_HEADS(Q), .NUM_KV_HEADS(K), .HEAD_DIM(D), .GROUP_SIZE(G),
    .VOCAB_SIZE(V), .MAX_SEQ_LEN(S)
  ) u_decoder (
    .clk(clk), .rst_n(run_n), .abort_error(cancel),
    .cmd_valid(state == DECODE_SEND && !cancel), .cmd_ready(d_ready),
    .cmd_format(configuration[1:0]), .cmd_slots(active_slots), .cmd_tokens(active_tokens),
    .cmd_positions(active_positions), .cmd_ancestors(active_ancestors),
    .cmd_prefix_length(active_prefix_length), .cmd_emit_logits(!is_batch),
    .cmd_sparse(configuration[3]), .cmd_finite_weights(finite_image),
    .cmd_threshold(sparse_threshold),
    .lookup_valid(d_lookup_valid), .lookup_ready(d_lookup_ready),
    .lookup_index(d_lookup_index), .lookup_rsp_valid(d_lookup_rsp_valid),
    .lookup_rsp_ready(d_lookup_rsp_ready), .lookup_base(held_lookup_base),
    .lookup_length(held_lookup_length), .lookup_error(held_lookup_error),
    .dma_valid(d_read_valid), .dma_ready(d_read_ready), .dma_address(d_read_address),
    .dma_burstcount(d_read_burstcount),
    .dma_data_valid(read_dma_data_valid && read_response_owned && !read_response_kv),
    .dma_data_ready(d_read_data_ready), .dma_data(read_dma_data), .dma_error(read_dma_error),
    .kv_store_valid(d_store_valid), .kv_store_ready(d_store_ready),
    .kv_store_node(d_store_node), .kv_store_layer(d_store_layer),
    .kv_store_column(d_store_column), .kv_store_first(d_store_first), .kv_store_last(d_store_last),
    .kv_store_key(d_store_key), .kv_store_value(d_store_value), .kv_store_error(k_store_error),
    .kv_read_valid(d_kv_valid), .kv_read_ready(d_kv_ready),
    .kv_read_provisional(d_kv_provisional), .kv_read_node(d_kv_node),
    .kv_read_layer(d_kv_layer), .kv_read_position(d_kv_position),
    .kv_read_head(d_kv_head), .kv_read_column(d_kv_column),
    .kv_rsp_valid(d_kv_rsp_valid), .kv_rsp_ready(d_kv_rsp_ready),
    .kv_key(d_kv_key), .kv_value(d_kv_value), .kv_rsp_error(d_kv_error),
    .logit_valid(d_logit_valid), .logit_ready(d_logit_ready), .logit_index(d_logit_index),
    .logit_data(d_logit_data), .logit_slots(d_logit_slots),
    .rsp_valid(d_valid), .rsp_ready(state == DECODE_WAIT || state == DRAIN),
    .rsp_targets(d_targets), .rsp_error(d_error), .busy(d_busy), .done(d_done),
    .stats_valid(d_stats_valid), .stats_dense_bytes(d_dense_bytes),
    .stats_avoided_bytes(d_avoided_bytes), .stats_replay_bytes(), .stats_replay_column()
  );
  anvil_q1_ht2_kv #(
    .NUM_LAYERS(L), .NUM_KV_HEADS(K), .HEAD_DIM(D), .MAX_SEQ_LEN(S)
  ) u_kv (
    .clk(clk), .rst_n(run_n), .flush(flush), .abort_error(cancel),
    .cmd_valid(state == KV_BEGIN && !cancel), .cmd_ready(k_begin_ready),
    .cmd_begin(1'b1), .cmd_slots(active_slots), .cmd_error(k_begin_error),
    .store_valid(d_store_valid), .store_ready(d_store_ready),
    .store_node(d_store_node), .store_layer(d_store_layer), .store_column(d_store_column),
    .store_first(d_store_first), .store_last(d_store_last),
    .store_key(d_store_key), .store_value(d_store_value), .store_error(k_store_error),
    .read_valid(d_kv_valid && cache_match && !cancel), .read_ready(k_read_ready),
    .read_provisional(d_kv_provisional), .read_fp16(configuration[1:0] == 1),
    .read_node(d_kv_node), .read_layer(d_kv_layer), .read_head(d_kv_head),
    .read_column(d_kv_column), .read_position(d_kv_position),
    .read_prefix_length(active_prefix_length),
    .read_key_base(cache_key_base), .read_value_base(cache_value_base),
    .read_key_length(cache_key_length), .read_value_length(cache_value_length),
    .read_rsp_valid(d_kv_rsp_valid), .read_rsp_ready(d_kv_rsp_ready),
    .read_rsp_key(d_kv_key), .read_rsp_value(d_kv_value), .read_rsp_error(d_kv_error),
    .copy_valid(k_copy_valid), .copy_ready(k_copy_ready),
    .copy_fp16(configuration[1:0] == 1), .copy_node(copying_node),
    .copy_layer({27'b0, copying_layer}), .copy_position(reserved_length),
    .copy_prefix_length(reserved_length),
    .copy_key_base(cache_key_base), .copy_value_base(cache_value_base),
    .copy_key_length(cache_key_length), .copy_value_length(cache_value_length),
    .copy_rsp_valid(k_copy_rsp_valid),
    .copy_rsp_ready(state == COPY_WAIT || state == DRAIN), .copy_rsp_error(k_copy_rsp_error),
    .read_dma_valid(k_read_valid), .read_dma_ready(k_read_dma_ready),
    .read_dma_address(k_read_address), .read_dma_burstcount(k_read_burstcount),
    .read_dma_data_valid(read_dma_data_valid && read_response_owned && read_response_kv),
    .read_dma_data_ready(k_read_data_ready), .read_dma_data(read_dma_data),
    .read_dma_error(read_dma_error),
    .write_dma_valid(write_dma_valid), .write_dma_ready(write_dma_ready),
    .write_dma_address(write_dma_address), .write_dma_data(write_dma_data),
    .write_dma_byteenable(write_dma_byteenable),
    .write_dma_rsp_valid(write_dma_rsp_valid), .write_dma_rsp_ready(write_dma_rsp_ready),
    .write_dma_error(write_dma_error)
  );
  assign d_kv_ready = run_n && !cancel && cache_match && k_read_ready;
  assign k_copy_valid = run_n && state == COPY_SEND && cache_match && !cancel;
  assign d_logit_ready = run_n && (state == DECODE_WAIT || state == DRAIN);
  assign read_dma_valid = run_n && !read_owned && (k_read_valid || d_read_valid);
  assign read_dma_address = !read_dma_valid ? 33'b0 :
    k_read_valid ? k_read_address : d_read_address;
  assign read_dma_burstcount = !read_dma_valid ? 8'b0 :
    k_read_valid ? k_read_burstcount : d_read_burstcount;
  assign k_read_dma_ready = run_n && !read_owned && read_dma_ready;
  assign d_read_ready = run_n && !read_owned && !k_read_valid && read_dma_ready;
  assign read_dma_data_ready = run_n && read_response_owned &&
    (read_response_kv ? k_read_data_ready : d_read_data_ready);

  assign d_lookup_ready = run_n && lookup_state == LM_IDLE;
  assign d_lookup_rsp_valid = run_n && lookup_state == LM_RESPONSE && !lookup_owner;
  assign lookup_valid = run_n && lookup_state == LM_COMMAND;
  assign lookup_index = lookup_valid ? held_lookup_index : 32'b0;
  assign lookup_rsp_ready = run_n &&
    (lookup_state == LM_WAIT || (lookup_valid && lookup_ready));
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      lookup_state <= LM_IDLE;
      lookup_owner <= 0;
      held_lookup_index <= 0;
      held_lookup_base <= 0;
      held_lookup_length <= 0;
      held_lookup_error <= 0;
    end else case (lookup_state)
      LM_IDLE: begin
        if (d_lookup_valid || c_lookup_valid) begin
          lookup_owner <= !d_lookup_valid;
          held_lookup_index <= d_lookup_valid ? d_lookup_index : c_lookup_index;
          lookup_state <= LM_COMMAND;
        end
      end
      LM_COMMAND: if (lookup_valid && lookup_ready) begin
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
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      cache_state <= KC_IDLE;
      cache_valid <= 0;
      cache_error <= 0;
      cache_layer <= 0;
      cache_key_base <= 0;
      cache_value_base <= 0;
      cache_key_length <= 0;
      cache_value_length <= 0;
    end else begin
      cache_error <= 0;
      if (flush || state == IDLE || cancel) cache_valid <= 0;
      case (cache_state)
        KC_IDLE: if (wants_cache && !cache_match && !cancel) begin
          cache_layer <= wanted_layer;
          cache_valid <= 0;
          cache_state <= KC_KEY_SEND;
        end
        KC_KEY_SEND: if (c_lookup_valid && c_lookup_ready) cache_state <= KC_KEY_WAIT;
        KC_KEY_WAIT: if (c_lookup_rsp_valid) begin
          if (cached_lookup_bad) begin
            cache_error <= 1;
            cache_state <= KC_IDLE;
          end else begin
            cache_key_base <= held_lookup_base;
            cache_key_length <= held_lookup_length;
            if (cancel) cache_state <= KC_IDLE;
            else cache_state <= KC_VALUE_SEND;
          end
        end
        KC_VALUE_SEND: if (c_lookup_valid && c_lookup_ready) cache_state <= KC_VALUE_WAIT;
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
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      read_owned <= 0;
      read_kv <= 0;
      read_remaining <= 0;
      copying_owned <= 0;
    end else begin
      if (read_command) begin
        read_owned <= !(read_response && read_dma_burstcount == 1);
        read_kv <= k_read_valid;
        read_remaining <= read_dma_burstcount - {7'b0, read_response};
      end
      if (read_response && read_owned) begin
        if (read_remaining == 1) begin read_owned <= 0; read_remaining <= 0; end
        else read_remaining <= read_remaining - 1'b1;
      end
      if (k_copy_valid && k_copy_ready) copying_owned <= 1;
      if (k_copy_rsp_valid && (state == COPY_WAIT || state == DRAIN)) copying_owned <= 0;
    end
  end

  assign token_ready = run_n && state == IDLE && image_valid && !flush && !abort_error;
  assign batch_ready = token_ready;
  assign logit_valid = run_n && state == LOGIT_EMIT && !flush && !abort_error;
  assign logit_index = logit_valid ? emit_index : 32'b0;
  assign logit_data = logit_valid ? emit_word : 32'b0;
  assign commit_valid = run_n && (state == COMMIT || (state == FAULT && is_batch)) &&
    !flush && !abort_error;
  assign commit_count = commit_valid && !failed ? result_count : 3'b0;
  assign commit_token_ids = commit_valid && !failed ? result_tokens : 128'b0;
  assign commit_position = commit_valid && !failed ? prefix_length : 32'b0;
  assign commit_error = commit_valid && failed;
  assign busy = run_n && state != IDLE;
  assign pending_results = run_n &&
    (state == LOGIT_READ || state == LOGIT_EMIT || state == COMMIT || state == FAULT);
  assign done = run_n && state == COMPLETE;
  assign error = done && failed;
  assign accepted_tokens = final_logit_transfer ? 3'd1 :
    commit_transfer && !failed ? result_count : 3'b0;
  assign completed_batch = commit_transfer && !failed;
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
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
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
    end else begin
      if (flush) begin
        prefix_valid <= 0;
        prefix_length <= 0;
        prefix_target <= 0;
      end
      if ((abort_error || flush || k_begin_error || k_store_error || cache_error) &&
          state != IDLE && state != COMPLETE && state != DRAIN) begin
        failed <= 1;
        state <= DRAIN;
      end else case (state)
        IDLE: if (command_accepted) begin
          is_batch <= batch_valid;
          correction <= 0;
          need_correction <= 0;
          failed <= 0;
          reserved_length <= prefix_length;
          logit_write_index <= 0;
          emit_index <= 0;
          remaining_mask <= 0;
          result_count <= 0;
          if (token_valid && batch_valid) begin failed <= 1; state <= FAULT; end
          else if (batch_valid) begin
            tokens <= batch_token_ids;
            count <= batch_count;
            slots <= 4'b1111 >> (4-batch_count);
            parents <= batch_parents;
            if (batch_bad) begin failed <= 1; state <= FAULT; end
            else state <= MASK_SEND;
          end else begin
            tokens <= {96'b0, token_id};
            positions <= {96'b0, token_pos};
            ancestors <= 16'h0001;
            slots <= 1;
            count <= 1;
            result_count <= 1;
            result_tokens <= {96'b0, token_id};
            parents <= 12'h004;
            if (token_id >= V || token_pos != prefix_length || prefix_length >= S ||
                configuration[1:0] == 3) begin failed <= 1; state <= FAULT; end
            else state <= KV_BEGIN;
          end
        end
        MASK_SEND: if (m_ready) state <= MASK_WAIT;
        MASK_WAIT: if (m_valid) begin
          if (m_error) begin failed <= 1; state <= FAULT; end
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
              failed <= 1;
              state <= DRAIN;
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
          if (verifier_bad) begin failed <= 1; state <= FAULT; end
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
            copying_node <= selected_node;
            copying_layer <= 0;
            state <= COPY_SEND;
          end else if (is_batch && need_correction && !correction) begin
            correction <= 1;
            state <= KV_BEGIN;
          end else if ({1'b0, reserved_length} !=
              {1'b0, prefix_length} + {30'b0, result_count}) begin
            failed <= 1;
            state <= DRAIN;
          end else if (is_batch) state <= COMMIT;
          else begin emit_index <= 0; state <= LOGIT_READ; end
        end
        COPY_SEND: if (k_copy_valid && k_copy_ready) state <= COPY_WAIT;
        COPY_WAIT: if (k_copy_rsp_valid) begin
          if (k_copy_rsp_error) begin failed <= 1; state <= DRAIN; end
          else if (copying_layer + 1 == L) begin
            remaining_mask[copying_node] <= 0;
            reserved_length <= reserved_length + 1'b1;
            next_target <= node_targets[32*copying_node+:32];
            state <= COPY_SELECT;
          end else begin copying_layer <= copying_layer + 1'b1; state <= COPY_SEND; end
        end
        LOGIT_READ: state <= LOGIT_EMIT;
        LOGIT_EMIT: if (logit_valid && logit_ready) begin
          if (final_logit_transfer) begin
            prefix_length <= reserved_length;
            prefix_target <= next_target;
            prefix_valid <= 1;
            state <= COMPLETE;
          end else begin emit_index <= emit_index + 1'b1; state <= LOGIT_READ; end
        end
        COMMIT: if (commit_transfer) begin
          prefix_length <= reserved_length;
          prefix_target <= next_target;
          prefix_valid <= 1;
          state <= COMPLETE;
        end
        FAULT: if (!is_batch || commit_transfer) state <= COMPLETE;
        COMPLETE: state <= IDLE;
        DRAIN: if (!d_busy && !read_owned && !copying_owned &&
            lookup_state == LM_IDLE && cache_state == KC_IDLE && !m_valid && !v_valid)
          state <= FAULT;
        default: begin failed <= 1; state <= DRAIN; end
      endcase
    end
  end
endmodule
