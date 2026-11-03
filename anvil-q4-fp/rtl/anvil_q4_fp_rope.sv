module anvil_q4_fp_rope (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_pos, cmd_generation, cmd_slot, cmd_heads,
  input wire [31:0] head_dim, hidden, intermediate,
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
  localparam [4:0] IDLE=0, READ_X0=1, WAIT_X0=2, READ_X1=3, WAIT_X1=4,
    READ_COS=5, WAIT_COS=6, READ_SIN=7, WAIT_SIN=8, MUL_ISSUE=9,
    MUL_WAIT=10, SUB_ISSUE=11, SUB_WAIT=12, ADD_ISSUE=13, ADD_WAIT=14,
    WRITE_X0=15, WRITE_WAIT0=16, WRITE_X1=17, WRITE_WAIT1=18, COMPLETE=19;
  reg [4:0] state;
  reg [31:0] position, generation, slot, heads, dimension, stride;
  reg [31:0] head, base, pair_index, x0, x1, cosine, sine;
  reg [31:0] p0, p1, p2, p3, y0, y1;
  reg [1:0] product_index;
  reg failed;
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire coefficient_read=state==READ_COS || state==READ_SIN;
  wire second_half=state==READ_X1 || state==WRITE_X1;
  wire writing=state==WRITE_X0 || state==WRITE_X1;
  wire issue=(state==READ_X0 || state==READ_X1 || coefficient_read || writing) && port_idle;
  wire [31:0] scratch_col=base+pair_index+(second_half ? dimension>>1 : 32'd0);
  anvil_q4_fp_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(writing),.kind(coefficient_read ? 4'd11 : 4'd8),
    .layer(coefficient_read ? generation : 32'd0),.proj(3'd0),
    .row(coefficient_read ? position : slot),
    .col(coefficient_read ? (pair_index<<1)+(state==READ_SIN ? 32'd1 : 32'd0) : scratch_col),
    .wdata(state==WRITE_X0 ? y0 : state==WRITE_X1 ? y1 : 32'd0),
    .stride(coefficient_read ? dimension : stride),.rdata(rdata),
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
  wire [31:0] left=state==MUL_ISSUE ?
    (product_index==0 || product_index==2 ? x0 : x1) : state==SUB_ISSUE ? p0 : p2;
  wire [31:0] right=state==MUL_ISSUE ?
    (product_index==0 || product_index==3 ? cosine : sine) : state==SUB_ISSUE ? p1 : p3;
  anvil_q4_fp32 arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MUL_ISSUE || state==SUB_ISSUE || state==ADD_ISSUE),
    .in_ready(fp_ready),.op(state==MUL_ISSUE ? 4'd2 : state==SUB_ISSUE ? 4'd1 : 4'd0),
    .a(left),.b(right),.out_valid(fp_valid),
    .out_ready(state==MUL_WAIT || state==SUB_WAIT || state==ADD_WAIT),
    .result(fp_result),.flags(fp_flags)
  );
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; position<=0; generation<=0; slot<=0; heads<=0; dimension<=0;
      stride<=0; head<=0; base<=0; pair_index<=0; x0<=0; x1<=0;
      cosine<=0; sine<=0; p0<=0; p1<=0; p2<=0; p3<=0;
      y0<=0; y1<=0; product_index<=0; failed<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (fault) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        position<=cmd_pos; generation<=cmd_generation; slot<=cmd_slot; heads<=cmd_heads;
        dimension<=head_dim; stride<=hidden>intermediate ? hidden : intermediate;
        head<=0; base<=0; pair_index<=0; failed<=0;
        if ((cmd_slot!=2 && cmd_slot!=3) || cmd_heads==0 || cmd_heads>128 ||
            head_dim<2 || head_dim>256 || head_dim[0] ||
            hidden<2 || hidden>8192 || intermediate<1 || intermediate>32768) begin
          failed<=1; state<=COMPLETE;
        end else state<=READ_X0;
      end
      READ_X0: if (issue) state<=WAIT_X0;
      WAIT_X0: if (complete) begin x0<=rdata; state<=READ_X1; end
      READ_X1: if (issue) state<=WAIT_X1;
      WAIT_X1: if (complete) begin x1<=rdata; state<=READ_COS; end
      READ_COS: if (issue) state<=WAIT_COS;
      WAIT_COS: if (complete) begin cosine<=rdata; state<=READ_SIN; end
      READ_SIN: if (issue) state<=WAIT_SIN;
      WAIT_SIN: if (complete) begin sine<=rdata; product_index<=0; state<=MUL_ISSUE; end
      MUL_ISSUE: if (fp_ready) state<=MUL_WAIT;
      MUL_WAIT: if (fp_valid) begin
        case (product_index)
          0: p0<=fp_result;
          1: p1<=fp_result;
          2: p2<=fp_result;
          3: p3<=fp_result;
        endcase
        if (product_index==3) state<=SUB_ISSUE;
        else begin product_index<=product_index+1'b1; state<=MUL_ISSUE; end
      end
      SUB_ISSUE: if (fp_ready) state<=SUB_WAIT;
      SUB_WAIT: if (fp_valid) begin y0<=fp_result; state<=ADD_ISSUE; end
      ADD_ISSUE: if (fp_ready) state<=ADD_WAIT;
      ADD_WAIT: if (fp_valid) begin y1<=fp_result; state<=WRITE_X0; end
      WRITE_X0: if (issue) state<=WRITE_WAIT0;
      WRITE_WAIT0: if (complete) state<=WRITE_X1;
      WRITE_X1: if (issue) state<=WRITE_WAIT1;
      WRITE_WAIT1: if (complete) begin
        if (pair_index+1<(dimension>>1)) begin pair_index<=pair_index+1'b1; state<=READ_X0; end
        else if (head+1<heads) begin
          head<=head+1'b1; base<=base+dimension; pair_index<=0; state<=READ_X0;
        end else state<=COMPLETE;
      end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
