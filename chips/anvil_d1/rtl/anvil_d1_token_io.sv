module anvil_d1_token_io #(
  parameter integer HIDDEN_SIZE=2048, VOCAB_SIZE=102400, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire cmd_project,
  input wire [31:0] cmd_token, cmd_pos,
  output wire done, error,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire c_req_valid,
  input wire c_req_ready,
  output wire c_req_write,
  output wire [3:0] c_req_kind,
  output wire [31:0] c_req_layer,
  output wire [2:0] c_req_proj,
  output wire [31:0] c_req_row, c_req_col, c_req_wdata,
  input wire c_rsp_valid,
  output wire c_rsp_ready,
  input wire [31:0] c_rsp_rdata,
  input wire c_rsp_error
);
  localparam IDLE=0, EMBED_READ=1, EMBED_RESPONSE=2, EMBED_WRITE=3, EMBED_ACK=4;
  localparam INPUT_READ=5, INPUT_RESPONSE=6, WEIGHT_READ=7, WEIGHT_RESPONSE=8;
  localparam MULTIPLY=9, MULTIPLY_WAIT=10, ACC=11, ACC_WAIT=12;
  localparam ROUND=13, ROUND_WAIT=14, LOGIT=15, COMPLETE=16, FAULTED=17, REJECT=18;
  reg [4:0] state;
  reg armed, failed;
  reg [31:0] token, component, vocabulary;
  reg signed [31:0] activation, weight, result;
  reg signed [127:0] product, sum;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==EMBED_READ || state==EMBED_WRITE ||
    state==INPUT_READ || state==WEIGHT_READ);
  wire mul_ready, mul_valid;
  wire signed [63:0] multiplied;
  wire acc_ready, acc_valid, acc_error;
  wire signed [127:0] accumulated;
  wire round_ready, round_valid;
  wire signed [31:0] rounded;
  generate if (HIDDEN_SIZE<8 || HIDDEN_SIZE>2048 || (HIDDEN_SIZE & 7)!=0 ||
      VOCAB_SIZE<4 || VOCAB_SIZE>151936 || MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: token IO geometry");
  end endgenerate
  assign cmd_ready=rst_n && armed && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  assign logit_valid=rst_n && !flush && state==LOGIT;
  assign logit_index=logit_valid ? vocabulary : 32'd0;
  assign logit_data=logit_valid ? result : 32'sd0;
  anvil_d1_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==EMBED_WRITE),
    .kind(state==INPUT_READ || state==EMBED_WRITE ? 4'd8 : 4'd0),
    .layer(32'd0),.proj(3'd0),
    .row(state==EMBED_READ ? token : state==WEIGHT_READ ? vocabulary :
      state==INPUT_READ ? 32'd14 : 32'd0),
    .col(component),.wdata(state==EMBED_WRITE ? activation : 32'd0),.rdata(rdata),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),
    .c_req_write(c_req_write),.c_req_kind(c_req_kind),.c_req_layer(c_req_layer),
    .c_req_proj(c_req_proj),.c_req_row(c_req_row),.c_req_col(c_req_col),
    .c_req_wdata(c_req_wdata),.c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
    .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error)
  );
  anvil_d1_mul32 multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MULTIPLY),.in_ready(mul_ready),.in_a(activation),.in_b(weight),
    .out_valid(mul_valid),.out_ready(1'b1),.out_product(multiplied)
  );
  anvil_d1_accumulator accumulator (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ACC),.in_ready(acc_ready),.in_first(component==0),.in_value(product),
    .out_valid(acc_valid),.out_ready(1'b1),.out_error(acc_error),.out_sum(accumulated)
  );
  anvil_d1_round_sat #(.SHIFT(16)) boundary (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ROUND),.in_ready(round_ready),.in_value(sum),
    .out_valid(round_valid),.out_ready(1'b1),.out_value(rounded)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; token<=0; component<=0; vocabulary<=0;
      activation<=0; weight<=0; result<=0; product<=0; sum<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; failed<=0; end
      else if (!failed && (memory_fault || (acc_valid && acc_error))) begin failed<=1; state<=COMPLETE; end
      else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          token<=cmd_token; component<=0; vocabulary<=0; failed<=0;
          if (cmd_token>=VOCAB_SIZE || cmd_pos>=MAX_SEQ_LEN) begin failed<=1; state<=REJECT; end
          else if (cmd_project) state<=INPUT_READ;
          else state<=EMBED_READ;
        end
        EMBED_READ: if (issue) state<=EMBED_RESPONSE;
        EMBED_RESPONSE: if (memory_complete) begin activation<=rdata; state<=EMBED_WRITE; end
        EMBED_WRITE: if (issue) state<=EMBED_ACK;
        EMBED_ACK: if (memory_complete) begin
          if (component==HIDDEN_SIZE-1) state<=COMPLETE;
          else begin component<=component+1'b1; state<=EMBED_READ; end
        end
        INPUT_READ: if (issue) state<=INPUT_RESPONSE;
        INPUT_RESPONSE: if (memory_complete) begin activation<=rdata; state<=WEIGHT_READ; end
        WEIGHT_READ: if (issue) state<=WEIGHT_RESPONSE;
        WEIGHT_RESPONSE: if (memory_complete) begin weight<=rdata; state<=MULTIPLY; end
        MULTIPLY: if (mul_ready) state<=MULTIPLY_WAIT;
        MULTIPLY_WAIT: if (mul_valid) begin product<={{64{multiplied[63]}},multiplied}; state<=ACC; end
        ACC: if (acc_ready) state<=ACC_WAIT;
        ACC_WAIT: if (acc_valid) begin
          if (component==HIDDEN_SIZE-1) begin sum<=accumulated; state<=ROUND; end
          else begin component<=component+1'b1; state<=INPUT_READ; end
        end
        ROUND: if (round_ready) state<=ROUND_WAIT;
        ROUND_WAIT: if (round_valid) begin result<=rounded; state<=LOGIT; end
        LOGIT: if (logit_ready) begin
          if (vocabulary==VOCAB_SIZE-1) state<=COMPLETE;
          else begin vocabulary<=vocabulary+1'b1; component<=0; state<=INPUT_READ; end
        end
        REJECT: state<=COMPLETE;
        COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
        FAULTED: state<=FAULTED;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
