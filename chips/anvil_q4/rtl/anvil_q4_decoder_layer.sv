module anvil_q4_decoder_layer #(
  parameter integer TILE_K=128, TILE_ROWS=8
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, cmd_epoch, cmd_generation, committed_tokens,
  input wire [31:0] protected_epoch, protected_tokens,
  input wire [31:0] hidden, intermediate, query_heads, kv_heads, head_dim,
  input wire [31:0] vocabulary, group_size, gqa_ratio, epsilon,
  input wire [31:0] context_capacity, page_tokens, physical_pages,
  input wire activation_format, activation_a8, weight_asymmetric, qkv_bias, cache_int8,
  input wire [1:0] weight_format,
  output wire done, error,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata, mem_req_stride,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  localparam [1:0] IDLE=0, START=1, WAIT=2, COMPLETE=3;
  reg [1:0] state;
  reg [3:0] phase;
  reg [31:0] layer, position, epoch, generation, committed;
  reg failed, cache_active;
  wire [2:0] unit_owner=phase==0 || phase==9 ? 3'd0 :
    phase==1 || phase==2 || phase==3 || phase==7 ? 3'd1 :
    phase==4 || phase==5 ? 3'd2 : phase==6 ? 3'd3 : phase==10 ? 3'd5 : 3'd6;
  wire [6:0] child_ready, child_done, child_error;
  wire [6:0] start=rst_n && !flush && state==START ? 7'b1 << unit_owner : 7'd0;
  wire [6:0] req_valid, req_ready, req_write, rsp_valid, rsp_ready;
  wire [27:0] req_kind;
  wire [20:0] req_proj;
  wire [223:0] req_layer, req_row, req_col, req_data, req_stride;
  wire cache_cmd_valid, cache_cmd_ready, cache_cmd_write, cache_cmd_value;
  wire [31:0] cache_cmd_layer, cache_cmd_pos, cache_cmd_epoch;
  wire [31:0] cache_cmd_head, cache_cmd_dimension, cache_committed;
  wire cache_out_valid, cache_out_ready, cache_error;
  wire [31:0] cache_result;
  wire unused_valid;
  wire [31:0] unused_index, unused_data;
  assign child_ready[4]=cache_cmd_ready;
  assign child_done[4]=1'b0;
  assign child_error[4]=1'b0;

  anvil_q4_rmsnorm norm (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(start[0]),.cmd_ready(child_ready[0]),.cmd_layer(layer),
    .hidden(hidden),.intermediate(intermediate),.epsilon(epsilon),
    .activation_format(activation_format),.cmd_mode(phase==9 ? 2'd1 : 2'd0),
    .done(child_done[0]),.error(child_error[0]),
    .mem_req_valid(req_valid[0]),.mem_req_ready(req_ready[0]),
    .mem_req_write(req_write[0]),.mem_req_kind(req_kind[0+:4]),
    .mem_req_layer(req_layer[0+:32]),.mem_req_proj(req_proj[0+:3]),
    .mem_req_row(req_row[0+:32]),.mem_req_col(req_col[0+:32]),
    .mem_req_wdata(req_data[0+:32]),.mem_req_stride(req_stride[0+:32]),
    .mem_rsp_valid(rsp_valid[0]),.mem_rsp_ready(rsp_ready[0]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q4_gemv #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) gemv (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(start[1]),.cmd_ready(child_ready[1]),.cmd_layer(layer),
    .cmd_proj(phase==1 ? 3'd0 : phase==2 ? 3'd1 : phase==3 ? 3'd2 : 3'd3),
    .cmd_lmhead(1'b0),.hidden(hidden),.intermediate(intermediate),
    .kv_heads(kv_heads),.head_dim(head_dim),.vocabulary(vocabulary),.group_size(group_size),
    .activation_format(activation_format),.activation_a8(activation_a8),
    .weight_asymmetric(weight_asymmetric),.qkv_bias(qkv_bias),.weight_format(weight_format),
    .done(child_done[1]),.error(child_error[1]),
    .result_valid(unused_valid),.result_ready(1'b1),
    .result_index(unused_index),.result_data(unused_data),
    .mem_req_valid(req_valid[1]),.mem_req_ready(req_ready[1]),
    .mem_req_write(req_write[1]),.mem_req_kind(req_kind[4+:4]),
    .mem_req_layer(req_layer[32+:32]),.mem_req_proj(req_proj[3+:3]),
    .mem_req_row(req_row[32+:32]),.mem_req_col(req_col[32+:32]),
    .mem_req_wdata(req_data[32+:32]),.mem_req_stride(req_stride[32+:32]),
    .mem_rsp_valid(rsp_valid[1]),.mem_rsp_ready(rsp_ready[1]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q4_rope rope (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(start[2]),.cmd_ready(child_ready[2]),
    .cmd_pos(position),.cmd_generation(generation),.cmd_slot(phase==4 ? 32'd2 : 32'd3),
    .cmd_heads(phase==4 ? query_heads : kv_heads),.head_dim(head_dim),
    .hidden(hidden),.intermediate(intermediate),
    .done(child_done[2]),.error(child_error[2]),
    .mem_req_valid(req_valid[2]),.mem_req_ready(req_ready[2]),
    .mem_req_write(req_write[2]),.mem_req_kind(req_kind[8+:4]),
    .mem_req_layer(req_layer[64+:32]),.mem_req_proj(req_proj[6+:3]),
    .mem_req_row(req_row[64+:32]),.mem_req_col(req_col[64+:32]),
    .mem_req_wdata(req_data[64+:32]),.mem_req_stride(req_stride[64+:32]),
    .mem_rsp_valid(rsp_valid[2]),.mem_rsp_ready(rsp_ready[2]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q4_gqa_attention attention (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(start[3]),.cmd_ready(child_ready[3]),
    .cmd_layer(layer),.cmd_pos(position),.cmd_epoch(epoch),.committed_tokens(committed),
    .hidden(hidden),.intermediate(intermediate),.query_heads(query_heads),
    .kv_heads(kv_heads),.head_dim(head_dim),.gqa_ratio(gqa_ratio),
    .context_capacity(context_capacity),
    .cache_cmd_valid(cache_cmd_valid),.cache_cmd_ready(cache_cmd_ready),
    .cache_cmd_write(cache_cmd_write),.cache_cmd_value(cache_cmd_value),
    .cache_cmd_layer(cache_cmd_layer),.cache_cmd_pos(cache_cmd_pos),
    .cache_cmd_epoch(cache_cmd_epoch),.cache_cmd_head(cache_cmd_head),
    .cache_cmd_dimension(cache_cmd_dimension),.cache_committed_tokens(cache_committed),
    .cache_out_valid(cache_out_valid),.cache_out_ready(cache_out_ready),
    .cache_result(cache_result),.cache_error(cache_error),
    .done(child_done[3]),.error(child_error[3]),
    .mem_req_valid(req_valid[3]),.mem_req_ready(req_ready[3]),
    .mem_req_write(req_write[3]),.mem_req_kind(req_kind[12+:4]),
    .mem_req_layer(req_layer[96+:32]),.mem_req_proj(req_proj[9+:3]),
    .mem_req_row(req_row[96+:32]),.mem_req_col(req_col[96+:32]),
    .mem_req_wdata(req_data[96+:32]),.mem_req_stride(req_stride[96+:32]),
    .mem_rsp_valid(rsp_valid[3]),.mem_rsp_ready(rsp_ready[3]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q4_kv_cache kv_cache (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(cache_cmd_valid),.cmd_ready(cache_cmd_ready),
    .cmd_write(cache_cmd_write),.cmd_value(cache_cmd_value),.cmd_allow_current(1'b1),
    .cmd_layer(cache_cmd_layer),.cmd_pos(cache_cmd_pos),.cmd_head(cache_cmd_head),
    .cmd_dimension(cache_cmd_dimension),.cmd_epoch(cache_cmd_epoch),
    .committed_tokens(cache_committed),.context_capacity(context_capacity),
    .protected_epoch(protected_epoch),.protected_tokens(protected_tokens),
    .kv_heads(kv_heads),.head_dim(head_dim),.hidden(hidden),.intermediate(intermediate),
    .cache_int8(cache_int8),.page_tokens(page_tokens),.physical_pages(physical_pages),
    .out_valid(cache_out_valid),.out_ready(cache_out_ready),
    .result(cache_result),.error(cache_error),
    .mem_req_valid(req_valid[4]),.mem_req_ready(req_ready[4]),
    .mem_req_write(req_write[4]),.mem_req_kind(req_kind[16+:4]),
    .mem_req_layer(req_layer[128+:32]),.mem_req_proj(req_proj[12+:3]),
    .mem_req_row(req_row[128+:32]),.mem_req_col(req_col[128+:32]),
    .mem_req_wdata(req_data[128+:32]),.mem_req_stride(req_stride[128+:32]),
    .mem_rsp_valid(rsp_valid[4]),.mem_rsp_ready(rsp_ready[4]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q4_swiglu_mlp #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) mlp (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(start[5]),.cmd_ready(child_ready[5]),.cmd_layer(layer),
    .hidden(hidden),.intermediate(intermediate),.kv_heads(kv_heads),.head_dim(head_dim),
    .vocabulary(vocabulary),.group_size(group_size),
    .activation_format(activation_format),.activation_a8(activation_a8),
    .weight_asymmetric(weight_asymmetric),.weight_format(weight_format),
    .done(child_done[5]),.error(child_error[5]),
    .mem_req_valid(req_valid[5]),.mem_req_ready(req_ready[5]),
    .mem_req_write(req_write[5]),.mem_req_kind(req_kind[20+:4]),
    .mem_req_layer(req_layer[160+:32]),.mem_req_proj(req_proj[15+:3]),
    .mem_req_row(req_row[160+:32]),.mem_req_col(req_col[160+:32]),
    .mem_req_wdata(req_data[160+:32]),.mem_req_stride(req_stride[160+:32]),
    .mem_rsp_valid(rsp_valid[5]),.mem_rsp_ready(rsp_ready[5]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q4_elementwise elementwise (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(start[6]),.cmd_ready(child_ready[6]),.cmd_operation(2'd0),
    .cmd_count(hidden),.cmd_source0(phase==8 ? 32'd0 : 32'd7),
    .cmd_source1(phase==8 ? 32'd6 : 32'd12),.cmd_target(phase==8 ? 32'd7 : 32'd0),
    .scratch_stride(hidden>intermediate ? hidden : intermediate),
    .done(child_done[6]),.error(child_error[6]),
    .mem_req_valid(req_valid[6]),.mem_req_ready(req_ready[6]),
    .mem_req_write(req_write[6]),.mem_req_kind(req_kind[24+:4]),
    .mem_req_layer(req_layer[192+:32]),.mem_req_proj(req_proj[18+:3]),
    .mem_req_row(req_row[192+:32]),.mem_req_col(req_col[192+:32]),
    .mem_req_wdata(req_data[192+:32]),.mem_req_stride(req_stride[192+:32]),
    .mem_rsp_valid(rsp_valid[6]),.mem_rsp_ready(rsp_ready[6]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  wire enabled=rst_n && !flush && (state==START || state==WAIT);
  wire [2:0] memory_owner=phase==6 && (cache_active || cache_cmd_valid) ? 3'd4 : unit_owner;
  for (genvar n=0;n<7;n=n+1) begin : memory_ownership
    assign req_ready[n]=enabled && memory_owner==n && mem_req_ready;
    assign rsp_valid[n]=enabled && memory_owner==n && mem_rsp_valid;
  end
  assign mem_req_valid=enabled && req_valid[memory_owner];
  assign mem_req_write=mem_req_valid && req_write[memory_owner];
  assign mem_req_kind=mem_req_valid ? req_kind[memory_owner*4+:4] : 4'd0;
  assign mem_req_layer=mem_req_valid ? req_layer[memory_owner*32+:32] : 32'd0;
  assign mem_req_proj=mem_req_valid ? req_proj[memory_owner*3+:3] : 3'd0;
  assign mem_req_row=mem_req_valid ? req_row[memory_owner*32+:32] : 32'd0;
  assign mem_req_col=mem_req_valid ? req_col[memory_owner*32+:32] : 32'd0;
  assign mem_req_wdata=mem_req_valid ? req_data[memory_owner*32+:32] : 32'd0;
  assign mem_req_stride=mem_req_valid ? req_stride[memory_owner*32+:32] : 32'd0;
  assign mem_rsp_ready=enabled && rsp_ready[memory_owner];
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; phase<=0; layer<=0; position<=0; epoch<=0;
      generation<=0; committed<=0; failed<=0; cache_active<=0;
    end else if (flush) begin state<=IDLE; failed<=0; cache_active<=0; end
    else begin
      if (cache_cmd_valid && cache_cmd_ready) cache_active<=1;
      if (cache_out_valid && cache_out_ready) cache_active<=0;
      case (state)
        IDLE: if (cmd_valid) begin
          layer<=cmd_layer; position<=cmd_pos; epoch<=cmd_epoch;
          generation<=cmd_generation; committed<=committed_tokens;
          phase<=0; failed<=0; state<=START;
        end
        START: if (child_ready[unit_owner]) state<=WAIT;
        WAIT: if (child_done[unit_owner]) begin
          if (child_error[unit_owner]) begin failed<=1; state<=COMPLETE; end
          else if (phase==11) state<=COMPLETE;
          else begin phase<=phase+1'b1; state<=START; end
        end
        COMPLETE: state<=IDLE;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
