module anvil_q3_elementwise #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos,
  input wire [1:0] cmd_mode,
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
  input wire mem_rsp_error
);
  localparam IDLE=0, A_READ=1, A_RESPONSE=2, B_READ=3, B_RESPONSE=4;
  localparam ADD=5, ADD_WAIT=6, SILU=7, SILU_WAIT=8;
  localparam MULTIPLY=9, MULTIPLY_WAIT=10, ROUND=11, WRITE=12;
  localparam WRITE_RESPONSE=13, COMPLETE=14, FAULTED=15;
  reg [3:0] state;
  reg [1:0] mode;
  reg failed;
  reg [31:0] index, length, source_a, source_b, destination, result;
  reg signed [31:0] a, b, silu_value;
  reg signed [127:0] arithmetic_result;
  wire unit_flush=flush || failed;
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==A_READ || state==B_READ || state==WRITE);
  wire add_ready, add_valid, add_error;
  wire signed [127:0] added;
  wire silu_ready, silu_done, silu_error;
  wire signed [31:0] silu_result;
  wire multiply_ready, multiply_done, multiply_error;
  wire signed [63:0] product;
  generate if (NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || INTERMEDIATE_SIZE<=0 ||
      MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>32768 ||
      128'(NUM_LAYERS)>128'hffffffff ||
      128'(HIDDEN_SIZE)*15>128'hffffffff ||
      128'(INTERMEDIATE_SIZE)*15>128'hffffffff) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: elementwise dimensions");
  end endgenerate
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;

  anvil_q3_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(state==WRITE),.kind(4'd8),.layer(32'd0),.proj(3'd0),
    .row(state==A_READ ? source_a : state==B_READ ? source_b : destination),
    .col(index),.wdata(state==WRITE ? result : 32'd0),.rdata(rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q3_add128 residual_adder (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.in_valid(state==ADD),
    .in_ready(add_ready),.in_a({{96{a[31]}},a}),.in_b({{96{b[31]}},b}),
    .out_valid(add_valid),.out_ready(1'b1),.out_error(add_error),.out_sum(added)
  );
  anvil_q3_silu silu (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.start(state==SILU),.x(a),
    .ready(silu_ready),.done(silu_done),.error(silu_error),.value(silu_result)
  );
  anvil_q3_multiplier #(.A_W(32),.B_W(32)) multiplier (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.start(state==MULTIPLY),
    .a(silu_value),.b(b),.ready(multiply_ready),
    .done(multiply_done),.error(multiply_error),.product(product)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; mode<=0; failed<=0; index<=0; length<=0;
      source_a<=0; source_b<=0; destination<=0; result<=0;
      a<=0; b<=0; silu_value<=0; arithmetic_result<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (!failed && (fault || (add_valid && add_error) ||
        (silu_done && silu_error) || (multiply_done && multiply_error))) begin
      failed<=1; state<=COMPLETE;
    end else case (state)
      IDLE: if (cmd_valid) begin
        mode<=cmd_mode; failed<=0; index<=0;
        length<=cmd_mode==2 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
        source_a<=cmd_mode==0 ? 0 : cmd_mode==1 ? 7 : 9;
        source_b<=cmd_mode==0 ? 6 : cmd_mode==1 ? 12 : 10;
        destination<=cmd_mode==0 ? 7 : cmd_mode==1 ? 0 : 11;
        if (cmd_mode>2 || cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin
          failed<=1; state<=COMPLETE;
        end else state<=A_READ;
      end
      A_READ: if (issue) state<=A_RESPONSE;
      A_RESPONSE: if (complete) begin a<=rdata; state<=B_READ; end
      B_READ: if (issue) state<=B_RESPONSE;
      B_RESPONSE: if (complete) begin
        b<=rdata;
        if (mode==2) state<=SILU; else state<=ADD;
      end
      ADD: if (add_ready) state<=ADD_WAIT;
      ADD_WAIT: if (add_valid) begin arithmetic_result<=added; state<=ROUND; end
      SILU: if (silu_ready) state<=SILU_WAIT;
      SILU_WAIT: if (silu_done) begin silu_value<=silu_result; state<=MULTIPLY; end
      MULTIPLY: if (multiply_ready) state<=MULTIPLY_WAIT;
      MULTIPLY_WAIT: if (multiply_done) begin
        arithmetic_result<={{64{product[63]}},product}; state<=ROUND;
      end
      ROUND: begin
        result<=anvil_q3_pkg::round_shift_sat32(arithmetic_result,mode==2 ? 16 : 0);
        state<=WRITE;
      end
      WRITE: if (issue) state<=WRITE_RESPONSE;
      WRITE_RESPONSE: if (complete) begin
        if (index+1<length) begin index<=index+1'b1; state<=A_READ; end
        else state<=COMPLETE;
      end
      COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
      FAULTED: state<=FAULTED;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
