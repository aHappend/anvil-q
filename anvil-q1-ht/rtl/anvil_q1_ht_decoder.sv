module anvil_q1_ht_decoder #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2, HEAD_DIM = 64,
  parameter GROUP_SIZE = 128, VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768,
  parameter COMPATIBILITY = 0
) (
  input wire clk, rst_n, engine_enable, storage_bf16, execution_fault,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire done, error, busy,
  output wire [63:0] token_cycles,
  output wire cache_new_sequence,
  input wire cache_initialized,

  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error,

  output wire block_valid,
  input wire block_ready,
  output wire [3:0] block_kind,
  output wire [31:0] block_layer,
  output wire [2:0] block_proj,
  output wire [31:0] block_offset, block_bytes,
  output wire [7:0] block_packet_bytes,
  input wire packet_valid,
  output wire packet_ready,
  input wire [1023:0] packet_data,
  input wire packet_last,
  input wire block_done, block_error,

  output wire tensor_in_valid,
  input wire tensor_in_ready,
  output wire tensor_in_first, tensor_in_last,
  output wire signed [31:0] tensor_in_activation,
  output wire [2367:0] tensor_in_weight_q16,
  output wire [63:0] tensor_in_mask,
  input wire tensor_out_valid,
  output wire tensor_out_ready,
  input wire [2047:0] tensor_out_data,
  input wire [63:0] tensor_out_mask,
  input wire tensor_protocol_error
);
  import anvil_q1_ht_numeric_pkg::*;
  localparam IDLE = 4'd0, INVALID = 4'd1, COMPLETE = 4'd2,
    CLEAR = 4'd3, CLEAR_WAIT = 4'd4,
    EMBEDDING_READ = 4'd5, EMBEDDING_RESPONSE = 4'd6,
    EMBEDDING_WRITE = 4'd7, EMBEDDING_ACK = 4'd8,
    DISPATCH = 4'd9, KERNEL_SEND = 4'd10, KERNEL_WAIT = 4'd11,
    PROJECTION_SEND = 4'd12, PROJECTION_WAIT = 4'd13;
  reg [3:0] state, step;
  reg failed, sequence_valid, final_norm;
  // Command rejection has not started execution or modified sequence history.
  wire abort_execution = execution_fault || (failed && state != INVALID);
  reg [31:0] token, position, next_position, component, layer;
  reg [31:0] cycles_low, cycles_high;
  reg signed [31:0] embedding_value;
  reg [2:0] kernel_operation;
  reg [3:0] projection;
  wire kernel_ready, kernel_done, kernel_error;
  wire projection_ready, projection_done, projection_error;
  wire p_logit_valid;
  wire [31:0] p_logit_index;
  wire signed [31:0] p_logit_data;
  wire select_kernel = state == KERNEL_SEND || state == KERNEL_WAIT;
  wire select_projection = state == PROJECTION_SEND || state == PROJECTION_WAIT;
  wire [2:0] req_valid, req_ready, req_write, rsp_valid, rsp_ready;
  wire [11:0] req_kind;
  wire [95:0] req_layer, req_row, req_col, req_wdata;
  wire [8:0] req_proj;
  wire [1:0] selected = select_kernel ? 2'd1 : select_projection ? 2'd2 : 2'd0;
  wire own_response = rsp_valid[0] && rsp_ready[0];
  wire own_read = state == EMBEDDING_READ || state == EMBEDDING_RESPONSE;
  wire final_transfer = logit_valid && logit_ready && logit_index == VOCAB_SIZE-1;
  wire [31:0] kernel_layer = final_norm ? 32'd0 : layer;
  wire child_rst_n;
  anvil_q1_ht_reset_sync u_child_reset (
    clk, rst_n && !(state == COMPLETE && failed), child_rst_n
  );

  assign token_ready = rst_n && engine_enable && cache_initialized && state == IDLE;
  assign busy = rst_n && state != IDLE;
  assign done = rst_n && state == COMPLETE;
  assign error = done && failed;
  assign token_cycles = rst_n ? {cycles_high, cycles_low} : 64'b0;
  assign cache_new_sequence = rst_n && state == CLEAR;
  assign logit_valid = rst_n && state == PROJECTION_WAIT && projection == 7 &&
                       p_logit_valid && !abort_execution;
  assign logit_index = logit_valid ? p_logit_index : 32'b0;
  assign logit_data = logit_valid ? p_logit_data : 32'sd0;
  assign mem_req_valid = rst_n && req_valid[selected];
  assign mem_req_write = mem_req_valid && req_write[selected];
  assign mem_req_kind = mem_req_valid ? req_kind[4*selected+:4] : 4'b0;
  assign mem_req_layer = mem_req_valid ? req_layer[32*selected+:32] : 32'b0;
  assign mem_req_proj = mem_req_valid ? req_proj[3*selected+:3] : 3'b0;
  assign mem_req_row = mem_req_valid ? req_row[32*selected+:32] : 32'b0;
  assign mem_req_col = mem_req_valid ? req_col[32*selected+:32] : 32'b0;
  assign mem_req_wdata = mem_req_write ? req_wdata[32*selected+:32] : 32'b0;
  assign mem_rsp_ready = rst_n && rsp_ready[selected];
  assign req_ready = rst_n && mem_req_ready ? (3'b001 << selected) : 3'b0;
  assign rsp_valid = rst_n && mem_rsp_valid ? (3'b001 << selected) : 3'b0;
  assign req_valid[0] = rst_n && !abort_execution &&
    (state == EMBEDDING_READ || state == EMBEDDING_WRITE);
  assign req_write[0] = state == EMBEDDING_WRITE;
  assign req_kind[0+:4] = own_read ? 4'd0 : 4'd8;
  assign req_layer[0+:32] = 0;
  assign req_proj[0+:3] = 0;
  assign req_row[0+:32] = own_read ? token : 32'b0;
  assign req_col[0+:32] = component;
  assign req_wdata[0+:32] = embedding_value;
  assign rsp_ready[0] = rst_n && (state == EMBEDDING_RESPONSE || state == EMBEDDING_ACK ||
    ((state == EMBEDDING_READ || state == EMBEDDING_WRITE) && req_ready[0]));

  anvil_q1_ht_kernel #(
    .NUM_LAYERS(NUM_LAYERS), .HIDDEN_SIZE(HIDDEN_SIZE), .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS), .NUM_KV_HEADS(NUM_KV_HEADS), .HEAD_DIM(HEAD_DIM),
    .MAX_SEQ_LEN(MAX_SEQ_LEN), .LEGACY_PARAMETERS(COMPATIBILITY)
  ) u_kernel (
    .clk(clk), .rst_n(child_rst_n), .abort_error(abort_execution),
    .cmd_valid(state == KERNEL_SEND && !abort_execution), .cmd_ready(kernel_ready),
    .cmd_op(kernel_operation), .cmd_layer(kernel_layer), .cmd_pos(position),
    .done(kernel_done), .error(kernel_error),
    .mem_req_valid(req_valid[1]), .mem_req_ready(req_ready[1]), .mem_req_write(req_write[1]),
    .mem_req_kind(req_kind[4+:4]), .mem_req_layer(req_layer[32+:32]),
    .mem_req_proj(req_proj[3+:3]), .mem_req_row(req_row[32+:32]),
    .mem_req_col(req_col[32+:32]), .mem_req_wdata(req_wdata[32+:32]),
    .mem_rsp_valid(rsp_valid[1]), .mem_rsp_ready(rsp_ready[1]),
    .mem_rsp_rdata(mem_rsp_rdata), .mem_rsp_error(mem_rsp_error)
  );
  generate if (COMPATIBILITY) begin : g_compatibility
    anvil_q1_ht_compat_projection #(
      .NUM_LAYERS(NUM_LAYERS), .HIDDEN_SIZE(HIDDEN_SIZE), .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
      .NUM_KV_HEADS(NUM_KV_HEADS), .HEAD_DIM(HEAD_DIM), .GROUP_SIZE(GROUP_SIZE),
      .VOCAB_SIZE(VOCAB_SIZE), .MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) u_projection (
      .clk(clk), .rst_n(child_rst_n), .abort_error(abort_execution),
      .cmd_valid(state == PROJECTION_SEND && !abort_execution),
      .cmd_ready(projection_ready), .cmd_layer(layer), .cmd_pos(position),
      .cmd_proj(projection), .done(projection_done), .error(projection_error),
      .mem_req_valid(req_valid[2]), .mem_req_ready(req_ready[2]), .mem_req_write(req_write[2]),
      .mem_req_kind(req_kind[8+:4]), .mem_req_layer(req_layer[64+:32]),
      .mem_req_proj(req_proj[6+:3]), .mem_req_row(req_row[64+:32]),
      .mem_req_col(req_col[64+:32]), .mem_req_wdata(req_wdata[64+:32]),
      .mem_rsp_valid(rsp_valid[2]), .mem_rsp_ready(rsp_ready[2]),
      .mem_rsp_rdata(mem_rsp_rdata), .mem_rsp_error(mem_rsp_error),
      .logit_valid(p_logit_valid), .logit_ready(logit_ready && logit_valid),
      .logit_index(p_logit_index), .logit_data(p_logit_data)
    );
    assign block_valid = 0;
    assign block_kind = 0;
    assign block_layer = 0;
    assign block_proj = 0;
    assign block_offset = 0;
    assign block_bytes = 0;
    assign block_packet_bytes = 0;
    assign packet_ready = 0;
    assign tensor_in_valid = 0;
    assign tensor_in_first = 0;
    assign tensor_in_last = 0;
    assign tensor_in_activation = 0;
    assign tensor_in_weight_q16 = 0;
    assign tensor_in_mask = 0;
    assign tensor_out_ready = 0;
  end else begin : g_parallel
    anvil_q1_ht_projection #(
    .NUM_LAYERS(NUM_LAYERS), .HIDDEN_SIZE(HIDDEN_SIZE), .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_KV_HEADS(NUM_KV_HEADS), .HEAD_DIM(HEAD_DIM), .GROUP_SIZE(GROUP_SIZE),
    .VOCAB_SIZE(VOCAB_SIZE), .MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) u_projection (
    .clk(clk), .rst_n(child_rst_n), .abort_error(abort_execution),
    .cmd_valid(state == PROJECTION_SEND && !abort_execution),
    .cmd_ready(projection_ready), .cmd_layer(layer), .cmd_pos(position),
    .cmd_proj(projection), .storage_bf16(storage_bf16),
    .done(projection_done), .error(projection_error),
    .mem_req_valid(req_valid[2]), .mem_req_ready(req_ready[2]), .mem_req_write(req_write[2]),
    .mem_req_kind(req_kind[8+:4]), .mem_req_layer(req_layer[64+:32]),
    .mem_req_proj(req_proj[6+:3]), .mem_req_row(req_row[64+:32]),
    .mem_req_col(req_col[64+:32]), .mem_req_wdata(req_wdata[64+:32]),
    .mem_rsp_valid(rsp_valid[2]), .mem_rsp_ready(rsp_ready[2]),
    .mem_rsp_rdata(mem_rsp_rdata), .mem_rsp_error(mem_rsp_error),
    .block_valid(block_valid), .block_ready(block_ready), .block_kind(block_kind),
    .block_layer(block_layer), .block_proj(block_proj), .block_offset(block_offset),
    .block_bytes(block_bytes), .block_packet_bytes(block_packet_bytes),
    .packet_valid(packet_valid), .packet_ready(packet_ready), .packet_data(packet_data),
    .packet_last(packet_last), .block_done(block_done), .block_error(block_error),
    .tensor_in_valid(tensor_in_valid), .tensor_in_ready(tensor_in_ready),
    .tensor_in_first(tensor_in_first), .tensor_in_last(tensor_in_last),
    .tensor_in_activation(tensor_in_activation), .tensor_in_weight_q16(tensor_in_weight_q16),
    .tensor_in_mask(tensor_in_mask), .tensor_out_valid(tensor_out_valid),
    .tensor_out_ready(tensor_out_ready), .tensor_out_data(tensor_out_data),
    .tensor_out_mask(tensor_out_mask), .tensor_protocol_error(tensor_protocol_error),
    .logit_valid(p_logit_valid), .logit_ready(logit_ready && logit_valid),
    .logit_index(p_logit_index), .logit_data(p_logit_data)
  );
  end endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      step <= 0;
      failed <= 0;
      sequence_valid <= 1;
      final_norm <= 0;
      token <= 0;
      position <= 0;
      next_position <= 0;
      component <= 0;
      layer <= 0;
      cycles_low <= 0;
      cycles_high <= 0;
      embedding_value <= 0;
      kernel_operation <= 0;
      projection <= 0;
    end else begin
      if (state != IDLE && state != COMPLETE) begin
        cycles_low <= cycles_low + 32'd1;
        if (&cycles_low) cycles_high <= cycles_high + 32'd1;
      end
      case (state)
        IDLE: if (token_valid && token_ready) begin
          failed <= 0;
          cycles_low <= 0;
          cycles_high <= 0;
          if (token_id >= VOCAB_SIZE || token_pos >= MAX_SEQ_LEN ||
              (new_sequence && token_pos != 0) ||
              (!new_sequence && (!sequence_valid || token_pos != next_position))) begin
            failed <= 1;
            state <= INVALID;
          end else begin
            token <= token_id;
            position <= token_pos;
            component <= 0;
            layer <= 0;
            step <= 0;
            final_norm <= 0;
            if (new_sequence) state <= CLEAR;
            else state <= EMBEDDING_READ;
          end
        end
        CLEAR: state <= CLEAR_WAIT;
        CLEAR_WAIT: if (cache_initialized) state <= EMBEDDING_READ;
        EMBEDDING_READ, EMBEDDING_RESPONSE: begin
          if (req_valid[0] && req_ready[0]) state <= EMBEDDING_RESPONSE;
          if (own_response) begin
            if (mem_rsp_error || fp16_invalid(mem_rsp_rdata[15:0])) begin
              failed <= 1;
              sequence_valid <= 0;
              state <= COMPLETE;
            end else begin
              embedding_value <= fp16_q16(mem_rsp_rdata[15:0]);
              state <= EMBEDDING_WRITE;
            end
          end
        end
        EMBEDDING_WRITE, EMBEDDING_ACK: begin
          if (req_valid[0] && req_ready[0]) state <= EMBEDDING_ACK;
          if (own_response) begin
            if (mem_rsp_error) begin
              failed <= 1;
              sequence_valid <= 0;
              state <= COMPLETE;
            end else if (component + 1 == HIDDEN_SIZE) state <= DISPATCH;
            else begin component <= component + 1; state <= EMBEDDING_READ; end
          end
        end
        DISPATCH: begin
          if (final_norm) begin kernel_operation <= 2; state <= KERNEL_SEND; end
          else case (step)
            0: begin kernel_operation <= 0; state <= KERNEL_SEND; end
            1: begin projection <= 0; state <= PROJECTION_SEND; end
            2: begin projection <= 1; state <= PROJECTION_SEND; end
            3: begin projection <= 2; state <= PROJECTION_SEND; end
            4: begin kernel_operation <= 3; state <= KERNEL_SEND; end
            5: begin kernel_operation <= 7; state <= KERNEL_SEND; end
            6: begin projection <= 3; state <= PROJECTION_SEND; end
            7: begin kernel_operation <= 4; state <= KERNEL_SEND; end
            8: begin kernel_operation <= 1; state <= KERNEL_SEND; end
            9: begin projection <= 4; state <= PROJECTION_SEND; end
            10: begin projection <= 5; state <= PROJECTION_SEND; end
            11: begin kernel_operation <= 6; state <= KERNEL_SEND; end
            12: begin projection <= 6; state <= PROJECTION_SEND; end
            13: begin kernel_operation <= 5; state <= KERNEL_SEND; end
            default: begin failed <= 1; sequence_valid <= 0; state <= COMPLETE; end
          endcase
        end
        KERNEL_SEND: if (kernel_ready) state <= KERNEL_WAIT;
        KERNEL_WAIT: if (kernel_done) begin
          if (kernel_error) begin
            failed <= 1;
            sequence_valid <= 0;
            state <= COMPLETE;
          end else if (final_norm) begin
            projection <= 7;
            layer <= 0;
            state <= PROJECTION_SEND;
          end else if (step == 13) begin
            if (layer + 1 == NUM_LAYERS) final_norm <= 1;
            else layer <= layer + 1;
            step <= 0;
            state <= DISPATCH;
          end else begin step <= step + 1; state <= DISPATCH; end
        end
        PROJECTION_SEND: if (projection_ready) state <= PROJECTION_WAIT;
        PROJECTION_WAIT: begin
          if (projection_done) begin
            if (projection_error || projection == 7) begin
              failed <= 1;
              sequence_valid <= 0;
              state <= COMPLETE;
            end else begin step <= step + 1; state <= DISPATCH; end
          end
          if (final_transfer) begin
            next_position <= position + 1;
            sequence_valid <= 1;
            state <= COMPLETE;
          end
        end
        INVALID: state <= COMPLETE;
        COMPLETE: state <= IDLE;
        default: begin failed <= 1; sequence_valid <= 0; state <= COMPLETE; end
      endcase
      // Keep response ownership until the accepted transaction or child drains.
      if (abort_execution && state != IDLE && state != COMPLETE) begin
        failed <= 1;
        sequence_valid <= 0;
        if (state != KERNEL_WAIT && state != PROJECTION_WAIT &&
            state != EMBEDDING_RESPONSE && state != EMBEDDING_ACK)
          state <= COMPLETE;
        else if ((state == KERNEL_WAIT && kernel_done) ||
                 (state == PROJECTION_WAIT && projection_done) ||
                 ((state == EMBEDDING_RESPONSE || state == EMBEDDING_ACK) && own_response))
          state <= COMPLETE;
      end
    end
  end
endmodule
