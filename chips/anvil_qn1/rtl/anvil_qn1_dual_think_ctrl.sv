module anvil_qn1_dual_think_ctrl #(
  parameter VOCAB_SIZE=151936, MAX_SEQ_LEN=40960
) (
  input wire clk, rst_n, flush, cancel,
  input wire start_valid,
  output wire start_ready,
  input wire [31:0] start_pos,
  output wire busy, done, error,
  input wire mode_valid, mode_value, observed_valid,
  input wire [31:0] observed_token,
  output wire think_active,
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
  input wire publish_ready,
  output wire verify_valid,
  input wire verify_ready,
  output wire [2:0] verify_parent,
  output wire [31:0] verify_pos,
  input wire verify_rsp_valid,
  output wire verify_rsp_ready,
  input wire [31:0] verify_argmax,
  input wire verify_error,
  output wire [2:0] event_draft_nodes, event_verified_nodes,
  output wire [2:0] event_accepted_nodes, event_rejected_nodes
);
  localparam IDLE=0, ROOT_REQ=1, ROOT_WAIT=2, ROOT_MODE=3, DRAFT_WAIT=4;
  localparam SELECT_TOKEN=5, NODE_REQ=6, NODE_WAIT=7, PUBLISH=8;
  localparam COMMIT=9, FINISH=10, FAULT=11;
  reg [3:0] state;
  reg thinking, tree_active, done_reg, error_reg;
  reg [31:0] position, target, request_position;
  reg [2:0] request_parent, current_parent, node_count, generated_count, accepted_count;
  reg [127:0] nodes;
  reg [11:0] parents;
  reg [159:0] generated;
  reg [2:0] draft_event, verified_event, accepted_event, rejected_event;
  reg malformed, child_found;
  reg [2:0] matching_child;
  reg [2:0] depths [0:3];
  reg committed_open, committed_close;
  integer i, j;
  wire active=rst_n && !flush && !cancel;
  wire response_expected=state==ROOT_WAIT || state==NODE_WAIT;
  wire protocol_fault=verify_rsp_valid && !response_expected;
  wire response_transfer=verify_rsp_valid && verify_rsp_ready;
  wire publication=commit_valid && commit_ready;
  wire target_marker=target==32'd151667 || target==32'd151668;
  wire [32:0] generated_position={1'b0,position}+{30'd0,generated_count}+33'd1;
  wire stop_at_capacity=generated_position==33'(MAX_SEQ_LEN-1);
  wire observed_open=observed_valid && observed_token==32'd151667;
  wire observed_close=observed_valid && observed_token==32'd151668;
  assign start_ready=active && state==IDLE && !done_reg && !error_reg;
  assign busy=active && state!=IDLE;
  assign done=active && done_reg;
  assign error=active && (error_reg || state==FAULT);
  assign think_active=rst_n && thinking;
  assign draft_ready=active && state==DRAFT_WAIT;
  assign commit_valid=active && !protocol_fault && state==COMMIT;
  assign commit_count=commit_valid ? generated_count : 3'd0;
  assign commit_tokens=commit_valid ? generated : 160'd0;
  assign commit_pos=commit_valid ? position+32'd1 : 32'd0;
  assign verify_valid=active && !protocol_fault && (state==ROOT_REQ || state==NODE_REQ);
  assign verify_parent=verify_valid ? request_parent : 3'd0;
  assign verify_pos=verify_valid ? request_position : 32'd0;
  assign verify_rsp_ready=active && response_expected;
  assign event_draft_nodes=active ? draft_event : 3'd0;
  assign event_verified_nodes=active ? verified_event : 3'd0;
  assign event_accepted_nodes=active ? accepted_event : 3'd0;
  assign event_rejected_nodes=active ? rejected_event : 3'd0;
  generate if (VOCAB_SIZE<1 || VOCAB_SIZE>151936 ||
      MAX_SEQ_LEN<1 || MAX_SEQ_LEN>40960) begin: invalid_parameters
    initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: thinking controller geometry");
  end endgenerate

  always @* begin
    malformed=draft_count<1 || draft_count>4;
    for (i=0;i<4;i=i+1) begin
      depths[i]=0;
      if (i<draft_count) begin
        if (draft_tokens[i*32+:32]>=VOCAB_SIZE) malformed=1;
        if (draft_parents[i*3+:3]==4) depths[i]=1;
        else if (draft_parents[i*3+:3]<i)
          depths[i]=depths[draft_parents[i*3+:3]]+3'd1;
        else malformed=1;
        if ({1'b0,position}+{30'd0,depths[i]}>=33'(MAX_SEQ_LEN))
          malformed=1;
        for (j=0;j<4;j=j+1)
          if (j<i && draft_parents[j*3+:3]==draft_parents[i*3+:3] &&
              draft_tokens[j*32+:32]==draft_tokens[i*32+:32])
            malformed=1;
      end
    end
    child_found=0;
    matching_child=0;
    for (i=0;i<4;i=i+1) begin
      if (tree_active && i<node_count && parents[i*3+:3]==current_parent &&
          nodes[i*32+:32]==target) begin
        child_found=1;
        matching_child=3'(i);
      end
    end
    committed_open=0; committed_close=0;
    if (publication) begin
      for (i=0;i<5;i=i+1) begin
        if (i<generated_count) begin
          if (generated[i*32+:32]==151667) committed_open=1;
          if (generated[i*32+:32]==151668) committed_close=1;
        end
      end
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) thinking<=0;
    else if (cancel || flush) thinking<=thinking;
    else if (observed_close || committed_close) thinking<=0;
    else if (observed_open || committed_open) thinking<=1;
    else if (mode_valid && state==IDLE) thinking<=mode_value;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; tree_active<=0; done_reg<=0; error_reg<=0;
      position<=0; target<=0; request_position<=0; request_parent<=0; current_parent<=4;
      node_count<=0; generated_count<=0; accepted_count<=0;
      nodes<=0; parents<=0; generated<=0;
      draft_event<=0; verified_event<=0; accepted_event<=0; rejected_event<=0;
    end else if (cancel || flush) begin
      state<=IDLE; tree_active<=0; done_reg<=0; error_reg<=0;
      node_count<=0; generated_count<=0; accepted_count<=0; generated<=0;
      draft_event<=0; verified_event<=0; accepted_event<=0; rejected_event<=0;
    end else begin
      done_reg<=0; error_reg<=0;
      draft_event<=0; verified_event<=0; accepted_event<=0; rejected_event<=0;
      if (protocol_fault) begin
        state<=FAULT;
      end else if (response_transfer && (verify_error || verify_argmax>=VOCAB_SIZE)) begin
        state<=FAULT;
      end else case (state)
        IDLE: if (start_valid && start_ready) begin
          position<=start_pos; request_position<=start_pos;
          request_parent<=4; current_parent<=4;
          generated<=0; generated_count<=0; accepted_count<=0; node_count<=0;
          tree_active<=0;
          if (start_pos>=MAX_SEQ_LEN-1) state<=FAULT;
          else state<=ROOT_REQ;
        end
        ROOT_REQ: if (verify_valid && verify_ready) state<=ROOT_WAIT;
        ROOT_WAIT: if (response_transfer) begin
          target<=verify_argmax; state<=ROOT_MODE;
        end
        ROOT_MODE: begin
          if (thinking) state<=DRAFT_WAIT;
          else state<=SELECT_TOKEN;
        end
        DRAFT_WAIT: if (draft_valid && draft_ready) begin
          draft_event<=draft_count;
          if (malformed) state<=FAULT;
          else begin
            nodes<=draft_tokens; parents<=draft_parents; node_count<=draft_count;
            tree_active<=1; state<=SELECT_TOKEN;
          end
        end
        SELECT_TOKEN: begin
          if (generated_count>=5 || generated_position>=33'(MAX_SEQ_LEN)) state<=FAULT;
          else begin
            generated[generated_count*32+:32]<=target;
            generated_count<=generated_count+1'b1;
            if (child_found) accepted_count<=accepted_count+1'b1;
            if (!child_found || target_marker || stop_at_capacity) state<=PUBLISH;
            else begin
              current_parent<=matching_child; request_parent<=matching_child;
              request_position<=generated_position[31:0];
              state<=NODE_REQ;
            end
          end
        end
        NODE_REQ: if (verify_valid && verify_ready) state<=NODE_WAIT;
        NODE_WAIT: if (response_transfer) begin
          target<=verify_argmax; verified_event<=1; state<=SELECT_TOKEN;
        end
        PUBLISH: if (publish_ready) state<=COMMIT;
        COMMIT: if (publication) begin
          accepted_event<=accepted_count;
          rejected_event<=node_count-accepted_count;
          state<=FINISH;
        end
        FINISH: begin done_reg<=1; state<=IDLE; end
        FAULT: begin
          error_reg<=1; state<=IDLE; generated<=0; generated_count<=0;
          node_count<=0; tree_active<=0;
        end
        default: state<=FAULT;
      endcase
    end
  end
endmodule
