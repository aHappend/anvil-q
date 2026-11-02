module anvil_q2_fp2_top #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
  AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  BANKS=4, CACHE_MODE=0, CACHE_BLOCK=16, QUEUE_DEPTH=3,
  FP_FORMAT=0, WEIGHT_MODE=0,
  SB=(BANKS==1 || BANKS==2 || BANKS==4) ? BANKS : 1,
  ACCEL_ENABLE=1, COUNTER_BITS=64
) (
  input wire clk, rst_n, cancel,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence, token_phase,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index, logit_data,
  output wire done, error, cancel_done,
  output wire [SB-1:0] mem_req_valid,
  input wire [SB-1:0] mem_req_ready,
  output wire [SB-1:0] mem_req_write,
  output wire [SB*4-1:0] mem_req_kind,
  output wire [SB*32-1:0] mem_req_layer,
  output wire [SB*3-1:0] mem_req_proj,
  output wire [SB*32-1:0] mem_req_row, mem_req_col, mem_req_wdata,
  output wire [SB*64-1:0] mem_req_tag,
  input wire [SB-1:0] mem_rsp_valid, mem_rsp_error,
  output wire [SB-1:0] mem_rsp_ready,
  input wire [SB*32-1:0] mem_rsp_rdata,
  input wire [SB*64-1:0] mem_rsp_tag,
  output wire ddr_req_valid,
  input wire ddr_req_ready,
  output wire ddr_req_write,
  output wire [3:0] ddr_req_kind,
  output wire [31:0] ddr_req_layer,
  output wire [2:0] ddr_req_proj,
  output wire [31:0] ddr_req_row, ddr_req_col,
  output wire [1:0] ddr_req_format,
  output wire [63:0] ddr_req_tag,
  output wire [511:0] ddr_req_wdata,
  output wire [63:0] ddr_req_wstrb,
  input wire ddr_rsp_valid, ddr_rsp_error,
  output wire ddr_rsp_ready,
  input wire [63:0] ddr_rsp_tag,
  input wire [511:0] ddr_rsp_rdata,
  input wire csr_req_valid, csr_req_write,
  input wire [15:0] csr_req_addr,
  input wire [31:0] csr_req_wdata,
  input wire [3:0] csr_req_wstrb,
  output wire csr_req_ready, csr_rsp_valid,
  output wire [31:0] csr_rsp_rdata,
  output wire csr_rsp_error,
  input wire csr_rsp_ready
);
  localparam SG=(GROUP_SIZE>0) ? GROUP_SIZE : 1;
  localparam SK=(NUM_KV_HEADS>0) ? NUM_KV_HEADS : 1;
  localparam CB=(CACHE_BLOCK>0) ? CACHE_BLOCK : 1;
  localparam [127:0] L=NUM_LAYERS, H=HIDDEN_SIZE, I=INTERMEDIATE_SIZE;
  localparam [127:0] Q=NUM_Q_HEADS, K=NUM_KV_HEADS, D=HEAD_DIM;
  localparam [127:0] V=VOCAB_SIZE, S=MAX_SEQ_LEN, B=CACHE_BLOCK;
  localparam [127:0] GROUP=GROUP_SIZE, LIMIT=128'd4294967295;
  localparam [127:0] NB=D/CB, NW=(B+3)/4;
  localparam FAST=ACCEL_ENABLE==1 && FP_FORMAT==0 &&
    (WEIGHT_MODE==0 || WEIGHT_MODE==2) && (CACHE_MODE==0 || CACHE_MODE==2);
  localparam LEGACY=(FP_FORMAT==0 || FP_FORMAT==1) &&
    (WEIGHT_MODE==0 || WEIGHT_MODE==1) && (CACHE_MODE==0 || CACHE_MODE==1);
  localparam BASE_VALID=NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_Q_HEADS>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 && GROUP_SIZE>0 &&
    VOCAB_SIZE>0 && MAX_SEQ_LEN>0 && AWQ_BITS==4 &&
    (BANKS==1 || BANKS==2 || BANKS==4) &&
    SB==((BANKS==1 || BANKS==2 || BANKS==4) ? BANKS : 1) &&
    QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    CACHE_BLOCK>0 && CACHE_BLOCK<=65536 &&
    (CACHE_BLOCK & (CACHE_BLOCK-1))==0 && HEAD_DIM%CB==0 &&
    L<=LIMIT && H<=LIMIT && I<=LIMIT && Q<=LIMIT && K<=LIMIT &&
    D<=LIMIT && GROUP<=LIMIT && V<=LIMIT && S<=128'd16777215 &&
    H==Q*D && NUM_Q_HEADS%SK==0 && HEAD_DIM%2==0 &&
    HIDDEN_SIZE%SG==0 && INTERMEDIATE_SIZE%SG==0 &&
    HIDDEN_SIZE%8==0 && INTERMEDIATE_SIZE%8==0 && (K*D)%8==0 &&
    V*H<=LIMIT && H*H<=LIMIT && H*I<=LIMIT && H*K*D<=LIMIT &&
    L*S*K*D<=LIMIT && S*D<=LIMIT && 2*D<=LIMIT &&
    15*H<=LIMIT && 15*I<=LIMIT &&
    K*NB*NW<=LIMIT && L*S*K*NB*NW<=LIMIT && L*S*K*NB<=LIMIT;
  localparam FAST_VALID=NUM_LAYERS<=28 && HIDDEN_SIZE<=1536 &&
    INTERMEDIATE_SIZE<=8960 && VOCAB_SIZE<=151936 && MAX_SEQ_LEN<=32768 &&
    HEAD_DIM>=2 && HEAD_DIM<=128 && NUM_Q_HEADS==6*NUM_KV_HEADS;
  localparam VALID=BASE_VALID && (ACCEL_ENABLE==0 || ACCEL_ENABLE==1) &&
    COUNTER_BITS>=1 && COUNTER_BITS<=64 &&
    ((FAST && FAST_VALID) || (!FAST && LEGACY));
  wire event_active, event_weight_underflow, event_tensor_bubble, event_epilogue_stall;
  wire [15:0] event_kv_reuses;
  wire narrow_stall=(|(mem_req_valid & ~mem_req_ready));
  wire ddr_transfer=ddr_req_valid && ddr_req_ready;
  wire kv_transfer=ddr_transfer && (ddr_req_kind==9 || ddr_req_kind==10 ||
    ddr_req_kind==12 || ddr_req_kind==13 || ddr_req_kind==14 || ddr_req_kind==15);
  anvil_q2_fp2_telemetry #(.COUNTER_BITS(COUNTER_BITS)) telemetry(
    .clk(clk),.rst_n(rst_n),.event_active(event_active),
    .event_mem_stall(narrow_stall || (ddr_req_valid && !ddr_req_ready)),
    .event_weight_underflow(event_weight_underflow),
    .event_tensor_bubble(event_tensor_bubble),
    .event_epilogue_stall(event_epilogue_stall),
    .event_kv_bytes(kv_transfer ? 16'd64 : 16'd0),
    .event_ddr_read(ddr_transfer && !ddr_req_write),
    .event_ddr_write(ddr_transfer && ddr_req_write),
    .event_kv_reuses(event_kv_reuses),
    .event_token_complete(done && !error),.event_mx_saturation(1'b0),
    .event_error_complete(done && error),
    .csr_req_valid(csr_req_valid),.csr_req_write(csr_req_write),
    .csr_req_addr(csr_req_addr),.csr_req_wdata(csr_req_wdata),
    .csr_req_wstrb(csr_req_wstrb),.csr_req_ready(csr_req_ready),
    .csr_rsp_valid(csr_rsp_valid),.csr_rsp_rdata(csr_rsp_rdata),
    .csr_rsp_error(csr_rsp_error),.csr_rsp_ready(csr_rsp_ready));
  generate if (!VALID) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_FP2 PARAMETER ERROR: dimensions, modes or address bounds");
    assign token_ready=0; assign logit_valid=0; assign logit_index=0; assign logit_data=0;
    assign done=0; assign error=0; assign cancel_done=0;
    assign mem_req_valid=0; assign mem_req_write=0; assign mem_req_kind=0;
    assign mem_req_layer=0; assign mem_req_proj=0; assign mem_req_row=0;
    assign mem_req_col=0; assign mem_req_wdata=0; assign mem_req_tag=0;
    assign mem_rsp_ready=0;
    assign ddr_req_valid=0; assign ddr_req_write=0; assign ddr_req_kind=0;
    assign ddr_req_layer=0; assign ddr_req_proj=0; assign ddr_req_row=0;
    assign ddr_req_col=0; assign ddr_req_format=0; assign ddr_req_tag=0;
    assign ddr_req_wdata=0; assign ddr_req_wstrb=0; assign ddr_rsp_ready=0;
    assign event_active=0; assign event_weight_underflow=0;
    assign event_tensor_bubble=0; assign event_epilogue_stall=0;
    assign event_kv_reuses=0;
  end else if (!FAST) begin: compatibility
    reg active;
    anvil_q2_fp_top #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
      .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
      .GROUP_SIZE(GROUP_SIZE),.AWQ_BITS(AWQ_BITS),.VOCAB_SIZE(VOCAB_SIZE),
      .MAX_SEQ_LEN(MAX_SEQ_LEN),.BANKS(BANKS),.CACHE_MODE(CACHE_MODE),
      .CACHE_BLOCK(CACHE_BLOCK),.QUEUE_DEPTH(QUEUE_DEPTH),.FP_FORMAT(FP_FORMAT),
      .WEIGHT_MODE(WEIGHT_MODE),.SB(SB)) parent(
      .clk(clk),.rst_n(rst_n),.cancel(cancel),
      .token_valid(token_valid),.token_ready(token_ready),
      .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),
      .token_phase(token_phase),
      .logit_valid(logit_valid),.logit_ready(logit_ready),
      .logit_index(logit_index),.logit_data(logit_data),
      .done(done),.error(error),.cancel_done(cancel_done),
      .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
      .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
      .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
      .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
      .mem_req_tag(mem_req_tag),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),
      .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag));
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) active<=0;
      else if (done || cancel_done) active<=0;
      else if (token_valid && token_ready) active<=1;
    end
    assign event_active=rst_n && active;
    assign event_weight_underflow=0; assign event_tensor_bubble=0;
    assign event_epilogue_stall=0; assign event_kv_reuses=0;
    assign ddr_req_valid=0; assign ddr_req_write=0; assign ddr_req_kind=0;
    assign ddr_req_layer=0; assign ddr_req_proj=0; assign ddr_req_row=0;
    assign ddr_req_col=0; assign ddr_req_format=0; assign ddr_req_tag=0;
    assign ddr_req_wdata=0; assign ddr_req_wstrb=0; assign ddr_rsp_ready=0;
  end else begin: accelerated
    wire flush_memory, memory_idle, memory_drain_done, memory_fault, memory_draining;
    wire req_valid, req_ready, req_write, rsp_valid, rsp_ready, rsp_error;
    wire [3:0] req_kind;
    wire [31:0] req_layer, req_row, req_col, req_tag, rsp_tag;
    wire [2:0] req_proj;
    wire [1:0] req_format;
    wire [511:0] req_wdata, rsp_data;
    wire [63:0] req_wstrb;
    wire tensor_flush, tw_valid, tw_ready, tw_format, tw_first, tw_last, tw_error;
    wire [511:0] tw_data;
    wire [15:0] tw_scale;
    wire [31:0] tw_tag;
    wire ti_valid, ti_ready, ti_first, ti_last, to_valid, to_ready, to_first, to_last, to_error;
    wire [2047:0] ti_a;
    wire [127:0] ti_mask;
    wire [31:0] ti_tag, to_data, to_tag;
    wire ep_flush, ei_valid, ei_ready, ei_first, ei_last;
    wire [2:0] ei_mode;
    wire [31:0] ei_a, ei_b, ei_gamma, ei_cos, ei_sin, ei_length, ei_index, ei_tag;
    wire eo_valid, eo_ready, eo_first, eo_last, eo_error;
    wire [31:0] eo_data, eo_pair, eo_index, eo_tag;
    localparam G=(HEAD_DIM+31) >> 5;
    wire attention_flush, ac_valid, ac_ready;
    wire [31:0] ac_layer, ac_head, ac_pos, ac_len, ac_tag;
    wire [6*HEAD_DIM*16-1:0] ac_query;
    wire ak_valid, ak_ready, ak_format, ak_last, ak_error;
    wire [HEAD_DIM*16-1:0] ak_key, ak_value;
    wire [G*8-1:0] ak_scale_key, ak_scale_value;
    wire [31:0] ak_index, ao_tag;
    wire ao_valid, ao_ready, ao_error;
    wire [6*HEAD_DIM*32-1:0] ao_data;
    assign mem_req_valid=0; assign mem_req_write=0; assign mem_req_kind=0;
    assign mem_req_layer=0; assign mem_req_proj=0; assign mem_req_row=0;
    assign mem_req_col=0; assign mem_req_wdata=0; assign mem_req_tag=0;
    assign mem_rsp_ready=0;
    anvil_q2_fp2_controller #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
      .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
      .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),
      .WEIGHT_MODE(WEIGHT_MODE),.CACHE_MODE(CACHE_MODE)) controller(
      .clk(clk),.rst_n(rst_n),.cancel(cancel),
      .token_valid(token_valid),.token_ready(token_ready),.token_id(token_id),
      .token_pos(token_pos),.new_sequence(new_sequence),.token_phase(token_phase),
      .logit_valid(logit_valid),.logit_ready(logit_ready),.logit_index(logit_index),
      .logit_data(logit_data),.done(done),.error(error),.cancel_done(cancel_done),
      .event_active(event_active),.event_weight_underflow(event_weight_underflow),
      .event_tensor_bubble(event_tensor_bubble),.event_epilogue_stall(event_epilogue_stall),
      .event_kv_reuses(event_kv_reuses),
      .memory_flush(flush_memory),.memory_idle(memory_idle),
      .memory_drain_done(memory_drain_done),.memory_fault(memory_fault),
      .req_valid(req_valid),.req_ready(req_ready),.req_write(req_write),
      .req_kind(req_kind),.req_layer(req_layer),.req_row(req_row),.req_col(req_col),
      .req_tag(req_tag),.req_proj(req_proj),.req_format(req_format),
      .req_wdata(req_wdata),.req_wstrb(req_wstrb),
      .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data),
      .rsp_tag(rsp_tag),.rsp_error(rsp_error),
      .tensor_flush(tensor_flush),
      .tensor_w_valid(tw_valid),.tensor_w_ready(tw_ready),.tensor_w_data(tw_data),
      .tensor_w_scale(tw_scale),.tensor_w_format(tw_format),
      .tensor_w_first(tw_first),.tensor_w_last(tw_last),
      .tensor_w_error(tw_error),.tensor_w_tag(tw_tag),
      .tensor_in_valid(ti_valid),.tensor_in_ready(ti_ready),.tensor_in_a(ti_a),
      .tensor_in_mask(ti_mask),.tensor_in_first(ti_first),
      .tensor_in_last(ti_last),.tensor_in_tag(ti_tag),
      .tensor_out_valid(to_valid),.tensor_out_ready(to_ready),.tensor_out_data(to_data),
      .tensor_out_tag(to_tag),.tensor_out_first(to_first),
      .tensor_out_last(to_last),.tensor_out_error(to_error),
      .epilogue_flush(ep_flush),
      .epilogue_in_valid(ei_valid),.epilogue_in_ready(ei_ready),.epilogue_in_mode(ei_mode),
      .epilogue_in_a(ei_a),.epilogue_in_b(ei_b),.epilogue_in_gamma(ei_gamma),
      .epilogue_in_cos(ei_cos),.epilogue_in_sin(ei_sin),.epilogue_in_length(ei_length),
      .epilogue_in_index(ei_index),.epilogue_in_tag(ei_tag),
      .epilogue_in_first(ei_first),.epilogue_in_last(ei_last),
      .epilogue_out_valid(eo_valid),.epilogue_out_ready(eo_ready),
      .epilogue_out_data(eo_data),.epilogue_out_pair(eo_pair),
      .epilogue_out_index(eo_index),.epilogue_out_tag(eo_tag),
      .epilogue_out_first(eo_first),.epilogue_out_last(eo_last),
      .epilogue_out_error(eo_error),
      .attention_flush(attention_flush),
      .attention_cmd_valid(ac_valid),.attention_cmd_ready(ac_ready),
      .attention_cmd_layer(ac_layer),.attention_cmd_kv_head(ac_head),
      .attention_cmd_pos(ac_pos),.attention_cmd_len(ac_len),.attention_cmd_tag(ac_tag),
      .attention_cmd_query(ac_query),
      .attention_kv_valid(ak_valid),.attention_kv_ready(ak_ready),
      .attention_kv_key(ak_key),.attention_kv_value(ak_value),
      .attention_kv_scale_key(ak_scale_key),.attention_kv_scale_value(ak_scale_value),
      .attention_kv_format(ak_format),.attention_kv_index(ak_index),
      .attention_kv_last(ak_last),.attention_kv_error(ak_error),
      .attention_out_valid(ao_valid),.attention_out_ready(ao_ready),
      .attention_out_data(ao_data),.attention_out_tag(ao_tag),.attention_out_error(ao_error));
    anvil_q2_fp2_bfp_tensor_array tensor_array(
      .clk(clk),.rst_n(rst_n),.flush(tensor_flush),
      .w_valid(tw_valid),.w_data(tw_data),.w_scale(tw_scale),.w_format(tw_format),
      .w_first(tw_first),.w_last(tw_last),.w_tag(tw_tag),.w_error(tw_error),.w_ready(tw_ready),
      .in_valid(ti_valid),.in_a(ti_a),.in_mask(ti_mask),.in_first(ti_first),
      .in_last(ti_last),.in_tag(ti_tag),.in_ready(ti_ready),
      .out_valid(to_valid),.out_data(to_data),.out_first(to_first),
      .out_last(to_last),.out_tag(to_tag),.out_error(to_error),.out_ready(to_ready));
    anvil_q2_fp2_epilogue_fusion epilogue(
      .clk(clk),.rst_n(rst_n),.flush(ep_flush),
      .in_valid(ei_valid),.in_mode(ei_mode),.in_a(ei_a),.in_b(ei_b),
      .in_gamma(ei_gamma),.in_cos(ei_cos),.in_sin(ei_sin),.in_length(ei_length),
      .in_index(ei_index),.in_tag(ei_tag),.in_first(ei_first),.in_last(ei_last),
      .in_ready(ei_ready),.out_valid(eo_valid),.out_data(eo_data),.out_pair(eo_pair),
      .out_index(eo_index),.out_tag(eo_tag),.out_first(eo_first),.out_last(eo_last),
      .out_error(eo_error),.out_ready(eo_ready));
    anvil_q2_fp2_flash_attn #(.HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)) flash_attention(
      .clk(clk),.rst_n(rst_n),.flush(attention_flush),
      .cmd_valid(ac_valid),.cmd_layer(ac_layer),.cmd_kv_head(ac_head),.cmd_pos(ac_pos),
      .cmd_len(ac_len),.cmd_tag(ac_tag),.cmd_query(ac_query),.cmd_ready(ac_ready),
      .kv_valid(ak_valid),.kv_key(ak_key),.kv_value(ak_value),
      .kv_scale_key(ak_scale_key),.kv_scale_value(ak_scale_value),.kv_format(ak_format),
      .kv_index(ak_index),.kv_last(ak_last),.kv_error(ak_error),.kv_ready(ak_ready),
      .out_valid(ao_valid),.out_data(ao_data),.out_tag(ao_tag),
      .out_error(ao_error),.out_ready(ao_ready));
    anvil_q2_fp2_ddr_engine #(.QUEUE_DEPTH(QUEUE_DEPTH)) memory_transport(
      .clk(clk),.rst_n(rst_n),.flush(flush_memory),
      .req_valid(req_valid),.req_ready(req_ready),.req_write(req_write),
      .req_kind(req_kind),.req_layer(req_layer),.req_proj(req_proj),
      .req_row(req_row),.req_col(req_col),.req_format(req_format),.req_tag(req_tag),
      .req_wdata(req_wdata),.req_wstrb(req_wstrb),
      .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_rdata(rsp_data),
      .rsp_tag(rsp_tag),.rsp_error(rsp_error),
      .idle(memory_idle),.draining(memory_draining),
      .drain_done(memory_drain_done),.fault(memory_fault),
      .ddr_req_valid(ddr_req_valid),.ddr_req_ready(ddr_req_ready),
      .ddr_req_write(ddr_req_write),.ddr_req_kind(ddr_req_kind),
      .ddr_req_layer(ddr_req_layer),.ddr_req_proj(ddr_req_proj),
      .ddr_req_row(ddr_req_row),.ddr_req_col(ddr_req_col),
      .ddr_req_format(ddr_req_format),.ddr_req_tag(ddr_req_tag),
      .ddr_req_wdata(ddr_req_wdata),.ddr_req_wstrb(ddr_req_wstrb),
      .ddr_rsp_valid(ddr_rsp_valid),.ddr_rsp_error(ddr_rsp_error),
      .ddr_rsp_ready(ddr_rsp_ready),.ddr_rsp_tag(ddr_rsp_tag),.ddr_rsp_rdata(ddr_rsp_rdata));
  end endgenerate
endmodule
