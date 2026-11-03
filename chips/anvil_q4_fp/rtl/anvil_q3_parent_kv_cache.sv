module anvil_q3_parent_kv_cache (
  input wire clk, rst_n, flush, cmd_valid,
  input wire invalidate,
  input wire [31:0] PROFILE, NUM_LAYERS, NUM_KV_HEADS, HEAD_DIM,
  input wire [31:0] MAX_SEQ_LEN, CACHE_MODE, CACHE_BLOCK,
  input wire INT4_ASYM,
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
  localparam SL=64, STORAGE=256;
  wire [31:0] CAP=CACHE_MODE==0 ? 32'd1 : CACHE_BLOCK;
  wire [31:0] BITS=CACHE_MODE==0 ? 32'd32 : CACHE_MODE==1 ? 32'd8 : 32'd4;
  reg [3:0] SHIFT;
  always @* begin
    case (CAP)
      2: SHIFT=1;
      4: SHIFT=2;
      8: SHIFT=3;
      16: SHIFT=4;
      32: SHIFT=5;
      64: SHIFT=6;
      128: SHIFT=7;
      256: SHIFT=8;
      default: SHIFT=0;
    endcase
  end
  wire [31:0] BLOCKS=(HEAD_DIM+CAP-1)>>SHIFT;
  wire [31:0] WORDS=(CAP*BITS+31)>>5;
  localparam IDLE=0, SCRATCH_READ=1, SCRATCH_RESPONSE=2, ENCODE=3, ENCODE_WAIT=4;
  localparam PAYLOAD_WRITE=5, PAYLOAD_ACK=6, METADATA_WRITE=7, METADATA_ACK=8;
  localparam ADVANCE=9, METADATA_READ=10, METADATA_RESPONSE=11;
  localparam PAYLOAD_READ=12, PAYLOAD_RESPONSE=13, DECODE=14, DECODE_WAIT=15;
  localparam COMPLETE=16, FAULTED=17;
  reg [4:0] state;
  reg failed, value_cache, reading;
  reg [31:0] layer, position, head, head_base, block_base, block_start;
  reg [31:0] block_index, lane, word_index, length, selected_lane;
  reg [31:0] committed [0:SL-1], prefill_count [0:SL-1];
  reg [SL-1:0] decoding;
  reg [STORAGE*32-1:0] values, payload;
  reg [31:0] metadata;
  reg signed [31:0] result;
  wire unit_flush=flush || failed;
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==SCRATCH_READ || state==PAYLOAD_WRITE ||
    state==METADATA_WRITE || state==METADATA_READ || state==PAYLOAD_READ);
  wire payload_access=state==PAYLOAD_WRITE || state==PAYLOAD_READ;
  wire metadata_access=state==METADATA_WRITE || state==METADATA_READ;
  wire codec_ready, codec_done, codec_error;
  wire [STORAGE*32-1:0] decoded, encoded;
  wire [31:0] encoded_metadata;
  wire [31:0] payload_tree [1:511];
  wire [31:0] decoded_tree [1:511];
  wire [31:0] selected_payload=word_index<STORAGE ? payload_tree[1] : 32'bx;
  wire [31:0] selected_decoded=selected_lane<STORAGE ? decoded_tree[1] : 32'bx;
  integer i;

  generate
    for (genvar w=0;w<STORAGE;w=w+1) begin: workspace_word
      assign payload_tree[STORAGE+w]=payload[w*32+:32];
      assign decoded_tree[STORAGE+w]=decoded[w*32+:32];
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          values[w*32+:32]<=0;
          payload[w*32+:32]<=0;
        end else if (!invalidate && !flush &&
            !(!failed && (fault || (codec_done && codec_error)))) begin
          if ((state==IDLE && cmd_valid) || state==ADVANCE) begin
            values[w*32+:32]<=0;
            payload[w*32+:32]<=0;
          end else begin
            if (state==SCRATCH_RESPONSE && complete && lane==w)
              values[w*32+:32]<=rdata;
            if (state==ENCODE_WAIT && codec_done)
              payload[w*32+:32]<=encoded[w*32+:32];
            else if (state==PAYLOAD_RESPONSE && complete && word_index==w)
              payload[w*32+:32]<=rdata;
          end
        end
      end
    end
    for (genvar level=0;level<8;level=level+1) begin: select_level
      for (genvar node=(1<<level);node<(1<<(level+1));node=node+1) begin: select_node
        assign payload_tree[node]=word_index[7-level] ?
          payload_tree[node*2+1] : payload_tree[node*2];
        assign decoded_tree[node]=selected_lane[7-level] ?
          decoded_tree[node*2+1] : decoded_tree[node*2];
      end
    end
  endgenerate

  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  assign read_data=rst_n && !flush && !failed ? result : 32'sd0;

  anvil_q3_parent_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(state==PAYLOAD_WRITE || state==METADATA_WRITE),
    .kind(state==SCRATCH_READ ? 4'd8 : CACHE_MODE==0 ? (value_cache ? 4'd10 : 4'd9) :
      metadata_access ? (value_cache ? 4'd15 : 4'd14) : (value_cache ? 4'd13 : 4'd12)),
    .layer(state==SCRATCH_READ ? 32'd0 : layer),.proj(3'd0),
    .row(state==SCRATCH_READ ? (value_cache ? 32'd4 : 32'd3) : position),
    .col(state==SCRATCH_READ ? head_base+block_start+lane :
      CACHE_MODE==0 ? head_base+block_start :
      payload_access ? (block_base+block_index)*32'(WORDS)+word_index : block_base+block_index),
    .wdata(state==METADATA_WRITE ? metadata :
      state==PAYLOAD_WRITE ? selected_payload : 32'd0),
    .rdata(rdata),.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q3_parent_cache_codec cache_codec (
    .PROFILE(PROFILE),.CACHE_MODE(CACHE_MODE),.INT4_ASYM(INT4_ASYM),.CACHE_BLOCK(CACHE_BLOCK),
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .start(state==ENCODE || state==DECODE),.ready(codec_ready),
    .done(codec_done),.error(codec_error),.decode(reading),.count(length),
    .values_in(values),.payload_in(payload),.metadata_in(metadata),
    .values_out(decoded),.payload_out(encoded),.metadata_out(encoded_metadata)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; value_cache<=0; reading<=0;
      layer<=0; position<=0; head<=0; head_base<=0; block_base<=0; block_start<=0;
      block_index<=0; lane<=0; word_index<=0; length<=0; selected_lane<=0;
      decoding<=0; metadata<=0; result<=0;
      for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else if (invalidate) begin
      state<=IDLE; failed<=0; decoding<=0; result<=0;
      for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else if (flush) begin
      state<=IDLE; failed<=0; result<=0;
    end else if (!failed && (fault || (codec_done && codec_error))) begin
      failed<=1; state<=COMPLETE; decoding<=0;
      for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else begin
      if (failed) begin
        decoding<=0;
        for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
      end
      case (state)
        IDLE: if (cmd_valid) begin
          failed<=0; result<=0; layer<=cmd_layer; position<=cmd_pos;
          head<=0; head_base<=0; block_base<=0; block_start<=0; block_index<=0;
          lane<=0; word_index<=0; metadata<=0; selected_lane<=0;
          length<=HEAD_DIM<CAP ? HEAD_DIM : CAP;
          value_cache<=cmd_op==2; reading<=cmd_op!=0;
          if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_op>2) begin
            failed<=1; state<=COMPLETE;
          end else if (cmd_op==0) begin
            if (cmd_pos!=committed[cmd_layer] ||
                (PROFILE!=1 && decoding[cmd_layer] && !cmd_phase) ||
                (PROFILE!=1 && decoding[cmd_layer] && cmd_pos<prefill_count[cmd_layer])) begin
              failed<=1; state<=COMPLETE;
            end else begin
              if (PROFILE!=1 && cmd_phase && !decoding[cmd_layer]) begin
                decoding[cmd_layer]<=1; prefill_count[cmd_layer]<=committed[cmd_layer];
              end
              value_cache<=0;
              state<=SCRATCH_READ;
            end
          end else if (cmd_head>=NUM_KV_HEADS || cmd_dim>=HEAD_DIM ||
              cmd_pos>=committed[cmd_layer]) begin
            failed<=1; state<=COMPLETE;
          end else begin
            head<=cmd_head; head_base<=cmd_head*HEAD_DIM;
            block_base<=cmd_head*32'(BLOCKS);
            block_index<=cmd_dim>>SHIFT;
            block_start<=(cmd_dim>>SHIFT)<<SHIFT;
            selected_lane<=cmd_dim&32'(CAP-1);
            length<=HEAD_DIM-((cmd_dim>>SHIFT)<<SHIFT)<CAP ?
              HEAD_DIM-((cmd_dim>>SHIFT)<<SHIFT) : CAP;
            if (CACHE_MODE==0) state<=PAYLOAD_READ; else state<=METADATA_READ;
          end
        end
        SCRATCH_READ: if (issue) state<=SCRATCH_RESPONSE;
        SCRATCH_RESPONSE: if (complete) begin
          if (lane+1<length) begin lane<=lane+1'b1; state<=SCRATCH_READ; end
          else state<=ENCODE;
        end
        ENCODE: if (codec_ready) state<=ENCODE_WAIT;
        ENCODE_WAIT: if (codec_done) begin
          metadata<=encoded_metadata; word_index<=0;
          state<=PAYLOAD_WRITE;
        end
        PAYLOAD_WRITE: if (issue) state<=PAYLOAD_ACK;
        PAYLOAD_ACK: if (complete) begin
          if (word_index+1<WORDS) begin word_index<=word_index+1'b1; state<=PAYLOAD_WRITE; end
          else if (CACHE_MODE==0) state<=ADVANCE;
          else state<=METADATA_WRITE;
        end
        METADATA_WRITE: if (issue) state<=METADATA_ACK;
        METADATA_ACK: if (complete) state<=ADVANCE;
        ADVANCE: begin
          lane<=0; word_index<=0; metadata<=0;
          if (block_index+1<BLOCKS) begin
            block_index<=block_index+1'b1; block_start<=block_start+CAP;
            length<=HEAD_DIM-(block_start+CAP)<CAP ? HEAD_DIM-(block_start+CAP) : CAP;
            state<=SCRATCH_READ;
          end else if (head+1<NUM_KV_HEADS) begin
            head<=head+1'b1; head_base<=head_base+HEAD_DIM; block_base<=block_base+32'(BLOCKS);
            block_index<=0; block_start<=0; length<=HEAD_DIM<CAP ? HEAD_DIM : CAP;
            state<=SCRATCH_READ;
          end else if (!value_cache) begin
            value_cache<=1; head<=0; head_base<=0; block_base<=0; block_index<=0; block_start<=0;
            length<=HEAD_DIM<CAP ? HEAD_DIM : CAP;
            state<=SCRATCH_READ;
          end else begin committed[layer]<=position+1'b1; state<=COMPLETE; end
        end
        METADATA_READ: if (issue) state<=METADATA_RESPONSE;
        METADATA_RESPONSE: if (complete) begin metadata<=rdata; state<=PAYLOAD_READ; end
        PAYLOAD_READ: if (issue) state<=PAYLOAD_RESPONSE;
        PAYLOAD_RESPONSE: if (complete) begin
          if (word_index+1<WORDS) begin word_index<=word_index+1'b1; state<=PAYLOAD_READ; end
          else state<=DECODE;
        end
        DECODE: if (codec_ready) state<=DECODE_WAIT;
        DECODE_WAIT: if (codec_done) begin result<=selected_decoded; state<=COMPLETE; end
        COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
        FAULTED: state<=FAULTED;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
