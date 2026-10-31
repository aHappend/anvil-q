module anvil_q2_ht2_configuration #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  parameter NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter CACHE_BLOCK=16
) (
  input wire clk, rst_n, annul, invalidate,
  input wire operation_busy, quiescent, ddr_ready, sticky_fault, cache_valid,
  input wire cfg_valid, cfg_write,
  input wire [15:0] cfg_addr,
  input wire [31:0] cfg_wdata,
  output wire cfg_ready, cfg_rsp_valid,
  input wire cfg_rsp_ready,
  output wire [31:0] cfg_rdata,
  output wire cfg_error,
  output wire [5:0] ht2_mode, mode_change_mask,
  output wire [2:0] ht2_k,
  output wire k_changed,
  output wire validating, model_loaded, configuration_changed,
  output wire legacy_weight_mode,
  output wire [1:0] legacy_cache_mode,
  output wire [32:0] kv_base, kv_length,
  input wire desc_req_valid,
  output wire desc_req_ready,
  input wire [8:0] desc_req_index,
  output wire desc_rsp_valid,
  input wire desc_rsp_ready,
  output wire [511:0] desc_rsp_data,
  output wire desc_rsp_error
);
  wire forwarded_valid, forwarded_write, forwarded_ready, forwarded_rsp_valid;
  wire forwarded_rsp_ready, forwarded_error;
  wire [15:0] forwarded_addr;
  wire [31:0] forwarded_wdata, forwarded_rdata;
  wire legacy=ht2_mode[1:0]==0;
  wire mode_changed=|mode_change_mask;
  wire legacy_rst_n=rst_n && !mode_changed && !invalidate;
  wire parent_cfg_ready, parent_cfg_valid, parent_cfg_error;
  wire native_cfg_ready, native_cfg_valid, native_cfg_error;
  wire [31:0] parent_cfg_data, native_cfg_data;
  wire parent_validating, parent_loaded, parent_changed;
  wire native_validating, native_loaded, native_changed;
  wire [32:0] parent_base, parent_length, native_base, native_length;
  wire parent_desc_ready, parent_desc_valid, parent_desc_error;
  wire native_desc_ready, native_desc_valid, native_desc_error;
  wire [511:0] parent_desc_data, native_desc_data;
  wire parent_weight;
  wire [1:0] parent_cache;
  wire descriptor_enable=rst_n && !annul && !invalidate && !mode_changed;

  anvil_q2_ht2_mode_control mode_control (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .operation_busy(operation_busy || validating),.quiescent(quiescent),
    .cache_valid(cache_valid),.sticky_fault(sticky_fault),
    .cfg_valid(cfg_valid),.cfg_write(cfg_write),.cfg_addr(cfg_addr),.cfg_wdata(cfg_wdata),
    .cfg_ready(cfg_ready),.cfg_rsp_valid(cfg_rsp_valid),.cfg_rsp_ready(cfg_rsp_ready),
    .cfg_rdata(cfg_rdata),.cfg_error(cfg_error),.ht2_mode(ht2_mode),
    .mode_change_mask(mode_change_mask),.ht2_k(ht2_k),.k_changed(k_changed),
    .legacy_cfg_valid(forwarded_valid),.legacy_cfg_write(forwarded_write),
    .legacy_cfg_addr(forwarded_addr),.legacy_cfg_wdata(forwarded_wdata),
    .legacy_cfg_ready(forwarded_ready),.legacy_cfg_rsp_valid(forwarded_rsp_valid),
    .legacy_cfg_rsp_ready(forwarded_rsp_ready),.legacy_cfg_rdata(forwarded_rdata),
    .legacy_cfg_error(forwarded_error)
  );
  anvil_q2_ht_configuration #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
    .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
    .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
    .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_BLOCK(CACHE_BLOCK)
  ) parent_configuration (
    .clk(clk),.rst_n(legacy_rst_n),.annul(annul),
    .operation_busy(operation_busy),.quiescent(quiescent),.ddr_ready(ddr_ready),
    .sticky_fault(sticky_fault),
    .cfg_valid(forwarded_valid && legacy),.cfg_write(forwarded_write),
    .cfg_addr(forwarded_addr),.cfg_wdata(forwarded_wdata),
    .cfg_ready(parent_cfg_ready),.cfg_rsp_valid(parent_cfg_valid),
    .cfg_rsp_ready(forwarded_rsp_ready && legacy),
    .cfg_rdata(parent_cfg_data),.cfg_error(parent_cfg_error),
    .validating(parent_validating),.model_loaded(parent_loaded),
    .configuration_changed(parent_changed),.weight_mode(parent_weight),
    .cache_mode(parent_cache),.kv_base(parent_base),.kv_length(parent_length),
    .desc_req_valid(descriptor_enable && legacy && desc_req_valid),
    .desc_req_ready(parent_desc_ready),.desc_req_index(desc_req_index),
    .desc_rsp_valid(parent_desc_valid),.desc_rsp_ready(desc_rsp_ready && legacy),
    .desc_rsp_data(parent_desc_data),.desc_rsp_error(parent_desc_error)
  );
  anvil_q2_ht2_native_configuration #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
    .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
    .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
    .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_BLOCK(CACHE_BLOCK)
  ) native_configuration (
    .clk(clk),.rst_n(rst_n),.annul(annul),.invalidate(invalidate || mode_changed),
    .ht2_mode(ht2_mode),.operation_busy(operation_busy),.quiescent(quiescent),
    .ddr_ready(ddr_ready),.sticky_fault(sticky_fault),
    .cfg_valid(forwarded_valid && !legacy),.cfg_write(forwarded_write),
    .cfg_addr(forwarded_addr),.cfg_wdata(forwarded_wdata),
    .cfg_ready(native_cfg_ready),.cfg_rsp_valid(native_cfg_valid),
    .cfg_rsp_ready(forwarded_rsp_ready && !legacy),
    .cfg_rdata(native_cfg_data),.cfg_error(native_cfg_error),
    .validating(native_validating),.model_loaded(native_loaded),
    .configuration_changed(native_changed),.kv_base(native_base),.kv_length(native_length),
    .desc_req_valid(descriptor_enable && !legacy && desc_req_valid),
    .desc_req_ready(native_desc_ready),.desc_req_index(desc_req_index),
    .desc_rsp_valid(native_desc_valid),.desc_rsp_ready(desc_rsp_ready && !legacy),
    .desc_rsp_data(native_desc_data),.desc_rsp_error(native_desc_error)
  );

  assign forwarded_ready=legacy ? parent_cfg_ready : native_cfg_ready;
  assign forwarded_rsp_valid=legacy ? parent_cfg_valid : native_cfg_valid;
  assign forwarded_rdata=legacy ? parent_cfg_data : native_cfg_data;
  assign forwarded_error=legacy ? parent_cfg_error : native_cfg_error;
  assign validating=rst_n && (legacy ? parent_validating : native_validating);
  assign model_loaded=descriptor_enable && (legacy ? parent_loaded : native_loaded);
  assign configuration_changed=rst_n &&
    (mode_changed || invalidate || (legacy ? parent_changed : native_changed));
  assign legacy_weight_mode=rst_n && legacy && parent_weight;
  assign legacy_cache_mode=rst_n && legacy ? parent_cache : 2'd0;
  assign kv_base=model_loaded ? (legacy ? parent_base : native_base) : 33'd0;
  assign kv_length=model_loaded ? (legacy ? parent_length : native_length) : 33'd0;
  assign desc_req_ready=descriptor_enable &&
    (legacy ? parent_desc_ready : native_desc_ready);
  assign desc_rsp_valid=descriptor_enable &&
    (legacy ? parent_desc_valid : native_desc_valid);
  assign desc_rsp_data=desc_rsp_valid ?
    (legacy ? parent_desc_data : native_desc_data) : 512'd0;
  assign desc_rsp_error=desc_rsp_valid && (legacy ? parent_desc_error : native_desc_error);
endmodule
