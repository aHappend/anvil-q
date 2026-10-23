module anvil_q2_w4a16_gemv #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
  AWQ_BITS=4, MAX_SEQ_LEN=32768, BANKS=4, EXTERNAL_CLIENTS=0,
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
  wire [SB-1:0] lane_ready, lane_done, lane_error;
  wire [SB-1:0] mac_waiting;
  wire mac_release=&(mac_waiting|completed|lane_done);
  wire [SB-1:0] reqv, reqr, reqw, rspv, rspr, rspe;
  wire [SB*4-1:0] reqk;
  wire [SB*3-1:0] reqp;
  wire [SB*32-1:0] reql, reqrow, reqcol, reqwd, rsprd;
  wire command=rst_n && state==0 && cmd_valid && (&lane_ready);
  assign cmd_ready=rst_n && state==0 && (&lane_ready);
  assign done=rst_n && state==2;
  assign error=done && failed;
  generate if(!(BANKS==1 || BANKS==2 || BANKS==4)) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2 PARAMETER ERROR: GEMV bank count");
  end endgenerate
  genvar g;
  generate for(g=0;g<SB;g=g+1) begin: engines
    anvil_q2_gemv_lane #(
      NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
      HEAD_DIM,GROUP_SIZE,AWQ_BITS,MAX_SEQ_LEN,g,SB,1) engine(
      .clk(clk),.rst_n(rst_n),.cmd_valid(command),.cmd_ready(lane_ready[g]),
      .cmd_layer(cmd_layer),.cmd_pos(cmd_pos),.cmd_proj(cmd_proj),
      .done(lane_done[g]),.error(lane_error[g]),
      .mem_req_valid(reqv[g]),.mem_req_ready(reqr[g]),.mem_req_write(reqw[g]),
      .mem_req_kind(reqk[g*4+:4]),.mem_req_layer(reql[g*32+:32]),
      .mem_req_proj(reqp[g*3+:3]),.mem_req_row(reqrow[g*32+:32]),
      .mem_req_col(reqcol[g*32+:32]),.mem_req_wdata(reqwd[g*32+:32]),
      .mem_rsp_valid(rspv[g]),.mem_rsp_ready(rspr[g]),
      .mem_rsp_rdata(rsprd[g*32+:32]),.mem_rsp_error(rspe[g]),
      .mac_waiting(mac_waiting[g]),.mac_release(mac_release));
  end
  if(EXTERNAL_CLIENTS) begin: external_routing
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
    if(!rst_n) begin state<=0; failed<=0; completed<=0; end
    else case(state)
      0: if(command) begin state<=1; failed<=0; completed<=0; end
      1: begin
        completed<=completed|lane_done;
        failed<=failed|(|lane_error);
        if(&(completed|lane_done)) state<=2;
      end
      2: state<=0;
      default: state<=0;
    endcase
  end
endmodule
