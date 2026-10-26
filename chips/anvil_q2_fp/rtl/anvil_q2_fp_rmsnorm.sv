module anvil_q2_fp_rmsnorm #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, MAX_SEQ_LEN=32768, FP_FORMAT=0
)(
  input wire clk, rst_n, cmd_valid, output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, input wire [1:0] cmd_mode,
  output wire done, error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  import anvil_q2_fp_pkg::*;
  localparam IDLE=0, READ_X=1, WAIT_X=2, SQUARE=3, WAIT_SQUARE=4,
    SUM=5, WAIT_SUM=6, MEAN=7, WAIT_MEAN=8, EPSILON=9, WAIT_EPSILON=10,
    ROOT=11, WAIT_ROOT=12, INVERSE=13, WAIT_INVERSE=14,
    READ_SECOND=15, WAIT_SECOND=16, READ_GAMMA=17, WAIT_GAMMA=18,
    NORMALIZE=19, WAIT_NORMALIZE=20, GAMMA=21, WAIT_PRODUCT=22,
    WRITE=23, WAIT_WRITE=24, OUTPUT=25, BAD_COMMAND=26;
  reg [4:0] state;
  reg failed;
  reg [31:0] layer, index, source_slot, target_slot;
  reg [3:0] norm_kind;
  reg [31:0] x, gamma, sum, partial, inverse, result;
  reg issue, write;
  reg [3:0] kind;
  reg [31:0] address_layer, row, write_data;
  wire idle, complete, fault;
  wire [31:0] read_data;
  reg alu_valid;
  wire alu_ready, alu_out_valid, alu_error;
  reg [2:0] alu_op;
  reg [31:0] alu_a, alu_b;
  wire [31:0] alu_result;
  assign cmd_ready=rst_n && state==IDLE;
  assign done=rst_n && state==OUTPUT;
  assign error=done && failed;
  generate if (NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || HIDDEN_SIZE%8!=0 ||
               MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>16777215 ||
               128'(HIDDEN_SIZE)*128'(HIDDEN_SIZE)>128'd4294967295 ||
               128'(NUM_LAYERS)>128'd4294967295 ||
               (FP_FORMAT!=0 && FP_FORMAT!=1)) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_FP PARAMETER ERROR: RMSNorm geometry");
  end endgenerate
  anvil_q2_fp_scalar arithmetic(
    .clk(clk),.rst_n(rst_n),.in_valid(alu_valid),.in_ready(alu_ready),
    .in_op(alu_op),.in_a(alu_a),.in_b(alu_b),.out_valid(alu_out_valid),
    .out_ready(1'b1),.out_data(alu_result),.out_error(alu_error));
  anvil_q2_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(write),.kind(kind),
    .layer(address_layer),.proj(3'd0),.row(row),.col(index),.wdata(write_data),
    .idle(idle),.complete(complete),.rdata(read_data),.fault(fault),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
  always @* begin
    issue=0; write=0; kind=0; address_layer=0; row=0; write_data=0;
    if (rst_n && idle) case (state)
      READ_X,READ_SECOND: begin issue=1; kind=8; row=source_slot; end
      READ_GAMMA: begin
        issue=1; kind=norm_kind; address_layer=norm_kind==7 ? 0 : layer;
      end
      WRITE: begin issue=1; write=1; kind=8; row=target_slot; write_data=result; end
      default: begin end
    endcase
  end
  always @* begin
    alu_valid=0; alu_op=0; alu_a=0; alu_b=0;
    if (rst_n) case (state)
      SQUARE: begin alu_valid=1; alu_op=1; alu_a=x; alu_b=x; end
      SUM: begin alu_valid=1; alu_a=sum; alu_b=partial; end
      MEAN: begin alu_valid=1; alu_op=2; alu_a=sum; alu_b=fp_from_int(HIDDEN_SIZE); end
      EPSILON: begin alu_valid=1; alu_a=partial; alu_b=FP_EPS; end
      ROOT: begin alu_valid=1; alu_op=3; alu_a=partial; end
      INVERSE: begin alu_valid=1; alu_op=2; alu_a=FP_ONE; alu_b=partial; end
      NORMALIZE: begin alu_valid=1; alu_op=1; alu_a=x; alu_b=inverse; end
      GAMMA: begin alu_valid=1; alu_op=1; alu_a=partial; alu_b=gamma; end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; layer<=0; index<=0; source_slot<=0; target_slot<=0;
      norm_kind<=0; x<=0; gamma<=0; sum<=0; partial<=0; inverse<=0; result<=0;
    end else if (fault || (alu_out_valid && alu_error)) begin failed<=1; state<=OUTPUT; end
    else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; layer<=cmd_layer; index<=0; sum<=0;
        if (cmd_mode>2 || cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin
          failed<=1; state<=BAD_COMMAND;
        end else begin
          source_slot<=cmd_mode==1 ? 7 : 0;
          target_slot<=cmd_mode==0 ? 1 : (cmd_mode==1 ? 8 : 14);
          norm_kind<=cmd_mode==0 ? 5 : (cmd_mode==1 ? 6 : 7); state<=READ_X;
        end
      end
      READ_X: if (issue) state<=WAIT_X;
      WAIT_X: if (complete) begin
        if (!fp_is_finite(read_data)) begin failed<=1; state<=OUTPUT; end
        else begin x<=read_data; state<=SQUARE; end
      end
      SQUARE: if (alu_ready) state<=WAIT_SQUARE;
      WAIT_SQUARE: if (alu_out_valid) begin partial<=alu_result; state<=SUM; end
      SUM: if (alu_ready) state<=WAIT_SUM;
      WAIT_SUM: if (alu_out_valid) begin
        sum<=alu_result;
        if (index+1<HIDDEN_SIZE) begin index<=index+1; state<=READ_X; end
        else state<=MEAN;
      end
      MEAN: if (alu_ready) state<=WAIT_MEAN;
      WAIT_MEAN: if (alu_out_valid) begin partial<=alu_result; state<=EPSILON; end
      EPSILON: if (alu_ready) state<=WAIT_EPSILON;
      WAIT_EPSILON: if (alu_out_valid) begin partial<=alu_result; state<=ROOT; end
      ROOT: if (alu_ready) state<=WAIT_ROOT;
      WAIT_ROOT: if (alu_out_valid) begin partial<=alu_result; state<=INVERSE; end
      INVERSE: if (alu_ready) state<=WAIT_INVERSE;
      WAIT_INVERSE: if (alu_out_valid) begin inverse<=alu_result; index<=0; state<=READ_SECOND; end
      READ_SECOND: if (issue) state<=WAIT_SECOND;
      WAIT_SECOND: if (complete) begin
        if (!fp_is_finite(read_data)) begin failed<=1; state<=OUTPUT; end
        else begin x<=read_data; state<=READ_GAMMA; end
      end
      READ_GAMMA: if (issue) state<=WAIT_GAMMA;
      WAIT_GAMMA: if (complete) begin
        if (read_data[31:16]!=0 ||
            !fp_is_finite(expand16(read_data[15:0],FP_FORMAT))) begin
          failed<=1; state<=OUTPUT;
        end else begin gamma<=expand16(read_data[15:0],FP_FORMAT); state<=NORMALIZE; end
      end
      NORMALIZE: if (alu_ready) state<=WAIT_NORMALIZE;
      WAIT_NORMALIZE: if (alu_out_valid) begin partial<=alu_result; state<=GAMMA; end
      GAMMA: if (alu_ready) state<=WAIT_PRODUCT;
      WAIT_PRODUCT: if (alu_out_valid) begin result<=alu_result; state<=WRITE; end
      WRITE: if (issue) state<=WAIT_WRITE;
      WAIT_WRITE: if (complete) begin
        if (index+1<HIDDEN_SIZE) begin index<=index+1; state<=READ_SECOND; end
        else state<=OUTPUT;
      end
      BAD_COMMAND: state<=OUTPUT;
      OUTPUT: state<=IDLE;
      default: begin failed<=1; state<=OUTPUT; end
    endcase
  end
endmodule
