module anvil_q3_ht2_tree_attention #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, NUM_Q_HEADS=16,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768,
  parameter CACHE_MODE=1, KV_RESIDENT_GROUPS=64
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_id, cmd_epoch, cmd_layer, cmd_base_pos,
  input wire [1:0] cmd_node,
  input wire [3:0] cmd_mask, cmd_visibility,
  input wire [127:0] cmd_positions,
  input wire [11:0] cmd_parents,
  output wire done, error, idle, fault, drain_done,
  output wire scratch_req_valid,
  input wire scratch_req_ready,
  output wire scratch_req_write,
  output wire [1:0] scratch_req_node,
  output wire [31:0] scratch_req_slot, scratch_req_index, scratch_req_wdata,
  input wire scratch_rsp_valid,
  output wire scratch_rsp_ready,
  input wire scratch_rsp_error,
  input wire [31:0] scratch_rsp_rdata,
  output wire memory_req_valid,
  input wire memory_req_ready,
  output wire memory_req_write,
  output wire [32:0] memory_req_address,
  output wire [511:0] memory_req_wdata,
  output wire [63:0] memory_req_byteenable,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata
);
  localparam CAP=CACHE_MODE==2 ? 64 : 32;
  localparam [127:0] GROUPS=(128'(HEAD_DIM)+CAP-1)>>$clog2(CAP);
  localparam [127:0] EXTENT=128'(NUM_LAYERS)*2*128'(NUM_KV_HEADS)*
    GROUPS*64*(128'(MAX_SEQ_LEN)+4);
  localparam LEGAL=NUM_LAYERS>0 && HIDDEN_SIZE>0 && NUM_KV_HEADS>0 &&
    128'(NUM_Q_HEADS)==128'(NUM_KV_HEADS)*8 && HEAD_DIM>0 &&
    (HEAD_DIM&1)==0 && 128'(HIDDEN_SIZE)==128'(NUM_Q_HEADS)*128'(HEAD_DIM) &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 && (CACHE_MODE==1 || CACHE_MODE==2) &&
    KV_RESIDENT_GROUPS>=1 && KV_RESIDENT_GROUPS<=256 &&
    EXTENT<=128'h100000000;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: causal tree attention geometry");
    assign cmd_ready=0;
    assign done=0;
    assign error=0;
    assign idle=0;
    assign fault=0;
    assign drain_done=0;
    assign scratch_req_valid=0;
    assign scratch_req_write=0;
    assign scratch_req_node=0;
    assign scratch_req_slot=0;
    assign scratch_req_index=0;
    assign scratch_req_wdata=0;
    assign scratch_rsp_ready=0;
    assign memory_req_valid=0;
    assign memory_req_write=0;
    assign memory_req_address=0;
    assign memory_req_wdata=0;
    assign memory_req_byteenable=0;
  end else begin: datapath
    localparam IDLE=0, WALK_CAPTURE=1, WALK_UPDATE=2, START=3,
      RUN=4, COMPLETE=5, ABORT_PULSE=6, ABORT_WAIT=7,
      CANCEL_WAIT=8, FAULTED=9, CACHE_INVALIDATE=10, CACHE_WAIT=11;
    reg [3:0] state;
    reg failed, scratch_outstanding, commit_ack;
    reg [31:0] transaction_id, epoch, layer, base_pos, position;
    reg [1:0] node;
    reg [3:0] active, visibility, ancestry;
    reg [127:0] positions;
    reg [11:0] parents;
    reg [1:0] walk_node;
    reg [31:0] walk_position, captured_position;
    reg [2:0] captured_parent;
    reg captured_active;
    wire running=rst_n && !flush && !failed;
    wire command_fire=cmd_valid && cmd_ready;
    wire kernel_ready, kernel_done, kernel_error;
    wire kernel_mem_valid, kernel_mem_ready, kernel_mem_write, kernel_rsp_ready;
    wire [3:0] kernel_mem_kind;
    wire [2:0] kernel_mem_proj;
    wire [31:0] kernel_mem_layer, kernel_mem_row, kernel_mem_col, kernel_mem_wdata;
    wire kv_valid, kv_ready, kv_done, kv_error, kv_phase;
    wire [1:0] kv_op;
    wire [31:0] kv_epoch, kv_layer, kv_pos, kv_head, kv_dim;
    wire signed [31:0] kv_data;
    wire reader_ready, reader_valid, reader_error, reader_idle, reader_fault, reader_drained;
    wire signed [31:0] reader_data;
    wire reader_flush=flush || state==ABORT_PULSE || state==CACHE_INVALIDATE;
    wire kernel_flush=flush || failed || state==CANCEL_WAIT;
    wire kernel_start_valid=running && state==START &&
      reader_idle && reader_drained && !scratch_outstanding;
    wire scratch_fire=scratch_req_valid && scratch_req_ready;
    wire scratch_expected=scratch_outstanding || scratch_fire;
    wire scratch_response_fire=scratch_rsp_valid && scratch_rsp_ready;
    wire scratch_protocol_error=scratch_rsp_valid &&
      (!scratch_expected || scratch_rsp_error);
    wire scratch_kind_error=kernel_mem_valid &&
      (kernel_mem_kind!=8 || kernel_mem_proj!=0 || kernel_mem_layer!=0 ||
       (kernel_mem_write ? kernel_mem_row!=5 : kernel_mem_row!=2) ||
       kernel_mem_col>=HIDDEN_SIZE);
    wire kv_identity_error=kv_valid &&
      (kv_epoch!=epoch || kv_layer!=layer || kv_op>2 || kv_pos>position);
    wire wrapper_fault=!failed && state!=CANCEL_WAIT &&
      state!=ABORT_PULSE && state!=ABORT_WAIT &&
      (reader_fault || (scratch_rsp_valid && !scratch_expected) ||
       (state==RUN && (kernel_error || scratch_protocol_error ||
        scratch_kind_error || kv_identity_error)));

    assign cmd_ready=running && state==IDLE && kernel_ready &&
      reader_idle && !scratch_outstanding;
    assign done=rst_n && !flush && state==COMPLETE;
    assign error=done && failed;
    assign idle=cmd_ready;
    assign fault=rst_n && !flush && failed;
    assign drain_done=rst_n && !flush && reader_drained && !scratch_outstanding &&
      (state==IDLE || state==COMPLETE || state==FAULTED);
    assign scratch_req_valid=running && state==RUN && kernel_mem_valid &&
      !scratch_outstanding && !scratch_kind_error;
    assign scratch_req_write=scratch_req_valid && kernel_mem_write;
    assign scratch_req_node=scratch_req_valid ? node : 2'd0;
    assign scratch_req_slot=scratch_req_valid ? kernel_mem_row : 32'd0;
    assign scratch_req_index=scratch_req_valid ? kernel_mem_col : 32'd0;
    assign scratch_req_wdata=scratch_req_write ? kernel_mem_wdata : 32'd0;
    assign kernel_mem_ready=scratch_req_valid && scratch_req_ready;
    assign scratch_rsp_ready=rst_n && !flush &&
      ((state==RUN && !failed && kernel_rsp_ready) ||
       ((state==CANCEL_WAIT || state==ABORT_WAIT) && scratch_outstanding));
    assign memory_req_write=1'b0;
    assign memory_req_wdata=512'd0;
    assign memory_req_byteenable=memory_req_valid ? 64'hffffffffffffffff : 64'd0;
    assign kv_ready=running && state==RUN &&
      (kv_op==0 ? !commit_ack : reader_ready);
    assign kv_done=running && state==RUN && (commit_ack || reader_valid);
    assign kv_error=kv_done && !commit_ack && reader_error;
    assign kv_data=kv_done && !commit_ack && !reader_error ? reader_data : 32'sd0;

    anvil_q3_ht_attention #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) q16_attention_kernel (
      .clk(clk),.rst_n(rst_n),.flush(kernel_flush),
      .cmd_valid(kernel_start_valid),.cmd_ready(kernel_ready),
      .cmd_epoch(epoch),.cmd_layer(layer),.cmd_pos(position),.cmd_phase(1'b1),
      .done(kernel_done),.error(kernel_error),
      .mem_req_valid(kernel_mem_valid),.mem_req_write(kernel_mem_write),
      .mem_req_ready(kernel_mem_ready),.mem_req_kind(kernel_mem_kind),
      .mem_req_layer(kernel_mem_layer),.mem_req_row(kernel_mem_row),
      .mem_req_col(kernel_mem_col),.mem_req_wdata(kernel_mem_wdata),.mem_req_proj(kernel_mem_proj),
      .mem_rsp_valid(scratch_rsp_valid && scratch_expected && running && state==RUN),
      .mem_rsp_error(scratch_rsp_error),.mem_rsp_ready(kernel_rsp_ready),
      .mem_rsp_rdata(scratch_rsp_rdata),
      .kv_cmd_valid(kv_valid),.kv_cmd_ready(kv_ready),.kv_cmd_op(kv_op),
      .kv_cmd_epoch(kv_epoch),.kv_cmd_layer(kv_layer),.kv_cmd_pos(kv_pos),
      .kv_cmd_head(kv_head),.kv_cmd_dim(kv_dim),.kv_cmd_phase(kv_phase),
      .kv_done(kv_done),.kv_error(kv_error),.kv_read_data(kv_data)
    );

    anvil_q3_ht2_kv_read_port #(
      .NUM_LAYERS(NUM_LAYERS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
      .MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_MODE(CACHE_MODE),.KV_RESIDENT_GROUPS(KV_RESIDENT_GROUPS)
    ) causal_kv_reader (
      .clk(clk),.rst_n(rst_n),.flush(reader_flush),
      .cmd_valid(running && state==RUN && kv_valid && kv_op!=0),
      .cmd_ready(reader_ready),.cmd_id(transaction_id),.cmd_epoch(kv_epoch),
      .cmd_layer(kv_layer),.cmd_pos(kv_pos),.cmd_head(kv_head),.cmd_dim(kv_dim),
      .cmd_value(kv_op==2),.cmd_prefix_count(base_pos),
      .cmd_visibility(visibility),.cmd_positions(positions),
      .out_valid(reader_valid),.out_ready(running && state==RUN),
      .out_error(reader_error),.out_data(reader_data),
      .idle(reader_idle),.fault(reader_fault),.drain_done(reader_drained),
      .memory_req_valid(memory_req_valid),.memory_req_ready(memory_req_ready),
      .memory_req_address(memory_req_address),.memory_rsp_valid(memory_rsp_valid),
      .memory_rsp_error(memory_rsp_error),.memory_rsp_rdata(memory_rsp_rdata)
    );

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) scratch_outstanding<=0;
      else begin
        if (scratch_fire) scratch_outstanding<=1;
        if (scratch_response_fire && scratch_expected) scratch_outstanding<=0;
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; commit_ack<=0;
        transaction_id<=0; epoch<=0; layer<=0; base_pos<=0; position<=0;
        node<=0; active<=0; visibility<=0; ancestry<=0; positions<=0; parents<=0;
        walk_node<=0; walk_position<=0; captured_position<=0;
        captured_parent<=0; captured_active<=0;
      end else if (flush) begin
        state<=CANCEL_WAIT; failed<=0; commit_ack<=0;
        transaction_id<=0; epoch<=0; layer<=0; base_pos<=0; position<=0;
        node<=0; active<=0; visibility<=0; ancestry<=0; positions<=0; parents<=0;
        walk_node<=0; walk_position<=0; captured_position<=0;
        captured_parent<=0; captured_active<=0;
      end else if (wrapper_fault) begin
        failed<=1; commit_ack<=0; state<=ABORT_PULSE;
      end else begin
        commit_ack<=running && state==RUN && kv_valid && kv_ready && kv_op==0;
        case (state)
          IDLE: if (command_fire) begin
            transaction_id<=cmd_id; epoch<=cmd_epoch; layer<=cmd_layer;
            base_pos<=cmd_base_pos; node<=cmd_node;
            position<=cmd_positions[cmd_node*32+:32];
            active<=cmd_mask; visibility<=cmd_visibility;
            ancestry<=0; positions<=cmd_positions; parents<=cmd_parents;
            walk_node<=cmd_node; walk_position<=cmd_positions[cmd_node*32+:32];
            if (cmd_layer>=NUM_LAYERS || !cmd_mask[cmd_node] ||
                !cmd_visibility[cmd_node] || (cmd_visibility&~cmd_mask)!=0 ||
                cmd_base_pos>=MAX_SEQ_LEN ||
                cmd_positions[cmd_node*32+:32]<cmd_base_pos ||
                cmd_positions[cmd_node*32+:32]>=MAX_SEQ_LEN ||
                {32'd0,cmd_positions[cmd_node*32+:32]}>
                  {32'd0,cmd_base_pos}+64'd3) begin
              failed<=1; state<=ABORT_PULSE;
            end else state<=CACHE_INVALIDATE;
          end
          CACHE_INVALIDATE: state<=CACHE_WAIT;
          CACHE_WAIT: if (reader_idle && reader_drained && !scratch_outstanding)
            state<=WALK_CAPTURE;
          WALK_CAPTURE: begin
            captured_parent<=parents[walk_node*3+:3];
            captured_position<=positions[walk_node*32+:32];
            captured_active<=active[walk_node]; state<=WALK_UPDATE;
          end
          WALK_UPDATE: begin
            if (!captured_active || captured_position!=walk_position ||
                ancestry[walk_node] || !visibility[walk_node]) begin
              failed<=1; state<=ABORT_PULSE;
            end else if (captured_parent==4) begin
              if (walk_position!=base_pos ||
                  (ancestry|(4'b0001<<walk_node))!=visibility) begin
                failed<=1; state<=ABORT_PULSE;
              end else state<=START;
            end else if (captured_parent>=walk_node || walk_position<=base_pos) begin
              failed<=1; state<=ABORT_PULSE;
            end else begin
              ancestry[walk_node]<=1; walk_node<=captured_parent[1:0];
              walk_position<=walk_position-1'b1; state<=WALK_CAPTURE;
            end
          end
          START: if (kernel_start_valid && kernel_ready) state<=RUN;
          RUN: if (kernel_done) state<=COMPLETE;
          COMPLETE: begin
            if (failed) state<=FAULTED;
            else state<=IDLE;
          end
          ABORT_PULSE: state<=ABORT_WAIT;
          ABORT_WAIT: if (reader_drained && !scratch_outstanding) state<=COMPLETE;
          CANCEL_WAIT: if (reader_drained && !scratch_outstanding) state<=IDLE;
          FAULTED: begin end
          default: begin failed<=1; state<=ABORT_PULSE; end
        endcase
      end
    end
  end endgenerate
endmodule
