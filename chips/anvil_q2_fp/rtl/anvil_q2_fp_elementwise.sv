module anvil_q2_fp_elementwise #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  MAX_SEQ_LEN=32768
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
  localparam IDLE=0, READ_A=1, WAIT_A=2, READ_B=3, WAIT_B=4,
    EXP=5, WAIT_EXP=6, DENOM=7, WAIT_DENOM=8, SIGMOID=9, WAIT_SIGMOID=10,
    SILU=11, WAIT_SILU=12, PRODUCT=13, WAIT_PRODUCT=14, ADD=15, WAIT_ADD=16,
    WRITE=17, WAIT_WRITE=18, OUTPUT=19, BAD_COMMAND=20;
  reg [4:0] state;
  reg [1:0] mode;
  reg failed;
  reg [31:0] index, a, b, exponential, denominator, partial, result;
  reg issue, write;
  reg [31:0] row, write_data;
  wire idle, complete, fault;
  wire [31:0] read_data;
  reg alu_valid;
  reg [2:0] alu_op;
  reg [31:0] alu_a, alu_b;
  wire alu_ready, alu_out_valid, alu_error;
  wire [31:0] alu_result;
  wire exp_ready, exp_out_valid, exp_error;
  wire [31:0] exp_result;
  assign cmd_ready=rst_n && state==IDLE;
  assign done=rst_n && state==OUTPUT;
  assign error=done && failed;
  generate if (NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || INTERMEDIATE_SIZE<=0 ||
               MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>16777215 ||
               HIDDEN_SIZE%8!=0 || INTERMEDIATE_SIZE%8!=0 ||
               128'(NUM_LAYERS)>128'd4294967295 ||
               128'(HIDDEN_SIZE)*15>128'd4294967295 ||
               128'(INTERMEDIATE_SIZE)*15>128'd4294967295) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_FP PARAMETER ERROR: elementwise geometry");
  end endgenerate
  anvil_q2_fp_exp exp_unit(
    .clk(clk),.rst_n(rst_n),.in_valid(rst_n && state==EXP),.in_ready(exp_ready),
    .in_x({1'b1,a[30:0]}),.out_valid(exp_out_valid),.out_ready(1'b1),
    .out_data(exp_result),.out_error(exp_error));
  anvil_q2_fp_scalar arithmetic(
    .clk(clk),.rst_n(rst_n),.in_valid(alu_valid),.in_ready(alu_ready),
    .in_op(alu_op),.in_a(alu_a),.in_b(alu_b),.out_valid(alu_out_valid),
    .out_ready(1'b1),.out_data(alu_result),.out_error(alu_error));
  anvil_q2_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(write),.kind(4'd8),.layer(32'd0),
    .proj(3'd0),.row(row),.col(index),.wdata(write_data),
    .idle(idle),.complete(complete),.rdata(read_data),.fault(fault),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
  always @* begin
    issue=0; write=0; row=0; write_data=0;
    if (rst_n && idle) case (state)
      READ_A: begin issue=1; row=mode==0 ? 0 : (mode==1 ? 7 : 9); end
      READ_B: begin issue=1; row=mode==0 ? 6 : (mode==1 ? 12 : 10); end
      WRITE: begin
        issue=1; write=1; row=mode==0 ? 7 : (mode==1 ? 0 : 11); write_data=result;
      end
      default: begin end
    endcase
  end
  always @* begin
    alu_valid=0; alu_op=0; alu_a=0; alu_b=0;
    if (rst_n) case (state)
      ADD: begin alu_valid=1; alu_a=a; alu_b=b; end
      DENOM: begin alu_valid=1; alu_a=FP_ONE; alu_b=exponential; end
      SIGMOID: begin
        alu_valid=1; alu_op=2; alu_a=a[31] ? exponential : FP_ONE; alu_b=denominator;
      end
      SILU: begin alu_valid=1; alu_op=1; alu_a=a; alu_b=partial; end
      PRODUCT: begin alu_valid=1; alu_op=1; alu_a=partial; alu_b=b; end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; mode<=0; failed<=0; index<=0; a<=0; b<=0;
      exponential<=0; denominator<=0; partial<=0; result<=0;
    end else if (fault || (alu_out_valid && alu_error) || (exp_out_valid && exp_error)) begin
      failed<=1; state<=OUTPUT;
    end else case (state)
      IDLE: if (cmd_valid) begin
        mode<=cmd_mode; failed<=0; index<=0;
        if (cmd_mode>2 || cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin
          failed<=1; state<=BAD_COMMAND;
        end else state<=READ_A;
      end
      READ_A: if (issue) state<=WAIT_A;
      WAIT_A: if (complete) begin
        if (!fp_is_finite(read_data)) begin failed<=1; state<=OUTPUT; end
        else begin a<=read_data; state<=READ_B; end
      end
      READ_B: if (issue) state<=WAIT_B;
      WAIT_B: if (complete) begin
        if (!fp_is_finite(read_data)) begin failed<=1; state<=OUTPUT; end
        else begin b<=read_data; if (mode==2) state<=EXP; else state<=ADD; end
      end
      EXP: if (exp_ready) state<=WAIT_EXP;
      WAIT_EXP: if (exp_out_valid) begin exponential<=exp_result; state<=DENOM; end
      DENOM: if (alu_ready) state<=WAIT_DENOM;
      WAIT_DENOM: if (alu_out_valid) begin denominator<=alu_result; state<=SIGMOID; end
      SIGMOID: if (alu_ready) state<=WAIT_SIGMOID;
      WAIT_SIGMOID: if (alu_out_valid) begin partial<=alu_result; state<=SILU; end
      SILU: if (alu_ready) state<=WAIT_SILU;
      WAIT_SILU: if (alu_out_valid) begin partial<=alu_result; state<=PRODUCT; end
      PRODUCT: if (alu_ready) state<=WAIT_PRODUCT;
      WAIT_PRODUCT: if (alu_out_valid) begin result<=alu_result; state<=WRITE; end
      ADD: if (alu_ready) state<=WAIT_ADD;
      WAIT_ADD: if (alu_out_valid) begin result<=alu_result; state<=WRITE; end
      WRITE: if (issue) state<=WAIT_WRITE;
      WAIT_WRITE: if (complete) begin
        if (index+1<(mode==2 ? INTERMEDIATE_SIZE : HIDDEN_SIZE)) begin
          index<=index+1; state<=READ_A;
        end else state<=OUTPUT;
      end
      BAD_COMMAND: state<=OUTPUT;
      OUTPUT: state<=IDLE;
      default: begin failed<=1; state<=OUTPUT; end
    endcase
  end
endmodule
