module anvil_q2_q1_compat #(
  parameter NUM_LAYERS=24, HIDDEN_SIZE=896, INTERMEDIATE_SIZE=4864,
  NUM_Q_HEADS=14, NUM_KV_HEADS=2, HEAD_DIM=64, GROUP_SIZE=128,
  AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768
)(
  input wire clk, rst_n,
  input wire token_valid, output wire token_ready,
  input wire [31:0] token_id, token_pos, input wire new_sequence,
  output wire logit_valid, input wire logit_ready,
  output wire [31:0] logit_index, output wire signed [31:0] logit_data,
  output wire done, error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  reg pending;
  reg [63:0] response_tag;
  wire req_valid, req_ready, rsp_ready;
  wire [63:0] request_tag;
  assign mem_req_valid=rst_n && !pending && req_valid;
  assign req_ready=rst_n && !pending && mem_req_ready;
  assign mem_rsp_ready=rst_n && pending && rsp_ready;
  anvil_q2_top #(
    .COMPAT_Q1(1),.NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
    .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
    .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
    .AWQ_BITS(AWQ_BITS),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),
    .BANKS(1),.CACHE_MODE(0),.CACHE_BLOCK(1)) core(
    .clk(clk),.rst_n(rst_n),.cancel(1'b0),
    .token_valid(token_valid),.token_ready(token_ready),.token_id(token_id),
    .token_pos(token_pos),.new_sequence(new_sequence),.token_phase(1'b0),
    .logit_valid(logit_valid),.logit_ready(logit_ready),.logit_index(logit_index),
    .logit_data(logit_data),.done(done),.error(error),.cancel_done(),
    .mem_req_valid(req_valid),.mem_req_ready(req_ready),.mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_tag(request_tag),.mem_rsp_valid(mem_rsp_valid && pending),
    .mem_rsp_error(mem_rsp_error),.mem_rsp_ready(rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(response_tag));
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin pending<=0; response_tag<=0; end
    else begin
      if(mem_req_valid && mem_req_ready) begin pending<=1; response_tag<=request_tag; end
      if(mem_rsp_valid && mem_rsp_ready) pending<=0;
    end
  end
endmodule
