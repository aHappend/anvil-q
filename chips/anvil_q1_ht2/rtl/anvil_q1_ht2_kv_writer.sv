module anvil_q1_ht2_kv_writer #(
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
  input wire dma_error
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam LEGAL = NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
    MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768;
  localparam C = LEGAL ? NUM_KV_HEADS*HEAD_DIM : 8;
  localparam S = LEGAL ? MAX_SEQ_LEN : 1;
  localparam BEATS = (2*C+63) >> 6;
  localparam STRIDE = BEATS << 6;
  localparam LENGTH = S*STRIDE;
  localparam IDLE = 4'd0, ADDRESS = 4'd1, CHECK = 4'd2,
    INPUT_WORD = 4'd3, PAD_WORD = 4'd4, STORE_BEAT = 4'd5,
    READ_BEAT = 4'd6, SEND_BEAT = 4'd7, WAIT_BEAT = 4'd8,
    ADVANCE = 4'd9, RESPONSE = 4'd10, DRAIN = 4'd11;
  wire run_n;
  reg [3:0] state;
  reg fp16, failed, command_bad, writing_value, dma_owned;
  reg [7:0] column;
  reg [4:0] word_index;
  reg [1:0] beat;
  reg [23:0] row_offset;
  reg [32:0] key_base, value_base;
  reg [33:0] key_address, value_address;
  reg [511:0] packed_key, packed_value, beat_q;
  (* ramstyle = "mlab", ram_style = "distributed", nomem2reg *)
  reg [1023:0] packed_beats [0:BEATS-1];
  wire [33:0] key_end = {1'b0, cmd_key_base} + {2'b0, cmd_key_length};
  wire [33:0] value_end = {1'b0, cmd_value_base} + {2'b0, cmd_value_length};
  wire input_bad = in_first != (column == 0) || in_last != (column+1 == C) ||
    fp32_nonfinite(expand16(in_key, fp16)) ||
    fp32_nonfinite(expand16(in_value, fp16));
  wire transfer = dma_valid && dma_ready;
  wire response = dma_rsp_valid && dma_rsp_ready;
  wire [33:0] current_address = (writing_value ? value_address : key_address) +
    {26'b0, beat, 6'b0};
  reg [1023:0] storage_q;

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native committed KV writer geometry");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  assign cmd_ready = run_n && state == IDLE && !abort_error;
  assign in_ready = run_n && state == INPUT_WORD && !abort_error;
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_error = rsp_valid && failed;
  assign dma_valid = run_n && state == SEND_BEAT && !abort_error;
  assign dma_address = dma_valid ? current_address[32:0] : 33'b0;
  assign dma_data = dma_valid ? beat_q : 512'b0;
  assign dma_byteenable = dma_valid ? 64'hffffffffffffffff : 64'b0;
  assign dma_rsp_ready = run_n &&
    (state == WAIT_BEAT || state == DRAIN || transfer);
  always @(posedge clk) begin
    if (run_n) begin
      if (state == STORE_BEAT) packed_beats[beat] <= {packed_value, packed_key};
      if (state == READ_BEAT) storage_q <= packed_beats[beat];
    end
  end
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      fp16 <= 0;
      failed <= 0;
      command_bad <= 0;
      writing_value <= 0;
      dma_owned <= 0;
      column <= 0;
      word_index <= 0;
      beat <= 0;
      row_offset <= 0;
      key_base <= 0;
      value_base <= 0;
      key_address <= 0;
      value_address <= 0;
      packed_key <= 0;
      packed_value <= 0;
      beat_q <= 0;
    end else begin
      if (transfer) dma_owned <= 1;
      if (response) dma_owned <= 0;
      if (abort_error && state != IDLE && state != RESPONSE && state != DRAIN) begin
        failed <= 1;
        state <= DRAIN;
      end else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          fp16 <= cmd_fp16;
          key_base <= cmd_key_base;
          value_base <= cmd_value_base;
          row_offset <= 24'(cmd_position*STRIDE);
          failed <= 0;
          command_bad <= !LEGAL || cmd_prefix_length > S ||
            cmd_position < cmd_prefix_length || cmd_position >= S ||
            cmd_key_length != LENGTH || cmd_value_length != LENGTH ||
            (|cmd_key_base[5:0]) || (|cmd_value_base[5:0]) ||
            key_end > 34'h200000000 || value_end > 34'h200000000;
          column <= 0;
          word_index <= 0;
          beat <= 0;
          writing_value <= 0;
          packed_key <= 0;
          packed_value <= 0;
          state <= ADDRESS;
        end
        ADDRESS: begin
          key_address <= {1'b0, key_base}+{10'b0, row_offset};
          value_address <= {1'b0, value_base}+{10'b0, row_offset};
          state <= CHECK;
        end
        CHECK: begin
          if (command_bad || key_address+STRIDE > 34'h200000000 ||
              value_address+STRIDE > 34'h200000000) begin
            failed <= 1;
            state <= RESPONSE;
          end else state <= INPUT_WORD;
        end
        INPUT_WORD: if (in_valid && in_ready) begin
          if (input_bad) begin failed <= 1; state <= RESPONSE; end
          else begin
            packed_key[16*word_index+:16] <= in_key;
            packed_value[16*word_index+:16] <= in_value;
            column <= column + 1'b1;
            if (word_index == 31) state <= STORE_BEAT;
            else begin
              word_index <= word_index + 1'b1;
              if (column+1 == C) state <= PAD_WORD;
            end
          end
        end
        PAD_WORD: begin
          packed_key[16*word_index+:16] <= 0;
          packed_value[16*word_index+:16] <= 0;
          if (word_index == 31) state <= STORE_BEAT;
          else word_index <= word_index + 1'b1;
        end
        STORE_BEAT: begin
          if (column == C) begin beat <= 0; state <= READ_BEAT; end
          else begin
            beat <= beat + 1'b1;
            word_index <= 0;
            packed_key <= 0;
            packed_value <= 0;
            state <= INPUT_WORD;
          end
        end
        READ_BEAT: state <= ADVANCE;
        ADVANCE: begin
          beat_q <= writing_value ? storage_q[1023:512] : storage_q[511:0];
          state <= SEND_BEAT;
        end
        SEND_BEAT: if (transfer) begin
          if (response) begin
            if (dma_error) begin failed <= 1; state <= RESPONSE; end
            else if (!writing_value) begin writing_value <= 1; state <= READ_BEAT; end
            else if (beat+1 == BEATS) state <= RESPONSE;
            else begin
              writing_value <= 0;
              beat <= beat + 1'b1;
              state <= READ_BEAT;
            end
          end else state <= WAIT_BEAT;
        end
        WAIT_BEAT: if (response) begin
          if (dma_error) begin failed <= 1; state <= RESPONSE; end
          else if (!writing_value) begin writing_value <= 1; state <= READ_BEAT; end
          else if (beat+1 == BEATS) state <= RESPONSE;
          else begin
            writing_value <= 0;
            beat <= beat + 1'b1;
            state <= READ_BEAT;
          end
        end
        DRAIN: if (!dma_owned || response) state <= RESPONSE;
        RESPONSE: if (rsp_valid && rsp_ready) state <= IDLE;
        default: begin failed <= 1; state <= DRAIN; end
      endcase
    end
  end
endmodule
