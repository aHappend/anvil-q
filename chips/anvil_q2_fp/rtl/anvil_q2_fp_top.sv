module anvil_q2_fp_top #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
  AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  BANKS=4, CACHE_MODE=0, CACHE_BLOCK=16, QUEUE_DEPTH=3,
  FP_FORMAT=0, WEIGHT_MODE=0,
  SB=(BANKS==1 || BANKS==2 || BANKS==4) ? BANKS : 1
)(
  input wire clk, rst_n, cancel,
  input wire token_valid, output wire token_ready,
  input wire [31:0] token_id, token_pos, input wire new_sequence, token_phase,
  output wire logit_valid, input wire logit_ready,
  output wire [31:0] logit_index, logit_data,
  output wire done, error, cancel_done,
  output wire [SB-1:0] mem_req_valid,
  input wire [SB-1:0] mem_req_ready,
  output wire [SB-1:0] mem_req_write,
  output wire [SB*4-1:0] mem_req_kind,
  output wire [SB*32-1:0] mem_req_layer,
  output wire [SB*3-1:0] mem_req_proj,
  output wire [SB*32-1:0] mem_req_row, mem_req_col, mem_req_wdata,
  output wire [SB*64-1:0] mem_req_tag,
  input wire [SB-1:0] mem_rsp_valid, mem_rsp_error,
  output wire [SB-1:0] mem_rsp_ready,
  input wire [SB*32-1:0] mem_rsp_rdata,
  input wire [SB*64-1:0] mem_rsp_tag
);
  import anvil_q2_fp_pkg::*;
  reg [4:0] state;
  reg failed, sequence_valid;
  reg clear_core, active_token, cancelled_active, cancel_pending, phase, decoding;
  reg [31:0] prefill_cursor, frozen_prefill_count;
  reg [31:0] token, position, next_position, component, vocabulary, layer;
  reg [15:0] raw_f16;
  reg [31:0] activation, logit_weight_reg, logit_sum, logit_product;
  wire [31:0] tensor_value=expand16(raw_f16,FP_FORMAT);
  wire [31:0] logit_input=expand16(narrow16(activation,FP_FORMAT),FP_FORMAT);
  wire alu_ready, alu_valid, alu_error;
  wire [31:0] alu_result;
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
  wire scheduler_idle, scheduler_drained, scheduler_fault;
  wire effective_phase=token_phase;
  wire core_rst_n=rst_n && !cancel && !clear_core &&
                   state!=24 && state!=25 && state!=26;
  wire operation_fault=own_fault || scheduler_fault ||
    (state==6 && finished[0] && faults[0]) ||
    (state==8 && finished[1] && faults[1]) ||
    (alu_valid && alu_error) ||
    (state==19 && !fp_is_finite(activation));
  wire [SB:0] c_reqv, c_reqr, c_reqw, c_rspv, c_rspr, c_rspe;
  wire [(SB+1)*4-1:0] c_reqk;
  wire [(SB+1)*3-1:0] c_reqp;
  wire [(SB+1)*32-1:0] c_reql, c_reqrow, c_reqcol, c_reqwd, c_rsprd;
  wire scalar_req_valid, scalar_req_ready;
  wire scalar_req_write;
  wire [3:0] scalar_req_kind;
  wire [2:0] scalar_req_proj;
  wire [31:0] scalar_req_layer, scalar_req_row, scalar_req_col, scalar_req_wdata;
  reg scalar_pending, scalar_write;
  reg [3:0] scalar_kind;
  reg [2:0] scalar_proj;
  reg [31:0] scalar_layer, scalar_row, scalar_col, scalar_wdata;
  anvil_q2_fp_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,VOCAB_SIZE,MAX_SEQ_LEN,
    BANKS,FP_FORMAT,WEIGHT_MODE,CACHE_MODE,CACHE_BLOCK,QUEUE_DEPTH) parameters_ok();
  assign selected=(state==5 || state==6) ? 1 : ((state==7 || state==8) ? 2 : 0);
  assign token_ready=rst_n && !cancel && state==0 && scheduler_idle;
  assign logit_valid=core_rst_n && state==15;
  assign logit_index=rst_n ? vocabulary : 0;
  assign logit_data=rst_n ? logit_sum : 32'd0;
  assign done=rst_n && !cancel && (state==31 || (state==26 && cancelled_active));
  assign error=done && failed;
  assign cancel_done=rst_n && !cancel && state==26;
  anvil_q2_mem_port memory_port(
    .clk(clk),.rst_n(core_rst_n),.issue(issue),.write(wr),.kind(kind),.layer(32'd0),
    .proj(3'd0),.row(row),.col(col),.wdata(wd),
    .idle(own_idle),.complete(own_complete),.rdata(rd),.fault(own_fault),
    .mem_req_valid(reqv[0]),.mem_req_ready(reqr[0]),
    .mem_req_write(reqw[0]),.mem_req_kind(reqk[0+:4]),
    .mem_req_layer(reql[0+:32]),.mem_req_proj(reqp[0+:3]),
    .mem_req_row(reqrow[0+:32]),.mem_req_col(reqcol[0+:32]),.mem_req_wdata(reqwd[0+:32]),
    .mem_rsp_valid(rspv[0]),.mem_rsp_ready(rspr[0]),
    .mem_rsp_rdata(rsprd[0+:32]),.mem_rsp_error(rspe[0]));
  anvil_q2_fp_decoder_layer #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,MAX_SEQ_LEN,BANKS,1,
    CACHE_MODE,CACHE_BLOCK,1,FP_FORMAT,WEIGHT_MODE) decoder(
    clk,core_rst_n,state==5,ready[0],layer,position,finished[0],faults[0],
    reqv[1],reqr[1],reqw[1],reqk[4+:4],reql[32+:32],reqp[3+:3],
    reqrow[32+:32],reqcol[32+:32],reqwd[32+:32],rspv[1],rspr[1],rsprd[32+:32],rspe[1],
    c_reqv[0+:SB],c_reqr[0+:SB],c_reqw[0+:SB],c_reqk[0+:SB*4],
    c_reql[0+:SB*32],c_reqp[0+:SB*3],c_reqrow[0+:SB*32],
    c_reqcol[0+:SB*32],c_reqwd[0+:SB*32],c_rspv[0+:SB],c_rspr[0+:SB],
    c_rsprd[0+:SB*32],c_rspe[0+:SB],phase);
  anvil_q2_fp_rmsnorm #(NUM_LAYERS,HIDDEN_SIZE,MAX_SEQ_LEN,FP_FORMAT) final_norm(
    clk,core_rst_n,state==7,ready[1],32'd0,position,2'd2,finished[1],faults[1],
    reqv[2],reqr[2],reqw[2],reqk[8+:4],reql[64+:32],reqp[6+:3],
    reqrow[64+:32],reqcol[64+:32],reqwd[64+:32],rspv[2],rspr[2],rsprd[64+:32],rspe[2]);
  anvil_q2_bus_mux #(3) bus(
    core_rst_n,selected,reqv,reqr,reqw,reqk,reql,reqp,reqrow,reqcol,reqwd,
    rspv,rspr,rsprd,rspe,scalar_req_valid,scalar_req_ready,scalar_req_write,
    scalar_req_kind,scalar_req_layer,scalar_req_proj,scalar_req_row,
    scalar_req_col,scalar_req_wdata,
    c_rspv[SB],c_rspr[SB],c_rsprd[SB*32+:32],c_rspe[SB]);
  // No ready look-through: mux selection and scheduler arbitration are separate paths.
  assign scalar_req_ready=core_rst_n && !scalar_pending;
  assign c_reqv[SB]=core_rst_n && scalar_pending;
  assign c_reqw[SB]=scalar_write;
  assign c_reqk[SB*4+:4]=scalar_kind;
  assign c_reql[SB*32+:32]=scalar_layer;
  assign c_reqp[SB*3+:3]=scalar_proj;
  assign c_reqrow[SB*32+:32]=scalar_row;
  assign c_reqcol[SB*32+:32]=scalar_col;
  assign c_reqwd[SB*32+:32]=scalar_wdata;
  always @(posedge clk or negedge core_rst_n) begin
    if(!core_rst_n) begin
      scalar_pending<=0; scalar_write<=0; scalar_kind<=0; scalar_proj<=0;
      scalar_layer<=0; scalar_row<=0; scalar_col<=0; scalar_wdata<=0;
    end else if(scalar_pending) begin
      if(c_reqr[SB]) scalar_pending<=0;
    end else if(scalar_req_valid && scalar_req_ready) begin
      scalar_pending<=1;
      scalar_write<=scalar_req_write; scalar_kind<=scalar_req_kind;
      scalar_layer<=scalar_req_layer; scalar_proj<=scalar_req_proj;
      scalar_row<=scalar_req_row; scalar_col<=scalar_req_col;
      scalar_wdata<=scalar_req_wdata;
    end
  end
  anvil_q2_bank_scheduler #(BANKS,SB+1,QUEUE_DEPTH) bank_scheduler(
    .clk(clk),.rst_n(rst_n),.flush(cancel || state==24),
    .idle(scheduler_idle),.drain_done(scheduler_drained),.fault(scheduler_fault),
    .c_req_valid(c_reqv),.c_req_ready(c_reqr),.c_req_write(c_reqw),
    .c_req_kind(c_reqk),.c_req_layer(c_reql),.c_req_proj(c_reqp),
    .c_req_row(c_reqrow),.c_req_col(c_reqcol),.c_req_wdata(c_reqwd),
    .c_rsp_valid(c_rspv),.c_rsp_ready(c_rspr),.c_rsp_rdata(c_rsprd),.c_rsp_error(c_rspe),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_tag(mem_req_tag),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag));
  anvil_q2_fp_scalar output_arithmetic(
    .clk(clk),.rst_n(core_rst_n),.in_valid(state==19 || state==21),.in_ready(alu_ready),
    .in_op(state==19 ? 3'd1 : 3'd0),
    .in_a(state==19 ? activation : logit_sum),
    .in_b(state==19 ? logit_weight_reg : logit_product),
    .out_valid(alu_valid),.out_ready(1'b1),.out_data(alu_result),.out_error(alu_error));
  always @* begin
    issue=0; wr=0; kind=0; row=0; col=0; wd=0;
    if(core_rst_n && own_idle) case(state)
      1: begin issue=1; kind=0; row=token; col=component; end
      3: begin issue=1; wr=1; kind=8; col=component; wd=activation; end
      9: begin issue=1; kind=8; row=14; col=component; end
      11: begin issue=1; kind=0; row=vocabulary; col=component; end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=0; failed<=0; sequence_valid<=0; token<=0; position<=0;
      next_position<=0; component<=0; vocabulary<=0; layer<=0;
      raw_f16<=0; activation<=0; logit_weight_reg<=0; logit_sum<=0; logit_product<=0;
      clear_core<=0; active_token<=0; cancelled_active<=0; phase<=0;
      cancel_pending<=0;
      decoding<=0; prefill_cursor<=0; frozen_prefill_count<=0;
    end else if(cancel) begin
      failed<=1; sequence_valid<=0; clear_core<=1;
      cancelled_active<=active_token; cancel_pending<=1; state<=25;
      decoding<=0; prefill_cursor<=0; frozen_prefill_count<=0;
    end else if(operation_fault && state!=24 && state!=25 && state!=26) begin
      failed<=1; sequence_valid<=0; clear_core<=1;
      cancelled_active<=0; cancel_pending<=0; state<=24;
      decoding<=0; prefill_cursor<=0; frozen_prefill_count<=0;
    end
    else case(state)
      0: if(token_valid && token_ready) begin
        failed<=0; cancelled_active<=0; cancel_pending<=0;
        if(token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN ||
           (new_sequence && token_pos!=0) ||
           (!new_sequence && (!sequence_valid || token_pos!=next_position ||
             (decoding && !effective_phase) ||
             (decoding && effective_phase && token_pos<frozen_prefill_count) ||
             (!effective_phase && token_pos!=prefill_cursor)))) begin
          failed<=1; sequence_valid<=0; clear_core<=1; active_token<=0; state<=31;
        end else begin
          token<=token_id; position<=token_pos; component<=0; vocabulary<=0;
          layer<=0; logit_sum<=0; active_token<=1; phase<=effective_phase;
          if(new_sequence) begin
            clear_core<=1; sequence_valid<=1; next_position<=0;
            decoding<=effective_phase; prefill_cursor<=0; frozen_prefill_count<=0;
            state<=16;
          end else begin
            if(effective_phase && !decoding) begin
              decoding<=1; frozen_prefill_count<=prefill_cursor;
            end
            clear_core<=0; state<=1;
          end
        end
      end
      1: if(issue) state<=2;
      2: if(own_complete) begin
        if (rd[31:16]!=0) begin
          failed<=1; sequence_valid<=0; clear_core<=1; state<=24;
        end else begin raw_f16<=rd[15:0]; state<=17; end
      end
      17: if(!fp_is_finite(tensor_value)) begin
        failed<=1; sequence_valid<=0; clear_core<=1; state<=24;
      end else begin activation<=tensor_value; state<=3; end
      3: if(issue) state<=4;
      4: if(own_complete) begin
        if(component+1<HIDDEN_SIZE) begin component<=component+1; state<=1; end
        else state<=5;
      end
      5: if(ready[0]) state<=6;
      6: if(finished[0]) begin
        if(layer+1<NUM_LAYERS) begin layer<=layer+1; state<=5; end
        else state<=7;
      end
      7: if(ready[1]) state<=8;
      8: if(finished[1]) begin
        component<=0; vocabulary<=0; logit_sum<=0; state<=9;
      end
      9: if(issue) state<=10;
      10: if(own_complete) begin
        if (!fp_is_finite(rd)) begin
          failed<=1; sequence_valid<=0; clear_core<=1; state<=24;
        end else begin activation<=rd; state<=11; end
      end
      11: if(issue) state<=12;
      12: if(own_complete) begin
        if (rd[31:16]!=0) begin
          failed<=1; sequence_valid<=0; clear_core<=1; state<=24;
        end else begin raw_f16<=rd[15:0]; state<=18; end
      end
      18: if(!fp_is_finite(tensor_value) || !fp_is_finite(logit_input)) begin
        failed<=1; sequence_valid<=0; clear_core<=1; state<=24;
      end else begin activation<=logit_input; logit_weight_reg<=tensor_value; state<=19; end
      19: if (alu_ready) state<=20;
      20: if (alu_valid) begin logit_product<=alu_result; state<=21; end
      21: if (alu_ready) state<=22;
      22: if (alu_valid) begin logit_sum<=alu_result; state<=13; end
      13: if(component+1<HIDDEN_SIZE) begin component<=component+1; state<=9; end
          else state<=15;
      15: if(logit_ready) begin
        if(vocabulary+1<VOCAB_SIZE) begin
          vocabulary<=vocabulary+1; component<=0; logit_sum<=0; state<=9;
        end else begin
          next_position<=position+1; sequence_valid<=1; state<=31;
          if(!phase) prefill_cursor<=position+1;
          active_token<=0;
        end
      end
      16: begin clear_core<=0; state<=1; end
      24: state<=25;
      25: if(scheduler_drained) begin
        active_token<=0;
        if(cancel_pending) state<=26;
        else state<=31;
      end
      26: begin cancelled_active<=0; state<=0; end
      31: begin active_token<=0; state<=0; end
      default: state<=0;
    endcase
  end
endmodule
