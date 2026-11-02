module anvil_q1_ht3_decoder #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2, HEAD_DIM = 64,
  parameter GROUP_SIZE = 128, VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768,
  parameter TILE_BEATS = 256, FLASH_TILE = 16
) (
  input wire clk, rst_n, abort_error, cmd_valid,
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
  output wire rsp_error, busy, done,
  output wire stats_valid,
  output wire [31:0] stats_dense_bytes, stats_avoided_bytes, stats_replay_bytes,
  output wire stats_replay_column,
  input wire [1:0] cmd_kv_format,
  input wire cmd_int8_weights,
  input wire [32:0] cmd_extension_base,
  input wire [31:0] cmd_extension_length, cmd_image,
  output wire [1:0] kv_store_format,
  output wire [31:0] kv_store_image,
  output wire kv_store_fault,
  output wire [31:0] kv_read_key_scale, kv_read_value_scale,
  input wire [31:0] kv_key_scale, kv_value_scale
);
  import anvil_q1_ht3_fp_pkg::*;
  import anvil_q1_ht3_layout_pkg::*;
  localparam LEGAL = geometry_legal(NUM_LAYERS, HIDDEN_SIZE, INTERMEDIATE_SIZE,
    NUM_Q_HEADS, NUM_KV_HEADS, HEAD_DIM, GROUP_SIZE, VOCAB_SIZE, MAX_SEQ_LEN) &&
    TILE_BEATS >= 1 && TILE_BEATS <= 256 && FLASH_TILE >= 1 && FLASH_TILE <= 128;
  initial if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 decoder geometry");
  generate if (!LEGAL) begin: g_invalid
    assign cmd_ready = 0;
    assign lookup_valid = 0;
    assign lookup_index = 0;
    assign lookup_rsp_ready = 0;
    assign dma_valid = 0;
    assign dma_address = 0;
    assign dma_burstcount = 0;
    assign dma_data_ready = 0;
    assign kv_store_valid = 0;
    assign kv_store_node = 0;
    assign kv_store_layer = 0;
    assign kv_store_column = 0;
    assign kv_store_first = 0;
    assign kv_store_last = 0;
    assign kv_store_key = 0;
    assign kv_store_value = 0;
    assign kv_store_format = 0;
    assign kv_store_image = 0;
    assign kv_store_fault = 0;
    assign kv_read_valid = 0;
    assign kv_read_provisional = 0;
    assign kv_read_node = 0;
    assign kv_read_layer = 0;
    assign kv_read_position = 0;
    assign kv_read_head = 0;
    assign kv_read_column = 0;
    assign kv_read_key_scale = 0;
    assign kv_read_value_scale = 0;
    assign kv_rsp_ready = 0;
    assign logit_valid = 0;
    assign logit_index = 0;
    assign logit_data = 0;
    assign logit_slots = 0;
    assign rsp_valid = 0;
    assign rsp_targets = 0;
    assign rsp_error = 0;
    assign busy = 0;
    assign done = 0;
    assign stats_valid = 0;
    assign stats_dense_bytes = 0;
    assign stats_avoided_bytes = 0;
    assign stats_replay_bytes = 0;
    assign stats_replay_column = 0;
  end else begin: g_legal
    localparam L = NUM_LAYERS, H = HIDDEN_SIZE, I = INTERMEDIATE_SIZE;
    localparam C = NUM_KV_HEADS*HEAD_DIM, V = VOCAB_SIZE, S = MAX_SEQ_LEN;
    localparam M = H > I ? H : I;
    localparam EMB_BYTES = ((V+63) >> 6)*H*128;
    localparam NORM_BYTES = ((2*H+63) >> 6)*64;
    localparam KV_BIAS_BYTES = ((2*C+63) >> 6)*64;
    localparam WEIGHT_ENTRIES = layer_scale_entries(H, I, C, GROUP_SIZE);
    localparam [223:0] SCALE_OFFSETS = {
      32'(projection_scale_offset(6,H,I,C,GROUP_SIZE)),
      32'(projection_scale_offset(5,H,I,C,GROUP_SIZE)),
      32'(projection_scale_offset(4,H,I,C,GROUP_SIZE)),
      32'(projection_scale_offset(3,H,I,C,GROUP_SIZE)),
      32'(projection_scale_offset(2,H,I,C,GROUP_SIZE)),
      32'(projection_scale_offset(1,H,I,C,GROUP_SIZE)),
      32'(projection_scale_offset(0,H,I,C,GROUP_SIZE))};
    localparam [223:0] SCALE_LENGTHS = {
      32'(4*projection_scale_entries(6,H,I,C,GROUP_SIZE)),
      32'(4*projection_scale_entries(5,H,I,C,GROUP_SIZE)),
      32'(4*projection_scale_entries(4,H,I,C,GROUP_SIZE)),
      32'(4*projection_scale_entries(3,H,I,C,GROUP_SIZE)),
      32'(4*projection_scale_entries(2,H,I,C,GROUP_SIZE)),
      32'(4*projection_scale_entries(1,H,I,C,GROUP_SIZE)),
      32'(4*projection_scale_entries(0,H,I,C,GROUP_SIZE))};
    localparam IDLE = 6'd0, LOOKUP_SEND = 6'd1, LOOKUP_WAIT = 6'd2,
      EMB_DESCRIPTOR = 6'd3, EMB_BEGIN = 6'd4, EMB_WORD = 6'd5, EMB_STORE = 6'd6,
      FETCH_CHECK = 6'd7, FETCH_SEND = 6'd8, FETCH_WAIT = 6'd9, FETCH_WORD = 6'd10,
      LAYER_BEGIN = 6'd11, SCALE_FETCH = 6'd12, SCALE_WORD = 6'd13,
      NORM_BEGIN = 6'd14, NORM_DESCRIPTOR = 6'd15, NORM_COMMAND = 6'd16,
      NORM_READ = 6'd17, NORM_FETCH = 6'd18, NORM_INPUT = 6'd19,
      E_OUTPUT = 6'd20, E_FINISH = 6'd21, PROJ_BEGIN = 6'd22,
      PROJ_WEIGHT = 6'd23, PROJ_ZERO = 6'd24, PROJ_SCALE = 6'd25,
      PROJ_BIAS_BEGIN = 6'd26, PROJ_BIAS = 6'd27,
      PROJ_NORM_BEGIN = 6'd28, PROJ_NORM = 6'd29, E_COMMAND = 6'd30,
      PROJ_COMMAND = 6'd31, PROJ_READ = 6'd32, PROJ_INPUT = 6'd33,
      PROJ_OUTPUT = 6'd34, ROW_BEGIN = 6'd35, ROW_BIAS = 6'd36,
      ROW_RESIDUAL = 6'd37, ROW_AUX = 6'd38, ROW_GAMMA = 6'd39,
      ROW_GAMMA_WORD = 6'd40, ROW_ADD_SEND = 6'd41, ROW_ADD_WAIT = 6'd42,
      ROW_STORE = 6'd43, ROW_E_INPUT = 6'd44, ROW_EMIT = 6'd45,
      ROW_NEXT = 6'd46, PROJ_RETIRE = 6'd47, PROJ_FINISH = 6'd48,
      STORE_READ = 6'd49, STORE_ISSUE = 6'd50, STORE_WAIT = 6'd51,
      STORE_SETTLE = 6'd52, ATTN_COMMAND = 6'd53, ATTN_READ = 6'd54,
      ATTN_INPUT = 6'd55, ATTN_OUTPUT = 6'd56, ATTN_FINISH = 6'd57,
      FAIL_DRAIN = 6'd58, RESPONSE = 6'd59, COMPLETE = 6'd60, ROW_AUX_LOAD = 6'd61;
    wire run_n;
    reg [5:0] state, lookup_return, fetch_return;
    reg [1:0] format_q, kv_format_q, embedding_slot, store_node;
    reg [3:0] slots_q;
    reg [127:0] tokens_q, positions_q;
    reg [15:0] ancestors_q, threshold_q, fetched_word, gamma_q;
    reg [31:0] prefix_q, image_q, extension_length_q;
    reg [32:0] extension_base_q;
    reg int8_q, emit_q, sparse_q, finite_q, failed, initial_norm;
    reg [4:0] layer_q;
    reg [2:0] projection_q;
    reg [12:0] index_q;
    reg [5:0] row_lane;
    reg [31:0] expected_panel;
    reg [1:0] scale_index, store_head;
    reg [6:0] store_dimension;
    reg [127:0] scales_q;
    reg [127:0] embedding_word, row_value, row_aux, row_sum, targets, maxima;
    reg [3:0] maximum_owned;
    reg [3:0] descriptor_kind;
    reg [2:0] descriptor_projection;
    reg [4:0] descriptor_layer;
    reg [32:0] scalar_base, weight_base, zero_base, scale_base, bias_base, norm_base;
    reg [31:0] scalar_length, weight_length, zero_length, scale_length, bias_length;
    reg [32:0] fetch_base;
    reg [31:0] fetch_length;
    reg [63:0] fetch_offset;
    reg [32:0] fetch_absolute;
    reg fetch_fp32, cache_valid, lookup_owned, scalar_owned;
    reg [32:0] cache_address;
    reg [511:0] cache_data;
    reg [31:0] fetched_scale;
    reg command_bad, row_bad, narrowing_bad, input_bad, output_bad;
    reg [3:0] ancestor_count;
    reg [32:0] expected_position;
    integer node, ancestor, peer, s, update_slot;
    genvar slot;
    wire fp16 = format_q == 1;
    wire int8_projection = int8_q && projection_q < 7;
    wire [1:0] projection_format = projection_q == 7 && format_q == 2 ?
      2'b0 : format_q;
    wire awq_projection = projection_format == 2 && !int8_projection;
    wire [31:0] projection_inputs = projection_q == 6 ? I : H;
    wire [31:0] projection_outputs = projection_q == 1 || projection_q == 2 ?
      C : projection_q == 4 || projection_q == 5 ? I : projection_q == 7 ? V : H;
    wire projection_epilogue = projection_q == 0 || projection_q == 1 ||
      projection_q == 3 || projection_q == 5 || projection_q == 6;
    wire residual_projection = projection_q == 3 || projection_q == 6;
    wire [2:0] epilogue_op = initial_norm ? 3'd1 :
      residual_projection ? 3'd6 : projection_q == 5 ? 3'd3 : 3'd2;
    wire [12:0] epilogue_length = initial_norm ? 13'(H) : projection_outputs[12:0];
    wire [31:0] row_index = p_panel + {26'b0, row_lane};
    wire row_active = p_mask[row_lane];
    wire last_panel = p_panel + 64 >= projection_outputs;
    wire [31:0] remaining_rows = projection_outputs - expected_panel;
    wire [63:0] expected_mask = remaining_rows >= 64 ? 64'hffffffffffffffff :
      64'hffffffffffffffff >> (64-remaining_rows);
    wire [63:0] fetch_candidate = {31'b0, fetch_base} + fetch_offset;
    wire [33:0] fetch_end = {1'b0, fetch_base} + {2'b0, fetch_length};
    wire [33:0] lookup_end = {1'b0, lookup_base} + {2'b0, lookup_length};
    wire [31:0] expanded_fetched = expand16(fetched_word, fp16);
    wire [31:0] projection_scale_offset_q = projection_q < 7 ?
      SCALE_OFFSETS[32*projection_q+:32] : 32'b0;
    wire [31:0] projection_scale_length_q = projection_q < 7 ?
      SCALE_LENGTHS[32*projection_q+:32] : 32'b0;
    wire [63:0] layer_weight_scale_offset = 64'(layer_q)*(4*WEIGHT_ENTRIES);
    wire [63:0] kv_scale_offset = (int8_q ? 64'(4*L*WEIGHT_ENTRIES) : 64'd0) +
      64'(layer_q)*(8*NUM_KV_HEADS) + {60'b0, scale_index, 2'b0};
    wire [63:0] int8_scale_candidate = {31'b0, extension_base_q} +
      layer_weight_scale_offset + {32'b0, projection_scale_offset_q};
    wire [31:0] required_extension_bytes = int8_q ?
      32'(4*L*WEIGHT_ENTRIES) + (kv_format_q[1] ? 32'(8*L*NUM_KV_HEADS) : 32'd0) :
      (kv_format_q[1] ? 32'(8*L*NUM_KV_HEADS) : 32'd0);
    wire [33:0] command_extension_end = {1'b0, cmd_extension_base} +
      {2'b0, cmd_extension_length};

    (* ramstyle = "M20K", nomem2reg *) reg [127:0] residuals [0:H-1];
    (* ramstyle = "M20K", nomem2reg *) reg [127:0] normalized [0:H-1];
    (* ramstyle = "M20K", nomem2reg *) reg [63:0] queries [0:H-1];
    (* ramstyle = "M20K", nomem2reg *) reg [127:0] keys [0:C-1];
    (* ramstyle = "M20K", nomem2reg *) reg [127:0] values [0:C-1];
    (* ramstyle = "M20K", nomem2reg *) reg [127:0] attention_vectors [0:H-1];
    (* ramstyle = "M20K", nomem2reg *) reg [127:0] gates [0:I-1];
    (* ramstyle = "M20K", nomem2reg *) reg [67:0] intermediates [0:I-1];
    reg [127:0] residual_read, normalized_read, attention_read, gate_read;
    reg [127:0] key_read, value_read;
    reg [63:0] query_read;
    reg [67:0] intermediate_read;
    wire [127:0] activation_source = projection_q == 3 ? attention_read : normalized_read;
    wire [63:0] activation_data;
    wire [3:0] activation_nonzero;
    wire [127:0] panel_row;
    wire [63:0] row_encoded;
    wire [3:0] add_valid;
    wire [127:0] add_data;
    wire [127:0] row_add_a = residual_projection ? row_aux : row_value;
    wire [127:0] row_add_b = residual_projection ? row_value : row_aux;
    wire e_ready, e_in_ready, e_valid, e_busy, e_done, e_error;
    wire [31:0] e_index;
    wire [127:0] e_data;
    wire [63:0] e_encoded;
    wire [3:0] e_slots;
    wire p_ready, p_in_ready, p_valid, p_busy, p_done, p_error;
    wire [31:0] p_panel;
    wire [8191:0] p_data;
    wire [63:0] p_mask;
    wire [3:0] p_slots;
    wire a_ready, a_in_ready, a_valid, a_busy, a_done, a_error;
    wire [31:0] a_index;
    wire [127:0] a_data;
    wire [3:0] a_slots;
    wire convert_ready, convert_busy;
    wire [3:0] mux_ready, mux_valid;
    wire [511:0] mux_data;
    wire mux_error, mux_busy, mux_fault;
    wire p_dma_valid, p_dma_ready, p_dma_data_ready;
    wire [32:0] p_dma_address;
    wire [7:0] p_dma_beats;
    wire r_ready, r_valid, r_error, r_dma_valid, r_dma_ready, r_dma_data_ready;
    wire [32:0] r_dma_address;
    wire [7:0] r_dma_beats;
    wire [1023:0] r_data;
    wire cancel = failed || abort_error || kv_store_error;
    wire worker_error = p_error || e_error || a_error || mux_fault ||
      kv_store_fault;
    wire scalar_request = run_n && state == FETCH_SEND && !cancel;
    wire scalar_response = r_valid && (state == FETCH_WAIT || state == FAIL_DRAIN);
    wire e_input = run_n && !cancel &&
      ((state == ROW_GAMMA_WORD && initial_norm) || state == ROW_E_INPUT);
    wire e_response = e_valid && (state == E_OUTPUT || state == FAIL_DRAIN);
    wire a_response = a_valid && (state == ATTN_OUTPUT || state == FAIL_DRAIN);

    function automatic greater32(input [31:0] a, input [31:0] b);
      begin
        if (a[30:0] == 0 && b[30:0] == 0) greater32 = 0;
        else if (a[31] != b[31]) greater32 = !a[31];
        else greater32 = a[31] ? a[30:0] < b[30:0] : a[30:0] > b[30:0];
      end
    endfunction
    wire [3:0] new_maximum;
    for (slot = 0; slot < 4; slot = slot + 1) begin: g_slot
      wire [15:0] rounded_activation = narrow32(activation_source[32*slot+:32], fp16);
      assign activation_data[16*slot+:16] = !slots_q[slot] ? 16'b0 :
        projection_q == 6 ? intermediate_read[16*slot+:16] : rounded_activation;
      assign activation_nonzero[slot] = slots_q[slot] &&
        (projection_q == 6 ? intermediate_read[64+slot] :
         (|activation_source[32*slot+:31]));
      assign panel_row[32*slot+:32] = slots_q[slot] ?
        p_data[32*(64*slot+row_lane)+:32] : 32'b0;
      assign row_encoded[16*slot+:16] = slots_q[slot] ?
        narrow32(row_value[32*slot+:32], fp16) : 16'b0;
      assign new_maximum[slot] = slots_q[slot] && (!maximum_owned[slot] ||
        greater32(row_value[32*slot+:32], maxima[32*slot+:32]));
      anvil_q1_ht3_fp32_add u_bias_residual_add (
        .clk(clk), .rst_n(rst_n), .enable(1'b1),
        .in_valid(run_n && state == ROW_ADD_SEND && !cancel),
        .in_a(slots_q[slot] ? row_add_a[32*slot+:32] : 32'b0),
        .in_b(slots_q[slot] ? row_add_b[32*slot+:32] : 32'b0),
        .out_valid(add_valid[slot]), .out_data(add_data[32*slot+:32])
      );
    end

    always @* begin
      command_bad = cmd_format == 3 || cmd_slots == 0 ||
        cmd_prefix_length >= S || (cmd_emit_logits && cmd_slots != 1) ||
        (cmd_sparse && (cmd_threshold[14:7] == 8'hff ||
         (cmd_threshold[15] && cmd_threshold[14:0] != 0))) ||
        ((cmd_int8_weights || cmd_kv_format[1]) &&
         ((|cmd_extension_base[5:0]) || cmd_extension_length == 0 ||
          command_extension_end > 34'h200000000));
      ancestor_count = 0;
      expected_position = 0;
      for (node = 0; node < 4; node = node + 1) begin
        if (cmd_slots[node]) begin
          if (cmd_tokens[32*node+:32] >= V || !cmd_ancestors[4*node+node])
            command_bad = 1;
          ancestor_count = 0;
          for (ancestor = 0; ancestor < 4; ancestor = ancestor + 1) begin
            if (cmd_ancestors[4*node+ancestor]) begin
              ancestor_count = ancestor_count + 1'b1;
              if (!cmd_slots[ancestor] || ancestor > node) command_bad = 1;
              if (ancestor != node &&
                  ((cmd_ancestors[4*ancestor+:4] & ~cmd_ancestors[4*node+:4]) != 0 ||
                   cmd_positions[32*ancestor+:32] >= cmd_positions[32*node+:32]))
                command_bad = 1;
              for (peer = 0; peer < 4; peer = peer + 1)
                if (peer < ancestor && cmd_ancestors[4*node+peer] &&
                    cmd_positions[32*peer+:32] == cmd_positions[32*ancestor+:32])
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
      input_bad = 0;
      output_bad = e_index != {19'b0, index_q} || e_slots != slots_q;
      for (s = 0; s < 4; s = s + 1) begin
        if (slots_q[s]) begin
          if (fp32_nonfinite(row_value[32*s+:32]) ||
              (residual_projection && fp32_nonfinite(row_sum[32*s+:32]))) row_bad = 1;
          if (fp32_nonfinite(expand16(row_encoded[16*s+:16], fp16))) narrowing_bad = 1;
          if (fp32_nonfinite(expand16(activation_data[16*s+:16], fp16))) input_bad = 1;
          if (fp32_nonfinite(e_data[32*s+:32])) output_bad = 1;
          if (!initial_norm && (projection_q == 0 || projection_q == 5) &&
              fp32_nonfinite(expand16(e_encoded[16*s+:16], fp16))) output_bad = 1;
        end
      end
    end
    anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
    anvil_q1_ht3_projection #(
      .HIDDEN_SIZE(H), .INTERMEDIATE_SIZE(I), .GROUP_SIZE(GROUP_SIZE),
      .VOCAB_SIZE(V), .TILE_BEATS(TILE_BEATS)
    ) u_projection (
      .clk(clk), .rst_n(rst_n), .abort_error(cancel),
      .cmd_valid(run_n && state == PROJ_COMMAND && !cancel), .cmd_ready(p_ready),
      .cmd_format(projection_format), .cmd_slots(slots_q),
      .cmd_inputs(projection_inputs), .cmd_outputs(projection_outputs),
      .cmd_weight_base(weight_base), .cmd_zero_base(zero_base), .cmd_scale_base(scale_base),
      .cmd_weight_length(weight_length), .cmd_zero_length(zero_length),
      .cmd_scale_length(scale_length), .cmd_down_projection(projection_q == 6),
      .cmd_sparse(sparse_q), .cmd_finite_weights(finite_q), .cmd_threshold(threshold_q),
      .cmd_int8_weights(int8_projection), .cmd_int8_scale_base(int8_scale_candidate[32:0]),
      .cmd_int8_scale_length(projection_scale_length_q),
      .activation_valid(run_n && state == PROJ_INPUT && !cancel && !input_bad),
      .activation_ready(p_in_ready), .activation_data(activation_data),
      .activation_nonzero(activation_nonzero),
      .result_valid(p_valid), .result_ready(state == PROJ_RETIRE || state == FAIL_DRAIN),
      .result_panel(p_panel), .result_data(p_data), .result_mask(p_mask),
      .result_slots(p_slots), .busy(p_busy), .done(p_done), .error(p_error),
      .dma_valid(p_dma_valid), .dma_ready(p_dma_ready), .dma_address(p_dma_address),
      .dma_burstcount(p_dma_beats), .dma_data_valid(mux_valid[0]),
      .dma_data_ready(p_dma_data_ready), .dma_data(mux_data), .dma_error(mux_error),
      .stats_valid(stats_valid), .stats_dense_bytes(stats_dense_bytes),
      .stats_avoided_bytes(stats_avoided_bytes), .stats_replay_bytes(stats_replay_bytes),
      .stats_replay_column(stats_replay_column)
    );
    anvil_q1_ht3_burst_reader u_scalar_reader (
      .clk(clk), .rst_n(rst_n), .cmd_valid(scalar_request), .cmd_ready(r_ready),
      .cmd_address({fetch_absolute[32:6],6'b0}), .cmd_burstcount(8'd1),
      .mem_valid(r_dma_valid), .mem_ready(r_dma_ready), .mem_address(r_dma_address),
      .mem_burstcount(r_dma_beats), .mem_data_valid(mux_valid[1]),
      .mem_data_ready(r_dma_data_ready), .mem_data(mux_data), .mem_error(mux_error),
      .rsp_valid(r_valid), .rsp_ready(state == FETCH_WAIT || state == FAIL_DRAIN),
      .rsp_data(r_data), .rsp_error(r_error)
    );
    anvil_q1_ht3_dma_mux #(.CHECK_RESPONSE_LAST(0)) u_read_arbiter (
      .clk(clk), .rst_n(rst_n), .client_valid({2'b0,r_dma_valid,p_dma_valid}),
      .client_ready(mux_ready), .client_write(4'b0),
      .client_address({66'b0,r_dma_address,p_dma_address}),
      .client_burstcount({16'b0,r_dma_beats,p_dma_beats}),
      .client_writedata(2048'b0), .client_byteenable(256'b0),
      .client_rsp_valid(mux_valid), .client_rsp_ready({2'b0,r_dma_data_ready,p_dma_data_ready}),
      .client_rsp_data(mux_data), .client_rsp_error(mux_error), .busy(mux_busy),
      .protocol_error(mux_fault), .req_valid(dma_valid), .req_ready(dma_ready),
      .req_write(), .req_address(dma_address), .req_burstcount(dma_burstcount),
      .req_writedata(), .req_byteenable(), .rsp_valid(dma_data_valid),
      .rsp_ready(dma_data_ready), .rsp_write(1'b0), .rsp_last(1'b0),
      .rsp_error(dma_error), .rsp_data(dma_data)
    );
    assign p_dma_ready = mux_ready[0];
    assign r_dma_ready = mux_ready[1];
    anvil_q1_ht3_epilogue_fusion #(
      .MAX_VECTOR(M), .HEAD_DIM(HEAD_DIM), .CHECK_ENCODED(0)
    ) u_epilogue (
      .clk(clk), .rst_n(rst_n), .abort_error(cancel),
      .cmd_valid(run_n && (state == NORM_COMMAND || state == E_COMMAND) && !cancel),
      .cmd_ready(e_ready), .cmd_op(epilogue_op), .cmd_slots(slots_q),
      .cmd_fp16(fp16), .cmd_length(epilogue_length), .cmd_positions(positions_q),
      .in_valid(e_input), .in_ready(e_in_ready),
      .in_data(initial_norm ? residual_read : projection_q == 5 ? row_aux : row_value),
      .in_aux(projection_q == 5 ? row_value : row_aux), .in_gamma(gamma_q),
      .out_valid(e_valid), .out_index(e_index), .out_data(e_data),
      .out_encoded(e_encoded), .out_slots(e_slots), .busy(e_busy),
      .done(e_done), .error(e_error), .out_ready(state == E_OUTPUT || state == FAIL_DRAIN)
    );
    anvil_q1_ht3_kv_store_convert u_store_converter (
      .clk(clk), .rst_n(rst_n), .abort_error(cancel),
      .in_valid(run_n && state == STORE_ISSUE && slots_q[store_node] && !cancel),
      .in_ready(convert_ready), .in_format(kv_format_q), .in_node(store_node),
      .in_layer({27'b0,layer_q}), .in_column({19'b0,index_q}),
      .in_first(index_q == 0), .in_last(index_q + 1'b1 == C),
      .in_key(key_read[32*store_node+:32]), .in_value(value_read[32*store_node+:32]),
      .in_key_scale(scales_q[64*store_head+:32]),
      .in_value_scale(scales_q[64*store_head+32+:32]), .in_image(image_q),
      .out_valid(kv_store_valid), .out_ready(kv_store_ready),
      .out_format(kv_store_format), .out_node(kv_store_node),
      .out_layer(kv_store_layer), .out_column(kv_store_column),
      .out_first(kv_store_first), .out_last(kv_store_last),
      .out_key(kv_store_key), .out_value(kv_store_value),
      .out_error(kv_store_fault), .out_image(kv_store_image), .busy(convert_busy)
    );
    anvil_q1_ht3_flash_attn #(
      .NUM_Q_HEADS(NUM_Q_HEADS), .NUM_KV_HEADS(NUM_KV_HEADS),
      .HEAD_DIM(HEAD_DIM), .MAX_SEQ_LEN(S), .TILE_TOKENS(FLASH_TILE)
    ) u_flash_attn (
      .clk(clk), .rst_n(rst_n), .abort_error(cancel),
      .cmd_valid(run_n && state == ATTN_COMMAND && !cancel), .cmd_ready(a_ready),
      .cmd_fp16(fp16), .cmd_slots(slots_q), .cmd_prefix_length(prefix_q),
      .cmd_positions(positions_q), .cmd_ancestors(ancestors_q),
      .cmd_kv_format(kv_format_q),
      .query_valid(run_n && state == ATTN_INPUT && !cancel),
      .query_ready(a_in_ready), .query_data(query_read),
      .kv_valid(kv_read_valid), .kv_ready(kv_read_ready),
      .kv_provisional(kv_read_provisional), .kv_node(kv_read_node),
      .kv_position(kv_read_position), .kv_head(kv_read_head), .kv_column(kv_read_column),
      .kv_rsp_valid(kv_rsp_valid), .kv_rsp_ready(kv_rsp_ready),
      .kv_key(kv_key), .kv_value(kv_value), .kv_rsp_error(kv_rsp_error),
      .kv_key_scale(kv_key_scale), .kv_value_scale(kv_value_scale),
      .out_valid(a_valid), .out_ready(state == ATTN_OUTPUT || state == FAIL_DRAIN),
      .out_index(a_index), .out_data(a_data), .out_slots(a_slots),
      .busy(a_busy), .done(a_done), .error(a_error)
    );
    assign cmd_ready = run_n && state == IDLE && !abort_error;
    assign lookup_valid = run_n && state == LOOKUP_SEND && !cancel;
    assign lookup_index = lookup_valid ? 32'(descriptor_layer)*96 +
      {25'b0,descriptor_kind,3'b0} + {29'b0,descriptor_projection} : 32'b0;
    assign lookup_rsp_ready = run_n && (state == LOOKUP_WAIT || state == FAIL_DRAIN);
    assign kv_read_layer = kv_read_valid ? {27'b0,layer_q} : 32'b0;
    assign kv_read_key_scale = kv_read_valid ? scales_q[64*kv_read_head+:32] : 32'b0;
    assign kv_read_value_scale = kv_read_valid ? scales_q[64*kv_read_head+32+:32] : 32'b0;
    assign logit_valid = run_n && state == ROW_EMIT;
    assign logit_index = logit_valid ? row_index : 32'b0;
    assign logit_data = logit_valid ? row_value : 128'b0;
    assign logit_slots = logit_valid ? slots_q : 4'b0;
    assign rsp_valid = run_n && state == RESPONSE;
    assign rsp_targets = rsp_valid && !failed ? targets : 128'b0;
    assign rsp_error = rsp_valid && failed;
    assign busy = run_n && state != IDLE;
    assign done = run_n && state == COMPLETE;

    always @(posedge clk) begin
      if (run_n) begin
        if (state == NORM_READ) residual_read <= residuals[index_q];
        if (state == PROJ_READ) begin
          if (projection_q == 6) intermediate_read <= intermediates[index_q];
          else if (projection_q == 3) attention_read <= attention_vectors[index_q];
          else normalized_read <= normalized[index_q];
        end
        if (state == ROW_RESIDUAL) residual_read <= residuals[row_index];
        if (state == ROW_AUX) gate_read <= gates[row_index];
        if (state == STORE_READ) begin
          key_read <= keys[index_q];
          value_read <= values[index_q];
        end
        if (state == ATTN_READ) query_read <= queries[index_q];
        if (!cancel) begin
          if (state == EMB_STORE) residuals[index_q] <= embedding_word;
          if (state == ROW_STORE && !row_bad && row_active) begin
            if (projection_q == 2) values[row_index] <= row_value;
            if (projection_q == 4) gates[row_index] <= row_value;
          end
          if (state == ROW_E_INPUT && e_in_ready && residual_projection && !row_bad)
            residuals[row_index] <= row_sum;
          if (state == E_OUTPUT && e_response && !output_bad) begin
            if (initial_norm || residual_projection) normalized[e_index] <= e_data;
            else case (projection_q)
              0: queries[e_index] <= e_encoded;
              1: keys[e_index] <= e_data;
              5: intermediates[e_index] <= {
                slots_q[3] && (|e_data[126:96]), slots_q[2] && (|e_data[94:64]),
                slots_q[1] && (|e_data[62:32]), slots_q[0] && (|e_data[30:0]), e_encoded};
              default: begin end
            endcase
          end
          if (state == ATTN_OUTPUT && a_response && a_index == index_q &&
              a_slots == slots_q) attention_vectors[a_index] <= a_data;
        end
      end
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        lookup_return <= IDLE;
        fetch_return <= IDLE;
        format_q <= 0;
        kv_format_q <= 0;
        slots_q <= 0;
        tokens_q <= 0;
        positions_q <= 0;
        ancestors_q <= 0;
        threshold_q <= 0;
        prefix_q <= 0;
        image_q <= 0;
        extension_base_q <= 0;
        extension_length_q <= 0;
        int8_q <= 0;
        emit_q <= 0;
        sparse_q <= 0;
        finite_q <= 0;
        failed <= 0;
        initial_norm <= 0;
        layer_q <= 0;
        projection_q <= 0;
        index_q <= 0;
        row_lane <= 0;
        expected_panel <= 0;
        embedding_slot <= 0;
        store_node <= 0;
        store_head <= 0;
        store_dimension <= 0;
        scale_index <= 0;
        scales_q <= 0;
        embedding_word <= 0;
        row_value <= 0;
        row_aux <= 0;
        row_sum <= 0;
        targets <= 0;
        maxima <= 0;
        maximum_owned <= 0;
        descriptor_kind <= 0;
        descriptor_projection <= 0;
        descriptor_layer <= 0;
        scalar_base <= 0;
        scalar_length <= 0;
        weight_base <= 0;
        weight_length <= 0;
        zero_base <= 0;
        zero_length <= 0;
        scale_base <= 0;
        scale_length <= 0;
        bias_base <= 0;
        bias_length <= 0;
        norm_base <= 0;
        fetch_base <= 0;
        fetch_length <= 0;
        fetch_offset <= 0;
        fetch_absolute <= 0;
        fetch_fp32 <= 0;
        fetched_word <= 0;
        fetched_scale <= 0;
        gamma_q <= 0;
        cache_valid <= 0;
        cache_address <= 0;
        cache_data <= 0;
        lookup_owned <= 0;
        scalar_owned <= 0;
      end else if (run_n) begin
        if (lookup_valid && lookup_ready) lookup_owned <= 1;
        if (lookup_rsp_valid && lookup_rsp_ready) lookup_owned <= 0;
        if (scalar_request && r_ready) scalar_owned <= 1;
        if (scalar_response) scalar_owned <= 0;
        if ((abort_error || kv_store_error || worker_error || failed) &&
            state != IDLE && state != RESPONSE && state != COMPLETE &&
            state != FAIL_DRAIN) begin
          failed <= 1;
          if (state != ROW_EMIT || logit_ready) state <= FAIL_DRAIN;
        end else case (state)
          IDLE: if (cmd_valid && cmd_ready) begin
            format_q <= cmd_format;
            kv_format_q <= cmd_kv_format;
            slots_q <= cmd_slots;
            tokens_q <= cmd_tokens;
            positions_q <= cmd_positions;
            ancestors_q <= cmd_ancestors;
            threshold_q <= cmd_threshold;
            prefix_q <= cmd_prefix_length;
            image_q <= cmd_image;
            extension_base_q <= cmd_extension_base;
            extension_length_q <= cmd_extension_length;
            int8_q <= cmd_int8_weights;
            emit_q <= cmd_emit_logits;
            sparse_q <= cmd_sparse;
            finite_q <= cmd_finite_weights;
            failed <= command_bad;
            initial_norm <= 1;
            layer_q <= 0;
            projection_q <= 0;
            index_q <= 0;
            embedding_slot <= 0;
            embedding_word <= 0;
            maximum_owned <= 0;
            targets <= 0;
            maxima <= 0;
            cache_valid <= 0;
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
                lookup_end > 34'h200000000) begin failed <= 1; state <= FAIL_DRAIN; end
            else begin
              scalar_base <= lookup_base;
              scalar_length <= lookup_length;
              state <= lookup_return;
            end
          end
          EMB_DESCRIPTOR: begin
            if (scalar_length != EMB_BYTES) begin failed <= 1; state <= FAIL_DRAIN; end
            else state <= EMB_BEGIN;
          end
          EMB_BEGIN: begin
            fetch_base <= scalar_base;
            fetch_length <= scalar_length;
            fetch_offset <= 64'(tokens_q[32*embedding_slot+:32] >> 6)*(H*128) +
              {44'b0,index_q,7'b0} + {57'b0,tokens_q[32*embedding_slot+:6],1'b0};
            fetch_fp32 <= 0;
            fetch_return <= EMB_WORD;
            if (!slots_q[embedding_slot]) begin
              embedding_word[32*embedding_slot+:32] <= 0;
              if (embedding_slot == 3) state <= EMB_STORE;
              else embedding_slot <= embedding_slot + 1'b1;
            end else state <= FETCH_CHECK;
          end
          EMB_WORD: begin
            if (fp32_nonfinite(expanded_fetched)) begin failed <= 1; state <= FAIL_DRAIN; end
            else begin
              embedding_word[32*embedding_slot+:32] <= expanded_fetched;
              if (embedding_slot == 3) state <= EMB_STORE;
              else begin embedding_slot <= embedding_slot + 1'b1; state <= EMB_BEGIN; end
            end
          end
          EMB_STORE: begin
            if (index_q + 1'b1 == H) state <= LAYER_BEGIN;
            else begin index_q <= index_q + 1'b1; embedding_slot <= 0; state <= EMB_BEGIN; end
          end
          FETCH_CHECK: begin
            fetch_absolute <= fetch_candidate[32:0];
            if (fetch_offset + (fetch_fp32 ? 64'd4 : 64'd2) > fetch_length ||
                fetch_candidate + (fetch_fp32 ? 64'd4 : 64'd2) > 64'h200000000 ||
                fetch_end > 34'h200000000 ||
                (fetch_fp32 && (|fetch_candidate[1:0])) ||
                (!fetch_fp32 && fetch_candidate[0])) begin
              failed <= 1; state <= FAIL_DRAIN;
            end else if (cache_valid &&
                cache_address == {fetch_candidate[32:6],6'b0}) begin
              fetched_word <= cache_data[8*fetch_candidate[5:0]+:16];
              fetched_scale <= cache_data[8*fetch_candidate[5:0]+:32];
              state <= fetch_return;
            end else state <= FETCH_SEND;
          end
          FETCH_SEND: if (scalar_request && r_ready) state <= FETCH_WAIT;
          FETCH_WAIT: if (scalar_response) begin
            if (r_error) begin failed <= 1; state <= FAIL_DRAIN; end
            else begin
              cache_valid <= 1;
              cache_address <= {fetch_absolute[32:6],6'b0};
              cache_data <= r_data[511:0];
              state <= FETCH_WORD;
            end
          end
          FETCH_WORD: begin
            fetched_word <= cache_data[8*fetch_absolute[5:0]+:16];
            fetched_scale <= cache_data[8*fetch_absolute[5:0]+:32];
            state <= fetch_return;
          end
          LAYER_BEGIN: begin
            scale_index <= 0;
            scales_q <= 0;
            if ((int8_q || kv_format_q[1]) && extension_length_q !=
                ((required_extension_bytes + 63) & 32'hffffffc0)) begin
              failed <= 1; state <= FAIL_DRAIN;
            end else if (kv_format_q[1]) state <= SCALE_FETCH;
            else if (initial_norm) state <= NORM_BEGIN;
            else state <= PROJ_BEGIN;
          end
          SCALE_FETCH: begin
            fetch_base <= extension_base_q;
            fetch_length <= extension_length_q;
            fetch_offset <= kv_scale_offset;
            fetch_fp32 <= 1;
            fetch_return <= SCALE_WORD;
            state <= FETCH_CHECK;
          end
          SCALE_WORD: begin
            if (fetched_scale[31] || fetched_scale[30:0] == 0 ||
                fp32_nonfinite(fetched_scale)) begin failed <= 1; state <= FAIL_DRAIN; end
            else begin
              scales_q[32*scale_index+:32] <= fetched_scale;
              if (scale_index + 1'b1 == 2*NUM_KV_HEADS) begin
                if (initial_norm) state <= NORM_BEGIN;
                else state <= PROJ_BEGIN;
              end else begin scale_index <= scale_index + 1'b1; state <= SCALE_FETCH; end
            end
          end
          NORM_BEGIN: begin
            descriptor_kind <= 5;
            descriptor_layer <= 0;
            descriptor_projection <= 0;
            lookup_return <= NORM_DESCRIPTOR;
            state <= LOOKUP_SEND;
          end
          NORM_DESCRIPTOR: begin
            if (scalar_length != NORM_BYTES) begin failed <= 1; state <= FAIL_DRAIN; end
            else begin norm_base <= scalar_base; state <= NORM_COMMAND; end
          end
          NORM_COMMAND: if (e_ready) begin index_q <= 0; state <= NORM_READ; end
          NORM_READ: state <= NORM_FETCH;
          NORM_FETCH: begin
            fetch_base <= norm_base;
            fetch_length <= NORM_BYTES;
            fetch_offset <= {50'b0,index_q,1'b0};
            fetch_fp32 <= 0;
            fetch_return <= NORM_INPUT;
            state <= FETCH_CHECK;
          end
          NORM_INPUT: begin
            gamma_q <= fetched_word;
            // Gamma reaches the input on the following edge through ROW_GAMMA_WORD.
            state <= ROW_GAMMA_WORD;
          end
          ROW_GAMMA_WORD: begin
            if (initial_norm) begin
              if (e_in_ready) begin
                if (index_q + 1'b1 == H) begin index_q <= 0; state <= E_OUTPUT; end
                else begin index_q <= index_q + 1'b1; state <= NORM_READ; end
              end
            end else begin gamma_q <= fetched_word; state <= ROW_E_INPUT; end
          end
          PROJ_BEGIN: begin
            descriptor_kind <= projection_q == 7 ? 4'd0 : 4'd1;
            descriptor_layer <= projection_q == 7 ? 5'd0 : layer_q;
            descriptor_projection <= projection_q == 7 ? 3'd0 : projection_q;
            lookup_return <= PROJ_WEIGHT;
            state <= LOOKUP_SEND;
          end
          PROJ_WEIGHT: begin
            weight_base <= scalar_base;
            weight_length <= scalar_length;
            zero_base <= 0;
            zero_length <= 0;
            scale_base <= 0;
            scale_length <= 0;
            if (awq_projection) begin
              descriptor_kind <= 2; lookup_return <= PROJ_ZERO; state <= LOOKUP_SEND;
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
            if (projection_q < 3) begin
              descriptor_kind <= 4;
              lookup_return <= PROJ_BIAS;
              state <= LOOKUP_SEND;
            end else state <= PROJ_NORM_BEGIN;
          end
          PROJ_BIAS: begin
            if (scalar_length != (projection_q == 0 ? NORM_BYTES : KV_BIAS_BYTES)) begin
              failed <= 1; state <= FAIL_DRAIN;
            end else begin
              bias_base <= scalar_base;
              bias_length <= scalar_length;
              state <= PROJ_NORM_BEGIN;
            end
          end
          PROJ_NORM_BEGIN: begin
            if (residual_projection) begin
              descriptor_kind <= projection_q == 3 ? 4'd6 :
                layer_q + 1'b1 == L ? 4'd7 : 4'd5;
              descriptor_layer <= projection_q == 3 ? layer_q :
                layer_q + 1'b1 == L ? 5'd0 : layer_q + 1'b1;
              descriptor_projection <= 0;
              lookup_return <= PROJ_NORM;
              state <= LOOKUP_SEND;
            end else if (projection_epilogue) state <= E_COMMAND;
            else state <= PROJ_COMMAND;
          end
          PROJ_NORM: begin
            if (scalar_length != NORM_BYTES) begin failed <= 1; state <= FAIL_DRAIN; end
            else begin norm_base <= scalar_base; state <= E_COMMAND; end
          end
          E_COMMAND: if (e_ready) state <= PROJ_COMMAND;
          PROJ_COMMAND: begin
            if (int8_projection && (int8_scale_candidate + projection_scale_length_q >
                {31'b0,extension_base_q} + extension_length_q ||
                int8_scale_candidate + projection_scale_length_q > 64'h200000000)) begin
              failed <= 1; state <= FAIL_DRAIN;
            end else if (p_ready) begin
              index_q <= 0;
              expected_panel <= 0;
              state <= PROJ_READ;
            end
          end
          PROJ_READ: state <= PROJ_INPUT;
          PROJ_INPUT: begin
            if (input_bad) begin failed <= 1; state <= FAIL_DRAIN; end
            else if (p_in_ready) begin
              if (index_q + 1'b1 == projection_inputs) state <= PROJ_OUTPUT;
              else begin index_q <= index_q + 1'b1; state <= PROJ_READ; end
            end
          end
          PROJ_OUTPUT: if (p_valid) begin
            if (p_slots != slots_q || p_panel != expected_panel ||
                p_panel >= projection_outputs || p_mask != expected_mask) begin
              failed <= 1; state <= FAIL_DRAIN;
            end else begin row_lane <= 0; state <= ROW_BEGIN; end
          end
          ROW_BEGIN: begin
            row_value <= panel_row;
            row_aux <= 0;
            if (!row_active) state <= ROW_NEXT;
            else if (row_index >= projection_outputs) begin failed <= 1; state <= FAIL_DRAIN; end
            else if (projection_q < 3) begin
              fetch_base <= bias_base;
              fetch_length <= bias_length;
              fetch_offset <= {31'b0,row_index,1'b0};
              fetch_fp32 <= 0;
              fetch_return <= ROW_BIAS;
              state <= FETCH_CHECK;
            end else if (residual_projection) state <= ROW_RESIDUAL;
            else if (projection_q == 5) state <= ROW_AUX;
            else state <= ROW_STORE;
          end
          ROW_BIAS: begin
            if (fp32_nonfinite(expanded_fetched)) begin failed <= 1; state <= FAIL_DRAIN; end
            else begin row_aux <= {4{expanded_fetched}}; state <= ROW_ADD_SEND; end
          end
          ROW_RESIDUAL: state <= ROW_GAMMA;
          ROW_GAMMA: begin
            row_aux <= residual_read;
            fetch_base <= norm_base;
            fetch_length <= NORM_BYTES;
            fetch_offset <= {31'b0,row_index,1'b0};
            fetch_fp32 <= 0;
            fetch_return <= ROW_ADD_SEND;
            state <= FETCH_CHECK;
          end
          ROW_AUX: state <= ROW_AUX_LOAD;
          ROW_AUX_LOAD: begin row_aux <= gate_read; state <= ROW_E_INPUT; end
          ROW_ADD_SEND: state <= ROW_ADD_WAIT;
          ROW_ADD_WAIT: if (&add_valid) begin
            if (residual_projection) begin
              row_sum <= add_data;
              gamma_q <= fetched_word;
              state <= ROW_E_INPUT;
            end else begin row_value <= add_data; state <= ROW_STORE; end
          end
          ROW_STORE: begin
            if (row_bad) begin
              failed <= 1; state <= FAIL_DRAIN;
            end else if (projection_epilogue) state <= ROW_E_INPUT;
            else if (projection_q == 7) begin
              for (update_slot = 0; update_slot < 4; update_slot = update_slot + 1)
                if (new_maximum[update_slot]) begin
                  maxima[32*update_slot+:32] <= row_value[32*update_slot+:32];
                  targets[32*update_slot+:32] <= row_index;
                  maximum_owned[update_slot] <= 1;
                end
              if (emit_q) state <= ROW_EMIT;
              else state <= ROW_NEXT;
            end else state <= ROW_NEXT;
          end
          ROW_E_INPUT: begin
            if (row_bad) begin failed <= 1; state <= FAIL_DRAIN; end
            else if (e_in_ready) state <= ROW_NEXT;
          end
          ROW_EMIT: if (logit_ready) state <= ROW_NEXT;
          ROW_NEXT: begin
            if (row_lane == 63) state <= PROJ_RETIRE;
            else begin row_lane <= row_lane + 1'b1; state <= ROW_BEGIN; end
          end
          PROJ_RETIRE: if (p_valid) begin
            if (last_panel) state <= PROJ_FINISH;
            else begin expected_panel <= expected_panel + 64; state <= PROJ_OUTPUT; end
          end
          PROJ_FINISH: if (p_done) begin
            if (projection_epilogue) begin index_q <= 0; state <= E_OUTPUT; end
            else case (projection_q)
              2: begin
                index_q <= 0; store_node <= 0; store_head <= 0;
                store_dimension <= 0; state <= STORE_READ;
              end
              4: begin projection_q <= 5; state <= PROJ_BEGIN; end
              7: begin
                if ((maximum_owned & slots_q) != slots_q) begin failed <= 1; state <= FAIL_DRAIN; end
                else state <= RESPONSE;
              end
              default: begin failed <= 1; state <= FAIL_DRAIN; end
            endcase
          end
          E_OUTPUT: if (e_response) begin
            if (output_bad) begin failed <= 1; state <= FAIL_DRAIN; end
            else if (index_q + 1'b1 == epilogue_length) state <= E_FINISH;
            else index_q <= index_q + 1'b1;
          end
          E_FINISH: if (e_done) begin
            if (initial_norm) begin
              initial_norm <= 0; projection_q <= 0; state <= PROJ_BEGIN;
            end else case (projection_q)
              0, 1: begin projection_q <= projection_q + 1'b1; state <= PROJ_BEGIN; end
              3: begin projection_q <= 4; state <= PROJ_BEGIN; end
              5: begin projection_q <= 6; state <= PROJ_BEGIN; end
              6: begin
                if (layer_q + 1'b1 == L) begin projection_q <= 7; state <= PROJ_BEGIN; end
                else begin
                  layer_q <= layer_q + 1'b1; projection_q <= 0; state <= LAYER_BEGIN;
                end
              end
              default: begin failed <= 1; state <= FAIL_DRAIN; end
            endcase
          end
          STORE_READ: state <= STORE_ISSUE;
          STORE_ISSUE: begin
            if (!slots_q[store_node]) begin
              if (store_node == 3) state <= STORE_SETTLE;
              else begin
                store_node <= store_node + 1'b1; index_q <= 0;
                store_head <= 0; store_dimension <= 0; state <= STORE_READ;
              end
            end else if (convert_ready) state <= STORE_WAIT;
          end
          STORE_WAIT: if (kv_store_valid && kv_store_ready) begin
            if (kv_store_node != store_node || kv_store_layer != layer_q ||
                kv_store_column != index_q || kv_store_image != image_q ||
                kv_store_format != kv_format_q || kv_store_first != (index_q == 0) ||
                kv_store_last != (index_q + 1'b1 == C)) begin
              failed <= 1; state <= FAIL_DRAIN;
            end else if (index_q + 1'b1 == C) begin
              if (store_node == 3) state <= STORE_SETTLE;
              else begin
                store_node <= store_node + 1'b1; index_q <= 0;
                store_head <= 0; store_dimension <= 0; state <= STORE_READ;
              end
            end else begin
              index_q <= index_q + 1'b1;
              if (store_dimension + 1'b1 == HEAD_DIM) begin
                store_dimension <= 0; store_head <= store_head + 1'b1;
              end else store_dimension <= store_dimension + 1'b1;
              state <= STORE_READ;
            end
          end
          STORE_SETTLE: if (!convert_busy) state <= ATTN_COMMAND;
          ATTN_COMMAND: if (a_ready) begin index_q <= 0; state <= ATTN_READ; end
          ATTN_READ: state <= ATTN_INPUT;
          ATTN_INPUT: if (a_in_ready) begin
            if (index_q + 1'b1 == H) begin index_q <= 0; state <= ATTN_OUTPUT; end
            else begin index_q <= index_q + 1'b1; state <= ATTN_READ; end
          end
          ATTN_OUTPUT: if (a_response) begin
            if (a_index != index_q || a_slots != slots_q) begin failed <= 1; state <= FAIL_DRAIN; end
            else if (index_q + 1'b1 == H) state <= ATTN_FINISH;
            else index_q <= index_q + 1'b1;
          end
          ATTN_FINISH: if (a_done) begin projection_q <= 3; state <= PROJ_BEGIN; end
          FAIL_DRAIN: if (!p_busy && !e_busy && !a_busy && !convert_busy &&
              !mux_busy && !lookup_owned && !scalar_owned && !r_valid) state <= RESPONSE;
          RESPONSE: if (rsp_ready) state <= COMPLETE;
          COMPLETE: state <= IDLE;
          default: begin failed <= 1; state <= FAIL_DRAIN; end
        endcase
      end
    end
  end endgenerate
endmodule
