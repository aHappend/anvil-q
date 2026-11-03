module anvil_q3_ht2_projection #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_layer,
  input wire [2:0] cmd_proj,
  input wire [3:0] cmd_token_mask,
  input wire cmd_sparse_enable,
  input wire [15:0] cmd_threshold_f16,
  output wire done, error, idle, fault, drain_done,
  output wire scratch_req_valid,
  input wire scratch_req_ready,
  output wire scratch_req_write,
  output wire [1:0] scratch_req_node,
  output wire [3:0] scratch_req_mask,
  output wire [31:0] scratch_req_slot, scratch_req_index,
  output wire signed [31:0] scratch_req_wdata,
  input wire scratch_rsp_valid,
  output wire scratch_rsp_ready,
  input wire scratch_rsp_error,
  input wire [1:0] scratch_rsp_node,
  input wire [3:0] scratch_rsp_mask,
  input wire [127:0] scratch_rsp_rdata,
  output wire [2:0] memory_req_valid,
  input wire [2:0] memory_req_ready,
  output wire [98:0] memory_req_address,
  output wire [23:0] memory_req_burstcount,
  input wire [2:0] memory_rsp_valid, memory_rsp_error,
  input wire [1535:0] memory_rsp_rdata,
  output wire [63:0] qweight_read_beats, metadata_read_beats, bias_read_beats,
  output wire [63:0] activation_read_columns,
  output wire [63:0] retained_column_beats, skipped_column_beats
);
  localparam [127:0] H=128'(HIDDEN_SIZE), I=128'(INTERMEDIATE_SIZE);
  localparam [127:0] KD=128'(NUM_KV_HEADS)*128'(HEAD_DIM);
  localparam GS=(GROUP_SIZE==8 || GROUP_SIZE==16 || GROUP_SIZE==32 ||
    GROUP_SIZE==64 || GROUP_SIZE==128) ? GROUP_SIZE : 8;
  localparam GSHIFT=$clog2(GS);
  function automatic [127:0] matrix_inputs(input integer p);
    matrix_inputs=p==6 ? I : H;
  endfunction
  function automatic [127:0] matrix_outputs(input integer p);
    matrix_outputs=p==1 || p==2 ? KD : p==4 || p==5 ? I : H;
  endfunction
  function automatic [127:0] matrix_bytes(input integer kind, p);
    reg [127:0] n,m,packed_stride,bytes;
    begin
      n=matrix_inputs(p); m=matrix_outputs(p);
      packed_stride=((m+7)>>3)<<2;
      if (kind==1) bytes=n*packed_stride;
      else if (kind==2) bytes=((n+GS-1)>>GSHIFT)*packed_stride;
      else bytes=((n+GS-1)>>GSHIFT)*m*2;
      matrix_bytes=(bytes+63)&128'hffffffffffffffffffffffffffffffc0;
    end
  endfunction
  function automatic [127:0] matrix_offset(input integer kind, p);
    reg [127:0] bytes;
    integer j;
    begin
      bytes=0;
      for (j=0;j<7;j=j+1)
        if (j<p) bytes=bytes+matrix_bytes(kind,j);
      matrix_offset=bytes;
    end
  endfunction
  localparam [127:0] QW_LAYER=matrix_offset(1,7);
  localparam [127:0] QZ_LAYER=matrix_offset(2,7);
  localparam [127:0] SC_LAYER=matrix_offset(3,7);
  localparam [127:0] BIAS_LAYER=(H+2*KD)*2;
  localparam LEGAL=NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_KV_HEADS>0 && HEAD_DIM>0 && (HEAD_DIM&1)==0 &&
    128'(NUM_Q_HEADS)==8*128'(NUM_KV_HEADS) && H==128'(NUM_Q_HEADS)*128'(HEAD_DIM) &&
    GROUP_SIZE==GS && (HIDDEN_SIZE&7)==0 && (INTERMEDIATE_SIZE&7)==0 &&
    (HIDDEN_SIZE&(GS-1))==0 && (INTERMEDIATE_SIZE&(GS-1))==0 &&
    VOCAB_SIZE>0 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    H<=128'hffffffff && I<=128'hffffffff &&
    128'(NUM_LAYERS)*QW_LAYER<=128'h60000000 &&
    128'(NUM_LAYERS)*QZ_LAYER<=128'h04000000 &&
    128'(NUM_LAYERS)*SC_LAYER<=128'h08000000 &&
    128'(NUM_LAYERS)*BIAS_LAYER<=128'h01000000;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: batched projection geometry or image extent");
    assign cmd_ready=0; assign done=0; assign error=0; assign idle=0;
    assign fault=0; assign drain_done=0; assign scratch_req_valid=0;
    assign scratch_req_write=0; assign scratch_req_node=0; assign scratch_req_mask=0;
    assign scratch_req_slot=0; assign scratch_req_index=0; assign scratch_req_wdata=0;
    assign scratch_rsp_ready=0; assign memory_req_valid=0;
    assign memory_req_address=0; assign memory_req_burstcount=0;
    assign qweight_read_beats=0; assign metadata_read_beats=0; assign bias_read_beats=0;
    assign activation_read_columns=0; assign retained_column_beats=0;
    assign skipped_column_beats=0;
  end else begin: datapath
    localparam MAX_INPUTS=HIDDEN_SIZE>INTERMEDIATE_SIZE ? HIDDEN_SIZE : INTERMEDIATE_SIZE;
    localparam IDLE=0, LOCAL_FLUSH=1, LOCAL_DRAIN=2, MAP_PRODUCT=3, MAP_OFFSET=4,
      MAP_BASE=5, BLOCK_META=6, META_LOAD=7, DMA_COMMAND=8, ACT_REQUEST=9,
      ACT_RETURN=10, ACT_CONVERT=11, ACT_CONVERT_WAIT=12, ACT_FEED=13,
      DESCRIPTOR=14, WEIGHT_WAIT=15, META_QUERY=16, META_RETURN=17,
      RESULT_WAIT=18, OUT_READ=19, OUT_SELECT=20, OUT_CONVERT=21,
      OUT_CONVERT_WAIT=22, BIAS_ROW=23, BIAS_ADDRESS=24, BIAS_REQUEST=25,
      BIAS_RETURN=26, BIAS_DECODE=27, BIAS_ADD=28, BIAS_SATURATE=29,
      WRITE_FIND=30, WRITE_REQUEST=31, WRITE_RETURN=32, NEXT_OUTPUT=33,
      COMPLETE=34, FAIL_FLUSH=35, FAIL_DRAIN=36, FAIL_DONE=37, FAULTED=38,
      CANCEL_DRAIN=39, CANCEL_DONE=40;
    reg [5:0] state;
    reg failed, sparse, dma_completed, scratch_pending, bias_pending;
    reg [31:0] epoch, layer, inputs, outputs, source_slot, target_slot;
    reg [31:0] row_base, input_column, output_row, output_index;
    reg [2:0] projection;
    reg [3:0] token_mask;
    reg [15:0] threshold, bias_f16;
    reg [1:0] write_node;
    reg [127:0] activation_q16, output_f32, output_q16;
    reg [63:0] activation_f16;
    reg signed [31:0] bias_q16;
    reg signed [32:0] biased [0:3];
    reg [63:0] qw_product,qz_product,sc_product,bias_product;
    reg [63:0] qw_offset,qz_offset,sc_offset,bias_offset;
    reg [32:0] qweight_base,qzero_base,scale_base,bias_base,bias_address;
    reg [63:0] qw_count,meta_count,bias_count,activation_count,retained_count,skip_count;
    reg [63:0] selected_qw_offset,selected_qz_offset,selected_sc_offset;
    wire [31:0] block_rows=outputs-row_base<128 ? outputs-row_base : 32'd128;
    wire [31:0] packed_outputs=32'((({32'd0,outputs}+64'd7)>>3)<<3);
    wire running=rst_n && !flush;
    wire unit_flush=flush || state==LOCAL_FLUSH || state==FAIL_FLUSH;
    wire active=running && !unit_flush && !failed &&
      state!=CANCEL_DRAIN && state!=CANCEL_DONE;
    wire dma_cmd_ready,dma_act_ready,dma_tile_valid,dma_weight_valid,dma_weight_ready;
    wire dma_done,dma_error,dma_idle,dma_drained,dma_fault;
    wire [31:0] dma_columns,dma_weight_column,dma_scanned,dma_skipped,dma_issued;
    wire [127:0] dma_row_mask;
    wire [127:0] true_row_mask, tile_row_mask;
    wire [511:0] dma_weight;
    wire [63:0] dma_activation;
    wire [3:0] dma_keep;
    wire dma_last,dma_mem_valid;
    wire [32:0] dma_mem_address;
    wire [7:0] dma_mem_burstcount;
    wire meta_cmd_ready,meta_done,meta_error,meta_idle,meta_fault,meta_drained;
    wire meta_query_ready,meta_valid,meta_operand_error,meta_operand_ready,meta_mem_valid;
    wire [511:0] meta_zero;
    wire [2047:0] meta_scale;
    wire [32:0] meta_mem_address;
    wire [7:0] meta_mem_burstcount;
    wire [31:0] meta_issued;
    wire mac_cmd_ready,mac_in_ready,mac_valid,mac_error,mac_idle,mac_fault;
    wire [31:0] mac_epoch,mac_layer,mac_row_base;
    wire [2:0] mac_projection;
    wire [3:0] mac_token_mask;
    wire [127:0] mac_row_mask;
    wire [16383:0] mac_sums;
    wire [3:0] a_valid,a_error,q_valid,q_error;
    wire [63:0] a_result;
    wire [127:0] q_result;
    wire [31:0] result_q [0:3][0:15];
    wire scratch_fire=scratch_req_valid && scratch_req_ready;
    wire scratch_known=scratch_pending || scratch_fire;
    wire scratch_return=scratch_rsp_valid && scratch_rsp_ready;
    wire bias_fire=memory_req_valid[2] && memory_req_ready[2];
    wire bias_known=bias_pending || bias_fire;
    wire bias_return=memory_rsp_valid[2] && bias_known;
    wire descriptor_fire=active && state==DESCRIPTOR && dma_tile_valid && mac_cmd_ready;
    wire weight_fire=active && state==META_RETURN && dma_weight_valid &&
      meta_valid && !meta_operand_error && mac_in_ready;
    wire mac_out_ready=active && state==RESULT_WAIT && (dma_completed || dma_done);
    wire result_fire=mac_valid && mac_out_ready;
    wire scratch_bad=scratch_rsp_valid && (!scratch_known ||
      scratch_rsp_error || ((state==ACT_RETURN || state==ACT_REQUEST) &&
        (scratch_rsp_mask!=token_mask || scratch_rsp_node!=0)) ||
      ((state==WRITE_RETURN || state==WRITE_REQUEST) &&
        (scratch_rsp_mask!=(4'b0001<<write_node) || scratch_rsp_node!=write_node)));
    wire result_bad=mac_valid && (mac_error || mac_epoch!=epoch || mac_layer!=layer ||
      mac_projection!=projection || mac_row_base!=row_base ||
      mac_token_mask!=token_mask || mac_row_mask!=dma_row_mask_saved);
    reg [127:0] dma_row_mask_saved;
    reg classification_bad;
    wire local_fault=active && (scratch_bad ||
      (memory_rsp_valid[2] && !bias_known) || memory_rsp_error[2] ||
      dma_fault || meta_fault || mac_fault || (dma_done && dma_error) ||
      meta_error || (meta_valid && meta_operand_error) || result_bad ||
      (state==ACT_CONVERT_WAIT && |(a_error&token_mask)) ||
      (state==OUT_CONVERT_WAIT && |(q_error&token_mask)) ||
      classification_bad);
    wire all_drained=dma_idle && meta_idle && mac_idle &&
      !scratch_pending && !bias_pending;
    wire signed [31:0] decoded_bias=anvil_q3_pkg::f16_q16(bias_f16);
    integer t;

    for (genvar r=0;r<128;r=r+1) begin: true_rows
      assign true_row_mask[r]=r<block_rows;
    end
    assign tile_row_mask=dma_row_mask & true_row_mask;

    always @* begin
      classification_bad=state==BIAS_DECODE && anvil_q3_pkg::f16_invalid(bias_f16);
`ifndef SYNTHESIS
      if (scratch_rsp_valid &&
          (^{scratch_rsp_error,scratch_rsp_node,scratch_rsp_mask})===1'bx)
        classification_bad=1;
      if (mac_valid &&
          (^{mac_error,mac_epoch,mac_layer,mac_row_base,mac_projection,
              mac_token_mask,mac_row_mask})===1'bx) classification_bad=1;
      if (state==BIAS_DECODE && (^bias_f16)===1'bx) classification_bad=1;
`endif
    end

    always @* begin
      selected_qw_offset=0; selected_qz_offset=0; selected_sc_offset=0;
      case (projection)
        0: begin
          selected_qw_offset=64'(matrix_offset(1,0));
          selected_qz_offset=64'(matrix_offset(2,0));
          selected_sc_offset=64'(matrix_offset(3,0));
        end
        1: begin
          selected_qw_offset=64'(matrix_offset(1,1));
          selected_qz_offset=64'(matrix_offset(2,1));
          selected_sc_offset=64'(matrix_offset(3,1));
        end
        2: begin
          selected_qw_offset=64'(matrix_offset(1,2));
          selected_qz_offset=64'(matrix_offset(2,2));
          selected_sc_offset=64'(matrix_offset(3,2));
        end
        3: begin
          selected_qw_offset=64'(matrix_offset(1,3));
          selected_qz_offset=64'(matrix_offset(2,3));
          selected_sc_offset=64'(matrix_offset(3,3));
        end
        4: begin
          selected_qw_offset=64'(matrix_offset(1,4));
          selected_qz_offset=64'(matrix_offset(2,4));
          selected_sc_offset=64'(matrix_offset(3,4));
        end
        5: begin
          selected_qw_offset=64'(matrix_offset(1,5));
          selected_qz_offset=64'(matrix_offset(2,5));
          selected_sc_offset=64'(matrix_offset(3,5));
        end
        default: begin
          selected_qw_offset=64'(matrix_offset(1,6));
          selected_qz_offset=64'(matrix_offset(2,6));
          selected_sc_offset=64'(matrix_offset(3,6));
        end
      endcase
    end

    assign cmd_ready=running && !failed && state==IDLE &&
      !scratch_pending && !bias_pending && !(|memory_rsp_valid) && !scratch_rsp_valid;
    assign done=running && (state==COMPLETE || state==FAIL_DONE);
    assign error=done && failed;
    assign idle=cmd_ready;
    assign fault=running && failed;
    assign drain_done=running && (state==CANCEL_DONE || state==IDLE);
    assign scratch_req_valid=active && !scratch_pending &&
      (state==ACT_REQUEST || state==WRITE_REQUEST);
    assign scratch_req_write=scratch_req_valid && state==WRITE_REQUEST;
    assign scratch_req_node=scratch_req_write ? write_node : 2'd0;
    assign scratch_req_mask=!scratch_req_valid ? 4'd0 :
      scratch_req_write ? (4'b0001<<write_node) : token_mask;
    assign scratch_req_slot=!scratch_req_valid ? 32'd0 :
      scratch_req_write ? target_slot : source_slot;
    assign scratch_req_index=!scratch_req_valid ? 32'd0 :
      scratch_req_write ? output_index : input_column;
    assign scratch_req_wdata=scratch_req_write ?
      $signed(output_q16[write_node*32+:32]) : 32'sd0;
    assign scratch_rsp_ready=running && (scratch_pending || scratch_fire);
    assign memory_req_valid={active && state==BIAS_REQUEST && !bias_pending,
      meta_mem_valid,dma_mem_valid};
    assign memory_req_address={memory_req_valid[2] ? {bias_address[32:6],6'd0} : 33'd0,
      meta_mem_address,dma_mem_address};
    assign memory_req_burstcount={memory_req_valid[2] ? 8'd1 : 8'd0,
      meta_mem_burstcount,dma_mem_burstcount};
    assign qweight_read_beats=running ? qw_count : 64'd0;
    assign metadata_read_beats=running ? meta_count : 64'd0;
    assign bias_read_beats=running ? bias_count : 64'd0;
    assign activation_read_columns=running ? activation_count : 64'd0;
    assign retained_column_beats=running ? retained_count : 64'd0;
    assign skipped_column_beats=running ? skip_count : 64'd0;
    assign dma_weight_ready=active && state==META_RETURN && meta_valid &&
      !meta_operand_error && mac_in_ready;
    assign meta_operand_ready=active && state==META_RETURN && dma_weight_valid &&
      mac_in_ready;

    anvil_q3_ht2_sparse_dma #(.MAX_COLUMNS(MAX_INPUTS),.RETAIN_SCAN(1)) sparse_dma (
      .clk(clk),.rst_n(rst_n),.flush(unit_flush),
      .cmd_valid(active && state==DMA_COMMAND),.cmd_ready(dma_cmd_ready),
      .cmd_epoch(epoch),.cmd_layer(layer),.cmd_proj(projection),
      .cmd_qweight_base(qweight_base),.cmd_output_count(packed_outputs),.cmd_row_base(row_base),
      .cmd_columns(inputs),.cmd_token_mask(token_mask),
      .cmd_sparse_enable(sparse),.cmd_threshold_f16(threshold),
      .act_valid(active && state==ACT_FEED),.act_ready(dma_act_ready),
      .act_column(input_column),.act_f16(activation_f16),
      .tile_valid(dma_tile_valid),.tile_ready(active && state==DESCRIPTOR && mac_cmd_ready),
      .tile_columns(dma_columns),.tile_row_mask(dma_row_mask),
      .memory_req_valid(dma_mem_valid),.memory_req_ready(memory_req_ready[0]),
      .memory_req_address(dma_mem_address),.memory_req_burstcount(dma_mem_burstcount),
      .memory_rsp_valid(memory_rsp_valid[0]),.memory_rsp_error(memory_rsp_error[0]),
      .memory_rsp_rdata(memory_rsp_rdata[511:0]),
      .weight_valid(dma_weight_valid),.weight_ready(dma_weight_ready),
      .weight_column(dma_weight_column),.weight_data(dma_weight),
      .weight_activation_f16(dma_activation),.weight_keep_mask(dma_keep),
      .weight_last(dma_last),.done(dma_done),.error(dma_error),
      .idle(dma_idle),.drain_done(dma_drained),.fault(dma_fault),
      .scanned_columns(dma_scanned),.skipped_columns(dma_skipped),
      .issued_weight_beats(dma_issued)
    );
    anvil_q3_ht2_projection_metadata #(
      .MAX_INPUTS(MAX_INPUTS),.GROUP_SIZE(GROUP_SIZE)
    ) resident_metadata (
      .clk(clk),.rst_n(rst_n),.flush(unit_flush),
      .cmd_valid(active && state==BLOCK_META),.cmd_ready(meta_cmd_ready),
      .cmd_qzeros_base(qzero_base),.cmd_scales_base(scale_base),
      .cmd_inputs(inputs),.cmd_outputs(outputs),.cmd_row_base(row_base),
      .done(meta_done),.error(meta_error),.idle(meta_idle),
      .fault(meta_fault),.drain_done(meta_drained),
      .query_valid(active && state==META_QUERY),.query_ready(meta_query_ready),
      .query_column(dma_weight_column),.operand_valid(meta_valid),
      .operand_ready(meta_operand_ready),.operand_error(meta_operand_error),
      .operand_qzero(meta_zero),.operand_scale_f16(meta_scale),
      .memory_req_valid(meta_mem_valid),.memory_req_ready(memory_req_ready[1]),
      .memory_req_address(meta_mem_address),.memory_req_burstcount(meta_mem_burstcount),
      .memory_rsp_valid(memory_rsp_valid[1]),.memory_rsp_error(memory_rsp_error[1]),
      .memory_rsp_rdata(memory_rsp_rdata[1023:512]),.issued_metadata_beats(meta_issued)
    );
    anvil_q3_ht2_tile_batch_mac #(
      .K(4),.WEIGHT_LANES(128),.NUM_LAYERS(NUM_LAYERS),
      .HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM)
    ) tile_batch_mac (
      .clk(clk),.rst_n(rst_n),.flush(unit_flush),
      .cmd_valid(active && state==DESCRIPTOR && dma_tile_valid),.cmd_ready(mac_cmd_ready),
      .cmd_epoch(epoch),.cmd_layer(layer),.cmd_proj(projection),
      .cmd_row_base(row_base),.cmd_columns(dma_columns),
      .cmd_token_mask(token_mask),.cmd_row_mask(tile_row_mask),
      .in_valid(active && state==META_RETURN && dma_weight_valid &&
        meta_valid && !meta_operand_error),.in_ready(mac_in_ready),
      .in_column(dma_weight_column),.in_qweight(dma_weight),.in_qzero(meta_zero),
      .in_scale_f16(meta_scale),.in_activation_f16(dma_activation),
      .in_keep_mask(dma_keep),.in_last(dma_last),
      .out_valid(mac_valid),.out_ready(mac_out_ready),.out_error(mac_error),
      .out_epoch(mac_epoch),.out_layer(mac_layer),.out_proj(mac_projection),
      .out_row_base(mac_row_base),.out_token_mask(mac_token_mask),
      .out_row_mask(mac_row_mask),.out_sum_f32(mac_sums),.idle(mac_idle),.fault(mac_fault)
    );
    for (genvar n=0;n<4;n=n+1) begin: token_boundary
      anvil_q3_ht2_q16_to_f16 activation_converter (
        .clk(clk),.rst_n(rst_n),.flush(unit_flush),.enable(1'b1),
        .in_valid(active && state==ACT_CONVERT && token_mask[n]),
        .in_q16($signed(activation_q16[n*32+:32])),
        .out_valid(a_valid[n]),.out_error(a_error[n]),.out_f16(a_result[n*16+:16])
      );
      anvil_q3_ht2_f32_to_q16 result_converter (
        .clk(clk),.rst_n(rst_n),.flush(unit_flush),.enable(1'b1),
        .in_valid(active && state==OUT_CONVERT && token_mask[n]),
        .in_f32(output_f32[n*32+:32]),
        .out_valid(q_valid[n]),.out_error(q_error[n]),.out_q16(q_result[n*32+:32])
      );
      for (genvar b=0;b<16;b=b+1) begin: result_bank
        reg [255:0] sums;
        reg [31:0] read_sum;
        assign result_q[n][b]=read_sum;
        always @(posedge clk) begin
          if (result_fire && !local_fault && !mac_error) begin
            for (integer j=0;j<8;j=j+1)
              sums[j*32+:32]<=mac_sums[(n*128+b*8+j)*32+:32];
          end
          if (active && state==OUT_READ)
            read_sum<=sums[{output_row[2:0],5'd0}+:32];
        end
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; sparse<=0; dma_completed<=0;
        scratch_pending<=0; bias_pending<=0; epoch<=0; layer<=0;
        inputs<=0; outputs<=0; source_slot<=0; target_slot<=0;
        row_base<=0; input_column<=0; output_row<=0; output_index<=0;
        projection<=0; token_mask<=0; threshold<=0; bias_f16<=0; write_node<=0;
        activation_q16<=0; output_f32<=0; output_q16<=0; activation_f16<=0;
        bias_q16<=0; qw_product<=0; qz_product<=0; sc_product<=0; bias_product<=0;
        qw_offset<=0; qz_offset<=0; sc_offset<=0; bias_offset<=0;
        qweight_base<=0; qzero_base<=0; scale_base<=0; bias_base<=0; bias_address<=0;
        qw_count<=0; meta_count<=0; bias_count<=0; activation_count<=0;
        retained_count<=0; skip_count<=0; dma_row_mask_saved<=0;
        for (t=0;t<4;t=t+1) biased[t]<=0;
      end else begin
        if (scratch_fire && !scratch_return) scratch_pending<=1;
        if (scratch_return && scratch_known) scratch_pending<=0;
        if (bias_fire && !memory_rsp_valid[2]) bias_pending<=1;
        if (memory_rsp_valid[2] && bias_known) bias_pending<=0;
        if (memory_req_valid[0] && memory_req_ready[0]) qw_count<=qw_count+1'b1;
        if (memory_req_valid[1] && memory_req_ready[1]) meta_count<=meta_count+1'b1;
        if (bias_fire) bias_count<=bias_count+1'b1;
        if (scratch_fire && !scratch_req_write) activation_count<=activation_count+1'b1;
        if (flush) begin
          state<=CANCEL_DRAIN; failed<=0; sparse<=0; dma_completed<=0;
          epoch<=0; layer<=0; inputs<=0; outputs<=0; source_slot<=0; target_slot<=0;
          row_base<=0; input_column<=0; output_row<=0; output_index<=0;
          projection<=0; token_mask<=0; threshold<=0; bias_f16<=0; write_node<=0;
          activation_q16<=0; output_f32<=0; output_q16<=0; activation_f16<=0;
          bias_q16<=0; qw_product<=0; qz_product<=0; sc_product<=0; bias_product<=0;
          qw_offset<=0; qz_offset<=0; sc_offset<=0; bias_offset<=0;
          qweight_base<=0; qzero_base<=0; scale_base<=0; bias_base<=0; bias_address<=0;
          qw_count<=0; meta_count<=0; bias_count<=0; activation_count<=0;
          retained_count<=0; skip_count<=0; dma_row_mask_saved<=0;
          for (t=0;t<4;t=t+1) biased[t]<=0;
        end else if (local_fault) begin
          failed<=1; state<=FAIL_FLUSH;
        end else begin
          if (dma_done && !dma_error) dma_completed<=1;
          case (state)
            IDLE: if (cmd_valid && cmd_ready) begin
              epoch<=cmd_epoch; layer<=cmd_layer; projection<=cmd_proj;
              token_mask<=cmd_token_mask; sparse<=cmd_sparse_enable; threshold<=cmd_threshold_f16;
              inputs<=cmd_proj==6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
              outputs<=cmd_proj==1 || cmd_proj==2 ? NUM_KV_HEADS*HEAD_DIM :
                cmd_proj==4 || cmd_proj==5 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
              case (cmd_proj)
                0: begin source_slot<=1; target_slot<=2; end
                1: begin source_slot<=1; target_slot<=3; end
                2: begin source_slot<=1; target_slot<=4; end
                3: begin source_slot<=5; target_slot<=6; end
                4: begin source_slot<=8; target_slot<=9; end
                5: begin source_slot<=8; target_slot<=10; end
                default: begin source_slot<=11; target_slot<=12; end
              endcase
              row_base<=0; input_column<=0; output_row<=0;
              qw_count<=0; meta_count<=0; bias_count<=0; activation_count<=0;
              retained_count<=0; skip_count<=0; dma_completed<=0;
              if (cmd_layer>=NUM_LAYERS || cmd_proj>6 || cmd_token_mask==0 ||
                  cmd_threshold_f16[14:10]==31 ||
                  (cmd_threshold_f16[15] && cmd_threshold_f16[14:0]!=0)) begin
                failed<=1; state<=FAIL_FLUSH;
              end else state<=LOCAL_FLUSH;
`ifndef SYNTHESIS
              if ((^{cmd_epoch,cmd_layer,cmd_proj,cmd_token_mask,
                      cmd_sparse_enable,cmd_threshold_f16})===1'bx) begin
                failed<=1; state<=FAIL_FLUSH;
              end
`endif
            end
            LOCAL_FLUSH: state<=LOCAL_DRAIN;
            LOCAL_DRAIN: if (all_drained) state<=MAP_PRODUCT;
            MAP_PRODUCT: begin
              qw_product<={32'd0,layer}*64'(QW_LAYER);
              qz_product<={32'd0,layer}*64'(QZ_LAYER);
              sc_product<={32'd0,layer}*64'(SC_LAYER);
              bias_product<={32'd0,layer}*64'(BIAS_LAYER);
              state<=MAP_OFFSET;
            end
            MAP_OFFSET: begin
              qw_offset<=qw_product+selected_qw_offset;
              qz_offset<=qz_product+selected_qz_offset;
              sc_offset<=sc_product+selected_sc_offset;
              bias_offset<=bias_product+
                (projection==0 ? 64'd0 : projection==1 ? 64'(H*2) : 64'((H+KD)*2));
              state<=MAP_BASE;
            end
            MAP_BASE: begin
              qweight_base<=33'(qw_offset);
              qzero_base<=33'(64'h60000000+qz_offset);
              scale_base<=33'(64'h64000000+sc_offset);
              bias_base<=33'(64'h6c000000+bias_offset);
              state<=BLOCK_META;
            end
            BLOCK_META: if (meta_cmd_ready) state<=META_LOAD;
            META_LOAD: if (meta_done) state<=DMA_COMMAND;
            DMA_COMMAND: if (dma_cmd_ready) begin
              dma_completed<=0;
              if (row_base==0) state<=ACT_REQUEST;
              else state<=DESCRIPTOR;
            end
            ACT_REQUEST: if (scratch_fire) begin
              if (scratch_return) begin activation_q16<=scratch_rsp_rdata; state<=ACT_CONVERT; end
              else state<=ACT_RETURN;
            end
            ACT_RETURN: if (scratch_return) begin
              activation_q16<=scratch_rsp_rdata; state<=ACT_CONVERT;
            end
            ACT_CONVERT: state<=ACT_CONVERT_WAIT;
            ACT_CONVERT_WAIT: if ((a_valid&token_mask)==token_mask) begin
              activation_f16<=a_result; state<=ACT_FEED;
            end
            ACT_FEED: if (dma_act_ready) begin
              if (input_column+1'b1==inputs) state<=DESCRIPTOR;
              else begin input_column<=input_column+1'b1; state<=ACT_REQUEST; end
            end
            DESCRIPTOR: if (descriptor_fire) begin
              dma_row_mask_saved<=tile_row_mask;
              retained_count<=retained_count+{32'd0,dma_columns};
              skip_count<=skip_count+{32'd0,dma_skipped};
              if (dma_columns==0) state<=RESULT_WAIT;
              else state<=WEIGHT_WAIT;
            end
            WEIGHT_WAIT: if (dma_weight_valid) state<=META_QUERY;
            META_QUERY: if (meta_query_ready) state<=META_RETURN;
            META_RETURN: if (weight_fire) begin
              if (dma_last) state<=RESULT_WAIT;
              else state<=WEIGHT_WAIT;
            end
            RESULT_WAIT: if (result_fire) begin output_row<=0; state<=OUT_READ; end
            OUT_READ: state<=OUT_SELECT;
            OUT_SELECT: begin
              for (t=0;t<4;t=t+1)
                output_f32[t*32+:32]<=result_q[t][output_row[6:3]];
              state<=OUT_CONVERT;
            end
            OUT_CONVERT: state<=OUT_CONVERT_WAIT;
            OUT_CONVERT_WAIT: if ((q_valid&token_mask)==token_mask) begin
              output_q16<=q_result;
              write_node<=0;
              if (projection<=2) state<=BIAS_ROW;
              else begin output_index<=row_base+output_row; state<=WRITE_FIND; end
            end
            BIAS_ROW: begin output_index<=row_base+output_row; state<=BIAS_ADDRESS; end
            BIAS_ADDRESS: begin
              bias_address<=bias_base+33'({1'b0,output_index}<<1);
              state<=BIAS_REQUEST;
            end
            BIAS_REQUEST: if (bias_fire) begin
              if (bias_return) begin
                bias_f16<=memory_rsp_rdata[1024+{bias_address[5:1],4'd0}+:16];
                state<=BIAS_DECODE;
              end else state<=BIAS_RETURN;
            end
            BIAS_RETURN: if (bias_return) begin
              bias_f16<=memory_rsp_rdata[1024+{bias_address[5:1],4'd0}+:16];
              state<=BIAS_DECODE;
            end
            BIAS_DECODE: begin bias_q16<=decoded_bias; state<=BIAS_ADD; end
            BIAS_ADD: begin
              for (t=0;t<4;t=t+1)
                biased[t]<=$signed({output_q16[t*32+31],output_q16[t*32+:32]})+
                  $signed({bias_q16[31],bias_q16});
              state<=BIAS_SATURATE;
            end
            BIAS_SATURATE: begin
              for (t=0;t<4;t=t+1) begin
                if (biased[t]>33'sd2147483647) output_q16[t*32+:32]<=32'h7fffffff;
                else if (biased[t]< -33'sd2147483648) output_q16[t*32+:32]<=32'h80000000;
                else output_q16[t*32+:32]<=biased[t][31:0];
              end
              state<=WRITE_FIND;
            end
            WRITE_FIND: begin
              if (token_mask[write_node]) state<=WRITE_REQUEST;
              else if (write_node==3) state<=NEXT_OUTPUT;
              else write_node<=write_node+1'b1;
            end
            WRITE_REQUEST: if (scratch_fire) begin
              if (!scratch_return) state<=WRITE_RETURN;
              else if (write_node==3) state<=NEXT_OUTPUT;
              else begin write_node<=write_node+1'b1; state<=WRITE_FIND; end
            end
            WRITE_RETURN: if (scratch_return) begin
              if (write_node==3) state<=NEXT_OUTPUT;
              else begin write_node<=write_node+1'b1; state<=WRITE_FIND; end
            end
            NEXT_OUTPUT: begin
              if (output_row+1'b1<block_rows) begin
                output_row<=output_row+1'b1; state<=OUT_READ;
              end else if (row_base+block_rows==outputs) state<=COMPLETE;
              else begin row_base<=row_base+block_rows; state<=BLOCK_META; end
            end
            COMPLETE: state<=IDLE;
            FAIL_FLUSH: state<=FAIL_DRAIN;
            FAIL_DRAIN: if (all_drained) state<=FAIL_DONE;
            FAIL_DONE: state<=FAULTED;
            FAULTED: state<=FAULTED;
            CANCEL_DRAIN: if (all_drained) state<=CANCEL_DONE;
            CANCEL_DONE: state<=IDLE;
            default: begin failed<=1; state<=FAIL_FLUSH; end
          endcase
        end
      end
    end
  end endgenerate
endmodule
