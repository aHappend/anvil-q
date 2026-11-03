module anvil_q4_parent_compat (
  input wire clk, rst_n, flush, invalidate, cmd_valid,
  output wire cmd_ready,
  input wire [1023:0] descriptor,
  input wire [31:0] cmd_token, cmd_pos,
  input wire cmd_phase, cmd_new_sequence,
  output wire done, error, logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index, logit_data,
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
  input wire mem_rsp_error
);
  localparam [2:0] IDLE=0, INVALIDATE=1, START=2, WAIT=3, COMPLETE=4;
  reg [2:0] state;
  reg [4:0] phase;
  reg [31:0] token, position, layer;
  reg token_phase, new_sequence, failed;
  wire [31:0] mode=descriptor[32+:32], layers=descriptor[7*32+:32];
  wire [31:0] hidden=descriptor[8*32+:32], intermediate=descriptor[9*32+:32];
  wire [31:0] qheads=descriptor[10*32+:32], kvheads=descriptor[11*32+:32];
  wire [31:0] dimension=descriptor[12*32+:32], capacity=descriptor[14*32+:32];
  wire [31:0] cache_encoding=descriptor[5*32+:32];
  wire [31:0] cache_mode=cache_encoding>=2 ? 32'd2 : cache_encoding;
  wire child_flush=flush || failed;
  wire cache_invalidate=invalidate || state==INVALIDATE;
  wire [2:0] owner=phase==0 || phase==16 ? 3'd0 :
    phase==1 || phase==9 || phase==15 ? 3'd1 :
    phase==5 ? 3'd3 : phase==6 ? 3'd4 :
    phase==8 || phase==12 || phase==14 ? 3'd5 : 3'd2;
  wire [2:0] projection=phase==3 ? 3'd1 : phase==4 ? 3'd2 :
    phase==7 ? 3'd3 : phase==10 ? 3'd4 : phase==11 ? 3'd5 : phase==13 ? 3'd6 : 3'd0;
  wire [5:0] ready, completed, faulted;
  wire [5:0] start=rst_n && !child_flush && state==START ? 6'd1 << owner : 6'd0;
  wire [6:0] req_valid, req_ready, req_write, rsp_valid, rsp_ready;
  wire [27:0] req_kind;
  wire [20:0] req_proj;
  wire [223:0] req_layer, req_row, req_col, req_data;

  anvil_q3_parent_token_io token_io (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),.cmd_valid(start[0]),.cmd_ready(ready[0]),
    .HIDDEN_SIZE(hidden),.VOCAB_SIZE(descriptor[13*32+:32]),.MAX_SEQ_LEN(capacity),
    .cmd_project(phase==16),.cmd_token(token),.cmd_pos(position),
    .done(completed[0]),.error(faulted[0]),.logit_valid(logit_valid),
    .logit_ready(logit_ready),.logit_index(logit_index),.logit_data(logit_data),
    .mem_req_valid(req_valid[0]),.mem_req_ready(req_ready[0]),.mem_req_write(req_write[0]),
    .mem_req_kind(req_kind[0+:4]),.mem_req_layer(req_layer[0+:32]),
    .mem_req_proj(req_proj[0+:3]),.mem_req_row(req_row[0+:32]),
    .mem_req_col(req_col[0+:32]),.mem_req_wdata(req_data[0+:32]),
    .mem_rsp_valid(rsp_valid[0]),.mem_rsp_ready(rsp_ready[0]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q3_parent_rmsnorm norm (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),.cmd_valid(start[1]),.cmd_ready(ready[1]),
    .NUM_LAYERS(layers),.HIDDEN_SIZE(hidden),.MAX_SEQ_LEN(capacity),
    .cmd_layer(layer),.cmd_pos(position),.cmd_mode(phase==9 ? 2'd1 : phase==15 ? 2'd2 : 2'd0),
    .done(completed[1]),.error(faulted[1]),
    .mem_req_valid(req_valid[1]),.mem_req_ready(req_ready[1]),.mem_req_write(req_write[1]),
    .mem_req_kind(req_kind[4+:4]),.mem_req_layer(req_layer[32+:32]),
    .mem_req_proj(req_proj[3+:3]),.mem_req_row(req_row[32+:32]),
    .mem_req_col(req_col[32+:32]),.mem_req_wdata(req_data[32+:32]),
    .mem_rsp_valid(rsp_valid[1]),.mem_rsp_ready(rsp_ready[1]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q4_parent_legacy_gemv gemv (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),.cmd_valid(start[2]),.cmd_ready(ready[2]),
    .cmd_layer(layer),.hidden(hidden),.intermediate(intermediate),
    .kv_heads(kvheads),.head_dim(dimension),.group_size(descriptor[15*32+:32]),
    .cmd_proj(projection),.done(completed[2]),.error(faulted[2]),
    .mem_req_valid(req_valid[2]),.mem_req_ready(req_ready[2]),.mem_req_write(req_write[2]),
    .mem_req_kind(req_kind[8+:4]),.mem_req_layer(req_layer[64+:32]),
    .mem_req_proj(req_proj[6+:3]),.mem_req_row(req_row[64+:32]),
    .mem_req_col(req_col[64+:32]),.mem_req_wdata(req_data[64+:32]),
    .mem_rsp_valid(rsp_valid[2]),.mem_rsp_ready(rsp_ready[2]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q3_parent_rope rope (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),.cmd_valid(start[3]),.cmd_ready(ready[3]),
    .NUM_LAYERS(layers),.HIDDEN_SIZE(hidden),.NUM_Q_HEADS(qheads),
    .NUM_KV_HEADS(kvheads),.HEAD_DIM(dimension),.MAX_SEQ_LEN(capacity),
    .cmd_layer(layer),.cmd_pos(position),.done(completed[3]),.error(faulted[3]),
    .mem_req_valid(req_valid[3]),.mem_req_ready(req_ready[3]),.mem_req_write(req_write[3]),
    .mem_req_kind(req_kind[12+:4]),.mem_req_layer(req_layer[96+:32]),
    .mem_req_proj(req_proj[9+:3]),.mem_req_row(req_row[96+:32]),
    .mem_req_col(req_col[96+:32]),.mem_req_wdata(req_data[96+:32]),
    .mem_rsp_valid(rsp_valid[3]),.mem_rsp_ready(rsp_ready[3]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q3_parent_gqa_attention attention (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),.invalidate(cache_invalidate),
    .cmd_valid(start[4]),.cmd_ready(ready[4]),
    .PROFILE(mode),.NUM_LAYERS(layers),.HIDDEN_SIZE(hidden),.NUM_Q_HEADS(qheads),
    .NUM_KV_HEADS(kvheads),.HEAD_DIM(dimension),.MAX_SEQ_LEN(capacity),
    .CACHE_MODE(cache_mode),.CACHE_BLOCK(descriptor[24*32+:32]),
    .RATIO(descriptor[22*32+:32]),.INT4_ASYM(cache_encoding==3),
    .cmd_layer(layer),.cmd_pos(position),.cmd_phase(token_phase),
    .done(completed[4]),.error(faulted[4]),
    .c_req_valid(req_valid[4+:2]),.c_req_ready(req_ready[4+:2]),.c_req_write(req_write[4+:2]),
    .c_req_kind(req_kind[16+:8]),.c_req_layer(req_layer[128+:64]),
    .c_req_proj(req_proj[12+:6]),.c_req_row(req_row[128+:64]),
    .c_req_col(req_col[128+:64]),.c_req_wdata(req_data[128+:64]),
    .c_rsp_valid(rsp_valid[4+:2]),.c_rsp_ready(rsp_ready[4+:2]),
    .c_rsp_rdata({2{mem_rsp_rdata}}),.c_rsp_error({2{mem_rsp_error}})
  );
  anvil_q3_parent_elementwise elementwise (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),.cmd_valid(start[5]),.cmd_ready(ready[5]),
    .NUM_LAYERS(layers),.HIDDEN_SIZE(hidden),.INTERMEDIATE_SIZE(intermediate),.MAX_SEQ_LEN(capacity),
    .cmd_layer(layer),.cmd_pos(position),.cmd_mode(phase==8 ? 2'd0 : phase==14 ? 2'd1 : 2'd2),
    .done(completed[5]),.error(faulted[5]),
    .mem_req_valid(req_valid[6]),.mem_req_ready(req_ready[6]),.mem_req_write(req_write[6]),
    .mem_req_kind(req_kind[24+:4]),.mem_req_layer(req_layer[192+:32]),
    .mem_req_proj(req_proj[18+:3]),.mem_req_row(req_row[192+:32]),
    .mem_req_col(req_col[192+:32]),.mem_req_wdata(req_data[192+:32]),
    .mem_rsp_valid(rsp_valid[6]),.mem_rsp_ready(rsp_ready[6]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  localparam [1:0] SELECT=0, REQUEST=1, RESPONSE=2;
  reg [1:0] memory_state;
  reg [2:0] memory_owner, round_robin;
  reg found;
  reg [2:0] selected;
  integer n, candidate;
  always @* begin
    found=0; selected=0; candidate=0;
    for (n=0;n<7;n=n+1) begin
      candidate=round_robin+n;
      if (candidate>=7) candidate=candidate-7;
      if (!found && req_valid[candidate]) begin found=1; selected=3'(candidate); end
    end
  end
  wire memory_enabled=rst_n && !child_flush;
  assign mem_req_valid=memory_enabled && memory_state==REQUEST && req_valid[memory_owner];
  assign mem_req_write=mem_req_valid && req_write[memory_owner];
  assign mem_req_kind=mem_req_valid ? req_kind[memory_owner*4+:4] : 4'd0;
  assign mem_req_layer=mem_req_valid ? req_layer[memory_owner*32+:32] : 32'd0;
  assign mem_req_proj=mem_req_valid ? req_proj[memory_owner*3+:3] : 3'd0;
  assign mem_req_row=mem_req_valid ? req_row[memory_owner*32+:32] : 32'd0;
  assign mem_req_col=mem_req_valid ? req_col[memory_owner*32+:32] : 32'd0;
  assign mem_req_wdata=mem_req_valid ? req_data[memory_owner*32+:32] : 32'd0;
  assign mem_rsp_ready=memory_enabled &&
    (memory_state==RESPONSE || (mem_req_valid && mem_req_ready)) && rsp_ready[memory_owner];
  for (genvar c=0;c<7;c=c+1) begin : response_ownership
    assign req_ready[c]=mem_req_valid && memory_owner==c && mem_req_ready;
    assign rsp_valid[c]=memory_enabled && memory_owner==c && mem_rsp_valid &&
      (memory_state==RESPONSE || (mem_req_valid && mem_req_ready));
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin memory_state<=SELECT; memory_owner<=0; round_robin<=0; end
    else if (child_flush) begin memory_state<=SELECT; round_robin<=0; end
    else case (memory_state)
      SELECT: if (found) begin memory_owner<=selected; memory_state<=REQUEST; end
      REQUEST: if (mem_req_valid && mem_req_ready) begin
        if (mem_rsp_valid && mem_rsp_ready) begin
          memory_state<=SELECT; round_robin<=memory_owner==6 ? 3'd0 : memory_owner+1'b1;
        end else memory_state<=RESPONSE;
      end
      RESPONSE: if (mem_rsp_valid && mem_rsp_ready) begin
        memory_state<=SELECT; round_robin<=memory_owner==6 ? 3'd0 : memory_owner+1'b1;
      end
      default: memory_state<=SELECT;
    endcase
  end
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; phase<=0; token<=0; position<=0; layer<=0;
      token_phase<=0; new_sequence<=0; failed<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else case (state)
      IDLE: if (cmd_valid) begin
        token<=cmd_token; position<=cmd_pos; layer<=0; token_phase<=cmd_phase;
        new_sequence<=cmd_new_sequence; failed<=0; phase<=0;
        if (cmd_new_sequence) state<=INVALIDATE; else state<=START;
      end
      INVALIDATE: state<=START;
      START: if (ready[owner]) state<=WAIT;
      WAIT: if (completed[owner]) begin
        if (faulted[owner]) begin failed<=1; state<=COMPLETE; end
        else if (phase==16) state<=COMPLETE;
        else if (phase==14 && layer+1<layers) begin
          layer<=layer+1'b1; phase<=1; state<=START;
        end else begin
          if (phase==14) layer<=0;
          phase<=phase+1'b1; state<=START;
        end
      end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
