module anvil_q1_ht2_kv_reader #(
  parameter NUM_KV_HEADS = 2, HEAD_DIM = 64, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n, abort_error, invalidate_cache,
  input wire req_valid,
  output wire req_ready,
  input wire req_fp16,
  input wire [31:0] req_prefix_length, req_position, req_head, req_column,
  input wire [32:0] req_key_base, req_value_base,
  input wire [31:0] req_key_length, req_value_length,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [15:0] rsp_key, rsp_value,
  output wire rsp_error,
  output wire dma_valid,
  input wire dma_ready,
  output wire [32:0] dma_address,
  output wire [7:0] dma_burstcount,
  input wire dma_data_valid,
  output wire dma_data_ready,
  input wire [511:0] dma_data,
  input wire dma_error
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam LEGAL = NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
    MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768;
  localparam K = LEGAL ? NUM_KV_HEADS : 1;
  localparam D = LEGAL ? HEAD_DIM : 8;
  localparam S = LEGAL ? MAX_SEQ_LEN : 1;
  localparam STRIDE = ((2*K*D+63) >> 6) << 6;
  localparam LENGTH = S*STRIDE;
  localparam IDLE = 4'd0, ADDRESS = 4'd1, CHECK = 4'd2,
    CACHE_LOOKUP = 4'd3, KEY_SEND = 4'd4, KEY_WAIT = 4'd5,
    VALUE_SEND = 4'd6, VALUE_WAIT = 4'd7, SELECT_WORD = 4'd8,
    RESPONSE = 4'd9, DRAIN = 4'd10;
  wire run_n;
  reg [3:0] state;
  reg fp16, failed, command_bad, cache_valid, reader_owned;
  reg [14:0] position;
  reg [6:0] logical_column;
  reg [23:0] row_offset;
  reg [32:0] key_base, value_base;
  reg [33:0] key_address, value_address;
  reg [32:0] cached_key_address, cached_value_address;
  reg [511:0] cached_key, cached_value;
  reg [15:0] result_key, result_value;
  wire [33:0] key_end = {1'b0, req_key_base} + {2'b0, req_key_length};
  wire [33:0] value_end = {1'b0, req_value_base} + {2'b0, req_value_length};
  wire reader_ready, reader_valid, reader_error;
  wire [1023:0] reader_data;
  wire reader_send = run_n && !abort_error &&
    (state == KEY_SEND || state == VALUE_SEND);
  wire reader_consume = run_n &&
    (state == KEY_WAIT || state == VALUE_WAIT || state == DRAIN);
  wire [32:0] reader_address = state == KEY_SEND ? key_address[32:0] : value_address[32:0];
  wire [15:0] selected_key = cached_key[16*logical_column[4:0]+:16];
  wire [15:0] selected_value = cached_value[16*logical_column[4:0]+:16];
  wire selected_bad = fp32_nonfinite(expand16(selected_key, fp16)) ||
    fp32_nonfinite(expand16(selected_value, fp16));

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native committed KV reader geometry");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  anvil_q1_ht2_burst_reader u_reader (
    .clk(clk), .rst_n(run_n), .cmd_valid(reader_send), .cmd_ready(reader_ready),
    .cmd_address(reader_address), .cmd_burstcount(8'd1),
    .mem_valid(dma_valid), .mem_ready(dma_ready), .mem_address(dma_address),
    .mem_burstcount(dma_burstcount), .mem_data_valid(dma_data_valid),
    .mem_data_ready(dma_data_ready), .mem_data(dma_data), .mem_error(dma_error),
    .rsp_valid(reader_valid), .rsp_ready(reader_consume),
    .rsp_data(reader_data), .rsp_error(reader_error)
  );
  assign req_ready = run_n && state == IDLE && !abort_error && !invalidate_cache;
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_key = rsp_valid && !failed ? result_key : 16'b0;
  assign rsp_value = rsp_valid && !failed ? result_value : 16'b0;
  assign rsp_error = rsp_valid && failed;
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      fp16 <= 0;
      failed <= 0;
      command_bad <= 0;
      cache_valid <= 0;
      reader_owned <= 0;
      position <= 0;
      logical_column <= 0;
      row_offset <= 0;
      key_base <= 0;
      value_base <= 0;
      key_address <= 0;
      value_address <= 0;
      cached_key_address <= 0;
      cached_value_address <= 0;
      cached_key <= 0;
      cached_value <= 0;
      result_key <= 0;
      result_value <= 0;
    end else begin
      if (reader_send && reader_ready) reader_owned <= 1;
      if (reader_valid && reader_consume) reader_owned <= 0;
      if (invalidate_cache || abort_error) cache_valid <= 0;
      if (abort_error && state != IDLE && state != RESPONSE && state != DRAIN) begin
        failed <= 1;
        state <= DRAIN;
      end else case (state)
        IDLE: if (req_valid && req_ready) begin
          fp16 <= req_fp16;
          position <= req_position[14:0];
          logical_column <= 7'(req_head*D+req_column);
          key_base <= req_key_base;
          value_base <= req_value_base;
          failed <= 0;
          command_bad <= !LEGAL || req_prefix_length > S ||
            req_position >= req_prefix_length || req_position >= S ||
            req_head >= K || req_column >= D ||
            req_key_length != LENGTH || req_value_length != LENGTH ||
            (|req_key_base[5:0]) || (|req_value_base[5:0]) ||
            key_end > 34'h200000000 || value_end > 34'h200000000;
          row_offset <= 24'(req_position * STRIDE);
          state <= ADDRESS;
        end
        ADDRESS: begin
          key_address <= {1'b0, key_base} + {10'b0, row_offset} +
            {26'b0, logical_column[6:5], 6'b0};
          value_address <= {1'b0, value_base} + {10'b0, row_offset} +
            {26'b0, logical_column[6:5], 6'b0};
          state <= CHECK;
        end
        CHECK: begin
          if (command_bad || key_address+34'd64 > 34'h200000000 ||
              value_address+34'd64 > 34'h200000000) begin
            failed <= 1;
            state <= RESPONSE;
          end else state <= CACHE_LOOKUP;
        end
        CACHE_LOOKUP: begin
          if (cache_valid && !invalidate_cache &&
              cached_key_address == key_address[32:0] &&
              cached_value_address == value_address[32:0]) state <= SELECT_WORD;
          else begin cache_valid <= 0; state <= KEY_SEND; end
        end
        KEY_SEND: if (reader_send && reader_ready) state <= KEY_WAIT;
        KEY_WAIT: if (reader_valid && reader_consume) begin
          if (reader_error) begin failed <= 1; state <= RESPONSE; end
          else begin cached_key <= reader_data[511:0]; state <= VALUE_SEND; end
        end
        VALUE_SEND: if (reader_send && reader_ready) state <= VALUE_WAIT;
        VALUE_WAIT: if (reader_valid && reader_consume) begin
          if (reader_error) begin failed <= 1; state <= RESPONSE; end
          else begin
            cached_value <= reader_data[511:0];
            cached_key_address <= key_address[32:0];
            cached_value_address <= value_address[32:0];
            cache_valid <= !invalidate_cache;
            state <= SELECT_WORD;
          end
        end
        SELECT_WORD: begin
          if (selected_bad) begin failed <= 1; cache_valid <= 0; end
          else begin result_key <= selected_key; result_value <= selected_value; end
          state <= RESPONSE;
        end
        DRAIN: if (!reader_owned || (reader_valid && reader_consume)) state <= RESPONSE;
        RESPONSE: if (rsp_valid && rsp_ready) state <= IDLE;
        default: begin failed <= 1; cache_valid <= 0; state <= DRAIN; end
      endcase
    end
  end
endmodule
