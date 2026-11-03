module anvil_d2_mtp_verdict #(
  parameter integer MAX_SEQ_LEN=32768, MTP_K=4
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_anchor,
  input wire [127:0] cmd_draft, cmd_verify,
  input wire [2:0] cmd_proposed, cmd_limit,
  input wire [31:0] cmd_first_pos, cmd_eos,
  output wire spec_valid,
  input wire spec_ready,
  output wire [31:0] spec_token, spec_pos,
  output wire spec_last,
  output wire [2:0] spec_count, spec_accepted,
  output wire accepted_retire, rejected_block,
  output wire publication_done, publication_error
);
  localparam IDLE=0, DECIDE=1, VERDICT=2, PUBLISH=3, COMPLETE=4, FAULTED=5;
  reg [2:0] state;
  reg armed, failed, rejected;
  reg [31:0] anchor, eos, first_pos;
  reg [127:0] drafts, verifies;
  reg [2:0] proposed, limit, visible_count, accepted_count, index;
  reg [31:0] tokens [0:4];
  reg [31:0] candidates [0:4];
  reg [2:0] matching, raw_count, bounded_count, selected_count, selected_accepted;
  reg prefix_matches, terminal_seen;
  reg [31:0] capacity;
  wire enabled=rst_n && armed && !flush;
  integer n, r;

  generate if (MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768 || MTP_K!=4) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: MTP verdict geometry");
  end endgenerate

  assign cmd_ready=enabled && state==IDLE;
  assign spec_valid=enabled && state==PUBLISH;
  assign spec_token=spec_valid ? tokens[index] : 32'd0;
  assign spec_pos=spec_valid ? first_pos+{29'd0,index} : 32'd0;
  assign spec_last=spec_valid && index==visible_count-1'b1;
  assign spec_count=spec_valid ? visible_count : 3'd0;
  assign spec_accepted=spec_valid ? accepted_count : 3'd0;
  assign accepted_retire=spec_valid && spec_ready && index!=0 && index<=accepted_count;
  assign rejected_block=enabled && state==VERDICT && rejected;
  assign publication_done=enabled && state==COMPLETE;
  assign publication_error=publication_done && failed;

  always @* begin
    matching=0;
    prefix_matches=1;
    for (n=0;n<4;n=n+1) begin
      if (n<proposed && prefix_matches) begin
        if (drafts[n*32+:32]==verifies[n*32+:32]) matching=matching+1'b1;
        else prefix_matches=0;
      end
    end
    for (n=0;n<5;n=n+1) candidates[n]=0;
    candidates[0]=anchor;
    for (n=0;n<4;n=n+1) begin
      if (n<matching) candidates[n+1]=drafts[n*32+:32];
      else if (n==matching && matching<proposed) candidates[n+1]=verifies[n*32+:32];
    end
    if (matching==proposed) raw_count=proposed+3'd1;
    else raw_count=matching+3'd2;
    capacity=MAX_SEQ_LEN-first_pos;
    bounded_count=raw_count;
    if (bounded_count>limit) bounded_count=limit;
    if ({29'd0,bounded_count}>capacity) bounded_count=capacity[2:0];
    selected_count=bounded_count;
    terminal_seen=0;
    for (n=0;n<5;n=n+1) begin
      if (n<bounded_count && !terminal_seen && candidates[n]==eos) begin
        selected_count=n+1;
        terminal_seen=1;
      end
    end
    selected_accepted=matching;
    if (selected_count==0) selected_accepted=0;
    else if (selected_accepted>selected_count-1'b1)
      selected_accepted=selected_count-1'b1;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; rejected<=0;
      anchor<=0; eos<=0; first_pos<=0; drafts<=0; verifies<=0;
      proposed<=0; limit<=0; visible_count<=0; accepted_count<=0; index<=0;
      for (r=0;r<5;r=r+1) tokens[r]<=0;
    end else begin
      armed<=1;
      if (flush) begin
        state<=IDLE; failed<=0; rejected<=0;
        visible_count<=0; accepted_count<=0; index<=0;
      end else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          anchor<=cmd_anchor; eos<=cmd_eos; first_pos<=cmd_first_pos;
          drafts<=cmd_draft; verifies<=cmd_verify;
          proposed<=cmd_proposed; limit<=cmd_limit; index<=0; rejected<=0;
          if (cmd_proposed>4 || cmd_limit==0 || cmd_limit>5 ||
              cmd_first_pos>=MAX_SEQ_LEN) begin failed<=1; state<=COMPLETE; end
          else begin failed<=0; state<=DECIDE; end
        end
        DECIDE: begin
          for (r=0;r<5;r=r+1) tokens[r]<=candidates[r];
          visible_count<=selected_count; accepted_count<=selected_accepted;
          rejected<=matching<proposed;
          state<=VERDICT;
        end
        VERDICT: state<=PUBLISH;
        PUBLISH: if (spec_valid && spec_ready) begin
          if (index==visible_count-1'b1) state<=COMPLETE;
          else index<=index+1'b1;
        end
        COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
        FAULTED: state<=FAULTED;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
