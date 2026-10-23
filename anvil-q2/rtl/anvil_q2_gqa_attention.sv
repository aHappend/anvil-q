module anvil_q2_gqa_attention #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, NUM_Q_HEADS=12,
  NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768, CACHE_MODE=0, CACHE_BLOCK=1, EXPLICIT_PHASE=0
)(
  input wire clk, rst_n, cmd_valid, output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, output wire done, error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error,
  input wire cmd_phase
);
  localparam RATIO = NUM_KV_HEADS>0 && NUM_Q_HEADS>=NUM_KV_HEADS ?
                      NUM_Q_HEADS/NUM_KV_HEADS : 1;
  localparam KV_SIZE = NUM_KV_HEADS*HEAD_DIM;
  reg [4:0] state;
  reg failed, context_pass, phase;
  reg [31:0] layer, position, index, head, time_index, dim, component;
  reg [31:0] kv_head, head_in_group;
  reg signed [31:0] attention_result;
  reg divide_negative;
  reg signed [31:0] q;
  reg signed [95:0] dot, max_score, current_score, weighted;
  reg [63:0] denominator;
  reg [31:0] exponential;
  wire signed [31:0] read_key, read_value;
  wire signed [63:0] dot_product;
  wire signed [64:0] weighted_product;
  wire signed [96:0] score_difference;
  wire signed [63:0] exp_argument;
  wire exp_ready, exp_done;
  wire [31:0] exp_result;
  wire [63:0] sqrt_dim;
  wire [127:0] dim_scaled;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  wire [1:0] reqv, reqr, reqw, rspv, rspr, rspe;
  wire [7:0] reqk;
  wire [5:0] reqp;
  wire [63:0] reql, reqrow, reqcol, reqwd, rsprd;
  wire cache_ready, cache_done, cache_error;
  wire signed [31:0] cache_read;
  wire cache_selected=state==1 || state==2 || state==8 || state==9 ||
                      state==13 || state==14;
  wire cache_command=rst_n && (state==1 || state==8 || state==13);
  wire divide_ready, divide_done, divide_error;
  wire [128:0] divide_quotient;
  reg [128:0] div_mag_reg;
  wire signed [127:0] divide_value=state==23 ?
    $signed({{32{dot[95]}},dot}) : $signed({{32{weighted[95]}},weighted});
  wire [63:0] divide_denominator=state==10 ? sqrt_dim : denominator;
  wire [128:0] divide_magnitude=divide_value<0 ?
    -$signed({divide_value[127],divide_value}) : {1'b0,divide_value};
  wire signed [127:0] divided_value=divide_negative ?
    -$signed(divide_quotient[127:0]) : $signed(divide_quotient[127:0]);
  anvil_q2_exp exp_unit(
    .clk(clk),.rst_n(rst_n),.start(rst_n && state==21),
    .x(exp_argument),.ready(exp_ready),.done(exp_done),.result(exp_result));
  anvil_q2_divider divider(
    .clk(clk),.rst_n(rst_n),.start(rst_n && (state==10 || state==19)),
    .numerator(div_mag_reg+({65'd0,divide_denominator} >> 1)),
    .denominator(divide_denominator),.ready(divide_ready),
    .done(divide_done),.error(divide_error),.quotient(divide_quotient));
  anvil_q2_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,HIDDEN_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,1,4,1,MAX_SEQ_LEN) parameters_ok();
  assign read_key=(cache_done && state==9) ? cache_read : 32'sd0;
  assign read_value=(cache_done && state==14) ? cache_read : 32'sd0;
  assign dot_product=$signed({{32{q[31]}},q})*
                     $signed({{32{read_key[31]}},read_key});
  assign dim_scaled=128'(HEAD_DIM)<<32;
  assign sqrt_dim=anvil_q2_pkg::isqrt128(dim_scaled);
  assign weighted_product=$signed({{33{read_value[31]}},read_value})*
                          $signed({33'd0,exponential});
  assign score_difference=$signed({current_score[95],current_score})-
                          $signed({max_score[95],max_score});
  assign exp_argument=score_difference < -97'sd1048576 ? -64'sd1048577 :
                      (score_difference > 0 ? 64'sd0 : $signed(score_difference[63:0]));
  assign cmd_ready=rst_n && state==0;
  assign done=rst_n && state==31;
  assign error=done && failed;
  anvil_q2_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(wr),.kind(kind),.layer(ml),
    .proj(3'd0),.row(row),.col(col),.wdata(wd),
    .idle(idle),.complete(complete),.rdata(rd),.fault(fault),
    .mem_req_valid(reqv[0]),.mem_req_ready(reqr[0]),
    .mem_req_write(reqw[0]),.mem_req_kind(reqk[0+:4]),
    .mem_req_layer(reql[0+:32]),.mem_req_proj(reqp[0+:3]),
    .mem_req_row(reqrow[0+:32]),.mem_req_col(reqcol[0+:32]),.mem_req_wdata(reqwd[0+:32]),
    .mem_rsp_valid(rspv[0]),.mem_rsp_ready(rspr[0]),
    .mem_rsp_rdata(rsprd[0+:32]),.mem_rsp_error(rspe[0]));
  anvil_q2_kv_cache #(
    NUM_LAYERS,NUM_KV_HEADS,HEAD_DIM,MAX_SEQ_LEN,CACHE_MODE,CACHE_BLOCK) kv_cache(
    .clk(clk),.rst_n(rst_n),.invalidate(1'b0),
    .cmd_valid(cache_command),.cmd_ready(cache_ready),
    .cmd_op(state==1 ? 2'd0 : (state==8 ? 2'd1 : 2'd2)),
    .cmd_layer(layer),.cmd_pos(state==1 || state==2 ? position : time_index),
    .cmd_head(kv_head),.cmd_dim(state==13 || state==14 ? component : dim),
    .cmd_phase(phase),.done(cache_done),.error(cache_error),.read_data(cache_read),
    .mem_req_valid(reqv[1]),.mem_req_ready(reqr[1]),
    .mem_req_write(reqw[1]),.mem_req_kind(reqk[4+:4]),
    .mem_req_layer(reql[32+:32]),.mem_req_proj(reqp[3+:3]),
    .mem_req_row(reqrow[32+:32]),.mem_req_col(reqcol[32+:32]),.mem_req_wdata(reqwd[32+:32]),
    .mem_rsp_valid(rspv[1]),.mem_rsp_ready(rspr[1]),
    .mem_rsp_rdata(rsprd[32+:32]),.mem_rsp_error(rspe[1]));
  anvil_q2_bus_mux #(2) bus(
    rst_n,{31'd0,cache_selected},reqv,reqr,reqw,reqk,reql,reqp,reqrow,reqcol,reqwd,
    rspv,rspr,rsprd,rspe,mem_req_valid,mem_req_ready,mem_req_write,mem_req_kind,
    mem_req_layer,mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata,
    mem_rsp_valid,mem_rsp_ready,mem_rsp_rdata,mem_rsp_error);
  always @* begin
    issue=0; wr=0; kind=0; row=0; col=0; wd=0; ml=0;
    if(rst_n && idle) case(state)
      6: begin issue=1; kind=8; row=2; col=head*HEAD_DIM+dim; end
      16: begin
        issue=1; wr=1; kind=8; row=5; col=head*HEAD_DIM+component;
        wd=attention_result;
      end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=0; failed<=0; context_pass<=0; phase<=0;
      layer<=0; position<=0; index<=0; head<=0; time_index<=0; dim<=0;
      component<=0; q<=0; dot<=0; max_score<=0; div_mag_reg<=0;
      kv_head<=0; head_in_group<=0; attention_result<=0; divide_negative<=0;
      current_score<=0; weighted<=0; denominator<=0; exponential<=0;
    end else if(fault || (cache_done && cache_error) || (divide_done && divide_error))
      begin failed<=1; state<=31; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; layer<=cmd_layer; position<=cmd_pos; index<=0;
        phase<=EXPLICIT_PHASE ? cmd_phase : 1'b0;
        head<=0; time_index<=0; dim<=0; component<=0; context_pass<=0;
        kv_head<=0; head_in_group<=0;
        dot<=0; max_score<={1'b1,95'd0}; weighted<=0; denominator<=0;
        if(cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || sqrt_dim==0)
          begin failed<=1; state<=30; end
        else state<=1;
      end
      1: if(cache_ready) state<=2;
      2: if(cache_done) state<=6;
      6: if(issue) state<=7;
      7: if(complete) begin q<=rd; state<=8; end
      8: if(cache_ready) state<=9;
      9: if(cache_done) begin
        dot<=dot+{{32{dot_product[63]}},dot_product};
        if(dim+1<HEAD_DIM) begin dim<=dim+1; state<=6; end
        else state<=23;
      end
      23: begin
        div_mag_reg<=divide_magnitude;
        divide_negative<=divide_value<0;
        state<=10;
      end
      10: if(divide_ready) begin state<=18; end
      18: if(divide_done) begin current_score<=divided_value[95:0]; state<=11; end
      11: if(!context_pass) begin
        if(current_score>max_score) max_score<=current_score;
        if(time_index<position) begin time_index<=time_index+1; dim<=0; dot<=0; state<=6; end
        else begin context_pass<=1; time_index<=0; dim<=0; dot<=0; state<=6; end
      end else state<=21;
      21: if(exp_ready) state<=22;
      22: if(exp_done) begin exponential<=exp_result; state<=12; end
      12: begin denominator<=denominator+exponential; state<=13; end
      13: if(cache_ready) state<=14;
      14: if(cache_done) begin weighted<=weighted+{{31{weighted_product[64]}},weighted_product}; state<=15; end
      15: if(time_index<position) begin
        time_index<=time_index+1; dim<=0; dot<=0; state<=6;
      end else if(denominator==0) begin failed<=1; state<=31; end
      else state<=24;
      24: begin
        div_mag_reg<=divide_magnitude;
        divide_negative<=divide_value<0;
        state<=19;
      end
      19: if(divide_ready) begin state<=20; end
      20: if(divide_done) begin
        attention_result<=anvil_q2_pkg::sat32(divided_value); state<=16;
      end
      16: if(issue) state<=17;
      17: if(complete) begin
        time_index<=0; dim<=0; dot<=0; weighted<=0; denominator<=0;
        if(component+1<HEAD_DIM) begin component<=component+1; state<=6; end
        else if(head+1<NUM_Q_HEADS) begin
          head<=head+1; component<=0; context_pass<=0;
          if(head_in_group==RATIO-1) begin head_in_group<=0; kv_head<=kv_head+1; end
          else head_in_group<=head_in_group+1;
          max_score<={1'b1,95'd0}; state<=6;
        end else state<=31;
      end
      30: state<=31;
      31: state<=0;
      default: state<=0;
    endcase
  end
endmodule
