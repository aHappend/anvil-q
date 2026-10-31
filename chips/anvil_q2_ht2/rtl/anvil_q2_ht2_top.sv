module anvil_q2_ht2_top #(
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
  input wire [1:0] avm_response,
  input wire draft_valid,
  output wire draft_ready,
  input wire [2:0] draft_count,
  input wire [127:0] draft_ids,
  input wire [7:0] draft_parent,
  input wire [31:0] draft_pos,
  input wire draft_new_sequence,
  output wire batch_valid,
  input wire batch_ready,
  output wire [2:0] batch_accepted,
  output wire [3:0] batch_mask,
  output wire [31:0] batch_next_token, batch_position,
  output wire batch_error,
  output wire [1:0] logit_slot,
  output wire [31:0] logit_fp32
);
  localparam SG=GROUP_SIZE>=1 ? GROUP_SIZE : 1;
  localparam CB=CACHE_BLOCK>=1 ? CACHE_BLOCK : 1;
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=1536 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=8960 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 &&
    NUM_KV_HEADS>=1 && NUM_KV_HEADS<=2 &&
    HEAD_DIM>=2 && HEAD_DIM<=128 && (HEAD_DIM & 1)==0 &&
    HIDDEN_SIZE==NUM_Q_HEADS*HEAD_DIM &&
    (NUM_KV_HEADS==1 || (NUM_KV_HEADS==2 && (NUM_Q_HEADS & 1)==0)) &&
    (HIDDEN_SIZE & 7)==0 && (INTERMEDIATE_SIZE & 7)==0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7)==0 &&
    GROUP_SIZE>=1 && GROUP_SIZE<=128 && (GROUP_SIZE & (GROUP_SIZE-1))==0 &&
    (HIDDEN_SIZE & (SG-1))==0 && (INTERMEDIATE_SIZE & (SG-1))==0 &&
    VOCAB_SIZE>=1 && VOCAB_SIZE<=151936 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    BANKS==16 && LANES_PER_BANK==8 && DDR_DATA_WIDTH==512 &&
    TILE_SLOTS>=2 && TILE_SLOTS<=8 &&
    READ_OUTSTANDING>=1 && READ_OUTSTANDING<=16 &&
    QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    CACHE_BLOCK>=1 && CACHE_BLOCK<=128 && (CACHE_BLOCK & (CACHE_BLOCK-1))==0 &&
    (HEAD_DIM & (CB-1))==0 && HOT_BLOCKS>=1 && HOT_BLOCKS<=64;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: top geometry or production width");
    assign token_ready=0; assign logit_valid=0; assign logit_index=0;
    assign logit_data=0; assign done=0; assign error=0; assign cancel_done=0;
    assign cfg_ready=0; assign cfg_rsp_valid=0; assign cfg_rdata=0; assign cfg_error=0;
    assign host_req_ready=0; assign host_rsp_valid=0;
    assign host_rsp_rdata=0; assign host_rsp_error=0;
    assign avm_address=0; assign avm_read=0; assign avm_write=0;
    assign avm_writedata=0; assign avm_byteenable=0; assign avm_burstcount=0;
    assign draft_ready=0; assign batch_valid=0; assign batch_accepted=0;
    assign batch_mask=0; assign batch_next_token=0; assign batch_position=0;
    assign batch_error=0; assign logit_slot=0; assign logit_fp32=0;
  end else begin: implementation
    wire [5:0] mode, mode_change_mask;
    wire [2:0] width;
    wire k_changed;
    wire legacy=mode[1:0]==0;
    wire mode_changed=|mode_change_mask;
    wire parent_rst_n=rst_n && legacy && !mode_changed;
    reg legacy_active, legacy_host_pending;
    reg legacy_retiring, legacy_retiring_error, legacy_completion, legacy_completion_error;
    reg native_active, native_legacy_token;
    reg draining, aborted_request, abort_response, cancel_pending, cancel_seen;
    reg completion, completion_error, cancellation_complete, sticky_fault;
    reg [1:0] settle;
    wire forwarded_valid, forwarded_write, forwarded_ready, forwarded_rsp_valid;
    wire forwarded_rsp_ready, forwarded_error;
    wire [15:0] forwarded_addr;
    wire [31:0] forwarded_wdata, forwarded_rdata;
    wire parent_cfg_ready, parent_cfg_valid, parent_cfg_error;
    wire [31:0] parent_cfg_data;
    wire native_cfg_ready, native_cfg_valid, native_cfg_error;
    wire [31:0] native_cfg_data;
    wire validating, loaded, configuration_changed;
    wire [32:0] cache_base, cache_length;
    wire cache_valid;
    wire native_busy, native_idle, native_fault, fabric_idle, fabric_fault;
    wire host_idle, host_memory_idle, host_write_accepted;
    wire native_token_ready, native_response_valid, native_response_error;
    wire [2:0] native_accepted;
    wire [3:0] native_mask;
    wire [31:0] native_next, native_position, committed_position;
    wire native_commit;
    wire native_logit_valid;
    wire [1:0] native_logit_slot;
    wire [31:0] native_logit_index, native_logit_fp32;
    wire signed [31:0] native_logit_data;
    wire parent_token_ready, parent_done, parent_error, parent_cancel_done;
    wire parent_logit_valid;
    wire [31:0] parent_logit_index;
    wire signed [31:0] parent_logit_data;
    wire legacy_logit_ready, legacy_logit_valid, legacy_logit_idle;
    wire [31:0] legacy_logit_index, legacy_logit_fp32;
    wire signed [31:0] legacy_logit_data;
    wire parent_host_ready, parent_host_valid, parent_host_error;
    wire [511:0] parent_host_data;
    wire [32:0] parent_address, native_address;
    wire parent_read, parent_write, native_read, native_write;
    wire [511:0] parent_wdata, native_wdata;
    wire [63:0] parent_be, native_be;
    wire [4:0] parent_burst, native_burst;
    wire native_host_ready, native_host_valid, native_host_error;
    wire [511:0] native_host_data;
    wire host_mem_valid, host_mem_ready, host_mem_write;
    wire [32:0] host_mem_address;
    wire [511:0] host_mem_wdata, host_mem_rsp_data;
    wire [63:0] host_mem_be;
    wire host_mem_rsp_valid, host_mem_rsp_ready, host_mem_rsp_error;
    wire desc_valid, desc_ready, desc_rsp_valid, desc_rsp_ready, desc_rsp_error;
    wire [8:0] desc_index;
    wire [511:0] desc_data;
    wire weight_valid, weight_ready, fill_valid, fill_ready, fill_error, fill_last;
    wire [32:0] weight_address;
    wire [6:0] weight_beats;
    wire [511:0] fill_data;
    wire scalar_valid, scalar_ready, scalar_rsp_valid, scalar_rsp_ready, scalar_rsp_error;
    wire [32:0] scalar_address;
    wire [511:0] scalar_data;
    wire kv_valid, kv_ready, kv_write, kv_rsp_valid, kv_rsp_ready, kv_rsp_error;
    wire [32:0] kv_address;
    wire [511:0] kv_wdata, kv_data;
    wire [63:0] kv_be;
    wire [2:0] client_ready, client_rsp_valid, client_rsp_error;
    wire [1535:0] client_data;
    wire [63:0] accepted_read_beats, accepted_write_beats;
    wire cancel_start=cancel && !cancel_seen;
    wire external_fault=ddr_fault || fabric_fault;
    wire abort_start=rst_n && !legacy && !draining && !abort_response &&
      (cancel_start || external_fault);
    wire inhibited=cancel || draining || abort_response || external_fault;
    wire resources_safe=native_idle && fabric_idle && host_memory_idle;
    wire operation_busy=legacy ? legacy_active :
      (native_active || native_busy || draining || abort_response);
    wire quiescent=rst_n && !legacy_active && !legacy_host_pending &&
      !native_active && native_idle && fabric_idle && host_idle &&
      !draining && !abort_response && !validating && !cancel && !ddr_fault &&
      (!legacy || parent_cfg_ready);
    wire native_enable=rst_n && !legacy && !inhibited && !native_active &&
      loaded && ddr_ready && !validating && !cfg_valid && !cfg_rsp_valid &&
      !host_req_valid && host_idle && fabric_idle;
    wire native_offer=native_enable && (token_valid || draft_valid);
    wire native_transfer=native_offer && native_token_ready;
    wire native_response_ready=native_legacy_token || batch_ready;
    wire native_batch_transfer=native_response_valid && native_response_ready && !inhibited;
    wire native_invalidate=mode_changed || configuration_changed;
    wire parent_token_offer=legacy && !legacy_active && !mode_changed && !cfg_valid &&
      !cfg_rsp_valid && token_valid;
    wire legacy_logit_annul=!legacy || mode_changed || cancel || ddr_fault ||
      parent_cancel_done;

    anvil_q2_ht2_mode_control mode_control (
      .clk(clk),.rst_n(rst_n),.annul(cancel || abort_start),
      .operation_busy(operation_busy || validating),.quiescent(quiescent),
      .cache_valid(cache_valid),.sticky_fault(sticky_fault || native_fault),
      .cfg_valid(cfg_valid),.cfg_write(cfg_write),.cfg_addr(cfg_addr),.cfg_wdata(cfg_wdata),
      .cfg_ready(cfg_ready),.cfg_rsp_valid(cfg_rsp_valid),.cfg_rsp_ready(cfg_rsp_ready),
      .cfg_rdata(cfg_rdata),.cfg_error(cfg_error),.ht2_mode(mode),
      .mode_change_mask(mode_change_mask),.ht2_k(width),.k_changed(k_changed),
      .legacy_cfg_valid(forwarded_valid),.legacy_cfg_write(forwarded_write),
      .legacy_cfg_addr(forwarded_addr),.legacy_cfg_wdata(forwarded_wdata),
      .legacy_cfg_ready(forwarded_ready),.legacy_cfg_rsp_valid(forwarded_rsp_valid),
      .legacy_cfg_rsp_ready(forwarded_rsp_ready),.legacy_cfg_rdata(forwarded_rdata),
      .legacy_cfg_error(forwarded_error)
    );
    anvil_q2_ht2_native_configuration #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
      .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
      .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_BLOCK(CACHE_BLOCK)
    ) native_configuration (
      .clk(clk),.rst_n(rst_n),.annul(cancel || abort_start),.invalidate(mode_changed),
      .ht2_mode(mode),.operation_busy(operation_busy),.quiescent(quiescent),
      .ddr_ready(ddr_ready),.sticky_fault(sticky_fault || native_fault),
      .cfg_valid(forwarded_valid && !legacy),.cfg_write(forwarded_write),
      .cfg_addr(forwarded_addr),.cfg_wdata(forwarded_wdata),
      .cfg_ready(native_cfg_ready),.cfg_rsp_valid(native_cfg_valid),
      .cfg_rsp_ready(forwarded_rsp_ready && !legacy),
      .cfg_rdata(native_cfg_data),.cfg_error(native_cfg_error),
      .validating(validating),.model_loaded(loaded),
      .configuration_changed(configuration_changed),
      .kv_base(cache_base),.kv_length(cache_length),
      .desc_req_valid(desc_valid),.desc_req_ready(desc_ready),.desc_req_index(desc_index),
      .desc_rsp_valid(desc_rsp_valid),.desc_rsp_ready(desc_rsp_ready),
      .desc_rsp_data(desc_data),.desc_rsp_error(desc_rsp_error)
    );
    anvil_q2_ht_top #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
      .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
      .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),.BANKS(BANKS),
      .LANES_PER_BANK(LANES_PER_BANK),.DDR_DATA_WIDTH(DDR_DATA_WIDTH),
      .TILE_SLOTS(TILE_SLOTS),.READ_OUTSTANDING(READ_OUTSTANDING),
      .QUEUE_DEPTH(QUEUE_DEPTH),.CACHE_BLOCK(CACHE_BLOCK),.HOT_BLOCKS(HOT_BLOCKS)
    ) legacy_product (
      .clk(clk),.rst_n(parent_rst_n),.cancel(cancel && legacy),
      .ddr_ready(ddr_ready),.ddr_fault(ddr_fault && legacy),
      .token_valid(parent_token_offer),.token_ready(parent_token_ready),
      .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),
      .token_phase(token_phase),.logit_valid(parent_logit_valid),
      .logit_ready(legacy_logit_ready),.logit_index(parent_logit_index),
      .logit_data(parent_logit_data),.done(parent_done),.error(parent_error),
      .cancel_done(parent_cancel_done),
      .cfg_valid(forwarded_valid && legacy),.cfg_write(forwarded_write),
      .cfg_addr(forwarded_addr),.cfg_wdata(forwarded_wdata),
      .cfg_ready(parent_cfg_ready),.cfg_rsp_valid(parent_cfg_valid),
      .cfg_rsp_ready(forwarded_rsp_ready && legacy),
      .cfg_rdata(parent_cfg_data),.cfg_error(parent_cfg_error),
      .host_req_valid(host_req_valid && legacy && !cfg_valid && !cfg_rsp_valid),
      .host_req_write(host_req_write),.host_req_addr(host_req_addr),
      .host_req_wdata(host_req_wdata),.host_req_be(host_req_be),
      .host_req_ready(parent_host_ready),.host_rsp_valid(parent_host_valid),
      .host_rsp_ready(host_rsp_ready && legacy),
      .host_rsp_rdata(parent_host_data),.host_rsp_error(parent_host_error),
      .avm_address(parent_address),.avm_read(parent_read),.avm_write(parent_write),
      .avm_writedata(parent_wdata),.avm_byteenable(parent_be),.avm_burstcount(parent_burst),
      .avm_waitrequest(avm_waitrequest || !legacy),.avm_readdata(avm_readdata),
      .avm_readdatavalid(avm_readdatavalid && legacy),
      .avm_writeresponsevalid(avm_writeresponsevalid && legacy),.avm_response(avm_response)
    );
    anvil_q2_ht2_legacy_logit_pipe legacy_logits (
      .clk(clk),.rst_n(rst_n),.annul(legacy_logit_annul),
      .s_valid(parent_logit_valid && legacy),.s_ready(legacy_logit_ready),
      .s_index(parent_logit_index),.s_data(parent_logit_data),
      .m_valid(legacy_logit_valid),.m_ready(logit_ready && legacy),
      .m_index(legacy_logit_index),.m_data(legacy_logit_data),
      .m_fp32(legacy_logit_fp32),.idle(legacy_logit_idle)
    );
    anvil_q2_ht2_model_sequencer #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
      .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
      .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_BLOCK(CACHE_BLOCK)
    ) native_model (
      .clk(clk),.rst_n(rst_n),.annul(abort_start),.invalidate(native_invalidate),
      .s_valid(native_offer),.s_ready(native_token_ready),
      .s_count(token_valid ? 3'd1 : draft_count),.s_k(token_valid ? 3'd1 : width),
      .s_ids(token_valid ? {96'd0,token_id} : draft_ids),
      .s_parent(token_valid ? 8'd0 : draft_parent),
      .s_position(token_valid ? token_pos : draft_pos),
      .s_new_sequence(token_valid ? new_sequence : draft_new_sequence),
      .s_mode(mode),.s_kv_base(cache_base),.s_kv_length(cache_length),
      .busy(native_busy),.idle(native_idle),.fault(native_fault),.cache_valid(cache_valid),
      .logit_valid(native_logit_valid),.logit_ready(logit_ready && !inhibited),
      .logit_slot(native_logit_slot),.logit_index(native_logit_index),
      .logit_fp32(native_logit_fp32),.logit_data(native_logit_data),
      .m_valid(native_response_valid),.m_error(native_response_error),
      .m_ready(native_response_ready && !inhibited),
      .m_accepted(native_accepted),.m_mask(native_mask),
      .m_next_token(native_next),.m_position(native_position),
      .committed_position(committed_position),.commit_valid(native_commit),
      .desc_req_valid(desc_valid),.desc_req_ready(desc_ready),.desc_req_index(desc_index),
      .desc_rsp_valid(desc_rsp_valid),.desc_rsp_error(desc_rsp_error),
      .desc_rsp_ready(desc_rsp_ready),.desc_rsp_data(desc_data),
      .weight_valid(weight_valid),.weight_ready(weight_ready),
      .weight_address(weight_address),.weight_beats(weight_beats),
      .fill_valid(fill_valid),.fill_error(fill_error),.fill_last(fill_last),
      .fill_ready(fill_ready),.fill_data(fill_data),
      .scalar_mem_valid(scalar_valid),.scalar_mem_ready(scalar_ready),
      .scalar_mem_address(scalar_address),.scalar_mem_rsp_valid(scalar_rsp_valid),
      .scalar_mem_rsp_error(scalar_rsp_error),.scalar_mem_rsp_ready(scalar_rsp_ready),
      .scalar_mem_rsp_data(scalar_data),
      .kv_mem_valid(kv_valid),.kv_mem_write(kv_write),.kv_mem_ready(kv_ready),
      .kv_mem_address(kv_address),.kv_mem_wdata(kv_wdata),.kv_mem_be(kv_be),
      .kv_mem_rsp_valid(kv_rsp_valid),.kv_mem_rsp_error(kv_rsp_error),
      .kv_mem_rsp_ready(kv_rsp_ready),.kv_mem_rsp_data(kv_data)
    );
    anvil_q2_ht_host_port native_host (
      .clk(clk),.rst_n(rst_n),
      .inhibit(legacy || inhibited || cfg_valid || cfg_rsp_valid || validating),
      .ddr_ready(ddr_ready),.operation_busy(native_active || native_busy || validating),
      .configuration_valid(loaded),.host_req_valid(host_req_valid && !legacy),
      .host_req_write(host_req_write),.host_req_addr(host_req_addr),
      .host_req_wdata(host_req_wdata),.host_req_be(host_req_be),
      .host_req_ready(native_host_ready),.host_rsp_valid(native_host_valid),
      .host_rsp_ready(host_rsp_ready && !legacy),
      .host_rsp_rdata(native_host_data),.host_rsp_error(native_host_error),
      .idle(host_idle),.memory_idle(host_memory_idle),.write_accepted(host_write_accepted),
      .mem_req_valid(host_mem_valid),.mem_req_ready(host_mem_ready),
      .mem_req_write(host_mem_write),.mem_req_addr(host_mem_address),
      .mem_req_wdata(host_mem_wdata),.mem_req_be(host_mem_be),
      .mem_rsp_valid(host_mem_rsp_valid),.mem_rsp_ready(host_mem_rsp_ready),
      .mem_rsp_rdata(host_mem_rsp_data),.mem_rsp_error(host_mem_rsp_error)
    );
    anvil_q2_ht2_ddr_fabric #(.READ_OUTSTANDING(READ_OUTSTANDING)) native_fabric (
      .clk(clk),.rst_n(rst_n),.annul(abort_start),.ddr_ready(ddr_ready && !legacy),
      .ddr_fault(ddr_fault && !legacy),
      .weight_valid(weight_valid),.weight_ready(weight_ready),
      .weight_address(weight_address),.weight_beats(weight_beats),
      .fill_valid(fill_valid),.fill_error(fill_error),.fill_last(fill_last),
      .fill_ready(fill_ready),.fill_data(fill_data),
      .c_req_valid({host_mem_valid,scalar_valid,kv_valid}),
      .c_req_write({host_mem_write,1'b0,kv_write}),.c_req_ready(client_ready),
      .c_req_address({host_mem_address,scalar_address,kv_address}),
      .c_req_wdata({host_mem_wdata,512'd0,kv_wdata}),
      .c_req_be({host_mem_be,64'hffffffffffffffff,kv_be}),
      .c_rsp_valid(client_rsp_valid),.c_rsp_error(client_rsp_error),
      .c_rsp_ready({host_mem_rsp_ready,scalar_rsp_ready,kv_rsp_ready}),
      .c_rsp_data(client_data),.idle(fabric_idle),.fault(fabric_fault),
      .accepted_read_beats(accepted_read_beats),.accepted_write_beats(accepted_write_beats),
      .avm_address(native_address),.avm_read(native_read),.avm_write(native_write),
      .avm_writedata(native_wdata),.avm_byteenable(native_be),.avm_burstcount(native_burst),
      .avm_waitrequest(avm_waitrequest || legacy),.avm_readdata(avm_readdata),
      .avm_readdatavalid(avm_readdatavalid && !legacy),
      .avm_writeresponsevalid(avm_writeresponsevalid && !legacy),.avm_response(avm_response)
    );

    assign {host_mem_ready,scalar_ready,kv_ready}=client_ready;
    assign {host_mem_rsp_valid,scalar_rsp_valid,kv_rsp_valid}=client_rsp_valid;
    assign {host_mem_rsp_error,scalar_rsp_error,kv_rsp_error}=client_rsp_error;
    assign {host_mem_rsp_data,scalar_data,kv_data}=client_data;
    assign forwarded_ready=legacy ? parent_cfg_ready : native_cfg_ready;
    assign forwarded_rsp_valid=legacy ? parent_cfg_valid : native_cfg_valid;
    assign forwarded_rdata=legacy ? parent_cfg_data : native_cfg_data;
    assign forwarded_error=legacy ? parent_cfg_error : native_cfg_error;
    assign token_ready=rst_n && (legacy ?
      (!legacy_active && !mode_changed && !cfg_valid && !cfg_rsp_valid && parent_token_ready) :
      (native_enable && native_token_ready));
    assign draft_ready=native_enable && !token_valid && native_token_ready;
    assign logit_valid=rst_n && (legacy ? legacy_logit_valid :
      (!inhibited && native_logit_valid));
    assign logit_index=logit_valid ?
      (legacy ? legacy_logit_index : native_logit_index) : 32'd0;
    assign logit_data=logit_valid ?
      (legacy ? legacy_logit_data : native_logit_data) : 32'sd0;
    assign logit_slot=logit_valid && !legacy ? native_logit_slot : 2'd0;
    assign logit_fp32=logit_valid ?
      (legacy ? legacy_logit_fp32 : native_logit_fp32) : 32'd0;
    assign batch_valid=rst_n && !cancel && !legacy && !native_legacy_token &&
      (abort_response || (!inhibited && native_response_valid));
    assign batch_error=batch_valid && (abort_response || native_response_error);
    assign batch_accepted=batch_valid && !batch_error ? native_accepted : 3'd0;
    assign batch_mask=batch_valid && !batch_error ? native_mask : 4'd0;
    assign batch_next_token=batch_valid && !batch_error ? native_next : 32'd0;
    assign batch_position=batch_valid ?
      (abort_response ? committed_position : native_position) : 32'd0;
    assign done=rst_n && (legacy ? legacy_completion : completion);
    assign error=done && (legacy ? legacy_completion_error : completion_error);
    assign cancel_done=rst_n && (legacy ? parent_cancel_done : cancellation_complete);
    assign host_req_ready=rst_n && (legacy ?
      (!cfg_valid && !cfg_rsp_valid && parent_host_ready) : native_host_ready);
    assign host_rsp_valid=rst_n && (legacy ? parent_host_valid : native_host_valid);
    assign host_rsp_rdata=host_rsp_valid ?
      (legacy ? parent_host_data : native_host_data) : 512'd0;
    assign host_rsp_error=host_rsp_valid && (legacy ? parent_host_error : native_host_error);
    assign avm_address=rst_n ? (legacy ? parent_address : native_address) : 33'd0;
    assign avm_read=rst_n && (legacy ? parent_read : native_read);
    assign avm_write=rst_n && (legacy ? parent_write : native_write);
    assign avm_writedata=rst_n ? (legacy ? parent_wdata : native_wdata) : 512'd0;
    assign avm_byteenable=rst_n ? (legacy ? parent_be : native_be) : 64'd0;
    assign avm_burstcount=rst_n ? (legacy ? parent_burst : native_burst) : 5'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        legacy_active<=0; legacy_host_pending<=0;
        legacy_retiring<=0; legacy_retiring_error<=0;
        legacy_completion<=0; legacy_completion_error<=0;
        native_active<=0; native_legacy_token<=0; draining<=0;
        aborted_request<=0; abort_response<=0; cancel_pending<=0; cancel_seen<=0;
        completion<=0; completion_error<=0; cancellation_complete<=0;
        legacy_completion<=0; legacy_completion_error<=0;
        sticky_fault<=0; settle<=0;
      end else begin
        completion<=0; completion_error<=0; cancellation_complete<=0;
        if (!cancel) cancel_seen<=0;
        else cancel_seen<=1;
        if (legacy && token_valid && token_ready) legacy_active<=1;
        if (parent_done) begin
          legacy_retiring<=1; legacy_retiring_error<=parent_error;
        end
        if (legacy_retiring && legacy_logit_idle && !parent_logit_valid) begin
          legacy_retiring<=0; legacy_active<=0;
          legacy_completion<=1; legacy_completion_error<=legacy_retiring_error;
        end
        if (legacy && host_req_valid && host_req_ready) legacy_host_pending<=1;
        if (legacy && host_rsp_valid && host_rsp_ready) legacy_host_pending<=0;
        if (native_transfer) begin
          native_active<=1; native_legacy_token<=token_valid;
        end
        if (native_batch_transfer) begin
          native_active<=0;
          completion<=native_legacy_token; completion_error<=native_response_error;
          if (native_response_error) sticky_fault<=1;
        end
        if (native_invalidate) sticky_fault<=0;
        if (native_fault || external_fault) sticky_fault<=1;
        if (abort_start) begin
          draining<=1; aborted_request<=native_active; native_active<=0;
          cancel_pending<=cancel_start; settle<=0;
        end else if (draining) begin
          if (cancel_start) cancel_pending<=1;
          if (resources_safe) begin
            if (settle!=3) settle<=settle+2'd1;
            else if (!cancel && !ddr_fault) begin
              draining<=0; abort_response<=aborted_request;
              cancellation_complete<=cancel_pending;
              cancel_pending<=0; aborted_request<=0;
            end
          end else settle<=0;
        end else if (abort_response && !cancel && (native_legacy_token || batch_ready)) begin
          abort_response<=0;
          completion<=native_legacy_token; completion_error<=1;
        end
      end
    end
  end endgenerate
endmodule
