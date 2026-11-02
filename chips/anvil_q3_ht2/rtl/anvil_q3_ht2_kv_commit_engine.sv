module anvil_q3_ht2_kv_commit_engine #(
  parameter NUM_LAYERS=36, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter MAX_SEQ_LEN=32768, CACHE_MODE=1
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_id, cmd_epoch, cmd_base_pos,
  input wire [3:0] cmd_mask,
  input wire stage_valid,
  output wire stage_ready,
  input wire [31:0] stage_id, stage_epoch,
  input wire [1:0] stage_node,
  input wire [31:0] stage_layer, stage_head,
  input wire stage_value,
  input wire [31:0] stage_group,
  input wire [511:0] stage_record,
  output wire staged,
  input wire commit_valid,
  output wire commit_ready,
  input wire [2:0] commit_count,
  input wire [7:0] commit_nodes,
  output wire publish_valid,
  output wire [2:0] publish_count,
  output wire [31:0] publish_pos, visible_count, visible_epoch,
  output wire done, error, idle, fault, drain_done,
  output wire memory_req_valid,
  input wire memory_req_ready,
  output wire memory_req_write,
  output wire [32:0] memory_req_address,
  output wire [511:0] memory_req_wdata,
  output wire [63:0] memory_req_byteenable,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata
);
  localparam CAP=CACHE_MODE==2 ? 64 : 32;
  localparam SHIFT=$clog2(CAP);
  localparam [127:0] GROUPS_WIDE=(128'(HEAD_DIM)+CAP-1)>>SHIFT;
  localparam [127:0] TOKEN_RECORDS_WIDE=128'(NUM_LAYERS)*2*
    128'(NUM_KV_HEADS)*GROUPS_WIDE;
  localparam [127:0] TOTAL_BYTES_WIDE=(TOKEN_RECORDS_WIDE<<6)*
    (128'(MAX_SEQ_LEN)+4);
  localparam [63:0] GROUPS=GROUPS_WIDE[63:0];
  localparam [63:0] HEAD_BYTES=GROUPS<<6;
  localparam [63:0] TOKEN_RECORDS=64'(NUM_LAYERS)*2*
    64'(NUM_KV_HEADS)*GROUPS;
  localparam [63:0] TOKEN_BYTES=TOKEN_RECORDS<<6;
  localparam [63:0] COMMITTED_BYTES=TOKEN_BYTES*64'(MAX_SEQ_LEN);
  localparam [63:0] TOTAL_BYTES=COMMITTED_BYTES+(TOKEN_BYTES<<2);
  localparam LEGAL=NUM_LAYERS>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 &&
    (HEAD_DIM&1)==0 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    (CACHE_MODE==1 || CACHE_MODE==2) && GROUPS<=64'hffffffff &&
    TOKEN_RECORDS_WIDE<=128'hffffffff && TOTAL_BYTES_WIDE<=128'h100000000 &&
    TOTAL_BYTES>=COMMITTED_BYTES && COMMITTED_BYTES>=TOKEN_BYTES;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: atomic KV geometry or shadow extent");
    assign cmd_ready=0;
    assign stage_ready=0;
    assign staged=0;
    assign commit_ready=0;
    assign publish_valid=0;
    assign publish_count=0;
    assign publish_pos=0;
    assign visible_count=0;
    assign visible_epoch=0;
    assign done=0;
    assign error=0;
    assign idle=0;
    assign fault=0;
    assign drain_done=0;
    assign memory_req_valid=0;
    assign memory_req_write=0;
    assign memory_req_address=0;
    assign memory_req_wdata=0;
    assign memory_req_byteenable=0;
  end else begin: datapath
    localparam IDLE=0, STAGE=1, VALIDATE_START=2, VALIDATE_WAIT=3,
      LAYER_VALUE=4, HEAD_PRODUCT=5, HEAD_ADD=6, GROUP_PRODUCT=7,
      GROUP_ADD=8, SHADOW_PRODUCT=9, SHADOW_BASE=10, SHADOW_ADDRESS=11,
      POSITION_PRODUCT=12, POSITION_ADD=13, DEST_HEAD_PRODUCT=14,
      DEST_HEAD_ADD=15, DEST_GROUP_PRODUCT=16, DEST_GROUP_ADD=17,
      DEST_ADDRESS=18, ADDRESS_CHECK=19, SHADOW_WRITE=20,
      COPY_READ=21, COPY_WAIT=22, COPY_WRITE=23, ADVANCE_COPY=24,
      FENCE_FIRST=25, FENCE_SECOND=26, PUBLICATION=27, COMPLETE=28,
      DRAIN=29, FAULTED=30, SHADOW_ORIGIN=31;
    reg [4:0] state;
    reg failed, cancelled, outstanding, copying, epoch_bound;
    reg [31:0] transaction_id, epoch, base_pos, committed, committed_epoch;
    reg [3:0] active;
    reg [1:0] node;
    reg [31:0] layer, head, group_index;
    reg value_cache;
    reg [511:0] record;
    reg [2:0] path_count, path_index;
    reg [7:0] path;
    reg [31:0] received [0:3];
    reg [31:0] expected_layer [0:3], expected_head [0:3], expected_group [0:3];
    reg [3:0] expected_value;
    reg [63:0] layer_value, head_product, head_ordinal, group_product;
    reg [63:0] record_ordinal, shadow_product, shadow_base, shadow_address;
    reg [63:0] position_product, position_ordinal, destination_head_product;
    reg [63:0] destination_head, destination_group_product, destination_group;
    reg [63:0] destination_address;
    wire running=rst_n && !flush && !failed && !cancelled;
    wire request_fire=memory_req_valid && memory_req_ready;
    wire read_fire=request_fire && !memory_req_write;
    wire response_known=outstanding || read_fire;
    wire response_bad=memory_rsp_valid && !response_known;
    wire transport_fault=memory_rsp_error || response_bad;
    wire stage_fire=stage_valid && stage_ready;
    wire stage_bad=stage_id!=transaction_id || stage_epoch!=epoch ||
      !active[stage_node] || received[stage_node]>=TOKEN_RECORDS ||
      stage_layer!=expected_layer[stage_node] ||
      stage_value!=expected_value[stage_node] ||
      stage_head!=expected_head[stage_node] ||
      stage_group!=expected_group[stage_node];
    wire all_staged=(!active[0] || received[0]==TOKEN_RECORDS) &&
      (!active[1] || received[1]==TOKEN_RECORDS) &&
      (!active[2] || received[2]==TOKEN_RECORDS) &&
      (!active[3] || received[3]==TOKEN_RECORDS);
    wire codec_ready, codec_valid, codec_error;
    wire [CAP*32-1:0] codec_values;
    wire [511:0] codec_record;
    wire [31:0] group_start=group_index<<SHIFT;
    wire [6:0] group_count=7'(HEAD_DIM-group_start<CAP ?
      HEAD_DIM-group_start : CAP);
    wire [63:0] selected_pos={32'd0,base_pos}+{61'd0,path_index};
    reg path_bad;
    reg [3:0] selected_nodes;
    integer i;

    always @* begin
      path_bad=commit_count>4 ||
        {32'd0,base_pos}+{61'd0,commit_count}>64'(MAX_SEQ_LEN);
      selected_nodes=0;
      for (integer p=0;p<4;p=p+1) begin
        if (p<commit_count) begin
          if (!active[commit_nodes[p*2+:2]] ||
              selected_nodes[commit_nodes[p*2+:2]]) path_bad=1;
          selected_nodes[commit_nodes[p*2+:2]]=1;
        end else if (commit_nodes[p*2+:2]!=0) path_bad=1;
      end
    end

    assign cmd_ready=running && state==IDLE && !outstanding;
    assign stage_ready=running && state==STAGE;
    assign staged=running && state==STAGE && all_staged;
    assign commit_ready=staged;
    assign publish_valid=running && state==COMPLETE;
    assign publish_count=publish_valid ? path_count : 3'd0;
    assign publish_pos=publish_valid ? committed : 32'd0;
    assign visible_count=rst_n && !flush ? committed : 32'd0;
    assign visible_epoch=rst_n && !flush && epoch_bound ? committed_epoch : 32'd0;
    assign done=running && state==COMPLETE;
    assign error=rst_n && !flush && state==FAULTED;
    assign idle=running && state==IDLE && !outstanding;
    assign fault=rst_n && !flush && failed;
    assign drain_done=rst_n && !flush && !outstanding &&
      (state==IDLE || state==FAULTED);
    assign memory_req_valid=running &&
      (state==SHADOW_WRITE || state==COPY_READ || state==COPY_WRITE);
    assign memory_req_write=memory_req_valid && state!=COPY_READ;
    assign memory_req_address=!memory_req_valid ? 33'd0 :
      state==COPY_WRITE ? destination_address[32:0] : shadow_address[32:0];
    assign memory_req_wdata=memory_req_write ? record : 512'd0;
    assign memory_req_byteenable=memory_req_valid ? 64'hffffffffffffffff : 64'd0;

    anvil_q3_ht_kv_codec #(.CACHE_MODE(CACHE_MODE)) record_validator (
      .clk(clk),.rst_n(rst_n),.flush(flush || failed || cancelled),
      .in_valid(running && state==VALIDATE_START),.in_ready(codec_ready),
      .decode(1'b1),.count(group_count),.values_in({CAP*32{1'b0}}),
      .record_in(record),.out_valid(codec_valid),.out_ready(1'b1),
      .out_error(codec_error),.values_out(codec_values),.record_out(codec_record)
    );

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) outstanding<=0;
      else begin
        if (read_fire) outstanding<=1;
        if (memory_rsp_valid && response_known) outstanding<=0;
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; cancelled<=0; copying<=0; epoch_bound<=0;
        transaction_id<=0; epoch<=0; base_pos<=0; committed<=0; committed_epoch<=0;
        active<=0; node<=0; layer<=0; head<=0; group_index<=0; value_cache<=0;
        record<=0; path_count<=0; path_index<=0; path<=0; expected_value<=0;
        layer_value<=0; head_product<=0; head_ordinal<=0; group_product<=0;
        record_ordinal<=0; shadow_product<=0; shadow_base<=0; shadow_address<=0;
        position_product<=0; position_ordinal<=0; destination_head_product<=0;
        destination_head<=0; destination_group_product<=0; destination_group<=0;
        destination_address<=0;
        for (i=0;i<4;i=i+1) begin
          received[i]<=0; expected_layer[i]<=0; expected_head[i]<=0; expected_group[i]<=0;
        end
      end else if (flush) begin
        state<=DRAIN; cancelled<=1; failed<=0; active<=0; record<=0;
        transaction_id<=0; epoch<=0; base_pos<=0; node<=0;
        layer<=0; head<=0; group_index<=0; value_cache<=0;
        path_count<=0; path_index<=0; path<=0;
        shadow_address<=0; destination_address<=0;
      end else if (state==DRAIN) begin
        if (transport_fault) failed<=1;
        if (!outstanding || (memory_rsp_valid && response_known)) begin
          cancelled<=0;
          if (failed || transport_fault) state<=FAULTED;
          else state<=IDLE;
        end
      end else if (state!=FAULTED && transport_fault) begin
        failed<=1; record<=0; active<=0;
        if ((outstanding || read_fire) && !(memory_rsp_valid && response_known)) state<=DRAIN;
        else state<=FAULTED;
      end else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          transaction_id<=cmd_id; epoch<=cmd_epoch; base_pos<=cmd_base_pos;
          active<=cmd_mask; path_count<=0; path_index<=0; path<=0;
          copying<=0; expected_value<=0;
          for (i=0;i<4;i=i+1) begin
            received[i]<=0; expected_layer[i]<=0; expected_head[i]<=0; expected_group[i]<=0;
          end
          if (cmd_mask==0 || cmd_base_pos!=committed ||
              cmd_base_pos>=MAX_SEQ_LEN ||
              (epoch_bound && cmd_epoch!=committed_epoch)) begin
            failed<=1; state<=FAULTED;
          end else begin
            if (!epoch_bound) begin committed_epoch<=cmd_epoch; epoch_bound<=1; end
            state<=STAGE;
          end
        end
        STAGE: begin
          if (stage_fire) begin
            if (stage_bad || (commit_valid && commit_ready)) begin
              failed<=1; state<=FAULTED;
            end else begin
              node<=stage_node; layer<=stage_layer; value_cache<=stage_value;
              head<=stage_head; group_index<=stage_group; record<=stage_record;
              copying<=0; state<=VALIDATE_START;
            end
          end else if (commit_valid && commit_ready) begin
            if (path_bad) begin failed<=1; state<=FAULTED; end
            else begin
              path_count<=commit_count; path<=commit_nodes; path_index<=0;
              node<=commit_nodes[1:0]; layer<=0; value_cache<=0; head<=0; group_index<=0;
              copying<=1;
              if (commit_count==0) state<=FENCE_FIRST;
              else state<=LAYER_VALUE;
            end
          end
        end
        VALIDATE_START: if (codec_ready) state<=VALIDATE_WAIT;
        VALIDATE_WAIT: if (codec_valid) begin
          if (codec_error) begin failed<=1; state<=FAULTED; record<=0; end
          else state<=LAYER_VALUE;
        end
        LAYER_VALUE: begin
          layer_value<=({32'd0,layer}<<1)+{63'd0,value_cache};
          state<=HEAD_PRODUCT;
        end
        HEAD_PRODUCT: begin head_product<=layer_value*64'(NUM_KV_HEADS); state<=HEAD_ADD; end
        HEAD_ADD: begin head_ordinal<=head_product+{32'd0,head}; state<=GROUP_PRODUCT; end
        GROUP_PRODUCT: begin group_product<=head_ordinal*GROUPS; state<=GROUP_ADD; end
        GROUP_ADD: begin record_ordinal<=group_product+{32'd0,group_index}; state<=SHADOW_PRODUCT; end
        SHADOW_PRODUCT: begin shadow_product<={62'd0,node}*TOKEN_BYTES; state<=SHADOW_ORIGIN; end
        SHADOW_ORIGIN: begin shadow_base<=64'h100000000+COMMITTED_BYTES; state<=SHADOW_BASE; end
        SHADOW_BASE: begin shadow_base<=shadow_base+shadow_product; state<=SHADOW_ADDRESS; end
        SHADOW_ADDRESS: begin
          shadow_address<=shadow_base+(record_ordinal<<6);
          if (copying) state<=POSITION_PRODUCT;
          else state<=ADDRESS_CHECK;
        end
        POSITION_PRODUCT: begin position_product<=layer_value*64'(MAX_SEQ_LEN); state<=POSITION_ADD; end
        POSITION_ADD: begin position_ordinal<=position_product+selected_pos; state<=DEST_HEAD_PRODUCT; end
        DEST_HEAD_PRODUCT: begin destination_head_product<=position_ordinal*64'(NUM_KV_HEADS); state<=DEST_HEAD_ADD; end
        DEST_HEAD_ADD: begin destination_head<=destination_head_product+{32'd0,head}; state<=DEST_GROUP_PRODUCT; end
        DEST_GROUP_PRODUCT: begin destination_group_product<=destination_head*GROUPS; state<=DEST_GROUP_ADD; end
        DEST_GROUP_ADD: begin destination_group<=destination_group_product+{32'd0,group_index}; state<=DEST_ADDRESS; end
        DEST_ADDRESS: begin destination_address<=64'h100000000+(destination_group<<6); state<=ADDRESS_CHECK; end
        ADDRESS_CHECK: begin
          if (record_ordinal>=TOKEN_RECORDS ||
              shadow_address<64'h100000000+COMMITTED_BYTES ||
              shadow_address+64>64'h100000000+TOTAL_BYTES ||
              shadow_address[5:0]!=0 ||
              (copying && (selected_pos<committed || selected_pos>=MAX_SEQ_LEN ||
               destination_address<64'h100000000 ||
               destination_address+64>64'h100000000+COMMITTED_BYTES ||
               destination_address[5:0]!=0))) begin
            failed<=1; state<=FAULTED;
          end else if (copying) state<=COPY_READ;
          else state<=SHADOW_WRITE;
        end
        SHADOW_WRITE: if (request_fire) begin
          received[node]<=received[node]+1'b1;
          if (group_index+1<GROUPS) expected_group[node]<=group_index+1'b1;
          else begin
            expected_group[node]<=0;
            if (head+1<NUM_KV_HEADS) expected_head[node]<=head+1'b1;
            else begin
              expected_head[node]<=0;
              if (!value_cache) expected_value[node]<=1;
              else begin expected_value[node]<=0; expected_layer[node]<=layer+1'b1; end
            end
          end
          record<=0; state<=STAGE;
        end
        COPY_READ: if (request_fire) begin
          if (memory_rsp_valid && response_known) begin record<=memory_rsp_rdata; state<=COPY_WRITE; end
          else state<=COPY_WAIT;
        end
        COPY_WAIT: if (memory_rsp_valid && response_known) begin
          record<=memory_rsp_rdata; state<=COPY_WRITE;
        end
        COPY_WRITE: if (request_fire) begin record<=0; state<=ADVANCE_COPY; end
        ADVANCE_COPY: begin
          if (group_index+1<GROUPS) begin group_index<=group_index+1'b1; state<=LAYER_VALUE; end
          else begin
            group_index<=0;
            if (head+1<NUM_KV_HEADS) begin head<=head+1'b1; state<=LAYER_VALUE; end
            else begin
              head<=0;
              if (!value_cache) begin value_cache<=1; state<=LAYER_VALUE; end
              else begin
                value_cache<=0;
                if (layer+1<NUM_LAYERS) begin layer<=layer+1'b1; state<=LAYER_VALUE; end
                else begin
                  layer<=0;
                  if (path_index+1<path_count) begin
                    path_index<=path_index+1'b1;
                    node<=path[(path_index+1'b1)*2+:2]; state<=LAYER_VALUE;
                  end else state<=FENCE_FIRST;
                end
              end
            end
          end
        end
        FENCE_FIRST: if (!outstanding) state<=FENCE_SECOND;
        FENCE_SECOND: state<=PUBLICATION;
        PUBLICATION: begin committed<=base_pos+{29'd0,path_count}; state<=COMPLETE; end
        COMPLETE: begin active<=0; path_count<=0; path<=0; state<=IDLE; end
        FAULTED: begin end
        default: begin failed<=1; state<=FAULTED; end
      endcase
    end
  end endgenerate
endmodule
