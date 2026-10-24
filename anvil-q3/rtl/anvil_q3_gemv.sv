module anvil_q3_gemv #(
  parameter BANKS=8, TILE_K=128, TILE_ROWS=8,
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128, MAX_SEQ_LEN=32768,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) ? BANKS : 1
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_layer, cmd_pos,
  input wire [2:0] cmd_proj,
  output wire done, error,
  output wire [SB:0] c_req_valid,
  input wire [SB:0] c_req_ready,
  output wire [SB:0] c_req_write,
  output wire [(SB+1)*4-1:0] c_req_kind,
  output wire [(SB+1)*32-1:0] c_req_layer,
  output wire [(SB+1)*3-1:0] c_req_proj,
  output wire [(SB+1)*32-1:0] c_req_row, c_req_col, c_req_wdata,
  input wire [SB:0] c_rsp_valid, c_rsp_error,
  output wire [SB:0] c_rsp_ready,
  input wire [(SB+1)*32-1:0] c_rsp_rdata
);
  localparam IDLE=0, TENSOR_CMD=1, LOAD_REQ=2, LOAD_RSP=3, LOAD_SEND=4;
  localparam RUN=5, BIAS_REQ=6, BIAS_RSP=7, BIAS_ADD=8, BIAS_WAIT=9;
  localparam ROUND=10, WRITE_REQ=11, WRITE_RSP=12, COMPLETE=13, FAULT_WAIT=14;
  generate if (!((BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) && SB==BANKS &&
      MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768)) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: GEMV banks or context");
  end endgenerate
  reg [3:0] state;
  reg failed, tensor_finished;
  reg [31:0] epoch, layer, input_count, input_index, source_slot, target_slot;
  reg [31:0] activation, output_index, rounded_output, round_robin;
  reg [2:0] projection;
  reg signed [127:0] output_accumulator;
  reg signed [31:0] bias;
  wire internal_flush=flush || failed;
  wire tensor_ready, tensor_load_ready, tensor_done, tensor_error;
  wire [SB-1:0] tensor_result_valid;
  reg [SB-1:0] tensor_result_ready;
  wire [SB*32-1:0] tensor_result_row;
  wire [SB*128-1:0] tensor_result_sum;
  wire bias_add_ready, bias_add_valid, bias_add_error;
  wire signed [127:0] biased_sum;
  wire scalar_request=state==LOAD_REQ || state==BIAS_REQ || state==WRITE_REQ;
  wire scalar_response=state==LOAD_RSP || state==BIAS_RSP || state==WRITE_RSP;
  wire [31:0] response_data=c_rsp_rdata[SB*32+:32];
  wire bad_response=c_rsp_valid[SB] && !scalar_response;
  wire response_fault=c_rsp_valid[SB] && scalar_response &&
    (c_rsp_error[SB] || (state==BIAS_RSP &&
      (response_data[31:16]!=0 || anvil_q3_pkg::f16_invalid(response_data[15:0]))));
  integer selected, candidate, offset;

  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  assign c_req_valid[SB]=rst_n && !internal_flush && scalar_request;
  assign c_req_write[SB]=c_req_valid[SB] && state==WRITE_REQ;
  assign c_req_kind[SB*4+:4]=!c_req_valid[SB] ? 4'd0 : state==BIAS_REQ ? 4'd4 : 4'd8;
  assign c_req_layer[SB*32+:32]=c_req_valid[SB] && state==BIAS_REQ ? layer : 32'd0;
  assign c_req_proj[SB*3+:3]=c_req_valid[SB] && state==BIAS_REQ ? projection : 3'd0;
  assign c_req_row[SB*32+:32]=!c_req_valid[SB] || state==BIAS_REQ ? 32'd0 :
    state==WRITE_REQ ? target_slot : source_slot;
  assign c_req_col[SB*32+:32]=!c_req_valid[SB] ? 32'd0 :
    state==LOAD_REQ ? input_index : output_index;
  assign c_req_wdata[SB*32+:32]=c_req_valid[SB] && state==WRITE_REQ ? rounded_output : 32'd0;
  assign c_rsp_ready[SB]=rst_n && !internal_flush;
  always @* begin
    selected=-1;
    candidate=0;
    tensor_result_ready=0;
    if (rst_n && !internal_flush && state==RUN) begin
      for (offset=0;offset<SB;offset=offset+1) begin
        candidate=(round_robin+offset)&(SB-1);
        if (selected<0 && tensor_result_valid[candidate]) selected=candidate;
      end
      if (selected>=0) tensor_result_ready[selected]=1;
    end
  end

  anvil_q3_tensor_array #(
    .BANKS(BANKS),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS),
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
    .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_KV_HEADS(NUM_KV_HEADS),
    .HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE)
  ) tensor_array (
    .clk(clk),.rst_n(rst_n),.flush(internal_flush),
    .cmd_valid(state==TENSOR_CMD),.cmd_ready(tensor_ready),
    .cmd_epoch(epoch),.cmd_layer(layer),.cmd_proj(projection),
    .load_valid(state==LOAD_SEND),.load_last(input_index+1==input_count),
    .load_ready(tensor_load_ready),.load_data(activation),
    .done(tensor_done),.error(tensor_error),
    .result_valid(tensor_result_valid),.result_ready(tensor_result_ready),
    .result_row(tensor_result_row),.result_sum(tensor_result_sum),
    .c_req_valid(c_req_valid[SB-1:0]),.c_req_ready(c_req_ready[SB-1:0]),
    .c_req_write(c_req_write[SB-1:0]),.c_req_kind(c_req_kind[SB*4-1:0]),
    .c_req_layer(c_req_layer[SB*32-1:0]),.c_req_proj(c_req_proj[SB*3-1:0]),
    .c_req_row(c_req_row[SB*32-1:0]),.c_req_col(c_req_col[SB*32-1:0]),
    .c_req_wdata(c_req_wdata[SB*32-1:0]),
    .c_rsp_valid(c_rsp_valid[SB-1:0]),.c_rsp_error(c_rsp_error[SB-1:0]),
    .c_rsp_ready(c_rsp_ready[SB-1:0]),.c_rsp_rdata(c_rsp_rdata[SB*32-1:0])
  );
  anvil_q3_add128 bias_accumulator (
    .clk(clk),.rst_n(rst_n),.flush(internal_flush),
    .in_valid(state==BIAS_ADD),.in_ready(bias_add_ready),
    .in_a(output_accumulator),.in_b({{80{bias[31]}},bias,16'd0}),
    .out_valid(bias_add_valid),.out_ready(1'b1),
    .out_error(bias_add_error),.out_sum(biased_sum)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; tensor_finished<=0;
      epoch<=0; layer<=0; input_count<=0; input_index<=0;
      source_slot<=0; target_slot<=0; activation<=0; output_index<=0;
      rounded_output<=0; round_robin<=0; projection<=0; output_accumulator<=0; bias<=0;
    end else if (flush) begin
      state<=IDLE; failed<=0; tensor_finished<=0;
    end else if (!failed && (bad_response || response_fault ||
        (tensor_done && tensor_error) || (bias_add_valid && bias_add_error))) begin
      state<=COMPLETE;
      failed<=1;
    end else begin
      if (tensor_done) tensor_finished<=1;
      case (state)
        IDLE: if (cmd_valid) begin
          failed<=0; tensor_finished<=0; round_robin<=0;
          epoch<=cmd_epoch; layer<=cmd_layer; projection<=cmd_proj; input_index<=0;
          input_count<=cmd_proj==6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
          case (cmd_proj)
            0: begin source_slot<=1; target_slot<=2; end
            1: begin source_slot<=1; target_slot<=3; end
            2: begin source_slot<=1; target_slot<=4; end
            3: begin source_slot<=5; target_slot<=6; end
            4: begin source_slot<=8; target_slot<=9; end
            5: begin source_slot<=8; target_slot<=10; end
            default: begin source_slot<=11; target_slot<=12; end
          endcase
          if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_proj>6) begin
            state<=COMPLETE; failed<=1;
          end else state<=TENSOR_CMD;
        end
        TENSOR_CMD: if (tensor_ready) state<=LOAD_REQ;
        LOAD_REQ: if (c_req_ready[SB]) state<=LOAD_RSP;
        LOAD_RSP: if (c_rsp_valid[SB]) begin activation<=response_data; state<=LOAD_SEND; end
        LOAD_SEND: if (tensor_load_ready) begin
          if (input_index+1==input_count) state<=RUN;
          else begin input_index<=input_index+1'b1; state<=LOAD_REQ; end
        end
        RUN: begin
          if (selected>=0) begin
            output_index<=tensor_result_row[selected*32+:32];
            output_accumulator<=tensor_result_sum[selected*128+:128];
            round_robin<=(selected+1)&(SB-1);
            if (projection<=2) state<=BIAS_REQ;
            else state<=ROUND;
          end else if (tensor_finished) state<=COMPLETE;
        end
        BIAS_REQ: if (c_req_ready[SB]) state<=BIAS_RSP;
        BIAS_RSP: if (c_rsp_valid[SB]) begin
          bias<=anvil_q3_pkg::f16_q16(response_data[15:0]);
          state<=BIAS_ADD;
        end
        BIAS_ADD: if (bias_add_ready) state<=BIAS_WAIT;
        BIAS_WAIT: if (bias_add_valid) begin output_accumulator<=biased_sum; state<=ROUND; end
        ROUND: begin
          rounded_output<=anvil_q3_pkg::round_q32_to_q16(output_accumulator);
          state<=WRITE_REQ;
        end
        WRITE_REQ: if (c_req_ready[SB]) state<=WRITE_RSP;
        WRITE_RSP: if (c_rsp_valid[SB]) state<=RUN;
        COMPLETE: if (failed) state<=FAULT_WAIT; else state<=IDLE;
        FAULT_WAIT: state<=FAULT_WAIT;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
