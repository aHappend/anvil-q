module anvil_q1_ht2_attention #(
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2,
  parameter HEAD_DIM = 64, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n, abort_error,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire cmd_fp16,
  input wire [3:0] cmd_slots,
  input wire [31:0] cmd_prefix_length,
  input wire [127:0] cmd_positions,
  input wire [15:0] cmd_ancestors,
  input wire query_valid,
  output wire query_ready,
  input wire [63:0] query_data,
  output wire kv_valid,
  input wire kv_ready,
  output wire kv_provisional,
  output wire [1:0] kv_node,
  output wire [31:0] kv_position, kv_head, kv_column,
  input wire kv_rsp_valid,
  output wire kv_rsp_ready,
  input wire [15:0] kv_key, kv_value,
  input wire kv_rsp_error,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_index,
  output wire [127:0] out_data,
  output wire [3:0] out_slots,
  output wire busy, done, error
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam SAFE_K = NUM_KV_HEADS > 0 ? NUM_KV_HEADS : 1;
  localparam LEGAL = NUM_Q_HEADS >= 1 && NUM_Q_HEADS <= 14 &&
    NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 &&
    NUM_Q_HEADS % SAFE_K == 0 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    NUM_Q_HEADS*HEAD_DIM >= 8 && NUM_Q_HEADS*HEAD_DIM <= 896 &&
    ((NUM_Q_HEADS*HEAD_DIM) & 7) == 0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
    MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768;
  localparam Q = LEGAL ? NUM_Q_HEADS : 1;
  localparam K = LEGAL ? NUM_KV_HEADS : 1;
  localparam D = LEGAL ? HEAD_DIM : 8;
  localparam S = LEGAL ? MAX_SEQ_LEN : 1;
  localparam RATIO = Q/K;
  localparam [31:0] D_FLOAT = pack32(1'b0, 64'(D), 0);
  localparam IDLE = 6'd0, QUERY_FILL = 6'd1,
    SCALE_ROOT_SEND = 6'd2, SCALE_ROOT_WAIT = 6'd3,
    SCALE_INV_SEND = 6'd4, SCALE_INV_WAIT = 6'd5,
    HEAD_BEGIN = 6'd6, SOURCE_BEGIN = 6'd7, QUERY_READ = 6'd8,
    KV_SEND = 6'd9, KV_WAIT = 6'd10, PRODUCT_SEND = 6'd11,
    PRODUCT_WAIT = 6'd12, CONTEXT_SEND = 6'd13, CONTEXT_WAIT = 6'd14,
    REDUCE0_SEND = 6'd15, REDUCE0_WAIT = 6'd16,
    REDUCE1_SEND = 6'd17, REDUCE1_WAIT = 6'd18,
    REDUCE2_SEND = 6'd19, REDUCE2_WAIT = 6'd20,
    SCORE_SCALE_SEND = 6'd21, SCORE_SCALE_WAIT = 6'd22,
    SCORE_STORE = 6'd23, EXP_BEGIN = 6'd24, SCORE_READ = 6'd25,
    SHIFT_SEND = 6'd26, SHIFT_WAIT = 6'd27,
    EXP_SEND = 6'd28, EXP_WAIT = 6'd29, EXP_STORE = 6'd30,
    SUM_SEND = 6'd31, SUM_WAIT = 6'd32,
    PROB_BEGIN = 6'd33, EXP_READ = 6'd34,
    PROB_SEND = 6'd35, PROB_WAIT = 6'd36, PROB_STORE = 6'd37,
    VALUE_BEGIN = 6'd38, VALUE_SOURCE = 6'd39, PROB_READ = 6'd40,
    OUTPUT_WORD = 6'd41, COMPLETE = 6'd42, DRAIN = 6'd43;
  wire run_n;
  reg [5:0] state;
  reg fp16, failed, cancel, value_phase, kv_owned;
  reg [3:0] slots, participating, maximum_owned;
  reg [31:0] prefix_length;
  reg [127:0] positions;
  reg [15:0] ancestors;
  reg [9:0] query_index, head_base;
  reg [3:0] head, mapped_head, mapped_offset;
  reg [5:0] column;
  reg [15:0] source_index, source_limit;
  reg [31:0] source_position;
  reg source_provisional;
  reg [1:0] source_node;
  reg [127:0] context0, context1, context2, context3;
  reg [127:0] product, reduced, current, maximum, sum, result;
  reg [31:0] scale_root, scale;
  reg [15:0] key_word, value_word;
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [63:0] queries [0:Q*D-1];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [127:0] scores [0:S+3];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [127:0] exponentials [0:S+3];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [63:0] probabilities [0:S+3];
  reg [63:0] query_q, probability_q;
  reg [127:0] score_q, exponential_q;
  wire worker_rst_n = run_n && !cancel;
  wire [3:0] scalar_ready, scalar_valid, scalar_error;
  wire [127:0] scalar_data, masked_result;
  wire scalar_send, scalar_consume;
  reg [2:0] scalar_opcode;
  reg [127:0] scalar_a, scalar_b;
  wire [127:0] selected_context = column[1:0] == 0 ? context0 :
    column[1:0] == 1 ? context1 : column[1:0] == 2 ? context2 : context3;
  wire [127:0] value_context = source_position[1:0] == 0 ? context0 :
    source_position[1:0] == 1 ? context1 :
    source_position[1:0] == 2 ? context2 : context3;
  wire [63:0] encoded_probability;
  wire kv_words_bad = fp32_nonfinite(expand16(kv_key, fp16)) ||
    fp32_nonfinite(expand16(kv_value, fp16));
  reg [3:0] next_participating;
  reg [31:0] next_position;
  reg [1:0] next_node;
  reg next_provisional, command_bad, query_bad, probability_bad;
  reg [3:0] ancestor_count;
  reg [32:0] expected_position;
  integer token, node, earlier, peer, update_slot;
  genvar slot;

  function automatic greater32(input [31:0] a, input [31:0] b);
    begin
      if (a[30:0] == 0 && b[30:0] == 0) greater32 = 0;
      else if (a[31] != b[31]) greater32 = !a[31];
      else if (a[31]) greater32 = a[30:0] < b[30:0];
      else greater32 = a[30:0] > b[30:0];
    end
  endfunction

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native GQA attention geometry");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    command_bad = !LEGAL || cmd_slots == 0 || cmd_prefix_length > S;
    ancestor_count = 0;
    expected_position = 0;
    for (node = 0; node < 4; node = node + 1) begin
      if (cmd_slots[node]) begin
        ancestor_count = 0;
        if (!cmd_ancestors[4*node+node]) command_bad = 1;
        for (earlier = 0; earlier < 4; earlier = earlier + 1) begin
          if (cmd_ancestors[4*node+earlier]) begin
            ancestor_count = ancestor_count + 1'b1;
            if (!cmd_slots[earlier] || earlier > node) command_bad = 1;
            if (earlier != node &&
                cmd_positions[32*earlier+:32] >= cmd_positions[32*node+:32])
              command_bad = 1;
            if (earlier != node &&
                (cmd_ancestors[4*earlier+:4] & ~cmd_ancestors[4*node+:4]) != 0)
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
    next_provisional = {16'b0, source_index} >= prefix_length;
    next_node = 2'({16'b0, source_index} - prefix_length);
    next_position = {16'b0, source_index};
    next_participating = slots;
    if (next_provisional) begin
      next_position = positions[32*next_node+:32];
      for (token = 0; token < 4; token = token + 1)
        next_participating[token] = slots[token] &&
          slots[next_node] && ancestors[4*token+next_node];
    end
    query_bad = 0;
    probability_bad = 0;
    for (token = 0; token < 4; token = token + 1) begin
      if (slots[token] && fp32_nonfinite(expand16(query_data[16*token+:16], fp16)))
        query_bad = 1;
      if (participating[token] &&
          fp32_nonfinite(expand16(encoded_probability[16*token+:16], fp16)))
        probability_bad = 1;
    end
    scalar_opcode = 0;
    scalar_a = 0;
    scalar_b = 0;
    for (token = 0; token < 4; token = token + 1) begin
      case (state)
        SCALE_ROOT_SEND: begin
          scalar_opcode = 3;
          scalar_a[32*token+:32] = D_FLOAT;
        end
        SCALE_INV_SEND: begin
          scalar_opcode = 2;
          scalar_a[32*token+:32] = 32'h3f800000;
          scalar_b[32*token+:32] = scale_root;
        end
        PRODUCT_SEND: begin
          scalar_opcode = 1;
          if (participating[token]) begin
            scalar_a[32*token+:32] = expand16(value_phase ?
              probability_q[16*token+:16] : query_q[16*token+:16], fp16);
            scalar_b[32*token+:32] = expand16(value_phase ? value_word : key_word, fp16);
          end
        end
        CONTEXT_SEND: begin
          scalar_a[32*token+:32] = value_phase ?
            value_context[32*token+:32] : selected_context[32*token+:32];
          scalar_b[32*token+:32] = product[32*token+:32];
        end
        REDUCE0_SEND: begin
          scalar_a[32*token+:32] = context0[32*token+:32];
          scalar_b[32*token+:32] = context1[32*token+:32];
        end
        REDUCE1_SEND, REDUCE2_SEND: begin
          scalar_a[32*token+:32] = reduced[32*token+:32];
          scalar_b[32*token+:32] = state == REDUCE1_SEND ?
            context2[32*token+:32] : context3[32*token+:32];
        end
        SCORE_SCALE_SEND: begin
          scalar_opcode = 1;
          scalar_a[32*token+:32] = reduced[32*token+:32];
          scalar_b[32*token+:32] = scale;
        end
        SHIFT_SEND: if (participating[token]) begin
          scalar_a[32*token+:32] = score_q[32*token+:32];
          scalar_b[32*token+:32] = {~maximum[32*token+31], maximum[32*token+:31]};
        end
        EXP_SEND: begin
          scalar_opcode = 4;
          scalar_a[32*token+:32] = current[32*token+:32];
        end
        SUM_SEND: begin
          scalar_a[32*token+:32] = sum[32*token+:32];
          scalar_b[32*token+:32] = current[32*token+:32];
        end
        PROB_SEND: begin
          scalar_opcode = 2;
          scalar_a[32*token+:32] = participating[token] ?
            exponential_q[32*token+:32] : 32'b0;
          scalar_b[32*token+:32] = participating[token] ?
            sum[32*token+:32] : 32'h3f800000;
        end
        default: begin end
      endcase
    end
  end
  assign scalar_send = run_n && !abort_error && (&scalar_ready) &&
    (state == SCALE_ROOT_SEND || state == SCALE_INV_SEND ||
     state == PRODUCT_SEND || state == CONTEXT_SEND ||
     state == REDUCE0_SEND || state == REDUCE1_SEND || state == REDUCE2_SEND ||
     state == SCORE_SCALE_SEND || state == SHIFT_SEND || state == EXP_SEND ||
     state == SUM_SEND || state == PROB_SEND);
  assign scalar_consume = run_n && (&scalar_valid) &&
    (state == SCALE_ROOT_WAIT || state == SCALE_INV_WAIT ||
     state == PRODUCT_WAIT || state == CONTEXT_WAIT ||
     state == REDUCE0_WAIT || state == REDUCE1_WAIT || state == REDUCE2_WAIT ||
     state == SCORE_SCALE_WAIT || state == SHIFT_WAIT || state == EXP_WAIT ||
     state == SUM_WAIT || state == PROB_WAIT);
  generate for (slot = 0; slot < 4; slot = slot + 1) begin : g_slot
    anvil_q1_ht2_scalar u_scalar (
      .clk(clk), .rst_n(worker_rst_n), .enable(1'b1),
      .req_valid(scalar_send), .req_ready(scalar_ready[slot]),
      .req_opcode(scalar_opcode),
      .req_a(scalar_a[32*slot+:32]), .req_b(scalar_b[32*slot+:32]),
      .rsp_valid(scalar_valid[slot]), .rsp_ready(scalar_consume),
      .rsp_data(scalar_data[32*slot+:32]), .rsp_aux(),
      .rsp_error(scalar_error[slot])
    );
    assign encoded_probability[16*slot+:16] =
      participating[slot] ? narrow32(current[32*slot+:32], fp16) : 16'b0;
    assign masked_result[32*slot+:32] = slots[slot] ? result[32*slot+:32] : 32'b0;
  end endgenerate
  assign cmd_ready = run_n && state == IDLE && !abort_error;
  assign query_ready = run_n && state == QUERY_FILL && !abort_error;
  assign kv_valid = run_n && state == KV_SEND && !abort_error;
  assign kv_provisional = kv_valid && source_provisional;
  assign kv_node = kv_valid && source_provisional ? source_node : 2'b0;
  assign kv_position = kv_valid ? source_position : 32'b0;
  assign kv_head = kv_valid ? {28'b0, mapped_head} : 32'b0;
  assign kv_column = kv_valid ? {26'b0, column} : 32'b0;
  assign kv_rsp_ready = run_n &&
    (state == KV_WAIT || state == DRAIN || (kv_valid && kv_ready));
  assign out_valid = run_n && state == OUTPUT_WORD;
  assign out_index = out_valid ? {22'b0, head_base}+{26'b0, column} : 32'b0;
  assign out_data = out_valid ? masked_result : 128'b0;
  assign out_slots = out_valid ? slots : 4'b0;
  assign busy = run_n && state != IDLE;
  assign done = run_n && state == COMPLETE;
  assign error = done && failed;

  always @(posedge clk) begin
    if (run_n) begin
      if (query_valid && query_ready && !query_bad) queries[query_index] <= query_data;
      if (state == QUERY_READ) query_q <= queries[head_base+{4'b0, column}];
      if (state == SCORE_STORE) scores[source_index] <= current;
      if (state == SCORE_READ && source_index < source_limit && next_participating != 0)
        score_q <= scores[source_index];
      if (state == EXP_STORE) exponentials[source_index] <= current;
      if (state == EXP_READ && source_index < source_limit && next_participating != 0)
        exponential_q <= exponentials[source_index];
      if (state == PROB_STORE && !probability_bad)
        probabilities[source_index] <= encoded_probability;
      if (state == PROB_READ) probability_q <= probabilities[source_index];
    end
  end
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      fp16 <= 0;
      failed <= 0;
      cancel <= 0;
      value_phase <= 0;
      kv_owned <= 0;
      slots <= 0;
      participating <= 0;
      maximum_owned <= 0;
      prefix_length <= 0;
      positions <= 0;
      ancestors <= 0;
      query_index <= 0;
      head_base <= 0;
      head <= 0;
      mapped_head <= 0;
      mapped_offset <= 0;
      column <= 0;
      source_index <= 0;
      source_limit <= 0;
      source_position <= 0;
      source_provisional <= 0;
      source_node <= 0;
      context0 <= 0;
      context1 <= 0;
      context2 <= 0;
      context3 <= 0;
      product <= 0;
      reduced <= 0;
      current <= 0;
      maximum <= 0;
      sum <= 0;
      result <= 0;
      scale_root <= 0;
      scale <= 0;
      key_word <= 0;
      value_word <= 0;
    end else begin
      if (kv_valid && kv_ready) kv_owned <= 1;
      if (kv_rsp_valid && kv_rsp_ready) kv_owned <= 0;
      if (abort_error && state != IDLE && state != COMPLETE && state != DRAIN) begin
        failed <= 1;
        cancel <= 1;
        state <= DRAIN;
      end else if (scalar_consume && |(scalar_error &
          ((state == SCALE_ROOT_WAIT || state == SCALE_INV_WAIT) ? 4'hf :
            value_phase ? slots : participating))) begin
        failed <= 1;
        cancel <= 1;
        state <= DRAIN;
      end else case (state)
        IDLE: begin
          cancel <= 0;
          if (cmd_valid && cmd_ready) begin
            fp16 <= cmd_fp16;
            slots <= cmd_slots;
            prefix_length <= cmd_prefix_length;
            positions <= cmd_positions;
            ancestors <= cmd_ancestors;
            source_limit <= 16'(cmd_prefix_length+4);
            query_index <= 0;
            head <= 0;
            head_base <= 0;
            mapped_head <= 0;
            mapped_offset <= 0;
            failed <= 0;
            value_phase <= 0;
            if (command_bad) begin failed <= 1; state <= COMPLETE; end
            else state <= QUERY_FILL;
          end
        end
        QUERY_FILL: if (query_valid && query_ready) begin
          if (query_bad) begin failed <= 1; state <= COMPLETE; end
          else if (query_index + 1'b1 == Q*D) state <= SCALE_ROOT_SEND;
          else query_index <= query_index + 1'b1;
        end
        SCALE_ROOT_SEND: if (scalar_send) state <= SCALE_ROOT_WAIT;
        SCALE_ROOT_WAIT: if (scalar_consume) begin
          scale_root <= scalar_data[31:0];
          state <= SCALE_INV_SEND;
        end
        SCALE_INV_SEND: if (scalar_send) state <= SCALE_INV_WAIT;
        SCALE_INV_WAIT: if (scalar_consume) begin
          scale <= scalar_data[31:0];
          state <= HEAD_BEGIN;
        end
        HEAD_BEGIN: begin
          maximum <= 0;
          maximum_owned <= 0;
          source_index <= 0;
          value_phase <= 0;
          state <= SOURCE_BEGIN;
        end
        SOURCE_BEGIN: begin
          if (source_index == source_limit) begin
            if (maximum_owned != slots) begin failed <= 1; state <= COMPLETE; end
            else state <= EXP_BEGIN;
          end else if (next_participating == 0) source_index <= source_index + 1'b1;
          else begin
            participating <= next_participating;
            source_position <= next_position;
            source_node <= next_node;
            source_provisional <= next_provisional;
            column <= 0;
            context0 <= 0;
            context1 <= 0;
            context2 <= 0;
            context3 <= 0;
            state <= QUERY_READ;
          end
        end
        QUERY_READ: state <= KV_SEND;
        KV_SEND: if (kv_valid && kv_ready) begin
          if (kv_rsp_valid && kv_rsp_ready) begin
            if (kv_rsp_error || kv_words_bad) begin
              failed <= 1;
              state <= COMPLETE;
            end else begin
              key_word <= kv_key;
              value_word <= kv_value;
              state <= PRODUCT_SEND;
            end
          end else state <= KV_WAIT;
        end
        KV_WAIT: if (kv_rsp_valid && kv_rsp_ready) begin
          if (kv_rsp_error || kv_words_bad) begin
            failed <= 1;
            state <= COMPLETE;
          end else begin
            key_word <= kv_key;
            value_word <= kv_value;
            state <= PRODUCT_SEND;
          end
        end
        PRODUCT_SEND: if (scalar_send) state <= PRODUCT_WAIT;
        PRODUCT_WAIT: if (scalar_consume) begin product <= scalar_data; state <= CONTEXT_SEND; end
        CONTEXT_SEND: if (scalar_send) state <= CONTEXT_WAIT;
        CONTEXT_WAIT: if (scalar_consume) begin
          for (update_slot = 0; update_slot < 4; update_slot = update_slot + 1) begin
            if (participating[update_slot]) case (value_phase ? source_position[1:0] : column[1:0])
              0: context0[32*update_slot+:32] <= scalar_data[32*update_slot+:32];
              1: context1[32*update_slot+:32] <= scalar_data[32*update_slot+:32];
              2: context2[32*update_slot+:32] <= scalar_data[32*update_slot+:32];
              3: context3[32*update_slot+:32] <= scalar_data[32*update_slot+:32];
            endcase
          end
          if (value_phase) begin source_index <= source_index + 1'b1; state <= VALUE_SOURCE; end
          else if (column + 1'b1 == D) state <= REDUCE0_SEND;
          else begin column <= column + 1'b1; state <= QUERY_READ; end
        end
        REDUCE0_SEND: if (scalar_send) state <= REDUCE0_WAIT;
        REDUCE0_WAIT: if (scalar_consume) begin reduced <= scalar_data; state <= REDUCE1_SEND; end
        REDUCE1_SEND: if (scalar_send) state <= REDUCE1_WAIT;
        REDUCE1_WAIT: if (scalar_consume) begin reduced <= scalar_data; state <= REDUCE2_SEND; end
        REDUCE2_SEND: if (scalar_send) state <= REDUCE2_WAIT;
        REDUCE2_WAIT: if (scalar_consume) begin
          reduced <= scalar_data;
          if (value_phase) begin result <= scalar_data; state <= OUTPUT_WORD; end
          else state <= SCORE_SCALE_SEND;
        end
        SCORE_SCALE_SEND: if (scalar_send) state <= SCORE_SCALE_WAIT;
        SCORE_SCALE_WAIT: if (scalar_consume) begin current <= scalar_data; state <= SCORE_STORE; end
        SCORE_STORE: begin
          for (update_slot = 0; update_slot < 4; update_slot = update_slot + 1) begin
            if (participating[update_slot]) begin
              if (!maximum_owned[update_slot] ||
                  greater32(current[32*update_slot+:32], maximum[32*update_slot+:32]))
                maximum[32*update_slot+:32] <= current[32*update_slot+:32];
              maximum_owned[update_slot] <= 1;
            end
          end
          source_index <= source_index + 1'b1;
          state <= SOURCE_BEGIN;
        end
        EXP_BEGIN: begin source_index <= 0; sum <= 0; state <= SCORE_READ; end
        SCORE_READ: begin
          if (source_index == source_limit) state <= PROB_BEGIN;
          else if (next_participating == 0) source_index <= source_index + 1'b1;
          else begin participating <= next_participating; state <= SHIFT_SEND; end
        end
        SHIFT_SEND: if (scalar_send) state <= SHIFT_WAIT;
        SHIFT_WAIT: if (scalar_consume) begin current <= scalar_data; state <= EXP_SEND; end
        EXP_SEND: if (scalar_send) state <= EXP_WAIT;
        EXP_WAIT: if (scalar_consume) begin current <= scalar_data; state <= EXP_STORE; end
        EXP_STORE: state <= SUM_SEND;
        SUM_SEND: if (scalar_send) state <= SUM_WAIT;
        SUM_WAIT: if (scalar_consume) begin
          for (update_slot = 0; update_slot < 4; update_slot = update_slot + 1)
            if (participating[update_slot])
              sum[32*update_slot+:32] <= scalar_data[32*update_slot+:32];
          source_index <= source_index + 1'b1;
          state <= SCORE_READ;
        end
        PROB_BEGIN: begin source_index <= 0; state <= EXP_READ; end
        EXP_READ: begin
          if (source_index == source_limit) begin column <= 0; state <= VALUE_BEGIN; end
          else if (next_participating == 0) source_index <= source_index + 1'b1;
          else begin participating <= next_participating; state <= PROB_SEND; end
        end
        PROB_SEND: if (scalar_send) state <= PROB_WAIT;
        PROB_WAIT: if (scalar_consume) begin current <= scalar_data; state <= PROB_STORE; end
        PROB_STORE: begin
          if (probability_bad) begin failed <= 1; state <= COMPLETE; end
          else begin source_index <= source_index + 1'b1; state <= EXP_READ; end
        end
        VALUE_BEGIN: begin
          value_phase <= 1;
          source_index <= 0;
          context0 <= 0;
          context1 <= 0;
          context2 <= 0;
          context3 <= 0;
          state <= VALUE_SOURCE;
        end
        VALUE_SOURCE: begin
          if (source_index == source_limit) state <= REDUCE0_SEND;
          else if (next_participating == 0) source_index <= source_index + 1'b1;
          else begin
            participating <= next_participating;
            source_position <= next_position;
            source_node <= next_node;
            source_provisional <= next_provisional;
            state <= PROB_READ;
          end
        end
        PROB_READ: state <= KV_SEND;
        OUTPUT_WORD: if (out_valid && out_ready) begin
          if (column + 1'b1 < D) begin column <= column + 1'b1; state <= VALUE_BEGIN; end
          else if (head + 1'b1 == Q) state <= COMPLETE;
          else begin
            head <= head + 1'b1;
            head_base <= head_base + 10'(D);
            if (mapped_offset + 1'b1 == RATIO) begin
              mapped_offset <= 0;
              mapped_head <= mapped_head + 1'b1;
            end else mapped_offset <= mapped_offset + 1'b1;
            state <= HEAD_BEGIN;
          end
        end
        DRAIN: if (!kv_owned || (kv_rsp_valid && kv_rsp_ready)) state <= COMPLETE;
        COMPLETE: state <= IDLE;
        default: begin failed <= 1; cancel <= 1; state <= DRAIN; end
      endcase
    end
  end
endmodule
