module anvil_q1_ht_compat_projection #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_KV_HEADS = 2, HEAD_DIM = 64, GROUP_SIZE = 128,
  parameter VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n, abort_error, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos,
  input wire [3:0] cmd_proj,
  output wire done, error,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output reg [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output reg [31:0] mem_req_row, mem_req_col,
  output wire [31:0] mem_req_wdata,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data
);
  import anvil_q1_ht_numeric_pkg::*;
  localparam IDLE = 5'd0, ZERO_REQ = 5'd1, ZERO_RSP = 5'd2,
    SCALE_REQ = 5'd3, SCALE_RSP = 5'd4, ACT_REQ = 5'd5, ACT_RSP = 5'd6,
    WEIGHT_REQ = 5'd7, WEIGHT_RSP = 5'd8, CONVERT = 5'd9, CONVERT_WAIT = 5'd10,
    PRODUCT = 5'd11, BIAS_REQ = 5'd12, BIAS_RSP = 5'd13, BIAS_PRODUCT = 5'd14,
    RESULT = 5'd15, WRITE_REQ = 5'd16, WRITE_RSP = 5'd17, LOGIT = 5'd18,
    NEXT_OUTPUT = 5'd19, COMPLETE = 5'd20;
  reg [4:0] state;
  reg failed, vocabulary, memory_pending;
  reg [3:0] projection;
  reg [31:0] layer, inputs, outputs, source_slot, target_slot;
  reg [31:0] k, c, group_index, group_component, qw, qz;
  reg [15:0] scale;
  reg signed [31:0] activation, result;
  reg signed [36:0] weight;
  wire request_state = state == ZERO_REQ || state == SCALE_REQ || state == ACT_REQ ||
    state == WEIGHT_REQ || state == BIAS_REQ || state == WRITE_REQ;
  wire response_state = state == ZERO_RSP || state == SCALE_RSP || state == ACT_RSP ||
    state == WEIGHT_RSP || state == BIAS_RSP || state == WRITE_RSP;
  wire response = mem_rsp_valid && mem_rsp_ready;
  wire metadata = mem_req_kind == 1 || mem_req_kind == 2 || mem_req_kind == 3 ||
                  mem_req_kind == 4;
  wire dequant_ready, dequant_valid, dequant_error;
  wire signed [36:0] dequant_weight;
  wire signed [31:0] converted_weight = fp16_q16(qw[15:0]);
  wire signed [31:0] converted_bias = fp16_q16(mem_rsp_rdata[15:0]);
  wire tensor_ready, tensor_valid, tensor_error;
  wire [2047:0] tensor_data;
  wire product_valid = rst_n && !abort_error && (state == PRODUCT || state == BIAS_PRODUCT);
  wire last_product = state == BIAS_PRODUCT || (k + 1 == inputs && (vocabulary || projection >= 3));

  assign cmd_ready = rst_n && state == IDLE;
  assign done = rst_n && state == COMPLETE;
  assign error = done && failed;
  assign mem_req_valid = rst_n && request_state && !abort_error;
  assign mem_req_write = mem_req_valid && state == WRITE_REQ;
  assign mem_req_layer = mem_req_valid && metadata ? layer : 32'b0;
  assign mem_req_proj = mem_req_valid && metadata ? projection[2:0] : 3'b0;
  assign mem_req_wdata = mem_req_write ? result : 32'b0;
  assign mem_rsp_ready = rst_n && (response_state || memory_pending ||
                                                 (mem_req_valid && mem_req_ready));
  assign logit_valid = rst_n && state == LOGIT && !abort_error;
  assign logit_index = logit_valid ? c : 32'b0;
  assign logit_data = logit_valid ? result : 32'sd0;
  always @* begin
    mem_req_kind = 0;
    mem_req_row = 0;
    mem_req_col = 0;
    if (mem_req_valid) case (state)
      ZERO_REQ: begin mem_req_kind = 2; mem_req_row = group_index; mem_req_col = c >> 3; end
      SCALE_REQ: begin mem_req_kind = 3; mem_req_row = group_index; mem_req_col = c; end
      ACT_REQ: begin mem_req_kind = 8; mem_req_row = source_slot; mem_req_col = k; end
      WEIGHT_REQ: begin
        mem_req_kind = vocabulary ? 4'd0 : 4'd1;
        mem_req_row = vocabulary ? c : k;
        mem_req_col = vocabulary ? k : c >> 3;
      end
      BIAS_REQ: begin mem_req_kind = 4; mem_req_col = c; end
      WRITE_REQ: begin mem_req_kind = 8; mem_req_row = target_slot; mem_req_col = c; end
      default: begin end
    endcase
  end
  anvil_q1_ht_dequant u_dequant (
    .clk(clk), .rst_n(rst_n), .in_valid(state == CONVERT && !vocabulary),
    .in_ready(dequant_ready), .in_bf16(1'b0), .in_qweight(qw), .in_qzero(qz),
    .in_lane(c[2:0]), .in_value(scale), .out_valid(dequant_valid),
    .out_ready(state == CONVERT_WAIT), .out_weight(dequant_weight), .out_error(dequant_error)
  );
  anvil_q1_ht_tensor_array u_dot (
    .clk(clk), .rst_n(rst_n), .in_valid(product_valid), .in_ready(tensor_ready),
    .in_first(state == PRODUCT && k == 0), .in_last(last_product),
    .in_activation(state == BIAS_PRODUCT ? 32'sd65536 : activation),
    .in_weight_q16({2331'b0, weight}), .in_mask(64'd1),
    .out_valid(tensor_valid), .out_ready(state == RESULT),
    .out_data(tensor_data), .out_mask(), .protocol_error(tensor_error)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      failed <= 0;
      vocabulary <= 0;
      memory_pending <= 0;
      projection <= 0;
      layer <= 0;
      inputs <= 0;
      outputs <= 0;
      source_slot <= 0;
      target_slot <= 0;
      k <= 0;
      c <= 0;
      group_index <= 0;
      group_component <= 0;
      qw <= 0;
      qz <= 0;
      scale <= 0;
      activation <= 0;
      result <= 0;
      weight <= 0;
    end else begin
      if (mem_req_valid && mem_req_ready) memory_pending <= 1;
      if (response) memory_pending <= 0;
      case (state)
        IDLE: if (cmd_valid) begin
          failed <= 0;
          vocabulary <= cmd_proj == 7;
          layer <= cmd_layer;
          projection <= cmd_proj;
          inputs <= cmd_proj == 6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
          k <= 0;
          c <= 0;
          group_index <= 0;
          group_component <= 0;
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
            failed <= 1; state <= COMPLETE;
          end else if (cmd_proj == 7) state <= ACT_REQ;
          else state <= ZERO_REQ;
        end
        ZERO_REQ, ZERO_RSP: begin
          if (mem_req_valid && mem_req_ready) state <= ZERO_RSP;
          if (response) begin qz <= mem_rsp_rdata; state <= SCALE_REQ; end
        end
        SCALE_REQ, SCALE_RSP: begin
          if (mem_req_valid && mem_req_ready) state <= SCALE_RSP;
          if (response) begin scale <= mem_rsp_rdata[15:0]; state <= ACT_REQ; end
        end
        ACT_REQ, ACT_RSP: begin
          if (mem_req_valid && mem_req_ready) state <= ACT_RSP;
          if (response) begin activation <= mem_rsp_rdata; state <= WEIGHT_REQ; end
        end
        WEIGHT_REQ, WEIGHT_RSP: begin
          if (mem_req_valid && mem_req_ready) state <= WEIGHT_RSP;
          if (response) begin qw <= mem_rsp_rdata; state <= CONVERT; end
        end
        CONVERT: begin
          if (vocabulary) begin
            weight <= {{5{converted_weight[31]}}, converted_weight};
            if (fp16_invalid(qw[15:0])) begin failed <= 1; state <= COMPLETE; end
            else state <= PRODUCT;
          end else if (dequant_ready) state <= CONVERT_WAIT;
        end
        CONVERT_WAIT: if (dequant_valid) begin
          weight <= dequant_weight;
          if (dequant_error) begin failed <= 1; state <= COMPLETE; end
          else state <= PRODUCT;
        end
        PRODUCT: if (tensor_ready) begin
          if (k + 1 == inputs) begin
            if (vocabulary || projection >= 3) state <= RESULT;
            else state <= BIAS_REQ;
          end else begin
            k <= k + 1;
            if (!vocabulary && group_component == GROUP_SIZE-1) begin
              group_component <= 0;
              group_index <= group_index + 1;
              state <= ZERO_REQ;
            end else begin group_component <= group_component + 1; state <= ACT_REQ; end
          end
        end
        BIAS_REQ, BIAS_RSP: begin
          if (mem_req_valid && mem_req_ready) state <= BIAS_RSP;
          if (response) begin
            weight <= {{5{converted_bias[31]}}, converted_bias};
            if (fp16_invalid(mem_rsp_rdata[15:0])) begin failed <= 1; state <= COMPLETE; end
            else state <= BIAS_PRODUCT;
          end
        end
        BIAS_PRODUCT: if (tensor_ready) state <= RESULT;
        RESULT: if (tensor_valid) begin
          result <= tensor_data[31:0];
          if (vocabulary) state <= LOGIT;
          else state <= WRITE_REQ;
        end
        WRITE_REQ, WRITE_RSP: begin
          if (mem_req_valid && mem_req_ready) state <= WRITE_RSP;
          if (response) state <= NEXT_OUTPUT;
        end
        LOGIT: if (logit_ready) state <= NEXT_OUTPUT;
        NEXT_OUTPUT: begin
          if (c + 1 == outputs) state <= COMPLETE;
          else begin
            c <= c + 1;
            k <= 0;
            group_index <= 0;
            group_component <= 0;
            if (vocabulary) state <= ACT_REQ;
            else state <= ZERO_REQ;
          end
        end
        COMPLETE: state <= IDLE;
        default: begin failed <= 1; state <= COMPLETE; end
      endcase
      if ((response && mem_rsp_error) || tensor_error ||
          (abort_error && state != IDLE && state != COMPLETE)) begin
        failed <= 1;
        if (!memory_pending || response) state <= COMPLETE;
      end
    end
  end
endmodule
