module anvil_d1_tensor (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_rows, cmd_cols,
  input wire cmd_wide, cmd_bias, cmd_head_reduction,
  input wire [31:0] cmd_rank,
  input wire [3:0] cmd_weight_kind, cmd_input_kind, cmd_output_kind,
  input wire [2:0] cmd_weight_proj, cmd_input_proj, cmd_output_proj,
  input wire [31:0] cmd_weight_row, cmd_bias_row,
  input wire [31:0] cmd_input_layer, cmd_input_row, cmd_input_col,
  input wire [31:0] cmd_output_layer, cmd_output_row, cmd_output_col,
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
  localparam IDLE=0, BIAS_READ=1, BIAS_RESPONSE=2, BIAS_ACC=3, BIAS_WAIT=4;
  localparam INPUT_READ=5, INPUT_RESPONSE=6, WEIGHT_READ=7, WEIGHT_RESPONSE=8;
  localparam MULTIPLY=9, MULTIPLY_WAIT=10, ACC=11, ACC_WAIT=12;
  localparam ROUND=13, ROUND_WAIT=14, WRITE=15, WRITE_RESPONSE=16;
  localparam COMPLETE=17, FAULTED=18, REJECT=19;
  reg [4:0] state;
  reg armed, failed, wide_weight, bias_enable, head_reduction;
  reg [31:0] layer, rows, cols, rank, row_index, col_index, rank_index;
  reg [3:0] reduction_head;
  reg [3:0] weight_kind, input_kind, output_kind;
  reg [2:0] weight_proj, input_proj, output_proj;
  reg [31:0] weight_row, bias_row, input_layer, input_row, input_col;
  reg [31:0] output_layer, output_row, output_col, weight_col;
  reg [1:0] word_number;
  reg signed [31:0] activation, bias_value, result;
  reg signed [95:0] weight;
  reg signed [127:0] product, sum;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==BIAS_READ || state==INPUT_READ ||
    state==WEIGHT_READ || state==WRITE);
  wire [31:0] selected_weight_row=head_reduction ?
    {reduction_head,weight_row[27:0]}+row_index : weight_row+row_index;
  wire mul_ready, mul_valid, mul32_ready, mul32_valid, mul96_ready, mul96_valid;
  wire signed [63:0] mul32_product;
  wire signed [127:0] mul_product, mul96_product;
  wire acc_ready, acc_valid, acc_error;
  wire signed [127:0] acc_sum;
  wire round16_ready, round16_valid, round32_ready, round32_valid;
  wire signed [31:0] round16_value, round32_value;
  assign cmd_ready=rst_n && armed && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  anvil_d1_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==WRITE),
    .kind(state==WRITE ? output_kind : state==INPUT_READ ? input_kind : weight_kind),
    .layer(state==WRITE ? output_layer : state==INPUT_READ ? input_layer : layer),
    .proj(state==WRITE ? output_proj : state==INPUT_READ ? input_proj : weight_proj),
    .row(state==WRITE ? output_row : state==INPUT_READ ? input_row :
      state==BIAS_READ ? bias_row+row_index : selected_weight_row),
    .col(state==WRITE ? output_col+row_index : state==INPUT_READ ? input_col+col_index :
      state==BIAS_READ ? {29'd0,weight_proj} : weight_col+{30'd0,word_number}),
    .wdata(state==WRITE ? result : 32'd0),.rdata(rdata),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),
    .c_req_write(c_req_write),.c_req_kind(c_req_kind),.c_req_layer(c_req_layer),
    .c_req_proj(c_req_proj),.c_req_row(c_req_row),.c_req_col(c_req_col),
    .c_req_wdata(c_req_wdata),.c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
    .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error)
  );
  assign mul_ready=wide_weight ? mul96_ready : mul32_ready;
  assign mul_valid=wide_weight ? mul96_valid : mul32_valid;
  assign mul_product=wide_weight ? mul96_product : {{64{mul32_product[63]}},mul32_product};
  anvil_d1_mul32 multiplier32 (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MULTIPLY && !wide_weight),.in_ready(mul32_ready),
    .in_a(weight[31:0]),.in_b(activation),
    .out_valid(mul32_valid),.out_ready(1'b1),.out_product(mul32_product)
  );
  anvil_d1_mul96x32 multiplier96 (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MULTIPLY && wide_weight),.in_ready(mul96_ready),.in_a(weight),.in_b(activation),
    .out_valid(mul96_valid),.out_ready(1'b1),.out_product(mul96_product)
  );
  anvil_d1_accumulator accumulator (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==BIAS_ACC || state==ACC),.in_ready(acc_ready),
    .in_first(state==BIAS_ACC || (!bias_enable && col_index==0)),
    .in_value(state==BIAS_ACC ? ($signed({{96{bias_value[31]}},bias_value})<<<16) : product),
    .out_valid(acc_valid),.out_ready(1'b1),.out_error(acc_error),.out_sum(acc_sum)
  );
  anvil_d1_round_sat #(.SHIFT(16)) round16 (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ROUND && !wide_weight),.in_ready(round16_ready),.in_value(sum),
    .out_valid(round16_valid),.out_ready(1'b1),.out_value(round16_value)
  );
  anvil_d1_round_sat #(.SHIFT(32)) round32 (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ROUND && wide_weight),.in_ready(round32_ready),.in_value(sum),
    .out_valid(round32_valid),.out_ready(1'b1),.out_value(round32_value)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; wide_weight<=0; bias_enable<=0;
      head_reduction<=0; layer<=0; rows<=0; cols<=0; rank<=0;
      row_index<=0; col_index<=0; rank_index<=0; reduction_head<=0;
      weight_kind<=0; input_kind<=0; output_kind<=0;
      weight_proj<=0; input_proj<=0; output_proj<=0; weight_row<=0; bias_row<=0;
      input_layer<=0; input_row<=0; input_col<=0;
      output_layer<=0; output_row<=0; output_col<=0; weight_col<=0;
      word_number<=0; activation<=0; bias_value<=0; result<=0; weight<=0; product<=0; sum<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; failed<=0; end
      else if (!failed && (memory_fault || (acc_valid && acc_error))) begin
        failed<=1; state<=COMPLETE;
      end else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          layer<=cmd_layer; rows<=cmd_rows; cols<=cmd_cols; rank<=cmd_rank;
          wide_weight<=cmd_wide; bias_enable<=cmd_bias; head_reduction<=cmd_head_reduction;
          weight_kind<=cmd_weight_kind; input_kind<=cmd_input_kind; output_kind<=cmd_output_kind;
          weight_proj<=cmd_weight_proj; input_proj<=cmd_input_proj; output_proj<=cmd_output_proj;
          weight_row<=cmd_weight_row; bias_row<=cmd_bias_row;
          input_layer<=cmd_input_layer; input_row<=cmd_input_row; input_col<=cmd_input_col;
          output_layer<=cmd_output_layer; output_row<=cmd_output_row; output_col<=cmd_output_col;
          row_index<=0; col_index<=0; rank_index<=0; reduction_head<=0; weight_col<=0;
          word_number<=0; failed<=0;
          if (cmd_rows==0 || cmd_rows>151936 || cmd_cols==0 || cmd_cols>11008 ||
              (cmd_head_reduction && (!cmd_wide || cmd_rank==0 || cmd_rank>512 ||
                cmd_cols>16*cmd_rank || cmd_weight_row[31:28]!=0)) ||
              (cmd_bias && cmd_wide) ||
              {1'b0,cmd_output_col}+{1'b0,cmd_rows}>33'h100000000 ||
              {1'b0,cmd_input_col}+{1'b0,cmd_cols}>33'h100000000 ||
              {1'b0,cmd_weight_row}+{1'b0,cmd_rows}>33'h100000000 ||
              (cmd_bias && {1'b0,cmd_bias_row}+{1'b0,cmd_rows}>33'h100000000)) begin
            failed<=1; state<=REJECT;
          end else if (cmd_bias) state<=BIAS_READ;
          else state<=INPUT_READ;
        end
        BIAS_READ: if (issue) state<=BIAS_RESPONSE;
        BIAS_RESPONSE: if (memory_complete) begin bias_value<=rdata; state<=BIAS_ACC; end
        BIAS_ACC: if (acc_ready) state<=BIAS_WAIT;
        BIAS_WAIT: if (acc_valid) state<=INPUT_READ;
        INPUT_READ: if (issue) state<=INPUT_RESPONSE;
        INPUT_RESPONSE: if (memory_complete) begin activation<=rdata; state<=WEIGHT_READ; end
        WEIGHT_READ: if (issue) state<=WEIGHT_RESPONSE;
        WEIGHT_RESPONSE: if (memory_complete) begin
          if (wide_weight) begin
            weight[word_number*32+:32]<=rdata;
            if (word_number==2) begin word_number<=0; state<=MULTIPLY; end
            else begin word_number<=word_number+1'b1; state<=WEIGHT_READ; end
          end else begin weight<={{64{rdata[31]}},rdata}; state<=MULTIPLY; end
        end
        MULTIPLY: if (mul_ready) state<=MULTIPLY_WAIT;
        MULTIPLY_WAIT: if (mul_valid) begin product<=mul_product; state<=ACC; end
        ACC: if (acc_ready) state<=ACC_WAIT;
        ACC_WAIT: if (acc_valid) begin
          if (col_index==cols-1'b1) begin sum<=acc_sum; state<=ROUND; end
          else begin
            col_index<=col_index+1'b1;
            if (head_reduction && rank_index==rank-1'b1) begin
              rank_index<=0; reduction_head<=reduction_head+1'b1; weight_col<=0;
            end else begin
              rank_index<=rank_index+1'b1;
              weight_col<=weight_col+(wide_weight ? 32'd3 : 32'd1);
            end
            state<=INPUT_READ;
          end
        end
        ROUND: if (wide_weight ? round32_ready : round16_ready) state<=ROUND_WAIT;
        ROUND_WAIT: if (wide_weight ? round32_valid : round16_valid) begin
          result<=wide_weight ? round32_value : round16_value; state<=WRITE;
        end
        WRITE: if (issue) state<=WRITE_RESPONSE;
        WRITE_RESPONSE: if (memory_complete) begin
          if (row_index==rows-1'b1) state<=COMPLETE;
          else begin
            row_index<=row_index+1'b1; col_index<=0; rank_index<=0;
            reduction_head<=0; weight_col<=0; word_number<=0;
            if (bias_enable) state<=BIAS_READ;
            else state<=INPUT_READ;
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
