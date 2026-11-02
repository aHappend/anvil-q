module anvil_d1_rope #(
  parameter integer QK_ROPE_HEAD_DIM=64, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos,
  input wire [31:0] cmd_source_row, cmd_source_col,
  input wire [2:0] cmd_target_proj,
  input wire [31:0] cmd_target_row, cmd_target_col,
  output wire done, error,
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
  localparam IDLE=0, READ=1, RESPONSE=2, MULTIPLY=3, MULTIPLY_WAIT=4;
  localparam ADD=5, ADD_WAIT=6, ROUND=7, ROUND_WAIT=8, WRITE=9;
  localparam WRITE_RESPONSE=10, COMPLETE=11, FAULTED=12, REJECT=13;
  reg [3:0] state;
  reg armed, failed, odd_output;
  reg [1:0] read_index, product_index;
  reg [31:0] layer, pos, source_row, source_col, target_row, target_col, pair_col;
  reg [2:0] target_proj;
  reg signed [31:0] x, y, cosine, sine, result;
  reg signed [63:0] first_product, second_product;
  reg signed [127:0] sum;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==READ || state==WRITE);
  wire mul_ready, mul_valid;
  wire signed [63:0] mul_product;
  wire add_ready, add_valid, add_error, sub_ready, sub_valid, sub_error;
  wire signed [127:0] added, subtracted;
  wire round_ready, round_valid;
  wire signed [31:0] rounded;
  assign cmd_ready=rst_n && armed && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  generate if (QK_ROPE_HEAD_DIM<2 || QK_ROPE_HEAD_DIM>64 ||
      (QK_ROPE_HEAD_DIM & 1)!=0 || MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: rotary geometry");
  end endgenerate
  anvil_d1_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==WRITE),.kind(4'd15),.layer(layer),
    .proj(state==WRITE ? target_proj : read_index[1] ? 3'd6 : 3'd7),
    .row(state==WRITE ? target_row : read_index[1] ? pos : source_row),
    .col(state==WRITE ? target_col+pair_col+{31'd0,odd_output} :
      read_index[1] ? pair_col+{31'd0,read_index[0]} :
      source_col+pair_col+{31'd0,read_index[0]}),
    .wdata(state==WRITE ? result : 32'd0),.rdata(rdata),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),
    .c_req_write(c_req_write),.c_req_kind(c_req_kind),.c_req_layer(c_req_layer),
    .c_req_proj(c_req_proj),.c_req_row(c_req_row),.c_req_col(c_req_col),
    .c_req_wdata(c_req_wdata),.c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
    .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error)
  );
  anvil_d1_mul32 multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MULTIPLY),.in_ready(mul_ready),
    .in_a(product_index[0] ? y : x),
    .in_b(product_index[0] ? (odd_output ? cosine : sine) :
      (odd_output ? sine : cosine)),
    .out_valid(mul_valid),.out_ready(1'b1),.out_product(mul_product)
  );
  anvil_d1_add128 adder (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ADD && odd_output),.in_ready(add_ready),
    .in_a({{64{first_product[63]}},first_product}),
    .in_b({{64{second_product[63]}},second_product}),
    .out_valid(add_valid),.out_ready(1'b1),.out_error(add_error),.out_sum(added)
  );
  anvil_d1_add128 #(.SUBTRACT(1)) subtractor (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ADD && !odd_output),.in_ready(sub_ready),
    .in_a({{64{first_product[63]}},first_product}),
    .in_b({{64{second_product[63]}},second_product}),
    .out_valid(sub_valid),.out_ready(1'b1),.out_error(sub_error),.out_sum(subtracted)
  );
  anvil_d1_round_sat #(.SHIFT(16)) boundary (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ROUND),.in_ready(round_ready),.in_value(sum),
    .out_valid(round_valid),.out_ready(1'b1),.out_value(rounded)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; odd_output<=0; read_index<=0; product_index<=0;
      layer<=0; pos<=0; source_row<=0; source_col<=0; target_row<=0; target_col<=0;
      pair_col<=0; target_proj<=0; x<=0; y<=0; cosine<=0; sine<=0;
      result<=0; first_product<=0; second_product<=0; sum<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; failed<=0; end
      else if (!failed && (memory_fault || (add_valid && add_error) ||
          (sub_valid && sub_error))) begin failed<=1; state<=COMPLETE; end
      else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          layer<=cmd_layer; pos<=cmd_pos; source_row<=cmd_source_row;
          source_col<=cmd_source_col; target_row<=cmd_target_row;
          target_col<=cmd_target_col; target_proj<=cmd_target_proj;
          pair_col<=0; read_index<=0; product_index<=0; odd_output<=0; failed<=0;
          if (cmd_pos>=MAX_SEQ_LEN || (cmd_target_proj!=3 && cmd_target_proj!=7) ||
              {1'b0,cmd_source_col}+33'(QK_ROPE_HEAD_DIM)>33'h100000000 ||
              {1'b0,cmd_target_col}+33'(QK_ROPE_HEAD_DIM)>33'h100000000) begin
            failed<=1; state<=REJECT;
          end else state<=READ;
        end
        READ: if (issue) state<=RESPONSE;
        RESPONSE: if (memory_complete) begin
          case (read_index)
            0: x<=rdata;
            1: y<=rdata;
            2: cosine<=rdata;
            3: sine<=rdata;
          endcase
          if (read_index==3) begin product_index<=0; state<=MULTIPLY; end
          else begin read_index<=read_index+1'b1; state<=READ; end
        end
        MULTIPLY: if (mul_ready) state<=MULTIPLY_WAIT;
        MULTIPLY_WAIT: if (mul_valid) begin
          if (!product_index[0]) begin
            first_product<=mul_product; product_index<=1; state<=MULTIPLY;
          end else begin second_product<=mul_product; state<=ADD; end
        end
        ADD: if (odd_output ? add_ready : sub_ready) state<=ADD_WAIT;
        ADD_WAIT: if (odd_output ? add_valid : sub_valid) begin
          sum<=odd_output ? added : subtracted; state<=ROUND;
        end
        ROUND: if (round_ready) state<=ROUND_WAIT;
        ROUND_WAIT: if (round_valid) begin result<=rounded; state<=WRITE; end
        WRITE: if (issue) state<=WRITE_RESPONSE;
        WRITE_RESPONSE: if (memory_complete) begin
          if (!odd_output) begin odd_output<=1; product_index<=0; state<=MULTIPLY; end
          else if (pair_col==QK_ROPE_HEAD_DIM-2) state<=COMPLETE;
          else begin
            pair_col<=pair_col+32'd2; odd_output<=0; read_index<=0; state<=READ;
          end
        end
        REJECT: state<=COMPLETE;
        COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
        FAULTED: state<=FAULTED;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
