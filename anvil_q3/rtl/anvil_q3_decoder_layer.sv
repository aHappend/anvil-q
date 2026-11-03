module anvil_q3_decoder_layer #(
  parameter PROFILE=3, BANKS=8, TILE_K=128, TILE_ROWS=8,
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
  parameter MAX_SEQ_LEN=32768, CACHE_MODE=0, INT4_ASYM=0, CACHE_BLOCK=1,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) ? BANKS : 1,
  localparam CLIENTS=SB+7
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_layer, cmd_pos,
  input wire cmd_phase,
  output wire done, error,
  output wire [CLIENTS-1:0] c_req_valid,
  input wire [CLIENTS-1:0] c_req_ready,
  output wire [CLIENTS-1:0] c_req_write,
  output wire [CLIENTS*4-1:0] c_req_kind,
  output wire [CLIENTS*32-1:0] c_req_layer,
  output wire [CLIENTS*3-1:0] c_req_proj,
  output wire [CLIENTS*32-1:0] c_req_row, c_req_col, c_req_wdata,
  input wire [CLIENTS-1:0] c_rsp_valid, c_rsp_error,
  output wire [CLIENTS-1:0] c_rsp_ready,
  input wire [CLIENTS*32-1:0] c_rsp_rdata
);
  localparam N=SB+1, R=SB+2, A=SB+3, M=SB+5, E=SB+6;
  localparam IDLE=0, NORM0=1, NORM0_WAIT=2, Q=3, Q_WAIT=4;
  localparam K=5, K_WAIT=6, V=7, V_WAIT=8, ROPE=9, ROPE_WAIT=10;
  localparam ATTENTION=11, ATTENTION_WAIT=12, O=13, O_WAIT=14;
  localparam RESIDUAL0=15, RESIDUAL0_WAIT=16, NORM1=17, NORM1_WAIT=18;
  localparam MLP=19, MLP_WAIT=20, RESIDUAL1=21, RESIDUAL1_WAIT=22;
  localparam COMPLETE=23, FAULTED=24;
  reg [4:0] state;
  reg failed, phase;
  reg [31:0] epoch, layer, position;
  wire unit_flush=flush || failed;
  wire norm_ready, norm_done, norm_error;
  wire gemv_ready, gemv_done, gemv_error;
  wire rope_ready, rope_done, rope_error;
  wire attention_ready, attention_done, attention_error;
  wire mlp_ready, mlp_done, mlp_error;
  wire residual_ready, residual_done, residual_error;
  wire mlp_gemv_valid;
  wire [2:0] mlp_projection;
  wire mlp_owns_gemv=state==MLP || state==MLP_WAIT;
  wire direct_gemv=state==Q || state==K || state==V || state==O;
  wire [2:0] projection=mlp_owns_gemv ? mlp_projection :
    state==K ? 3'd1 : state==V ? 3'd2 : state==O ? 3'd3 : 3'd0;

  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  anvil_q3_rmsnorm #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) norm (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.cmd_valid(state==NORM0 || state==NORM1),
    .cmd_ready(norm_ready),.cmd_layer(layer),.cmd_pos(position),
    .cmd_mode(state==NORM1 || state==NORM1_WAIT ? 2'd1 : 2'd0),
    .done(norm_done),.error(norm_error),
    .mem_req_valid(c_req_valid[N]),.mem_req_ready(c_req_ready[N]),
    .mem_req_write(c_req_write[N]),.mem_req_kind(c_req_kind[N*4+:4]),
    .mem_req_layer(c_req_layer[N*32+:32]),.mem_req_proj(c_req_proj[N*3+:3]),
    .mem_req_row(c_req_row[N*32+:32]),.mem_req_col(c_req_col[N*32+:32]),.mem_req_wdata(c_req_wdata[N*32+:32]),
    .mem_rsp_valid(c_rsp_valid[N]),.mem_rsp_ready(c_rsp_ready[N]),
    .mem_rsp_rdata(c_rsp_rdata[N*32+:32]),.mem_rsp_error(c_rsp_error[N])
  );
  anvil_q3_gemv #(
    .BANKS(BANKS),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS),
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) gemv (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .cmd_valid(direct_gemv || (mlp_owns_gemv && mlp_gemv_valid)),
    .cmd_ready(gemv_ready),.cmd_epoch(epoch),.cmd_layer(layer),.cmd_pos(position),.cmd_proj(projection),
    .done(gemv_done),.error(gemv_error),
    .c_req_valid(c_req_valid[0+:SB+1]),.c_req_ready(c_req_ready[0+:SB+1]),
    .c_req_write(c_req_write[0+:SB+1]),.c_req_kind(c_req_kind[0+:(SB+1)*4]),
    .c_req_layer(c_req_layer[0+:(SB+1)*32]),.c_req_proj(c_req_proj[0+:(SB+1)*3]),
    .c_req_row(c_req_row[0+:(SB+1)*32]),.c_req_col(c_req_col[0+:(SB+1)*32]),
    .c_req_wdata(c_req_wdata[0+:(SB+1)*32]),
    .c_rsp_valid(c_rsp_valid[0+:SB+1]),.c_rsp_error(c_rsp_error[0+:SB+1]),
    .c_rsp_ready(c_rsp_ready[0+:SB+1]),.c_rsp_rdata(c_rsp_rdata[0+:(SB+1)*32])
  );
  anvil_q3_rope #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
    .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) rope (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.cmd_valid(state==ROPE),.cmd_ready(rope_ready),
    .cmd_layer(layer),.cmd_pos(position),.done(rope_done),.error(rope_error),
    .mem_req_valid(c_req_valid[R]),.mem_req_ready(c_req_ready[R]),
    .mem_req_write(c_req_write[R]),.mem_req_kind(c_req_kind[R*4+:4]),
    .mem_req_layer(c_req_layer[R*32+:32]),.mem_req_proj(c_req_proj[R*3+:3]),
    .mem_req_row(c_req_row[R*32+:32]),.mem_req_col(c_req_col[R*32+:32]),.mem_req_wdata(c_req_wdata[R*32+:32]),
    .mem_rsp_valid(c_rsp_valid[R]),.mem_rsp_ready(c_rsp_ready[R]),
    .mem_rsp_rdata(c_rsp_rdata[R*32+:32]),.mem_rsp_error(c_rsp_error[R])
  );
  anvil_q3_gqa_attention #(
    .PROFILE(PROFILE),.NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
    .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN),
    .CACHE_MODE(CACHE_MODE),.INT4_ASYM(INT4_ASYM),.CACHE_BLOCK(CACHE_BLOCK)
  ) attention (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.cmd_valid(state==ATTENTION),
    .cmd_ready(attention_ready),.cmd_layer(layer),.cmd_pos(position),.cmd_phase(phase),
    .done(attention_done),.error(attention_error),
    .c_req_valid(c_req_valid[A+:2]),.c_req_ready(c_req_ready[A+:2]),
    .c_req_write(c_req_write[A+:2]),.c_req_kind(c_req_kind[A*4+:8]),
    .c_req_layer(c_req_layer[A*32+:64]),.c_req_proj(c_req_proj[A*3+:6]),
    .c_req_row(c_req_row[A*32+:64]),.c_req_col(c_req_col[A*32+:64]),.c_req_wdata(c_req_wdata[A*32+:64]),
    .c_rsp_valid(c_rsp_valid[A+:2]),.c_rsp_error(c_rsp_error[A+:2]),
    .c_rsp_ready(c_rsp_ready[A+:2]),.c_rsp_rdata(c_rsp_rdata[A*32+:64])
  );
  anvil_q3_swiglu_mlp #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
    .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) mlp (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.cmd_valid(state==MLP),.cmd_ready(mlp_ready),
    .cmd_layer(layer),.cmd_pos(position),.done(mlp_done),.error(mlp_error),
    .gemv_cmd_valid(mlp_gemv_valid),.gemv_cmd_ready(mlp_owns_gemv && gemv_ready),
    .gemv_cmd_proj(mlp_projection),.gemv_done(mlp_owns_gemv && gemv_done),
    .gemv_error(mlp_owns_gemv && gemv_error),
    .mem_req_valid(c_req_valid[M]),.mem_req_ready(c_req_ready[M]),
    .mem_req_write(c_req_write[M]),.mem_req_kind(c_req_kind[M*4+:4]),
    .mem_req_layer(c_req_layer[M*32+:32]),.mem_req_proj(c_req_proj[M*3+:3]),
    .mem_req_row(c_req_row[M*32+:32]),.mem_req_col(c_req_col[M*32+:32]),.mem_req_wdata(c_req_wdata[M*32+:32]),
    .mem_rsp_valid(c_rsp_valid[M]),.mem_rsp_ready(c_rsp_ready[M]),
    .mem_rsp_rdata(c_rsp_rdata[M*32+:32]),.mem_rsp_error(c_rsp_error[M])
  );
  anvil_q3_elementwise #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
    .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) residual (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .cmd_valid(state==RESIDUAL0 || state==RESIDUAL1),.cmd_ready(residual_ready),
    .cmd_layer(layer),.cmd_pos(position),
    .cmd_mode(state==RESIDUAL1 || state==RESIDUAL1_WAIT ? 2'd1 : 2'd0),
    .done(residual_done),.error(residual_error),
    .mem_req_valid(c_req_valid[E]),.mem_req_ready(c_req_ready[E]),
    .mem_req_write(c_req_write[E]),.mem_req_kind(c_req_kind[E*4+:4]),
    .mem_req_layer(c_req_layer[E*32+:32]),.mem_req_proj(c_req_proj[E*3+:3]),
    .mem_req_row(c_req_row[E*32+:32]),.mem_req_col(c_req_col[E*32+:32]),.mem_req_wdata(c_req_wdata[E*32+:32]),
    .mem_rsp_valid(c_rsp_valid[E]),.mem_rsp_ready(c_rsp_ready[E]),
    .mem_rsp_rdata(c_rsp_rdata[E*32+:32]),.mem_rsp_error(c_rsp_error[E])
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin state<=IDLE; failed<=0; phase<=0; epoch<=0; layer<=0; position<=0; end
    else if (flush) begin state<=IDLE; failed<=0; end
    else if (!failed && ((norm_done && norm_error) || (gemv_done && gemv_error) ||
        (rope_done && rope_error) || (attention_done && attention_error) ||
        (mlp_done && mlp_error) || (residual_done && residual_error))) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        epoch<=cmd_epoch; layer<=cmd_layer; position<=cmd_pos; phase<=PROFILE!=1 && cmd_phase; failed<=0;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin failed<=1; state<=COMPLETE; end
        else state<=NORM0;
      end
      NORM0: if (norm_ready) state<=NORM0_WAIT;
      NORM0_WAIT: if (norm_done) state<=Q;
      Q: if (gemv_ready) state<=Q_WAIT;
      Q_WAIT: if (gemv_done) state<=K;
      K: if (gemv_ready) state<=K_WAIT;
      K_WAIT: if (gemv_done) state<=V;
      V: if (gemv_ready) state<=V_WAIT;
      V_WAIT: if (gemv_done) state<=ROPE;
      ROPE: if (rope_ready) state<=ROPE_WAIT;
      ROPE_WAIT: if (rope_done) state<=ATTENTION;
      ATTENTION: if (attention_ready) state<=ATTENTION_WAIT;
      ATTENTION_WAIT: if (attention_done) state<=O;
      O: if (gemv_ready) state<=O_WAIT;
      O_WAIT: if (gemv_done) state<=RESIDUAL0;
      RESIDUAL0: if (residual_ready) state<=RESIDUAL0_WAIT;
      RESIDUAL0_WAIT: if (residual_done) state<=NORM1;
      NORM1: if (norm_ready) state<=NORM1_WAIT;
      NORM1_WAIT: if (norm_done) state<=MLP;
      MLP: if (mlp_ready) state<=MLP_WAIT;
      MLP_WAIT: if (mlp_done) state<=RESIDUAL1;
      RESIDUAL1: if (residual_ready) state<=RESIDUAL1_WAIT;
      RESIDUAL1_WAIT: if (residual_done) state<=COMPLETE;
      COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
      FAULTED: state<=FAULTED;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
