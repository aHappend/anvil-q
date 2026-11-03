module anvil_q3_ht2_kv_stage #(
  parameter NUM_LAYERS=36, NUM_KV_HEADS=2, HEAD_DIM=128, CACHE_MODE=1
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_id, cmd_epoch, cmd_layer,
  input wire [3:0] cmd_mask,
  output wire done, error, idle, fault, drain_done,
  output wire scratch_req_valid,
  input wire scratch_req_ready,
  output wire scratch_req_write,
  output wire [1:0] scratch_req_node,
  output wire [3:0] scratch_req_mask,
  output wire [31:0] scratch_req_slot, scratch_req_index, scratch_req_wdata,
  input wire scratch_rsp_valid,
  output wire scratch_rsp_ready,
  input wire scratch_rsp_error,
  input wire [1:0] scratch_rsp_node,
  input wire [3:0] scratch_rsp_mask,
  input wire [127:0] scratch_rsp_rdata,
  output wire stage_valid,
  input wire stage_ready,
  output wire [31:0] stage_id, stage_epoch, stage_layer, stage_head, stage_group,
  output wire [1:0] stage_node,
  output wire stage_value,
  output wire [511:0] stage_record
);
  localparam CAP=CACHE_MODE==2 ? 64 : 32;
  localparam SHIFT=$clog2(CAP);
  localparam [127:0] GROUPS=(128'(HEAD_DIM)+CAP-1)>>SHIFT;
  localparam LEGAL=NUM_LAYERS>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 &&
    (HEAD_DIM&1)==0 && (CACHE_MODE==1 || CACHE_MODE==2) &&
    128'(NUM_KV_HEADS)*128'(HEAD_DIM)<=128'hffffffff &&
    GROUPS<=128'hffffffff;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: quantized KV staging");
    assign cmd_ready=0; assign done=0; assign error=0; assign idle=0;
    assign fault=0; assign drain_done=0; assign scratch_req_valid=0;
    assign scratch_req_write=0; assign scratch_req_node=0; assign scratch_req_mask=0;
    assign scratch_req_slot=0; assign scratch_req_index=0; assign scratch_req_wdata=0;
    assign scratch_rsp_ready=0; assign stage_valid=0; assign stage_id=0;
    assign stage_epoch=0; assign stage_layer=0; assign stage_head=0;
    assign stage_group=0; assign stage_node=0; assign stage_value=0; assign stage_record=0;
  end else begin: datapath
    localparam IDLE=0, NODE_FIND=1, HEAD_PRODUCT=2, GROUP_OFFSET=3,
      ADDRESS=4, READ_REQUEST=5, READ_RETURN=6, ENCODE=7, ENCODE_WAIT=8,
      STAGE=9, SETTLE=10, RETIRE=11, ADVANCE=12, COMPLETE=13,
      CANCEL_DRAIN=14, FAIL_DRAIN=15, FAIL_DONE=16, FAULTED=17;
    reg [4:0] state;
    reg failed, scratch_pending, value_cache;
    reg [31:0] id, epoch, layer, head, group_index, head_base, group_base, index;
    reg [3:0] mask;
    reg [1:0] node;
    reg [6:0] component, count;
    reg [CAP*32-1:0] values;
    reg [511:0] record;
    wire running=rst_n && !flush;
    wire active=running && !failed && state!=CANCEL_DRAIN && state!=FAIL_DRAIN;
    wire scratch_fire=scratch_req_valid && scratch_req_ready;
    wire scratch_known=scratch_pending || scratch_fire;
    wire scratch_return=scratch_rsp_valid && scratch_rsp_ready;
    wire codec_ready, codec_valid, codec_error;
    wire [511:0] codec_record;
    wire codec_flush=flush || state==FAIL_DRAIN;
    wire [31:0] group_start=group_index<<SHIFT;
    wire [6:0] group_count=7'(HEAD_DIM-group_start<CAP ? HEAD_DIM-group_start : CAP);
    reg classification_bad;
    wire scratch_bad=scratch_rsp_valid && (!scratch_known || scratch_rsp_error ||
      scratch_rsp_node!=node || scratch_rsp_mask!=(4'b0001<<node));
    wire fault_now=active && (scratch_bad || classification_bad ||
      (codec_valid && codec_error));

    always @* begin
      classification_bad=0;
`ifndef SYNTHESIS
      if (scratch_rsp_valid && scratch_known &&
          (^{scratch_rsp_error,scratch_rsp_node,scratch_rsp_mask,
              scratch_rsp_rdata[node*32+:32]})===1'bx) classification_bad=1;
`endif
    end
    assign cmd_ready=active && state==IDLE && !scratch_pending &&
      codec_ready && !scratch_rsp_valid;
    assign done=running && (state==COMPLETE || state==FAIL_DONE);
    assign error=done && failed;
    assign idle=cmd_ready;
    assign fault=running && failed;
    assign drain_done=running && !scratch_pending &&
      (state==IDLE || state==FAULTED);
    assign scratch_req_valid=active && state==READ_REQUEST && !scratch_pending;
    assign scratch_req_write=1'b0;
    assign scratch_req_node=scratch_req_valid ? node : 2'd0;
    assign scratch_req_mask=scratch_req_valid ? (4'b0001<<node) : 4'd0;
    assign scratch_req_slot=scratch_req_valid ? (value_cache ? 32'd4 : 32'd3) : 32'd0;
    assign scratch_req_index=scratch_req_valid ? index : 32'd0;
    assign scratch_req_wdata=32'd0;
    assign scratch_rsp_ready=running && scratch_known;
    assign stage_valid=active && state==STAGE;
    assign stage_id=stage_valid ? id : 32'd0;
    assign stage_epoch=stage_valid ? epoch : 32'd0;
    assign stage_layer=stage_valid ? layer : 32'd0;
    assign stage_head=stage_valid ? head : 32'd0;
    assign stage_group=stage_valid ? group_index : 32'd0;
    assign stage_node=stage_valid ? node : 2'd0;
    assign stage_value=stage_valid && value_cache;
    assign stage_record=stage_valid ? record : 512'd0;

    anvil_q3_ht_kv_codec #(.CACHE_MODE(CACHE_MODE)) quantize_record (
      .clk(clk),.rst_n(rst_n),.flush(codec_flush),
      .in_valid(active && state==ENCODE),.in_ready(codec_ready),
      .decode(1'b0),.count(count),.values_in(values),.record_in(512'd0),
      .out_valid(codec_valid),.out_ready(active && state==ENCODE_WAIT),
      .out_error(codec_error),.values_out(),.record_out(codec_record)
    );

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; scratch_pending<=0; value_cache<=0;
        id<=0; epoch<=0; layer<=0; head<=0; group_index<=0;
        head_base<=0; group_base<=0; index<=0; mask<=0; node<=0;
        component<=0; count<=0; values<=0; record<=0;
      end else begin
        if (scratch_fire && !scratch_return) scratch_pending<=1;
        if (scratch_return && scratch_known) scratch_pending<=0;
        if (flush) begin
          state<=CANCEL_DRAIN; failed<=0; value_cache<=0;
          id<=0; epoch<=0; layer<=0; head<=0; group_index<=0;
          head_base<=0; group_base<=0; index<=0; mask<=0; node<=0;
          component<=0; count<=0; values<=0; record<=0;
        end else if (fault_now) begin failed<=1; record<=0; state<=FAIL_DRAIN; end
        else case (state)
          IDLE: if (cmd_valid && cmd_ready) begin
            id<=cmd_id; epoch<=cmd_epoch; layer<=cmd_layer; mask<=cmd_mask;
            node<=0; head<=0; group_index<=0; value_cache<=0; values<=0;
            if (cmd_layer>=NUM_LAYERS || cmd_mask==0) begin
              failed<=1; state<=FAIL_DRAIN;
            end else state<=NODE_FIND;
`ifndef SYNTHESIS
            if ((^{cmd_id,cmd_epoch,cmd_layer,cmd_mask})===1'bx) begin
              failed<=1; state<=FAIL_DRAIN;
            end
`endif
          end
          NODE_FIND: begin
            if (mask[node]) state<=HEAD_PRODUCT;
            else if (node==3) state<=COMPLETE;
            else node<=node+1'b1;
          end
          HEAD_PRODUCT: begin
            head_base<=32'({32'd0,head}*64'(HEAD_DIM));
            state<=GROUP_OFFSET;
          end
          GROUP_OFFSET: begin
            group_base<=head_base+group_start; count<=group_count;
            component<=0; values<=0; state<=ADDRESS;
          end
          ADDRESS: begin index<=group_base+{25'd0,component}; state<=READ_REQUEST; end
          READ_REQUEST: if (scratch_fire) begin
            if (!scratch_return) state<=READ_RETURN;
            else begin
              values[component*32+:32]<=scratch_rsp_rdata[node*32+:32];
              if (component+1'b1==count) state<=ENCODE;
              else begin component<=component+1'b1; state<=ADDRESS; end
            end
          end
          READ_RETURN: if (scratch_return) begin
            values[component*32+:32]<=scratch_rsp_rdata[node*32+:32];
            if (component+1'b1==count) state<=ENCODE;
            else begin component<=component+1'b1; state<=ADDRESS; end
          end
          ENCODE: if (codec_ready) state<=ENCODE_WAIT;
          ENCODE_WAIT: if (codec_valid) begin record<=codec_record; state<=STAGE; end
          STAGE: if (stage_ready) begin record<=0; state<=SETTLE; end
          // The sink acknowledges shadow writes by becoming ready again.
          SETTLE: state<=RETIRE;
          RETIRE: if (stage_ready) state<=ADVANCE;
          ADVANCE: begin
            if (group_index+1'b1<32'(GROUPS)) begin
              group_index<=group_index+1'b1; state<=GROUP_OFFSET;
            end else begin
              group_index<=0;
              if (head+1'b1<NUM_KV_HEADS) begin head<=head+1'b1; state<=HEAD_PRODUCT; end
              else begin
                head<=0;
                if (!value_cache) begin value_cache<=1; state<=HEAD_PRODUCT; end
                else begin
                  value_cache<=0;
                  if (node==3) state<=COMPLETE;
                  else begin node<=node+1'b1; state<=NODE_FIND; end
                end
              end
            end
          end
          COMPLETE: state<=IDLE;
          CANCEL_DRAIN: if (!scratch_pending) state<=IDLE;
          FAIL_DRAIN: if (!scratch_pending) state<=FAIL_DONE;
          FAIL_DONE: state<=FAULTED;
          FAULTED: begin end
          default: begin failed<=1; state<=FAIL_DRAIN; end
        endcase
      end
    end
  end endgenerate
endmodule
