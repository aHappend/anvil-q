module anvil_q3_top #(
  parameter PROFILE=3,
  parameter NUM_LAYERS=PROFILE==1 ? 24 : PROFILE==2 ? 28 : 36,
  parameter HIDDEN_SIZE=PROFILE==1 ? 896 : PROFILE==2 ? 1536 : 2048,
  parameter INTERMEDIATE_SIZE=PROFILE==1 ? 4864 : PROFILE==2 ? 8960 : 11008,
  parameter NUM_Q_HEADS=PROFILE==1 ? 14 : PROFILE==2 ? 12 : 16,
  parameter NUM_KV_HEADS=2, HEAD_DIM=PROFILE==1 ? 64 : 128,
  parameter GROUP_SIZE=128, AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter BANKS=8, CACHE_MODE=0, INT4_ASYM=0, CACHE_BLOCK=1,
  parameter QUEUE_DEPTH=3, TILE_K=128, TILE_ROWS=8,
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
  input wire [SB*64-1:0] mem_rsp_tag
);
  localparam DC=SB+7, FN=DC, IO=DC+1, CLIENTS=DC+2;
  localparam IDLE=0, SEQUENCE_FLUSH=1, SEQUENCE_DRAIN=2, EMBED=3, EMBED_WAIT=4;
  localparam DECODER=5, DECODER_WAIT=6, FINAL_NORM=7, FINAL_NORM_WAIT=8;
  localparam PROJECT=9, PROJECT_WAIT=10, COMPLETE=11;
  localparam ABORT_FLUSH=12, ABORT_DRAIN=13, CANCEL_COMPLETE=14;
  reg [3:0] state;
  reg failed, sequence_valid, active_token, cancelled_active, cancel_pending;
  reg phase, decoding;
  reg [31:0] token, position, next_position, layer, epoch;
  reg [31:0] prefill_count, frozen_prefill_count;
  wire effective_phase=PROFILE!=1 && token_phase;
  wire scheduler_idle, scheduler_drained, scheduler_fault;
  wire scheduler_flush=cancel || state==SEQUENCE_FLUSH || state==ABORT_FLUSH;
  wire core_flush=cancel || state==SEQUENCE_FLUSH || state==SEQUENCE_DRAIN ||
    state==ABORT_FLUSH || state==ABORT_DRAIN || state==CANCEL_COMPLETE ||
    (state==COMPLETE && failed);
  wire decoder_ready, decoder_done, decoder_error;
  wire norm_ready, norm_done, norm_error;
  wire io_ready, io_done, io_error;
  wire io_logit_valid;
  wire [31:0] io_logit_index;
  wire signed [31:0] io_logit_data;
  wire operation_fault=scheduler_fault || (decoder_done && decoder_error) ||
    (norm_done && norm_error) || (io_done && io_error);
  wire accepting_token=token_valid && token_ready;
  wire last_logit=logit_valid && logit_ready && io_logit_index==VOCAB_SIZE-1;
  wire [CLIENTS-1:0] c_req_valid, c_req_ready, c_req_write;
  wire [CLIENTS*4-1:0] c_req_kind;
  wire [CLIENTS*32-1:0] c_req_layer;
  wire [CLIENTS*3-1:0] c_req_proj;
  wire [CLIENTS*32-1:0] c_req_row, c_req_col, c_req_wdata;
  wire [CLIENTS-1:0] c_rsp_valid, c_rsp_error, c_rsp_ready;
  wire [CLIENTS*32-1:0] c_rsp_rdata;

  anvil_q3_parameters #(
    .PROFILE(PROFILE),.NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
    .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),
    .HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),.AWQ_BITS(AWQ_BITS),.VOCAB_SIZE(VOCAB_SIZE),
    .MAX_SEQ_LEN(MAX_SEQ_LEN),.BANKS(BANKS),.CACHE_MODE(CACHE_MODE),.INT4_ASYM(INT4_ASYM),
    .CACHE_BLOCK(CACHE_BLOCK),.QUEUE_DEPTH(QUEUE_DEPTH),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
  ) parameters_ok ();

  assign token_ready=rst_n && !cancel && !scheduler_fault && state==IDLE && scheduler_idle;
  assign logit_valid=rst_n && !core_flush && state==PROJECT_WAIT && io_logit_valid;
  assign logit_index=rst_n ? io_logit_index : 32'd0;
  assign logit_data=rst_n ? io_logit_data : 32'sd0;
  assign done=rst_n && !cancel && (state==COMPLETE || (state==CANCEL_COMPLETE && cancelled_active));
  assign error=done && failed;
  assign cancel_done=rst_n && !cancel && state==CANCEL_COMPLETE;

  anvil_q3_decoder_layer #(
    .PROFILE(PROFILE),.BANKS(BANKS),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS),
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .GROUP_SIZE(GROUP_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_MODE(CACHE_MODE),
    .INT4_ASYM(INT4_ASYM),.CACHE_BLOCK(CACHE_BLOCK)
  ) decoder (
    .clk(clk),.rst_n(rst_n),.flush(core_flush),.cmd_valid(state==DECODER),
    .cmd_ready(decoder_ready),.cmd_epoch(epoch),.cmd_layer(layer),.cmd_pos(position),.cmd_phase(phase),
    .done(decoder_done),.error(decoder_error),
    .c_req_valid(c_req_valid[0+:DC]),.c_req_ready(c_req_ready[0+:DC]),
    .c_req_write(c_req_write[0+:DC]),.c_req_kind(c_req_kind[0+:DC*4]),
    .c_req_layer(c_req_layer[0+:DC*32]),.c_req_proj(c_req_proj[0+:DC*3]),
    .c_req_row(c_req_row[0+:DC*32]),.c_req_col(c_req_col[0+:DC*32]),.c_req_wdata(c_req_wdata[0+:DC*32]),
    .c_rsp_valid(c_rsp_valid[0+:DC]),.c_rsp_error(c_rsp_error[0+:DC]),
    .c_rsp_ready(c_rsp_ready[0+:DC]),.c_rsp_rdata(c_rsp_rdata[0+:DC*32])
  );
  anvil_q3_rmsnorm #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) final_norm (
    .clk(clk),.rst_n(rst_n),.flush(core_flush),.cmd_valid(state==FINAL_NORM),.cmd_ready(norm_ready),
    .cmd_layer(32'd0),.cmd_pos(position),.cmd_mode(2'd2),.done(norm_done),.error(norm_error),
    .mem_req_valid(c_req_valid[FN]),.mem_req_ready(c_req_ready[FN]),
    .mem_req_write(c_req_write[FN]),.mem_req_kind(c_req_kind[FN*4+:4]),
    .mem_req_layer(c_req_layer[FN*32+:32]),.mem_req_proj(c_req_proj[FN*3+:3]),
    .mem_req_row(c_req_row[FN*32+:32]),.mem_req_col(c_req_col[FN*32+:32]),.mem_req_wdata(c_req_wdata[FN*32+:32]),
    .mem_rsp_valid(c_rsp_valid[FN]),.mem_rsp_ready(c_rsp_ready[FN]),
    .mem_rsp_rdata(c_rsp_rdata[FN*32+:32]),.mem_rsp_error(c_rsp_error[FN])
  );
  anvil_q3_token_io #(
    .HIDDEN_SIZE(HIDDEN_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) token_io (
    .clk(clk),.rst_n(rst_n),.flush(core_flush),
    .cmd_valid(state==EMBED || state==PROJECT),.cmd_ready(io_ready),.cmd_project(state==PROJECT),
    .cmd_token(token),.cmd_pos(position),.done(io_done),.error(io_error),
    .logit_valid(io_logit_valid),.logit_ready(!core_flush && state==PROJECT_WAIT && logit_ready),
    .logit_index(io_logit_index),.logit_data(io_logit_data),
    .mem_req_valid(c_req_valid[IO]),.mem_req_ready(c_req_ready[IO]),
    .mem_req_write(c_req_write[IO]),.mem_req_kind(c_req_kind[IO*4+:4]),
    .mem_req_layer(c_req_layer[IO*32+:32]),.mem_req_proj(c_req_proj[IO*3+:3]),
    .mem_req_row(c_req_row[IO*32+:32]),.mem_req_col(c_req_col[IO*32+:32]),.mem_req_wdata(c_req_wdata[IO*32+:32]),
    .mem_rsp_valid(c_rsp_valid[IO]),.mem_rsp_ready(c_rsp_ready[IO]),
    .mem_rsp_rdata(c_rsp_rdata[IO*32+:32]),.mem_rsp_error(c_rsp_error[IO])
  );
  anvil_q3_bank_scheduler #(.BANKS(BANKS),.CLIENTS(CLIENTS),.QUEUE_DEPTH(QUEUE_DEPTH)) bank_scheduler (
    .clk(clk),.rst_n(rst_n),.flush(scheduler_flush),
    .idle(scheduler_idle),.drain_done(scheduler_drained),.fault(scheduler_fault),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
    .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
    .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
    .c_rsp_valid(c_rsp_valid),.c_rsp_error(c_rsp_error),.c_rsp_ready(c_rsp_ready),.c_rsp_rdata(c_rsp_rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),.mem_req_tag(mem_req_tag),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; sequence_valid<=PROFILE==1; active_token<=0;
      cancelled_active<=0; cancel_pending<=0; phase<=0; decoding<=0;
      token<=0; position<=0; next_position<=0; layer<=0; epoch<=0;
      prefill_count<=0; frozen_prefill_count<=0;
    end else if (cancel) begin
      failed<=1; sequence_valid<=0; cancelled_active<=active_token; cancel_pending<=1;
      decoding<=0; prefill_count<=0; frozen_prefill_count<=0; state<=ABORT_DRAIN;
    end else if (operation_fault && state!=ABORT_FLUSH && state!=ABORT_DRAIN &&
        state!=CANCEL_COMPLETE && !(state==COMPLETE && failed)) begin
      failed<=1; sequence_valid<=0; cancelled_active<=0; cancel_pending<=0;
      decoding<=0; prefill_count<=0; frozen_prefill_count<=0; state<=ABORT_FLUSH;
    end else case (state)
      IDLE: if (accepting_token) begin
        failed<=0; active_token<=1; cancelled_active<=0; cancel_pending<=0;
        if (token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN ||
            (new_sequence && token_pos!=0) ||
            (!new_sequence && (!sequence_valid || token_pos!=next_position ||
              (PROFILE!=1 && decoding && !effective_phase) ||
              (PROFILE!=1 && decoding && token_pos<frozen_prefill_count)))) begin
          failed<=1; sequence_valid<=0; decoding<=0; prefill_count<=0;
          frozen_prefill_count<=0; state<=ABORT_FLUSH;
        end else begin
          token<=token_id; position<=token_pos; phase<=effective_phase; layer<=0;
          if (new_sequence) begin
            sequence_valid<=1; next_position<=0; prefill_count<=0; frozen_prefill_count<=0;
            decoding<=effective_phase; epoch<=epoch+1'b1; state<=SEQUENCE_FLUSH;
          end else begin
            if (effective_phase && !decoding) begin decoding<=1; frozen_prefill_count<=prefill_count; end
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
        if (layer+1<NUM_LAYERS) begin layer<=layer+1'b1; state<=DECODER; end
        else state<=FINAL_NORM;
      end
      FINAL_NORM: if (norm_ready) state<=FINAL_NORM_WAIT;
      FINAL_NORM_WAIT: if (norm_done) state<=PROJECT;
      PROJECT: if (io_ready) state<=PROJECT_WAIT;
      PROJECT_WAIT: if (last_logit) begin
        failed<=0; active_token<=0; next_position<=position+1'b1; sequence_valid<=1;
        if (!phase) prefill_count<=position+1'b1;
        state<=COMPLETE;
      end
      COMPLETE: begin active_token<=0; state<=IDLE; end
      ABORT_FLUSH: state<=ABORT_DRAIN;
      ABORT_DRAIN: if (scheduler_drained) begin
        active_token<=0;
        if (cancel_pending) state<=CANCEL_COMPLETE; else state<=COMPLETE;
      end
      CANCEL_COMPLETE: begin cancelled_active<=0; state<=IDLE; end
      default: begin
        failed<=1; sequence_valid<=0; cancel_pending<=0; state<=ABORT_FLUSH;
      end
    endcase
  end
endmodule
