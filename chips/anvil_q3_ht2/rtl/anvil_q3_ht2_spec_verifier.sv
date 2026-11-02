module anvil_q3_ht2_spec_verifier #(
  parameter NUM_LAYERS=36, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter MAX_SEQ_LEN=32768, CACHE_MODE=1, VOCAB_SIZE=151936
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_id, cmd_epoch, cmd_base_pos,
  input wire [3:0] cmd_mask,
  input wire [127:0] cmd_tokens,
  input wire [11:0] cmd_parents,
  input wire [31:0] cmd_root_target,
  output wire eval_valid,
  input wire eval_ready,
  output wire [31:0] eval_id, eval_epoch,
  output wire [3:0] eval_mask,
  output wire [127:0] eval_tokens,
  output wire [11:0] eval_parents,
  output wire [127:0] eval_positions,
  output wire [15:0] eval_visibility,
  input wire logit_valid,
  output wire logit_ready,
  input wire [31:0] logit_id, logit_epoch,
  input wire [1:0] logit_node,
  input wire [31:0] logit_index,
  input wire signed [31:0] logit_data,
  input wire logit_last,
  input wire eval_done, eval_error,
  input wire stage_valid,
  output wire stage_ready,
  input wire [31:0] stage_id, stage_epoch,
  input wire [1:0] stage_node,
  input wire [31:0] stage_layer, stage_head,
  input wire stage_value,
  input wire [31:0] stage_group,
  input wire [511:0] stage_record,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_id,
  output wire out_error,
  output wire [3:0] out_mask,
  output wire [2:0] out_count,
  output wire [127:0] out_tokens,
  output wire [31:0] out_next_token, out_committed_pos,
  output wire idle, fault, drain_done,
  output wire publication_valid,
  output wire [31:0] publication_pos, publication_next_token,
  output wire memory_req_valid,
  input wire memory_req_ready,
  output wire memory_req_write,
  output wire [32:0] memory_req_address,
  output wire [511:0] memory_req_wdata,
  output wire [63:0] memory_req_byteenable,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata
);
  localparam CAP=CACHE_MODE==2 ? 64 : 32;
  localparam [127:0] GROUPS_WIDE=(128'(HEAD_DIM)+CAP-1)>>$clog2(CAP);
  localparam [127:0] TOKEN_BYTES_WIDE=128'(NUM_LAYERS)*2*
    128'(NUM_KV_HEADS)*GROUPS_WIDE*64;
  localparam [127:0] EXTENT_WIDE=TOKEN_BYTES_WIDE*(128'(MAX_SEQ_LEN)+4);
  localparam LEGAL=NUM_LAYERS>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 &&
    (HEAD_DIM&1)==0 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    (CACHE_MODE==1 || CACHE_MODE==2) && VOCAB_SIZE>0 &&
    EXTENT_WIDE<=128'h100000000 &&
    (TOKEN_BYTES_WIDE>>6)<=128'hffffffff;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: speculative verifier geometry");
    assign cmd_ready=0;
    assign eval_valid=0;
    assign eval_id=0;
    assign eval_epoch=0;
    assign eval_mask=0;
    assign eval_tokens=0;
    assign eval_parents=0;
    assign eval_positions=0;
    assign eval_visibility=0;
    assign logit_ready=0;
    assign stage_ready=0;
    assign out_valid=0;
    assign out_id=0;
    assign out_error=0;
    assign out_mask=0;
    assign out_count=0;
    assign out_tokens=0;
    assign out_next_token=0;
    assign out_committed_pos=0;
    assign idle=0;
    assign fault=0;
    assign drain_done=0;
    assign publication_valid=0;
    assign publication_pos=0;
    assign publication_next_token=0;
    assign memory_req_valid=0;
    assign memory_req_write=0;
    assign memory_req_address=0;
    assign memory_req_wdata=0;
    assign memory_req_byteenable=0;
  end else begin: datapath
    localparam IDLE=0, GRAPH_CAPTURE=1, GRAPH_UPDATE=2, ENGINE_START=3,
      EVALUATE=4, RECEIVE=5, SEARCH=6, SELECT=7, COMMIT=8, COMMIT_WAIT=9,
      RESPONSE=10, ABORT_PULSE=11, ABORT_WAIT=12, ERROR_RESPONSE=13,
      CANCEL_WAIT=14, FAULTED=15;
    reg [3:0] state;
    reg failed, evaluation_done;
    reg [31:0] transaction_id, epoch, base_pos, root_target;
    reg [3:0] active;
    reg [127:0] tokens, positions;
    reg [11:0] parents;
    reg [15:0] visibility;
    reg [2:0] depths [0:3];
    reg [1:0] graph_node;
    reg graph_bad;
    reg [2:0] captured_depth;
    reg [3:0] captured_visibility;
    reg [63:0] captured_position;
    reg [31:0] next_index [0:3], best_id [0:3];
    reg signed [31:0] best_value [0:3];
    reg [3:0] logits_complete;
    reg compare_valid;
    reg [1:0] compare_node;
    reg [31:0] compare_index;
    reg signed [31:0] compare_value;
    reg [2:0] current_parent, accepted_count;
    reg [31:0] current_target;
    reg [3:0] selected_mask;
    reg [7:0] selected_path;
    reg [127:0] selected_tokens;
    reg found_valid;
    reg [1:0] found_node;
    reg response_error;
    reg [31:0] response_id, response_next, response_position;
    reg [3:0] response_mask;
    reg [2:0] response_count;
    reg [127:0] response_tokens;
    wire running=rst_n && !flush && !failed;
    wire engine_ready, engine_stage_ready, engine_staged, engine_commit_ready;
    wire engine_publish, engine_done, engine_error, engine_idle, engine_fault, engine_drained;
    wire engine_publication;
    wire [2:0] engine_publish_count;
    wire [31:0] engine_publish_pos, visible_count, visible_epoch;
    wire logit_fire=logit_valid && logit_ready;
    reg logit_bad, command_bad;
    wire all_logits=(!active[0] || logits_complete[0]) &&
      (!active[1] || logits_complete[1]) &&
      (!active[2] || logits_complete[2]) &&
      (!active[3] || logits_complete[3]);
    wire receive_fault=state==RECEIVE &&
      (eval_error || (logit_fire && logit_bad) ||
       (evaluation_done && !compare_valid && !all_logits) ||
       (evaluation_done && engine_stage_ready && !engine_staged));
    wire unexpected_completion=(eval_done || eval_error) &&
      state!=RECEIVE && state!=ABORT_PULSE && state!=ABORT_WAIT &&
      state!=CANCEL_WAIT && state!=FAULTED;
    wire transaction_fault=engine_fault || engine_error ||
      receive_fault || unexpected_completion;
    wire incoming_fault=unexpected_completion ||
      (state==RECEIVE && (eval_error || (logit_fire && logit_bad)));
    wire engine_flush=flush || state==ABORT_PULSE ||
      (!failed && state!=CANCEL_WAIT && incoming_fault);
    wire [2:0] graph_parent=parents[graph_node*3+:3];
    wire [1:0] safe_parent=graph_parent[1:0];
    reg calculated_bad, calculated_found;
    reg [2:0] calculated_depth;
    reg [3:0] calculated_visibility;
    reg [1:0] calculated_node;
    integer i;

    always @* begin
      logit_bad=logit_id!=transaction_id || logit_epoch!=epoch ||
        !active[logit_node] || logits_complete[logit_node] ||
        logit_index!=next_index[logit_node] || logit_index>=VOCAB_SIZE ||
        logit_last!=(logit_index==VOCAB_SIZE-1);
      command_bad=cmd_mask==0 || cmd_root_target>=VOCAB_SIZE ||
        cmd_base_pos!=visible_count || cmd_base_pos>=MAX_SEQ_LEN ||
        (visible_count!=0 && cmd_epoch!=visible_epoch);
`ifndef SYNTHESIS
      if ((^{logit_id,logit_epoch,logit_node,logit_index,logit_data,logit_last})===1'bx)
        logit_bad=1;
      if ((^{cmd_id,cmd_epoch,cmd_base_pos,cmd_mask,cmd_tokens,cmd_parents,
             cmd_root_target})===1'bx) command_bad=1;
`endif
      calculated_bad=0;
      calculated_depth=0;
      calculated_visibility=0;
      if (active[graph_node]) begin
        calculated_bad=tokens[graph_node*32+:32]>=VOCAB_SIZE ||
          (graph_parent!=4 &&
           (graph_parent>=graph_node || !active[safe_parent]));
        calculated_depth=graph_parent==4 ? 3'd0 : depths[safe_parent]+1'b1;
        calculated_visibility=(4'b0001<<graph_node) |
          (graph_parent==4 ? 4'd0 : visibility[safe_parent*4+:4]);
        for (integer n=0;n<4;n=n+1)
          if (n<graph_node && active[n] && parents[n*3+:3]==graph_parent &&
              tokens[n*32+:32]==tokens[graph_node*32+:32]) calculated_bad=1;
      end else if (tokens[graph_node*32+:32]!=0 || graph_parent!=0) calculated_bad=1;
      calculated_found=0;
      calculated_node=0;
      for (integer n=0;n<4;n=n+1)
        if (active[n] && parents[n*3+:3]==current_parent &&
            tokens[n*32+:32]==current_target) begin
          calculated_found=1; calculated_node=2'(n);
        end
    end

    assign cmd_ready=running && state==IDLE && engine_ready;
    assign eval_valid=running && state==EVALUATE;
    assign eval_id=eval_valid ? transaction_id : 32'd0;
    assign eval_epoch=eval_valid ? epoch : 32'd0;
    assign eval_mask=eval_valid ? active : 4'd0;
    assign eval_tokens=eval_valid ? tokens : 128'd0;
    assign eval_parents=eval_valid ? parents : 12'd0;
    assign eval_positions=eval_valid ? positions : 128'd0;
    assign eval_visibility=eval_valid ? visibility : 16'd0;
    assign logit_ready=running && state==RECEIVE && !evaluation_done;
    assign stage_ready=running && state==RECEIVE && !evaluation_done && engine_stage_ready;
    assign out_valid=rst_n && !flush && (state==RESPONSE || state==ERROR_RESPONSE);
    assign out_id=out_valid ? response_id : 32'd0;
    assign out_error=out_valid && response_error;
    assign out_mask=out_valid && !response_error ? response_mask : 4'd0;
    assign out_count=out_valid && !response_error ? response_count : 3'd0;
    assign out_tokens=out_valid && !response_error ? response_tokens : 128'd0;
    assign out_next_token=out_valid && !response_error ? response_next : 32'd0;
    assign out_committed_pos=out_valid && !response_error ? response_position : 32'd0;
    assign idle=running && state==IDLE && engine_idle;
    assign fault=rst_n && !flush && failed;
    assign drain_done=rst_n && !flush && engine_drained &&
      (state==IDLE || state==FAULTED || state==ERROR_RESPONSE);
    assign publication_valid=running && state==COMMIT_WAIT && engine_publication;
    assign publication_pos=publication_valid ? base_pos+{29'd0,accepted_count} : 32'd0;
    assign publication_next_token=publication_valid ? current_target : 32'd0;

    anvil_q3_ht2_kv_commit_engine #(
      .NUM_LAYERS(NUM_LAYERS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
      .MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_MODE(CACHE_MODE)
    ) kv_commit_engine (
      .clk(clk),.rst_n(rst_n),.flush(engine_flush),
      .cmd_valid(running && state==ENGINE_START),.cmd_ready(engine_ready),
      .cmd_id(transaction_id),.cmd_epoch(epoch),.cmd_base_pos(base_pos),.cmd_mask(active),
      .stage_valid(stage_valid && running && state==RECEIVE && !evaluation_done),
      .stage_ready(engine_stage_ready),.stage_id(stage_id),.stage_epoch(stage_epoch),
      .stage_node(stage_node),.stage_layer(stage_layer),.stage_head(stage_head),
      .stage_value(stage_value),.stage_group(stage_group),.stage_record(stage_record),
      .staged(engine_staged),.commit_valid(running && state==COMMIT),
      .commit_ready(engine_commit_ready),.commit_count(accepted_count),
      .commit_nodes(selected_path),.publish_valid(engine_publish),
      .publication_valid(engine_publication),
      .publish_count(engine_publish_count),.publish_pos(engine_publish_pos),
      .visible_count(visible_count),.visible_epoch(visible_epoch),
      .done(engine_done),.error(engine_error),.idle(engine_idle),
      .fault(engine_fault),.drain_done(engine_drained),
      .memory_req_valid(memory_req_valid),.memory_req_ready(memory_req_ready),
      .memory_req_write(memory_req_write),.memory_req_address(memory_req_address),
      .memory_req_wdata(memory_req_wdata),.memory_req_byteenable(memory_req_byteenable),
      .memory_rsp_valid(memory_rsp_valid),.memory_rsp_error(memory_rsp_error),
      .memory_rsp_rdata(memory_rsp_rdata)
    );

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; evaluation_done<=0;
        transaction_id<=0; epoch<=0; base_pos<=0; root_target<=0;
        active<=0; tokens<=0; positions<=0; parents<=0; visibility<=0;
        graph_node<=0; graph_bad<=0; captured_depth<=0; captured_visibility<=0;
        captured_position<=0; logits_complete<=0; compare_valid<=0;
        compare_node<=0; compare_index<=0; compare_value<=0;
        current_parent<=0; current_target<=0; accepted_count<=0;
        selected_mask<=0; selected_path<=0; selected_tokens<=0; found_valid<=0; found_node<=0;
        response_error<=0; response_id<=0; response_next<=0; response_position<=0;
        response_mask<=0; response_count<=0; response_tokens<=0;
        for (i=0;i<4;i=i+1) begin
          depths[i]<=0; next_index[i]<=0; best_id[i]<=0; best_value[i]<=0;
        end
      end else if (flush) begin
        state<=CANCEL_WAIT; failed<=0; evaluation_done<=0;
        transaction_id<=0; epoch<=0; base_pos<=0; root_target<=0;
        active<=0; tokens<=0; positions<=0; parents<=0; visibility<=0;
        graph_node<=0; graph_bad<=0; captured_depth<=0; captured_visibility<=0;
        captured_position<=0; logits_complete<=0; compare_valid<=0;
        compare_node<=0; compare_index<=0; compare_value<=0;
        current_parent<=0; current_target<=0; accepted_count<=0;
        selected_mask<=0; selected_path<=0; selected_tokens<=0; found_valid<=0; found_node<=0;
        response_error<=0; response_id<=0; response_next<=0; response_position<=0;
        response_mask<=0; response_count<=0; response_tokens<=0;
        for (i=0;i<4;i=i+1) begin
          depths[i]<=0; next_index[i]<=0; best_id[i]<=0; best_value[i]<=0;
        end
      end else if (!failed && state!=CANCEL_WAIT && transaction_fault) begin
        failed<=1; compare_valid<=0; response_error<=1;
        response_id<=transaction_id; response_mask<=0; response_count<=0;
        response_tokens<=0; response_next<=0; response_position<=0;
        state<=ABORT_PULSE;
      end else begin
        compare_valid<=logit_fire && !logit_bad;
        if (logit_fire && !logit_bad) begin
          compare_node<=logit_node; compare_index<=logit_index; compare_value<=logit_data;
          next_index[logit_node]<=next_index[logit_node]+1'b1;
          if (logit_last) logits_complete[logit_node]<=1;
        end
        if (compare_valid) begin
          if (compare_index==0 || compare_value>best_value[compare_node] ||
              (compare_value==best_value[compare_node] && compare_index<best_id[compare_node])) begin
            best_value[compare_node]<=compare_value;
            best_id[compare_node]<=compare_index;
          end
        end
        case (state)
          IDLE: if (cmd_valid && cmd_ready) begin
            transaction_id<=cmd_id; epoch<=cmd_epoch; base_pos<=cmd_base_pos;
            root_target<=cmd_root_target; active<=cmd_mask; tokens<=cmd_tokens;
            parents<=cmd_parents; positions<=0; visibility<=0; graph_node<=0;
            evaluation_done<=0; logits_complete<=0; compare_valid<=0;
            accepted_count<=0; selected_mask<=0; selected_path<=0; selected_tokens<=0;
            response_error<=0; response_id<=0; response_next<=0; response_position<=0;
            response_mask<=0; response_count<=0; response_tokens<=0;
            for (i=0;i<4;i=i+1) begin
              depths[i]<=0; next_index[i]<=0; best_id[i]<=0;
              best_value[i]<=32'sh80000000;
            end
            if (command_bad) begin
              failed<=1; response_error<=1; response_id<=cmd_id; state<=ABORT_PULSE;
            end else state<=GRAPH_CAPTURE;
          end
          GRAPH_CAPTURE: begin
            graph_bad<=calculated_bad; captured_depth<=calculated_depth;
            captured_visibility<=calculated_visibility;
            captured_position<={32'd0,base_pos}+{61'd0,calculated_depth};
            state<=GRAPH_UPDATE;
          end
          GRAPH_UPDATE: begin
            if (graph_bad || (active[graph_node] && captured_position>=MAX_SEQ_LEN)) begin
              failed<=1; response_error<=1; response_id<=transaction_id; state<=ABORT_PULSE;
            end else begin
              depths[graph_node]<=captured_depth;
              visibility[graph_node*4+:4]<=captured_visibility;
              positions[graph_node*32+:32]<=active[graph_node] ? captured_position[31:0] : 32'd0;
              if (graph_node==3) state<=ENGINE_START;
              else begin graph_node<=graph_node+1'b1; state<=GRAPH_CAPTURE; end
            end
          end
          ENGINE_START: if (engine_ready) state<=EVALUATE;
          EVALUATE: if (eval_ready) state<=RECEIVE;
          RECEIVE: begin
            if (eval_done) evaluation_done<=1;
            if (evaluation_done && !compare_valid && all_logits && engine_staged) begin
              current_parent<=3'd4; current_target<=root_target; state<=SEARCH;
            end
          end
          SEARCH: begin found_valid<=calculated_found; found_node<=calculated_node; state<=SELECT; end
          SELECT: begin
            if (!found_valid) state<=COMMIT;
            else begin
              selected_mask[found_node]<=1;
              selected_path[accepted_count*2+:2]<=found_node;
              selected_tokens[accepted_count*32+:32]<=tokens[found_node*32+:32];
              accepted_count<=accepted_count+1'b1;
              current_parent<={1'b0,found_node}; current_target<=best_id[found_node];
              if (accepted_count==3) state<=COMMIT;
              else state<=SEARCH;
            end
          end
          COMMIT: if (engine_commit_ready) state<=COMMIT_WAIT;
          COMMIT_WAIT: if (engine_publish && engine_done) begin
            if (engine_publish_count!=accepted_count ||
                engine_publish_pos!=base_pos+{29'd0,accepted_count}) begin
              failed<=1; response_error<=1; response_id<=transaction_id; state<=ABORT_PULSE;
            end else begin
              response_id<=transaction_id; response_error<=0; response_mask<=selected_mask;
              response_count<=engine_publish_count; response_tokens<=selected_tokens;
              response_next<=current_target; response_position<=engine_publish_pos;
              state<=RESPONSE;
            end
          end
          RESPONSE: if (out_ready) state<=IDLE;
          ABORT_PULSE: state<=ABORT_WAIT;
          ABORT_WAIT: if (engine_drained) state<=ERROR_RESPONSE;
          ERROR_RESPONSE: if (out_ready) state<=FAULTED;
          CANCEL_WAIT: if (engine_drained) state<=IDLE;
          FAULTED: begin end
          default: begin failed<=1; response_error<=1; response_id<=transaction_id; state<=ABORT_PULSE; end
        endcase
      end
    end
  end endgenerate
endmodule
