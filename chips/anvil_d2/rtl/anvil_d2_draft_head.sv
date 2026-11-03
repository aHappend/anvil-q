module anvil_d2_draft_head #(
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=10944,
  parameter integer NUM_Q_HEADS=16, KV_LORA_RANK=512, QK_NOPE_HEAD_DIM=128,
  parameter integer QK_ROPE_HEAD_DIM=64, V_HEAD_DIM=128,
  parameter integer ROUTED_EXPERTS=64, TOP_K=6, SHARED_EXPERTS=2,
  parameter integer MOE_INTERMEDIATE_SIZE=1408,
  parameter integer VOCAB_SIZE=102400, MAX_SEQ_LEN=32768, TILE_K=128, TILE_ROWS=8
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_token, cmd_pos,
  input wire [2:0] cmd_head,
  input wire in_valid,
  output wire in_ready,
  input wire signed [31:0] in_hidden,
  output wire out_valid,
  input wire out_ready,
  output wire signed [31:0] out_hidden,
  output wire [31:0] out_index,
  output wire out_last,
  output wire result_valid,
  input wire result_ready,
  output wire [31:0] result_token,
  input wire commit_valid,
  output wire commit_ready,
  input wire [31:0] commit_through_pos,
  output wire commit_done,
  output wire idle, fault,
  output wire [8:0] c_req_valid, c_req_write,
  input wire [8:0] c_req_ready,
  output wire [35:0] c_req_kind,
  output wire [287:0] c_req_layer,
  output wire [26:0] c_req_proj,
  output wire [287:0] c_req_row, c_req_col, c_req_wdata,
  input wire [8:0] c_rsp_valid, c_rsp_error,
  output wire [8:0] c_rsp_ready,
  input wire [287:0] c_rsp_rdata
);
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=36 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=2048 && (HIDDEN_SIZE & 7)==0 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=11008 && (INTERMEDIATE_SIZE & 7)==0 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 && KV_LORA_RANK>=1 && KV_LORA_RANK<=512 &&
    QK_NOPE_HEAD_DIM>=1 && QK_NOPE_HEAD_DIM<=128 &&
    QK_ROPE_HEAD_DIM>=2 && QK_ROPE_HEAD_DIM<=64 && (QK_ROPE_HEAD_DIM & 1)==0 &&
    V_HEAD_DIM>=1 && V_HEAD_DIM<=128 && ROUTED_EXPERTS>=1 && ROUTED_EXPERTS<=64 &&
    TOP_K>=1 && TOP_K<=6 && TOP_K<=ROUTED_EXPERTS && SHARED_EXPERTS==2 &&
    MOE_INTERMEDIATE_SIZE>=8 && MOE_INTERMEDIATE_SIZE<=1408 &&
    (MOE_INTERMEDIATE_SIZE & 7)==0 && VOCAB_SIZE>=4 && VOCAB_SIZE<=151936 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 && TILE_K>=8 && TILE_K<=128 &&
    (TILE_K & 7)==0 && TILE_ROWS>=1 && TILE_ROWS<=8;
  generate
    if (!LEGAL) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: native draft head geometry");
      assign cmd_ready=0;
      assign in_ready=0;
      assign out_valid=0;
      assign out_hidden=0;
      assign out_index=0;
      assign out_last=0;
      assign result_valid=0;
      assign result_token=0;
      assign commit_ready=0;
      assign commit_done=0;
      assign idle=0;
      assign fault=0;
      assign c_req_valid=0;
      assign c_req_write=0;
      assign c_req_kind=0;
      assign c_req_layer=0;
      assign c_req_proj=0;
      assign c_req_row=0;
      assign c_req_col=0;
      assign c_req_wdata=0;
      assign c_rsp_ready=0;
    end else begin: native_head
      localparam IDLE=0, PROJECTION=1, INPUT_HIDDEN=2, PROJECT_CAPTURE=3;
      localparam PROJECT_WRITE=4, PROJECT_ACK=5, PROJECT_FINISH=6;
      localparam CACHE_COMMAND=7, DECODER=8, DECODER_WAIT=9;
      localparam NORMALIZE=10, NORMALIZE_WAIT=11, LOGITS=12, LOGITS_WAIT=13;
      localparam HIDDEN_READ=14, HIDDEN_RESPONSE=15, HIDDEN_PUBLISH=16;
      localparam RESULT=17, RELEASE=18, FAULTED=19;
      reg [4:0] state;
      reg armed, failed, projection_finished, last_projected, cache_owned;
      reg [2:0] head;
      reg [31:0] epoch, token, position, relative_position, component;
      reg [31:0] best_token;
      reg signed [31:0] held_hidden, best_logit;
      wire enabled=rst_n && armed && !flush;
      wire child_flush=flush || failed;
      wire projection_ready, projection_input_ready, projection_valid, projection_last;
      wire projection_done, projection_error;
      wire signed [31:0] projection_hidden;
      wire [31:0] projection_index;
      wire decoder_ready, decoder_done, decoder_error;
      wire norm_ready, norm_done, norm_error, io_ready, io_done, io_error;
      wire io_logit_valid;
      wire [31:0] io_logit_index;
      wire signed [31:0] io_logit_data;
      wire scratch_idle, cache_ready, cache_release_ready, cache_idle, cache_fault;
      wire cache_commit_ready;
      wire port_idle, memory_complete, memory_fault;
      wire [31:0] rdata;
      wire issue=enabled && !failed && port_idle &&
        (state==PROJECT_WRITE || state==HIDDEN_READ);
      wire [7:0] s_req_valid, s_req_ready, s_req_write, s_rsp_valid, s_rsp_ready, s_rsp_error;
      wire [31:0] s_req_kind;
      wire [23:0] s_req_proj;
      wire [255:0] s_req_layer, s_req_row, s_req_col, s_req_wdata, s_rsp_rdata;
      wire [7:0] x_req_valid, x_req_ready, x_req_write, x_rsp_valid, x_rsp_ready, x_rsp_error;
      wire [31:0] x_req_kind;
      wire [23:0] x_req_proj;
      wire [255:0] x_req_layer, x_req_row, x_req_col, x_req_wdata, x_rsp_rdata;
      wire cache_address=x_req_kind[4+:4]==15 && x_req_proj[3+:3]==3;
      wire cache_req_valid=x_req_valid[1] && cache_address;
      wire cache_req_ready, cache_rsp_valid, cache_rsp_ready, cache_rsp_error;
      wire [31:0] cache_rsp_data;
      wire child_fault=(projection_done && projection_error) ||
        (decoder_done && decoder_error) || (norm_done && norm_error) ||
        (io_done && io_error) || memory_fault || cache_fault;
      wire projection_transfer=enabled && state==PROJECT_CAPTURE && projection_valid;

      assign cmd_ready=enabled && !failed && state==IDLE && cache_idle &&
        scratch_idle && !commit_valid;
      assign idle=enabled && !failed && state==IDLE && cache_idle && scratch_idle;
      assign fault=enabled && failed;
      assign commit_ready=enabled && !failed && state==IDLE && cache_commit_ready;
      assign in_ready=enabled && !failed && state==INPUT_HIDDEN && projection_input_ready;
      assign out_valid=enabled && !failed && state==HIDDEN_PUBLISH;
      assign out_hidden=out_valid ? held_hidden : 32'sd0;
      assign out_index=out_valid ? component : 32'd0;
      assign out_last=out_valid && component==HIDDEN_SIZE-1;
      assign result_valid=enabled && !failed && state==RESULT;
      assign result_token=result_valid ? best_token : 32'd0;
      assign cache_rsp_ready=x_rsp_ready[1] && cache_owned;

      anvil_d2_mtp_projection #(
        .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
        .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
      ) input_projection (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),
        .cmd_valid(enabled && !failed && state==PROJECTION),.cmd_ready(projection_ready),
        .cmd_head(head),.cmd_token(token),.cmd_pos(position),
        .in_valid(enabled && !failed && state==INPUT_HIDDEN && in_valid),
        .in_ready(projection_input_ready),.in_hidden(in_hidden),
        .out_valid(projection_valid),.out_ready(enabled && !failed && state==PROJECT_CAPTURE),
        .out_hidden(projection_hidden),.out_index(projection_index),.out_last(projection_last),
        .done(projection_done),.error(projection_error),
        .c_req_valid(c_req_valid[7]),.c_req_ready(c_req_ready[7]),
        .c_req_write(c_req_write[7]),.c_req_kind(c_req_kind[28+:4]),
        .c_req_layer(c_req_layer[224+:32]),.c_req_proj(c_req_proj[21+:3]),
        .c_req_row(c_req_row[224+:32]),.c_req_col(c_req_col[224+:32]),
        .c_req_wdata(c_req_wdata[224+:32]),
        .c_rsp_valid(c_rsp_valid[7]),.c_rsp_ready(c_rsp_ready[7]),
        .c_rsp_rdata(c_rsp_rdata[224+:32]),.c_rsp_error(c_rsp_error[7])
      );
      anvil_d1_decoder_layer #(
        .NUM_LAYERS(4),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
        .NUM_Q_HEADS(NUM_Q_HEADS),.KV_LORA_RANK(KV_LORA_RANK),
        .QK_NOPE_HEAD_DIM(QK_NOPE_HEAD_DIM),.QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),
        .V_HEAD_DIM(V_HEAD_DIM),.ROUTED_EXPERTS(ROUTED_EXPERTS),.TOP_K(TOP_K),
        .SHARED_EXPERTS(SHARED_EXPERTS),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
        .FIRST_DENSE_LAYERS(0),.MAX_SEQ_LEN(MAX_SEQ_LEN),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)
      ) transformer (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),
        .cmd_valid(enabled && !failed && state==DECODER),.cmd_ready(decoder_ready),
        .cmd_epoch(epoch),.cmd_layer({29'd0,head}),.cmd_pos(relative_position),.cmd_phase(1'b1),
        .done(decoder_done),.error(decoder_error),
        .kv_read_bytes(),.kv_write_bytes(),.kv_dense_equiv_bytes(),
        .expert_dma_bytes(),.expert_dense_equiv_bytes(),
        .shared_busy_cycles(),.prefetch_busy_cycles(),.overlap_cycles(),
        .mla_complete(),.moe_complete(),
        .c_req_valid(s_req_valid[0+:5]),.c_req_ready(s_req_ready[0+:5]),
        .c_req_write(s_req_write[0+:5]),.c_req_kind(s_req_kind[0+:20]),
        .c_req_layer(s_req_layer[0+:160]),.c_req_proj(s_req_proj[0+:15]),
        .c_req_row(s_req_row[0+:160]),.c_req_col(s_req_col[0+:160]),
        .c_req_wdata(s_req_wdata[0+:160]),
        .c_rsp_valid(s_rsp_valid[0+:5]),.c_rsp_ready(s_rsp_ready[0+:5]),
        .c_rsp_rdata(s_rsp_rdata[0+:160]),.c_rsp_error(s_rsp_error[0+:5])
      );
      anvil_d1_rmsnorm #(
        .NUM_LAYERS(4),.HIDDEN_SIZE(HIDDEN_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
      ) final_normalization (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),
        .cmd_valid(enabled && !failed && state==NORMALIZE),.cmd_ready(norm_ready),
        .cmd_layer({29'd0,head}),.cmd_pos(relative_position),.cmd_mode(2'd2),
        .done(norm_done),.error(norm_error),
        .mem_req_valid(s_req_valid[5]),.mem_req_ready(s_req_ready[5]),
        .mem_req_write(s_req_write[5]),.mem_req_kind(s_req_kind[20+:4]),
        .mem_req_layer(s_req_layer[160+:32]),.mem_req_proj(s_req_proj[15+:3]),
        .mem_req_row(s_req_row[160+:32]),.mem_req_col(s_req_col[160+:32]),
        .mem_req_wdata(s_req_wdata[160+:32]),
        .mem_rsp_valid(s_rsp_valid[5]),.mem_rsp_ready(s_rsp_ready[5]),
        .mem_rsp_rdata(s_rsp_rdata[160+:32]),.mem_rsp_error(s_rsp_error[5])
      );
      anvil_d1_token_io #(
        .HIDDEN_SIZE(HIDDEN_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
      ) shared_output (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),
        .cmd_valid(enabled && !failed && state==LOGITS),.cmd_ready(io_ready),
        .cmd_project(1'b1),.cmd_token(token),.cmd_pos(relative_position),
        .done(io_done),.error(io_error),.logit_valid(io_logit_valid),
        .logit_ready(enabled && !failed && state==LOGITS_WAIT),
        .logit_index(io_logit_index),.logit_data(io_logit_data),
        .c_req_valid(s_req_valid[6]),.c_req_ready(s_req_ready[6]),
        .c_req_write(s_req_write[6]),.c_req_kind(s_req_kind[24+:4]),
        .c_req_layer(s_req_layer[192+:32]),.c_req_proj(s_req_proj[18+:3]),
        .c_req_row(s_req_row[192+:32]),.c_req_col(s_req_col[192+:32]),
        .c_req_wdata(s_req_wdata[192+:32]),
        .c_rsp_valid(s_rsp_valid[6]),.c_rsp_ready(s_rsp_ready[6]),
        .c_rsp_rdata(s_rsp_rdata[192+:32]),.c_rsp_error(s_rsp_error[6])
      );
      anvil_d1_mem_port hidden_port (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),.issue(issue),
        .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
        .write(state==PROJECT_WRITE),.kind(4'd8),.layer(32'd0),.proj(3'd0),
        .row(32'd0),.col(component),.wdata(held_hidden),.rdata(rdata),
        .c_req_valid(s_req_valid[7]),.c_req_ready(s_req_ready[7]),
        .c_req_write(s_req_write[7]),.c_req_kind(s_req_kind[28+:4]),
        .c_req_layer(s_req_layer[224+:32]),.c_req_proj(s_req_proj[21+:3]),
        .c_req_row(s_req_row[224+:32]),.c_req_col(s_req_col[224+:32]),
        .c_req_wdata(s_req_wdata[224+:32]),
        .c_rsp_valid(s_rsp_valid[7]),.c_rsp_ready(s_rsp_ready[7]),
        .c_rsp_rdata(s_rsp_rdata[224+:32]),.c_rsp_error(s_rsp_error[7])
      );
      anvil_d2_lane_memory #(
        .CLIENTS(8),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
        .NUM_Q_HEADS(NUM_Q_HEADS),.KV_LORA_RANK(KV_LORA_RANK),
        .QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),.MOE_INTERMEDIATE_SIZE(MOE_INTERMEDIATE_SIZE),
        .ROUTED_EXPERTS(ROUTED_EXPERTS)
      ) local_memory (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),.idle(scratch_idle),
        .s_req_valid(s_req_valid),.s_req_ready(s_req_ready),.s_req_write(s_req_write),
        .s_req_kind(s_req_kind),.s_req_layer(s_req_layer),.s_req_proj(s_req_proj),
        .s_req_row(s_req_row),.s_req_col(s_req_col),.s_req_wdata(s_req_wdata),
        .s_rsp_valid(s_rsp_valid),.s_rsp_ready(s_rsp_ready),.s_rsp_rdata(s_rsp_rdata),
        .s_rsp_error(s_rsp_error),
        .c_req_valid(x_req_valid),.c_req_ready(x_req_ready),.c_req_write(x_req_write),
        .c_req_kind(x_req_kind),.c_req_layer(x_req_layer),.c_req_proj(x_req_proj),
        .c_req_row(x_req_row),.c_req_col(x_req_col),.c_req_wdata(x_req_wdata),
        .c_rsp_valid(x_rsp_valid),.c_rsp_ready(x_rsp_ready),.c_rsp_rdata(x_rsp_rdata),
        .c_rsp_error(x_rsp_error)
      );
      anvil_d2_draft_cache #(
        .NUM_LAYERS(NUM_LAYERS),.KV_LORA_RANK(KV_LORA_RANK),
        .QK_ROPE_HEAD_DIM(QK_ROPE_HEAD_DIM),.MAX_SEQ_LEN(MAX_SEQ_LEN)
      ) private_cache (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),
        .cmd_valid(enabled && !failed && state==CACHE_COMMAND),.cmd_ready(cache_ready),
        .cmd_epoch(epoch),.cmd_pos(position),.cmd_head(head),
        .release_valid(enabled && !failed && state==RELEASE && scratch_idle),
        .release_ready(cache_release_ready),
        .commit_valid(enabled && !failed && state==IDLE && commit_valid),
        .commit_ready(cache_commit_ready),.commit_through_pos(commit_through_pos),
        .commit_done(commit_done),.idle(cache_idle),.fault(cache_fault),
        .s_req_valid(cache_req_valid),.s_req_ready(cache_req_ready),.s_req_write(x_req_write[1]),
        .s_req_layer(x_req_layer[32+:32]),.s_req_row(x_req_row[32+:32]),
        .s_req_col(x_req_col[32+:32]),.s_req_wdata(x_req_wdata[32+:32]),
        .s_rsp_valid(cache_rsp_valid),.s_rsp_ready(cache_rsp_ready),
        .s_rsp_rdata(cache_rsp_data),.s_rsp_error(cache_rsp_error),
        .c_req_valid(c_req_valid[8]),.c_req_ready(c_req_ready[8]),
        .c_req_write(c_req_write[8]),.c_req_kind(c_req_kind[32+:4]),
        .c_req_layer(c_req_layer[256+:32]),.c_req_proj(c_req_proj[24+:3]),
        .c_req_row(c_req_row[256+:32]),.c_req_col(c_req_col[256+:32]),
        .c_req_wdata(c_req_wdata[256+:32]),
        .c_rsp_valid(c_rsp_valid[8]),.c_rsp_ready(c_rsp_ready[8]),
        .c_rsp_rdata(c_rsp_rdata[256+:32]),.c_rsp_error(c_rsp_error[8])
      );

      for (genvar port_number=0;port_number<7;port_number=port_number+1) begin: tensor_map
        localparam integer p=port_number;
        wire [3:0] kind=x_req_kind[p*4+:4];
        wire [2:0] projection=x_req_proj[p*3+:3];
        wire [31:0] row=x_req_row[p*32+:32];
        wire gain=kind==5 || kind==6 || kind==7;
        wire native_tensor=kind==15;
        wire absorbed=native_tensor && (projection==1 || projection==2);
        wire router=native_tensor && projection==4;
        wire rotary=native_tensor && projection==6;
        wire head_tensor=gain || native_tensor;
        wire [2:0] mapped_projection=gain ? 3'd3 : absorbed ? 3'd7 :
          router || rotary || (native_tensor && projection==0) ? 3'd4 : projection;
        wire [31:0] mapped_row=gain ? {28'd0,kind}-32'd5 :
          absorbed ? {row[31:28],(projection==2),row[26:0]} :
          router ? 32'h70000000+row :
          rotary ? 32'h80000000+row+{29'd0,head}+32'd1 : row;
        assign c_req_valid[p]=x_req_valid[p] && !(p==1 && cache_address);
        assign c_req_write[p]=c_req_valid[p] && x_req_write[p];
        assign c_req_kind[p*4+:4]=!c_req_valid[p] ? 4'd0 : head_tensor ? 4'd12 : kind;
        assign c_req_layer[p*32+:32]=!c_req_valid[p] ? 32'd0 :
          head_tensor ? NUM_LAYERS+{29'd0,head} : x_req_layer[p*32+:32];
        assign c_req_proj[p*3+:3]=c_req_valid[p] ? mapped_projection : 3'd0;
        assign c_req_row[p*32+:32]=c_req_valid[p] ? mapped_row : 32'd0;
        assign c_req_col[p*32+:32]=c_req_valid[p] ? x_req_col[p*32+:32] : 32'd0;
        assign c_req_wdata[p*32+:32]=c_req_valid[p] ? x_req_wdata[p*32+:32] : 32'd0;
        assign x_req_ready[p]=p==1 && cache_address ? cache_req_ready : c_req_ready[p];
        assign x_rsp_valid[p]=p==1 && cache_owned ? cache_rsp_valid : c_rsp_valid[p];
        assign x_rsp_error[p]=p==1 && cache_owned ? cache_rsp_error : c_rsp_error[p];
        assign x_rsp_rdata[p*32+:32]=p==1 && cache_owned ? cache_rsp_data : c_rsp_rdata[p*32+:32];
        assign c_rsp_ready[p]=x_rsp_ready[p] && !(p==1 && cache_owned);
      end
      assign x_req_ready[7]=0;
      assign x_rsp_valid[7]=0;
      assign x_rsp_error[7]=0;
      assign x_rsp_rdata[224+:32]=0;

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state<=IDLE; armed<=0; failed<=0; projection_finished<=0; last_projected<=0;
          cache_owned<=0; head<=0; epoch<=0; token<=0; position<=0; relative_position<=0;
          component<=0; best_token<=0; held_hidden<=0; best_logit<=32'sh80000000;
        end else begin
          armed<=1;
          if (flush) begin
            state<=IDLE; failed<=0; projection_finished<=0; last_projected<=0;
            cache_owned<=0; component<=0;
          end else if (!failed && child_fault) begin
            state<=FAULTED; failed<=1; cache_owned<=0;
          end else begin
            if (cache_rsp_valid && cache_rsp_ready) cache_owned<=0;
            if (cache_req_valid && cache_req_ready) cache_owned<=1;
            if (projection_done) projection_finished<=1;
            if (enabled && state==LOGITS_WAIT && io_logit_valid &&
                (io_logit_index==0 || io_logit_data>best_logit ||
                 (io_logit_data==best_logit && io_logit_index<best_token))) begin
              best_token<=io_logit_index; best_logit<=io_logit_data;
            end
            case (state)
              IDLE: if (cmd_valid && cmd_ready) begin
                head<=cmd_head; epoch<=cmd_epoch; token<=cmd_token; position<=cmd_pos;
                relative_position<=cmd_pos-{29'd0,cmd_head}-32'd1;
                component<=0; projection_finished<=0; last_projected<=0;
                best_token<=0; best_logit<=32'sh80000000;
                if (cmd_head>3 || cmd_token>=VOCAB_SIZE || cmd_pos>=MAX_SEQ_LEN ||
                    cmd_pos<{29'd0,cmd_head}+32'd1) begin failed<=1; state<=FAULTED; end
                else state<=PROJECTION;
              end
              PROJECTION: if (projection_ready) state<=INPUT_HIDDEN;
              INPUT_HIDDEN: if (in_valid && in_ready) begin
                if (component==HIDDEN_SIZE-1) begin component<=0; state<=PROJECT_CAPTURE; end
                else component<=component+1'b1;
              end
              PROJECT_CAPTURE: if (projection_transfer) begin
                if (projection_index!=component ||
                    projection_last!=(component==HIDDEN_SIZE-1)) begin
                  failed<=1; state<=FAULTED;
                end else begin
                  held_hidden<=projection_hidden; last_projected<=projection_last;
                  state<=PROJECT_WRITE;
                end
              end
              PROJECT_WRITE: if (issue) state<=PROJECT_ACK;
              PROJECT_ACK: if (memory_complete) begin
                if (last_projected) state<=PROJECT_FINISH;
                else begin component<=component+1'b1; state<=PROJECT_CAPTURE; end
              end
              PROJECT_FINISH: if (projection_finished) state<=CACHE_COMMAND;
              CACHE_COMMAND: if (cache_ready) state<=DECODER;
              DECODER: if (decoder_ready) state<=DECODER_WAIT;
              DECODER_WAIT: if (decoder_done) state<=NORMALIZE;
              NORMALIZE: if (norm_ready) state<=NORMALIZE_WAIT;
              NORMALIZE_WAIT: if (norm_done) state<=LOGITS;
              LOGITS: if (io_ready) state<=LOGITS_WAIT;
              LOGITS_WAIT: if (io_done) begin component<=0; state<=HIDDEN_READ; end
              HIDDEN_READ: if (issue) state<=HIDDEN_RESPONSE;
              HIDDEN_RESPONSE: if (memory_complete) begin held_hidden<=$signed(rdata); state<=HIDDEN_PUBLISH; end
              HIDDEN_PUBLISH: if (out_valid && out_ready) begin
                if (component==HIDDEN_SIZE-1) state<=RESULT;
                else begin component<=component+1'b1; state<=HIDDEN_READ; end
              end
              RESULT: if (result_valid && result_ready) state<=RELEASE;
              RELEASE: if (scratch_idle && cache_release_ready) state<=IDLE;
              FAULTED: state<=FAULTED;
              default: begin failed<=1; state<=FAULTED; end
            endcase
          end
        end
      end
    end
  endgenerate
endmodule
