module anvil_q4_fp_elementwise (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [1:0] cmd_operation,
  input wire [31:0] cmd_count, cmd_source0, cmd_source1, cmd_target, scratch_stride,
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
  localparam [3:0] IDLE=0, READ0=1, WAIT0=2, READ1=3, WAIT1=4,
    SILU_ISSUE=5, SILU_WAIT=6, FP_ISSUE=7, FP_WAIT=8,
    WRITE=9, WRITE_WAIT=10, COMPLETE=11;
  reg [3:0] state;
  reg [1:0] operation;
  reg [31:0] count, source0, source1, target, stride, index, a, b, result_register;
  reg failed;
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire issue=(state==READ0 || state==READ1 || state==WRITE) && port_idle;
  anvil_q4_fp_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(state==WRITE),.kind(4'd8),.layer(32'd0),.proj(3'd0),
    .row(state==READ0 ? source0 : state==READ1 ? source1 : target),
    .col(index),.wdata(state==WRITE ? result_register : 32'd0),
    .stride(stride),.rdata(rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_stride(mem_req_stride),.mem_rsp_valid(mem_rsp_valid),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  wire silu_ready, silu_valid, fp_ready, fp_valid;
  wire [31:0] silu_result, fp_result;
  wire [4:0] silu_flags, fp_flags;
  anvil_q4_fp_silu silu (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==SILU_ISSUE),.in_ready(silu_ready),.x(a),
    .out_valid(silu_valid),.out_ready(state==SILU_WAIT),
    .result(silu_result),.flags(silu_flags)
  );
  anvil_q4_fp32 arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==FP_ISSUE),.in_ready(fp_ready),
    .op(operation==0 ? 4'd0 : 4'd2),.a(a),.b(b),
    .out_valid(fp_valid),.out_ready(state==FP_WAIT),.result(fp_result),.flags(fp_flags)
  );
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; operation<=0; count<=0; source0<=0; source1<=0;
      target<=0; stride<=0; index<=0; a<=0; b<=0; result_register<=0; failed<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (fault) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        operation<=cmd_operation; count<=cmd_count; source0<=cmd_source0;
        source1<=cmd_source1; target<=cmd_target; stride<=scratch_stride; index<=0; failed<=0;
        if (cmd_operation>2 || cmd_count==0 || cmd_count>scratch_stride ||
            scratch_stride>32768 || cmd_source0>=15 || cmd_source0==13 ||
            cmd_target>=15 || cmd_target==13 ||
            (cmd_operation!=2 && (cmd_source1>=15 || cmd_source1==13))) begin
          failed<=1; state<=COMPLETE;
        end else state<=READ0;
      end
      READ0: if (issue) state<=WAIT0;
      WAIT0: if (complete) begin
        a<=rdata;
        if (operation==2) begin result_register<=rdata; state<=WRITE; end
        else state<=READ1;
      end
      READ1: if (issue) state<=WAIT1;
      WAIT1: if (complete) begin
        b<=rdata;
        if (operation==1) state<=SILU_ISSUE;
        else state<=FP_ISSUE;
      end
      SILU_ISSUE: if (silu_ready) state<=SILU_WAIT;
      SILU_WAIT: if (silu_valid) begin a<=silu_result; state<=FP_ISSUE; end
      FP_ISSUE: if (fp_ready) state<=FP_WAIT;
      FP_WAIT: if (fp_valid) begin result_register<=fp_result; state<=WRITE; end
      WRITE: if (issue) state<=WRITE_WAIT;
      WRITE_WAIT: if (complete) begin
        if (index+1<count) begin index<=index+1'b1; state<=READ0; end
        else state<=COMPLETE;
      end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
