module anvil_d2_top #(
  parameter MODEL_MODE=0, PROFILE=3,
  parameter NUM_LAYERS=MODEL_MODE==1 ? (PROFILE==1 ? 24 : PROFILE==2 ? 28 : 36) : 27,
  parameter HIDDEN_SIZE=MODEL_MODE==1 ? (PROFILE==1 ? 896 : PROFILE==2 ? 1536 : 2048) : 2048,
  parameter INTERMEDIATE_SIZE=MODEL_MODE==1 ? (PROFILE==1 ? 4864 : PROFILE==2 ? 8960 : 11008) : 10944,
  parameter NUM_Q_HEADS=MODEL_MODE==1 ? (PROFILE==1 ? 14 : PROFILE==2 ? 12 : 16) : 16,
  parameter NUM_KV_HEADS=2, HEAD_DIM=PROFILE==1 ? 64 : 128,
  parameter GROUP_SIZE=128, AWQ_BITS=4,
  parameter VOCAB_SIZE=MODEL_MODE==1 ? 151936 : 102400, MAX_SEQ_LEN=32768,
  parameter BANKS=8, CACHE_MODE=0, INT4_ASYM=0, CACHE_BLOCK=1,
  parameter QUEUE_DEPTH=3, TILE_K=128, TILE_ROWS=8,
  parameter KV_LORA_RANK=512, QK_NOPE_HEAD_DIM=128, QK_ROPE_HEAD_DIM=64, V_HEAD_DIM=128,
  parameter ROUTED_EXPERTS=64, TOP_K=6, SHARED_EXPERTS=2,
  parameter MOE_INTERMEDIATE_SIZE=1408, FIRST_DENSE_LAYERS=1,
  parameter integer MTP_K=4,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) ? BANKS : 1
) (
  input wire clk, rst_n, cancel,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence, token_phase,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
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
  input wire csr_valid, csr_write,
  input wire [11:0] csr_addr,
  input wire [31:0] csr_wdata,
  input wire [3:0] csr_wstrb,
  input wire csr_rsp_ready,
  output wire csr_ready, csr_rsp_valid,
  output wire [31:0] csr_rdata,
  output wire csr_error,
  output wire spec_valid,
  input wire spec_ready,
  output wire [31:0] spec_token, spec_pos,
  output wire spec_last,
  output wire [2:0] spec_count, spec_accepted
);
  localparam NATIVE_GEOMETRY=
    NUM_LAYERS>=1 && NUM_LAYERS<=36 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=2048 && (HIDDEN_SIZE & 7)==0 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=11008 && (INTERMEDIATE_SIZE & 7)==0 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 && KV_LORA_RANK>=1 && KV_LORA_RANK<=512 &&
    QK_NOPE_HEAD_DIM>=1 && QK_NOPE_HEAD_DIM<=128 &&
    QK_ROPE_HEAD_DIM>=2 && QK_ROPE_HEAD_DIM<=64 && (QK_ROPE_HEAD_DIM & 1)==0 &&
    V_HEAD_DIM>=1 && V_HEAD_DIM<=128 && ROUTED_EXPERTS>=1 && ROUTED_EXPERTS<=64 &&
    TOP_K>=1 && TOP_K<=6 && TOP_K<=ROUTED_EXPERTS && SHARED_EXPERTS==2 &&
    MOE_INTERMEDIATE_SIZE>=8 && MOE_INTERMEDIATE_SIZE<=1408 &&
    (MOE_INTERMEDIATE_SIZE & 7)==0 && FIRST_DENSE_LAYERS>=0 && FIRST_DENSE_LAYERS<=NUM_LAYERS &&
    VOCAB_SIZE>=4 && VOCAB_SIZE<=151936 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    (BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) &&
    QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 && TILE_K>=8 && TILE_K<=128 &&
    (TILE_K & 7)==0 && TILE_ROWS>=1 && TILE_ROWS<=8 && GROUP_SIZE==128 && MTP_K==4;
  localparam NATIVE_ADDRESSES=
    128'(NUM_Q_HEADS)*128'(V_HEAD_DIM)<=128'hffffffff &&
    128'(NUM_Q_HEADS)*128'(KV_LORA_RANK)<=128'hffffffff &&
    128'(NUM_Q_HEADS)*128'(QK_ROPE_HEAD_DIM)<=128'hffffffff &&
    128'(HIDDEN_SIZE)*3<=128'hffffffff && 128'(KV_LORA_RANK)*3<=128'hffffffff &&
    128'(KV_LORA_RANK)+128'(QK_ROPE_HEAD_DIM)<=128'hffffffff &&
    128'(MAX_SEQ_LEN)*(128'(KV_LORA_RANK)+128'(QK_ROPE_HEAD_DIM))*4<=128'hffffffff &&
    128'(HIDDEN_SIZE)*128'(MOE_INTERMEDIATE_SIZE)*4<=128'hffffffff &&
    128'(HIDDEN_SIZE)*128'(INTERMEDIATE_SIZE)*4<=128'hffffffff &&
    128'(HIDDEN_SIZE)*128'(VOCAB_SIZE)*4<=128'hffffffff;
  localparam NATIVE_ENABLED=MODEL_MODE==0 && NATIVE_GEOMETRY && NATIVE_ADDRESSES;
  wire mtp_enable, fp8_enable, generation_enable;
  wire [31:0] generation_limit, eos_token;
  wire [2:0] selected_domain;
  wire [31:0] think_begin_token, think_end_token;
  reg reasoning, token_busy;
  wire accepting=token_valid && token_ready;
  wire reasoning_for_token=token_id!=think_end_token &&
    (token_id==think_begin_token || (!new_sequence && reasoning));
  wire reasoning_active=rst_n && !cancel && !(done && error) &&
    (accepting ? reasoning_for_token : token_busy && reasoning);
  wire work_busy, generation_active, accepted_retire, rejected_block, verification_active;
  wire [2:0] proposed_increment;
  wire engine_flush, active_fp8;
  wire [31:0] epoch;
  wire engine_idle, engine_ready, engine_done, engine_error, engine_cancel_done;
  wire engine_logit_valid, engine_spec_valid, engine_spec_last;
  wire [31:0] engine_logit_index, engine_spec_token, engine_spec_pos;
  wire signed [31:0] engine_logit_data;
  wire [2:0] engine_spec_count, engine_spec_accepted;
  wire adapter_idle, adapter_fault, scheduler_idle, scheduler_drained, scheduler_fault;
  wire service_idle, service_fault;
  wire [28:0] s_req_valid, s_req_ready, s_req_write, s_rsp_valid, s_rsp_ready, s_rsp_error;
  wire [115:0] s_req_kind;
  wire [86:0] s_req_proj;
  wire [927:0] s_req_layer, s_req_row, s_req_col, s_req_wdata, s_rsp_rdata;
  wire group_cmd_valid, group_cmd_ready, group_cmd_write, group_cmd_expert;
  wire [31:0] group_epoch, group_layer, group_row, group_base;
  wire [8:0] group_count;
  wire group_in_valid, group_in_ready, group_out_valid, group_out_ready;
  wire signed [31:0] group_in_q16, group_out_q16;
  wire [6:0] group_out_index;
  wire group_out_last, group_done, group_error;
  wire f_req_valid, f_req_ready, f_req_write, f_rsp_valid, f_rsp_ready, f_rsp_error;
  wire [3:0] f_req_kind;
  wire [2:0] f_req_proj;
  wire [31:0] f_req_layer, f_req_row, f_req_col, f_req_wdata, f_rsp_rdata;
  reg [31:0] cache_reads, cache_writes, expert_reads, other_reads, other_writes;
  reg [31:0] cache_payload_reads, cache_payload_writes, cache_scales;
  reg [31:0] expert_payload_reads, expert_scales;
  wire shared_event, prefetch_event;
  wire [31:0] cache_dense_increment, expert_dense_increment;
  integer b;

  anvil_d2_parameters #(
    .MODEL_MODE(MODEL_MODE),.NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
    .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
    .KV_LORA_RANK(KV_LORA_RANK),.QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),
    .QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),.V_HEAD_DIM(V_HEAD_DIM),
    .ROUTED_EXPERTS(ROUTED_EXPERTS),.TOP_K(TOP_K),.SHARED_EXPERTS(SHARED_EXPERTS),
    .MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),.FIRST_DENSE_LAYERS(FIRST_DENSE_LAYERS),
    .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),.BANKS(BANKS),
    .QUEUE_DEPTH(QUEUE_DEPTH),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS),
    .GROUP_SIZE(GROUP_SIZE),.MTP_K(MTP_K)
  ) parameters_ok ();

  anvil_d2_mtp_engine #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.KV_LORA_RANK(KV_LORA_RANK),
    .QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),.QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),
    .V_HEAD_DIM(V_HEAD_DIM),.ROUTED_EXPERTS(ROUTED_EXPERTS),.TOP_K(TOP_K),
    .SHARED_EXPERTS(SHARED_EXPERTS),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
    .FIRST_DENSE_LAYERS(FIRST_DENSE_LAYERS),.VOCAB_SIZE(VOCAB_SIZE),
    .MAX_SEQ_LEN(MAX_SEQ_LEN),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS),
    .MTP_K(MTP_K),.ENABLE(NATIVE_ENABLED)
  ) mtp (
    .clk(clk),.rst_n(rst_n),.cancel(cancel),
    .token_valid(token_valid && NATIVE_ENABLED),.token_ready(engine_ready),
    .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),.token_phase(token_phase),
    .mtp_enable(mtp_enable),.fp8_enable(fp8_enable),.generation_enable(generation_enable),
    .generation_limit(generation_limit),.eos_token(eos_token),
    .logit_valid(engine_logit_valid),.logit_ready(logit_ready),
    .logit_index(engine_logit_index),.logit_data(engine_logit_data),
    .spec_valid(engine_spec_valid),.spec_ready(spec_ready),.spec_token(engine_spec_token),
    .spec_pos(engine_spec_pos),.spec_last(engine_spec_last),
    .spec_count(engine_spec_count),.spec_accepted(engine_spec_accepted),
    .done(engine_done),.error(engine_error),.cancel_done(engine_cancel_done),.idle(engine_idle),
    .generation_active(generation_active),.accepted_retire(accepted_retire),
    .rejected_block(rejected_block),.verification_active(verification_active),
    .proposed_increment(proposed_increment),.transport_flush(engine_flush),
    .active_fp8(active_fp8),.active_epoch(epoch),
    .transport_idle(adapter_idle && service_idle && scheduler_idle),
    .transport_drained(scheduler_drained),
    .transport_fault(adapter_fault || service_fault || scheduler_fault),
    .c_req_valid(s_req_valid),.c_req_ready(s_req_ready),.c_req_write(s_req_write),
    .c_req_kind(s_req_kind),.c_req_layer(s_req_layer),.c_req_proj(s_req_proj),
    .c_req_row(s_req_row),.c_req_col(s_req_col),.c_req_wdata(s_req_wdata),
    .c_rsp_valid(s_rsp_valid),.c_rsp_ready(s_rsp_ready),.c_rsp_error(s_rsp_error),
    .c_rsp_rdata(s_rsp_rdata),
    .shared_busy(shared_event),.prefetch_busy(prefetch_event),
    .cache_dense_increment(cache_dense_increment),.expert_dense_increment(expert_dense_increment)
  );
  anvil_d2_fp8_mla_moe fp8 (
    .clk(clk),.rst_n(rst_n),.flush(engine_flush || !NATIVE_ENABLED),
    .cmd_valid(group_cmd_valid),.cmd_ready(group_cmd_ready),
    .cmd_write(group_cmd_write),.cmd_expert(group_cmd_expert),.cmd_prefetch(1'b0),
    .cmd_epoch(group_epoch),.cmd_layer(group_layer),.cmd_row(group_row),
    .cmd_base_col(group_base),.cmd_count(group_count),
    .in_valid(group_in_valid),.in_ready(group_in_ready),.in_q16(group_in_q16),
    .out_valid(group_out_valid),.out_ready(group_out_ready),.out_q16(group_out_q16),
    .out_fp32(),.out_bf16(),.out_index(group_out_index),.out_last(group_out_last),
    .done(group_done),.error(group_error),.fault(service_fault),.idle(service_idle),
    .c_req_valid(f_req_valid),.c_req_ready(f_req_ready),.c_req_write(f_req_write),
    .c_req_kind(f_req_kind),.c_req_layer(f_req_layer),.c_req_proj(f_req_proj),
    .c_req_row(f_req_row),.c_req_col(f_req_col),.c_req_wdata(f_req_wdata),
    .c_rsp_valid(f_rsp_valid),.c_rsp_ready(f_rsp_ready),.c_rsp_rdata(f_rsp_rdata),.c_rsp_error(f_rsp_error)
  );
  anvil_d2_csr #(.MODEL_MODE(MODEL_MODE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)) csr (
    .clk(clk),.rst_n(rst_n),.csr_valid(csr_valid),.csr_write(csr_write),
    .csr_addr(csr_addr),.csr_wdata(csr_wdata),.csr_wstrb(csr_wstrb),.csr_rsp_ready(csr_rsp_ready),
    .csr_ready(csr_ready),.csr_rsp_valid(csr_rsp_valid),.csr_rdata(csr_rdata),.csr_error(csr_error),
    .work_busy(work_busy),.token_accept(accepting),.token_complete(done || cancel_done),
    .token_error(done && error),.reasoning_active(reasoning_active),
    .shared_busy(shared_event),.prefetch_busy(prefetch_event),
    .cache_read_bytes(cache_reads),.cache_write_bytes(cache_writes),
    .cache_dense_equiv_bytes(cache_dense_increment),.expert_read_bytes(expert_reads),
    .expert_dense_equiv_bytes(expert_dense_increment),.other_read_bytes(other_reads),
    .other_write_bytes(other_writes),.generation_active(generation_active),
    .generated_retire(spec_valid && spec_ready),.accepted_retire(accepted_retire),
    .rejected_block(rejected_block),.proposed_increment(proposed_increment),
    .cache_payload_read_bytes(cache_payload_reads),.cache_payload_write_bytes(cache_payload_writes),
    .cache_scale_bytes(cache_scales),.expert_payload_read_bytes(expert_payload_reads),
    .expert_scale_bytes(expert_scales),.verification_active(verification_active),
    .domain_select(selected_domain),.think_begin_token(think_begin_token),
    .think_end_token(think_end_token),.mtp_enable(mtp_enable),.fp8_enable(fp8_enable),
    .generation_enable(generation_enable),.generation_limit(generation_limit),.eos_token(eos_token)
  );
  always @* begin
    cache_reads=0; cache_writes=0; expert_reads=0; other_reads=0; other_writes=0;
    cache_payload_reads=0; cache_payload_writes=0; cache_scales=0;
    expert_payload_reads=0; expert_scales=0;
    for (b=0;b<SB;b=b+1) begin
      if (rst_n && mem_req_valid[b] && mem_req_ready[b]) begin
        if (MODEL_MODE==0 && mem_req_proj[b*3+:3]==3 &&
            (mem_req_kind[b*4+:4]==15 || mem_req_kind[b*4+:4]==13 || mem_req_kind[b*4+:4]==14)) begin
          if (mem_req_write[b]) cache_writes=cache_writes+32'd4;
          else cache_reads=cache_reads+32'd4;
          if (mem_req_kind[b*4+:4]==14) cache_scales=cache_scales+32'd4;
          else if (mem_req_kind[b*4+:4]==13 || mem_req_col[b*32+:32]<KV_LORA_RANK) begin
            if (mem_req_write[b]) cache_payload_writes=cache_payload_writes+32'd4;
            else cache_payload_reads=cache_payload_reads+32'd4;
          end
        end else if (MODEL_MODE==0 && mem_req_proj[b*3+:3]==5 && !mem_req_write[b] &&
            (mem_req_kind[b*4+:4]==15 || mem_req_kind[b*4+:4]==12 ||
             mem_req_kind[b*4+:4]==13 || mem_req_kind[b*4+:4]==14)) begin
          expert_reads=expert_reads+32'd4;
          if (mem_req_kind[b*4+:4]==14) expert_scales=expert_scales+32'd4;
          else if (mem_req_kind[b*4+:4]==13 ||
              (mem_req_row[b*32+25+:7]<ROUTED_EXPERTS && mem_req_row[b*32+23+:2]!=3))
            expert_payload_reads=expert_payload_reads+32'd4;
        end else if (mem_req_write[b]) other_writes=other_writes+32'd4;
        else other_reads=other_reads+32'd4;
      end
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin reasoning<=0; token_busy<=0; end
    else begin
      if (accepting) begin reasoning<=reasoning_for_token; token_busy<=1; end
      if (spec_valid && spec_ready) begin
        if (spec_token==think_end_token) reasoning<=0;
        else if (spec_token==think_begin_token) reasoning<=1;
      end
      if (cancel || (done && error)) reasoning<=0;
      if (done || cancel_done) token_busy<=0;
    end
  end
  generate
    if (NATIVE_ENABLED) begin: native
      wire [29:0] c_req_valid, c_req_ready, c_req_write, c_rsp_valid, c_rsp_ready, c_rsp_error;
      wire [119:0] c_req_kind;
      wire [89:0] c_req_proj;
      wire [959:0] c_req_layer, c_req_row, c_req_col, c_req_wdata, c_rsp_rdata;
      assign token_ready=engine_ready;
      assign logit_valid=engine_logit_valid;
      assign logit_index=engine_logit_index;
      assign logit_data=engine_logit_data;
      assign done=engine_done;
      assign error=engine_error;
      assign cancel_done=engine_cancel_done;
      assign spec_valid=engine_spec_valid;
      assign spec_token=engine_spec_token;
      assign spec_pos=engine_spec_pos;
      assign spec_last=engine_spec_last;
      assign spec_count=engine_spec_count;
      assign spec_accepted=engine_spec_accepted;
      assign work_busy=!engine_idle;
      assign c_req_valid[29]=f_req_valid;
      assign c_req_write[29]=f_req_write;
      assign c_req_kind[116+:4]=f_req_kind;
      assign c_req_layer[928+:32]=f_req_layer;
      assign c_req_proj[87+:3]=f_req_proj;
      assign c_req_row[928+:32]=f_req_row;
      assign c_req_col[928+:32]=f_req_col;
      assign c_req_wdata[928+:32]=f_req_wdata;
      assign f_req_ready=c_req_ready[29];
      assign f_rsp_valid=c_rsp_valid[29];
      assign f_rsp_error=c_rsp_error[29];
      assign f_rsp_rdata=c_rsp_rdata[928+:32];
      assign c_rsp_ready[29]=f_rsp_ready;
      anvil_d2_fp8_adapter #(
        .CLIENTS(29),.NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
        .KV_LORA_RANK(KV_LORA_RANK),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
        .ROUTED_EXPERTS(ROUTED_EXPERTS),.MAX_SEQ_LEN(MAX_SEQ_LEN),.MTP_K(MTP_K)
      ) adapter (
        .clk(clk),.rst_n(rst_n),.flush(engine_flush),.fp8_enable(active_fp8),
        .epoch(epoch),.idle(adapter_idle),.fault(adapter_fault),
        .s_req_valid(s_req_valid),.s_req_ready(s_req_ready),.s_req_write(s_req_write),
        .s_req_kind(s_req_kind),.s_req_layer(s_req_layer),.s_req_proj(s_req_proj),
        .s_req_row(s_req_row),.s_req_col(s_req_col),.s_req_wdata(s_req_wdata),
        .s_rsp_valid(s_rsp_valid),.s_rsp_ready(s_rsp_ready),.s_rsp_error(s_rsp_error),
        .s_rsp_rdata(s_rsp_rdata),.c_req_valid(c_req_valid[28:0]),
        .c_req_ready(c_req_ready[28:0]),.c_req_write(c_req_write[28:0]),
        .c_req_kind(c_req_kind[115:0]),.c_req_layer(c_req_layer[927:0]),
        .c_req_proj(c_req_proj[86:0]),.c_req_row(c_req_row[927:0]),
        .c_req_col(c_req_col[927:0]),.c_req_wdata(c_req_wdata[927:0]),
        .c_rsp_valid(c_rsp_valid[28:0]),.c_rsp_ready(c_rsp_ready[28:0]),
        .c_rsp_error(c_rsp_error[28:0]),.c_rsp_rdata(c_rsp_rdata[927:0]),
        .group_cmd_valid(group_cmd_valid),.group_cmd_ready(group_cmd_ready),
        .group_cmd_write(group_cmd_write),.group_cmd_expert(group_cmd_expert),
        .group_cmd_epoch(group_epoch),.group_cmd_layer(group_layer),.group_cmd_row(group_row),
        .group_cmd_base_col(group_base),.group_cmd_count(group_count),
        .group_in_valid(group_in_valid),.group_in_ready(group_in_ready),.group_in_q16(group_in_q16),
        .group_out_valid(group_out_valid),.group_out_ready(group_out_ready),
        .group_out_q16(group_out_q16),.group_out_index(group_out_index),
        .group_out_last(group_out_last),.group_done(group_done),.group_error(group_error)
      );
      anvil_d2_bank_scheduler #(.BANKS(BANKS),.CLIENTS(30),.QUEUE_DEPTH(QUEUE_DEPTH)) scheduler (
        .clk(clk),.rst_n(rst_n),.flush(engine_flush),
        .idle(scheduler_idle),.drain_done(scheduler_drained),.fault(scheduler_fault),
        .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
        .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
        .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
        .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),.c_rsp_error(c_rsp_error),
        .c_rsp_rdata(c_rsp_rdata),.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
        .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),
        .mem_req_proj(mem_req_proj),.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),
        .mem_req_wdata(mem_req_wdata),.mem_req_tag(mem_req_tag),
        .mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),
        .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag)
      );
    end else begin: other_mode
      assign adapter_idle=0;
      assign adapter_fault=0;
      assign scheduler_idle=0;
      assign scheduler_drained=0;
      assign scheduler_fault=0;
      assign s_req_ready=0;
      assign s_rsp_valid=0;
      assign s_rsp_error=0;
      assign s_rsp_rdata=0;
      assign group_cmd_valid=0;
      assign group_cmd_write=0;
      assign group_cmd_expert=0;
      assign group_epoch=0;
      assign group_layer=0;
      assign group_row=0;
      assign group_base=0;
      assign group_count=0;
      assign group_in_valid=0;
      assign group_in_q16=0;
      assign group_out_ready=0;
      assign f_req_ready=0;
      assign f_rsp_valid=0;
      assign f_rsp_error=0;
      assign f_rsp_rdata=0;
      assign spec_valid=0;
      assign spec_token=0;
      assign spec_pos=0;
      assign spec_last=0;
      assign spec_count=0;
      assign spec_accepted=0;
      assign work_busy=token_busy || !token_ready;
      if (MODEL_MODE==1) begin: legacy
        anvil_q3_top #(
          .PROFILE(PROFILE),.NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
          .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
          .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
          .AWQ_BITS(AWQ_BITS),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),
          .BANKS(BANKS),.CACHE_MODE(CACHE_MODE),.INT4_ASYM(INT4_ASYM),
          .CACHE_BLOCK(CACHE_BLOCK),.QUEUE_DEPTH(QUEUE_DEPTH),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
        ) parent (
          .clk(clk),.rst_n(rst_n),.cancel(cancel),.token_valid(token_valid),.token_ready(token_ready),
          .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),.token_phase(token_phase),
          .logit_valid(logit_valid),.logit_ready(logit_ready),.logit_index(logit_index),
          .logit_data(logit_data),.done(done),.error(error),.cancel_done(cancel_done),
          .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
          .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
          .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
          .mem_req_tag(mem_req_tag),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),
          .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag)
        );
      end else begin: invalid_parameters
        assign token_ready=0;
        assign logit_valid=0;
        assign logit_index=0;
        assign logit_data=0;
        assign done=0;
        assign error=0;
        assign cancel_done=0;
        assign mem_req_valid=0;
        assign mem_req_write=0;
        assign mem_req_kind=0;
        assign mem_req_layer=0;
        assign mem_req_proj=0;
        assign mem_req_row=0;
        assign mem_req_col=0;
        assign mem_req_wdata=0;
        assign mem_req_tag=0;
        assign mem_rsp_ready=0;
      end
    end
  endgenerate
endmodule
