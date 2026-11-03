module anvil_d2_draft_cache #(
  parameter integer NUM_LAYERS=27, KV_LORA_RANK=512,
  parameter integer QK_ROPE_HEAD_DIM=64, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_pos,
  input wire [2:0] cmd_head,
  input wire release_valid,
  output wire release_ready,
  input wire commit_valid,
  output wire commit_ready,
  input wire [31:0] commit_through_pos,
  output wire commit_done,
  output wire idle, fault,
  input wire s_req_valid, s_req_write,
  output wire s_req_ready,
  input wire [31:0] s_req_layer, s_req_row, s_req_col, s_req_wdata,
  output wire s_rsp_valid, s_rsp_error,
  input wire s_rsp_ready,
  output wire [31:0] s_rsp_rdata,
  output wire c_req_valid, c_req_write,
  input wire c_req_ready,
  output wire [3:0] c_req_kind,
  output wire [31:0] c_req_layer,
  output wire [2:0] c_req_proj,
  output wire [31:0] c_req_row, c_req_col, c_req_wdata,
  input wire c_rsp_valid, c_rsp_error,
  output wire c_rsp_ready,
  input wire [31:0] c_rsp_rdata
);
  generate
    if (NUM_LAYERS<1 || NUM_LAYERS>36 || KV_LORA_RANK<1 ||
        KV_LORA_RANK>512 || QK_ROPE_HEAD_DIM<2 || QK_ROPE_HEAD_DIM>64 ||
        (QK_ROPE_HEAD_DIM & 1)!=0 || MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: draft cache geometry");
      assign cmd_ready=0;
      assign release_ready=0;
      assign commit_ready=0;
      assign commit_done=0;
      assign idle=0;
      assign fault=0;
      assign s_req_ready=0;
      assign s_rsp_valid=0;
      assign s_rsp_error=0;
      assign s_rsp_rdata=0;
      assign c_req_valid=0;
      assign c_req_write=0;
      assign c_req_kind=0;
      assign c_req_layer=0;
      assign c_req_proj=0;
      assign c_req_row=0;
      assign c_req_col=0;
      assign c_req_wdata=0;
      assign c_rsp_ready=0;
    end else begin: cache
      localparam integer CW=KV_LORA_RANK+QK_ROPE_HEAD_DIM;
      localparam integer AW=$clog2(16*CW);
      localparam IDLE=0, ACTIVE=1, LOCAL_RESPONSE=2, PREFIX_REQUEST=3;
      localparam PREFIX_RESPONSE=4, PREFIX_PUBLISH=5, COMMIT_SELECT=6;
      localparam COMMIT_READ=7, COMMIT_REQUEST=8, COMMIT_RESPONSE=9;
      localparam COMMIT_COMPLETE=10, FAULTED=11;
      reg [3:0] state;
      reg armed, failed, epoch_valid, response_error, response_write;
      reg [31:0] epoch, position, written, through_pos;
      reg [1:0] head, commit_head;
      reg [2:0] commit_slot, committed_rows;
      reg [31:0] commit_col;
      reg [31:0] frontier [0:3];
      reg [2:0] private_count [0:3];
      reg [31:0] prefix_row, prefix_col, prefix_word;
      reg [AW-1:0] commit_address;
      (* ramstyle="M20K", nomem2reg *) reg [31:0] candidates [0:16*CW-1];
      reg [31:0] private_q, commit_q;
      wire enabled=rst_n && armed && !flush;
      wire [32:0] absolute_row={1'b0,s_req_row}+{31'd0,head}+33'd1;
      wire request_bad=s_req_layer!={30'd0,head} || s_req_col>=CW ||
        absolute_row[32] || absolute_row[31:0]>position ||
        (s_req_write ? (written>=CW || absolute_row[31:0]!=position ||
                       s_req_col!=written) : written!=CW);
      wire private_read=absolute_row[31:0]>=frontier[head];
      wire [31:0] private_slot=absolute_row[31:0]-frontier[head];
      wire [31:0] write_address=32'(head)*(4*CW)+32'(private_count[head])*CW+s_req_col;
      wire [31:0] read_address=32'(head)*(4*CW)+private_slot*CW+s_req_col;
      wire request_transfer=s_req_valid && s_req_ready;
      wire [31:0] selected_position=frontier[commit_head]+{29'd0,commit_slot};
      wire command_bad=cmd_head>3 || cmd_pos>=MAX_SEQ_LEN ||
        (epoch_valid && cmd_epoch!=epoch) ||
        (cmd_head<4 && (private_count[cmd_head[1:0]]>=4 ||
         cmd_pos!=frontier[cmd_head[1:0]]+{29'd0,private_count[cmd_head[1:0]]}));

      assign cmd_ready=enabled && !failed && state==IDLE && !commit_valid;
      assign release_ready=enabled && !failed && state==ACTIVE && written==CW && !s_req_valid;
      assign commit_ready=enabled && !failed && state==IDLE;
      assign commit_done=enabled && state==COMMIT_COMPLETE;
      assign idle=enabled && !failed && state==IDLE;
      assign fault=enabled && failed;
      assign s_req_ready=enabled && !failed && state==ACTIVE && !release_valid;
      assign s_rsp_valid=enabled && (state==LOCAL_RESPONSE || state==PREFIX_PUBLISH);
      assign s_rsp_error=s_rsp_valid && response_error;
      assign s_rsp_rdata=!s_rsp_valid || response_error || response_write ? 32'd0 :
        state==PREFIX_PUBLISH ? prefix_word : private_q;
      assign c_req_valid=enabled && !failed &&
        (state==PREFIX_REQUEST || state==COMMIT_REQUEST);
      assign c_req_write=c_req_valid && state==COMMIT_REQUEST;
      assign c_req_kind=c_req_valid ? 4'd12 : 4'd0;
      assign c_req_layer=!c_req_valid ? 32'd0 : NUM_LAYERS+
        (state==COMMIT_REQUEST ? {30'd0,commit_head} : {30'd0,head});
      assign c_req_proj=c_req_valid ? 3'd6 : 3'd0;
      assign c_req_row=!c_req_valid ? 32'd0 :
        state==COMMIT_REQUEST ? selected_position : prefix_row;
      assign c_req_col=!c_req_valid ? 32'd0 :
        state==COMMIT_REQUEST ? commit_col : prefix_col;
      assign c_req_wdata=c_req_write ? commit_q : 32'd0;
      assign c_rsp_ready=enabled && !failed &&
        (state==PREFIX_RESPONSE || state==COMMIT_RESPONSE);

      always @(posedge clk) begin
        if (request_transfer && !request_bad) begin
          if (s_req_write) candidates[AW'(write_address)]<=s_req_wdata;
          else if (private_read) private_q<=candidates[AW'(read_address)];
        end
        if (enabled && !failed && state==COMMIT_READ)
          commit_q<=candidates[commit_address];
      end

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state<=IDLE; armed<=0; failed<=0; epoch_valid<=0;
          response_error<=0; response_write<=0; epoch<=0; position<=0; written<=0;
          through_pos<=0; head<=0; commit_head<=0; commit_slot<=0;
          committed_rows<=0; commit_col<=0; prefix_row<=0; prefix_col<=0;
          prefix_word<=0; commit_address<=0;
          for (integer h=0;h<4;h=h+1) begin frontier[h]<=h+1; private_count[h]<=0; end
        end else begin
          armed<=1;
          if (flush) begin
            state<=IDLE; failed<=0; epoch_valid<=0; written<=0;
            response_error<=0; response_write<=0;
            for (integer h=0;h<4;h=h+1) begin frontier[h]<=h+1; private_count[h]<=0; end
          end else case (state)
            IDLE: begin
              if (commit_valid && commit_ready) begin
                if (commit_through_pos>=MAX_SEQ_LEN) begin failed<=1; state<=FAULTED; end
                else begin
                  through_pos<=commit_through_pos; commit_head<=0;
                  commit_slot<=0; committed_rows<=0; commit_col<=0; state<=COMMIT_SELECT;
                end
              end else if (cmd_valid && cmd_ready) begin
                if (command_bad) begin failed<=1; state<=FAULTED; end
                else begin
                  epoch<=cmd_epoch; epoch_valid<=1; head<=cmd_head[1:0];
                  position<=cmd_pos; written<=0; state<=ACTIVE;
                end
              end
            end
            ACTIVE: begin
              if (release_valid && release_ready) begin
                private_count[head]<=private_count[head]+1'b1; state<=IDLE;
              end else if (request_transfer) begin
                response_error<=request_bad; response_write<=s_req_write;
                if (request_bad) begin failed<=1; state<=LOCAL_RESPONSE; end
                else if (s_req_write || private_read) begin
                  if (s_req_write) written<=written+1'b1;
                  state<=LOCAL_RESPONSE;
                end else begin
                  prefix_row<=absolute_row[31:0]; prefix_col<=s_req_col;
                  state<=PREFIX_REQUEST;
                end
              end
            end
            LOCAL_RESPONSE: if (s_rsp_ready) begin
              if (failed) state<=FAULTED;
              else state<=ACTIVE;
            end
            PREFIX_REQUEST: if (c_req_ready) state<=PREFIX_RESPONSE;
            PREFIX_RESPONSE: if (c_rsp_valid && c_rsp_ready) begin
              if (c_rsp_error) begin failed<=1; state<=FAULTED; end
              else begin prefix_word<=c_rsp_rdata; state<=PREFIX_PUBLISH; end
            end
            PREFIX_PUBLISH: if (s_rsp_ready) state<=ACTIVE;
            COMMIT_SELECT: begin
              if (commit_slot>=private_count[commit_head] || selected_position>through_pos) begin
                frontier[commit_head]<=frontier[commit_head]+{29'd0,committed_rows};
                private_count[commit_head]<=0;
                if (commit_head==3) state<=COMMIT_COMPLETE;
                else begin
                  commit_head<=commit_head+1'b1; commit_slot<=0;
                  committed_rows<=0; commit_col<=0;
                end
              end else begin
                commit_address<=AW'(32'(commit_head)*(4*CW)+32'(commit_slot)*CW+commit_col);
                state<=COMMIT_READ;
              end
            end
            COMMIT_READ: state<=COMMIT_REQUEST;
            COMMIT_REQUEST: if (c_req_ready) state<=COMMIT_RESPONSE;
            COMMIT_RESPONSE: if (c_rsp_valid && c_rsp_ready) begin
              if (c_rsp_error) begin failed<=1; state<=FAULTED; end
              else begin
                if (commit_col==CW-1) begin
                  commit_col<=0; commit_slot<=commit_slot+1'b1;
                  committed_rows<=committed_rows+1'b1;
                end else commit_col<=commit_col+1'b1;
                state<=COMMIT_SELECT;
              end
            end
            COMMIT_COMPLETE: state<=IDLE;
            FAULTED: state<=FAULTED;
            default: begin failed<=1; state<=FAULTED; end
          endcase
        end
      end
    end
  endgenerate
endmodule
