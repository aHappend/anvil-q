module anvil_q4_parent_rmsnorm (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, hidden, intermediate, epsilon,
  input wire activation_format,
  input wire [1:0] cmd_mode,
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
  localparam [5:0] IDLE=0, SUM_READ=1, SUM_WAIT=2,
    SQUARE_ISSUE=3, SQUARE_WAIT=4, ADD_ISSUE=5, ADD_WAIT=6,
    H_ISSUE=7, H_WAIT=8, MEAN_ISSUE=9, MEAN_WAIT=10,
    EPS_ISSUE=11, EPS_WAIT=12, ROOT_ISSUE=13, ROOT_WAIT=14,
    X_READ=15, X_WAIT=16, GAMMA_READ=17, GAMMA_WAIT=18,
    WIDEN_ISSUE=19, WIDEN_WAIT=20, MUL_ISSUE=21, MUL_WAIT=22,
    DIV_ISSUE=23, DIV_WAIT=24, WRITE=25, WRITE_WAIT=26, COMPLETE=27;
  reg [5:0] state;
  reg [31:0] layer, count, stride, eps, index, source_slot, target_slot;
  reg [31:0] x, operand, sum, root, h_float, result_register;
  reg [3:0] gamma_kind;
  reg native_fp16, failed;
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire reading_gamma=state==GAMMA_READ;
  wire writing=state==WRITE;
  wire issue=(state==SUM_READ || state==X_READ || reading_gamma || writing) && port_idle;
  anvil_q4_parent_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(writing),.kind(reading_gamma ? gamma_kind : 4'd8),
    .layer(reading_gamma && gamma_kind!=7 ? layer : 32'd0),.proj(3'd0),
    .row(reading_gamma ? 32'd0 : writing ? target_slot : source_slot),
    .col(index),.wdata(writing ? result_register : 32'd0),
    .stride(reading_gamma ? count : stride),.rdata(rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_stride(mem_req_stride),.mem_rsp_valid(mem_rsp_valid),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  wire fp_ready, fp_valid;
  wire [31:0] fp_result;
  wire [4:0] fp_flags;
  wire fp_issue=state==SQUARE_ISSUE || state==ADD_ISSUE || state==H_ISSUE ||
    state==MEAN_ISSUE || state==EPS_ISSUE || state==ROOT_ISSUE ||
    state==WIDEN_ISSUE || state==MUL_ISSUE || state==DIV_ISSUE;
  wire fp_wait=state==SQUARE_WAIT || state==ADD_WAIT || state==H_WAIT ||
    state==MEAN_WAIT || state==EPS_WAIT || state==ROOT_WAIT ||
    state==WIDEN_WAIT || state==MUL_WAIT || state==DIV_WAIT;
  wire [3:0] operation=state==SQUARE_ISSUE || state==MUL_ISSUE ? 4'd2 :
    state==ADD_ISSUE || state==EPS_ISSUE ? 4'd0 : state==H_ISSUE ? 4'd9 :
    state==ROOT_ISSUE ? 4'd4 : state==WIDEN_ISSUE ?
      (native_fp16 ? 4'd6 : 4'd5) : 4'd3;
  wire [31:0] left=state==H_ISSUE ? count :
    state==SQUARE_ISSUE || state==MUL_ISSUE ? x :
    state==ADD_ISSUE || state==MEAN_ISSUE || state==EPS_ISSUE ? sum : operand;
  wire [31:0] right=state==SQUARE_ISSUE ? x : state==ADD_ISSUE ? operand :
    state==MEAN_ISSUE ? h_float : state==EPS_ISSUE ? eps :
    state==DIV_ISSUE ? root : operand;
  anvil_q4_parent_fp32 arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(fp_issue),.in_ready(fp_ready),.op(operation),.a(left),.b(right),
    .out_valid(fp_valid),.out_ready(fp_wait),.result(fp_result),.flags(fp_flags)
  );
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; layer<=0; count<=0; stride<=0; eps<=0; index<=0;
      source_slot<=0; target_slot<=0; x<=0; operand<=0; sum<=0;
      root<=0; h_float<=0; result_register<=0;
      gamma_kind<=0; native_fp16<=0; failed<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (fault) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        layer<=cmd_layer; count<=hidden; stride<=hidden>intermediate ? hidden : intermediate;
        eps<=epsilon; index<=0; sum<=0; native_fp16<=activation_format; failed<=0;
        source_slot<=cmd_mode==1 ? 32'd7 : 32'd0;
        target_slot<=cmd_mode==0 ? 32'd1 : cmd_mode==1 ? 32'd8 : 32'd14;
        gamma_kind<=cmd_mode==0 ? 4'd5 : cmd_mode==1 ? 4'd6 : 4'd7;
        if (hidden<2 || hidden>8192 || intermediate<1 || intermediate>32768 ||
            cmd_mode>2) begin failed<=1; state<=COMPLETE; end
        else state<=SUM_READ;
      end
      SUM_READ: if (issue) state<=SUM_WAIT;
      SUM_WAIT: if (complete) begin x<=rdata; state<=SQUARE_ISSUE; end
      SQUARE_ISSUE: if (fp_ready) state<=SQUARE_WAIT;
      SQUARE_WAIT: if (fp_valid) begin operand<=fp_result; state<=ADD_ISSUE; end
      ADD_ISSUE: if (fp_ready) state<=ADD_WAIT;
      ADD_WAIT: if (fp_valid) begin
        sum<=fp_result;
        if (index+1<count) begin index<=index+1'b1; state<=SUM_READ; end
        else state<=H_ISSUE;
      end
      H_ISSUE: if (fp_ready) state<=H_WAIT;
      H_WAIT: if (fp_valid) begin h_float<=fp_result; state<=MEAN_ISSUE; end
      MEAN_ISSUE: if (fp_ready) state<=MEAN_WAIT;
      MEAN_WAIT: if (fp_valid) begin sum<=fp_result; state<=EPS_ISSUE; end
      EPS_ISSUE: if (fp_ready) state<=EPS_WAIT;
      EPS_WAIT: if (fp_valid) begin operand<=fp_result; state<=ROOT_ISSUE; end
      ROOT_ISSUE: if (fp_ready) state<=ROOT_WAIT;
      ROOT_WAIT: if (fp_valid) begin root<=fp_result; index<=0; state<=X_READ; end
      X_READ: if (issue) state<=X_WAIT;
      X_WAIT: if (complete) begin x<=rdata; state<=GAMMA_READ; end
      GAMMA_READ: if (issue) state<=GAMMA_WAIT;
      GAMMA_WAIT: if (complete) begin
        if (rdata[31:16]!=0) begin failed<=1; state<=COMPLETE; end
        else begin operand<=rdata; state<=WIDEN_ISSUE; end
      end
      WIDEN_ISSUE: if (fp_ready) state<=WIDEN_WAIT;
      WIDEN_WAIT: if (fp_valid) begin operand<=fp_result; state<=MUL_ISSUE; end
      MUL_ISSUE: if (fp_ready) state<=MUL_WAIT;
      MUL_WAIT: if (fp_valid) begin operand<=fp_result; state<=DIV_ISSUE; end
      DIV_ISSUE: if (fp_ready) state<=DIV_WAIT;
      DIV_WAIT: if (fp_valid) begin result_register<=fp_result; state<=WRITE; end
      WRITE: if (issue) state<=WRITE_WAIT;
      WRITE_WAIT: if (complete) begin
        if (index+1<count) begin index<=index+1'b1; state<=X_READ; end
        else state<=COMPLETE;
      end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
