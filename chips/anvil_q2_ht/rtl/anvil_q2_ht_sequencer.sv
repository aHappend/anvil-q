module anvil_q2_ht_sequencer #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  parameter NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter CACHE_BLOCK=16, TILE_SLOTS=4,
  parameter CW=(CACHE_BLOCK>=1 && CACHE_BLOCK<=128) ? CACHE_BLOCK : 1
) (
  input wire clk, rst_n, flush, resources_drained, invalidate_weights,
  input wire weight_mode,
  input wire [1:0] cache_mode,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence, token_phase,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire done, error, busy, fault, memory_idle, projection_idle,
  output wire kv_invalidate,
  output wire desc_req_valid,
  input wire desc_req_ready,
  output wire [8:0] desc_req_index,
  input wire desc_rsp_valid,
  output wire desc_rsp_ready,
  input wire [511:0] desc_rsp_data,
  input wire desc_rsp_error,
  output wire kv_cmd_valid,
  input wire kv_cmd_ready,
  output wire kv_cmd_write, kv_cmd_value,
  output wire [31:0] kv_cmd_layer, kv_cmd_pos, kv_cmd_head, kv_cmd_block,
  output wire [CW*32-1:0] kv_cmd_data,
  input wire kv_rsp_valid,
  output wire kv_rsp_ready,
  input wire [CW*32-1:0] kv_rsp_data,
  input wire kv_rsp_error,
  output wire kv_commit_valid,
  input wire kv_commit_ready,
  output wire [31:0] kv_commit_layer, kv_commit_pos,
  output wire prefetch_valid,
  input wire prefetch_ready,
  output wire [32:0] prefetch_address,
  output wire [6:0] prefetch_beats,
  output wire [2:0] prefetch_slot,
  output wire [31:0] prefetch_generation,
  output wire alloc_valid,
  input wire alloc_ready,
  output wire [2:0] alloc_slot,
  output wire [31:0] alloc_generation,
  output wire alloc_mode,
  output wire operand_valid,
  input wire operand_ready,
  output wire [2:0] operand_slot,
  output wire [31:0] operand_generation,
  output wire [4095:0] operand_activation,
  output wire [127:0] operand_keep,
  output wire meta_valid,
  input wire meta_ready,
  output wire [2:0] meta_slot,
  output wire [31:0] meta_generation,
  output wire [3:0] meta_row,
  output wire [511:0] meta_zero,
  output wire [2047:0] meta_scale,
  output wire execute_valid,
  input wire execute_ready,
  output wire [2:0] execute_slot,
  output wire [31:0] execute_generation,
  output wire issue_valid,
  input wire issue_ready,
  output wire [2:0] issue_slot,
  output wire [31:0] issue_generation,
  output wire [3:0] issue_row,
  output wire [63:0] issue_tag,
  output wire release_valid,
  input wire release_ready,
  output wire [2:0] release_slot,
  output wire [31:0] release_generation,
  input wire array_valid, array_mode,
  output wire array_ready,
  input wire signed [127:0] array_sum,
  input wire [31:0] array_fp32,
  input wire [63:0] array_tag,
  input wire array_error,
  output wire direct_active, direct_valid,
  input wire direct_ready,
  output wire [127:0] direct_keep,
  output wire [4095:0] direct_act,
  output wire [2047:0] direct_bf16,
  output wire [63:0] direct_tag,
  output wire seq_mem_req_valid,
  input wire seq_mem_req_ready,
  output wire [32:0] seq_mem_req_addr,
  input wire seq_mem_rsp_valid,
  output wire seq_mem_rsp_ready,
  input wire [511:0] seq_mem_rsp_rdata,
  input wire seq_mem_rsp_error,
  output wire proj_mem_req_valid,
  input wire proj_mem_req_ready,
  output wire [32:0] proj_mem_req_addr,
  input wire proj_mem_rsp_valid,
  output wire proj_mem_rsp_ready,
  input wire [511:0] proj_mem_rsp_rdata,
  input wire proj_mem_rsp_error
);
  import anvil_q2_ht_int_pkg::*;
  localparam SAFE_HEAD=HEAD_DIM>=2 ? HEAD_DIM : 2;
  localparam BLOCK_SHIFT=$clog2(CW);
  localparam BLOCKS=SAFE_HEAD >> BLOCK_SHIFT;
  localparam SAFE_KV=NUM_KV_HEADS>=1 ? NUM_KV_HEADS : 1;
  localparam HEAD_RATIO=NUM_Q_HEADS/SAFE_KV;
  localparam VECTOR_WORDS=INTERMEDIATE_SIZE>HIDDEN_SIZE ?
    INTERMEDIATE_SIZE : HIDDEN_SIZE;
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=1536 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=8960 &&
    HEAD_DIM>=2 && HEAD_DIM<=128 && (HEAD_DIM & 1)==0 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 &&
    NUM_KV_HEADS>=1 && NUM_KV_HEADS<=2 &&
    HIDDEN_SIZE==NUM_Q_HEADS*HEAD_DIM && HEAD_RATIO*NUM_KV_HEADS==NUM_Q_HEADS &&
    (HIDDEN_SIZE & 7)==0 && (INTERMEDIATE_SIZE & 7)==0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7)==0 &&
    CACHE_BLOCK>=1 && CACHE_BLOCK<=128 &&
    CW==CACHE_BLOCK && (CACHE_BLOCK & (CACHE_BLOCK-1))==0 &&
    (HEAD_DIM & (CW-1))==0 && VOCAB_SIZE>=1 && VOCAB_SIZE<=151936 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768;
  localparam [3:0] VX=0, VN=1, VQ=2, VK=3, VV=4, VA=5, VO=6,
    VG=7, VU=8, VM=9;
  localparam [8:0]
    IDLE=0, FAILED=1, INVALID_DONE=2,
    VREAD_REQ=3, VREAD_RSP=4, VWRITE=5, DESC_REQ=6, DESC_RSP=7,
    COEFF_REQ=8, COEFF_RSP=9, CONV_REQ=10, CONV_RSP=11,
    MATH_REQ=12, MATH_RSP=13, EXP_REQ=14, EXP_RSP=15,
    FP_WAIT=16, KV_REQ=17, KV_RSP=18, KV_COMMIT=19,
    EMBED_DESC=32, EMBED_BASE=33, EMBED_READ=34, EMBED_CONVERT=35,
    EMBED_WRITE=36, EMBED_NEXT=37,
    NORM_START=40, NORM_SCAN=41, NORM_SQUARE=42, NORM_SUM=43,
    NORM_NEXT=44, NORM_MEAN=45, NORM_EPSILON=46, NORM_ROOT=47,
    NORM_RECIP=48, NORM_APPLY=49, NORM_X=50, NORM_GAMMA=51,
    NORM_CONVERT=52, NORM_PRODUCT=53, NORM_SCALE=54,
    NORM_ROUND=55, NORM_WRITE=56, NORM_ADVANCE=57,
    PROJ_START=64, PROJ_DESC=65, PROJ_BIAS_DESC=66, PROJ_COMMAND=67,
    PROJ_RESULT=68, PROJ_BIAS=69, PROJ_BIAS_CONVERT=70,
    PROJ_BIAS_ADD=71, PROJ_FINAL=72, PROJ_CONVERT=73,
    PROJ_WRITE=74, PROJ_NEXT=75,
    ROPE_START=80, ROPE_BASE=81, ROPE_READ_X=82, ROPE_X=83,
    ROPE_Y=84, ROPE_COS=85, ROPE_SIN=86, ROPE_XCOS=87,
    ROPE_YSIN=88, ROPE_SUB=89, ROPE_ROUND_X=90, ROPE_YCOS=91,
    ROPE_XSIN=92, ROPE_ADD=93, ROPE_ROUND_Y=94,
    ROPE_WRITE_X=95, ROPE_WRITE_Y=96, ROPE_NEXT=97,
    STORE_START=104, STORE_READ=105, STORE_WORD=106, STORE_ENCODE=107,
    STORE_INSERT=108, STORE_SEND=109, STORE_NEXT=110, STORE_COMMIT=111,
    ATTN_SCALE=120, ATTN_HEAD=121, ATTN_DOT=122, ATTN_Q=123,
    ATTN_KEY=124, ATTN_KEY_CONVERT=125, ATTN_MUL=126,
    ATTN_SUM=127, ATTN_DIM_NEXT=128, ATTN_SCORE=129,
    ATTN_SCORE_SAVE=130, ATTN_COMPARE=131, ATTN_TIME_NEXT=132,
    ATTN_EXP_READ=133, ATTN_EXP_LATCH=134, ATTN_DIFF=135,
    ATTN_EXP=136, ATTN_EXP_SAVE=137, ATTN_DENOM=138,
    ATTN_WEIGHT_START=139, ATTN_WEIGHT_READ=140, ATTN_WEIGHT_LATCH=141,
    ATTN_VALUE=142, ATTN_VALUE_CONVERT=143, ATTN_WEIGHT_MUL=144,
    ATTN_WEIGHT_ADD=145, ATTN_WEIGHT_NEXT=146, ATTN_DIVIDE=147,
    ATTN_WRITE=148, ATTN_COMPONENT_NEXT=149,
    RESIDUAL_START=160, RESIDUAL_X=161, RESIDUAL_O=162,
    RESIDUAL_ADD=163, RESIDUAL_WRITE=164, RESIDUAL_NEXT=165,
    SWIGLU_START=176, SWIGLU_GATE=177, SWIGLU_UP=178,
    SWIGLU_EXP=179, SWIGLU_SIGMOID=180, SWIGLU_SILU=181,
    SWIGLU_SILU_ROUND=182, SWIGLU_PRODUCT=183,
    SWIGLU_ROUND=184, SWIGLU_WRITE=185, SWIGLU_NEXT=186,
    HEAD_START=192, HEAD_DESC=193, HEAD_ROW=194, HEAD_BASE=195,
    HEAD_W4_READ=196, HEAD_W4_X=197, HEAD_W4_WEIGHT=198,
    HEAD_W4_CONVERT=199, HEAD_W4_MUL=200, HEAD_W4_SUM=201,
    HEAD_W4_NEXT=202, HEAD_W4_FINAL=203,
    HEAD_BF_ACT=208, HEAD_BF_ACT_WAIT=209, HEAD_BF_LOAD=210,
    HEAD_BF_WORD=211, HEAD_BF_INSERT=212, HEAD_BF_ISSUE=213,
    HEAD_BF_RESULT=214, HEAD_BF_ACCUM=215, HEAD_BF_NEXT=216,
    HEAD_BF_FINAL=217, HEAD_EMIT=220, TOKEN_FINISH=221;

  reg [8:0] state, continuation;
  reg sequence_valid, decoding, phase, completed, completed_error, faulted;
  reg invalidate_pulse, mode, row_last, rope_key, store_value, head_first;
  reg [31:0] token, position, next_position, prefill_count, frozen_prefill;
  reg [31:0] layer, index, output_row, vocabulary, head, kv_head, head_in_group;
  reg [31:0] pair_index, dimension, time_index, component, block_index, block_word;
  reg [31:0] input_col, lane_index;
  reg [1:0] norm_kind;
  reg [2:0] projection;
  reg [3:0] projection_src, projection_dst;
  reg [511:0] descriptor, projection_descriptor, bias_descriptor;
  reg [32:0] row_base;
  reg signed [31:0] x, y, cosine, sine, rotated_x;
  reg signed [127:0] accumulator, saved_product, saved_sum, max_score, score;
  reg [63:0] reciprocal, attention_scale, denominator;
  reg [31:0] exponential, floating_sum, output_data;
  reg [CW*32-1:0] block_data, returned_block;
  reg [4095:0] head_activations;
  reg [2047:0] head_weights;
  reg [127:0] head_keep;
  reg [8:0] requested_descriptor;
  reg [3:0] read_vector, write_vector;
  reg [31:0] read_index, write_index, write_data, vector_value;
  reg [32:0] coefficient_address;
  reg coefficient_word32;
  reg [31:0] coefficient_value, conversion_input, conversion_value;
  reg [3:0] conversion_op, math_op;
  reg signed [127:0] math_a, math_b, math_value, exp_argument;
  reg [31:0] exp_value, fp_a, fp_b, fp_value;
  reg [2:0] fp_count;
  reg cache_write, cache_value, cache_commit;
  reg [31:0] cache_position, cache_head, cache_block;
  reg [CW*32-1:0] cache_data;
  reg [511:0] descriptor_value;
  reg signed [127:0] score_read;
  reg [31:0] exponent_read;
  (* ramstyle = "M20K, no_rw_check" , nomem2reg *) reg signed [127:0] score_ram [0:(MAX_SEQ_LEN>0 ? MAX_SEQ_LEN : 1)-1];
  (* ramstyle = "M20K, no_rw_check" , nomem2reg *) reg [31:0] exponent_ram [0:(MAX_SEQ_LEN>0 ? MAX_SEQ_LEN : 1)-1];

  wire running=rst_n && !flush && !faulted;
  wire vf_ready, vf_valid, vf_error;
  wire [31:0] vf_data;
  wire tile_ready, tile_valid, tile_error;
  wire [4095:0] tile_data;
  wire p_act_req_valid, p_act_req_ready, p_act_rsp_ready;
  wire [31:0] p_act_col;
  wire head_tile=state==HEAD_BF_ACT || state==HEAD_BF_ACT_WAIT;
  wire reader_ready, reader_valid, reader_error, reader_idle;
  wire [31:0] reader_data;
  wire convert_ready, convert_valid, convert_error;
  wire [31:0] convert_data;
  wire math_ready, math_valid, math_error;
  wire signed [127:0] math_data;
  wire exp_ready, exp_valid, exp_error;
  wire [31:0] exp_data, fp_data;
  wire fp_error;
  wire projection_ready, projection_done, projection_fault, projection_array_ready;
  wire projection_result_valid, projection_result_last;
  wire [31:0] projection_result_row, projection_result_fp32;
  wire signed [127:0] projection_result_sum;
  wire local_annul=flush || invalidate_weights;
  wire active_head=state>=HEAD_BF_ACT && state<=HEAD_BF_FINAL;
  wire [31:0] vector_head_base=head*HEAD_DIM;
  wire [31:0] rope_head_count=rope_key ? NUM_KV_HEADS : NUM_Q_HEADS;
  wire [31:0] store_index=kv_head*HEAD_DIM+(block_index << BLOCK_SHIFT)+block_word;
  wire [31:0] selected_block_word=returned_block[
    (dimension & (CW-1))*32+:32];
  wire [31:0] selected_value_word=returned_block[
    (component & (CW-1))*32+:32];
  wire invalid_token=token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN ||
    (new_sequence && token_pos!=0) ||
    (!new_sequence && (!sequence_valid || token_pos!=next_position ||
      (decoding && !token_phase) ||
      (decoding && token_phase && token_pos<frozen_prefill) ||
      (!token_phase && token_pos!=prefill_count)));
  integer activation_lane;

  task automatic read_word(input [3:0] vector_id, input [31:0] word_index,
                            input [8:0] resume);
    begin
      read_vector<=vector_id; read_index<=word_index;
      continuation<=resume; state<=VREAD_REQ;
    end
  endtask
  task automatic write_word(input [3:0] vector_id, input [31:0] word_index,
                             input [31:0] data, input [8:0] resume);
    begin
      write_vector<=vector_id; write_index<=word_index; write_data<=data;
      continuation<=resume; state<=VWRITE;
    end
  endtask
  task automatic get_descriptor(input [8:0] entry, input [8:0] resume);
    begin requested_descriptor<=entry; continuation<=resume; state<=DESC_REQ; end
  endtask
  task automatic read_coefficient(input [32:0] address, input word32,
                                   input [8:0] resume);
    begin
      coefficient_address<=address; coefficient_word32<=word32;
      continuation<=resume; state<=COEFF_REQ;
    end
  endtask
  task automatic convert_word(input [3:0] operation, input [31:0] data,
                               input [8:0] resume);
    begin
      conversion_op<=operation; conversion_input<=data;
      continuation<=resume; state<=CONV_REQ;
    end
  endtask
  task automatic calculate(input [3:0] operation,
                            input signed [127:0] first, second,
                            input [8:0] resume);
    begin
      math_op<=operation; math_a<=first; math_b<=second;
      continuation<=resume; state<=MATH_REQ;
    end
  endtask
  task automatic exponential_of(input signed [127:0] argument, input [8:0] resume);
    begin exp_argument<=argument; continuation<=resume; state<=EXP_REQ; end
  endtask
  task automatic floating_add(input [31:0] first, second, input [8:0] resume);
    begin
      fp_a<=first; fp_b<=second; fp_count<=0;
      continuation<=resume; state<=FP_WAIT;
    end
  endtask
  task automatic cache_access(input write_access, value_select,
      input [31:0] pos, cache_head_index, cache_block_index,
      input [CW*32-1:0] data, input [8:0] resume);
    begin
      cache_write<=write_access; cache_value<=value_select;
      cache_position<=pos; cache_head<=cache_head_index; cache_block<=cache_block_index;
      cache_data<=data; cache_commit<=0; continuation<=resume; state<=KV_REQ;
    end
  endtask

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT PARAMETER ERROR: sequencer geometry");
  end endgenerate

  anvil_q2_ht_vector_store #(.WORDS(VECTOR_WORDS)) vectors (
    .clk(clk),.rst_n(rst_n),.annul(local_annul),
    .wr_valid(running && state==VWRITE),.wr_vector(write_vector),
    .wr_index(write_index),.wr_data(write_data),
    .rd_valid(running && state==VREAD_REQ),.rd_ready(vf_ready),
    .rd_vector(read_vector),.rd_index(read_index),
    .rsp_valid(vf_valid),.rsp_ready(running && state==VREAD_RSP),
    .rsp_data(vf_data),.rsp_error(vf_error),
    .tile_valid(running && (head_tile ? state==HEAD_BF_ACT : p_act_req_valid)),
    .tile_ready(tile_ready),.tile_vector(head_tile ? VN : projection_src),
    .tile_col(head_tile ? input_col : p_act_col),
    .tile_rsp_valid(tile_valid),
    .tile_rsp_ready(running && (head_tile ? state==HEAD_BF_ACT_WAIT : p_act_rsp_ready)),
    .tile_rsp_data(tile_data),.tile_rsp_error(tile_error));
  assign p_act_req_ready=!head_tile && tile_ready;
  anvil_q2_ht_scalar_reader coefficients (
    .clk(clk),.rst_n(rst_n),.invalidate(local_annul),
    .cmd_valid(running && state==COEFF_REQ),.cmd_ready(reader_ready),
    .cmd_address(coefficient_address),.cmd_word32(coefficient_word32),
    .rsp_valid(reader_valid),.rsp_ready(running && state==COEFF_RSP),
    .rsp_data(reader_data),.rsp_error(reader_error),.idle(reader_idle),
    .mem_req_valid(seq_mem_req_valid),.mem_req_ready(seq_mem_req_ready),
    .mem_req_addr(seq_mem_req_addr),.mem_rsp_valid(seq_mem_rsp_valid),
    .mem_rsp_ready(seq_mem_rsp_ready),.mem_rsp_rdata(seq_mem_rsp_rdata),
    .mem_rsp_error(seq_mem_rsp_error));
  anvil_q2_ht_convert converter (
    .clk(clk),.rst_n(rst_n && !local_annul),
    .s_valid(running && state==CONV_REQ),.s_ready(convert_ready),
    .s_op(conversion_op),.s_data(conversion_input),
    .m_valid(convert_valid),.m_ready(running && state==CONV_RSP),
    .m_data(convert_data),.m_error(convert_error));
  anvil_q2_ht_integer_math arithmetic (
    .clk(clk),.rst_n(rst_n),.annul(local_annul),
    .cmd_valid(running && state==MATH_REQ),.cmd_ready(math_ready),
    .cmd_op(math_op),.cmd_a(math_a),.cmd_b(math_b),
    .rsp_valid(math_valid),.rsp_ready(running && state==MATH_RSP),
    .rsp_data(math_data),.rsp_error(math_error));
  anvil_q2_ht_exp exponential_unit (
    .clk(clk),.rst_n(rst_n),.annul(local_annul),
    .cmd_valid(running && state==EXP_REQ),.cmd_ready(exp_ready),.cmd_x(exp_argument),
    .rsp_valid(exp_valid),.rsp_ready(running && state==EXP_RSP),
    .rsp_data(exp_data),.rsp_error(exp_error));
  anvil_q2_ht_fp32_add_pipe floating_adder (
    .clk(clk),.rst_n(rst_n && !local_annul),.advance(1'b1),
    .a(fp_a),.b(fp_b),.sum(fp_data),.error(fp_error));
  anvil_q2_ht_projection #(.TILE_SLOTS(TILE_SLOTS),.GROUP_SIZE(GROUP_SIZE)) projections (
    .clk(clk),.rst_n(rst_n),.flush(local_annul),.resources_drained(resources_drained),
    .cmd_valid(running && state==PROJ_COMMAND),.cmd_ready(projection_ready),
    .cmd_mode(mode),.cmd_descriptor(projection_descriptor),
    .idle(projection_idle),.done(projection_done),.fault(projection_fault),
    .result_valid(projection_result_valid),.result_ready(running && state==PROJ_RESULT),
    .result_row(projection_result_row),.result_sum(projection_result_sum),
    .result_fp32(projection_result_fp32),.result_last(projection_result_last),
    .act_req_valid(p_act_req_valid),.act_req_ready(p_act_req_ready),.act_req_col(p_act_col),
    .act_rsp_valid(tile_valid && !head_tile),.act_rsp_ready(p_act_rsp_ready),
    .act_rsp_data(tile_data),.act_rsp_error(tile_error),
    .prefetch_valid(prefetch_valid),.prefetch_ready(prefetch_ready),
    .prefetch_address(prefetch_address),.prefetch_beats(prefetch_beats),
    .prefetch_slot(prefetch_slot),.prefetch_generation(prefetch_generation),
    .alloc_valid(alloc_valid),.alloc_ready(alloc_ready),.alloc_slot(alloc_slot),
    .alloc_generation(alloc_generation),.alloc_mode(alloc_mode),
    .operand_valid(operand_valid),.operand_ready(operand_ready),.operand_slot(operand_slot),
    .operand_generation(operand_generation),.operand_activation(operand_activation),
    .operand_keep(operand_keep),.meta_valid(meta_valid),.meta_ready(meta_ready),
    .meta_slot(meta_slot),.meta_generation(meta_generation),.meta_row(meta_row),
    .meta_zero(meta_zero),.meta_scale(meta_scale),
    .execute_valid(execute_valid),.execute_ready(execute_ready),.execute_slot(execute_slot),
    .execute_generation(execute_generation),.issue_valid(issue_valid),.issue_ready(issue_ready),
    .issue_slot(issue_slot),.issue_generation(issue_generation),.issue_row(issue_row),
    .issue_tag(issue_tag),.release_valid(release_valid),.release_ready(release_ready),
    .release_slot(release_slot),.release_generation(release_generation),
    .array_valid(array_valid && !active_head),.array_mode(array_mode),
    .array_ready(projection_array_ready),.array_sum(array_sum),.array_fp32(array_fp32),
    .array_tag(array_tag),.array_error(array_error),
    .mem_req_valid(proj_mem_req_valid),.mem_req_ready(proj_mem_req_ready),
    .mem_req_addr(proj_mem_req_addr),.mem_rsp_valid(proj_mem_rsp_valid),
    .mem_rsp_ready(proj_mem_rsp_ready),.mem_rsp_rdata(proj_mem_rsp_rdata),
    .mem_rsp_error(proj_mem_rsp_error));
  assign array_ready=running && (active_head ?
    state==HEAD_BF_RESULT : projection_array_ready);
  assign direct_active=running && active_head;
  assign direct_valid=running && state==HEAD_BF_ISSUE;
  assign direct_keep=direct_valid ? head_keep : 128'd0;
  assign direct_act=direct_valid ? head_activations : 4096'd0;
  assign direct_bf16=direct_valid ? head_weights : 2048'd0;
  assign direct_tag=direct_valid ? {vocabulary,input_col} : 64'd0;
  assign token_ready=running && state==IDLE && reader_idle && projection_idle;
  assign logit_valid=running && state==HEAD_EMIT;
  assign logit_index=logit_valid ? vocabulary : 32'd0;
  assign logit_data=logit_valid ? output_data : 32'sd0;
  assign done=rst_n && !flush && completed;
  assign error=done && completed_error;
  assign busy=rst_n && state!=IDLE;
  assign fault=rst_n && faulted;
  assign memory_idle=reader_idle;
  assign kv_invalidate=rst_n && invalidate_pulse;
  assign desc_req_valid=running && state==DESC_REQ;
  assign desc_req_index=desc_req_valid ? requested_descriptor : 9'd0;
  assign desc_rsp_ready=running && state==DESC_RSP;
  assign kv_cmd_valid=running && state==KV_REQ;
  assign kv_cmd_write=kv_cmd_valid && cache_write;
  assign kv_cmd_value=kv_cmd_valid && cache_value;
  assign kv_cmd_layer=kv_cmd_valid ? layer : 32'd0;
  assign kv_cmd_pos=kv_cmd_valid ? cache_position : 32'd0;
  assign kv_cmd_head=kv_cmd_valid ? cache_head : 32'd0;
  assign kv_cmd_block=kv_cmd_valid ? cache_block : 32'd0;
  assign kv_cmd_data=kv_cmd_valid && cache_write ? cache_data : {CW*32{1'b0}};
  assign kv_rsp_ready=running && state==KV_RSP;
  assign kv_commit_valid=running && state==KV_COMMIT;
  assign kv_commit_layer=kv_commit_valid ? layer : 32'd0;
  assign kv_commit_pos=kv_commit_valid ? position : 32'd0;

  always @(posedge clk) begin
    if (running && state==ATTN_SCORE_SAVE) score_ram[time_index]<=score;
    if (running && state==ATTN_EXP_READ) score_read<=score_ram[time_index];
    if (running && state==ATTN_EXP_SAVE) exponent_ram[time_index]<=exp_value;
    if (running && state==ATTN_WEIGHT_READ) exponent_read<=exponent_ram[time_index];
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; continuation<=IDLE; sequence_valid<=0; decoding<=0; phase<=0;
      completed<=0; completed_error<=0; faulted<=0; invalidate_pulse<=0;
      mode<=0; row_last<=0; rope_key<=0; store_value<=0; head_first<=0;
      token<=0; position<=0; next_position<=0; prefill_count<=0; frozen_prefill<=0;
      layer<=0; index<=0; output_row<=0; vocabulary<=0; head<=0; kv_head<=0;
      head_in_group<=0; pair_index<=0; dimension<=0; time_index<=0; component<=0;
      block_index<=0; block_word<=0; input_col<=0; lane_index<=0;
      norm_kind<=0; projection<=0; projection_src<=0; projection_dst<=0;
      descriptor<=0; projection_descriptor<=0; bias_descriptor<=0; row_base<=0;
      x<=0; y<=0; cosine<=0; sine<=0; rotated_x<=0;
      accumulator<=0; saved_product<=0; saved_sum<=0; max_score<=0; score<=0;
      reciprocal<=0; attention_scale<=0; denominator<=0; exponential<=0;
      floating_sum<=0; output_data<=0; block_data<=0; returned_block<=0;
      head_activations<=0; head_weights<=0; head_keep<=0;
      requested_descriptor<=0; read_vector<=0; write_vector<=0; read_index<=0;
      write_index<=0; write_data<=0; vector_value<=0;
      coefficient_address<=0; coefficient_word32<=0; coefficient_value<=0;
      conversion_input<=0; conversion_value<=0; conversion_op<=0;
      math_op<=0; math_a<=0; math_b<=0; math_value<=0; exp_argument<=0;
      exp_value<=0; fp_a<=0; fp_b<=0; fp_value<=0; fp_count<=0;
      cache_write<=0; cache_value<=0; cache_commit<=0; cache_position<=0;
      cache_head<=0; cache_block<=0; cache_data<=0; descriptor_value<=0;
    end else begin
      completed<=0; completed_error<=0; invalidate_pulse<=0;
      if (local_annul) begin
        state<=IDLE; faulted<=0; sequence_valid<=0; decoding<=0;
        prefill_count<=0; frozen_prefill<=0; next_position<=0;
      end else if (projection_fault) begin state<=FAILED; faulted<=1; end
      else case (state)
        IDLE: if (token_valid && token_ready) begin
          if (invalid_token) begin
            sequence_valid<=0; decoding<=0; prefill_count<=0; frozen_prefill<=0;
            invalidate_pulse<=1; state<=INVALID_DONE;
          end else begin
            token<=token_id; position<=token_pos; phase<=token_phase; mode<=weight_mode;
            index<=0; layer<=0; vocabulary<=0; norm_kind<=0;
            if (new_sequence) begin
              sequence_valid<=1; decoding<=token_phase; prefill_count<=0;
              frozen_prefill<=0; next_position<=0; invalidate_pulse<=1;
            end else if (token_phase && !decoding) begin
              decoding<=1; frozen_prefill<=prefill_count;
            end
            get_descriptor(9'd0,EMBED_DESC);
          end
        end
        INVALID_DONE: begin completed<=1; completed_error<=1; state<=IDLE; end
        FAILED: begin end
        VREAD_REQ: if (vf_ready) state<=VREAD_RSP;
        VREAD_RSP: if (vf_valid) begin
          vector_value<=vf_data; state<=continuation;
          if (vf_error) begin faulted<=1; state<=FAILED; end
        end
        VWRITE: state<=continuation;
        DESC_REQ: if (desc_req_ready) state<=DESC_RSP;
        DESC_RSP: if (desc_rsp_valid) begin
          descriptor_value<=desc_rsp_data; state<=continuation;
          if (desc_rsp_error) begin faulted<=1; state<=FAILED; end
        end
        COEFF_REQ: if (reader_ready) state<=COEFF_RSP;
        COEFF_RSP: if (reader_valid) begin
          coefficient_value<=reader_data; state<=continuation;
          if (reader_error) begin faulted<=1; state<=FAILED; end
        end
        CONV_REQ: if (convert_ready) state<=CONV_RSP;
        CONV_RSP: if (convert_valid) begin
          conversion_value<=convert_data; state<=continuation;
          if (convert_error) begin faulted<=1; state<=FAILED; end
        end
        MATH_REQ: if (math_ready) state<=MATH_RSP;
        MATH_RSP: if (math_valid) begin
          math_value<=math_data; state<=continuation;
          if (math_error) begin faulted<=1; state<=FAILED; end
        end
        EXP_REQ: if (exp_ready) state<=EXP_RSP;
        EXP_RSP: if (exp_valid) begin
          exp_value<=exp_data; state<=continuation;
          if (exp_error) begin faulted<=1; state<=FAILED; end
        end
        FP_WAIT: if (fp_count==4) begin
          fp_value<=fp_data; state<=continuation;
          if (fp_error) begin faulted<=1; state<=FAILED; end
        end else fp_count<=fp_count+3'd1;
        KV_REQ: if (kv_cmd_ready) state<=KV_RSP;
        KV_COMMIT: if (kv_commit_ready) state<=KV_RSP;
        KV_RSP: if (kv_rsp_valid) begin
          returned_block<=kv_rsp_data; state<=continuation;
          if (kv_rsp_error) begin faulted<=1; state<=FAILED; end
        end

        EMBED_DESC: begin
          descriptor<=descriptor_value;
          calculate(M_MUL64,{96'd0,token},
            {96'd0,descriptor_value[320+:32]},EMBED_BASE);
        end
        EMBED_BASE: begin
          row_base<=descriptor[32:0]+math_value[32:0]; state<=EMBED_READ;
        end
        EMBED_READ: read_coefficient(row_base+({1'b0,index} << 1),0,EMBED_CONVERT);
        EMBED_CONVERT: convert_word(mode ? 4'd1 : 4'd0,coefficient_value,EMBED_WRITE);
        EMBED_WRITE: write_word(VX,index,conversion_value,EMBED_NEXT);
        EMBED_NEXT: if (index+32'd1<HIDDEN_SIZE) begin index<=index+32'd1; state<=EMBED_READ; end
          else begin norm_kind<=0; state<=NORM_START; end

        NORM_START: begin
          index<=0; accumulator<=0;
          get_descriptor(norm_kind==2 ? 9'd2 :
            (9'd16+9'(layer << 4)+(norm_kind==0 ? 9'd7 : 9'd8)),NORM_SCAN);
        end
        NORM_SCAN: begin descriptor<=descriptor_value; read_word(VX,index,NORM_SQUARE); end
        NORM_SQUARE: calculate(M_MUL32,sx32(vector_value),sx32(vector_value),NORM_SUM);
        NORM_SUM: calculate(M_ADD,accumulator,math_value,NORM_NEXT);
        NORM_NEXT: begin
          accumulator<=math_value;
          if (index+32'd1<HIDDEN_SIZE) begin
            index<=index+32'd1; read_word(VX,index+32'd1,NORM_SQUARE);
          end else calculate(M_UDIV,math_value << 32,128'(HIDDEN_SIZE),NORM_MEAN);
        end
        NORM_MEAN: calculate(M_ADD,math_value,128'd18446744073710,NORM_EPSILON);
        NORM_EPSILON: calculate(M_SQRT,math_value,0,NORM_ROOT);
        NORM_ROOT: calculate(M_UDIV,128'd1 << 64,math_value,NORM_RECIP);
        NORM_RECIP: begin reciprocal<=math_value[63:0]; index<=0; state<=NORM_APPLY; end
        NORM_APPLY: read_word(VX,index,NORM_X);
        NORM_X: begin
          x<=vector_value;
          read_coefficient(descriptor[32:0]+({1'b0,index} << 1),0,NORM_GAMMA);
        end
        NORM_GAMMA: convert_word(mode ? 4'd1 : 4'd0,coefficient_value,NORM_CONVERT);
        NORM_CONVERT: calculate(M_MUL32,sx32(x),sx32(conversion_value),NORM_PRODUCT);
        NORM_PRODUCT: calculate(M_MUL64,math_value,{64'd0,reciprocal},NORM_SCALE);
        NORM_SCALE: calculate(M_ROUND,math_value,128'd48,NORM_ROUND);
        NORM_ROUND: write_word(VN,index,clamp32(math_value),NORM_ADVANCE);
        NORM_ADVANCE: if (index+32'd1<HIDDEN_SIZE) begin index<=index+32'd1; state<=NORM_APPLY; end
          else if (norm_kind==2) state<=HEAD_START;
          else begin projection<=norm_kind==0 ? 3'd0 : 3'd4; state<=PROJ_START; end

        PROJ_START: begin
          case (projection)
            0: begin projection_src<=VN; projection_dst<=VQ; end
            1: begin projection_src<=VN; projection_dst<=VK; end
            2: begin projection_src<=VN; projection_dst<=VV; end
            3: begin projection_src<=VA; projection_dst<=VO; end
            4: begin projection_src<=VN; projection_dst<=VG; end
            5: begin projection_src<=VN; projection_dst<=VU; end
            6: begin projection_src<=VM; projection_dst<=VO; end
            default: begin faulted<=1; state<=FAILED; end
          endcase
          get_descriptor(9'd16+9'(layer << 4)+{6'd0,projection},PROJ_DESC);
        end
        PROJ_DESC: begin
          projection_descriptor<=descriptor_value;
          if (projection<3) get_descriptor(
            9'd25+9'(layer << 4)+{6'd0,projection},PROJ_BIAS_DESC);
          else state<=PROJ_COMMAND;
        end
        PROJ_BIAS_DESC: begin bias_descriptor<=descriptor_value; state<=PROJ_COMMAND; end
        PROJ_COMMAND: if (projection_ready) state<=PROJ_RESULT;
        PROJ_RESULT: if (projection_result_valid) begin
          saved_sum<=projection_result_sum; floating_sum<=projection_result_fp32;
          output_row<=projection_result_row; row_last<=projection_result_last;
          if (projection<3) read_coefficient(
            bias_descriptor[32:0]+({1'b0,projection_result_row} << 1),0,PROJ_BIAS);
          else state<=PROJ_FINAL;
        end
        PROJ_BIAS: convert_word(mode ? 4'd7 : 4'd0,coefficient_value,PROJ_BIAS_CONVERT);
        PROJ_BIAS_CONVERT: if (mode)
          floating_add(floating_sum,conversion_value,PROJ_BIAS_ADD);
          else calculate(M_ADD,saved_sum,sx32(conversion_value) << 16,PROJ_BIAS_ADD);
        PROJ_BIAS_ADD: begin
          if (mode) floating_sum<=fp_value; else saved_sum<=math_value;
          state<=PROJ_FINAL;
        end
        PROJ_FINAL: if (mode) convert_word(4'd2,floating_sum,PROJ_CONVERT);
          else calculate(M_ROUND,saved_sum,128'd16,PROJ_CONVERT);
        PROJ_CONVERT: write_word(projection_dst,output_row,
          mode ? conversion_value : clamp32(math_value),PROJ_NEXT);
        PROJ_NEXT: if (!row_last) state<=PROJ_RESULT;
          else case (projection)
            0,1,4: begin projection<=projection+3'd1; state<=PROJ_START; end
            2: state<=ROPE_START;
            3,6: state<=RESIDUAL_START;
            5: state<=SWIGLU_START;
            default: begin faulted<=1; state<=FAILED; end
          endcase

        ROPE_START: begin
          head<=0; pair_index<=0; rope_key<=0; get_descriptor(9'd3,ROPE_BASE);
        end
        ROPE_BASE: begin
          descriptor<=descriptor_value;
          calculate(M_MUL64,{96'd0,position},
            {96'd0,descriptor_value[320+:32]},ROPE_READ_X);
        end
        ROPE_READ_X: begin
          row_base<=descriptor[32:0]+math_value[32:0];
          read_word(rope_key ? VK : VQ,vector_head_base+pair_index,ROPE_X);
        end
        ROPE_X: begin
          x<=vector_value;
          read_word(rope_key ? VK : VQ,
            vector_head_base+pair_index+(HEAD_DIM >> 1),ROPE_Y);
        end
        ROPE_Y: begin
          y<=vector_value; read_coefficient(row_base+({1'b0,pair_index} << 3),1,ROPE_COS);
        end
        ROPE_COS: begin
          cosine<=coefficient_value;
          read_coefficient(row_base+({1'b0,pair_index} << 3)+33'd4,1,ROPE_SIN);
        end
        ROPE_SIN: begin
          sine<=coefficient_value;
          calculate(M_MUL32,sx32(x),sx32(cosine),ROPE_XCOS);
        end
        ROPE_XCOS: begin
          saved_product<=math_value;
          calculate(M_MUL32,sx32(y),sx32(sine),ROPE_YSIN);
        end
        ROPE_YSIN: calculate(M_SUB,saved_product,math_value,ROPE_SUB);
        ROPE_SUB: calculate(M_ROUND,math_value,128'd30,ROPE_ROUND_X);
        ROPE_ROUND_X: begin
          rotated_x<=clamp32(math_value);
          calculate(M_MUL32,sx32(y),sx32(cosine),ROPE_YCOS);
        end
        ROPE_YCOS: begin
          saved_product<=math_value; calculate(M_MUL32,sx32(x),sx32(sine),ROPE_XSIN);
        end
        ROPE_XSIN: calculate(M_ADD,saved_product,math_value,ROPE_ADD);
        ROPE_ADD: calculate(M_ROUND,math_value,128'd30,ROPE_ROUND_Y);
        ROPE_ROUND_Y: begin
          y<=clamp32(math_value);
          write_word(rope_key ? VK : VQ,vector_head_base+pair_index,rotated_x,ROPE_WRITE_Y);
        end
        ROPE_WRITE_Y: write_word(rope_key ? VK : VQ,
          vector_head_base+pair_index+(HEAD_DIM >> 1),y,ROPE_NEXT);
        ROPE_NEXT: begin
          if (pair_index+32'd1<(HEAD_DIM >> 1)) begin
            pair_index<=pair_index+32'd1;
            read_word(rope_key ? VK : VQ,vector_head_base+pair_index+32'd1,ROPE_X);
          end else if (head+32'd1<rope_head_count) begin
            pair_index<=0; head<=head+32'd1;
            read_word(rope_key ? VK : VQ,(head+32'd1)*HEAD_DIM,ROPE_X);
          end else if (!rope_key) begin
            rope_key<=1; head<=0; pair_index<=0; read_word(VK,0,ROPE_X);
          end else state<=STORE_START;
        end

        STORE_START: begin
          kv_head<=0; block_index<=0; block_word<=0; store_value<=0; block_data<=0;
          state<=STORE_READ;
        end
        STORE_READ: read_word(store_value ? VV : VK,store_index,STORE_WORD);
        STORE_WORD: if (cache_mode==1) convert_word(4'd3,vector_value,STORE_ENCODE);
          else begin conversion_value<=vector_value; state<=STORE_INSERT; end
        STORE_ENCODE: state<=STORE_INSERT;
        STORE_INSERT: begin
          block_data[block_word*32+:32]<=conversion_value;
          if (block_word+32'd1<CW) begin block_word<=block_word+32'd1; state<=STORE_READ; end
          else state<=STORE_SEND;
        end
        STORE_SEND: cache_access(1,store_value,position,kv_head,block_index,
          block_data,STORE_NEXT);
        STORE_NEXT: begin
          block_word<=0; block_data<=0;
          if (block_index+32'd1<BLOCKS) begin block_index<=block_index+32'd1; state<=STORE_READ; end
          else if (kv_head+32'd1<NUM_KV_HEADS) begin
            block_index<=0; kv_head<=kv_head+32'd1; state<=STORE_READ;
          end else if (!store_value) begin
            store_value<=1; kv_head<=0; block_index<=0; state<=STORE_READ;
          end else begin continuation<=STORE_COMMIT; state<=KV_COMMIT; end
        end
        STORE_COMMIT: calculate(M_SQRT,128'(HEAD_DIM) << 32,0,ATTN_SCALE);
        ATTN_SCALE: begin
          attention_scale<=math_value[63:0]; head<=0; kv_head<=0; head_in_group<=0;
          state<=ATTN_HEAD;
        end
        ATTN_HEAD: begin
          time_index<=0; dimension<=0; accumulator<=0; max_score<=0; state<=ATTN_DOT;
        end
        ATTN_DOT: read_word(VQ,vector_head_base+dimension,ATTN_Q);
        ATTN_Q: begin
          x<=vector_value;
          cache_access(0,0,time_index,kv_head,dimension >> BLOCK_SHIFT,0,ATTN_KEY);
        end
        ATTN_KEY: if (cache_mode==1) convert_word(4'd0,selected_block_word,ATTN_KEY_CONVERT);
          else begin conversion_value<=selected_block_word; state<=ATTN_KEY_CONVERT; end
        ATTN_KEY_CONVERT: calculate(M_MUL32,sx32(x),sx32(conversion_value),ATTN_MUL);
        ATTN_MUL: calculate(M_ADD,accumulator,math_value,ATTN_SUM);
        ATTN_SUM: begin
          accumulator<=math_value;
          if (dimension+32'd1<HEAD_DIM) begin
            dimension<=dimension+32'd1; state<=ATTN_DOT;
          end else calculate(M_RDIV,math_value,{64'd0,attention_scale},ATTN_SCORE);
        end
        ATTN_SCORE: begin score<=math_value; state<=ATTN_SCORE_SAVE; end
        ATTN_SCORE_SAVE: if (time_index==0) begin
            max_score<=score; state<=ATTN_TIME_NEXT;
          end else calculate(M_SUB,score,max_score,ATTN_COMPARE);
        ATTN_COMPARE: begin
          if (math_value>0) max_score<=score; state<=ATTN_TIME_NEXT;
        end
        ATTN_TIME_NEXT: if (time_index<position) begin
            time_index<=time_index+32'd1; dimension<=0; accumulator<=0; state<=ATTN_DOT;
          end else begin time_index<=0; denominator<=0; state<=ATTN_EXP_READ; end
        ATTN_EXP_READ: state<=ATTN_EXP_LATCH;
        ATTN_EXP_LATCH: calculate(M_SUB,score_read,max_score,ATTN_DIFF);
        ATTN_DIFF: exponential_of(math_value,ATTN_EXP);
        ATTN_EXP: state<=ATTN_EXP_SAVE;
        ATTN_EXP_SAVE: calculate(M_ADD,{64'd0,denominator},{96'd0,exp_value},ATTN_DENOM);
        ATTN_DENOM: begin
          denominator<=math_value[63:0];
          if (time_index<position) begin time_index<=time_index+32'd1; state<=ATTN_EXP_READ; end
          else begin component<=0; state<=ATTN_WEIGHT_START; end
        end
        ATTN_WEIGHT_START: begin time_index<=0; accumulator<=0; state<=ATTN_WEIGHT_READ; end
        ATTN_WEIGHT_READ: state<=ATTN_WEIGHT_LATCH;
        ATTN_WEIGHT_LATCH: begin
          exponential<=exponent_read;
          cache_access(0,1,time_index,kv_head,component >> BLOCK_SHIFT,0,ATTN_VALUE);
        end
        ATTN_VALUE: if (cache_mode==1) convert_word(4'd0,selected_value_word,ATTN_VALUE_CONVERT);
          else begin conversion_value<=selected_value_word; state<=ATTN_VALUE_CONVERT; end
        ATTN_VALUE_CONVERT: calculate(M_MUL64,sx32(conversion_value),
          {96'd0,exponential},ATTN_WEIGHT_MUL);
        ATTN_WEIGHT_MUL: calculate(M_ADD,accumulator,math_value,ATTN_WEIGHT_ADD);
        ATTN_WEIGHT_ADD: begin
          accumulator<=math_value;
          if (time_index<position) begin
            time_index<=time_index+32'd1; state<=ATTN_WEIGHT_READ;
          end else calculate(M_RDIV,math_value,{64'd0,denominator},ATTN_DIVIDE);
        end
        ATTN_DIVIDE: write_word(VA,vector_head_base+component,clamp32(math_value),ATTN_COMPONENT_NEXT);
        ATTN_COMPONENT_NEXT: if (component+32'd1<HEAD_DIM) begin
            component<=component+32'd1; state<=ATTN_WEIGHT_START;
          end else if (head+32'd1<NUM_Q_HEADS) begin
            head<=head+32'd1;
            if (head_in_group+32'd1==HEAD_RATIO) begin
              head_in_group<=0; kv_head<=kv_head+32'd1;
            end else head_in_group<=head_in_group+32'd1;
            state<=ATTN_HEAD;
          end else begin projection<=3; state<=PROJ_START; end

        RESIDUAL_START: begin index<=0; read_word(VX,0,RESIDUAL_X); end
        RESIDUAL_X: begin x<=vector_value; read_word(VO,index,RESIDUAL_O); end
        RESIDUAL_O: calculate(M_ADD,sx32(x),sx32(vector_value),RESIDUAL_ADD);
        RESIDUAL_ADD: write_word(VX,index,clamp32(math_value),RESIDUAL_NEXT);
        RESIDUAL_NEXT: if (index+32'd1<HIDDEN_SIZE) begin
            index<=index+32'd1; read_word(VX,index+32'd1,RESIDUAL_X);
          end else if (projection==3) begin norm_kind<=1; state<=NORM_START; end
          else if (layer+32'd1<NUM_LAYERS) begin
            layer<=layer+32'd1; norm_kind<=0; state<=NORM_START;
          end else begin norm_kind<=2; state<=NORM_START; end

        SWIGLU_START: begin index<=0; read_word(VG,0,SWIGLU_GATE); end
        SWIGLU_GATE: begin x<=vector_value; read_word(VU,index,SWIGLU_UP); end
        SWIGLU_UP: begin
          y<=vector_value;
          if (x[31]) exponential_of(sx32(x),SWIGLU_EXP);
          else calculate(M_SUB,0,sx32(x),SWIGLU_SIGMOID);
        end
        SWIGLU_SIGMOID: exponential_of(math_value,SWIGLU_EXP);
        SWIGLU_EXP: calculate(M_UDIV,x[31] ? ({96'd0,exp_value} << 24) :
            (128'd1 << 48),{96'd0,(32'd16777216+exp_value)},SWIGLU_SILU);
        SWIGLU_SILU: calculate(M_MUL64,sx32(x),math_value,SWIGLU_SILU_ROUND);
        SWIGLU_SILU_ROUND: calculate(M_ROUND,math_value,128'd24,SWIGLU_PRODUCT);
        SWIGLU_PRODUCT: calculate(M_MUL32,sx32(clamp32(math_value)),sx32(y),SWIGLU_ROUND);
        SWIGLU_ROUND: calculate(M_ROUND,math_value,128'd16,SWIGLU_WRITE);
        SWIGLU_WRITE: write_word(VM,index,clamp32(math_value),SWIGLU_NEXT);
        SWIGLU_NEXT: if (index+32'd1<INTERMEDIATE_SIZE) begin
            index<=index+32'd1; read_word(VG,index+32'd1,SWIGLU_GATE);
          end else begin projection<=6; state<=PROJ_START; end

        HEAD_START: get_descriptor(9'd1,HEAD_DESC);
        HEAD_DESC: begin descriptor<=descriptor_value; vocabulary<=0; state<=HEAD_ROW; end
        HEAD_ROW: begin
          index<=0; input_col<=0; accumulator<=0; floating_sum<=0; head_first<=1;
          calculate(M_MUL64,{96'd0,vocabulary},
            {96'd0,descriptor[320+:32]},HEAD_BASE);
        end
        HEAD_BASE: begin
          row_base<=descriptor[32:0]+math_value[32:0];
          if (mode) state<=HEAD_BF_ACT; else state<=HEAD_W4_READ;
        end
        HEAD_W4_READ: read_word(VN,index,HEAD_W4_X);
        HEAD_W4_X: begin
          x<=vector_value; read_coefficient(row_base+({1'b0,index} << 1),0,HEAD_W4_WEIGHT);
        end
        HEAD_W4_WEIGHT: convert_word(4'd0,coefficient_value,HEAD_W4_CONVERT);
        HEAD_W4_CONVERT: calculate(M_MUL32,sx32(x),sx32(conversion_value),HEAD_W4_MUL);
        HEAD_W4_MUL: calculate(M_ADD,accumulator,math_value,HEAD_W4_SUM);
        HEAD_W4_SUM: begin
          accumulator<=math_value;
          if (index+32'd1<HIDDEN_SIZE) begin index<=index+32'd1; state<=HEAD_W4_READ; end
          else calculate(M_ROUND,math_value,128'd16,HEAD_W4_FINAL);
        end
        HEAD_W4_FINAL: begin output_data<=clamp32(math_value); state<=HEAD_EMIT; end
        HEAD_BF_ACT: if (tile_ready) state<=HEAD_BF_ACT_WAIT;
        HEAD_BF_ACT_WAIT: if (tile_valid) begin
          if (tile_error) begin faulted<=1; state<=FAILED; end
          else begin
            for (activation_lane=0; activation_lane<128; activation_lane=activation_lane+1)
              head_activations[activation_lane*32+:32]<=
                input_col+32'(activation_lane)<HIDDEN_SIZE ?
                  tile_data[activation_lane*32+:32] : 32'd0;
            head_weights<=0; head_keep<=0;
            lane_index<=0; state<=HEAD_BF_LOAD;
          end
        end
        HEAD_BF_LOAD: if (input_col+lane_index<HIDDEN_SIZE)
            read_coefficient(row_base+(({1'b0,input_col}+{1'b0,lane_index}) << 1),0,HEAD_BF_WORD);
          else state<=HEAD_BF_INSERT;
        HEAD_BF_WORD: begin
          head_weights[lane_index*16+:16]<=coefficient_value[15:0];
          head_keep[lane_index]<=1; state<=HEAD_BF_INSERT;
        end
        HEAD_BF_INSERT: if (lane_index==127) state<=HEAD_BF_ISSUE;
          else begin lane_index<=lane_index+32'd1; state<=HEAD_BF_LOAD; end
        HEAD_BF_ISSUE: if (direct_ready) state<=HEAD_BF_RESULT;
        HEAD_BF_RESULT: if (array_valid) begin
          if (array_error || !array_mode || array_tag!={vocabulary,input_col}) begin
            faulted<=1; state<=FAILED;
          end else if (head_first) begin
            floating_sum<=array_fp32; head_first<=0; state<=HEAD_BF_NEXT;
          end else floating_add(floating_sum,array_fp32,HEAD_BF_ACCUM);
        end
        HEAD_BF_ACCUM: begin floating_sum<=fp_value; state<=HEAD_BF_NEXT; end
        HEAD_BF_NEXT: if (input_col+32'd128<HIDDEN_SIZE) begin
            input_col<=input_col+32'd128; state<=HEAD_BF_ACT;
          end else convert_word(4'd2,floating_sum,HEAD_BF_FINAL);
        HEAD_BF_FINAL: begin output_data<=conversion_value; state<=HEAD_EMIT; end
        HEAD_EMIT: if (logit_ready) begin
          if (vocabulary+32'd1<VOCAB_SIZE) begin
            vocabulary<=vocabulary+32'd1; state<=HEAD_ROW;
          end else state<=TOKEN_FINISH;
        end
        TOKEN_FINISH: begin
          next_position<=position+32'd1;
          if (!phase) prefill_count<=position+32'd1;
          completed<=1; state<=IDLE;
        end
        default: begin faulted<=1; state<=FAILED; end
      endcase
    end
  end
endmodule
