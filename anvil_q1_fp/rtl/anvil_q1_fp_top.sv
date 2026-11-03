module anvil_q1_fp_top #(
  parameter NUM_LAYERS=24, HIDDEN_SIZE=896, INTERMEDIATE_SIZE=4864,
  NUM_Q_HEADS=14, NUM_KV_HEADS=2, HEAD_DIM=64, GROUP_SIZE=128,
  AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768
)(
  input wire clk, rst_n,
  input wire token_valid, output wire token_ready,
  input wire [31:0] token_id, token_pos, input wire new_sequence,
  output wire logit_valid, input wire logit_ready,
  output wire [31:0] logit_index, output wire signed [31:0] logit_data,
  output wire done, error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error,
  input wire [1:0] precision_mode
);
  reg [4:0] state;
  reg failed, sequence_valid;
  reg [1:0] precision, sequence_precision;
  reg [31:0] token, position, next_position, component, vocabulary, layer;
  reg signed [31:0] activation;
  reg signed [95:0] logit_sum;
  reg signed [63:0] logit_product;
  reg [15:0] native_weight;
  reg [31:0] native_sum, tensor_word;
  wire [31:0] native_tensor;
  wire native_valid;
  wire [31:0] native_result;
  wire [4:0] native_status;
  wire [1:0] ready, finished, faults;
  wire [2:0] reqv, reqr, reqw, rspv, rspr, rspe;
  wire [11:0] reqk;
  wire [8:0] reqp;
  wire [95:0] reql, reqrow, reqcol, reqwd, rsprd;
  wire [31:0] selected;
  wire own_idle, own_complete, own_fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd;
  anvil_q1_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,VOCAB_SIZE,MAX_SEQ_LEN) parameters_ok();
  assign selected=(state==5 || state==6) ? 1 : ((state==7 || state==8) ? 2 : 0);
  assign native_tensor=anvil_q1_fp_pkg::widen16(rd[15:0],precision);
  anvil_q1_fp_dot8_mixed output_dot(
    clk,rst_n,state==18,precision,{224'd0,activation},{112'd0,native_weight},
    8'b00000001,native_sum,native_valid,native_result,native_status);
  assign token_ready=rst_n && state==0;
  assign logit_valid=rst_n && state==15;
  assign logit_index=rst_n ? vocabulary : 0;
  assign logit_data=rst_n ? (precision==0 ? anvil_q1_fp_compat_pkg::sat32(
    anvil_q1_fp_compat_pkg::round_shift({{32{logit_sum[95]}},logit_sum},16)) : native_sum) : 0;
  assign done=rst_n && state==31;
  assign error=done && failed;
  anvil_q1_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(wr),.kind(kind),.layer(32'd0),
    .proj(3'd0),.row(row),.col(col),.wdata(wd),
    .idle(own_idle),.complete(own_complete),.rdata(rd),.fault(own_fault),
    .mem_req_valid(reqv[0]),.mem_req_ready(reqr[0]),
    .mem_req_write(reqw[0]),.mem_req_kind(reqk[0+:4]),
    .mem_req_layer(reql[0+:32]),.mem_req_proj(reqp[0+:3]),
    .mem_req_row(reqrow[0+:32]),.mem_req_col(reqcol[0+:32]),.mem_req_wdata(reqwd[0+:32]),
    .mem_rsp_valid(rspv[0]),.mem_rsp_ready(rspr[0]),
    .mem_rsp_rdata(rsprd[0+:32]),.mem_rsp_error(rspe[0]));
  anvil_q1_fp_decoder_layer #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,MAX_SEQ_LEN) decoder(
    clk,rst_n,rst_n && state==5,ready[0],layer,position,finished[0],faults[0],
    reqv[1],reqr[1],reqw[1],reqk[4+:4],reql[32+:32],reqp[3+:3],
    reqrow[32+:32],reqcol[32+:32],reqwd[32+:32],rspv[1],rspr[1],rsprd[32+:32],rspe[1],precision);
  anvil_q1_fp_rmsnorm #(NUM_LAYERS,HIDDEN_SIZE,MAX_SEQ_LEN) final_norm(
    clk,rst_n,rst_n && state==7,ready[1],32'd0,position,2'd2,finished[1],faults[1],
    reqv[2],reqr[2],reqw[2],reqk[8+:4],reql[64+:32],reqp[6+:3],
    reqrow[64+:32],reqcol[64+:32],reqwd[64+:32],rspv[2],rspr[2],rsprd[64+:32],rspe[2],precision);
  anvil_q1_bus_mux #(3) bus(
    rst_n,selected,reqv,reqr,reqw,reqk,reql,reqp,reqrow,reqcol,reqwd,
    rspv,rspr,rsprd,rspe,mem_req_valid,mem_req_ready,mem_req_write,mem_req_kind,
    mem_req_layer,mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata,
    mem_rsp_valid,mem_rsp_ready,mem_rsp_rdata,mem_rsp_error);
  always @* begin
    issue=0; wr=0; kind=0; row=0; col=0; wd=0;
    if(rst_n && own_idle) case(state)
      1: begin issue=1; kind=0; row=token; col=component; end
      3: begin issue=1; wr=1; kind=8; col=component; wd=activation; end
      9: begin issue=1; kind=8; row=14; col=component; end
      11: begin issue=1; kind=0; row=vocabulary; col=component; end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; failed<=0; sequence_valid<=1; token<=0; position<=0;
      next_position<=0; component<=0; vocabulary<=0; layer<=0;
      activation<=0; logit_sum<=0; logit_product<=0; tensor_word<=0;
      precision<=0; sequence_precision<=0; native_sum<=0; native_weight<=0;
    end else if(own_fault || (state==19 && native_valid && |native_status[4:2])) begin
      failed<=1; sequence_valid<=0; state<=31;
    end else case(state)
      0: if(token_valid) begin
        failed<=0;
        if(token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN || precision_mode==3 ||
           (new_sequence && token_pos!=0) ||
           (!new_sequence && (!sequence_valid || token_pos!=next_position ||
             precision_mode!=sequence_precision))) begin
          failed<=1; sequence_valid<=0; state<=30;
        end else begin
          token<=token_id; position<=token_pos; component<=0; vocabulary<=0;
          precision<=precision_mode; sequence_precision<=precision_mode;
          layer<=0; logit_sum<=0; native_sum<=0; state<=1;
        end
      end
      1: if(issue) state<=2;
      2: if(own_complete) begin
        if((precision==0 && anvil_q1_fp_compat_pkg::f16_invalid(rd[15:0])) ||
           (precision!=0 && (rd[31:16]!=0 || native_tensor[30:23]==255)))
          begin failed<=1; sequence_valid<=0; state<=31; end
        else begin
          if(precision==0) activation<=anvil_q1_fp_compat_pkg::f16_q16(rd[15:0]);
          else activation<=native_tensor;
          state<=3;
        end
      end
      3: if(issue) state<=4;
      4: if(own_complete) begin
        if(component+1<HIDDEN_SIZE) begin component<=component+1; state<=1; end
        else state<=5;
      end
      5: if(ready[0]) state<=6;
      6: if(finished[0]) begin
        if(faults[0]) begin failed<=1; sequence_valid<=0; state<=31; end
        else if(layer+1<NUM_LAYERS) begin layer<=layer+1; state<=5; end
        else state<=7;
      end
      7: if(ready[1]) state<=8;
      8: if(finished[1]) begin
        if(faults[1]) begin failed<=1; sequence_valid<=0; state<=31; end
        else begin component<=0; vocabulary<=0; logit_sum<=0; native_sum<=0; state<=9; end
      end
      9: if(issue) state<=10;
      10: if(own_complete) begin
        if(precision!=0 && rd[30:23]==255) begin failed<=1; sequence_valid<=0; state<=31; end
        else begin activation<=rd; state<=11; end
      end
      11: if(issue) state<=12;
      12: if(own_complete) begin
        if((precision==0 && anvil_q1_fp_compat_pkg::f16_invalid(rd[15:0])) ||
           (precision!=0 && (rd[31:16]!=0 || native_tensor[30:23]==255)))
          begin failed<=1; sequence_valid<=0; state<=31; end
        else if(precision==0) begin
          tensor_word<=anvil_q1_fp_compat_pkg::f16_q16(rd[15:0]); state<=16;
        end else begin native_weight<=rd[15:0]; state<=18; end
      end
      16: begin logit_product<=$signed(activation)*$signed(tensor_word); state<=17; end
      17: begin logit_sum<=logit_sum+{{32{logit_product[63]}},logit_product}; state<=13; end
      18: state<=19;
      19: if(native_valid) begin native_sum<=native_result; state<=13; end
      13: if(component+1<HIDDEN_SIZE) begin component<=component+1; state<=9; end
          else state<=15;
      15: if(logit_ready) begin
        if(vocabulary+1<VOCAB_SIZE) begin
          vocabulary<=vocabulary+1; component<=0; logit_sum<=0; native_sum<=0; state<=9;
        end else begin
          next_position<=position+1; sequence_valid<=1; state<=31;
        end
      end
      30: state<=31;
      31: state<=0;
      default: state<=0;
    endcase
  end
endmodule
