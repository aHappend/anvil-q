module anvil_q1_ht_kv_window #(
  parameter NUM_LAYERS = 24,
  parameter NUM_KV_HEADS = 2,
  parameter HEAD_DIM = 64,
  parameter MAX_SEQ_LEN = 32768,
  parameter KV_WINDOW = 128
) (
  input wire clk,
  input wire rst_n,
  input wire new_sequence,
  output wire initialized,
  input wire req_valid,
  output wire req_ready,
  input wire req_write,
  input wire req_value,
  input wire [31:0] req_layer,
  input wire [31:0] req_head,
  input wire [31:0] req_pos,
  input wire [31:0] req_dim,
  input wire signed [31:0] req_wdata,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire signed [31:0] rsp_data,
  output wire rsp_error,
  output wire rsp_hit,
  output wire protocol_error,
  output wire spill_valid,
  input wire spill_ready,
  output wire spill_write,
  output wire spill_value,
  output wire [31:0] spill_layer,
  output wire [31:0] spill_pos,
  output wire [31:0] spill_col,
  output wire signed [31:0] spill_wdata,
  input wire spill_rsp_valid,
  output wire spill_rsp_ready,
  input wire signed [31:0] spill_rsp_data,
  input wire spill_rsp_error
);
  localparam LEGAL = NUM_LAYERS >= 1 && NUM_LAYERS <= 24 &&
                     NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 &&
                     HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
                     ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
                     MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768 &&
                     KV_WINDOW >= 1 && KV_WINDOW <= 128 && KV_WINDOW <= MAX_SEQ_LEN;
  generate if (LEGAL) begin : g_legal
    localparam KV_WIDTH = NUM_KV_HEADS*HEAD_DIM;
    localparam ENTRIES = NUM_LAYERS*KV_WINDOW;
    localparam WORDS = ENTRIES*KV_WIDTH;
    localparam SLOT_BITS = KV_WINDOW > 1 ? $clog2(KV_WINDOW) : 1;
    localparam ENTRY_BITS = ENTRIES > 1 ? $clog2(ENTRIES) : 1;
    localparam WORD_BITS = WORDS > 1 ? $clog2(WORDS) : 1;
    localparam IDLE = 4'd0, INITIALIZE = 4'd1, LOOKUP = 4'd2,
               HIT_CHECK = 4'd3, EVICT_READ = 4'd4, EVICT_LATCH = 4'd5,
               EVICT_ISSUE = 4'd6, EVICT_WAIT = 4'd7, INSTALL = 4'd8,
               MISS_ISSUE = 4'd9, MISS_WAIT = 4'd10, RESULT = 4'd11;
    (* ramstyle = "M20K", ram_style = "block" *) reg [31:0] key_mem [0:WORDS-1];
    (* ramstyle = "M20K", ram_style = "block" *) reg [31:0] value_mem [0:WORDS-1];
    (* ramstyle = "M20K", ram_style = "block" *) reg [31:0] tags [0:ENTRIES-1];
    (* ramstyle = "M20K", ram_style = "block" *)
      reg [2*KV_WIDTH-1:0] valid_words [0:ENTRIES-1];
    reg [31:0] history_next [0:NUM_LAYERS-1];
    reg [3:0] state;
    reg init_done, failed, result_error, result_hit;
    reg [31:0] result_data;
    reg [ENTRY_BITS-1:0] clear_entry, entry_address;
    reg [WORD_BITS-1:0] data_address;
    reg [SLOT_BITS-1:0] slot;
    reg wr, value_select, invalid_request;
    reg [31:0] layer, position, column, write_data;
    reg [31:0] tag_data, key_data, value_data;
    reg [2*KV_WIDTH-1:0] mask_data;
    reg [31:0] evict_position, evict_column, evict_data, evict_base;
    reg evict_value;
    wire [31:0] flat_column = req_head*HEAD_DIM + req_dim;
    wire [31:0] lookup_entry = layer*KV_WINDOW + {{(32-SLOT_BITS){1'b0}}, slot};
    wire [31:0] lookup_word = lookup_entry*KV_WIDTH + column;
    wire [2*KV_WIDTH-1:0] selected_bit =
      {{(2*KV_WIDTH-1){1'b0}}, 1'b1} << (column + (value_select ? KV_WIDTH : 0));
    wire [2*KV_WIDTH-1:0] new_mask =
      (tag_data == position ? mask_data : {2*KV_WIDTH{1'b0}}) | selected_bit;
    wire selected_valid = |(mask_data & selected_bit);
    wire spill_response = spill_rsp_valid && spill_rsp_ready;
    wire spill_accept = spill_valid && spill_ready;
    integer h;

    function automatic [SLOT_BITS-1:0] calc_slot(input [31:0] pos);
      reg [15:0] rem;
      integer b;
      begin
        rem = 16'd0;
        for (b = 15; b >= 0; b = b - 1) begin
          rem = {rem[14:0], pos[b]};
          if (rem >= KV_WINDOW[15:0]) rem = rem - KV_WINDOW[15:0];
        end
        calc_slot = rem[SLOT_BITS-1:0];
      end
    endfunction

    assign initialized = rst_n && init_done;
    assign req_ready = rst_n && init_done && !new_sequence && !failed && state == IDLE;
    assign rsp_valid = rst_n && state == RESULT;
    assign rsp_data = rsp_valid && !result_error ? $signed(result_data) : 32'sd0;
    assign rsp_error = rsp_valid && result_error;
    assign rsp_hit = rsp_valid && !result_error && result_hit;
    assign protocol_error = rst_n && failed;
    assign spill_valid = rst_n && (state == EVICT_ISSUE || state == MISS_ISSUE);
    assign spill_write = spill_valid && state == EVICT_ISSUE;
    assign spill_value = spill_valid ? (state == EVICT_ISSUE ? evict_value : value_select) : 1'b0;
    assign spill_layer = spill_valid ? layer : 32'b0;
    assign spill_pos = spill_valid ? (state == EVICT_ISSUE ? evict_position : position) : 32'b0;
    assign spill_col = spill_valid ? (state == EVICT_ISSUE ? evict_column : column) : 32'b0;
    assign spill_wdata = spill_write ? $signed(evict_data) : 32'sd0;
    assign spill_rsp_ready = rst_n && (state == EVICT_WAIT || state == MISS_WAIT ||
                                      (spill_valid && spill_ready));

    always @(posedge clk) begin
      if (rst_n) begin
        if (state == LOOKUP && !invalid_request) begin
          tag_data <= tags[lookup_entry];
          mask_data <= valid_words[lookup_entry];
          key_data <= key_mem[lookup_word];
          value_data <= value_mem[lookup_word];
        end
        if (state == EVICT_READ) begin
          key_data <= key_mem[evict_base + evict_column];
          value_data <= value_mem[evict_base + evict_column];
        end
        if (state == INITIALIZE) begin
          valid_words[clear_entry] <= 0;
          tags[clear_entry] <= 0;
        end else if (state == INSTALL) begin
          tags[entry_address] <= position;
          valid_words[entry_address] <= new_mask;
          if (value_select) value_mem[data_address] <= write_data;
          else key_mem[data_address] <= write_data;
        end
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= INITIALIZE;
        init_done <= 0;
        failed <= 0;
        result_error <= 0;
        result_hit <= 0;
        result_data <= 0;
        clear_entry <= 0;
        entry_address <= 0;
        data_address <= 0;
        slot <= 0;
        wr <= 0;
        value_select <= 0;
        invalid_request <= 0;
        layer <= 0;
        position <= 0;
        column <= 0;
        write_data <= 0;
        evict_position <= 0;
        evict_column <= 0;
        evict_data <= 0;
        evict_base <= 0;
        evict_value <= 0;
        for (h = 0; h < NUM_LAYERS; h = h + 1) history_next[h] <= 0;
      end else if (new_sequence && state == IDLE) begin
        init_done <= 0;
        failed <= 0;
        clear_entry <= 0;
        for (h = 0; h < NUM_LAYERS; h = h + 1) history_next[h] <= 0;
        state <= INITIALIZE;
      end else case (state)
        INITIALIZE: begin
          if (clear_entry == ENTRIES-1) begin
            init_done <= 1;
            state <= IDLE;
          end else clear_entry <= clear_entry + 1'b1;
        end
        IDLE: if (req_valid && req_ready) begin
          wr <= req_write;
          value_select <= req_value;
          layer <= req_layer;
          position <= req_pos;
          column <= flat_column;
          write_data <= req_wdata;
          invalid_request <= req_layer >= NUM_LAYERS || req_head >= NUM_KV_HEADS ||
                             req_dim >= HEAD_DIM || req_pos >= MAX_SEQ_LEN;
          if (req_pos < MAX_SEQ_LEN) slot <= calc_slot(req_pos);
          else slot <= 0;
          result_data <= 0;
          result_error <= 0;
          result_hit <= 0;
          state <= LOOKUP;
        end
        LOOKUP: begin
          entry_address <= ENTRY_BITS'(lookup_entry);
          data_address <= WORD_BITS'(lookup_word);
          state <= HIT_CHECK;
        end
        HIT_CHECK: begin
          if (invalid_request || (wr && position != history_next[layer]) ||
              (!wr && position > history_next[layer])) begin
            result_error <= 1;
            failed <= 1;
            state <= RESULT;
          end else if (!wr) begin
            if (mask_data != 0 && tag_data == position && selected_valid) begin
              result_data <= value_select ? value_data : key_data;
              result_hit <= 1;
              state <= RESULT;
            end else if (position < history_next[layer]) state <= MISS_ISSUE;
            else begin
              result_error <= 1;
              failed <= 1;
              state <= RESULT;
            end
          end else if (mask_data != 0 && tag_data != position) begin
            if (!(&mask_data)) begin
              result_error <= 1;
              failed <= 1;
              state <= RESULT;
            end else begin
              evict_position <= tag_data;
              evict_column <= 0;
              evict_value <= 0;
              evict_base <= lookup_entry*KV_WIDTH;
              state <= EVICT_READ;
            end
          end else state <= INSTALL;
        end
        EVICT_READ: state <= EVICT_LATCH;
        EVICT_LATCH: begin
          evict_data <= evict_value ? value_data : key_data;
          state <= EVICT_ISSUE;
        end
        EVICT_ISSUE, EVICT_WAIT: begin
          if (spill_response) begin
            if (spill_rsp_error) begin
              result_error <= 1;
              failed <= 1;
              state <= RESULT;
            end else if (evict_column + 1 < KV_WIDTH) begin
              evict_column <= evict_column + 32'd1;
              state <= EVICT_READ;
            end else if (!evict_value) begin
              evict_value <= 1;
              evict_column <= 0;
              state <= EVICT_READ;
            end else state <= INSTALL;
          end else if (spill_accept) state <= EVICT_WAIT;
        end
        INSTALL: begin
          if (&new_mask) history_next[layer] <= position + 32'd1;
          result_hit <= mask_data != 0 && tag_data == position;
          state <= RESULT;
        end
        MISS_ISSUE, MISS_WAIT: begin
          if (spill_response) begin
            if (spill_rsp_error) begin
              result_error <= 1;
              failed <= 1;
            end else result_data <= spill_rsp_data;
            state <= RESULT;
          end else if (spill_accept) state <= MISS_WAIT;
        end
        RESULT: if (rsp_ready) state <= IDLE;
        default: begin
          result_error <= 1;
          failed <= 1;
          state <= RESULT;
        end
      endcase
    end
  end else begin : g_illegal
    initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: KV dimensions or window");
    assign initialized = 0;
    assign req_ready = 0;
    assign rsp_valid = 0;
    assign rsp_data = 0;
    assign rsp_error = 0;
    assign rsp_hit = 0;
    assign protocol_error = 0;
    assign spill_valid = 0;
    assign spill_write = 0;
    assign spill_value = 0;
    assign spill_layer = 0;
    assign spill_pos = 0;
    assign spill_col = 0;
    assign spill_wdata = 0;
    assign spill_rsp_ready = 0;
  end endgenerate
endmodule
