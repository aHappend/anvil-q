module anvil_d2_verify_cache #(
  parameter integer NUM_LAYERS=27, KV_LORA_RANK=512,
  parameter integer QK_ROPE_HEAD_DIM=64, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush,
  input wire layer_valid,
  output wire layer_ready,
  input wire [31:0] layer_epoch, layer_index, layer_first_pos,
  input wire [2:0] layer_lanes,
  input wire layer_fp8,
  output wire layer_done,
  input wire commit_valid,
  output wire commit_ready,
  input wire [2:0] commit_count,
  output wire commit_done,
  output wire fault, idle,
  input wire [3:0] s_req_valid, s_req_write,
  output wire [3:0] s_req_ready,
  input wire [127:0] s_req_layer, s_req_row, s_req_col, s_req_wdata,
  output wire [3:0] s_rsp_valid, s_rsp_error,
  input wire [3:0] s_rsp_ready,
  output wire [127:0] s_rsp_rdata,
  output wire c_req_valid,
  input wire c_req_ready,
  output wire c_req_write,
  output wire [3:0] c_req_kind,
  output wire [31:0] c_req_layer,
  output wire [2:0] c_req_proj,
  output wire [31:0] c_req_row, c_req_col, c_req_wdata,
  input wire c_rsp_valid,
  output wire c_rsp_ready,
  input wire [31:0] c_rsp_rdata,
  input wire c_rsp_error
);
  generate
    if (NUM_LAYERS<1 || NUM_LAYERS>36 || KV_LORA_RANK<1 ||
        KV_LORA_RANK>512 || QK_ROPE_HEAD_DIM<2 || QK_ROPE_HEAD_DIM>64 ||
        (QK_ROPE_HEAD_DIM & 1)!=0 || MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: verification cache geometry");
      assign layer_ready=0;
      assign layer_done=0;
      assign commit_ready=0;
      assign commit_done=0;
      assign fault=0;
      assign idle=0;
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
      localparam integer WORDS=NUM_LAYERS*4*CW, AW=$clog2(WORDS);
      localparam IDLE=0, CAPTURE=1, WRITE_ACK=2, QUANT_COMMAND=3;
      localparam QUANT_READ=4, QUANT_FEED=5, QUANT_OUTPUT=6;
      localparam DEQUANT_WAIT=7, CONVERT=8, CONVERT_WAIT=9, EFFECTIVE_STORE=10;
      localparam QUANT_FINISH=11, BARRIER=12, GATHER=13, LOCAL_READ=14;
      localparam LOCAL_CAPTURE=15, PREFIX_REQUEST=16, PREFIX_RESPONSE=17;
      localparam BROADCAST=18, LAYER_COMPLETE=19;
      localparam COMMIT_READ=20, COMMIT_REQUEST=21, COMMIT_RESPONSE=22;
      localparam COMMIT_COMPLETE=23, FAULTED=24;
      reg [4:0] state;
      reg armed, failed, block_valid, fp8_mode, quant_finished, read_pass;
      reg [31:0] epoch, current_layer, first_pos, next_layer;
      reg [2:0] lanes, committed_lanes;
      reg [NUM_LAYERS-1:0] completed_layers;
      reg [31:0] written [0:3];
      reg [1:0] writer_cursor, writer, quant_lane, commit_lane;
      reg [31:0] read_row, read_col, commit_layer, commit_col;
      reg [31:0] layer_base, quant_lane_base, commit_layer_base, commit_lane_base;
      reg [31:0] group_base;
      reg [8:0] group_count;
      reg [6:0] feed_index, result_index;
      reg [3:0] response_pending, request_mask;
      reg [31:0] response_word;
      reg [15:0] dequant_bf16;
      reg signed [31:0] converted;
      reg [AW-1:0] read_address;
      (* ramstyle="M20K", nomem2reg *) reg signed [31:0] raw [0:WORDS-1];
      (* ramstyle="M20K", nomem2reg *) reg signed [31:0] effective [0:WORDS-1];
      reg signed [31:0] raw_q, effective_q;
      reg writer_found, all_written, all_at_barrier, gather_complete, request_bad;
      reg [1:0] selected_writer;
      reg [3:0] write_ready, read_ready, expected_mask, lane_mask;
      reg [127:0] response_data;
      integer n, offset, candidate;
      wire enabled=rst_n && armed && !flush;
      wire write_transfer=enabled && state==CAPTURE && writer_found &&
        s_req_valid[selected_writer] && write_ready[selected_writer];
      wire [31:0] write_address=layer_base+32'(selected_writer)*CW+
        s_req_col[selected_writer*32+:32];
      wire [31:0] effective_address=quant_lane_base+group_base+{25'd0,result_index};
      wire quant_ready, quant_input_ready, quant_valid, quant_last, quant_done, quant_error;
      wire [7:0] quant_fp8;
      wire [6:0] quant_index;
      wire [31:0] quant_scale;
      wire dequant_ready, dequant_valid, dequant_error;
      wire [31:0] dequant_fp32;
      wire [15:0] dequant_result;
      wire convert_ready, convert_valid, convert_error;
      wire signed [31:0] convert_result;
      wire children_flush=flush || failed;
      wire quant_output_transfer=quant_valid && enabled && state==QUANT_OUTPUT && dequant_ready;
      wire quant_protocol_bad=quant_output_transfer &&
        (quant_index!=result_index ||
         quant_last!=({2'd0,result_index}+9'd1==group_count));
      wire arithmetic_fault=(quant_done && quant_error) ||
        (state==DEQUANT_WAIT && dequant_valid && dequant_error) ||
        (state==CONVERT_WAIT && convert_valid && convert_error) || quant_protocol_bad;
      wire broadcast_finished=(response_pending & ~s_rsp_ready)==0;
      wire memory_response=c_rsp_valid && c_rsp_ready;
      wire first_layer_bad=layer_index==0 && layer_first_pos+{29'd0,layer_lanes}>MAX_SEQ_LEN;
      wire subsequent_layer_bad=layer_index!=0 &&
        (!block_valid || layer_index!=next_layer || layer_epoch!=epoch ||
         layer_first_pos!=first_pos || layer_lanes!=lanes || layer_fp8!=fp8_mode);
      wire layer_command_bad=layer_index>=NUM_LAYERS || layer_lanes<1 ||
        layer_lanes>4 || layer_first_pos>=MAX_SEQ_LEN ||
        first_layer_bad || subsequent_layer_bad;

      assign layer_ready=enabled && !failed && state==IDLE;
      assign layer_done=enabled && state==LAYER_COMPLETE;
      assign commit_ready=enabled && !failed && state==IDLE && block_valid &&
        &completed_layers;
      assign commit_done=enabled && state==COMMIT_COMPLETE;
      assign idle=enabled && !failed && state==IDLE;
      assign fault=enabled && failed;
      assign s_req_ready=enabled ? write_ready | read_ready : 4'd0;
      assign s_rsp_valid=enabled && (state==WRITE_ACK || state==BROADCAST) ?
        response_pending : 4'd0;
      assign s_rsp_error=0;
      assign s_rsp_rdata=response_data;
      assign c_req_valid=enabled && !failed &&
        (state==PREFIX_REQUEST || state==COMMIT_REQUEST);
      assign c_req_write=c_req_valid && state==COMMIT_REQUEST;
      assign c_req_kind=c_req_valid ? 4'd15 : 4'd0;
      assign c_req_layer=!c_req_valid ? 32'd0 :
        state==COMMIT_REQUEST ? commit_layer : current_layer;
      assign c_req_proj=c_req_valid ? 3'd3 : 3'd0;
      assign c_req_row=!c_req_valid ? 32'd0 : state==COMMIT_REQUEST ?
        first_pos+{30'd0,commit_lane} : read_row;
      assign c_req_col=!c_req_valid ? 32'd0 : state==COMMIT_REQUEST ? commit_col : read_col;
      assign c_req_wdata=c_req_write ? raw_q : 32'd0;
      assign c_rsp_ready=enabled && !failed &&
        (state==PREFIX_RESPONSE || state==COMMIT_RESPONSE);

      always @* begin
        writer_found=0; selected_writer=0; candidate=0; write_ready=0; read_ready=0;
        all_written=1; all_at_barrier=1; request_bad=0;
        lane_mask=0; expected_mask=0; gather_complete=1;
        response_data=0;
        for (n=0;n<4;n=n+1) begin
          lane_mask[n]=n<lanes;
          if (n<lanes && written[n]!=CW) all_written=0;
          if (n<lanes && !(s_req_valid[n] && !s_req_write[n] &&
              s_req_layer[n*32+:32]==current_layer &&
              s_req_row[n*32+:32]==0 && s_req_col[n*32+:32]==0))
            all_at_barrier=0;
          expected_mask[n]=n<lanes && read_row<=first_pos+n;
          if (expected_mask[n] && !(s_req_valid[n] && !s_req_write[n] &&
              s_req_layer[n*32+:32]==current_layer &&
              s_req_row[n*32+:32]==read_row && s_req_col[n*32+:32]==read_col))
            gather_complete=0;
          if (enabled && (state==WRITE_ACK || state==BROADCAST) && response_pending[n])
            response_data[n*32+:32]=state==WRITE_ACK ? 32'd0 : response_word;
          if (enabled && s_req_valid[n] && (state==CAPTURE || state==BARRIER || state==GATHER)) begin
            if (n>=lanes || s_req_layer[n*32+:32]!=current_layer) request_bad=1;
            else if (state==CAPTURE && s_req_write[n]) begin
              if (s_req_row[n*32+:32]!=first_pos+n ||
                  s_req_col[n*32+:32]!=written[n] || written[n]>=CW) request_bad=1;
            end else if (!s_req_write[n]) begin
              if (state==CAPTURE || state==BARRIER) begin
                if (written[n]!=CW || s_req_row[n*32+:32]!=0 ||
                    s_req_col[n*32+:32]!=0) request_bad=1;
              end else if (expected_mask[n]) begin
                if (s_req_row[n*32+:32]!=read_row || s_req_col[n*32+:32]!=read_col)
                  request_bad=1;
              end else if (read_pass || s_req_row[n*32+:32]!=0 ||
                  s_req_col[n*32+:32]!=0) request_bad=1;
            end else request_bad=1;
          end
        end
        if (enabled && !failed && state==CAPTURE) begin
          for (offset=0;offset<4;offset=offset+1) begin
            candidate=32'(writer_cursor)+offset;
            if (candidate>=4) candidate=candidate-4;
            if (!writer_found && candidate<lanes && s_req_valid[candidate] &&
                s_req_write[candidate]) begin
              writer_found=1; selected_writer=2'(candidate);
            end
          end
          if (writer_found && !request_bad) write_ready[selected_writer]=1;
        end
        if (enabled && !failed && state==GATHER && gather_complete && !request_bad)
          read_ready=expected_mask;
      end

      anvil_d2_fp8_group_quantizer quantizer (
        .clk(clk),.rst_n(rst_n),.flush(children_flush),
        .cmd_valid(enabled && state==QUANT_COMMAND),.cmd_ready(quant_ready),
        .cmd_count(group_count),
        .in_valid(enabled && state==QUANT_FEED),.in_ready(quant_input_ready),.in_q16(raw_q),
        .out_valid(quant_valid),.out_ready(enabled && state==QUANT_OUTPUT && dequant_ready),
        .out_fp8(quant_fp8),.out_index(quant_index),.out_last(quant_last),
        .out_scale(quant_scale),.done(quant_done),.error(quant_error)
      );
      anvil_d2_fp8_dequant dequantizer (
        .clk(clk),.rst_n(rst_n),.flush(children_flush),
        .in_valid(enabled && state==QUANT_OUTPUT && quant_valid),.in_ready(dequant_ready),
        .in_fp8(quant_fp8),.in_scale(quant_scale),
        .out_valid(dequant_valid),.out_ready(enabled && state==DEQUANT_WAIT),
        .out_fp32(dequant_fp32),.out_bf16(dequant_result),.out_error(dequant_error)
      );
      anvil_d2_bf16_to_q16 consumer_boundary (
        .clk(clk),.rst_n(rst_n),.flush(children_flush),
        .in_valid(enabled && state==CONVERT),.in_ready(convert_ready),
        .in_bf16(dequant_bf16),
        .out_valid(convert_valid),.out_ready(enabled && state==CONVERT_WAIT),
        .out_q16(convert_result),.out_error(convert_error)
      );

      always @(posedge clk) begin
        if (write_transfer) raw[AW'(write_address)]<=s_req_wdata[selected_writer*32+:32];
        if (enabled && (state==QUANT_READ || state==COMMIT_READ || state==LOCAL_READ)) begin
          raw_q<=raw[read_address];
          effective_q<=effective[read_address];
        end
        if (enabled && state==EFFECTIVE_STORE) effective[AW'(effective_address)]<=converted;
      end
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state<=IDLE; armed<=0; failed<=0; block_valid<=0; fp8_mode<=0;
          quant_finished<=0; read_pass<=0;
          epoch<=0; current_layer<=0; first_pos<=0; next_layer<=0; lanes<=0;
          committed_lanes<=0; completed_layers<=0; writer_cursor<=0; writer<=0;
          quant_lane<=0; commit_lane<=0; read_row<=0; read_col<=0;
          commit_layer<=0; commit_col<=0; layer_base<=0; quant_lane_base<=0;
          commit_layer_base<=0; commit_lane_base<=0; group_base<=0; group_count<=0;
          feed_index<=0; result_index<=0; response_pending<=0; request_mask<=0;
          response_word<=0; dequant_bf16<=0; converted<=0; read_address<=0;
          for (integer r=0;r<4;r=r+1) written[r]<=0;
        end else begin
          armed<=1;
          if (flush) begin
            state<=IDLE; failed<=0; block_valid<=0; completed_layers<=0;
            response_pending<=0; request_mask<=0; next_layer<=0;
            quant_finished<=0; writer_cursor<=0; read_pass<=0;
            for (integer r=0;r<4;r=r+1) written[r]<=0;
          end else if (!failed && (arithmetic_fault || request_bad ||
              (memory_response && c_rsp_error))) begin
            failed<=1; block_valid<=0; completed_layers<=0;
            response_pending<=0; state<=FAULTED;
          end else begin
            if (quant_done) quant_finished<=1;
            case (state)
              IDLE: begin
                if (layer_valid && layer_ready) begin
                  if (commit_valid || layer_command_bad) begin
                    failed<=1; block_valid<=0; completed_layers<=0; state<=FAULTED;
                  end else begin
                    epoch<=layer_epoch; current_layer<=layer_index; first_pos<=layer_first_pos;
                    lanes<=layer_lanes; fp8_mode<=layer_fp8;
                    layer_base<=layer_index*(4*CW); writer_cursor<=0;
                    if (layer_index==0) begin block_valid<=1; completed_layers<=0; end
                    for (integer r=0;r<4;r=r+1) written[r]<=0;
                    state<=CAPTURE;
                  end
                end else if (commit_valid && commit_ready) begin
                  if (commit_count==0 || commit_count>lanes) begin
                    failed<=1; block_valid<=0; state<=FAULTED;
                  end else begin
                    committed_lanes<=commit_count; commit_layer<=0; commit_lane<=0;
                    commit_col<=0; commit_layer_base<=0; commit_lane_base<=0;
                    read_address<=0; state<=COMMIT_READ;
                  end
                end
              end
              CAPTURE: begin
                if (write_transfer) begin
                  writer<=selected_writer; writer_cursor<=selected_writer+1'b1;
                  written[selected_writer]<=written[selected_writer]+1'b1;
                  response_pending<=4'b0001<<selected_writer;
                  state<=WRITE_ACK;
                end else if (all_written) begin
                  if (fp8_mode) begin
                    quant_lane<=0; quant_lane_base<=layer_base;
                    group_base<=0; feed_index<=0; result_index<=0; quant_finished<=0;
                    group_count<=KV_LORA_RANK>128 ? 9'd128 : 9'(KV_LORA_RANK);
                    state<=QUANT_COMMAND;
                  end else state<=BARRIER;
                end
              end
              WRITE_ACK: if (s_rsp_ready[writer]) begin response_pending<=0; state<=CAPTURE; end
              QUANT_COMMAND: if (quant_ready) begin
                read_address<=AW'(quant_lane_base+group_base);
                feed_index<=0; result_index<=0; quant_finished<=0; state<=QUANT_READ;
              end
              QUANT_READ: state<=QUANT_FEED;
              QUANT_FEED: if (quant_input_ready) begin
                if ({2'd0,feed_index}+9'd1==group_count) state<=QUANT_OUTPUT;
                else begin
                  feed_index<=feed_index+1'b1;
                  read_address<=AW'(quant_lane_base+group_base+{25'd0,feed_index}+1'b1);
                  state<=QUANT_READ;
                end
              end
              QUANT_OUTPUT: if (quant_output_transfer) state<=DEQUANT_WAIT;
              DEQUANT_WAIT: if (dequant_valid) begin dequant_bf16<=dequant_result; state<=CONVERT; end
              CONVERT: if (convert_ready) state<=CONVERT_WAIT;
              CONVERT_WAIT: if (convert_valid) begin converted<=convert_result; state<=EFFECTIVE_STORE; end
              EFFECTIVE_STORE: begin
                if ({2'd0,result_index}+9'd1==group_count) state<=QUANT_FINISH;
                else begin result_index<=result_index+1'b1; state<=QUANT_OUTPUT; end
              end
              QUANT_FINISH: if (quant_finished || quant_done) begin
                if (group_base+{23'd0,group_count}<KV_LORA_RANK) begin
                  group_base<=group_base+32'd128;
                  group_count<=KV_LORA_RANK-group_base-32'd128>128 ?
                    9'd128 : 9'(KV_LORA_RANK-group_base-32'd128);
                  state<=QUANT_COMMAND;
                end else if ({1'b0,quant_lane}+3'd1<lanes) begin
                  quant_lane<=quant_lane+1'b1; quant_lane_base<=quant_lane_base+CW;
                  group_base<=0; group_count<=KV_LORA_RANK>128 ? 9'd128 : 9'(KV_LORA_RANK);
                  state<=QUANT_COMMAND;
                end else state<=BARRIER;
              end
              BARRIER: if (all_at_barrier) begin
                read_row<=0; read_col<=0; read_pass<=0; state<=GATHER;
              end
              GATHER: if (gather_complete) begin
                request_mask<=expected_mask;
                if (read_row<first_pos) state<=PREFIX_REQUEST;
                else begin
                  read_address<=AW'(layer_base+(read_row-first_pos)*CW+read_col);
                  state<=LOCAL_READ;
                end
              end
              LOCAL_READ: state<=LOCAL_CAPTURE;
              LOCAL_CAPTURE: begin
                response_word<=fp8_mode && read_col<KV_LORA_RANK ? effective_q : raw_q;
                response_pending<=request_mask; state<=BROADCAST;
              end
              PREFIX_REQUEST: if (c_req_valid && c_req_ready) state<=PREFIX_RESPONSE;
              PREFIX_RESPONSE: if (memory_response) begin
                response_word<=c_rsp_rdata; response_pending<=request_mask; state<=BROADCAST;
              end
              BROADCAST: begin
                response_pending<=response_pending & ~s_rsp_ready;
                if (broadcast_finished) begin
                  if (read_col==CW-1) begin
                    read_col<=0;
                    if (read_row==first_pos+{29'd0,lanes}-1'b1) begin
                      if (read_pass) begin
                        completed_layers[current_layer]<=1; next_layer<=current_layer+1'b1;
                        state<=LAYER_COMPLETE;
                      end else begin read_row<=0; read_pass<=1; state<=GATHER; end
                    end else begin read_row<=read_row+1'b1; state<=GATHER; end
                  end else begin read_col<=read_col+1'b1; state<=GATHER; end
                end
              end
              LAYER_COMPLETE: state<=IDLE;
              COMMIT_READ: state<=COMMIT_REQUEST;
              COMMIT_REQUEST: if (c_req_valid && c_req_ready) state<=COMMIT_RESPONSE;
              COMMIT_RESPONSE: if (memory_response) begin
                if (commit_col!=CW-1) begin
                  commit_col<=commit_col+1'b1;
                  read_address<=AW'(commit_lane_base+commit_col+1'b1);
                  state<=COMMIT_READ;
                end else begin
                  commit_col<=0;
                  if ({1'b0,commit_lane}+3'd1<committed_lanes) begin
                    commit_lane<=commit_lane+1'b1; commit_lane_base<=commit_lane_base+CW;
                    read_address<=AW'(commit_lane_base+CW); state<=COMMIT_READ;
                  end else if (commit_layer!=NUM_LAYERS-1) begin
                    commit_layer<=commit_layer+1'b1; commit_layer_base<=commit_layer_base+4*CW;
                    commit_lane<=0; commit_lane_base<=commit_layer_base+4*CW;
                    read_address<=AW'(commit_layer_base+4*CW); state<=COMMIT_READ;
                  end else begin
                    completed_layers<=0; block_valid<=0; state<=COMMIT_COMPLETE;
                  end
                end
              end
              COMMIT_COMPLETE: state<=IDLE;
              FAULTED: state<=FAULTED;
              default: begin failed<=1; block_valid<=0; completed_layers<=0; state<=FAULTED; end
            endcase
          end
        end
      end
    end
  endgenerate
endmodule
