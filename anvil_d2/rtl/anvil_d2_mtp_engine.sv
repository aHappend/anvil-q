module anvil_d2_mtp_engine #(
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=10944,
  parameter integer NUM_Q_HEADS=16, KV_LORA_RANK=512, QK_NOPE_HEAD_DIM=128,
  parameter integer QK_ROPE_HEAD_DIM=64, V_HEAD_DIM=128,
  parameter integer ROUTED_EXPERTS=64, TOP_K=6, SHARED_EXPERTS=2,
  parameter integer MOE_INTERMEDIATE_SIZE=1408, FIRST_DENSE_LAYERS=1,
  parameter integer VOCAB_SIZE=102400, MAX_SEQ_LEN=32768, TILE_K=128, TILE_ROWS=8,
  parameter integer MTP_K=4, ENABLE=1
) (
  input wire clk, rst_n, cancel,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence, token_phase,
  input wire mtp_enable, fp8_enable, generation_enable,
  input wire [31:0] generation_limit, eos_token,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire spec_valid,
  input wire spec_ready,
  output wire [31:0] spec_token, spec_pos,
  output wire spec_last,
  output wire [2:0] spec_count, spec_accepted,
  output wire done, error, cancel_done, idle, generation_active,
  output wire accepted_retire, rejected_block, verification_active,
  output wire shared_busy, prefetch_busy,
  output wire [31:0] cache_dense_increment, expert_dense_increment,
  output wire [2:0] proposed_increment,
  output wire transport_flush, active_fp8,
  output wire [31:0] active_epoch,
  input wire transport_idle, transport_drained, transport_fault,
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
  generate if (ENABLE==0) begin: disabled
    assign token_ready=0;
    assign logit_valid=0;
    assign logit_index=0;
    assign logit_data=0;
    assign spec_valid=0;
    assign spec_token=0;
    assign spec_pos=0;
    assign spec_last=0;
    assign spec_count=0;
    assign spec_accepted=0;
    assign done=0;
    assign error=0;
    assign cancel_done=0;
    assign idle=0;
    assign generation_active=0;
    assign accepted_retire=0;
    assign rejected_block=0;
    assign verification_active=0;
    assign shared_busy=0;
    assign prefetch_busy=0;
    assign cache_dense_increment=0;
    assign expert_dense_increment=0;
    assign proposed_increment=0;
    assign transport_flush=0;
    assign active_fp8=0;
    assign active_epoch=0;
    assign c_req_valid=0;
    assign c_req_write=0;
    assign c_req_kind=0;
    assign c_req_layer=0;
    assign c_req_proj=0;
    assign c_req_row=0;
    assign c_req_col=0;
    assign c_req_wdata=0;
    assign c_rsp_ready=0;
  end else begin: engine
  localparam integer JS=MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 ? MAX_SEQ_LEN : 1;
  localparam integer JW=JS==1 ? 1 : $clog2(JS);
  localparam IDLE=0, CONTEXT_FLUSH=1, CONTEXT_DRAIN=2, JOURNAL_READ=3;
  localparam JOURNAL_CAPTURE=4, TARGET_COMMAND=5, TARGET_RESULT=6;
  localparam TARGET_COMMIT=7, TARGET_COMMIT_WAIT=8, APPEND_SELECT=9;
  localparam APPEND_SWITCH=10, APPEND_COMMAND=11, HIDDEN_REQUEST=12;
  localparam HIDDEN_RESPONSE=13, HIDDEN_FEED=14, APPEND_WAIT=15;
  localparam APPEND_DRAIN=16, TARGET_RELEASE=17, AFTER_TARGET=18;
  localparam BLOCK_PREPARE=19, DRAFT_SWITCH=20, DRAFT_COMMAND=21;
  localparam DRAFT_RESULT=22, DRAFT_WAIT=23, DRAFT_DRAIN=24;
  localparam VERDICT_COMMAND=25, PUBLISH=26, PUBLICATION_WAIT=27;
  localparam BLOCK_FINISH=28, COMPLETE=29, ABORT_FLUSH=30;
  localparam ABORT_DRAIN=31, CANCEL_COMPLETE=32;
  localparam SEED=0, REPLAY=1, VERIFY=2, MATERIALIZE=3;
  reg [5:0] state;
  reg armed, failed, active, cancelled_active, cancel_pending;
  reg sequence_valid, decoding, generating, use_mtp, precision;
  reg context_precision, heads_current, replay_needed, draft_owner;
  reg seed_phase, work_phase, terminal;
  reg [1:0] operation;
  reg [31:0] epoch, next_position, seed_token, seed_position;
  reg [31:0] work_token, work_position, replay_position;
  reg [31:0] anchor, first_position, last_token, last_position;
  reg [31:0] emitted, limit, eos, component;
  reg [2:0] depths, target_lanes, kept_lanes, append_lane;
  reg [2:0] visible_count, visible_accepted;
  reg [127:0] candidate_tokens, draft_tokens, verification_tokens;
  reg [127:0] target_predictions;
  reg signed [31:0] hidden_word;
  (* ramstyle="M20K", nomem2reg *) reg [32:0] journal [0:JS-1];
  reg [32:0] journal_q;
  wire enabled=rst_n && armed && !cancel;
  wire child_flush=cancel || state==CONTEXT_FLUSH ||
    state==ABORT_FLUSH || state==ABORT_DRAIN || state==CANCEL_COMPLETE;
  wire accepting=token_valid && token_ready;
  wire generation_entry=generation_enable && token_phase;
  wire command_bad=token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN ||
    (new_sequence ? token_pos!=0 :
      (!sequence_valid || token_pos!=next_position || (decoding && !token_phase))) ||
    (generation_entry && token_pos==MAX_SEQ_LEN-1);
  wire need_replay=!new_sequence && token_pos!=0 &&
    (context_precision!=fp8_enable || (mtp_enable && !heads_current));
  wire [31:0] remaining=limit-emitted;
  wire [31:0] capacity=MAX_SEQ_LEN-first_position;
  wire [31:0] block_capacity=remaining<capacity ? remaining : capacity;
  wire [2:0] block_limit=block_capacity>5 ? 3'd5 : block_capacity[2:0];
  wire [2:0] planned_depths=use_mtp && block_limit>1 ? block_limit-3'd1 : 3'd0;
  wire target_ready, target_result_valid, target_commit_ready, target_commit_done;
  wire target_release_ready, target_fault, target_idle, target_verify_active;
  wire [127:0] target_result_tokens;
  wire h_req_ready, h_rsp_valid, h_rsp_error;
  wire signed [31:0] h_rsp_data;
  wire [28:0] t_req_valid, t_req_write, t_rsp_ready;
  wire [115:0] t_req_kind;
  wire [927:0] t_req_layer, t_req_row, t_req_col, t_req_wdata;
  wire [86:0] t_req_proj;
  wire draft_ready, draft_in_ready, draft_result_valid, draft_done, draft_error;
  wire draft_idle, draft_fault, proposed_pulse;
  wire target_shared, target_prefetch, draft_shared, draft_prefetch;
  wire [31:0] target_cache_dense, target_expert_dense, draft_cache_dense, draft_expert_dense;
  wire [127:0] draft_result_tokens;
  wire [2:0] draft_proposed;
  wire [8:0] d_req_valid, d_req_write, d_rsp_ready;
  wire [35:0] d_req_kind;
  wire [287:0] d_req_layer, d_req_row, d_req_col, d_req_wdata;
  wire [26:0] d_req_proj;
  wire verdict_ready, publication_done, publication_error;
  wire v_valid, v_last, v_accepted_retire, v_rejected;
  wire [31:0] v_token, v_pos;
  wire [2:0] v_count, v_accepted;
  wire retire=spec_valid && spec_ready;
  wire append_command=state==APPEND_COMMAND;
  wire speculate_command=state==DRAFT_COMMAND;
  wire [31:0] append_position=work_position+{29'd0,append_lane};
  wire [31:0] append_token=operation==VERIFY ?
    candidate_tokens[append_lane*32+:32] : work_token;
  wire operation_fault=transport_fault || target_fault || draft_fault ||
    (draft_done && draft_error) || (publication_done && publication_error) ||
    (state==HIDDEN_RESPONSE && h_rsp_valid && h_rsp_error) ||
    (state==DRAFT_RESULT && draft_result_valid && draft_proposed!=depths);
  wire public_logits=enabled && active && !generating && operation==SEED;
  wire [2:0] visible_kept=visible_count<visible_accepted+3'd1 ?
    visible_count : visible_accepted+3'd1;
  wire [2:0] verified_kept=visible_kept<target_lanes ? visible_kept : target_lanes;

  if (MTP_K!=4 || MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: MTP engine geometry");
  end
  assign token_ready=enabled && state==IDLE && transport_idle &&
    target_idle && draft_idle && !transport_fault;
  assign idle=token_ready;
  assign transport_flush=cancel || state==CONTEXT_FLUSH || state==ABORT_FLUSH;
  assign active_fp8=rst_n && precision;
  assign active_epoch=rst_n ? epoch : 32'd0;
  assign done=enabled && (state==COMPLETE ||
    (state==CANCEL_COMPLETE && cancelled_active));
  assign error=done && failed;
  assign cancel_done=enabled && state==CANCEL_COMPLETE;
  assign generation_active=enabled && active && generating && state!=COMPLETE &&
    state!=CANCEL_COMPLETE;
  assign spec_valid=enabled && generating && state==PUBLISH && v_valid;
  assign spec_token=spec_valid ? v_token : 32'd0;
  assign spec_pos=spec_valid ? v_pos : 32'd0;
  assign spec_last=spec_valid && v_last;
  assign spec_count=spec_valid ? v_count : 3'd0;
  assign spec_accepted=spec_valid ? v_accepted : 3'd0;
  assign accepted_retire=spec_valid && spec_ready && v_accepted_retire;
  assign rejected_block=enabled && generating && v_rejected;
  assign verification_active=enabled && operation==VERIFY && target_verify_active;
  assign proposed_increment=enabled && proposed_pulse ? 3'd1 : 3'd0;
  assign shared_busy=enabled && (draft_owner ? draft_shared : target_shared);
  assign prefetch_busy=enabled && (draft_owner ? draft_prefetch : target_prefetch);
  assign cache_dense_increment=enabled && !draft_owner ? target_cache_dense : 32'd0;
  assign expert_dense_increment=!enabled ? 32'd0 :
    draft_owner ? draft_expert_dense : target_expert_dense;

  for (genvar c=0;c<29;c=c+1) begin: shared_transport
    if (c<9) begin: with_draft
      assign c_req_valid[c]=!child_flush && (draft_owner ? d_req_valid[c] : t_req_valid[c]);
      assign c_req_write[c]=c_req_valid[c] && (draft_owner ? d_req_write[c] : t_req_write[c]);
      assign c_req_kind[c*4+:4]=!c_req_valid[c] ? 4'd0 :
        draft_owner ? d_req_kind[c*4+:4] : t_req_kind[c*4+:4];
      assign c_req_layer[c*32+:32]=!c_req_valid[c] ? 32'd0 :
        draft_owner ? d_req_layer[c*32+:32] : t_req_layer[c*32+:32];
      assign c_req_proj[c*3+:3]=!c_req_valid[c] ? 3'd0 :
        draft_owner ? d_req_proj[c*3+:3] : t_req_proj[c*3+:3];
      assign c_req_row[c*32+:32]=!c_req_valid[c] ? 32'd0 :
        draft_owner ? d_req_row[c*32+:32] : t_req_row[c*32+:32];
      assign c_req_col[c*32+:32]=!c_req_valid[c] ? 32'd0 :
        draft_owner ? d_req_col[c*32+:32] : t_req_col[c*32+:32];
      assign c_req_wdata[c*32+:32]=!c_req_valid[c] ? 32'd0 :
        draft_owner ? d_req_wdata[c*32+:32] : t_req_wdata[c*32+:32];
      assign c_rsp_ready[c]=!child_flush && (draft_owner ? d_rsp_ready[c] : t_rsp_ready[c]);
    end else begin: target_only
      assign c_req_valid[c]=!child_flush && !draft_owner && t_req_valid[c];
      assign c_req_write[c]=c_req_valid[c] && t_req_write[c];
      assign c_req_kind[c*4+:4]=c_req_valid[c] ? t_req_kind[c*4+:4] : 4'd0;
      assign c_req_layer[c*32+:32]=c_req_valid[c] ? t_req_layer[c*32+:32] : 32'd0;
      assign c_req_proj[c*3+:3]=c_req_valid[c] ? t_req_proj[c*3+:3] : 3'd0;
      assign c_req_row[c*32+:32]=c_req_valid[c] ? t_req_row[c*32+:32] : 32'd0;
      assign c_req_col[c*32+:32]=c_req_valid[c] ? t_req_col[c*32+:32] : 32'd0;
      assign c_req_wdata[c*32+:32]=c_req_valid[c] ? t_req_wdata[c*32+:32] : 32'd0;
      assign c_rsp_ready[c]=!child_flush && !draft_owner && t_rsp_ready[c];
    end
  end

  anvil_d2_target_lanes #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.KV_LORA_RANK(KV_LORA_RANK),
    .QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),.QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),
    .V_HEAD_DIM(V_HEAD_DIM),.ROUTED_EXPERTS(ROUTED_EXPERTS),.TOP_K(TOP_K),
    .SHARED_EXPERTS(SHARED_EXPERTS),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
    .FIRST_DENSE_LAYERS(FIRST_DENSE_LAYERS),.VOCAB_SIZE(VOCAB_SIZE),
    .MAX_SEQ_LEN(MAX_SEQ_LEN),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
  ) target (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),
    .cmd_valid(enabled && state==TARGET_COMMAND),.cmd_ready(target_ready),
    .cmd_epoch(epoch),.cmd_first_pos(work_position),
    .cmd_tokens(operation==VERIFY ? candidate_tokens : {96'd0,work_token}),
    .cmd_lanes(operation==VERIFY ? target_lanes : 3'd1),
    .cmd_phase(work_phase),.cmd_fp8(precision),
    .cmd_emit_logits(!generating && operation==SEED),
    .result_valid(target_result_valid),.result_ready(enabled && state==TARGET_RESULT),
    .result_tokens(target_result_tokens),
    .commit_valid(enabled && state==TARGET_COMMIT),.commit_ready(target_commit_ready),
    .commit_count(kept_lanes),.commit_done(target_commit_done),
    .release_valid(enabled && state==TARGET_RELEASE && transport_idle),.release_ready(target_release_ready),
    .h_req_valid(enabled && state==HIDDEN_REQUEST),.h_req_ready(h_req_ready),
    .h_req_lane(append_lane[1:0]),.h_req_index(component),
    .h_rsp_valid(h_rsp_valid),.h_rsp_ready(enabled && state==HIDDEN_RESPONSE),
    .h_rsp_data(h_rsp_data),.h_rsp_error(h_rsp_error),
    .logit_valid(logit_valid),.logit_ready(public_logits && logit_ready),
    .logit_index(logit_index),.logit_data(logit_data),
    .fault(target_fault),.idle(target_idle),.verify_active(target_verify_active),
    .shared_busy(target_shared),.prefetch_busy(target_prefetch),
    .cache_dense_increment(target_cache_dense),.expert_dense_increment(target_expert_dense),
    .c_req_valid(t_req_valid),.c_req_ready(draft_owner ? 29'd0 : c_req_ready),
    .c_req_write(t_req_write),.c_req_kind(t_req_kind),.c_req_layer(t_req_layer),
    .c_req_proj(t_req_proj),.c_req_row(t_req_row),.c_req_col(t_req_col),
    .c_req_wdata(t_req_wdata),.c_rsp_valid(draft_owner ? 29'd0 : c_rsp_valid),
    .c_rsp_ready(t_rsp_ready),.c_rsp_rdata(c_rsp_rdata),
    .c_rsp_error(draft_owner ? 29'd0 : c_rsp_error)
  );
  anvil_d2_draft_sequence #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.KV_LORA_RANK(KV_LORA_RANK),
    .QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),.QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),
    .V_HEAD_DIM(V_HEAD_DIM),.ROUTED_EXPERTS(ROUTED_EXPERTS),.TOP_K(TOP_K),
    .SHARED_EXPERTS(SHARED_EXPERTS),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
    .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
  ) draft (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),
    .cmd_valid(enabled && (append_command || speculate_command)),.cmd_ready(draft_ready),
    .cmd_speculate(speculate_command),.cmd_new_sequence(append_command && append_position==0),
    .cmd_epoch(epoch),.cmd_token(speculate_command ? anchor : append_token),
    .cmd_pos(speculate_command ? first_position : append_position),.cmd_depths(depths),
    .in_valid(enabled && state==HIDDEN_FEED),.in_ready(draft_in_ready),.in_hidden(hidden_word),
    .result_valid(draft_result_valid),.result_ready(enabled && state==DRAFT_RESULT),
    .result_draft(draft_result_tokens),.result_proposed(draft_proposed),
    .proposed_pulse(proposed_pulse),.done(draft_done),.error(draft_error),
    .idle(draft_idle),.fault(draft_fault),
    .shared_busy(draft_shared),.prefetch_busy(draft_prefetch),
    .cache_dense_increment(draft_cache_dense),.expert_dense_increment(draft_expert_dense),
    .c_req_valid(d_req_valid),.c_req_ready(draft_owner ? c_req_ready[8:0] : 9'd0),
    .c_req_write(d_req_write),.c_req_kind(d_req_kind),.c_req_layer(d_req_layer),
    .c_req_proj(d_req_proj),.c_req_row(d_req_row),.c_req_col(d_req_col),
    .c_req_wdata(d_req_wdata),.c_rsp_valid(draft_owner ? c_rsp_valid[8:0] : 9'd0),
    .c_rsp_ready(d_rsp_ready),.c_rsp_rdata(c_rsp_rdata[287:0]),
    .c_rsp_error(draft_owner ? c_rsp_error[8:0] : 9'd0)
  );
  anvil_d2_mtp_verdict #(.MAX_SEQ_LEN(MAX_SEQ_LEN),.MTP_K(MTP_K)) verdict (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),
    .cmd_valid(enabled && state==VERDICT_COMMAND),.cmd_ready(verdict_ready),
    .cmd_anchor(anchor),.cmd_draft(draft_tokens),.cmd_verify(verification_tokens),
    .cmd_proposed(depths),.cmd_limit(block_limit),.cmd_first_pos(first_position),.cmd_eos(eos),
    .spec_valid(v_valid),.spec_ready(enabled && state==PUBLISH && spec_ready),
    .spec_token(v_token),.spec_pos(v_pos),.spec_last(v_last),
    .spec_count(v_count),.spec_accepted(v_accepted),
    .accepted_retire(v_accepted_retire),.rejected_block(v_rejected),
    .publication_done(publication_done),.publication_error(publication_error)
  );

  always @(posedge clk) begin
    if (accepting && !command_bad)
      journal[JW'(token_pos)]<={token_phase,token_id};
    else if (retire) journal[JW'(spec_pos)]<={1'b1,spec_token};
    if (enabled && state==JOURNAL_READ) journal_q<=journal[JW'(replay_position)];
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; active<=0; cancelled_active<=0; cancel_pending<=0;
      sequence_valid<=0; decoding<=0; generating<=0; use_mtp<=0; precision<=0;
      context_precision<=0; heads_current<=0; replay_needed<=0; draft_owner<=0;
      seed_phase<=0; work_phase<=0; terminal<=0; operation<=SEED;
      epoch<=0; next_position<=0; seed_token<=0; seed_position<=0; work_token<=0;
      work_position<=0; replay_position<=0; anchor<=0; first_position<=0;
      last_token<=0; last_position<=0; emitted<=0; limit<=1; eos<=VOCAB_SIZE-1;
      component<=0; depths<=0; target_lanes<=0; kept_lanes<=0; append_lane<=0;
      visible_count<=0; visible_accepted<=0; candidate_tokens<=0; draft_tokens<=0;
      verification_tokens<=0; target_predictions<=0; hidden_word<=0;
    end else begin
      armed<=1;
      if (cancel) begin
        failed<=1; sequence_valid<=0; decoding<=0; heads_current<=0;
        cancel_pending<=1; cancelled_active<=cancelled_active || active; state<=ABORT_DRAIN;
      end else if (operation_fault && state!=ABORT_FLUSH && state!=ABORT_DRAIN &&
          state!=CANCEL_COMPLETE && !(state==COMPLETE && failed)) begin
        failed<=1; sequence_valid<=0; decoding<=0; heads_current<=0;
        cancel_pending<=0; cancelled_active<=0; state<=ABORT_FLUSH;
      end else begin
        if (retire) begin
          last_token<=spec_token; last_position<=spec_pos;
          emitted<=emitted+1'b1; next_position<=spec_pos+1'b1;
          visible_count<=spec_count; visible_accepted<=spec_accepted;
          if (spec_token==eos || emitted+32'd1==limit || spec_pos==MAX_SEQ_LEN-1)
            terminal<=1;
        end
        case (state)
          IDLE: if (accepting) begin
            active<=1; failed<=0; cancelled_active<=0; cancel_pending<=0;
            generating<=generation_entry; use_mtp<=mtp_enable; precision<=fp8_enable;
            seed_token<=token_id; seed_position<=token_pos; seed_phase<=token_phase;
            emitted<=0; limit<=generation_limit; eos<=eos_token; terminal<=0;
            draft_owner<=0; depths<=0; target_lanes<=1; kept_lanes<=1;
            replay_needed<=need_replay; replay_position<=0;
            if (command_bad) begin
              failed<=1; sequence_valid<=0; decoding<=0; heads_current<=0; state<=ABORT_FLUSH;
            end else begin
              work_token<=token_id; work_position<=token_pos; work_phase<=token_phase;
              operation<=SEED;
              if (!mtp_enable) heads_current<=0;
              if (new_sequence || need_replay) begin
                epoch<=epoch+1'b1; heads_current<=0; state<=CONTEXT_FLUSH;
                if (new_sequence) begin sequence_valid<=1; decoding<=token_phase; end
              end else state<=TARGET_COMMAND;
              if (token_phase) decoding<=1;
            end
          end
          CONTEXT_FLUSH: state<=CONTEXT_DRAIN;
          CONTEXT_DRAIN: if (transport_drained && transport_idle) begin
            if (replay_needed) state<=JOURNAL_READ;
            else state<=TARGET_COMMAND;
          end
          JOURNAL_READ: state<=JOURNAL_CAPTURE;
          JOURNAL_CAPTURE: begin
            operation<=REPLAY; work_token<=journal_q[31:0]; work_phase<=journal_q[32];
            work_position<=replay_position; kept_lanes<=1; state<=TARGET_COMMAND;
          end
          TARGET_COMMAND: if (target_ready) state<=TARGET_RESULT;
          TARGET_RESULT: if (target_result_valid) begin
            target_predictions<=target_result_tokens;
            if (operation==VERIFY) begin
              verification_tokens<=target_result_tokens; state<=VERDICT_COMMAND;
            end else begin
              anchor<=target_result_tokens[31:0]; kept_lanes<=1; state<=TARGET_COMMIT;
            end
          end
          TARGET_COMMIT: if (target_commit_ready) state<=TARGET_COMMIT_WAIT;
          TARGET_COMMIT_WAIT: if (target_commit_done) begin append_lane<=0; state<=APPEND_SELECT; end
          APPEND_SELECT: begin
            if (use_mtp && append_lane<kept_lanes) state<=APPEND_SWITCH;
            else state<=TARGET_RELEASE;
          end
          APPEND_SWITCH: if (transport_idle) begin
            draft_owner<=1; component<=0; state<=APPEND_COMMAND;
          end
          APPEND_COMMAND: if (draft_ready) state<=HIDDEN_REQUEST;
          HIDDEN_REQUEST: if (h_req_ready) state<=HIDDEN_RESPONSE;
          HIDDEN_RESPONSE: if (h_rsp_valid) begin hidden_word<=h_rsp_data; state<=HIDDEN_FEED; end
          HIDDEN_FEED: if (draft_in_ready) begin
            if (component==HIDDEN_SIZE-1) state<=APPEND_WAIT;
            else begin component<=component+1'b1; state<=HIDDEN_REQUEST; end
          end
          APPEND_WAIT: if (draft_done) state<=APPEND_DRAIN;
          APPEND_DRAIN: if (draft_idle && transport_idle) begin
            draft_owner<=0; append_lane<=append_lane+1'b1; state<=APPEND_SELECT;
          end
          TARGET_RELEASE: if (target_release_ready && transport_idle) state<=AFTER_TARGET;
          AFTER_TARGET: begin
            if (operation==REPLAY) begin
              if (replay_position+32'd1<seed_position) begin
                replay_position<=replay_position+1'b1; state<=JOURNAL_READ;
              end else begin
                operation<=SEED; work_token<=seed_token; work_position<=seed_position;
                work_phase<=seed_phase; kept_lanes<=1; replay_needed<=0; state<=TARGET_COMMAND;
              end
            end else if (operation==SEED) begin
              next_position<=seed_position+1'b1; context_precision<=precision;
              heads_current<=use_mtp;
              if (generating) begin first_position<=seed_position+1'b1; state<=BLOCK_PREPARE; end
              else state<=COMPLETE;
            end else if (operation==VERIFY) begin
              if (visible_count>kept_lanes) begin
                operation<=MATERIALIZE; work_token<=last_token; work_position<=last_position;
                work_phase<=1; kept_lanes<=1; state<=TARGET_COMMAND;
              end else begin
                anchor<=target_predictions[(kept_lanes-3'd1)*32+:32]; state<=BLOCK_FINISH;
              end
            end else state<=BLOCK_FINISH;
          end
          BLOCK_PREPARE: begin
            depths<=planned_depths; target_lanes<=planned_depths;
            draft_tokens<=0; verification_tokens<=0; visible_count<=0; visible_accepted<=0;
            if (planned_depths!=0) state<=DRAFT_SWITCH;
            else state<=VERDICT_COMMAND;
          end
          DRAFT_SWITCH: if (transport_idle) begin draft_owner<=1; state<=DRAFT_COMMAND; end
          DRAFT_COMMAND: if (draft_ready) state<=DRAFT_RESULT;
          DRAFT_RESULT: if (draft_result_valid) begin
            draft_tokens<=draft_result_tokens;
            candidate_tokens<={draft_result_tokens[95:0],anchor};
            state<=DRAFT_WAIT;
          end
          DRAFT_WAIT: if (draft_done) state<=DRAFT_DRAIN;
          DRAFT_DRAIN: if (draft_idle && transport_idle) begin
            draft_owner<=0; work_position<=first_position; work_phase<=1;
            operation<=VERIFY; state<=TARGET_COMMAND;
          end
          VERDICT_COMMAND: if (verdict_ready) state<=PUBLISH;
          PUBLISH: if (retire && spec_last) state<=PUBLICATION_WAIT;
          PUBLICATION_WAIT: if (publication_done) begin
            if (depths!=0) begin kept_lanes<=verified_kept; state<=TARGET_COMMIT; end
            else begin
              operation<=MATERIALIZE; work_token<=last_token; work_position<=last_position;
              work_phase<=1; kept_lanes<=1; state<=TARGET_COMMAND;
            end
          end
          BLOCK_FINISH: begin
            heads_current<=use_mtp; context_precision<=precision;
            if (terminal) state<=COMPLETE;
            else begin first_position<=last_position+1'b1; state<=BLOCK_PREPARE; end
          end
          COMPLETE: begin active<=0; generating<=0; state<=IDLE; end
          ABORT_FLUSH: state<=ABORT_DRAIN;
          ABORT_DRAIN: if (transport_drained) begin
            active<=0;
            if (cancel_pending) state<=CANCEL_COMPLETE;
            else state<=COMPLETE;
          end
          CANCEL_COMPLETE: begin
            active<=0; generating<=0; cancelled_active<=0; cancel_pending<=0; state<=IDLE;
          end
          default: begin failed<=1; sequence_valid<=0; heads_current<=0; state<=ABORT_FLUSH; end
        endcase
      end
    end
  end
  end endgenerate
endmodule
