module anvil_q3_fp_token_io #(
  parameter HIDDEN_SIZE=2048, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush, cmd_valid, cmd_fp16,
  output wire cmd_ready,
  input wire cmd_project,
  input wire [31:0] cmd_token, cmd_pos,
  output wire done, error,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
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
  localparam IDLE=0, EMBED_READ=1, EMBED_RESPONSE=2, EMBED_WRITE=3, EMBED_ACK=4;
  localparam ACT_READ=5, ACT_RESPONSE=6, WEIGHT_READ=7, WEIGHT_RESPONSE=8;
  localparam MULTIPLY=9, MULTIPLY_WAIT=10, ACCUMULATE=11, ACCUMULATE_WAIT=12;
  localparam LOGIT=13, COMPLETE=14, FAULTED=15;
  reg [3:0] state;
  reg failed, fp16;
  reg [31:0] token, component, vocabulary, activation, weight, embedding, term, sum, result;
  wire unit_flush=flush || failed;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire [31:0] widened_response=anvil_q3_fp_pkg::widen16(rdata[15:0],fp16);
  wire issue=port_idle && (state==EMBED_READ || state==EMBED_WRITE ||
    state==ACT_READ || state==WEIGHT_READ);
  wire multiply_ready, multiply_valid, add_ready, add_valid;
  wire [31:0] product, accumulated;
  wire malformed=memory_complete &&
    (state==EMBED_RESPONSE || state==ACT_RESPONSE || state==WEIGHT_RESPONSE) && rdata[31:16]!=0;
  generate if (HIDDEN_SIZE<=0 || VOCAB_SIZE<=0 || MAX_SEQ_LEN<1 ||
      MAX_SEQ_LEN>32768 || 128'(VOCAB_SIZE)>128'hffffffff ||
      128'(HIDDEN_SIZE)*15>128'hffffffff ||
      128'(VOCAB_SIZE)*128'(HIDDEN_SIZE)*4>128'hffffffffffffffff) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_FP PARAMETER ERROR: token IO dimensions");
  end endgenerate
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  assign logit_valid=rst_n && !unit_flush && state==LOGIT;
  assign logit_index=rst_n && !flush ? vocabulary : 32'd0;
  assign logit_data=rst_n && !flush ? result : 32'd0;
  anvil_q3_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==EMBED_WRITE),
    .kind(state==EMBED_WRITE || state==ACT_READ ? 4'd8 : 4'd0),
    .layer(32'd0),.proj(3'd0),
    .row(state==EMBED_READ ? token : state==WEIGHT_READ ? vocabulary :
      state==ACT_READ ? 32'd14 : 32'd0),
    .col(component),.wdata(state==EMBED_WRITE ? embedding : 32'd0),.rdata(rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q3_fp_mul multiplier (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.in_valid(state==MULTIPLY),
    .in_a(activation),.in_b(weight),.in_ready(multiply_ready),
    .out_valid(multiply_valid),.out_ready(1'b1),.out_data(product),.out_flags()
  );
  anvil_q3_fp_add accumulator (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.in_valid(state==ACCUMULATE),
    .in_ready(add_ready),.in_a(sum),.in_b(term),
    .out_valid(add_valid),.out_ready(1'b1),.out_data(accumulated),.out_flags()
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; fp16<=0; token<=0; component<=0; vocabulary<=0;
      activation<=0; weight<=0; embedding<=0; term<=0; sum<=0; result<=0;
    end else if (flush) begin state<=IDLE; failed<=0; result<=0; end
    else if (!failed && (memory_fault || malformed)) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; fp16<=cmd_fp16; token<=cmd_token;
        component<=0; vocabulary<=0; sum<=0; result<=0;
        if (cmd_token>=VOCAB_SIZE || cmd_pos>=MAX_SEQ_LEN) begin failed<=1; state<=COMPLETE; end
        else if (cmd_project) state<=ACT_READ; else state<=EMBED_READ;
      end
      EMBED_READ: if (issue) state<=EMBED_RESPONSE;
      EMBED_RESPONSE: if (memory_complete) begin embedding<=rdata; state<=EMBED_WRITE; end
      EMBED_WRITE: if (issue) state<=EMBED_ACK;
      EMBED_ACK: if (memory_complete) begin
        if (component+1<HIDDEN_SIZE) begin component<=component+1'b1; state<=EMBED_READ; end
        else state<=COMPLETE;
      end
      ACT_READ: if (issue) state<=ACT_RESPONSE;
      ACT_RESPONSE: if (memory_complete) begin activation<=widened_response; state<=WEIGHT_READ; end
      WEIGHT_READ: if (issue) state<=WEIGHT_RESPONSE;
      WEIGHT_RESPONSE: if (memory_complete) begin weight<=widened_response; state<=MULTIPLY; end
      MULTIPLY: if (multiply_ready) state<=MULTIPLY_WAIT;
      MULTIPLY_WAIT: if (multiply_valid) begin term<=product; state<=ACCUMULATE; end
      ACCUMULATE: if (add_ready) state<=ACCUMULATE_WAIT;
      ACCUMULATE_WAIT: if (add_valid) begin
        sum<=accumulated;
        if (component+1<HIDDEN_SIZE) begin component<=component+1'b1; state<=ACT_READ; end
        else begin result<=accumulated; state<=LOGIT; end
      end
      LOGIT: if (logit_ready) begin
        if (vocabulary+1<VOCAB_SIZE) begin
          vocabulary<=vocabulary+1'b1; component<=0; sum<=0; state<=ACT_READ;
        end else state<=COMPLETE;
      end
      COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
      FAULTED: state<=FAULTED;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
