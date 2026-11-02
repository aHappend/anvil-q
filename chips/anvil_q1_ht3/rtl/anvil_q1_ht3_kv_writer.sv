module anvil_q1_ht3_kv_writer #(
  parameter NUM_KV_HEADS = 2, HEAD_DIM = 64, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n, abort_error,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire cmd_fp16,
  input wire [31:0] cmd_prefix_length, cmd_position,
  input wire [32:0] cmd_key_base, cmd_value_base,
  input wire [31:0] cmd_key_length, cmd_value_length,
  input wire in_valid,
  output wire in_ready,
  input wire [15:0] in_key, in_value,
  input wire in_first, in_last,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire rsp_error,
  output wire dma_valid,
  input wire dma_ready,
  output wire [32:0] dma_address,
  output wire [511:0] dma_data,
  output wire [63:0] dma_byteenable,
  input wire dma_rsp_valid,
  output wire dma_rsp_ready,
  input wire dma_error,
  input wire [1:0] cmd_kv_format
);
  import anvil_q1_ht3_fp_pkg::*;
  localparam LEGAL = NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
    MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768;
  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 committed KV writer geometry");
  end
  generate if (!LEGAL) begin: g_invalid
    assign cmd_ready = 0;
    assign in_ready = 0;
    assign rsp_valid = 0;
    assign rsp_error = 0;
    assign dma_valid = 0;
    assign dma_address = 0;
    assign dma_data = 0;
    assign dma_byteenable = 0;
    assign dma_rsp_ready = 0;
  end else begin: g_legal
    localparam C = NUM_KV_HEADS*HEAD_DIM;
    localparam NATIVE_BEATS = (16*C+511) >> 9;
    localparam INT4_BEATS = (4*C+511) >> 9;
    localparam INT8_BEATS = (8*C+511) >> 9;
    localparam RECORD_BITS = NATIVE_BEATS*512;
    localparam IDLE = 4'd0, ADDRESS = 4'd1, CHECK = 4'd2,
      INPUT_WORD = 4'd3, PREPARE = 4'd4, SEND = 4'd5,
      WAIT_RSP = 4'd6, RESPONSE = 4'd7, OFFSET = 4'd8;
    wire run_n;
    reg [3:0] state;
    reg [1:0] format_q, beat_q;
    reg [2:0] beats_q;
    reg [8:0] stride_q;
    reg [7:0] column_q;
    reg [10:0] bit_offset;
    reg writing_value, canceled, failed, command_bad;
    reg [32:0] key_base_q, value_base_q;
    reg [33:0] key_address_q, value_address_q;
    reg [31:0] position_q;
    reg [31:0] row_offset;
    reg [32:0] address_q;
    reg [511:0] data_q;
    reg [RECORD_BITS-1:0] key_record, value_record;
    wire [2:0] requested_beats = cmd_kv_format == 2 ? 3'(INT4_BEATS) :
      cmd_kv_format == 3 ? 3'(INT8_BEATS) : 3'(NATIVE_BEATS);
    wire [31:0] requested_stride = {23'b0, requested_beats, 6'b0};
    wire [31:0] requested_length = MAX_SEQ_LEN*requested_stride;
    wire [33:0] key_end = {1'b0, cmd_key_base} + {2'b0, cmd_key_length};
    wire [33:0] value_end = {1'b0, cmd_value_base} + {2'b0, cmd_value_length};
    wire overlap = {1'b0, cmd_key_base} < value_end &&
      {1'b0, cmd_value_base} < key_end;
    wire input_bits_bad = format_q == 2 ? ((|in_key[15:4]) || (|in_value[15:4])) :
      format_q == 3 ? ((|in_key[15:8]) || (|in_value[15:8])) :
      (fp32_nonfinite(expand16(in_key, format_q == 1)) ||
       fp32_nonfinite(expand16(in_value, format_q == 1)));
    wire input_bad = input_bits_bad || in_first != (column_q == 0) ||
      in_last != (column_q + 1'b1 == C);
    wire request_transfer = dma_valid && dma_ready;
    wire response_transfer = dma_rsp_valid && dma_rsp_ready;
    wire final_beat = beat_q + 1'b1 == beats_q;
    wire [1:0] following_beat = final_beat ? 2'b0 : beat_q + 1'b1;
    wire following_value = writing_value || final_beat;
    wire [511:0] following_data = following_value ?
      value_record[512*following_beat+:512] : key_record[512*following_beat+:512];

    anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
    assign cmd_ready = run_n && state == IDLE && !abort_error;
    assign in_ready = run_n && state == INPUT_WORD && !abort_error;
    assign rsp_valid = run_n && state == RESPONSE;
    assign rsp_error = rsp_valid && failed;
    assign dma_valid = run_n && state == SEND;
    assign dma_address = dma_valid ? address_q : 33'b0;
    assign dma_data = dma_valid ? data_q : 512'b0;
    assign dma_byteenable = dma_valid ? 64'hffffffffffffffff : 64'b0;
    assign dma_rsp_ready = run_n &&
      (state == WAIT_RSP || (state == SEND && dma_ready));

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        format_q <= 0;
        beat_q <= 0;
        beats_q <= 0;
        stride_q <= 0;
        column_q <= 0;
        bit_offset <= 0;
        writing_value <= 0;
        canceled <= 0;
        failed <= 0;
        command_bad <= 0;
        key_base_q <= 0;
        value_base_q <= 0;
        key_address_q <= 0;
        value_address_q <= 0;
        position_q <= 0;
        row_offset <= 0;
        address_q <= 0;
        data_q <= 0;
        key_record <= 0;
        value_record <= 0;
      end else if (run_n) begin
        if (abort_error && state != IDLE && state != RESPONSE) begin
          canceled <= 1;
          failed <= 1;
          if (state != SEND && state != WAIT_RSP) state <= RESPONSE;
        end
        if (!abort_error || state == SEND || state == WAIT_RSP || state == RESPONSE) begin
          case (state)
            IDLE: if (cmd_valid && cmd_ready) begin
              format_q <= cmd_kv_format;
              beats_q <= requested_beats;
              stride_q <= requested_stride[8:0];
              key_base_q <= cmd_key_base;
              value_base_q <= cmd_value_base;
              position_q <= cmd_position;
              key_record <= 0;
              value_record <= 0;
              column_q <= 0;
              bit_offset <= 0;
              beat_q <= 0;
              writing_value <= 0;
              canceled <= 0;
              failed <= 0;
              command_bad <= cmd_prefix_length > MAX_SEQ_LEN ||
                cmd_position < cmd_prefix_length || cmd_position >= MAX_SEQ_LEN ||
                cmd_key_length != requested_length || cmd_value_length != requested_length ||
                (|cmd_key_base[5:0]) || (|cmd_value_base[5:0]) || overlap ||
                key_end > 34'h200000000 || value_end > 34'h200000000;
              state <= OFFSET;
            end
            OFFSET: begin row_offset <= position_q*stride_q; state <= ADDRESS; end
            ADDRESS: begin
              key_address_q <= {1'b0, key_base_q} + {2'b0, row_offset};
              value_address_q <= {1'b0, value_base_q} + {2'b0, row_offset};
              state <= CHECK;
            end
            CHECK: begin
              if (command_bad || key_address_q + stride_q > 34'h200000000 ||
                  value_address_q + stride_q > 34'h200000000) begin
                failed <= 1;
                state <= RESPONSE;
              end else state <= INPUT_WORD;
            end
            INPUT_WORD: if (in_valid && in_ready) begin
              if (input_bad) begin failed <= 1; state <= RESPONSE; end
              else begin
                case (format_q)
                  2: begin
                    key_record[bit_offset+:4] <= in_key[3:0];
                    value_record[bit_offset+:4] <= in_value[3:0];
                    bit_offset <= bit_offset + 4;
                  end
                  3: begin
                    key_record[bit_offset+:8] <= in_key[7:0];
                    value_record[bit_offset+:8] <= in_value[7:0];
                    bit_offset <= bit_offset + 8;
                  end
                  default: begin
                    key_record[bit_offset+:16] <= in_key;
                    value_record[bit_offset+:16] <= in_value;
                    bit_offset <= bit_offset + 16;
                  end
                endcase
                if (column_q + 1'b1 == C) state <= PREPARE;
                else column_q <= column_q + 1'b1;
              end
            end
            PREPARE: begin
              address_q <= key_address_q[32:0];
              data_q <= key_record[511:0];
              state <= SEND;
            end
            SEND, WAIT_RSP: begin
              if (request_transfer && !response_transfer) state <= WAIT_RSP;
              if (response_transfer) begin
                if (dma_error || canceled || abort_error) begin
                  failed <= 1;
                  state <= RESPONSE;
                end else if (writing_value && final_beat) state <= RESPONSE;
                else begin
                  beat_q <= following_beat;
                  writing_value <= following_value;
                  data_q <= following_data;
                  if (final_beat) address_q <= value_address_q[32:0];
                  else address_q <= address_q + 33'd64;
                  state <= SEND;
                end
              end
            end
            RESPONSE: if (rsp_ready) state <= IDLE;
            default: begin failed <= 1; state <= RESPONSE; end
          endcase
        end
      end
    end
  end endgenerate
endmodule
