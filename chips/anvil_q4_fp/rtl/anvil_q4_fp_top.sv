module anvil_q4_fp_top #(
  parameter integer BANKS=16, QUEUE_DEPTH=3, TILE_K=128, TILE_ROWS=16,
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
    TILE_K>=1 && TILE_K<=128 && TILE_ROWS>=1 && TILE_ROWS<=16;
  generate if (!LEGAL) begin : invalid_parameters
    initial $fatal(1,"PARAMETER ERROR: anvil_q4_fp_top geometry");
    assign token_ready=0; assign logit_valid=0; assign logit_index=0; assign logit_data=0;
    assign done=0; assign error=0; assign cancel_done=0;
    assign cfg_ready=0; assign cfg_done=0; assign cfg_error=0;
    assign draft_ready=0; assign verify_valid=0; assign verify_accepted=0; assign verify_error=0;
    assign mem_req_valid=0; assign mem_req_write=0; assign mem_req_kind=0;
    assign mem_req_layer=0; assign mem_req_proj=0; assign mem_req_row=0;
    assign mem_req_col=0; assign mem_req_wdata=0; assign mem_req_tag=0; assign mem_rsp_ready=0;
  end else begin : legal
    import anvil_q4_fp_pkg::*;
    localparam [4:0] IDLE=0,EMBED=1,EMBED_WAIT=2,DECODE=3,DECODE_WAIT=4,
      NORM=5,NORM_WAIT=6,PROJECT=7,PROJECT_WAIT=8,FENCE=9,FINISH=10,
      COMPLETE=11,SPEC_WAIT=12,TARGET_COMPLETE=13,ABORT_FLUSH=14,
      ABORT_DRAIN=15,CANCEL_COMPLETE=16;
    reg [4:0] state,resume_state;
    reg failed,command_active,batch_active,batch_new,batch_epoch_valid;
    reg cancel_pending,cancelled_active,sequence_valid,prediction_valid;
    reg result_published,result_retired;
    reg [31:0] committed,prediction,epoch,epoch_serial,generation;
    reg [31:0] token,position,layer,work_epoch,work_committed,batch_position;
    reg [31:0] argmax,maximum;
    reg have_maximum;
    wire [1023:0] words;
    wire native_mode=words[0+:32]==2 && words[32+:32]==5;
    wire [31:0] layers=words[7*32+:32],hidden=words[8*32+:32];
    wire [31:0] intermediate=words[9*32+:32],query_heads=words[10*32+:32];
    wire [31:0] kv_heads=words[11*32+:32],head_dim=words[12*32+:32];
    wire [31:0] vocabulary=words[13*32+:32],capacity=words[14*32+:32];
    wire [31:0] group_size=words[15*32+:32],epsilon=words[18*32+:32];
    wire scheduler_idle,scheduler_drained,scheduler_fault,routing_idle;
    wire descriptor_ready,cfg_busy,parent_cfg_ready,parent_cfg_done,parent_cfg_error;
    wire config_accepted=cfg_done && !cfg_error;
    wire aborting=state==ABORT_FLUSH || state==ABORT_DRAIN || state==CANCEL_COMPLETE;
    wire engine_flush=cancel || aborting || config_accepted ||
      state==COMPLETE || state==TARGET_COMPLETE;
    wire scheduler_flush=(native_mode && cancel) || state==ABORT_FLUSH || config_accepted;
    wire [2:0] unit_ready,unit_done,unit_error;
    wire [50:0] c_req_valid,c_req_ready,c_req_write,c_rsp_valid,c_rsp_ready,c_rsp_error;
    wire [203:0] c_req_kind;
    wire [152:0] c_req_proj;
    wire [1631:0] c_req_layer,c_req_row,c_req_col,c_req_data,c_req_stride,c_rsp_data;
    wire [16:0] s_req_valid,s_req_ready,s_req_write,s_rsp_valid,s_rsp_ready,s_rsp_error;
    wire [67:0] s_req_kind;
    wire [50:0] s_req_proj;
    wire [543:0] s_req_layer,s_req_row,s_req_col,s_req_data,s_req_stride,s_rsp_data;
    wire io_logit_valid;
    wire [31:0] io_logit_index,io_logit_data;
    wire projecting=state==PROJECT_WAIT;
    wire stream_ready=rst_n && native_mode && !engine_flush && projecting &&
      (batch_active || logit_ready);
    wire logit_transfer=io_logit_valid && stream_ready;
    wire better=!is_nan(io_logit_data) &&
      (!have_maximum || ordered_less(maximum,io_logit_data));
    wire operation_fault=scheduler_fault || |(unit_done & unit_error);
    wire spec_busy,spec_draft_ready,target_valid,target_ready,target_new,spec_commit;
    wire spec_verify_valid,spec_verify_error,spec_result_visible;
    wire [1:0] spec_verify_accepted,commit_length;
    wire [31:0] target_token,target_pos,commit_prediction;
    wire spec_enabled=native_mode && state==IDLE && scheduler_idle && routing_idle &&
      parent_cfg_ready && !cfg_valid && !cfg_busy && !cfg_done && !token_valid;
    wire native_token_ready=rst_n && native_mode && !cancel && state==IDLE && !spec_busy &&
      scheduler_idle && routing_idle && parent_cfg_ready && !cfg_valid && !cfg_busy &&
      !cfg_done && !scheduler_fault;
    wire accepting_draft=native_mode && draft_valid && spec_draft_ready;
    wire accepting_token=token_valid && native_token_ready;
    wire accepting_target=target_valid && target_ready;
    wire parent_token_ready,parent_logit_valid,parent_done,parent_error,parent_cancel_done;
    wire parent_draft_ready,parent_verify_valid,parent_verify_error;
    wire [1:0] parent_verify_accepted;
    wire [31:0] parent_logit_index,parent_logit_data;
    wire [SB-1:0] n_req_valid,n_req_write,n_rsp_ready,p_req_valid,p_req_write,p_rsp_ready;
    wire [4*SB-1:0] n_req_kind,p_req_kind;
    wire [3*SB-1:0] n_req_proj,p_req_proj;
    wire [32*SB-1:0] n_req_layer,n_req_row,n_req_col,n_req_data;
    wire [32*SB-1:0] p_req_layer,p_req_row,p_req_col,p_req_data;
    wire [64*SB-1:0] n_req_tag,p_req_tag;
    wire [SB-1:0] parent_bad_tags;
    reg parent_identity_fault;
    wire parent_cancel=cancel || parent_identity_fault || (config_accepted && native_mode);
    assign cfg_ready=descriptor_ready && parent_cfg_ready;
    assign token_ready=native_mode ? native_token_ready :
      rst_n && !parent_identity_fault && !cfg_valid && !cfg_busy && !cfg_done && parent_token_ready;
    assign logit_valid=rst_n && !cancel && (native_mode ?
      !engine_flush && projecting && !batch_active && io_logit_valid : parent_logit_valid);
    assign logit_index=logit_valid ? (native_mode ? io_logit_index : parent_logit_index) : 32'd0;
    assign logit_data=logit_valid ? (native_mode ? io_logit_data : parent_logit_data) : 32'd0;
    assign done=rst_n && !cancel && (native_mode ?
      state==COMPLETE || (state==CANCEL_COMPLETE && cancelled_active) : parent_done);
    assign error=done && (native_mode ? failed : parent_error || parent_identity_fault);
    assign cancel_done=rst_n && !cancel && (native_mode ? state==CANCEL_COMPLETE : parent_cancel_done);
    assign draft_ready=native_mode ? spec_draft_ready :
      rst_n && !parent_identity_fault && !cfg_valid && !cfg_busy && !cfg_done && parent_draft_ready;
    assign spec_result_visible=native_mode &&
      ((state==SPEC_WAIT && scheduler_idle && routing_idle) || result_published);
    assign verify_valid=rst_n && !cancel && (native_mode ?
      spec_verify_valid && spec_result_visible : parent_verify_valid);
    assign verify_accepted=verify_valid ? (native_mode ? spec_verify_accepted : parent_verify_accepted) : 2'd0;
    assign verify_error=verify_valid && (native_mode ? spec_verify_error : parent_verify_error);
    assign target_ready=rst_n && !cancel && native_mode && state==SPEC_WAIT &&
      scheduler_idle && routing_idle && !spec_verify_valid && !failed;

    anvil_q4_fp_descriptor #(.BANKS(BANKS)) descriptor (
      .clk(clk),.rst_n(rst_n),.cancel(cancel),
      .quiescent(state==IDLE && !spec_busy && scheduler_idle && routing_idle && parent_cfg_ready),
      .cfg_valid(cfg_valid && parent_cfg_ready),.cfg_commit(cfg_commit),
      .cfg_index(cfg_index),.cfg_wdata(cfg_wdata),.cfg_ready(descriptor_ready),
      .cfg_done(cfg_done),.cfg_error(cfg_error),.cfg_busy(cfg_busy),.active_words(words)
    );
    anvil_q4_fp_speculative speculative (
      .clk(clk),.rst_n(rst_n),.flush(cancel || config_accepted),
      .abort(operation_fault || aborting),.enabled(spec_enabled),
      .draft_valid(draft_valid && native_mode),.draft_ready(spec_draft_ready),
      .draft_token0(draft_token0),.draft_token1(draft_token1),.draft_pos(draft_pos),
      .draft_new_sequence(draft_new_sequence),.vocabulary(vocabulary),.context_capacity(capacity),
      .committed_tokens(committed),.sequence_valid(sequence_valid),
      .prediction_valid(prediction_valid),.prediction(prediction),
      .target_valid(target_valid),.target_ready(target_ready),
      .target_token(target_token),.target_pos(target_pos),.target_new_sequence(target_new),
      .target_done(state==TARGET_COMPLETE),.target_error(failed),.target_argmax(argmax),
      .verify_valid(spec_verify_valid),.verify_ready(verify_ready && spec_result_visible),
      .verify_accepted(spec_verify_accepted),.verify_error(spec_verify_error),
      .commit_valid(spec_commit),.commit_length(commit_length),
      .commit_prediction(commit_prediction),.busy(spec_busy)
    );
    anvil_q4_fp_token_io #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) token_io (
      .clk(clk),.rst_n(rst_n),.flush(engine_flush),
      .cmd_valid(state==EMBED || state==PROJECT),.cmd_ready(unit_ready[0]),
      .cmd_lmhead(state==PROJECT),.cmd_token(token),
      .hidden(hidden),.intermediate(intermediate),.kv_heads(kv_heads),.head_dim(head_dim),
      .vocabulary(vocabulary),.group_size(group_size),.activation_format(words[2*32]),
      .done(unit_done[0]),.error(unit_error[0]),.logit_valid(io_logit_valid),
      .logit_ready(stream_ready),.logit_index(io_logit_index),.logit_data(io_logit_data),
      .mem_req_valid(c_req_valid[0+:17]),.mem_req_ready(c_req_ready[0+:17]),
      .mem_req_write(c_req_write[0+:17]),.mem_req_kind(c_req_kind[0+:68]),
      .mem_req_layer(c_req_layer[0+:544]),.mem_req_proj(c_req_proj[0+:51]),
      .mem_req_row(c_req_row[0+:544]),.mem_req_col(c_req_col[0+:544]),
      .mem_req_wdata(c_req_data[0+:544]),.mem_req_stride(c_req_stride[0+:544]),
      .mem_rsp_valid(c_rsp_valid[0+:17]),.mem_rsp_ready(c_rsp_ready[0+:17]),
      .mem_rsp_rdata(c_rsp_data[0+:544]),.mem_rsp_error(c_rsp_error[0+:17])
    );
    anvil_q4_fp_decoder_layer #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) decoder (
      .clk(clk),.rst_n(rst_n),.flush(engine_flush),
      .cmd_valid(state==DECODE),.cmd_ready(unit_ready[1]),
      .cmd_layer(layer),.cmd_pos(position),.cmd_epoch(work_epoch),.cmd_generation(generation),
      .protected_epoch(epoch),
      .protected_tokens(sequence_valid && work_epoch!=epoch ? committed : 32'd0),
      .committed_tokens(work_committed),.hidden(hidden),.intermediate(intermediate),
      .query_heads(query_heads),.kv_heads(kv_heads),.head_dim(head_dim),
      .vocabulary(vocabulary),.group_size(group_size),.gqa_ratio(words[22*32+:32]),
      .epsilon(epsilon),.context_capacity(capacity),.page_tokens(words[19*32+:32]),
      .physical_pages(words[20*32+:32]),.activation_format(words[2*32]),
      .activation_a8(1'b0),.weight_asymmetric(1'b0),.qkv_bias(words[16*32]),
      .cache_format(words[5*32+:2]),.weight_format(2'd0),
      .done(unit_done[1]),.error(unit_error[1]),
      .mem_req_valid(c_req_valid[17+:17]),.mem_req_ready(c_req_ready[17+:17]),
      .mem_req_write(c_req_write[17+:17]),.mem_req_kind(c_req_kind[68+:68]),
      .mem_req_layer(c_req_layer[544+:544]),.mem_req_proj(c_req_proj[51+:51]),
      .mem_req_row(c_req_row[544+:544]),.mem_req_col(c_req_col[544+:544]),
      .mem_req_wdata(c_req_data[544+:544]),.mem_req_stride(c_req_stride[544+:544]),
      .mem_rsp_valid(c_rsp_valid[17+:17]),.mem_rsp_ready(c_rsp_ready[17+:17]),
      .mem_rsp_rdata(c_rsp_data[544+:544]),.mem_rsp_error(c_rsp_error[17+:17])
    );
    assign c_req_valid[34+:16]=0;
    assign c_req_write[34+:16]=0;
    assign c_req_kind[136+:64]=0;
    assign c_req_proj[102+:48]=0;
    assign c_req_layer[1088+:512]=0;
    assign c_req_row[1088+:512]=0;
    assign c_req_col[1088+:512]=0;
    assign c_req_data[1088+:512]=0;
    assign c_req_stride[1088+:512]=0;
    assign c_rsp_ready[34+:16]=0;
    anvil_q4_fp_rmsnorm final_norm (
      .clk(clk),.rst_n(rst_n),.flush(engine_flush),.cmd_valid(state==NORM),
      .cmd_ready(unit_ready[2]),.cmd_layer(32'd0),.cmd_mode(2'd2),
      .hidden(hidden),.intermediate(intermediate),.epsilon(epsilon),
      .activation_format(words[2*32]),.done(unit_done[2]),.error(unit_error[2]),
      .mem_req_valid(c_req_valid[50]),.mem_req_ready(c_req_ready[50]),
      .mem_req_write(c_req_write[50]),.mem_req_kind(c_req_kind[200+:4]),
      .mem_req_layer(c_req_layer[1600+:32]),.mem_req_proj(c_req_proj[150+:3]),
      .mem_req_row(c_req_row[1600+:32]),.mem_req_col(c_req_col[1600+:32]),
      .mem_req_wdata(c_req_data[1600+:32]),.mem_req_stride(c_req_stride[1600+:32]),
      .mem_rsp_valid(c_rsp_valid[50]),.mem_rsp_ready(c_rsp_ready[50]),
      .mem_rsp_rdata(c_rsp_data[1600+:32]),.mem_rsp_error(c_rsp_error[50])
    );
    anvil_q4_fp_channel_mux #(.CLIENTS(3)) stage_routing (
      .clk(clk),.rst_n(rst_n),.flush(engine_flush),.idle(routing_idle),
      .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
      .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
      .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_data),.c_req_stride(c_req_stride),
      .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
      .c_rsp_rdata(c_rsp_data),.c_rsp_error(c_rsp_error),
      .mem_req_valid(s_req_valid),.mem_req_ready(s_req_ready),.mem_req_write(s_req_write),
      .mem_req_kind(s_req_kind),.mem_req_layer(s_req_layer),.mem_req_proj(s_req_proj),
      .mem_req_row(s_req_row),.mem_req_col(s_req_col),.mem_req_wdata(s_req_data),
      .mem_req_stride(s_req_stride),.mem_rsp_valid(s_rsp_valid),
      .mem_rsp_ready(s_rsp_ready),.mem_rsp_rdata(s_rsp_data),.mem_rsp_error(s_rsp_error)
    );
    anvil_q4_fp_bank_scheduler #(.BANKS(BANKS),.CLIENTS(17),.QUEUE_DEPTH(QUEUE_DEPTH)) bank_scheduler (
      .clk(clk),.rst_n(rst_n),.flush(scheduler_flush),.legacy_mode(1'b0),
      .active_banks(words[6*32+:5]),.idle(scheduler_idle),
      .drain_done(scheduler_drained),.fault(scheduler_fault),
      .c_req_valid(s_req_valid),.c_req_ready(s_req_ready),.c_req_write(s_req_write),
      .c_req_kind(s_req_kind),.c_req_layer(s_req_layer),.c_req_proj(s_req_proj),
      .c_req_row(s_req_row),.c_req_col(s_req_col),.c_req_wdata(s_req_data),
      .c_req_stride(s_req_stride),.c_rsp_valid(s_rsp_valid),.c_rsp_ready(s_rsp_ready),
      .c_rsp_rdata(s_rsp_data),.c_rsp_error(s_rsp_error),
      .mem_req_valid(n_req_valid),.mem_req_ready(native_mode ? mem_req_ready : {SB{1'b0}}),
      .mem_req_write(n_req_write),.mem_req_kind(n_req_kind),.mem_req_layer(n_req_layer),
      .mem_req_proj(n_req_proj),.mem_req_row(n_req_row),.mem_req_col(n_req_col),
      .mem_req_wdata(n_req_data),.mem_req_tag(n_req_tag),
      .mem_rsp_valid(native_mode ? mem_rsp_valid : {SB{1'b0}}),
      .mem_rsp_error(mem_rsp_error),.mem_rsp_ready(n_rsp_ready),
      .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag)
    );
    anvil_q4_parent_top #(.BANKS(BANKS),.QUEUE_DEPTH(QUEUE_DEPTH),
      .TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS>8 ? 8 : TILE_ROWS)) compatibility (
      .clk(clk),.rst_n(rst_n),.cancel(parent_cancel),
      .token_valid(!native_mode && token_valid && !cfg_valid && !cfg_busy && !cfg_done &&
        !parent_identity_fault),.token_ready(parent_token_ready),
      .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),.token_phase(token_phase),
      .logit_valid(parent_logit_valid),.logit_ready(!native_mode && logit_ready),
      .logit_index(parent_logit_index),.logit_data(parent_logit_data),
      .done(parent_done),.error(parent_error),.cancel_done(parent_cancel_done),
      .cfg_valid(cfg_valid && cfg_ready),.cfg_commit(cfg_commit),
      .cfg_index(cfg_index),.cfg_wdata(cfg_wdata),.cfg_ready(parent_cfg_ready),
      .cfg_done(parent_cfg_done),.cfg_error(parent_cfg_error),
      .draft_valid(!native_mode && draft_valid && !cfg_valid && !cfg_busy && !cfg_done &&
        !parent_identity_fault),.draft_token0(draft_token0),.draft_token1(draft_token1),
      .draft_pos(draft_pos),.draft_new_sequence(draft_new_sequence),.draft_ready(parent_draft_ready),
      .verify_valid(parent_verify_valid),.verify_accepted(parent_verify_accepted),
      .verify_error(parent_verify_error),.verify_ready(!native_mode && verify_ready),
      .mem_req_valid(p_req_valid),
      .mem_req_ready(!native_mode ? mem_req_ready & ~parent_bad_tags : {SB{1'b0}}),
      .mem_req_write(p_req_write),.mem_req_kind(p_req_kind),.mem_req_layer(p_req_layer),
      .mem_req_proj(p_req_proj),.mem_req_row(p_req_row),.mem_req_col(p_req_col),
      .mem_req_wdata(p_req_data),.mem_req_tag(p_req_tag),
      .mem_rsp_valid(!native_mode ? mem_rsp_valid : {SB{1'b0}}),
      .mem_rsp_error(mem_rsp_error),.mem_rsp_ready(p_rsp_ready),
      .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag)
    );
    for (genvar n=0;n<SB;n=n+1) begin : external_banks
      assign parent_bad_tags[n]=p_req_valid[n] && p_req_tag[n*64+63];
      assign mem_req_valid[n]=rst_n && (native_mode ? n_req_valid[n] :
        p_req_valid[n] && !parent_bad_tags[n]);
      assign mem_req_write[n]=mem_req_valid[n] && (native_mode ? n_req_write[n] : p_req_write[n]);
      assign mem_req_kind[n*4+:4]=mem_req_valid[n] ?
        (native_mode ? n_req_kind[n*4+:4] : p_req_kind[n*4+:4]) : 4'd0;
      assign mem_req_layer[n*32+:32]=mem_req_valid[n] ?
        (native_mode ? n_req_layer[n*32+:32] : p_req_layer[n*32+:32]) : 32'd0;
      assign mem_req_proj[n*3+:3]=mem_req_valid[n] ?
        (native_mode ? n_req_proj[n*3+:3] : p_req_proj[n*3+:3]) : 3'd0;
      assign mem_req_row[n*32+:32]=mem_req_valid[n] ?
        (native_mode ? n_req_row[n*32+:32] : p_req_row[n*32+:32]) : 32'd0;
      assign mem_req_col[n*32+:32]=mem_req_valid[n] ?
        (native_mode ? n_req_col[n*32+:32] : p_req_col[n*32+:32]) : 32'd0;
      assign mem_req_wdata[n*32+:32]=mem_req_valid[n] ?
        (native_mode ? n_req_data[n*32+:32] : p_req_data[n*32+:32]) : 32'd0;
      assign mem_req_tag[n*64+:64]=mem_req_valid[n] ?
        (native_mode ? n_req_tag[n*64+:64] : p_req_tag[n*64+:64]) : 64'd0;
      assign mem_rsp_ready[n]=rst_n && (native_mode ? n_rsp_ready[n] : p_rsp_ready[n]);
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) parent_identity_fault<=0;
      else if (|parent_bad_tags) parent_identity_fault<=1;
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin result_published<=0; result_retired<=0; end
      else if (cancel || config_accepted || accepting_draft) begin
        result_published<=0; result_retired<=0;
      end else if (native_mode && verify_valid) begin
        result_published<=1;
        if (verify_ready) result_retired<=1;
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; resume_state<=IDLE; failed<=0; command_active<=0; batch_active<=0;
        batch_new<=0; batch_epoch_valid<=0; cancel_pending<=0; cancelled_active<=0;
        sequence_valid<=0; prediction_valid<=0; committed<=0; prediction<=0;
        epoch<=0; epoch_serial<=0; generation<=0; token<=0; position<=0; layer<=0;
        work_epoch<=0; work_committed<=0; batch_position<=0;
        argmax<=0; maximum<=0; have_maximum<=0;
      end else if (native_mode && cancel) begin
        if (!aborting) cancelled_active<=command_active || batch_active;
        failed<=1; cancel_pending<=1; state<=ABORT_DRAIN;
      end else if (config_accepted) begin
        sequence_valid<=0; prediction_valid<=0; committed<=0; prediction<=0;
        generation<=generation+1'b1;
      end else if (native_mode && operation_fault && !aborting &&
          state!=COMPLETE && state!=TARGET_COMPLETE) begin
        failed<=1; cancel_pending<=0; state<=ABORT_FLUSH;
      end else begin
        if (logit_transfer && better) begin
          have_maximum<=1; maximum<=io_logit_data; argmax<=io_logit_index;
        end
        case (state)
          IDLE: begin
            if (accepting_token) begin
              failed<=0; command_active<=1; batch_active<=0; cancel_pending<=0;
              token<=token_id; position<=token_pos; layer<=0;
              have_maximum<=0; argmax<=0; maximum<=0;
              if (token_id>=vocabulary || token_pos>=capacity ||
                  (new_sequence && epoch_serial==32'hffffffff) ||
                  (new_sequence ? token_pos!=0 : !sequence_valid || token_pos!=committed)) begin
                failed<=1; state<=COMPLETE;
              end else begin
                work_committed<=new_sequence ? 32'd0 : committed;
                if (new_sequence) begin
                  epoch_serial<=epoch_serial+1'b1; work_epoch<=epoch_serial+1'b1;
                end else work_epoch<=epoch;
                state<=EMBED;
              end
            end else if (accepting_draft) begin
              failed<=0; command_active<=1; batch_active<=1; cancel_pending<=0;
              batch_new<=draft_new_sequence; batch_position<=draft_pos;
              batch_epoch_valid<=!draft_new_sequence || epoch_serial!=32'hffffffff;
              if (draft_new_sequence && epoch_serial!=32'hffffffff) begin
                epoch_serial<=epoch_serial+1'b1; work_epoch<=epoch_serial+1'b1;
              end else work_epoch<=epoch;
              state<=SPEC_WAIT;
            end
          end
          SPEC_WAIT: begin
            if (result_retired || (verify_valid && verify_ready)) begin
              failed<=failed || spec_verify_error;
              if (spec_commit && !failed && commit_length!=0) begin
                committed<=batch_position+{30'd0,commit_length}; epoch<=work_epoch;
                sequence_valid<=1; prediction_valid<=1; prediction<=commit_prediction;
              end
              command_active<=0; batch_active<=0; state<=COMPLETE;
            end else if (accepting_target) begin
              token<=target_token; position<=target_pos; layer<=0;
              work_committed<=target_pos; have_maximum<=0; argmax<=0; maximum<=0;
              if (!batch_epoch_valid) begin failed<=1; state<=TARGET_COMPLETE; end
              else state<=EMBED;
            end
          end
          EMBED: if (unit_ready[0]) state<=EMBED_WAIT;
          EMBED_WAIT: if (unit_done[0]) begin resume_state<=DECODE; state<=FENCE; end
          DECODE: if (unit_ready[1]) state<=DECODE_WAIT;
          DECODE_WAIT: if (unit_done[1]) begin
            if (layer+1<layers) begin layer<=layer+1'b1; resume_state<=DECODE; end
            else resume_state<=NORM;
            state<=FENCE;
          end
          NORM: if (unit_ready[2]) state<=NORM_WAIT;
          NORM_WAIT: if (unit_done[2]) begin resume_state<=PROJECT; state<=FENCE; end
          PROJECT: if (unit_ready[0]) state<=PROJECT_WAIT;
          PROJECT_WAIT: if (unit_done[0]) begin resume_state<=FINISH; state<=FENCE; end
          FENCE: if (scheduler_idle && routing_idle) state<=resume_state;
          FINISH: begin
            if (batch_active) state<=TARGET_COMPLETE;
            else begin
              committed<=position+1'b1; epoch<=work_epoch; sequence_valid<=1;
              prediction_valid<=1; prediction<=argmax; command_active<=0; state<=COMPLETE;
            end
          end
          TARGET_COMPLETE: state<=SPEC_WAIT;
          COMPLETE: begin command_active<=0; state<=IDLE; end
          ABORT_FLUSH: state<=ABORT_DRAIN;
          ABORT_DRAIN: if (scheduler_drained || scheduler_idle) begin
            if (cancel_pending) begin
              batch_active<=0; command_active<=0; state<=CANCEL_COMPLETE;
            end else if (batch_active) state<=SPEC_WAIT;
            else begin command_active<=0; state<=COMPLETE; end
          end
          CANCEL_COMPLETE: begin cancelled_active<=0; cancel_pending<=0; state<=IDLE; end
          default: begin failed<=1; cancel_pending<=0; state<=ABORT_FLUSH; end
        endcase
      end
    end
  end endgenerate
endmodule
