module anvil_d2_target_lanes #(
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=10944,
  parameter integer NUM_Q_HEADS=16, KV_LORA_RANK=512, QK_NOPE_HEAD_DIM=128,
  parameter integer QK_ROPE_HEAD_DIM=64, V_HEAD_DIM=128,
  parameter integer ROUTED_EXPERTS=64, TOP_K=6, SHARED_EXPERTS=2,
  parameter integer MOE_INTERMEDIATE_SIZE=1408, FIRST_DENSE_LAYERS=1,
  parameter integer VOCAB_SIZE=102400, MAX_SEQ_LEN=32768, TILE_K=128, TILE_ROWS=8
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_first_pos,
  input wire [127:0] cmd_tokens,
  input wire [2:0] cmd_lanes,
  input wire cmd_phase, cmd_fp8, cmd_emit_logits,
  output wire result_valid,
  input wire result_ready,
  output wire [127:0] result_tokens,
  input wire commit_valid,
  output wire commit_ready,
  input wire [2:0] commit_count,
  output wire commit_done,
  input wire release_valid,
  output wire release_ready,
  input wire h_req_valid,
  output wire h_req_ready,
  input wire [1:0] h_req_lane,
  input wire [31:0] h_req_index,
  output wire h_rsp_valid,
  input wire h_rsp_ready,
  output wire signed [31:0] h_rsp_data,
  output wire h_rsp_error,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire fault, idle, verify_active,
  output wire shared_busy, prefetch_busy,
  output wire [31:0] cache_dense_increment, expert_dense_increment,
  output wire [28:0] c_req_valid, c_req_write,
  input wire [28:0] c_req_ready,
  output wire [115:0] c_req_kind,
  output wire [927:0] c_req_layer,
  output wire [86:0] c_req_proj,
  output wire [927:0] c_req_row, c_req_col, c_req_wdata,
  input wire [28:0] c_rsp_valid, c_rsp_error,
  output wire [28:0] c_rsp_ready,
  input wire [927:0] c_rsp_rdata
);
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=36 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=2048 && (HIDDEN_SIZE & 7)==0 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=11008 && (INTERMEDIATE_SIZE & 7)==0 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 && KV_LORA_RANK>=1 && KV_LORA_RANK<=512 &&
    QK_NOPE_HEAD_DIM>=1 && QK_NOPE_HEAD_DIM<=128 &&
    QK_ROPE_HEAD_DIM>=2 && QK_ROPE_HEAD_DIM<=64 && (QK_ROPE_HEAD_DIM & 1)==0 &&
    V_HEAD_DIM>=1 && V_HEAD_DIM<=128 && ROUTED_EXPERTS>=1 && ROUTED_EXPERTS<=64 &&
    TOP_K>=1 && TOP_K<=6 && TOP_K<=ROUTED_EXPERTS && SHARED_EXPERTS==2 &&
    MOE_INTERMEDIATE_SIZE>=8 && MOE_INTERMEDIATE_SIZE<=1408 &&
    (MOE_INTERMEDIATE_SIZE & 7)==0 &&
    FIRST_DENSE_LAYERS>=0 && FIRST_DENSE_LAYERS<=NUM_LAYERS &&
    VOCAB_SIZE>=4 && VOCAB_SIZE<=151936 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    TILE_K>=8 && TILE_K<=128 && (TILE_K & 7)==0 && TILE_ROWS>=1 && TILE_ROWS<=8;
  generate
    if (!LEGAL) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: target lane geometry");
      assign cmd_ready=0;
      assign result_valid=0;
      assign result_tokens=0;
      assign commit_ready=0;
      assign commit_done=0;
      assign release_ready=0;
      assign h_req_ready=0;
      assign h_rsp_valid=0;
      assign h_rsp_data=0;
      assign h_rsp_error=0;
      assign logit_valid=0;
      assign logit_index=0;
      assign logit_data=0;
      assign fault=0;
      assign idle=0;
      assign verify_active=0;
      assign shared_busy=0;
      assign prefetch_busy=0;
      assign cache_dense_increment=0;
      assign expert_dense_increment=0;
      assign c_req_valid=0;
      assign c_req_write=0;
      assign c_req_kind=0;
      assign c_req_layer=0;
      assign c_req_proj=0;
      assign c_req_row=0;
      assign c_req_col=0;
      assign c_req_wdata=0;
      assign c_rsp_ready=0;
    end else begin: target
      localparam IDLE=0, EMBED=1, EMBED_WAIT=2, LAYER_PREPARE=3;
      localparam DECODER=4, DECODER_WAIT=5, NORMALIZE=6, NORMALIZE_WAIT=7;
      localparam PROJECT=8, PROJECT_WAIT=9, RESULT=10, HOLD=11, FAULTED=12;
      reg [3:0] state;
      reg armed, failed, phase, fp8_mode, emit_logits, cache_finished, committed;
      reg h_pending, h_bad;
      reg [1:0] h_lane;
      reg [31:0] epoch, first_pos, layer;
      reg [127:0] tokens;
      reg [2:0] lanes;
      reg [3:0] issued, finished;
      reg [31:0] best_token [0:3];
      reg signed [31:0] best_logit [0:3];
      wire [3:0] lane_mask;
      wire [3:0] io_ready, io_done, io_error, norm_ready, norm_done, norm_error;
      wire [3:0] decoder_ready, decoder_done, decoder_error;
      wire [3:0] shared_events, prefetch_events;
      wire [127:0] cache_dense_events, expert_dense_events;
      wire [3:0] io_logit_valid, io_logit_ready, scratch_idle;
      wire [127:0] io_logit_index, io_logit_data;
      wire [3:0] cache_req_valid, cache_req_ready, cache_req_write;
      wire [127:0] cache_req_layer, cache_req_row, cache_req_col, cache_req_wdata;
      wire [3:0] cache_rsp_valid, cache_rsp_ready, cache_rsp_error;
      wire [127:0] cache_rsp_rdata;
      wire cache_layer_ready, cache_layer_done, cache_commit_ready, cache_commit_done;
      wire cache_fault, cache_idle;
      wire [3:0] h_local_ready, h_local_valid, h_local_error;
      wire [127:0] h_local_data;
      wire h_invalid=h_req_lane>=lanes || h_req_index>=HIDDEN_SIZE;
      wire enabled=rst_n && armed && !flush;
      wire child_flush=flush || failed;
      wire io_stage=state==EMBED || state==EMBED_WAIT || state==PROJECT || state==PROJECT_WAIT;
      wire decoder_stage=state==DECODER || state==DECODER_WAIT;
      wire norm_stage=state==NORMALIZE || state==NORMALIZE_WAIT;
      wire [3:0] stage_ready=decoder_stage ? decoder_ready :
        norm_stage ? norm_ready : io_ready;
      wire [3:0] stage_done=decoder_stage ? decoder_done :
        norm_stage ? norm_done : io_done;
      wire [3:0] issue_next=issued | (stage_ready & lane_mask);
      wire [3:0] finish_next=finished | (stage_done & lane_mask);
      wire stage_fault=(io_stage && |(io_done & io_error & lane_mask)) ||
        (decoder_stage && |(decoder_done & decoder_error & lane_mask)) ||
        (norm_stage && |(norm_done & norm_error & lane_mask)) || cache_fault;
      reg command_bad;
      integer n;

      for (genvar m=0;m<4;m=m+1) begin: masks
        assign lane_mask[m]=m<lanes;
        assign result_tokens[m*32+:32]=result_valid ? best_token[m] : 32'd0;
      end
      assign cmd_ready=enabled && !failed && state==IDLE && &scratch_idle && cache_idle;
      assign result_valid=enabled && !failed && state==RESULT;
      assign commit_ready=enabled && !failed && state==HOLD && !committed && cache_commit_ready;
      assign commit_done=enabled && !failed && state==HOLD && cache_commit_done;
      assign release_ready=enabled && !failed && state==HOLD && committed &&
        !h_pending && &scratch_idle && cache_idle;
      assign h_req_ready=enabled && !failed && state==HOLD && !h_pending &&
        (h_invalid || h_local_ready[h_req_lane]);
      assign h_rsp_valid=enabled && !failed && h_pending && (h_bad || h_local_valid[h_lane]);
      assign h_rsp_error=h_rsp_valid && (h_bad || h_local_error[h_lane]);
      assign h_rsp_data=h_rsp_valid && !h_rsp_error ? $signed(h_local_data[h_lane*32+:32]) : 32'sd0;
      assign logit_valid=enabled && !failed && emit_logits &&
        state==PROJECT_WAIT && io_logit_valid[0];
      assign logit_index=logit_valid ? io_logit_index[0+:32] : 32'd0;
      assign logit_data=logit_valid ? $signed(io_logit_data[0+:32]) : 32'sd0;
      assign fault=enabled && failed;
      assign idle=cmd_ready;
      assign verify_active=enabled && !failed && decoder_stage;
      assign shared_busy=enabled && !failed && |shared_events;
      assign prefetch_busy=enabled && !failed && |prefetch_events;
      assign cache_dense_increment=cache_dense_events[0+:32]+cache_dense_events[32+:32]+
        cache_dense_events[64+:32]+cache_dense_events[96+:32];
      assign expert_dense_increment=expert_dense_events[0+:32]+expert_dense_events[32+:32]+
        expert_dense_events[64+:32]+expert_dense_events[96+:32];

      always @* begin
        command_bad=cmd_lanes<1 || cmd_lanes>4 || cmd_first_pos>=MAX_SEQ_LEN ||
          cmd_first_pos+{29'd0,cmd_lanes}>MAX_SEQ_LEN ||
          (cmd_emit_logits && cmd_lanes!=1);
        for (n=0;n<4;n=n+1)
          if (n<cmd_lanes && cmd_tokens[n*32+:32]>=VOCAB_SIZE) command_bad=1;
      end

      for (genvar lane_number=0;lane_number<4;lane_number=lane_number+1) begin: lane
        localparam integer v=lane_number;
        wire [7:0] s_req_valid, s_req_ready, s_req_write, s_rsp_valid, s_rsp_ready, s_rsp_error;
        wire [31:0] s_req_kind;
        wire [23:0] s_req_proj;
        wire [255:0] s_req_layer, s_req_row, s_req_col, s_req_wdata, s_rsp_rdata;
        wire [7:0] x_req_valid, x_req_ready, x_req_write, x_rsp_valid, x_rsp_ready, x_rsp_error;
        wire [31:0] x_req_kind;
        wire [23:0] x_req_proj;
        wire [255:0] x_req_layer, x_req_row, x_req_col, x_req_wdata, x_rsp_rdata;
        reg cache_owned;
        reg [63:0] previous_shared, previous_prefetch;
        wire [63:0] shared_cycles, prefetch_cycles, kv_dense, expert_dense;
        wire mla_complete, moe_complete;
        assign shared_events[v]=lane_mask[v] && shared_cycles>previous_shared;
        assign prefetch_events[v]=lane_mask[v] && prefetch_cycles>previous_prefetch;
        assign cache_dense_events[v*32+:32]=enabled && mla_complete ? kv_dense[31:0] : 32'd0;
        assign expert_dense_events[v*32+:32]=enabled && moe_complete ? expert_dense[31:0] : 32'd0;
        wire cache_address=x_req_kind[4+:4]==15 && x_req_proj[3+:3]==3;
        wire io_command=enabled && !failed && lane_mask[v] && !issued[v] &&
          (state==EMBED || state==PROJECT);
        wire decoder_command=enabled && !failed && lane_mask[v] && !issued[v] && state==DECODER;
        wire norm_command=enabled && !failed && lane_mask[v] && !issued[v] && state==NORMALIZE;
        assign io_logit_ready[v]=enabled && !failed && state==PROJECT_WAIT &&
          (v==0 && emit_logits ? logit_ready : 1'b1);

        anvil_d1_decoder_layer #(
          .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
          .NUM_Q_HEADS(NUM_Q_HEADS),.KV_LORA_RANK(KV_LORA_RANK),
          .QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),.QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),
          .V_HEAD_DIM(V_HEAD_DIM),.ROUTED_EXPERTS(ROUTED_EXPERTS),.TOP_K(TOP_K),
          .SHARED_EXPERTS(SHARED_EXPERTS),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
          .FIRST_DENSE_LAYERS(FIRST_DENSE_LAYERS),.MAX_SEQ_LEN(MAX_SEQ_LEN),
          .TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
        ) decoder (
          .clk(clk),.rst_n(rst_n),.flush(child_flush),
          .cmd_valid(decoder_command),.cmd_ready(decoder_ready[v]),
          .cmd_epoch(epoch),.cmd_layer(layer),.cmd_pos(first_pos+v),.cmd_phase(phase),
          .done(decoder_done[v]),.error(decoder_error[v]),
          .kv_read_bytes(),.kv_write_bytes(),.kv_dense_equiv_bytes(kv_dense),
          .expert_dma_bytes(),.expert_dense_equiv_bytes(expert_dense),
          .shared_busy_cycles(shared_cycles),.prefetch_busy_cycles(prefetch_cycles),.overlap_cycles(),
          .mla_complete(mla_complete),.moe_complete(moe_complete),
          .c_req_valid(s_req_valid[0+:5]),.c_req_ready(s_req_ready[0+:5]),
          .c_req_write(s_req_write[0+:5]),.c_req_kind(s_req_kind[0+:20]),
          .c_req_layer(s_req_layer[0+:160]),.c_req_proj(s_req_proj[0+:15]),
          .c_req_row(s_req_row[0+:160]),.c_req_col(s_req_col[0+:160]),
          .c_req_wdata(s_req_wdata[0+:160]),
          .c_rsp_valid(s_rsp_valid[0+:5]),.c_rsp_ready(s_rsp_ready[0+:5]),
          .c_rsp_rdata(s_rsp_rdata[0+:160]),.c_rsp_error(s_rsp_error[0+:5])
        );
        anvil_d1_rmsnorm #(
          .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
        ) final_normalization (
          .clk(clk),.rst_n(rst_n),.flush(child_flush),
          .cmd_valid(norm_command),.cmd_ready(norm_ready[v]),.cmd_layer(32'd0),
          .cmd_pos(first_pos+v),.cmd_mode(2'd2),.done(norm_done[v]),.error(norm_error[v]),
          .mem_req_valid(s_req_valid[5]),.mem_req_ready(s_req_ready[5]),
          .mem_req_write(s_req_write[5]),.mem_req_kind(s_req_kind[20+:4]),
          .mem_req_layer(s_req_layer[160+:32]),.mem_req_proj(s_req_proj[15+:3]),
          .mem_req_row(s_req_row[160+:32]),.mem_req_col(s_req_col[160+:32]),
          .mem_req_wdata(s_req_wdata[160+:32]),
          .mem_rsp_valid(s_rsp_valid[5]),.mem_rsp_ready(s_rsp_ready[5]),
          .mem_rsp_rdata(s_rsp_rdata[160+:32]),.mem_rsp_error(s_rsp_error[5])
        );
        anvil_d1_token_io #(
          .HIDDEN_SIZE(HIDDEN_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
        ) token_io (
          .clk(clk),.rst_n(rst_n),.flush(child_flush),.cmd_valid(io_command),
          .cmd_ready(io_ready[v]),.cmd_project(state==PROJECT),
          .cmd_token(tokens[v*32+:32]),.cmd_pos(first_pos+v),
          .done(io_done[v]),.error(io_error[v]),.logit_valid(io_logit_valid[v]),
          .logit_ready(io_logit_ready[v]),.logit_index(io_logit_index[v*32+:32]),
          .logit_data(io_logit_data[v*32+:32]),
          .c_req_valid(s_req_valid[6]),.c_req_ready(s_req_ready[6]),
          .c_req_write(s_req_write[6]),.c_req_kind(s_req_kind[24+:4]),
          .c_req_layer(s_req_layer[192+:32]),.c_req_proj(s_req_proj[18+:3]),
          .c_req_row(s_req_row[192+:32]),.c_req_col(s_req_col[192+:32]),
          .c_req_wdata(s_req_wdata[192+:32]),
          .c_rsp_valid(s_rsp_valid[6]),.c_rsp_ready(s_rsp_ready[6]),
          .c_rsp_rdata(s_rsp_rdata[192+:32]),.c_rsp_error(s_rsp_error[6])
        );
        assign s_req_valid[7]=enabled && !failed && state==HOLD && !h_pending &&
          h_req_valid && !h_invalid && h_req_lane==v;
        assign s_req_write[7]=0;
        assign s_req_kind[28+:4]=4'd8;
        assign s_req_layer[224+:32]=0;
        assign s_req_proj[21+:3]=0;
        assign s_req_row[224+:32]=0;
        assign s_req_col[224+:32]=h_req_index;
        assign s_req_wdata[224+:32]=0;
        assign h_local_ready[v]=s_req_ready[7];
        assign h_local_valid[v]=s_rsp_valid[7];
        assign h_local_error[v]=s_rsp_error[7];
        assign h_local_data[v*32+:32]=s_rsp_rdata[224+:32];
        assign s_rsp_ready[7]=enabled && h_pending && !h_bad && h_lane==v && h_rsp_ready;

        anvil_d2_lane_memory #(
          .CLIENTS(8),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
          .NUM_Q_HEADS(NUM_Q_HEADS),.KV_LORA_RANK(KV_LORA_RANK),
          .QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
          .ROUTED_EXPERTS(ROUTED_EXPERTS)
        ) local_memory (
          .clk(clk),.rst_n(rst_n),.flush(child_flush),.idle(scratch_idle[v]),
          .s_req_valid(s_req_valid),.s_req_ready(s_req_ready),.s_req_write(s_req_write),
          .s_req_kind(s_req_kind),.s_req_layer(s_req_layer),.s_req_proj(s_req_proj),
          .s_req_row(s_req_row),.s_req_col(s_req_col),.s_req_wdata(s_req_wdata),
          .s_rsp_valid(s_rsp_valid),.s_rsp_ready(s_rsp_ready),.s_rsp_rdata(s_rsp_rdata),
          .s_rsp_error(s_rsp_error),
          .c_req_valid(x_req_valid),.c_req_ready(x_req_ready),.c_req_write(x_req_write),
          .c_req_kind(x_req_kind),.c_req_layer(x_req_layer),.c_req_proj(x_req_proj),
          .c_req_row(x_req_row),.c_req_col(x_req_col),.c_req_wdata(x_req_wdata),
          .c_rsp_valid(x_rsp_valid),.c_rsp_ready(x_rsp_ready),.c_rsp_rdata(x_rsp_rdata),
          .c_rsp_error(x_rsp_error)
        );
        assign cache_req_valid[v]=x_req_valid[1] && cache_address;
        assign cache_req_write[v]=x_req_write[1];
        assign cache_req_layer[v*32+:32]=x_req_layer[32+:32];
        assign cache_req_row[v*32+:32]=x_req_row[32+:32];
        assign cache_req_col[v*32+:32]=x_req_col[32+:32];
        assign cache_req_wdata[v*32+:32]=x_req_wdata[32+:32];
        assign cache_rsp_ready[v]=x_rsp_ready[1] && cache_owned;
        for (genvar p=0;p<7;p=p+1) begin: transport
          assign c_req_valid[v*7+p]=x_req_valid[p] && !(p==1 && cache_address);
          assign c_req_write[v*7+p]=c_req_valid[v*7+p] && x_req_write[p];
          assign c_req_kind[(v*7+p)*4+:4]=c_req_valid[v*7+p] ? x_req_kind[p*4+:4] : 4'd0;
          assign c_req_layer[(v*7+p)*32+:32]=c_req_valid[v*7+p] ? x_req_layer[p*32+:32] : 32'd0;
          assign c_req_proj[(v*7+p)*3+:3]=c_req_valid[v*7+p] ? x_req_proj[p*3+:3] : 3'd0;
          assign c_req_row[(v*7+p)*32+:32]=c_req_valid[v*7+p] ? x_req_row[p*32+:32] : 32'd0;
          assign c_req_col[(v*7+p)*32+:32]=c_req_valid[v*7+p] ? x_req_col[p*32+:32] : 32'd0;
          assign c_req_wdata[(v*7+p)*32+:32]=c_req_valid[v*7+p] ? x_req_wdata[p*32+:32] : 32'd0;
          assign x_req_ready[p]=p==1 && cache_address ? cache_req_ready[v] : c_req_ready[v*7+p];
          assign x_rsp_valid[p]=p==1 && cache_owned ? cache_rsp_valid[v] : c_rsp_valid[v*7+p];
          assign x_rsp_error[p]=p==1 && cache_owned ? cache_rsp_error[v] : c_rsp_error[v*7+p];
          assign x_rsp_rdata[p*32+:32]=p==1 && cache_owned ? cache_rsp_rdata[v*32+:32] :
            c_rsp_rdata[(v*7+p)*32+:32];
          assign c_rsp_ready[v*7+p]=x_rsp_ready[p] && !(p==1 && cache_owned);
        end
        assign x_req_ready[7]=0;
        assign x_rsp_valid[7]=0;
        assign x_rsp_error[7]=0;
        assign x_rsp_rdata[224+:32]=0;
        always @(posedge clk or negedge rst_n) begin
          if (!rst_n) begin cache_owned<=0; previous_shared<=0; previous_prefetch<=0; end
          else if (child_flush) begin cache_owned<=0; previous_shared<=0; previous_prefetch<=0; end
          else begin
            previous_shared<=shared_cycles; previous_prefetch<=prefetch_cycles;
            if (cache_rsp_valid[v] && cache_rsp_ready[v]) cache_owned<=0;
            if (cache_req_valid[v] && cache_req_ready[v]) cache_owned<=1;
          end
        end
      end

      anvil_d2_verify_cache #(
        .NUM_LAYERS(NUM_LAYERS),.KV_LORA_RANK(KV_LORA_RANK),
        .QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)
      ) candidate_cache (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),
        .layer_valid(enabled && !failed && state==LAYER_PREPARE),.layer_ready(cache_layer_ready),
        .layer_epoch(epoch),.layer_index(layer),.layer_first_pos(first_pos),
        .layer_lanes(lanes),.layer_fp8(fp8_mode),.layer_done(cache_layer_done),
        .commit_valid(enabled && !failed && state==HOLD && !committed && commit_valid),
        .commit_ready(cache_commit_ready),.commit_count(commit_count),.commit_done(cache_commit_done),
        .fault(cache_fault),.idle(cache_idle),
        .s_req_valid(cache_req_valid),.s_req_ready(cache_req_ready),.s_req_write(cache_req_write),
        .s_req_layer(cache_req_layer),.s_req_row(cache_req_row),.s_req_col(cache_req_col),
        .s_req_wdata(cache_req_wdata),.s_rsp_valid(cache_rsp_valid),.s_rsp_ready(cache_rsp_ready),
        .s_rsp_error(cache_rsp_error),.s_rsp_rdata(cache_rsp_rdata),
        .c_req_valid(c_req_valid[28]),.c_req_ready(c_req_ready[28]),.c_req_write(c_req_write[28]),
        .c_req_kind(c_req_kind[112+:4]),.c_req_layer(c_req_layer[896+:32]),
        .c_req_proj(c_req_proj[84+:3]),.c_req_row(c_req_row[896+:32]),
        .c_req_col(c_req_col[896+:32]),.c_req_wdata(c_req_wdata[896+:32]),
        .c_rsp_valid(c_rsp_valid[28]),.c_rsp_ready(c_rsp_ready[28]),
        .c_rsp_error(c_rsp_error[28]),.c_rsp_rdata(c_rsp_rdata[896+:32])
      );

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state<=IDLE; armed<=0; failed<=0; phase<=0; fp8_mode<=0; emit_logits<=0;
          cache_finished<=0; committed<=0; h_pending<=0; h_bad<=0; h_lane<=0;
          epoch<=0; first_pos<=0; layer<=0; tokens<=0; lanes<=0; issued<=0; finished<=0;
          for (integer r=0;r<4;r=r+1) begin best_token[r]<=0; best_logit[r]<=32'sh80000000; end
        end else begin
          armed<=1;
          if (flush) begin
            state<=IDLE; failed<=0; issued<=0; finished<=0; cache_finished<=0;
            committed<=0; h_pending<=0; h_bad<=0;
          end else if (!failed && stage_fault) begin
            failed<=1; state<=FAULTED; h_pending<=0;
          end else begin
            if (cache_layer_done) cache_finished<=1;
            if (cache_commit_done) committed<=1;
            if (h_req_valid && h_req_ready) begin h_pending<=1; h_lane<=h_req_lane; h_bad<=h_invalid; end
            if (h_rsp_valid && h_rsp_ready) begin h_pending<=0; h_bad<=0; end
            if (state==PROJECT_WAIT) begin
              for (integer r=0;r<4;r=r+1) begin
                if (lane_mask[r] && io_logit_valid[r] && io_logit_ready[r] &&
                    (io_logit_index[r*32+:32]==0 ||
                     $signed(io_logit_data[r*32+:32])>best_logit[r] ||
                     ($signed(io_logit_data[r*32+:32])==best_logit[r] &&
                      io_logit_index[r*32+:32]<best_token[r]))) begin
                  best_token[r]<=io_logit_index[r*32+:32];
                  best_logit[r]<=$signed(io_logit_data[r*32+:32]);
                end
              end
            end
            if (io_stage || decoder_stage || norm_stage) finished<=finish_next;
            case (state)
              IDLE: if (cmd_valid && cmd_ready) begin
                if (command_bad) begin failed<=1; state<=FAULTED; end
                else begin
                  epoch<=cmd_epoch; first_pos<=cmd_first_pos; tokens<=cmd_tokens;
                  lanes<=cmd_lanes; phase<=cmd_phase; fp8_mode<=cmd_fp8;
                  emit_logits<=cmd_emit_logits; layer<=0; issued<=0; finished<=0;
                  cache_finished<=0; committed<=0; state<=EMBED;
                  for (integer r=0;r<4;r=r+1) begin
                    best_token[r]<=0; best_logit[r]<=32'sh80000000;
                  end
                end
              end
              EMBED: begin
                issued<=issue_next;
                if ((issue_next & lane_mask)==lane_mask) state<=EMBED_WAIT;
              end
              EMBED_WAIT: if ((finish_next & lane_mask)==lane_mask) begin
                issued<=0; finished<=0; cache_finished<=0; state<=LAYER_PREPARE;
              end
              LAYER_PREPARE: if (cache_layer_ready) begin issued<=0; finished<=0; state<=DECODER; end
              DECODER: begin
                issued<=issue_next;
                if ((issue_next & lane_mask)==lane_mask) state<=DECODER_WAIT;
              end
              DECODER_WAIT: if ((finish_next & lane_mask)==lane_mask && cache_finished) begin
                issued<=0; finished<=0; cache_finished<=0;
                if (layer==NUM_LAYERS-1) state<=NORMALIZE;
                else begin layer<=layer+1'b1; state<=LAYER_PREPARE; end
              end
              NORMALIZE: begin
                issued<=issue_next;
                if ((issue_next & lane_mask)==lane_mask) state<=NORMALIZE_WAIT;
              end
              NORMALIZE_WAIT: if ((finish_next & lane_mask)==lane_mask) begin
                issued<=0; finished<=0; state<=PROJECT;
              end
              PROJECT: begin
                issued<=issue_next;
                if ((issue_next & lane_mask)==lane_mask) state<=PROJECT_WAIT;
              end
              PROJECT_WAIT: if ((finish_next & lane_mask)==lane_mask) state<=RESULT;
              RESULT: if (result_ready) state<=HOLD;
              HOLD: if (release_valid && release_ready) state<=IDLE;
              FAULTED: state<=FAULTED;
              default: begin failed<=1; h_pending<=0; state<=FAULTED; end
            endcase
          end
        end
      end
    end
  endgenerate
endmodule
