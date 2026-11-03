module anvil_qn1_decoder #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2560, INTERMEDIATE_SIZE=9728,
  parameter NUM_Q_HEADS=32, NUM_KV_HEADS=8, HEAD_DIM=128,
  parameter VOCAB_SIZE=151936, MAX_SEQ_LEN=40960, GROUP_SIZE=128
) (
  input wire clk, rst_n, flush, start_valid,
  output wire start_ready,
  input wire [31:0] start_token, start_pos,
  output wire result_valid,
  input wire result_ready,
  output wire [31:0] result_argmax,
  output wire error, qk_busy, qk_blocked, score_valid,
  output wire [31:0] score_fp32,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index, logit_data,
  output wire req_valid,
  input wire req_ready,
  output wire req_write,
  output wire [3:0] req_kind,
  output wire [2:0] req_proj,
  output wire [31:0] req_layer, req_row, req_col, req_wdata, req_tag,
  input wire rsp_valid,
  output wire rsp_ready,
  input wire [31:0] rsp_data, rsp_tag,
  input wire rsp_error
);
  import anvil_qn1_pkg::*;
  localparam Q_DIM=NUM_Q_HEADS*HEAD_DIM, KV_DIM=NUM_KV_HEADS*HEAD_DIM;
  localparam MAX_INPUT=INTERMEDIATE_SIZE>Q_DIM ?
    (INTERMEDIATE_SIZE>HIDDEN_SIZE ? INTERMEDIATE_SIZE : HIDDEN_SIZE) :
    (Q_DIM>HIDDEN_SIZE ? Q_DIM : HIDDEN_SIZE);
  localparam MAX_OUTPUT=VOCAB_SIZE>MAX_INPUT ? VOCAB_SIZE : MAX_INPUT;
  localparam DS=$clog2(HEAD_DIM);
  localparam IDLE=0, EMB_READ=1, EMB_WAIT=2, EMB_WRITE=3, EMB_ACK=4;
  localparam PRE_NORM=5, PRE_WAIT=6, COEFF_READ=7, COEFF_WAIT=8;
  localparam Q_CMD=9, Q_WAIT=10, K_CMD=11, K_WAIT=12, V_CMD=13, V_WAIT=14;
  localparam FUSION_WAIT=15, QUERY_READ=16, QUERY_WAIT=17, ATT_CMD=18;
  localparam ATT_OUTPUT=19, CTX_WRITE=20, CTX_ACK=21, CTX_RETIRE=22;
  localparam O_CMD=23, O_WAIT=24, ADD1=25, ADD1_WAIT=26;
  localparam POST_NORM=27, POST_WAIT=28, MLP_CMD=29, MLP_WAIT=30;
  localparam ADD2=31, ADD2_WAIT=32, FINAL_NORM=33, FINAL_WAIT=34;
  localparam LM_CMD=35, LM_WAIT=36, RESULT=37, FAULT=38;
  reg [5:0] state;
  reg [31:0] token, position, layer, cursor, io_expected_tag;
  reg [1:0] coefficient;
  reg [5:0] attention_head;
  reg [15:0] io_data;
  reg [31:0] context_index;
  reg [HEAD_DIM*16-1:0] q_gamma, k_gamma, query;
  reg [(HEAD_DIM/2)*16-1:0] cosine, sine;
  reg [31:0] maximum_logit, argmax;
  reg error_reg;
  wire [7:0] cv, cw, cr, rv, rr, re;
  wire [31:0] ck;
  wire [23:0] cp;
  wire [255:0] cl, crow, cc, cd, ct, rd, rt;
  wire router_error;
  wire norm_error, att_error, mlp_error, residual_error, gemv_error, head_error;
  wire fused_error, projection_fault, fusion_fault;
  wire any_error=router_error || norm_error || att_error || mlp_error ||
    residual_error || gemv_error || head_error || fused_error ||
    projection_fault || fusion_fault;
  wire abort=flush || state==FAULT;
  anvil_qn1_client_router memory_router (
    .clk(clk),.rst_n(rst_n),.flush(abort),
    .client_valid(cv),.client_write(cw),.client_ready(cr),
    .client_kind(ck),.client_proj(cp),.client_layer(cl),.client_row(crow),
    .client_col(cc),.client_wdata(cd),.client_tag(ct),
    .client_rsp_valid(rv),.client_rsp_ready(rr),.client_rsp_data(rd),
    .client_rsp_tag(rt),.client_rsp_error(re),
    .req_valid(req_valid),.req_ready(req_ready),.req_write(req_write),
    .req_kind(req_kind),.req_proj(req_proj),.req_layer(req_layer),
    .req_row(req_row),.req_col(req_col),.req_wdata(req_wdata),.req_tag(req_tag),
    .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data),
    .rsp_tag(rsp_tag),.rsp_error(rsp_error),.error(router_error)
  );

  wire norm_ready, norm_done;
  wire norm_command=state==PRE_NORM || state==POST_NORM || state==FINAL_NORM;
  anvil_qn1_norm_memory #(.HIDDEN_SIZE(HIDDEN_SIZE)) normalization (
    .clk(clk),.rst_n(rst_n),.flush(abort),.start_valid(norm_command),
    .start_ready(norm_ready),.start_layer(layer),
    .start_source_slot(state==PRE_NORM ? 32'd0 : state==POST_NORM ? 32'd7 : 32'd0),
    .start_target_slot(state==PRE_NORM ? 32'd1 : state==POST_NORM ? 32'd8 : 32'd14),
    .start_gamma_kind(state==PRE_NORM ? 4'd5 : state==POST_NORM ? 4'd6 : 4'd7),
    .done(norm_done),.error(norm_error),
    .req_valid(cv[2]),.req_ready(cr[2]),.req_write(cw[2]),.req_kind(ck[8+:4]),
    .req_layer(cl[64+:32]),.req_row(crow[64+:32]),.req_col(cc[64+:32]),
    .req_wdata(cd[64+:32]),.req_tag(ct[64+:32]),
    .rsp_valid(rv[2]),.rsp_ready(rr[2]),.rsp_data(rd[64+:32]),
    .rsp_tag(rt[64+:32]),.rsp_error(re[2])
  );
  assign cp[6+:3]=0;

  wire residual_ready, residual_done;
  anvil_qn1_elementwise #(.HIDDEN_SIZE(HIDDEN_SIZE)) residuals (
    .clk(clk),.rst_n(rst_n),.flush(abort),.start_valid(state==ADD1 || state==ADD2),
    .start_ready(residual_ready),.start_a_slot(state==ADD1 ? 32'd0 : 32'd7),
    .start_b_slot(state==ADD1 ? 32'd6 : 32'd12),
    .start_target_slot(state==ADD1 ? 32'd7 : 32'd0),
    .done(residual_done),.error(residual_error),
    .req_valid(cv[5]),.req_ready(cr[5]),.req_write(cw[5]),.req_kind(ck[20+:4]),
    .req_row(crow[160+:32]),.req_col(cc[160+:32]),.req_wdata(cd[160+:32]),
    .req_tag(ct[160+:32]),.rsp_valid(rv[5]),.rsp_ready(rr[5]),
    .rsp_data(rd[160+:32]),.rsp_tag(rt[160+:32]),.rsp_error(re[5])
  );
  assign cp[15+:3]=0; assign cl[160+:32]=0;

  wire mlp_ready, mlp_done, mcommand, mcommand_ready;
  wire [2:0] mproj;
  wire [31:0] mlayer, minput, moutput, msource, mtarget;
  reg projection_done, projection_owner_mlp;
  anvil_qn1_mlp #(.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE)) mlp (
    .clk(clk),.rst_n(rst_n),.flush(abort),.start_valid(state==MLP_CMD),
    .start_ready(mlp_ready),.start_layer(layer),.done(mlp_done),.error(mlp_error),
    .gemv_valid(mcommand),.gemv_ready(mcommand_ready),.gemv_proj(mproj),
    .gemv_layer(mlayer),.gemv_input_extent(minput),.gemv_output_extent(moutput),
    .gemv_source_slot(msource),.gemv_target_slot(mtarget),
    .gemv_done(projection_done && projection_owner_mlp),.gemv_error(1'b0),
    .req_valid(cv[4]),.req_ready(cr[4]),.req_write(cw[4]),.req_kind(ck[16+:4]),
    .req_row(crow[128+:32]),.req_col(cc[128+:32]),.req_wdata(cd[128+:32]),
    .req_tag(ct[128+:32]),.rsp_valid(rv[4]),.rsp_ready(rr[4]),
    .rsp_data(rd[128+:32]),.rsp_tag(rt[128+:32]),.rsp_error(re[4])
  );
  assign cp[12+:3]=0; assign cl[128+:32]=0;

  wire attention_ready, attention_done, attention_out_valid, attention_out_ready;
  wire [31:0] attention_index;
  wire [15:0] attention_data;
  anvil_qn1_attention #(.HEAD_DIM(HEAD_DIM),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.MAX_SEQ_LEN(MAX_SEQ_LEN)) attention (
    .clk(clk),.rst_n(rst_n),.flush(abort),.start_valid(state==ATT_CMD),
    .start_ready(attention_ready),.start_layer(layer),.start_pos(position),
    .start_head(attention_head),.start_query(query),.out_valid(attention_out_valid),
    .out_ready(attention_out_ready),.out_index(attention_index),.out_data(attention_data),
    .done(attention_done),.error(att_error),.score_valid(score_valid),.score_fp32(score_fp32),
    .req_valid(cv[3]),.req_ready(cr[3]),.req_kind(ck[12+:4]),
    .req_layer(cl[96+:32]),.req_row(crow[96+:32]),.req_col(cc[96+:32]),
    .req_tag(ct[96+:32]),.rsp_valid(rv[3]),.rsp_ready(rr[3]),
    .rsp_data(rd[96+:32]),.rsp_tag(rt[96+:32]),.rsp_error(re[3])
  );
  assign cw[3]=0; assign cp[9+:3]=0; assign cd[96+:32]=0;
  assign attention_out_ready=rst_n && !abort && state==CTX_RETIRE;

  localparam G_IDLE=0, G_RUN=1, G_WRITE=2, G_ACK=3, G_KV_WRITE=4, G_KV_ACK=5, G_RETIRE=6;
  reg [2:0] gstate;
  reg [2:0] projection_id;
  reg [1:0] raw_projection;
  reg projection_lm;
  reg [31:0] projection_target, projection_layer, saved_index, projection_expected;
  reg [15:0] saved_value;
  wire main_command=state==Q_CMD || state==K_CMD || state==V_CMD ||
    state==O_CMD || state==LM_CMD;
  wire gemv_start_ready, projection_ready;
  wire head_start_ready;
  wire configuring_head=state==Q_CMD || state==K_CMD;
  wire main_ready=projection_ready && (!configuring_head || head_start_ready);
  wire command_valid=(main_command && (!configuring_head || head_start_ready)) ||
    (state==MLP_WAIT && mcommand);
  wire command_mlp=state==MLP_WAIT;
  wire command_lm=state==LM_CMD;
  wire [2:0] command_proj=command_mlp ? mproj : state==K_CMD ? 3'd1 :
    state==V_CMD ? 3'd2 : state==O_CMD ? 3'd3 : 3'd0;
  wire [31:0] command_input=command_mlp ? minput : state==O_CMD ? Q_DIM : HIDDEN_SIZE;
  wire [31:0] command_output=command_mlp ? moutput : state==Q_CMD ? Q_DIM :
    state==K_CMD || state==V_CMD ? KV_DIM : state==O_CMD ? HIDDEN_SIZE : VOCAB_SIZE;
  wire [31:0] command_source=command_mlp ? msource :
    state==O_CMD ? 32'd5 : command_lm ? 32'd14 : 32'd1;
  wire [31:0] command_target=command_mlp ? mtarget :
    state==V_CMD ? 32'd4 : state==O_CMD ? 32'd6 : 32'd0;
  assign projection_ready=rst_n && !abort && gstate==G_IDLE &&
    !projection_done && gemv_start_ready;
  assign mcommand_ready=state==MLP_WAIT && projection_ready;
  wire gemv_out_valid, gemv_out_ready, gemv_done;
  wire [31:0] gemv_index, gemv_fp32;
  wire [15:0] gemv_bf16;
  wire tv, tr, tw4, tov, tor, toe;
  wire [1023:0] tq, tz;
  wire [4095:0] ts, ta, tb;
  wire [255:0] tm;
  wire [31:0] tt, tsum, tot;
  anvil_qn1_gemv #(.GROUP_SIZE(GROUP_SIZE),.MAX_INPUT(MAX_INPUT),
      .MAX_OUTPUT(MAX_OUTPUT)) projections (
    .clk(clk),.rst_n(rst_n),.flush(abort),.start_valid(command_valid && gstate==G_IDLE &&
      !projection_done),.start_ready(gemv_start_ready),.start_w4(!command_lm),
    .start_input_extent(command_input),.start_output_extent(command_output),
    .start_layer(command_mlp ? mlayer : layer),.start_source_slot(command_source),
    .start_proj(command_proj),.out_valid(gemv_out_valid),.out_ready(gemv_out_ready),
    .out_index(gemv_index),.out_fp32(gemv_fp32),.out_bf16(gemv_bf16),
    .done(gemv_done),.error(gemv_error),.req_valid(cv[1]),.req_ready(cr[1]),
    .req_kind(ck[4+:4]),.req_layer(cl[32+:32]),.req_row(crow[32+:32]),
    .req_col(cc[32+:32]),.req_tag(ct[32+:32]),.req_proj(cp[3+:3]),
    .rsp_valid(rv[1]),.rsp_ready(rr[1]),.rsp_data(rd[32+:32]),
    .rsp_tag(rt[32+:32]),.rsp_error(re[1]),
    .tensor_valid(tv),.tensor_ready(tr),.tensor_w4(tw4),.tensor_q(tq),.tensor_z(tz),
    .tensor_scale(ts),.tensor_activation(ta),.tensor_weight(tb),.tensor_mask(tm),
    .tensor_tag(tt),.tensor_rsp_valid(tov),.tensor_rsp_ready(tor),.tensor_sum(tsum),
    .tensor_rsp_tag(tot),.tensor_error(toe)
  );
  assign cw[1]=0; assign cd[32+:32]=0;
  anvil_qn1_tensor_array tensor_array (
    .clk(clk),.rst_n(rst_n),.flush(abort),.in_valid(tv),.in_ready(tr),.in_w4(tw4),
    .q(tq),.z(tz),.scale_bf16(ts),.activation_bf16(ta),.weight_bf16(tb),
    .lane_mask(tm),.in_tag(tt),.out_valid(tov),.out_ready(tor),
    .out_sum(tsum),.out_tag(tot),.out_error(toe)
  );

  wire hb_valid, hb_ready, hb_key, hb_last, hb_input_done, hb_in_ready;
  wire [5:0] hb_head;
  wire [31:0] hb_layer, hb_pos;
  wire [HEAD_DIM*16-1:0] hb_data, hb_gamma;
  wire [(HEAD_DIM/2)*16-1:0] hb_cos, hb_sin;
  anvil_qn1_head_buffer #(.HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)) projected_heads (
    .clk(clk),.rst_n(rst_n),.flush(abort),
    .start_valid(configuring_head && projection_ready),.start_ready(head_start_ready),
    .start_is_key(state==K_CMD),.start_heads(state==K_CMD ? 6'(NUM_KV_HEADS) : 6'(NUM_Q_HEADS)),
    .start_layer(layer),.start_pos(position),.start_gamma(state==K_CMD ? k_gamma : q_gamma),
    .start_cos(cosine),.start_sin(sine),
    .in_valid(gemv_out_valid && gstate==G_RUN && raw_projection!=0),
    .in_ready(hb_in_ready),.in_index(gemv_index),.in_data(gemv_bf16),
    .head_valid(hb_valid),.head_ready(hb_ready),.head_is_key(hb_key),
    .head_index(hb_head),.head_layer(hb_layer),.head_pos(hb_pos),.head_data(hb_data),
    .head_gamma(hb_gamma),.head_cos(hb_cos),.head_sin(hb_sin),
    .head_last(hb_last),.input_done(hb_input_done),.error(head_error)
  );
  wire fused_valid, fused_ready, fused_key, fused_in_ready;
  wire [5:0] fused_head;
  wire [31:0] fused_layer, fused_pos;
  wire [HEAD_DIM*16-1:0] fused_data;
  anvil_qn1_qknorm_rope #(.HEAD_DIM(HEAD_DIM),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.NUM_LAYERS(NUM_LAYERS),
      .MAX_SEQ_LEN(MAX_SEQ_LEN)) qknorm_rope (
    .clk(clk),.rst_n(rst_n),.flush(abort),.in_valid(hb_valid),.in_ready(fused_in_ready),
    .in_is_key(hb_key),.in_head(hb_head),.in_layer(hb_layer),.in_pos(hb_pos),
    .in_data(hb_data),.in_gamma(hb_gamma),.in_cos(hb_cos),.in_sin(hb_sin),
    .out_valid(fused_valid),.out_ready(fused_ready),.out_error(fused_error),
    .out_is_key(fused_key),.out_head(fused_head),.out_layer(fused_layer),
    .out_pos(fused_pos),.out_data(fused_data)
  );
  assign hb_ready=fused_in_ready;
  localparam F_IDLE=0, F_WRITE=1, F_ACK=2, F_KV_WRITE=3, F_KV_ACK=4, F_RETIRE=5;
  reg [2:0] fstate;
  reg fused_owned, fusion_key;
  reg [5:0] fusion_head;
  reg [31:0] fusion_layer, fusion_position, fusion_cursor, fusion_expected, fused_count;
  reg [HEAD_DIM*16-1:0] fusion_data;
  assign qk_busy=rst_n && !flush && fused_owned;
  assign qk_blocked=rst_n && !flush &&
    ((hb_valid && !fused_in_ready) || (fused_valid && !fused_ready));
  assign fused_ready=rst_n && !abort && fstate==F_RETIRE;
  assign cv[7]=rst_n && !abort && (fstate==F_WRITE || fstate==F_KV_WRITE);
  assign cw[7]=cv[7]; assign ck[28+:4]=fstate==F_KV_WRITE ? 4'd9 : 4'd8;
  assign cp[21+:3]=0; assign cl[224+:32]=fstate==F_KV_WRITE ? fusion_layer : 32'd0;
  assign crow[224+:32]=fstate==F_KV_WRITE ? fusion_position :
    fusion_key ? 32'd3 : 32'd2;
  assign cc[224+:32]=({26'd0,fusion_head} << DS)+fusion_cursor;
  assign cd[224+:32]={16'd0,fusion_data[fusion_cursor*16+:16]};
  assign ct[224+:32]={fusion_cursor[26:0],fstate==F_KV_WRITE};
  assign rr[7]=rst_n && !flush;
  assign fusion_fault=rv[7] && ((fstate!=F_ACK && fstate!=F_KV_ACK) ||
    re[7] || rt[224+:32]!=fusion_expected);

  assign logit_valid=rst_n && !abort && projection_lm && gstate==G_RUN && gemv_out_valid;
  assign logit_index=logit_valid ? gemv_index : 32'd0;
  assign logit_data=logit_valid ? gemv_fp32 : 32'd0;
  assign gemv_out_ready=rst_n && !abort && (gstate==G_RETIRE ||
    (gstate==G_RUN && (projection_lm ? logit_ready : raw_projection!=0 && hb_in_ready)));
  assign cv[6]=rst_n && !abort && (gstate==G_WRITE || gstate==G_KV_WRITE);
  assign cw[6]=cv[6]; assign ck[24+:4]=gstate==G_KV_WRITE ? 4'd10 : 4'd8;
  assign cp[18+:3]=0; assign cl[192+:32]=gstate==G_KV_WRITE ? projection_layer : 32'd0;
  assign crow[192+:32]=gstate==G_KV_WRITE ? position : projection_target;
  assign cc[192+:32]=saved_index; assign cd[192+:32]={16'd0,saved_value};
  assign ct[192+:32]={saved_index[26:0],gstate==G_KV_WRITE};
  assign rr[6]=rst_n && !flush;
  assign projection_fault=rv[6] && ((gstate!=G_ACK && gstate!=G_KV_ACK) ||
    re[6] || rt[192+:32]!=projection_expected);
  wire logit_better=gemv_index==0 || fp32_greater(gemv_fp32,maximum_logit);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      gstate<=G_IDLE; projection_id<=0; raw_projection<=0; projection_lm<=0;
      projection_target<=0; projection_layer<=0; saved_index<=0; saved_value<=0;
      projection_expected<=0; projection_done<=0; projection_owner_mlp<=0;
      maximum_logit<=0; argmax<=0;
    end else if (abort) begin
      gstate<=G_IDLE; projection_done<=0; raw_projection<=0; projection_lm<=0;
    end else begin
      projection_done<=0;
      if (cv[6] && cr[6]) projection_expected<=ct[192+:32];
      if (logit_valid && logit_ready && logit_better) begin
        maximum_logit<=gemv_fp32; argmax<=gemv_index;
      end
      case (gstate)
        G_IDLE: if (command_valid && projection_ready) begin
          projection_id<=command_proj; projection_lm<=command_lm;
          projection_target<=command_target; projection_layer<=command_mlp ? mlayer : layer;
          projection_owner_mlp<=command_mlp;
          raw_projection<=state==Q_CMD ? 2'd1 : state==K_CMD ? 2'd2 : 2'd0;
          gstate<=G_RUN;
        end
        G_RUN: begin
          if (gemv_done) begin gstate<=G_IDLE; projection_done<=1; end
          else if (gemv_out_valid && !projection_lm && raw_projection==0) begin
            saved_index<=gemv_index; saved_value<=gemv_bf16; gstate<=G_WRITE;
          end
        end
        G_WRITE: if (cv[6] && cr[6]) gstate<=G_ACK;
        G_ACK: if (rv[6]) begin
          if (projection_id==2) gstate<=G_KV_WRITE;
          else gstate<=G_RETIRE;
        end
        G_KV_WRITE: if (cv[6] && cr[6]) gstate<=G_KV_ACK;
        G_KV_ACK: if (rv[6]) gstate<=G_RETIRE;
        G_RETIRE: if (gemv_out_valid && gemv_out_ready) gstate<=G_RUN;
        default: gstate<=G_IDLE;
      endcase
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      fstate<=F_IDLE; fused_owned<=0; fusion_key<=0; fusion_head<=0;
      fusion_layer<=0; fusion_position<=0; fusion_cursor<=0; fusion_expected<=0;
      fusion_data<=0; fused_count<=0;
    end else if (abort) begin fstate<=F_IDLE; fused_owned<=0; fused_count<=0; end
    else begin
      if (state==PRE_NORM && norm_ready) fused_count<=0;
      if (hb_valid && hb_ready) fused_owned<=1;
      if (cv[7] && cr[7]) fusion_expected<=ct[224+:32];
      case (fstate)
        F_IDLE: if (fused_valid) begin
          fusion_key<=fused_key; fusion_head<=fused_head; fusion_layer<=fused_layer;
          fusion_position<=fused_pos; fusion_data<=fused_data; fusion_cursor<=0;
          fstate<=F_WRITE;
        end
        F_WRITE: if (cv[7] && cr[7]) fstate<=F_ACK;
        F_ACK: if (rv[7]) begin
          if (fusion_key) fstate<=F_KV_WRITE;
          else if (fusion_cursor==HEAD_DIM-1) fstate<=F_RETIRE;
          else begin fusion_cursor<=fusion_cursor+1'b1; fstate<=F_WRITE; end
        end
        F_KV_WRITE: if (cv[7] && cr[7]) fstate<=F_KV_ACK;
        F_KV_ACK: if (rv[7]) begin
          if (fusion_cursor==HEAD_DIM-1) fstate<=F_RETIRE;
          else begin fusion_cursor<=fusion_cursor+1'b1; fstate<=F_WRITE; end
        end
        F_RETIRE: if (fused_valid && fused_ready) begin
          fstate<=F_IDLE; fused_owned<=0; fused_count<=fused_count+1'b1;
        end
        default: fstate<=F_IDLE;
      endcase
    end
  end

  wire io_read=state==EMB_READ || state==COEFF_READ || state==QUERY_READ;
  wire io_write=state==EMB_WRITE || state==CTX_WRITE;
  wire io_wait=state==EMB_WAIT || state==COEFF_WAIT || state==QUERY_WAIT ||
    state==EMB_ACK || state==CTX_ACK;
  wire io_bad=rv[0] && (!io_wait || re[0] || rt[0+:32]!=io_expected_tag ||
    ((state==EMB_WAIT || state==COEFF_WAIT || state==QUERY_WAIT) &&
      (rd[16+:16]!=0 || bf16_invalid(rd[0+:16]))));
  assign cv[0]=rst_n && !abort && !io_bad && (io_read || io_write);
  assign cw[0]=cv[0] && io_write;
  assign ck[0+:4]=state==EMB_READ ? 4'd0 : state==COEFF_READ ?
    (coefficient==0 ? 4'd12 : coefficient==1 ? 4'd13 : 4'd11) : 4'd8;
  assign cp[0+:3]=0;
  assign cl[0+:32]=state==COEFF_READ && coefficient<2 ? layer : 32'd0;
  assign crow[0+:32]=state==EMB_READ ? token : state==COEFF_READ ?
    (coefficient<2 ? 32'd0 : position) : state==QUERY_READ ? 32'd2 :
    state==CTX_WRITE ? 32'd5 : 32'd0;
  assign cc[0+:32]=state==QUERY_READ ? ({26'd0,attention_head} << DS)+cursor :
    state==CTX_WRITE ? context_index :
    state==COEFF_READ && coefficient>=2 ? (cursor << 1)+{31'd0,coefficient[0]} : cursor;
  assign cd[0+:32]=io_write ? {16'd0,io_data} : 32'd0;
  assign ct[0+:32]={22'd0,state,cursor[3:0]};
  assign rr[0]=rst_n && !flush;
  assign start_ready=rst_n && !abort && state==IDLE && !error_reg;
  assign result_valid=rst_n && !abort && state==RESULT;
  assign result_argmax=result_valid ? argmax : 32'd0;
  assign error=rst_n && !flush && (error_reg || state==FAULT || any_error || io_bad);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; token<=0; position<=0; layer<=0; cursor<=0;
      io_expected_tag<=0; coefficient<=0; attention_head<=0; io_data<=0;
      context_index<=0; q_gamma<=0; k_gamma<=0; query<=0; cosine<=0; sine<=0;
      error_reg<=0;
    end else if (flush) begin state<=IDLE; error_reg<=0; end
    else begin
      error_reg<=0;
      if (any_error || io_bad) state<=FAULT;
      else begin
        if (cv[0] && cr[0]) io_expected_tag<=ct[0+:32];
        case (state)
          IDLE: if (start_valid && start_ready) begin
            token<=start_token; position<=start_pos; layer<=0; cursor<=0;
            if (start_token>=VOCAB_SIZE || start_pos>=MAX_SEQ_LEN) state<=FAULT;
            else state<=EMB_READ;
          end
          EMB_READ: if (cv[0] && cr[0]) state<=EMB_WAIT;
          EMB_WAIT: if (rv[0]) begin io_data<=rd[0+:16]; state<=EMB_WRITE; end
          EMB_WRITE: if (cv[0] && cr[0]) state<=EMB_ACK;
          EMB_ACK: if (rv[0]) begin
            if (cursor==HIDDEN_SIZE-1) state<=PRE_NORM;
            else begin cursor<=cursor+1'b1; state<=EMB_READ; end
          end
          PRE_NORM: if (norm_ready) state<=PRE_WAIT;
          PRE_WAIT: if (norm_done) begin cursor<=0; coefficient<=0; state<=COEFF_READ; end
          COEFF_READ: if (cv[0] && cr[0]) state<=COEFF_WAIT;
          COEFF_WAIT: if (rv[0]) begin
            case (coefficient)
              0: q_gamma[cursor*16+:16]<=rd[0+:16];
              1: k_gamma[cursor*16+:16]<=rd[0+:16];
              2: cosine[cursor*16+:16]<=rd[0+:16];
              3: sine[cursor*16+:16]<=rd[0+:16];
            endcase
            if (cursor==(coefficient<2 ? HEAD_DIM-1 : HEAD_DIM/2-1)) begin
              cursor<=0;
              if (coefficient==3) state<=Q_CMD;
              else begin coefficient<=coefficient+1'b1; state<=COEFF_READ; end
            end else begin cursor<=cursor+1'b1; state<=COEFF_READ; end
          end
          Q_CMD: if (main_ready) state<=Q_WAIT;
          Q_WAIT: if (projection_done && !projection_owner_mlp) state<=K_CMD;
          K_CMD: if (main_ready) state<=K_WAIT;
          K_WAIT: if (projection_done && !projection_owner_mlp) state<=V_CMD;
          V_CMD: if (main_ready) state<=V_WAIT;
          V_WAIT: if (projection_done && !projection_owner_mlp) state<=FUSION_WAIT;
          FUSION_WAIT: if (fused_count==NUM_Q_HEADS+NUM_KV_HEADS && !fused_owned &&
              !hb_valid && fstate==F_IDLE) begin
            attention_head<=0; cursor<=0; state<=QUERY_READ;
          end
          QUERY_READ: if (cv[0] && cr[0]) state<=QUERY_WAIT;
          QUERY_WAIT: if (rv[0]) begin
            query[cursor*16+:16]<=rd[0+:16];
            if (cursor==HEAD_DIM-1) state<=ATT_CMD;
            else begin cursor<=cursor+1'b1; state<=QUERY_READ; end
          end
          ATT_CMD: if (attention_ready) state<=ATT_OUTPUT;
          ATT_OUTPUT: begin
            if (attention_out_valid) begin
              io_data<=attention_data; context_index<=attention_index; state<=CTX_WRITE;
            end else if (attention_done) begin
              if (attention_head==NUM_Q_HEADS-1) state<=O_CMD;
              else begin attention_head<=attention_head+1'b1; cursor<=0; state<=QUERY_READ; end
            end
          end
          CTX_WRITE: if (cv[0] && cr[0]) state<=CTX_ACK;
          CTX_ACK: if (rv[0]) state<=CTX_RETIRE;
          CTX_RETIRE: if (attention_out_valid && attention_out_ready) state<=ATT_OUTPUT;
          O_CMD: if (main_ready) state<=O_WAIT;
          O_WAIT: if (projection_done && !projection_owner_mlp) state<=ADD1;
          ADD1: if (residual_ready) state<=ADD1_WAIT;
          ADD1_WAIT: if (residual_done) state<=POST_NORM;
          POST_NORM: if (norm_ready) state<=POST_WAIT;
          POST_WAIT: if (norm_done) state<=MLP_CMD;
          MLP_CMD: if (mlp_ready) state<=MLP_WAIT;
          MLP_WAIT: if (mlp_done) state<=ADD2;
          ADD2: if (residual_ready) state<=ADD2_WAIT;
          ADD2_WAIT: if (residual_done) begin
            if (layer==NUM_LAYERS-1) state<=FINAL_NORM;
            else begin layer<=layer+1'b1; state<=PRE_NORM; end
          end
          FINAL_NORM: if (norm_ready) state<=FINAL_WAIT;
          FINAL_WAIT: if (norm_done) state<=LM_CMD;
          LM_CMD: if (main_ready) state<=LM_WAIT;
          LM_WAIT: if (projection_done && !projection_owner_mlp) state<=RESULT;
          RESULT: if (result_valid && result_ready) state<=IDLE;
          FAULT: begin error_reg<=1; state<=IDLE; end
          default: state<=FAULT;
        endcase
      end
    end
  end
endmodule
