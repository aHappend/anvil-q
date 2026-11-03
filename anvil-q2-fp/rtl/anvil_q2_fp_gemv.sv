module anvil_q2_fp_gemv #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
  AWQ_BITS=4, MAX_SEQ_LEN=32768, BANKS=4, EXTERNAL_CLIENTS=0,
  FP_FORMAT=0, WEIGHT_MODE=0,
  SB=(BANKS==1 || BANKS==2 || BANKS==4) ? BANKS : 1
)(
  input wire clk, rst_n, cmd_valid, output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, input wire [2:0] cmd_proj,
  output wire done, error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error,
  output wire [SB-1:0] g_req_valid,
  input wire [SB-1:0] g_req_ready,
  output wire [SB-1:0] g_req_write,
  output wire [SB*4-1:0] g_req_kind,
  output wire [SB*32-1:0] g_req_layer,
  output wire [SB*3-1:0] g_req_proj,
  output wire [SB*32-1:0] g_req_row, g_req_col, g_req_wdata,
  input wire [SB-1:0] g_rsp_valid,
  output wire [SB-1:0] g_rsp_ready,
  input wire [SB*32-1:0] g_rsp_rdata,
  input wire [SB-1:0] g_rsp_error
);
  reg [1:0] state;
  reg failed;
  reg [SB-1:0] completed;
  wire [SB-1:0] ready, finished, faults;
  wire [SB-1:0] reqv, reqr, reqw, rspv, rspr, rspe;
  wire [SB*4-1:0] reqk;
  wire [SB*3-1:0] reqp;
  wire [SB*32-1:0] reql, reqrow, reqcol, reqwd, rsprd;
  wire command=cmd_valid && cmd_ready;
  assign cmd_ready=rst_n && state==0 && (&ready);
  assign done=rst_n && state==2;
  assign error=done && failed;
  anvil_q2_fp_parameters #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .GROUP_SIZE(GROUP_SIZE),.AWQ_BITS(AWQ_BITS),.VOCAB_SIZE(1),.MAX_SEQ_LEN(MAX_SEQ_LEN),
    .BANKS(BANKS),.FP_FORMAT(FP_FORMAT),.WEIGHT_MODE(WEIGHT_MODE),
    .CACHE_BLOCK(1)) parameters_ok();
  genvar b;
  generate for (b=0;b<SB;b=b+1) begin: banks
    wire iv, ir, first, last, ov, ore, ol;
    wire [15:0] a;
    wire [127:0] w;
    wire [255:0] sum;
    anvil_q2_fp_dot_lane #(.FP_FORMAT(FP_FORMAT)) lane(
      .clk(clk),.rst_n(rst_n),.in_valid(iv),.in_ready(ir),.in_a(a),.in_b(w),
      .in_first(first),.in_last(last),.out_valid(ov),.out_ready(ore),
      .out_sum(sum),.out_last(ol));
    anvil_q2_fp_gemv_bank #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
      .MAX_SEQ_LEN(MAX_SEQ_LEN),.BANK_ID(b),.BANKS(SB),
      .FP_FORMAT(FP_FORMAT),.WEIGHT_MODE(WEIGHT_MODE)) controller(
      .clk(clk),.rst_n(rst_n),.cmd_valid(command),.cmd_ready(ready[b]),
      .cmd_layer(cmd_layer),.cmd_pos(cmd_pos),.cmd_proj(cmd_proj),
      .done(finished[b]),.error(faults[b]),
      .mem_req_valid(reqv[b]),.mem_req_ready(reqr[b]),.mem_req_write(reqw[b]),
      .mem_req_kind(reqk[b*4+:4]),.mem_req_layer(reql[b*32+:32]),.mem_req_proj(reqp[b*3+:3]),
      .mem_req_row(reqrow[b*32+:32]),.mem_req_col(reqcol[b*32+:32]),
      .mem_req_wdata(reqwd[b*32+:32]),.mem_rsp_valid(rspv[b]),.mem_rsp_ready(rspr[b]),
      .mem_rsp_rdata(rsprd[b*32+:32]),.mem_rsp_error(rspe[b]),
      .lane_in_valid(iv),.lane_in_ready(ir),.lane_in_a(a),.lane_in_b(w),
      .lane_in_first(first),.lane_in_last(last),.lane_out_valid(ov),.lane_out_ready(ore),
      .lane_out_sum(sum),.lane_out_last(ol));
  end
  if (EXTERNAL_CLIENTS) begin: external_routing
    assign g_req_valid=reqv; assign reqr=g_req_ready;
    assign g_req_write=reqw; assign g_req_kind=reqk; assign g_req_layer=reql;
    assign g_req_proj=reqp; assign g_req_row=reqrow; assign g_req_col=reqcol;
    assign g_req_wdata=reqwd; assign rspv=g_rsp_valid; assign g_rsp_ready=rspr;
    assign rsprd=g_rsp_rdata; assign rspe=g_rsp_error;
    assign mem_req_valid=0; assign mem_req_write=0; assign mem_req_kind=0;
    assign mem_req_layer=0; assign mem_req_proj=0; assign mem_req_row=0;
    assign mem_req_col=0; assign mem_req_wdata=0; assign mem_rsp_ready=0;
  end else begin: scalar_routing
    assign g_req_valid=0; assign g_req_write=0; assign g_req_kind=0;
    assign g_req_layer=0; assign g_req_proj=0; assign g_req_row=0;
    assign g_req_col=0; assign g_req_wdata=0; assign g_rsp_ready=0;
    anvil_q2_scalar_arbiter #(SB) scalar_bus(
      clk,rst_n,reqv,reqr,reqw,reqk,reql,reqp,reqrow,reqcol,reqwd,
      rspv,rspr,rsprd,rspe,mem_req_valid,mem_req_ready,mem_req_write,
      mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata,
      mem_rsp_valid,mem_rsp_ready,mem_rsp_rdata,mem_rsp_error);
  end endgenerate
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin state<=0; failed<=0; completed<=0; end
    else case (state)
      0: if (command) begin state<=1; failed<=0; completed<=0; end
      1: begin
        completed<=completed|finished;
        failed<=failed|(|faults);
        if (&(completed|finished)) state<=2;
      end
      2: state<=0;
      default: state<=0;
    endcase
  end
endmodule
