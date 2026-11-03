module anvil_d1_moe_router_dma #(
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=10944,
  parameter integer MOE_INTERMEDIATE_SIZE=1408, FIRST_DENSE_LAYERS=1,
  parameter integer ROUTED_EXPERTS=64, TOP_K=6, SHARED_EXPERTS=2,
  parameter integer MAX_SEQ_LEN=32768, TILE_K=128, TILE_ROWS=8,
  localparam integer NE=(ROUTED_EXPERTS>=1 && ROUTED_EXPERTS<=64) ? ROUTED_EXPERTS : 1,
  localparam integer NK=(TOP_K>=1 && TOP_K<=6) ? TOP_K : 1,
  localparam integer HW=(HIDDEN_SIZE>=8 && HIDDEN_SIZE<=2048) ? HIDDEN_SIZE : 8,
  localparam integer TK=(TILE_K>=8 && TILE_K<=128) ? TILE_K : 8,
  localparam integer TR=(TILE_ROWS>=1 && TILE_ROWS<=8) ? TILE_ROWS : 1,
  localparam integer TILE_WORDS=TK*TR
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_layer, cmd_pos,
  input wire cmd_phase,
  output wire done, error,
  output wire [63:0] expert_dma_bytes, expert_dense_equiv_bytes,
  output wire [63:0] shared_busy_cycles, prefetch_busy_cycles, overlap_cycles,
  output wire [1:0] c_req_valid,
  input wire [1:0] c_req_ready,
  output wire [1:0] c_req_write,
  output wire [7:0] c_req_kind,
  output wire [63:0] c_req_layer,
  output wire [5:0] c_req_proj,
  output wire [63:0] c_req_row, c_req_col, c_req_wdata,
  input wire [1:0] c_rsp_valid,
  output wire [1:0] c_rsp_ready,
  input wire [63:0] c_rsp_rdata,
  input wire [1:0] c_rsp_error
);
  localparam IDLE=0, SCORES=1, SCORES_WAIT=2, SCORE_READ=3, SCORE_RESPONSE=4;
  localparam EXP=5, EXP_WAIT=6, DEN_ADD=7, DEN_ADD_WAIT=8;
  localparam PROB_DIV=9, PROB_DIV_WAIT=10, PICK_BEGIN=11, PICK_SCAN=12, PICK_SAVE=13;
  localparam WEIGHT_DIV=14, WEIGHT_DIV_WAIT=15, WEIGHT_REMAINDER=16, DISTRIBUTE=17;
  localparam START_SHARED=18, EXPERT=19, EXPERT_WAIT=20;
  localparam MIX_READ=21, MIX_RESPONSE=22, MIX_ADDRESS=23, MIX_RAM=24;
  localparam MIX_MULTIPLY=25, MIX_MULTIPLY_WAIT=26, MIX_ADD=27, MIX_ADD_WAIT=28;
  localparam NEXT_EXPERT=29, WAIT_PREFETCH=30, OUTPUT_ADDRESS=31, OUTPUT_RAM=32;
  localparam OUTPUT_ROUND=33, OUTPUT_ROUND_WAIT=34, OUTPUT_WRITE=35, OUTPUT_RESPONSE=36;
  localparam COMPLETE=37, FAULTED=38, REJECT=39;
  localparam P_IDLE=0, P_READ=1, P_RESPONSE=2, P_DONE=3, P_FAULT=4;
  localparam [63:0] MOE_BASELINE=64'(ROUTED_EXPERTS+SHARED_EXPERTS)*
    (64'(3)*64'(HIDDEN_SIZE)*64'(MOE_INTERMEDIATE_SIZE)+
      64'(2)*64'(MOE_INTERMEDIATE_SIZE)+64'(HIDDEN_SIZE))*64'd4;
  localparam [63:0] DENSE_BASELINE=(64'(3)*64'(HIDDEN_SIZE)*64'(INTERMEDIATE_SIZE)+
    64'(2)*64'(INTERMEDIATE_SIZE)+64'(HIDDEN_SIZE))*64'd4;
  reg [5:0] state;
  reg [2:0] prefetch_state;
  reg armed, failed, dense, baseline_counted, routed_phase, second_shared;
  reg prefetch_failed, prefetch_owned;
  reg [31:0] layer, epoch, position, scan_index, probability_index, hidden_index;
  reg [31:0] prefetch_row, prefetch_col, prefetch_tile_index, prefetch_base;
  reg [31:0] active_tile_base, mixture_address;
  reg [2:0] selected_index, routed_index, prefetch_winner, distribution_index;
  reg [6:0] expert_id, best_id;
  reg signed [31:0] max_score, best_score, expert_output, output_value;
  reg [NE-1:0] selected;
  reg [NK-1:0] tile_complete;
  reg [63:0] denominator;
  reg [24:0] exp_result, coefficient;
  reg [31:0] selected_probability_sum, weight_sum, remaining_units;
  reg signed [127:0] mixture_product;
  reg signed [31:0] scores [0:NE-1];
  reg [24:0] exponentials [0:NE-1], probabilities [0:NE-1];
  reg [6:0] winners [0:NK-1];
  reg [24:0] winner_weights [0:NK-1];
  (* ramstyle="M20K", nomem2reg *) reg [31:0] tiles [0:NK*TILE_WORDS-1];
  (* ramstyle="M20K", nomem2reg *) reg signed [127:0] mixture [0:HW-1];
  reg signed [127:0] mixture_word;
  reg [31:0] tile_data;
  reg tile_valid;
  wire [2:0] s_req_valid, s_req_ready, s_req_write, s_rsp_valid, s_rsp_ready, s_rsp_error;
  wire [11:0] s_req_kind;
  wire [8:0] s_req_proj;
  wire [95:0] s_req_layer, s_req_row, s_req_col, s_req_wdata, s_rsp_rdata;
  wire scoring=state==SCORES || state==SCORES_WAIT;
  wire executing=state==EXPERT || state==EXPERT_WAIT;
  wire [1:0] selected_client=scoring ? 2'd0 : executing ? 2'd1 : 2'd2;
  wire tensor_ready, tensor_done, tensor_error;
  wire expert_ready, expert_done, expert_error, expert_arithmetic;
  wire expert_tile_valid, expert_tile_ready, expert_tile_rsp_ready;
  wire [31:0] expert_tile_index;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==SCORE_READ || state==MIX_READ || state==OUTPUT_WRITE);
  wire prefetch_idle, prefetch_complete, prefetch_fault;
  wire [31:0] prefetch_rdata;
  wire prefetch_issue=prefetch_idle && prefetch_state==P_READ;
  wire prefetch_transfer=c_req_valid[1] && c_req_ready[1];
  wire prefetch_response=c_rsp_valid[1] && c_rsp_ready[1];
  wire shared_active=executing && !dense && !routed_phase && expert_arithmetic;
  wire prefetch_active=rst_n && !flush && (prefetch_owned || prefetch_transfer);
  wire exp_ready, exp_valid, exp_error;
  wire [24:0] exp_value;
  wire signed [32:0] exp_argument=$signed({scores[probability_index][31],scores[probability_index]})-
    $signed({max_score[31],max_score});
  wire div_ready, div_valid, div_error;
  wire [63:0] quotient, division_remainder;
  wire mul_ready, mul_valid;
  wire signed [63:0] multiplied;
  wire add_ready, add_valid, add_error;
  wire signed [127:0] added;
  wire round_ready, round_valid;
  wire signed [31:0] rounded;
  wire child_fault=(scoring && tensor_done && tensor_error) ||
    (executing && expert_done && expert_error);
  wire accepting=cmd_valid && cmd_ready;
  wire [35:0] parameter_increment=
    ((c_req_valid[0] && c_req_ready[0] && !c_req_write[0] &&
      c_req_kind[0+:4]==15 && c_req_proj[0+:3]==5) ? 36'd4 : 36'd0)+
    ((prefetch_transfer && !c_req_write[1] &&
      c_req_kind[4+:4]==15 && c_req_proj[3+:3]==5) ? 36'd4 : 36'd0);
  wire [63:0] dma_snapshot, shared_snapshot, prefetch_snapshot, overlap_snapshot;
  wire dma_overflow, shared_overflow, prefetch_overflow, overlap_overflow;
  reg [63:0] baseline;
  integer n;
  generate if (NUM_LAYERS<1 || NUM_LAYERS>36 || FIRST_DENSE_LAYERS<0 ||
      FIRST_DENSE_LAYERS>NUM_LAYERS || ROUTED_EXPERTS<1 || ROUTED_EXPERTS>64 ||
      TOP_K<1 || TOP_K>6 || TOP_K>ROUTED_EXPERTS || SHARED_EXPERTS!=2 ||
      MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: router geometry");
  end endgenerate
  assign cmd_ready=rst_n && armed && !flush && state==IDLE;
  assign done=rst_n && !flush && (state==COMPLETE || child_fault ||
    (state==EXPERT_WAIT && dense && expert_done));
  assign error=done && (failed || child_fault || prefetch_failed);
  assign expert_dense_equiv_bytes=rst_n ? baseline : 64'd0;
  assign expert_tile_ready=rst_n && !flush && executing && routed_phase &&
    tile_complete[routed_index] && !tile_valid;
  anvil_d1_mem_mux #(.CLIENTS(3)) memory_mux (
    .rst_n(rst_n),.flush(flush),.select_client(selected_client),
    .s_req_valid(s_req_valid),.s_req_ready(s_req_ready),.s_req_write(s_req_write),
    .s_req_kind(s_req_kind),.s_req_layer(s_req_layer),.s_req_proj(s_req_proj),
    .s_req_row(s_req_row),.s_req_col(s_req_col),.s_req_wdata(s_req_wdata),
    .s_rsp_valid(s_rsp_valid),.s_rsp_ready(s_rsp_ready),
    .s_rsp_rdata(s_rsp_rdata),.s_rsp_error(s_rsp_error),
    .c_req_valid(c_req_valid[0]),.c_req_ready(c_req_ready[0]),
    .c_req_write(c_req_write[0]),.c_req_kind(c_req_kind[0+:4]),
    .c_req_layer(c_req_layer[0+:32]),.c_req_proj(c_req_proj[0+:3]),
    .c_req_row(c_req_row[0+:32]),.c_req_col(c_req_col[0+:32]),.c_req_wdata(c_req_wdata[0+:32]),
    .c_rsp_valid(c_rsp_valid[0]),.c_rsp_ready(c_rsp_ready[0]),
    .c_rsp_rdata(c_rsp_rdata[0+:32]),.c_rsp_error(c_rsp_error[0])
  );
  anvil_d1_tensor affinity_tensor (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(state==SCORES),.cmd_ready(tensor_ready),
    .cmd_layer(layer),.cmd_rows(32'(ROUTED_EXPERTS)),.cmd_cols(32'(HIDDEN_SIZE)),
    .cmd_wide(1'b0),.cmd_bias(1'b0),.cmd_head_reduction(1'b0),.cmd_rank(32'd1),
    .cmd_weight_kind(4'd15),.cmd_input_kind(4'd8),.cmd_output_kind(4'd15),
    .cmd_weight_proj(3'd4),.cmd_input_proj(3'd0),.cmd_output_proj(3'd7),
    .cmd_weight_row(32'd0),.cmd_bias_row(32'd0),.cmd_input_layer(32'd0),
    .cmd_input_row(32'd8),.cmd_input_col(32'd0),.cmd_output_layer(layer),
    .cmd_output_row(32'd8),.cmd_output_col(32'd0),.done(tensor_done),.error(tensor_error),
    .c_req_valid(s_req_valid[0]),.c_req_ready(s_req_ready[0]),.c_req_write(s_req_write[0]),
    .c_req_kind(s_req_kind[0+:4]),.c_req_layer(s_req_layer[0+:32]),
    .c_req_proj(s_req_proj[0+:3]),.c_req_row(s_req_row[0+:32]),
    .c_req_col(s_req_col[0+:32]),.c_req_wdata(s_req_wdata[0+:32]),
    .c_rsp_valid(s_rsp_valid[0]),.c_rsp_ready(s_rsp_ready[0]),
    .c_rsp_rdata(s_rsp_rdata[0+:32]),.c_rsp_error(s_rsp_error[0])
  );
  anvil_d1_expert #(
    .HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
  ) expert_tensor (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(state==EXPERT),.cmd_ready(expert_ready),
    .cmd_layer(layer),.cmd_expert(expert_id),.cmd_dense(dense),
    .cmd_prefetched(routed_phase),.done(expert_done),.error(expert_error),
    .arithmetic_busy(expert_arithmetic),
    .tile_read_valid(expert_tile_valid),.tile_read_ready(expert_tile_ready),
    .tile_read_index(expert_tile_index),.tile_rsp_valid(tile_valid),
    .tile_rsp_ready(expert_tile_rsp_ready),.tile_rsp_data(tile_data),.tile_rsp_error(1'b0),
    .c_req_valid(s_req_valid[1]),.c_req_ready(s_req_ready[1]),.c_req_write(s_req_write[1]),
    .c_req_kind(s_req_kind[4+:4]),.c_req_layer(s_req_layer[32+:32]),
    .c_req_proj(s_req_proj[3+:3]),.c_req_row(s_req_row[32+:32]),
    .c_req_col(s_req_col[32+:32]),.c_req_wdata(s_req_wdata[32+:32]),
    .c_rsp_valid(s_rsp_valid[1]),.c_rsp_ready(s_rsp_ready[1]),
    .c_rsp_rdata(s_rsp_rdata[32+:32]),.c_rsp_error(s_rsp_error[1])
  );
  anvil_d1_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==OUTPUT_WRITE),.kind(4'd15),.layer(layer),.proj(3'd7),
    .row(state==OUTPUT_WRITE ? 32'd4 : 32'd8),
    .col(state==SCORE_READ ? scan_index : state==MIX_READ ?
      32'(MOE_INTERMEDIATE_SIZE)+hidden_index : hidden_index),
    .wdata(state==OUTPUT_WRITE ? output_value : 32'd0),.rdata(rdata),
    .c_req_valid(s_req_valid[2]),.c_req_ready(s_req_ready[2]),.c_req_write(s_req_write[2]),
    .c_req_kind(s_req_kind[8+:4]),.c_req_layer(s_req_layer[64+:32]),
    .c_req_proj(s_req_proj[6+:3]),.c_req_row(s_req_row[64+:32]),
    .c_req_col(s_req_col[64+:32]),.c_req_wdata(s_req_wdata[64+:32]),
    .c_rsp_valid(s_rsp_valid[2]),.c_rsp_ready(s_rsp_ready[2]),
    .c_rsp_rdata(s_rsp_rdata[64+:32]),.c_rsp_error(s_rsp_error[2])
  );
  anvil_d1_mem_port prefetch_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(prefetch_issue),
    .idle(prefetch_idle),.complete(prefetch_complete),.fault(prefetch_fault),
    .write(1'b0),.kind(4'd15),.layer(layer),.proj(3'd5),
    .row({winners[prefetch_winner],2'd0,prefetch_row[22:0]}),.col(prefetch_col),
    .wdata(32'd0),.rdata(prefetch_rdata),
    .c_req_valid(c_req_valid[1]),.c_req_ready(c_req_ready[1]),
    .c_req_write(c_req_write[1]),.c_req_kind(c_req_kind[4+:4]),
    .c_req_layer(c_req_layer[32+:32]),.c_req_proj(c_req_proj[3+:3]),
    .c_req_row(c_req_row[32+:32]),.c_req_col(c_req_col[32+:32]),.c_req_wdata(c_req_wdata[32+:32]),
    .c_rsp_valid(c_rsp_valid[1]),.c_rsp_ready(c_rsp_ready[1]),
    .c_rsp_rdata(c_rsp_rdata[32+:32]),.c_rsp_error(c_rsp_error[1])
  );
  anvil_d1_exp exponential (
    .clk(clk),.rst_n(rst_n),.flush(flush),.in_valid(state==EXP),.in_ready(exp_ready),
    .in_x(exp_argument),.out_valid(exp_valid),.out_ready(1'b1),
    .out_error(exp_error),.out_value(exp_value)
  );
  anvil_d1_udiv #(.NUM_W(64),.DEN_W(64)) probability_divider (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==PROB_DIV || state==WEIGHT_DIV),.in_ready(div_ready),
    .numerator(state==PROB_DIV ? {15'd0,exponentials[probability_index],24'd0} :
      {15'd0,probabilities[winners[selected_index]],24'd0}),
    .denominator(state==PROB_DIV ? denominator : {32'd0,selected_probability_sum}),
    .out_valid(div_valid),.out_ready(1'b1),.out_error(div_error),
    .quotient(quotient),.remainder(division_remainder)
  );
  anvil_d1_mul32 mixture_multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MIX_MULTIPLY),.in_ready(mul_ready),
    .in_a(expert_output),.in_b($signed({7'd0,coefficient})),
    .out_valid(mul_valid),.out_ready(1'b1),.out_product(multiplied)
  );
  anvil_d1_add128 adder (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==DEN_ADD || state==MIX_ADD),.in_ready(add_ready),
    .in_a(state==DEN_ADD ? $signed({64'd0,denominator}) :
      (!routed_phase && !second_shared ? 128'sd0 : mixture_word)),
    .in_b(state==DEN_ADD ? $signed({103'd0,exp_result}) : mixture_product),
    .out_valid(add_valid),.out_ready(1'b1),.out_error(add_error),.out_sum(added)
  );
  anvil_d1_round_sat #(.SHIFT(24)) mixture_boundary (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==OUTPUT_ROUND),.in_ready(round_ready),.in_value(mixture_word),
    .out_valid(round_valid),.out_ready(1'b1),.out_value(rounded)
  );
  anvil_d1_counter64 dma_counter (
    .clk(clk),.rst_n(rst_n),.clear(accepting),.snapshot(1'b0),.increment(parameter_increment),
    .live_value(expert_dma_bytes),.snapshot_value(dma_snapshot),.overflow(dma_overflow)
  );
  anvil_d1_counter64 shared_counter (
    .clk(clk),.rst_n(rst_n),.clear(accepting),.snapshot(1'b0),
    .increment(shared_active ? 36'd1 : 36'd0),
    .live_value(shared_busy_cycles),.snapshot_value(shared_snapshot),.overflow(shared_overflow)
  );
  anvil_d1_counter64 prefetch_counter (
    .clk(clk),.rst_n(rst_n),.clear(accepting),.snapshot(1'b0),
    .increment(prefetch_active ? 36'd1 : 36'd0),
    .live_value(prefetch_busy_cycles),.snapshot_value(prefetch_snapshot),.overflow(prefetch_overflow)
  );
  anvil_d1_counter64 overlap_counter (
    .clk(clk),.rst_n(rst_n),.clear(accepting),.snapshot(1'b0),
    .increment(shared_active && prefetch_active ? 36'd1 : 36'd0),
    .live_value(overlap_cycles),.snapshot_value(overlap_snapshot),.overflow(overlap_overflow)
  );
  always @(posedge clk) begin
    mixture_word<=mixture[mixture_address];
    if (rst_n && !flush && state==MIX_ADD_WAIT && add_valid && !add_error)
      mixture[hidden_index]<=added;
    if (rst_n && !flush && prefetch_state==P_RESPONSE && prefetch_complete && !prefetch_fault)
      tiles[prefetch_base+prefetch_tile_index]<=prefetch_rdata;
    if (expert_tile_valid && expert_tile_ready)
      tile_data<=tiles[active_tile_base+expert_tile_index];
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      tile_valid<=0;
    end else if (flush || accepting) tile_valid<=0;
    else begin
      if (tile_valid && expert_tile_rsp_ready) tile_valid<=0;
      if (expert_tile_valid && expert_tile_ready) tile_valid<=1;
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      prefetch_state<=P_IDLE; prefetch_failed<=0; prefetch_owned<=0;
      prefetch_winner<=0; prefetch_row<=0; prefetch_col<=0;
      prefetch_tile_index<=0; prefetch_base<=0; tile_complete<=0;
    end else if (flush || accepting) begin
      prefetch_state<=P_IDLE; prefetch_failed<=0; prefetch_owned<=0; tile_complete<=0;
      prefetch_winner<=0; prefetch_row<=0; prefetch_col<=0;
      prefetch_tile_index<=0; prefetch_base<=0;
    end else begin
      if (prefetch_response) prefetch_owned<=0;
      else if (prefetch_transfer) prefetch_owned<=1;
      if (prefetch_fault) begin prefetch_failed<=1; prefetch_state<=P_FAULT; tile_complete<=0; end
      else case (prefetch_state)
        P_IDLE: if (state==START_SHARED) prefetch_state<=P_READ;
        P_READ: if (prefetch_issue) prefetch_state<=P_RESPONSE;
        P_RESPONSE: if (prefetch_complete) begin
          if (prefetch_col==(HIDDEN_SIZE<TILE_K ? HIDDEN_SIZE-1 : TILE_K-1)) begin
            prefetch_col<=0;
            if (prefetch_row==(MOE_INTERMEDIATE_SIZE<TILE_ROWS ? MOE_INTERMEDIATE_SIZE-1 : TILE_ROWS-1)) begin
              tile_complete[prefetch_winner]<=1;
              if (prefetch_winner==TOP_K-1) prefetch_state<=P_DONE;
              else begin
                prefetch_winner<=prefetch_winner+1'b1; prefetch_base<=prefetch_base+32'(TILE_WORDS);
                prefetch_row<=0; prefetch_tile_index<=0; prefetch_state<=P_READ;
              end
            end else begin
              prefetch_row<=prefetch_row+1'b1;
              prefetch_tile_index<=prefetch_tile_index+32'(TILE_K)-
                32'(HIDDEN_SIZE<TILE_K ? HIDDEN_SIZE-1 : TILE_K-1);
              prefetch_state<=P_READ;
            end
          end else begin
            prefetch_col<=prefetch_col+1'b1; prefetch_tile_index<=prefetch_tile_index+1'b1;
            prefetch_state<=P_READ;
          end
        end
        P_DONE: prefetch_state<=P_DONE;
        P_FAULT: prefetch_state<=P_FAULT;
        default: begin prefetch_state<=P_FAULT; prefetch_failed<=1; end
      endcase
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; dense<=0; baseline_counted<=0;
      routed_phase<=0; second_shared<=0; layer<=0; epoch<=0; position<=0;
      scan_index<=0; probability_index<=0; hidden_index<=0; active_tile_base<=0; mixture_address<=0;
      selected_index<=0; routed_index<=0; distribution_index<=0; expert_id<=0; best_id<=0;
      max_score<=0; best_score<=0; expert_output<=0; output_value<=0; selected<=0;
      denominator<=0; exp_result<=0; coefficient<=0; selected_probability_sum<=0;
      weight_sum<=0; remaining_units<=0; mixture_product<=0; baseline<=0;
      for (n=0;n<NE;n=n+1) begin scores[n]<=0; exponentials[n]<=0; probabilities[n]<=0; end
      for (n=0;n<NK;n=n+1) begin winners[n]<=0; winner_weights[n]<=0; end
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; failed<=0; end
      else if (child_fault) begin failed<=1; state<=FAULTED; end
      else if (!failed && (memory_fault || prefetch_failed ||
          (exp_valid && exp_error) || (div_valid && div_error) || (add_valid && add_error) ||
          dma_overflow || shared_overflow || prefetch_overflow || overlap_overflow)) begin
        failed<=1; state<=COMPLETE;
      end else begin
        if (!baseline_counted && parameter_increment!=0) begin
          baseline<=dense ? DENSE_BASELINE : MOE_BASELINE; baseline_counted<=1;
        end
        case (state)
          IDLE: if (accepting) begin
            layer<=cmd_layer; epoch<=cmd_epoch; position<=cmd_pos;
            dense<=cmd_layer<FIRST_DENSE_LAYERS; baseline_counted<=0; baseline<=0;
            failed<=0; selected<=0; selected_index<=0; routed_index<=0;
            routed_phase<=0; second_shared<=0; denominator<=0; selected_probability_sum<=0;
            weight_sum<=0; scan_index<=0; probability_index<=0; hidden_index<=0;
            max_score<=32'sh80000000; active_tile_base<=0;
            if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin failed<=1; state<=REJECT; end
            else if (cmd_layer<FIRST_DENSE_LAYERS) begin expert_id<=127; state<=EXPERT; end
            else state<=SCORES;
          end
          SCORES: if (tensor_ready) state<=SCORES_WAIT;
          SCORES_WAIT: if (tensor_done) state<=SCORE_READ;
          SCORE_READ: if (issue) state<=SCORE_RESPONSE;
          SCORE_RESPONSE: if (memory_complete) begin
            scores[scan_index]<=rdata;
            if ($signed(rdata)>max_score) max_score<=rdata;
            if (scan_index==ROUTED_EXPERTS-1) begin probability_index<=0; state<=EXP; end
            else begin scan_index<=scan_index+1'b1; state<=SCORE_READ; end
          end
          EXP: if (exp_ready) state<=EXP_WAIT;
          EXP_WAIT: if (exp_valid) begin
            exp_result<=exp_value; exponentials[probability_index]<=exp_value; state<=DEN_ADD;
          end
          DEN_ADD: if (add_ready) state<=DEN_ADD_WAIT;
          DEN_ADD_WAIT: if (add_valid) begin
            if (added[127:64]!=0) begin failed<=1; state<=COMPLETE; end
            else begin
              denominator<=added[63:0];
              if (probability_index==ROUTED_EXPERTS-1) begin probability_index<=0; state<=PROB_DIV; end
              else begin probability_index<=probability_index+1'b1; state<=EXP; end
            end
          end
          PROB_DIV: if (div_ready) state<=PROB_DIV_WAIT;
          PROB_DIV_WAIT: if (div_valid) begin
            if (quotient>64'd16777216) begin failed<=1; state<=COMPLETE; end
            else begin
              probabilities[probability_index]<=quotient[24:0];
              if (probability_index==ROUTED_EXPERTS-1) state<=PICK_BEGIN;
              else begin probability_index<=probability_index+1'b1; state<=PROB_DIV; end
            end
          end
          PICK_BEGIN: begin scan_index<=0; best_id<=127; best_score<=32'sh80000000; state<=PICK_SCAN; end
          PICK_SCAN: begin
            if (!selected[scan_index] &&
                (best_id==127 || scores[scan_index]>best_score)) begin
              best_id<=scan_index[6:0]; best_score<=scores[scan_index];
            end
            if (scan_index==ROUTED_EXPERTS-1) state<=PICK_SAVE;
            else scan_index<=scan_index+1'b1;
          end
          PICK_SAVE: begin
            if (best_id>=ROUTED_EXPERTS) begin failed<=1; state<=COMPLETE; end
            else begin
              selected[best_id]<=1; winners[selected_index]<=best_id;
              selected_probability_sum<=selected_probability_sum+{7'd0,probabilities[best_id]};
              if (selected_index==TOP_K-1) begin selected_index<=0; state<=WEIGHT_DIV; end
              else begin selected_index<=selected_index+1'b1; state<=PICK_BEGIN; end
            end
          end
          WEIGHT_DIV: if (div_ready) state<=WEIGHT_DIV_WAIT;
          WEIGHT_DIV_WAIT: if (div_valid) begin
            if (quotient>64'd16777216) begin failed<=1; state<=COMPLETE; end
            else begin
              winner_weights[selected_index]<=quotient[24:0]; weight_sum<=weight_sum+quotient[31:0];
              if (selected_index==TOP_K-1) state<=WEIGHT_REMAINDER;
              else begin selected_index<=selected_index+1'b1; state<=WEIGHT_DIV; end
            end
          end
          WEIGHT_REMAINDER: begin
            if (weight_sum>32'd16777216 || 32'd16777216-weight_sum>=TOP_K) begin
              failed<=1; state<=COMPLETE;
            end else begin remaining_units<=32'd16777216-weight_sum; distribution_index<=0; state<=DISTRIBUTE; end
          end
          DISTRIBUTE: begin
            if (remaining_units!=0) begin
              winner_weights[distribution_index]<=winner_weights[distribution_index]+1'b1;
              remaining_units<=remaining_units-1'b1;
              distribution_index<=distribution_index+1'b1;
            end else state<=START_SHARED;
          end
          START_SHARED: begin
            expert_id<=7'(ROUTED_EXPERTS); coefficient<=25'd16777216; state<=EXPERT;
          end
          EXPERT: if (expert_ready) state<=EXPERT_WAIT;
          EXPERT_WAIT: if (expert_done) begin
            if (dense) state<=IDLE;
            else begin hidden_index<=0; state<=MIX_READ; end
          end
          MIX_READ: if (issue) state<=MIX_RESPONSE;
          MIX_RESPONSE: if (memory_complete) begin expert_output<=rdata; state<=MIX_ADDRESS; end
          MIX_ADDRESS: begin mixture_address<=hidden_index; state<=MIX_RAM; end
          MIX_RAM: state<=MIX_MULTIPLY;
          MIX_MULTIPLY: if (mul_ready) state<=MIX_MULTIPLY_WAIT;
          MIX_MULTIPLY_WAIT: if (mul_valid) begin
            mixture_product<={{64{multiplied[63]}},multiplied}; state<=MIX_ADD;
          end
          MIX_ADD: if (add_ready) state<=MIX_ADD_WAIT;
          MIX_ADD_WAIT: if (add_valid) begin
            if (hidden_index==HIDDEN_SIZE-1) state<=NEXT_EXPERT;
            else begin hidden_index<=hidden_index+1'b1; state<=MIX_READ; end
          end
          NEXT_EXPERT: begin
            if (!routed_phase && !second_shared) begin
              second_shared<=1; expert_id<=7'(ROUTED_EXPERTS+1); state<=EXPERT;
            end else if (!routed_phase) state<=WAIT_PREFETCH;
            else if (routed_index==TOP_K-1) begin hidden_index<=0; state<=OUTPUT_ADDRESS; end
            else begin
              routed_index<=routed_index+1'b1; active_tile_base<=active_tile_base+32'(TILE_WORDS);
              expert_id<=winners[routed_index+1'b1]; coefficient<=winner_weights[routed_index+1'b1];
              state<=EXPERT;
            end
          end
          WAIT_PREFETCH: if (prefetch_state==P_DONE) begin
            routed_phase<=1; routed_index<=0; active_tile_base<=0;
            expert_id<=winners[0]; coefficient<=winner_weights[0]; state<=EXPERT;
          end
          OUTPUT_ADDRESS: begin mixture_address<=hidden_index; state<=OUTPUT_RAM; end
          OUTPUT_RAM: state<=OUTPUT_ROUND;
          OUTPUT_ROUND: if (round_ready) state<=OUTPUT_ROUND_WAIT;
          OUTPUT_ROUND_WAIT: if (round_valid) begin output_value<=rounded; state<=OUTPUT_WRITE; end
          OUTPUT_WRITE: if (issue) state<=OUTPUT_RESPONSE;
          OUTPUT_RESPONSE: if (memory_complete) begin
            if (hidden_index==HIDDEN_SIZE-1) state<=COMPLETE;
            else begin hidden_index<=hidden_index+1'b1; state<=OUTPUT_ADDRESS; end
          end
          REJECT: state<=COMPLETE;
          COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
          FAULTED: state<=FAULTED;
          default: begin failed<=1; state<=COMPLETE; end
        endcase
      end
    end
  end
endmodule
