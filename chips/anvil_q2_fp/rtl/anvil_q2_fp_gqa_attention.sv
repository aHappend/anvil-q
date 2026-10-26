module anvil_q2_fp_gqa_attention #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, NUM_Q_HEADS=12,
  NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768,
  CACHE_MODE=0, CACHE_BLOCK=16, EXPLICIT_PHASE=0, FP_FORMAT=0,
  SS=(MAX_SEQ_LEN>0 && MAX_SEQ_LEN<=16777215 &&
      128'(NUM_LAYERS)*MAX_SEQ_LEN*NUM_KV_HEADS*HEAD_DIM<=128'd4294967295) ?
      MAX_SEQ_LEN : 1
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
  import anvil_q2_fp_pkg::*;
  localparam RATIO=NUM_KV_HEADS>0 && NUM_Q_HEADS>=NUM_KV_HEADS ?
    NUM_Q_HEADS/NUM_KV_HEADS : 1;
  localparam IDLE=0, ROOT=1, WAIT_ROOT=2, COMMIT=3, WAIT_COMMIT=4,
    QUERY=5, WAIT_QUERY=6, CONVERT_QUERY=7, KEY=8, WAIT_KEY=9,
    DOT_PRODUCT=10, WAIT_DOT_PRODUCT=11, DOT_SUM=12, WAIT_DOT_SUM=13,
    SCALE_SCORE=14, WAIT_SCORE=15, STORE_SCORE=16, LOAD_SCORE=17,
    DIFFERENCE=18, WAIT_DIFFERENCE=19, EXP=20, WAIT_EXP=21,
    DENOM_SUM=22, WAIT_DENOM_SUM=23, LOAD_WEIGHT=24,
    VALUE=25, WAIT_VALUE=26, WEIGHT_PRODUCT=27, WAIT_WEIGHT_PRODUCT=28,
    WEIGHT_SUM=29, WAIT_WEIGHT_SUM=30, DIVIDE=31, WAIT_DIVIDE=32,
    WRITE=33, WAIT_WRITE=34, FINISH=35, BAD_COMMAND=36;
  reg [5:0] state;
  reg failed, phase;
  reg [31:0] layer, position, head, head_base, kv_head, head_in_group;
  reg [31:0] time_index, dim, component;
  reg [31:0] query32, q, cache_value, dot, partial, sqrt_dim;
  reg [31:0] score, max_score, denominator, weighted, exponential, result;
  (* nomem2reg *) reg [31:0] scores [0:SS-1];
  wire [15:0] query16=narrow16(query32,FP_FORMAT);
  wire [31:0] converted_query=expand16(query16,FP_FORMAT);
  wire [1:0] reqv, reqr, reqw, rspv, rspr, rspe;
  wire [7:0] reqk;
  wire [5:0] reqp;
  wire [63:0] reql, reqrow, reqcol, reqwd, rsprd;
  wire idle, complete, fault;
  wire [31:0] rd;
  wire issue=rst_n && idle && (state==QUERY || state==WRITE);
  wire cache_selected=state==COMMIT || state==WAIT_COMMIT ||
    state==KEY || state==WAIT_KEY || state==VALUE || state==WAIT_VALUE;
  wire cache_command=rst_n && (state==COMMIT || state==KEY || state==VALUE);
  wire cache_ready, cache_done, cache_error;
  wire [31:0] cache_read;
  reg alu_valid;
  reg [2:0] alu_op;
  reg [31:0] alu_a, alu_b;
  wire alu_ready, alu_out_valid, alu_error;
  wire [31:0] alu_result;
  wire exp_ready, exp_valid, exp_error;
  wire [31:0] exp_result;
  assign cmd_ready=rst_n && state==IDLE;
  assign done=rst_n && state==FINISH;
  assign error=done && failed;
  anvil_q2_fp_parameters #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(HIDDEN_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .GROUP_SIZE(1),.VOCAB_SIZE(1),.MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_MODE(CACHE_MODE),
    .CACHE_BLOCK(CACHE_BLOCK),.FP_FORMAT(FP_FORMAT)) parameters_ok();
  anvil_q2_fp_scalar arithmetic(
    .clk(clk),.rst_n(rst_n),.in_valid(alu_valid),.in_ready(alu_ready),
    .in_op(alu_op),.in_a(alu_a),.in_b(alu_b),.out_valid(alu_out_valid),
    .out_ready(1'b1),.out_data(alu_result),.out_error(alu_error));
  anvil_q2_fp_exp exp_unit(
    .clk(clk),.rst_n(rst_n),.in_valid(rst_n && state==EXP),.in_ready(exp_ready),
    .in_x(partial),.out_valid(exp_valid),.out_ready(1'b1),
    .out_data(exp_result),.out_error(exp_error));
  anvil_q2_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(state==WRITE),.kind(4'd8),
    .layer(32'd0),.proj(3'd0),.row(state==WRITE ? 32'd5 : 32'd2),
    .col(head_base+(state==WRITE ? component : dim)),.wdata(state==WRITE ? result : 0),
    .idle(idle),.complete(complete),.rdata(rd),.fault(fault),
    .mem_req_valid(reqv[0]),.mem_req_ready(reqr[0]),
    .mem_req_write(reqw[0]),.mem_req_kind(reqk[0+:4]),
    .mem_req_layer(reql[0+:32]),.mem_req_proj(reqp[0+:3]),
    .mem_req_row(reqrow[0+:32]),.mem_req_col(reqcol[0+:32]),.mem_req_wdata(reqwd[0+:32]),
    .mem_rsp_valid(rspv[0]),.mem_rsp_ready(rspr[0]),
    .mem_rsp_rdata(rsprd[0+:32]),.mem_rsp_error(rspe[0]));
  anvil_q2_fp_kv_cache #(
    .NUM_LAYERS(NUM_LAYERS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_MODE(CACHE_MODE),.CACHE_BLOCK(CACHE_BLOCK),
    .FP_FORMAT(FP_FORMAT)) kv_cache(
    .clk(clk),.rst_n(rst_n),.invalidate(1'b0),
    .cmd_valid(cache_command),.cmd_ready(cache_ready),
    .cmd_op(state==COMMIT ? 2'd0 : (state==KEY ? 2'd1 : 2'd2)),
    .cmd_layer(layer),.cmd_pos(state==COMMIT || state==WAIT_COMMIT ? position : time_index),
    .cmd_head(kv_head),.cmd_dim(state==VALUE || state==WAIT_VALUE ? component : dim),
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
    alu_valid=0; alu_op=0; alu_a=0; alu_b=0;
    if (rst_n) case (state)
      ROOT: begin alu_valid=1; alu_op=3; alu_a=fp_from_int(HEAD_DIM); end
      DOT_PRODUCT: begin alu_valid=1; alu_op=1; alu_a=q; alu_b=cache_value; end
      DOT_SUM: begin alu_valid=1; alu_a=dot; alu_b=partial; end
      SCALE_SCORE: begin alu_valid=1; alu_op=2; alu_a=dot; alu_b=sqrt_dim; end
      DIFFERENCE: begin alu_valid=1; alu_a=score; alu_b={~max_score[31],max_score[30:0]}; end
      DENOM_SUM: begin alu_valid=1; alu_a=denominator; alu_b=exponential; end
      WEIGHT_PRODUCT: begin alu_valid=1; alu_op=1; alu_a=exponential; alu_b=cache_value; end
      WEIGHT_SUM: begin alu_valid=1; alu_a=weighted; alu_b=partial; end
      DIVIDE: begin alu_valid=1; alu_op=2; alu_a=weighted; alu_b=denominator; end
      default: begin end
    endcase
  end
  // Unreset RAM is read only after this command has written every causal entry.
  always @(posedge clk) begin
    if (rst_n && state==STORE_SCORE) scores[time_index]<=score;
    if (rst_n && state==WAIT_EXP && exp_valid && !exp_error)
      scores[time_index]<=exp_result;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; phase<=0; layer<=0; position<=0;
      head<=0; head_base<=0; kv_head<=0; head_in_group<=0;
      time_index<=0; dim<=0; component<=0; query32<=0; q<=0; cache_value<=0;
      dot<=0; partial<=0; sqrt_dim<=0; score<=0; max_score<=0;
      denominator<=0; weighted<=0; exponential<=0; result<=0;
    end else if (fault || (cache_done && cache_error) ||
                 (alu_out_valid && alu_error) || (exp_valid && exp_error)) begin
      failed<=1; state<=FINISH;
    end else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; layer<=cmd_layer; position<=cmd_pos;
        phase<=EXPLICIT_PHASE ? cmd_phase : 1'b0;
        head<=0; head_base<=0; kv_head<=0; head_in_group<=0;
        time_index<=0; dim<=0; component<=0; dot<=0;
        weighted<=0; denominator<=0; max_score<=32'hff800000;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin
          failed<=1; state<=BAD_COMMAND;
        end else state<=ROOT;
      end
      ROOT: if (alu_ready) state<=WAIT_ROOT;
      WAIT_ROOT: if (alu_out_valid) begin sqrt_dim<=alu_result; state<=COMMIT; end
      COMMIT: if (cache_ready) state<=WAIT_COMMIT;
      WAIT_COMMIT: if (cache_done) state<=QUERY;
      QUERY: if (issue) state<=WAIT_QUERY;
      WAIT_QUERY: if (complete) begin query32<=rd; state<=CONVERT_QUERY; end
      CONVERT_QUERY: begin
        if (!fp_is_finite(query32) || !fp_is_finite(converted_query)) begin
          failed<=1; state<=FINISH;
        end else begin q<=converted_query; state<=KEY; end
      end
      KEY: if (cache_ready) state<=WAIT_KEY;
      WAIT_KEY: if (cache_done) begin cache_value<=cache_read; state<=DOT_PRODUCT; end
      DOT_PRODUCT: if (alu_ready) state<=WAIT_DOT_PRODUCT;
      WAIT_DOT_PRODUCT: if (alu_out_valid) begin partial<=alu_result; state<=DOT_SUM; end
      DOT_SUM: if (alu_ready) state<=WAIT_DOT_SUM;
      WAIT_DOT_SUM: if (alu_out_valid) begin
        dot<=alu_result;
        if (dim+1<HEAD_DIM) begin dim<=dim+1; state<=QUERY; end
        else state<=SCALE_SCORE;
      end
      SCALE_SCORE: if (alu_ready) state<=WAIT_SCORE;
      WAIT_SCORE: if (alu_out_valid) begin score<=alu_result; state<=STORE_SCORE; end
      STORE_SCORE: begin
        if (fp_less(max_score,score)) max_score<=score;
        if (time_index<position) begin
          time_index<=time_index+1; dim<=0; dot<=0; state<=QUERY;
        end else begin time_index<=0; denominator<=0; state<=LOAD_SCORE; end
      end
      LOAD_SCORE: begin score<=scores[time_index]; state<=DIFFERENCE; end
      DIFFERENCE: if (alu_ready) state<=WAIT_DIFFERENCE;
      WAIT_DIFFERENCE: if (alu_out_valid) begin partial<=alu_result; state<=EXP; end
      EXP: if (exp_ready) state<=WAIT_EXP;
      WAIT_EXP: if (exp_valid) begin exponential<=exp_result; state<=DENOM_SUM; end
      DENOM_SUM: if (alu_ready) state<=WAIT_DENOM_SUM;
      WAIT_DENOM_SUM: if (alu_out_valid) begin
        denominator<=alu_result;
        if (time_index<position) begin time_index<=time_index+1; state<=LOAD_SCORE; end
        else if (fp_is_zero(alu_result)) begin failed<=1; state<=FINISH; end
        else begin time_index<=0; component<=0; weighted<=0; state<=LOAD_WEIGHT; end
      end
      LOAD_WEIGHT: begin exponential<=scores[time_index]; state<=VALUE; end
      VALUE: if (cache_ready) state<=WAIT_VALUE;
      WAIT_VALUE: if (cache_done) begin cache_value<=cache_read; state<=WEIGHT_PRODUCT; end
      WEIGHT_PRODUCT: if (alu_ready) state<=WAIT_WEIGHT_PRODUCT;
      WAIT_WEIGHT_PRODUCT: if (alu_out_valid) begin partial<=alu_result; state<=WEIGHT_SUM; end
      WEIGHT_SUM: if (alu_ready) state<=WAIT_WEIGHT_SUM;
      WAIT_WEIGHT_SUM: if (alu_out_valid) begin
        weighted<=alu_result;
        if (time_index<position) begin time_index<=time_index+1; state<=LOAD_WEIGHT; end
        else state<=DIVIDE;
      end
      DIVIDE: if (alu_ready) state<=WAIT_DIVIDE;
      WAIT_DIVIDE: if (alu_out_valid) begin result<=alu_result; state<=WRITE; end
      WRITE: if (issue) state<=WAIT_WRITE;
      WAIT_WRITE: if (complete) begin
        time_index<=0; weighted<=0;
        if (component+1<HEAD_DIM) begin component<=component+1; state<=LOAD_WEIGHT; end
        else if (head+1<NUM_Q_HEADS) begin
          head<=head+1; head_base<=head_base+HEAD_DIM; component<=0;
          if (head_in_group==RATIO-1) begin head_in_group<=0; kv_head<=kv_head+1; end
          else head_in_group<=head_in_group+1;
          dim<=0; dot<=0; max_score<=32'hff800000; denominator<=0; state<=QUERY;
        end else state<=FINISH;
      end
      BAD_COMMAND: state<=FINISH;
      FINISH: state<=IDLE;
      default: begin failed<=1; state<=FINISH; end
    endcase
  end
endmodule
