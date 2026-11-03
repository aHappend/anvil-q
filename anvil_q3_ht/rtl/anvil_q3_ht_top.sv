module anvil_q3_ht_top #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter BANKS=16, LANES_PER_BANK=16, CACHE_MODE=0, INT4_ASYM=0,
  parameter TILE_K=128, TILE_ROWS=8, TILE_SLOTS=4,
  parameter QUEUE_DEPTH=3, BURST_BEATS=16, KV_RESIDENT_GROUPS=64,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 ||
    BANKS==8 || BANKS==16) ? BANKS : 1,
  localparam TS=TILE_SLOTS>=2 && TILE_SLOTS<=4 ? TILE_SLOTS : 2
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
  input wire [1:0] avm_response
);
  localparam LEGAL=SB==BANKS && LANES_PER_BANK==16 && CACHE_MODE>=0 && CACHE_MODE<=2 &&
    INT4_ASYM==0 && AWQ_BITS==4 && TS==TILE_SLOTS &&
    (TILE_K==16 || TILE_K==32 || TILE_K==64 || TILE_K==128) &&
    TILE_ROWS>=1 && TILE_ROWS<=8 && QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    (BURST_BEATS==1 || BURST_BEATS==2 || BURST_BEATS==4 ||
     BURST_BEATS==8 || BURST_BEATS==16) &&
    KV_RESIDENT_GROUPS>=1 && KV_RESIDENT_GROUPS<=256 &&
    NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_KV_HEADS>0 && 64'(NUM_Q_HEADS)==8*64'(NUM_KV_HEADS) &&
    HEAD_DIM>0 && (HEAD_DIM&1)==0 &&
    64'(HIDDEN_SIZE)==64'(NUM_Q_HEADS)*64'(HEAD_DIM) &&
    GROUP_SIZE>=8 && GROUP_SIZE<=128 && (GROUP_SIZE&(GROUP_SIZE-1))==0 &&
    (HIDDEN_SIZE&7)==0 && (INTERMEDIATE_SIZE&7)==0 &&
    (HIDDEN_SIZE&(GROUP_SIZE-1))==0 && (INTERMEDIATE_SIZE&(GROUP_SIZE-1))==0 &&
    VOCAB_SIZE>0 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768;
  wire core_flush, memory_flush, inference_idle;
  wire memory_idle, memory_drained, memory_fault;
  wire ddr_idle, ddr_fault, host_busy, host_fault;
  wire scalar_idle, scalar_drained, scalar_fault;
  wire prefetch_idle, prefetch_drained, prefetch_fault;
  wire kv_idle, kv_drained, kv_fault, scratch_idle, scratch_fault;
  wire scratch_storage_idle, scratch_drained, scratch_storage_fault;
  wire tensor_idle, tensor_fault, tile_idle, tile_fault, projection_idle;
  wire decoder_valid, decoder_ready, decoder_done, decoder_error;
  wire norm_valid, norm_ready, norm_done, norm_error;
  wire io_valid, io_project, io_ready, io_done, io_error, logits_enabled;
  wire io_logit_valid;
  wire [31:0] io_logit_index;
  wire signed [31:0] io_logit_data;
  wire [31:0] epoch, active_token, position, layer;
  wire phase;
  wire projection_valid, projection_ready, projection_done, projection_error;
  wire [31:0] projection_epoch, projection_layer, projection_pos;
  wire [2:0] projection_id;
  wire kv_cmd_valid, kv_cmd_ready, kv_done, kv_error, kv_cmd_phase;
  wire [1:0] kv_cmd_op;
  wire [31:0] kv_cmd_epoch, kv_cmd_layer, kv_cmd_pos, kv_cmd_head, kv_cmd_dim;
  wire signed [31:0] kv_read_data;
  wire [7:0] c_req_valid, c_req_ready, c_req_write, c_rsp_valid, c_rsp_ready, c_rsp_error;
  wire [31:0] c_req_kind;
  wire [23:0] c_req_proj;
  wire [255:0] c_req_layer, c_req_row, c_req_col, c_req_wdata, c_rsp_rdata;
  wire [4:0] d_req_valid, d_req_ready, d_req_write, d_rsp_valid, d_rsp_error;
  wire [164:0] d_req_address;
  wire [2559:0] d_req_wdata, d_rsp_rdata;
  wire [319:0] d_req_byteenable;
  wire [39:0] d_req_burstcount;
  wire [1:0] s_req_valid, s_req_ready, s_req_write, s_rsp_valid, s_rsp_ready, s_rsp_error;
  wire [63:0] s_req_slot, s_req_index, s_req_wdata, s_rsp_rdata;
  wire scratch_req_valid, scratch_req_ready, scratch_req_write;
  wire scratch_rsp_valid, scratch_rsp_ready, scratch_rsp_error;
  wire [31:0] scratch_req_slot, scratch_req_index, scratch_req_wdata, scratch_rsp_rdata;
  wire prefetch_valid, prefetch_ready, prefetch_data_valid, prefetch_data_ready;
  wire prefetch_data_last, prefetch_data_error;
  wire [32:0] prefetch_address;
  wire [31:0] prefetch_beats;
  wire [159:0] prefetch_meta, prefetch_data_meta;
  wire [511:0] prefetch_data;
  wire tile_alloc_valid, tile_alloc_ready, tile_write_valid, tile_write_ready;
  wire tile_seal_valid, tile_seal_ready, tile_activate_valid, tile_activate_ready;
  wire tile_operand_valid, tile_operand_ready, tile_operand_last;
  wire [1:0] tile_alloc_slot, tile_write_slot, tile_seal_slot, tile_activate_slot;
  wire [3:0] tile_write_bank;
  wire [31:0] tile_alloc_entries, tile_write_entry, tile_operand_entry;
  wire [159:0] tile_alloc_meta, tile_write_meta, tile_seal_meta, tile_activate_meta, tile_operand_meta;
  wire [63:0] tile_write_q, tile_write_z;
  wire [255:0] tile_write_scale;
  wire [15:0] tile_write_mask;
  wire [511:0] tile_write_activation, tile_operand_activation;
  wire [SB*64-1:0] tile_operand_q, tile_operand_z, operand_q, operand_z;
  wire [SB*256-1:0] tile_operand_scale, operand_scale;
  wire [SB*16-1:0] tile_operand_mask, operand_mask;
  wire [TS*2-1:0] tile_slot_states;
  wire [SB-1:0] operand_valid, operand_ready, result_valid, result_ready;
  wire [SB*512-1:0] operand_activation;
  wire [SB*160-1:0] operand_meta, result_meta;
  wire [SB*128-1:0] result_sum;
  wire host_write=host_req_valid && host_req_ready && host_req_write;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: top geometry, banks, lanes, cache, tile, queue or burst");
  end endgenerate
  assign memory_idle=ddr_idle && scalar_idle && prefetch_idle && kv_idle &&
    scratch_idle && scratch_storage_idle && tensor_idle && tile_idle && projection_idle;
  assign memory_drained=ddr_idle && scalar_drained && prefetch_drained && kv_drained && scratch_drained;
  assign memory_fault=ddr_fault || host_fault || scalar_fault || prefetch_fault ||
    kv_fault || scratch_fault || scratch_storage_fault || tensor_fault || tile_fault;
  assign logit_valid=rst_n && logits_enabled && io_logit_valid;
  assign logit_index=logit_valid ? io_logit_index : 32'd0;
  assign logit_data=logit_valid ? io_logit_data : 32'sd0;
  assign d_req_burstcount[7:0]=8'd1;
  assign d_req_burstcount[23:16]=8'd1;
  assign d_req_burstcount[31:24]=8'd1;
  assign d_req_burstcount[39:32]=8'd1;
  assign s_req_write[1]=1'b0;
  assign s_req_wdata[63:32]=32'd0;

  anvil_q3_ht_token_controller #(
    .NUM_LAYERS(NUM_LAYERS),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) token_controller (
    .clk(clk),.rst_n(rst_n),.cancel(cancel),
    .run_enable(LEGAL && model_ready && ddr_cal_ready && !host_busy && !host_req_valid && !model_commit),
    .token_valid(token_valid),.token_ready(token_ready),
    .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),.token_phase(token_phase),
    .done(done),.error(error),.cancel_done(cancel_done),.inference_idle(inference_idle),
    .memory_idle(memory_idle),.memory_drained(memory_drained),.memory_fault(memory_fault),
    .core_flush(core_flush),.memory_flush(memory_flush),
    .decoder_valid(decoder_valid),.decoder_ready(decoder_ready),
    .decoder_done(decoder_done),.decoder_error(decoder_error),
    .norm_valid(norm_valid),.norm_ready(norm_ready),.norm_done(norm_done),.norm_error(norm_error),
    .io_valid(io_valid),.io_project(io_project),.io_ready(io_ready),.io_done(io_done),.io_error(io_error),
    .last_logit_transfer(logit_valid && logit_ready && io_logit_index==VOCAB_SIZE-1),
    .logits_enabled(logits_enabled),.epoch(epoch),.active_token_id(active_token),
    .active_position(position),.active_layer(layer),.active_phase(phase)
  );
  anvil_q3_ht_decoder_layer #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) decoder_layer (
    .clk(clk),.rst_n(rst_n),.flush(core_flush),.cmd_valid(decoder_valid),.cmd_ready(decoder_ready),
    .cmd_epoch(epoch),.cmd_layer(layer),.cmd_pos(position),.cmd_phase(phase),
    .done(decoder_done),.error(decoder_error),
    .projection_valid(projection_valid),.projection_ready(projection_ready),
    .projection_done(projection_done),.projection_error(projection_error),
    .projection_epoch(projection_epoch),.projection_layer(projection_layer),
    .projection_pos(projection_pos),.projection_id(projection_id),
    .kv_cmd_valid(kv_cmd_valid),.kv_cmd_ready(kv_cmd_ready),.kv_cmd_op(kv_cmd_op),
    .kv_cmd_epoch(kv_cmd_epoch),.kv_cmd_layer(kv_cmd_layer),.kv_cmd_pos(kv_cmd_pos),
    .kv_cmd_head(kv_cmd_head),.kv_cmd_dim(kv_cmd_dim),.kv_cmd_phase(kv_cmd_phase),
    .kv_done(kv_done),.kv_error(kv_error),.kv_read_data(kv_read_data),
    .c_req_valid(c_req_valid[4:0]),.c_req_ready(c_req_ready[4:0]),.c_req_write(c_req_write[4:0]),
    .c_req_kind(c_req_kind[19:0]),.c_req_layer(c_req_layer[159:0]),.c_req_proj(c_req_proj[14:0]),
    .c_req_row(c_req_row[159:0]),.c_req_col(c_req_col[159:0]),.c_req_wdata(c_req_wdata[159:0]),
    .c_rsp_valid(c_rsp_valid[4:0]),.c_rsp_ready(c_rsp_ready[4:0]),
    .c_rsp_error(c_rsp_error[4:0]),.c_rsp_rdata(c_rsp_rdata[159:0])
  );
  anvil_q3_rmsnorm #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) final_norm (
    .clk(clk),.rst_n(rst_n),.flush(core_flush),.cmd_valid(norm_valid),.cmd_ready(norm_ready),
    .cmd_layer(32'd0),.cmd_pos(position),.cmd_mode(2'd2),.done(norm_done),.error(norm_error),
    .mem_req_valid(c_req_valid[5]),.mem_req_ready(c_req_ready[5]),
    .mem_req_write(c_req_write[5]),.mem_req_kind(c_req_kind[20+:4]),
    .mem_req_layer(c_req_layer[160+:32]),.mem_req_proj(c_req_proj[15+:3]),
    .mem_req_row(c_req_row[160+:32]),.mem_req_col(c_req_col[160+:32]),.mem_req_wdata(c_req_wdata[160+:32]),
    .mem_rsp_valid(c_rsp_valid[5]),.mem_rsp_ready(c_rsp_ready[5]),
    .mem_rsp_rdata(c_rsp_rdata[160+:32]),.mem_rsp_error(c_rsp_error[5])
  );
  anvil_q3_token_io #(
    .HIDDEN_SIZE(HIDDEN_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) token_io (
    .clk(clk),.rst_n(rst_n),.flush(core_flush),
    .cmd_valid(io_valid),.cmd_ready(io_ready),.cmd_project(io_project),
    .cmd_token(active_token),.cmd_pos(position),.done(io_done),.error(io_error),
    .logit_valid(io_logit_valid),.logit_ready(logits_enabled && logit_ready),
    .logit_index(io_logit_index),.logit_data(io_logit_data),
    .mem_req_valid(c_req_valid[6]),.mem_req_ready(c_req_ready[6]),
    .mem_req_write(c_req_write[6]),.mem_req_kind(c_req_kind[24+:4]),
    .mem_req_layer(c_req_layer[192+:32]),.mem_req_proj(c_req_proj[18+:3]),
    .mem_req_row(c_req_row[192+:32]),.mem_req_col(c_req_col[192+:32]),.mem_req_wdata(c_req_wdata[192+:32]),
    .mem_rsp_valid(c_rsp_valid[6]),.mem_rsp_ready(c_rsp_ready[6]),
    .mem_rsp_rdata(c_rsp_rdata[192+:32]),.mem_rsp_error(c_rsp_error[6])
  );
  anvil_q3_ht_projection #(
    .BANKS(BANKS),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS),.TILE_SLOTS(TILE_SLOTS),
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .GROUP_SIZE(GROUP_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) projection_scheduler (
    .clk(clk),.rst_n(rst_n),.flush(core_flush),.cmd_valid(projection_valid),.cmd_ready(projection_ready),
    .cmd_epoch(projection_epoch),.cmd_layer(projection_layer),.cmd_pos(projection_pos),.cmd_proj(projection_id),
    .done(projection_done),.error(projection_error),.idle(projection_idle),
    .mem_req_valid(c_req_valid[7]),.mem_req_ready(c_req_ready[7]),
    .mem_req_write(c_req_write[7]),.mem_req_kind(c_req_kind[28+:4]),
    .mem_req_layer(c_req_layer[224+:32]),.mem_req_proj(c_req_proj[21+:3]),
    .mem_req_row(c_req_row[224+:32]),.mem_req_col(c_req_col[224+:32]),.mem_req_wdata(c_req_wdata[224+:32]),
    .mem_rsp_valid(c_rsp_valid[7]),.mem_rsp_ready(c_rsp_ready[7]),
    .mem_rsp_rdata(c_rsp_rdata[224+:32]),.mem_rsp_error(c_rsp_error[7]),
    .prefetch_valid(prefetch_valid),.prefetch_ready(prefetch_ready),
    .prefetch_address(prefetch_address),.prefetch_beats(prefetch_beats),.prefetch_meta(prefetch_meta),
    .prefetch_data_valid(prefetch_data_valid),.prefetch_data_ready(prefetch_data_ready),
    .prefetch_data(prefetch_data),.prefetch_data_meta(prefetch_data_meta),
    .prefetch_data_last(prefetch_data_last),.prefetch_data_error(prefetch_data_error),
    .prefetch_idle(prefetch_idle),.prefetch_fault(prefetch_fault),
    .tile_alloc_valid(tile_alloc_valid),.tile_alloc_ready(tile_alloc_ready),.tile_alloc_slot(tile_alloc_slot),
    .tile_alloc_entries(tile_alloc_entries),.tile_alloc_meta(tile_alloc_meta),
    .tile_write_valid(tile_write_valid),.tile_write_ready(tile_write_ready),
    .tile_write_slot(tile_write_slot),.tile_write_bank(tile_write_bank),.tile_write_entry(tile_write_entry),
    .tile_write_meta(tile_write_meta),.tile_write_q(tile_write_q),.tile_write_z(tile_write_z),
    .tile_write_scale(tile_write_scale),.tile_write_mask(tile_write_mask),
    .tile_write_activation(tile_write_activation),
    .tile_seal_valid(tile_seal_valid),.tile_seal_ready(tile_seal_ready),
    .tile_seal_slot(tile_seal_slot),.tile_seal_meta(tile_seal_meta),
    .tile_activate_valid(tile_activate_valid),.tile_activate_ready(tile_activate_ready),
    .tile_activate_slot(tile_activate_slot),.tile_activate_meta(tile_activate_meta),
    .tile_operand_valid(tile_operand_valid),.tile_operand_ready(tile_operand_ready),
    .tile_operand_q(tile_operand_q),.tile_operand_z(tile_operand_z),
    .tile_operand_scale(tile_operand_scale),.tile_operand_mask(tile_operand_mask),
    .tile_operand_activation(tile_operand_activation),
    .tile_operand_meta(tile_operand_meta),.tile_operand_entry(tile_operand_entry),
    .tile_operand_last(tile_operand_last),.tile_slot_states(tile_slot_states),
    .tile_idle(tile_idle),.tile_fault(tile_fault),
    .operand_valid(operand_valid),.operand_ready(operand_ready),
    .operand_q(operand_q),.operand_z(operand_z),.operand_scale(operand_scale),
    .operand_activation(operand_activation),.operand_mask(operand_mask),.operand_meta(operand_meta),
    .result_valid(result_valid),.result_ready(result_ready),.result_sum(result_sum),.result_meta(result_meta),
    .tensor_idle(tensor_idle),.tensor_fault(tensor_fault)
  );
  anvil_q3_ht_tile_buffers #(
    .BANKS(BANKS),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS),.TILE_SLOTS(TILE_SLOTS)
  ) tile_buffers (
    .clk(clk),.rst_n(rst_n),.flush(core_flush),
    .alloc_valid(tile_alloc_valid),.alloc_ready(tile_alloc_ready),.alloc_slot(tile_alloc_slot),
    .alloc_entries(tile_alloc_entries),.alloc_meta(tile_alloc_meta),
    .write_valid(tile_write_valid),.write_ready(tile_write_ready),
    .write_slot(tile_write_slot),.write_bank(tile_write_bank),.write_entry(tile_write_entry),
    .write_meta(tile_write_meta),.write_q(tile_write_q),.write_z(tile_write_z),
    .write_scale(tile_write_scale),.write_mask(tile_write_mask),
    .write_activation(tile_write_activation),
    .seal_valid(tile_seal_valid),.seal_ready(tile_seal_ready),.seal_slot(tile_seal_slot),.seal_meta(tile_seal_meta),
    .activate_valid(tile_activate_valid),.activate_ready(tile_activate_ready),
    .activate_slot(tile_activate_slot),.activate_meta(tile_activate_meta),
    .operand_valid(tile_operand_valid),.operand_ready(tile_operand_ready),
    .operand_q(tile_operand_q),.operand_z(tile_operand_z),
    .operand_scale(tile_operand_scale),.operand_mask(tile_operand_mask),
    .operand_activation(tile_operand_activation),
    .operand_meta(tile_operand_meta),.operand_entry(tile_operand_entry),.operand_last(tile_operand_last),
    .slot_states(tile_slot_states),.idle(tile_idle),.fault(tile_fault)
  );
  anvil_q3_ht_tensor_array #(
    .BANKS(BANKS),.LANES_PER_BANK(LANES_PER_BANK),.TILE_ROWS(TILE_ROWS)
  ) tensor_array (
    .clk(clk),.rst_n(rst_n),.flush(core_flush),
    .operand_valid(operand_valid),.operand_ready(operand_ready),.operand_q(operand_q),.operand_z(operand_z),
    .operand_scale(operand_scale),.operand_activation(operand_activation),
    .operand_mask(operand_mask),.operand_meta(operand_meta),
    .result_valid(result_valid),.result_ready(result_ready),.result_sum(result_sum),.result_meta(result_meta),
    .idle(tensor_idle),.fault(tensor_fault)
  );
  anvil_q3_ht_ddr_prefetcher #(.QUEUE_DEPTH(QUEUE_DEPTH),.BURST_BEATS(BURST_BEATS)) ddr_prefetcher (
    .clk(clk),.rst_n(rst_n),.flush(memory_flush),
    .cmd_valid(prefetch_valid),.cmd_ready(prefetch_ready),
    .cmd_address(prefetch_address),.cmd_beats(prefetch_beats),.cmd_meta(prefetch_meta),
    .data_valid(prefetch_data_valid),.data_ready(prefetch_data_ready),
    .data(prefetch_data),.data_meta(prefetch_data_meta),
    .data_last(prefetch_data_last),.data_error(prefetch_data_error),
    .idle(prefetch_idle),.drain_done(prefetch_drained),.fault(prefetch_fault),
    .avm_address(d_req_address[33+:33]),.avm_read(d_req_valid[1]),
    .avm_burstcount(d_req_burstcount[8+:8]),.avm_waitrequest(!d_req_ready[1]),
    .avm_readdata(d_rsp_rdata[512+:512]),.avm_readdatavalid(d_rsp_valid[1]),
    .avm_response(d_rsp_error[1] ? 2'b10 : 2'b00)
  );
  assign d_req_write[1]=1'b0;
  assign d_req_wdata[512+:512]=512'd0;
  assign d_req_byteenable[64+:64]=64'hffffffffffffffff;
  anvil_q3_ht_kv_hierarchy #(
    .NUM_LAYERS(NUM_LAYERS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_MODE(CACHE_MODE),.KV_RESIDENT_GROUPS(KV_RESIDENT_GROUPS)
  ) kv_hierarchy (
    .clk(clk),.rst_n(rst_n),.flush(memory_flush),
    .cmd_valid(kv_cmd_valid),.cmd_ready(kv_cmd_ready),.cmd_op(kv_cmd_op),
    .cmd_epoch(kv_cmd_epoch),.cmd_layer(kv_cmd_layer),.cmd_pos(kv_cmd_pos),
    .cmd_head(kv_cmd_head),.cmd_dim(kv_cmd_dim),.cmd_phase(kv_cmd_phase),.cmd_bypass(1'b0),
    .done(kv_done),.error(kv_error),.read_data(kv_read_data),
    .idle(kv_idle),.drain_done(kv_drained),.fault(kv_fault),
    .scratch_req_valid(s_req_valid[1]),.scratch_req_ready(s_req_ready[1]),
    .scratch_req_slot(s_req_slot[32+:32]),.scratch_req_index(s_req_index[32+:32]),
    .scratch_rsp_valid(s_rsp_valid[1]),.scratch_rsp_error(s_rsp_error[1]),
    .scratch_rsp_ready(s_rsp_ready[1]),.scratch_rsp_rdata(s_rsp_rdata[32+:32]),
    .memory_req_valid(d_req_valid[3]),.memory_req_ready(d_req_ready[3]),
    .memory_req_write(d_req_write[3]),.memory_req_address(d_req_address[99+:33]),
    .memory_req_wdata(d_req_wdata[1536+:512]),.memory_req_byteenable(d_req_byteenable[192+:64]),
    .memory_rsp_valid(d_rsp_valid[3]),.memory_rsp_error(d_rsp_error[3]),
    .memory_rsp_rdata(d_rsp_rdata[1536+:512])
  );
  anvil_q3_ht_scalar_adapter #(
    .CLIENTS(8),.NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .GROUP_SIZE(GROUP_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) scalar_adapter (
    .clk(clk),.rst_n(rst_n),.flush(memory_flush),.invalidate(host_write),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
    .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
    .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
    .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),.c_rsp_error(c_rsp_error),.c_rsp_rdata(c_rsp_rdata),
    .idle(scalar_idle),.drain_done(scalar_drained),.fault(scalar_fault),
    .scratch_req_valid(s_req_valid[0]),.scratch_req_ready(s_req_ready[0]),
    .scratch_req_write(s_req_write[0]),.scratch_req_slot(s_req_slot[0+:32]),
    .scratch_req_index(s_req_index[0+:32]),.scratch_req_wdata(s_req_wdata[0+:32]),
    .scratch_rsp_valid(s_rsp_valid[0]),.scratch_rsp_ready(s_rsp_ready[0]),
    .scratch_rsp_error(s_rsp_error[0]),.scratch_rsp_rdata(s_rsp_rdata[0+:32]),
    .memory_req_valid(d_req_valid[2]),.memory_req_ready(d_req_ready[2]),
    .memory_req_write(d_req_write[2]),.memory_req_address(d_req_address[66+:33]),
    .memory_req_wdata(d_req_wdata[1024+:512]),.memory_req_byteenable(d_req_byteenable[128+:64]),
    .memory_rsp_valid(d_rsp_valid[2]),.memory_rsp_error(d_rsp_error[2]),
    .memory_rsp_rdata(d_rsp_rdata[1024+:512])
  );
  anvil_q3_ht_scratch_arbiter #(.CLIENTS(2)) scratch_arbiter (
    .clk(clk),.rst_n(rst_n),.flush(memory_flush),
    .c_req_valid(s_req_valid),.c_req_ready(s_req_ready),.c_req_write(s_req_write),
    .c_req_slot(s_req_slot),.c_req_index(s_req_index),.c_req_wdata(s_req_wdata),
    .c_rsp_valid(s_rsp_valid),.c_rsp_ready(s_rsp_ready),.c_rsp_error(s_rsp_error),.c_rsp_rdata(s_rsp_rdata),
    .idle(scratch_idle),.fault(scratch_fault),
    .req_valid(scratch_req_valid),.req_ready(scratch_req_ready),.req_write(scratch_req_write),
    .req_slot(scratch_req_slot),.req_index(scratch_req_index),.req_wdata(scratch_req_wdata),
    .rsp_valid(scratch_rsp_valid),.rsp_ready(scratch_rsp_ready),.rsp_error(scratch_rsp_error),
    .rsp_rdata(scratch_rsp_rdata)
  );
  anvil_q3_ht_scratchpad #(
    .HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM)
  ) scratchpad (
    .clk(clk),.rst_n(rst_n),.flush(memory_flush),.memory_enable(ddr_cal_ready),
    .req_valid(scratch_req_valid),.req_ready(scratch_req_ready),.req_write(scratch_req_write),
    .req_slot(scratch_req_slot),.req_index(scratch_req_index),.req_wdata(scratch_req_wdata),
    .rsp_valid(scratch_rsp_valid),.rsp_ready(scratch_rsp_ready),.rsp_error(scratch_rsp_error),
    .rsp_rdata(scratch_rsp_rdata),
    .idle(scratch_storage_idle),.drain_done(scratch_drained),.fault(scratch_storage_fault),
    .memory_req_valid(d_req_valid[4]),.memory_req_ready(d_req_ready[4]),
    .memory_req_write(d_req_write[4]),.memory_req_address(d_req_address[132+:33]),
    .memory_req_wdata(d_req_wdata[2048+:512]),.memory_req_byteenable(d_req_byteenable[256+:64]),
    .memory_rsp_valid(d_rsp_valid[4]),.memory_rsp_error(d_rsp_error[4]),
    .memory_rsp_rdata(d_rsp_rdata[2048+:512])
  );
  anvil_q3_ht_host_loader host_loader (
    .clk(clk),.rst_n(rst_n),.inference_idle(inference_idle && !cancel),
    .memory_idle(memory_idle),.ddr_cal_ready(ddr_cal_ready),.model_commit(model_commit),
    .model_ready(model_ready),.busy(host_busy),.fault(host_fault),
    .host_req_valid(host_req_valid),.host_req_ready(host_req_ready),.host_req_write(host_req_write),
    .host_req_address(host_req_address),.host_req_wdata(host_req_wdata),.host_req_byteenable(host_req_byteenable),
    .host_rsp_valid(host_rsp_valid),.host_rsp_ready(host_rsp_ready),
    .host_rsp_rdata(host_rsp_rdata),.host_rsp_error(host_rsp_error),
    .memory_req_valid(d_req_valid[0]),.memory_req_ready(d_req_ready[0]),
    .memory_req_write(d_req_write[0]),.memory_req_address(d_req_address[0+:33]),
    .memory_req_wdata(d_req_wdata[0+:512]),.memory_req_byteenable(d_req_byteenable[0+:64]),
    .memory_rsp_valid(d_rsp_valid[0]),.memory_rsp_error(d_rsp_error[0]),.memory_rsp_rdata(d_rsp_rdata[0+:512])
  );
  anvil_q3_ht_ddr_arbiter #(.CLIENTS(5),.READ_SLOTS(8)) ddr_arbiter (
    .clk(clk),.rst_n(rst_n),.flush(memory_flush || (core_flush && memory_drained)),
    .c_req_valid(d_req_valid),.c_req_ready(d_req_ready),.c_req_write(d_req_write),
    .c_req_address(d_req_address),.c_req_wdata(d_req_wdata),.c_req_byteenable(d_req_byteenable),
    .c_req_burstcount(d_req_burstcount),.c_rsp_valid(d_rsp_valid),.c_rsp_error(d_rsp_error),
    .c_rsp_rdata(d_rsp_rdata),.idle(ddr_idle),.fault(ddr_fault),
    .avm_address(avm_address),.avm_read(avm_read),.avm_write(avm_write),.avm_writedata(avm_writedata),
    .avm_byteenable(avm_byteenable),.avm_burstcount(avm_burstcount),
    .avm_waitrequest(avm_waitrequest),.avm_readdata(avm_readdata),
    .avm_readdatavalid(avm_readdatavalid),.avm_response(avm_response)
  );
endmodule
