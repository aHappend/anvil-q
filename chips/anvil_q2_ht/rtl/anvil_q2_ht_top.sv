module anvil_q2_ht_top #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  parameter NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter BANKS=16, LANES_PER_BANK=8, DDR_DATA_WIDTH=512,
  parameter TILE_SLOTS=4, READ_OUTSTANDING=8, QUEUE_DEPTH=3,
  parameter CACHE_BLOCK=16, HOT_BLOCKS=64
) (
  input wire clk, rst_n, cancel, ddr_ready, ddr_fault,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence, token_phase,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire done, error, cancel_done,
  input wire cfg_valid, cfg_write,
  input wire [15:0] cfg_addr,
  input wire [31:0] cfg_wdata,
  output wire cfg_ready, cfg_rsp_valid,
  input wire cfg_rsp_ready,
  output wire [31:0] cfg_rdata,
  output wire cfg_error,
  input wire host_req_valid, host_req_write,
  input wire [32:0] host_req_addr,
  input wire [511:0] host_req_wdata,
  input wire [63:0] host_req_be,
  output wire host_req_ready, host_rsp_valid,
  input wire host_rsp_ready,
  output wire [511:0] host_rsp_rdata,
  output wire host_rsp_error,
  output wire [32:0] avm_address,
  output wire avm_read, avm_write,
  output wire [511:0] avm_writedata,
  output wire [63:0] avm_byteenable,
  output wire [4:0] avm_burstcount,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid, avm_writeresponsevalid,
  input wire [1:0] avm_response
);
  localparam SAFE_GROUP=GROUP_SIZE>=1 ? GROUP_SIZE : 1;
  localparam SAFE_KV=NUM_KV_HEADS>=1 ? NUM_KV_HEADS : 1;
  localparam CW=(CACHE_BLOCK>=1 && CACHE_BLOCK<=128) ? CACHE_BLOCK : 1;
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=1536 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=8960 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 &&
    NUM_KV_HEADS>=1 && NUM_KV_HEADS<=2 &&
    HEAD_DIM>=2 && HEAD_DIM<=128 && (HEAD_DIM & 1)==0 &&
    HIDDEN_SIZE==NUM_Q_HEADS*HEAD_DIM &&
    (NUM_Q_HEADS/SAFE_KV)*NUM_KV_HEADS==NUM_Q_HEADS &&
    (HIDDEN_SIZE & 7)==0 && (INTERMEDIATE_SIZE & 7)==0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7)==0 &&
    GROUP_SIZE>=1 && GROUP_SIZE<=128 &&
    (GROUP_SIZE & (GROUP_SIZE-1))==0 &&
    (HIDDEN_SIZE & (SAFE_GROUP-1))==0 &&
    (INTERMEDIATE_SIZE & (SAFE_GROUP-1))==0 &&
    VOCAB_SIZE>=1 && VOCAB_SIZE<=151936 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    BANKS==16 && LANES_PER_BANK==8 && DDR_DATA_WIDTH==512 &&
    TILE_SLOTS>=2 && TILE_SLOTS<=8 &&
    READ_OUTSTANDING>=1 && READ_OUTSTANDING<=16 &&
    QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    CACHE_BLOCK>=1 && CACHE_BLOCK<=128 &&
    (CACHE_BLOCK & (CACHE_BLOCK-1))==0 && (HEAD_DIM & (CW-1))==0 &&
    HOT_BLOCKS>=1 && HOT_BLOCKS<=64;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT PARAMETER ERROR: top geometry or production width");
    assign token_ready=0; assign logit_valid=0; assign logit_index=0;
    assign logit_data=0; assign done=0; assign error=0; assign cancel_done=0;
    assign cfg_ready=0; assign cfg_rsp_valid=0; assign cfg_rdata=0; assign cfg_error=0;
    assign host_req_ready=0; assign host_rsp_valid=0;
    assign host_rsp_rdata=0; assign host_rsp_error=0;
    assign avm_address=0; assign avm_read=0; assign avm_write=0;
    assign avm_writedata=0; assign avm_byteenable=0; assign avm_burstcount=0;
  end else begin: implementation
    reg draining, active_token, abort_active, cancel_pending, cancel_seen;
    reg sticky_fault, abort_completed, aborted_token, cancellation_completed;
    reg [1:0] settle;
    wire seq_busy, seq_done, seq_error, seq_fault, seq_memory_idle, projection_idle;
    wire seq_token_ready, seq_token_valid, seq_logit_valid;
    wire [31:0] seq_logit_index;
    wire signed [31:0] seq_logit_data;
    wire host_idle, host_memory_idle, host_write_accepted;
    wire fabric_idle, fabric_fault, prefetch_idle, prefetch_drained, prefetch_fault;
    wire tile_fault, kv_idle, kv_burst_idle, kv_invalidate, sequence_invalidate;
    wire validating, model_loaded, configuration_changed, weight_mode;
    wire [1:0] cache_mode;
    wire [32:0] kv_base, kv_length;
    wire desc_req_valid, desc_req_ready, desc_rsp_valid, desc_rsp_ready, desc_rsp_error;
    wire [8:0] desc_req_index;
    wire [511:0] desc_rsp_data;
    wire prefetch_valid, prefetch_ready;
    wire [32:0] prefetch_address;
    wire [6:0] prefetch_beats;
    wire [2:0] prefetch_slot;
    wire [31:0] prefetch_generation;
    wire alloc_valid, alloc_ready, alloc_mode, operand_valid, operand_ready;
    wire [2:0] alloc_slot, operand_slot;
    wire [31:0] alloc_generation, operand_generation;
    wire [4095:0] operand_activation;
    wire [127:0] operand_keep;
    wire meta_valid, meta_ready;
    wire [2:0] meta_slot;
    wire [31:0] meta_generation;
    wire [3:0] meta_row;
    wire [511:0] meta_zero;
    wire [2047:0] meta_scale;
    wire execute_valid, execute_ready, issue_valid, issue_ready, release_valid, release_ready;
    wire [2:0] execute_slot, issue_slot, release_slot;
    wire [31:0] execute_generation, issue_generation, release_generation;
    wire [3:0] issue_row;
    wire [63:0] issue_tag;
    wire fill_valid, fill_last, fill_error, reject_valid;
    wire [2:0] fill_slot, reject_slot;
    wire [31:0] fill_generation, reject_generation;
    wire [5:0] fill_beat;
    wire [511:0] fill_data;
    wire tile_valid, tile_ready, tile_mode;
    wire [127:0] tile_keep;
    wire [4095:0] tile_act;
    wire [511:0] tile_w4, tile_zero;
    wire [2047:0] tile_scale, tile_bf16;
    wire [63:0] tile_tag;
    wire array_valid, array_ready, array_mode, array_error, array_input_ready;
    wire signed [127:0] array_sum;
    wire [31:0] array_fp32;
    wire [63:0] array_tag;
    wire direct_active, direct_valid, direct_ready;
    wire [127:0] direct_keep;
    wire [4095:0] direct_act;
    wire [2047:0] direct_bf16;
    wire [63:0] direct_tag;
    wire kv_cmd_valid, kv_cmd_ready, kv_cmd_write, kv_cmd_value;
    wire [31:0] kv_cmd_layer, kv_cmd_pos, kv_cmd_head, kv_cmd_block;
    wire [CW*32-1:0] kv_cmd_data;
    wire kv_rsp_valid, kv_rsp_ready, kv_rsp_error, kv_commit_valid, kv_commit_ready;
    wire [CW*32-1:0] kv_rsp_data;
    wire [31:0] kv_commit_layer, kv_commit_pos;
    wire host_mem_req_valid, host_mem_req_ready, host_mem_req_write;
    wire [32:0] host_mem_req_addr;
    wire [511:0] host_mem_req_wdata;
    wire [63:0] host_mem_req_be;
    wire host_mem_rsp_valid, host_mem_rsp_ready, host_mem_rsp_error;
    wire [511:0] host_mem_rsp_rdata;
    wire kv_mem_req_valid, kv_mem_req_ready, kv_mem_req_write;
    wire [32:0] kv_mem_req_addr;
    wire [511:0] kv_mem_req_wdata;
    wire [63:0] kv_mem_req_be;
    wire kv_mem_rsp_valid, kv_mem_rsp_ready, kv_mem_rsp_error;
    wire [511:0] kv_mem_rsp_rdata;
    wire kv_back_req_valid, kv_back_req_ready, kv_back_req_write;
    wire [32:0] kv_back_req_addr;
    wire [511:0] kv_back_req_wdata;
    wire [63:0] kv_back_req_be;
    wire kv_back_rsp_valid, kv_back_rsp_ready, kv_back_rsp_error;
    wire [511:0] kv_back_rsp_rdata;
    wire [32:0] k_address;
    wire k_read, k_waitrequest, k_readdatavalid;
    wire [4:0] k_burstcount;
    wire [511:0] k_readdata;
    wire [1:0] k_response;
    wire seq_mem_req_valid, seq_mem_req_ready, seq_mem_rsp_valid, seq_mem_rsp_ready;
    wire seq_mem_rsp_error;
    wire [32:0] seq_mem_req_addr;
    wire [511:0] seq_mem_rsp_rdata;
    wire proj_mem_req_valid, proj_mem_req_ready, proj_mem_rsp_valid, proj_mem_rsp_ready;
    wire proj_mem_rsp_error;
    wire [32:0] proj_mem_req_addr;
    wire [511:0] proj_mem_rsp_rdata;
    wire [32:0] p_address;
    wire p_read, p_waitrequest, p_readdatavalid;
    wire [4:0] p_burstcount;
    wire [511:0] p_readdata;
    wire [1:0] p_response;
    wire [3:0] c_req_ready, c_rsp_valid, c_rsp_error;
    wire [2047:0] c_rsp_rdata;
    wire any_fault=ddr_fault || seq_fault || tile_fault || prefetch_fault || fabric_fault;
    wire cancel_start=cancel && !cancel_seen;
    wire abort_start=rst_n && !draining && (cancel_start || any_fault);
    wire flush=abort_start || configuration_changed;
    wire inhibit=cancel || draining || any_fault;
    wire resources_drained=fabric_idle && (prefetch_idle || prefetch_drained) &&
      kv_idle && kv_burst_idle && seq_memory_idle && host_memory_idle;
    wire quiescent=!active_token && !seq_busy && host_idle && fabric_idle &&
      prefetch_idle && kv_idle && kv_burst_idle && projection_idle && !draining;
    wire token_enable=rst_n && !inhibit && !active_token && model_loaded &&
      ddr_ready && !cfg_valid && !cfg_rsp_valid && !validating &&
      !host_req_valid && host_idle && fabric_idle && prefetch_idle &&
      kv_idle && kv_burst_idle && projection_idle;
    assign token_ready=token_enable && seq_token_ready;
    assign seq_token_valid=token_valid && token_enable;
    assign logit_valid=rst_n && !inhibit && seq_logit_valid;
    assign logit_index=logit_valid ? seq_logit_index : 32'd0;
    assign logit_data=logit_valid ? seq_logit_data : 32'sd0;
    assign done=rst_n && !cancel && ((!draining && seq_done) ||
      (abort_completed && aborted_token));
    assign error=done && (abort_completed || seq_error);
    assign cancel_done=rst_n && !cancel && cancellation_completed;
    assign kv_invalidate=flush || sequence_invalidate;
    assign tile_ready=array_input_ready && !direct_active && !inhibit;
    assign direct_ready=array_input_ready && direct_active && !inhibit;
    assign host_mem_req_ready=c_req_ready[0];
    assign kv_mem_req_ready=c_req_ready[1];
    assign seq_mem_req_ready=c_req_ready[2];
    assign proj_mem_req_ready=c_req_ready[3];
    assign {proj_mem_rsp_valid,seq_mem_rsp_valid,kv_mem_rsp_valid,host_mem_rsp_valid}=c_rsp_valid;
    assign {proj_mem_rsp_error,seq_mem_rsp_error,kv_mem_rsp_error,host_mem_rsp_error}=c_rsp_error;
    assign {proj_mem_rsp_rdata,seq_mem_rsp_rdata,kv_mem_rsp_rdata,host_mem_rsp_rdata}=c_rsp_rdata;

    anvil_q2_ht_configuration #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
      .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
      .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_BLOCK(CACHE_BLOCK)
    ) configuration (
      .clk(clk),.rst_n(rst_n),.annul(inhibit),
      .operation_busy(active_token || seq_busy || !host_idle || draining),
      .quiescent(quiescent),.ddr_ready(ddr_ready),.sticky_fault(sticky_fault),
      .cfg_valid(cfg_valid),.cfg_write(cfg_write),.cfg_addr(cfg_addr),.cfg_wdata(cfg_wdata),
      .cfg_ready(cfg_ready),.cfg_rsp_valid(cfg_rsp_valid),.cfg_rsp_ready(cfg_rsp_ready),
      .cfg_rdata(cfg_rdata),.cfg_error(cfg_error),
      .validating(validating),.model_loaded(model_loaded),
      .configuration_changed(configuration_changed),.weight_mode(weight_mode),
      .cache_mode(cache_mode),.kv_base(kv_base),.kv_length(kv_length),
      .desc_req_valid(desc_req_valid),.desc_req_ready(desc_req_ready),
      .desc_req_index(desc_req_index),.desc_rsp_valid(desc_rsp_valid),
      .desc_rsp_ready(desc_rsp_ready),.desc_rsp_data(desc_rsp_data),.desc_rsp_error(desc_rsp_error));

    anvil_q2_ht_host_port host_port (
      .clk(clk),.rst_n(rst_n),.inhibit(inhibit || cfg_valid || cfg_rsp_valid || validating),
      .ddr_ready(ddr_ready),.operation_busy(active_token || seq_busy || draining),
      .configuration_valid(model_loaded),
      .host_req_valid(host_req_valid),.host_req_write(host_req_write),
      .host_req_addr(host_req_addr),.host_req_wdata(host_req_wdata),.host_req_be(host_req_be),
      .host_req_ready(host_req_ready),.host_rsp_valid(host_rsp_valid),
      .host_rsp_ready(host_rsp_ready),.host_rsp_rdata(host_rsp_rdata),
      .host_rsp_error(host_rsp_error),.idle(host_idle),.memory_idle(host_memory_idle),
      .write_accepted(host_write_accepted),
      .mem_req_valid(host_mem_req_valid),.mem_req_ready(host_mem_req_ready),
      .mem_req_write(host_mem_req_write),.mem_req_addr(host_mem_req_addr),
      .mem_req_wdata(host_mem_req_wdata),.mem_req_be(host_mem_req_be),
      .mem_rsp_valid(host_mem_rsp_valid),.mem_rsp_ready(host_mem_rsp_ready),
      .mem_rsp_rdata(host_mem_rsp_rdata),.mem_rsp_error(host_mem_rsp_error));

    anvil_q2_ht_ddr_prefetcher #(
      .TILE_SLOTS(TILE_SLOTS),.READ_OUTSTANDING(READ_OUTSTANDING),.QUEUE_DEPTH(QUEUE_DEPTH)
    ) prefetcher (
      .clk(clk),.rst_n(rst_n),.flush(flush),.ddr_ready(ddr_ready),.ddr_fault(ddr_fault),
      .region_base(33'd0),.region_end(34'd8589934592),
      .cmd_valid(prefetch_valid),.cmd_ready(prefetch_ready),.cmd_address(prefetch_address),
      .cmd_beats(prefetch_beats),.cmd_slot(prefetch_slot),.cmd_generation(prefetch_generation),
      .fill_valid(fill_valid),.fill_slot(fill_slot),.fill_generation(fill_generation),
      .fill_beat(fill_beat),.fill_data(fill_data),.fill_last(fill_last),.fill_error(fill_error),
      .reject_valid(reject_valid),.reject_slot(reject_slot),.reject_generation(reject_generation),
      .fault(prefetch_fault),.idle(prefetch_idle),.drained(prefetch_drained),
      .avm_address(p_address),.avm_read(p_read),.avm_burstcount(p_burstcount),
      .avm_waitrequest(p_waitrequest),.avm_readdata(p_readdata),
      .avm_readdatavalid(p_readdatavalid),.avm_response(p_response));

    anvil_q2_ht_tile_buffers #(.TILE_SLOTS(TILE_SLOTS)) tile_buffers (
      .clk(clk),.rst_n(rst_n),.flush(flush),.drain_complete(resources_drained),
      .alloc_valid(alloc_valid),.alloc_ready(alloc_ready),.alloc_slot(alloc_slot),
      .alloc_generation(alloc_generation),.alloc_mode(alloc_mode),
      .operand_valid(operand_valid),.operand_ready(operand_ready),.operand_slot(operand_slot),
      .operand_generation(operand_generation),.operand_activation(operand_activation),
      .operand_keep(operand_keep),.meta_valid(meta_valid),.meta_ready(meta_ready),
      .meta_slot(meta_slot),.meta_generation(meta_generation),.meta_row(meta_row),
      .meta_zero(meta_zero),.meta_scale(meta_scale),.fill_valid(fill_valid),.fill_slot(fill_slot),
      .fill_generation(fill_generation),.fill_beat(fill_beat),.fill_data(fill_data),
      .fill_last(fill_last),.fill_error(fill_error),
      .execute_valid(execute_valid),.execute_ready(execute_ready),.execute_slot(execute_slot),
      .execute_generation(execute_generation),.issue_valid(issue_valid),.issue_ready(issue_ready),
      .issue_slot(issue_slot),.issue_generation(issue_generation),.issue_row(issue_row),
      .issue_tag(issue_tag),.release_valid(release_valid),.release_ready(release_ready),
      .release_slot(release_slot),.release_generation(release_generation),
      .m_valid(tile_valid),.m_ready(tile_ready),.m_mode(tile_mode),.m_keep(tile_keep),
      .m_act(tile_act),.m_w4(tile_w4),.m_zero(tile_zero),.m_scale(tile_scale),
      .m_bf16(tile_bf16),.m_tag(tile_tag),.fault(tile_fault));

    anvil_q2_ht_tensor_array tensor_array (
      .clk(clk),.rst_n(rst_n && !flush),
      .s_valid(!inhibit && (direct_active ? direct_valid : tile_valid)),
      .s_ready(array_input_ready),.s_mode(direct_active ? 1'b1 : tile_mode),
      .s_keep(direct_active ? direct_keep : tile_keep),
      .s_act(direct_active ? direct_act : tile_act),
      .s_w4(direct_active ? 512'd0 : tile_w4),.s_zero(direct_active ? 512'd0 : tile_zero),
      .s_scale(direct_active ? 2048'd0 : tile_scale),
      .s_bf16(direct_active ? direct_bf16 : tile_bf16),
      .s_tag(direct_active ? direct_tag : tile_tag),
      .m_ready(array_ready),.m_valid(array_valid),.m_mode(array_mode),
      .m_sum(array_sum),.m_fp32(array_fp32),.m_tag(array_tag),.m_error(array_error));

    anvil_q2_ht_kv_cache #(
      .NUM_LAYERS(NUM_LAYERS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
      .MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_BLOCK(CACHE_BLOCK),.HOT_BLOCKS(HOT_BLOCKS)
    ) kv_cache (
      .clk(clk),.rst_n(rst_n),.invalidate(kv_invalidate),
      .cfg_mode(cache_mode),.cfg_base(kv_base),.cfg_length(kv_length),
      .cmd_valid(kv_cmd_valid),.cmd_ready(kv_cmd_ready),.cmd_write(kv_cmd_write),
      .cmd_value(kv_cmd_value),.cmd_layer(kv_cmd_layer),.cmd_pos(kv_cmd_pos),
      .cmd_head(kv_cmd_head),.cmd_block(kv_cmd_block),.cmd_data(kv_cmd_data),
      .rsp_valid(kv_rsp_valid),.rsp_ready(kv_rsp_ready),.rsp_data(kv_rsp_data),
      .rsp_error(kv_rsp_error),.commit_valid(kv_commit_valid),.commit_ready(kv_commit_ready),
      .commit_layer(kv_commit_layer),.commit_pos(kv_commit_pos),.idle(kv_idle),
      .mem_req_valid(kv_back_req_valid),.mem_req_ready(kv_back_req_ready),
      .mem_req_write(kv_back_req_write),.mem_req_addr(kv_back_req_addr),
      .mem_req_wdata(kv_back_req_wdata),.mem_req_be(kv_back_req_be),
      .mem_rsp_valid(kv_back_rsp_valid),.mem_rsp_ready(kv_back_rsp_ready),
      .mem_rsp_rdata(kv_back_rsp_rdata),.mem_rsp_error(kv_back_rsp_error));

    anvil_q2_ht_kv_burst kv_burst (
      .clk(clk),.rst_n(rst_n),.invalidate(kv_invalidate),
      .region_base(kv_base),.region_length(kv_length),
      .req_valid(kv_back_req_valid),.req_ready(kv_back_req_ready),
      .req_write(kv_back_req_write),.req_address(kv_back_req_addr),
      .req_data(kv_back_req_wdata),.req_mask(kv_back_req_be),
      .rsp_valid(kv_back_rsp_valid),.rsp_ready(kv_back_rsp_ready),
      .rsp_data(kv_back_rsp_rdata),.rsp_error(kv_back_rsp_error),.idle(kv_burst_idle),
      .k_address(k_address),.k_read(k_read),.k_burstcount(k_burstcount),
      .k_waitrequest(k_waitrequest),.k_readdata(k_readdata),
      .k_readdatavalid(k_readdatavalid),.k_response(k_response),
      .write_valid(kv_mem_req_valid),.write_ready(kv_mem_req_ready),
      .write_address(kv_mem_req_addr),.write_data(kv_mem_req_wdata),.write_mask(kv_mem_req_be),
      .write_rsp_valid(kv_mem_rsp_valid),.write_rsp_ready(kv_mem_rsp_ready),
      .write_rsp_error(kv_mem_rsp_error));
    assign kv_mem_req_write=kv_mem_req_valid;

    anvil_q2_ht_sequencer #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
      .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
      .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),
      .CACHE_BLOCK(CACHE_BLOCK),.TILE_SLOTS(TILE_SLOTS)
    ) sequencer (
      .token_valid(seq_token_valid),.token_ready(seq_token_ready),
      .logit_valid(seq_logit_valid),.logit_ready(logit_ready && !inhibit),
      .logit_index(seq_logit_index),.logit_data(seq_logit_data),
      .done(seq_done),.error(seq_error),.busy(seq_busy),.fault(seq_fault),
      .memory_idle(seq_memory_idle),.kv_invalidate(sequence_invalidate),
      .invalidate_weights(host_write_accepted),.*);

    anvil_q2_ht_ddr_fabric #(.CLIENTS(4),.READ_OUTSTANDING(READ_OUTSTANDING)) fabric (
      .clk(clk),.rst_n(rst_n),.ddr_ready(ddr_ready),.ddr_fault(ddr_fault),
      .p_address(p_address),.p_read(p_read),.p_burstcount(p_burstcount),
      .p_waitrequest(p_waitrequest),.p_readdata(p_readdata),
      .p_readdatavalid(p_readdatavalid),.p_response(p_response),
      .k_address(k_address),.k_read(k_read),.k_burstcount(k_burstcount),
      .k_waitrequest(k_waitrequest),.k_readdata(k_readdata),
      .k_readdatavalid(k_readdatavalid),.k_response(k_response),
      .c_req_valid({proj_mem_req_valid,seq_mem_req_valid,kv_mem_req_valid,host_mem_req_valid}),
      .c_req_write({2'b00,kv_mem_req_write,host_mem_req_write}),
      .c_req_ready(c_req_ready),
      .c_req_addr({proj_mem_req_addr,seq_mem_req_addr,kv_mem_req_addr,host_mem_req_addr}),
      .c_req_wdata({1024'd0,kv_mem_req_wdata,host_mem_req_wdata}),
      .c_req_be({128'hffffffffffffffffffffffffffffffff,kv_mem_req_be,host_mem_req_be}),
      .c_rsp_valid(c_rsp_valid),
      .c_rsp_ready({proj_mem_rsp_ready,seq_mem_rsp_ready,kv_mem_rsp_ready,host_mem_rsp_ready}),
      .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error),
      .idle(fabric_idle),.fault(fabric_fault),
      .avm_address(avm_address),.avm_read(avm_read),.avm_write(avm_write),
      .avm_writedata(avm_writedata),.avm_byteenable(avm_byteenable),
      .avm_burstcount(avm_burstcount),.avm_waitrequest(avm_waitrequest),
      .avm_readdata(avm_readdata),.avm_readdatavalid(avm_readdatavalid),
      .avm_writeresponsevalid(avm_writeresponsevalid),.avm_response(avm_response));

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        draining<=0; active_token<=0; abort_active<=0; cancel_pending<=0;
        cancel_seen<=0; sticky_fault<=0; abort_completed<=0;
        aborted_token<=0; cancellation_completed<=0; settle<=0;
      end else begin
        abort_completed<=0; aborted_token<=0; cancellation_completed<=0;
        if (!cancel) cancel_seen<=0;
        else cancel_seen<=1;
        if (token_valid && token_ready) active_token<=1;
        if (seq_done && !inhibit) active_token<=0;
        if (configuration_changed && model_loaded && !any_fault) sticky_fault<=0;
        if (any_fault) sticky_fault<=1;
        if (abort_start) begin
          draining<=1; abort_active<=active_token; active_token<=0;
          cancel_pending<=cancel_start; settle<=0;
        end else if (draining) begin
          if (cancel_start) cancel_pending<=1;
          if (resources_drained && projection_idle && prefetch_idle && !seq_busy) begin
            if (settle!=3) settle<=settle+2'd1;
            else if (!cancel && !ddr_fault) begin
              abort_completed<=1; aborted_token<=abort_active;
              cancellation_completed<=cancel_pending;
              abort_active<=0; cancel_pending<=0; draining<=0;
            end
          end else settle<=0;
        end
      end
    end
  end endgenerate
endmodule
