module anvil_q1_ht_top #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2, HEAD_DIM = 64, GROUP_SIZE = 128,
  parameter AWQ_BITS = 4, VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768,
  parameter LANES = 64, BANKS = 8, LANES_PER_BANK = 8, DDR_WIDTH = 512,
  parameter TILE_BEATS = 256, KV_WINDOW = 128
) (
  input wire clk, ddr_clk, rst_n,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire done, error,
  input wire csr_valid, csr_write,
  input wire [15:0] csr_address,
  input wire [31:0] csr_wdata,
  output wire csr_ready, csr_rsp_valid,
  input wire csr_rsp_ready,
  output wire [31:0] csr_rdata,
  output wire csr_error,
  input wire load_valid,
  output wire load_ready,
  input wire [32:0] load_address,
  input wire [511:0] load_data,
  input wire [63:0] load_byteenable,
  input wire load_last,
  output wire load_done, load_error,
  output wire [32:0] avm_address,
  output wire [7:0] avm_burstcount,
  output wire avm_read, avm_write,
  output wire [511:0] avm_writedata,
  output wire [63:0] avm_byteenable,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid,
  input wire [1:0] avm_response,
  input wire avm_writeresponsevalid
);
  localparam SG = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  localparam SK = NUM_KV_HEADS > 0 ? NUM_KV_HEADS : 1;
  localparam VALID = NUM_LAYERS > 0 && NUM_LAYERS <= 24 &&
    HIDDEN_SIZE > 0 && HIDDEN_SIZE <= 896 &&
    INTERMEDIATE_SIZE > 0 && INTERMEDIATE_SIZE <= 4864 &&
    NUM_Q_HEADS > 0 && NUM_Q_HEADS <= 14 && NUM_KV_HEADS > 0 && NUM_KV_HEADS <= 2 &&
    HEAD_DIM > 0 && HEAD_DIM <= 64 && !(HEAD_DIM % 2) &&
    HIDDEN_SIZE == NUM_Q_HEADS*HEAD_DIM && !(NUM_Q_HEADS % SK) &&
    !(HIDDEN_SIZE % 8) && !(INTERMEDIATE_SIZE % 8) &&
    !((NUM_KV_HEADS*HEAD_DIM) % 8) &&
    GROUP_SIZE > 0 && GROUP_SIZE <= HIDDEN_SIZE &&
    !(HIDDEN_SIZE % SG) && !(INTERMEDIATE_SIZE % SG) &&
    VOCAB_SIZE > 0 && VOCAB_SIZE <= 151936 &&
    MAX_SEQ_LEN > 0 && MAX_SEQ_LEN <= 32768 &&
    LANES == 64 && BANKS == 8 && LANES_PER_BANK == 8 && DDR_WIDTH == 512 && AWQ_BITS == 4 &&
    TILE_BEATS >= 1 && TILE_BEATS <= 256 &&
    KV_WINDOW >= 1 && KV_WINDOW <= 128 && KV_WINDOW <= MAX_SEQ_LEN;
  // Invalid configurations elaborate only safe dimensions before the explicit diagnostic.
  localparam L = VALID ? NUM_LAYERS : 1, H = VALID ? HIDDEN_SIZE : 8;
  localparam I = VALID ? INTERMEDIATE_SIZE : 8, Q = VALID ? NUM_Q_HEADS : 1;
  localparam K = VALID ? NUM_KV_HEADS : 1, D = VALID ? HEAD_DIM : 8;
  localparam G = VALID ? GROUP_SIZE : 1, V = VALID ? VOCAB_SIZE : 8;
  localparam S = VALID ? MAX_SEQ_LEN : 1, T = VALID ? TILE_BEATS : 1;
  localparam W = VALID ? KV_WINDOW : 1;
  wire core_rst_n, ddr_rst_n;
  wire initialized, image_valid, bf16, sticky_error, configuration_busy;
  wire clear_load_error, load_busy_core, load_failed_core, image_modified;
  wire load_enable, load_clear, load_idle_ddr, available, emif_initialized;
  wire decoder_busy, decoder_ready, decoder_done, decoder_error, cache_clear, kv_initialized;
  wire engine_enable, engine_eligible, fatal_core, fatal_ddr;
  wire [63:0] token_cycles, read_snapshot;
  reg [31:0] read_count_low, read_count_high;
  wire [63:0] read_count = {read_count_high, read_count_low};
  (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
  reg fatal_meta, fatal_sync;
  wire mux_error, scalar_protocol_error, dma_protocol_error, kv_protocol_error;
  wire tiles_error, tile_fill_error, tensor_protocol_error;
  wire descriptor_lookup_valid, descriptor_lookup_ready;
  wire [31:0] descriptor_lookup_index;
  wire descriptor_rsp_valid, descriptor_rsp_ready, descriptor_rsp_error;
  wire [32:0] descriptor_base;
  wire [31:0] descriptor_length;
  wire [1:0] lookup_valid, lookup_ready, lookup_rsp_valid, lookup_rsp_ready;
  wire [63:0] lookup_index;
  wire [131:0] lookup_result;
  wire [65:0] descriptor_result = {descriptor_rsp_error, descriptor_base, descriptor_length};
  wire memory_valid, memory_ready, memory_write, memory_rsp_valid, memory_rsp_ready, memory_rsp_error;
  wire [3:0] memory_kind;
  wire [31:0] memory_layer, memory_row, memory_col, memory_wdata, memory_rdata;
  wire [2:0] memory_proj;
  wire external_valid, external_ready, external_write, external_rsp_valid, external_rsp_ready;
  wire external_rsp_error;
  wire [3:0] external_kind;
  wire [31:0] external_layer, external_row, external_col, external_wdata, external_rdata;
  wire [2:0] external_proj;
  wire kv_valid, kv_ready, kv_write, kv_value, kv_rsp_valid, kv_rsp_ready, kv_rsp_error;
  wire [31:0] kv_layer, kv_head, kv_pos, kv_dim;
  wire signed [31:0] kv_wdata, kv_rdata;
  wire spill_valid, spill_ready, spill_write, spill_value, spill_rsp_valid, spill_rsp_ready;
  wire spill_rsp_error;
  wire [31:0] spill_layer, spill_pos, spill_col;
  wire signed [31:0] spill_wdata, spill_rdata;
  wire [1:0] address_client_valid, address_client_ready, address_rsp_valid, address_rsp_ready;
  wire [271:0] address_client_data;
  wire [65:0] address_client_response;
  wire address_valid, address_ready, address_rsp_valid_one, address_rsp_ready_one;
  wire [135:0] address_request;
  wire [31:0] address_rdata;
  wire address_error;
  wire scalar_valid, scalar_ready, scalar_write, scalar_rsp_valid, scalar_rsp_ready, scalar_error;
  wire [32:0] scalar_address;
  wire [511:0] scalar_wdata, scalar_rdata;
  wire [63:0] scalar_byteenable;
  wire block_valid, block_ready, packet_valid, packet_ready, packet_last, block_done, block_error;
  wire [3:0] block_kind;
  wire [31:0] block_layer, block_offset, block_bytes;
  wire [2:0] block_proj;
  wire [7:0] block_packet_bytes;
  wire [1023:0] packet_data;
  wire dma_valid, dma_ready, dma_done, dma_done_ready, dma_error, dma_abort;
  wire [32:0] dma_address;
  wire [31:0] dma_bytes;
  wire [26:0] dma_tiles;
  wire fill_valid, fill_ready, fill_data_valid, fill_data_ready, fill_last, fill_abort;
  wire [8:0] fill_beats;
  wire [63:0] fill_tail;
  wire [511:0] fill_data;
  wire tile_valid, tile_ready, release_valid, release_ready, read_valid, read_ready;
  wire read_rsp_valid, read_rsp_ready;
  wire [8:0] tile_beats;
  wire [7:0] read_address;
  wire [511:0] read_data;
  wire [63:0] read_mask;
  wire tensor_in_valid, tensor_in_ready, tensor_in_first, tensor_in_last;
  wire signed [31:0] tensor_activation;
  wire [2367:0] tensor_weights;
  wire [63:0] tensor_mask, tensor_out_mask;
  wire tensor_out_valid, tensor_out_ready;
  wire [2047:0] tensor_out_data;
  wire [65:0] client_address;
  wire [15:0] client_burstcount;
  wire [1:0] client_read, client_write, client_waitrequest;
  wire [1023:0] client_writedata, client_readdata;
  wire [127:0] client_byteenable;
  wire [1:0] client_readdatavalid, client_writeresponsevalid;
  wire [3:0] client_response;
  wire dma_load_done, dma_load_error, dma_load_ready;

  anvil_q1_ht_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,HEAD_DIM,
    GROUP_SIZE,AWQ_BITS,VOCAB_SIZE,MAX_SEQ_LEN,LANES,BANKS,LANES_PER_BANK,DDR_WIDTH,
    TILE_BEATS,KV_WINDOW
  ) u_parameters();
  anvil_q1_ht_reset_sync u_core_reset(clk, rst_n && VALID, core_rst_n);
  anvil_q1_ht_reset_sync u_ddr_reset(ddr_clk, rst_n && VALID, ddr_rst_n);
  assign fatal_ddr = mux_error || scalar_protocol_error || dma_protocol_error || tile_fill_error;
  assign fatal_core = fatal_sync || tiles_error || tensor_protocol_error;
  assign engine_eligible = initialized && image_valid && available && emif_initialized &&
    !configuration_busy && !fatal_core && !sticky_error;
  assign engine_enable = engine_eligible && !csr_valid && !csr_rsp_valid;
  assign token_ready = core_rst_n && decoder_ready;
  assign done = core_rst_n && decoder_done;
  assign error = done && decoder_error;
  assign load_ready = ddr_rst_n && dma_load_ready && load_enable;
  assign load_done = ddr_rst_n && dma_load_done;
  assign load_error = ddr_rst_n && dma_load_error;
  always @(posedge clk or negedge core_rst_n) begin
    if (!core_rst_n) begin fatal_meta <= 0; fatal_sync <= 0; end
    else begin fatal_meta <= fatal_ddr; fatal_sync <= fatal_meta; end
  end
  always @(posedge ddr_clk or negedge ddr_rst_n) begin
    if (!ddr_rst_n) begin read_count_low <= 0; read_count_high <= 0; end
    else if (avm_readdatavalid && |client_readdatavalid) begin
      read_count_low <= read_count_low + 32'd1;
      if (&read_count_low) read_count_high <= read_count_high + 32'd1;
    end
  end
  // Keep the last acknowledged snapshot, including while its mailbox is empty.
  wire snapshot_valid;
  wire [63:0] snapshot_data;
  reg [63:0] held_snapshot;
  anvil_q1_ht_cdc_mailbox #(.WIDTH(64)) u_read_counter (
    .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n && VALID),
    .source_valid(1'b1), .source_ready(), .source_data(read_count),
    .destination_valid(snapshot_valid), .destination_ready(1'b1),
    .destination_data(snapshot_data)
  );
  always @(posedge clk or negedge core_rst_n) begin
    if (!core_rst_n) held_snapshot <= 0;
    else if (snapshot_valid) held_snapshot <= snapshot_data;
  end
  assign read_snapshot = held_snapshot;
  anvil_q1_ht_image_guard u_image_guard (
    .clk(clk), .ddr_clk(ddr_clk), .rst_n(rst_n && VALID),
    .engine_busy(decoder_busy), .configuration_busy(configuration_busy),
    .csr_active(csr_valid || csr_rsp_valid), .descriptors_initialized(initialized),
    .load_valid(load_valid), .dma_load_idle(load_idle_ddr),
    .dma_load_done(dma_load_done), .dma_load_error(dma_load_error),
    .clear_load_error(clear_load_error), .load_enable(load_enable), .load_clear(load_clear),
    .image_modified(image_modified), .load_busy(load_busy_core), .load_failed(load_failed_core),
    .core_available(available), .emif_initialized(emif_initialized)
  );
  anvil_q1_ht_descriptors #(L,H,I,K,D,G,V,S) u_descriptors (
    .clk(clk), .rst_n(core_rst_n),
    .csr_valid(csr_valid), .csr_write(csr_write), .csr_address(csr_address),
    .csr_wdata(csr_wdata), .csr_ready(csr_ready), .csr_rsp_valid(csr_rsp_valid),
    .csr_rsp_ready(csr_rsp_ready), .csr_rdata(csr_rdata), .csr_error(csr_error),
    .engine_busy(decoder_busy), .load_busy(load_busy_core), .load_failed(load_failed_core),
    .emif_initialized(emif_initialized),
    .fault_event(fatal_core || (decoder_done && decoder_error)),
    .image_modified(image_modified),
    .engine_ready(engine_eligible && !decoder_busy && kv_initialized),
    .token_cycles(token_cycles), .read_beats(read_snapshot),
    .initialized(initialized), .image_valid(image_valid), .storage_bf16(bf16),
    .sticky_error(sticky_error), .clear_load_error(clear_load_error),
    .configuration_busy(configuration_busy),
    .lookup_valid(descriptor_lookup_valid), .lookup_ready(descriptor_lookup_ready),
    .lookup_index(descriptor_lookup_index), .lookup_rsp_valid(descriptor_rsp_valid),
    .lookup_rsp_ready(descriptor_rsp_ready), .lookup_base(descriptor_base),
    .lookup_length(descriptor_length), .lookup_error(descriptor_rsp_error)
  );
  anvil_q1_ht_transaction_mux #(.CLIENTS(2), .REQUEST_WIDTH(32), .RESPONSE_WIDTH(66))
  u_lookup_mux (
    .clk(clk), .rst_n(core_rst_n), .client_valid(lookup_valid), .client_ready(lookup_ready),
    .client_data(lookup_index), .client_rsp_valid(lookup_rsp_valid),
    .client_rsp_ready(lookup_rsp_ready), .client_rsp_data(lookup_result),
    .request_valid(descriptor_lookup_valid), .request_ready(descriptor_lookup_ready),
    .request_data(descriptor_lookup_index), .response_valid(descriptor_rsp_valid),
    .response_ready(descriptor_rsp_ready), .response_data(descriptor_result)
  );
  anvil_q1_ht_decoder #(L,H,I,Q,K,D,G,V,S) u_decoder (
    .clk(clk), .rst_n(core_rst_n), .engine_enable(engine_enable), .storage_bf16(bf16),
    .execution_fault(fatal_core),
    .token_valid(token_valid), .token_ready(decoder_ready),
    .token_id(token_id), .token_pos(token_pos), .new_sequence(new_sequence),
    .logit_valid(logit_valid), .logit_ready(logit_ready), .logit_index(logit_index),
    .logit_data(logit_data), .done(decoder_done), .error(decoder_error),
    .busy(decoder_busy), .token_cycles(token_cycles),
    .cache_new_sequence(cache_clear), .cache_initialized(kv_initialized),
    .mem_req_valid(memory_valid), .mem_req_ready(memory_ready), .mem_req_write(memory_write),
    .mem_req_kind(memory_kind), .mem_req_layer(memory_layer), .mem_req_proj(memory_proj),
    .mem_req_row(memory_row), .mem_req_col(memory_col), .mem_req_wdata(memory_wdata),
    .mem_rsp_valid(memory_rsp_valid), .mem_rsp_ready(memory_rsp_ready),
    .mem_rsp_rdata(memory_rdata), .mem_rsp_error(memory_rsp_error),
    .block_valid(block_valid), .block_ready(block_ready), .block_kind(block_kind),
    .block_layer(block_layer), .block_proj(block_proj), .block_offset(block_offset),
    .block_bytes(block_bytes), .block_packet_bytes(block_packet_bytes),
    .packet_valid(packet_valid), .packet_ready(packet_ready), .packet_data(packet_data),
    .packet_last(packet_last), .block_done(block_done), .block_error(block_error),
    .tensor_in_valid(tensor_in_valid), .tensor_in_ready(tensor_in_ready),
    .tensor_in_first(tensor_in_first), .tensor_in_last(tensor_in_last),
    .tensor_in_activation(tensor_activation), .tensor_in_weight_q16(tensor_weights),
    .tensor_in_mask(tensor_mask), .tensor_out_valid(tensor_out_valid),
    .tensor_out_ready(tensor_out_ready), .tensor_out_data(tensor_out_data),
    .tensor_out_mask(tensor_out_mask), .tensor_protocol_error(tensor_protocol_error)
  );
  wire tensor_rst_n;
  anvil_q1_ht_reset_sync u_tensor_reset (
    clk, core_rst_n && !(decoder_done && decoder_error), tensor_rst_n
  );
  anvil_q1_ht_tensor_array u_tensor (
    .clk(clk), .rst_n(tensor_rst_n), .in_valid(tensor_in_valid), .in_ready(tensor_in_ready),
    .in_first(tensor_in_first), .in_last(tensor_in_last), .in_activation(tensor_activation),
    .in_weight_q16(tensor_weights), .in_mask(tensor_mask),
    .out_valid(tensor_out_valid), .out_ready(tensor_out_ready),
    .out_data(tensor_out_data), .out_mask(tensor_out_mask),
    .protocol_error(tensor_protocol_error)
  );
  anvil_q1_ht_logical_memory #(L,H,I,K,D,S) u_memory (
    .clk(clk), .rst_n(core_rst_n),
    .req_valid(memory_valid), .req_ready(memory_ready), .req_write(memory_write),
    .req_kind(memory_kind), .req_layer(memory_layer), .req_proj(memory_proj),
    .req_row(memory_row), .req_col(memory_col), .req_wdata(memory_wdata),
    .rsp_valid(memory_rsp_valid), .rsp_ready(memory_rsp_ready),
    .rsp_data(memory_rdata), .rsp_error(memory_rsp_error),
    .external_valid(external_valid), .external_ready(external_ready),
    .external_write(external_write), .external_kind(external_kind),
    .external_layer(external_layer), .external_proj(external_proj),
    .external_row(external_row), .external_col(external_col), .external_wdata(external_wdata),
    .external_rsp_valid(external_rsp_valid), .external_rsp_ready(external_rsp_ready),
    .external_rsp_data(external_rdata), .external_rsp_error(external_rsp_error),
    .kv_valid(kv_valid), .kv_ready(kv_ready), .kv_write(kv_write), .kv_value(kv_value),
    .kv_layer(kv_layer), .kv_head(kv_head), .kv_pos(kv_pos), .kv_dim(kv_dim),
    .kv_wdata(kv_wdata), .kv_rsp_valid(kv_rsp_valid), .kv_rsp_ready(kv_rsp_ready),
    .kv_rsp_data(kv_rdata), .kv_rsp_error(kv_rsp_error)
  );
  anvil_q1_ht_kv_window #(L,K,D,S,W) u_kv (
    .clk(clk), .rst_n(core_rst_n), .new_sequence(cache_clear), .initialized(kv_initialized),
    .req_valid(kv_valid), .req_ready(kv_ready), .req_write(kv_write), .req_value(kv_value),
    .req_layer(kv_layer), .req_head(kv_head), .req_pos(kv_pos), .req_dim(kv_dim),
    .req_wdata(kv_wdata), .rsp_valid(kv_rsp_valid), .rsp_ready(kv_rsp_ready),
    .rsp_data(kv_rdata), .rsp_error(kv_rsp_error), .rsp_hit(),
    .protocol_error(kv_protocol_error),
    .spill_valid(spill_valid), .spill_ready(spill_ready), .spill_write(spill_write),
    .spill_value(spill_value), .spill_layer(spill_layer), .spill_pos(spill_pos),
    .spill_col(spill_col), .spill_wdata(spill_wdata), .spill_rsp_valid(spill_rsp_valid),
    .spill_rsp_ready(spill_rsp_ready), .spill_rsp_data(spill_rdata),
    .spill_rsp_error(spill_rsp_error)
  );
  assign address_client_valid = {spill_valid, external_valid};
  assign {spill_ready, external_ready} = address_client_ready;
  assign address_client_data[0+:136] = {external_write, external_kind, external_layer,
    external_proj, external_row, external_col, external_wdata};
  assign address_client_data[136+:136] = {spill_write, spill_value ? 4'd10 : 4'd9,
    spill_layer, 3'b0, spill_pos, spill_col, spill_wdata};
  assign {spill_rsp_valid, external_rsp_valid} = address_rsp_valid;
  assign address_rsp_ready = {spill_rsp_ready, external_rsp_ready};
  assign {external_rsp_error, external_rdata} = address_client_response[0+:33];
  assign {spill_rsp_error, spill_rdata} = address_client_response[33+:33];
  anvil_q1_ht_transaction_mux #(.CLIENTS(2), .REQUEST_WIDTH(136), .RESPONSE_WIDTH(33))
  u_scalar_mux (
    .clk(clk), .rst_n(core_rst_n), .client_valid(address_client_valid),
    .client_ready(address_client_ready), .client_data(address_client_data),
    .client_rsp_valid(address_rsp_valid), .client_rsp_ready(address_rsp_ready),
    .client_rsp_data(address_client_response),
    .request_valid(address_valid), .request_ready(address_ready), .request_data(address_request),
    .response_valid(address_rsp_valid_one), .response_ready(address_rsp_ready_one),
    .response_data({address_error, address_rdata})
  );
  anvil_q1_ht_address #(L,H,I,K,D,G,V,S) u_address (
    .clk(clk), .rst_n(core_rst_n), .storage_bf16(bf16),
    .req_valid(address_valid), .req_ready(address_ready),
    .req_write(address_request[135]), .req_kind(address_request[134:131]),
    .req_layer(address_request[130:99]), .req_proj(address_request[98:96]),
    .req_row(address_request[95:64]), .req_col(address_request[63:32]),
    .req_wdata(address_request[31:0]),
    .rsp_valid(address_rsp_valid_one), .rsp_ready(address_rsp_ready_one),
    .rsp_data(address_rdata), .rsp_error(address_error),
    .lookup_valid(lookup_valid[0]), .lookup_ready(lookup_ready[0]),
    .lookup_index(lookup_index[0+:32]), .lookup_rsp_valid(lookup_rsp_valid[0]),
    .lookup_rsp_ready(lookup_rsp_ready[0]), .lookup_base(lookup_result[32+:33]),
    .lookup_length(lookup_result[0+:32]), .lookup_error(lookup_result[65]),
    .ddr_valid(scalar_valid), .ddr_ready(scalar_ready), .ddr_write(scalar_write),
    .ddr_address(scalar_address), .ddr_wdata(scalar_wdata), .ddr_byteenable(scalar_byteenable),
    .ddr_rsp_valid(scalar_rsp_valid), .ddr_rsp_ready(scalar_rsp_ready),
    .ddr_rsp_data(scalar_rdata), .ddr_rsp_error(scalar_error)
  );
  anvil_q1_ht_ddr_scalar u_scalar (
    .clk(clk), .ddr_clk(ddr_clk), .rst_n(rst_n && VALID),
    .req_valid(scalar_valid), .req_ready(scalar_ready), .req_write(scalar_write),
    .req_address(scalar_address), .req_wdata(scalar_wdata), .req_byteenable(scalar_byteenable),
    .rsp_valid(scalar_rsp_valid), .rsp_ready(scalar_rsp_ready),
    .rsp_data(scalar_rdata), .rsp_error(scalar_error), .protocol_error(scalar_protocol_error),
    .avm_address(client_address[33+:33]), .avm_burstcount(client_burstcount[8+:8]),
    .avm_read(client_read[1]), .avm_write(client_write[1]),
    .avm_writedata(client_writedata[512+:512]), .avm_byteenable(client_byteenable[64+:64]),
    .avm_waitrequest(client_waitrequest[1]), .avm_readdata(client_readdata[512+:512]),
    .avm_readdatavalid(client_readdatavalid[1]), .avm_response(client_response[2+:2]),
    .avm_writeresponsevalid(client_writeresponsevalid[1])
  );
  anvil_q1_ht_weight_stream u_stream (
    .clk(clk), .rst_n(core_rst_n), .abort_error(fatal_core),
    .command_valid(block_valid), .command_ready(block_ready),
    .command_kind(block_kind), .command_layer(block_layer), .command_proj(block_proj),
    .command_offset(block_offset), .command_bytes(block_bytes),
    .command_packet_bytes(block_packet_bytes),
    .packet_valid(packet_valid), .packet_ready(packet_ready), .packet_data(packet_data),
    .packet_last(packet_last), .done(block_done), .error(block_error),
    .lookup_valid(lookup_valid[1]), .lookup_ready(lookup_ready[1]),
    .lookup_index(lookup_index[32+:32]), .lookup_rsp_valid(lookup_rsp_valid[1]),
    .lookup_rsp_ready(lookup_rsp_ready[1]), .lookup_base(lookup_result[98+:33]),
    .lookup_length(lookup_result[66+:32]), .lookup_error(lookup_result[131]),
    .dma_valid(dma_valid), .dma_ready(dma_ready), .dma_address(dma_address),
    .dma_bytes(dma_bytes), .dma_done(dma_done), .dma_done_ready(dma_done_ready),
    .dma_abort(dma_abort),
    .dma_error(dma_error), .dma_tiles(dma_tiles),
    .tile_valid(tile_valid), .tile_ready(tile_ready), .tile_beats(tile_beats),
    .release_valid(release_valid), .release_ready(release_ready),
    .read_valid(read_valid), .read_ready(read_ready), .read_address(read_address),
    .read_rsp_valid(read_rsp_valid), .read_rsp_ready(read_rsp_ready),
    .read_data(read_data), .read_mask(read_mask), .tile_error(tiles_error)
  );
  anvil_q1_ht_weight_dma #(.TILE_BEATS(T)) u_dma (
    .clk(clk), .ddr_clk(ddr_clk), .rst_n(rst_n && VALID),
    .request_valid(dma_valid), .request_ready(dma_ready),
    .request_address(dma_address), .request_bytes(dma_bytes),
    .request_abort(dma_abort),
    .completion_valid(dma_done), .completion_ready(dma_done_ready),
    .completion_error(dma_error), .completion_tiles(dma_tiles),
    .load_enable(load_enable), .load_clear(load_clear),
    .load_valid(load_valid && load_enable), .load_ready(dma_load_ready),
    .load_address(load_address), .load_data(load_data), .load_byteenable(load_byteenable),
    .load_last(load_last), .load_done(dma_load_done), .load_error(dma_load_error),
    .load_idle(load_idle_ddr),
    .fill_valid(fill_valid), .fill_ready(fill_ready), .fill_beats(fill_beats),
    .fill_tail(fill_tail), .fill_data_valid(fill_data_valid), .fill_data_ready(fill_data_ready),
    .fill_data(fill_data), .fill_last(fill_last), .fill_abort(fill_abort), .fill_error(tile_fill_error),
    .avm_address(client_address[0+:33]), .avm_burstcount(client_burstcount[0+:8]),
    .avm_read(client_read[0]), .avm_write(client_write[0]),
    .avm_writedata(client_writedata[0+:512]), .avm_byteenable(client_byteenable[0+:64]),
    .avm_waitrequest(client_waitrequest[0]), .avm_readdata(client_readdata[0+:512]),
    .avm_readdatavalid(client_readdatavalid[0]), .avm_response(client_response[0+:2]),
    .avm_writeresponsevalid(client_writeresponsevalid[0]),
    .accepted_read_beats(), .protocol_error(dma_protocol_error)
  );
  anvil_q1_ht_weight_tiles #(.TILE_BEATS(T)) u_tiles (
    .clk(clk), .ddr_clk(ddr_clk), .rst_n(rst_n && VALID),
    .fill_valid(fill_valid), .fill_ready(fill_ready), .fill_bank(),
    .fill_beats(fill_beats), .fill_tail(fill_tail),
    .fill_data_valid(fill_data_valid), .fill_data_ready(fill_data_ready),
    .fill_data(fill_data), .fill_last(fill_last), .fill_abort(fill_abort), .fill_error(tile_fill_error),
    .tile_valid(tile_valid), .tile_ready(tile_ready), .tile_bank(), .tile_beats(tile_beats),
    .tile_tail(), .release_valid(release_valid), .release_ready(release_ready),
    .read_valid(read_valid), .read_ready(read_ready), .read_address(read_address),
    .read_rsp_valid(read_rsp_valid), .read_rsp_ready(read_rsp_ready),
    .read_data(read_data), .read_mask(read_mask), .compute_error(tiles_error)
  );
  anvil_q1_ht_avalon_mux u_avalon (
    .ddr_clk(ddr_clk), .rst_n(ddr_rst_n),
    .client_address(client_address), .client_burstcount(client_burstcount),
    .client_read(client_read), .client_write(client_write), .client_writedata(client_writedata),
    .client_byteenable(client_byteenable), .client_waitrequest(client_waitrequest),
    .client_readdata(client_readdata), .client_readdatavalid(client_readdatavalid),
    .client_response(client_response), .client_writeresponsevalid(client_writeresponsevalid),
    .avm_address(avm_address), .avm_burstcount(avm_burstcount),
    .avm_read(avm_read), .avm_write(avm_write), .avm_writedata(avm_writedata),
    .avm_byteenable(avm_byteenable), .avm_waitrequest(avm_waitrequest),
    .avm_readdata(avm_readdata), .avm_readdatavalid(avm_readdatavalid),
    .avm_response(avm_response), .avm_writeresponsevalid(avm_writeresponsevalid),
    .protocol_error(mux_error)
  );
endmodule
