module anvil_q1_ht_projection #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_KV_HEADS = 2, HEAD_DIM = 64, GROUP_SIZE = 128,
  parameter VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n, abort_error,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos,
  input wire [3:0] cmd_proj,
  input wire storage_bf16,
  output wire done, error,

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
  input wire tensor_protocol_error,

  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data
);
  import anvil_q1_ht_numeric_pkg::*;
  localparam SAFE_GROUP = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  localparam GROUPS_H = HIDDEN_SIZE / SAFE_GROUP, GROUPS_I = INTERMEDIATE_SIZE / SAFE_GROUP;
  localparam MAX_INPUTS = HIDDEN_SIZE > INTERMEDIATE_SIZE ? HIDDEN_SIZE : INTERMEDIATE_SIZE;
  localparam LEGAL = NUM_LAYERS >= 1 && NUM_LAYERS <= 24 &&
      HIDDEN_SIZE >= 8 && HIDDEN_SIZE <= 896 && (HIDDEN_SIZE & 7) == 0 &&
      INTERMEDIATE_SIZE >= 8 && INTERMEDIATE_SIZE <= 4864 && (INTERMEDIATE_SIZE & 7) == 0 &&
      NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 && HEAD_DIM >= 2 && HEAD_DIM <= 64 &&
      (HEAD_DIM & 1) == 0 && ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
      GROUP_SIZE >= 1 && HIDDEN_SIZE % SAFE_GROUP == 0 &&
      INTERMEDIATE_SIZE % SAFE_GROUP == 0 &&
      VOCAB_SIZE >= 1 && VOCAB_SIZE <= 151936 &&
      MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768;
  generate if (LEGAL) begin : g_legal
    localparam IDLE = 6'd0, COMPLETE = 6'd1, INVALID = 6'd2,
      INPUT_REQUEST = 6'd3, INPUT_RESPONSE = 6'd4,
      PANEL = 6'd5, PANEL_ADDRESS = 6'd6,
      ZERO_REQUEST = 6'd7, ZERO_PACKET = 6'd8, ZERO_DONE = 6'd9,
      SCALE_REQUEST = 6'd10, SCALE_PACKET = 6'd11, SCALE_DONE = 6'd12,
      WEIGHT_REQUEST = 6'd13, WEIGHT_PACKET = 6'd14,
      DEQUANT_REQUEST = 6'd15, DEQUANT_RESULT = 6'd16,
      TENSOR_SEND = 6'd17, WEIGHT_DONE = 6'd18,
      BIAS_REQUEST = 6'd19, BIAS_PACKET = 6'd20, BIAS_DONE = 6'd21,
      BIAS_SEND = 6'd22, TENSOR_RESULT = 6'd23,
      OUTPUT_REQUEST = 6'd24, OUTPUT_RESPONSE = 6'd25,
      LOGIT = 6'd26, NEXT_PANEL = 6'd27, FAIL_DRAIN = 6'd28,
      FP16_CONVERT = 6'd29;
    reg [5:0] state;
    reg failed, bf16, vocabulary, block_active, block_finished, memory_pending;
    reg [31:0] layer, position, inputs, outputs, source_slot, target_slot;
    reg [3:0] projection;
    reg [31:0] k, panel, input_index, group_row, group_inputs;
    reg [6:0] lanes;
    reg [5:0] output_lane;
    reg [63:0] mask;
    reg [7:0] row_bytes;
    reg [31:0] panel_weight_offset, panel_zero_offset, panel_scale_offset;
    reg [31:0] group_weight_offset, group_zero_offset, group_scale_offset;
    reg [31:0] weight_length, panel_weight_length, panel_zero_length, panel_scale_length;
    reg [255:0] zero_words;
    reg [1023:0] scale_words, row_words;
    reg [2367:0] weights;
    reg [2047:0] results;
    reg signed [31:0] activation;
    (* ramstyle = "M20K", ram_style = "block" *)
      reg signed [31:0] activation_store [0:MAX_INPUTS-1];
    wire [63:0] dequant_ready, dequant_valid, dequant_error;
    wire [2367:0] dequant_weights;
    wire memory_response = mem_rsp_valid && mem_rsp_ready;
    wire block_accept = block_valid && block_ready;
    wire block_settled = block_finished || block_done;
    wire row_last = k + 1 == inputs;
    wire group_last = group_row + 1 == group_inputs;
    wire [31:0] remaining_outputs = outputs - panel;
    wire [31:0] group_count = inputs == INTERMEDIATE_SIZE ? GROUPS_I : GROUPS_H;
    wire [31:0] result_column = panel + {26'b0, output_lane};
    wire signed [31:0] selected_result = results[32*output_lane+:32];
    wire fp16_bad;
    wire [63:0] fp16_invalid_lanes;
    wire [2367:0] fp16_weights;
    genvar lane;

    for (lane = 0; lane < 64; lane = lane + 1) begin : g_dequant
      localparam [2:0] LOGICAL_LANE = lane & 7;
      wire [15:0] value_bits = mask[lane] ?
        (bf16 ? row_words[16*lane+:16] : scale_words[16*lane+:16]) : 16'b0;
      wire signed [31:0] fp16_value = fp16_q16(row_words[16*lane+:16]);
      anvil_q1_ht_dequant u_dequant (
        .clk(clk), .rst_n(rst_n), .in_valid(state == DEQUANT_REQUEST && (&dequant_ready)),
        .in_ready(dequant_ready[lane]), .in_bf16(bf16),
        .in_qweight(row_words[32*(lane >> 3)+:32]),
        .in_qzero(zero_words[32*(lane >> 3)+:32]),
        .in_lane(LOGICAL_LANE), .in_value(value_bits),
        .out_valid(dequant_valid[lane]),
        .out_ready(state == DEQUANT_RESULT || state == FAIL_DRAIN),
        .out_weight(dequant_weights[37*lane+:37]), .out_error(dequant_error[lane])
      );
      assign fp16_invalid_lanes[lane] = mask[lane] && fp16_invalid(row_words[16*lane+:16]);
      assign fp16_weights[37*lane+:37] = mask[lane] ?
        {{5{fp16_value[31]}}, fp16_value} : 37'b0;
    end
    assign fp16_bad = |fp16_invalid_lanes;
    assign cmd_ready = rst_n && state == IDLE;
    assign done = rst_n && state == COMPLETE;
    assign error = done && failed;
    assign mem_req_valid = rst_n && !abort_error &&
      (state == INPUT_REQUEST || state == OUTPUT_REQUEST);
    assign mem_req_write = mem_req_valid && state == OUTPUT_REQUEST;
    assign mem_req_kind = mem_req_valid ? 4'd8 : 4'b0;
    assign mem_req_layer = 0;
    assign mem_req_proj = 0;
    assign mem_req_row = mem_req_valid ? (state == INPUT_REQUEST ? source_slot : target_slot) : 0;
    assign mem_req_col = mem_req_valid ? (state == INPUT_REQUEST ? input_index : result_column) : 0;
    assign mem_req_wdata = mem_req_write ? selected_result : 32'b0;
    assign mem_rsp_ready = rst_n && ((state == FAIL_DRAIN && memory_pending) ||
      state == INPUT_RESPONSE || state == OUTPUT_RESPONSE ||
      ((state == INPUT_REQUEST || state == OUTPUT_REQUEST) && mem_req_ready));
    assign block_valid = rst_n && !abort_error && (state == ZERO_REQUEST || state == SCALE_REQUEST ||
                                   state == WEIGHT_REQUEST || state == BIAS_REQUEST);
    assign block_kind = !block_valid ? 4'b0 : state == ZERO_REQUEST ? 4'd2 :
      state == SCALE_REQUEST ? 4'd3 : state == BIAS_REQUEST ? 4'd4 : vocabulary ? 4'd0 : 4'd1;
    assign block_layer = block_valid && !vocabulary ? layer : 32'b0;
    assign block_proj = block_valid && !vocabulary ? projection[2:0] : 3'b0;
    assign block_offset = !block_valid ? 32'b0 :
      state == ZERO_REQUEST ? panel_zero_offset + group_zero_offset :
      state == SCALE_REQUEST ? panel_scale_offset + group_scale_offset :
      state == BIAS_REQUEST ? (panel << 1) : panel_weight_offset + group_weight_offset;
    assign block_bytes = !block_valid ? 32'b0 :
      state == ZERO_REQUEST ? {26'b0, lanes[6:1]} :
      (state == SCALE_REQUEST || state == BIAS_REQUEST) ? {24'b0, lanes, 1'b0} : weight_length;
    assign block_packet_bytes = !block_valid ? 8'b0 :
      state == ZERO_REQUEST ? {2'b0, lanes[6:1]} :
      (state == SCALE_REQUEST || state == BIAS_REQUEST) ? {lanes, 1'b0} : row_bytes;
    assign packet_ready = rst_n && (state == ZERO_PACKET || state == SCALE_PACKET ||
                                    state == WEIGHT_PACKET || state == BIAS_PACKET ||
                                    state == FAIL_DRAIN);
    assign tensor_in_valid = rst_n && !failed && !abort_error &&
                             (state == TENSOR_SEND || state == BIAS_SEND);
    assign tensor_in_first = tensor_in_valid && state == TENSOR_SEND && k == 0;
    assign tensor_in_last = tensor_in_valid &&
      (state == BIAS_SEND || (row_last && (vocabulary || projection >= 3)));
    assign tensor_in_activation = tensor_in_valid ?
      (state == BIAS_SEND ? 32'sd65536 : activation) : 32'sd0;
    assign tensor_in_weight_q16 = tensor_in_valid ? weights : 2368'b0;
    assign tensor_in_mask = tensor_in_valid ? mask : 64'b0;
    assign tensor_out_ready = rst_n && state == TENSOR_RESULT;
    assign logit_valid = rst_n && state == LOGIT && !failed && !abort_error;
    assign logit_index = logit_valid ? result_column : 32'b0;
    assign logit_data = logit_valid ? selected_result : 32'sd0;

    always @(posedge clk) begin
      if (rst_n) begin
        if (memory_response && state != OUTPUT_REQUEST && state != OUTPUT_RESPONSE &&
            !mem_rsp_error) activation_store[input_index] <= mem_rsp_rdata;
        if (state == WEIGHT_PACKET && packet_valid) activation <= activation_store[k];
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        failed <= 0;
        bf16 <= 0;
        vocabulary <= 0;
        block_active <= 0;
        block_finished <= 0;
        memory_pending <= 0;
        layer <= 0;
        position <= 0;
        inputs <= 0;
        outputs <= 0;
        source_slot <= 0;
        target_slot <= 0;
        projection <= 0;
        k <= 0;
        panel <= 0;
        input_index <= 0;
        group_row <= 0;
        group_inputs <= 0;
        lanes <= 0;
        output_lane <= 0;
        mask <= 0;
        row_bytes <= 0;
        panel_weight_offset <= 0;
        panel_zero_offset <= 0;
        panel_scale_offset <= 0;
        group_weight_offset <= 0;
        group_zero_offset <= 0;
        group_scale_offset <= 0;
        weight_length <= 0;
        panel_weight_length <= 0;
        panel_zero_length <= 0;
        panel_scale_length <= 0;
        zero_words <= 0;
        scale_words <= 0;
        row_words <= 0;
        weights <= 0;
        results <= 0;
      end else begin
        if (mem_req_valid && mem_req_ready) memory_pending <= 1;
        if (memory_response) memory_pending <= 0;
        if (block_accept) begin
          block_active <= 1;
          block_finished <= 0;
        end
        if (block_done) begin
          block_active <= 0;
          block_finished <= 1;
        end
        case (state)
          IDLE: if (cmd_valid) begin
            failed <= 0;
            bf16 <= storage_bf16;
            vocabulary <= cmd_proj == 7;
            layer <= cmd_layer;
            position <= cmd_pos;
            projection <= cmd_proj;
            inputs <= cmd_proj == 6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
            panel <= 0;
            input_index <= 0;
            panel_weight_offset <= 0;
            panel_zero_offset <= 0;
            panel_scale_offset <= 0;
            case (cmd_proj)
              0: begin outputs <= HIDDEN_SIZE; source_slot <= 1; target_slot <= 2; end
              1: begin outputs <= NUM_KV_HEADS*HEAD_DIM; source_slot <= 1; target_slot <= 3; end
              2: begin outputs <= NUM_KV_HEADS*HEAD_DIM; source_slot <= 1; target_slot <= 4; end
              3: begin outputs <= HIDDEN_SIZE; source_slot <= 5; target_slot <= 6; end
              4: begin outputs <= INTERMEDIATE_SIZE; source_slot <= 8; target_slot <= 9; end
              5: begin outputs <= INTERMEDIATE_SIZE; source_slot <= 8; target_slot <= 10; end
              6: begin outputs <= HIDDEN_SIZE; source_slot <= 11; target_slot <= 12; end
              default: begin outputs <= VOCAB_SIZE; source_slot <= 14; target_slot <= 0; end
            endcase
            if (cmd_layer >= NUM_LAYERS || cmd_pos >= MAX_SEQ_LEN || cmd_proj > 7) begin
              failed <= 1;
              state <= INVALID;
            end else state <= INPUT_REQUEST;
          end
          INPUT_REQUEST, INPUT_RESPONSE: begin
            if (mem_req_valid && mem_req_ready) state <= INPUT_RESPONSE;
            if (memory_response) begin
              if (input_index + 1 == inputs) state <= PANEL;
              else begin
                input_index <= input_index + 1;
                state <= INPUT_REQUEST;
              end
            end
          end
          PANEL: begin
            lanes <= remaining_outputs < 64 ? remaining_outputs[6:0] : 7'd64;
            mask <= remaining_outputs < 64 ?
              (64'hffffffffffffffff >> (32'd64 - remaining_outputs)) : 64'hffffffffffffffff;
            k <= 0;
            group_row <= 0;
            group_weight_offset <= 0;
            group_zero_offset <= 0;
            group_scale_offset <= 0;
            output_lane <= 0;
            state <= PANEL_ADDRESS;
          end
          PANEL_ADDRESS: begin
            row_bytes <= bf16 || vocabulary ? {lanes, 1'b0} : {2'b0, lanes[6:1]};
            group_inputs <= bf16 || vocabulary ? inputs : GROUP_SIZE;
            weight_length <= bf16 || vocabulary ? (inputs * {lanes, 1'b0}) :
                                                  (GROUP_SIZE * {2'b0, lanes[6:1]});
            panel_weight_length <= bf16 || vocabulary ? (inputs * {lanes, 1'b0}) :
                                                        (inputs * {2'b0, lanes[6:1]});
            panel_zero_length <= group_count * {2'b0, lanes[6:1]};
            panel_scale_length <= group_count * {lanes, 1'b0};
            if (bf16 || vocabulary) state <= WEIGHT_REQUEST;
            else state <= ZERO_REQUEST;
          end
          ZERO_REQUEST: if (block_accept) state <= ZERO_PACKET;
          ZERO_PACKET: if (packet_valid) begin
            zero_words <= packet_data[255:0];
            if (!packet_last) begin failed <= 1; state <= FAIL_DRAIN; end
            else state <= ZERO_DONE;
          end
          ZERO_DONE: if (block_settled) state <= SCALE_REQUEST;
          SCALE_REQUEST: if (block_accept) state <= SCALE_PACKET;
          SCALE_PACKET: if (packet_valid) begin
            scale_words <= packet_data;
            if (!packet_last) begin failed <= 1; state <= FAIL_DRAIN; end
            else state <= SCALE_DONE;
          end
          SCALE_DONE: if (block_settled) state <= WEIGHT_REQUEST;
          WEIGHT_REQUEST: if (block_accept) state <= WEIGHT_PACKET;
          WEIGHT_PACKET: if (packet_valid) begin
            row_words <= packet_data;
            if (packet_last != group_last) begin failed <= 1; state <= FAIL_DRAIN; end
            else if (vocabulary) state <= FP16_CONVERT;
            else state <= DEQUANT_REQUEST;
          end
          DEQUANT_REQUEST: if (&dequant_ready) state <= DEQUANT_RESULT;
          DEQUANT_RESULT: if (&dequant_valid) begin
            if (|(dequant_error & mask)) begin failed <= 1; state <= FAIL_DRAIN; end
            else begin weights <= dequant_weights; state <= TENSOR_SEND; end
          end
          FP16_CONVERT: begin
            weights <= fp16_weights;
            if (fp16_bad) begin failed <= 1; state <= FAIL_DRAIN; end
            else state <= TENSOR_SEND;
          end
          TENSOR_SEND: if (tensor_in_ready) begin
            if (group_last) state <= WEIGHT_DONE;
            else begin
              k <= k + 1;
              group_row <= group_row + 1;
              state <= WEIGHT_PACKET;
            end
          end
          WEIGHT_DONE: if (block_settled) begin
            if (row_last) begin
              if (!vocabulary && projection < 3) state <= BIAS_REQUEST;
              else state <= TENSOR_RESULT;
            end else begin
              k <= k + 1;
              group_row <= 0;
              group_weight_offset <= group_weight_offset + weight_length;
              group_zero_offset <= group_zero_offset + {26'b0, lanes[6:1]};
              group_scale_offset <= group_scale_offset + {24'b0, lanes, 1'b0};
              state <= ZERO_REQUEST;
            end
          end
          BIAS_REQUEST: if (block_accept) state <= BIAS_PACKET;
          BIAS_PACKET: if (packet_valid) begin
            row_words <= packet_data;
            if (!packet_last) begin failed <= 1; state <= FAIL_DRAIN; end
            else state <= BIAS_DONE;
          end
          BIAS_DONE: if (block_settled) begin
            weights <= fp16_weights;
            if (fp16_bad) begin failed <= 1; state <= FAIL_DRAIN; end
            else state <= BIAS_SEND;
          end
          BIAS_SEND: if (tensor_in_ready) state <= TENSOR_RESULT;
          TENSOR_RESULT: if (tensor_out_valid) begin
            results <= tensor_out_data;
            output_lane <= 0;
            if (tensor_out_mask != mask) begin failed <= 1; state <= FAIL_DRAIN; end
            else if (vocabulary) state <= LOGIT;
            else state <= OUTPUT_REQUEST;
          end
          OUTPUT_REQUEST, OUTPUT_RESPONSE: begin
            if (mem_req_valid && mem_req_ready) state <= OUTPUT_RESPONSE;
            if (memory_response) begin
              if ({1'b0, output_lane} + 7'd1 == lanes) state <= NEXT_PANEL;
              else begin output_lane <= output_lane + 1'b1; state <= OUTPUT_REQUEST; end
            end
          end
          LOGIT: if (logit_ready) begin
            if ({1'b0, output_lane} + 7'd1 == lanes) state <= NEXT_PANEL;
            else output_lane <= output_lane + 1'b1;
          end
          NEXT_PANEL: begin
            if (panel + {25'b0, lanes} == outputs) state <= COMPLETE;
            else begin
              panel <= panel + {25'b0, lanes};
              panel_weight_offset <= panel_weight_offset + panel_weight_length;
              panel_zero_offset <= panel_zero_offset + panel_zero_length;
              panel_scale_offset <= panel_scale_offset + panel_scale_length;
              state <= PANEL;
            end
          end
          FAIL_DRAIN: if ((!block_active || block_done) &&
                         (!memory_pending || memory_response)) state <= COMPLETE;
          INVALID: state <= COMPLETE;
          COMPLETE: state <= IDLE;
          default: begin failed <= 1; state <= FAIL_DRAIN; end
        endcase
        if ((memory_response && mem_rsp_error) || (block_done && block_error) ||
            ((tensor_protocol_error || abort_error) && state != IDLE && state != COMPLETE &&
             state != FAIL_DRAIN)) begin
          failed <= 1;
          state <= FAIL_DRAIN;
        end
      end
    end
  end else begin : g_illegal
    initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: projection dimensions");
    assign cmd_ready = 0;
    assign done = 0;
    assign error = 0;
    assign mem_req_valid = 0;
    assign mem_req_write = 0;
    assign mem_req_kind = 0;
    assign mem_req_layer = 0;
    assign mem_req_proj = 0;
    assign mem_req_row = 0;
    assign mem_req_col = 0;
    assign mem_req_wdata = 0;
    assign mem_rsp_ready = 0;
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
    assign logit_valid = 0;
    assign logit_index = 0;
    assign logit_data = 0;
  end endgenerate
endmodule
