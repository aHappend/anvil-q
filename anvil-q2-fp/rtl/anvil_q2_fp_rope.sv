module anvil_q2_fp_rope #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, NUM_Q_HEADS=12,
  NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768
)(
  input wire clk, rst_n, cmd_valid, output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, output wire done, error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  import anvil_q2_fp_pkg::*;
  localparam IDLE=0, READ_X=1, WAIT_X=2, READ_Y=3, WAIT_Y=4,
    READ_COS=5, WAIT_COS=6, READ_SIN=7, WAIT_SIN=8,
    MUL_XC=9, WAIT_XC=10, MUL_YS=11, WAIT_YS=12, SUB=13, WAIT_SUB=14,
    MUL_YC=15, WAIT_YC=16, MUL_XS=17, WAIT_XS=18, ADD=19, WAIT_ADD=20,
    WRITE_X=21, WAIT_WRITE_X=22, WRITE_Y=23, WAIT_WRITE_Y=24,
    OUTPUT=25, BAD_COMMAND=26;
  localparam HALF=HEAD_DIM >> 1;
  reg [4:0] state;
  reg failed, key_vector;
  reg [31:0] position, head, head_base, pair_index;
  reg [31:0] x, y, cosine, sine, product1, product2, rotated_x, rotated_y;
  reg issue, write;
  reg [3:0] kind;
  reg [31:0] row, col, write_data;
  wire idle, complete, fault;
  wire [31:0] read_data;
  reg alu_valid;
  reg [2:0] alu_op;
  reg [31:0] alu_a, alu_b;
  wire alu_ready, alu_out_valid, alu_error;
  wire [31:0] alu_result;
  anvil_q2_fp_parameters #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(HIDDEN_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .GROUP_SIZE(1),.VOCAB_SIZE(1),.MAX_SEQ_LEN(MAX_SEQ_LEN),.CACHE_BLOCK(1)) parameters_ok();
  assign cmd_ready=rst_n && state==IDLE;
  assign done=rst_n && state==OUTPUT;
  assign error=done && failed;
  anvil_q2_fp_scalar arithmetic(
    .clk(clk),.rst_n(rst_n),.in_valid(alu_valid),.in_ready(alu_ready),
    .in_op(alu_op),.in_a(alu_a),.in_b(alu_b),.out_valid(alu_out_valid),
    .out_ready(1'b1),.out_data(alu_result),.out_error(alu_error));
  anvil_q2_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(write),.kind(kind),.layer(32'd0),
    .proj(3'd0),.row(row),.col(col),.wdata(write_data),
    .idle(idle),.complete(complete),.rdata(read_data),.fault(fault),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
  always @* begin
    issue=0; write=0; kind=0; row=0; col=0; write_data=0;
    if (rst_n && idle) case (state)
      READ_X,READ_Y,WRITE_X,WRITE_Y: begin
        issue=1; kind=8; row=key_vector ? 3 : 2;
        col=head_base+pair_index+((state==READ_Y || state==WRITE_Y) ? HALF : 0);
        write=state==WRITE_X || state==WRITE_Y;
        write_data=state==WRITE_X ? rotated_x : rotated_y;
      end
      READ_COS,READ_SIN: begin
        issue=1; kind=11; row=position; col=(pair_index << 1)+(state==READ_SIN);
      end
      default: begin end
    endcase
  end
  always @* begin
    alu_valid=0; alu_op=0; alu_a=0; alu_b=0;
    if (rst_n) case (state)
      MUL_XC: begin alu_valid=1; alu_op=1; alu_a=x; alu_b=cosine; end
      MUL_YS: begin alu_valid=1; alu_op=1; alu_a=y; alu_b=sine; end
      SUB: begin alu_valid=1; alu_a=product1; alu_b={~product2[31],product2[30:0]}; end
      MUL_YC: begin alu_valid=1; alu_op=1; alu_a=y; alu_b=cosine; end
      MUL_XS: begin alu_valid=1; alu_op=1; alu_a=x; alu_b=sine; end
      ADD: begin alu_valid=1; alu_a=product1; alu_b=product2; end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; key_vector<=0; position<=0; head<=0; head_base<=0;
      pair_index<=0; x<=0; y<=0; cosine<=0; sine<=0; product1<=0; product2<=0;
      rotated_x<=0; rotated_y<=0;
    end else if (fault || (alu_out_valid && alu_error)) begin failed<=1; state<=OUTPUT; end
    else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; position<=cmd_pos; head<=0; head_base<=0; pair_index<=0; key_vector<=0;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin
          failed<=1; state<=BAD_COMMAND;
        end else state<=READ_X;
      end
      READ_X: if (issue) state<=WAIT_X;
      WAIT_X: if (complete) begin
        if (!fp_is_finite(read_data)) begin failed<=1; state<=OUTPUT; end
        else begin x<=read_data; state<=READ_Y; end
      end
      READ_Y: if (issue) state<=WAIT_Y;
      WAIT_Y: if (complete) begin
        if (!fp_is_finite(read_data)) begin failed<=1; state<=OUTPUT; end
        else begin y<=read_data; state<=READ_COS; end
      end
      READ_COS: if (issue) state<=WAIT_COS;
      WAIT_COS: if (complete) begin
        if (!fp_is_finite(read_data)) begin failed<=1; state<=OUTPUT; end
        else begin cosine<=read_data; state<=READ_SIN; end
      end
      READ_SIN: if (issue) state<=WAIT_SIN;
      WAIT_SIN: if (complete) begin
        if (!fp_is_finite(read_data)) begin failed<=1; state<=OUTPUT; end
        else begin sine<=read_data; state<=MUL_XC; end
      end
      MUL_XC: if (alu_ready) state<=WAIT_XC;
      WAIT_XC: if (alu_out_valid) begin product1<=alu_result; state<=MUL_YS; end
      MUL_YS: if (alu_ready) state<=WAIT_YS;
      WAIT_YS: if (alu_out_valid) begin product2<=alu_result; state<=SUB; end
      SUB: if (alu_ready) state<=WAIT_SUB;
      WAIT_SUB: if (alu_out_valid) begin rotated_x<=alu_result; state<=MUL_YC; end
      MUL_YC: if (alu_ready) state<=WAIT_YC;
      WAIT_YC: if (alu_out_valid) begin product1<=alu_result; state<=MUL_XS; end
      MUL_XS: if (alu_ready) state<=WAIT_XS;
      WAIT_XS: if (alu_out_valid) begin product2<=alu_result; state<=ADD; end
      ADD: if (alu_ready) state<=WAIT_ADD;
      WAIT_ADD: if (alu_out_valid) begin rotated_y<=alu_result; state<=WRITE_X; end
      WRITE_X: if (issue) state<=WAIT_WRITE_X;
      WAIT_WRITE_X: if (complete) state<=WRITE_Y;
      WRITE_Y: if (issue) state<=WAIT_WRITE_Y;
      WAIT_WRITE_Y: if (complete) begin
        if (pair_index+1<HALF) begin pair_index<=pair_index+1; state<=READ_X; end
        else if (head+1<(key_vector ? NUM_KV_HEADS : NUM_Q_HEADS)) begin
          pair_index<=0; head<=head+1; head_base<=head_base+HEAD_DIM; state<=READ_X;
        end else if (!key_vector) begin
          key_vector<=1; head<=0; head_base<=0; pair_index<=0; state<=READ_X;
        end else state<=OUTPUT;
      end
      BAD_COMMAND: state<=OUTPUT;
      OUTPUT: state<=IDLE;
      default: begin failed<=1; state<=OUTPUT; end
    endcase
  end
endmodule
