module anvil_qn1_top #(
  parameter PROFILE=3, COMPACT=0,
  parameter NUM_LAYERS=PROFILE==3 ? 36 : 28,
  parameter HIDDEN_SIZE=PROFILE==1 ? 1024 : PROFILE==2 ? 2048 : 2560,
  parameter INTERMEDIATE_SIZE=PROFILE==1 ? 3072 : PROFILE==2 ? 6144 : 9728,
  parameter NUM_Q_HEADS=PROFILE==3 ? 32 : 16, NUM_KV_HEADS=8,
  parameter HEAD_DIM=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=40960,
  parameter GROUP_SIZE=128, BANKS=8, QUEUE_DEPTH=3,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) ? BANKS : 1
) (
  input wire clk, rst_n, cancel, token_valid, new_sequence, token_phase, logit_ready,
  input wire [31:0] token_id, token_pos,
  output wire token_ready, logit_valid, done, error, cancel_done,
  output wire [31:0] logit_index, logit_data,
  output wire [SB-1:0] mem_req_valid, mem_req_write,
  input wire [SB-1:0] mem_req_ready,
  output wire [SB*4-1:0] mem_req_kind,
  output wire [SB*32-1:0] mem_req_layer, mem_req_row, mem_req_col, mem_req_wdata,
  output wire [SB*3-1:0] mem_req_proj,
  output wire [SB*64-1:0] mem_req_tag,
  input wire [SB-1:0] mem_rsp_valid, mem_rsp_error,
  output wire [SB-1:0] mem_rsp_ready,
  input wire [SB*32-1:0] mem_rsp_rdata,
  input wire [SB*64-1:0] mem_rsp_tag,
  input wire draft_valid,
  output wire draft_ready,
  input wire [2:0] draft_count,
  input wire [127:0] draft_tokens,
  input wire [11:0] draft_parents,
  output wire commit_valid,
  input wire commit_ready,
  output wire [2:0] commit_count,
  output wire [159:0] commit_tokens,
  output wire [31:0] commit_pos,
  output wire think_active,
  input wire csr_valid, csr_write,
  output wire csr_ready,
  input wire [11:0] csr_addr,
  input wire [31:0] csr_wdata,
  input wire [3:0] csr_wstrb,
  output wire csr_rsp_valid,
  input wire csr_rsp_ready,
  output wire [31:0] csr_rdata,
  output wire csr_error
);
  localparam LEGAL=anvil_qn1_pkg::configuration_valid(PROFILE,COMPACT,
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,VOCAB_SIZE,MAX_SEQ_LEN,GROUP_SIZE,BANKS,QUEUE_DEPTH);
  generate if (LEGAL) begin: native
    localparam IDLE=0, CTRL_START=1, SINGLE_START=2, SINGLE_WAIT=3, ACTIVE=4;
    localparam SINGLE_FINISH=5, COMPLETE=6, CANCEL_DRAIN=7, FAULT_DRAIN=8;
    reg [3:0] state;
    reg sequence_valid, exhausted, decode_started, pending_final, input_precommitted;
    reg [31:0] next_position, pending_token, pending_position;
    reg [31:0] host_token, host_position, committed_extent, staged_extent;
    reg host_phase, backend_owned, backend_root, draft_owned;
    reg [31:0] backend_position;
    reg [127:0] owned_drafts;
    reg [2:0] owned_draft_count;
    reg done_reg, error_reg, cancel_done_reg, cancel_seen;
    wire ctrl_ready, ctrl_done, ctrl_error, ctrl_busy, ctrl_draft_ready;
    wire ctrl_commit_valid, ctrl_commit_ready;
    wire [2:0] ctrl_commit_count;
    wire [159:0] ctrl_commit_tokens;
    wire [31:0] ctrl_commit_pos;
    wire verify_valid, verify_ready, verify_rsp_ready;
    wire [2:0] verify_parent;
    wire [31:0] verify_position;
    wire [2:0] draft_event, verified_event, accepted_event, rejected_event;
    wire mode_valid, mode_value;
    wire decoder_ready, decoder_result_valid, decoder_result_ready, decoder_error;
    wire [31:0] decoder_argmax;
    wire decoder_qk_busy, decoder_qk_blocked, decoder_score_valid;
    wire [31:0] decoder_score;
    wire decoder_logit_valid;
    wire [31:0] decoder_logit_index, decoder_logit_data;
    wire dreq_valid, dreq_ready, dreq_write, drsp_valid, drsp_ready, drsp_error;
    wire [3:0] dreq_kind;
    wire [2:0] dreq_proj;
    wire [31:0] dreq_layer, dreq_row, dreq_col, dreq_wdata, dreq_tag, drsp_data, drsp_tag;
    wire bank_fault, bank_drained, bank_req_ready;
    wire [SB-1:0] bank_mem_valid, bank_mem_write;
    wire [SB*4-1:0] bank_mem_kind;
    wire [SB*3-1:0] bank_mem_proj;
    wire [SB*32-1:0] bank_mem_layer, bank_mem_row, bank_mem_col, bank_mem_data;
    wire [SB*64-1:0] bank_mem_tag;
    wire draining=state==CANCEL_DRAIN || state==FAULT_DRAIN;
    wire flush=cancel || draining;
    wire active=rst_n && !flush;
    wire token_transfer=token_valid && token_ready;
    wire draft_transfer=draft_valid && draft_ready;
    wire commit_transfer=commit_valid && commit_ready;
    wire result_transfer=decoder_result_valid && decoder_result_ready;
    wire root_publication=result_transfer &&
      (state==SINGLE_WAIT || (state==ACTIVE && backend_root));
    wire observed_valid=active && root_publication && !input_precommitted;
    wire host_request_bad=token_transfer &&
      (token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN ||
       (new_sequence ? token_pos!=0 :
        (!sequence_valid || exhausted || token_pos!=next_position ||
         (decode_started && !token_phase) ||
         (pending_final && (!token_phase || token_pos!=pending_position ||
          token_id!=pending_token)))));
    wire [32:0] batch_end={1'b0,host_position}+{30'd0,ctrl_commit_count};
    wire commit_fault=ctrl_commit_valid &&
      (state!=ACTIVE || ctrl_commit_count<1 || ctrl_commit_count>5 ||
       ctrl_commit_pos!=host_position+32'd1 || batch_end>=33'(MAX_SEQ_LEN) ||
       staged_extent!=batch_end[31:0]-32'd1 || backend_owned || !bank_drained);
    wire backend_fault=verify_valid && state==ACTIVE &&
      (verify_parent>4 || verify_position>=MAX_SEQ_LEN ||
       (verify_parent==4 ? verify_position!=host_position :
        (!draft_owned || verify_parent>=owned_draft_count ||
         !sequence_valid || staged_extent<committed_extent ||
         verify_position!=staged_extent+32'd1)));
    wire [31:0] evaluating_position=state==SINGLE_WAIT ? host_position : backend_position;
    wire cache_fault=dreq_valid && !dreq_write && (dreq_kind==9 || dreq_kind==10) &&
      ((state!=SINGLE_WAIT && (state!=ACTIVE || !backend_owned)) ||
       dreq_row>evaluating_position ||
       (dreq_row!=evaluating_position && (!sequence_valid || dreq_row>staged_extent)));
    wire logic_fault=decoder_error || ctrl_error || commit_fault || backend_fault ||
      cache_fault || host_request_bad;
    wire detected_fault=logic_fault || bank_fault;
    wire publication_ready=active && !detected_fault && state==ACTIVE &&
      !backend_owned && decoder_ready && bank_drained;
    wire decoder_start_valid=active && !detected_fault &&
      (state==SINGLE_START || (state==ACTIVE && verify_valid && !backend_owned));
    wire [31:0] decoder_start_token=state==SINGLE_START || verify_parent==4 ?
      host_token : owned_drafts[verify_parent*32+:32];
    wire [31:0] decoder_start_pos=state==SINGLE_START ? host_position : verify_position;
    assign verify_ready=active && !detected_fault && state==ACTIVE &&
      !backend_owned && decoder_ready;
    assign decoder_result_ready=active && !detected_fault && bank_drained &&
      (state==SINGLE_WAIT || (state==ACTIVE && backend_owned && verify_rsp_ready));
    assign token_ready=active && !bank_fault && !decoder_error && !ctrl_error && state==IDLE &&
      !done_reg && !error_reg && !cancel_done_reg && bank_drained &&
      csr_ready && !csr_valid && !csr_rsp_valid && !mode_valid;
    assign draft_ready=active && !detected_fault && state==ACTIVE &&
      ctrl_draft_ready && !draft_owned;
    assign commit_valid=active && !detected_fault && state==ACTIVE && ctrl_commit_valid;
    assign ctrl_commit_ready=commit_ready && commit_valid;
    assign commit_count=commit_valid ? ctrl_commit_count : 3'd0;
    assign commit_tokens=commit_valid ? ctrl_commit_tokens : 160'd0;
    assign commit_pos=commit_valid ? ctrl_commit_pos : 32'd0;
    assign logit_valid=active && !detected_fault && decoder_logit_valid;
    assign logit_index=logit_valid ? decoder_logit_index : 32'd0;
    assign logit_data=logit_valid ? decoder_logit_data : 32'd0;
    assign done=rst_n && !cancel && done_reg;
    assign error=rst_n && !cancel && error_reg;
    assign cancel_done=rst_n && cancel_done_reg;

    anvil_qn1_decoder #(.NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
        .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
        .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.VOCAB_SIZE(VOCAB_SIZE),
        .MAX_SEQ_LEN(MAX_SEQ_LEN),.GROUP_SIZE(GROUP_SIZE)) decoder (
      .clk(clk),.rst_n(rst_n),.flush(flush),.start_valid(decoder_start_valid),
      .start_ready(decoder_ready),.start_token(decoder_start_token),
      .start_pos(decoder_start_pos),.result_valid(decoder_result_valid),
      .result_ready(decoder_result_ready),.result_argmax(decoder_argmax),
      .error(decoder_error),.qk_busy(decoder_qk_busy),.qk_blocked(decoder_qk_blocked),
      .score_valid(decoder_score_valid),.score_fp32(decoder_score),
      .logit_valid(decoder_logit_valid),
      .logit_ready(logit_ready && active && !detected_fault),
      .logit_index(decoder_logit_index),.logit_data(decoder_logit_data),
      .req_valid(dreq_valid),.req_ready(dreq_ready),.req_write(dreq_write),
      .req_kind(dreq_kind),.req_proj(dreq_proj),.req_layer(dreq_layer),
      .req_row(dreq_row),.req_col(dreq_col),.req_wdata(dreq_wdata),.req_tag(dreq_tag),
      .rsp_valid(drsp_valid),.rsp_ready(drsp_ready),.rsp_data(drsp_data),
      .rsp_tag(drsp_tag),.rsp_error(drsp_error)
    );
    anvil_qn1_dual_think_ctrl #(.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN))
        dual_think_ctrl (
      .clk(clk),.rst_n(rst_n),.flush(draining),.cancel(cancel),
      .start_valid(active && state==CTRL_START),.start_ready(ctrl_ready),
      .start_pos(host_position),.busy(ctrl_busy),.done(ctrl_done),.error(ctrl_error),
      .mode_valid(mode_valid),.mode_value(mode_value),
      .observed_valid(observed_valid),.observed_token(host_token),.think_active(think_active),
      .draft_valid(draft_valid && draft_ready),.draft_ready(ctrl_draft_ready),
      .draft_count(draft_count),.draft_tokens(draft_tokens),.draft_parents(draft_parents),
      .commit_valid(ctrl_commit_valid),.commit_ready(ctrl_commit_ready),
      .commit_count(ctrl_commit_count),.commit_tokens(ctrl_commit_tokens),
      .commit_pos(ctrl_commit_pos),.publish_ready(publication_ready),
      .verify_valid(verify_valid),.verify_ready(verify_ready),
      .verify_parent(verify_parent),.verify_pos(verify_position),
      .verify_rsp_valid(active && bank_drained && decoder_result_valid &&
        state==ACTIVE && backend_owned),
      .verify_rsp_ready(verify_rsp_ready),.verify_argmax(decoder_argmax),
      .verify_error(1'b0),.event_draft_nodes(draft_event),
      .event_verified_nodes(verified_event),.event_accepted_nodes(accepted_event),
      .event_rejected_nodes(rejected_event)
    );
    wire success_exhaustion=active && !detected_fault && state==SINGLE_FINISH &&
      exhausted && bank_drained && decoder_ready;
    anvil_qn1_csr_perf #(.PROFILE(PROFILE)) csr_perf (
      .clk(clk),.rst_n(rst_n),.csr_valid(csr_valid),.csr_ready(csr_ready),
      .csr_write(csr_write),.csr_addr(csr_addr),.csr_wdata(csr_wdata),.csr_wstrb(csr_wstrb),
      .csr_rsp_valid(csr_rsp_valid),.csr_rsp_ready(csr_rsp_ready),
      .csr_rdata(csr_rdata),.csr_error(csr_error),
      .busy(state!=IDLE),.think_active(think_active),
      .qk_busy(decoder_qk_busy),.qk_blocked(decoder_qk_blocked),
      .arith_error(active && decoder_error),.mem_error(active && bank_fault),
      .sequence_done(success_exhaustion),
      .direct_tokens(commit_transfer && !think_active ? ctrl_commit_count : 3'd0),
      .think_tokens(commit_transfer && think_active ? ctrl_commit_count : 3'd0),
      .draft_nodes(draft_event),.verified_nodes(verified_event),
      .accepted_nodes(accepted_event),.rejected_nodes(rejected_event),
      .score_valid(decoder_score_valid),.score_fp32(decoder_score),
      .mode_valid(mode_valid),.mode_value(mode_value)
    );
    anvil_qn1_bank_scheduler #(.BANKS(BANKS),.QUEUE_DEPTH(QUEUE_DEPTH)) bank_scheduler (
      .clk(clk),.rst_n(rst_n),.cancel(flush),
      .req_valid(dreq_valid && !logic_fault),.req_ready(bank_req_ready),
      .req_write(dreq_write),.req_kind(dreq_kind),.req_proj(dreq_proj),
      .req_layer(dreq_layer),.req_row(dreq_row),.req_col(dreq_col),
      .req_wdata(dreq_wdata),.req_tag(dreq_tag),
      .rsp_valid(drsp_valid),.rsp_ready(drsp_ready),.rsp_data(drsp_data),
      .rsp_tag(drsp_tag),.rsp_error(drsp_error),.fault(bank_fault),.drained(bank_drained),
      .mem_req_valid(bank_mem_valid),.mem_req_ready(mem_req_ready & {SB{!logic_fault}}),
      .mem_req_write(bank_mem_write),.mem_req_kind(bank_mem_kind),
      .mem_req_proj(bank_mem_proj),.mem_req_layer(bank_mem_layer),
      .mem_req_row(bank_mem_row),.mem_req_col(bank_mem_col),.mem_req_wdata(bank_mem_data),
      .mem_req_tag(bank_mem_tag),.mem_rsp_valid(mem_rsp_valid),
      .mem_rsp_error(mem_rsp_error),.mem_rsp_ready(mem_rsp_ready),
      .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag)
    );
    assign dreq_ready=bank_req_ready && !logic_fault;
    genvar bank;
    for (bank=0;bank<SB;bank=bank+1) begin: external_banks
      wire visible=bank_mem_valid[bank] && !logic_fault;
      assign mem_req_valid[bank]=visible;
      assign mem_req_write[bank]=visible && bank_mem_write[bank];
      assign mem_req_kind[bank*4+:4]=visible ? bank_mem_kind[bank*4+:4] : 4'd0;
      assign mem_req_proj[bank*3+:3]=visible ? bank_mem_proj[bank*3+:3] : 3'd0;
      assign mem_req_layer[bank*32+:32]=visible ? bank_mem_layer[bank*32+:32] : 32'd0;
      assign mem_req_row[bank*32+:32]=visible ? bank_mem_row[bank*32+:32] : 32'd0;
      assign mem_req_col[bank*32+:32]=visible ? bank_mem_col[bank*32+:32] : 32'd0;
      assign mem_req_wdata[bank*32+:32]=visible ? bank_mem_data[bank*32+:32] : 32'd0;
      assign mem_req_tag[bank*64+:64]=visible ? bank_mem_tag[bank*64+:64] : 64'd0;
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; sequence_valid<=0; exhausted<=0; decode_started<=0;
        pending_final<=0; input_precommitted<=0; next_position<=0;
        pending_token<=0; pending_position<=0; host_token<=0; host_position<=0;
        committed_extent<=0; staged_extent<=0; host_phase<=0;
        backend_owned<=0; backend_root<=0; backend_position<=0;
        draft_owned<=0; owned_drafts<=0; owned_draft_count<=0;
        done_reg<=0; error_reg<=0; cancel_done_reg<=0; cancel_seen<=0;
      end else begin
        done_reg<=0; error_reg<=0; cancel_done_reg<=0;
        if (!cancel) cancel_seen<=0;
        else cancel_seen<=1;
        if (cancel && !cancel_seen) begin
          state<=CANCEL_DRAIN; sequence_valid<=0; exhausted<=0;
          pending_final<=0; backend_owned<=0; draft_owned<=0;
        end else if (!draining && detected_fault) begin
          state<=FAULT_DRAIN; sequence_valid<=0; exhausted<=0;
          pending_final<=0; backend_owned<=0; draft_owned<=0;
        end else begin
          if (draft_transfer) begin
            draft_owned<=1; owned_drafts<=draft_tokens; owned_draft_count<=draft_count;
          end
          if (state==ACTIVE && verify_valid && verify_ready) begin
            backend_owned<=1; backend_root<=verify_parent==4; backend_position<=verify_position;
          end
          if (result_transfer) begin
            backend_owned<=0;
            staged_extent<=state==SINGLE_WAIT ? host_position : backend_position;
            if (root_publication) begin
              sequence_valid<=1; committed_extent<=host_position; pending_final<=0;
              next_position<=host_position+32'd1;
              if (host_phase) decode_started<=1;
            end
          end
          if (commit_transfer) begin
            pending_final<=1; pending_position<=batch_end[31:0];
            pending_token<=ctrl_commit_tokens[(ctrl_commit_count-1'b1)*32+:32];
            next_position<=batch_end[31:0]; committed_extent<=batch_end[31:0]-32'd1;
          end
          case (state)
            IDLE: if (token_transfer) begin
              host_token<=token_id; host_position<=token_pos; host_phase<=token_phase;
              input_precommitted<=!new_sequence && pending_final;
              draft_owned<=0; backend_owned<=0; owned_draft_count<=0;
              if (new_sequence) begin
                sequence_valid<=0; exhausted<=0; decode_started<=0;
                pending_final<=0; committed_extent<=0; staged_extent<=0;
              end
              if (!token_phase || token_pos==MAX_SEQ_LEN-1) state<=SINGLE_START;
              else state<=CTRL_START;
            end
            CTRL_START: if (ctrl_ready) state<=ACTIVE;
            SINGLE_START: if (decoder_start_valid && decoder_ready) state<=SINGLE_WAIT;
            SINGLE_WAIT: if (result_transfer) begin
              exhausted<=host_position==MAX_SEQ_LEN-1; state<=SINGLE_FINISH;
            end
            SINGLE_FINISH: if (bank_drained && decoder_ready) begin
              done_reg<=1; state<=COMPLETE;
            end
            ACTIVE: if (ctrl_done && bank_drained && !backend_owned && decoder_ready) begin
              done_reg<=1; state<=COMPLETE;
            end
            COMPLETE: state<=IDLE;
            CANCEL_DRAIN: if (bank_drained) begin cancel_done_reg<=1; state<=COMPLETE; end
            FAULT_DRAIN: if (bank_drained) begin error_reg<=1; state<=COMPLETE; end
            default: state<=FAULT_DRAIN;
          endcase
        end
      end
    end
  end else begin: invalid_parameters
    initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: profile, geometry or address bounds");
    assign token_ready=0; assign logit_valid=0; assign done=0; assign error=0;
    assign cancel_done=0; assign logit_index=0; assign logit_data=0;
    assign mem_req_valid=0; assign mem_req_write=0; assign mem_req_kind=0;
    assign mem_req_layer=0; assign mem_req_row=0; assign mem_req_col=0;
    assign mem_req_wdata=0; assign mem_req_proj=0; assign mem_req_tag=0;
    assign mem_rsp_ready=0; assign draft_ready=0; assign commit_valid=0;
    assign commit_count=0; assign commit_tokens=0; assign commit_pos=0;
    assign think_active=0; assign csr_ready=0; assign csr_rsp_valid=0;
    assign csr_rdata=0; assign csr_error=0;
  end endgenerate
endmodule
