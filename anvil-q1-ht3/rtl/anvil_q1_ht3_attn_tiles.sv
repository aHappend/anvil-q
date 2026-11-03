module anvil_q1_ht3_attn_tiles #(
  parameter HEAD_DIM = 64, TILE_TOKENS = 16
) (
  input wire clk, rst_n, abort_error,
  input wire start_valid,
  output wire start_ready,
  input wire [31:0] start_head, start_prefix,
  input wire [3:0] start_slots,
  input wire [127:0] start_positions,
  input wire [15:0] start_ancestors,
  output wire [1:0] tile_valid,
  output wire [15:0] tile_counts,
  output wire [1:0] tile_last,
  input wire release_valid, release_buffer,
  input wire read_valid, read_buffer,
  input wire [7:0] read_token,
  input wire [6:0] read_column,
  output reg [15:0] read_key, read_value,
  output reg [31:0] read_key_scale, read_value_scale,
  output reg [3:0] read_slots,
  output wire kv_valid,
  input wire kv_ready,
  output wire kv_provisional,
  output wire [1:0] kv_node,
  output wire [31:0] kv_position, kv_head, kv_column,
  input wire kv_rsp_valid,
  output wire kv_rsp_ready,
  input wire [15:0] kv_key, kv_value,
  input wire [31:0] kv_key_scale, kv_value_scale,
  input wire kv_rsp_error,
  output wire busy, fetch_done, error
);
  localparam LEGAL = HEAD_DIM >= 2 && HEAD_DIM <= 64 &&
    (HEAD_DIM & 1) == 0 && TILE_TOKENS >= 1 && TILE_TOKENS <= 128;
  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 attention tile geometry");
  end
  generate if (!LEGAL) begin: g_invalid
    assign start_ready = 0;
    assign tile_valid = 0;
    assign tile_counts = 0;
    assign tile_last = 0;
    assign kv_valid = 0;
    assign kv_provisional = 0;
    assign kv_node = 0;
    assign kv_position = 0;
    assign kv_head = 0;
    assign kv_column = 0;
    assign kv_rsp_ready = 0;
    assign busy = 0;
    assign fetch_done = 0;
    assign error = 0;
    always @* begin
      read_key = 0;
      read_value = 0;
      read_key_scale = 0;
      read_value_scale = 0;
      read_slots = 0;
    end
  end else begin: g_legal
    localparam IDLE = 3'd0, PICK = 3'd1, SCAN = 3'd2,
      SEND = 3'd3, WAIT_RSP = 3'd4, PUBLISH = 3'd5,
      FINISH = 3'd6, DRAIN = 3'd7;
    wire run_n;
    reg [2:0] state;
    reg [1:0] ready_q, last_q;
    reg [7:0] count0, count1, fill_count;
    reg fill_buffer, next_buffer, owned, canceled, failed, finished, read_owned;
    reg [16:0] source_index, source_limit;
    reg [31:0] prefix_q, head_q, position_q;
    reg [127:0] positions_q;
    reg [15:0] ancestors_q;
    reg [3:0] slots_q, source_slots;
    reg provisional_q;
    reg [1:0] node_q;
    reg [6:0] column_q;
    reg [13:0] fill_address;
    reg [3:0] next_slots;
    reg [31:0] next_position;
    wire next_provisional = {15'b0, source_index} >= prefix_q;
    wire [1:0] next_node = 2'({15'b0, source_index} - prefix_q);
    wire request_transfer = kv_valid && kv_ready;
    wire response_transfer = kv_rsp_valid && kv_rsp_ready;
    wire store_response = response_transfer && !kv_rsp_error &&
      !canceled && !abort_error;
    wire [14:0] write_address = (fill_buffer ? 15'(TILE_TOKENS*HEAD_DIM) : 0) +
      {1'b0, fill_address};
    wire [14:0] read_address = (read_buffer ? 15'(TILE_TOKENS*HEAD_DIM) : 0) +
      15'(read_token*HEAD_DIM) + {8'b0, read_column};
    (* ramstyle = "M20K", nomem2reg *) reg [95:0] words [0:2*TILE_TOKENS*HEAD_DIM-1];
    (* ramstyle = "M20K", nomem2reg *) reg [3:0] masks [0:2*TILE_TOKENS-1];
    reg [95:0] word_read;
    reg [3:0] mask_read;
    integer s;

    anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
    assign start_ready = run_n && state == IDLE && !abort_error;
    assign tile_valid = run_n ? ready_q : 2'b0;
    assign tile_counts = run_n ? {count1, count0} : 16'b0;
    assign tile_last = run_n ? last_q : 2'b0;
    assign kv_valid = run_n && state == SEND;
    assign kv_provisional = kv_valid && provisional_q;
    assign kv_node = kv_valid && provisional_q ? node_q : 2'b0;
    assign kv_position = kv_valid ? position_q : 32'b0;
    assign kv_head = kv_valid ? head_q : 32'b0;
    assign kv_column = kv_valid ? {25'b0, column_q} : 32'b0;
    assign kv_rsp_ready = run_n &&
      (state == WAIT_RSP || (state == SEND && kv_ready) ||
       (state == DRAIN && owned));
    assign busy = run_n && state != IDLE;
    assign fetch_done = run_n && finished && state != PUBLISH;
    assign error = run_n && failed;

    always @* begin
      next_position = {15'b0, source_index};
      next_slots = slots_q;
      if (next_provisional) begin
        next_position = positions_q[32*next_node+:32];
        for (s = 0; s < 4; s = s + 1)
          next_slots[s] = slots_q[s] && slots_q[next_node] &&
            ancestors_q[4*s+next_node];
      end
      read_key = 0;
      read_value = 0;
      read_key_scale = 0;
      read_value_scale = 0;
      read_slots = 0;
      if (run_n && read_owned) begin
        read_key = word_read[15:0];
        read_value = word_read[31:16];
        read_key_scale = word_read[63:32];
        read_value_scale = word_read[95:64];
        read_slots = mask_read;
      end
    end

    always @(posedge clk) begin
      if (run_n) begin
        if (store_response) begin
          words[write_address] <= {kv_value_scale, kv_key_scale, kv_value, kv_key};
          if (column_q == 0)
            masks[(fill_buffer ? TILE_TOKENS : 0) + fill_count] <= source_slots;
        end
        if (read_valid) begin
          word_read <= words[read_address];
          mask_read <= masks[(read_buffer ? TILE_TOKENS : 0) + read_token];
        end
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        ready_q <= 0;
        last_q <= 0;
        count0 <= 0;
        count1 <= 0;
        fill_count <= 0;
        fill_buffer <= 0;
        next_buffer <= 0;
        owned <= 0;
        canceled <= 0;
        failed <= 0;
        finished <= 0;
        read_owned <= 0;
        source_index <= 0;
        source_limit <= 0;
        prefix_q <= 0;
        head_q <= 0;
        position_q <= 0;
        positions_q <= 0;
        ancestors_q <= 0;
        slots_q <= 0;
        source_slots <= 0;
        provisional_q <= 0;
        node_q <= 0;
        column_q <= 0;
        fill_address <= 0;
      end else if (run_n) begin
        if (read_valid) read_owned <= 1;
        if (release_valid) ready_q[release_buffer] <= 0;
        if (request_transfer) owned <= 1;
        if (response_transfer) owned <= 0;
        if (abort_error && state != IDLE) begin
          canceled <= 1;
          failed <= 1;
          ready_q <= 0;
          // A displayed request and every accepted response must drain.
          if (state != SEND && state != WAIT_RSP) state <= DRAIN;
        end
        if ((!abort_error || state == SEND || state == WAIT_RSP) &&
            (!canceled || state == IDLE || state == SEND ||
             state == WAIT_RSP || state == DRAIN)) begin
          case (state)
            IDLE: if (start_valid && start_ready) begin
              prefix_q <= start_prefix;
              head_q <= start_head;
              slots_q <= start_slots;
              positions_q <= start_positions;
              ancestors_q <= start_ancestors;
              source_limit <= 17'(start_prefix + 4);
              source_index <= 0;
              fill_count <= 0;
              fill_address <= 0;
              column_q <= 0;
              ready_q <= 0;
              last_q <= 0;
              next_buffer <= 0;
              canceled <= 0;
              failed <= 0;
              finished <= 0;
              state <= PICK;
            end
            PICK: if (!ready_q[next_buffer] ||
                (release_valid && release_buffer == next_buffer)) begin
              fill_buffer <= next_buffer;
              fill_count <= 0;
              fill_address <= 0;
              column_q <= 0;
              state <= SCAN;
            end
            SCAN: begin
              if (source_index == source_limit) begin
                finished <= 1;
                if (fill_count != 0) state <= PUBLISH;
                else state <= FINISH;
              end else if (next_slots == 0) source_index <= source_index + 1'b1;
              else begin
                source_slots <= next_slots;
                position_q <= next_position;
                node_q <= next_node;
                provisional_q <= next_provisional;
                column_q <= 0;
                state <= SEND;
              end
            end
            SEND, WAIT_RSP: begin
              if (request_transfer && !response_transfer) state <= WAIT_RSP;
              if (response_transfer) begin
                if (kv_rsp_error || canceled || abort_error) begin
                  failed <= 1;
                  canceled <= 1;
                  ready_q <= 0;
                  state <= DRAIN;
                end else begin
                  fill_address <= fill_address + 1'b1;
                  if (column_q + 1'b1 == HEAD_DIM) begin
                    source_index <= source_index + 1'b1;
                    fill_count <= fill_count + 1'b1;
                    column_q <= 0;
                    if (fill_count + 1'b1 == TILE_TOKENS) state <= PUBLISH;
                    else state <= SCAN;
                  end else begin
                    column_q <= column_q + 1'b1;
                    state <= SEND;
                  end
                end
              end
            end
            PUBLISH: begin
              ready_q[fill_buffer] <= 1;
              last_q[fill_buffer] <= finished;
              if (fill_buffer) count1 <= fill_count;
              else count0 <= fill_count;
              next_buffer <= !fill_buffer;
              if (finished) state <= FINISH;
              else state <= PICK;
            end
            FINISH: if (ready_q == 0 ||
                (release_valid && ready_q == (release_buffer ? 2'b10 : 2'b01)))
              state <= IDLE;
            DRAIN: if (!owned || response_transfer) begin
              ready_q <= 0;
              finished <= 1;
              state <= IDLE;
            end
            default: begin
              failed <= 1;
              canceled <= 1;
              state <= DRAIN;
            end
          endcase
        end else if (state == DRAIN && (!owned || response_transfer)) begin
          ready_q <= 0;
          finished <= 1;
          state <= IDLE;
        end
      end
    end
  end endgenerate
endmodule
