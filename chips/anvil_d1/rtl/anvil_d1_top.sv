module anvil_d1_top #(
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
  output wire csr_error
);
  wire accepting_token=token_valid && token_ready;
  wire [2:0] selected_domain;
  wire [31:0] think_begin_token, think_end_token;
  reg reasoning, csr_token_busy;
  wire reasoning_for_token=token_id!=think_end_token &&
    (token_id==think_begin_token || (!new_sequence && reasoning));
  wire reasoning_active=rst_n && !cancel && !(done && error) &&
    (accepting_token ? reasoning_for_token : csr_token_busy && reasoning);
  wire shared_event, prefetch_event;
  wire [31:0] cache_dense_increment, expert_dense_increment;
  reg [5:0] cache_reads, cache_writes, expert_reads, other_reads, other_writes;
  integer b;
  always @* begin
    cache_reads=0; cache_writes=0; expert_reads=0; other_reads=0; other_writes=0;
    for (b=0;b<SB;b=b+1) begin
      if (rst_n && mem_req_valid[b] && mem_req_ready[b]) begin
        if (MODEL_MODE==0 && mem_req_kind[b*4+:4]==15 && mem_req_proj[b*3+:3]==3) begin
          if (mem_req_write[b]) cache_writes=cache_writes+6'd4;
          else cache_reads=cache_reads+6'd4;
        end else if (MODEL_MODE==0 && mem_req_kind[b*4+:4]==15 &&
            mem_req_proj[b*3+:3]==5 && !mem_req_write[b]) expert_reads=expert_reads+6'd4;
        else if (mem_req_write[b]) other_writes=other_writes+6'd4;
        else other_reads=other_reads+6'd4;
      end
    end
  end
  anvil_d1_csr_perf #(.VOCAB_SIZE(VOCAB_SIZE)) performance (
    .clk(clk),.rst_n(rst_n),.csr_valid(csr_valid),.csr_write(csr_write),
    .csr_addr(csr_addr),.csr_wdata(csr_wdata),.csr_wstrb(csr_wstrb),
    .csr_rsp_ready(csr_rsp_ready),.csr_ready(csr_ready),.csr_rsp_valid(csr_rsp_valid),
    .csr_rdata(csr_rdata),.csr_error(csr_error),
    .token_accept(accepting_token),.token_complete(done || cancel_done),
    .token_error(done && error),.reasoning_active(reasoning_active),
    .shared_busy(shared_event),.prefetch_busy(prefetch_event),.domain_id(selected_domain),
    .cache_read_bytes({26'd0,cache_reads}),.cache_write_bytes({26'd0,cache_writes}),
    .cache_dense_equiv_bytes(cache_dense_increment),
    .expert_read_bytes({26'd0,expert_reads}),.expert_dense_equiv_bytes(expert_dense_increment),
    .other_read_bytes({26'd0,other_reads}),.other_write_bytes({26'd0,other_writes}),
    .domain_select(selected_domain),.think_begin_token(think_begin_token),
    .think_end_token(think_end_token)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin reasoning<=0; csr_token_busy<=0; end
    else begin
      if (accepting_token) begin reasoning<=reasoning_for_token; csr_token_busy<=1; end
      if (cancel || (done && error)) reasoning<=0;
      if (done || cancel_done) csr_token_busy<=0;
    end
  end
  generate
    if (MODEL_MODE==1) begin: legacy
      assign shared_event=1'b0;
      assign prefetch_event=1'b0;
      assign cache_dense_increment=32'd0;
      assign expert_dense_increment=32'd0;
      anvil_q3_top #(
        .PROFILE(PROFILE),.NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
        .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
        .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
        .AWQ_BITS(AWQ_BITS),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),
        .BANKS(BANKS),.CACHE_MODE(CACHE_MODE),.INT4_ASYM(INT4_ASYM),
        .CACHE_BLOCK(CACHE_BLOCK),.QUEUE_DEPTH(QUEUE_DEPTH),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
      ) parent (
        .clk(clk),.rst_n(rst_n),.cancel(cancel),
        .token_valid(token_valid),.token_ready(token_ready),
        .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),.token_phase(token_phase),
        .logit_valid(logit_valid),.logit_ready(logit_ready),
        .logit_index(logit_index),.logit_data(logit_data),.done(done),.error(error),.cancel_done(cancel_done),
        .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
        .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),
        .mem_req_proj(mem_req_proj),.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),
        .mem_req_wdata(mem_req_wdata),.mem_req_tag(mem_req_tag),
        .mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),
        .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag)
      );
    end else if (MODEL_MODE==0) begin: native
      localparam IDLE=0, SEQUENCE_FLUSH=1, SEQUENCE_DRAIN=2, EMBED=3, EMBED_WAIT=4;
      localparam DECODER=5, DECODER_WAIT=6, FINAL_NORM=7, FINAL_NORM_WAIT=8;
      localparam PROJECT=9, PROJECT_WAIT=10, COMPLETE=11;
      localparam ABORT_FLUSH=12, ABORT_DRAIN=13, CANCEL_COMPLETE=14;
      reg [3:0] state;
      reg armed, failed, sequence_valid, active_token, cancelled_active, cancel_pending;
      reg phase, decoding;
      reg [31:0] token, position, next_position, layer, epoch;
      wire scheduler_idle, scheduler_drained, scheduler_fault;
      wire scheduler_flush=cancel || state==SEQUENCE_FLUSH || state==ABORT_FLUSH;
      wire core_flush=cancel || state==SEQUENCE_FLUSH || state==SEQUENCE_DRAIN ||
        state==ABORT_FLUSH || state==ABORT_DRAIN || state==CANCEL_COMPLETE ||
        (state==COMPLETE && failed);
      wire decoder_ready, decoder_done, decoder_error;
      wire norm_ready, norm_done, norm_error, io_ready, io_done, io_error;
      wire io_logit_valid;
      wire [31:0] io_logit_index;
      wire signed [31:0] io_logit_data;
      wire operation_fault=scheduler_fault || (decoder_done && decoder_error) ||
        (norm_done && norm_error) || (io_done && io_error);
      wire last_logit=logit_valid && logit_ready && logit_index==VOCAB_SIZE-1;
      wire [6:0] c_req_valid, c_req_ready, c_req_write, c_rsp_valid, c_rsp_ready, c_rsp_error;
      wire [27:0] c_req_kind;
      wire [20:0] c_req_proj;
      wire [223:0] c_req_layer, c_req_row, c_req_col, c_req_wdata, c_rsp_rdata;
      wire [63:0] kv_reads, kv_writes, kv_dense, expert_bytes, expert_dense;
      wire [63:0] shared_cycles, prefetch_cycles, overlap;
      reg [63:0] previous_shared, previous_prefetch;
      wire mla_complete, moe_complete;
      assign shared_event=rst_n && !core_flush && shared_cycles>previous_shared;
      assign prefetch_event=rst_n && !core_flush && prefetch_cycles>previous_prefetch;
      assign cache_dense_increment=mla_complete ? kv_dense[31:0] : 32'd0;
      assign expert_dense_increment=moe_complete ? expert_dense[31:0] : 32'd0;
      assign token_ready=rst_n && armed && !cancel && !scheduler_fault &&
        state==IDLE && scheduler_idle;
      assign logit_valid=rst_n && !core_flush && state==PROJECT_WAIT && io_logit_valid;
      assign logit_index=logit_valid ? io_logit_index : 32'd0;
      assign logit_data=logit_valid ? io_logit_data : 32'sd0;
      assign done=rst_n && !cancel && (state==COMPLETE ||
        (state==CANCEL_COMPLETE && cancelled_active));
      assign error=done && failed;
      assign cancel_done=rst_n && !cancel && state==CANCEL_COMPLETE;
      anvil_d1_parameters #(
        .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
        .NUM_Q_HEADS(NUM_Q_HEADS),.KV_LORA_RANK(KV_LORA_RANK),
        .QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),.QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),
        .V_HEAD_DIM(V_HEAD_DIM),.ROUTED_EXPERTS(ROUTED_EXPERTS),.TOP_K(TOP_K),
        .SHARED_EXPERTS(SHARED_EXPERTS),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
        .FIRST_DENSE_LAYERS(FIRST_DENSE_LAYERS),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),
        .BANKS(BANKS),.QUEUE_DEPTH(QUEUE_DEPTH),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
      ) parameters_ok ();
      anvil_d1_decoder_layer #(
        .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
        .NUM_Q_HEADS(NUM_Q_HEADS),.KV_LORA_RANK(KV_LORA_RANK),
        .QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),.QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),
        .V_HEAD_DIM(V_HEAD_DIM),.ROUTED_EXPERTS(ROUTED_EXPERTS),.TOP_K(TOP_K),
        .SHARED_EXPERTS(SHARED_EXPERTS),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
        .FIRST_DENSE_LAYERS(FIRST_DENSE_LAYERS),.MAX_SEQ_LEN(MAX_SEQ_LEN),
        .TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
      ) decoder (
        .clk(clk),.rst_n(rst_n),.flush(core_flush),
        .cmd_valid(state==DECODER),.cmd_ready(decoder_ready),
        .cmd_epoch(epoch),.cmd_layer(layer),.cmd_pos(position),.cmd_phase(phase),
        .done(decoder_done),.error(decoder_error),
        .kv_read_bytes(kv_reads),.kv_write_bytes(kv_writes),.kv_dense_equiv_bytes(kv_dense),
        .expert_dma_bytes(expert_bytes),.expert_dense_equiv_bytes(expert_dense),
        .shared_busy_cycles(shared_cycles),.prefetch_busy_cycles(prefetch_cycles),
        .overlap_cycles(overlap),.mla_complete(mla_complete),.moe_complete(moe_complete),
        .c_req_valid(c_req_valid[0+:5]),.c_req_ready(c_req_ready[0+:5]),
        .c_req_write(c_req_write[0+:5]),.c_req_kind(c_req_kind[0+:20]),
        .c_req_layer(c_req_layer[0+:160]),.c_req_proj(c_req_proj[0+:15]),
        .c_req_row(c_req_row[0+:160]),.c_req_col(c_req_col[0+:160]),
        .c_req_wdata(c_req_wdata[0+:160]),
        .c_rsp_valid(c_rsp_valid[0+:5]),.c_rsp_ready(c_rsp_ready[0+:5]),
        .c_rsp_rdata(c_rsp_rdata[0+:160]),.c_rsp_error(c_rsp_error[0+:5])
      );
      anvil_d1_rmsnorm #(
        .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
      ) final_normalization (
        .clk(clk),.rst_n(rst_n),.flush(core_flush),
        .cmd_valid(state==FINAL_NORM),.cmd_ready(norm_ready),
        .cmd_layer(32'd0),.cmd_pos(position),.cmd_mode(2'd2),.done(norm_done),.error(norm_error),
        .mem_req_valid(c_req_valid[5]),.mem_req_ready(c_req_ready[5]),.mem_req_write(c_req_write[5]),
        .mem_req_kind(c_req_kind[20+:4]),.mem_req_layer(c_req_layer[160+:32]),
        .mem_req_proj(c_req_proj[15+:3]),.mem_req_row(c_req_row[160+:32]),
        .mem_req_col(c_req_col[160+:32]),.mem_req_wdata(c_req_wdata[160+:32]),
        .mem_rsp_valid(c_rsp_valid[5]),.mem_rsp_ready(c_rsp_ready[5]),
        .mem_rsp_rdata(c_rsp_rdata[160+:32]),.mem_rsp_error(c_rsp_error[5])
      );
      anvil_d1_token_io #(
        .HIDDEN_SIZE(HIDDEN_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
      ) token_io (
        .clk(clk),.rst_n(rst_n),.flush(core_flush),.cmd_valid(state==EMBED || state==PROJECT),
        .cmd_ready(io_ready),.cmd_project(state==PROJECT),.cmd_token(token),.cmd_pos(position),
        .done(io_done),.error(io_error),.logit_valid(io_logit_valid),
        .logit_ready(!core_flush && state==PROJECT_WAIT && logit_ready),
        .logit_index(io_logit_index),.logit_data(io_logit_data),
        .c_req_valid(c_req_valid[6]),.c_req_ready(c_req_ready[6]),.c_req_write(c_req_write[6]),
        .c_req_kind(c_req_kind[24+:4]),.c_req_layer(c_req_layer[192+:32]),
        .c_req_proj(c_req_proj[18+:3]),.c_req_row(c_req_row[192+:32]),
        .c_req_col(c_req_col[192+:32]),.c_req_wdata(c_req_wdata[192+:32]),
        .c_rsp_valid(c_rsp_valid[6]),.c_rsp_ready(c_rsp_ready[6]),
        .c_rsp_rdata(c_rsp_rdata[192+:32]),.c_rsp_error(c_rsp_error[6])
      );
      anvil_d1_bank_scheduler #(.BANKS(BANKS),.CLIENTS(7),.QUEUE_DEPTH(QUEUE_DEPTH)) bank_scheduler (
        .clk(clk),.rst_n(rst_n),.flush(scheduler_flush),
        .idle(scheduler_idle),.drain_done(scheduler_drained),.fault(scheduler_fault),
        .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
        .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
        .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
        .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),.c_rsp_rdata(c_rsp_rdata),
        .c_rsp_error(c_rsp_error),.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
        .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),
        .mem_req_proj(mem_req_proj),.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),
        .mem_req_wdata(mem_req_wdata),.mem_req_tag(mem_req_tag),
        .mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),.mem_rsp_ready(mem_rsp_ready),
        .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag)
      );
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin previous_shared<=0; previous_prefetch<=0; end
        else begin previous_shared<=shared_cycles; previous_prefetch<=prefetch_cycles; end
      end
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state<=IDLE; armed<=0; failed<=0; sequence_valid<=0; active_token<=0;
          cancelled_active<=0; cancel_pending<=0; phase<=0; decoding<=0;
          token<=0; position<=0; next_position<=0; layer<=0; epoch<=0;
        end else begin
          armed<=1;
          if (cancel) begin
            failed<=1; sequence_valid<=0; decoding<=0; cancel_pending<=1;
            cancelled_active<=cancelled_active || active_token; state<=ABORT_DRAIN;
          end else if (operation_fault && state!=ABORT_FLUSH && state!=ABORT_DRAIN &&
              state!=CANCEL_COMPLETE && !(state==COMPLETE && failed)) begin
            failed<=1; sequence_valid<=0; decoding<=0;
            cancelled_active<=0; cancel_pending<=0; state<=ABORT_FLUSH;
          end else case (state)
            IDLE: if (accepting_token) begin
              failed<=0; active_token<=1; cancelled_active<=0; cancel_pending<=0;
              if (token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN ||
                  (new_sequence && token_pos!=0) ||
                  (!new_sequence && (!sequence_valid || token_pos!=next_position ||
                    (decoding && !token_phase)))) begin
                failed<=1; sequence_valid<=0; decoding<=0; state<=ABORT_FLUSH;
              end else begin
                token<=token_id; position<=token_pos; phase<=token_phase; layer<=0;
                if (new_sequence) begin
                  sequence_valid<=1; next_position<=0; decoding<=token_phase;
                  epoch<=epoch+1'b1; state<=SEQUENCE_FLUSH;
                end else begin
                  if (token_phase) decoding<=1;
                  state<=EMBED;
                end
              end
            end
            SEQUENCE_FLUSH: state<=SEQUENCE_DRAIN;
            SEQUENCE_DRAIN: if (scheduler_drained) state<=EMBED;
            EMBED: if (io_ready) state<=EMBED_WAIT;
            EMBED_WAIT: if (io_done) state<=DECODER;
            DECODER: if (decoder_ready) state<=DECODER_WAIT;
            DECODER_WAIT: if (decoder_done) begin
              if (layer==NUM_LAYERS-1) state<=FINAL_NORM;
              else begin layer<=layer+1'b1; state<=DECODER; end
            end
            FINAL_NORM: if (norm_ready) state<=FINAL_NORM_WAIT;
            FINAL_NORM_WAIT: if (norm_done) state<=PROJECT;
            PROJECT: if (io_ready) state<=PROJECT_WAIT;
            PROJECT_WAIT: if (last_logit) begin
              active_token<=0; next_position<=position+1'b1; state<=COMPLETE;
            end
            COMPLETE: begin active_token<=0; state<=IDLE; end
            ABORT_FLUSH: state<=ABORT_DRAIN;
            ABORT_DRAIN: if (scheduler_drained) begin
              active_token<=0;
              if (cancel_pending) state<=CANCEL_COMPLETE;
              else state<=COMPLETE;
            end
            CANCEL_COMPLETE: begin cancelled_active<=0; state<=IDLE; end
            default: begin failed<=1; sequence_valid<=0; state<=ABORT_FLUSH; end
          endcase
        end
      end
    end else begin: invalid_mode
      initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: MODEL_MODE");
      assign token_ready=1'b0;
      assign logit_valid=1'b0;
      assign logit_index=32'd0;
      assign logit_data=32'sd0;
      assign done=1'b0;
      assign error=1'b0;
      assign cancel_done=1'b0;
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
      assign shared_event=1'b0;
      assign prefetch_event=1'b0;
      assign cache_dense_increment=32'd0;
      assign expert_dense_increment=32'd0;
    end
  endgenerate
endmodule
