module anvil_q3_fp_kv_cache #(
  parameter PROFILE=3, NUM_LAYERS=36, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter MAX_SEQ_LEN=32768, CACHE_MODE=0, MODE1_FP8=0, INT4_ASYM=0, CACHE_BLOCK=1,
  localparam CAP=CACHE_MODE==0 ? 2 : CACHE_MODE==1 ? 32 : 64,
  localparam SL=NUM_LAYERS>0 && 128'(NUM_LAYERS)<=128'hffffffff ? NUM_LAYERS : 1
) (
  input wire clk, rst_n, flush, cmd_valid, cmd_fp16,
  output wire cmd_ready,
  input wire [1:0] cmd_op,
  input wire [31:0] cmd_layer, cmd_pos, cmd_head, cmd_dim,
  input wire cmd_phase,
  output wire done, error,
  output wire signed [31:0] read_data,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  localparam [127:0] BLOCKS=(128'(HEAD_DIM)+CAP-1)/CAP;
  localparam SHIFT=$clog2(CAP);
  localparam IDLE=0, CODEC_CMD=1, READ_INPUT=2, READ_WAIT=3, SEND_INPUT=4;
  localparam RECV_OUTPUT=5, WRITE_OUTPUT=6, WRITE_WAIT=7, CODEC_WAIT=8;
  localparam ADVANCE=9, COMPLETE=10, FAULTED=11;
  reg [3:0] state;
  reg failed, reading, value_cache, fp16, codec_finished, output_last;
  reg [31:0] layer, position, head, head_base, block_base, block_index, block_start;
  reg [31:0] input_index, output_index, selected_lane, selected_result;
  reg [31:0] input_word, output_word;
  reg [6:0] length;
  reg [31:0] committed [0:SL-1], prefill_count [0:SL-1];
  reg [SL-1:0] decoding, format_valid, format_fp16;
  wire unit_flush=flush || failed;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==READ_INPUT || state==WRITE_OUTPUT);
  wire metadata_access=CACHE_MODE!=0 && (state==READ_INPUT ? input_index==0 : output_index==0);
  wire [31:0] payload_word_index=state==READ_INPUT ?
    input_index-1'b1 : output_index-1'b1;
  wire [31:0] logical_block=block_base+block_index;
  wire [31:0] cache_col=CACHE_MODE==0 || metadata_access ?
    logical_block : (logical_block<<3)+payload_word_index;
  wire input_last=reading ? (CACHE_MODE==0 || input_index==8) : input_index+1==length;
  wire codec_ready, codec_done, codec_error, codec_in_ready, codec_out_valid, codec_out_last;
  wire [31:0] codec_out_data;
  wire [31:0] command_group=cmd_dim>>SHIFT;
  integer i;

  generate if (PROFILE!=3 || NUM_LAYERS<=0 || NUM_KV_HEADS<=0 || HEAD_DIM<=0 ||
      HEAD_DIM%2!=0 || MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768 ||
      CACHE_MODE<0 || CACHE_MODE>2 || CACHE_BLOCK!=1 ||
      (MODE1_FP8!=0 && MODE1_FP8!=1) || (INT4_ASYM!=0 && INT4_ASYM!=1) ||
      128'(NUM_LAYERS)>128'hffffffff ||
      128'(NUM_KV_HEADS)*128'(HEAD_DIM)>128'hffffffff ||
      128'(NUM_KV_HEADS)*BLOCKS*8>128'hffffffff) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_FP PARAMETER ERROR: KV cache geometry");
  end endgenerate
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  assign read_data=rst_n && !flush && !failed ? selected_result : 32'd0;

  anvil_q3_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==WRITE_OUTPUT),
    .kind(state==READ_INPUT && !reading ? 4'd8 :
      CACHE_MODE==0 ? (value_cache ? 4'd10 : 4'd9) :
      metadata_access ? (value_cache ? 4'd15 : 4'd14) :
      (value_cache ? 4'd13 : 4'd12)),
    .layer(state==READ_INPUT && !reading ? 32'd0 : layer),.proj(3'd0),
    .row(state==READ_INPUT && !reading ? (value_cache ? 32'd4 : 32'd3) : position),
    .col(state==READ_INPUT && !reading ? head_base+block_start+input_index : cache_col),
    .wdata(state==WRITE_OUTPUT ? output_word : 32'd0),.rdata(rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q3_fp_cache_codec #(
    .CACHE_MODE(CACHE_MODE),.MODE1_FP8(MODE1_FP8),.INT4_ASYM(INT4_ASYM)
  ) cache_codec (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .cmd_valid(state==CODEC_CMD),.cmd_ready(codec_ready),
    .cmd_decode(reading),.cmd_fp16(fp16),.cmd_count(length),
    .done(codec_done),.error(codec_error),
    .in_valid(state==SEND_INPUT),.in_ready(codec_in_ready),
    .in_last(input_last),.in_data(input_word),
    .out_valid(codec_out_valid),.out_ready(state==RECV_OUTPUT),
    .out_last(codec_out_last),.out_data(codec_out_data)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; reading<=0; value_cache<=0; fp16<=0;
      codec_finished<=0; output_last<=0; layer<=0; position<=0;
      head<=0; head_base<=0; block_base<=0; block_index<=0; block_start<=0;
      input_index<=0; output_index<=0; selected_lane<=0; selected_result<=0;
      input_word<=0; output_word<=0; length<=0;
      decoding<=0; format_valid<=0; format_fp16<=0;
      for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else if (flush) begin
      state<=IDLE; failed<=0; selected_result<=0; codec_finished<=0;
      decoding<=0; format_valid<=0;
      for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else if (!failed && (memory_fault || (codec_done && codec_error))) begin
      failed<=1; state<=COMPLETE; decoding<=0; format_valid<=0;
      for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else begin
      if (codec_done) codec_finished<=1;
      case (state)
        IDLE: if (cmd_valid) begin
          failed<=0; selected_result<=0; layer<=cmd_layer; position<=cmd_pos;
          fp16<=cmd_fp16; codec_finished<=0; output_last<=0;
          head<=0; head_base<=0; block_base<=0; block_index<=0; block_start<=0;
          input_index<=0; output_index<=0; selected_lane<=0;
          length<=7'(HEAD_DIM<CAP ? HEAD_DIM : CAP);
          reading<=cmd_op!=0; value_cache<=cmd_op==2;
          if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_op>2) begin
            failed<=1; state<=COMPLETE;
          end else if (format_valid[cmd_layer] && format_fp16[cmd_layer]!=cmd_fp16) begin
            failed<=1; state<=COMPLETE;
          end else if (cmd_op==0) begin
            if (cmd_pos!=committed[cmd_layer] ||
                (decoding[cmd_layer] && !cmd_phase) ||
                (decoding[cmd_layer] && cmd_pos<prefill_count[cmd_layer])) begin
              failed<=1; state<=COMPLETE;
            end else begin
              if (cmd_phase && !decoding[cmd_layer]) begin
                decoding[cmd_layer]<=1; prefill_count[cmd_layer]<=committed[cmd_layer];
              end
              format_valid[cmd_layer]<=1; format_fp16[cmd_layer]<=cmd_fp16;
              value_cache<=0; state<=CODEC_CMD;
            end
          end else if (cmd_head>=NUM_KV_HEADS || cmd_dim>=HEAD_DIM ||
              cmd_pos>=committed[cmd_layer]) begin
            failed<=1; state<=COMPLETE;
          end else begin
            head<=cmd_head; head_base<=cmd_head*HEAD_DIM;
            block_base<=cmd_head*32'(BLOCKS); block_index<=command_group;
            block_start<=command_group<<SHIFT;
            selected_lane<=cmd_dim&32'(CAP-1);
            length<=7'(HEAD_DIM-(command_group<<SHIFT)<CAP ?
              HEAD_DIM-(command_group<<SHIFT) : CAP);
            state<=CODEC_CMD;
          end
        end
        CODEC_CMD: if (codec_ready) begin
          codec_finished<=0; input_index<=0; output_index<=0; state<=READ_INPUT;
        end
        READ_INPUT: if (issue) state<=READ_WAIT;
        READ_WAIT: if (memory_complete) begin input_word<=rdata; state<=SEND_INPUT; end
        SEND_INPUT: if (codec_in_ready) begin
          if (input_last) state<=RECV_OUTPUT;
          else begin input_index<=input_index+1'b1; state<=READ_INPUT; end
        end
        RECV_OUTPUT: if (codec_out_valid) begin
          if (reading) begin
            if (output_index==selected_lane) selected_result<=codec_out_data;
            if (codec_out_last) state<=CODEC_WAIT;
            else output_index<=output_index+1'b1;
          end else begin
            output_word<=codec_out_data; output_last<=codec_out_last; state<=WRITE_OUTPUT;
          end
        end
        WRITE_OUTPUT: if (issue) state<=WRITE_WAIT;
        WRITE_WAIT: if (memory_complete) begin
          if (output_last) state<=CODEC_WAIT;
          else begin output_index<=output_index+1'b1; state<=RECV_OUTPUT; end
        end
        CODEC_WAIT: if (codec_finished || codec_done) begin
          if (reading) state<=COMPLETE; else state<=ADVANCE;
        end
        ADVANCE: begin
          if (block_index+1<32'(BLOCKS)) begin
            block_index<=block_index+1'b1; block_start<=block_start+CAP;
            length<=7'(HEAD_DIM-(block_start+CAP)<CAP ? HEAD_DIM-(block_start+CAP) : CAP);
            state<=CODEC_CMD;
          end else if (head+1<NUM_KV_HEADS) begin
            head<=head+1'b1; head_base<=head_base+HEAD_DIM; block_base<=block_base+32'(BLOCKS);
            block_index<=0; block_start<=0; length<=7'(HEAD_DIM<CAP ? HEAD_DIM : CAP);
            state<=CODEC_CMD;
          end else if (!value_cache) begin
            value_cache<=1; head<=0; head_base<=0; block_base<=0; block_index<=0; block_start<=0;
            length<=7'(HEAD_DIM<CAP ? HEAD_DIM : CAP); state<=CODEC_CMD;
          end else begin committed[layer]<=position+1'b1; state<=COMPLETE; end
        end
        COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
        FAULTED: state<=FAULTED;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
