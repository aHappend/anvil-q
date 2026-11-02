module anvil_q2_fp2_controller #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  parameter NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter VOCAB_SIZE=151936, MAX_SEQ_LEN=32768, WEIGHT_MODE=0, CACHE_MODE=0,
  parameter G=(HEAD_DIM+31) >> 5
) (
  input wire clk, rst_n, cancel,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence, token_phase,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index, logit_data,
  output wire done, error, cancel_done,
  output wire event_active, event_weight_underflow, event_tensor_bubble,
  output wire event_epilogue_stall,
  output wire [15:0] event_kv_reuses,
  output wire memory_flush,
  input wire memory_idle, memory_drain_done, memory_fault,
  output wire req_valid,
  input wire req_ready,
  output wire req_write,
  output wire [3:0] req_kind,
  output wire [31:0] req_layer, req_row, req_col, req_tag,
  output wire [2:0] req_proj,
  output wire [1:0] req_format,
  output wire [511:0] req_wdata,
  output wire [63:0] req_wstrb,
  input wire rsp_valid,
  output wire rsp_ready,
  input wire [511:0] rsp_data,
  input wire [31:0] rsp_tag,
  input wire rsp_error,
  output wire tensor_flush,
  output wire tensor_w_valid,
  input wire tensor_w_ready,
  output wire [511:0] tensor_w_data,
  output wire [15:0] tensor_w_scale,
  output wire tensor_w_format, tensor_w_first, tensor_w_last, tensor_w_error,
  output wire [31:0] tensor_w_tag,
  output wire tensor_in_valid,
  input wire tensor_in_ready,
  output wire [2047:0] tensor_in_a,
  output wire [127:0] tensor_in_mask,
  output wire tensor_in_first, tensor_in_last,
  output wire [31:0] tensor_in_tag,
  input wire tensor_out_valid,
  output wire tensor_out_ready,
  input wire [31:0] tensor_out_data, tensor_out_tag,
  input wire tensor_out_first, tensor_out_last, tensor_out_error,
  output wire epilogue_flush,
  output reg epilogue_in_valid,
  input wire epilogue_in_ready,
  output reg [2:0] epilogue_in_mode,
  output reg [31:0] epilogue_in_a, epilogue_in_b, epilogue_in_gamma,
  output reg [31:0] epilogue_in_cos, epilogue_in_sin,
  output reg [31:0] epilogue_in_length, epilogue_in_index, epilogue_in_tag,
  output reg epilogue_in_first, epilogue_in_last,
  input wire epilogue_out_valid,
  output wire epilogue_out_ready,
  input wire [31:0] epilogue_out_data, epilogue_out_pair,
  input wire [31:0] epilogue_out_index, epilogue_out_tag,
  input wire epilogue_out_first, epilogue_out_last, epilogue_out_error,
  output wire attention_flush,
  output wire attention_cmd_valid,
  input wire attention_cmd_ready,
  output wire [31:0] attention_cmd_layer, attention_cmd_kv_head,
  output wire [31:0] attention_cmd_pos, attention_cmd_len, attention_cmd_tag,
  output wire [6*HEAD_DIM*16-1:0] attention_cmd_query,
  output wire attention_kv_valid,
  input wire attention_kv_ready,
  output wire [HEAD_DIM*16-1:0] attention_kv_key, attention_kv_value,
  output wire [G*8-1:0] attention_kv_scale_key, attention_kv_scale_value,
  output wire attention_kv_format,
  output wire [31:0] attention_kv_index,
  output wire attention_kv_last, attention_kv_error,
  input wire attention_out_valid,
  output wire attention_out_ready,
  input wire [6*HEAD_DIM*32-1:0] attention_out_data,
  input wire [31:0] attention_out_tag,
  input wire attention_out_error
);
  localparam KD=NUM_KV_HEADS*HEAD_DIM, HALF=HEAD_DIM >> 1;
  localparam IDLE=0, EMB_REQ=1, EMB_WAIT=2, EMB_UNPACK=3,
    COEFF_REQ=4, COEFF_WAIT=5, COEFF_UNPACK=6,
    NORM_BEGIN=7, NORM_G_REQ=8, NORM_G_WAIT=9,
    NORM_READ=10, NORM_SEND=11, NORM_DRAIN=12,
    BIAS_BEGIN=13, BIAS_REQ=14, BIAS_WAIT=15, BIAS_UNPACK=16,
    GEMV_CMD=17, GEMV_ROWS=18, ROW_READ=19, ROW_PREPARE=20,
    BIAS_SEND=21, BIAS_SUM_WAIT=22, ROW_DISPATCH=23,
    EPILOGUE_WAIT=24, ROPE_SECOND=25, ROW_NEXT=26, LOGIT=27,
    CACHE_BEGIN=28, CACHE_READ=29, CACHE_PACK=30,
    CACHE_NATIVE_REQ=31, CACHE_NATIVE_WAIT=32,
    CACHE_ENCODE=33, CACHE_ENCODE_WAIT=34,
    CACHE_MX_REQ=35, CACHE_MX_WAIT=36, CACHE_META_REQ=37, CACHE_META_WAIT=38,
    CACHE_NEXT=39, ATTN_BEGIN=40, ATTN_QUERY_READ=41, ATTN_QUERY_PACK=42,
    ATTN_CMD=43, ATTN_READ_REQ=44, ATTN_READ_WAIT=45,
    ATTN_SEND=46, ATTN_WAIT=47, ATTN_STORE_READ=48, ATTN_STORE_WRITE=49,
    ABORT_START=50, DRAIN=51, FINISH=52, CANCEL_FINISH=53;
  reg [5:0] state;
  reg active, failed, sequence_valid, decoding, phase, cancel_pending, cancelled_active;
  reg [31:0] position, token, layer, next_position, prefill_cursor, frozen_prefill_count;
  reg [31:0] index, beat_base;
  reg [5:0] unpack_index;
  reg [511:0] read_beat;
  reg [1:0] norm_mode;
  reg norm_running;
  reg [2:0] projection;
  reg logits_projection;
  reg [31:0] row_value, row_number, row_head_offset;
  reg row_final;
  reg [15:0] second_rotated;
  reg [31:0] pending_logit;
  reg [31:0] cache_head, cache_head_base, cache_dimension;
  reg cache_value_select;
  reg [5:0] cache_pack_index;
  reg [511:0] cache_beat, encode_group;
  reg [63:0] cache_strobe;
  reg [31:0] encode_mask;
  reg [2:0] cache_group;
  reg [1023:0] encoded_payload;
  reg [31:0] encoded_scales;
  reg cache_payload_beat;
  reg [31:0] attention_head, query_base, query_component, attention_position;
  reg [31:0] attention_component;
  reg [6*HEAD_DIM*16-1:0] query_buffer;
  reg [HEAD_DIM*16-1:0] key_buffer, value_buffer;
  reg [G*8-1:0] key_scales, value_scales;
  reg [1:0] attention_read_kind;
  reg [2:0] attention_read_beat;
  reg [31:0] attention_element;
  wire abort_local=cancel || state==ABORT_START || state==DRAIN ||
    state==CANCEL_FINISH;
  wire live=rst_n && !abort_local;
  assign memory_flush=cancel || state==ABORT_START;
  assign epilogue_flush=abort_local;
  assign attention_flush=abort_local;
  assign token_ready=live && state==IDLE && memory_idle;
  assign logit_valid=live && state==LOGIT;
  assign logit_index=rst_n ? row_number : 32'd0;
  assign logit_data=rst_n ? pending_logit : 32'd0;
  assign done=rst_n && !cancel && (state==FINISH ||
    (state==CANCEL_FINISH && cancelled_active));
  assign error=done && failed;
  assign cancel_done=rst_n && !cancel && state==CANCEL_FINISH;
  assign event_active=rst_n && active;
  assign event_epilogue_stall=epilogue_out_valid && !epilogue_out_ready;
  localparam [15:0] BROADCAST_USES=10*G;
  assign event_kv_reuses=(attention_kv_valid && attention_kv_ready) ?
    BROADCAST_USES : 16'd0;

  wire gm_busy, gm_cmd_ready, gm_row_valid, gm_row_error, gm_row_last;
  wire [31:0] gm_row_data, gm_row_index;
  wire gm_req_valid, gm_rsp_ready;
  wire [3:0] gm_req_kind;
  wire [31:0] gm_req_layer, gm_req_row, gm_req_col, gm_req_tag;
  wire [2:0] gm_req_proj;
  wire [1:0] gm_req_format;
  wire activation_read;
  wire [31:0] activation_column;
  wire hidden_tile_valid, ffn_tile_valid;
  wire [2047:0] hidden_tile, ffn_tile;
  wire [31:0] projection_inputs=(projection==6 && !logits_projection) ?
    INTERMEDIATE_SIZE : HIDDEN_SIZE;
  wire [31:0] projection_outputs=logits_projection ? VOCAB_SIZE :
    ((projection==1 || projection==2) ? KD :
     ((projection==4 || projection==5) ? INTERMEDIATE_SIZE : HIDDEN_SIZE));
  anvil_q2_fp2_gemv_stream gemv(
    .clk(clk),.rst_n(rst_n),.flush(abort_local),
    .cmd_valid(live && state==GEMV_CMD),.cmd_ready(gm_cmd_ready),
    .cmd_layer(layer),.cmd_inputs(projection_inputs),.cmd_outputs(projection_outputs),
    .cmd_projection(projection),.cmd_embedding(logits_projection),
    .cmd_mx(WEIGHT_MODE==2 && !logits_projection),.busy(gm_busy),
    .row_valid(gm_row_valid),.row_ready(live && state==GEMV_ROWS),
    .row_data(gm_row_data),.row_index(gm_row_index),
    .row_last(gm_row_last),.row_error(gm_row_error),
    .event_weight_underflow(event_weight_underflow),
    .event_tensor_bubble(event_tensor_bubble),
    .act_read_valid(activation_read),.act_read_column(activation_column),
    .act_data_valid((projection==6 && !logits_projection) ?
      ffn_tile_valid : hidden_tile_valid),
    .act_data((projection==6 && !logits_projection) ? ffn_tile : hidden_tile),
    .req_valid(gm_req_valid),.req_ready(req_ready && gm_busy && live),
    .req_kind(gm_req_kind),.req_layer(gm_req_layer),.req_row(gm_req_row),
    .req_col(gm_req_col),.req_tag(gm_req_tag),.req_proj(gm_req_proj),
    .req_format(gm_req_format),
    .rsp_valid(rsp_valid && gm_busy),.rsp_ready(gm_rsp_ready),
    .rsp_data(rsp_data),.rsp_tag(rsp_tag),.rsp_error(rsp_error),
    .tensor_flush(tensor_flush),
    .w_valid(tensor_w_valid),.w_ready(tensor_w_ready),.w_data(tensor_w_data),
    .w_scale(tensor_w_scale),.w_format(tensor_w_format),
    .w_first(tensor_w_first),.w_last(tensor_w_last),
    .w_error(tensor_w_error),.w_tag(tensor_w_tag),
    .in_valid(tensor_in_valid),.in_ready(tensor_in_ready),.in_a(tensor_in_a),
    .in_mask(tensor_in_mask),.in_first(tensor_in_first),.in_last(tensor_in_last),
    .in_tag(tensor_in_tag),
    .out_valid(tensor_out_valid),.out_ready(tensor_out_ready),
    .out_data(tensor_out_data),.out_tag(tensor_out_tag),
    .out_first(tensor_out_first),.out_last(tensor_out_last),
    .out_error(tensor_out_error));

  wire ep_accept=epilogue_out_valid && epilogue_out_ready;
  wire norm_accept=norm_running && ep_accept;
  wire row_ep_accept=state==EPILOGUE_WAIT && ep_accept;
  wire [15:0] ep_bf16, pair_bf16, attention_bf16;
  wire ep_narrow_error, pair_narrow_error, attention_narrow_error;
  anvil_q2_fp2_bf16_round ep_round(epilogue_out_data,ep_bf16,ep_narrow_error);
  anvil_q2_fp2_bf16_round pair_round(epilogue_out_pair,pair_bf16,pair_narrow_error);
  anvil_q2_fp2_bf16_round attention_round(attention_element,
    attention_bf16,attention_narrow_error);
  wire [15:0] unpacked_bf16=read_beat[16*unpack_index+:16];
  wire [31:0] unpacked_fp32=read_beat[32*unpack_index+:32];
  wire x_write=live && (state==EMB_UNPACK ||
    (row_ep_accept && !logits_projection && (projection==3 || projection==6)));
  wire [31:0] x_write_index=state==EMB_UNPACK ? beat_base+unpack_index : row_number;
  wire [31:0] x_write_data=state==EMB_UNPACK ?
    {unpacked_bf16,16'd0} : epilogue_out_data;
  wire [31:0] x_data;
  anvil_q2_fp2_scalar_store #(.LENGTH(HIDDEN_SIZE)) residual_state(
    clk,rst_n,x_write,x_write_index,x_write_data,
    (live && (state==NORM_READ || (state==ROW_READ &&
      !logits_projection && (projection==3 || projection==6)))),
    (state==NORM_READ ? index : row_number),x_data);
  wire bias_write=live && state==BIAS_UNPACK;
  wire [15:0] bias_data;
  anvil_q2_fp2_scalar_store #(.WIDTH(16),.LENGTH(HIDDEN_SIZE)) bias_state(
    clk,rst_n,bias_write,beat_base+{26'd0,unpack_index},unpacked_bf16,
    (live && state==ROW_READ && !logits_projection && projection<3),
    row_number,bias_data);
  wire [31:0] gate_data;
  anvil_q2_fp2_scalar_store #(.LENGTH(INTERMEDIATE_SIZE)) gate_branch(
    clk,rst_n,(live && state==ROW_DISPATCH && !logits_projection && projection==4),
    row_number,row_value,
    (live && state==ROW_READ && !logits_projection && projection==5),
    row_number,gate_data);
  wire [31:0] join_data;
  wire join_write=live && state==ROW_DISPATCH && !logits_projection &&
    projection<2 && row_head_offset<HALF;
  anvil_q2_fp2_scalar_store #(.LENGTH(HALF)) rope_join(
    clk,rst_n,join_write,row_head_offset,row_value,
    (live && state==ROW_READ && !logits_projection &&
      projection<2 && row_head_offset>=HALF),
    (row_head_offset-HALF),join_data);
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] cosines [0:HALF-1];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] sines [0:HALF-1];
  reg [31:0] cosine, sine;
  wire [31:0] coefficient_index=(beat_base+{26'd0,unpack_index}) >> 1;
  wire [31:0] pair_index=row_head_offset-HALF;
  always @(posedge clk) begin
    if (live) begin
      if (state==COEFF_UNPACK) begin
        if (unpack_index[0]) sines[coefficient_index]<=unpacked_fp32;
        else cosines[coefficient_index]<=unpacked_fp32;
      end
      if (state==ROW_READ && !logits_projection &&
          projection<2 && row_head_offset>=HALF) begin
        cosine<=cosines[pair_index];
        sine<=sines[pair_index];
      end
    end
  end
  wire q_write=live && !logits_projection && projection==0 &&
    (row_ep_accept || state==ROPE_SECOND);
  wire k_write=live && !logits_projection && projection==1 &&
    (row_ep_accept || state==ROPE_SECOND);
  wire v_write=live && !logits_projection && projection==2 && row_ep_accept;
  wire [31:0] rotated_index=(state==ROPE_SECOND) ? row_number : row_number-HALF;
  wire [15:0] rotated_data=(state==ROPE_SECOND) ? second_rotated : ep_bf16;
  wire [15:0] q_data, k_data, v_data;
  anvil_q2_fp2_scalar_store #(.WIDTH(16),.LENGTH(HIDDEN_SIZE)) query_state(
    clk,rst_n,q_write,rotated_index,rotated_data,
    (live && state==ATTN_QUERY_READ),query_base+query_component,q_data);
  anvil_q2_fp2_scalar_store #(.WIDTH(16),.LENGTH(KD)) key_state(
    clk,rst_n,k_write,rotated_index,rotated_data,
    (live && state==CACHE_READ && !cache_value_select),
    cache_head_base+cache_dimension,k_data);
  anvil_q2_fp2_scalar_store #(.WIDTH(16),.LENGTH(KD)) value_state(
    clk,rst_n,v_write,row_number,ep_bf16,
    (live && state==CACHE_READ && cache_value_select),
    cache_head_base+cache_dimension,v_data);
  wire hidden_write=live && (norm_accept || state==ATTN_STORE_WRITE);
  wire [31:0] hidden_index=norm_accept ? epilogue_out_index :
    query_base+attention_component;
  wire [15:0] hidden_data=norm_accept ? ep_bf16 : attention_bf16;
  anvil_q2_fp2_vector_store #(.LENGTH(HIDDEN_SIZE)) hidden_operands(
    clk,rst_n,hidden_write,hidden_index,hidden_data,
    (activation_read && !(projection==6 && !logits_projection)),
    activation_column,hidden_tile_valid,hidden_tile);
  anvil_q2_fp2_vector_store #(.LENGTH(INTERMEDIATE_SIZE)) ffn_operands(
    clk,rst_n,(live && row_ep_accept && !logits_projection && projection==5),
    row_number,ep_bf16,(activation_read && projection==6 && !logits_projection),
    activation_column,ffn_tile_valid,ffn_tile);

  wire bias_sum_valid, bias_sum_error;
  wire [31:0] bias_sum;
  anvil_q2_fp2_add4 bias_add(
    clk,rst_n,abort_local,1'b1,(live && state==BIAS_SEND),
    1'b0,row_value,{bias_data,16'd0},
    bias_sum_valid,bias_sum,bias_sum_error);
  assign epilogue_out_ready=live && (norm_running || state==EPILOGUE_WAIT);
  always @* begin
    epilogue_in_valid=0; epilogue_in_mode=0;
    epilogue_in_a=0; epilogue_in_b=0; epilogue_in_gamma=0;
    epilogue_in_cos=0; epilogue_in_sin=0;
    epilogue_in_length=0; epilogue_in_index=0; epilogue_in_tag=0;
    epilogue_in_first=0; epilogue_in_last=0;
    if (live) begin
      if (state==NORM_SEND) begin
        epilogue_in_valid=1; epilogue_in_mode=0; epilogue_in_a=x_data;
        epilogue_in_gamma={read_beat[16*index[4:0]+:16],16'd0};
        epilogue_in_length=HIDDEN_SIZE; epilogue_in_index=index;
        epilogue_in_first=index==0; epilogue_in_last=index+1==HIDDEN_SIZE;
      end else if (state==ROW_DISPATCH &&
          (logits_projection || projection!=4) &&
          (logits_projection || projection>=2 || row_head_offset>=HALF)) begin
        epilogue_in_valid=1;
        epilogue_in_index=row_number; epilogue_in_tag=row_number;
        epilogue_in_first=row_number==0; epilogue_in_last=row_final;
        epilogue_in_a=row_value;
        if (logits_projection || projection==2) epilogue_in_mode=4;
        else if (projection<2) begin
          epilogue_in_mode=1; epilogue_in_a=join_data; epilogue_in_b=row_value;
          epilogue_in_cos=cosine; epilogue_in_sin=sine;
          epilogue_in_index=row_number-HALF;
        end else if (projection==3 || projection==6) begin
          epilogue_in_mode=3; epilogue_in_a=x_data; epilogue_in_b=row_value;
        end else begin
          epilogue_in_mode=2; epilogue_in_a=gate_data; epilogue_in_b=row_value;
        end
      end
    end
  end

  wire encoder_ready, encoder_valid, encoder_error;
  wire [255:0] encoder_payload;
  wire [7:0] encoder_scale;
  wire [31:0] encoder_tag;
  anvil_q2_fp2_mx_encode32 cache_encoder(
    clk,rst_n,abort_local,(live && state==CACHE_ENCODE),encoder_ready,
    encode_group,encode_mask,{29'd0,cache_group},
    encoder_valid,(live && state==CACHE_ENCODE_WAIT),
    encoder_payload,encoder_scale,encoder_tag,encoder_error);
  wire [15:0] cache_source=cache_value_select ? v_data : k_data;
  assign attention_cmd_valid=live && state==ATTN_CMD;
  assign attention_cmd_layer=layer;
  assign attention_cmd_kv_head=attention_head;
  assign attention_cmd_pos=position;
  assign attention_cmd_len=position+1;
  assign attention_cmd_tag=attention_head;
  assign attention_cmd_query=query_buffer;
  assign attention_kv_valid=live && state==ATTN_SEND;
  assign attention_kv_key=key_buffer;
  assign attention_kv_value=value_buffer;
  assign attention_kv_scale_key=key_scales;
  assign attention_kv_scale_value=value_scales;
  assign attention_kv_format=CACHE_MODE==2;
  assign attention_kv_index=attention_position;
  assign attention_kv_last=attention_position==position;
  assign attention_kv_error=0;
  assign attention_out_ready=live && state==ATTN_STORE_WRITE &&
    attention_component+1==6*HEAD_DIM;

  reg own_req_valid, own_req_write, own_rsp_ready;
  reg [3:0] own_req_kind;
  reg [31:0] own_req_layer, own_req_row, own_req_col;
  reg [2:0] own_req_proj;
  reg [1:0] own_req_format;
  reg [511:0] own_req_wdata;
  reg [63:0] own_req_wstrb;
  wire [31:0] cache_payload_column=cache_head_base+
    (cache_payload_beat ? 32'd64 : 32'd0);
  wire [31:0] attention_payload_column=attention_head*HEAD_DIM+
    ((CACHE_MODE==2) ? ({29'd0,attention_read_beat} << 6) :
      ({29'd0,attention_read_beat} << 5));
  wire [31:0] attention_payload_offset=(CACHE_MODE==2) ?
    ({29'd0,attention_read_beat} << 6) : ({29'd0,attention_read_beat} << 5);
  always @* begin
    own_req_valid=0; own_req_write=0; own_rsp_ready=0;
    own_req_kind=0; own_req_layer=0; own_req_row=0; own_req_col=0;
    own_req_proj=0; own_req_format=0; own_req_wdata=0; own_req_wstrb=0;
    if (live && !gm_busy) case (state)
      EMB_REQ: begin
        own_req_valid=1; own_req_kind=0; own_req_row=token;
        own_req_col=beat_base; own_req_format=1;
      end
      COEFF_REQ: begin
        own_req_valid=1; own_req_kind=11; own_req_row=position;
        own_req_col=beat_base; own_req_format=0;
      end
      NORM_G_REQ: begin
        own_req_valid=1;
        own_req_kind=(norm_mode==0) ? 4'd5 : ((norm_mode==1) ? 4'd6 : 4'd7);
        own_req_layer=(norm_mode==2) ? 32'd0 : layer;
        own_req_col=beat_base; own_req_format=1;
      end
      BIAS_REQ: begin
        own_req_valid=1; own_req_kind=4; own_req_layer=layer;
        own_req_proj=projection; own_req_col=beat_base; own_req_format=1;
      end
      CACHE_NATIVE_REQ: begin
        own_req_valid=1; own_req_write=1;
        own_req_kind=cache_value_select ? 4'd10 : 4'd9;
        own_req_layer=layer; own_req_row=position;
        own_req_col=cache_head_base+cache_dimension-{26'd0,cache_pack_index};
        own_req_format=1; own_req_wdata=cache_beat; own_req_wstrb=cache_strobe;
      end
      CACHE_MX_REQ: begin
        own_req_valid=1; own_req_write=1;
        own_req_kind=cache_value_select ? 4'd13 : 4'd12;
        own_req_layer=layer; own_req_row=position;
        own_req_col=cache_payload_column; own_req_format=2;
        own_req_wdata=cache_payload_beat ? encoded_payload[1023:512] :
          encoded_payload[511:0];
        if (cache_payload_beat)
          own_req_wstrb=64'hffffffffffffffff >> (128-HEAD_DIM);
        else if (HEAD_DIM>=64) own_req_wstrb=64'hffffffffffffffff;
        else own_req_wstrb=64'hffffffffffffffff >> (64-HEAD_DIM);
      end
      CACHE_META_REQ: begin
        own_req_valid=1; own_req_write=1;
        own_req_kind=cache_value_select ? 4'd15 : 4'd14;
        own_req_layer=layer; own_req_row=position;
        own_req_col=cache_head*G; own_req_format=3;
        own_req_wdata={480'd0,encoded_scales};
        own_req_wstrb=64'hffffffffffffffff >> (64-G);
      end
      ATTN_READ_REQ: begin
        own_req_valid=1; own_req_layer=layer; own_req_row=attention_position;
        if (attention_read_kind<2) begin
          own_req_kind=(CACHE_MODE==2) ?
            (attention_read_kind[0] ? 4'd13 : 4'd12) :
            (attention_read_kind[0] ? 4'd10 : 4'd9);
          own_req_col=attention_payload_column;
          own_req_format=(CACHE_MODE==2) ? 2'd2 : 2'd1;
        end else begin
          own_req_kind=attention_read_kind[0] ? 4'd15 : 4'd14;
          own_req_col=attention_head*G; own_req_format=3;
        end
      end
      EMB_WAIT,COEFF_WAIT,NORM_G_WAIT,BIAS_WAIT,
      CACHE_NATIVE_WAIT,CACHE_MX_WAIT,CACHE_META_WAIT,ATTN_READ_WAIT:
        own_rsp_ready=1;
      default: begin end
    endcase
  end
  assign req_valid=live && (gm_busy ? gm_req_valid : own_req_valid);
  assign req_write=req_valid && !gm_busy && own_req_write;
  assign req_kind=req_valid ? (gm_busy ? gm_req_kind : own_req_kind) : 4'd0;
  assign req_layer=req_valid ? (gm_busy ? gm_req_layer : own_req_layer) : 32'd0;
  assign req_proj=req_valid ? (gm_busy ? gm_req_proj : own_req_proj) : 3'd0;
  assign req_row=req_valid ? (gm_busy ? gm_req_row : own_req_row) : 32'd0;
  assign req_col=req_valid ? (gm_busy ? gm_req_col : own_req_col) : 32'd0;
  assign req_tag=gm_busy ? gm_req_tag : 32'h80000000;
  assign req_format=req_valid ? (gm_busy ? gm_req_format : own_req_format) : 2'd0;
  assign req_wdata=req_write ? own_req_wdata : 512'd0;
  assign req_wstrb=req_write ? own_req_wstrb : 64'd0;
  assign rsp_ready=live && (gm_busy ? gm_rsp_ready : own_rsp_ready);
  wire own_response=rsp_valid && rsp_ready && !gm_busy;
  wire own_request=req_valid && req_ready && !gm_busy;
  wire own_response_bad=own_response && (rsp_error || rsp_tag!=32'h80000000);
  wire ep_metadata_bad=ep_accept && (norm_running ?
    (epilogue_out_index>=HIDDEN_SIZE || epilogue_out_tag!=0 ||
      epilogue_out_first!=(epilogue_out_index==0) ||
      epilogue_out_last!=(epilogue_out_index+1==HIDDEN_SIZE)) :
    (epilogue_out_tag!=row_number ||
      epilogue_out_index!=((!logits_projection && projection<2) ?
        row_number-HALF : row_number) || epilogue_out_last!=row_final));
  wire ep_narrow_used=norm_running || (!logits_projection &&
    (projection<=2 || projection==5));
  wire arithmetic_fault=(ep_accept && (epilogue_out_error || ep_metadata_bad ||
      (ep_narrow_used && ep_narrow_error) ||
      (!norm_running && !logits_projection && projection<2 && pair_narrow_error))) ||
    (state==BIAS_SUM_WAIT && bias_sum_valid && bias_sum_error) ||
    (state==CACHE_ENCODE_WAIT && encoder_valid &&
      (encoder_error || encoder_tag!={29'd0,cache_group})) ||
    (state==ATTN_STORE_WRITE && attention_narrow_error);
  wire unpack_fault=((state==EMB_UNPACK || state==BIAS_UNPACK) &&
      (&unpacked_bf16[14:7])) ||
    (state==COEFF_UNPACK && (&unpacked_fp32[30:23]));
  wire work_fault=memory_fault || own_response_bad || arithmetic_fault ||
    unpack_fault || (state==GEMV_ROWS && gm_row_valid && gm_row_error) ||
    (state==ATTN_WAIT && attention_out_valid &&
      (attention_out_error || attention_out_tag!=attention_head));
  integer element;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; active<=0; failed<=0; sequence_valid<=0; decoding<=0;
      phase<=0; cancel_pending<=0; cancelled_active<=0;
      position<=0; token<=0; layer<=0; next_position<=0;
      prefill_cursor<=0; frozen_prefill_count<=0;
      index<=0; beat_base<=0; unpack_index<=0; read_beat<=0;
      norm_mode<=0; norm_running<=0; projection<=0; logits_projection<=0;
      row_value<=0; row_number<=0; row_head_offset<=0; row_final<=0;
      second_rotated<=0; pending_logit<=0;
      cache_head<=0; cache_head_base<=0; cache_dimension<=0;
      cache_value_select<=0; cache_pack_index<=0; cache_beat<=0; cache_strobe<=0;
      encode_group<=0; encode_mask<=0; cache_group<=0;
      encoded_payload<=0; encoded_scales<=0; cache_payload_beat<=0;
      attention_head<=0; query_base<=0; query_component<=0; attention_position<=0;
      attention_component<=0; query_buffer<=0; key_buffer<=0; value_buffer<=0;
      key_scales<=0; value_scales<=0; attention_read_kind<=0;
      attention_read_beat<=0; attention_element<=0;
    end else if (cancel) begin
      state<=DRAIN; failed<=1; sequence_valid<=0; norm_running<=0;
      decoding<=0; prefill_cursor<=0; frozen_prefill_count<=0;
      if (!cancel_pending) cancelled_active<=active;
      cancel_pending<=1;
    end else if (work_fault && active && state!=ABORT_START &&
        state!=DRAIN && state!=FINISH && state!=CANCEL_FINISH) begin
      state<=ABORT_START; failed<=1; sequence_valid<=0; norm_running<=0;
      decoding<=0; prefill_cursor<=0; frozen_prefill_count<=0;
    end else begin
      if (memory_fault && !active) sequence_valid<=0;
      if (norm_accept && epilogue_out_last) begin
        norm_running<=0; row_head_offset<=0; row_number<=0;
        if (norm_mode==0) begin
          projection<=0; logits_projection<=0; state<=BIAS_BEGIN;
        end else if (norm_mode==1) begin
          projection<=4; logits_projection<=0; state<=GEMV_CMD;
        end else begin
          projection<=0; logits_projection<=1; state<=GEMV_CMD;
        end
      end
      case (state)
        IDLE: if (token_valid && token_ready) begin
          failed<=0; cancel_pending<=0; cancelled_active<=0;
          if (token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN ||
              (new_sequence && token_pos!=0) ||
              (!new_sequence && (!sequence_valid || token_pos!=next_position ||
               (decoding && !token_phase) ||
               (decoding && token_phase && token_pos<frozen_prefill_count) ||
               (!token_phase && token_pos!=prefill_cursor)))) begin
            failed<=1; sequence_valid<=0; active<=0; state<=FINISH;
          end else begin
            active<=1; token<=token_id; position<=token_pos; phase<=token_phase;
            layer<=0; beat_base<=0; unpack_index<=0; norm_mode<=0;
            logits_projection<=0; state<=EMB_REQ;
            if (new_sequence) begin
              sequence_valid<=1; next_position<=0; decoding<=token_phase;
              prefill_cursor<=0; frozen_prefill_count<=0;
            end else if (token_phase && !decoding) begin
              decoding<=1; frozen_prefill_count<=prefill_cursor;
            end
          end
        end
        EMB_REQ: if (own_request) state<=EMB_WAIT;
        EMB_WAIT: if (own_response) begin
          read_beat<=rsp_data; unpack_index<=0; state<=EMB_UNPACK;
        end
        EMB_UNPACK: begin
          if (beat_base+unpack_index+1==HIDDEN_SIZE) begin
            beat_base<=0; unpack_index<=0; state<=COEFF_REQ;
          end else if (unpack_index==31) begin
            beat_base<=beat_base+32; unpack_index<=0; state<=EMB_REQ;
          end else unpack_index<=unpack_index+1'b1;
        end
        COEFF_REQ: if (own_request) state<=COEFF_WAIT;
        COEFF_WAIT: if (own_response) begin
          read_beat<=rsp_data; unpack_index<=0; state<=COEFF_UNPACK;
        end
        COEFF_UNPACK: begin
          if (beat_base+unpack_index+1==HEAD_DIM) begin
            norm_mode<=0; state<=NORM_BEGIN;
          end else if (unpack_index==15) begin
            beat_base<=beat_base+16; unpack_index<=0; state<=COEFF_REQ;
          end else unpack_index<=unpack_index+1'b1;
        end
        NORM_BEGIN: begin
          index<=0; beat_base<=0; norm_running<=1; state<=NORM_G_REQ;
        end
        NORM_G_REQ: if (own_request) state<=NORM_G_WAIT;
        NORM_G_WAIT: if (own_response) begin read_beat<=rsp_data; state<=NORM_READ; end
        NORM_READ: state<=NORM_SEND;
        NORM_SEND: if (epilogue_in_valid && epilogue_in_ready) begin
          if (index+1==HIDDEN_SIZE) state<=NORM_DRAIN;
          else begin
            index<=index+1;
            if (index[4:0]==31) begin beat_base<=beat_base+32; state<=NORM_G_REQ; end
            else state<=NORM_READ;
          end
        end
        NORM_DRAIN: begin end
        BIAS_BEGIN: begin beat_base<=0; unpack_index<=0; state<=BIAS_REQ; end
        BIAS_REQ: if (own_request) state<=BIAS_WAIT;
        BIAS_WAIT: if (own_response) begin
          read_beat<=rsp_data; unpack_index<=0; state<=BIAS_UNPACK;
        end
        BIAS_UNPACK: begin
          if (beat_base+unpack_index+1==projection_outputs) state<=GEMV_CMD;
          else if (unpack_index==31) begin
            beat_base<=beat_base+32; unpack_index<=0; state<=BIAS_REQ;
          end else unpack_index<=unpack_index+1'b1;
        end
        GEMV_CMD: if (gm_cmd_ready) begin
          row_head_offset<=0; row_number<=0; state<=GEMV_ROWS;
        end
        GEMV_ROWS: if (gm_row_valid) begin
          row_value<=gm_row_data; row_number<=gm_row_index;
          row_final<=gm_row_last; state<=ROW_READ;
        end
        ROW_READ: state<=ROW_PREPARE;
        ROW_PREPARE: begin
          if (!logits_projection && projection<3) state<=BIAS_SEND;
          else state<=ROW_DISPATCH;
        end
        BIAS_SEND: state<=BIAS_SUM_WAIT;
        BIAS_SUM_WAIT: if (bias_sum_valid) begin row_value<=bias_sum; state<=ROW_DISPATCH; end
        ROW_DISPATCH: begin
          if (join_write || (!logits_projection && projection==4)) state<=ROW_NEXT;
          else if (epilogue_in_valid && epilogue_in_ready) state<=EPILOGUE_WAIT;
        end
        EPILOGUE_WAIT: if (row_ep_accept) begin
          if (logits_projection) begin pending_logit<=epilogue_out_data; state<=LOGIT; end
          else if (projection<2) begin second_rotated<=pair_bf16; state<=ROPE_SECOND; end
          else state<=ROW_NEXT;
        end
        ROPE_SECOND: state<=ROW_NEXT;
        ROW_NEXT: begin
          if (!logits_projection && projection<2) begin
            if (row_head_offset+1==HEAD_DIM) row_head_offset<=0;
            else row_head_offset<=row_head_offset+1;
          end
          if (!row_final) state<=GEMV_ROWS;
          else if (logits_projection) state<=FINISH;
          else case (projection)
            0,1: begin projection<=projection+1'b1; state<=BIAS_BEGIN; end
            2: begin
              cache_head<=0; cache_head_base<=0; cache_value_select<=0;
              state<=CACHE_BEGIN;
            end
            3: begin norm_mode<=1; state<=NORM_BEGIN; end
            4: begin projection<=5; state<=GEMV_CMD; end
            5: begin projection<=6; state<=GEMV_CMD; end
            default: begin
              if (layer+1<NUM_LAYERS) begin
                layer<=layer+1; norm_mode<=0; state<=NORM_BEGIN;
              end else begin norm_mode<=2; state<=NORM_BEGIN; end
            end
          endcase
        end
        LOGIT: if (logit_ready) begin
          if (row_final) begin
            next_position<=position+1;
            if (!phase) prefill_cursor<=position+1;
            state<=FINISH;
          end else state<=ROW_NEXT;
        end
        CACHE_BEGIN: begin
          cache_dimension<=0; cache_pack_index<=0; cache_beat<=0; cache_strobe<=0;
          cache_group<=0; encode_group<=0; encode_mask<=0;
          encoded_payload<=0; encoded_scales<=0; cache_payload_beat<=0;
          state<=CACHE_READ;
        end
        CACHE_READ: state<=CACHE_PACK;
        CACHE_PACK: begin
          if (CACHE_MODE==0) begin
            cache_beat[16*cache_pack_index+:16]<=cache_source;
            cache_strobe[2*cache_pack_index+:2]<=2'b11;
            if (cache_dimension+1==HEAD_DIM || cache_pack_index==31)
              state<=CACHE_NATIVE_REQ;
            else begin
              cache_dimension<=cache_dimension+1;
              cache_pack_index<=cache_pack_index+1'b1; state<=CACHE_READ;
            end
          end else begin
            encode_group[16*cache_dimension[4:0]+:16]<=cache_source;
            encode_mask[cache_dimension[4:0]]<=1;
            if (cache_dimension+1==HEAD_DIM || cache_dimension[4:0]==31)
              state<=CACHE_ENCODE;
            else begin cache_dimension<=cache_dimension+1; state<=CACHE_READ; end
          end
        end
        CACHE_NATIVE_REQ: if (own_request) state<=CACHE_NATIVE_WAIT;
        CACHE_NATIVE_WAIT: if (own_response) begin
          if (cache_dimension+1==HEAD_DIM) state<=CACHE_NEXT;
          else begin
            cache_dimension<=cache_dimension+1; cache_pack_index<=0;
            cache_beat<=0; cache_strobe<=0; state<=CACHE_READ;
          end
        end
        CACHE_ENCODE: if (encoder_ready) state<=CACHE_ENCODE_WAIT;
        CACHE_ENCODE_WAIT: if (encoder_valid) begin
          encoded_payload[256*cache_group+:256]<=encoder_payload;
          encoded_scales[8*cache_group+:8]<=encoder_scale;
          if (cache_dimension+1==HEAD_DIM) begin
            cache_payload_beat<=0; state<=CACHE_MX_REQ;
          end else begin
            cache_dimension<=cache_dimension+1; cache_group<=cache_group+1'b1;
            encode_group<=0; encode_mask<=0; state<=CACHE_READ;
          end
        end
        CACHE_MX_REQ: if (own_request) state<=CACHE_MX_WAIT;
        CACHE_MX_WAIT: if (own_response) begin
          if (!cache_payload_beat && HEAD_DIM>64) begin
            cache_payload_beat<=1; state<=CACHE_MX_REQ;
          end else state<=CACHE_META_REQ;
        end
        CACHE_META_REQ: if (own_request) state<=CACHE_META_WAIT;
        CACHE_META_WAIT: if (own_response) state<=CACHE_NEXT;
        CACHE_NEXT: begin
          if (!cache_value_select) begin
            cache_value_select<=1; state<=CACHE_BEGIN;
          end else if (cache_head+1<NUM_KV_HEADS) begin
            cache_head<=cache_head+1; cache_head_base<=cache_head_base+HEAD_DIM;
            cache_value_select<=0; state<=CACHE_BEGIN;
          end else begin attention_head<=0; query_base<=0; state<=ATTN_BEGIN; end
        end
        ATTN_BEGIN: begin
          query_component<=0; attention_position<=0; state<=ATTN_QUERY_READ;
        end
        ATTN_QUERY_READ: state<=ATTN_QUERY_PACK;
        ATTN_QUERY_PACK: begin
          query_buffer[16*query_component+:16]<=q_data;
          if (query_component+1==6*HEAD_DIM) state<=ATTN_CMD;
          else begin query_component<=query_component+1; state<=ATTN_QUERY_READ; end
        end
        ATTN_CMD: if (attention_cmd_ready) begin
          key_buffer<=0; value_buffer<=0; key_scales<=0; value_scales<=0;
          attention_read_kind<=0; attention_read_beat<=0; state<=ATTN_READ_REQ;
        end
        ATTN_READ_REQ: if (own_request) state<=ATTN_READ_WAIT;
        ATTN_READ_WAIT: if (own_response) begin
          if (attention_read_kind<2) begin
            if (CACHE_MODE==0) begin
              for (element=0;element<32;element=element+1)
                if (attention_payload_offset+element<HEAD_DIM) begin
                  if (attention_read_kind[0])
                    value_buffer[16*(attention_payload_offset+element)+:16]<=
                      rsp_data[16*element+:16];
                  else key_buffer[16*(attention_payload_offset+element)+:16]<=
                    rsp_data[16*element+:16];
                end
            end else begin
              for (element=0;element<64;element=element+1)
                if (attention_payload_offset+element<HEAD_DIM) begin
                  if (attention_read_kind[0])
                    value_buffer[8*(attention_payload_offset+element)+:8]<=
                      rsp_data[8*element+:8];
                  else key_buffer[8*(attention_payload_offset+element)+:8]<=
                    rsp_data[8*element+:8];
                end
            end
            if (attention_payload_offset+((CACHE_MODE==2) ? 64 : 32)<HEAD_DIM) begin
              attention_read_beat<=attention_read_beat+1'b1; state<=ATTN_READ_REQ;
            end else if (!attention_read_kind[0] || CACHE_MODE==2) begin
              attention_read_kind<=attention_read_kind+1'b1;
              attention_read_beat<=0; state<=ATTN_READ_REQ;
            end else state<=ATTN_SEND;
          end else begin
            if (attention_read_kind[0]) value_scales<=rsp_data[G*8-1:0];
            else key_scales<=rsp_data[G*8-1:0];
            if (attention_read_kind==2) begin
              attention_read_kind<=3; state<=ATTN_READ_REQ;
            end else state<=ATTN_SEND;
          end
        end
        ATTN_SEND: if (attention_kv_ready) begin
          if (attention_position==position) state<=ATTN_WAIT;
          else begin
            attention_position<=attention_position+1;
            key_buffer<=0; value_buffer<=0; key_scales<=0; value_scales<=0;
            attention_read_kind<=0; attention_read_beat<=0; state<=ATTN_READ_REQ;
          end
        end
        ATTN_WAIT: if (attention_out_valid) begin
          attention_component<=0; state<=ATTN_STORE_READ;
        end
        ATTN_STORE_READ: begin
          attention_element<=attention_out_data[32*attention_component+:32];
          state<=ATTN_STORE_WRITE;
        end
        ATTN_STORE_WRITE: begin
          if (attention_component+1==6*HEAD_DIM) begin
            if (attention_head+1<NUM_KV_HEADS) begin
              attention_head<=attention_head+1; query_base<=query_base+6*HEAD_DIM;
              state<=ATTN_BEGIN;
            end else begin projection<=3; logits_projection<=0; state<=GEMV_CMD; end
          end else begin
            attention_component<=attention_component+1; state<=ATTN_STORE_READ;
          end
        end
        ABORT_START: state<=DRAIN;
        DRAIN: if (memory_drain_done) begin
          if (cancel_pending) state<=CANCEL_FINISH;
          else state<=FINISH;
        end
        FINISH: begin active<=0; state<=IDLE; end
        CANCEL_FINISH: begin
          active<=0; cancel_pending<=0; cancelled_active<=0; state<=IDLE;
        end
        default: begin failed<=1; sequence_valid<=0; state<=ABORT_START; end
      endcase
    end
  end
endmodule
