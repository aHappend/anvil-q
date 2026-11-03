module anvil_q4_fp_swiglu_mlp #(
  parameter integer TILE_K=128, TILE_ROWS=16
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer,
  input wire [31:0] hidden, intermediate, kv_heads, head_dim, vocabulary, group_size,
  input wire activation_format, activation_a8, weight_asymmetric,
  input wire [1:0] weight_format,
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
  localparam [3:0] IDLE=0, GATE=1, GATE_WAIT=2, UP=3, UP_WAIT=4,
    ACTIVATE=5, ACTIVATE_WAIT=6, DOWN=7, DOWN_WAIT=8, COMPLETE=9, FENCE=10;
  reg [3:0] state, resume_state;
  reg [31:0] layer;
  reg failed;
  wire activation_owner=state==ACTIVATE || state==ACTIVATE_WAIT;
  wire gemv_owner=state==GATE || state==GATE_WAIT || state==UP ||
    state==UP_WAIT || state==DOWN || state==DOWN_WAIT;
  wire [33:0] req_valid, req_ready, req_write, rsp_valid, rsp_ready, rsp_error;
  wire [135:0] req_kind;
  wire [101:0] req_proj;
  wire [1087:0] req_layer, req_row, req_col, req_data, req_stride, rsp_data;
  wire routing_idle;
  assign req_valid[17+:16]=0;
  assign req_write[17+:16]=0;
  assign req_kind[68+:64]=0;
  assign req_proj[51+:48]=0;
  assign req_layer[544+:512]=0;
  assign req_row[544+:512]=0;
  assign req_col[544+:512]=0;
  assign req_data[544+:512]=0;
  assign req_stride[544+:512]=0;
  assign rsp_ready[17+:16]=0;
  wire gemv_ready, gemv_done, gemv_error, element_ready, element_done, element_error;
  wire unused_valid;
  wire [31:0] unused_index, unused_data;
  anvil_q4_fp_gemv #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) gemv (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(state==GATE || state==UP || state==DOWN),.cmd_ready(gemv_ready),
    .cmd_layer(layer),.cmd_proj(state==GATE || state==GATE_WAIT ? 3'd4 :
      state==UP || state==UP_WAIT ? 3'd5 : 3'd6),.cmd_lmhead(1'b0),
    .hidden(hidden),.intermediate(intermediate),.kv_heads(kv_heads),.head_dim(head_dim),
    .vocabulary(vocabulary),.group_size(group_size),.activation_format(activation_format),
    .activation_a8(activation_a8),.weight_asymmetric(weight_asymmetric),
    .qkv_bias(1'b0),.weight_format(weight_format),
    .done(gemv_done),.error(gemv_error),.result_valid(unused_valid),
    .result_ready(1'b1),.result_index(unused_index),.result_data(unused_data),
    .mem_req_valid(req_valid[0+:17]),.mem_req_ready(req_ready[0+:17]),
    .mem_req_write(req_write[0+:17]),.mem_req_kind(req_kind[0+:68]),
    .mem_req_layer(req_layer[0+:544]),.mem_req_proj(req_proj[0+:51]),
    .mem_req_row(req_row[0+:544]),.mem_req_col(req_col[0+:544]),
    .mem_req_wdata(req_data[0+:544]),.mem_req_stride(req_stride[0+:544]),
    .mem_rsp_valid(rsp_valid[0+:17]),.mem_rsp_ready(rsp_ready[0+:17]),
    .mem_rsp_rdata(rsp_data[0+:544]),.mem_rsp_error(rsp_error[0+:17])
  );
  anvil_q4_fp_elementwise activation (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(state==ACTIVATE),.cmd_ready(element_ready),
    .cmd_operation(2'd1),.cmd_count(intermediate),
    .cmd_source0(32'd9),.cmd_source1(32'd10),.cmd_target(32'd11),
    .scratch_stride(hidden>intermediate ? hidden : intermediate),
    .done(element_done),.error(element_error),
    .mem_req_valid(req_valid[33]),.mem_req_ready(req_ready[33]),
    .mem_req_write(req_write[33]),.mem_req_kind(req_kind[132+:4]),
    .mem_req_layer(req_layer[1056+:32]),.mem_req_proj(req_proj[99+:3]),
    .mem_req_row(req_row[1056+:32]),.mem_req_col(req_col[1056+:32]),
    .mem_req_wdata(req_data[1056+:32]),.mem_req_stride(req_stride[1056+:32]),
    .mem_rsp_valid(rsp_valid[33]),.mem_rsp_ready(rsp_ready[33]),
    .mem_rsp_rdata(rsp_data[1056+:32]),.mem_rsp_error(rsp_error[33])
  );
  anvil_q4_fp_channel_mux #(.CLIENTS(2)) routing (
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
    if (!rst_n) begin state<=IDLE; resume_state<=IDLE; layer<=0; failed<=0; end
    else if (flush) begin state<=IDLE; failed<=0; end
    else case (state)
      IDLE: if (cmd_valid) begin layer<=cmd_layer; failed<=0; state<=GATE; end
      GATE: if (gemv_ready) state<=GATE_WAIT;
      GATE_WAIT: if (gemv_done) begin
        failed<=gemv_error; resume_state<=UP; state<=FENCE;
      end
      UP: if (gemv_ready) state<=UP_WAIT;
      UP_WAIT: if (gemv_done) begin
        failed<=gemv_error; resume_state<=ACTIVATE; state<=FENCE;
      end
      ACTIVATE: if (element_ready) state<=ACTIVATE_WAIT;
      ACTIVATE_WAIT: if (element_done) begin
        failed<=element_error; resume_state<=DOWN; state<=FENCE;
      end
      DOWN: if (gemv_ready) state<=DOWN_WAIT;
      DOWN_WAIT: if (gemv_done) begin
        failed<=gemv_error; resume_state<=COMPLETE; state<=FENCE;
      end
      FENCE: if (routing_idle) begin
        if (failed) state<=COMPLETE; else state<=resume_state;
      end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
