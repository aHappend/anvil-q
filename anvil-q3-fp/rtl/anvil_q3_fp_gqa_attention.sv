module anvil_q3_fp_gqa_attention #(
  parameter PROFILE=3, NUM_LAYERS=36, HIDDEN_SIZE=2048, NUM_Q_HEADS=16,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768,
  parameter CACHE_MODE=0, MODE1_FP8=0, INT4_ASYM=0, CACHE_BLOCK=1
) (
  input wire clk, rst_n, flush, cmd_valid, cmd_fp16,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos,
  input wire cmd_phase,
  output wire done, error,
  output wire [1:0] c_req_valid,
  input wire [1:0] c_req_ready,
  output wire [1:0] c_req_write,
  output wire [7:0] c_req_kind,
  output wire [63:0] c_req_layer,
  output wire [5:0] c_req_proj,
  output wire [63:0] c_req_row, c_req_col, c_req_wdata,
  input wire [1:0] c_rsp_valid, c_rsp_error,
  output wire [1:0] c_rsp_ready,
  input wire [63:0] c_rsp_rdata
);
  localparam IDLE=0, ROOT=1, ROOT_WAIT=2, COMMIT=3, COMMIT_WAIT=4;
  localparam Q_READ=5, Q_RESPONSE=6, KEY=7, KEY_WAIT=8, KEY_MUL=9, KEY_MUL_WAIT=10;
  localparam DOT_ADD=11, DOT_WAIT=12, SCORE_DIVIDE=13, SCORE_WAIT=14, SCORE=15;
  localparam DIFFERENCE=16, DIFFERENCE_WAIT=17, EXP=18, EXP_WAIT=19;
  localparam DEN_ADD=20, DEN_WAIT=21, VALUE=22, VALUE_WAIT=23;
  localparam VALUE_MUL=24, VALUE_MUL_WAIT=25, WEIGHT_ADD=26, WEIGHT_WAIT=27;
  localparam CONTEXT_DIVIDE=28, CONTEXT_WAIT=29, WRITE=30;
  localparam WRITE_RESPONSE=31, COMPLETE=32, FAULTED=33;
  localparam [31:0] DIMENSION_FP=anvil_q3_fp_pkg::uint32_to_fp32(32'(HEAD_DIM));
  reg [5:0] state;
  reg failed, phase, context_pass, fp16;
  reg [31:0] layer, position, head, head_base, time_index, dimension, component;
  reg [31:0] q, key, value, scale_denominator, exponential, exponential_sum, context_result;
  reg [31:0] term, dot, max_score, current_score, difference, weighted;
  wire unit_flush=flush || failed;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire [31:0] widened_response=anvil_q3_fp_pkg::widen16(rdata[15:0],fp16);
  wire issue=port_idle && (state==Q_READ || state==WRITE);
  wire cache_ready, cache_done, cache_error;
  wire [31:0] cache_read;
  wire [31:0] widened_cache=anvil_q3_fp_pkg::widen16(cache_read[15:0],fp16);
  wire multiply_ready, multiply_valid, add_ready, add_valid;
  wire divide_ready, divide_done, divide_error, root_ready, root_done, root_error;
  wire exp_ready, exp_done, exp_error;
  wire [31:0] product, added, quotient, root, exp_value;
  wire [20:0] narrowed_context=anvil_q3_fp_pkg::narrow16(quotient,fp16);
  wire malformed=memory_complete && state==Q_RESPONSE && rdata[31:16]!=0;
  wire current_nan=anvil_q3_fp_pkg::is_nan32(current_score);
  wire maximum_nan=anvil_q3_fp_pkg::is_nan32(max_score);
  wire score_greater=current_score[31]!=max_score[31] ?
    (!current_score[31] && (|current_score[30:0] || |max_score[30:0])) :
    (current_score[31] ? current_score[30:0]<max_score[30:0] :
      current_score[30:0]>max_score[30:0]);
  wire [31:0] add_a=state==DOT_ADD ? (dimension==0 ? 32'd0 : dot) :
    state==DIFFERENCE ? current_score :
    state==DEN_ADD ? (time_index==0 ? 32'd0 : exponential_sum) :
    (time_index==0 ? 32'd0 : weighted);
  wire [31:0] add_b=state==DIFFERENCE ? {~max_score[31],max_score[30:0]} :
    state==DEN_ADD ? exponential : term;
  generate if (PROFILE!=3 || NUM_LAYERS<=0 || HIDDEN_SIZE<=0 ||
      NUM_Q_HEADS<=0 || NUM_KV_HEADS<=0 || HEAD_DIM<=0 || HEAD_DIM%2!=0 ||
      MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768 ||
      128'(HIDDEN_SIZE)!=128'(NUM_Q_HEADS)*128'(HEAD_DIM) ||
      128'(NUM_Q_HEADS)!=8*128'(NUM_KV_HEADS) ||
      128'(NUM_LAYERS)>128'hffffffff || 128'(HIDDEN_SIZE)>128'hffffffff ||
      128'(HEAD_DIM)*2>128'hffffffff) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_FP PARAMETER ERROR: attention geometry");
  end endgenerate
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  anvil_q3_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==WRITE),.kind(4'd8),.layer(32'd0),.proj(3'd0),
    .row(state==WRITE ? 32'd5 : 32'd2),
    .col(head_base+(state==WRITE ? component : dimension)),
    .wdata(state==WRITE ? context_result : 32'd0),.rdata(rdata),
    .mem_req_valid(c_req_valid[0]),.mem_req_ready(c_req_ready[0]),
    .mem_req_write(c_req_write[0]),.mem_req_kind(c_req_kind[0+:4]),
    .mem_req_layer(c_req_layer[0+:32]),.mem_req_proj(c_req_proj[0+:3]),
    .mem_req_row(c_req_row[0+:32]),.mem_req_col(c_req_col[0+:32]),.mem_req_wdata(c_req_wdata[0+:32]),
    .mem_rsp_valid(c_rsp_valid[0]),.mem_rsp_ready(c_rsp_ready[0]),
    .mem_rsp_rdata(c_rsp_rdata[0+:32]),.mem_rsp_error(c_rsp_error[0])
  );
  anvil_q3_fp_kv_cache #(
    .PROFILE(PROFILE),.NUM_LAYERS(NUM_LAYERS),.NUM_KV_HEADS(NUM_KV_HEADS),
    .HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_MODE(CACHE_MODE),
    .MODE1_FP8(MODE1_FP8),.INT4_ASYM(INT4_ASYM),.CACHE_BLOCK(CACHE_BLOCK)
  ) kv_cache (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.cmd_fp16(fp16),
    .cmd_valid(state==COMMIT || state==KEY || state==VALUE),.cmd_ready(cache_ready),
    .cmd_op(state==COMMIT ? 2'd0 : state==KEY ? 2'd1 : 2'd2),
    .cmd_layer(layer),.cmd_pos(state==COMMIT ? position : time_index),
    .cmd_head(head>>3),.cmd_dim(state==VALUE ? component : dimension),
    .cmd_phase(phase),.done(cache_done),.error(cache_error),.read_data(cache_read),
    .mem_req_valid(c_req_valid[1]),.mem_req_ready(c_req_ready[1]),
    .mem_req_write(c_req_write[1]),.mem_req_kind(c_req_kind[4+:4]),
    .mem_req_layer(c_req_layer[32+:32]),.mem_req_proj(c_req_proj[3+:3]),
    .mem_req_row(c_req_row[32+:32]),.mem_req_col(c_req_col[32+:32]),.mem_req_wdata(c_req_wdata[32+:32]),
    .mem_rsp_valid(c_rsp_valid[1]),.mem_rsp_ready(c_rsp_ready[1]),
    .mem_rsp_rdata(c_rsp_rdata[32+:32]),.mem_rsp_error(c_rsp_error[1])
  );
  anvil_q3_fp_mul multiplier (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .in_valid(state==KEY_MUL || state==VALUE_MUL),.in_ready(multiply_ready),
    .in_a(state==KEY_MUL ? q : value),.in_b(state==KEY_MUL ? key : exponential),
    .out_valid(multiply_valid),.out_ready(1'b1),.out_data(product),.out_flags()
  );
  anvil_q3_fp_add adder (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .in_valid(state==DOT_ADD || state==DIFFERENCE || state==DEN_ADD || state==WEIGHT_ADD),
    .in_ready(add_ready),.in_a(add_a),.in_b(add_b),
    .out_valid(add_valid),.out_ready(1'b1),.out_data(added),.out_flags()
  );
  anvil_q3_fp_divider divider (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .start(state==SCORE_DIVIDE || state==CONTEXT_DIVIDE),
    .numerator(state==SCORE_DIVIDE ? dot : weighted),
    .denominator(state==SCORE_DIVIDE ? scale_denominator : exponential_sum),
    .ready(divide_ready),.done(divide_done),.error(divide_error),.quotient(quotient),.flags()
  );
  anvil_q3_fp_sqrt dimension_root (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.start(state==ROOT),
    .radicand(DIMENSION_FP),.ready(root_ready),.done(root_done),.error(root_error),
    .value(root),.flags()
  );
  anvil_q3_fp_exp exponential_unit (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.start(state==EXP),
    .x(difference),.ready(exp_ready),.done(exp_done),.error(exp_error),.value(exp_value)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; phase<=0; context_pass<=0; fp16<=0;
      layer<=0; position<=0; head<=0; head_base<=0; time_index<=0; dimension<=0; component<=0;
      q<=0; key<=0; value<=0; scale_denominator<=0; exponential<=0;
      exponential_sum<=0; context_result<=0; term<=0; dot<=0; max_score<=0;
      current_score<=0; difference<=0; weighted<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (!failed && (memory_fault || malformed || (cache_done && cache_error) ||
        (divide_done && divide_error) || (root_done && root_error) ||
        (exp_done && exp_error))) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; layer<=cmd_layer; position<=cmd_pos; phase<=cmd_phase; fp16<=cmd_fp16;
        head<=0; head_base<=0; time_index<=0; dimension<=0; component<=0; context_pass<=0;
        max_score<=32'hff800000;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin failed<=1; state<=COMPLETE; end
        else state<=ROOT;
      end
      ROOT: if (root_ready) state<=ROOT_WAIT;
      ROOT_WAIT: if (root_done) begin scale_denominator<=root; state<=COMMIT; end
      COMMIT: if (cache_ready) state<=COMMIT_WAIT;
      COMMIT_WAIT: if (cache_done) state<=Q_READ;
      Q_READ: if (issue) state<=Q_RESPONSE;
      Q_RESPONSE: if (memory_complete) begin q<=widened_response; state<=KEY; end
      KEY: if (cache_ready) state<=KEY_WAIT;
      KEY_WAIT: if (cache_done) begin key<=widened_cache; state<=KEY_MUL; end
      KEY_MUL: if (multiply_ready) state<=KEY_MUL_WAIT;
      KEY_MUL_WAIT: if (multiply_valid) begin term<=product; state<=DOT_ADD; end
      DOT_ADD: if (add_ready) state<=DOT_WAIT;
      DOT_WAIT: if (add_valid) begin
        dot<=added;
        if (dimension+1<HEAD_DIM) begin dimension<=dimension+1'b1; state<=Q_READ; end
        else state<=SCORE_DIVIDE;
      end
      SCORE_DIVIDE: if (divide_ready) state<=SCORE_WAIT;
      SCORE_WAIT: if (divide_done) begin current_score<=quotient; state<=SCORE; end
      SCORE: if (!context_pass) begin
        if (current_nan) max_score<=anvil_q3_fp_pkg::CANONICAL_NAN;
        else if (!maximum_nan && score_greater) max_score<=current_score;
        dimension<=0;
        if (time_index<position) begin time_index<=time_index+1'b1; state<=Q_READ; end
        else begin context_pass<=1; time_index<=0; state<=Q_READ; end
      end else state<=DIFFERENCE;
      DIFFERENCE: if (add_ready) state<=DIFFERENCE_WAIT;
      DIFFERENCE_WAIT: if (add_valid) begin
        if (anvil_q3_fp_pkg::is_nan32(added)) begin
          exponential<=anvil_q3_fp_pkg::CANONICAL_NAN; state<=DEN_ADD;
        end else begin difference<=added; state<=EXP; end
      end
      EXP: if (exp_ready) state<=EXP_WAIT;
      EXP_WAIT: if (exp_done) begin exponential<=exp_value; state<=DEN_ADD; end
      DEN_ADD: if (add_ready) state<=DEN_WAIT;
      DEN_WAIT: if (add_valid) begin exponential_sum<=added; state<=VALUE; end
      VALUE: if (cache_ready) state<=VALUE_WAIT;
      VALUE_WAIT: if (cache_done) begin value<=widened_cache; state<=VALUE_MUL; end
      VALUE_MUL: if (multiply_ready) state<=VALUE_MUL_WAIT;
      VALUE_MUL_WAIT: if (multiply_valid) begin term<=product; state<=WEIGHT_ADD; end
      WEIGHT_ADD: if (add_ready) state<=WEIGHT_WAIT;
      WEIGHT_WAIT: if (add_valid) begin
        weighted<=added;
        if (time_index<position) begin time_index<=time_index+1'b1; dimension<=0; state<=Q_READ; end
        else state<=CONTEXT_DIVIDE;
      end
      CONTEXT_DIVIDE: if (divide_ready) state<=CONTEXT_WAIT;
      CONTEXT_WAIT: if (divide_done) begin
        context_result<={16'd0,narrowed_context[15:0]}; state<=WRITE;
      end
      WRITE: if (issue) state<=WRITE_RESPONSE;
      WRITE_RESPONSE: if (memory_complete) begin
        time_index<=0; dimension<=0;
        if (component+1<HEAD_DIM) begin component<=component+1'b1; state<=Q_READ; end
        else if (head+1<NUM_Q_HEADS) begin
          head<=head+1'b1; head_base<=head_base+HEAD_DIM; component<=0; context_pass<=0;
          max_score<=32'hff800000; state<=Q_READ;
        end else state<=COMPLETE;
      end
      COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
      FAULTED: state<=FAULTED;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
