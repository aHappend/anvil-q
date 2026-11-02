module anvil_q1_fp2_epilogue_fusion #(
  parameter MAX_VECTOR=4864, HEAD_DIM=64, MAX_POS=32768
) (
  input wire clk, rst_n,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [1:0] cmd_op,
  input wire [31:0] cmd_len, cmd_pos,
  input wire in_valid,
  output wire in_ready,
  input wire [31:0] in_data, in_aux, in_residual,
  input wire in_last,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_data,
  output wire out_last,
  output wire [4:0] status,
  output wire done, error
);
  localparam ADDR_BITS=MAX_VECTOR>1 ? $clog2(MAX_VECTOR) : 1;
  localparam IDLE=0, COLLECT=1, READ_X=2, LATCH_X=3, READ_Y=4, LATCH_Y=5;
  localparam MUL_ISSUE=6, MUL_WAIT=7, ADD_ISSUE=8, ADD_WAIT=9;
  localparam RECIP_ISSUE=10, RECIP_WAIT=11, RSQRT_ISSUE=12, RSQRT_WAIT=13;
  localparam EXP_ISSUE=14, EXP_WAIT=15, NEXT_ELEMENT=16;
  localparam OUT_READ=17, OUT_LATCH=18, OUTPUT=19, COMPLETE_WAIT=20;
  localparam ERROR_WAIT0=21, ERROR_WAIT1=22, FINISH=23;
  localparam SQUARE=0, REDUCE=1, MEAN=2, EPSILON=3, NORM_X=4, NORM_GAMMA=5;
  localparam ROTATE_X=6, ROTATE_Y=7, RESIDUAL=8, SIGMOID_DENOM=9;
  localparam SIGMOID_NEG=10, SWISH=11, GATED_UP=12;
  reg [4:0] state;
  reg [3:0] arithmetic;
  reg [1:0] operation;
  reg failed, normalization_pass;
  reg [31:0] length, received, index, partner, head_base, pair_index, output_index;
  reg [31:0] x_value, aux_value, residual_value, y_value, sine_value;
  reg [31:0] sum, norm_factor, temporary, exponential, inverse;
  reg [31:0] product0, product1;
  reg [31:0] payload;
  reg [4:0] flags;
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] data_mem [0:MAX_VECTOR-1];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] aux_mem [0:MAX_VECTOR-1];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] residual_mem [0:MAX_VECTOR-1];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] result_mem [0:MAX_VECTOR-1];
  reg [31:0] data_q, aux_q, residual_q, result_q;
  wire [31:0] read_address=(state==READ_Y || state==LATCH_Y) ? partner : index;
  reg result_write;
  reg [31:0] result_address, result_value;
  reg [31:0] mul_a0, mul_b0, mul_a1, mul_b1, add_a, add_b, reciprocal_x;
  wire [1:0] mul_valid, mul_ready;
  wire [31:0] mul_result [0:1];
  wire [4:0] mul_status [0:1];
  wire add_valid, add_ready, recip_valid, exp_valid, rsqrt_valid;
  wire [31:0] add_result, recip_result, exp_result, rsqrt_result;
  wire [4:0] add_status, recip_status, exp_status, rsqrt_status;
  function automatic rope_length_valid(input [31:0] n);
    integer heads;
    begin
      rope_length_valid=0;
      for (heads=1;heads<=MAX_VECTOR/HEAD_DIM;heads=heads+1)
        if (n==heads*HEAD_DIM) rope_length_valid=1;
    end
  endfunction
  generate if (MAX_VECTOR<1 || HEAD_DIM<2 || (HEAD_DIM & 1)!=0 || MAX_POS<1) begin: invalid_parameters
    initial $fatal(1,"FP2 EPILOGUE PARAMETER ERROR");
  end endgenerate
  anvil_q1_fp2_fp32_binary #(.MULTIPLY(1)) multiply0(
    .clk(clk),.rst_n(rst_n),.in_valid(state==MUL_ISSUE),.in_ready(mul_ready[0]),
    .out_ready(1'b1),.a(mul_a0),.b(mul_b0),.out_valid(mul_valid[0]),
    .result(mul_result[0]),.status(mul_status[0]));
  anvil_q1_fp2_fp32_binary #(.MULTIPLY(1)) multiply1(
    .clk(clk),.rst_n(rst_n),
    .in_valid(state==MUL_ISSUE && (arithmetic==ROTATE_X || arithmetic==ROTATE_Y)),
    .in_ready(mul_ready[1]),.out_ready(1'b1),.a(mul_a1),.b(mul_b1),
    .out_valid(mul_valid[1]),.result(mul_result[1]),.status(mul_status[1]));
  anvil_q1_fp2_fp32_binary #(.MULTIPLY(0)) add(
    .clk(clk),.rst_n(rst_n),.in_valid(state==ADD_ISSUE),.in_ready(add_ready),
    .out_ready(1'b1),.a(add_a),.b(add_b),.out_valid(add_valid),
    .result(add_result),.status(add_status));
  anvil_q1_fp2_reciprocal reciprocal(
    .clk(clk),.rst_n(rst_n),.in_valid(state==RECIP_ISSUE),.x(reciprocal_x),
    .out_valid(recip_valid),.result(recip_result),.status(recip_status));
  anvil_q1_fp2_fast_rsqrt fast_rsqrt(
    .clk(clk),.rst_n(rst_n),.in_valid(state==RSQRT_ISSUE),.x(temporary),
    .out_valid(rsqrt_valid),.result(rsqrt_result),.status(rsqrt_status));
  anvil_q1_fp2_exp exponential_pipeline(
    .clk(clk),.rst_n(rst_n),.in_valid(state==EXP_ISSUE),
    .x({1'b1,x_value[30:0]}),.out_valid(exp_valid),
    .result(exp_result),.status(exp_status));

  assign cmd_ready=rst_n && state==IDLE;
  assign in_ready=rst_n && state==COLLECT;
  assign out_valid=rst_n && state==OUTPUT;
  assign out_data=out_valid ? payload : 32'd0;
  assign out_last=out_valid && output_index+1==length;
  assign status=rst_n && (out_valid || done) ? flags : 5'd0;
  assign done=rst_n && state==FINISH;
  assign error=done && failed;
  always @* begin
    mul_a0=x_value; mul_b0=x_value; mul_a1=0; mul_b1=0;
    case (arithmetic)
      MEAN: begin mul_a0=sum; mul_b0=inverse; end
      NORM_X: mul_b0=norm_factor;
      NORM_GAMMA: begin mul_a0=temporary; mul_b0=aux_value; end
      ROTATE_X: begin
        mul_b0=aux_value; mul_a1=y_value; mul_b1=sine_value;
      end
      ROTATE_Y: begin
        mul_a0=y_value; mul_b0=aux_value; mul_a1=x_value; mul_b1=sine_value;
      end
      SIGMOID_NEG: begin mul_a0=exponential; mul_b0=inverse; end
      SWISH: begin
        mul_a0=(x_value==32'hff800000) ? 32'h80000000 : x_value;
        mul_b0=temporary;
      end
      GATED_UP: begin mul_a0=temporary; mul_b0=aux_value; end
      default: begin end
    endcase
    add_a=product0; add_b=product1;
    case (arithmetic)
      REDUCE: begin add_a=sum; add_b=temporary; end
      EPSILON: begin add_a=temporary; add_b=32'h358637bd; end
      ROTATE_X: add_b={~product1[31],product1[30:0]};
      RESIDUAL: begin add_a=x_value; add_b=residual_value; end
      SIGMOID_DENOM: begin add_a=32'h3f800000; add_b=exponential; end
      default: begin end
    endcase
    reciprocal_x=operation==0 ? anvil_q1_fp2_pkg::uint32_to_fp32(length) : temporary;
    result_write=0; result_address=index; result_value=0;
    if (rst_n && state==MUL_WAIT && mul_valid[0] &&
        (arithmetic==NORM_GAMMA || arithmetic==GATED_UP)) begin
      result_write=1; result_value=mul_result[0];
    end
    if (rst_n && state==ADD_WAIT && add_valid &&
        (arithmetic==ROTATE_X || arithmetic==ROTATE_Y || arithmetic==RESIDUAL)) begin
      result_write=1; result_value=add_result;
      if (arithmetic==ROTATE_Y) result_address=partner;
    end
  end
  always @(posedge clk) begin
    if (rst_n && in_valid && in_ready) begin
      data_mem[received[ADDR_BITS-1:0]]<=in_data;
      aux_mem[received[ADDR_BITS-1:0]]<=in_aux;
      residual_mem[received[ADDR_BITS-1:0]]<=in_residual;
    end
    data_q<=data_mem[read_address[ADDR_BITS-1:0]];
    aux_q<=aux_mem[read_address[ADDR_BITS-1:0]];
    residual_q<=residual_mem[read_address[ADDR_BITS-1:0]];
    if (result_write) result_mem[result_address[ADDR_BITS-1:0]]<=result_value;
    result_q<=result_mem[output_index[ADDR_BITS-1:0]];
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=IDLE; arithmetic<=SQUARE; operation<=0; failed<=0;
      normalization_pass<=0; length<=0; received<=0; index<=0; partner<=0;
      head_base<=0; pair_index<=0; output_index<=0; payload<=0; flags<=0;
      x_value<=0; aux_value<=0; residual_value<=0; y_value<=0; sine_value<=0;
      sum<=0; norm_factor<=0; temporary<=0; exponential<=0; inverse<=0;
      product0<=0; product1<=0;
    end else case (state)
      IDLE: if (cmd_valid) begin
        operation<=cmd_op; length<=cmd_len; received<=0; index<=0;
        partner<=HEAD_DIM/2; head_base<=0; pair_index<=0; output_index<=0;
        flags<=0; failed<=0; sum<=0; normalization_pass<=0;
        if (cmd_len==0 || cmd_len>MAX_VECTOR ||
            (cmd_op==1 && (cmd_pos>=MAX_POS || !rope_length_valid(cmd_len)))) begin
          failed<=1; state<=ERROR_WAIT0;
        end else state<=COLLECT;
      end
      COLLECT: if (in_valid) begin
        if (in_last!=(received+1==length)) begin failed<=1; state<=ERROR_WAIT0; end
        else if (in_last) begin index<=0; state<=READ_X; end
        else received<=received+1;
      end
      READ_X: state<=LATCH_X;
      LATCH_X: begin
        x_value<=data_q; aux_value<=aux_q; residual_value<=residual_q;
        case (operation)
          0: begin
            if (normalization_pass) arithmetic<=NORM_X;
            else arithmetic<=SQUARE;
            state<=MUL_ISSUE;
          end
          1: state<=READ_Y;
          2: state<=EXP_ISSUE;
          3: begin arithmetic<=RESIDUAL; state<=ADD_ISSUE; end
        endcase
      end
      READ_Y: state<=LATCH_Y;
      LATCH_Y: begin
        y_value<=data_q; sine_value<=aux_q; arithmetic<=ROTATE_X; state<=MUL_ISSUE;
      end
      MUL_ISSUE: if (&mul_ready) state<=MUL_WAIT;
      MUL_WAIT: if (mul_valid[0]) begin
        flags<=flags | mul_status[0] |
          ((arithmetic==ROTATE_X || arithmetic==ROTATE_Y) ? mul_status[1] : 5'd0);
        case (arithmetic)
          SQUARE: begin temporary<=mul_result[0]; arithmetic<=REDUCE; state<=ADD_ISSUE; end
          MEAN: begin temporary<=mul_result[0]; arithmetic<=EPSILON; state<=ADD_ISSUE; end
          NORM_X: begin temporary<=mul_result[0]; arithmetic<=NORM_GAMMA; state<=MUL_ISSUE; end
          NORM_GAMMA, GATED_UP: state<=NEXT_ELEMENT;
          ROTATE_X, ROTATE_Y: begin
            product0<=mul_result[0]; product1<=mul_result[1]; state<=ADD_ISSUE;
          end
          SIGMOID_NEG: begin temporary<=mul_result[0]; arithmetic<=SWISH; state<=MUL_ISSUE; end
          SWISH: begin temporary<=mul_result[0]; arithmetic<=GATED_UP; state<=MUL_ISSUE; end
          default: begin failed<=1; state<=ERROR_WAIT0; end
        endcase
      end
      ADD_ISSUE: if (add_ready) state<=ADD_WAIT;
      ADD_WAIT: if (add_valid) begin
        flags<=flags | add_status;
        case (arithmetic)
          REDUCE: begin
            sum<=add_result;
            if (index+1==length) state<=RECIP_ISSUE;
            else begin index<=index+1; state<=READ_X; end
          end
          EPSILON: begin temporary<=add_result; state<=RSQRT_ISSUE; end
          ROTATE_X: begin arithmetic<=ROTATE_Y; state<=MUL_ISSUE; end
          ROTATE_Y, RESIDUAL: state<=NEXT_ELEMENT;
          SIGMOID_DENOM: begin temporary<=add_result; state<=RECIP_ISSUE; end
          default: begin failed<=1; state<=ERROR_WAIT0; end
        endcase
      end
      RECIP_ISSUE: state<=RECIP_WAIT;
      RECIP_WAIT: if (recip_valid) begin
        flags<=flags | recip_status; inverse<=recip_result;
        if (operation==0) begin arithmetic<=MEAN; state<=MUL_ISSUE; end
        else if (x_value[31]) begin arithmetic<=SIGMOID_NEG; state<=MUL_ISSUE; end
        else begin temporary<=recip_result; arithmetic<=SWISH; state<=MUL_ISSUE; end
      end
      RSQRT_ISSUE: state<=RSQRT_WAIT;
      RSQRT_WAIT: if (rsqrt_valid) begin
        flags<=flags | rsqrt_status; norm_factor<=rsqrt_result;
        normalization_pass<=1; index<=0; state<=READ_X;
      end
      EXP_ISSUE: state<=EXP_WAIT;
      EXP_WAIT: if (exp_valid) begin
        flags<=flags | exp_status; exponential<=exp_result;
        arithmetic<=SIGMOID_DENOM; state<=ADD_ISSUE;
      end
      NEXT_ELEMENT: begin
        if (operation==1) begin
          if (pair_index+1<HEAD_DIM/2) begin
            pair_index<=pair_index+1; index<=index+1; partner<=partner+1; state<=READ_X;
          end else if (head_base+HEAD_DIM<length) begin
            head_base<=head_base+HEAD_DIM; pair_index<=0;
            index<=head_base+HEAD_DIM; partner<=head_base+HEAD_DIM+HEAD_DIM/2;
            state<=READ_X;
          end else begin output_index<=0; state<=OUT_READ; end
        end else if (index+1<length) begin index<=index+1; state<=READ_X; end
        else begin output_index<=0; state<=OUT_READ; end
      end
      OUT_READ: state<=OUT_LATCH;
      OUT_LATCH: begin payload<=result_q; state<=OUTPUT; end
      OUTPUT: if (out_ready) begin
        if (output_index+1==length) state<=COMPLETE_WAIT;
        else begin output_index<=output_index+1; state<=OUT_READ; end
      end
      COMPLETE_WAIT: state<=FINISH;
      ERROR_WAIT0: state<=ERROR_WAIT1;
      ERROR_WAIT1: state<=FINISH;
      FINISH: state<=IDLE;
      default: begin failed<=1; state<=ERROR_WAIT0; end
    endcase
  end
endmodule
