module anvil_q3_gqa_attention #(
  parameter PROFILE=3, NUM_LAYERS=36, HIDDEN_SIZE=2048, NUM_Q_HEADS=16,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768,
  parameter CACHE_MODE=0, INT4_ASYM=0, CACHE_BLOCK=1
) (
  input wire clk, rst_n, flush, cmd_valid,
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
  localparam RATIO=NUM_KV_HEADS>0 ? NUM_Q_HEADS/NUM_KV_HEADS : 1;
  localparam IDLE=0, ROOT=1, ROOT_WAIT=2, COMMIT=3, COMMIT_WAIT=4;
  localparam Q_READ=5, Q_RESPONSE=6, KEY=7, KEY_WAIT=8, KEY_MUL=9, KEY_MUL_WAIT=10;
  localparam DOT_ADD=11, DOT_WAIT=12, SCORE_DIVIDE=13, SCORE_WAIT=14, SCORE=15;
  localparam DIFFERENCE=16, DIFFERENCE_WAIT=17, EXP=18, EXP_WAIT=19;
  localparam DEN_ADD=20, DEN_WAIT=21, VALUE=22, VALUE_WAIT=23;
  localparam VALUE_MUL=24, VALUE_MUL_WAIT=25, WEIGHT_ADD=26, WEIGHT_WAIT=27;
  localparam CONTEXT_DIVIDE=28, CONTEXT_WAIT=29, ROUND=30, WRITE=31;
  localparam WRITE_RESPONSE=32, COMPLETE=33, FAULTED=34;
  reg [5:0] state;
  reg failed, phase, context_pass;
  reg [31:0] layer, position, head, head_base, kv_head, head_in_group;
  reg [31:0] time_index, dimension, component, exponential, context_result;
  reg signed [31:0] q, key, value;
  reg [63:0] scale_denominator, exponential_sum;
  reg signed [127:0] term, dot, max_score, current_score, difference, weighted, divided_context;
  wire unit_flush=flush || failed;
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==Q_READ || state==WRITE);
  wire cache_ready, cache_done, cache_error;
  wire signed [31:0] cache_read;
  wire multiply_ready, multiply_done, multiply_error;
  wire signed [64:0] product;
  wire dot_ready, dot_valid, dot_error;
  wire signed [127:0] dot_sum;
  wire den_ready, den_valid, den_error;
  wire signed [127:0] denominator_sum;
  wire weight_ready, weight_valid, weight_error;
  wire signed [127:0] weighted_sum;
  wire subtract_ready, subtract_valid, subtract_error;
  wire signed [127:0] subtracted;
  wire divide_ready, divide_done, divide_error;
  wire signed [127:0] quotient;
  wire root_ready, root_done, root_error;
  wire [63:0] root;
  wire [64:0] root_remainder;
  wire exp_ready, exp_done, exp_error;
  wire [31:0] exp_value;
  wire signed [63:0] exp_argument=difference< -128'sd1048576 ?
    -64'sd1048577 : $signed(difference[63:0]);

  generate if ((PROFILE!=1 && PROFILE!=2 && PROFILE!=3) ||
      NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || NUM_Q_HEADS<=0 || NUM_KV_HEADS<=0 ||
      HEAD_DIM<=0 || HEAD_DIM%2!=0 || MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>32768 ||
      128'(HIDDEN_SIZE)!=128'(NUM_Q_HEADS)*128'(HEAD_DIM) ||
      NUM_Q_HEADS%(NUM_KV_HEADS>0 ? NUM_KV_HEADS : 1)!=0 ||
      (PROFILE==3 && 128'(NUM_Q_HEADS)!=8*128'(NUM_KV_HEADS)) ||
      128'(HIDDEN_SIZE)>128'hffffffff ||
      128'(HEAD_DIM)*128'd4611686018427387904>=(128'd1<<95)) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: attention geometry");
  end endgenerate
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  anvil_q3_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
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
  anvil_q3_kv_cache #(
    .PROFILE(PROFILE),.NUM_LAYERS(NUM_LAYERS),.NUM_KV_HEADS(NUM_KV_HEADS),
    .HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_MODE(CACHE_MODE),
    .INT4_ASYM(INT4_ASYM),.CACHE_BLOCK(CACHE_BLOCK)
  ) kv_cache (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .cmd_valid(state==COMMIT || state==KEY || state==VALUE),.cmd_ready(cache_ready),
    .cmd_op(state==COMMIT ? 2'd0 : state==KEY ? 2'd1 : 2'd2),
    .cmd_layer(layer),.cmd_pos(state==COMMIT ? position : time_index),
    .cmd_head(kv_head),.cmd_dim(state==VALUE ? component : dimension),
    .cmd_phase(phase),.done(cache_done),.error(cache_error),.read_data(cache_read),
    .mem_req_valid(c_req_valid[1]),.mem_req_ready(c_req_ready[1]),
    .mem_req_write(c_req_write[1]),.mem_req_kind(c_req_kind[4+:4]),
    .mem_req_layer(c_req_layer[32+:32]),.mem_req_proj(c_req_proj[3+:3]),
    .mem_req_row(c_req_row[32+:32]),.mem_req_col(c_req_col[32+:32]),.mem_req_wdata(c_req_wdata[32+:32]),
    .mem_rsp_valid(c_rsp_valid[1]),.mem_rsp_ready(c_rsp_ready[1]),
    .mem_rsp_rdata(c_rsp_rdata[32+:32]),.mem_rsp_error(c_rsp_error[1])
  );
  anvil_q3_multiplier #(.A_W(32),.B_W(33)) multiplier (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .start(state==KEY_MUL || state==VALUE_MUL),
    .a(state==KEY_MUL ? q : value),
    .b(state==KEY_MUL ? $signed({key[31],key}) : $signed({1'b0,exponential})),
    .ready(multiply_ready),.done(multiply_done),.error(multiply_error),.product(product)
  );
  anvil_q3_accumulator dot_accumulator (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .in_valid(state==DOT_ADD),.in_ready(dot_ready),.in_first(dimension==0),.in_value(term),
    .out_valid(dot_valid),.out_ready(1'b1),.out_error(dot_error),.out_sum(dot_sum)
  );
  anvil_q3_accumulator denominator_accumulator (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .in_valid(state==DEN_ADD),.in_ready(den_ready),.in_first(time_index==0),
    .in_value({96'd0,exponential}),.out_valid(den_valid),.out_ready(1'b1),
    .out_error(den_error),.out_sum(denominator_sum)
  );
  anvil_q3_accumulator weighted_accumulator (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .in_valid(state==WEIGHT_ADD),.in_ready(weight_ready),.in_first(time_index==0),.in_value(term),
    .out_valid(weight_valid),.out_ready(1'b1),.out_error(weight_error),.out_sum(weighted_sum)
  );
  anvil_q3_add128 #(.SUBTRACT(1)) score_difference (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.in_valid(state==DIFFERENCE),
    .in_ready(subtract_ready),.in_a(current_score),.in_b(max_score),
    .out_valid(subtract_valid),.out_ready(1'b1),.out_error(subtract_error),.out_sum(subtracted)
  );
  anvil_q3_signed_divider divider (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .start(state==SCORE_DIVIDE || state==CONTEXT_DIVIDE),
    .numerator(state==SCORE_DIVIDE ? dot : weighted),
    .denominator(state==SCORE_DIVIDE ? scale_denominator : exponential_sum),
    .ready(divide_ready),.done(divide_done),.error(divide_error),.quotient(quotient)
  );
  anvil_q3_isqrt dimension_root (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.start(state==ROOT),
    .radicand(128'(HEAD_DIM)<<32),.ready(root_ready),.done(root_done),.error(root_error),
    .root(root),.remainder(root_remainder)
  );
  anvil_q3_exp exponential_unit (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.start(state==EXP),
    .x(exp_argument),.ready(exp_ready),.done(exp_done),.error(exp_error),.value(exp_value)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; phase<=0; context_pass<=0;
      layer<=0; position<=0; head<=0; head_base<=0; kv_head<=0; head_in_group<=0;
      time_index<=0; dimension<=0; component<=0; exponential<=0; context_result<=0;
      q<=0; key<=0; value<=0; scale_denominator<=0; exponential_sum<=0;
      term<=0; dot<=0; max_score<=0; current_score<=0; difference<=0; weighted<=0; divided_context<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (!failed && (fault || (cache_done && cache_error) ||
        (multiply_done && multiply_error) || (dot_valid && dot_error) ||
        (den_valid && den_error) || (weight_valid && weight_error) ||
        (subtract_valid && subtract_error) || (divide_done && divide_error) ||
        (root_done && root_error) || (exp_done && exp_error))) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; layer<=cmd_layer; position<=cmd_pos; phase<=PROFILE!=1 && cmd_phase;
        head<=0; head_base<=0; kv_head<=0; head_in_group<=0; time_index<=0;
        dimension<=0; component<=0; context_pass<=0;
        max_score<=128'sh80000000000000000000000000000000;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin failed<=1; state<=COMPLETE; end
        else state<=ROOT;
      end
      ROOT: if (root_ready) state<=ROOT_WAIT;
      ROOT_WAIT: if (root_done) begin
        if (root==0) begin failed<=1; state<=COMPLETE; end
        else begin scale_denominator<=root; state<=COMMIT; end
      end
      COMMIT: if (cache_ready) state<=COMMIT_WAIT;
      COMMIT_WAIT: if (cache_done) state<=Q_READ;
      Q_READ: if (issue) state<=Q_RESPONSE;
      Q_RESPONSE: if (complete) begin q<=rdata; state<=KEY; end
      KEY: if (cache_ready) state<=KEY_WAIT;
      KEY_WAIT: if (cache_done) begin key<=cache_read; state<=KEY_MUL; end
      KEY_MUL: if (multiply_ready) state<=KEY_MUL_WAIT;
      KEY_MUL_WAIT: if (multiply_done) begin term<={{63{product[64]}},product}; state<=DOT_ADD; end
      DOT_ADD: if (dot_ready) state<=DOT_WAIT;
      DOT_WAIT: if (dot_valid) begin
        dot<=dot_sum;
        if (dimension+1<HEAD_DIM) begin dimension<=dimension+1'b1; state<=Q_READ; end
        else state<=SCORE_DIVIDE;
      end
      SCORE_DIVIDE: if (divide_ready) state<=SCORE_WAIT;
      SCORE_WAIT: if (divide_done) begin current_score<=quotient; state<=SCORE; end
      SCORE: if (!context_pass) begin
        if (current_score>max_score) max_score<=current_score;
        dimension<=0;
        if (time_index<position) begin time_index<=time_index+1'b1; state<=Q_READ; end
        else begin context_pass<=1; time_index<=0; state<=Q_READ; end
      end else state<=DIFFERENCE;
      DIFFERENCE: if (subtract_ready) state<=DIFFERENCE_WAIT;
      DIFFERENCE_WAIT: if (subtract_valid) begin
        if (subtracted>0) begin failed<=1; state<=COMPLETE; end
        else begin difference<=subtracted; state<=EXP; end
      end
      EXP: if (exp_ready) state<=EXP_WAIT;
      EXP_WAIT: if (exp_done) begin exponential<=exp_value; state<=DEN_ADD; end
      DEN_ADD: if (den_ready) state<=DEN_WAIT;
      DEN_WAIT: if (den_valid) begin
        if (|denominator_sum[127:64]) begin failed<=1; state<=COMPLETE; end
        else begin exponential_sum<=denominator_sum[63:0]; state<=VALUE; end
      end
      VALUE: if (cache_ready) state<=VALUE_WAIT;
      VALUE_WAIT: if (cache_done) begin value<=cache_read; state<=VALUE_MUL; end
      VALUE_MUL: if (multiply_ready) state<=VALUE_MUL_WAIT;
      VALUE_MUL_WAIT: if (multiply_done) begin term<={{63{product[64]}},product}; state<=WEIGHT_ADD; end
      WEIGHT_ADD: if (weight_ready) state<=WEIGHT_WAIT;
      WEIGHT_WAIT: if (weight_valid) begin
        weighted<=weighted_sum;
        if (time_index<position) begin time_index<=time_index+1'b1; dimension<=0; state<=Q_READ; end
        else if (exponential_sum==0) begin failed<=1; state<=COMPLETE; end
        else state<=CONTEXT_DIVIDE;
      end
      CONTEXT_DIVIDE: if (divide_ready) state<=CONTEXT_WAIT;
      CONTEXT_WAIT: if (divide_done) begin divided_context<=quotient; state<=ROUND; end
      ROUND: begin context_result<=anvil_q3_pkg::round_shift_sat32(divided_context,0); state<=WRITE; end
      WRITE: if (issue) state<=WRITE_RESPONSE;
      WRITE_RESPONSE: if (complete) begin
        time_index<=0; dimension<=0;
        if (component+1<HEAD_DIM) begin component<=component+1'b1; state<=Q_READ; end
        else if (head+1<NUM_Q_HEADS) begin
          head<=head+1'b1; head_base<=head_base+HEAD_DIM; component<=0; context_pass<=0;
          max_score<=128'sh80000000000000000000000000000000;
          if (head_in_group+1<RATIO) head_in_group<=head_in_group+1'b1;
          else begin head_in_group<=0; kv_head<=kv_head+1'b1; end
          state<=Q_READ;
        end else state<=COMPLETE;
      end
      COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
      FAULTED: state<=FAULTED;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
