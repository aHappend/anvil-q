module anvil_q4_parent_top #(
  parameter integer BANKS=16, QUEUE_DEPTH=3, TILE_K=128, TILE_ROWS=8,
  localparam integer SB=(BANKS==1 || BANKS==2 || BANKS==4 ||
    BANKS==8 || BANKS==16) ? BANKS : 1
) (
  input wire clk, rst_n, cancel, token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence, token_phase,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index, logit_data,
  output wire done, error, cancel_done,
  input wire cfg_valid, cfg_commit,
  input wire [5:0] cfg_index,
  input wire [31:0] cfg_wdata,
  output wire cfg_ready, cfg_done, cfg_error,
  input wire draft_valid,
  input wire [31:0] draft_token0, draft_token1, draft_pos,
  input wire draft_new_sequence,
  output wire draft_ready, verify_valid,
  output wire [1:0] verify_accepted,
  output wire verify_error,
  input wire verify_ready,
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
  localparam integer LEGAL=BANKS==SB && QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    TILE_K>=1 && TILE_K<=128 && TILE_ROWS>=1 && TILE_ROWS<=8;
  generate if (!LEGAL) begin : invalid_parameters
    initial $fatal(1,"PARAMETER ERROR: anvil_q4_parent_top geometry");
    assign token_ready=0;
    assign logit_valid=0;
    assign logit_index=0;
    assign logit_data=0;
    assign done=0;
    assign error=0;
    assign cancel_done=0;
    assign cfg_ready=0;
    assign cfg_done=0;
    assign cfg_error=0;
    assign draft_ready=0;
    assign verify_valid=0;
    assign verify_accepted=0;
    assign verify_error=0;
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
  end else begin : legal
    import anvil_q4_parent_fp_pkg::*;
    localparam [4:0] IDLE=0, EMBED=1, EMBED_WAIT=2, DECODE=3,
      DECODE_WAIT=4, NORM=5, NORM_WAIT=6, PROJECT=7, PROJECT_WAIT=8,
      COMPLETE=9, ABORT_FLUSH=10, ABORT_DRAIN=11, CANCEL_COMPLETE=12,
      SPEC_WAIT=13, TARGET_COMPLETE=14, LEGACY=15, LEGACY_WAIT=16;
    reg [4:0] state;
    reg failed, command_active, batch_active, cancelled_active, cancel_pending;
    reg sequence_valid, prediction_valid, decoding, batch_new, batch_epoch_valid;
    reg batch_result_retired;
    reg [31:0] committed, prediction, epoch, epoch_serial, generation;
    reg [31:0] token, position, layer, work_epoch, work_committed, batch_position;
    reg [31:0] argmax, maximum;
    reg have_maximum, phase;
    wire [1023:0] words;
    wire [31:0] mode=words[32+:32];
    wire legacy_mode=mode!=4;
    wire [31:0] layers=words[7*32+:32], hidden=words[8*32+:32];
    wire [31:0] intermediate=words[9*32+:32], query_heads=words[10*32+:32];
    wire [31:0] kv_heads=words[11*32+:32], head_dim=words[12*32+:32];
    wire [31:0] vocabulary=words[13*32+:32], capacity=words[14*32+:32];
    wire [31:0] group_size=words[15*32+:32], epsilon=words[18*32+:32];
    wire scheduler_idle, scheduler_drained, scheduler_fault, cfg_busy;
    wire [3:0] unit_ready, unit_done, unit_error;
    wire config_accepted=cfg_done && !cfg_error;
    wire aborting=state==ABORT_FLUSH || state==ABORT_DRAIN || state==CANCEL_COMPLETE;
    wire engine_flush=cancel || aborting || state==COMPLETE ||
      state==TARGET_COMPLETE || config_accepted;
    wire scheduler_flush=cancel || state==ABORT_FLUSH || config_accepted;
    wire [3:0] c_req_valid, c_req_ready, c_req_write, c_rsp_valid, c_rsp_ready, c_rsp_error;
    wire [15:0] c_req_kind;
    wire [11:0] c_req_proj;
    wire [127:0] c_req_layer, c_req_row, c_req_col, c_req_wdata, c_req_stride, c_rsp_rdata;
    wire io_logit_valid, legacy_logit_valid;
    wire [31:0] io_logit_index, io_logit_data, legacy_logit_index, legacy_logit_data;
    wire stream_valid=legacy_mode ? legacy_logit_valid : io_logit_valid;
    wire [31:0] stream_index=legacy_mode ? legacy_logit_index : io_logit_index;
    wire [31:0] stream_data=legacy_mode ? legacy_logit_data : io_logit_data;
    wire projecting=state==PROJECT_WAIT || state==LEGACY_WAIT;
    wire stream_ready=rst_n && !engine_flush && projecting && (batch_active || logit_ready);
    wire logit_transfer=projecting && stream_valid && stream_ready;
    wire final_logit=logit_transfer && stream_index+1==vocabulary;
    wire better=!have_maximum ||
      (legacy_mode ? $signed(stream_data)>$signed(maximum) : ordered_less(maximum,stream_data));
    wire [31:0] next_argmax=better ? stream_index : argmax;
    wire operation_fault=scheduler_fault ||
      |(unit_done & unit_error);
    wire spec_busy, target_valid, target_ready, target_new, spec_commit;
    wire [31:0] target_token, target_pos, commit_prediction;
    wire [1:0] commit_length;
    wire spec_enabled=!legacy_mode && state==IDLE && scheduler_idle && !cfg_valid &&
      !cfg_busy && !cfg_done && !token_valid;
    wire accepting_draft=draft_valid && draft_ready;
    wire accepting_token=token_valid && token_ready;
    wire accepting_target=target_valid && target_ready;
    wire invalid_epoch=(new_sequence && epoch_serial==32'hffffffff);

    assign token_ready=rst_n && !cancel && state==IDLE && !spec_busy &&
      scheduler_idle && !cfg_valid && !cfg_busy && !cfg_done && !scheduler_fault;
    assign logit_valid=rst_n && !engine_flush && projecting && !batch_active && stream_valid;
    assign logit_index=logit_valid ? stream_index : 32'd0;
    assign logit_data=logit_valid ? stream_data : 32'd0;
    assign done=rst_n && !cancel &&
      (state==COMPLETE || (state==CANCEL_COMPLETE && cancelled_active));
    assign error=done && failed;
    assign cancel_done=rst_n && !cancel && state==CANCEL_COMPLETE;
    assign target_ready=rst_n && !cancel && state==SPEC_WAIT && scheduler_idle &&
      unit_ready[0] && unit_ready[1] && unit_ready[2];

    anvil_q4_parent_descriptor #(.BANKS(BANKS)) descriptor (
      .clk(clk),.rst_n(rst_n),.cancel(cancel),
      .quiescent(state==IDLE && !spec_busy && scheduler_idle),
      .cfg_valid(cfg_valid),.cfg_commit(cfg_commit),.cfg_index(cfg_index),.cfg_wdata(cfg_wdata),
      .cfg_ready(cfg_ready),.cfg_done(cfg_done),.cfg_error(cfg_error),
      .cfg_busy(cfg_busy),.active_words(words)
    );
    anvil_q4_parent_speculative speculative (
      .clk(clk),.rst_n(rst_n),.flush(cancel || config_accepted),
      .abort(operation_fault || aborting),
      .enabled(spec_enabled),.draft_valid(draft_valid),.draft_ready(draft_ready),
      .draft_token0(draft_token0),.draft_token1(draft_token1),.draft_pos(draft_pos),
      .draft_new_sequence(draft_new_sequence),.vocabulary(vocabulary),.context_capacity(capacity),
      .committed_tokens(committed),.sequence_valid(sequence_valid),
      .prediction_valid(prediction_valid),.prediction(prediction),
      .target_valid(target_valid),.target_ready(target_ready),
      .target_token(target_token),.target_pos(target_pos),.target_new_sequence(target_new),
      .target_done(state==TARGET_COMPLETE),.target_error(failed),.target_argmax(argmax),
      .verify_valid(verify_valid),.verify_ready(verify_ready),
      .verify_accepted(verify_accepted),.verify_error(verify_error),
      .commit_valid(spec_commit),.commit_length(commit_length),
      .commit_prediction(commit_prediction),.busy(spec_busy)
    );
    anvil_q4_parent_token_io #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) token_io (
      .clk(clk),.rst_n(rst_n),.flush(engine_flush),
      .cmd_valid(state==EMBED || state==PROJECT),.cmd_ready(unit_ready[2]),
      .cmd_lmhead(state==PROJECT),.cmd_token(token),
      .hidden(hidden),.intermediate(intermediate),.kv_heads(kv_heads),.head_dim(head_dim),
      .vocabulary(vocabulary),.group_size(group_size),.activation_format(words[2*32]),
      .done(unit_done[2]),.error(unit_error[2]),.logit_valid(io_logit_valid),
      .logit_ready(stream_ready && !legacy_mode),
      .logit_index(io_logit_index),.logit_data(io_logit_data),
      .mem_req_valid(c_req_valid[2]),.mem_req_ready(c_req_ready[2]),
      .mem_req_write(c_req_write[2]),.mem_req_kind(c_req_kind[8+:4]),
      .mem_req_layer(c_req_layer[64+:32]),.mem_req_proj(c_req_proj[6+:3]),
      .mem_req_row(c_req_row[64+:32]),.mem_req_col(c_req_col[64+:32]),
      .mem_req_wdata(c_req_wdata[64+:32]),.mem_req_stride(c_req_stride[64+:32]),
      .mem_rsp_valid(c_rsp_valid[2]),.mem_rsp_ready(c_rsp_ready[2]),
      .mem_rsp_rdata(c_rsp_rdata[64+:32]),.mem_rsp_error(c_rsp_error[2])
    );
    anvil_q4_parent_decoder_layer #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) decoder (
      .clk(clk),.rst_n(rst_n),.flush(engine_flush),
      .cmd_valid(state==DECODE),.cmd_ready(unit_ready[0]),
      .cmd_layer(layer),.cmd_pos(position),.cmd_epoch(work_epoch),.cmd_generation(generation),
      .protected_epoch(epoch),
      .protected_tokens(batch_active && batch_new && sequence_valid ? committed : 32'd0),
      .committed_tokens(work_committed),.hidden(hidden),.intermediate(intermediate),
      .query_heads(query_heads),.kv_heads(kv_heads),.head_dim(head_dim),
      .vocabulary(vocabulary),.group_size(group_size),.gqa_ratio(words[22*32+:32]),
      .epsilon(epsilon),.context_capacity(capacity),.page_tokens(words[19*32+:32]),
      .physical_pages(words[20*32+:32]),.activation_format(words[2*32]),
      .activation_a8(words[4*32]),.weight_asymmetric(words[21*32]),.qkv_bias(words[16*32]),
      .cache_int8(words[5*32]),.weight_format(words[3*32+:2]),
      .done(unit_done[0]),.error(unit_error[0]),
      .mem_req_valid(c_req_valid[0]),.mem_req_ready(c_req_ready[0]),
      .mem_req_write(c_req_write[0]),.mem_req_kind(c_req_kind[0+:4]),
      .mem_req_layer(c_req_layer[0+:32]),.mem_req_proj(c_req_proj[0+:3]),
      .mem_req_row(c_req_row[0+:32]),.mem_req_col(c_req_col[0+:32]),
      .mem_req_wdata(c_req_wdata[0+:32]),.mem_req_stride(c_req_stride[0+:32]),
      .mem_rsp_valid(c_rsp_valid[0]),.mem_rsp_ready(c_rsp_ready[0]),
      .mem_rsp_rdata(c_rsp_rdata[0+:32]),.mem_rsp_error(c_rsp_error[0])
    );
    anvil_q4_parent_rmsnorm final_norm (
      .clk(clk),.rst_n(rst_n),.flush(engine_flush),.cmd_valid(state==NORM),
      .cmd_ready(unit_ready[1]),.cmd_layer(32'd0),.cmd_mode(2'd2),
      .hidden(hidden),.intermediate(intermediate),.epsilon(epsilon),
      .activation_format(words[2*32]),.done(unit_done[1]),.error(unit_error[1]),
      .mem_req_valid(c_req_valid[1]),.mem_req_ready(c_req_ready[1]),
      .mem_req_write(c_req_write[1]),.mem_req_kind(c_req_kind[4+:4]),
      .mem_req_layer(c_req_layer[32+:32]),.mem_req_proj(c_req_proj[3+:3]),
      .mem_req_row(c_req_row[32+:32]),.mem_req_col(c_req_col[32+:32]),
      .mem_req_wdata(c_req_wdata[32+:32]),.mem_req_stride(c_req_stride[32+:32]),
      .mem_rsp_valid(c_rsp_valid[1]),.mem_rsp_ready(c_rsp_ready[1]),
      .mem_rsp_rdata(c_rsp_rdata[32+:32]),.mem_rsp_error(c_rsp_error[1])
    );
    anvil_q4_parent_compat compatibility (
      .clk(clk),.rst_n(rst_n),.flush(engine_flush),
      .invalidate(config_accepted || cancel || (legacy_mode && state==COMPLETE && failed)),
      .cmd_valid(state==LEGACY),.cmd_ready(unit_ready[3]),
      .descriptor(words),.cmd_token(token),.cmd_pos(position),.cmd_phase(phase),
      .cmd_new_sequence(position==0),.done(unit_done[3]),.error(unit_error[3]),
      .logit_valid(legacy_logit_valid),.logit_ready(stream_ready && legacy_mode),
      .logit_index(legacy_logit_index),.logit_data(legacy_logit_data),
      .mem_req_valid(c_req_valid[3]),.mem_req_ready(c_req_ready[3]),
      .mem_req_write(c_req_write[3]),.mem_req_kind(c_req_kind[12+:4]),
      .mem_req_layer(c_req_layer[96+:32]),.mem_req_proj(c_req_proj[9+:3]),
      .mem_req_row(c_req_row[96+:32]),.mem_req_col(c_req_col[96+:32]),
      .mem_req_wdata(c_req_wdata[96+:32]),
      .mem_rsp_valid(c_rsp_valid[3]),.mem_rsp_ready(c_rsp_ready[3]),
      .mem_rsp_rdata(c_rsp_rdata[96+:32]),.mem_rsp_error(c_rsp_error[3])
    );
    assign c_req_stride[96+:32]=0;
    anvil_q4_parent_bank_scheduler #(.BANKS(BANKS),.CLIENTS(4),.QUEUE_DEPTH(QUEUE_DEPTH)) bank_scheduler (
      .clk(clk),.rst_n(rst_n),.flush(scheduler_flush),.legacy_mode(legacy_mode),
      .active_banks(words[6*32+:5]),.idle(scheduler_idle),
      .drain_done(scheduler_drained),.fault(scheduler_fault),
      .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
      .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
      .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
      .c_req_stride(c_req_stride),.c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
      .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error),
      .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
      .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
      .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
      .mem_req_tag(mem_req_tag),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),
      .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag)
    );

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; command_active<=0; batch_active<=0;
        cancelled_active<=0; cancel_pending<=0; sequence_valid<=0; prediction_valid<=0;
        decoding<=0; batch_new<=0; batch_epoch_valid<=0; batch_result_retired<=0;
        committed<=0; prediction<=0; epoch<=0; epoch_serial<=0;
        generation<=0; token<=0; position<=0; layer<=0; work_epoch<=0; work_committed<=0;
        batch_position<=0; argmax<=0; maximum<=0; have_maximum<=0; phase<=0;
      end else if (cancel) begin
        if (!aborting) cancelled_active<=command_active || batch_active;
        failed<=1; cancel_pending<=1; sequence_valid<=0; prediction_valid<=0;
        committed<=0; decoding<=0; state<=ABORT_DRAIN;
      end else if (config_accepted) begin
        sequence_valid<=0; prediction_valid<=0; committed<=0; decoding<=0;
        generation<=generation+1'b1;
      end else if (operation_fault && !aborting && state!=COMPLETE &&
          state!=TARGET_COMPLETE) begin
        failed<=1; cancel_pending<=0; state<=ABORT_FLUSH;
        if (legacy_mode || (!batch_active && work_epoch!=epoch)) begin
          sequence_valid<=0; prediction_valid<=0; committed<=0; decoding<=0;
        end
      end else begin
        if (batch_active && verify_valid && verify_ready) batch_result_retired<=1;
        if (logit_transfer) begin
          have_maximum<=1;
          if (better) begin maximum<=stream_data; argmax<=stream_index; end
        end
        case (state)
          IDLE: begin
            if (accepting_token) begin
              failed<=0; command_active<=1; batch_active<=0; cancel_pending<=0;
              token<=token_id; position<=token_pos; layer<=0;
              have_maximum<=0; argmax<=0; maximum<=0;
              phase<=legacy_mode && mode!=1 && token_phase;
              if (token_id>=vocabulary || token_pos>=capacity || invalid_epoch ||
                  (new_sequence ? token_pos!=0 :
                    ((!sequence_valid && mode!=1) || token_pos!=committed ||
                      (legacy_mode && mode!=1 && decoding && !token_phase)))) begin
                failed<=1; state<=COMPLETE;
                if (legacy_mode) begin
                  sequence_valid<=0; prediction_valid<=0; committed<=0; decoding<=0;
                end
              end else begin
                work_committed<=new_sequence ? 32'd0 : committed;
                if (new_sequence) begin
                  epoch_serial<=epoch_serial+1'b1; work_epoch<=epoch_serial+1'b1;
                end else work_epoch<=epoch;
                if (legacy_mode) state<=LEGACY; else state<=EMBED;
              end
            end else if (accepting_draft) begin
              failed<=0; command_active<=1; batch_active<=1; cancel_pending<=0;
              batch_result_retired<=0;
              batch_new<=draft_new_sequence; batch_position<=draft_pos;
              batch_epoch_valid<=!draft_new_sequence || epoch_serial!=32'hffffffff;
              if (draft_new_sequence && epoch_serial!=32'hffffffff) begin
                epoch_serial<=epoch_serial+1'b1; work_epoch<=epoch_serial+1'b1;
              end else work_epoch<=epoch;
              state<=SPEC_WAIT;
            end
          end
          SPEC_WAIT: begin
            if (batch_result_retired || (verify_valid && verify_ready)) begin
              failed<=failed || verify_error;
              if (spec_commit && !failed && commit_length!=0) begin
                committed<=batch_position+{30'd0,commit_length}; epoch<=work_epoch;
                sequence_valid<=1; prediction_valid<=1; prediction<=commit_prediction;
                if (batch_new) decoding<=0;
              end
              command_active<=0; batch_active<=0; state<=COMPLETE;
            end else if (accepting_target) begin
              token<=target_token; position<=target_pos; layer<=0;
              work_committed<=target_pos; have_maximum<=0; argmax<=0; maximum<=0;
              if (!batch_epoch_valid) begin
                failed<=1; state<=TARGET_COMPLETE;
              end else state<=EMBED;
            end
          end
          EMBED: if (unit_ready[2]) state<=EMBED_WAIT;
          EMBED_WAIT: if (unit_done[2]) state<=DECODE;
          DECODE: if (unit_ready[0]) state<=DECODE_WAIT;
          DECODE_WAIT: if (unit_done[0]) begin
            if (layer+1<layers) begin layer<=layer+1'b1; state<=DECODE; end
            else state<=NORM;
          end
          NORM: if (unit_ready[1]) state<=NORM_WAIT;
          NORM_WAIT: if (unit_done[1]) state<=PROJECT;
          PROJECT: if (unit_ready[2]) state<=PROJECT_WAIT;
          LEGACY: if (unit_ready[3]) state<=LEGACY_WAIT;
          PROJECT_WAIT, LEGACY_WAIT: if (final_logit) begin
            argmax<=next_argmax;
            if (batch_active) state<=TARGET_COMPLETE;
            else begin
              committed<=position+1'b1; epoch<=work_epoch; sequence_valid<=1;
              prediction_valid<=1; prediction<=next_argmax; decoding<=phase;
              failed<=0; command_active<=0; state<=COMPLETE;
            end
          end
          TARGET_COMPLETE: state<=SPEC_WAIT;
          COMPLETE: begin command_active<=0; state<=IDLE; end
          ABORT_FLUSH: state<=ABORT_DRAIN;
          ABORT_DRAIN: if (scheduler_drained || scheduler_idle) begin
            if (cancel_pending) begin
              batch_active<=0; command_active<=0; state<=CANCEL_COMPLETE;
            end else if (batch_active && spec_busy &&
                !batch_result_retired && !(verify_valid && verify_ready))
              state<=SPEC_WAIT;
            else if (batch_active) begin
              batch_active<=0; command_active<=0; state<=COMPLETE;
            end
            else begin command_active<=0; state<=COMPLETE; end
          end
          CANCEL_COMPLETE: begin cancelled_active<=0; cancel_pending<=0; state<=IDLE; end
          default: begin failed<=1; cancel_pending<=0; state<=ABORT_FLUSH; end
        endcase
      end
    end
  end endgenerate
endmodule
