module anvil_q3_swiglu_mlp #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos,
  output wire done, error,
  output wire gemv_cmd_valid,
  input wire gemv_cmd_ready,
  output wire [2:0] gemv_cmd_proj,
  input wire gemv_done, gemv_error,
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
  localparam IDLE=0, GATE=1, GATE_WAIT=2, UP=3, UP_WAIT=4;
  localparam PRODUCT=5, PRODUCT_WAIT=6, DOWN=7, DOWN_WAIT=8, COMPLETE=9, FAULTED=10;
  reg [3:0] state;
  reg failed;
  reg [31:0] layer, position;
  wire product_ready, product_done, product_error;
  wire unit_flush=flush || failed;
  wire gemv_waiting=state==GATE_WAIT || state==UP_WAIT || state==DOWN_WAIT;
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  assign gemv_cmd_valid=rst_n && !unit_flush && (state==GATE || state==UP || state==DOWN);
  assign gemv_cmd_proj=!gemv_cmd_valid ? 3'd0 : state==GATE ? 3'd4 : state==UP ? 3'd5 : 3'd6;
  anvil_q3_elementwise #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
    .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) silu_product (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.cmd_valid(state==PRODUCT),
    .cmd_ready(product_ready),.cmd_layer(layer),.cmd_pos(position),.cmd_mode(2'd2),
    .done(product_done),.error(product_error),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin state<=IDLE; failed<=0; layer<=0; position<=0; end
    else if (flush) begin state<=IDLE; failed<=0; end
    else if (!failed && ((gemv_waiting && gemv_done && gemv_error) ||
        (product_done && product_error))) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        layer<=cmd_layer; position<=cmd_pos; failed<=0;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin failed<=1; state<=COMPLETE; end
        else state<=GATE;
      end
      GATE: if (gemv_cmd_ready) state<=GATE_WAIT;
      GATE_WAIT: if (gemv_done) state<=UP;
      UP: if (gemv_cmd_ready) state<=UP_WAIT;
      UP_WAIT: if (gemv_done) state<=PRODUCT;
      PRODUCT: if (product_ready) state<=PRODUCT_WAIT;
      PRODUCT_WAIT: if (product_done) state<=DOWN;
      DOWN: if (gemv_cmd_ready) state<=DOWN_WAIT;
      DOWN_WAIT: if (gemv_done) state<=COMPLETE;
      COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
      FAULTED: state<=FAULTED;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
