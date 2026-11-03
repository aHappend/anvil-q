module anvil_q3_ht2_top #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter BANKS=16, LANES_PER_BANK=16, CACHE_MODE=1, INT4_ASYM=0,
  parameter TILE_K=128, TILE_ROWS=8, TILE_SLOTS=4,
  parameter QUEUE_DEPTH=3, BURST_BEATS=16, KV_RESIDENT_GROUPS=64
) (
  input wire clk, rst_n, cancel, token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence, token_phase, logit_ready, ddr_cal_ready, model_commit,
  output wire logit_valid,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire done, error, cancel_done, model_ready,
  input wire host_req_valid, host_req_write,
  input wire [32:0] host_req_address,
  input wire [511:0] host_req_wdata,
  input wire [63:0] host_req_byteenable,
  input wire host_rsp_ready,
  output wire host_req_ready, host_rsp_valid,
  output wire [511:0] host_rsp_rdata,
  output wire host_rsp_error,
  output wire [32:0] avm_address,
  output wire avm_read, avm_write,
  output wire [511:0] avm_writedata,
  output wire [63:0] avm_byteenable,
  output wire [7:0] avm_burstcount,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid,
  input wire [1:0] avm_response,
  input wire ht2_enable, sparse_enable,
  input wire [15:0] sparse_threshold_f16,
  input wire spec_req_valid,
  output wire spec_req_ready,
  input wire [31:0] spec_req_id, spec_base_pos,
  input wire [3:0] draft_mask,
  input wire [127:0] draft_tokens,
  input wire [11:0] draft_parents,
  output wire spec_rsp_valid,
  input wire spec_rsp_ready,
  output wire [31:0] spec_rsp_id,
  output wire spec_rsp_error,
  output wire [3:0] accepted_mask,
  output wire [2:0] accepted_count,
  output wire [127:0] accepted_tokens,
  output wire [31:0] next_token, committed_pos
);
  localparam GS=(GROUP_SIZE==8 || GROUP_SIZE==16 || GROUP_SIZE==32 ||
    GROUP_SIZE==64 || GROUP_SIZE==128) ? GROUP_SIZE : 8;
  localparam [127:0] H=128'(HIDDEN_SIZE), I=128'(INTERMEDIATE_SIZE);
  localparam [127:0] KD=128'(NUM_KV_HEADS)*128'(HEAD_DIM);
  localparam CAP=CACHE_MODE==2 ? 64 : CACHE_MODE==1 ? 32 : 16;
  function automatic [127:0] packed_extent(input integer kind);
    reg [127:0] n, m, packed_stride, bytes, total;
    begin
      total=0;
      for (integer p=0;p<7;p=p+1) begin
        n=p==6 ? I : H;
        m=p==1 || p==2 ? KD : p==4 || p==5 ? I : H;
        packed_stride=((m+7)>>3)<<2;
        if (kind==0) bytes=n*packed_stride;
        else if (kind==1) bytes=(n>>$clog2(GS))*packed_stride;
        else bytes=(n>>$clog2(GS))*m*2;
        total=total+((bytes+63)&128'hffffffffffffffffffffffffffffffc0);
      end
      packed_extent=total*128'(NUM_LAYERS);
    end
  endfunction
  localparam [127:0] KV_BYTES=128'(NUM_LAYERS)*2*128'(NUM_KV_HEADS)*
    ((128'(HEAD_DIM)+CAP-1)>>$clog2(CAP))*64*
    (128'(MAX_SEQ_LEN)+(CACHE_MODE==0 ? 0 : 4));
  localparam LEGAL=NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_KV_HEADS>0 && HEAD_DIM>0 && (HEAD_DIM&1)==0 &&
    128'(NUM_Q_HEADS)==8*128'(NUM_KV_HEADS) &&
    H==128'(NUM_Q_HEADS)*128'(HEAD_DIM) && GROUP_SIZE==GS &&
    (HIDDEN_SIZE&7)==0 && (INTERMEDIATE_SIZE&7)==0 &&
    (HIDDEN_SIZE&(GS-1))==0 && (INTERMEDIATE_SIZE&(GS-1))==0 &&
    VOCAB_SIZE>0 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    (BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8 || BANKS==16) &&
    LANES_PER_BANK==16 && AWQ_BITS==4 && CACHE_MODE>=0 && CACHE_MODE<=2 &&
    INT4_ASYM==0 && (TILE_K==16 || TILE_K==32 || TILE_K==64 || TILE_K==128) &&
    TILE_ROWS>=1 && TILE_ROWS<=8 && TILE_SLOTS>=2 && TILE_SLOTS<=4 &&
    QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    (BURST_BEATS==1 || BURST_BEATS==2 || BURST_BEATS==4 ||
      BURST_BEATS==8 || BURST_BEATS==16) &&
    KV_RESIDENT_GROUPS>=1 && KV_RESIDENT_GROUPS<=256 &&
    H<=128'hffffffff && I<=128'hffffffff &&
    packed_extent(0)<=128'h60000000 && packed_extent(1)<=128'h04000000 &&
    packed_extent(2)<=128'h08000000 &&
    128'(NUM_LAYERS)*(H+2*KD)*2<=128'h01000000 &&
    (2*128'(NUM_LAYERS)+1)*H*2<=128'h01000000 &&
    128'(MAX_SEQ_LEN)*128'(HEAD_DIM)*4<=128'h12000000 &&
    ((128'(VOCAB_SIZE)*H*2+63)&128'hffffffffffffffffffffffffffffffc0)<=128'h40000000 &&
    (10*H+3*I+2*KD)*16<=128'h3e000000 && KV_BYTES<=128'h100000000;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: top geometry, image/cache extent or transport");
    assign token_ready=0; assign logit_valid=0; assign logit_index=0; assign logit_data=0;
    assign done=0; assign error=0; assign cancel_done=0; assign model_ready=0;
    assign host_req_ready=0; assign host_rsp_valid=0; assign host_rsp_rdata=0;
    assign host_rsp_error=0; assign avm_address=0; assign avm_read=0; assign avm_write=0;
    assign avm_writedata=0; assign avm_byteenable=0; assign avm_burstcount=0;
    assign spec_req_ready=0; assign spec_rsp_valid=0; assign spec_rsp_id=0;
    assign spec_rsp_error=0; assign accepted_mask=0; assign accepted_count=0;
    assign accepted_tokens=0; assign next_token=0; assign committed_pos=0;
  end else begin: datapath
    reg sequence_mode, legacy_busy, ht2_bus_owned;
    wire selected_mode=new_sequence ? ht2_enable : sequence_mode;
    wire legacy_token_ready, legacy_logit_valid, legacy_done, legacy_error, legacy_cancel_done;
    wire legacy_model_ready, legacy_host_ready, legacy_host_valid, legacy_host_error;
    wire [511:0] legacy_host_data;
    wire [31:0] legacy_logit_index;
    wire signed [31:0] legacy_logit_data;
    wire [32:0] legacy_address, ht2_address;
    wire legacy_read, legacy_write, ht2_read, ht2_write;
    wire [511:0] legacy_writedata, ht2_writedata;
    wire [63:0] legacy_byteenable, ht2_byteenable;
    wire [7:0] legacy_burstcount, ht2_burstcount;
    wire batch_ready, batch_idle, batch_done, batch_error, batch_cancel_done;
    wire batch_logit_valid;
    wire [31:0] batch_logit_index;
    wire signed [31:0] batch_logit_data;
    wire bus_idle, bus_fault, bus_drained, bus_flush;
    wire [6:0] req_valid, req_ready, req_write, rsp_valid, rsp_error;
    wire [230:0] req_address;
    wire [55:0] req_burstcount;
    wire [3583:0] req_wdata, rsp_rdata;
    wire [447:0] req_byteenable;
    wire host_available=rst_n && !ht2_bus_owned;
    wire quiet_legacy=!legacy_busy && !legacy_read && !legacy_write &&
      !legacy_host_valid && legacy_host_ready && !host_req_valid && !model_commit;
    wire batch_enable=legacy_model_ready && ddr_cal_ready && quiet_legacy &&
      !legacy_busy && !ht2_bus_owned;
    wire ordinary_ht2=token_valid && selected_mode;
    wire legacy_token_valid=token_valid && !selected_mode && !ht2_bus_owned;
    wire ht2_token_fire=ordinary_ht2 && token_ready;
    wire legacy_token_fire=legacy_token_valid && token_ready;
    wire speculative_fire=spec_req_valid && spec_req_ready;
    wire invalidate=host_req_valid && host_req_ready && host_req_write;

    assign token_ready=rst_n && !cancel && (selected_mode ?
      batch_ready && batch_enable : legacy_token_ready && !ht2_bus_owned);
    assign model_ready=legacy_model_ready;
    assign host_req_ready=host_available && legacy_host_ready;
    assign host_rsp_valid=host_available && legacy_host_valid;
    assign host_rsp_rdata=host_rsp_valid ? legacy_host_data : 512'd0;
    assign host_rsp_error=host_rsp_valid && legacy_host_error;
    assign logit_valid=rst_n && !cancel && (ht2_bus_owned ? batch_logit_valid : legacy_logit_valid);
    assign logit_index=logit_valid ? (ht2_bus_owned ? batch_logit_index : legacy_logit_index) : 32'd0;
    assign logit_data=logit_valid ? (ht2_bus_owned ? batch_logit_data : legacy_logit_data) : 32'sd0;
    assign done=rst_n && !cancel && (ht2_bus_owned ? batch_done : legacy_done);
    assign error=rst_n && !cancel && ((ht2_bus_owned ? batch_error : legacy_error) ||
      (ht2_bus_owned && model_commit));
    assign cancel_done=rst_n && !cancel &&
      (ht2_bus_owned || sequence_mode ? batch_cancel_done : legacy_cancel_done);
    assign avm_read=ht2_bus_owned ? ht2_read : legacy_read;
    assign avm_write=ht2_bus_owned ? ht2_write : legacy_write;
    assign avm_address=avm_read || avm_write ?
      (ht2_bus_owned ? ht2_address : legacy_address) : 33'd0;
    assign avm_writedata=avm_write ? (ht2_bus_owned ? ht2_writedata : legacy_writedata) : 512'd0;
    assign avm_byteenable=avm_read || avm_write ?
      (ht2_bus_owned ? ht2_byteenable : legacy_byteenable) : 64'd0;
    assign avm_burstcount=avm_read || avm_write ?
      (ht2_bus_owned ? ht2_burstcount : legacy_burstcount) : 8'd0;

    anvil_q3_ht_top #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
      .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
      .GROUP_SIZE(GROUP_SIZE),.AWQ_BITS(AWQ_BITS),.VOCAB_SIZE(VOCAB_SIZE),
      .MAX_SEQ_LEN(MAX_SEQ_LEN),.BANKS(BANKS),.LANES_PER_BANK(LANES_PER_BANK),
      .CACHE_MODE(CACHE_MODE),.INT4_ASYM(INT4_ASYM),.TILE_K(TILE_K),
      .TILE_ROWS(TILE_ROWS),.TILE_SLOTS(TILE_SLOTS),.QUEUE_DEPTH(QUEUE_DEPTH),
      .BURST_BEATS(BURST_BEATS),.KV_RESIDENT_GROUPS(KV_RESIDENT_GROUPS)
    ) legacy_core (
      .clk(clk),.rst_n(rst_n),.cancel(cancel && !sequence_mode && !ht2_bus_owned),
      .token_valid(legacy_token_valid),.token_ready(legacy_token_ready),
      .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),
      .token_phase(token_phase),.logit_ready(logit_ready && !ht2_bus_owned),
      .ddr_cal_ready(ddr_cal_ready && (!ht2_bus_owned || !model_commit)),
      .model_commit(model_commit),
      .logit_valid(legacy_logit_valid),.logit_index(legacy_logit_index),
      .logit_data(legacy_logit_data),.done(legacy_done),.error(legacy_error),
      .cancel_done(legacy_cancel_done),.model_ready(legacy_model_ready),
      .host_req_valid(host_req_valid && host_available),.host_req_write(host_req_write),
      .host_req_address(host_req_address),.host_req_wdata(host_req_wdata),
      .host_req_byteenable(host_req_byteenable),.host_rsp_ready(host_rsp_ready && host_available),
      .host_req_ready(legacy_host_ready),.host_rsp_valid(legacy_host_valid),
      .host_rsp_rdata(legacy_host_data),.host_rsp_error(legacy_host_error),
      .avm_address(legacy_address),.avm_read(legacy_read),.avm_write(legacy_write),
      .avm_writedata(legacy_writedata),.avm_byteenable(legacy_byteenable),
      .avm_burstcount(legacy_burstcount),
      .avm_waitrequest(ht2_bus_owned || avm_waitrequest),
      .avm_readdata(ht2_bus_owned ? 512'd0 : avm_readdata),
      .avm_readdatavalid(!ht2_bus_owned && avm_readdatavalid),
      .avm_response(ht2_bus_owned ? 2'd0 : avm_response)
    );
    if (CACHE_MODE==1 || CACHE_MODE==2) begin: compressed_ht2
      wire internal_spec_ready;
      assign spec_req_ready=sequence_mode && batch_enable && !token_valid && internal_spec_ready;
      anvil_q3_ht2_batch_controller #(
        .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
        .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
        .GROUP_SIZE(GROUP_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),
        .CACHE_MODE(CACHE_MODE),.KV_RESIDENT_GROUPS(KV_RESIDENT_GROUPS)
      ) batch_scheduler (
        .clk(clk),.rst_n(rst_n),.cancel(cancel && (sequence_mode || ht2_bus_owned)),
        .invalidate(invalidate || model_commit || legacy_token_fire),.run_enable(batch_enable),
        .memory_idle(bus_idle),.memory_fault(bus_fault),
        .token_valid(ordinary_ht2 && batch_enable),.token_ready(batch_ready),
        .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),
        .token_phase(token_phase),.sparse_enable(sparse_enable),
        .sparse_threshold_f16(sparse_threshold_f16),
        .logit_valid(batch_logit_valid),.logit_ready(logit_ready),
        .logit_index(batch_logit_index),.logit_data(batch_logit_data),
        .done(batch_done),.error(batch_error),.cancel_done(batch_cancel_done),
        .idle(batch_idle),.transport_flush(bus_flush),
        .spec_req_valid(spec_req_valid && sequence_mode && batch_enable && !token_valid),
        .spec_req_ready(internal_spec_ready),.spec_req_id(spec_req_id),
        .spec_base_pos(spec_base_pos),.draft_mask(draft_mask),
        .draft_tokens(draft_tokens),.draft_parents(draft_parents),
        .spec_rsp_valid(spec_rsp_valid),.spec_rsp_ready(spec_rsp_ready),
        .spec_rsp_id(spec_rsp_id),.spec_rsp_error(spec_rsp_error),
        .accepted_mask(accepted_mask),.accepted_count(accepted_count),
        .accepted_tokens(accepted_tokens),.next_token(next_token),.committed_pos(committed_pos),
        .memory_req_valid(req_valid),.memory_req_ready(req_ready),.memory_req_write(req_write),
        .memory_req_address(req_address),.memory_req_burstcount(req_burstcount),
        .memory_req_wdata(req_wdata),.memory_req_byteenable(req_byteenable),
        .memory_rsp_valid(rsp_valid),
        .memory_rsp_error(rsp_error | {7{ht2_bus_owned && model_commit}}),
        .memory_rsp_rdata(rsp_rdata)
      );
      anvil_q3_ht2_ddr_arbiter #(.CLIENTS(7)) shared_ddr (
        .clk(clk),.rst_n(rst_n),.flush(bus_flush),
        .c_req_valid(req_valid),.c_req_ready(req_ready),.c_req_write(req_write),
        .c_req_address(req_address),.c_req_wdata(req_wdata),
        .c_req_byteenable(req_byteenable),.c_req_burstcount(req_burstcount),
        .c_rsp_valid(rsp_valid),.c_rsp_error(rsp_error),.c_rsp_rdata(rsp_rdata),
        .idle(bus_idle),.fault(bus_fault),.drain_done(bus_drained),
        .avm_address(ht2_address),.avm_read(ht2_read),.avm_write(ht2_write),
        .avm_writedata(ht2_writedata),.avm_byteenable(ht2_byteenable),
        .avm_burstcount(ht2_burstcount),.avm_waitrequest(!ht2_bus_owned || avm_waitrequest),
        .avm_readdata(ht2_bus_owned ? avm_readdata : 512'd0),
        .avm_readdatavalid(ht2_bus_owned && avm_readdatavalid),
        .avm_response(ht2_bus_owned ? avm_response : 2'd0)
      );
    end else begin: legacy_cache_only
      assign batch_ready=0; assign batch_idle=1; assign batch_done=0;
      assign batch_error=0; assign batch_cancel_done=0; assign batch_logit_valid=0;
      assign batch_logit_index=0; assign batch_logit_data=0;
      assign bus_idle=1; assign bus_fault=0; assign bus_drained=1; assign bus_flush=0;
      assign ht2_read=0; assign ht2_write=0; assign ht2_address=0;
      assign ht2_writedata=0; assign ht2_byteenable=0; assign ht2_burstcount=0;
      assign spec_req_ready=0; assign spec_rsp_valid=0; assign spec_rsp_id=0;
      assign spec_rsp_error=0; assign accepted_mask=0; assign accepted_count=0;
      assign accepted_tokens=0; assign next_token=0; assign committed_pos=0;
`ifndef SYNTHESIS
      always @(posedge clk)
        if (rst_n && token_valid && selected_mode)
          $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: CACHE_MODE=0 is legacy-only");
`endif
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin sequence_mode<=0; legacy_busy<=0; ht2_bus_owned<=0; end
      else begin
        if ((ht2_token_fire || legacy_token_fire) && new_sequence)
          sequence_mode<=ht2_enable;
        if (legacy_token_fire) legacy_busy<=1;
        if (legacy_done || legacy_cancel_done) legacy_busy<=0;
        if (ht2_token_fire || speculative_fire ||
            (cancel && sequence_mode && !legacy_busy)) ht2_bus_owned<=1;
        else if (ht2_bus_owned && batch_idle && bus_drained) ht2_bus_owned<=0;
      end
    end
  end endgenerate
endmodule
