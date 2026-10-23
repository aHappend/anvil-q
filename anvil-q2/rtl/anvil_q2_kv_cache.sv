module anvil_q2_kv_cache #(
  parameter NUM_LAYERS=28, NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768,
  CACHE_MODE=0, CACHE_BLOCK=16,
  SL=(NUM_LAYERS>0 && MAX_SEQ_LEN>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 &&
      128'(NUM_LAYERS)*MAX_SEQ_LEN*NUM_KV_HEADS*HEAD_DIM<=128'd4294967295) ?
      NUM_LAYERS : 1,
  CB=(CACHE_BLOCK>0 && CACHE_BLOCK<=HEAD_DIM &&
      (CACHE_BLOCK & (CACHE_BLOCK-1))==0) ? CACHE_BLOCK : 1
)(
  input wire clk, rst_n, invalidate,
  input wire cmd_valid, output wire cmd_ready,
  input wire [1:0] cmd_op,
  input wire [31:0] cmd_layer, cmd_pos, cmd_head, cmd_dim,
  input wire cmd_phase,
  output wire done, error,
  output wire signed [31:0] read_data,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  localparam NB=HEAD_DIM/CB, NW=(CB+3)/4;
  localparam IDLE=0, SCRATCH_REQ=1, SCRATCH_WAIT=2, BYPASS_REQ=3, BYPASS_WAIT=4,
    ENCODE=5, PACK_REQ=6, PACK_WAIT=7, EXP_WRITE_REQ=8, EXP_WRITE_WAIT=9,
    ADVANCE=10, LOSS_REQ=11, LOSS_WAIT=12, EXP_READ_REQ=13, EXP_READ_WAIT=14,
    BYTE_REQ=15, BYTE_WAIT=16, DECODE=17, FINISH=18, ENCODE_EXP=19;
  reg [4:0] state;
  reg failed, value_cache, phase;
  reg [31:0] layer, position, head, dimension, block_index, within_block, word_index;
  reg [31:0] committed [0:SL-1], prefill_count [0:SL-1];
  reg [SL-1:0] decoding;
  reg signed [31:0] value, result;
  reg [CB*32-1:0] values;
  wire [CB*8-1:0] encoded_bytes;
  wire [7:0] encoded_exponent;
  reg [NW*32-1:0] packed_bytes;
  reg [7:0] exponent, byte_value;
  wire signed [31:0] decoded_value;
  wire invalid_exponent;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  reg [63:0] resolved_position, resolved_component;
  integer i;

  generate if(NUM_LAYERS<=0 || NUM_KV_HEADS<=0 || HEAD_DIM<=0 ||
      MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>16777215 ||
      (CACHE_MODE!=0 && CACHE_MODE!=1) || CACHE_BLOCK<=0 ||
      (CACHE_BLOCK & (CACHE_BLOCK-1))!=0 || CACHE_BLOCK>HEAD_DIM ||
      HEAD_DIM%CB!=0 ||
      128'(NUM_LAYERS)*MAX_SEQ_LEN*NUM_KV_HEADS*HEAD_DIM>128'd4294967295)
    begin: invalid_parameters
      initial $fatal(1,"ANVIL_Q2 PARAMETER ERROR: KV cache geometry");
    end
  endgenerate
  anvil_q2_cache_codec #(CACHE_BLOCK,CB,1) codec(
    .block_values(values),.block_bytes(encoded_bytes),.block_exponent(encoded_exponent),
    .read_byte(byte_value),.read_exponent(exponent),
    .read_value(decoded_value),.invalid_exponent(invalid_exponent));
  assign cmd_ready=rst_n && !invalidate && state==IDLE;
  assign done=rst_n && !invalidate && state==FINISH;
  assign error=done && failed;
  assign read_data=rst_n ? result : 0;
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
    // Factor the token-major coordinate using the already bounded head and dimension.
    resolved_position=phase ? {32'd0,position} : {32'd0,committed[layer]};
    resolved_component={32'd0,head}*HEAD_DIM+block_index*CB+within_block;
  end
  always @* begin
    issue=0; wr=0; kind=0; row=0; col=0; wd=0; ml=0;
    if(rst_n && !invalidate && idle) case(state)
      SCRATCH_REQ: begin
        issue=1; kind=8; row=value_cache ? 4 : 3;
        col=head*HEAD_DIM+block_index*CB+within_block;
      end
      BYPASS_REQ: begin
        issue=1; wr=1; kind=value_cache ? 10 : 9; ml=layer;
        row=resolved_position[31:0]; col=resolved_component[31:0]; wd=value;
      end
      PACK_REQ: begin
        issue=1; wr=1; kind=value_cache ? 13 : 12; ml=layer;
        row=resolved_position[31:0]; col=(head*NB+block_index)*NW+word_index;
        wd=packed_bytes[word_index*32+:32];
      end
      EXP_WRITE_REQ: begin
        issue=1; wr=1; kind=value_cache ? 15 : 14; ml=layer;
        row=resolved_position[31:0]; col=head*NB+block_index; wd={24'd0,exponent};
      end
      LOSS_REQ: begin
        issue=1; kind=value_cache ? 10 : 9; ml=layer;
        row=position; col=head*HEAD_DIM+dimension;
      end
      EXP_READ_REQ: begin
        issue=1; kind=value_cache ? 15 : 14; ml=layer;
        row=position; col=head*NB+(dimension >> $clog2(CB));
      end
      BYTE_REQ: begin
        issue=1; kind=value_cache ? 13 : 12; ml=layer;
        row=position; col=(head*NB+(dimension >> $clog2(CB)))*NW+
                           ((dimension & (CB-1)) >> 2);
      end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=IDLE; failed<=0; value_cache<=0; phase<=0; decoding<=0;
      layer<=0; position<=0; head<=0; dimension<=0; block_index<=0;
      within_block<=0; word_index<=0; value<=0; result<=0; values<=0;
      packed_bytes<=0; exponent<=0; byte_value<=0;
      for(i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else if(invalidate) begin
      state<=IDLE; failed<=0; result<=0; decoding<=0;
      for(i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else if(fault) begin
      failed<=1; state<=FINISH;
      for(i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
      decoding<=0;
    end else case(state)
      IDLE: if(cmd_valid) begin
        failed<=0; result<=0; values<=0; packed_bytes<=0;
        head<=0; dimension<=0; block_index<=0; within_block<=0; word_index<=0;
        value_cache<=cmd_op==2; phase<=cmd_phase;
        if(cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_op>2) begin
          failed<=1; state<=FINISH;
        end else if(cmd_op==0) begin
          if(cmd_pos!=committed[cmd_layer] || (!cmd_phase && decoding[cmd_layer]) ||
             (cmd_phase && decoding[cmd_layer] && cmd_pos<prefill_count[cmd_layer])) begin
            failed<=1; state<=FINISH;
          end else begin
            layer<=cmd_layer; position<=cmd_pos; value_cache<=0;
            if(cmd_phase && !decoding[cmd_layer]) begin
              decoding[cmd_layer]<=1;
              prefill_count[cmd_layer]<=committed[cmd_layer];
            end
            state<=SCRATCH_REQ;
          end
        end else if(cmd_head>=NUM_KV_HEADS || cmd_dim>=HEAD_DIM ||
                    cmd_pos>=committed[cmd_layer]) begin
          failed<=1; state<=FINISH;
        end else begin
          layer<=cmd_layer; position<=cmd_pos; head<=cmd_head; dimension<=cmd_dim;
          if(CACHE_MODE==0) state<=LOSS_REQ; else state<=EXP_READ_REQ;
        end
      end
      SCRATCH_REQ: if(issue) state<=SCRATCH_WAIT;
      SCRATCH_WAIT: if(complete) begin
        value<=rd;
        values[within_block*32+:32]<=rd;
        if(CACHE_MODE==0) state<=BYPASS_REQ;
        else if(within_block+1<CB) begin
          within_block<=within_block+1; state<=SCRATCH_REQ;
        end else state<=ENCODE_EXP;
      end
      BYPASS_REQ: if(issue) state<=BYPASS_WAIT;
      BYPASS_WAIT: if(complete) begin
        if(within_block+1<CB) begin within_block<=within_block+1; state<=SCRATCH_REQ; end
        else state<=ADVANCE;
      end
      ENCODE_EXP: begin
        exponent<=encoded_exponent; state<=ENCODE;
      end
      ENCODE: begin
        packed_bytes<={{(NW*32-CB*8){1'b0}},encoded_bytes};
        word_index<=0; state<=PACK_REQ;
      end
      PACK_REQ: if(issue) state<=PACK_WAIT;
      PACK_WAIT: if(complete) begin
        if(word_index+1<NW) begin word_index<=word_index+1; state<=PACK_REQ; end
        else state<=EXP_WRITE_REQ;
      end
      EXP_WRITE_REQ: if(issue) state<=EXP_WRITE_WAIT;
      EXP_WRITE_WAIT: if(complete) state<=ADVANCE;
      ADVANCE: begin
        within_block<=0; word_index<=0; values<=0;
        if(block_index+1<NB) begin block_index<=block_index+1; state<=SCRATCH_REQ; end
        else if(head+1<NUM_KV_HEADS) begin
          head<=head+1; block_index<=0; state<=SCRATCH_REQ;
        end else if(!value_cache) begin
          value_cache<=1; head<=0; block_index<=0; state<=SCRATCH_REQ;
        end else begin committed[layer]<=position+1; state<=FINISH; end
      end
      LOSS_REQ: if(issue) state<=LOSS_WAIT;
      LOSS_WAIT: if(complete) begin result<=rd; state<=FINISH; end
      EXP_READ_REQ: if(issue) state<=EXP_READ_WAIT;
      EXP_READ_WAIT: if(complete) begin
        if(rd>25) begin failed<=1; state<=FINISH; end
        else begin exponent<=rd[7:0]; state<=BYTE_REQ; end
      end
      BYTE_REQ: if(issue) state<=BYTE_WAIT;
      BYTE_WAIT: if(complete) begin
        byte_value<=rd[((dimension & (CB-1)) & 3)*8+:8]; state<=DECODE;
      end
      DECODE: begin
        if(invalid_exponent || byte_value==8'h80) failed<=1;
        else result<=decoded_value;
        state<=FINISH;
      end
      FINISH: state<=IDLE;
      default: begin failed<=1; state<=FINISH; end
    endcase
  end
endmodule
