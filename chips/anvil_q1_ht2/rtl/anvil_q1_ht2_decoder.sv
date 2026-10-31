module anvil_q1_ht2_decoder #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2, HEAD_DIM = 64,
  parameter GROUP_SIZE = 128, VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n, abort_error,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [1:0] cmd_format,
  input wire [3:0] cmd_slots,
  input wire [127:0] cmd_tokens, cmd_positions,
  input wire [15:0] cmd_ancestors,
  input wire [31:0] cmd_prefix_length,
  input wire cmd_emit_logits, cmd_sparse, cmd_finite_weights,
  input wire [15:0] cmd_threshold,
  output wire lookup_valid,
  input wire lookup_ready,
  output wire [31:0] lookup_index,
  input wire lookup_rsp_valid,
  output wire lookup_rsp_ready,
  input wire [32:0] lookup_base,
  input wire [31:0] lookup_length,
  input wire lookup_error,
  output wire dma_valid,
  input wire dma_ready,
  output wire [32:0] dma_address,
  output wire [7:0] dma_burstcount,
  input wire dma_data_valid,
  output wire dma_data_ready,
  input wire [511:0] dma_data,
  input wire dma_error,
  output wire kv_store_valid,
  input wire kv_store_ready,
  output wire [1:0] kv_store_node,
  output wire [31:0] kv_store_layer, kv_store_column,
  output wire kv_store_first, kv_store_last,
  output wire [15:0] kv_store_key, kv_store_value,
  input wire kv_store_error,
  output wire kv_read_valid,
  input wire kv_read_ready,
  output wire kv_read_provisional,
  output wire [1:0] kv_read_node,
  output wire [31:0] kv_read_layer, kv_read_position, kv_read_head, kv_read_column,
  input wire kv_rsp_valid,
  output wire kv_rsp_ready,
  input wire [15:0] kv_key, kv_value,
  input wire kv_rsp_error,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire [127:0] logit_data,
  output wire [3:0] logit_slots,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [127:0] rsp_targets,
  output wire rsp_error,
  output wire busy, done,
  output wire stats_valid,
  output wire [31:0] stats_dense_bytes, stats_avoided_bytes, stats_replay_bytes,
  output wire stats_replay_column
);
  import anvil_q1_ht2_fp_pkg::*;
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
  localparam S = LEGAL ? MAX_SEQ_LEN : 1, C = K*D;
  localparam [31:0] EMBEDDING_BYTES = ((V+63)/64)*H*128;
  localparam [31:0] NORM_BYTES = ((2*H+63)/64)*64;
  localparam [31:0] KV_BIAS_BYTES = ((2*C+63)/64)*64;
  localparam IDLE = 7'd0, LOOKUP_SEND = 7'd1, LOOKUP_WAIT = 7'd2,
    EMB_DESCRIPTOR = 7'd3, EMB_BEGIN = 7'd4, EMB_WORD = 7'd5, EMB_STORE = 7'd6,
    FETCH_ADDRESS = 7'd7, FETCH_CHECK = 7'd8, FETCH_SEND = 7'd9,
    FETCH_WAIT = 7'd10, FETCH_WORD = 7'd11,
    NORM_BEGIN = 7'd12, NORM_DESCRIPTOR = 7'd13, NORM_COMMAND = 7'd14,
    NORM_READ = 7'd15, NORM_FETCH = 7'd16, NORM_INPUT = 7'd17,
    NORM_OUTPUT = 7'd18, NORM_FINISH = 7'd19,
    PROJ_BEGIN = 7'd20, PROJ_WEIGHT = 7'd21, PROJ_ZERO = 7'd22,
    PROJ_SCALE = 7'd23, PROJ_BIAS_BEGIN = 7'd24, PROJ_BIAS = 7'd25,
    PROJ_COMMAND = 7'd26, PROJ_READ = 7'd27, PROJ_INPUT = 7'd28,
    PROJ_OUTPUT = 7'd29, ROW_BEGIN = 7'd30, ROW_BIAS = 7'd31,
    ROW_RESIDUAL = 7'd32, ROW_ADD_SEND = 7'd33, ROW_ADD_WAIT = 7'd34,
    ROW_STORE = 7'd35, ROW_EMIT = 7'd36, ROW_NEXT = 7'd37,
    PROJ_RETIRE = 7'd38, PROJ_FINISH = 7'd39,
    ROPE_COMMAND = 7'd40, ROPE_READ = 7'd41, ROPE_INPUT = 7'd42,
    ROPE_OUTPUT = 7'd43, ROPE_FINISH = 7'd44,
    STORE_READ = 7'd45, STORE_SEND = 7'd46, STORE_SETTLE = 7'd47,
    ATTN_COMMAND = 7'd48, ATTN_READ = 7'd49, ATTN_INPUT = 7'd50,
    ATTN_OUTPUT = 7'd51, ATTN_FINISH = 7'd52,
    SWIGLU_COMMAND = 7'd53, SWIGLU_READ = 7'd54, SWIGLU_INPUT = 7'd55,
    SWIGLU_OUTPUT = 7'd56, SWIGLU_FINISH = 7'd57,
    RESPONSE = 7'd58, COMPLETE = 7'd59, FAIL_DRAIN = 7'd60;
  wire run_n;
  reg [6:0] state, lookup_return, fetch_return;
  reg [1:0] format, norm_phase;
  reg [3:0] slots;
  reg [127:0] tokens, positions;
  reg [15:0] ancestors, threshold;
  reg [31:0] prefix_length;
  reg emit_logits, sparse, finite_weights, failed;
  reg [4:0] layer;
  reg [2:0] projection;
  reg [12:0] vector_index;
  reg [12:0] swiglu_received;
  reg [1:0] embedding_slot, store_node;
  reg [127:0] embedding_word, row_value, row_operand, targets, maxima;
  reg [3:0] maximum_owned;
  reg [5:0] row_lane;
  reg [31:0] expected_panel;
  reg rope_key;
  reg [9:0] rope_base;
  reg [4:0] rope_pair;
  reg [3:0] descriptor_kind;
  reg [2:0] descriptor_projection;
  reg [4:0] descriptor_layer;
  reg [32:0] scalar_base, weight_base, zero_base, scale_base;
  reg [31:0] scalar_length, weight_length, zero_length, scale_length;
  reg [31:0] expected_scalar_length;
  reg [63:0] fetch_offset;
  reg [33:0] fetch_absolute;
  reg [31:0] fetch_index;
  reg fetch_embedding;
  reg [15:0] fetched_word;
  wire [31:0] expanded_fetched = expand16(fetched_word, fp16);
  reg cache_valid;
  reg [32:0] cache_address;
  reg [511:0] cache_data;
  reg lookup_owned;
  wire cancel = failed || abort_error || kv_store_error;
  wire fp16 = format == 1;
  wire [1:0] projection_format = projection == 7 && format == 2 ? 2'b0 : format;
  wire awq_projection = projection_format == 2;
  wire [31:0] projection_inputs = projection == 6 ? I : H;
  wire [31:0] projection_outputs = projection == 1 || projection == 2 ? C :
    projection == 4 || projection == 5 ? I : projection == 7 ? V : H;
  wire [33:0] lookup_end = {1'b0, lookup_base} + {2'b0, lookup_length};
  wire [33:0] scalar_end = {1'b0, scalar_base} + {2'b0, scalar_length};
  wire [63:0] candidate_fetch_address = {31'b0, scalar_base} + fetch_offset;
  wire [31:0] row_index = p_panel + {26'b0, row_lane};
  wire last_panel = p_panel + 32'd64 >= projection_outputs;
  wire row_active = p_mask[row_lane];
  wire [31:0] expected_rows = projection_outputs - expected_panel;
  wire [63:0] expected_panel_mask = expected_rows >= 64 ? 64'hffffffffffffffff :
    64'hffffffffffffffff >> (64-expected_rows);

  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [127:0] residuals [0:H-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [127:0] normalized [0:H-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [127:0] queries [0:H-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [127:0] keys [0:C-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [63:0] query_encoded [0:H-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [63:0] key_encoded [0:C-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [63:0] value_encoded [0:C-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [127:0] attention_vectors [0:H-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [127:0] gate_vectors [0:I-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [127:0] up_vectors [0:I-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [67:0] intermediate_vectors [0:I-1];
  reg [127:0] residual_q, normalized_q, attention_q, gate_q, up_q;
  reg [127:0] query_first_q, query_second_q, key_first_q, key_second_q;
  reg [63:0] encoded_query_q, encoded_key_q, encoded_value_q;
  reg [67:0] intermediate_q;
  wire [9:0] rope_first_index = rope_base + {5'b0, rope_pair};
  wire [9:0] rope_second_index = rope_first_index + (D >> 1);
  wire [127:0] projection_source = projection == 3 ? attention_q : normalized_q;
  wire [63:0] projection_activation, row_encoded;
  wire [3:0] projection_nonzero;
  wire [127:0] selected_panel_row;
  reg command_bad, row_bad, narrowing_bad, fetch_bad, input_narrowing_bad;
  reg [3:0] ancestor_count;
  reg [32:0] expected_position;
  integer token, node, earlier, peer, update_slot;
  genvar slot;

  wire p_ready, p_activation_ready, p_valid, p_busy, p_done, p_error;
  wire [31:0] p_panel;
  wire [8191:0] p_data;
  wire [63:0] p_mask;
  wire [3:0] p_slots;
  wire p_dma_valid, p_dma_ready, p_data_ready;
  wire [32:0] p_dma_address;
  wire [7:0] p_dma_burstcount;
  wire s_ready, s_valid, s_error, s_dma_valid, s_dma_ready, s_data_ready;
  wire [32:0] s_dma_address;
  wire [7:0] s_dma_burstcount;
  wire [1023:0] s_data;
  reg dma_owned, dma_scalar;
  reg [7:0] dma_remaining;
  wire scalar_command = state == FETCH_SEND && !cancel;
  wire scalar_response = s_valid && (state == FETCH_WAIT || state == FAIL_DRAIN);
  wire dma_command_transfer = dma_valid && dma_ready;
  wire dma_beat_transfer = dma_data_valid && dma_data_ready;
  wire response_owned = dma_owned || dma_command_transfer;
  wire response_scalar = dma_owned ? dma_scalar : s_dma_valid;
  wire n_ready, n_input_ready, n_valid, n_busy, n_done, n_error;
  wire [31:0] n_index;
  wire [127:0] n_data;
  wire [3:0] n_slots;
  wire [1:0] r_ready, r_input_ready, r_valid, r_busy, r_done, r_error;
  wire [63:0] r_first_index, r_second_index;
  wire [127:0] r_first_encoded, r_second_encoded;
  wire [7:0] r_slots;
  wire a_ready, a_query_ready, a_valid, a_busy, a_done, a_error;
  wire [31:0] a_index;
  wire [127:0] a_data;
  wire [3:0] a_slots;
  wire w_ready, w_input_ready, w_valid, w_busy, w_done, w_error;
  wire [31:0] w_index;
  wire [63:0] w_activation;
  wire [3:0] w_nonzero, w_slots;
  wire swiglu_active = state == SWIGLU_READ || state == SWIGLU_INPUT ||
    state == SWIGLU_OUTPUT;
  wire swiglu_response = swiglu_active && w_valid && !cancel;
  wire swiglu_bad = swiglu_response &&
    (w_index != {19'b0, swiglu_received} || w_index >= I || w_slots != slots);
  wire [3:0] add_valid;
  wire [127:0] add_data;
  wire worker_error = p_error || n_error || (|r_error) || a_error || w_error;
  wire workers_busy = p_busy || n_busy || (|r_busy) || a_busy || w_busy;
  wire selected_rope_valid = r_valid[rope_key];
  wire selected_rope_done = r_done[rope_key];
  wire [31:0] selected_rope_first = r_first_index[32*rope_key+:32];
  wire [31:0] selected_rope_second = r_second_index[32*rope_key+:32];
  wire [63:0] selected_rope_first_encoded = r_first_encoded[64*rope_key+:64];
  wire [63:0] selected_rope_second_encoded = r_second_encoded[64*rope_key+:64];

  function automatic greater32(input [31:0] a, input [31:0] b);
    begin
      if (a[30:0] == 0 && b[30:0] == 0) greater32 = 0;
      else if (a[31] != b[31]) greater32 = !a[31];
      else if (a[31]) greater32 = a[30:0] < b[30:0];
      else greater32 = a[30:0] > b[30:0];
    end
  endfunction

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native decoder geometry");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    command_bad = !LEGAL || cmd_format == 3 || cmd_slots == 0 ||
      cmd_prefix_length >= S ||
      (cmd_emit_logits && cmd_slots != 1) ||
      (cmd_sparse && (cmd_threshold[14:7] == 8'hff ||
        (cmd_threshold[15] && cmd_threshold[14:0] != 0)));
    ancestor_count = 0;
    expected_position = 0;
    for (node = 0; node < 4; node = node + 1) begin
      if (cmd_slots[node]) begin
        if (cmd_tokens[32*node+:32] >= V || !cmd_ancestors[4*node+node])
          command_bad = 1;
        ancestor_count = 0;
        for (earlier = 0; earlier < 4; earlier = earlier + 1) begin
          if (cmd_ancestors[4*node+earlier]) begin
            ancestor_count = ancestor_count + 1'b1;
            if (!cmd_slots[earlier] || earlier > node) command_bad = 1;
            if (earlier != node &&
                ((cmd_ancestors[4*earlier+:4] & ~cmd_ancestors[4*node+:4]) != 0 ||
                 cmd_positions[32*earlier+:32] >= cmd_positions[32*node+:32]))
              command_bad = 1;
            for (peer = 0; peer < 4; peer = peer + 1)
              if (peer < earlier && cmd_ancestors[4*node+peer] &&
                  cmd_positions[32*peer+:32] == cmd_positions[32*earlier+:32])
                command_bad = 1;
          end
        end
        expected_position = {1'b0, cmd_prefix_length} + {29'b0, ancestor_count} - 1'b1;
        if (expected_position >= S ||
            {1'b0, cmd_positions[32*node+:32]} != expected_position) command_bad = 1;
      end else if (cmd_ancestors[4*node+:4] != 0) command_bad = 1;
    end
    row_bad = 0;
    narrowing_bad = 0;
    input_narrowing_bad = 0;
    for (token = 0; token < 4; token = token + 1) begin
      if (slots[token]) begin
        if (fp32_nonfinite(row_value[32*token+:32])) row_bad = 1;
        if (fp32_nonfinite(expand16(row_encoded[16*token+:16], fp16))) narrowing_bad = 1;
        if (fp32_nonfinite(expand16(projection_activation[16*token+:16], fp16)))
          input_narrowing_bad = 1;
      end
    end
    fetch_bad = fp32_nonfinite(expanded_fetched);
  end
  generate for (slot = 0; slot < 4; slot = slot + 1) begin : g_slot
    wire [15:0] rounded_source = narrow32(projection_source[32*slot+:32], fp16);
    assign projection_activation[16*slot+:16] = !slots[slot] ? 16'b0 :
      projection == 6 ? intermediate_q[16*slot+:16] : rounded_source;
    assign projection_nonzero[slot] = slots[slot] &&
      (projection == 6 ? intermediate_q[64+slot] : (|projection_source[32*slot+:31]));
    assign row_encoded[16*slot+:16] = narrow32(row_value[32*slot+:32], fp16);
    assign selected_panel_row[32*slot+:32] = slots[slot] ?
      p_data[32*(64*slot+row_lane)+:32] : 32'b0;
    anvil_q1_ht2_fp32_add u_row_add (
      .clk(clk), .rst_n(run_n), .enable(1'b1),
      .in_valid(run_n && state == ROW_ADD_SEND && !cancel),
      .in_a(!slots[slot] ? 32'b0 : (projection == 3 || projection == 6) ?
        residual_q[32*slot+:32] : row_value[32*slot+:32]),
      .in_b(!slots[slot] ? 32'b0 : (projection == 3 || projection == 6) ?
        row_value[32*slot+:32] : row_operand[32*slot+:32]),
      .out_valid(add_valid[slot]), .out_data(add_data[32*slot+:32])
    );
  end endgenerate

  anvil_q1_ht2_projection #(
    .HIDDEN_SIZE(H), .INTERMEDIATE_SIZE(I), .GROUP_SIZE(G), .VOCAB_SIZE(V)
  ) u_projection (
    .clk(clk), .rst_n(run_n), .abort_error(cancel),
    .cmd_valid(state == PROJ_COMMAND && !cancel), .cmd_ready(p_ready),
    .cmd_format(projection_format), .cmd_slots(slots),
    .cmd_inputs(projection_inputs), .cmd_outputs(projection_outputs),
    .cmd_weight_base(weight_base), .cmd_zero_base(zero_base), .cmd_scale_base(scale_base),
    .cmd_weight_length(weight_length), .cmd_zero_length(zero_length),
    .cmd_scale_length(scale_length), .cmd_down_projection(projection == 6),
    .cmd_sparse(sparse), .cmd_finite_weights(finite_weights), .cmd_threshold(threshold),
    .activation_valid(state == PROJ_INPUT && !cancel && !input_narrowing_bad),
    .activation_ready(p_activation_ready), .activation_data(projection_activation),
    .activation_nonzero(projection_nonzero),
    .result_valid(p_valid), .result_ready(state == PROJ_RETIRE || state == FAIL_DRAIN),
    .result_panel(p_panel), .result_data(p_data), .result_mask(p_mask), .result_slots(p_slots),
    .busy(p_busy), .done(p_done), .error(p_error),
    .dma_valid(p_dma_valid), .dma_ready(p_dma_ready), .dma_address(p_dma_address),
    .dma_burstcount(p_dma_burstcount),
    .dma_data_valid(dma_data_valid && response_owned && !response_scalar),
    .dma_data_ready(p_data_ready), .dma_data(dma_data), .dma_error(dma_error),
    .stats_valid(stats_valid), .stats_dense_bytes(stats_dense_bytes),
    .stats_avoided_bytes(stats_avoided_bytes), .stats_replay_bytes(stats_replay_bytes),
    .stats_replay_column(stats_replay_column)
  );
  anvil_q1_ht2_burst_reader u_scalar_reader (
    .clk(clk), .rst_n(run_n), .cmd_valid(scalar_command), .cmd_ready(s_ready),
    .cmd_address({fetch_absolute[32:6], 6'b0}), .cmd_burstcount(8'd1),
    .mem_valid(s_dma_valid), .mem_ready(s_dma_ready), .mem_address(s_dma_address),
    .mem_burstcount(s_dma_burstcount),
    .mem_data_valid(dma_data_valid && response_owned && response_scalar),
    .mem_data_ready(s_data_ready), .mem_data(dma_data), .mem_error(dma_error),
    .rsp_valid(s_valid), .rsp_ready(state == FETCH_WAIT || state == FAIL_DRAIN),
    .rsp_data(s_data), .rsp_error(s_error)
  );
  assign dma_valid = run_n && !dma_owned && (s_dma_valid || p_dma_valid);
  assign dma_address = !dma_valid ? 33'b0 : s_dma_valid ? s_dma_address : p_dma_address;
  assign dma_burstcount = !dma_valid ? 8'b0 :
    s_dma_valid ? s_dma_burstcount : p_dma_burstcount;
  assign s_dma_ready = run_n && !dma_owned && dma_ready;
  assign p_dma_ready = run_n && !dma_owned && !s_dma_valid && dma_ready;
  assign dma_data_ready = run_n && response_owned &&
    (response_scalar ? s_data_ready : p_data_ready);
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      dma_owned <= 0;
      dma_scalar <= 0;
      dma_remaining <= 0;
    end else begin
      if (dma_command_transfer) begin
        dma_owned <= !(dma_beat_transfer && dma_burstcount == 1);
        dma_scalar <= s_dma_valid;
        dma_remaining <= dma_burstcount - {7'b0, dma_beat_transfer};
      end
      if (dma_beat_transfer && dma_owned) begin
        if (dma_remaining == 1) begin dma_owned <= 0; dma_remaining <= 0; end
        else dma_remaining <= dma_remaining - 1'b1;
      end
    end
  end

  anvil_q1_ht2_rmsnorm #(.HIDDEN_SIZE(H)) u_norm (
    .clk(clk), .rst_n(run_n), .abort_error(cancel),
    .cmd_valid(state == NORM_COMMAND && !cancel), .cmd_ready(n_ready),
    .cmd_slots(slots), .cmd_fp16(fp16),
    .in_valid(state == NORM_INPUT && !cancel), .in_ready(n_input_ready),
    .in_data(residual_q), .in_gamma(fetched_word),
    .out_valid(n_valid), .out_ready(state == NORM_OUTPUT || state == FAIL_DRAIN),
    .out_index(n_index), .out_data(n_data), .out_slots(n_slots),
    .busy(n_busy), .done(n_done), .error(n_error)
  );
  generate for (slot = 0; slot < 2; slot = slot + 1) begin : g_rope
    anvil_q1_ht2_rope #(.HEAD_DIM(D), .HEADS(slot == 0 ? Q : K)) u_rope (
      .clk(clk), .rst_n(run_n), .abort_error(cancel),
      .cmd_valid(state == ROPE_COMMAND && rope_key == slot && !cancel),
      .cmd_ready(r_ready[slot]), .cmd_slots(slots), .cmd_fp16(fp16),
      .cmd_positions(positions),
      .in_valid(state == ROPE_INPUT && rope_key == slot && !cancel),
      .in_ready(r_input_ready[slot]),
      .in_first(slot == 0 ? query_first_q : key_first_q),
      .in_second(slot == 0 ? query_second_q : key_second_q),
      .out_valid(r_valid[slot]),
      .out_ready((state == ROPE_OUTPUT && rope_key == slot) || state == FAIL_DRAIN),
      .out_first_index(r_first_index[32*slot+:32]),
      .out_second_index(r_second_index[32*slot+:32]),
      .out_first(), .out_second(),
      .out_first_encoded(r_first_encoded[64*slot+:64]),
      .out_second_encoded(r_second_encoded[64*slot+:64]),
      .out_slots(r_slots[4*slot+:4]),
      .busy(r_busy[slot]), .done(r_done[slot]), .error(r_error[slot])
    );
  end endgenerate
  anvil_q1_ht2_attention #(
    .NUM_Q_HEADS(Q), .NUM_KV_HEADS(K), .HEAD_DIM(D), .MAX_SEQ_LEN(S)
  ) u_attention (
    .clk(clk), .rst_n(run_n), .abort_error(cancel),
    .cmd_valid(state == ATTN_COMMAND && !cancel), .cmd_ready(a_ready),
    .cmd_fp16(fp16), .cmd_slots(slots), .cmd_prefix_length(prefix_length),
    .cmd_positions(positions), .cmd_ancestors(ancestors),
    .query_valid(state == ATTN_INPUT && !cancel), .query_ready(a_query_ready),
    .query_data(encoded_query_q),
    .kv_valid(kv_read_valid), .kv_ready(kv_read_ready),
    .kv_provisional(kv_read_provisional), .kv_node(kv_read_node),
    .kv_position(kv_read_position), .kv_head(kv_read_head), .kv_column(kv_read_column),
    .kv_rsp_valid(kv_rsp_valid), .kv_rsp_ready(kv_rsp_ready),
    .kv_key(kv_key), .kv_value(kv_value), .kv_rsp_error(kv_rsp_error),
    .out_valid(a_valid), .out_ready(state == ATTN_OUTPUT || state == FAIL_DRAIN),
    .out_index(a_index), .out_data(a_data), .out_slots(a_slots),
    .busy(a_busy), .done(a_done), .error(a_error)
  );
  anvil_q1_ht2_swiglu #(.INTERMEDIATE_SIZE(I)) u_swiglu (
    .clk(clk), .rst_n(run_n), .abort_error(cancel),
    .cmd_valid(state == SWIGLU_COMMAND && !cancel), .cmd_ready(w_ready),
    .cmd_slots(slots), .cmd_fp16(fp16),
    .in_valid(state == SWIGLU_INPUT && !cancel), .in_ready(w_input_ready),
    .in_gate(gate_q), .in_up(up_q),
    .out_valid(w_valid), .out_ready(swiglu_active || state == FAIL_DRAIN),
    .out_index(w_index), .out_data(), .out_activation(w_activation),
    .out_nonzero(w_nonzero), .out_slots(w_slots),
    .busy(w_busy), .done(w_done), .error(w_error)
  );

  assign cmd_ready = run_n && state == IDLE && !abort_error;
  assign lookup_valid = run_n && state == LOOKUP_SEND && !cancel;
  assign lookup_index = !lookup_valid ? 32'b0 :
    ({27'b0, descriptor_layer} << 6) + ({27'b0, descriptor_layer} << 5) +
    ({28'b0, descriptor_kind} << 3) + {29'b0, descriptor_projection};
  assign lookup_rsp_ready = run_n && (state == LOOKUP_WAIT || state == FAIL_DRAIN);
  assign kv_store_valid = run_n && state == STORE_SEND && slots[store_node] && !cancel;
  assign kv_store_node = kv_store_valid ? store_node : 2'b0;
  assign kv_store_layer = kv_store_valid ? {27'b0, layer} : 32'b0;
  assign kv_store_column = kv_store_valid ? {19'b0, vector_index} : 32'b0;
  assign kv_store_first = kv_store_valid && vector_index == 0;
  assign kv_store_last = kv_store_valid && vector_index + 1 == C;
  assign kv_store_key = kv_store_valid ? encoded_key_q[16*store_node+:16] : 16'b0;
  assign kv_store_value = kv_store_valid ? encoded_value_q[16*store_node+:16] : 16'b0;
  assign kv_read_layer = kv_read_valid ? {27'b0, layer} : 32'b0;
  assign logit_valid = run_n && state == ROW_EMIT && !failed;
  assign logit_index = logit_valid ? row_index : 32'b0;
  assign logit_data = logit_valid ? row_value : 128'b0;
  assign logit_slots = logit_valid ? slots : 4'b0;
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_targets = rsp_valid && !failed ? targets : 128'b0;
  assign rsp_error = rsp_valid && failed;
  assign busy = run_n && state != IDLE;
  assign done = run_n && state == COMPLETE;

  always @(posedge clk) begin
    if (run_n) begin
      if (state == NORM_READ) residual_q <= residuals[vector_index];
      if (state == PROJ_READ) begin
        if (projection == 6) intermediate_q <= intermediate_vectors[vector_index];
        else if (projection == 3) attention_q <= attention_vectors[vector_index];
        else normalized_q <= normalized[vector_index];
      end
      if (state == ROW_RESIDUAL) residual_q <= residuals[row_index];
      if (state == ROPE_READ) begin
        if (rope_key) begin
          key_first_q <= keys[rope_first_index];
          key_second_q <= keys[rope_second_index];
        end else begin
          query_first_q <= queries[rope_first_index];
          query_second_q <= queries[rope_second_index];
        end
      end
      if (state == STORE_READ) begin
        encoded_key_q <= key_encoded[vector_index];
        encoded_value_q <= value_encoded[vector_index];
      end
      if (state == ATTN_READ) encoded_query_q <= query_encoded[vector_index];
      if (state == SWIGLU_READ) begin
        gate_q <= gate_vectors[vector_index];
        up_q <= up_vectors[vector_index];
      end
      if (!cancel) begin
        if (state == EMB_STORE) residuals[vector_index] <= embedding_word;
        if (state == NORM_OUTPUT && n_valid && n_index < H && n_slots == slots)
          normalized[n_index] <= n_data;
        if (state == ROW_STORE && !row_bad && row_active) begin
          case (projection)
            0: queries[row_index] <= row_value;
            1: keys[row_index] <= row_value;
            2: if (!narrowing_bad) value_encoded[row_index] <= row_encoded;
            3, 6: residuals[row_index] <= row_value;
            4: gate_vectors[row_index] <= row_value;
            5: up_vectors[row_index] <= row_value;
            default: begin end
          endcase
        end
        if (state == ROPE_OUTPUT && selected_rope_valid &&
            r_slots[4*rope_key+:4] == slots) begin
          if (rope_key) begin
            if (selected_rope_first < C && selected_rope_second < C) begin
              key_encoded[selected_rope_first] <= selected_rope_first_encoded;
              key_encoded[selected_rope_second] <= selected_rope_second_encoded;
            end
          end else if (selected_rope_first < H && selected_rope_second < H) begin
            query_encoded[selected_rope_first] <= selected_rope_first_encoded;
            query_encoded[selected_rope_second] <= selected_rope_second_encoded;
          end
        end
        if (state == ATTN_OUTPUT && a_valid && a_index < H && a_slots == slots)
          attention_vectors[a_index] <= a_data;
        if (swiglu_response && !swiglu_bad)
          intermediate_vectors[w_index] <= {w_nonzero, w_activation};
      end
    end
  end

  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      lookup_return <= IDLE;
      fetch_return <= IDLE;
      format <= 0;
      norm_phase <= 0;
      slots <= 0;
      tokens <= 0;
      positions <= 0;
      ancestors <= 0;
      threshold <= 0;
      prefix_length <= 0;
      emit_logits <= 0;
      sparse <= 0;
      finite_weights <= 0;
      failed <= 0;
      layer <= 0;
      projection <= 0;
      vector_index <= 0;
      swiglu_received <= 0;
      embedding_slot <= 0;
      store_node <= 0;
      embedding_word <= 0;
      row_value <= 0;
      row_operand <= 0;
      targets <= 0;
      maxima <= 0;
      maximum_owned <= 0;
      row_lane <= 0;
      expected_panel <= 0;
      rope_key <= 0;
      rope_base <= 0;
      rope_pair <= 0;
      descriptor_kind <= 0;
      descriptor_projection <= 0;
      descriptor_layer <= 0;
      scalar_base <= 0;
      scalar_length <= 0;
      expected_scalar_length <= 0;
      weight_base <= 0;
      zero_base <= 0;
      scale_base <= 0;
      weight_length <= 0;
      zero_length <= 0;
      scale_length <= 0;
      fetch_offset <= 0;
      fetch_absolute <= 0;
      fetch_index <= 0;
      fetch_embedding <= 0;
      fetched_word <= 0;
      cache_valid <= 0;
      cache_address <= 0;
      cache_data <= 0;
      lookup_owned <= 0;
    end else begin
      if (lookup_valid && lookup_ready) lookup_owned <= 1;
      if (lookup_rsp_valid && lookup_rsp_ready) lookup_owned <= 0;
      if (swiglu_response && !swiglu_bad) swiglu_received <= swiglu_received + 1'b1;
      if ((abort_error || kv_store_error || worker_error || swiglu_bad) &&
          state != IDLE && state != RESPONSE && state != COMPLETE && state != FAIL_DRAIN) begin
        failed <= 1;
        state <= FAIL_DRAIN;
      end else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          format <= cmd_format;
          slots <= cmd_slots;
          tokens <= cmd_tokens;
          positions <= cmd_positions;
          ancestors <= cmd_ancestors;
          prefix_length <= cmd_prefix_length;
          emit_logits <= cmd_emit_logits;
          sparse <= cmd_sparse;
          finite_weights <= cmd_finite_weights;
          threshold <= cmd_threshold;
          cache_valid <= 0;
          failed <= command_bad;
          maximum_owned <= 0;
          targets <= 0;
          maxima <= 0;
          layer <= 0;
          norm_phase <= 0;
          vector_index <= 0;
          embedding_slot <= 0;
          embedding_word <= 0;
          descriptor_kind <= 0;
          descriptor_projection <= 0;
          descriptor_layer <= 0;
          lookup_return <= EMB_DESCRIPTOR;
          if (command_bad) state <= RESPONSE;
          else state <= LOOKUP_SEND;
        end
        LOOKUP_SEND: if (lookup_valid && lookup_ready) state <= LOOKUP_WAIT;
        LOOKUP_WAIT: if (lookup_rsp_valid) begin
          if (lookup_error || lookup_length == 0 || (|lookup_base[5:0]) ||
              lookup_end > 34'h200000000) begin
            failed <= 1;
            state <= FAIL_DRAIN;
          end else begin
            scalar_base <= lookup_base;
            scalar_length <= lookup_length;
            state <= lookup_return;
          end
        end
        EMB_DESCRIPTOR: begin
          if (scalar_length != EMBEDDING_BYTES) begin failed <= 1; state <= FAIL_DRAIN; end
          else state <= EMB_BEGIN;
        end
        EMB_BEGIN: begin
          fetch_embedding <= 1;
          fetch_index <= {19'b0, vector_index};
          fetch_return <= EMB_WORD;
          if (!slots[embedding_slot]) begin
            embedding_word[32*embedding_slot+:32] <= 0;
            if (embedding_slot == 3) state <= EMB_STORE;
            else embedding_slot <= embedding_slot + 1'b1;
          end else state <= FETCH_ADDRESS;
        end
        EMB_WORD: begin
          if (fetch_bad) begin failed <= 1; state <= FAIL_DRAIN; end
          else begin
            embedding_word[32*embedding_slot+:32] <= expanded_fetched;
            if (embedding_slot == 3) state <= EMB_STORE;
            else begin embedding_slot <= embedding_slot + 1'b1; state <= EMB_BEGIN; end
          end
        end
        EMB_STORE: begin
          if (vector_index + 1 == H) begin norm_phase <= 0; state <= NORM_BEGIN; end
          else begin
            vector_index <= vector_index + 1'b1;
            embedding_slot <= 0;
            state <= EMB_BEGIN;
          end
        end
        FETCH_ADDRESS: begin
          if (fetch_embedding)
            fetch_offset <= {32'b0, (tokens[32*embedding_slot+:32] >> 6)}*(H*128) +
              ({32'b0, fetch_index} << 7) +
              {57'b0, tokens[32*embedding_slot+:6], 1'b0};
          else fetch_offset <= {32'b0, fetch_index} << 1;
          state <= FETCH_CHECK;
        end
        FETCH_CHECK: begin
          fetch_absolute <= candidate_fetch_address[33:0];
          if (fetch_offset + 64'd2 > {32'b0, scalar_length} ||
              candidate_fetch_address + 64'd2 > 64'h200000000 ||
              scalar_end > 34'h200000000) begin failed <= 1; state <= FAIL_DRAIN; end
          else if (cache_valid && cache_address == {candidate_fetch_address[32:6], 6'b0}) begin
            fetched_word <= cache_data[8*candidate_fetch_address[5:0]+:16];
            state <= fetch_return;
          end else state <= FETCH_SEND;
        end
        FETCH_SEND: if (scalar_command && s_ready) state <= FETCH_WAIT;
        FETCH_WAIT: if (scalar_response) begin
          if (s_error) begin failed <= 1; state <= FAIL_DRAIN; end
          else begin
            cache_valid <= 1;
            cache_address <= {fetch_absolute[32:6], 6'b0};
            cache_data <= s_data[511:0];
            state <= FETCH_WORD;
          end
        end
        FETCH_WORD: begin
          fetched_word <= cache_data[8*fetch_absolute[5:0]+:16];
          state <= fetch_return;
        end
        NORM_BEGIN: begin
          descriptor_kind <= norm_phase == 0 ? 4'd5 : norm_phase == 1 ? 4'd6 : 4'd7;
          descriptor_layer <= norm_phase == 2 ? 5'd0 : layer;
          descriptor_projection <= 0;
          lookup_return <= NORM_DESCRIPTOR;
          state <= LOOKUP_SEND;
        end
        NORM_DESCRIPTOR: begin
          if (scalar_length != NORM_BYTES) begin failed <= 1; state <= FAIL_DRAIN; end
          else state <= NORM_COMMAND;
        end
        NORM_COMMAND: if (n_ready) begin vector_index <= 0; state <= NORM_READ; end
        NORM_READ: state <= NORM_FETCH;
        NORM_FETCH: begin
          fetch_embedding <= 0;
          fetch_index <= {19'b0, vector_index};
          fetch_return <= NORM_INPUT;
          state <= FETCH_ADDRESS;
        end
        NORM_INPUT: begin
          if (fetch_bad) begin failed <= 1; state <= FAIL_DRAIN; end
          else if (n_input_ready) begin
            if (vector_index + 1 == H) begin vector_index <= 0; state <= NORM_OUTPUT; end
            else begin vector_index <= vector_index + 1'b1; state <= NORM_READ; end
          end
        end
        NORM_OUTPUT: if (n_valid) begin
          if (n_index != vector_index || n_slots != slots) begin
            failed <= 1; state <= FAIL_DRAIN;
          end else if (vector_index + 1 == H) state <= NORM_FINISH;
          else vector_index <= vector_index + 1'b1;
        end
        NORM_FINISH: if (n_done) begin
          projection <= norm_phase == 0 ? 3'd0 : norm_phase == 1 ? 3'd4 : 3'd7;
          state <= PROJ_BEGIN;
        end
        PROJ_BEGIN: begin
          descriptor_kind <= projection == 7 ? 4'd0 : 4'd1;
          descriptor_projection <= projection == 7 ? 3'd0 : projection;
          descriptor_layer <= projection == 7 ? 5'd0 : layer;
          lookup_return <= PROJ_WEIGHT;
          state <= LOOKUP_SEND;
        end
        PROJ_WEIGHT: begin
          weight_base <= scalar_base;
          weight_length <= scalar_length;
          zero_base <= 0;
          scale_base <= 0;
          zero_length <= 0;
          scale_length <= 0;
          if (awq_projection) begin
            descriptor_kind <= 2;
            lookup_return <= PROJ_ZERO;
            state <= LOOKUP_SEND;
          end else state <= PROJ_BIAS_BEGIN;
        end
        PROJ_ZERO: begin
          zero_base <= scalar_base;
          zero_length <= scalar_length;
          descriptor_kind <= 3;
          lookup_return <= PROJ_SCALE;
          state <= LOOKUP_SEND;
        end
        PROJ_SCALE: begin
          scale_base <= scalar_base;
          scale_length <= scalar_length;
          state <= PROJ_BIAS_BEGIN;
        end
        PROJ_BIAS_BEGIN: begin
          if (projection < 3) begin
            descriptor_kind <= 4;
            expected_scalar_length <= projection == 0 ? NORM_BYTES : KV_BIAS_BYTES;
            lookup_return <= PROJ_BIAS;
            state <= LOOKUP_SEND;
          end else state <= PROJ_COMMAND;
        end
        PROJ_BIAS: begin
          if (scalar_length != expected_scalar_length) begin failed <= 1; state <= FAIL_DRAIN; end
          else state <= PROJ_COMMAND;
        end
        PROJ_COMMAND: if (p_ready) begin
          vector_index <= 0;
          expected_panel <= 0;
          state <= PROJ_READ;
        end
        PROJ_READ: state <= PROJ_INPUT;
        PROJ_INPUT: begin
          if (input_narrowing_bad) begin failed <= 1; state <= FAIL_DRAIN; end
          else if (p_activation_ready) begin
            if ({19'b0, vector_index} + 1 == projection_inputs) state <= PROJ_OUTPUT;
            else begin vector_index <= vector_index + 1'b1; state <= PROJ_READ; end
          end
        end
        PROJ_OUTPUT: if (p_valid) begin
          if (p_slots != slots || p_panel != expected_panel ||
              p_panel >= projection_outputs || p_mask != expected_panel_mask) begin
            failed <= 1; state <= FAIL_DRAIN;
          end
          else begin row_lane <= 0; state <= ROW_BEGIN; end
        end
        ROW_BEGIN: begin
          row_value <= selected_panel_row;
          if (!row_active) state <= ROW_NEXT;
          else if (row_index >= projection_outputs) begin failed <= 1; state <= FAIL_DRAIN; end
          else if (projection < 3) begin
            fetch_embedding <= 0;
            fetch_index <= row_index;
            fetch_return <= ROW_BIAS;
            state <= FETCH_ADDRESS;
          end else if (projection == 3 || projection == 6) state <= ROW_RESIDUAL;
          else state <= ROW_STORE;
        end
        ROW_BIAS: begin
          if (fetch_bad) begin failed <= 1; state <= FAIL_DRAIN; end
          else begin row_operand <= {4{expanded_fetched}}; state <= ROW_ADD_SEND; end
        end
        ROW_RESIDUAL: state <= ROW_ADD_SEND;
        ROW_ADD_SEND: state <= ROW_ADD_WAIT;
        ROW_ADD_WAIT: if (&add_valid) begin row_value <= add_data; state <= ROW_STORE; end
        ROW_STORE: begin
          if (row_bad || (projection == 2 && narrowing_bad)) begin
            failed <= 1;
            state <= FAIL_DRAIN;
          end else if (projection == 7) begin
            for (update_slot = 0; update_slot < 4; update_slot = update_slot + 1) begin
              if (slots[update_slot] && (!maximum_owned[update_slot] ||
                  greater32(row_value[32*update_slot+:32], maxima[32*update_slot+:32]))) begin
                maxima[32*update_slot+:32] <= row_value[32*update_slot+:32];
                targets[32*update_slot+:32] <= row_index;
                maximum_owned[update_slot] <= 1;
              end
            end
            if (emit_logits) state <= ROW_EMIT;
            else state <= ROW_NEXT;
          end else state <= ROW_NEXT;
        end
        ROW_EMIT: if (logit_valid && logit_ready) state <= ROW_NEXT;
        ROW_NEXT: begin
          if (row_lane == 63) state <= PROJ_RETIRE;
          else begin row_lane <= row_lane + 1'b1; state <= ROW_BEGIN; end
        end
        PROJ_RETIRE: if (p_valid) begin
          if (last_panel) state <= PROJ_FINISH;
          else begin expected_panel <= expected_panel + 32'd64; state <= PROJ_OUTPUT; end
        end
        PROJ_FINISH: if (p_done) begin
          case (projection)
            0, 1, 4: begin projection <= projection + 1'b1; state <= PROJ_BEGIN; end
            2: begin rope_key <= 0; rope_base <= 0; rope_pair <= 0; state <= ROPE_COMMAND; end
            3: begin norm_phase <= 1; state <= NORM_BEGIN; end
            5: state <= SWIGLU_COMMAND;
            6: begin
              if (layer + 1 == L) begin norm_phase <= 2; state <= NORM_BEGIN; end
              else begin layer <= layer + 1'b1; norm_phase <= 0; state <= NORM_BEGIN; end
            end
            7: begin
              if ((maximum_owned & slots) != slots) begin failed <= 1; state <= FAIL_DRAIN; end
              else state <= RESPONSE;
            end
            default: begin failed <= 1; state <= FAIL_DRAIN; end
          endcase
        end
        ROPE_COMMAND: if (r_ready[rope_key]) state <= ROPE_READ;
        ROPE_READ: state <= ROPE_INPUT;
        ROPE_INPUT: if (r_input_ready[rope_key]) state <= ROPE_OUTPUT;
        ROPE_OUTPUT: if (selected_rope_valid) begin
          if (selected_rope_first != {22'b0, rope_first_index} ||
              selected_rope_second != {22'b0, rope_second_index} ||
              r_slots[4*rope_key+:4] != slots) begin failed <= 1; state <= FAIL_DRAIN; end
          else if (rope_pair + 1 == (D >> 1)) begin
            rope_pair <= 0;
            if ({22'b0, rope_base} + D == (rope_key ? C : H)) state <= ROPE_FINISH;
            else begin rope_base <= rope_base + D; state <= ROPE_READ; end
          end else begin rope_pair <= rope_pair + 1'b1; state <= ROPE_READ; end
        end
        ROPE_FINISH: if (selected_rope_done) begin
          if (!rope_key) begin
            rope_key <= 1;
            rope_base <= 0;
            rope_pair <= 0;
            state <= ROPE_COMMAND;
          end else begin vector_index <= 0; store_node <= 0; state <= STORE_READ; end
        end
        STORE_READ: state <= STORE_SEND;
        STORE_SEND: begin
          if (!slots[store_node]) begin
            if (store_node == 3) state <= STORE_SETTLE;
            else begin store_node <= store_node + 1'b1; vector_index <= 0; state <= STORE_READ; end
          end else if (kv_store_valid && kv_store_ready) begin
            if (vector_index + 1 == C) begin
              if (store_node == 3) state <= STORE_SETTLE;
              else begin store_node <= store_node + 1'b1; vector_index <= 0; state <= STORE_READ; end
            end else begin vector_index <= vector_index + 1'b1; state <= STORE_READ; end
          end
        end
        STORE_SETTLE: state <= ATTN_COMMAND;
        ATTN_COMMAND: if (a_ready) begin vector_index <= 0; state <= ATTN_READ; end
        ATTN_READ: state <= ATTN_INPUT;
        ATTN_INPUT: if (a_query_ready) begin
          if (vector_index + 1 == H) begin vector_index <= 0; state <= ATTN_OUTPUT; end
          else begin vector_index <= vector_index + 1'b1; state <= ATTN_READ; end
        end
        ATTN_OUTPUT: if (a_valid) begin
          if (a_index != {19'b0, vector_index} || a_slots != slots) begin
            failed <= 1; state <= FAIL_DRAIN;
          end else if (vector_index + 1 == H) state <= ATTN_FINISH;
          else vector_index <= vector_index + 1'b1;
        end
        ATTN_FINISH: if (a_done) begin projection <= 3; state <= PROJ_BEGIN; end
        SWIGLU_COMMAND: if (w_ready) begin
          vector_index <= 0;
          swiglu_received <= 0;
          state <= SWIGLU_READ;
        end
        SWIGLU_READ: state <= SWIGLU_INPUT;
        SWIGLU_INPUT: if (w_input_ready) begin
          if (vector_index + 1 == I) state <= SWIGLU_OUTPUT;
          else begin vector_index <= vector_index + 1'b1; state <= SWIGLU_READ; end
        end
        SWIGLU_OUTPUT: if (swiglu_received == I) state <= SWIGLU_FINISH;
        SWIGLU_FINISH: if (w_done) begin projection <= 6; state <= PROJ_BEGIN; end
        FAIL_DRAIN: if (!workers_busy && !dma_owned && !s_valid && !lookup_owned)
          state <= RESPONSE;
        RESPONSE: if (rsp_valid && rsp_ready) state <= COMPLETE;
        COMPLETE: state <= IDLE;
        default: begin failed <= 1; state <= FAIL_DRAIN; end
      endcase
    end
  end
endmodule
