module anvil_q1_ht3_top #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2, HEAD_DIM = 64, GROUP_SIZE = 128,
  parameter AWQ_BITS = 4, VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768,
  parameter LANES = 64, BANKS = 8, LANES_PER_BANK = 8, DDR_WIDTH = 512,
  parameter TILE_BEATS = 256, KV_WINDOW = 128, FLASH_TILE = 16
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
  input wire avm_writeresponsevalid,
  input wire batch_valid,
  output wire batch_ready,
  input wire [2:0] batch_count,
  input wire [127:0] batch_token_ids,
  input wire [11:0] batch_parents,
  output wire commit_valid,
  input wire commit_ready,
  output wire [2:0] commit_count,
  output wire [127:0] commit_token_ids,
  output wire [31:0] commit_position,
  output wire commit_error
);
  import anvil_q1_ht3_layout_pkg::*;
  localparam LEGAL = geometry_legal(NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,
    NUM_Q_HEADS,NUM_KV_HEADS,HEAD_DIM,GROUP_SIZE,VOCAB_SIZE,MAX_SEQ_LEN) &&
    AWQ_BITS == 4 && LANES == 64 && BANKS == 8 && LANES_PER_BANK == 8 &&
    DDR_WIDTH == 512 && TILE_BEATS >= 1 && TILE_BEATS <= 256 &&
    KV_WINDOW >= 1 && KV_WINDOW <= 128 && KV_WINDOW <= MAX_SEQ_LEN &&
    FLASH_TILE >= 1 && FLASH_TILE <= 128;
  initial if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 top geometry");
  generate if (!LEGAL) begin: g_invalid
    assign token_ready = 0;
    assign logit_valid = 0;
    assign logit_index = 0;
    assign logit_data = 0;
    assign done = 0;
    assign error = 0;
    assign csr_ready = 0;
    assign csr_rsp_valid = 0;
    assign csr_rdata = 0;
    assign csr_error = 0;
    assign load_ready = 0;
    assign load_done = 0;
    assign load_error = 0;
    assign avm_address = 0;
    assign avm_burstcount = 0;
    assign avm_read = 0;
    assign avm_write = 0;
    assign avm_writedata = 0;
    assign avm_byteenable = 0;
    assign batch_ready = 0;
    assign commit_valid = 0;
    assign commit_count = 0;
    assign commit_token_ids = 0;
    assign commit_position = 0;
    assign commit_error = 0;
  end else begin: g_legal
    wire run_n, ddr_run_n;
    wire [3:0] configuration;
    wire [2:0] extension_control;
    wire [1:0] cache_format = extension_control[1:0] == 0 && configuration[1:0] == 1 ?
      2'd1 : extension_control[1:0];
    wire [32:0] extension_base;
    wire [31:0] extension_length, image_generation;
    wire [15:0] threshold;
    wire initialized, image_valid, finite_image, sticky_error, configuration_busy;
    wire control_invalidate_image, control_invalidate_prefix, descriptor_invalidate_prefix;
    wire legacy_valid, legacy_write, legacy_ready, legacy_rsp_valid, legacy_rsp_ready;
    wire [15:0] legacy_address;
    wire [31:0] legacy_wdata, legacy_rdata;
    wire legacy_error;
    wire load_busy, load_failed, acquire_pending, image_modified, clear_load_error;
    wire execution_busy, pending_results, execution_token_ready, execution_batch_ready;
    wire execution_done, execution_error;
    wire [2:0] accepted_tokens;
    wire completed_batch;
    wire [31:0] eligible_bytes, avoided_bytes;
    wire lookup_valid, lookup_ready, lookup_rsp_valid, lookup_rsp_ready, lookup_error;
    wire [31:0] lookup_index, lookup_length;
    wire [32:0] lookup_base;
    wire transport_available, transport_error, mux_error, mux_busy, ddr_read_beat;
    wire [3:0] memory_valid, memory_ready, memory_rsp_valid, memory_rsp_ready;
    wire [32:0] execution_read_address, execution_write_address, validation_address, upload_address;
    wire [7:0] execution_read_beats, validation_beats;
    wire [511:0] execution_write_data, upload_data, memory_data;
    wire [63:0] execution_write_mask, upload_mask;
    wire memory_error;
    wire transport_req_valid, transport_req_ready, transport_req_write;
    wire [32:0] transport_req_address;
    wire [7:0] transport_req_beats;
    wire [511:0] transport_req_data, transport_rsp_data;
    wire [63:0] transport_req_mask;
    wire transport_rsp_valid, transport_rsp_ready, transport_rsp_write;
    wire transport_rsp_last, transport_rsp_error;
    reg csr_owned;
    reg [63:0] token_cycles, held_read_beats, physical_read_beats;
    wire snapshot_valid;
    wire [63:0] snapshot_data;
    wire csr_active = csr_owned || csr_valid || csr_rsp_valid || legacy_valid || legacy_rsp_valid;
    wire fatal_error = transport_error || mux_error;
    wire admission = run_n && initialized && image_valid && transport_available &&
      !sticky_error && !fatal_error && !load_busy && !acquire_pending &&
      !configuration_busy && !csr_active && !control_invalidate_image &&
      !descriptor_invalidate_prefix && !image_modified;
    wire command_accepted = (token_valid && token_ready) || (batch_valid && batch_ready);
    wire engine_ready = run_n && initialized && image_valid && transport_available &&
      !sticky_error && !fatal_error && !execution_busy && !load_busy &&
      !acquire_pending && !configuration_busy;
    wire loader_acquire = initialized && transport_available && !execution_busy &&
      !pending_results && !configuration_busy && !csr_active && !fatal_error && !mux_busy;
    anvil_q1_ht3_reset_sync u_core_reset(clk,rst_n,run_n);
    anvil_q1_ht3_reset_sync u_ddr_reset(ddr_clk,rst_n,ddr_run_n);
    assign token_ready = run_n && admission && execution_token_ready;
    assign batch_ready = run_n && admission && execution_batch_ready;
    assign done = run_n && execution_done;
    assign error = done && execution_error;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin csr_owned <= 0; token_cycles <= 0; held_read_beats <= 0; end
      else if (run_n) begin
        if (csr_valid && csr_ready) csr_owned <= 1;
        if (csr_rsp_valid && csr_rsp_ready) csr_owned <= 0;
        if (command_accepted) token_cycles <= 0;
        else if (execution_busy && !execution_done) token_cycles <= token_cycles + 1'b1;
        if (snapshot_valid) held_read_beats <= snapshot_data;
      end
    end
    always @(posedge ddr_clk or negedge rst_n) begin
      if (!rst_n) physical_read_beats <= 0;
      else if (ddr_run_n && ddr_read_beat) physical_read_beats <= physical_read_beats + 1'b1;
    end
    anvil_q1_ht3_mailbox #(.WIDTH(64)) u_legacy_read_snapshot (
      .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n),
      .source_valid(1'b1), .source_ready(), .source_data(physical_read_beats),
      .destination_valid(snapshot_valid), .destination_ready(1'b1), .destination_data(snapshot_data)
    );
    anvil_q1_ht3_control u_control (
      .clk(clk), .ddr_clk(ddr_clk), .rst_n(rst_n),
      .initialized(initialized), .image_valid(image_valid),
      .execution_busy(execution_busy || configuration_busy || mux_busy),
      .image_loading(load_busy || acquire_pending), .pending_results(pending_results),
      .sticky_error(sticky_error || fatal_error), .ddr_read_beat(ddr_read_beat),
      .accepted_tokens(accepted_tokens), .completed_batch(completed_batch),
      .eligible_bytes(eligible_bytes), .avoided_bytes(avoided_bytes),
      .configuration(configuration), .sparse_threshold(threshold),
      .invalidate_image(control_invalidate_image), .invalidate_prefix(control_invalidate_prefix),
      .extension_control(extension_control), .extension_base(extension_base),
      .extension_length(extension_length),
      .csr_valid(csr_valid), .csr_write(csr_write), .csr_address(csr_address),
      .csr_wdata(csr_wdata), .csr_ready(csr_ready), .csr_rsp_valid(csr_rsp_valid),
      .csr_rsp_ready(csr_rsp_ready), .csr_rdata(csr_rdata), .csr_error(csr_error),
      .legacy_valid(legacy_valid), .legacy_write(legacy_write), .legacy_address(legacy_address),
      .legacy_wdata(legacy_wdata), .legacy_ready(legacy_ready), .legacy_rsp_valid(legacy_rsp_valid),
      .legacy_rsp_ready(legacy_rsp_ready), .legacy_rdata(legacy_rdata), .legacy_error(legacy_error)
    );
    anvil_q1_ht3_descriptors #(
      NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_KV_HEADS,HEAD_DIM,GROUP_SIZE,VOCAB_SIZE,MAX_SEQ_LEN
    ) u_descriptors (
      .clk(clk), .rst_n(rst_n), .format(configuration[1:0]), .kv_format(cache_format),
      .int8_weights(extension_control[2]), .extension_base(extension_base),
      .extension_length(extension_length), .invalidate_image(control_invalidate_image),
      .csr_valid(legacy_valid), .csr_write(legacy_write), .csr_address(legacy_address),
      .csr_wdata(legacy_wdata), .csr_ready(legacy_ready), .csr_rsp_valid(legacy_rsp_valid),
      .csr_rsp_ready(legacy_rsp_ready), .csr_rdata(legacy_rdata), .csr_error(legacy_error),
      .engine_busy(execution_busy || pending_results || mux_busy),
      .load_busy(load_busy || acquire_pending), .load_failed(load_failed),
      .emif_initialized(transport_available),
      .fault_event(fatal_error || error || (csr_rsp_valid && csr_error)),
      .image_modified(image_modified), .engine_ready(engine_ready),
      .token_cycles(token_cycles), .read_beats(held_read_beats),
      .initialized(initialized), .image_valid(image_valid), .finite_image(finite_image),
      .sticky_error(sticky_error), .clear_load_error(clear_load_error),
      .configuration_busy(configuration_busy), .invalidate_prefix(descriptor_invalidate_prefix),
      .image_generation(image_generation),
      .lookup_valid(lookup_valid), .lookup_ready(lookup_ready), .lookup_index(lookup_index),
      .lookup_rsp_valid(lookup_rsp_valid), .lookup_rsp_ready(lookup_rsp_ready),
      .lookup_base(lookup_base), .lookup_length(lookup_length), .lookup_error(lookup_error),
      .dma_valid(memory_valid[2]), .dma_ready(memory_ready[2]), .dma_address(validation_address),
      .dma_burstcount(validation_beats), .dma_data_valid(memory_rsp_valid[2]),
      .dma_data_ready(memory_rsp_ready[2]), .dma_data(memory_data), .dma_error(memory_error)
    );
    anvil_q1_ht3_image_loader u_loader (
      .clk(clk), .ddr_clk(ddr_clk), .rst_n(rst_n),
      .allow_acquire(loader_acquire), .clear_error(clear_load_error),
      .acquire_pending(acquire_pending), .busy(load_busy), .failed(load_failed),
      .image_modified(image_modified), .load_valid(load_valid), .load_ready(load_ready),
      .load_address(load_address), .load_data(load_data), .load_byteenable(load_byteenable),
      .load_last(load_last), .load_done(load_done), .load_error(load_error),
      .dma_valid(memory_valid[3]), .dma_ready(memory_ready[3]), .dma_address(upload_address),
      .dma_data(upload_data), .dma_byteenable(upload_mask),
      .dma_rsp_valid(memory_rsp_valid[3]), .dma_rsp_ready(memory_rsp_ready[3]), .dma_error(memory_error)
    );
    anvil_q1_ht3_execution #(
      NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,HEAD_DIM,
      GROUP_SIZE,VOCAB_SIZE,MAX_SEQ_LEN,TILE_BEATS,FLASH_TILE
    ) u_execution (
      .clk(clk), .rst_n(rst_n), .new_sequence(new_sequence),
      .invalidate_image(control_invalidate_prefix || descriptor_invalidate_prefix || image_modified),
      .abort_error(fatal_error), .image_valid(image_valid), .finite_image(finite_image),
      .configuration(configuration), .sparse_threshold(threshold),
      .token_valid(token_valid && admission), .token_ready(execution_token_ready),
      .token_id(token_id), .token_pos(token_pos), .batch_valid(batch_valid && admission),
      .batch_ready(execution_batch_ready), .batch_count(batch_count),
      .batch_token_ids(batch_token_ids), .batch_parents(batch_parents),
      .logit_valid(logit_valid), .logit_ready(logit_ready), .logit_index(logit_index),
      .logit_data(logit_data), .commit_valid(commit_valid), .commit_ready(commit_ready),
      .commit_count(commit_count), .commit_token_ids(commit_token_ids),
      .commit_position(commit_position), .commit_error(commit_error),
      .busy(execution_busy), .pending_results(pending_results), .done(execution_done),
      .error(execution_error), .accepted_tokens(accepted_tokens), .completed_batch(completed_batch),
      .eligible_bytes(eligible_bytes), .avoided_bytes(avoided_bytes),
      .lookup_valid(lookup_valid), .lookup_ready(lookup_ready), .lookup_index(lookup_index),
      .lookup_rsp_valid(lookup_rsp_valid), .lookup_rsp_ready(lookup_rsp_ready),
      .lookup_base(lookup_base), .lookup_length(lookup_length), .lookup_error(lookup_error),
      .read_dma_valid(memory_valid[0]), .read_dma_ready(memory_ready[0]),
      .read_dma_address(execution_read_address), .read_dma_burstcount(execution_read_beats),
      .read_dma_data_valid(memory_rsp_valid[0]), .read_dma_data_ready(memory_rsp_ready[0]),
      .read_dma_data(memory_data), .read_dma_error(memory_error),
      .write_dma_valid(memory_valid[1]), .write_dma_ready(memory_ready[1]),
      .write_dma_address(execution_write_address), .write_dma_data(execution_write_data),
      .write_dma_byteenable(execution_write_mask), .write_dma_rsp_valid(memory_rsp_valid[1]),
      .write_dma_rsp_ready(memory_rsp_ready[1]), .write_dma_error(memory_error),
      .kv_format(cache_format), .int8_weights(extension_control[2]),
      .extension_base(extension_base), .extension_length(extension_length),
      .image_generation(image_generation)
    );
    anvil_q1_ht3_dma_mux u_dma_mux (
      .clk(clk), .rst_n(rst_n), .client_valid(memory_valid), .client_ready(memory_ready),
      .client_write(4'b1010),
      .client_address({upload_address,validation_address,execution_write_address,execution_read_address}),
      .client_burstcount({8'd1,validation_beats,8'd1,execution_read_beats}),
      .client_writedata({upload_data,512'b0,execution_write_data,512'b0}),
      .client_byteenable({upload_mask,64'hffffffffffffffff,execution_write_mask,64'hffffffffffffffff}),
      .client_rsp_valid(memory_rsp_valid), .client_rsp_ready(memory_rsp_ready),
      .client_rsp_data(memory_data), .client_rsp_error(memory_error),
      .busy(mux_busy), .protocol_error(mux_error),
      .req_valid(transport_req_valid), .req_ready(transport_req_ready), .req_write(transport_req_write),
      .req_address(transport_req_address), .req_burstcount(transport_req_beats),
      .req_writedata(transport_req_data), .req_byteenable(transport_req_mask),
      .rsp_valid(transport_rsp_valid), .rsp_ready(transport_rsp_ready), .rsp_write(transport_rsp_write),
      .rsp_last(transport_rsp_last), .rsp_error(transport_rsp_error), .rsp_data(transport_rsp_data)
    );
    anvil_q1_ht3_transport u_transport (
      .clk(clk), .ddr_clk(ddr_clk), .rst_n(rst_n),
      .req_valid(transport_req_valid), .req_ready(transport_req_ready), .req_write(transport_req_write),
      .req_address(transport_req_address), .req_burstcount(transport_req_beats),
      .req_writedata(transport_req_data), .req_byteenable(transport_req_mask),
      .rsp_valid(transport_rsp_valid), .rsp_ready(transport_rsp_ready), .rsp_write(transport_rsp_write),
      .rsp_last(transport_rsp_last), .rsp_error(transport_rsp_error), .rsp_data(transport_rsp_data),
      .available(transport_available), .protocol_error(transport_error), .ddr_read_beat(ddr_read_beat),
      .avm_address(avm_address), .avm_burstcount(avm_burstcount), .avm_read(avm_read),
      .avm_write(avm_write), .avm_writedata(avm_writedata), .avm_byteenable(avm_byteenable),
      .avm_waitrequest(avm_waitrequest), .avm_readdata(avm_readdata),
      .avm_readdatavalid(avm_readdatavalid), .avm_response(avm_response),
      .avm_writeresponsevalid(avm_writeresponsevalid)
    );
  end endgenerate
endmodule
