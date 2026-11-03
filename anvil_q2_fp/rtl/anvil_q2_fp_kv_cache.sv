module anvil_q2_fp_kv_cache #(
  parameter NUM_LAYERS=28, NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768,
  CACHE_MODE=0, CACHE_BLOCK=16, FP_FORMAT=0,
  SL=(NUM_LAYERS>0 && MAX_SEQ_LEN>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 &&
      128'(NUM_LAYERS)*MAX_SEQ_LEN*NUM_KV_HEADS*HEAD_DIM<=128'd4294967295) ?
      NUM_LAYERS : 1,
  CB=(CACHE_BLOCK>0 && CACHE_BLOCK<=65536 &&
      (CACHE_BLOCK & (CACHE_BLOCK-1))==0) ? CACHE_BLOCK : 1
)(
  input wire clk, rst_n, invalidate,
  input wire cmd_valid, output wire cmd_ready,
  input wire [1:0] cmd_op,
  input wire [31:0] cmd_layer, cmd_pos, cmd_head, cmd_dim,
  input wire cmd_phase,
  output wire done, error, output wire [31:0] read_data,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  import anvil_q2_fp_pkg::*;
  localparam NB=HEAD_DIM/CB, NW=(CB+3)/4;
  localparam IDLE=0, SCRATCH=1, WAIT_SCRATCH=2, CONVERT=3,
    NATIVE_WRITE=4, WAIT_NATIVE_WRITE=5, ENCODE=6, WAIT_ENCODE=7,
    PACK_WRITE=8, WAIT_PACK_WRITE=9, META_WRITE=10, WAIT_META_WRITE=11,
    ADVANCE=12, NATIVE_READ=13, WAIT_NATIVE_READ=14,
    META_READ=15, WAIT_META_READ=16, PACK_READ=17, WAIT_PACK_READ=18,
    DECODE=19, WAIT_DECODE=20, FINISH=21, ABORT=22, BAD_COMMAND=23;
  reg [4:0] state;
  reg failed, value_cache;
  reg [31:0] layer, position, head, dimension, block_index, offset, word_index;
  reg [31:0] committed [0:SL-1], prefill_count [0:SL-1];
  reg [SL-1:0] decoding;
  reg [31:0] source_value, result, native_pair, exponent;
  reg [CB*16-1:0] values;
  reg [NW*32-1:0] packed_bytes;
  wire [15:0] converted=narrow16(source_value,FP_FORMAT);
  wire [31:0] expanded=expand16(converted,FP_FORMAT);
  wire codec_ready, codec_valid, codec_error;
  wire [CB*16-1:0] decoded_values;
  wire [CB*8-1:0] encoded_bytes;
  wire [31:0] encoded_exponent;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  wire [31:0] block_component=block_index*CB+offset;
  wire [31:0] scratch_component=head*HEAD_DIM+
    (CACHE_MODE==0 ? dimension : block_component);
  wire [31:0] read_block=dimension >> $clog2(CB);
  integer i;

  generate if (NUM_LAYERS<=0 || NUM_KV_HEADS<=0 || HEAD_DIM<=0 ||
      HEAD_DIM%2!=0 || (128'(NUM_KV_HEADS)*HEAD_DIM)%8!=0 ||
      MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>16777215 ||
      (CACHE_MODE!=0 && CACHE_MODE!=1) || (FP_FORMAT!=0 && FP_FORMAT!=1) ||
      CACHE_BLOCK<=0 || CACHE_BLOCK>65536 ||
      (CACHE_BLOCK & (CACHE_BLOCK-1))!=0 || HEAD_DIM%CB!=0 ||
      128'(NUM_LAYERS)*MAX_SEQ_LEN*NUM_KV_HEADS*HEAD_DIM>128'd4294967295)
    begin: invalid_parameters
      initial $fatal(1,"ANVIL_Q2_FP PARAMETER ERROR: KV cache geometry");
    end
  endgenerate
  assign cmd_ready=rst_n && !invalidate && state==IDLE && idle && codec_ready;
  assign done=rst_n && !invalidate && state==FINISH;
  assign error=done && failed;
  assign read_data=rst_n ? result : 32'd0;
  anvil_q2_fp_cache_codec #(.FP_FORMAT(FP_FORMAT),.CACHE_BLOCK(CB)) codec(
    .clk(clk),.rst_n(rst_n),
    .in_valid(rst_n && !invalidate && (state==ENCODE || state==DECODE)),
    .in_ready(codec_ready),.in_decode(state==DECODE),.in_values(values),
    .in_quantized(packed_bytes[CB*8-1:0]),.in_exponent(exponent),
    .out_valid(codec_valid),.out_ready(1'b1),.out_values(decoded_values),
    .out_quantized(encoded_bytes),.out_exponent(encoded_exponent),.out_error(codec_error));
  anvil_q2_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(wr),.kind(kind),.layer(ml),
    .proj(3'd0),.row(row),.col(col),.wdata(wd),
    .idle(idle),.complete(complete),.rdata(rd),.fault(fault),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
  always @* begin
    issue=0; wr=0; kind=0; row=0; col=0; wd=0; ml=0;
    if (rst_n && !invalidate && idle) case (state)
      SCRATCH: begin
        issue=1; kind=8; row=value_cache ? 4 : 3; col=scratch_component;
      end
      NATIVE_WRITE: begin
        issue=1; wr=1; kind=value_cache ? 10 : 9; ml=layer;
        row=position; col=(head*HEAD_DIM+dimension) >> 1; wd=native_pair;
      end
      PACK_WRITE: begin
        issue=1; wr=1; kind=value_cache ? 13 : 12; ml=layer; row=position;
        col=(head*NB+block_index)*NW+word_index; wd=packed_bytes[word_index*32+:32];
      end
      META_WRITE: begin
        issue=1; wr=1; kind=value_cache ? 15 : 14; ml=layer;
        row=position; col=head*NB+block_index; wd=exponent;
      end
      NATIVE_READ: begin
        issue=1; kind=value_cache ? 10 : 9; ml=layer;
        row=position; col=(head*HEAD_DIM+dimension) >> 1;
      end
      META_READ: begin
        issue=1; kind=value_cache ? 15 : 14; ml=layer;
        row=position; col=head*NB+read_block;
      end
      PACK_READ: begin
        issue=1; kind=value_cache ? 13 : 12; ml=layer;
        row=position; col=(head*NB+read_block)*NW+word_index;
      end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; value_cache<=0; decoding<=0;
      layer<=0; position<=0; head<=0; dimension<=0; block_index<=0;
      offset<=0; word_index<=0; source_value<=0; result<=0;
      native_pair<=0; exponent<=0; values<=0; packed_bytes<=0;
      for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else if (invalidate) begin
      state<=ABORT; failed<=0; result<=0; decoding<=0;
      for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else if (fault && state!=ABORT) begin
      failed<=1; state<=FINISH; decoding<=0;
      for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else case (state)
      IDLE: if (cmd_valid && cmd_ready) begin
        failed<=0; result<=0; values<=0; packed_bytes<=0; native_pair<=0;
        offset<=0; word_index<=0; block_index<=0; dimension<=0; head<=0;
        value_cache<=cmd_op==2;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_op>2) begin
          failed<=1; state<=BAD_COMMAND;
          if (cmd_op==0) begin
            decoding<=0;
            for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
          end
        end else if (cmd_op==0) begin
          if (cmd_pos!=committed[cmd_layer] || (!cmd_phase && decoding[cmd_layer]) ||
              (cmd_phase && decoding[cmd_layer] && cmd_pos<prefill_count[cmd_layer])) begin
            failed<=1; state<=BAD_COMMAND;
            committed[cmd_layer]<=0; prefill_count[cmd_layer]<=0;
            decoding[cmd_layer]<=0;
          end else begin
            layer<=cmd_layer; position<=cmd_pos; value_cache<=0;
            if (cmd_phase && !decoding[cmd_layer]) begin
              decoding[cmd_layer]<=1; prefill_count[cmd_layer]<=committed[cmd_layer];
            end
            state<=SCRATCH;
          end
        end else if (cmd_head>=NUM_KV_HEADS || cmd_dim>=HEAD_DIM ||
                      cmd_pos>=committed[cmd_layer]) begin
          failed<=1; state<=BAD_COMMAND;
        end else begin
          layer<=cmd_layer; position<=cmd_pos; head<=cmd_head; dimension<=cmd_dim;
          if (CACHE_MODE==0) state<=NATIVE_READ; else state<=META_READ;
        end
      end
      SCRATCH: if (issue) state<=WAIT_SCRATCH;
      WAIT_SCRATCH: if (complete) begin source_value<=rd; state<=CONVERT; end
      CONVERT: begin
        if (!fp_is_finite(source_value) || !fp_is_finite(expanded)) begin
          failed<=1; committed[layer]<=0; prefill_count[layer]<=0;
          decoding[layer]<=0; state<=FINISH;
        end else if (CACHE_MODE==0) begin
          if (!dimension[0]) begin
            native_pair[15:0]<=converted; dimension<=dimension+1; state<=SCRATCH;
          end else begin native_pair[31:16]<=converted; state<=NATIVE_WRITE; end
        end else begin
          values[offset*16+:16]<=converted;
          if (offset+1<CB) begin offset<=offset+1; state<=SCRATCH; end
          else state<=ENCODE;
        end
      end
      NATIVE_WRITE: if (issue) state<=WAIT_NATIVE_WRITE;
      WAIT_NATIVE_WRITE: if (complete) begin
        if (dimension+1<HEAD_DIM) begin dimension<=dimension+1; state<=SCRATCH; end
        else state<=ADVANCE;
      end
      ENCODE: if (codec_ready) state<=WAIT_ENCODE;
      WAIT_ENCODE: if (codec_valid) begin
        if (codec_error) begin
          failed<=1; committed[layer]<=0; prefill_count[layer]<=0;
          decoding[layer]<=0; state<=FINISH;
        end else begin
          packed_bytes<={{(NW*32-CB*8){1'b0}},encoded_bytes};
          exponent<=encoded_exponent; word_index<=0; state<=PACK_WRITE;
        end
      end
      PACK_WRITE: if (issue) state<=WAIT_PACK_WRITE;
      WAIT_PACK_WRITE: if (complete) begin
        if (word_index+1<NW) begin word_index<=word_index+1; state<=PACK_WRITE; end
        else state<=META_WRITE;
      end
      META_WRITE: if (issue) state<=WAIT_META_WRITE;
      WAIT_META_WRITE: if (complete) state<=ADVANCE;
      ADVANCE: begin
        offset<=0; word_index<=0; values<=0; native_pair<=0;
        if (CACHE_MODE==1 && block_index+1<NB) begin
          block_index<=block_index+1; state<=SCRATCH;
        end else if (head+1<NUM_KV_HEADS) begin
          head<=head+1; block_index<=0; dimension<=0; state<=SCRATCH;
        end else if (!value_cache) begin
          value_cache<=1; head<=0; block_index<=0; dimension<=0; state<=SCRATCH;
        end else begin
          // Only the acknowledgement of the final V write permits visibility.
          committed[layer]<=position+1; state<=FINISH;
        end
      end
      NATIVE_READ: if (issue) state<=WAIT_NATIVE_READ;
      WAIT_NATIVE_READ: if (complete) begin
        if (!fp_is_finite(expand16(rd[15:0],FP_FORMAT)) ||
            !fp_is_finite(expand16(rd[31:16],FP_FORMAT))) begin
          failed<=1; state<=FINISH;
        end else begin
          result<=expand16(dimension[0] ? rd[31:16] : rd[15:0],FP_FORMAT);
          state<=FINISH;
        end
      end
      META_READ: if (issue) state<=WAIT_META_READ;
      WAIT_META_READ: if (complete) begin
        if (rd[31:16]!={16{rd[15]}} ||
            $signed(rd)<(FP_FORMAT==0 ? -139 : -30) ||
            $signed(rd)>(FP_FORMAT==0 ? 122 : 10)) begin
          failed<=1; state<=FINISH;
        end else begin exponent<=rd; word_index<=0; packed_bytes<=0; state<=PACK_READ; end
      end
      PACK_READ: if (issue) state<=WAIT_PACK_READ;
      WAIT_PACK_READ: if (complete) begin
        if ((CB==1 && rd[31:8]!=0) || (CB==2 && rd[31:16]!=0)) begin
          failed<=1; state<=FINISH;
        end else begin
          packed_bytes[word_index*32+:32]<=rd;
          if (word_index+1<NW) begin word_index<=word_index+1; state<=PACK_READ; end
          else state<=DECODE;
        end
      end
      DECODE: if (codec_ready) state<=WAIT_DECODE;
      WAIT_DECODE: if (codec_valid) begin
        if (codec_error) failed<=1;
        else result<=expand16(decoded_values[(dimension & (CB-1))*16+:16],FP_FORMAT);
        state<=FINISH;
      end
      BAD_COMMAND: state<=FINISH;
      FINISH: state<=IDLE;
      ABORT: if (idle && codec_ready) state<=IDLE;
      default: begin failed<=1; state<=FINISH; end
    endcase
  end
endmodule
