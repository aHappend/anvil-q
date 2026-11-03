module anvil_q3_ht2_kv_read_port #(
  parameter NUM_LAYERS=36, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter MAX_SEQ_LEN=32768, CACHE_MODE=1, KV_RESIDENT_GROUPS=64
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_id, cmd_epoch, cmd_layer, cmd_pos, cmd_head, cmd_dim,
  input wire cmd_value,
  input wire [31:0] cmd_prefix_count,
  input wire [3:0] cmd_visibility,
  input wire [127:0] cmd_positions,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire signed [31:0] out_data,
  output wire idle, fault, drain_done,
  output wire memory_req_valid,
  input wire memory_req_ready,
  output wire [32:0] memory_req_address,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata
);
  localparam CAP=CACHE_MODE==2 ? 64 : 32;
  localparam SHIFT=$clog2(CAP);
  localparam [127:0] GW=(128'(HEAD_DIM)+CAP-1)>>SHIFT;
  localparam [127:0] TBW=128'(NUM_LAYERS)*2*128'(NUM_KV_HEADS)*GW*64;
  localparam [127:0] EXTENT=TBW*(128'(MAX_SEQ_LEN)+4);
  localparam [63:0] GROUPS=GW[63:0], TOKEN_BYTES=TBW[63:0];
  localparam [63:0] COMMITTED_BYTES=TOKEN_BYTES*64'(MAX_SEQ_LEN);
  localparam RG=KV_RESIDENT_GROUPS>=1 && KV_RESIDENT_GROUPS<=256 ? KV_RESIDENT_GROUPS : 1;
  localparam RW=RG>1 ? $clog2(RG) : 1;
  localparam LEGAL=NUM_LAYERS>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 &&
    (HEAD_DIM&1)==0 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    (CACHE_MODE==1 || CACHE_MODE==2) && KV_RESIDENT_GROUPS==RG &&
    EXTENT<=128'h100000000 && (TBW>>6)<=128'hffffffff;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: KV reader geometry or residency");
    assign cmd_ready=0;
    assign out_valid=0;
    assign out_error=0;
    assign out_data=0;
    assign idle=0;
    assign fault=0;
    assign drain_done=0;
    assign memory_req_valid=0;
    assign memory_req_address=0;
  end else begin: datapath
    localparam IDLE=0, LAYER_VALUE=1, POSITION_PRODUCT=2, POSITION_ADD=3,
      HEAD_PRODUCT=4, HEAD_ADD=5, GROUP_PRODUCT=6, GROUP_ADD=7,
      SHADOW_PRODUCT=8, ORIGIN=9, ORIGIN_ADD=10, ADDRESS=11, CHECK=12,
      LOOKUP_READ=13, LOOKUP_COMPARE=14, REQUEST=15, WAIT_RETURN=16,
      DECODE_START=17, DECODE_WAIT=18, INSTALL=19, RESPONSE=20,
      DRAIN=21, FAULTED=22;
    reg [4:0] state;
    reg failed, cancelled, outstanding, private_record, missed;
    reg [31:0] transaction_id, epoch, layer, position, head, group_index;
    reg value_cache;
    reg [1:0] node;
    reg [5:0] lane;
    reg [6:0] length;
    reg [63:0] layer_value, position_product, position_index;
    reg [63:0] head_product, head_index, group_product, record_index;
    reg [63:0] node_product, origin, address;
    reg [511:0] record;
    reg signed [31:0] result;
    reg [RG-1:0] cache_valid;
    reg [RW-1:0] lookup_index, replacement;
    (* ramstyle="M20K", nomem2reg *) reg [96:0] tags [0:RG-1];
    (* ramstyle="M20K", nomem2reg *) reg [511:0] records [0:RG-1];
    reg [96:0] lookup_tag;
    reg [511:0] lookup_record;
    reg lookup_valid;
    wire [96:0] wanted_tag={epoch,transaction_id,address[32:0]};
    wire running=rst_n && !flush && !failed && !cancelled;
    wire request_fire=memory_req_valid && memory_req_ready;
    wire response_known=outstanding || request_fire;
    wire transport_fault=memory_rsp_error || (memory_rsp_valid && !response_known);
    wire lookup=running && state==LOOKUP_READ;
    wire install=running && state==INSTALL && missed;
    wire codec_ready, codec_valid, codec_error;
    wire [CAP*32-1:0] codec_values;
    wire [511:0] codec_record;
    wire [31:0] command_group=cmd_dim>>SHIFT;
    wire [31:0] command_group_start=command_group<<SHIFT;
    reg [2:0] private_matches;
    reg [1:0] private_node;

    always @* begin
      private_matches=0; private_node=0;
      for (integer n=0;n<4;n=n+1)
        if (cmd_visibility[n] && cmd_positions[n*32+:32]==cmd_pos) begin
          private_matches=private_matches+1'b1; private_node=2'(n);
        end
    end

    assign cmd_ready=running && state==IDLE && !outstanding;
    assign out_valid=rst_n && !flush && !cancelled && state==RESPONSE;
    assign out_error=out_valid && failed;
    assign out_data=out_valid && !failed ? result : 32'sd0;
    assign idle=running && state==IDLE && !outstanding;
    assign fault=rst_n && !flush && failed;
    assign drain_done=rst_n && !flush && !outstanding &&
      (state==IDLE || state==FAULTED || state==RESPONSE);
    assign memory_req_valid=running && state==REQUEST;
    assign memory_req_address=memory_req_valid ? address[32:0] : 33'd0;

    anvil_q3_ht_kv_codec #(.CACHE_MODE(CACHE_MODE)) record_decoder (
      .clk(clk),.rst_n(rst_n),.flush(flush || failed || cancelled),
      .in_valid(running && state==DECODE_START),.in_ready(codec_ready),
      .decode(1'b1),.count(length),.values_in({CAP*32{1'b0}}),.record_in(record),
      .out_valid(codec_valid),.out_ready(1'b1),.out_error(codec_error),
      .values_out(codec_values),.record_out(codec_record)
    );

    always @(posedge clk) begin
      if (lookup) begin
        lookup_tag<=tags[lookup_index]; lookup_record<=records[lookup_index];
        lookup_valid<=cache_valid[lookup_index];
      end
      if (install) begin tags[replacement]<=wanted_tag; records[replacement]<=record; end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) outstanding<=0;
      else begin
        if (request_fire) outstanding<=1;
        if (memory_rsp_valid && response_known) outstanding<=0;
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; cancelled<=0; private_record<=0; missed<=0;
        transaction_id<=0; epoch<=0; layer<=0; position<=0; head<=0; group_index<=0;
        value_cache<=0; node<=0; lane<=0; length<=0;
        layer_value<=0; position_product<=0; position_index<=0; head_product<=0;
        head_index<=0; group_product<=0; record_index<=0; node_product<=0;
        origin<=0; address<=0; record<=0; result<=0;
        cache_valid<=0; lookup_index<=0; replacement<=0;
      end else if (flush) begin
        state<=DRAIN; failed<=0; cancelled<=1; record<=0; result<=0;
        transaction_id<=0; epoch<=0; layer<=0; position<=0; head<=0; group_index<=0;
        value_cache<=0; node<=0; lane<=0; length<=0; address<=0;
        cache_valid<=0; lookup_index<=0; replacement<=0;
      end else if (state==DRAIN) begin
        if (transport_fault) failed<=1;
        if (!outstanding || (memory_rsp_valid && response_known)) begin
          cancelled<=0;
          if (failed || transport_fault) begin
            if (cancelled) state<=FAULTED;
            else state<=RESPONSE;
          end
          else state<=IDLE;
        end
      end else if (!failed && transport_fault) begin
        failed<=1; cache_valid<=0; record<=0; result<=0;
        if ((outstanding || request_fire) && !(memory_rsp_valid && response_known)) state<=DRAIN;
        else state<=RESPONSE;
      end else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          transaction_id<=cmd_id; epoch<=cmd_epoch; layer<=cmd_layer;
          position<=cmd_pos; head<=cmd_head; group_index<=command_group;
          value_cache<=cmd_value; private_record<=cmd_pos>=cmd_prefix_count;
          node<=private_node; lane<=6'(cmd_dim&(CAP-1));
          length<=7'(HEAD_DIM-command_group_start<CAP ?
            HEAD_DIM-command_group_start : CAP);
          record<=0; result<=0; missed<=0;
          if (cmd_layer>=NUM_LAYERS || cmd_head>=NUM_KV_HEADS ||
              cmd_dim>=HEAD_DIM || cmd_pos>=MAX_SEQ_LEN ||
              cmd_prefix_count>MAX_SEQ_LEN ||
              (cmd_pos>=cmd_prefix_count && private_matches!=1)) begin
            failed<=1; state<=RESPONSE;
          end else state<=LAYER_VALUE;
        end
        LAYER_VALUE: begin layer_value<=({32'd0,layer}<<1)+{63'd0,value_cache}; state<=POSITION_PRODUCT; end
        POSITION_PRODUCT: begin
          position_product<=private_record ? layer_value : layer_value*64'(MAX_SEQ_LEN);
          state<=POSITION_ADD;
        end
        POSITION_ADD: begin
          position_index<=private_record ? position_product : position_product+{32'd0,position};
          state<=HEAD_PRODUCT;
        end
        HEAD_PRODUCT: begin head_product<=position_index*64'(NUM_KV_HEADS); state<=HEAD_ADD; end
        HEAD_ADD: begin head_index<=head_product+{32'd0,head}; state<=GROUP_PRODUCT; end
        GROUP_PRODUCT: begin group_product<=head_index*GROUPS; state<=GROUP_ADD; end
        GROUP_ADD: begin record_index<=group_product+{32'd0,group_index}; state<=SHADOW_PRODUCT; end
        SHADOW_PRODUCT: begin node_product<={62'd0,node}*TOKEN_BYTES; state<=ORIGIN; end
        ORIGIN: begin origin<=private_record ? 64'h100000000+COMMITTED_BYTES : 64'h100000000; state<=ORIGIN_ADD; end
        ORIGIN_ADD: begin origin<=private_record ? origin+node_product : origin; state<=ADDRESS; end
        ADDRESS: begin address<=origin+(record_index<<6); state<=CHECK; end
        CHECK: begin
          if (address<origin || address[5:0]!=0 ||
              (private_record ?
                address+64>origin+TOKEN_BYTES :
                address+64>64'h100000000+COMMITTED_BYTES)) begin
            failed<=1; state<=RESPONSE;
          end else begin lookup_index<=0; state<=LOOKUP_READ; end
        end
        LOOKUP_READ: state<=LOOKUP_COMPARE;
        LOOKUP_COMPARE: begin
          if (lookup_valid && lookup_tag==wanted_tag) begin
            record<=lookup_record; missed<=0; state<=DECODE_START;
          end else if (lookup_index==RG-1) begin missed<=1; state<=REQUEST; end
          else begin lookup_index<=lookup_index+1'b1; state<=LOOKUP_READ; end
        end
        REQUEST: if (request_fire) begin
          if (memory_rsp_valid && response_known) begin record<=memory_rsp_rdata; state<=DECODE_START; end
          else state<=WAIT_RETURN;
        end
        WAIT_RETURN: if (memory_rsp_valid && response_known) begin record<=memory_rsp_rdata; state<=DECODE_START; end
        DECODE_START: if (codec_ready) state<=DECODE_WAIT;
        DECODE_WAIT: if (codec_valid) begin
          if (codec_error) begin failed<=1; result<=0; state<=RESPONSE; end
          else begin result<=codec_values[lane*32+:32]; state<=INSTALL; end
        end
        INSTALL: begin
          if (missed) begin
            cache_valid[replacement]<=1;
            if (replacement==RG-1) replacement<=0;
            else replacement<=replacement+1'b1;
          end
          state<=RESPONSE;
        end
        RESPONSE: if (out_ready) begin
          result<=0;
          if (failed) state<=FAULTED;
          else state<=IDLE;
        end
        FAULTED: begin end
        default: begin failed<=1; state<=RESPONSE; result<=0; end
      endcase
    end
  end endgenerate
endmodule
