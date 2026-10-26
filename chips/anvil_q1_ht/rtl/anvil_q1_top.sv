module anvil_q1_top #(
  parameter NUM_LAYERS=24, HIDDEN_SIZE=896, INTERMEDIATE_SIZE=4864,
  NUM_Q_HEADS=14, NUM_KV_HEADS=2, HEAD_DIM=64, GROUP_SIZE=128,
  AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768
) (
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
  localparam [127:0] PL=NUM_LAYERS, PH=HIDDEN_SIZE, PI=INTERMEDIATE_SIZE;
  localparam [127:0] PQ=NUM_Q_HEADS, PK=NUM_KV_HEADS, PD=HEAD_DIM;
  localparam [127:0] PG=GROUP_SIZE, PV=VOCAB_SIZE, PS=MAX_SEQ_LEN;
  localparam [127:0] LIMIT=128'd4294967295;
  localparam SG=GROUP_SIZE>0 ? GROUP_SIZE : 1, SK=NUM_KV_HEADS>0 ? NUM_KV_HEADS : 1;
  localparam VALID =
    NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_Q_HEADS>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 && GROUP_SIZE>0 &&
    VOCAB_SIZE>0 && MAX_SEQ_LEN>0 && AWQ_BITS==4 &&
    PL<=LIMIT && PH<=LIMIT && PI<=LIMIT && PQ<=LIMIT && PK<=LIMIT &&
    PD<=LIMIT && PG<=LIMIT && PV<=LIMIT && PS<=128'd16777215 &&
    PH==PQ*PD && NUM_Q_HEADS%SK==0 && HEAD_DIM%2==0 &&
    HIDDEN_SIZE%SG==0 && INTERMEDIATE_SIZE%SG==0 &&
    HIDDEN_SIZE%8==0 && INTERMEDIATE_SIZE%8==0 && (PK*PD)%8==0 &&
    PV*PH<=LIMIT && PH*PH<=LIMIT && PH*PI<=LIMIT && PH*PK*PD<=LIMIT &&
    PL*PS*PK*PD<=LIMIT && PS*PD<=LIMIT && 2*PD<=LIMIT &&
    15*PH<=LIMIT && 15*PI<=LIMIT;
  localparam L=VALID ? NUM_LAYERS : 1, H=VALID ? HIDDEN_SIZE : 8;
  localparam I=VALID ? INTERMEDIATE_SIZE : 8, Q=VALID ? NUM_Q_HEADS : 1;
  localparam K=VALID ? NUM_KV_HEADS : 1, D=VALID ? HEAD_DIM : 8;
  localparam G=VALID ? GROUP_SIZE : 1, V=VALID ? VOCAB_SIZE : 8;
  localparam S=VALID ? MAX_SEQ_LEN : 1;
  wire core_rst_n;
  generate if (!VALID) begin : g_illegal
    initial $fatal(1, "ANVIL_Q1 PARAMETER ERROR: unsupported dimensions or address bounds");
  end endgenerate
  anvil_q1_ht_reset_sync u_reset(clk, rst_n && VALID, core_rst_n);
  anvil_q1_ht_decoder #(L,H,I,Q,K,D,G,V,S,1) u_compatibility (
    .clk(clk), .rst_n(core_rst_n), .engine_enable(1'b1), .storage_bf16(1'b0),
    .execution_fault(1'b0),
    .token_valid(token_valid), .token_ready(token_ready),
    .token_id(token_id), .token_pos(token_pos), .new_sequence(new_sequence),
    .logit_valid(logit_valid), .logit_ready(logit_ready),
    .logit_index(logit_index), .logit_data(logit_data), .done(done), .error(error),
    .busy(), .token_cycles(), .cache_new_sequence(), .cache_initialized(1'b1),
    .mem_req_valid(mem_req_valid), .mem_req_ready(mem_req_ready), .mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind), .mem_req_layer(mem_req_layer), .mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row), .mem_req_col(mem_req_col), .mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid), .mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata), .mem_rsp_error(mem_rsp_error),
    .block_valid(), .block_ready(1'b0), .block_kind(), .block_layer(), .block_proj(),
    .block_offset(), .block_bytes(), .block_packet_bytes(),
    .packet_valid(1'b0), .packet_ready(), .packet_data(1024'b0), .packet_last(1'b0),
    .block_done(1'b0), .block_error(1'b0),
    .tensor_in_valid(), .tensor_in_ready(1'b0), .tensor_in_first(), .tensor_in_last(),
    .tensor_in_activation(), .tensor_in_weight_q16(), .tensor_in_mask(),
    .tensor_out_valid(1'b0), .tensor_out_ready(), .tensor_out_data(2048'b0),
    .tensor_out_mask(64'b0), .tensor_protocol_error(1'b0)
  );
endmodule
