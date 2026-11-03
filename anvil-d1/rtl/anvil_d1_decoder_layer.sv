module anvil_d1_decoder_layer #(
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=10944,
  parameter integer NUM_Q_HEADS=16, KV_LORA_RANK=512, QK_NOPE_HEAD_DIM=128,
  parameter integer QK_ROPE_HEAD_DIM=64, V_HEAD_DIM=128,
  parameter integer ROUTED_EXPERTS=64, TOP_K=6, SHARED_EXPERTS=2,
  parameter integer MOE_INTERMEDIATE_SIZE=1408, FIRST_DENSE_LAYERS=1,
  parameter integer MAX_SEQ_LEN=32768, TILE_K=128, TILE_ROWS=8
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_layer, cmd_pos,
  input wire cmd_phase,
  output wire done, error,
  output wire [63:0] kv_read_bytes, kv_write_bytes, kv_dense_equiv_bytes,
  output wire [63:0] expert_dma_bytes, expert_dense_equiv_bytes,
  output wire [63:0] shared_busy_cycles, prefetch_busy_cycles, overlap_cycles,
  output wire mla_complete, moe_complete,
  output wire [4:0] c_req_valid,
  input wire [4:0] c_req_ready,
  output wire [4:0] c_req_write,
  output wire [19:0] c_req_kind,
  output wire [159:0] c_req_layer,
  output wire [14:0] c_req_proj,
  output wire [159:0] c_req_row, c_req_col, c_req_wdata,
  input wire [4:0] c_rsp_valid,
  output wire [4:0] c_rsp_ready,
  input wire [159:0] c_rsp_rdata,
  input wire [4:0] c_rsp_error
);
  localparam IDLE=0, NORM=1, NORM_WAIT=2, MLA=3, MLA_WAIT=4;
  localparam RESIDUAL_READ=5, RESIDUAL_RESPONSE=6, RESULT_READ=7, RESULT_RESPONSE=8;
  localparam ADD=9, ADD_WAIT=10, BOUNDARY=11, BOUNDARY_WAIT=12;
  localparam WRITE=13, WRITE_RESPONSE=14, MOE=15, MOE_WAIT=16;
  localparam COMPLETE=17, FAULTED=18, REJECT=19;
  reg [4:0] state;
  reg armed, failed, second_residual, phase;
  reg [31:0] epoch, layer, position, component;
  reg signed [31:0] residual, branch, result;
  reg signed [127:0] sum;
  wire norm_ready, norm_done, norm_error, mla_ready, mla_done, mla_error;
  wire moe_ready, moe_done, moe_error;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==RESIDUAL_READ || state==RESULT_READ || state==WRITE);
  wire add_ready, add_valid, add_error, round_ready, round_valid;
  wire signed [127:0] added;
  wire signed [31:0] rounded;
  wire child_fault=(state==NORM_WAIT && norm_done && norm_error) ||
    (state==MLA_WAIT && mla_done && mla_error) ||
    (state==MOE_WAIT && moe_done && moe_error);
  assign cmd_ready=rst_n && armed && !flush && state==IDLE;
  assign done=rst_n && !flush && (state==COMPLETE || child_fault);
  assign error=done && (failed || child_fault);
  assign mla_complete=rst_n && !flush && state==MLA_WAIT && mla_done;
  assign moe_complete=rst_n && !flush && state==MOE_WAIT && moe_done;
  anvil_d1_rmsnorm #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) normalization (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(state==NORM),.cmd_ready(norm_ready),
    .cmd_layer(layer),.cmd_pos(position),.cmd_mode(second_residual ? 2'd1 : 2'd0),
    .done(norm_done),.error(norm_error),
    .mem_req_valid(c_req_valid[0]),.mem_req_ready(c_req_ready[0]),.mem_req_write(c_req_write[0]),
    .mem_req_kind(c_req_kind[0+:4]),.mem_req_layer(c_req_layer[0+:32]),
    .mem_req_proj(c_req_proj[0+:3]),.mem_req_row(c_req_row[0+:32]),
    .mem_req_col(c_req_col[0+:32]),.mem_req_wdata(c_req_wdata[0+:32]),
    .mem_rsp_valid(c_rsp_valid[0]),.mem_rsp_ready(c_rsp_ready[0]),
    .mem_rsp_rdata(c_rsp_rdata[0+:32]),.mem_rsp_error(c_rsp_error[0])
  );
  anvil_d1_mla_engine #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
    .KV_LORA_RANK(KV_LORA_RANK),.QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),
    .QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),.V_HEAD_DIM(V_HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) mla (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(state==MLA),.cmd_ready(mla_ready),
    .cmd_epoch(epoch),.cmd_layer(layer),.cmd_pos(position),.cmd_phase(phase),
    .done(mla_done),.error(mla_error),.kv_read_bytes(kv_read_bytes),
    .kv_write_bytes(kv_write_bytes),.kv_dense_equiv_bytes(kv_dense_equiv_bytes),
    .c_req_valid(c_req_valid[1]),.c_req_ready(c_req_ready[1]),.c_req_write(c_req_write[1]),
    .c_req_kind(c_req_kind[4+:4]),.c_req_layer(c_req_layer[32+:32]),
    .c_req_proj(c_req_proj[3+:3]),.c_req_row(c_req_row[32+:32]),
    .c_req_col(c_req_col[32+:32]),.c_req_wdata(c_req_wdata[32+:32]),
    .c_rsp_valid(c_rsp_valid[1]),.c_rsp_ready(c_rsp_ready[1]),
    .c_rsp_rdata(c_rsp_rdata[32+:32]),.c_rsp_error(c_rsp_error[1])
  );
  anvil_d1_moe_router_dma #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),.FIRST_DENSE_LAYERS(FIRST_DENSE_LAYERS),
    .ROUTED_EXPERTS(ROUTED_EXPERTS),.TOP_K(TOP_K),.SHARED_EXPERTS(SHARED_EXPERTS),
    .MAX_SEQ_LEN(MAX_SEQ_LEN),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
  ) moe (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(state==MOE),.cmd_ready(moe_ready),
    .cmd_epoch(epoch),.cmd_layer(layer),.cmd_pos(position),.cmd_phase(phase),
    .done(moe_done),.error(moe_error),.expert_dma_bytes(expert_dma_bytes),
    .expert_dense_equiv_bytes(expert_dense_equiv_bytes),
    .shared_busy_cycles(shared_busy_cycles),.prefetch_busy_cycles(prefetch_busy_cycles),
    .overlap_cycles(overlap_cycles),
    .c_req_valid(c_req_valid[2+:2]),.c_req_ready(c_req_ready[2+:2]),
    .c_req_write(c_req_write[2+:2]),.c_req_kind(c_req_kind[8+:8]),
    .c_req_layer(c_req_layer[64+:64]),.c_req_proj(c_req_proj[6+:6]),
    .c_req_row(c_req_row[64+:64]),.c_req_col(c_req_col[64+:64]),
    .c_req_wdata(c_req_wdata[64+:64]),
    .c_rsp_valid(c_rsp_valid[2+:2]),.c_rsp_ready(c_rsp_ready[2+:2]),
    .c_rsp_rdata(c_rsp_rdata[64+:64]),.c_rsp_error(c_rsp_error[2+:2])
  );
  anvil_d1_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==WRITE),.kind(state==RESULT_READ ? 4'd15 : 4'd8),
    .layer(state==RESULT_READ ? layer : 32'd0),
    .proj(state==RESULT_READ ? 3'd7 : 3'd0),
    .row(state==RESULT_READ ? (second_residual ? 32'd4 : 32'd3) :
      state==WRITE ? (second_residual ? 32'd0 : 32'd7) : second_residual ? 32'd7 : 32'd0),
    .col(component),.wdata(state==WRITE ? result : 32'd0),.rdata(rdata),
    .c_req_valid(c_req_valid[4]),.c_req_ready(c_req_ready[4]),.c_req_write(c_req_write[4]),
    .c_req_kind(c_req_kind[16+:4]),.c_req_layer(c_req_layer[128+:32]),
    .c_req_proj(c_req_proj[12+:3]),.c_req_row(c_req_row[128+:32]),
    .c_req_col(c_req_col[128+:32]),.c_req_wdata(c_req_wdata[128+:32]),
    .c_rsp_valid(c_rsp_valid[4]),.c_rsp_ready(c_rsp_ready[4]),
    .c_rsp_rdata(c_rsp_rdata[128+:32]),.c_rsp_error(c_rsp_error[4])
  );
  anvil_d1_add128 residual_adder (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ADD),.in_ready(add_ready),
    .in_a({{96{residual[31]}},residual}),.in_b({{96{branch[31]}},branch}),
    .out_valid(add_valid),.out_ready(1'b1),.out_error(add_error),.out_sum(added)
  );
  anvil_d1_round_sat #(.SHIFT(0)) residual_boundary (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==BOUNDARY),.in_ready(round_ready),.in_value(sum),
    .out_valid(round_valid),.out_ready(1'b1),.out_value(rounded)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; second_residual<=0; phase<=0;
      epoch<=0; layer<=0; position<=0; component<=0;
      residual<=0; branch<=0; result<=0; sum<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; failed<=0; end
      else if (child_fault) begin failed<=1; state<=FAULTED; end
      else if (!failed && (memory_fault || (add_valid && add_error))) begin
        failed<=1; state<=COMPLETE;
      end else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          epoch<=cmd_epoch; layer<=cmd_layer; position<=cmd_pos; phase<=cmd_phase;
          failed<=0; second_residual<=0; component<=0;
          if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin failed<=1; state<=REJECT; end
          else state<=NORM;
        end
        NORM: if (norm_ready) state<=NORM_WAIT;
        NORM_WAIT: if (norm_done) begin
          if (second_residual) state<=MOE;
          else state<=MLA;
        end
        MLA: if (mla_ready) state<=MLA_WAIT;
        MLA_WAIT: if (mla_done) begin component<=0; state<=RESIDUAL_READ; end
        MOE: if (moe_ready) state<=MOE_WAIT;
        MOE_WAIT: if (moe_done) begin component<=0; state<=RESIDUAL_READ; end
        RESIDUAL_READ: if (issue) state<=RESIDUAL_RESPONSE;
        RESIDUAL_RESPONSE: if (memory_complete) begin residual<=rdata; state<=RESULT_READ; end
        RESULT_READ: if (issue) state<=RESULT_RESPONSE;
        RESULT_RESPONSE: if (memory_complete) begin branch<=rdata; state<=ADD; end
        ADD: if (add_ready) state<=ADD_WAIT;
        ADD_WAIT: if (add_valid) begin sum<=added; state<=BOUNDARY; end
        BOUNDARY: if (round_ready) state<=BOUNDARY_WAIT;
        BOUNDARY_WAIT: if (round_valid) begin result<=rounded; state<=WRITE; end
        WRITE: if (issue) state<=WRITE_RESPONSE;
        WRITE_RESPONSE: if (memory_complete) begin
          if (component!=HIDDEN_SIZE-1) begin component<=component+1'b1; state<=RESIDUAL_READ; end
          else if (!second_residual) begin second_residual<=1; state<=NORM; end
          else state<=COMPLETE;
        end
        REJECT: state<=COMPLETE;
        COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
        FAULTED: state<=FAULTED;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
