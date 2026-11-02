module anvil_q1_fp2_top #(
  parameter NUM_LAYERS=24, HIDDEN_SIZE=896, INTERMEDIATE_SIZE=4864,
  NUM_Q_HEADS=14, NUM_KV_HEADS=2, HEAD_DIM=64, GROUP_SIZE=128,
  AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768, ENABLE_FP2=1
) (
  input wire clk, rst_n,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire done, error,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error,
  input wire [1:0] precision_mode,
  output wire ddr_req_valid,
  input wire ddr_req_ready,
  output wire ddr_req_write, ddr_req_id, ddr_req_scale,
  output wire [3:0] ddr_req_kind,
  output wire [31:0] ddr_req_layer,
  output wire [2:0] ddr_req_proj,
  output wire [31:0] ddr_req_row, ddr_req_col,
  output wire [511:0] ddr_req_wdata,
  output wire [63:0] ddr_req_wstrb,
  input wire ddr_rsp_valid,
  output wire ddr_rsp_ready,
  input wire ddr_rsp_id, ddr_rsp_error,
  input wire [511:0] ddr_rsp_rdata,
  input wire csr_req_valid,
  output wire csr_req_ready,
  input wire csr_req_write,
  input wire [11:0] csr_req_addr,
  input wire [31:0] csr_req_wdata,
  input wire [3:0] csr_req_wstrb,
  input wire csr_rsp_ready,
  output wire csr_rsp_valid,
  output wire [31:0] csr_rsp_rdata,
  output wire csr_rsp_error
);
  localparam IDLE=0, START_LEGACY=1, LEGACY=2, START_FP2=3, FP2=4;
  localparam ERROR_WAIT=5, FINISH=6;
  localparam MAX_VECTOR=INTERMEDIATE_SIZE>HIDDEN_SIZE ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
  localparam RATIO=NUM_Q_HEADS/(NUM_KV_HEADS>0 ? NUM_KV_HEADS : 1);
  localparam GROUP_HEADS=RATIO>0 ? RATIO : 1;
  reg [2:0] state;
  reg failed, sequence_valid, sequence_new;
  reg [1:0] mode, sequence_mode;
  reg [31:0] token, position, next_position;
  wire legacy_ready, legacy_logit_valid, legacy_done, legacy_error;
  wire [31:0] legacy_logit_index, legacy_logit_data;
  wire legacy_req_valid, legacy_req_write, legacy_rsp_ready;
  wire [3:0] legacy_req_kind;
  wire [31:0] legacy_req_layer, legacy_req_row, legacy_req_col, legacy_req_data;
  wire [2:0] legacy_req_proj;
  wire fp2_ready, fp2_done, fp2_error, fp2_active, operators_rst_n;
  wire fp2_logit_valid, fp2_req_valid, fp2_rsp_ready;
  wire [31:0] fp2_logit_index, fp2_logit_data;
  wire [3:0] fp2_req_kind;
  wire [31:0] fp2_req_layer, fp2_req_row, fp2_req_col;
  wire [2:0] fp2_req_proj;
  wire tensor_valid, tensor_ready, tensor_out_valid;
  wire [1023:0] tensor_a, tensor_b;
  wire [63:0] tensor_mask;
  wire [31:0] tensor_acc, tensor_result;
  wire [4:0] tensor_status;
  wire [6:0] alignment_count;
  wire ep_cmd_valid, ep_cmd_ready, ep_in_valid, ep_in_ready, ep_in_last;
  wire ep_out_valid, ep_out_ready, ep_out_last, ep_done, ep_error;
  wire [1:0] ep_cmd_op;
  wire [31:0] ep_cmd_len, ep_cmd_pos, ep_in_data, ep_in_aux, ep_in_residual, ep_out_data;
  wire [4:0] ep_status;
  wire group_cmd_valid, group_cmd_ready, query_valid, query_ready, query_last;
  wire [31:0] group_cmd_len;
  wire [15:0] query_data;
  wire kv_valid, kv_ready, kv_last;
  wire [15:0] k_data, v_data;
  wire group_out_valid, group_out_ready, group_out_last, group_done, group_error;
  wire [31:0] group_out_data, group_out_head, group_out_component;
  wire [4:0] group_status;
  wire engines_rst_n;
  wire [GROUP_HEADS-1:0] engine_cmd_valid, engine_cmd_ready;
  wire [31:0] engine_cmd_len;
  wire [GROUP_HEADS-1:0] engine_q_valid, engine_q_ready, engine_kv_valid, engine_kv_ready;
  wire [15:0] engine_q_data, engine_k_data, engine_v_data;
  wire engine_q_last, engine_kv_last;
  wire [GROUP_HEADS-1:0] engine_out_valid, engine_out_ready, engine_out_last;
  wire [32*GROUP_HEADS-1:0] engine_out_data;
  wire [5*GROUP_HEADS-1:0] engine_status;
  wire [GROUP_HEADS-1:0] engine_done, engine_error;
  wire fetch_valid, fetch_ready, fetch_write, fetch_scale;
  wire [3:0] fetch_kind;
  wire [31:0] fetch_layer, fetch_row, fetch_col, fetch_tag;
  wire [2:0] fetch_proj;
  wire [511:0] fetch_data, response_data;
  wire [63:0] fetch_strobes;
  wire response_valid, response_ready, response_write, response_error;
  wire [31:0] response_tag;
  wire work_active, result_needed, stall_event, epilogue_bubble, ulp_valid, bridge_rsp_ready;
  wire [31:0] ulp_distance;
  wire using_legacy=state==START_LEGACY || state==LEGACY;
  wire using_fp2=ENABLE_FP2!=0 && (state==START_FP2 || state==FP2);
  wire child_done=(using_legacy && legacy_done) || (using_fp2 && fp2_done);
  wire child_error=using_legacy ? legacy_error : fp2_error;
  anvil_q1_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,VOCAB_SIZE,MAX_SEQ_LEN) parameters_ok();
  generate if (ENABLE_FP2!=0 && ENABLE_FP2!=1) begin: invalid_parameters
    initial $fatal(1,"FP2 TOP PARAMETER ERROR: ENABLE_FP2 must be 0 or 1");
  end endgenerate
  assign token_ready=rst_n && state==IDLE;
  assign logit_valid=rst_n && (using_legacy ? legacy_logit_valid :
    (using_fp2 && fp2_logit_valid));
  assign logit_index=logit_valid ? (using_legacy ? legacy_logit_index : fp2_logit_index) : 32'd0;
  assign logit_data=logit_valid ? (using_legacy ? legacy_logit_data : fp2_logit_data) : 32'd0;
  assign done=rst_n && state==FINISH;
  assign error=done && failed;
  assign mem_req_valid=rst_n && (using_legacy ? legacy_req_valid :
    (using_fp2 && fp2_req_valid));
  assign mem_req_write=mem_req_valid && using_legacy && legacy_req_write;
  assign mem_req_kind=mem_req_valid ? (using_legacy ? legacy_req_kind : fp2_req_kind) : 4'd0;
  assign mem_req_layer=mem_req_valid ? (using_legacy ? legacy_req_layer : fp2_req_layer) : 32'd0;
  assign mem_req_proj=mem_req_valid ? (using_legacy ? legacy_req_proj : fp2_req_proj) : 3'd0;
  assign mem_req_row=mem_req_valid ? (using_legacy ? legacy_req_row : fp2_req_row) : 32'd0;
  assign mem_req_col=mem_req_valid ? (using_legacy ? legacy_req_col : fp2_req_col) : 32'd0;
  assign mem_req_wdata=mem_req_valid && using_legacy ? legacy_req_data : 32'd0;
  assign mem_rsp_ready=rst_n && (using_legacy ? legacy_rsp_ready :
    (using_fp2 && fp2_rsp_ready));
  assign ddr_rsp_ready=ENABLE_FP2!=0 && bridge_rsp_ready;
  anvil_q1_fp_top #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,VOCAB_SIZE,MAX_SEQ_LEN) compatibility_decoder(
    .clk(clk),.rst_n(rst_n),.token_valid(state==START_LEGACY),.token_ready(legacy_ready),
    .token_id(token),.token_pos(position),.new_sequence(sequence_new),
    .logit_valid(legacy_logit_valid),.logit_ready(logit_ready && using_legacy),
    .logit_index(legacy_logit_index),.logit_data(legacy_logit_data),
    .done(legacy_done),.error(legacy_error),.mem_req_valid(legacy_req_valid),
    .mem_req_ready(mem_req_ready && using_legacy),.mem_req_write(legacy_req_write),
    .mem_req_kind(legacy_req_kind),.mem_req_layer(legacy_req_layer),.mem_req_proj(legacy_req_proj),
    .mem_req_row(legacy_req_row),.mem_req_col(legacy_req_col),.mem_req_wdata(legacy_req_data),
    .mem_rsp_valid(mem_rsp_valid && using_legacy),.mem_rsp_ready(legacy_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error),.precision_mode(mode));
  anvil_q1_fp2_decoder_control #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)) decoder_control(
    .clk(clk),.rst_n(rst_n),.cmd_valid(ENABLE_FP2!=0 && state==START_FP2),
    .cmd_ready(fp2_ready),.cmd_format_mx(mode==3),.cmd_token(token),.cmd_pos(position),
    .done(fp2_done),.error(fp2_error),.active(fp2_active),.operators_rst_n(operators_rst_n),
    .tensor_valid(tensor_valid),.tensor_ready(tensor_ready),.tensor_a(tensor_a),.tensor_b(tensor_b),
    .tensor_mask(tensor_mask),.tensor_acc(tensor_acc),.tensor_result_valid(tensor_out_valid),
    .tensor_result(tensor_result),.tensor_status(tensor_status),
    .ep_cmd_valid(ep_cmd_valid),.ep_cmd_ready(ep_cmd_ready),.ep_cmd_op(ep_cmd_op),
    .ep_cmd_len(ep_cmd_len),.ep_cmd_pos(ep_cmd_pos),.ep_in_valid(ep_in_valid),
    .ep_in_ready(ep_in_ready),.ep_in_data(ep_in_data),.ep_in_aux(ep_in_aux),
    .ep_in_residual(ep_in_residual),.ep_in_last(ep_in_last),.ep_out_valid(ep_out_valid),
    .ep_out_ready(ep_out_ready),.ep_out_data(ep_out_data),.ep_out_last(ep_out_last),
    .ep_done(ep_done),.ep_error(ep_error),.ep_status(ep_status),
    .group_cmd_valid(group_cmd_valid),.group_cmd_ready(group_cmd_ready),.group_cmd_len(group_cmd_len),
    .query_valid(query_valid),.query_ready(query_ready),.query_data(query_data),.query_last(query_last),
    .kv_valid(kv_valid),.kv_ready(kv_ready),.k_data(k_data),.v_data(v_data),.kv_last(kv_last),
    .group_out_valid(group_out_valid),.group_out_ready(group_out_ready),
    .group_out_data(group_out_data),.group_out_head(group_out_head),
    .group_out_component(group_out_component),.group_out_last(group_out_last),
    .group_done(group_done),.group_error(group_error),.group_status(group_status),
    .logit_valid(fp2_logit_valid),.logit_ready(logit_ready && using_fp2),
    .logit_index(fp2_logit_index),.logit_data(fp2_logit_data),.mem_req_valid(fp2_req_valid),
    .mem_req_ready(mem_req_ready && using_fp2),.mem_req_kind(fp2_req_kind),
    .mem_req_layer(fp2_req_layer),.mem_req_proj(fp2_req_proj),.mem_req_row(fp2_req_row),
    .mem_req_col(fp2_req_col),.mem_rsp_valid(mem_rsp_valid && using_fp2),
    .mem_rsp_ready(fp2_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error),
    .fetch_valid(fetch_valid),.fetch_ready(fetch_ready),.fetch_write(fetch_write),
    .fetch_scale(fetch_scale),.fetch_kind(fetch_kind),.fetch_layer(fetch_layer),
    .fetch_proj(fetch_proj),.fetch_row(fetch_row),.fetch_col(fetch_col),.fetch_tag(fetch_tag),
    .fetch_data(fetch_data),.fetch_strobes(fetch_strobes),.response_valid(response_valid),
    .response_ready(response_ready),.response_tag(response_tag),.response_write(response_write),
    .response_error(response_error),.response_data(response_data),
    .work_active(work_active),.result_needed(result_needed),
    .epilogue_bubble(epilogue_bubble),.ulp_valid(ulp_valid),.ulp_distance(ulp_distance));
  anvil_q1_fp2_bfp_tensor_array tensor_array(
    .clk(clk),.rst_n(operators_rst_n),.in_valid(tensor_valid),.in_ready(tensor_ready),
    .out_ready(1'b1),.format_mx(1'b0),.a(tensor_a),.b(tensor_b),
    .a_scale(16'd0),.b_scale(16'd0),.lane_mask(tensor_mask),.acc_in(tensor_acc),
    .out_valid(tensor_out_valid),.result(tensor_result),.status(tensor_status),
    .alignment_events(alignment_count));
  anvil_q1_fp2_epilogue_fusion #(
    .MAX_VECTOR(MAX_VECTOR),.HEAD_DIM(HEAD_DIM),.MAX_POS(MAX_SEQ_LEN)) epilogue_fusion(
    .clk(clk),.rst_n(operators_rst_n),.cmd_valid(ep_cmd_valid),.cmd_ready(ep_cmd_ready),
    .cmd_op(ep_cmd_op),.cmd_len(ep_cmd_len),.cmd_pos(ep_cmd_pos),
    .in_valid(ep_in_valid),.in_ready(ep_in_ready),.in_data(ep_in_data),
    .in_aux(ep_in_aux),.in_residual(ep_in_residual),.in_last(ep_in_last),
    .out_valid(ep_out_valid),.out_ready(ep_out_ready),.out_data(ep_out_data),
    .out_last(ep_out_last),.status(ep_status),.done(ep_done),.error(ep_error));
  anvil_q1_fp2_gqa_group #(
    .GROUP_HEADS(GROUP_HEADS),.HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)) query_group(
    .clk(clk),.rst_n(operators_rst_n),.cmd_valid(group_cmd_valid),.cmd_ready(group_cmd_ready),
    .cmd_len(group_cmd_len),.query_valid(query_valid),.query_ready(query_ready),
    .query_data(query_data),.query_last(query_last),.kv_valid(kv_valid),.kv_ready(kv_ready),
    .k_data(k_data),.v_data(v_data),.kv_last(kv_last),.out_valid(group_out_valid),
    .out_ready(group_out_ready),.out_data(group_out_data),.out_head(group_out_head),
    .out_component(group_out_component),.out_last(group_out_last),.status(group_status),
    .done(group_done),.error(group_error),.engines_rst_n(engines_rst_n),
    .engine_cmd_valid(engine_cmd_valid),.engine_cmd_ready(engine_cmd_ready),
    .engine_cmd_len(engine_cmd_len),.engine_q_valid(engine_q_valid),.engine_q_ready(engine_q_ready),
    .engine_q_data(engine_q_data),.engine_q_last(engine_q_last),
    .engine_kv_valid(engine_kv_valid),.engine_kv_ready(engine_kv_ready),
    .engine_k_data(engine_k_data),.engine_v_data(engine_v_data),.engine_kv_last(engine_kv_last),
    .engine_out_valid(engine_out_valid),.engine_out_ready(engine_out_ready),
    .engine_out_data(engine_out_data),.engine_out_last(engine_out_last),
    .engine_status(engine_status),.engine_done(engine_done),.engine_error(engine_error));
  anvil_q1_fp2_flash_attn #(.HEAD_DIM(HEAD_DIM),.TILE_TOKENS(16),
    .MAX_SEQ_LEN(MAX_SEQ_LEN)) flash_attn(
    .clk(clk),.rst_n(engines_rst_n),.cmd_valid(engine_cmd_valid[0]),
    .cmd_ready(engine_cmd_ready[0]),.cmd_len(engine_cmd_len),
    .q_valid(engine_q_valid[0]),.q_ready(engine_q_ready[0]),
    .q_data(engine_q_data),.q_last(engine_q_last),
    .kv_valid(engine_kv_valid[0]),.kv_ready(engine_kv_ready[0]),
    .k_data(engine_k_data),.v_data(engine_v_data),.kv_last(engine_kv_last),
    .out_valid(engine_out_valid[0]),.out_ready(engine_out_ready[0]),
    .out_data(engine_out_data[0+:32]),.out_last(engine_out_last[0]),
    .done(engine_done[0]),.error(engine_error[0]),.status(engine_status[0+:5]));
  generate for (genvar n=1;n<GROUP_HEADS;n=n+1) begin: sibling_heads
    anvil_q1_fp2_flash_attn #(.HEAD_DIM(HEAD_DIM),.TILE_TOKENS(16),
      .MAX_SEQ_LEN(MAX_SEQ_LEN)) attention(
      .clk(clk),.rst_n(engines_rst_n),.cmd_valid(engine_cmd_valid[n]),
      .cmd_ready(engine_cmd_ready[n]),.cmd_len(engine_cmd_len),
      .q_valid(engine_q_valid[n]),.q_ready(engine_q_ready[n]),
      .q_data(engine_q_data),.q_last(engine_q_last),
      .kv_valid(engine_kv_valid[n]),.kv_ready(engine_kv_ready[n]),
      .k_data(engine_k_data),.v_data(engine_v_data),.kv_last(engine_kv_last),
      .out_valid(engine_out_valid[n]),.out_ready(engine_out_ready[n]),
      .out_data(engine_out_data[32*n+:32]),.out_last(engine_out_last[n]),
      .done(engine_done[n]),.error(engine_error[n]),.status(engine_status[5*n+:5]));
  end endgenerate
  anvil_q1_fp2_ddr_pingpong ddr_pingpong(
    .clk(clk),.rst_n(rst_n),.cmd_valid(fetch_valid && ENABLE_FP2!=0),
    .cmd_ready(fetch_ready),.cmd_write(fetch_write),.cmd_scale(fetch_scale),
    .cmd_kind(fetch_kind),.cmd_layer(fetch_layer),.cmd_proj(fetch_proj),
    .cmd_row(fetch_row),.cmd_col(fetch_col),.cmd_tag(fetch_tag),
    .cmd_wdata(fetch_data),.cmd_wstrb(fetch_strobes),
    .out_valid(response_valid),.out_ready(response_ready),.out_tag(response_tag),
    .out_write(response_write),.out_error(response_error),.out_data(response_data),
    .work_active(work_active),.result_needed(result_needed),.stall_event(stall_event),
    .ddr_req_valid(ddr_req_valid),.ddr_req_ready(ddr_req_ready && ENABLE_FP2!=0),
    .ddr_req_write(ddr_req_write),.ddr_req_id(ddr_req_id),.ddr_req_scale(ddr_req_scale),
    .ddr_req_kind(ddr_req_kind),.ddr_req_layer(ddr_req_layer),.ddr_req_proj(ddr_req_proj),
    .ddr_req_row(ddr_req_row),.ddr_req_col(ddr_req_col),.ddr_req_wdata(ddr_req_wdata),
    .ddr_req_wstrb(ddr_req_wstrb),.ddr_rsp_valid(ddr_rsp_valid && ENABLE_FP2!=0),
    .ddr_rsp_ready(bridge_rsp_ready),.ddr_rsp_id(ENABLE_FP2!=0 && ddr_rsp_id),
    .ddr_rsp_error(ddr_rsp_error),.ddr_rsp_rdata(ddr_rsp_rdata));
  anvil_q1_fp2_telemetry_csr telemetry_csr(
    .clk(clk),.rst_n(rst_n),.csr_req_valid(csr_req_valid),.csr_req_ready(csr_req_ready),
    .csr_req_write(csr_req_write),.csr_req_addr(csr_req_addr),.csr_req_wdata(csr_req_wdata),
    .csr_req_wstrb(csr_req_wstrb),.csr_rsp_valid(csr_rsp_valid),.csr_rsp_ready(csr_rsp_ready),
    .csr_rsp_rdata(csr_rsp_rdata),.csr_rsp_error(csr_rsp_error),
    .active(state!=IDLE && state!=FINISH),.error_event(done && failed),
    .fp_ddr_stall_event(stall_event),
    .alignment_events(tensor_out_valid ? alignment_count : 7'd0),
    .epilogue_bubble_event(epilogue_bubble),.ulp_valid(ulp_valid),.ulp_distance(ulp_distance));
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; sequence_valid<=0; sequence_new<=0;
      mode<=0; sequence_mode<=0; token<=0; position<=0; next_position<=0;
    end else case (state)
      IDLE: if (token_valid) begin
        token<=token_id; position<=token_pos; mode<=precision_mode; sequence_new<=new_sequence;
        failed<=0;
        if (ENABLE_FP2!=0 && (token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN ||
            (new_sequence && token_pos!=0) ||
            (!new_sequence && (!sequence_valid || token_pos!=next_position ||
              precision_mode!=sequence_mode)))) begin
          failed<=1; sequence_valid<=0; state<=ERROR_WAIT;
        end else if (ENABLE_FP2!=0 && (precision_mode==1 || precision_mode==3)) state<=START_FP2;
        else state<=START_LEGACY;
      end
      START_LEGACY: if (legacy_ready) state<=LEGACY;
      START_FP2: if (fp2_ready) state<=FP2;
      LEGACY, FP2: if (child_done) begin
        failed<=child_error; sequence_valid<=!child_error;
        if (!child_error) begin next_position<=position+1'b1; sequence_mode<=mode; end
        state<=FINISH;
      end
      ERROR_WAIT: state<=FINISH;
      FINISH: state<=IDLE;
      default: begin failed<=1; sequence_valid<=0; state<=ERROR_WAIT; end
    endcase
  end
endmodule
