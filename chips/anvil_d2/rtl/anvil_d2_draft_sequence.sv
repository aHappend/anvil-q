module anvil_d2_draft_sequence #(
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=10944,
  parameter integer NUM_Q_HEADS=16, KV_LORA_RANK=512, QK_NOPE_HEAD_DIM=128,
  parameter integer QK_ROPE_HEAD_DIM=64, V_HEAD_DIM=128,
  parameter integer ROUTED_EXPERTS=64, TOP_K=6, SHARED_EXPERTS=2,
  parameter integer MOE_INTERMEDIATE_SIZE=1408,
  parameter integer VOCAB_SIZE=102400, MAX_SEQ_LEN=32768, TILE_K=128, TILE_ROWS=8
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire cmd_speculate, cmd_new_sequence,
  input wire [31:0] cmd_epoch, cmd_token, cmd_pos,
  input wire [2:0] cmd_depths,
  input wire in_valid,
  output wire in_ready,
  input wire signed [31:0] in_hidden,
  output wire result_valid,
  input wire result_ready,
  output wire [127:0] result_draft,
  output wire [2:0] result_proposed,
  output wire proposed_pulse,
  output wire done, error, idle, fault,
  output wire [8:0] c_req_valid, c_req_write,
  input wire [8:0] c_req_ready,
  output wire [35:0] c_req_kind,
  output wire [287:0] c_req_layer,
  output wire [26:0] c_req_proj,
  output wire [287:0] c_req_row, c_req_col, c_req_wdata,
  input wire [8:0] c_rsp_valid, c_rsp_error,
  output wire [8:0] c_rsp_ready,
  input wire [287:0] c_rsp_rdata
);
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=36 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=2048 && (HIDDEN_SIZE & 7)==0 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=11008 && (INTERMEDIATE_SIZE & 7)==0 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 && KV_LORA_RANK>=1 && KV_LORA_RANK<=512 &&
    QK_NOPE_HEAD_DIM>=1 && QK_NOPE_HEAD_DIM<=128 &&
    QK_ROPE_HEAD_DIM>=2 && QK_ROPE_HEAD_DIM<=64 && (QK_ROPE_HEAD_DIM & 1)==0 &&
    V_HEAD_DIM>=1 && V_HEAD_DIM<=128 && ROUTED_EXPERTS>=1 && ROUTED_EXPERTS<=64 &&
    TOP_K>=1 && TOP_K<=6 && TOP_K<=ROUTED_EXPERTS && SHARED_EXPERTS==2 &&
    MOE_INTERMEDIATE_SIZE>=8 && MOE_INTERMEDIATE_SIZE<=1408 &&
    (MOE_INTERMEDIATE_SIZE & 7)==0 && VOCAB_SIZE>=4 && VOCAB_SIZE<=151936 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 && TILE_K>=8 && TILE_K<=128 &&
    (TILE_K & 7)==0 && TILE_ROWS>=1 && TILE_ROWS<=8;
  generate
    if (!LEGAL) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: draft sequence geometry");
      assign cmd_ready=0;
      assign in_ready=0;
      assign result_valid=0;
      assign result_draft=0;
      assign result_proposed=0;
      assign proposed_pulse=0;
      assign done=0;
      assign error=0;
      assign idle=0;
      assign fault=0;
      assign c_req_valid=0;
      assign c_req_write=0;
      assign c_req_kind=0;
      assign c_req_layer=0;
      assign c_req_proj=0;
      assign c_req_row=0;
      assign c_req_col=0;
      assign c_req_wdata=0;
      assign c_rsp_ready=0;
    end else begin: sequence_datapath
      localparam integer STAGING=5*HIDDEN_SIZE, SPECULATIVE=10*HIDDEN_SIZE;
      localparam integer AW=$clog2(18*HIDDEN_SIZE);
      localparam IDLE=0, RESTART=1, INPUT_HIDDEN=2, SELECT=3, HEAD_COMMAND=4;
      localparam SOURCE_READ=5, SOURCE_FEED=6, HEAD_OUTPUT=7, HEAD_RESULT=8;
      localparam COMMIT=9, COMMIT_WAIT=10, COPY_READ=11, COPY_WRITE=12;
      localparam RESULT=13, COMPLETE=14, FAULTED=15;
      reg [3:0] state;
      reg armed, failed, speculate, context_valid;
      reg [31:0] epoch, token, position, last_position, context_epoch;
      reg [31:0] component, copy_index, copy_words;
      reg [2:0] head, column, depths;
      reg [127:0] drafts;
      (* ramstyle="M20K", nomem2reg *) reg signed [31:0] history [0:18*HIDDEN_SIZE-1];
      reg signed [31:0] history_q;
      wire enabled=rst_n && armed && !flush;
      wire child_flush=flush || failed || state==RESTART;
      wire head_ready, head_input_ready, head_output_valid, head_output_last;
      wire [31:0] head_output_index, head_result_token;
      wire signed [31:0] head_output_hidden;
      wire head_result_valid, head_commit_ready, head_commit_done, head_idle, head_fault;
      wire [31:0] current_position=position+(speculate ? {29'd0,column} : 32'd0);
      wire [31:0] previous_column_base=SPECULATIVE+
        (column[0] ? 32'd0 : 32'(4*HIDDEN_SIZE));
      wire [31:0] current_column_base=SPECULATIVE+
        (column[0] ? 32'(4*HIDDEN_SIZE) : 32'd0);
      wire [31:0] source_address=speculate && column!=0 ?
        previous_column_base+({29'd0,head}-32'd1)*HIDDEN_SIZE+component :
        {29'd0,head}*HIDDEN_SIZE+component;
      wire [31:0] destination_address=speculate ?
        current_column_base+{29'd0,head}*HIDDEN_SIZE+component :
        STAGING+({29'd0,head}+32'd1)*HIDDEN_SIZE+component;
      wire source_transfer=enabled && state==SOURCE_FEED && head_input_ready;
      wire output_transfer=enabled && state==HEAD_OUTPUT && head_output_valid;
      wire output_bad=output_transfer &&
        (head_output_index!=component || head_output_last!=(component==HIDDEN_SIZE-1));
      wire [32:0] proposed_last={1'b0,cmd_pos}+{30'd0,cmd_depths};
      wire command_bad=cmd_token>=VOCAB_SIZE || cmd_pos>=MAX_SEQ_LEN ||
        (cmd_speculate ?
          (cmd_new_sequence || !context_valid || cmd_epoch!=context_epoch ||
           cmd_pos!=last_position+32'd1 || cmd_depths>4 || proposed_last>=MAX_SEQ_LEN) :
          (cmd_new_sequence ? cmd_pos!=0 :
           (!context_valid || cmd_epoch!=context_epoch || cmd_pos!=last_position+32'd1)));

      assign cmd_ready=enabled && !failed && state==IDLE && head_idle;
      assign idle=cmd_ready;
      assign fault=enabled && failed;
      assign in_ready=enabled && !failed && state==INPUT_HIDDEN;
      assign result_valid=enabled && !failed && state==RESULT;
      assign result_draft=result_valid ? drafts : 128'd0;
      assign result_proposed=result_valid ? depths : 3'd0;
      assign proposed_pulse=enabled && !failed && speculate && state==HEAD_RESULT &&
        head_result_valid && head==column;
      assign done=enabled && state==COMPLETE;
      assign error=done && failed;

      anvil_d2_draft_head #(
        .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
        .NUM_Q_HEADS(NUM_Q_HEADS),.KV_LORA_RANK(KV_LORA_RANK),
        .QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),.QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),
        .V_HEAD_DIM(V_HEAD_DIM),.ROUTED_EXPERTS(ROUTED_EXPERTS),.TOP_K(TOP_K),
        .SHARED_EXPERTS(SHARED_EXPERTS),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
        .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
      ) head_datapath (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),
        .cmd_valid(enabled && !failed && state==HEAD_COMMAND),.cmd_ready(head_ready),
        .cmd_epoch(epoch),.cmd_token(token),.cmd_pos(current_position),.cmd_head(head),
        .in_valid(enabled && !failed && state==SOURCE_FEED),.in_ready(head_input_ready),
        .in_hidden(history_q),.out_valid(head_output_valid),
        .out_ready(enabled && !failed && state==HEAD_OUTPUT),
        .out_hidden(head_output_hidden),.out_index(head_output_index),.out_last(head_output_last),
        .result_valid(head_result_valid),.result_ready(enabled && !failed && state==HEAD_RESULT),
        .result_token(head_result_token),
        .commit_valid(enabled && !failed && state==COMMIT),.commit_ready(head_commit_ready),
        .commit_through_pos(speculate ? last_position : position),.commit_done(head_commit_done),
        .idle(head_idle),.fault(head_fault),
        .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
        .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
        .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
        .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
        .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error)
      );

      always @(posedge clk) begin
        if (enabled && !failed) begin
          if (state==INPUT_HIDDEN && in_valid)
            history[AW'(STAGING+component)]<=in_hidden;
          if (state==SOURCE_READ) history_q<=history[AW'(source_address)];
          if (output_transfer && !output_bad)
            history[AW'(destination_address)]<=head_output_hidden;
          if (state==COPY_READ) history_q<=history[AW'(STAGING+copy_index)];
          if (state==COPY_WRITE) history[AW'(copy_index)]<=history_q;
        end
      end

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state<=IDLE; armed<=0; failed<=0; speculate<=0; context_valid<=0;
          epoch<=0; token<=0; position<=0; last_position<=0; context_epoch<=0;
          component<=0; copy_index<=0; copy_words<=0; head<=0; column<=0;
          depths<=0; drafts<=0;
        end else begin
          armed<=1;
          if (flush) begin
            state<=IDLE; failed<=0; context_valid<=0; drafts<=0;
            component<=0; copy_index<=0; head<=0; column<=0; depths<=0;
          end else if (!failed && (head_fault || output_bad)) begin
            state<=COMPLETE; failed<=1; context_valid<=0;
          end else case (state)
            IDLE: if (cmd_valid && cmd_ready) begin
              if (command_bad) begin failed<=1; context_valid<=0; state<=COMPLETE; end
              else begin
                epoch<=cmd_epoch; token<=cmd_token; position<=cmd_pos;
                speculate<=cmd_speculate; head<=0; column<=0; component<=0; drafts<=0;
                copy_index<=0; copy_words<=cmd_pos>=4 ?
                  32'(5*HIDDEN_SIZE) : (cmd_pos+32'd1)*HIDDEN_SIZE;
                if (cmd_speculate) begin depths<=cmd_depths; state<=SELECT; end
                else begin
                  depths<=cmd_pos>=4 ? 3'd4 : cmd_pos[2:0];
                  if (cmd_new_sequence) begin context_valid<=0; state<=RESTART; end
                  else state<=INPUT_HIDDEN;
                end
              end
            end
            RESTART: state<=INPUT_HIDDEN;
            INPUT_HIDDEN: if (in_valid && in_ready) begin
              if (component==HIDDEN_SIZE-1) begin component<=0; state<=SELECT; end
              else component<=component+1'b1;
            end
            SELECT: begin
              if (head>=depths) begin
                if (speculate && column+3'd1<depths) begin
                  token<=drafts[column*32+:32];
                  column<=column+1'b1; head<=column+1'b1;
                end else state<=COMMIT;
              end else if (current_position<{29'd0,head}+32'd1) head<=head+1'b1;
              else begin component<=0; state<=HEAD_COMMAND; end
            end
            HEAD_COMMAND: if (head_ready) state<=SOURCE_READ;
            SOURCE_READ: state<=SOURCE_FEED;
            SOURCE_FEED: if (source_transfer) begin
              if (component==HIDDEN_SIZE-1) begin component<=0; state<=HEAD_OUTPUT; end
              else begin component<=component+1'b1; state<=SOURCE_READ; end
            end
            HEAD_OUTPUT: if (output_transfer) begin
              if (component==HIDDEN_SIZE-1) begin component<=0; state<=HEAD_RESULT; end
              else component<=component+1'b1;
            end
            HEAD_RESULT: if (head_result_valid) begin
              if (speculate && head==column) drafts[column*32+:32]<=head_result_token;
              head<=head+1'b1; state<=SELECT;
            end
            COMMIT: if (head_commit_ready) state<=COMMIT_WAIT;
            COMMIT_WAIT: if (head_commit_done) begin
              if (speculate) state<=RESULT;
              else begin copy_index<=0; state<=COPY_READ; end
            end
            COPY_READ: state<=COPY_WRITE;
            COPY_WRITE: begin
              if (copy_index==copy_words-1'b1) begin
                context_valid<=1; last_position<=position; context_epoch<=epoch;
                state<=COMPLETE;
              end else begin copy_index<=copy_index+1'b1; state<=COPY_READ; end
            end
            RESULT: if (result_valid && result_ready) state<=COMPLETE;
            COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
            FAULTED: state<=FAULTED;
            default: begin failed<=1; context_valid<=0; state<=COMPLETE; end
          endcase
        end
      end
    end
  endgenerate
endmodule
