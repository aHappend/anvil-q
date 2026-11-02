module anvil_q3_ht_kv_hierarchy #(
  parameter NUM_LAYERS=36, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter MAX_SEQ_LEN=32768, CACHE_MODE=0, KV_RESIDENT_GROUPS=64,
  localparam SL=NUM_LAYERS>=1 ? NUM_LAYERS : 1,
  localparam RG=KV_RESIDENT_GROUPS>=1 && KV_RESIDENT_GROUPS<=256 ?
    KV_RESIDENT_GROUPS : 1,
  localparam RW=RG>1 ? $clog2(RG) : 1,
  localparam CAP=CACHE_MODE==2 ? 64 : CACHE_MODE==1 ? 32 : 16
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [1:0] cmd_op,
  input wire [31:0] cmd_epoch, cmd_layer, cmd_pos, cmd_head, cmd_dim,
  input wire cmd_phase, cmd_bypass,
  output wire done, error,
  output wire signed [31:0] read_data,
  output wire idle, drain_done, fault,
  output wire scratch_req_valid,
  input wire scratch_req_ready,
  output wire [31:0] scratch_req_slot, scratch_req_index,
  input wire scratch_rsp_valid, scratch_rsp_error,
  output wire scratch_rsp_ready,
  input wire [31:0] scratch_rsp_rdata,
  output wire memory_req_valid,
  input wire memory_req_ready,
  output wire memory_req_write,
  output wire [32:0] memory_req_address,
  output wire [511:0] memory_req_wdata,
  output wire [63:0] memory_req_byteenable,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata
);
  localparam SHIFT=$clog2(CAP);
  localparam [63:0] GROUPS=(64'(HEAD_DIM)+CAP-1)>>SHIFT;
  localparam [63:0] HEAD_BYTES=GROUPS<<6;
  localparam [63:0] KV_BYTES=64'(NUM_LAYERS)*2*64'(MAX_SEQ_LEN)*
    64'(NUM_KV_HEADS)*HEAD_BYTES;
  localparam LEGAL=NUM_LAYERS==SL && NUM_KV_HEADS>0 && HEAD_DIM>0 &&
    (HEAD_DIM&1)==0 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    CACHE_MODE>=0 && CACHE_MODE<=2 && KV_RESIDENT_GROUPS==RG &&
    KV_BYTES<=64'h100000000 && GROUPS<=64'hffffffff &&
    64'(NUM_KV_HEADS)*64'(HEAD_DIM)<=64'hffffffff;
  localparam IDLE=0, ADDRESS_POSITION=1, ADDRESS_HEAD=2, ADDRESS_RECORD=3;
  localparam ADDRESS_CHECK=4, SCRATCH_REQUEST=5, SCRATCH_RESPONSE=6;
  localparam ENCODE_START=7, ENCODE_WAIT=8, MEMORY_START=9, MEMORY_WAIT=10;
  localparam LOOKUP_READ=11, LOOKUP_COMPARE=12, DECODE_START=13, DECODE_WAIT=14;
  localparam INSTALL=15, ADVANCE=16, COMPLETE=17, ABORT=18, FAULTED=19;
  reg [4:0] state;
  reg failed, reading, value_cache, phase, bypass, missed;
  reg [31:0] epoch, layer, position, head, group_index, selected_lane;
  reg [6:0] length, lane;
  reg [31:0] group_start;
  reg [63:0] position_index, head_index, record_address;
  reg [CAP*32-1:0] source_values;
  reg [511:0] record;
  reg signed [31:0] result;
  reg [31:0] committed [0:SL-1], prefill_count [0:SL-1], layer_epoch [0:SL-1];
  reg [SL-1:0] decoding;
  reg [RG-1:0] cache_valid;
  reg [RW-1:0] lookup_index, replacement;
  (* ramstyle="M20K", nomem2reg *) reg [64:0] tags [0:RG-1];
  (* ramstyle="M20K", nomem2reg *) reg [511:0] records [0:RG-1];
  reg [64:0] lookup_tag;
  reg [511:0] lookup_record;
  reg lookup_valid;
  wire [64:0] wanted_tag={epoch,record_address[32:0]};
  wire running=rst_n && LEGAL && !flush;
  wire cache_hit=lookup_valid && lookup_tag==wanted_tag;
  wire install=running && !failed && state==INSTALL && !bypass && (!reading || missed);
  wire lookup=running && !failed && state==LOOKUP_READ;
  wire codec_ready, codec_valid, codec_error;
  wire [CAP*32-1:0] codec_values;
  wire [511:0] codec_record;
  wire codec_flush=flush || state==ABORT;
  wire [31:0] safe_cmd_layer=cmd_layer<SL ? cmd_layer : 32'd0;
  wire [31:0] safe_layer=layer<SL ? layer : 32'd0;
  wire bad_command=cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_op>2 ||
    (cmd_op==0 ?
      (cmd_pos!=committed[safe_cmd_layer] ||
       (committed[safe_cmd_layer]!=0 && cmd_epoch!=layer_epoch[safe_cmd_layer]) ||
       (decoding[safe_cmd_layer] && !cmd_phase) ||
       (decoding[safe_cmd_layer] && cmd_pos<prefill_count[safe_cmd_layer])) :
      (cmd_head>=NUM_KV_HEADS || cmd_dim>=HEAD_DIM ||
       cmd_pos>=committed[safe_cmd_layer] || cmd_epoch!=layer_epoch[safe_cmd_layer]));

  wire [511:0] response_data;
  wire memory_complete, memory_error, transport_failed, memory_ready, memory_drained;
  wire memory_start=running && !failed && state==MEMORY_START;
  wire memory_fault=transport_failed || (state==MEMORY_WAIT && memory_complete && memory_error);
  wire scratch_fault=state==SCRATCH_RESPONSE && scratch_rsp_valid && scratch_rsp_error;
  wire numerical_fault=(state==ENCODE_WAIT || state==DECODE_WAIT) &&
    codec_valid && codec_error;
  integer i;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: KV geometry, mode, residency or backing extent");
  end endgenerate
  assign cmd_ready=running && !failed && state==IDLE && memory_ready;
  assign done=running && state==COMPLETE;
  assign error=done && failed;
  assign read_data=done && !failed && reading ? result : 32'sd0;
  assign drain_done=memory_drained;
  assign idle=running && !failed && state==IDLE && memory_ready;
  assign fault=rst_n && (failed || transport_failed);
  assign scratch_req_valid=running && !failed && state==SCRATCH_REQUEST;
  assign scratch_req_slot=scratch_req_valid ? (value_cache ? 32'd4 : 32'd3) : 32'd0;
  assign scratch_req_index=scratch_req_valid ?
    head*32'(HEAD_DIM)+group_start+{25'd0,lane} : 32'd0;
  assign scratch_rsp_ready=running && state==SCRATCH_RESPONSE;

  anvil_q3_ht_ddr_record_port record_port (
    .clk(clk),.rst_n(rst_n),.flush(flush || state==ABORT),
    .in_valid(memory_start),.in_ready(memory_ready),.in_write(!reading),
    .in_address(record_address[32:0]),.in_wdata(record),
    .in_byteenable(64'hffffffffffffffff),
    .out_valid(memory_complete),.out_ready(1'b1),
    .out_error(memory_error),.out_rdata(response_data),
    .idle(),.drain_done(memory_drained),.fault(transport_failed),
    .memory_req_valid(memory_req_valid),.memory_req_ready(memory_req_ready),
    .memory_req_write(memory_req_write),.memory_req_address(memory_req_address),
    .memory_req_wdata(memory_req_wdata),.memory_req_byteenable(memory_req_byteenable),
    .memory_rsp_valid(memory_rsp_valid),.memory_rsp_error(memory_rsp_error),
    .memory_rsp_rdata(memory_rsp_rdata)
  );

  anvil_q3_ht_kv_codec #(.CACHE_MODE(CACHE_MODE)) codec (
    .clk(clk),.rst_n(rst_n),.flush(codec_flush),
    .in_valid(running && !failed && (state==ENCODE_START || state==DECODE_START)),
    .in_ready(codec_ready),.decode(state==DECODE_START),.count(length),
    .values_in(source_values),.record_in(record),
    .out_valid(codec_valid),.out_ready(1'b1),.out_error(codec_error),
    .values_out(codec_values),.record_out(codec_record)
  );

  always @(posedge clk) begin
    if (lookup) begin
      lookup_tag<=tags[lookup_index];
      lookup_record<=records[lookup_index];
      lookup_valid<=cache_valid[lookup_index];
    end
    if (install) begin
      tags[replacement]<=wanted_tag;
      records[replacement]<=record;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; reading<=0; value_cache<=0;
      phase<=0; bypass<=0; missed<=0;
      epoch<=0; layer<=0; position<=0; head<=0; group_index<=0; selected_lane<=0;
      length<=0; lane<=0; group_start<=0;
      position_index<=0; head_index<=0; record_address<=0;
      source_values<=0; record<=0; result<=0;
      decoding<=0; cache_valid<=0; lookup_index<=0; replacement<=0;
      for (i=0;i<SL;i=i+1) begin
        committed[i]<=0; prefill_count[i]<=0; layer_epoch[i]<=0;
      end
    end else if (flush) begin
      state<=ABORT; failed<=0; decoding<=0; cache_valid<=0;
      lookup_index<=0; replacement<=0; result<=0;
      for (i=0;i<SL;i=i+1) begin
        committed[i]<=0; prefill_count[i]<=0; layer_epoch[i]<=0;
      end
    end else if (state!=ABORT && !failed &&
        (memory_fault || scratch_fault || numerical_fault)) begin
      failed<=1; state<=COMPLETE; decoding<=0; cache_valid<=0;
      for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
    end else case (state)
      IDLE: if (cmd_valid && cmd_ready) begin
        failed<=0; reading<=cmd_op!=0; value_cache<=cmd_op==2;
        phase<=cmd_phase; bypass<=cmd_bypass; missed<=0;
        epoch<=cmd_epoch; layer<=cmd_layer; position<=cmd_pos;
        head<=cmd_op==0 ? 32'd0 : cmd_head;
        group_index<=cmd_op==0 ? 32'd0 : cmd_dim>>SHIFT;
        group_start<=cmd_op==0 ? 32'd0 : (cmd_dim>>SHIFT)<<SHIFT;
        selected_lane<=cmd_dim&32'(CAP-1);
        lane<=0; source_values<=0; record<=0; result<=0;
        length<=cmd_op==0 ? 7'(HEAD_DIM<CAP ? HEAD_DIM : CAP) :
          7'(HEAD_DIM-((cmd_dim>>SHIFT)<<SHIFT)<CAP ?
             HEAD_DIM-((cmd_dim>>SHIFT)<<SHIFT) : CAP);
        if (bad_command) begin failed<=1; state<=COMPLETE; end
        else begin
          if (cmd_op==0) begin
            layer_epoch[safe_cmd_layer]<=cmd_epoch;
            if (cmd_phase && !decoding[safe_cmd_layer]) begin
              decoding[safe_cmd_layer]<=1;
              prefill_count[safe_cmd_layer]<=committed[safe_cmd_layer];
            end
          end
          state<=ADDRESS_POSITION;
        end
      end
      ADDRESS_POSITION: begin
        position_index<=(64'(layer)*2+(value_cache ? 1 : 0))*
          64'(MAX_SEQ_LEN)+64'(position);
        state<=ADDRESS_HEAD;
      end
      ADDRESS_HEAD: begin
        head_index<=position_index*64'(NUM_KV_HEADS)+64'(head);
        state<=ADDRESS_RECORD;
      end
      ADDRESS_RECORD: begin
        record_address<=64'h100000000+head_index*HEAD_BYTES+(64'(group_index)<<6);
        state<=ADDRESS_CHECK;
      end
      ADDRESS_CHECK: begin
        if (record_address<64'h100000000 || record_address+64>64'h200000000 ||
            record_address[5:0]!=0 || group_index>=GROUPS) begin
          failed<=1; state<=COMPLETE;
        end else if (!reading) state<=SCRATCH_REQUEST;
        else if (bypass) begin missed<=1; state<=MEMORY_START; end
        else begin lookup_index<=0; state<=LOOKUP_READ; end
      end
      SCRATCH_REQUEST: if (scratch_req_ready) state<=SCRATCH_RESPONSE;
      SCRATCH_RESPONSE: if (scratch_rsp_valid) begin
        source_values[lane*32+:32]<=scratch_rsp_rdata;
        if (lane+1==length) begin lane<=0; state<=ENCODE_START; end
        else begin lane<=lane+1'b1; state<=SCRATCH_REQUEST; end
      end
      ENCODE_START: if (codec_ready) state<=ENCODE_WAIT;
      ENCODE_WAIT: if (codec_valid) begin record<=codec_record; state<=MEMORY_START; end
      MEMORY_START: if (memory_ready) state<=MEMORY_WAIT;
      MEMORY_WAIT: if (memory_complete) begin
        if (reading) begin record<=response_data; state<=DECODE_START; end
        else state<=INSTALL;
      end
      LOOKUP_READ: state<=LOOKUP_COMPARE;
      LOOKUP_COMPARE: begin
        if (cache_hit) begin
          record<=lookup_record; missed<=0; state<=DECODE_START;
        end else if (lookup_index==RG-1) begin missed<=1; state<=MEMORY_START; end
        else begin lookup_index<=lookup_index+1'b1; state<=LOOKUP_READ; end
      end
      DECODE_START: if (codec_ready) state<=DECODE_WAIT;
      DECODE_WAIT: if (codec_valid) begin
        result<=codec_values[selected_lane*32+:32];
        state<=INSTALL;
      end
      INSTALL: begin
        if (install) begin
          cache_valid[replacement]<=1;
          replacement<=replacement==RG-1 ? 0 : replacement+1'b1;
        end
        if (reading) state<=COMPLETE;
        else state<=ADVANCE;
      end
      ADVANCE: begin
        source_values<=0; record<=0; lane<=0;
        if (group_index+1<GROUPS) begin
          group_index<=group_index+1'b1;
          group_start<=group_start+CAP;
          length<=7'(HEAD_DIM-(group_start+CAP)<CAP ?
            HEAD_DIM-(group_start+CAP) : CAP);
          state<=ADDRESS_POSITION;
        end else begin
          group_index<=0; group_start<=0;
          length<=7'(HEAD_DIM<CAP ? HEAD_DIM : CAP);
          if (head+1<NUM_KV_HEADS) begin head<=head+1'b1; state<=ADDRESS_POSITION; end
          else if (!value_cache) begin head<=0; value_cache<=1; state<=ADDRESS_POSITION; end
          else begin committed[safe_layer]<=position+1'b1; state<=COMPLETE; end
        end
      end
      COMPLETE: begin
        if (failed) begin
          decoding<=0; cache_valid<=0;
          for (i=0;i<SL;i=i+1) begin committed[i]<=0; prefill_count[i]<=0; end
          state<=FAULTED;
        end else state<=IDLE;
      end
      ABORT: if (memory_drained && !transport_failed) state<=IDLE;
      FAULTED: state<=FAULTED;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
