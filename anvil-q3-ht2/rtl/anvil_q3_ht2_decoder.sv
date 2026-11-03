module anvil_q3_ht2_decoder #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter CACHE_MODE=1, KV_RESIDENT_GROUPS=64
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_id, cmd_epoch, cmd_base_pos,
  input wire [3:0] cmd_mask,
  input wire [127:0] cmd_tokens, cmd_positions,
  input wire [11:0] cmd_parents,
  input wire [15:0] cmd_visibility,
  input wire cmd_sparse_enable,
  input wire [15:0] cmd_threshold_f16,
  output wire done, error, idle, fault, drain_done,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_id, logit_epoch, logit_index,
  output wire [1:0] logit_node,
  output wire signed [31:0] logit_data,
  output wire logit_last,
  output wire argmax_valid,
  output wire [127:0] argmax_tokens,
  output wire stage_valid,
  input wire stage_ready,
  output wire [31:0] stage_id, stage_epoch, stage_layer, stage_head, stage_group,
  output wire [1:0] stage_node,
  output wire stage_value,
  output wire [511:0] stage_record,
  output wire [5:0] memory_req_valid,
  input wire [5:0] memory_req_ready,
  output wire [5:0] memory_req_write,
  output wire [197:0] memory_req_address,
  output wire [47:0] memory_req_burstcount,
  output wire [3071:0] memory_req_wdata,
  output wire [383:0] memory_req_byteenable,
  input wire [5:0] memory_rsp_valid, memory_rsp_error,
  input wire [3071:0] memory_rsp_rdata,
  output wire [383:0] physical_read_beats
);
  localparam GS=(GROUP_SIZE==8 || GROUP_SIZE==16 || GROUP_SIZE==32 ||
    GROUP_SIZE==64 || GROUP_SIZE==128) ? GROUP_SIZE : 8;
  localparam CAP=CACHE_MODE==2 ? 64 : 32;
  localparam [127:0] H=128'(HIDDEN_SIZE), I=128'(INTERMEDIATE_SIZE);
  localparam [127:0] KD=128'(NUM_KV_HEADS)*128'(HEAD_DIM);
  localparam [127:0] KV_BYTES=128'(NUM_LAYERS)*2*128'(NUM_KV_HEADS)*
    ((128'(HEAD_DIM)+CAP-1)>>$clog2(CAP))*64*(128'(MAX_SEQ_LEN)+4);
  localparam LEGAL=NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_KV_HEADS>0 && HEAD_DIM>0 && (HEAD_DIM&1)==0 &&
    128'(NUM_Q_HEADS)==8*128'(NUM_KV_HEADS) &&
    H==128'(NUM_Q_HEADS)*128'(HEAD_DIM) &&
    GROUP_SIZE==GS && (HIDDEN_SIZE&7)==0 && (INTERMEDIATE_SIZE&7)==0 &&
    (HIDDEN_SIZE&(GS-1))==0 && (INTERMEDIATE_SIZE&(GS-1))==0 &&
    VOCAB_SIZE>0 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    (CACHE_MODE==1 || CACHE_MODE==2) && KV_BYTES<=128'h100000000 &&
    KV_RESIDENT_GROUPS>=1 && KV_RESIDENT_GROUPS<=256 &&
    H<=128'hffffffff && I<=128'hffffffff && KD<=128'hffffffff &&
    (10*H+3*I+2*KD)*16<=128'h3e000000;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: batched decoder geometry");
    assign cmd_ready=0; assign done=0; assign error=0; assign idle=0;
    assign fault=0; assign drain_done=0; assign logit_valid=0; assign logit_id=0;
    assign logit_epoch=0; assign logit_index=0; assign logit_node=0;
    assign logit_data=0; assign logit_last=0; assign argmax_valid=0; assign argmax_tokens=0;
    assign stage_valid=0; assign stage_id=0; assign stage_epoch=0; assign stage_layer=0;
    assign stage_head=0; assign stage_group=0; assign stage_node=0;
    assign stage_value=0; assign stage_record=0; assign memory_req_valid=0;
    assign memory_req_write=0; assign memory_req_address=0; assign memory_req_burstcount=0;
    assign memory_req_wdata=0; assign memory_req_byteenable=0; assign physical_read_beats=0;
  end else begin: datapath
    localparam IDLE=0, GRAPH_CAPTURE=1, GRAPH_CHECK=2, CLEAR_PULSE=3,
      CLEAR_WAIT=4, EMBED=5, EMBED_WAIT=6, SCALAR_SELECT=7, SCALAR_CAPTURE=8,
      SCALAR_START=9, SCALAR_WAIT=10, SCALAR_NEXT=11, PROJECT=12,
      PROJECT_WAIT=13, KV_STAGE=14, KV_WAIT=15, ATTN_SELECT=16,
      ATTN_CAPTURE=17, ATTN_START=18, ATTN_WAIT=19, HEAD=20, HEAD_WAIT=21,
      COMPLETE=22, FAIL_FLUSH=23, FAIL_DRAIN=24, FAIL_DONE=25,
      FAULTED=26, CANCEL_DRAIN=27;
    localparam NORM0=0, ROTATE=1, RESIDUAL0=2, NORM1=3,
      SWIGLU=4, RESIDUAL1=5, FINAL_NORM=6;
    localparam P=0, T=1, S=2, K=3, A=4;
    reg [4:0] state;
    reg failed, sparse;
    reg [31:0] id, epoch, base_pos, layer, selected_position;
    reg [3:0] mask;
    reg [127:0] tokens, positions, maxima;
    reg [11:0] parents;
    reg [15:0] visibility;
    reg [15:0] threshold;
    reg [1:0] node, graph_node;
    reg [2:0] projection, scalar_kind;
    reg [31:0] captured_token, captured_position;
    reg [2:0] captured_parent;
    reg [3:0] captured_visibility;
    reg captured_active;
    reg [63:0] read_counts [0:5];
    wire running=rst_n && !flush;
    wire local_flush=flush || state==FAIL_FLUSH;
    wire active=running && !failed && state!=CANCEL_DRAIN;
    wire command_fire=cmd_valid && cmd_ready;
    wire projection_ready, projection_done, projection_error, projection_idle;
    wire projection_fault, projection_drained;
    wire io_ready, io_done, io_error, io_idle, io_fault, io_drained;
    wire io_logit_valid, io_argmax_valid;
    wire [31:0] io_logit_id, io_logit_epoch, io_logit_index;
    wire [1:0] io_logit_node;
    wire signed [31:0] io_logit_data;
    wire io_logit_last;
    wire [127:0] io_argmax_tokens;
    wire norm_ready, norm_done, norm_error, rope_ready, rope_done, rope_error;
    wire element_ready, element_done, element_error;
    wire scalar_idle, scalar_fault, scalar_drained;
    wire stage_cmd_ready, stage_done, stage_error, stage_idle, stage_fault, stage_drained;
    wire attention_ready, attention_done, attention_error, attention_idle;
    wire attention_fault, attention_drained;
    wire scratch_idle, scratch_fault, scratch_drained;
    wire arbiter_idle, arbiter_fault, arbiter_drained;
    wire [4:0] s_req_valid, s_req_ready, s_req_write, s_rsp_valid, s_rsp_ready, s_rsp_error;
    wire [9:0] s_req_node, s_rsp_node;
    wire [19:0] s_req_mask, s_rsp_mask;
    wire [159:0] s_req_slot, s_req_index, s_req_wdata;
    wire [639:0] s_rsp_rdata;
    wire scratch_req_valid, scratch_req_ready, scratch_req_write;
    wire [1:0] scratch_req_node, scratch_rsp_node;
    wire [3:0] scratch_req_mask, scratch_rsp_mask;
    wire [31:0] scratch_req_slot, scratch_req_index, scratch_req_wdata;
    wire scratch_rsp_valid, scratch_rsp_ready, scratch_rsp_error;
    wire [127:0] scratch_rsp_rdata;
    wire [2:0] c_req_valid, c_req_ready, c_req_write, c_rsp_valid, c_rsp_ready, c_rsp_error;
    wire [11:0] c_req_kind;
    wire [8:0] c_req_proj;
    wire [95:0] c_req_layer, c_req_row, c_req_col, c_req_wdata, c_rsp_rdata;
    wire [5:0] c_req_node={3{node}};
    wire [31:0] attention_scratch_rdata=s_rsp_rdata[A*128+node*32+:32];
    wire [1:0] norm_mode=scalar_kind==NORM1 ? 2'd1 :
      scalar_kind==FINAL_NORM ? 2'd2 : 2'd0;
    wire [1:0] element_mode=scalar_kind==SWIGLU ? 2'd2 :
      scalar_kind==RESIDUAL1 ? 2'd1 : 2'd0;
    wire scalar_start=active && state==SCALAR_START;
    wire scalar_is_norm=scalar_kind==NORM0 || scalar_kind==NORM1 || scalar_kind==FINAL_NORM;
    wire selected_scalar_ready=scalar_is_norm ? norm_ready :
      scalar_kind==ROTATE ? rope_ready : element_ready;
    wire selected_scalar_done=scalar_is_norm ? norm_done :
      scalar_kind==ROTATE ? rope_done : element_done;
    wire selected_scalar_error=scalar_is_norm ? norm_error :
      scalar_kind==ROTATE ? rope_error : element_error;
    wire all_drained=projection_drained && io_drained && scalar_drained &&
      stage_drained && attention_drained && arbiter_drained && scratch_drained &&
      scratch_idle;
    wire sub_fault=projection_fault || io_fault || scalar_fault || stage_fault ||
      attention_fault || arbiter_fault || scratch_fault ||
      (projection_done && projection_error) || (io_done && io_error) ||
      (stage_done && stage_error) || (attention_done && attention_error) ||
      (state==SCALAR_WAIT && selected_scalar_done && selected_scalar_error);
    wire transaction_fault=active && state!=IDLE && state!=CLEAR_PULSE &&
      state!=CLEAR_WAIT && sub_fault;
    reg graph_bad;
    wire [1:0] parent_node=captured_parent[1:0];

    always @* begin
      graph_bad=0;
      if (captured_active) begin
        graph_bad=captured_token>=VOCAB_SIZE || captured_position<base_pos ||
          captured_position>=MAX_SEQ_LEN;
        if (captured_parent==4) begin
          graph_bad=graph_bad || captured_position!=base_pos ||
            captured_visibility!=(4'b0001<<graph_node);
        end else begin
          graph_bad=graph_bad || captured_parent>=graph_node ||
            !mask[parent_node] || {32'd0,captured_position}!=
              {32'd0,positions[parent_node*32+:32]}+64'd1 ||
            captured_visibility!=((4'b0001<<graph_node)|visibility[parent_node*4+:4]);
        end
        for (integer sibling=0;sibling<4;sibling=sibling+1)
          if (sibling<graph_node && mask[sibling] &&
              parents[sibling*3+:3]==captured_parent &&
              tokens[sibling*32+:32]==captured_token) graph_bad=1;
      end else graph_bad=captured_token!=0 || captured_position!=0 ||
        captured_parent!=0 || captured_visibility!=0;
`ifndef SYNTHESIS
      if ((^{captured_active,captured_token,captured_position,captured_parent,
              captured_visibility})===1'bx) graph_bad=1;
`endif
    end

    assign cmd_ready=active && state==IDLE && all_drained && norm_ready &&
      rope_ready && element_ready && !(|memory_rsp_valid);
    assign idle=cmd_ready;
    assign done=running && (state==COMPLETE || state==FAIL_DONE);
    assign error=done && failed;
    assign fault=running && failed;
    assign drain_done=running && all_drained && (state==IDLE || state==FAULTED);
    assign logit_valid=active && state==HEAD_WAIT && io_logit_valid;
    assign logit_id=logit_valid ? io_logit_id : 32'd0;
    assign logit_epoch=logit_valid ? io_logit_epoch : 32'd0;
    assign logit_node=logit_valid ? io_logit_node : 2'd0;
    assign logit_index=logit_valid ? io_logit_index : 32'd0;
    assign logit_data=logit_valid ? io_logit_data : 32'sd0;
    assign logit_last=logit_valid && io_logit_last;
    assign argmax_valid=done && !failed;
    assign argmax_tokens=argmax_valid ? maxima : 128'd0;
    assign memory_req_write[4:0]=5'd0;
    assign memory_req_wdata[2559:0]=2560'd0;
    for (genvar m=0;m<5;m=m+1) begin: read_clients
      assign memory_req_byteenable[m*64+:64]=memory_req_valid[m] ?
        64'hffffffffffffffff : 64'd0;
    end
    assign memory_req_burstcount[47:40]=memory_req_valid[5] ? 8'd1 : 8'd0;
    for (genvar m=0;m<6;m=m+1) begin: counters
      assign physical_read_beats[m*64+:64]=running ? read_counts[m] : 64'd0;
    end
    assign s_req_mask[A*4+:4]=s_req_valid[A] ? (4'b0001<<s_req_node[A*2+:2]) : 4'd0;

    anvil_q3_ht2_projection #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
      .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
      .GROUP_SIZE(GROUP_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) batched_projection (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),
      .cmd_valid(active && state==PROJECT),.cmd_ready(projection_ready),
      .cmd_epoch(epoch),.cmd_layer(layer),.cmd_proj(projection),.cmd_token_mask(mask),
      .cmd_sparse_enable(sparse),.cmd_threshold_f16(threshold),
      .done(projection_done),.error(projection_error),.idle(projection_idle),
      .fault(projection_fault),.drain_done(projection_drained),
      .scratch_req_valid(s_req_valid[P]),.scratch_req_ready(s_req_ready[P]),
      .scratch_req_write(s_req_write[P]),.scratch_req_node(s_req_node[P*2+:2]),
      .scratch_req_mask(s_req_mask[P*4+:4]),.scratch_req_slot(s_req_slot[P*32+:32]),
      .scratch_req_index(s_req_index[P*32+:32]),.scratch_req_wdata(s_req_wdata[P*32+:32]),
      .scratch_rsp_valid(s_rsp_valid[P]),.scratch_rsp_ready(s_rsp_ready[P]),
      .scratch_rsp_error(s_rsp_error[P]),.scratch_rsp_node(s_rsp_node[P*2+:2]),
      .scratch_rsp_mask(s_rsp_mask[P*4+:4]),.scratch_rsp_rdata(s_rsp_rdata[P*128+:128]),
      .memory_req_valid(memory_req_valid[2:0]),.memory_req_ready(memory_req_ready[2:0]),
      .memory_req_address(memory_req_address[98:0]),
      .memory_req_burstcount(memory_req_burstcount[23:0]),
      .memory_rsp_valid(memory_rsp_valid[2:0]),.memory_rsp_error(memory_rsp_error[2:0]),
      .memory_rsp_rdata(memory_rsp_rdata[1535:0]),
      .qweight_read_beats(),.metadata_read_beats(),.bias_read_beats(),
      .activation_read_columns(),.retained_column_beats(),.skipped_column_beats()
    );
    anvil_q3_ht2_token_io #(.HIDDEN_SIZE(HIDDEN_SIZE),.VOCAB_SIZE(VOCAB_SIZE)) token_io (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),
      .cmd_valid(active && (state==EMBED || state==HEAD)),.cmd_ready(io_ready),
      .cmd_id(id),.cmd_epoch(epoch),.cmd_project(state==HEAD),.cmd_mask(mask),.cmd_tokens(tokens),
      .done(io_done),.error(io_error),.idle(io_idle),.fault(io_fault),.drain_done(io_drained),
      .logit_valid(io_logit_valid),.logit_ready(active && state==HEAD_WAIT && logit_ready),
      .logit_id(io_logit_id),.logit_epoch(io_logit_epoch),.logit_index(io_logit_index),
      .logit_node(io_logit_node),.logit_data(io_logit_data),.logit_last(io_logit_last),
      .argmax_valid(io_argmax_valid),.argmax_tokens(io_argmax_tokens),
      .scratch_req_valid(s_req_valid[T]),.scratch_req_ready(s_req_ready[T]),
      .scratch_req_write(s_req_write[T]),.scratch_req_node(s_req_node[T*2+:2]),
      .scratch_req_mask(s_req_mask[T*4+:4]),.scratch_req_slot(s_req_slot[T*32+:32]),
      .scratch_req_index(s_req_index[T*32+:32]),.scratch_req_wdata(s_req_wdata[T*32+:32]),
      .scratch_rsp_valid(s_rsp_valid[T]),.scratch_rsp_ready(s_rsp_ready[T]),
      .scratch_rsp_error(s_rsp_error[T]),.scratch_rsp_node(s_rsp_node[T*2+:2]),
      .scratch_rsp_mask(s_rsp_mask[T*4+:4]),.scratch_rsp_rdata(s_rsp_rdata[T*128+:128]),
      .memory_req_valid(memory_req_valid[3]),.memory_req_ready(memory_req_ready[3]),
      .memory_req_address(memory_req_address[99+:33]),
      .memory_req_burstcount(memory_req_burstcount[24+:8]),
      .memory_rsp_valid(memory_rsp_valid[3]),.memory_rsp_error(memory_rsp_error[3]),
      .memory_rsp_rdata(memory_rsp_rdata[1536+:512]),
      .physical_read_beats(),.activation_read_columns(),.candidate_weight_values()
    );
    anvil_q3_rmsnorm #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) normalization (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),
      .cmd_valid(scalar_start && scalar_is_norm),.cmd_ready(norm_ready),
      .cmd_layer(layer),.cmd_pos(selected_position),.cmd_mode(norm_mode),
      .done(norm_done),.error(norm_error),
      .mem_req_valid(c_req_valid[0]),.mem_req_ready(c_req_ready[0]),.mem_req_write(c_req_write[0]),
      .mem_req_kind(c_req_kind[0+:4]),.mem_req_proj(c_req_proj[0+:3]),
      .mem_req_layer(c_req_layer[0+:32]),.mem_req_row(c_req_row[0+:32]),
      .mem_req_col(c_req_col[0+:32]),.mem_req_wdata(c_req_wdata[0+:32]),
      .mem_rsp_valid(c_rsp_valid[0]),.mem_rsp_ready(c_rsp_ready[0]),
      .mem_rsp_error(c_rsp_error[0]),.mem_rsp_rdata(c_rsp_rdata[0+:32])
    );
    anvil_q3_rope #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) rotary (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),
      .cmd_valid(scalar_start && scalar_kind==ROTATE),.cmd_ready(rope_ready),
      .cmd_layer(layer),.cmd_pos(selected_position),.done(rope_done),.error(rope_error),
      .mem_req_valid(c_req_valid[1]),.mem_req_ready(c_req_ready[1]),.mem_req_write(c_req_write[1]),
      .mem_req_kind(c_req_kind[4+:4]),.mem_req_proj(c_req_proj[3+:3]),
      .mem_req_layer(c_req_layer[32+:32]),.mem_req_row(c_req_row[32+:32]),
      .mem_req_col(c_req_col[32+:32]),.mem_req_wdata(c_req_wdata[32+:32]),
      .mem_rsp_valid(c_rsp_valid[1]),.mem_rsp_ready(c_rsp_ready[1]),
      .mem_rsp_error(c_rsp_error[1]),.mem_rsp_rdata(c_rsp_rdata[32+:32])
    );
    anvil_q3_elementwise #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
      .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) residual_swiglu (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),
      .cmd_valid(scalar_start && !scalar_is_norm && scalar_kind!=ROTATE),
      .cmd_ready(element_ready),.cmd_layer(layer),.cmd_pos(selected_position),
      .cmd_mode(element_mode),.done(element_done),.error(element_error),
      .mem_req_valid(c_req_valid[2]),.mem_req_ready(c_req_ready[2]),.mem_req_write(c_req_write[2]),
      .mem_req_kind(c_req_kind[8+:4]),.mem_req_proj(c_req_proj[6+:3]),
      .mem_req_layer(c_req_layer[64+:32]),.mem_req_row(c_req_row[64+:32]),
      .mem_req_col(c_req_col[64+:32]),.mem_req_wdata(c_req_wdata[64+:32]),
      .mem_rsp_valid(c_rsp_valid[2]),.mem_rsp_ready(c_rsp_ready[2]),
      .mem_rsp_error(c_rsp_error[2]),.mem_rsp_rdata(c_rsp_rdata[64+:32])
    );
    anvil_q3_ht2_scalar_adapter #(
      .CLIENTS(3),.NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
      .HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) scalar_image_scratch (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),.invalidate(command_fire),
      .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
      .c_req_node(c_req_node),.c_req_kind(c_req_kind),.c_req_proj(c_req_proj),
      .c_req_layer(c_req_layer),.c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
      .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
      .c_rsp_error(c_rsp_error),.c_rsp_rdata(c_rsp_rdata),
      .idle(scalar_idle),.fault(scalar_fault),.drain_done(scalar_drained),
      .scratch_req_valid(s_req_valid[S]),.scratch_req_ready(s_req_ready[S]),
      .scratch_req_write(s_req_write[S]),.scratch_req_node(s_req_node[S*2+:2]),
      .scratch_req_mask(s_req_mask[S*4+:4]),.scratch_req_slot(s_req_slot[S*32+:32]),
      .scratch_req_index(s_req_index[S*32+:32]),.scratch_req_wdata(s_req_wdata[S*32+:32]),
      .scratch_rsp_valid(s_rsp_valid[S]),.scratch_rsp_ready(s_rsp_ready[S]),
      .scratch_rsp_error(s_rsp_error[S]),.scratch_rsp_node(s_rsp_node[S*2+:2]),
      .scratch_rsp_mask(s_rsp_mask[S*4+:4]),.scratch_rsp_rdata(s_rsp_rdata[S*128+:128]),
      .memory_req_valid(memory_req_valid[4]),.memory_req_ready(memory_req_ready[4]),
      .memory_req_address(memory_req_address[132+:33]),
      .memory_req_burstcount(memory_req_burstcount[32+:8]),
      .memory_rsp_valid(memory_rsp_valid[4]),.memory_rsp_error(memory_rsp_error[4]),
      .memory_rsp_rdata(memory_rsp_rdata[2048+:512]),.physical_read_beats()
    );
    anvil_q3_ht2_kv_stage #(
      .NUM_LAYERS(NUM_LAYERS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.CACHE_MODE(CACHE_MODE)
    ) quantized_shadow_staging (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),
      .cmd_valid(active && state==KV_STAGE),.cmd_ready(stage_cmd_ready),
      .cmd_id(id),.cmd_epoch(epoch),.cmd_layer(layer),.cmd_mask(mask),
      .done(stage_done),.error(stage_error),.idle(stage_idle),
      .fault(stage_fault),.drain_done(stage_drained),
      .scratch_req_valid(s_req_valid[K]),.scratch_req_ready(s_req_ready[K]),
      .scratch_req_write(s_req_write[K]),.scratch_req_node(s_req_node[K*2+:2]),
      .scratch_req_mask(s_req_mask[K*4+:4]),.scratch_req_slot(s_req_slot[K*32+:32]),
      .scratch_req_index(s_req_index[K*32+:32]),.scratch_req_wdata(s_req_wdata[K*32+:32]),
      .scratch_rsp_valid(s_rsp_valid[K]),.scratch_rsp_ready(s_rsp_ready[K]),
      .scratch_rsp_error(s_rsp_error[K]),.scratch_rsp_node(s_rsp_node[K*2+:2]),
      .scratch_rsp_mask(s_rsp_mask[K*4+:4]),.scratch_rsp_rdata(s_rsp_rdata[K*128+:128]),
      .stage_valid(stage_valid),.stage_ready(stage_ready),.stage_id(stage_id),.stage_epoch(stage_epoch),
      .stage_layer(stage_layer),.stage_head(stage_head),.stage_group(stage_group),
      .stage_node(stage_node),.stage_value(stage_value),.stage_record(stage_record)
    );
    anvil_q3_ht2_tree_attention #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN),
      .CACHE_MODE(CACHE_MODE),.KV_RESIDENT_GROUPS(KV_RESIDENT_GROUPS)
    ) tree_attention (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),
      .cmd_valid(active && state==ATTN_START),.cmd_ready(attention_ready),
      .cmd_id(id),.cmd_epoch(epoch),.cmd_layer(layer),.cmd_base_pos(base_pos),
      .cmd_node(node),.cmd_mask(mask),.cmd_visibility(visibility[node*4+:4]),
      .cmd_positions(positions),.cmd_parents(parents),
      .done(attention_done),.error(attention_error),.idle(attention_idle),
      .fault(attention_fault),.drain_done(attention_drained),
      .scratch_req_valid(s_req_valid[A]),.scratch_req_ready(s_req_ready[A]),
      .scratch_req_write(s_req_write[A]),.scratch_req_node(s_req_node[A*2+:2]),
      .scratch_req_slot(s_req_slot[A*32+:32]),.scratch_req_index(s_req_index[A*32+:32]),
      .scratch_req_wdata(s_req_wdata[A*32+:32]),.scratch_rsp_valid(s_rsp_valid[A]),
      .scratch_rsp_ready(s_rsp_ready[A]),.scratch_rsp_error(s_rsp_error[A]),
      .scratch_rsp_rdata(attention_scratch_rdata),
      .memory_req_valid(memory_req_valid[5]),.memory_req_ready(memory_req_ready[5]),
      .memory_req_write(memory_req_write[5]),.memory_req_address(memory_req_address[165+:33]),
      .memory_req_wdata(memory_req_wdata[2560+:512]),
      .memory_req_byteenable(memory_req_byteenable[320+:64]),
      .memory_rsp_valid(memory_rsp_valid[5]),.memory_rsp_error(memory_rsp_error[5]),
      .memory_rsp_rdata(memory_rsp_rdata[2560+:512])
    );
    anvil_q3_ht2_scratch_arbiter #(.CLIENTS(5)) scratch_arbiter (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),
      .c_req_valid(s_req_valid),.c_req_ready(s_req_ready),.c_req_write(s_req_write),
      .c_req_node(s_req_node),.c_req_mask(s_req_mask),
      .c_req_slot(s_req_slot),.c_req_index(s_req_index),.c_req_wdata(s_req_wdata),
      .c_rsp_valid(s_rsp_valid),.c_rsp_ready(s_rsp_ready),.c_rsp_error(s_rsp_error),
      .c_rsp_node(s_rsp_node),.c_rsp_mask(s_rsp_mask),.c_rsp_rdata(s_rsp_rdata),
      .req_valid(scratch_req_valid),.req_ready(scratch_req_ready),.req_write(scratch_req_write),
      .req_node(scratch_req_node),.req_mask(scratch_req_mask),
      .req_slot(scratch_req_slot),.req_index(scratch_req_index),.req_wdata(scratch_req_wdata),
      .rsp_valid(scratch_rsp_valid),.rsp_ready(scratch_rsp_ready),.rsp_error(scratch_rsp_error),
      .rsp_node(scratch_rsp_node),.rsp_mask(scratch_rsp_mask),.rsp_rdata(scratch_rsp_rdata),
      .idle(arbiter_idle),.drain_done(arbiter_drained),.fault(arbiter_fault)
    );
    anvil_q3_ht2_private_scratch #(
      .HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM)
    ) private_scratch (
      .clk(clk),.rst_n(rst_n),.flush(running && state==CLEAR_PULSE),
      .req_valid(scratch_req_valid),.req_ready(scratch_req_ready),.req_write(scratch_req_write),
      .req_node(scratch_req_node),.req_mask(scratch_req_mask),
      .req_slot(scratch_req_slot),.req_index(scratch_req_index),.req_wdata(scratch_req_wdata),
      .rsp_valid(scratch_rsp_valid),.rsp_ready(scratch_rsp_ready),.rsp_error(scratch_rsp_error),
      .rsp_node(scratch_rsp_node),.rsp_mask(scratch_rsp_mask),.rsp_rdata(scratch_rsp_rdata),
      .idle(scratch_idle),.fault(scratch_fault),.drain_done(scratch_drained)
    );

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; sparse<=0; id<=0; epoch<=0; base_pos<=0;
        layer<=0; selected_position<=0; mask<=0; tokens<=0; positions<=0;
        maxima<=0; parents<=0; visibility<=0; threshold<=0; node<=0; graph_node<=0;
        projection<=0; scalar_kind<=0; captured_token<=0; captured_position<=0;
        captured_parent<=0; captured_visibility<=0; captured_active<=0;
        for (integer m=0;m<6;m=m+1) read_counts[m]<=0;
      end else begin
        for (integer m=0;m<6;m=m+1)
          if (memory_req_valid[m] && memory_req_ready[m] && !memory_req_write[m])
            read_counts[m]<=read_counts[m]+{56'd0,memory_req_burstcount[m*8+:8]};
        if (flush) begin
          state<=CANCEL_DRAIN; failed<=0; sparse<=0; id<=0; epoch<=0; base_pos<=0;
          layer<=0; selected_position<=0; mask<=0; tokens<=0; positions<=0;
          maxima<=0; parents<=0; visibility<=0; threshold<=0; node<=0; graph_node<=0;
          projection<=0; scalar_kind<=0; captured_token<=0; captured_position<=0;
          captured_parent<=0; captured_visibility<=0; captured_active<=0;
          for (integer m=0;m<6;m=m+1) read_counts[m]<=0;
        end else if (transaction_fault) begin failed<=1; state<=FAIL_FLUSH; end
        else case (state)
          IDLE: if (command_fire) begin
            id<=cmd_id; epoch<=cmd_epoch; base_pos<=cmd_base_pos; mask<=cmd_mask;
            tokens<=cmd_tokens; positions<=cmd_positions; parents<=cmd_parents;
            visibility<=cmd_visibility; sparse<=cmd_sparse_enable; threshold<=cmd_threshold_f16;
            layer<=0; node<=0; graph_node<=0; maxima<=0;
            for (integer m=0;m<6;m=m+1) read_counts[m]<=0;
            if (cmd_mask==0 || cmd_base_pos>=MAX_SEQ_LEN ||
                cmd_threshold_f16[14:10]==31 ||
                (cmd_threshold_f16[15] && cmd_threshold_f16[14:0]!=0)) begin
              failed<=1; state<=FAIL_FLUSH;
            end else state<=GRAPH_CAPTURE;
`ifndef SYNTHESIS
            if ((^{cmd_id,cmd_epoch,cmd_base_pos,cmd_mask,
                    cmd_sparse_enable,cmd_threshold_f16})===1'bx) begin
              failed<=1; state<=FAIL_FLUSH;
            end
`endif
          end
          GRAPH_CAPTURE: begin
            captured_active<=mask[graph_node]; captured_token<=tokens[graph_node*32+:32];
            captured_position<=positions[graph_node*32+:32];
            captured_parent<=parents[graph_node*3+:3];
            captured_visibility<=visibility[graph_node*4+:4]; state<=GRAPH_CHECK;
          end
          GRAPH_CHECK: begin
            if (graph_bad) begin failed<=1; state<=FAIL_FLUSH; end
            else if (graph_node==3) state<=CLEAR_PULSE;
            else begin graph_node<=graph_node+1'b1; state<=GRAPH_CAPTURE; end
          end
          CLEAR_PULSE: state<=CLEAR_WAIT;
          CLEAR_WAIT: if (scratch_idle) state<=EMBED;
          EMBED: if (io_ready) state<=EMBED_WAIT;
          EMBED_WAIT: if (io_done) begin
            scalar_kind<=NORM0; node<=0; state<=SCALAR_SELECT;
          end
          SCALAR_SELECT: begin
            if (mask[node]) state<=SCALAR_CAPTURE;
            else if (node==3) state<=SCALAR_NEXT;
            else node<=node+1'b1;
          end
          SCALAR_CAPTURE: begin selected_position<=positions[node*32+:32]; state<=SCALAR_START; end
          SCALAR_START: if (selected_scalar_ready) state<=SCALAR_WAIT;
          SCALAR_WAIT: if (selected_scalar_done) begin
            if (node==3) state<=SCALAR_NEXT;
            else begin node<=node+1'b1; state<=SCALAR_SELECT; end
          end
          SCALAR_NEXT: begin
            node<=0;
            case (scalar_kind)
              NORM0: begin projection<=0; state<=PROJECT; end
              ROTATE: state<=KV_STAGE;
              RESIDUAL0: begin scalar_kind<=NORM1; state<=SCALAR_SELECT; end
              NORM1: begin projection<=4; state<=PROJECT; end
              SWIGLU: begin projection<=6; state<=PROJECT; end
              RESIDUAL1: begin
                if (layer+1'b1==NUM_LAYERS) begin scalar_kind<=FINAL_NORM; state<=SCALAR_SELECT; end
                else begin layer<=layer+1'b1; scalar_kind<=NORM0; state<=SCALAR_SELECT; end
              end
              FINAL_NORM: state<=HEAD;
              default: begin failed<=1; state<=FAIL_FLUSH; end
            endcase
          end
          PROJECT: if (projection_ready) state<=PROJECT_WAIT;
          PROJECT_WAIT: if (projection_done) begin
            node<=0;
            case (projection)
              0,1,4: begin projection<=projection+1'b1; state<=PROJECT; end
              2: begin scalar_kind<=ROTATE; state<=SCALAR_SELECT; end
              3: begin scalar_kind<=RESIDUAL0; state<=SCALAR_SELECT; end
              5: begin scalar_kind<=SWIGLU; state<=SCALAR_SELECT; end
              6: begin scalar_kind<=RESIDUAL1; state<=SCALAR_SELECT; end
              default: begin failed<=1; state<=FAIL_FLUSH; end
            endcase
          end
          KV_STAGE: if (stage_cmd_ready) state<=KV_WAIT;
          KV_WAIT: if (stage_done) begin node<=0; state<=ATTN_SELECT; end
          ATTN_SELECT: begin
            if (mask[node]) state<=ATTN_CAPTURE;
            else if (node==3) begin projection<=3; state<=PROJECT; end
            else node<=node+1'b1;
          end
          ATTN_CAPTURE: begin selected_position<=positions[node*32+:32]; state<=ATTN_START; end
          ATTN_START: if (attention_ready) state<=ATTN_WAIT;
          ATTN_WAIT: if (attention_done) begin
            if (node==3) begin projection<=3; state<=PROJECT; end
            else begin node<=node+1'b1; state<=ATTN_SELECT; end
          end
          HEAD: if (io_ready) state<=HEAD_WAIT;
          HEAD_WAIT: if (io_done) begin
            if (!io_argmax_valid) begin failed<=1; state<=FAIL_FLUSH; end
            else begin maxima<=io_argmax_tokens; state<=COMPLETE; end
          end
          COMPLETE: state<=IDLE;
          FAIL_FLUSH: state<=FAIL_DRAIN;
          FAIL_DRAIN: if (all_drained) state<=FAIL_DONE;
          FAIL_DONE: state<=FAULTED;
          FAULTED: begin end
          CANCEL_DRAIN: if (all_drained) state<=IDLE;
          default: begin failed<=1; state<=FAIL_FLUSH; end
        endcase
      end
    end
  end endgenerate
endmodule
