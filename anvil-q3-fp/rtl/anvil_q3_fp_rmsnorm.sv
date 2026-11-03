module anvil_q3_fp_rmsnorm #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush, cmd_valid, cmd_fp16,
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
  localparam IDLE=0, SUM_READ=1, SUM_RESPONSE=2, SQUARE=3, SQUARE_WAIT=4;
  localparam ACCUMULATE=5, ACCUMULATE_WAIT=6, MEAN_DIVIDE=7, MEAN_WAIT=8;
  localparam EPS_ADD=9, EPS_WAIT=10, ROOT=11, ROOT_WAIT=12;
  localparam RECIP_DIVIDE=13, RECIP_WAIT=14, X_READ=15, X_RESPONSE=16;
  localparam GAMMA_READ=17, GAMMA_RESPONSE=18, GAMMA_MUL=19, GAMMA_WAIT=20;
  localparam RECIP_MUL=21, RECIP_MUL_WAIT=22, ROUND=23, WRITE=24;
  localparam WRITE_RESPONSE=25, COMPLETE=26, FAULTED=27;
  localparam [31:0] DIMENSION_FP=anvil_q3_fp_pkg::uint32_to_fp32(32'(HIDDEN_SIZE));
  reg [4:0] state;
  reg failed, fp16;
  reg [31:0] layer, index, source_slot, target_slot, result;
  reg [3:0] norm_kind;
  reg [31:0] x, gamma, scaled_x, reciprocal, denominator, square, sum, mean, scaled_result;
  wire unit_flush=flush || failed;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire [31:0] widened_response=anvil_q3_fp_pkg::widen16(rdata[15:0],fp16);
  wire [20:0] narrowed_result=anvil_q3_fp_pkg::narrow16(scaled_result,fp16);
  wire issue=port_idle && (state==SUM_READ || state==X_READ ||
    state==GAMMA_READ || state==WRITE);
  wire malformed=memory_complete &&
    (state==SUM_RESPONSE || state==X_RESPONSE || state==GAMMA_RESPONSE) && rdata[31:16]!=0;
  wire multiply_ready, multiply_valid, add_ready, add_valid;
  wire divide_ready, divide_done, divide_error, root_ready, root_done, root_error;
  wire [31:0] product, added, quotient, root;
  generate if (NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || MAX_SEQ_LEN<1 ||
      MAX_SEQ_LEN>32768 || 128'(NUM_LAYERS)>128'hffffffff ||
      128'(HIDDEN_SIZE)*15>128'hffffffff) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_FP PARAMETER ERROR: RMSNorm dimensions");
  end endgenerate
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  anvil_q3_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==WRITE),.kind(state==GAMMA_READ ? norm_kind : 4'd8),
    .layer(state==GAMMA_READ && norm_kind!=7 ? layer : 32'd0),.proj(3'd0),
    .row(state==GAMMA_READ ? 32'd0 : state==WRITE ? target_slot : source_slot),
    .col(index),.wdata(state==WRITE ? result : 32'd0),.rdata(rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q3_fp_mul multiplier (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .in_valid(state==SQUARE || state==GAMMA_MUL || state==RECIP_MUL),
    .in_a(state==RECIP_MUL ? scaled_x : x),
    .in_b(state==SQUARE ? x : state==GAMMA_MUL ? gamma : reciprocal),
    .in_ready(multiply_ready),.out_valid(multiply_valid),.out_ready(1'b1),
    .out_data(product),.out_flags()
  );
  anvil_q3_fp_add adder (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .in_valid(state==ACCUMULATE || state==EPS_ADD),.in_ready(add_ready),
    .in_a(state==EPS_ADD ? mean : sum),
    .in_b(state==EPS_ADD ? 32'h358637bd : square),
    .out_valid(add_valid),.out_ready(1'b1),.out_data(added),.out_flags()
  );
  anvil_q3_fp_divider divider (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),
    .start(state==MEAN_DIVIDE || state==RECIP_DIVIDE),
    .numerator(state==MEAN_DIVIDE ? sum : 32'h3f800000),
    .denominator(state==MEAN_DIVIDE ? DIMENSION_FP : denominator),
    .ready(divide_ready),.done(divide_done),.error(divide_error),
    .quotient(quotient),.flags()
  );
  anvil_q3_fp_sqrt square_root (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.start(state==ROOT),
    .radicand(mean),.ready(root_ready),.done(root_done),.error(root_error),
    .value(root),.flags()
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; fp16<=0; layer<=0; index<=0;
      source_slot<=0; target_slot<=0; result<=0; norm_kind<=0;
      x<=0; gamma<=0; scaled_x<=0; reciprocal<=0; denominator<=0;
      square<=0; sum<=0; mean<=0; scaled_result<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (!failed && (memory_fault || malformed ||
        (divide_done && divide_error) || (root_done && root_error))) begin
      failed<=1; state<=COMPLETE;
    end else case (state)
      IDLE: if (cmd_valid) begin
        layer<=cmd_layer; index<=0; sum<=0; failed<=0; fp16<=cmd_fp16;
        source_slot<=cmd_mode==1 ? 7 : 0;
        target_slot<=cmd_mode==0 ? 1 : cmd_mode==1 ? 8 : 14;
        norm_kind<=cmd_mode==0 ? 5 : cmd_mode==1 ? 6 : 7;
        if (cmd_mode>2 || cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin
          failed<=1; state<=COMPLETE;
        end else state<=SUM_READ;
      end
      SUM_READ: if (issue) state<=SUM_RESPONSE;
      SUM_RESPONSE: if (memory_complete) begin x<=widened_response; state<=SQUARE; end
      SQUARE: if (multiply_ready) state<=SQUARE_WAIT;
      SQUARE_WAIT: if (multiply_valid) begin square<=product; state<=ACCUMULATE; end
      ACCUMULATE: if (add_ready) state<=ACCUMULATE_WAIT;
      ACCUMULATE_WAIT: if (add_valid) begin
        sum<=added;
        if (index+1<HIDDEN_SIZE) begin index<=index+1'b1; state<=SUM_READ; end
        else state<=MEAN_DIVIDE;
      end
      MEAN_DIVIDE: if (divide_ready) state<=MEAN_WAIT;
      MEAN_WAIT: if (divide_done) begin mean<=quotient; state<=EPS_ADD; end
      EPS_ADD: if (add_ready) state<=EPS_WAIT;
      EPS_WAIT: if (add_valid) begin mean<=added; state<=ROOT; end
      ROOT: if (root_ready) state<=ROOT_WAIT;
      ROOT_WAIT: if (root_done) begin denominator<=root; state<=RECIP_DIVIDE; end
      RECIP_DIVIDE: if (divide_ready) state<=RECIP_WAIT;
      RECIP_WAIT: if (divide_done) begin reciprocal<=quotient; index<=0; state<=X_READ; end
      X_READ: if (issue) state<=X_RESPONSE;
      X_RESPONSE: if (memory_complete) begin x<=widened_response; state<=GAMMA_READ; end
      GAMMA_READ: if (issue) state<=GAMMA_RESPONSE;
      GAMMA_RESPONSE: if (memory_complete) begin gamma<=widened_response; state<=GAMMA_MUL; end
      GAMMA_MUL: if (multiply_ready) state<=GAMMA_WAIT;
      GAMMA_WAIT: if (multiply_valid) begin scaled_x<=product; state<=RECIP_MUL; end
      RECIP_MUL: if (multiply_ready) state<=RECIP_MUL_WAIT;
      RECIP_MUL_WAIT: if (multiply_valid) begin scaled_result<=product; state<=ROUND; end
      ROUND: begin result<={16'd0,narrowed_result[15:0]}; state<=WRITE; end
      WRITE: if (issue) state<=WRITE_RESPONSE;
      WRITE_RESPONSE: if (memory_complete) begin
        if (index+1<HIDDEN_SIZE) begin index<=index+1'b1; state<=X_READ; end
        else state<=COMPLETE;
      end
      COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
      FAULTED: state<=FAULTED;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
