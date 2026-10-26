module anvil_q2_fp_decoder_layer #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
  AWQ_BITS=4, MAX_SEQ_LEN=32768, BANKS=4, EXTERNAL_CLIENTS=0,
  CACHE_MODE=0, CACHE_BLOCK=16, EXPLICIT_PHASE=0, FP_FORMAT=0, WEIGHT_MODE=0,
  SB=(BANKS==1 || BANKS==2 || BANKS==4) ? BANKS : 1
)(
  input wire clk, rst_n, cmd_valid, output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, output wire done, error,
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
  input wire [SB-1:0] g_rsp_error,
  input wire cmd_phase
);
  reg [2:0] state;
  reg [3:0] step;
  reg failed;
  reg [31:0] layer, position;
  reg phase;
  reg [31:0] selected;
  reg [2:0] projection;
  reg [1:0] norm_mode, element_mode;
  wire [5:0] ready, finished, faults;
  wire [5:0] reqv, reqr, reqw, rspv, rspr, rspe;
  wire [23:0] reqk;
  wire [17:0] reqp;
  wire [191:0] reql, reqrow, reqcol, reqwd, rsprd;
  wire [5:0] command;
  wire [SB-1:0] eg_reqv, eg_reqr, eg_reqw, eg_rspv, eg_rspr, eg_rspe;
  wire [SB-1:0] mg_reqv, mg_reqr, mg_reqw, mg_rspv, mg_rspr, mg_rspe;
  wire [SB*4-1:0] eg_reqk, mg_reqk;
  wire [SB*3-1:0] eg_reqp, mg_reqp;
  wire [SB*32-1:0] eg_reql, eg_reqrow, eg_reqcol, eg_reqwd, eg_rsprd;
  wire [SB*32-1:0] mg_reql, mg_reqrow, mg_reqcol, mg_reqwd, mg_rsprd;
  genvar g;
  generate for(g=0;g<6;g=g+1) begin: commands
    assign command[g]=rst_n && state==1 && selected==g;
  end
  for(g=0;g<SB;g=g+1) begin: engine_routes
    anvil_q2_bus_mux #(2) route(
      rst_n,selected==4 ? 32'd1 : 32'd0,
      {mg_reqv[g],eg_reqv[g]},{mg_reqr[g],eg_reqr[g]},
      {mg_reqw[g],eg_reqw[g]},
      {mg_reqk[g*4+:4],eg_reqk[g*4+:4]},
      {mg_reql[g*32+:32],eg_reql[g*32+:32]},
      {mg_reqp[g*3+:3],eg_reqp[g*3+:3]},
      {mg_reqrow[g*32+:32],eg_reqrow[g*32+:32]},
      {mg_reqcol[g*32+:32],eg_reqcol[g*32+:32]},
      {mg_reqwd[g*32+:32],eg_reqwd[g*32+:32]},
      {mg_rspv[g],eg_rspv[g]},{mg_rspr[g],eg_rspr[g]},
      {mg_rsprd[g*32+:32],eg_rsprd[g*32+:32]},
      {mg_rspe[g],eg_rspe[g]},g_req_valid[g],g_req_ready[g],g_req_write[g],
      g_req_kind[g*4+:4],g_req_layer[g*32+:32],g_req_proj[g*3+:3],
      g_req_row[g*32+:32],g_req_col[g*32+:32],g_req_wdata[g*32+:32],
      g_rsp_valid[g],g_rsp_ready[g],g_rsp_rdata[g*32+:32],g_rsp_error[g]);
  end endgenerate
  assign cmd_ready=rst_n && state==0;
  assign done=rst_n && state==3;
  assign error=done && failed;
  always @* begin
    selected=0; projection=0; norm_mode=0; element_mode=0;
    case(step)
      0: begin selected=0; norm_mode=0; end
      1: begin selected=1; projection=0; end
      2: begin selected=1; projection=1; end
      3: begin selected=1; projection=2; end
      4: selected=2;
      5: selected=3;
      6: begin selected=1; projection=3; end
      7: begin selected=5; element_mode=0; end
      8: begin selected=0; norm_mode=1; end
      9: selected=4;
      10: begin selected=5; element_mode=1; end
      default: selected=0;
    endcase
  end
  anvil_q2_fp_rmsnorm #(NUM_LAYERS,HIDDEN_SIZE,MAX_SEQ_LEN,FP_FORMAT) norm(
    clk,rst_n,command[0],ready[0],layer,position,norm_mode,finished[0],faults[0],
    reqv[0],reqr[0],reqw[0],reqk[0+:4],reql[0+:32],reqp[0+:3],
    reqrow[0+:32],reqcol[0+:32],reqwd[0+:32],rspv[0],rspr[0],rsprd[0+:32],rspe[0]);
  anvil_q2_fp_gemv #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,MAX_SEQ_LEN,BANKS,EXTERNAL_CLIENTS,
    FP_FORMAT,WEIGHT_MODE) gemv(
    clk,rst_n,command[1],ready[1],layer,position,projection,finished[1],faults[1],
    reqv[1],reqr[1],reqw[1],reqk[4+:4],reql[32+:32],reqp[3+:3],
    reqrow[32+:32],reqcol[32+:32],reqwd[32+:32],rspv[1],rspr[1],rsprd[32+:32],rspe[1],
    eg_reqv,eg_reqr,eg_reqw,eg_reqk,eg_reql,eg_reqp,eg_reqrow,eg_reqcol,eg_reqwd,
    eg_rspv,eg_rspr,eg_rsprd,eg_rspe);
  anvil_q2_fp_rope #(
    NUM_LAYERS,HIDDEN_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,HEAD_DIM,MAX_SEQ_LEN) rope(
    clk,rst_n,command[2],ready[2],layer,position,finished[2],faults[2],
    reqv[2],reqr[2],reqw[2],reqk[8+:4],reql[64+:32],reqp[6+:3],
    reqrow[64+:32],reqcol[64+:32],reqwd[64+:32],rspv[2],rspr[2],rsprd[64+:32],rspe[2]);
  anvil_q2_fp_gqa_attention #(
    NUM_LAYERS,HIDDEN_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,HEAD_DIM,MAX_SEQ_LEN,
    CACHE_MODE,CACHE_BLOCK,1,FP_FORMAT) attention(
    clk,rst_n,command[3],ready[3],layer,position,finished[3],faults[3],
    reqv[3],reqr[3],reqw[3],reqk[12+:4],reql[96+:32],reqp[9+:3],
    reqrow[96+:32],reqcol[96+:32],reqwd[96+:32],rspv[3],rspr[3],rsprd[96+:32],rspe[3],
    phase);
  anvil_q2_fp_swiglu_mlp #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,MAX_SEQ_LEN,BANKS,EXTERNAL_CLIENTS,
    CACHE_MODE,CACHE_BLOCK,EXPLICIT_PHASE,FP_FORMAT,WEIGHT_MODE) mlp(
    clk,rst_n,command[4],ready[4],layer,position,finished[4],faults[4],
    reqv[4],reqr[4],reqw[4],reqk[16+:4],reql[128+:32],reqp[12+:3],
    reqrow[128+:32],reqcol[128+:32],reqwd[128+:32],rspv[4],rspr[4],rsprd[128+:32],rspe[4],
    mg_reqv,mg_reqr,mg_reqw,mg_reqk,mg_reql,mg_reqp,mg_reqrow,mg_reqcol,mg_reqwd,
    mg_rspv,mg_rspr,mg_rsprd,mg_rspe);
  anvil_q2_fp_elementwise #(NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,MAX_SEQ_LEN) residual(
    clk,rst_n,command[5],ready[5],layer,position,element_mode,finished[5],faults[5],
    reqv[5],reqr[5],reqw[5],reqk[20+:4],reql[160+:32],reqp[15+:3],
    reqrow[160+:32],reqcol[160+:32],reqwd[160+:32],rspv[5],rspr[5],rsprd[160+:32],rspe[5]);
  anvil_q2_bus_mux #(6) bus(
    rst_n,selected,reqv,reqr,reqw,reqk,reql,reqp,reqrow,reqcol,reqwd,
    rspv,rspr,rsprd,rspe,mem_req_valid,mem_req_ready,mem_req_write,mem_req_kind,
    mem_req_layer,mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata,
    mem_rsp_valid,mem_rsp_ready,mem_rsp_rdata,mem_rsp_error);
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin state<=0; step<=0; failed<=0; layer<=0; position<=0; phase<=0; end
    else case(state)
      0: if(cmd_valid) begin
        layer<=cmd_layer; position<=cmd_pos; failed<=0; step<=0;
        phase<=EXPLICIT_PHASE ? cmd_phase : 1'b0;
        if(cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN)
          begin failed<=1; state<=4; end
        else state<=1;
      end
      1: if(ready[selected]) state<=2;
      2: if(finished[selected]) begin
        if(faults[selected]) begin failed<=1; state<=3; end
        else if(step==10) state<=3;
        else begin step<=step+1; state<=1; end
      end
      3: state<=0;
      4: state<=3;
      default: state<=0;
    endcase
  end
endmodule
