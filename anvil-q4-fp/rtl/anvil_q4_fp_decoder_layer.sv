module anvil_q4_fp_decoder_layer #(
  parameter integer TILE_K=128, TILE_ROWS=16
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, cmd_epoch, cmd_generation, committed_tokens,
  input wire [31:0] protected_epoch, protected_tokens,
  input wire [31:0] hidden, intermediate, query_heads, kv_heads, head_dim,
  input wire [31:0] vocabulary, group_size, gqa_ratio, epsilon,
  input wire [31:0] context_capacity, page_tokens, physical_pages,
  input wire activation_format, activation_a8, weight_asymmetric, qkv_bias,
  input wire [1:0] weight_format, cache_format,
  output wire done, error,
  output wire [16:0] mem_req_valid,
  input wire [16:0] mem_req_ready,
  output wire [16:0] mem_req_write,
  output wire [67:0] mem_req_kind,
  output wire [543:0] mem_req_layer,
  output wire [50:0] mem_req_proj,
  output wire [543:0] mem_req_row, mem_req_col, mem_req_wdata, mem_req_stride,
  input wire [16:0] mem_rsp_valid,
  output wire [16:0] mem_rsp_ready,
  input wire [543:0] mem_rsp_rdata,
  input wire [16:0] mem_rsp_error
);
  localparam [2:0] IDLE=0, START=1, WAIT=2, COMPLETE=3, FENCE=4;
  reg [2:0] state;
  reg [3:0] phase;
  reg [31:0] layer, position, epoch, generation, committed;
  reg failed, cache_active;
  wire [2:0] unit_owner=phase==0 || phase==9 ? 3'd0 :
    phase==1 || phase==2 || phase==3 || phase==7 ? 3'd1 :
    phase==4 || phase==5 ? 3'd2 : phase==6 ? 3'd3 : phase==10 ? 3'd5 : 3'd6;
  wire [6:0] child_ready, child_done, child_error;
  wire [6:0] start=rst_n && !flush && state==START ? 7'b1 << unit_owner : 7'd0;
  wire [118:0] req_valid, req_ready, req_write, rsp_valid, rsp_ready, rsp_error;
  wire [475:0] req_kind;
  wire [356:0] req_proj;
  wire [3807:0] req_layer, req_row, req_col, req_data, req_stride, rsp_data;
  wire routing_idle;
  for (genvar n=0;n<7;n=n+1) begin : scalar_clients
    if (n!=1 && n!=5) begin : mask_weight_channels
      assign req_valid[n*17+:16]=0;
      assign req_write[n*17+:16]=0;
      assign req_kind[n*68+:64]=0;
      assign req_proj[n*51+:48]=0;
      assign req_layer[n*544+:512]=0;
      assign req_row[n*544+:512]=0;
      assign req_col[n*544+:512]=0;
      assign req_data[n*544+:512]=0;
      assign req_stride[n*544+:512]=0;
      assign rsp_ready[n*17+:16]=0;
    end
  end
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

  anvil_q4_fp_rmsnorm norm (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(start[0]),.cmd_ready(child_ready[0]),.cmd_layer(layer),
    .hidden(hidden),.intermediate(intermediate),.epsilon(epsilon),
    .activation_format(activation_format),.cmd_mode(phase==9 ? 2'd1 : 2'd0),
    .done(child_done[0]),.error(child_error[0]),
    .mem_req_valid(req_valid[16]),.mem_req_ready(req_ready[16]),
    .mem_req_write(req_write[16]),.mem_req_kind(req_kind[64+:4]),
    .mem_req_layer(req_layer[512+:32]),.mem_req_proj(req_proj[48+:3]),
    .mem_req_row(req_row[512+:32]),.mem_req_col(req_col[512+:32]),
    .mem_req_wdata(req_data[512+:32]),.mem_req_stride(req_stride[512+:32]),
    .mem_rsp_valid(rsp_valid[16]),.mem_rsp_ready(rsp_ready[16]),
    .mem_rsp_rdata(rsp_data[512+:32]),.mem_rsp_error(rsp_error[16])
  );
  anvil_q4_fp_gemv #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) gemv (
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
    .mem_req_valid(req_valid[17+:17]),.mem_req_ready(req_ready[17+:17]),
    .mem_req_write(req_write[17+:17]),.mem_req_kind(req_kind[68+:68]),
    .mem_req_layer(req_layer[544+:544]),.mem_req_proj(req_proj[51+:51]),
    .mem_req_row(req_row[544+:544]),.mem_req_col(req_col[544+:544]),
    .mem_req_wdata(req_data[544+:544]),.mem_req_stride(req_stride[544+:544]),
    .mem_rsp_valid(rsp_valid[17+:17]),.mem_rsp_ready(rsp_ready[17+:17]),
    .mem_rsp_rdata(rsp_data[544+:544]),.mem_rsp_error(rsp_error[17+:17])
  );
  anvil_q4_fp_rope rope (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(start[2]),.cmd_ready(child_ready[2]),
    .cmd_pos(position),.cmd_generation(generation),.cmd_slot(phase==4 ? 32'd2 : 32'd3),
    .cmd_heads(phase==4 ? query_heads : kv_heads),.head_dim(head_dim),
    .hidden(hidden),.intermediate(intermediate),
    .done(child_done[2]),.error(child_error[2]),
    .mem_req_valid(req_valid[50]),.mem_req_ready(req_ready[50]),
    .mem_req_write(req_write[50]),.mem_req_kind(req_kind[200+:4]),
    .mem_req_layer(req_layer[1600+:32]),.mem_req_proj(req_proj[150+:3]),
    .mem_req_row(req_row[1600+:32]),.mem_req_col(req_col[1600+:32]),
    .mem_req_wdata(req_data[1600+:32]),.mem_req_stride(req_stride[1600+:32]),
    .mem_rsp_valid(rsp_valid[50]),.mem_rsp_ready(rsp_ready[50]),
    .mem_rsp_rdata(rsp_data[1600+:32]),.mem_rsp_error(rsp_error[50])
  );
  anvil_q4_fp_gqa_attention attention (
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
    .mem_req_valid(req_valid[67]),.mem_req_ready(req_ready[67]),
    .mem_req_write(req_write[67]),.mem_req_kind(req_kind[268+:4]),
    .mem_req_layer(req_layer[2144+:32]),.mem_req_proj(req_proj[201+:3]),
    .mem_req_row(req_row[2144+:32]),.mem_req_col(req_col[2144+:32]),
    .mem_req_wdata(req_data[2144+:32]),.mem_req_stride(req_stride[2144+:32]),
    .mem_rsp_valid(rsp_valid[67]),.mem_rsp_ready(rsp_ready[67]),
    .mem_rsp_rdata(rsp_data[2144+:32]),.mem_rsp_error(rsp_error[67])
  );
  anvil_q4_fp_kv_cache kv_cache (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(cache_cmd_valid),.cmd_ready(cache_cmd_ready),
    .cmd_write(cache_cmd_write),.cmd_value(cache_cmd_value),.cmd_allow_current(1'b1),
    .cmd_layer(cache_cmd_layer),.cmd_pos(cache_cmd_pos),.cmd_head(cache_cmd_head),
    .cmd_dimension(cache_cmd_dimension),.cmd_epoch(cache_cmd_epoch),
    .committed_tokens(cache_committed),.context_capacity(context_capacity),
    .protected_epoch(protected_epoch),.protected_tokens(protected_tokens),
    .kv_heads(kv_heads),.head_dim(head_dim),.hidden(hidden),.intermediate(intermediate),
    .cache_format(cache_format),.page_tokens(page_tokens),.physical_pages(physical_pages),
    .out_valid(cache_out_valid),.out_ready(cache_out_ready),
    .result(cache_result),.error(cache_error),
    .mem_req_valid(req_valid[84]),.mem_req_ready(req_ready[84]),
    .mem_req_write(req_write[84]),.mem_req_kind(req_kind[336+:4]),
    .mem_req_layer(req_layer[2688+:32]),.mem_req_proj(req_proj[252+:3]),
    .mem_req_row(req_row[2688+:32]),.mem_req_col(req_col[2688+:32]),
    .mem_req_wdata(req_data[2688+:32]),.mem_req_stride(req_stride[2688+:32]),
    .mem_rsp_valid(rsp_valid[84]),.mem_rsp_ready(rsp_ready[84]),
    .mem_rsp_rdata(rsp_data[2688+:32]),.mem_rsp_error(rsp_error[84])
  );
  anvil_q4_fp_swiglu_mlp #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) mlp (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(start[5]),.cmd_ready(child_ready[5]),.cmd_layer(layer),
    .hidden(hidden),.intermediate(intermediate),.kv_heads(kv_heads),.head_dim(head_dim),
    .vocabulary(vocabulary),.group_size(group_size),
    .activation_format(activation_format),.activation_a8(activation_a8),
    .weight_asymmetric(weight_asymmetric),.weight_format(weight_format),
    .done(child_done[5]),.error(child_error[5]),
    .mem_req_valid(req_valid[85+:17]),.mem_req_ready(req_ready[85+:17]),
    .mem_req_write(req_write[85+:17]),.mem_req_kind(req_kind[340+:68]),
    .mem_req_layer(req_layer[2720+:544]),.mem_req_proj(req_proj[255+:51]),
    .mem_req_row(req_row[2720+:544]),.mem_req_col(req_col[2720+:544]),
    .mem_req_wdata(req_data[2720+:544]),.mem_req_stride(req_stride[2720+:544]),
    .mem_rsp_valid(rsp_valid[85+:17]),.mem_rsp_ready(rsp_ready[85+:17]),
    .mem_rsp_rdata(rsp_data[2720+:544]),.mem_rsp_error(rsp_error[85+:17])
  );
  anvil_q4_fp_elementwise elementwise (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(start[6]),.cmd_ready(child_ready[6]),.cmd_operation(2'd0),
    .cmd_count(hidden),.cmd_source0(phase==8 ? 32'd0 : 32'd7),
    .cmd_source1(phase==8 ? 32'd6 : 32'd12),.cmd_target(phase==8 ? 32'd7 : 32'd0),
    .scratch_stride(hidden>intermediate ? hidden : intermediate),
    .done(child_done[6]),.error(child_error[6]),
    .mem_req_valid(req_valid[118]),.mem_req_ready(req_ready[118]),
    .mem_req_write(req_write[118]),.mem_req_kind(req_kind[472+:4]),
    .mem_req_layer(req_layer[3776+:32]),.mem_req_proj(req_proj[354+:3]),
    .mem_req_row(req_row[3776+:32]),.mem_req_col(req_col[3776+:32]),
    .mem_req_wdata(req_data[3776+:32]),.mem_req_stride(req_stride[3776+:32]),
    .mem_rsp_valid(rsp_valid[118]),.mem_rsp_ready(rsp_ready[118]),
    .mem_rsp_rdata(rsp_data[3776+:32]),.mem_rsp_error(rsp_error[118])
  );
  anvil_q4_fp_channel_mux #(.CLIENTS(7)) routing (
    .clk(clk),.rst_n(rst_n),.flush(flush),.idle(routing_idle),
    .c_req_valid(req_valid),.c_req_ready(req_ready),.c_req_write(req_write),
    .c_req_kind(req_kind),.c_req_layer(req_layer),.c_req_proj(req_proj),
    .c_req_row(req_row),.c_req_col(req_col),.c_req_wdata(req_data),.c_req_stride(req_stride),
    .c_rsp_valid(rsp_valid),.c_rsp_ready(rsp_ready),.c_rsp_rdata(rsp_data),.c_rsp_error(rsp_error),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_stride(mem_req_stride),.mem_rsp_valid(mem_rsp_valid),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
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
          failed<=child_error[unit_owner]; state<=FENCE;
        end
        FENCE: if (routing_idle) begin
          if (failed || phase==11) state<=COMPLETE;
          else begin phase<=phase+1'b1; state<=START; end
        end
        COMPLETE: state<=IDLE;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
