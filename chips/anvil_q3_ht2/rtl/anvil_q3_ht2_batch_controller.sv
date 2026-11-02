module anvil_q3_ht2_batch_controller #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter CACHE_MODE=1, KV_RESIDENT_GROUPS=64
) (
  input wire clk, rst_n, cancel, invalidate, run_enable, memory_idle, memory_fault,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence, token_phase,
  input wire sparse_enable,
  input wire [15:0] sparse_threshold_f16,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire done, error, cancel_done, idle, transport_flush,
  input wire spec_req_valid,
  output wire spec_req_ready,
  input wire [31:0] spec_req_id, spec_base_pos,
  input wire [3:0] draft_mask,
  input wire [127:0] draft_tokens,
  input wire [11:0] draft_parents,
  output wire spec_rsp_valid,
  input wire spec_rsp_ready,
  output wire [31:0] spec_rsp_id,
  output wire spec_rsp_error,
  output wire [3:0] accepted_mask,
  output wire [2:0] accepted_count,
  output wire [127:0] accepted_tokens,
  output wire [31:0] next_token, committed_pos,
  output wire [6:0] memory_req_valid, memory_req_write,
  input wire [6:0] memory_req_ready,
  output wire [230:0] memory_req_address,
  output wire [55:0] memory_req_burstcount,
  output wire [3583:0] memory_req_wdata,
  output wire [447:0] memory_req_byteenable,
  input wire [6:0] memory_rsp_valid, memory_rsp_error,
  input wire [3583:0] memory_rsp_rdata
);
  localparam IDLE=0, SEQUENCE_RESET=1, START=2, RUN=3,
    COMPLETE=4, RECOVER_FLUSH=5, RECOVER_DRAIN=6,
    CANCEL_DRAIN=7, CANCEL_COMPLETE=8, INVALID_COMPLETE=9;
  reg [3:0] state;
  reg speculative, sequence_valid, decoding, failed, cancelled_active;
  reg sparse;
  reg [15:0] threshold;
  reg [31:0] epoch, id_counter, id, base, root_target, prefix_count, cached_next;
  reg [3:0] mask;
  reg [127:0] tokens;
  reg [11:0] parents;
  wire running=rst_n && !cancel;
  wire children_rst_n=rst_n && state!=SEQUENCE_RESET;
  wire children_flush=cancel || state==RECOVER_FLUSH;
  wire decoder_ready, decoder_idle, decoder_drained, decoder_done, decoder_error;
  wire decoder_fault, decoder_logit_valid, decoder_logit_ready;
  wire [31:0] decoder_logit_id, decoder_logit_epoch, decoder_logit_index;
  wire [1:0] decoder_logit_node;
  wire signed [31:0] decoder_logit_data;
  wire decoder_logit_last;
  wire stage_valid, stage_ready, stage_value;
  wire [31:0] stage_id, stage_epoch, stage_layer, stage_head, stage_group;
  wire [1:0] stage_node;
  wire [511:0] stage_record;
  wire verifier_ready, verifier_idle, verifier_drained, verifier_fault;
  wire eval_valid, eval_ready;
  wire [31:0] eval_id, eval_epoch;
  wire [3:0] eval_mask;
  wire [127:0] eval_tokens, eval_positions;
  wire [11:0] eval_parents;
  wire [15:0] eval_visibility;
  wire verifier_logit_ready, response_valid, response_ready, response_error;
  wire [31:0] response_id, response_next, response_position;
  wire [3:0] response_mask;
  wire [2:0] response_count;
  wire [127:0] response_tokens;
  wire publication_valid;
  wire [31:0] publication_pos, publication_next;
  wire all_drained=memory_idle && decoder_drained && verifier_drained;
  wire eligible=running && run_enable && state==IDLE &&
    memory_idle && !memory_fault && decoder_idle && verifier_idle;
  wire token_fire=token_valid && token_ready;
  wire spec_fire=spec_req_valid && spec_req_ready;

  assign token_ready=eligible;
  assign spec_req_ready=eligible && !token_valid && sequence_valid && prefix_count!=0;
  assign idle=running && state==IDLE && all_drained;
  assign transport_flush=rst_n && children_flush;
  assign done=running && ((!speculative && (state==COMPLETE || state==INVALID_COMPLETE)) ||
    (state==CANCEL_COMPLETE && cancelled_active));
  assign error=done && (failed || state==CANCEL_COMPLETE);
  assign cancel_done=running && state==CANCEL_COMPLETE;
  assign logit_valid=running && state==RUN && !speculative &&
    decoder_logit_valid && verifier_logit_ready;
  assign logit_index=logit_valid ? decoder_logit_index : 32'd0;
  assign logit_data=logit_valid ? decoder_logit_data : 32'sd0;
  assign decoder_logit_ready=running && state==RUN && verifier_logit_ready &&
    (speculative || logit_ready);
  assign eval_ready=running && state==RUN && decoder_ready;
  assign response_ready=running && state==RUN && (speculative ? spec_rsp_ready : 1'b1);
  assign spec_rsp_valid=running && state==RUN && speculative && response_valid;
  assign spec_rsp_id=spec_rsp_valid ? response_id : 32'd0;
  assign spec_rsp_error=spec_rsp_valid && response_error;
  assign accepted_mask=spec_rsp_valid && !response_error ? response_mask : 4'd0;
  assign accepted_count=spec_rsp_valid && !response_error ? response_count : 3'd0;
  assign accepted_tokens=spec_rsp_valid && !response_error ? response_tokens : 128'd0;
  assign next_token=spec_rsp_valid && !response_error ? response_next : 32'd0;
  assign committed_pos=spec_rsp_valid && !response_error ? response_position : 32'd0;
  assign memory_req_burstcount[55:48]=memory_req_valid[6] ? 8'd1 : 8'd0;

  anvil_q3_ht2_spec_verifier #(
    .NUM_LAYERS(NUM_LAYERS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_MODE(CACHE_MODE),.VOCAB_SIZE(VOCAB_SIZE)
  ) spec_verifier (
    .clk(clk),.rst_n(children_rst_n),.flush(children_flush),
    .cmd_valid(running && state==START),.cmd_ready(verifier_ready),
    .cmd_id(id),.cmd_epoch(epoch),.cmd_base_pos(base),.cmd_mask(mask),
    .cmd_tokens(tokens),.cmd_parents(parents),.cmd_root_target(root_target),
    .eval_valid(eval_valid),.eval_ready(eval_ready),.eval_id(eval_id),.eval_epoch(eval_epoch),
    .eval_mask(eval_mask),.eval_tokens(eval_tokens),.eval_parents(eval_parents),
    .eval_positions(eval_positions),.eval_visibility(eval_visibility),
    .logit_valid(decoder_logit_valid && running && state==RUN &&
      (speculative || logit_ready)),.logit_ready(verifier_logit_ready),
    .logit_id(decoder_logit_id),.logit_epoch(decoder_logit_epoch),
    .logit_node(decoder_logit_node),.logit_index(decoder_logit_index),
    .logit_data(decoder_logit_data),.logit_last(decoder_logit_last),
    .eval_done(decoder_done),.eval_error(decoder_error),
    .stage_valid(stage_valid),.stage_ready(stage_ready),.stage_id(stage_id),
    .stage_epoch(stage_epoch),.stage_node(stage_node),.stage_layer(stage_layer),
    .stage_head(stage_head),.stage_value(stage_value),.stage_group(stage_group),
    .stage_record(stage_record),.out_valid(response_valid),.out_ready(response_ready),
    .out_id(response_id),.out_error(response_error),.out_mask(response_mask),
    .out_count(response_count),.out_tokens(response_tokens),
    .out_next_token(response_next),.out_committed_pos(response_position),
    .idle(verifier_idle),.fault(verifier_fault),.drain_done(verifier_drained),
    .publication_valid(publication_valid),.publication_pos(publication_pos),
    .publication_next_token(publication_next),
    .memory_req_valid(memory_req_valid[6]),.memory_req_ready(memory_req_ready[6]),
    .memory_req_write(memory_req_write[6]),.memory_req_address(memory_req_address[198+:33]),
    .memory_req_wdata(memory_req_wdata[3072+:512]),
    .memory_req_byteenable(memory_req_byteenable[384+:64]),
    .memory_rsp_valid(memory_rsp_valid[6]),.memory_rsp_error(memory_rsp_error[6]),
    .memory_rsp_rdata(memory_rsp_rdata[3072+:512])
  );
  anvil_q3_ht2_decoder #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .GROUP_SIZE(GROUP_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),
    .CACHE_MODE(CACHE_MODE),.KV_RESIDENT_GROUPS(KV_RESIDENT_GROUPS)
  ) batched_decoder (
    .clk(clk),.rst_n(children_rst_n),.flush(children_flush),
    .cmd_valid(eval_valid && running && state==RUN),.cmd_ready(decoder_ready),
    .cmd_id(eval_id),.cmd_epoch(eval_epoch),.cmd_base_pos(base),.cmd_mask(eval_mask),
    .cmd_tokens(eval_tokens),.cmd_positions(eval_positions),.cmd_parents(eval_parents),
    .cmd_visibility(eval_visibility),.cmd_sparse_enable(sparse),.cmd_threshold_f16(threshold),
    .done(decoder_done),.error(decoder_error),.idle(decoder_idle),
    .fault(decoder_fault),.drain_done(decoder_drained),
    .logit_valid(decoder_logit_valid),.logit_ready(decoder_logit_ready),
    .logit_id(decoder_logit_id),.logit_epoch(decoder_logit_epoch),
    .logit_node(decoder_logit_node),.logit_index(decoder_logit_index),
    .logit_data(decoder_logit_data),.logit_last(decoder_logit_last),
    .argmax_valid(),.argmax_tokens(),
    .stage_valid(stage_valid),.stage_ready(stage_ready),.stage_id(stage_id),
    .stage_epoch(stage_epoch),.stage_node(stage_node),.stage_layer(stage_layer),
    .stage_head(stage_head),.stage_value(stage_value),.stage_group(stage_group),
    .stage_record(stage_record),.memory_req_valid(memory_req_valid[5:0]),
    .memory_req_ready(memory_req_ready[5:0]),.memory_req_write(memory_req_write[5:0]),
    .memory_req_address(memory_req_address[197:0]),
    .memory_req_burstcount(memory_req_burstcount[47:0]),
    .memory_req_wdata(memory_req_wdata[3071:0]),
    .memory_req_byteenable(memory_req_byteenable[383:0]),
    .memory_rsp_valid(memory_rsp_valid[5:0]),.memory_rsp_error(memory_rsp_error[5:0]),
    .memory_rsp_rdata(memory_rsp_rdata[3071:0]),.physical_read_beats()
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; speculative<=0; sequence_valid<=0; decoding<=0; failed<=0;
      cancelled_active<=0; sparse<=0; threshold<=0; epoch<=0; id_counter<=0;
      id<=0; base<=0; root_target<=0; prefix_count<=0; cached_next<=0;
      mask<=0; tokens<=0; parents<=0;
    end else if (cancel) begin
      if (state!=CANCEL_DRAIN && state!=CANCEL_COMPLETE)
        cancelled_active<=state!=IDLE;
      state<=CANCEL_DRAIN; failed<=0;
      id<=0; base<=0; root_target<=0; mask<=0; tokens<=0; parents<=0;
      sparse<=0; threshold<=0;
    end else begin
      if (publication_valid) begin
        prefix_count<=publication_pos; cached_next<=publication_next;
        sequence_valid<=1;
      end
      if (invalidate) begin sequence_valid<=0; cached_next<=0; end
      case (state)
        IDLE: begin
          cancelled_active<=0;
          if (token_fire) begin
            speculative<=0; failed<=0; sparse<=sparse_enable;
            threshold<=sparse_threshold_f16; id<=id_counter; id_counter<=id_counter+1'b1;
            base<=token_pos; root_target<=token_id;
            mask<=4'b0001; tokens<={96'd0,token_id}; parents<=12'd4;
            if (token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN ||
                (new_sequence && token_pos!=0) ||
                (!new_sequence && (!sequence_valid || token_pos!=prefix_count ||
                  (decoding && !token_phase)))) begin
              failed<=1; state<=INVALID_COMPLETE;
            end else if (new_sequence) begin
              epoch<=epoch+1'b1; prefix_count<=0; cached_next<=0;
              sequence_valid<=0; decoding<=token_phase; state<=SEQUENCE_RESET;
            end else begin
              if (token_phase) decoding<=1;
              state<=START;
            end
          end else if (spec_fire) begin
            speculative<=1; failed<=0; decoding<=1; sparse<=sparse_enable;
            threshold<=sparse_threshold_f16; id<=spec_req_id; base<=spec_base_pos;
            root_target<=cached_next; mask<=draft_mask; tokens<=draft_tokens;
            parents<=draft_parents; state<=START;
          end
        end
        SEQUENCE_RESET: state<=START;
        START: if (verifier_ready) state<=RUN;
        RUN: if (response_valid && response_ready) begin
          failed<=response_error; state<=COMPLETE;
        end
        COMPLETE: begin
          id<=0; base<=0; root_target<=0; mask<=0; tokens<=0; parents<=0;
          sparse<=0; threshold<=0;
          if (failed || decoder_fault || verifier_fault || memory_fault)
            state<=RECOVER_FLUSH;
          else state<=IDLE;
        end
        INVALID_COMPLETE: state<=RECOVER_FLUSH;
        RECOVER_FLUSH: state<=RECOVER_DRAIN;
        RECOVER_DRAIN: if (all_drained) state<=IDLE;
        CANCEL_DRAIN: if (all_drained) state<=CANCEL_COMPLETE;
        CANCEL_COMPLETE: begin cancelled_active<=0; state<=RECOVER_FLUSH; end
        default: begin failed<=1; state<=RECOVER_FLUSH; end
      endcase
    end
  end
endmodule
