module anvil_d1_mla_engine #(
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048, NUM_Q_HEADS=16,
  parameter integer KV_LORA_RANK=512, QK_NOPE_HEAD_DIM=128,
  parameter integer QK_ROPE_HEAD_DIM=64, V_HEAD_DIM=128, MAX_SEQ_LEN=32768,
  localparam integer NH=(NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16) ? NUM_Q_HEADS : 1,
  localparam integer RK=(KV_LORA_RANK>=1 && KV_LORA_RANK<=512) ? KV_LORA_RANK : 1,
  localparam integer RP=(QK_ROPE_HEAD_DIM>=2 && QK_ROPE_HEAD_DIM<=64) ? QK_ROPE_HEAD_DIM : 2,
  localparam integer CW=RK+RP,
  localparam integer QW=NH*CW,
  localparam integer NW=NH*RK
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_layer, cmd_pos,
  input wire cmd_phase,
  output wire done, error,
  output wire [63:0] kv_read_bytes, kv_write_bytes, kv_dense_equiv_bytes,
  output wire c_req_valid,
  input wire c_req_ready,
  output wire c_req_write,
  output wire [3:0] c_req_kind,
  output wire [31:0] c_req_layer,
  output wire [2:0] c_req_proj,
  output wire [31:0] c_req_row, c_req_col, c_req_wdata,
  input wire c_rsp_valid,
  output wire c_rsp_ready,
  input wire [31:0] c_rsp_rdata,
  input wire c_rsp_error
);
  function automatic [31:0] constant_sqrt(input [63:0] x);
    reg [63:0] remainder_value, trial;
    reg [31:0] root_value;
    integer n;
    begin
      remainder_value=0; root_value=0;
      for (n=31;n>=0;n=n-1) begin
        remainder_value=(remainder_value<<2) | ((x>>(n*2)) & 64'd3);
        trial=({32'd0,root_value}<<2) | 64'd1;
        if (remainder_value>=trial) begin
          remainder_value=remainder_value-trial; root_value=(root_value<<1) | 32'd1;
        end else root_value=root_value<<1;
      end
      constant_sqrt=root_value;
    end
  endfunction
  localparam [31:0] SCORE_SCALE=constant_sqrt(64'(QK_NOPE_HEAD_DIM+QK_ROPE_HEAD_DIM)<<32);
  localparam [35:0] DENSE_BYTES=36'(NUM_Q_HEADS*(QK_NOPE_HEAD_DIM+QK_ROPE_HEAD_DIM+V_HEAD_DIM)*4);
  localparam IDLE=0, ABSORB=1, ABSORB_WAIT=2, PROJECT=3, PROJECT_WAIT=4;
  localparam ROTATE=5, ROTATE_WAIT=6, QUERY_READ=7, QUERY_RESPONSE=8;
  localparam CACHE_READ=9, CACHE_RESPONSE=10, SCORE_ADDRESS=11, SCORE_READ=12;
  localparam SCORE_MULTIPLY=13, SCORE_MULTIPLY_WAIT=14, SCORE_ACC=15, SCORE_ACC_WAIT=16;
  localparam SCORE_DIVIDE=17, SCORE_DIVIDE_WAIT=18, SCORE_BOUNDARY=19;
  localparam EXPONENTIAL=20, EXPONENTIAL_WAIT=21, Z_ADD=22, Z_ADD_WAIT=23;
  localparam N_ADDRESS=24, N_READ=25, N_MULTIPLY=26, N_MULTIPLY_WAIT=27;
  localparam N_ADD=28, N_ADD_WAIT=29, NEXT_HEAD=30, NEXT_TOKEN=31;
  localparam CONTEXT_ADDRESS=32, CONTEXT_READ=33, CONTEXT_DIVIDE=34;
  localparam CONTEXT_DIVIDE_WAIT=35, CONTEXT_ROUND_ADD=36, CONTEXT_ROUND_WAIT=37;
  localparam CONTEXT_BOUNDARY=38, CONTEXT_BOUNDARY_WAIT=39;
  localparam CONTEXT_WRITE=40, CONTEXT_WRITE_RESPONSE=41, OUTPUT_PROJECT=42;
  localparam OUTPUT_WAIT=43, COMPLETE=44, FAULTED=45, REJECT=46;
  localparam CONTEXT_PREPARE=47;
  reg [5:0] state;
  reg armed, failed, second_pass, query_rope, context_negative;
  reg [2:0] projection;
  reg [31:0] epoch, layer, position, token_index, component;
  reg [3:0] head;
  reg [31:0] rank_head_base, rope_head_base, query_head_base;
  reg [31:0] load_head_base, load_component, load_col;
  reg [3:0] load_head;
  reg signed [127:0] product, score_sum, context_integer;
  reg signed [31:0] score, context_result;
  reg [24:0] exponential;
  reg [127:0] context_magnitude, context_quotient;
  reg [63:0] context_remainder;
  reg [31:0] query_address, cache_address, numerator_address;
  (* ramstyle="M20K", nomem2reg *) reg signed [31:0] queries [0:QW-1];
  (* ramstyle="M20K", nomem2reg *) reg signed [31:0] cached_token [0:CW-1];
  (* ramstyle="M20K", nomem2reg *) reg signed [127:0] numerators [0:NW-1];
  reg signed [31:0] query_word, cache_word;
  reg signed [127:0] numerator_word;
  reg signed [31:0] maxima [0:NH-1];
  reg [63:0] denominators [0:NH-1];
  wire [3:0] s_req_valid, s_req_ready, s_req_write, s_rsp_valid, s_rsp_ready, s_rsp_error;
  wire [15:0] s_req_kind;
  wire [11:0] s_req_proj;
  wire [127:0] s_req_layer, s_req_row, s_req_col, s_req_wdata, s_rsp_rdata;
  wire absorbing=state==ABSORB || state==ABSORB_WAIT;
  wire projecting=state==PROJECT || state==PROJECT_WAIT ||
    state==OUTPUT_PROJECT || state==OUTPUT_WAIT;
  wire rotating=state==ROTATE || state==ROTATE_WAIT;
  wire [1:0] selected_client=absorbing ? 2'd0 : projecting ? 2'd1 : rotating ? 2'd2 : 2'd3;
  wire abs_ready, abs_done, abs_error, tensor_ready, tensor_done, tensor_error;
  wire rope_ready, rope_done, rope_error;
  wire [63:0] absorption_reads, absorption_writes;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==QUERY_READ || state==CACHE_READ || state==CONTEXT_WRITE);
  wire [31:0] raw_project_row=projection==0 ? 32'h00000000 :
    projection==1 ? 32'h10000000 :
    projection==2 ? {head,28'd0} : {4'd3,head,24'd0};
  wire output_projection=state==OUTPUT_PROJECT || state==OUTPUT_WAIT;
  wire wide_projection=projection==2 || output_projection;
  wire [31:0] projection_rows=output_projection ? 32'(HIDDEN_SIZE) :
    projection==0 || projection==2 ? 32'(KV_LORA_RANK) : 32'(QK_ROPE_HEAD_DIM);
  wire [31:0] projection_output_col=projection==0 || projection==1 ? 32'd0 :
    projection==2 ? rank_head_base : rope_head_base;
  wire child_fault=(absorbing && abs_done && abs_error) ||
    (projecting && tensor_done && tensor_error) ||
    (rotating && rope_done && rope_error);
  wire mul_ready, mul_valid;
  wire signed [63:0] multiplied;
  wire score_acc_ready, score_acc_valid, score_acc_error;
  wire signed [127:0] accumulated_score;
  wire score_div_ready, score_div_valid, score_div_error;
  wire signed [128:0] score_quotient;
  wire [31:0] score_remainder;
  wire exp_ready, exp_valid, exp_error;
  wire [24:0] exp_value;
  wire signed [32:0] score_delta=$signed({score[31],score})-
    $signed({maxima[head][31],maxima[head]});
  wire add_ready, add_valid, add_error;
  wire signed [127:0] added;
  wire context_div_ready, context_div_valid, context_div_error;
  wire [127:0] divided_context;
  wire [63:0] divided_remainder;
  wire [127:0] negative_numerator, negative_context;
  wire unused_n_borrow, unused_c_borrow;
  wire [64:0] remainder_difference;
  wire remainder_borrow;
  wire round_up=!remainder_borrow;
  wire boundary_ready, boundary_valid;
  wire signed [31:0] boundary_value;
  wire arithmetic_fault=(score_acc_valid && score_acc_error) ||
    (score_div_valid && score_div_error) || (exp_valid && exp_error) ||
    (add_valid && add_error) || (context_div_valid && context_div_error);
  wire accepting=cmd_valid && cmd_ready;
  wire cache_transfer=c_req_valid && c_req_ready && c_req_kind==15 && c_req_proj==3;
  wire [63:0] read_snapshot, write_snapshot, dense_snapshot;
  wire read_overflow, write_overflow, dense_overflow;
  integer n;
  generate if (NUM_LAYERS<1 || NUM_LAYERS>36 || HIDDEN_SIZE<8 || HIDDEN_SIZE>2048 ||
      (HIDDEN_SIZE & 7)!=0 || NUM_Q_HEADS<1 || NUM_Q_HEADS>16 ||
      KV_LORA_RANK<1 || KV_LORA_RANK>512 || QK_NOPE_HEAD_DIM<1 || QK_NOPE_HEAD_DIM>128 ||
      QK_ROPE_HEAD_DIM<2 || QK_ROPE_HEAD_DIM>64 || (QK_ROPE_HEAD_DIM & 1)!=0 ||
      V_HEAD_DIM<1 || V_HEAD_DIM>128 || MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: MLA geometry");
  end endgenerate
  assign cmd_ready=rst_n && armed && !flush && state==IDLE;
  assign done=rst_n && !flush && (state==COMPLETE || child_fault ||
    (state==OUTPUT_WAIT && tensor_done));
  assign error=done && (failed || child_fault);
  anvil_d1_mem_mux #(.CLIENTS(4)) memory_mux (
    .rst_n(rst_n),.flush(flush),.select_client(selected_client),
    .s_req_valid(s_req_valid),.s_req_ready(s_req_ready),.s_req_write(s_req_write),
    .s_req_kind(s_req_kind),.s_req_layer(s_req_layer),.s_req_proj(s_req_proj),
    .s_req_row(s_req_row),.s_req_col(s_req_col),.s_req_wdata(s_req_wdata),
    .s_rsp_valid(s_rsp_valid),.s_rsp_ready(s_rsp_ready),
    .s_rsp_rdata(s_rsp_rdata),.s_rsp_error(s_rsp_error),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),
    .c_req_write(c_req_write),.c_req_kind(c_req_kind),.c_req_layer(c_req_layer),
    .c_req_proj(c_req_proj),.c_req_row(c_req_row),.c_req_col(c_req_col),
    .c_req_wdata(c_req_wdata),.c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
    .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error)
  );
  anvil_d1_absorption #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
    .KV_LORA_RANK(KV_LORA_RANK),.QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),.V_HEAD_DIM(V_HEAD_DIM)
  ) absorption (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(state==ABSORB),.cmd_ready(abs_ready),
    .cmd_epoch(epoch),.cmd_layer(layer),.done(abs_done),.error(abs_error),
    .raw_read_bytes(absorption_reads),.absorbed_write_bytes(absorption_writes),
    .c_req_valid(s_req_valid[0]),.c_req_ready(s_req_ready[0]),.c_req_write(s_req_write[0]),
    .c_req_kind(s_req_kind[0+:4]),.c_req_layer(s_req_layer[0+:32]),
    .c_req_proj(s_req_proj[0+:3]),.c_req_row(s_req_row[0+:32]),
    .c_req_col(s_req_col[0+:32]),.c_req_wdata(s_req_wdata[0+:32]),
    .c_rsp_valid(s_rsp_valid[0]),.c_rsp_ready(s_rsp_ready[0]),
    .c_rsp_rdata(s_rsp_rdata[0+:32]),.c_rsp_error(s_rsp_error[0])
  );
  anvil_d1_tensor tensor (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(state==PROJECT || state==OUTPUT_PROJECT),.cmd_ready(tensor_ready),
    .cmd_layer(layer),.cmd_rows(projection_rows),
    .cmd_cols(output_projection ? 32'(NUM_Q_HEADS*KV_LORA_RANK) : 32'(HIDDEN_SIZE)),
    .cmd_wide(wide_projection),.cmd_bias(1'b0),.cmd_head_reduction(output_projection),
    .cmd_rank(32'(KV_LORA_RANK)),.cmd_weight_kind(4'd15),
    .cmd_input_kind(output_projection ? 4'd15 : 4'd8),.cmd_output_kind(4'd15),
    .cmd_weight_proj(output_projection ? 3'd2 : projection==2 ? 3'd1 : 3'd0),
    .cmd_input_proj(output_projection ? 3'd7 : 3'd0),
    .cmd_output_proj(projection==0 && !output_projection ? 3'd3 : 3'd7),
    .cmd_weight_row(output_projection ? 32'd0 : raw_project_row),.cmd_bias_row(32'd0),
    .cmd_input_layer(output_projection ? layer : 32'd0),
    .cmd_input_row(output_projection ? 32'd7 : 32'd1),.cmd_input_col(32'd0),
    .cmd_output_layer(layer),
    .cmd_output_row(output_projection ? 32'd3 : projection==0 ? position :
      projection==2 ? 32'd5 : 32'd6),
    .cmd_output_col(output_projection ? 32'd0 : projection_output_col),
    .done(tensor_done),.error(tensor_error),
    .c_req_valid(s_req_valid[1]),.c_req_ready(s_req_ready[1]),.c_req_write(s_req_write[1]),
    .c_req_kind(s_req_kind[4+:4]),.c_req_layer(s_req_layer[32+:32]),
    .c_req_proj(s_req_proj[3+:3]),.c_req_row(s_req_row[32+:32]),
    .c_req_col(s_req_col[32+:32]),.c_req_wdata(s_req_wdata[32+:32]),
    .c_rsp_valid(s_rsp_valid[1]),.c_rsp_ready(s_rsp_ready[1]),
    .c_rsp_rdata(s_rsp_rdata[32+:32]),.c_rsp_error(s_rsp_error[1])
  );
  anvil_d1_rope #(.QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)) rotary (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(state==ROTATE),.cmd_ready(rope_ready),
    .cmd_layer(layer),.cmd_pos(position),.cmd_source_row(32'd6),
    .cmd_source_col(projection==1 ? 32'd0 : rope_head_base),
    .cmd_target_proj(projection==1 ? 3'd3 : 3'd7),
    .cmd_target_row(projection==1 ? position : 32'd6),
    .cmd_target_col(projection==1 ? 32'(KV_LORA_RANK) : rope_head_base),
    .done(rope_done),.error(rope_error),
    .c_req_valid(s_req_valid[2]),.c_req_ready(s_req_ready[2]),.c_req_write(s_req_write[2]),
    .c_req_kind(s_req_kind[8+:4]),.c_req_layer(s_req_layer[64+:32]),
    .c_req_proj(s_req_proj[6+:3]),.c_req_row(s_req_row[64+:32]),
    .c_req_col(s_req_col[64+:32]),.c_req_wdata(s_req_wdata[64+:32]),
    .c_rsp_valid(s_rsp_valid[2]),.c_rsp_ready(s_rsp_ready[2]),
    .c_rsp_rdata(s_rsp_rdata[64+:32]),.c_rsp_error(s_rsp_error[2])
  );
  anvil_d1_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==CONTEXT_WRITE),.kind(4'd15),.layer(layer),
    .proj(state==CACHE_READ ? 3'd3 : 3'd7),
    .row(state==CACHE_READ ? token_index : state==CONTEXT_WRITE ? 32'd7 :
      query_rope ? 32'd6 : 32'd5),
    .col(state==CACHE_READ ? load_component : state==CONTEXT_WRITE ?
      rank_head_base+component : load_col),
    .wdata(state==CONTEXT_WRITE ? context_result : 32'd0),.rdata(rdata),
    .c_req_valid(s_req_valid[3]),.c_req_ready(s_req_ready[3]),.c_req_write(s_req_write[3]),
    .c_req_kind(s_req_kind[12+:4]),.c_req_layer(s_req_layer[96+:32]),
    .c_req_proj(s_req_proj[9+:3]),.c_req_row(s_req_row[96+:32]),
    .c_req_col(s_req_col[96+:32]),.c_req_wdata(s_req_wdata[96+:32]),
    .c_rsp_valid(s_rsp_valid[3]),.c_rsp_ready(s_rsp_ready[3]),
    .c_rsp_rdata(s_rsp_rdata[96+:32]),.c_rsp_error(s_rsp_error[3])
  );
  anvil_d1_mul32 multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==SCORE_MULTIPLY || state==N_MULTIPLY),.in_ready(mul_ready),
    .in_a(state==N_MULTIPLY ? $signed({7'd0,exponential}) : query_word),.in_b(cache_word),
    .out_valid(mul_valid),.out_ready(1'b1),.out_product(multiplied)
  );
  anvil_d1_accumulator score_accumulator (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==SCORE_ACC),.in_ready(score_acc_ready),
    .in_first(component==0),.in_value(product),
    .out_valid(score_acc_valid),.out_ready(1'b1),
    .out_error(score_acc_error),.out_sum(accumulated_score)
  );
  anvil_d1_sdiv #(.NUM_W(128),.DEN_W(32)) score_divider (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==SCORE_DIVIDE),.in_ready(score_div_ready),
    .numerator(score_sum),.denominator(SCORE_SCALE),
    .out_valid(score_div_valid),.out_ready(1'b1),.out_error(score_div_error),
    .quotient(score_quotient),.remainder(score_remainder)
  );
  anvil_d1_exp exp (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==EXPONENTIAL),.in_ready(exp_ready),.in_x(score_delta),
    .out_valid(exp_valid),.out_ready(1'b1),.out_error(exp_error),.out_value(exp_value)
  );
  anvil_d1_add128 adder (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==Z_ADD || state==N_ADD || state==CONTEXT_ROUND_ADD),
    .in_ready(add_ready),
    .in_a(state==Z_ADD ? $signed({64'd0,denominators[head]}) :
      state==CONTEXT_ROUND_ADD ? $signed(context_quotient) :
      token_index==0 ? 128'sd0 : numerator_word),
    .in_b(state==Z_ADD ? $signed({103'd0,exponential}) :
      state==CONTEXT_ROUND_ADD ? $signed({127'd0,round_up}) : product),
    .out_valid(add_valid),.out_ready(1'b1),.out_error(add_error),.out_sum(added)
  );
  anvil_d1_sub_unsigned #(.WIDTH(128)) numerator_negation (
    .a(128'd0),.b(numerator_word),.difference(negative_numerator),.borrow(unused_n_borrow)
  );
  anvil_d1_sub_unsigned #(.WIDTH(65)) half_comparison (
    .a({context_remainder,1'b0}),.b({1'b0,denominators[head]}),
    .difference(remainder_difference),.borrow(remainder_borrow)
  );
  anvil_d1_sub_unsigned #(.WIDTH(128)) context_negation (
    .a(128'd0),.b(context_integer),.difference(negative_context),.borrow(unused_c_borrow)
  );
  anvil_d1_udiv #(.NUM_W(128),.DEN_W(64)) context_divider (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==CONTEXT_DIVIDE),.in_ready(context_div_ready),
    .numerator(context_magnitude),.denominator(denominators[head]),
    .out_valid(context_div_valid),.out_ready(1'b1),.out_error(context_div_error),
    .quotient(divided_context),.remainder(divided_remainder)
  );
  anvil_d1_round_sat #(.SHIFT(0)) context_boundary (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==CONTEXT_BOUNDARY),.in_ready(boundary_ready),
    .in_value(context_negative ? $signed(negative_context) : context_integer),
    .out_valid(boundary_valid),.out_ready(1'b1),.out_value(boundary_value)
  );
  anvil_d1_counter64 reads (
    .clk(clk),.rst_n(rst_n),.clear(accepting),.snapshot(1'b0),
    .increment(cache_transfer && !c_req_write ? 36'd4 : 36'd0),
    .live_value(kv_read_bytes),.snapshot_value(read_snapshot),.overflow(read_overflow)
  );
  anvil_d1_counter64 writes (
    .clk(clk),.rst_n(rst_n),.clear(accepting),.snapshot(1'b0),
    .increment(cache_transfer && c_req_write ? 36'd4 : 36'd0),
    .live_value(kv_write_bytes),.snapshot_value(write_snapshot),.overflow(write_overflow)
  );
  anvil_d1_counter64 dense_equivalent (
    .clk(clk),.rst_n(rst_n),.clear(accepting),.snapshot(1'b0),
    .increment(cache_transfer && c_req_col==0 ? DENSE_BYTES : 36'd0),
    .live_value(kv_dense_equiv_bytes),.snapshot_value(dense_snapshot),.overflow(dense_overflow)
  );
  always @(posedge clk) begin
    query_word<=queries[query_address];
    cache_word<=cached_token[cache_address];
    numerator_word<=numerators[numerator_address];
    if (rst_n && !flush && state==QUERY_RESPONSE && memory_complete && !memory_fault)
      queries[load_head_base+load_component+(query_rope ? RK : 0)]<=rdata;
    if (rst_n && !flush && state==CACHE_RESPONSE && memory_complete && !memory_fault)
      cached_token[load_component]<=rdata;
    if (rst_n && !flush && state==N_ADD_WAIT && add_valid && !add_error)
      numerators[rank_head_base+component]<=added;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; second_pass<=0; query_rope<=0; context_negative<=0;
      projection<=0; epoch<=0; layer<=0; position<=0; token_index<=0; component<=0;
      head<=0; rank_head_base<=0; rope_head_base<=0; query_head_base<=0;
      load_head_base<=0; load_component<=0; load_col<=0; load_head<=0;
      product<=0; score_sum<=0; context_integer<=0; score<=0; context_result<=0;
      exponential<=0; context_magnitude<=0; context_quotient<=0; context_remainder<=0;
      query_address<=0; cache_address<=0; numerator_address<=0;
      for (n=0;n<NH;n=n+1) begin maxima[n]<=0; denominators[n]<=0; end
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; failed<=0; end
      else if (child_fault) begin failed<=1; state<=FAULTED; end
      else if (!failed && (memory_fault || arithmetic_fault ||
          read_overflow || write_overflow || dense_overflow)) begin
        failed<=1; state<=COMPLETE;
      end else case (state)
        IDLE: if (accepting) begin
          epoch<=cmd_epoch; layer<=cmd_layer; position<=cmd_pos;
          failed<=0; second_pass<=0; projection<=0; head<=0;
          rank_head_base<=0; rope_head_base<=0; query_head_base<=0;
          token_index<=0; component<=0; load_component<=0; load_col<=0;
          query_rope<=0; load_head_base<=0; load_head<=0;
          for (n=0;n<NH;n=n+1) begin
            maxima[n]<=32'sh80000000; denominators[n]<=0;
          end
          if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin
            failed<=1; state<=REJECT;
          end else state<=ABSORB;
        end
        ABSORB: if (abs_ready) state<=ABSORB_WAIT;
        ABSORB_WAIT: if (abs_done) state<=PROJECT;
        PROJECT: if (tensor_ready) state<=PROJECT_WAIT;
        PROJECT_WAIT: if (tensor_done) begin
          if (projection==0) begin projection<=1; state<=PROJECT; end
          else if (projection==2) begin projection<=3; state<=PROJECT; end
          else state<=ROTATE;
        end
        ROTATE: if (rope_ready) state<=ROTATE_WAIT;
        ROTATE_WAIT: if (rope_done) begin
          if (projection==1) begin projection<=2; state<=PROJECT; end
          else if (head==NUM_Q_HEADS-1) begin
            head<=0; rank_head_base<=0; rope_head_base<=0; state<=QUERY_READ;
          end else begin
            head<=head+1'b1; rank_head_base<=rank_head_base+32'(KV_LORA_RANK);
            rope_head_base<=rope_head_base+32'(QK_ROPE_HEAD_DIM);
            projection<=2; state<=PROJECT;
          end
        end
        QUERY_READ: if (issue) state<=QUERY_RESPONSE;
        QUERY_RESPONSE: if (memory_complete) begin
          if (load_component==(query_rope ? RP-1 : RK-1)) begin
            load_component<=0;
            if (load_head==NUM_Q_HEADS-1) begin
              load_head<=0; load_head_base<=0; load_col<=0;
              if (!query_rope) begin query_rope<=1; state<=QUERY_READ; end
              else state<=CACHE_READ;
            end else begin
              load_head<=load_head+1'b1; load_head_base<=load_head_base+32'(CW);
              load_col<=load_col+1'b1; state<=QUERY_READ;
            end
          end else begin
            load_component<=load_component+1'b1; load_col<=load_col+1'b1; state<=QUERY_READ;
          end
        end
        CACHE_READ: if (issue) state<=CACHE_RESPONSE;
        CACHE_RESPONSE: if (memory_complete) begin
          if (load_component==CW-1) begin load_component<=0; state<=SCORE_ADDRESS; end
          else begin load_component<=load_component+1'b1; state<=CACHE_READ; end
        end
        SCORE_ADDRESS: begin
          query_address<=query_head_base+component; cache_address<=component; state<=SCORE_READ;
        end
        SCORE_READ: state<=SCORE_MULTIPLY;
        SCORE_MULTIPLY: if (mul_ready) state<=SCORE_MULTIPLY_WAIT;
        SCORE_MULTIPLY_WAIT: if (mul_valid) begin
          product<={{64{multiplied[63]}},multiplied}; state<=SCORE_ACC;
        end
        SCORE_ACC: if (score_acc_ready) state<=SCORE_ACC_WAIT;
        SCORE_ACC_WAIT: if (score_acc_valid) begin
          if (component==CW-1) begin score_sum<=accumulated_score; state<=SCORE_DIVIDE; end
          else begin component<=component+1'b1; state<=SCORE_ADDRESS; end
        end
        SCORE_DIVIDE: if (score_div_ready) state<=SCORE_DIVIDE_WAIT;
        SCORE_DIVIDE_WAIT: if (score_div_valid) begin
          if (score_quotient>129'sd2147483647) score<=32'sh7fffffff;
          else if (score_quotient< -129'sd2147483648) score<=32'sh80000000;
          else score<=score_quotient[31:0];
          state<=SCORE_BOUNDARY;
        end
        SCORE_BOUNDARY: begin
          if (second_pass) state<=EXPONENTIAL;
          else begin
            if (score>maxima[head]) maxima[head]<=score;
            state<=NEXT_HEAD;
          end
        end
        EXPONENTIAL: if (exp_ready) state<=EXPONENTIAL_WAIT;
        EXPONENTIAL_WAIT: if (exp_valid) begin exponential<=exp_value; state<=Z_ADD; end
        Z_ADD: if (add_ready) state<=Z_ADD_WAIT;
        Z_ADD_WAIT: if (add_valid) begin
          if (added[127:64]!=0) begin failed<=1; state<=COMPLETE; end
          else begin denominators[head]<=added[63:0]; component<=0; state<=N_ADDRESS; end
        end
        N_ADDRESS: begin
          cache_address<=component; numerator_address<=rank_head_base+component; state<=N_READ;
        end
        N_READ: state<=N_MULTIPLY;
        N_MULTIPLY: if (mul_ready) state<=N_MULTIPLY_WAIT;
        N_MULTIPLY_WAIT: if (mul_valid) begin
          product<={{64{multiplied[63]}},multiplied}; state<=N_ADD;
        end
        N_ADD: if (add_ready) state<=N_ADD_WAIT;
        N_ADD_WAIT: if (add_valid) begin
          if (component==RK-1) state<=NEXT_HEAD;
          else begin component<=component+1'b1; state<=N_ADDRESS; end
        end
        NEXT_HEAD: begin
          component<=0;
          if (head==NUM_Q_HEADS-1) begin
            head<=0; rank_head_base<=0; query_head_base<=0; state<=NEXT_TOKEN;
          end else begin
            head<=head+1'b1; rank_head_base<=rank_head_base+32'(RK);
            query_head_base<=query_head_base+32'(CW); state<=SCORE_ADDRESS;
          end
        end
        NEXT_TOKEN: begin
          if (token_index==position) begin
            token_index<=0;
            if (!second_pass) begin second_pass<=1; state<=CACHE_READ; end
            else state<=CONTEXT_ADDRESS;
          end else begin token_index<=token_index+1'b1; state<=CACHE_READ; end
        end
        CONTEXT_ADDRESS: begin
          numerator_address<=rank_head_base+component; state<=CONTEXT_READ;
        end
        CONTEXT_READ: state<=CONTEXT_PREPARE;
        CONTEXT_PREPARE: begin
          context_magnitude<=numerator_word[127] ? negative_numerator : $unsigned(numerator_word);
          context_negative<=numerator_word[127]; state<=CONTEXT_DIVIDE;
        end
        CONTEXT_DIVIDE: if (context_div_ready) state<=CONTEXT_DIVIDE_WAIT;
        CONTEXT_DIVIDE_WAIT: if (context_div_valid) begin
          context_quotient<=divided_context; context_remainder<=divided_remainder;
          state<=CONTEXT_ROUND_ADD;
        end
        CONTEXT_ROUND_ADD: if (add_ready) state<=CONTEXT_ROUND_WAIT;
        CONTEXT_ROUND_WAIT: if (add_valid) begin context_integer<=added; state<=CONTEXT_BOUNDARY; end
        CONTEXT_BOUNDARY: if (boundary_ready) state<=CONTEXT_BOUNDARY_WAIT;
        CONTEXT_BOUNDARY_WAIT: if (boundary_valid) begin
          context_result<=boundary_value; state<=CONTEXT_WRITE;
        end
        CONTEXT_WRITE: if (issue) state<=CONTEXT_WRITE_RESPONSE;
        CONTEXT_WRITE_RESPONSE: if (memory_complete) begin
          if (component!=RK-1) begin component<=component+1'b1; state<=CONTEXT_ADDRESS; end
          else if (head!=NUM_Q_HEADS-1) begin
            component<=0; head<=head+1'b1; rank_head_base<=rank_head_base+32'(RK);
            state<=CONTEXT_ADDRESS;
          end else state<=OUTPUT_PROJECT;
        end
        OUTPUT_PROJECT: if (tensor_ready) state<=OUTPUT_WAIT;
        OUTPUT_WAIT: if (tensor_done) state<=IDLE;
        REJECT: state<=COMPLETE;
        COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
        FAULTED: state<=FAULTED;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
