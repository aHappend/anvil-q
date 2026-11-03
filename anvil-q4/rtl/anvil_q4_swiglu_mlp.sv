module anvil_q4_swiglu_mlp #(
  parameter integer TILE_K=128, TILE_ROWS=8
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer,
  input wire [31:0] hidden, intermediate, kv_heads, head_dim, vocabulary, group_size,
  input wire activation_format, activation_a8, weight_asymmetric,
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
  localparam [3:0] IDLE=0, GATE=1, GATE_WAIT=2, UP=3, UP_WAIT=4,
    ACTIVATE=5, ACTIVATE_WAIT=6, DOWN=7, DOWN_WAIT=8, COMPLETE=9;
  reg [3:0] state;
  reg [31:0] layer;
  reg failed;
  wire activation_owner=state==ACTIVATE || state==ACTIVATE_WAIT;
  wire gemv_owner=state==GATE || state==GATE_WAIT || state==UP ||
    state==UP_WAIT || state==DOWN || state==DOWN_WAIT;
  wire [1:0] req_valid, req_ready, req_write, rsp_valid, rsp_ready;
  wire [7:0] req_kind;
  wire [5:0] req_proj;
  wire [63:0] req_layer, req_row, req_col, req_data, req_stride;
  wire gemv_ready, gemv_done, gemv_error, element_ready, element_done, element_error;
  wire unused_valid;
  wire [31:0] unused_index, unused_data;
  anvil_q4_gemv #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) gemv (
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
    .mem_req_valid(req_valid[0]),.mem_req_ready(req_ready[0]),
    .mem_req_write(req_write[0]),.mem_req_kind(req_kind[0+:4]),
    .mem_req_layer(req_layer[0+:32]),.mem_req_proj(req_proj[0+:3]),
    .mem_req_row(req_row[0+:32]),.mem_req_col(req_col[0+:32]),
    .mem_req_wdata(req_data[0+:32]),.mem_req_stride(req_stride[0+:32]),
    .mem_rsp_valid(rsp_valid[0]),.mem_rsp_ready(rsp_ready[0]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q4_elementwise activation (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(state==ACTIVATE),.cmd_ready(element_ready),
    .cmd_operation(2'd1),.cmd_count(intermediate),
    .cmd_source0(32'd9),.cmd_source1(32'd10),.cmd_target(32'd11),
    .scratch_stride(hidden>intermediate ? hidden : intermediate),
    .done(element_done),.error(element_error),
    .mem_req_valid(req_valid[1]),.mem_req_ready(req_ready[1]),
    .mem_req_write(req_write[1]),.mem_req_kind(req_kind[4+:4]),
    .mem_req_layer(req_layer[32+:32]),.mem_req_proj(req_proj[3+:3]),
    .mem_req_row(req_row[32+:32]),.mem_req_col(req_col[32+:32]),
    .mem_req_wdata(req_data[32+:32]),.mem_req_stride(req_stride[32+:32]),
    .mem_rsp_valid(rsp_valid[1]),.mem_rsp_ready(rsp_ready[1]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  wire owner=activation_owner;
  wire enabled=rst_n && !flush && (activation_owner || gemv_owner);
  assign req_ready[0]=enabled && gemv_owner && mem_req_ready;
  assign req_ready[1]=enabled && activation_owner && mem_req_ready;
  assign rsp_valid[0]=enabled && gemv_owner && mem_rsp_valid;
  assign rsp_valid[1]=enabled && activation_owner && mem_rsp_valid;
  assign mem_req_valid=enabled && req_valid[owner];
  assign mem_req_write=mem_req_valid && req_write[owner];
  assign mem_req_kind=mem_req_valid ? req_kind[owner*4+:4] : 4'd0;
  assign mem_req_layer=mem_req_valid ? req_layer[owner*32+:32] : 32'd0;
  assign mem_req_proj=mem_req_valid ? req_proj[owner*3+:3] : 3'd0;
  assign mem_req_row=mem_req_valid ? req_row[owner*32+:32] : 32'd0;
  assign mem_req_col=mem_req_valid ? req_col[owner*32+:32] : 32'd0;
  assign mem_req_wdata=mem_req_valid ? req_data[owner*32+:32] : 32'd0;
  assign mem_req_stride=mem_req_valid ? req_stride[owner*32+:32] : 32'd0;
  assign mem_rsp_ready=enabled && rsp_ready[owner];
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin state<=IDLE; layer<=0; failed<=0; end
    else if (flush) begin state<=IDLE; failed<=0; end
    else case (state)
      IDLE: if (cmd_valid) begin layer<=cmd_layer; failed<=0; state<=GATE; end
      GATE: if (gemv_ready) state<=GATE_WAIT;
      GATE_WAIT: if (gemv_done) begin
        if (gemv_error) begin failed<=1; state<=COMPLETE; end
        else state<=UP;
      end
      UP: if (gemv_ready) state<=UP_WAIT;
      UP_WAIT: if (gemv_done) begin
        if (gemv_error) begin failed<=1; state<=COMPLETE; end
        else state<=ACTIVATE;
      end
      ACTIVATE: if (element_ready) state<=ACTIVATE_WAIT;
      ACTIVATE_WAIT: if (element_done) begin
        if (element_error) begin failed<=1; state<=COMPLETE; end
        else state<=DOWN;
      end
      DOWN: if (gemv_ready) state<=DOWN_WAIT;
      DOWN_WAIT: if (gemv_done) begin failed<=gemv_error; state<=COMPLETE; end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
