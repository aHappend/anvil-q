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
  localparam RMS_SQUARE=24, RMS_NORMALIZE=25;
  localparam ROPE_FIRST=26, ROPE_SECOND=27, ROPE_DRAIN=28;
  localparam SWIGLU_SIGMOID=29, SWIGLU_PRODUCT=30, RESIDUAL_STREAM=31;
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
  reg [31:0] rms_read_count, rms_completed;
  reg rms_read_valid;
  reg [31:0] gamma_pipe [0:8];
  (* nomem2reg *) reg [31:0] rope_address_pipe [0:17];
  reg [17:0] rope_subtract_pipe;
  reg [31:0] sigmoid_sign_pipe;
  reg [31:0] exp_pipe [0:14];
  reg [31:0] inverse_pipe [0:8];
  integer gamma_stage;
  reg [31:0] payload;
  reg [4:0] flags;
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] data_mem [0:MAX_VECTOR-1];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] aux_mem [0:MAX_VECTOR-1];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] residual_mem [0:MAX_VECTOR-1];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] result_mem [0:MAX_VECTOR-1];
  reg [31:0] data_q, aux_q, residual_q, result_q;
  wire rms_stream=state==RMS_SQUARE || state==RMS_NORMALIZE;
  wire swiglu_stream=state==SWIGLU_SIGMOID || state==SWIGLU_PRODUCT;
  wire vector_stream=rms_stream || swiglu_stream || state==RESIDUAL_STREAM;
  wire rope_stream=operation==1 &&
    (state==READ_X || state==LATCH_X || state==READ_Y || state==LATCH_Y ||
     state==ROPE_FIRST || state==ROPE_SECOND || state==ROPE_DRAIN);
  wire rope_issue=state==ROPE_FIRST || state==ROPE_SECOND;
  wire [31:0] read_address=vector_stream ?
    (rms_read_count<length ? rms_read_count : 32'd0) :
    ((state==READ_Y || state==LATCH_Y) ? partner : index);
  wire [31:0] result_read_address=state==SWIGLU_PRODUCT ? read_address :
    (operation==0 && !normalization_pass ? index : output_index);
  wire rms_mul_issue=rms_stream && rms_read_valid;
  wire swiglu_mul_issue=(state==SWIGLU_SIGMOID && recip_valid) ||
    (state==SWIGLU_PRODUCT && rms_read_valid);
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
    .clk(clk),.rst_n(rst_n),
    .in_valid(state==MUL_ISSUE || rms_mul_issue || rope_issue || swiglu_mul_issue),
    .in_ready(mul_ready[0]),
    .out_ready(1'b1),.a(mul_a0),.b(mul_b0),.out_valid(mul_valid[0]),
    .result(mul_result[0]),.status(mul_status[0]));
  anvil_q1_fp2_fp32_binary #(.MULTIPLY(1)) multiply1(
    .clk(clk),.rst_n(rst_n),
    .in_valid((state==MUL_ISSUE && (arithmetic==ROTATE_X || arithmetic==ROTATE_Y)) ||
      ((state==RMS_NORMALIZE || state==SWIGLU_PRODUCT) && mul_valid[0]) ||
      rope_issue),
    .in_ready(mul_ready[1]),.out_ready(1'b1),.a(mul_a1),.b(mul_b1),
    .out_valid(mul_valid[1]),.result(mul_result[1]),.status(mul_status[1]));
  anvil_q1_fp2_fp32_binary #(.MULTIPLY(0)) add(
    .clk(clk),.rst_n(rst_n),
    .in_valid(state==ADD_ISSUE || (rope_stream && mul_valid[0]) ||
      (state==SWIGLU_SIGMOID && exp_valid) ||
      (state==RESIDUAL_STREAM && rms_read_valid)),.in_ready(add_ready),
    .out_ready(1'b1),.a(add_a),.b(add_b),.out_valid(add_valid),
    .result(add_result),.status(add_status));
  anvil_q1_fp2_reciprocal reciprocal(
    .clk(clk),.rst_n(rst_n),
    .in_valid(state==RECIP_ISSUE || (state==SWIGLU_SIGMOID && add_valid)),
    .x(reciprocal_x),
    .out_valid(recip_valid),.result(recip_result),.status(recip_status));
  anvil_q1_fp2_fast_rsqrt fast_rsqrt(
    .clk(clk),.rst_n(rst_n),.in_valid(state==RSQRT_ISSUE),.x(temporary),
    .out_valid(rsqrt_valid),.result(rsqrt_result),.status(rsqrt_status));
  anvil_q1_fp2_exp exponential_pipeline(
    .clk(clk),.rst_n(rst_n),
    .in_valid(state==EXP_ISSUE || (state==SWIGLU_SIGMOID && rms_read_valid)),
    .x({1'b1,(state==SWIGLU_SIGMOID ? data_q[30:0] : x_value[30:0])}),
    .out_valid(exp_valid),
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
    if (state==RMS_SQUARE) begin mul_a0=data_q; mul_b0=data_q; end
    if (state==RMS_NORMALIZE) begin
      mul_a0=data_q; mul_b0=norm_factor;
      mul_a1=mul_result[0]; mul_b1=gamma_pipe[8];
    end
    if (rope_issue) begin
      mul_a0=state==ROPE_FIRST ? x_value : y_value; mul_b0=aux_value;
      mul_a1=state==ROPE_FIRST ? y_value : x_value; mul_b1=sine_value;
    end
    if (state==SWIGLU_SIGMOID) begin
      mul_a0=exp_pipe[14]; mul_b0=recip_result;
    end
    if (state==SWIGLU_PRODUCT) begin
      mul_a0=data_q==32'hff800000 ? 32'h80000000 : data_q;
      mul_b0=result_q; mul_a1=mul_result[0]; mul_b1=gamma_pipe[8];
    end
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
    if (rope_stream) begin
      add_a=mul_result[0];
      add_b={mul_result[1][31]^rope_subtract_pipe[8],mul_result[1][30:0]};
    end
    if (state==SWIGLU_SIGMOID) begin
      add_a=32'h3f800000; add_b=exp_result; reciprocal_x=add_result;
    end
    if (state==RESIDUAL_STREAM) begin add_a=data_q; add_b=residual_q; end
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
    if (rst_n && state==RMS_SQUARE && mul_valid[0]) begin
      result_write=1; result_address=rms_completed; result_value=mul_result[0];
    end
    if (rst_n && state==RMS_NORMALIZE && mul_valid[1]) begin
      result_write=1; result_address=rms_completed; result_value=mul_result[1];
    end
    if (rst_n && rope_stream && add_valid) begin
      result_write=1; result_address=rope_address_pipe[17]; result_value=add_result;
    end
    if (rst_n && state==SWIGLU_SIGMOID && mul_valid[0]) begin
      result_write=1; result_address=rms_completed;
      result_value=sigmoid_sign_pipe[31] ? mul_result[0] : inverse_pipe[8];
    end
    if (rst_n && state==SWIGLU_PRODUCT && mul_valid[1]) begin
      result_write=1; result_address=rms_completed; result_value=mul_result[1];
    end
    if (rst_n && state==RESIDUAL_STREAM && add_valid) begin
      result_write=1; result_address=rms_completed; result_value=add_result;
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
    result_q<=result_mem[result_read_address[ADDR_BITS-1:0]];
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      rms_read_valid<=0;
      rope_subtract_pipe<=0; sigmoid_sign_pipe<=0;
      for (gamma_stage=0;gamma_stage<9;gamma_stage=gamma_stage+1)
        gamma_pipe[gamma_stage]<=0;
    end else begin
      rms_read_valid<=vector_stream && rms_read_count<length;
      gamma_pipe[0]<=rms_read_valid ? aux_q : 32'd0;
      for (gamma_stage=1;gamma_stage<9;gamma_stage=gamma_stage+1)
        gamma_pipe[gamma_stage]<=gamma_pipe[gamma_stage-1];
      rope_address_pipe[0]<=state==ROPE_FIRST ? index : partner;
      for (gamma_stage=1;gamma_stage<18;gamma_stage=gamma_stage+1)
        rope_address_pipe[gamma_stage]<=rope_address_pipe[gamma_stage-1];
      rope_subtract_pipe<={rope_subtract_pipe[16:0],state==ROPE_FIRST};
      sigmoid_sign_pipe<={sigmoid_sign_pipe[30:0],data_q[31]};
      exp_pipe[0]<=exp_result;
      for (gamma_stage=1;gamma_stage<15;gamma_stage=gamma_stage+1)
        exp_pipe[gamma_stage]<=exp_pipe[gamma_stage-1];
      inverse_pipe[0]<=recip_result;
      for (gamma_stage=1;gamma_stage<9;gamma_stage=gamma_stage+1)
        inverse_pipe[gamma_stage]<=inverse_pipe[gamma_stage-1];
    end
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=IDLE; arithmetic<=SQUARE; operation<=0; failed<=0;
      normalization_pass<=0; length<=0; received<=0; index<=0; partner<=0;
      head_base<=0; pair_index<=0; output_index<=0; payload<=0; flags<=0;
      x_value<=0; aux_value<=0; residual_value<=0; y_value<=0; sine_value<=0;
      sum<=0; norm_factor<=0; temporary<=0; exponential<=0; inverse<=0;
      product0<=0; product1<=0;
      rms_read_count<=0; rms_completed<=0;
    end else case (state)
      IDLE: if (cmd_valid) begin
        operation<=cmd_op; length<=cmd_len; received<=0; index<=0;
        partner<=HEAD_DIM/2; head_base<=0; pair_index<=0; output_index<=0;
        flags<=0; failed<=0; sum<=0; normalization_pass<=0;
        rms_read_count<=0; rms_completed<=0;
        if (cmd_len==0 || cmd_len>MAX_VECTOR ||
            (cmd_op==1 && (cmd_pos>=MAX_POS || !rope_length_valid(cmd_len)))) begin
          failed<=1; state<=ERROR_WAIT0;
        end else state<=COLLECT;
      end
      COLLECT: if (in_valid) begin
        if (in_last!=(received+1==length)) begin failed<=1; state<=ERROR_WAIT0; end
        else if (in_last) begin
          index<=0;
          if (operation==0) state<=RMS_SQUARE;
          else if (operation==2) state<=SWIGLU_SIGMOID;
          else if (operation==3) state<=RESIDUAL_STREAM;
          else state<=READ_X;
        end
        else received<=received+1;
      end
      READ_X: state<=LATCH_X;
      LATCH_X: begin
        x_value<=data_q; aux_value<=aux_q; residual_value<=residual_q;
        case (operation)
          0: begin
            temporary<=result_q; arithmetic<=REDUCE; state<=ADD_ISSUE;
          end
          1: state<=READ_Y;
          2: state<=EXP_ISSUE;
          3: begin arithmetic<=RESIDUAL; state<=ADD_ISSUE; end
        endcase
      end
      READ_Y: state<=LATCH_Y;
      LATCH_Y: begin
        y_value<=data_q; sine_value<=aux_q; state<=ROPE_FIRST;
      end
      ROPE_FIRST: state<=ROPE_SECOND;
      ROPE_SECOND: begin
        if (pair_index+1<HEAD_DIM/2) begin
          pair_index<=pair_index+1; index<=index+1; partner<=partner+1; state<=READ_X;
        end else if (head_base+HEAD_DIM<length) begin
          head_base<=head_base+HEAD_DIM; pair_index<=0;
          index<=head_base+HEAD_DIM; partner<=head_base+HEAD_DIM+HEAD_DIM/2;
          state<=READ_X;
        end else state<=ROPE_DRAIN;
      end
      ROPE_DRAIN: begin end
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
        normalization_pass<=1; index<=0;
        rms_read_count<=0; rms_completed<=0; state<=RMS_NORMALIZE;
      end
      RMS_SQUARE: begin
        if (rms_read_count<length) rms_read_count<=rms_read_count+1;
        if (mul_valid[0]) begin
          flags<=flags | mul_status[0];
          rms_completed<=rms_completed+1;
          if (rms_completed+1==length) begin index<=0; state<=READ_X; end
        end
      end
      RMS_NORMALIZE: begin
        if (rms_read_count<length) rms_read_count<=rms_read_count+1;
        flags<=flags | (mul_valid[0] ? mul_status[0] : 5'd0) |
          (mul_valid[1] ? mul_status[1] : 5'd0);
        if (mul_valid[1]) begin
          rms_completed<=rms_completed+1;
          if (rms_completed+1==length) begin output_index<=0; state<=OUT_READ; end
        end
      end
      SWIGLU_SIGMOID: begin
        if (rms_read_count<length) rms_read_count<=rms_read_count+1;
        flags<=flags | (exp_valid ? exp_status : 5'd0) |
          (add_valid ? add_status : 5'd0) | (recip_valid ? recip_status : 5'd0) |
          (mul_valid[0] && sigmoid_sign_pipe[31] ? mul_status[0] : 5'd0);
        if (mul_valid[0]) begin
          rms_completed<=rms_completed+1;
          if (rms_completed+1==length) begin
            rms_read_count<=0; rms_completed<=0; state<=SWIGLU_PRODUCT;
          end
        end
      end
      SWIGLU_PRODUCT: begin
        if (rms_read_count<length) rms_read_count<=rms_read_count+1;
        flags<=flags | (mul_valid[0] ? mul_status[0] : 5'd0) |
          (mul_valid[1] ? mul_status[1] : 5'd0);
        if (mul_valid[1]) begin
          rms_completed<=rms_completed+1;
          if (rms_completed+1==length) begin output_index<=0; state<=OUT_READ; end
        end
      end
      RESIDUAL_STREAM: begin
        if (rms_read_count<length) rms_read_count<=rms_read_count+1;
        if (add_valid) begin
          flags<=flags | add_status; rms_completed<=rms_completed+1;
          if (rms_completed+1==length) begin output_index<=0; state<=OUT_READ; end
        end
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
    if (rst_n && rope_stream) begin
      flags<=flags | (mul_valid[0] ? mul_status[0] : 5'd0) |
        (mul_valid[1] ? mul_status[1] : 5'd0) | (add_valid ? add_status : 5'd0);
      if (add_valid) begin
        rms_completed<=rms_completed+1;
        if (rms_completed+1==length) begin output_index<=0; state<=OUT_READ; end
      end
    end
  end
endmodule
