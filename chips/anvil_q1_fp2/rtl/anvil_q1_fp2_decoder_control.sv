module anvil_q1_fp2_decoder_control #(
  parameter NUM_LAYERS=24, HIDDEN_SIZE=896, INTERMEDIATE_SIZE=4864,
  NUM_Q_HEADS=14, NUM_KV_HEADS=2, HEAD_DIM=64,
  VOCAB_SIZE=151936, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, cmd_valid,
  output wire cmd_ready,
  input wire cmd_format_mx,
  input wire [31:0] cmd_token, cmd_pos,
  output wire done, error, active, operators_rst_n,
  output wire tensor_valid,
  input wire tensor_ready,
  output wire [1023:0] tensor_a, tensor_b,
  output wire [63:0] tensor_mask,
  output wire [31:0] tensor_acc,
  input wire tensor_result_valid,
  input wire [31:0] tensor_result,
  input wire [4:0] tensor_status,
  output wire ep_cmd_valid,
  input wire ep_cmd_ready,
  output wire [1:0] ep_cmd_op,
  output wire [31:0] ep_cmd_len, ep_cmd_pos,
  output wire ep_in_valid,
  input wire ep_in_ready,
  output wire [31:0] ep_in_data, ep_in_aux, ep_in_residual,
  output wire ep_in_last,
  input wire ep_out_valid,
  output wire ep_out_ready,
  input wire [31:0] ep_out_data,
  input wire ep_out_last, ep_done, ep_error,
  input wire [4:0] ep_status,
  output wire group_cmd_valid,
  input wire group_cmd_ready,
  output wire [31:0] group_cmd_len,
  output wire query_valid,
  input wire query_ready,
  output wire [15:0] query_data,
  output wire query_last,
  output wire kv_valid,
  input wire kv_ready,
  output wire [15:0] k_data, v_data,
  output wire kv_last,
  input wire group_out_valid,
  output wire group_out_ready,
  input wire [31:0] group_out_data, group_out_head, group_out_component,
  input wire group_out_last, group_done, group_error,
  input wire [4:0] group_status,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index, logit_data,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error,
  output wire fetch_valid,
  input wire fetch_ready,
  output wire fetch_write, fetch_scale,
  output wire [3:0] fetch_kind,
  output wire [31:0] fetch_layer,
  output wire [2:0] fetch_proj,
  output wire [31:0] fetch_row, fetch_col, fetch_tag,
  output wire [511:0] fetch_data,
  output wire [63:0] fetch_strobes,
  input wire response_valid,
  output wire response_ready,
  input wire [31:0] response_tag,
  input wire response_write, response_error,
  input wire [511:0] response_data,
  output wire work_active, result_needed, epilogue_bubble,
  output wire ulp_valid,
  output wire [31:0] ulp_distance
);
  localparam MAX_VECTOR=INTERMEDIATE_SIZE>HIDDEN_SIZE ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
  localparam VB=$clog2(15*MAX_VECTOR);
  localparam LB=VOCAB_SIZE>1 ? $clog2(VOCAB_SIZE) : 1;
  localparam GROUP_HEADS=NUM_Q_HEADS/(NUM_KV_HEADS>0 ? NUM_KV_HEADS : 1);
  localparam GROUP_WIDTH=GROUP_HEADS*HEAD_DIM;
  localparam KV_WIDTH=NUM_KV_HEADS*HEAD_DIM;
  localparam IDLE=0, START=1, EMBED=2, FEED_READ=3, FEED_LATCH=4;
  localparam CONFIG_REQ=5, CONFIG_RSP=6, FEED_SEND=7, WAIT_WORK=8;
  localparam GROUP_START=9, QUERY_READ=10, QUERY_LATCH=11, QUERY_SEND=12;
  localparam KV_START=13, ATTEND=14, ADVANCE=15, LOGIT_READ=16;
  localparam LOGIT_LATCH=17, LOGIT_SEND=18, COMPLETE_WAIT=19;
  localparam ERROR_WAIT0=20, ERROR_WAIT1=21, FINISH=22;
  reg [4:0] state, step;
  reg failed, format_mx, group_finished, reader_finished, group_failed;
  reg [31:0] token, position, layer, index, received, group_head, query_component;
  reg [31:0] x_value, aux_value, residual_value, coefficient, logit_payload;
  reg [4:0] flags;
  reg [3:0] source_slot, target_slot, auxiliary_slot, residual_slot;
  reg [31:0] length, projection_outputs;
  reg [2:0] projection;
  reg [1:0] operation;
  reg [3:0] config_kind;
  reg is_projection, is_epilogue, is_writer;
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] vectors [0:15*MAX_VECTOR-1];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] logits [0:VOCAB_SIZE-1];
  reg [31:0] vector_q, auxiliary_q, residual_q, logit_q;
  wire [31:0] vector_index=(state==QUERY_READ || state==QUERY_LATCH ||
    state==QUERY_SEND) ? group_head*GROUP_WIDTH+index : index;
  wire [31:0] source_address=source_slot*MAX_VECTOR+vector_index;
  wire [31:0] auxiliary_address=auxiliary_slot*MAX_VECTOR+index;
  wire [31:0] residual_address=residual_slot*MAX_VECTOR+index;
  wire feed_last=index+1==length;
  wire need_config=is_epilogue && (operation==0 || operation==1);
  wire [31:0] rope_column=query_component<HEAD_DIM/2 ?
    query_component*2 : (query_component-HEAD_DIM/2)*2+1;
  wire [20:0] converted_query=anvil_q1_fp2_pkg::fp32_to_bf16(x_value);
  wire [31:0] query_roundtrip={converted_query[15:0],16'd0};
  wire [31:0] ordered_query=x_value[31] ? ~x_value : x_value ^ 32'h80000000;
  wire [31:0] ordered_roundtrip=query_roundtrip[31] ?
    ~query_roundtrip : query_roundtrip ^ 32'h80000000;
  wire [31:0] query_distance=x_value[30:23]==255 || query_roundtrip[30:23]==255 ?
    32'hffffffff : (ordered_query>ordered_roundtrip ?
      ordered_query-ordered_roundtrip : ordered_roundtrip-ordered_query);
  wire [3:0] client_valid, client_ready, client_scale, client_response_ready;
  wire [3:0] client_work, client_needed;
  wire [15:0] client_kind;
  wire [127:0] client_layer, client_row, client_col, client_tag;
  wire [11:0] client_proj;
  wire [1:0] selected=step==0 ? 2'd0 : (step==9 ? 2'd3 :
    (is_writer ? 2'd2 : 2'd1));
  wire embed_ready, embed_valid, embed_last, embed_done, embed_error;
  wire [15:0] embed_data;
  wire [4:0] embed_status;
  wire projection_ready, projection_in_ready, projection_valid, projection_last;
  wire projection_done, projection_error, projection_ulp;
  wire [31:0] projection_data, projection_index, projection_distance;
  wire [4:0] projection_status;
  wire bias_valid, bias_ready, bias_response_ready;
  wire [31:0] bias_layer, bias_col;
  wire [2:0] bias_proj;
  wire writer_ready, writer_in_ready, writer_done, writer_error, writer_ulp;
  wire [4:0] writer_status;
  wire [31:0] writer_distance;
  wire [511:0] writer_data;
  wire [63:0] writer_strobes;
  wire kvreader_ready, kvreader_valid, kvreader_last, kvreader_done, kvreader_error;
  wire [15:0] key, value;
  wire [4:0] kvreader_status;
  wire feed_ready=is_projection ? projection_in_ready :
    (is_writer ? writer_in_ready : ep_in_ready);
  wire feed_transfer=state==FEED_SEND && feed_ready;
  wire ep_transfer=ep_out_valid && ep_out_ready;
  wire projection_transfer=projection_valid && is_projection && state==WAIT_WORK;
  wire group_transfer=group_out_valid && group_out_ready;
  wire operand_failure=(ep_done && is_epilogue && (ep_error || (|ep_status[4:2]))) ||
    (projection_done && is_projection && projection_error) ||
    (writer_done && is_writer && writer_error);
  wire output_frame_failure=(ep_transfer && ep_out_last!=(received+1==length)) ||
    (projection_transfer && (projection_index!=received ||
      projection_last!=(received+1==projection_outputs))) ||
    (group_transfer && (group_out_head>=GROUP_HEADS ||
      group_out_component>=HEAD_DIM ||
      group_out_last!=(group_out_head+1==GROUP_HEADS && group_out_component+1==HEAD_DIM)));
  assign cmd_ready=rst_n && state==IDLE;
  assign done=rst_n && state==FINISH;
  assign error=done && failed;
  assign active=rst_n && state!=IDLE && state!=FINISH;
  assign operators_rst_n=rst_n && state!=ERROR_WAIT0 && state!=ERROR_WAIT1 &&
    !(state==FINISH && failed);
  assign ep_cmd_valid=operators_rst_n && state==START && is_epilogue;
  assign ep_cmd_op=ep_cmd_valid ? operation : 2'd0;
  assign ep_cmd_len=ep_cmd_valid ? length : 32'd0;
  assign ep_cmd_pos=ep_cmd_valid ? position : 32'd0;
  assign ep_in_valid=operators_rst_n && is_epilogue && state==FEED_SEND;
  assign ep_in_data=ep_in_valid ? x_value : 32'd0;
  assign ep_in_aux=ep_in_valid ? (need_config ? coefficient : aux_value) : 32'd0;
  assign ep_in_residual=ep_in_valid ? residual_value : 32'd0;
  assign ep_in_last=ep_in_valid && feed_last;
  assign ep_out_ready=operators_rst_n && is_epilogue && state==WAIT_WORK;
  assign epilogue_bubble=operators_rst_n && is_epilogue && ep_in_ready &&
    (state==FEED_READ || state==FEED_LATCH || state==CONFIG_REQ || state==CONFIG_RSP);
  assign group_cmd_valid=operators_rst_n && state==GROUP_START;
  assign group_cmd_len=group_cmd_valid ? position+1 : 32'd0;
  assign query_valid=operators_rst_n && state==QUERY_SEND &&
    !(|converted_query[20:18]) && x_value[30:23]!=255;
  assign query_data=query_valid ? converted_query[15:0] : 16'd0;
  assign query_last=query_valid && query_component+1==HEAD_DIM;
  assign kv_valid=operators_rst_n && state==ATTEND && kvreader_valid && !group_failed;
  assign k_data=kv_valid ? key : 16'd0;
  assign v_data=kv_valid ? value : 16'd0;
  assign kv_last=kv_valid && kvreader_last;
  assign group_out_ready=operators_rst_n && state==ATTEND && !group_failed;
  assign logit_valid=rst_n && state==LOGIT_SEND;
  assign logit_index=logit_valid ? index : 32'd0;
  assign logit_data=logit_valid ? logit_payload : 32'd0;
  assign mem_req_valid=operators_rst_n &&
    ((is_projection && bias_valid) || state==CONFIG_REQ);
  assign mem_req_kind=mem_req_valid ? (is_projection ? 4'd4 : config_kind) : 4'd0;
  assign mem_req_layer=mem_req_valid ? (is_projection ? bias_layer :
    (config_kind==7 || config_kind==11 ? 32'd0 : layer)) : 32'd0;
  assign mem_req_proj=mem_req_valid && is_projection ? bias_proj : 3'd0;
  assign mem_req_row=mem_req_valid && config_kind==11 && !is_projection ? position : 32'd0;
  assign mem_req_col=mem_req_valid ? (is_projection ? bias_col :
    (config_kind==11 ? rope_column : index)) : 32'd0;
  assign mem_rsp_ready=operators_rst_n &&
    (is_projection ? bias_response_ready : state==CONFIG_RSP);
  assign bias_ready=is_projection && mem_req_ready;
  assign fetch_valid=operators_rst_n && client_valid[selected];
  assign fetch_write=fetch_valid && selected==2;
  assign fetch_scale=fetch_valid && client_scale[selected];
  assign fetch_kind=fetch_valid ? client_kind[4*selected+:4] : 4'd0;
  assign fetch_layer=fetch_valid ? client_layer[32*selected+:32] : 32'd0;
  assign fetch_proj=fetch_valid ? client_proj[3*selected+:3] : 3'd0;
  assign fetch_row=fetch_valid ? client_row[32*selected+:32] : 32'd0;
  assign fetch_col=fetch_valid ? client_col[32*selected+:32] : 32'd0;
  assign fetch_tag=fetch_valid ? client_tag[32*selected+:32] : 32'd0;
  assign fetch_data=fetch_write ? writer_data : 512'd0;
  assign fetch_strobes=fetch_write ? writer_strobes : 64'd0;
  assign response_ready=operators_rst_n && client_response_ready[selected];
  assign work_active=operators_rst_n && client_work[selected];
  assign result_needed=operators_rst_n && client_needed[selected];
  assign ulp_valid=projection_ulp || writer_ulp || (query_valid && query_ready);
  assign ulp_distance=projection_ulp ? projection_distance :
    (writer_ulp ? writer_distance : (query_valid && query_ready ? query_distance : 32'd0));
  generate for (genvar n=0;n<4;n=n+1) begin: route
    assign client_ready[n]=operators_rst_n && selected==n && fetch_ready;
  end endgenerate
  assign client_proj[0+:3]=0;
  assign client_proj[6+:3]=0;
  anvil_q1_fp2_ddr_read_stream embedding_reader(
    .clk(clk),.rst_n(operators_rst_n),.cmd_valid(state==START && step==0),
    .cmd_ready(embed_ready),.cmd_format_mx(format_mx),.cmd_kind(4'd0),
    .cmd_layer(32'd0),.cmd_proj(3'd0),.cmd_row(token),.cmd_first(32'd0),
    .cmd_len(32'(HIDDEN_SIZE)),.out_valid(embed_valid),.out_ready(state==EMBED),
    .out_data(embed_data),.out_last(embed_last),.status(embed_status),
    .done(embed_done),.error(embed_error),.work_active(client_work[0]),
    .result_needed(client_needed[0]),.fetch_valid(client_valid[0]),
    .fetch_ready(client_ready[0]),.fetch_scale(client_scale[0]),
    .fetch_kind(client_kind[0+:4]),.fetch_layer(client_layer[0+:32]),
    .fetch_proj(),.fetch_row(client_row[0+:32]),.fetch_col(client_col[0+:32]),
    .fetch_tag(client_tag[0+:32]),.response_valid(response_valid && selected==0),
    .response_ready(client_response_ready[0]),.response_tag(response_tag),
    .response_write(response_write),.response_error(response_error),.response_data(response_data));
  anvil_q1_fp2_projection #(.MAX_INPUT(MAX_VECTOR),
    .MAX_OUTPUT(VOCAB_SIZE>MAX_VECTOR ? VOCAB_SIZE : MAX_VECTOR)) projection_engine(
    .clk(clk),.rst_n(operators_rst_n),.cmd_valid(state==START && is_projection),
    .cmd_ready(projection_ready),.cmd_format_mx(format_mx),.cmd_head(step==19),
    .cmd_layer(layer),.cmd_inputs(length),.cmd_outputs(projection_outputs),.cmd_proj(projection),
    .in_valid(state==FEED_SEND && is_projection),.in_ready(projection_in_ready),
    .in_data(x_value),.in_last(feed_last),.out_valid(projection_valid),
    .out_ready(state==WAIT_WORK && is_projection),.out_data(projection_data),
    .out_index(projection_index),.out_last(projection_last),
    .done(projection_done),.error(projection_error),.status(projection_status),
    .ulp_valid(projection_ulp),.ulp_distance(projection_distance),
    .tensor_valid(tensor_valid),.tensor_ready(tensor_ready),.tensor_a(tensor_a),
    .tensor_b(tensor_b),.tensor_mask(tensor_mask),.tensor_acc(tensor_acc),
    .tensor_result_valid(tensor_result_valid),.tensor_result(tensor_result),
    .tensor_status(tensor_status),.fetch_valid(client_valid[1]),
    .fetch_ready(client_ready[1]),.fetch_scale(client_scale[1]),
    .fetch_kind(client_kind[4+:4]),.fetch_layer(client_layer[32+:32]),
    .fetch_proj(client_proj[3+:3]),.fetch_row(client_row[32+:32]),
    .fetch_col(client_col[32+:32]),.fetch_tag(client_tag[32+:32]),
    .response_valid(response_valid && selected==1),.response_ready(client_response_ready[1]),
    .response_tag(response_tag),.response_write(response_write),
    .response_error(response_error),.response_data(response_data),
    .work_active(client_work[1]),.result_needed(client_needed[1]),
    .bias_req_valid(bias_valid),.bias_req_ready(bias_ready),.bias_layer(bias_layer),
    .bias_col(bias_col),.bias_proj(bias_proj),
    .bias_rsp_valid(mem_rsp_valid && is_projection),
    .bias_rsp_ready(bias_response_ready),.bias_rsp_data(mem_rsp_rdata),
    .bias_rsp_error(mem_rsp_error));
  anvil_q1_fp2_kv_writer #(.MAX_VECTOR(KV_WIDTH)) kv_writer(
    .clk(clk),.rst_n(operators_rst_n),.cmd_valid(state==START && is_writer),
    .cmd_ready(writer_ready),.cmd_format_mx(format_mx),
    .cmd_kind(step==7 ? 4'd9 : 4'd10),.cmd_layer(layer),.cmd_row(position),
    .cmd_len(32'(KV_WIDTH)),.in_valid(state==FEED_SEND && is_writer),
    .in_ready(writer_in_ready),.in_data(x_value),.in_last(feed_last),
    .done(writer_done),.error(writer_error),.status(writer_status),
    .ulp_valid(writer_ulp),.ulp_distance(writer_distance),
    .fetch_valid(client_valid[2]),.fetch_ready(client_ready[2]),
    .fetch_scale(client_scale[2]),.fetch_kind(client_kind[8+:4]),
    .fetch_layer(client_layer[64+:32]),.fetch_row(client_row[64+:32]),
    .fetch_col(client_col[64+:32]),.fetch_tag(client_tag[64+:32]),
    .fetch_data(writer_data),.fetch_strobes(writer_strobes),
    .response_valid(response_valid && selected==2),.response_ready(client_response_ready[2]),
    .response_tag(response_tag),.response_write(response_write),.response_error(response_error),
    .work_active(client_work[2]),.result_needed(client_needed[2]));
  anvil_q1_fp2_kv_reader #(.HEAD_DIM(HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)) kv_reader(
    .clk(clk),.rst_n(operators_rst_n),.cmd_valid(state==KV_START),
    .cmd_ready(kvreader_ready),.cmd_format_mx(format_mx),
    .cmd_layer(layer),.cmd_first(group_head*HEAD_DIM),.cmd_len(position+1),
    .kv_valid(kvreader_valid),.kv_ready(state==ATTEND && (group_failed || kv_ready)),
    .k_data(key),.v_data(value),.kv_last(kvreader_last),.status(kvreader_status),
    .done(kvreader_done),.error(kvreader_error),
    .work_active(client_work[3]),.result_needed(client_needed[3]),
    .fetch_valid(client_valid[3]),.fetch_ready(client_ready[3]),
    .fetch_scale(client_scale[3]),.fetch_kind(client_kind[12+:4]),
    .fetch_layer(client_layer[96+:32]),.fetch_proj(client_proj[9+:3]),
    .fetch_row(client_row[96+:32]),.fetch_col(client_col[96+:32]),
    .fetch_tag(client_tag[96+:32]),.response_valid(response_valid && selected==3),
    .response_ready(client_response_ready[3]),.response_tag(response_tag),
    .response_write(response_write),.response_error(response_error),.response_data(response_data));
  always @* begin
    source_slot=0; target_slot=0; auxiliary_slot=0; residual_slot=0;
    length=HIDDEN_SIZE; projection_outputs=HIDDEN_SIZE; projection=0;
    operation=0; config_kind=0; is_projection=0; is_epilogue=0; is_writer=0;
    case (step)
      1: begin is_epilogue=1; source_slot=0; target_slot=1; config_kind=5; end
      2: begin is_projection=1; projection=0; source_slot=1; target_slot=2; end
      3: begin
        is_projection=1; projection=1; source_slot=1; target_slot=3;
        projection_outputs=KV_WIDTH;
      end
      4: begin
        is_projection=1; projection=2; source_slot=1; target_slot=4;
        projection_outputs=KV_WIDTH;
      end
      5: begin
        is_epilogue=1; operation=1; source_slot=2; target_slot=2; config_kind=11;
      end
      6: begin
        is_epilogue=1; operation=1; source_slot=3; target_slot=3;
        length=KV_WIDTH; config_kind=11;
      end
      7: begin is_writer=1; source_slot=3; length=KV_WIDTH; end
      8: begin is_writer=1; source_slot=4; length=KV_WIDTH; end
      9: begin source_slot=2; target_slot=5; end
      10: begin is_projection=1; projection=3; source_slot=5; target_slot=6; end
      11: begin
        is_epilogue=1; operation=3; source_slot=6; residual_slot=0; target_slot=7;
      end
      12: begin is_epilogue=1; source_slot=7; target_slot=8; config_kind=6; end
      13: begin
        is_projection=1; projection=4; source_slot=8; target_slot=9;
        projection_outputs=INTERMEDIATE_SIZE;
      end
      14: begin
        is_projection=1; projection=5; source_slot=8; target_slot=10;
        projection_outputs=INTERMEDIATE_SIZE;
      end
      15: begin
        is_epilogue=1; operation=2; source_slot=9; auxiliary_slot=10;
        target_slot=11; length=INTERMEDIATE_SIZE;
      end
      16: begin
        is_projection=1; projection=6; source_slot=11; target_slot=12;
        length=INTERMEDIATE_SIZE;
      end
      17: begin
        is_epilogue=1; operation=3; source_slot=12; residual_slot=7; target_slot=0;
      end
      18: begin is_epilogue=1; source_slot=0; target_slot=14; config_kind=7; end
      19: begin
        is_projection=1; source_slot=14; projection_outputs=VOCAB_SIZE;
      end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    vector_q<=vectors[source_address[VB-1:0]];
    auxiliary_q<=vectors[auxiliary_address[VB-1:0]];
    residual_q<=vectors[residual_address[VB-1:0]];
    logit_q<=logits[index[LB-1:0]];
    if (operators_rst_n && state==EMBED && embed_valid)
      vectors[received[VB-1:0]]<={embed_data,16'd0};
    if (ep_transfer) vectors[VB'(target_slot*MAX_VECTOR+received)]<=ep_out_data;
    if (projection_transfer && step!=19)
      vectors[VB'(target_slot*MAX_VECTOR+projection_index)]<=projection_data;
    if (projection_transfer && step==19) logits[projection_index[LB-1:0]]<=projection_data;
    if (group_transfer)
      vectors[VB'(5*MAX_VECTOR+group_head*GROUP_WIDTH+
        group_out_head*HEAD_DIM+group_out_component)]<=group_out_data;
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=IDLE; step<=0; failed<=0; format_mx<=0; group_finished<=0;
      reader_finished<=0; group_failed<=0; token<=0; position<=0; layer<=0;
      index<=0; received<=0; group_head<=0; query_component<=0;
      x_value<=0; aux_value<=0; residual_value<=0; coefficient<=0; logit_payload<=0; flags<=0;
    end else if (operand_failure || output_frame_failure) begin
      failed<=1; state<=ERROR_WAIT0;
    end else if (step==0 && embed_done && embed_error) begin
      failed<=1; flags<=flags | embed_status; state<=ERROR_WAIT0;
    end else if (step==9 && kvreader_done && kvreader_error) begin
      failed<=1; flags<=flags | kvreader_status; state<=ERROR_WAIT0;
    end else begin
      if (ep_transfer) begin
        received<=received+1'b1; flags<=flags | ep_status;
      end
      if (projection_transfer) begin
        received<=received+1'b1; flags<=flags | projection_status;
      end
      case (state)
        IDLE: if (cmd_valid) begin
          token<=cmd_token; position<=cmd_pos; format_mx<=cmd_format_mx;
          layer<=0; step<=0; index<=0; received<=0; group_head<=0;
          failed<=0; flags<=0; group_failed<=0; group_finished<=0; reader_finished<=0;
          if (cmd_token>=VOCAB_SIZE || cmd_pos>=MAX_SEQ_LEN) begin
            failed<=1; state<=ERROR_WAIT0;
          end else state<=START;
        end
        START: begin
          index<=0; received<=0; query_component<=0;
          if (step==0 && embed_ready) state<=EMBED;
          else if ((is_projection && projection_ready) ||
              (is_epilogue && ep_cmd_ready) || (is_writer && writer_ready))
            state<=FEED_READ;
        end
        EMBED: begin
          if (embed_valid) begin received<=received+1'b1; flags<=flags | embed_status; end
          if (embed_done) begin
            if (received!=HIDDEN_SIZE) begin failed<=1; state<=ERROR_WAIT0; end
            else state<=ADVANCE;
          end
        end
        FEED_READ: state<=FEED_LATCH;
        FEED_LATCH: begin
          x_value<=vector_q; aux_value<=auxiliary_q; residual_value<=residual_q;
          if (need_config) state<=CONFIG_REQ; else state<=FEED_SEND;
        end
        CONFIG_REQ: if (mem_req_ready) state<=CONFIG_RSP;
        CONFIG_RSP: if (mem_rsp_valid) begin
          if (mem_rsp_error ||
              (config_kind!=11 && (mem_rsp_rdata[31:16]!=0 || mem_rsp_rdata[14:7]==255)) ||
              (config_kind==11 && mem_rsp_rdata[30:23]==255)) begin
            failed<=1; state<=ERROR_WAIT0;
          end else begin
            coefficient<=config_kind==11 ? mem_rsp_rdata : {mem_rsp_rdata[15:0],16'd0};
            state<=FEED_SEND;
          end
        end
        FEED_SEND: if (feed_transfer) begin
          if (feed_last) state<=WAIT_WORK;
          else begin
            index<=index+1'b1;
            if (query_component+1==HEAD_DIM) query_component<=0;
            else query_component<=query_component+1'b1;
            state<=FEED_READ;
          end
        end
        WAIT_WORK: if ((is_epilogue && ep_done) ||
            (is_projection && projection_done) || (is_writer && writer_done)) begin
          if ((is_epilogue && received!=length) ||
              (is_projection && received!=projection_outputs)) begin
            failed<=1; state<=ERROR_WAIT0;
          end else state<=ADVANCE;
        end
        GROUP_START: if (group_cmd_ready) begin
          index<=0; query_component<=0; group_finished<=0; reader_finished<=0;
          group_failed<=0; state<=QUERY_READ;
        end
        QUERY_READ: state<=QUERY_LATCH;
        QUERY_LATCH: begin x_value<=vector_q; state<=QUERY_SEND; end
        QUERY_SEND: begin
          if ((|converted_query[20:18]) || x_value[30:23]==255) begin
            failed<=1; state<=ERROR_WAIT0;
          end else if (query_ready) begin
            flags<=flags | converted_query[20:16];
            if (index+1==GROUP_WIDTH) state<=KV_START;
            else begin
              index<=index+1'b1;
              if (query_component+1==HEAD_DIM) query_component<=0;
              else query_component<=query_component+1'b1;
              state<=QUERY_READ;
            end
          end
        end
        KV_START: if (kvreader_ready) state<=ATTEND;
        ATTEND: begin
          if (kvreader_done) begin reader_finished<=1; flags<=flags | kvreader_status; end
          if (group_done) begin
            group_finished<=1; group_failed<=group_error; flags<=flags | group_status;
          end
          if ((reader_finished || kvreader_done) && (group_finished || group_done)) begin
            if (group_failed || (group_done && group_error)) begin
              failed<=1; state<=ERROR_WAIT0;
            end else if (group_head+1==NUM_KV_HEADS) state<=ADVANCE;
            else begin group_head<=group_head+1'b1; state<=GROUP_START; end
          end
        end
        ADVANCE: begin
          index<=0; received<=0;
          if (step==8) begin step<=9; group_head<=0; state<=GROUP_START; end
          else if (step==17) begin
            if (layer+1<NUM_LAYERS) begin layer<=layer+1'b1; step<=1; state<=START; end
            else begin step<=18; state<=START; end
          end else if (step==19) state<=LOGIT_READ;
          else begin step<=step+1'b1; state<=START; end
        end
        LOGIT_READ: state<=LOGIT_LATCH;
        LOGIT_LATCH: begin logit_payload<=logit_q; state<=LOGIT_SEND; end
        LOGIT_SEND: if (logit_ready) begin
          if (index+1==VOCAB_SIZE) state<=COMPLETE_WAIT;
          else begin index<=index+1'b1; state<=LOGIT_READ; end
        end
        COMPLETE_WAIT: state<=FINISH;
        ERROR_WAIT0: state<=ERROR_WAIT1;
        ERROR_WAIT1: state<=FINISH;
        FINISH: state<=IDLE;
        default: begin failed<=1; state<=ERROR_WAIT0; end
      endcase
    end
  end
endmodule
