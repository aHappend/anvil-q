module anvil_d2_fp8_adapter #(
  parameter integer CLIENTS=7, NUM_LAYERS=27, HIDDEN_SIZE=2048,
  parameter integer KV_LORA_RANK=512, MOE_INTERMEDIATE_SIZE=1408,
  parameter integer ROUTED_EXPERTS=64, MAX_SEQ_LEN=32768, MTP_K=4,
  localparam integer SC=CLIENTS>=1 && CLIENTS<=32 ? CLIENTS : 1
) (
  input wire clk, rst_n, flush, fp8_enable,
  input wire [31:0] epoch,
  output wire idle, fault,
  input wire [SC-1:0] s_req_valid, s_req_write,
  output wire [SC-1:0] s_req_ready,
  input wire [SC*4-1:0] s_req_kind,
  input wire [SC*32-1:0] s_req_layer,
  input wire [SC*3-1:0] s_req_proj,
  input wire [SC*32-1:0] s_req_row, s_req_col, s_req_wdata,
  output wire [SC-1:0] s_rsp_valid, s_rsp_error,
  input wire [SC-1:0] s_rsp_ready,
  output wire [SC*32-1:0] s_rsp_rdata,
  output wire [SC-1:0] c_req_valid, c_req_write,
  input wire [SC-1:0] c_req_ready,
  output wire [SC*4-1:0] c_req_kind,
  output wire [SC*32-1:0] c_req_layer,
  output wire [SC*3-1:0] c_req_proj,
  output wire [SC*32-1:0] c_req_row, c_req_col, c_req_wdata,
  input wire [SC-1:0] c_rsp_valid, c_rsp_error,
  output wire [SC-1:0] c_rsp_ready,
  input wire [SC*32-1:0] c_rsp_rdata,
  output wire group_cmd_valid,
  input wire group_cmd_ready,
  output wire group_cmd_write, group_cmd_expert,
  output wire [31:0] group_cmd_epoch, group_cmd_layer, group_cmd_row, group_cmd_base_col,
  output wire [8:0] group_cmd_count,
  output wire group_in_valid,
  input wire group_in_ready,
  output wire signed [31:0] group_in_q16,
  input wire group_out_valid,
  output wire group_out_ready,
  input wire signed [31:0] group_out_q16,
  input wire [6:0] group_out_index,
  input wire group_out_last, group_done, group_error
);
  generate
    if (CLIENTS<1 || CLIENTS>32 || NUM_LAYERS<1 || NUM_LAYERS>36 ||
        HIDDEN_SIZE<8 || HIDDEN_SIZE>2048 || (HIDDEN_SIZE & 7)!=0 ||
        KV_LORA_RANK<1 || KV_LORA_RANK>512 || MOE_INTERMEDIATE_SIZE<8 ||
        MOE_INTERMEDIATE_SIZE>1408 || (MOE_INTERMEDIATE_SIZE & 7)!=0 ||
        ROUTED_EXPERTS<1 || ROUTED_EXPERTS>64 ||
        MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768 || MTP_K!=4) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: FP8 scalar adapter geometry");
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
      assign group_cmd_valid=0;
      assign group_cmd_write=0;
      assign group_cmd_expert=0;
      assign group_cmd_epoch=0;
      assign group_cmd_layer=0;
      assign group_cmd_row=0;
      assign group_cmd_base_col=0;
      assign group_cmd_count=0;
      assign group_in_valid=0;
      assign group_in_q16=0;
      assign group_out_ready=0;
    end else begin: adapter
      localparam integer CW=SC==1 ? 1 : $clog2(SC);
      localparam IDLE=0, LOOKUP=1, HIT_READ=2, RESPONSE=3;
      localparam READ_COMMAND=4, READ_STREAM=5, READ_DONE=6;
      localparam WRITE_FILL=7, WRITE_COMMAND=8, WRITE_READ=9, WRITE_FEED=10;
      localparam WRITE_DONE=11, FAULTED=12;
      reg [3:0] state;
      reg armed, failed, request_expert, request_write, response_failed, continue_fill;
      reg [CW-1:0] owner, cursor;
      reg [SC-1:0] external_owned;
      reg [31:0] request_epoch, request_layer, request_row, request_base;
      reg [8:0] request_count;
      reg [6:0] request_index, feed_index;
      reg [7:0] fill_count, receive_count;
      reg [3:0] victim, selected_line;
      reg [15:0] line_valid, line_expert;
      reg [31:0] line_epoch [0:15], line_layer [0:15];
      reg [31:0] line_row [0:15], line_base [0:15];
      reg [8:0] line_count [0:15];
      (* ramstyle="M20K", nomem2reg *) reg signed [31:0] decoded [0:2047];
      (* ramstyle="M20K", nomem2reg *) reg signed [31:0] captured [0:127];
      reg signed [31:0] decoded_q, captured_q;
      reg [SC-1:0] transformed, expert_address, ready_local;
      reg [SC-1:0] response_valids, response_errors;
      reg [SC*32-1:0] response_words;
      reg found, hit;
      reg [CW-1:0] selected;
      reg [3:0] hit_line;
      reg [31:0] selected_cols, selected_rows, selected_base, remaining;
      reg [8:0] selected_count;
      reg selected_legal;
      integer n, offset, candidate, l;
      wire enabled=rst_n && armed && !flush;
      wire transfer=enabled && found && s_req_valid[selected] && ready_local[selected];
      wire capture=transfer && s_req_write[selected] && selected_legal &&
        (state==IDLE || state==WRITE_FILL);
      wire receiving=enabled && state==READ_STREAM && group_out_valid && group_out_ready;
      wire stream_bad=receiving &&
        (group_out_index!=receive_count[6:0] ||
         group_out_last!=({1'b0,receive_count}+9'd1==request_count));
      wire write_matches=s_req_write[owner] && !expert_address[owner] &&
        s_req_layer[owner*32+:32]==request_layer &&
        s_req_row[owner*32+:32]==request_row &&
        s_req_col[owner*32+:32]==request_base+{24'd0,fill_count} &&
        epoch==request_epoch;

      assign fault=enabled && failed;
      assign idle=enabled && !failed && state==IDLE && external_owned==0;
      assign group_cmd_valid=enabled && !failed &&
        (state==READ_COMMAND || state==WRITE_COMMAND);
      assign group_cmd_write=group_cmd_valid && request_write;
      assign group_cmd_expert=group_cmd_valid && request_expert;
      assign group_cmd_epoch=group_cmd_valid ? request_epoch : 32'd0;
      assign group_cmd_layer=group_cmd_valid ? request_layer : 32'd0;
      assign group_cmd_row=group_cmd_valid ? request_row : 32'd0;
      assign group_cmd_base_col=group_cmd_valid ? request_base : 32'd0;
      assign group_cmd_count=group_cmd_valid ? request_count : 9'd0;
      assign group_in_valid=enabled && !failed && state==WRITE_FEED;
      assign group_in_q16=group_in_valid ? captured_q : 32'sd0;
      assign group_out_ready=enabled && !failed && state==READ_STREAM;
      assign s_rsp_valid=response_valids;
      assign s_rsp_error=response_errors;
      assign s_rsp_rdata=response_words;

      always @* begin
        transformed=0; expert_address=0;
        for (n=0;n<SC;n=n+1) begin
          expert_address[n]=(s_req_kind[n*4+:4]==15 || s_req_kind[n*4+:4]==12) &&
            s_req_proj[n*3+:3]==5 &&
            s_req_row[n*32+25+:7]<ROUTED_EXPERTS &&
            s_req_row[n*32+23+:2]!=3 && !s_req_write[n];
          transformed[n]=fp8_enable &&
            ((s_req_kind[n*4+:4]==15 && s_req_proj[n*3+:3]==3 &&
              s_req_col[n*32+:32]<KV_LORA_RANK) || expert_address[n]);
        end
        found=0; selected=owner; candidate=0; ready_local=0;
        if (enabled && !failed) begin
          if (state==IDLE) begin
            for (offset=0;offset<SC;offset=offset+1) begin
              candidate=32'(cursor)+offset;
              if (candidate>=SC) candidate=candidate-SC;
              if (!found && transformed[candidate] && s_req_valid[candidate] &&
                  !external_owned[candidate]) begin
                found=1; selected=CW'(candidate);
              end
            end
          end else if (state==WRITE_FILL && transformed[owner] &&
              s_req_valid[owner] && !external_owned[owner]) begin
            found=1; selected=owner;
          end
          if (found) ready_local[selected]=1;
        end
        selected_cols=KV_LORA_RANK;
        selected_rows=MAX_SEQ_LEN;
        if (expert_address[selected]) begin
          if (s_req_row[selected*32+23+:2]==2) begin
            selected_cols=MOE_INTERMEDIATE_SIZE; selected_rows=HIDDEN_SIZE;
          end else begin selected_cols=HIDDEN_SIZE; selected_rows=MOE_INTERMEDIATE_SIZE; end
        end
        selected_base={s_req_col[selected*32+7+:25],7'd0};
        remaining=selected_cols-selected_base;
        selected_count=remaining>128 ? 9'd128 : remaining[8:0];
        selected_legal=(s_req_kind[selected*4+:4]==12 ?
          (expert_address[selected] && s_req_layer[selected*32+:32]>=NUM_LAYERS &&
           s_req_layer[selected*32+:32]<NUM_LAYERS+MTP_K) :
          s_req_layer[selected*32+:32]<NUM_LAYERS) &&
          s_req_col[selected*32+:32]<selected_cols &&
          (expert_address[selected] ?
            {9'd0,s_req_row[selected*32+:23]}<selected_rows :
            s_req_row[selected*32+:32]<selected_rows);
        if (state==WRITE_FILL) selected_legal=selected_legal && write_matches;
        else if (s_req_write[selected])
          selected_legal=selected_legal && s_req_col[selected*32+:7]==0;

        hit=0; hit_line=0;
        for (integer k=0;k<16;k=k+1) begin
          if (!hit && line_valid[k] && line_expert[k]==request_expert &&
              line_epoch[k]==request_epoch && line_layer[k]==request_layer &&
              line_row[k]==request_row && line_base[k]==request_base &&
              line_count[k]==request_count) begin hit=1; hit_line=4'(k); end
        end
        response_valids=0; response_errors=0; response_words=0;
        if (enabled) begin
          for (integer r=0;r<SC;r=r+1) begin
            if (external_owned[r]) begin
              response_valids[r]=c_rsp_valid[r];
              response_errors[r]=c_rsp_valid[r] && c_rsp_error[r];
              response_words[r*32+:32]=c_rsp_valid[r] ? c_rsp_rdata[r*32+:32] : 32'd0;
            end
          end
          if (state==RESPONSE) begin
            response_valids[owner]=1;
            response_errors[owner]=response_failed;
            response_words[owner*32+:32]=request_write || response_failed ? 32'd0 : decoded_q;
          end
        end
      end

      for (genvar c=0;c<SC;c=c+1) begin: external_port
        wire locally_owned=state!=IDLE && state!=WRITE_FILL && owner==c;
        wire passthrough=enabled && !external_owned[c] && !locally_owned && !transformed[c];
        assign s_req_ready[c]=enabled && !external_owned[c] && !locally_owned &&
          (transformed[c] ? ready_local[c] : c_req_ready[c]) ||
          (enabled && state==WRITE_FILL && owner==c && ready_local[c]);
        assign c_req_valid[c]=passthrough && s_req_valid[c];
        assign c_req_write[c]=c_req_valid[c] && s_req_write[c];
        assign c_req_kind[c*4+:4]=c_req_valid[c] ? s_req_kind[c*4+:4] : 4'd0;
        assign c_req_layer[c*32+:32]=c_req_valid[c] ? s_req_layer[c*32+:32] : 32'd0;
        assign c_req_proj[c*3+:3]=c_req_valid[c] ? s_req_proj[c*3+:3] : 3'd0;
        assign c_req_row[c*32+:32]=c_req_valid[c] ? s_req_row[c*32+:32] : 32'd0;
        assign c_req_col[c*32+:32]=c_req_valid[c] ? s_req_col[c*32+:32] : 32'd0;
        assign c_req_wdata[c*32+:32]=c_req_valid[c] ? s_req_wdata[c*32+:32] : 32'd0;
        assign c_rsp_ready[c]=enabled && external_owned[c] && s_rsp_ready[c];
      end

      always @(posedge clk) begin
        if (capture) captured[state==IDLE ? 7'd0 : fill_count[6:0]]<=s_req_wdata[selected*32+:32];
        if (enabled && state==WRITE_READ) captured_q<=captured[feed_index];
        if (receiving && !stream_bad) decoded[{selected_line,group_out_index}]<=group_out_q16;
        if (enabled && state==HIT_READ) decoded_q<=decoded[{selected_line,request_index}];
      end
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state<=IDLE; armed<=0; failed<=0; request_expert<=0; request_write<=0;
          response_failed<=0; continue_fill<=0; owner<=0; cursor<=0; external_owned<=0;
          request_epoch<=0; request_layer<=0; request_row<=0; request_base<=0;
          request_count<=0; request_index<=0; feed_index<=0; fill_count<=0;
          receive_count<=0; victim<=0; selected_line<=0; line_valid<=0; line_expert<=0;
          for (l=0;l<16;l=l+1) begin
            line_epoch[l]<=0; line_layer[l]<=0; line_row[l]<=0;
            line_base[l]<=0; line_count[l]<=0;
          end
        end else begin
          armed<=1;
          if (flush) begin
            state<=IDLE; failed<=0; response_failed<=0; continue_fill<=0;
            external_owned<=0; line_valid<=0; fill_count<=0; receive_count<=0;
            feed_index<=0; owner<=0; cursor<=0; victim<=0;
          end else begin
            for (integer c=0;c<SC;c=c+1) begin
              if (c_rsp_valid[c] && c_rsp_ready[c]) external_owned[c]<=0;
              if (c_req_valid[c] && c_req_ready[c]) external_owned[c]<=1;
            end
            if (stream_bad || (group_done && group_error &&
                (state==READ_STREAM || state==READ_DONE || state==WRITE_DONE))) begin
              failed<=1; response_failed<=1; continue_fill<=0;
              line_valid<=0; state<=RESPONSE;
            end else case (state)
              IDLE: if (transfer) begin
                owner<=selected; request_expert<=expert_address[selected];
                request_write<=s_req_write[selected]; response_failed<=0; continue_fill<=0;
                request_epoch<=epoch; request_layer<=s_req_layer[selected*32+:32];
                request_row<=s_req_row[selected*32+:32]; request_base<=selected_base;
                request_count<=selected_count; request_index<=s_req_col[selected*32+:7];
                if (selected==SC-1) cursor<=0; else cursor<=selected+1'b1;
                if (!selected_legal) begin
                  response_failed<=1; failed<=1; line_valid<=0; state<=RESPONSE;
                end else if (s_req_write[selected]) begin
                  for (integer k=0;k<16;k=k+1)
                    if (!line_expert[k] && line_layer[k]==s_req_layer[selected*32+:32] &&
                        line_row[k]==s_req_row[selected*32+:32] && line_base[k]==selected_base)
                      line_valid[k]<=0;
                  fill_count<=1; feed_index<=0;
                  if (selected_count==1) state<=WRITE_COMMAND;
                  else begin continue_fill<=1; state<=RESPONSE; end
                end else state<=LOOKUP;
              end
              LOOKUP: begin
                if (hit) begin selected_line<=hit_line; state<=HIT_READ; end
                else begin
                  selected_line<=victim; line_valid[victim]<=0; victim<=victim+1'b1;
                  receive_count<=0; state<=READ_COMMAND;
                end
              end
              HIT_READ: state<=RESPONSE;
              RESPONSE: if (s_rsp_ready[owner]) begin
                if (failed) state<=FAULTED;
                else if (continue_fill) state<=WRITE_FILL;
                else state<=IDLE;
              end
              READ_COMMAND: if (group_cmd_valid && group_cmd_ready) state<=READ_STREAM;
              READ_STREAM: if (receiving) begin
                receive_count<=receive_count+1'b1;
                if (group_out_last) state<=READ_DONE;
              end
              READ_DONE: if (group_done) begin
                if ({1'b0,receive_count}!=request_count) begin
                  failed<=1; response_failed<=1; line_valid<=0; state<=RESPONSE;
                end else begin
                  line_valid[selected_line]<=1; line_expert[selected_line]<=request_expert;
                  line_epoch[selected_line]<=request_epoch; line_layer[selected_line]<=request_layer;
                  line_row[selected_line]<=request_row; line_base[selected_line]<=request_base;
                  line_count[selected_line]<=request_count; state<=HIT_READ;
                end
              end
              WRITE_FILL: if (transfer) begin
                if (!selected_legal) begin
                  failed<=1; response_failed<=1; continue_fill<=0;
                  line_valid<=0; state<=RESPONSE;
                end else begin
                  fill_count<=fill_count+1'b1;
                  if ({1'b0,fill_count}+9'd1==request_count) begin
                    continue_fill<=0; feed_index<=0; state<=WRITE_COMMAND;
                  end else begin continue_fill<=1; state<=RESPONSE; end
                end
              end
              WRITE_COMMAND: if (group_cmd_valid && group_cmd_ready) begin
                feed_index<=0; state<=WRITE_READ;
              end
              WRITE_READ: state<=WRITE_FEED;
              WRITE_FEED: if (group_in_valid && group_in_ready) begin
                if ({2'd0,feed_index}+9'd1==request_count) state<=WRITE_DONE;
                else begin feed_index<=feed_index+1'b1; state<=WRITE_READ; end
              end
              WRITE_DONE: if (group_done) begin continue_fill<=0; state<=RESPONSE; end
              FAULTED: state<=FAULTED;
              default: begin
                failed<=1; response_failed<=1; continue_fill<=0;
                line_valid<=0; state<=RESPONSE;
              end
            endcase
          end
        end
      end
    end
  endgenerate
endmodule
