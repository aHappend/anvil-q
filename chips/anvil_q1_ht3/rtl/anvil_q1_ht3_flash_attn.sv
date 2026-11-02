module anvil_q1_ht3_flash_attn #(
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2,
  parameter HEAD_DIM = 64, MAX_SEQ_LEN = 32768,
  parameter TILE_TOKENS = 16
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
  output wire busy, done, error,
  input wire [1:0] cmd_kv_format,
  input wire [31:0] kv_key_scale, kv_value_scale
);
  import anvil_q1_ht3_fp_pkg::*;
  function automatic integer head_ratio(input integer q, input integer k);
    integer n;
    begin
      head_ratio = 0;
      for (n = 1; n <= 14; n = n + 1)
        if (n*k == q) head_ratio = n;
    end
  endfunction
  localparam RATIO = head_ratio(NUM_Q_HEADS, NUM_KV_HEADS);
  localparam LEGAL = NUM_Q_HEADS >= 1 && NUM_Q_HEADS <= 14 &&
    NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 && RATIO != 0 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    NUM_Q_HEADS*HEAD_DIM >= 8 && NUM_Q_HEADS*HEAD_DIM <= 896 &&
    ((NUM_Q_HEADS*HEAD_DIM) & 7) == 0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
    MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768 &&
    TILE_TOKENS >= 1 && TILE_TOKENS <= 128;
  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 FlashAttention geometry");
  end
  generate if (!LEGAL) begin: g_invalid
    assign cmd_ready = 0;
    assign query_ready = 0;
    assign kv_valid = 0;
    assign kv_provisional = 0;
    assign kv_node = 0;
    assign kv_position = 0;
    assign kv_head = 0;
    assign kv_column = 0;
    assign kv_rsp_ready = 0;
    assign out_valid = 0;
    assign out_index = 0;
    assign out_data = 0;
    assign out_slots = 0;
    assign busy = 0;
    assign done = 0;
    assign error = 0;
  end else begin: g_legal
    localparam IDLE = 5'd0, QUERY_FILL = 5'd1, HEAD_START = 5'd2,
      TILE_WAIT = 5'd3, SCORE_READ = 5'd4, VALUE_READ = 5'd5,
      O_READ = 5'd6, ISSUE = 5'd7, WAIT_ARITH = 5'd8,
      SCORE_WRITE = 5'd9, O_WRITE = 5'd10, TILE_RETIRE = 5'd11,
      OUTPUT_READ = 5'd12, OUTPUT_HOLD = 5'd13, DRAIN = 5'd14,
      COMPLETE = 5'd15, SCORE_LOAD = 5'd16;
    localparam ROOT = 5'd0, INVERSE = 5'd1, KEY_DEQUANT = 5'd2,
      DOT_MUL = 5'd3, DOT_ADD = 5'd4, SCORE_SCALE = 5'd5,
      ALPHA_SUB = 5'd6, ALPHA_EXP = 5'd7, SUM_RESCALE = 5'd8,
      O_RESCALE = 5'd9, P_SUB = 5'd10, P_EXP = 5'd11,
      SUM_ADD = 5'd12, VALUE_DEQUANT = 5'd13,
      VALUE_MUL = 5'd14, O_ADD = 5'd15, FINAL_DIV = 5'd16;
    wire run_n;
    reg [4:0] state;
    reg [4:0] phase;
    reg [3:0] slots_q, participating, maximum_owned, tile_owned;
    reg fp16_q, failed, canceled, tile_started;
    reg [1:0] format_q;
    reg [31:0] prefix_q;
    reg [127:0] positions_q;
    reg [15:0] ancestors_q;
    reg [9:0] query_index, head_base;
    reg [3:0] head_q, mapped_head, mapped_offset;
    reg [6:0] column_q;
    reg [7:0] token_q, tile_count;
    reg buffer_q;
    reg [127:0] accumulator, product_q, key_q, value_q;
    reg [127:0] maximum, next_maximum, alpha, sum, probability;
    reg [127:0] current, result_q;
    reg [31:0] root_q, scale_q;
    reg [63:0] query_q;
    reg [15:0] key_word_q, value_word_q;
    reg [31:0] key_scale_q, value_scale_q;
    reg [127:0] o_q, score_q;
    wire [31:0] dimension_float = pack32(1'b0, 64'(HEAD_DIM), 0);
    (* ramstyle = "M20K", nomem2reg *)
    reg [63:0] queries [0:NUM_Q_HEADS*HEAD_DIM-1];
    (* ramstyle = "M20K", nomem2reg *) reg [127:0] output_state [0:HEAD_DIM-1];
    (* ramstyle = "M20K", nomem2reg *) reg [131:0] scores [0:TILE_TOKENS-1];
    reg [63:0] query_read;
    reg [127:0] output_read;
    reg [131:0] score_read;
    wire [1:0] tiles_valid, tiles_last;
    wire [15:0] tiles_counts;
    wire tile_start_ready, tile_busy, tile_fetch_done, tile_error;
    wire tile_fault = tile_started && tile_error;
    wire [15:0] tile_key, tile_value;
    wire [31:0] tile_key_scale, tile_value_scale;
    wire [3:0] tile_slots;
    wire tile_start = run_n && state == HEAD_START && !canceled &&
      !abort_error && tile_start_ready;
    wire tile_read = run_n && (state == SCORE_READ || state == VALUE_READ);
    wire tile_release = run_n && state == O_WRITE && phase == O_ADD &&
      column_q + 1'b1 == HEAD_DIM && token_q + 1'b1 == tile_count;
    wire [3:0] arithmetic_ready, arithmetic_valid, arithmetic_errors;
    wire [127:0] arithmetic_data;
    reg [2:0] arithmetic_opcode;
    reg [127:0] arithmetic_a, arithmetic_b;
    reg [3:0] arithmetic_mask;
    wire arithmetic_issue = run_n && state == ISSUE && !canceled &&
      !abort_error && (&arithmetic_ready);
    wire arithmetic_retire = run_n && state == WAIT_ARITH && (&arithmetic_valid);
    wire arithmetic_bad = |(arithmetic_errors & arithmetic_mask);
    wire arithmetic_drain = run_n && state == DRAIN;
    wire [31:0] integer_key, integer_value;
    wire [7:0] key_magnitude = format_q == 2 ?
      (key_word_q[3] ? {4'b0, (~key_word_q[3:0] + 4'd1)} :
                       {4'b0, key_word_q[3:0]}) :
      (key_word_q[7] ? (~key_word_q[7:0] + 8'd1) : key_word_q[7:0]);
    wire [7:0] value_magnitude = format_q == 2 ?
      (value_word_q[3] ? {4'b0, (~value_word_q[3:0] + 4'd1)} :
                         {4'b0, value_word_q[3:0]}) :
      (value_word_q[7] ? (~value_word_q[7:0] + 8'd1) : value_word_q[7:0]);
    wire key_negative = format_q == 2 ? key_word_q[3] : key_word_q[7];
    wire value_negative = format_q == 2 ? value_word_q[3] : value_word_q[7];
    assign integer_key = pack32(key_negative, {56'b0, key_magnitude}, 0);
    assign integer_value = pack32(value_negative, {56'b0, value_magnitude}, 0);
    wire key_scale_bad = key_scale_q[31] || key_scale_q[30:0] == 0 ||
      fp32_nonfinite(key_scale_q);
    wire value_scale_bad = value_scale_q[31] || value_scale_q[30:0] == 0 ||
      fp32_nonfinite(value_scale_q);
    wire packed_word_bad = format_q == 2 ?
      (|key_word_q[15:4]) || (|value_word_q[15:4]) :
      (|key_word_q[15:8]) || (|value_word_q[15:8]);
    reg command_bad, query_bad, tile_word_bad;
    reg [3:0] ancestor_count;
    reg [32:0] expected_position;
    reg [127:0] masked_result;
    integer check_slot, memory_slot, n, a, peer;
    genvar slot;

    function automatic greater32(input [31:0] x, input [31:0] y);
      begin
        if (x[30:0] == 0 && y[30:0] == 0) greater32 = 0;
        else if (x[31] != y[31]) greater32 = !x[31];
        else if (x[31]) greater32 = x[30:0] < y[30:0];
        else greater32 = x[30:0] > y[30:0];
      end
    endfunction

    anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
    anvil_q1_ht3_attn_tiles #(.HEAD_DIM(HEAD_DIM), .TILE_TOKENS(TILE_TOKENS)) u_tiles (
      .clk(clk), .rst_n(rst_n), .abort_error(canceled || abort_error),
      .start_valid(tile_start), .start_ready(tile_start_ready),
      .start_head({28'b0, mapped_head}), .start_prefix(prefix_q),
      .start_slots(slots_q), .start_positions(positions_q), .start_ancestors(ancestors_q),
      .tile_valid(tiles_valid), .tile_counts(tiles_counts), .tile_last(tiles_last),
      .release_valid(tile_release), .release_buffer(buffer_q),
      .read_valid(tile_read), .read_buffer(buffer_q),
      .read_token(token_q), .read_column(column_q),
      .read_key(tile_key), .read_value(tile_value),
      .read_key_scale(tile_key_scale), .read_value_scale(tile_value_scale),
      .read_slots(tile_slots), .kv_valid(kv_valid), .kv_ready(kv_ready),
      .kv_provisional(kv_provisional), .kv_node(kv_node),
      .kv_position(kv_position), .kv_head(kv_head), .kv_column(kv_column),
      .kv_rsp_valid(kv_rsp_valid), .kv_rsp_ready(kv_rsp_ready),
      .kv_key(kv_key), .kv_value(kv_value), .kv_key_scale(kv_key_scale),
      .kv_value_scale(kv_value_scale), .kv_rsp_error(kv_rsp_error),
      .busy(tile_busy), .fetch_done(tile_fetch_done), .error(tile_error)
    );
    for (slot = 0; slot < 4; slot = slot + 1) begin: g_slot
      anvil_q1_ht3_scalar u_scalar (
        .clk(clk), .rst_n(rst_n),
        .req_valid(arithmetic_issue), .req_ready(arithmetic_ready[slot]),
        .req_opcode(arithmetic_opcode),
        .req_a(arithmetic_a[32*slot+:32]), .req_b(arithmetic_b[32*slot+:32]),
        .rsp_valid(arithmetic_valid[slot]),
        .rsp_ready(arithmetic_retire || arithmetic_drain),
        .rsp_data(arithmetic_data[32*slot+:32]), .rsp_error(arithmetic_errors[slot])
      );
    end
    assign cmd_ready = run_n && state == IDLE && !abort_error;
    assign query_ready = run_n && state == QUERY_FILL && !abort_error;
    assign out_valid = run_n && state == OUTPUT_HOLD;
    assign out_index = out_valid ? {22'b0, head_base} + {25'b0, column_q} : 32'b0;
    assign out_data = out_valid ? masked_result : 128'b0;
    assign out_slots = out_valid ? slots_q : 4'b0;
    assign busy = run_n && state != IDLE;
    assign done = run_n && state == COMPLETE;
    assign error = done && failed;

    always @* begin
      command_bad = cmd_slots == 0 || cmd_prefix_length > MAX_SEQ_LEN;
      ancestor_count = 0;
      expected_position = 0;
      for (n = 0; n < 4; n = n + 1) begin
        if (cmd_slots[n]) begin
          ancestor_count = 0;
          if (!cmd_ancestors[4*n+n]) command_bad = 1;
          for (a = 0; a < 4; a = a + 1) begin
            if (cmd_ancestors[4*n+a]) begin
              ancestor_count = ancestor_count + 1'b1;
              if (!cmd_slots[a] || a > n) command_bad = 1;
              if (a != n && cmd_positions[32*a+:32] >= cmd_positions[32*n+:32])
                command_bad = 1;
              if (a != n &&
                  (cmd_ancestors[4*a+:4] & ~cmd_ancestors[4*n+:4]) != 0)
                command_bad = 1;
              for (peer = 0; peer < 4; peer = peer + 1)
                if (peer < a && cmd_ancestors[4*n+peer] &&
                    cmd_positions[32*peer+:32] == cmd_positions[32*a+:32])
                  command_bad = 1;
            end
          end
          expected_position = {1'b0, cmd_prefix_length} +
            {29'b0, ancestor_count} - 1'b1;
          if (expected_position >= MAX_SEQ_LEN ||
              {1'b0, cmd_positions[32*n+:32]} != expected_position)
            command_bad = 1;
        end else if (cmd_ancestors[4*n+:4] != 0) command_bad = 1;
      end
      query_bad = 0;
      masked_result = 0;
      for (check_slot = 0; check_slot < 4; check_slot = check_slot + 1) begin
        if (slots_q[check_slot]) begin
          if (fp32_nonfinite(expand16(query_data[16*check_slot+:16], fp16_q))) query_bad = 1;
          masked_result[32*check_slot+:32] = result_q[32*check_slot+:32];
        end
      end
      tile_word_bad = 0;
      if (format_q[1])
        tile_word_bad = key_scale_bad || value_scale_bad || packed_word_bad;
      else tile_word_bad = fp32_nonfinite(expand16(key_word_q, format_q == 1)) ||
        fp32_nonfinite(expand16(value_word_q, format_q == 1));
    end

    always @* begin: p_operands
      integer s;
      arithmetic_opcode = 0;
      arithmetic_a = 0;
      arithmetic_b = 0;
      arithmetic_mask = slots_q;
      if (phase == KEY_DEQUANT || phase == DOT_MUL || phase == DOT_ADD ||
          phase == SCORE_SCALE || phase == P_SUB || phase == P_EXP ||
          phase == SUM_ADD || phase == VALUE_DEQUANT || phase == VALUE_MUL ||
          phase == O_ADD) arithmetic_mask = participating;
      for (s = 0; s < 4; s = s + 1) begin
        case (phase)
          ROOT: begin arithmetic_opcode = 3; arithmetic_a[32*s+:32] = dimension_float; end
          INVERSE: begin
            arithmetic_opcode = 2;
            arithmetic_a[32*s+:32] = 32'h3f800000;
            arithmetic_b[32*s+:32] = root_q;
          end
          KEY_DEQUANT: begin
            arithmetic_opcode = 1;
            if (participating[s]) begin
              arithmetic_a[32*s+:32] = integer_key;
              arithmetic_b[32*s+:32] = key_scale_q;
            end
          end
          DOT_MUL: begin
            arithmetic_opcode = 1;
            if (participating[s]) begin
              arithmetic_a[32*s+:32] = expand16(query_q[16*s+:16], fp16_q);
              arithmetic_b[32*s+:32] = key_q[32*s+:32];
            end
          end
          DOT_ADD: if (participating[s]) begin
            arithmetic_a[32*s+:32] = accumulator[32*s+:32];
            arithmetic_b[32*s+:32] = product_q[32*s+:32];
          end
          SCORE_SCALE: begin
            arithmetic_opcode = 1;
            if (participating[s]) begin
              arithmetic_a[32*s+:32] = accumulator[32*s+:32];
              arithmetic_b[32*s+:32] = scale_q;
            end
          end
          ALPHA_SUB: if (slots_q[s] && maximum_owned[s]) begin
            arithmetic_a[32*s+:32] = maximum[32*s+:32];
            arithmetic_b[32*s+:32] =
              {~next_maximum[32*s+31], next_maximum[32*s+:31]};
          end
          ALPHA_EXP: begin arithmetic_opcode = 4; arithmetic_a[32*s+:32] = current[32*s+:32]; end
          SUM_RESCALE: begin
            arithmetic_opcode = 1;
            if (slots_q[s]) begin
              arithmetic_a[32*s+:32] = alpha[32*s+:32];
              arithmetic_b[32*s+:32] = sum[32*s+:32];
            end
          end
          O_RESCALE: begin
            arithmetic_opcode = 1;
            if (slots_q[s] && maximum_owned[s]) begin
              arithmetic_a[32*s+:32] = alpha[32*s+:32];
              arithmetic_b[32*s+:32] = o_q[32*s+:32];
            end
          end
          P_SUB: if (participating[s]) begin
            arithmetic_a[32*s+:32] = score_q[32*s+:32];
            arithmetic_b[32*s+:32] =
              {~next_maximum[32*s+31], next_maximum[32*s+:31]};
          end
          P_EXP: begin arithmetic_opcode = 4; arithmetic_a[32*s+:32] = current[32*s+:32]; end
          SUM_ADD: if (participating[s]) begin
            arithmetic_a[32*s+:32] = sum[32*s+:32];
            arithmetic_b[32*s+:32] = probability[32*s+:32];
          end
          VALUE_DEQUANT: begin
            arithmetic_opcode = 1;
            if (participating[s]) begin
              arithmetic_a[32*s+:32] = integer_value;
              arithmetic_b[32*s+:32] = value_scale_q;
            end
          end
          VALUE_MUL: begin
            arithmetic_opcode = 1;
            if (participating[s]) begin
              arithmetic_a[32*s+:32] = probability[32*s+:32];
              arithmetic_b[32*s+:32] = value_q[32*s+:32];
            end
          end
          O_ADD: if (participating[s]) begin
            arithmetic_a[32*s+:32] = o_q[32*s+:32];
            arithmetic_b[32*s+:32] = product_q[32*s+:32];
          end
          FINAL_DIV: begin
            arithmetic_opcode = 2;
            arithmetic_b[32*s+:32] = 32'h3f800000;
            if (slots_q[s]) begin
              arithmetic_a[32*s+:32] = o_q[32*s+:32];
              arithmetic_b[32*s+:32] = sum[32*s+:32];
            end
          end
          default: begin end
        endcase
      end
    end

    always @(posedge clk) begin
      if (run_n) begin
        if (query_valid && query_ready && !query_bad) queries[query_index] <= query_data;
        if (state == SCORE_READ)
          query_read <= queries[head_base + {3'b0, column_q}];
        if (state == O_READ || state == VALUE_READ || state == OUTPUT_READ)
          output_read <= output_state[column_q];
        if (state == O_READ && phase == P_SUB) score_read <= scores[token_q];
        if (state == SCORE_WRITE) scores[token_q] <= {participating, current};
        if (state == O_WRITE) begin
          if (phase == O_ADD) begin
            for (memory_slot = 0; memory_slot < 4; memory_slot = memory_slot + 1)
              if (participating[memory_slot])
                output_state[column_q][32*memory_slot+:32] <= current[32*memory_slot+:32];
          end else output_state[column_q] <= current;
        end
      end
    end

    always @(posedge clk or negedge rst_n) begin: p_control
      integer s;
      if (!rst_n) begin
        state <= IDLE;
        phase <= ROOT;
        slots_q <= 0;
        participating <= 0;
        maximum_owned <= 0;
        tile_owned <= 0;
        fp16_q <= 0;
        failed <= 0;
        canceled <= 0;
        tile_started <= 0;
        format_q <= 0;
        prefix_q <= 0;
        positions_q <= 0;
        ancestors_q <= 0;
        query_index <= 0;
        head_base <= 0;
        head_q <= 0;
        mapped_head <= 0;
        mapped_offset <= 0;
        column_q <= 0;
        token_q <= 0;
        tile_count <= 0;
        buffer_q <= 0;
        accumulator <= 0;
        product_q <= 0;
        key_q <= 0;
        value_q <= 0;
        maximum <= 0;
        next_maximum <= 0;
        alpha <= 0;
        sum <= 0;
        probability <= 0;
        current <= 0;
        result_q <= 0;
        root_q <= 0;
        scale_q <= 0;
        query_q <= 0;
        key_word_q <= 0;
        value_word_q <= 0;
        key_scale_q <= 0;
        value_scale_q <= 0;
        o_q <= 0;
        score_q <= 0;
      end else if (run_n) begin
        if ((abort_error || tile_fault) && state != IDLE && state != COMPLETE) begin
          canceled <= 1;
          failed <= 1;
          if (state != OUTPUT_HOLD) state <= DRAIN;
        end
        if (!(abort_error || tile_fault) || state == OUTPUT_HOLD ||
            state == DRAIN || state == COMPLETE) begin
          case (state)
            IDLE: if (cmd_valid && cmd_ready) begin
              fp16_q <= cmd_fp16;
              format_q <= cmd_kv_format;
              slots_q <= cmd_slots;
              prefix_q <= cmd_prefix_length;
              positions_q <= cmd_positions;
              ancestors_q <= cmd_ancestors;
              query_index <= 0;
              head_base <= 0;
              head_q <= 0;
              mapped_head <= 0;
              mapped_offset <= 0;
              canceled <= 0;
              tile_started <= 0;
              failed <= 0;
              if (command_bad) begin failed <= 1; state <= COMPLETE; end
              else state <= QUERY_FILL;
            end
            QUERY_FILL: if (query_valid && query_ready) begin
              if (query_bad) begin failed <= 1; state <= DRAIN; canceled <= 1; end
              else if (query_index + 1'b1 == NUM_Q_HEADS*HEAD_DIM) begin
                phase <= ROOT;
                state <= ISSUE;
              end else query_index <= query_index + 1'b1;
            end
            HEAD_START: if (tile_start) begin
              tile_started <= 1;
              maximum <= 0;
              maximum_owned <= 0;
              next_maximum <= 0;
              tile_owned <= 0;
              sum <= 0;
              buffer_q <= 0;
              token_q <= 0;
              column_q <= 0;
              accumulator <= 0;
              state <= TILE_WAIT;
            end
            TILE_WAIT: begin
              if (tiles_valid[buffer_q]) begin
                tile_count <= tiles_counts[8*buffer_q+:8];
                token_q <= 0;
                column_q <= 0;
                accumulator <= 0;
                next_maximum <= maximum;
                tile_owned <= maximum_owned;
                phase <= KEY_DEQUANT;
                state <= SCORE_READ;
              end else if (tile_fetch_done) begin
                if (maximum_owned != slots_q) begin
                  failed <= 1;
                  canceled <= 1;
                  state <= DRAIN;
                end else begin
                  column_q <= 0;
                  phase <= FINAL_DIV;
                  state <= OUTPUT_READ;
                end
              end
            end
            SCORE_READ, VALUE_READ: begin
              // The synchronous tile/Q/o read completes after this edge.
              state <= O_READ;
            end
            O_READ: begin
              if (phase == KEY_DEQUANT || phase == VALUE_DEQUANT) begin
                key_word_q <= tile_key;
                value_word_q <= tile_value;
                key_scale_q <= tile_key_scale;
                value_scale_q <= tile_value_scale;
                participating <= tile_slots;
                query_q <= query_read;
                o_q <= output_read;
                if (format_q[1]) state <= ISSUE;
                else begin
                  for (s = 0; s < 4; s = s + 1) begin
                    key_q[32*s+:32] <= tile_slots[s] ?
                      expand16(tile_key, format_q == 1) : 32'b0;
                    value_q[32*s+:32] <= tile_slots[s] ?
                      expand16(tile_value, format_q == 1) : 32'b0;
                  end
                  if (phase == KEY_DEQUANT) phase <= DOT_MUL;
                  else phase <= VALUE_MUL;
                  state <= ISSUE;
                end
              end else if (phase == P_SUB) state <= SCORE_LOAD;
              else begin o_q <= output_read; state <= ISSUE; end
            end
            SCORE_LOAD: begin
              participating <= score_read[131:128];
              score_q <= score_read[127:0];
              state <= ISSUE;
            end
            ISSUE: begin
              if ((phase == KEY_DEQUANT || phase == DOT_MUL ||
                   phase == VALUE_DEQUANT || phase == VALUE_MUL) &&
                  participating != 0 && tile_word_bad) begin
                failed <= 1;
                canceled <= 1;
                state <= DRAIN;
              end else if (arithmetic_issue) state <= WAIT_ARITH;
            end
            WAIT_ARITH: if (arithmetic_retire) begin
              if (arithmetic_bad) begin
                failed <= 1;
                canceled <= 1;
                state <= DRAIN;
              end else begin
                case (phase)
                  ROOT: begin root_q <= arithmetic_data[31:0]; phase <= INVERSE; state <= ISSUE; end
                  INVERSE: begin scale_q <= arithmetic_data[31:0]; state <= HEAD_START; end
                  KEY_DEQUANT: begin key_q <= arithmetic_data; phase <= DOT_MUL; state <= ISSUE; end
                  DOT_MUL: begin product_q <= arithmetic_data; phase <= DOT_ADD; state <= ISSUE; end
                  DOT_ADD: begin
                    accumulator <= arithmetic_data;
                    if (column_q + 1'b1 == HEAD_DIM) begin phase <= SCORE_SCALE; state <= ISSUE; end
                    else begin
                      column_q <= column_q + 1'b1;
                      phase <= KEY_DEQUANT;
                      state <= SCORE_READ;
                    end
                  end
                  SCORE_SCALE: begin current <= arithmetic_data; state <= SCORE_WRITE; end
                  ALPHA_SUB: begin current <= arithmetic_data; phase <= ALPHA_EXP; state <= ISSUE; end
                  ALPHA_EXP: begin
                    for (s = 0; s < 4; s = s + 1)
                      alpha[32*s+:32] <= slots_q[s] && maximum_owned[s] ?
                        arithmetic_data[32*s+:32] : 32'b0;
                    phase <= SUM_RESCALE;
                    state <= ISSUE;
                  end
                  SUM_RESCALE: begin
                    sum <= arithmetic_data;
                    column_q <= 0;
                    phase <= O_RESCALE;
                    state <= OUTPUT_READ;
                  end
                  O_RESCALE: begin current <= arithmetic_data; state <= O_WRITE; end
                  P_SUB: begin current <= arithmetic_data; phase <= P_EXP; state <= ISSUE; end
                  P_EXP: begin
                    for (s = 0; s < 4; s = s + 1)
                      probability[32*s+:32] <= participating[s] ?
                        arithmetic_data[32*s+:32] : 32'b0;
                    phase <= SUM_ADD;
                    state <= ISSUE;
                  end
                  SUM_ADD: begin
                    for (s = 0; s < 4; s = s + 1)
                      if (participating[s]) sum[32*s+:32] <= arithmetic_data[32*s+:32];
                    column_q <= 0;
                    phase <= VALUE_DEQUANT;
                    state <= VALUE_READ;
                  end
                  VALUE_DEQUANT: begin value_q <= arithmetic_data; phase <= VALUE_MUL; state <= ISSUE; end
                  VALUE_MUL: begin product_q <= arithmetic_data; phase <= O_ADD; state <= ISSUE; end
                  O_ADD: begin current <= arithmetic_data; state <= O_WRITE; end
                  FINAL_DIV: begin result_q <= arithmetic_data; state <= OUTPUT_HOLD; end
                  default: begin failed <= 1; canceled <= 1; state <= DRAIN; end
                endcase
              end
            end
            SCORE_WRITE: begin
              for (s = 0; s < 4; s = s + 1)
                if (participating[s]) begin
                  if (!tile_owned[s] ||
                      greater32(current[32*s+:32], next_maximum[32*s+:32]))
                    next_maximum[32*s+:32] <= current[32*s+:32];
                  tile_owned[s] <= 1;
                end
              if (token_q + 1'b1 == tile_count) begin
                phase <= ALPHA_SUB;
                state <= ISSUE;
              end else begin
                token_q <= token_q + 1'b1;
                column_q <= 0;
                accumulator <= 0;
                phase <= KEY_DEQUANT;
                state <= SCORE_READ;
              end
            end
            O_WRITE: begin
              if (column_q + 1'b1 != HEAD_DIM) begin
                column_q <= column_q + 1'b1;
                if (phase == O_ADD) begin phase <= VALUE_DEQUANT; state <= VALUE_READ; end
                else state <= OUTPUT_READ;
              end else if (phase == O_RESCALE) begin
                token_q <= 0;
                column_q <= 0;
                phase <= P_SUB;
                state <= O_READ;
              end else if (token_q + 1'b1 != tile_count) begin
                token_q <= token_q + 1'b1;
                phase <= P_SUB;
                state <= O_READ;
              end else begin
                maximum <= next_maximum;
                maximum_owned <= tile_owned;
                buffer_q <= !buffer_q;
                token_q <= 0;
                column_q <= 0;
                accumulator <= 0;
                if (tiles_valid[!buffer_q]) begin
                  tile_count <= tiles_counts[8*(!buffer_q)+:8];
                  phase <= KEY_DEQUANT;
                  state <= SCORE_READ;
                end else if (tiles_last[buffer_q] || tile_fetch_done) begin
                  if (tile_owned != slots_q) begin
                    failed <= 1;
                    canceled <= 1;
                    state <= DRAIN;
                  end else begin phase <= FINAL_DIV; state <= OUTPUT_READ; end
                end else state <= TILE_WAIT;
              end
            end
            OUTPUT_READ: state <= O_READ;
            OUTPUT_HOLD: if (out_ready) begin
              if (canceled || abort_error || tile_fault) state <= DRAIN;
              else if (column_q + 1'b1 != HEAD_DIM) begin
                column_q <= column_q + 1'b1;
                phase <= FINAL_DIV;
                state <= OUTPUT_READ;
              end else if (head_q + 1'b1 == NUM_Q_HEADS) state <= DRAIN;
              else begin
                head_q <= head_q + 1'b1;
                head_base <= head_base + HEAD_DIM;
                if (mapped_offset + 1'b1 == RATIO) begin
                  mapped_offset <= 0;
                  mapped_head <= mapped_head + 1'b1;
                end else mapped_offset <= mapped_offset + 1'b1;
                state <= HEAD_START;
              end
            end
            DRAIN: if (!tile_busy && (&arithmetic_ready)) state <= COMPLETE;
            COMPLETE: state <= IDLE;
            default: begin failed <= 1; canceled <= 1; state <= DRAIN; end
          endcase
        end
      end
    end
  end endgenerate
endmodule
