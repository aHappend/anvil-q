module anvil_q1_fp2_flash_attn #(
  parameter HEAD_DIM=64, TILE_TOKENS=16, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_len,
  input wire q_valid,
  output wire q_ready,
  input wire [15:0] q_data,
  input wire q_last,
  input wire kv_valid,
  output wire kv_ready,
  input wire [15:0] k_data, v_data,
  input wire kv_last,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_data,
  output wire out_last,
  output wire done, error,
  output wire [4:0] status
);
  localparam Q_BITS=HEAD_DIM>1 ? $clog2(HEAD_DIM) : 1;
  localparam TILE_WORDS=HEAD_DIM*TILE_TOKENS;
  localparam T_BITS=TILE_WORDS>1 ? $clog2(TILE_WORDS) : 1;
  localparam IDLE=0, QUERY=1, FILL=2, DOT_READ=3, DOT_ISSUE=4, DOT_WAIT=5;
  localparam DOT_ADD=6, DOT_ADD_WAIT=7, SCALE=8, SCALE_WAIT=9;
  localparam DIFFERENCE=10, DIFFERENCE_WAIT=11, EXPONENTIATE=12, EXP_WAIT=13;
  localparam SUM_SCALE=14, SUM_SCALE_WAIT=15, SUM_ADD=16, SUM_ADD_WAIT=17;
  localparam O_READ=18, O_LATCH=19, O_SCALE=20, O_SCALE_WAIT=21;
  localparam O_ADD=22, O_ADD_WAIT=23, RECIP=24, RECIP_WAIT=25;
  localparam NORMALIZE_READ=26, NORMALIZE_LATCH=27, NORMALIZE=28;
  localparam NORMALIZE_WAIT=29, OUTPUT=30, COMPLETE_WAIT=31;
  localparam ERROR_WAIT0=32, ERROR_WAIT1=33, FINISH=34;
  // Elaboration-only integer construction of RNE(1/sqrt(HEAD_DIM)).
  function automatic [31:0] head_scale(input integer dimension);
    reg [127:0] radicand, trial_square;
    reg [63:0] root, candidate;
    reg [24:0] rounded;
    reg guard_bit, sticky_bit;
    integer bit_index, high, distance;
    begin
      radicand=(128'd1 << 126)/128'(dimension);
      root=0;
      for (bit_index=63;bit_index>=0;bit_index=bit_index-1) begin
        candidate=root | (64'd1 << bit_index);
        trial_square={64'd0,candidate}*{64'd0,candidate};
        if (trial_square<=radicand) root=candidate;
      end
      high=0;
      for (bit_index=0;bit_index<64;bit_index=bit_index+1)
        if (root[bit_index]) high=bit_index;
      distance=high-23;
      guard_bit=|(root & (64'd1 << (distance-1)));
      sticky_bit=|(root & ((64'd1 << (distance-1))-1)) ||
        ({64'd0,root}*{64'd0,root}!=radicand);
      rounded={1'b0,24'(root >> distance)}+
        {24'd0,guard_bit && (sticky_bit || root[distance])};
      if (rounded[24]) head_scale={1'b0,8'(high+65),23'd0};
      else head_scale={1'b0,8'(high+64),rounded[22:0]};
    end
  endfunction
  localparam [31:0] SCORE_SCALE=head_scale(HEAD_DIM>0 ? HEAD_DIM : 1);
  function automatic greater(input [31:0] a,b);
    begin
      if (a[30:0]==0 && b[30:0]==0) greater=0;
      else if (a[31]!=b[31]) greater=!a[31];
      else if (a[31]) greater=a[30:0]<b[30:0];
      else greater=a[30:0]>b[30:0];
    end
  endfunction
  generate if (HEAD_DIM<1 || TILE_TOKENS<1 || TILE_TOKENS>16 ||
      MAX_SEQ_LEN<1 || 128'(HEAD_DIM)*128'(TILE_TOKENS)>32'hffffffff) begin: invalid_parameters
    initial $fatal(1,"FP2 ATTENTION PARAMETER ERROR");
  end endgenerate
  reg [5:0] state;
  reg failed;
  reg [4:0] flags;
  reg [31:0] length, component, fill_component, fill_address;
  reg [31:0] filled_tokens, tile_token, tile_offset, processed;
  reg [31:0] score, maximum, next_maximum, running_sum, alpha, probability;
  reg [31:0] temporary, product0, product1, delta0, delta1, inverse, payload;
  reg [31:0] old_output, current_value;
  (* ramstyle = "M20K", nomem2reg *) reg [15:0] query_mem [0:HEAD_DIM-1];
  (* ramstyle = "M20K", nomem2reg *) reg [15:0] key_tile [0:TILE_WORDS-1];
  (* ramstyle = "M20K", nomem2reg *) reg [15:0] value_tile [0:TILE_WORDS-1];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] output_mem [0:HEAD_DIM-1];
  reg [15:0] query_q, key_q, value_q;
  reg [31:0] output_q;
  wire [31:0] tile_address=tile_offset+component;
  wire output_write=rst_n && state==O_ADD_WAIT && add_valid[0] &&
    !(|add_status[0][4:2]);
  wire [1:0] mul_valid, mul_ready, add_valid, add_ready, exp_valid;
  wire [31:0] mul_result [0:1], add_result [0:1], exp_result [0:1];
  wire [4:0] mul_status [0:1], add_status [0:1], exp_status [0:1];
  reg [31:0] mul_a0, mul_b0, mul_a1, mul_b1, add_a0, add_b0, add_a1, add_b1;
  wire recip_valid;
  wire [31:0] recip_result;
  wire [4:0] recip_status;
  wire multiply_issue=state==DOT_ISSUE || state==SCALE ||
    state==SUM_SCALE || state==O_SCALE || state==NORMALIZE;
  wire addition_issue=state==DOT_ADD || state==DIFFERENCE ||
    state==SUM_ADD || state==O_ADD;
  anvil_q1_fp2_fp32_binary #(.MULTIPLY(1)) multiply0(
    .clk(clk),.rst_n(rst_n),.in_valid(multiply_issue),.in_ready(mul_ready[0]),
    .out_ready(1'b1),.a(mul_a0),.b(mul_b0),.out_valid(mul_valid[0]),
    .result(mul_result[0]),.status(mul_status[0]));
  anvil_q1_fp2_fp32_binary #(.MULTIPLY(1)) multiply1(
    .clk(clk),.rst_n(rst_n),.in_valid(state==O_SCALE),.in_ready(mul_ready[1]),
    .out_ready(1'b1),.a(mul_a1),.b(mul_b1),.out_valid(mul_valid[1]),
    .result(mul_result[1]),.status(mul_status[1]));
  anvil_q1_fp2_fp32_binary #(.MULTIPLY(0)) add0(
    .clk(clk),.rst_n(rst_n),.in_valid(addition_issue),.in_ready(add_ready[0]),
    .out_ready(1'b1),.a(add_a0),.b(add_b0),.out_valid(add_valid[0]),
    .result(add_result[0]),.status(add_status[0]));
  anvil_q1_fp2_fp32_binary #(.MULTIPLY(0)) add1(
    .clk(clk),.rst_n(rst_n),.in_valid(state==DIFFERENCE),.in_ready(add_ready[1]),
    .out_ready(1'b1),.a(add_a1),.b(add_b1),.out_valid(add_valid[1]),
    .result(add_result[1]),.status(add_status[1]));
  anvil_q1_fp2_exp exponent0(
    .clk(clk),.rst_n(rst_n),.in_valid(state==EXPONENTIATE),.x(delta0),
    .out_valid(exp_valid[0]),.result(exp_result[0]),.status(exp_status[0]));
  anvil_q1_fp2_exp exponent1(
    .clk(clk),.rst_n(rst_n),.in_valid(state==EXPONENTIATE),.x(delta1),
    .out_valid(exp_valid[1]),.result(exp_result[1]),.status(exp_status[1]));
  anvil_q1_fp2_reciprocal reciprocal(
    .clk(clk),.rst_n(rst_n),.in_valid(state==RECIP),.x(running_sum),
    .out_valid(recip_valid),.result(recip_result),.status(recip_status));
  assign cmd_ready=rst_n && state==IDLE;
  assign q_ready=rst_n && state==QUERY;
  assign kv_ready=rst_n && state==FILL;
  assign out_valid=rst_n && state==OUTPUT;
  assign out_data=out_valid ? payload : 32'd0;
  assign out_last=out_valid && component+1==HEAD_DIM;
  assign done=rst_n && state==FINISH;
  assign error=done && failed;
  assign status=rst_n && (out_valid || done) ? flags : 5'd0;
  always @* begin
    mul_a0={query_q,16'd0}; mul_b0={key_q,16'd0};
    mul_a1=probability; mul_b1=current_value;
    case (state)
      SCALE: begin mul_a0=score; mul_b0=SCORE_SCALE; end
      SUM_SCALE: begin mul_a0=alpha; mul_b0=running_sum; end
      O_SCALE: begin mul_a0=alpha; mul_b0=old_output; end
      NORMALIZE: begin mul_a0=old_output; mul_b0=inverse; end
      default: begin end
    endcase
    add_a0=score; add_b0=temporary; add_a1=score;
    add_b1={~next_maximum[31],next_maximum[30:0]};
    case (state)
      DIFFERENCE: begin
        add_a0=maximum; add_b0={~next_maximum[31],next_maximum[30:0]};
      end
      SUM_ADD: begin add_a0=temporary; add_b0=probability; end
      O_ADD: begin add_a0=product0; add_b0=product1; end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if (q_valid && q_ready) query_mem[component[Q_BITS-1:0]]<=q_data;
    if (kv_valid && kv_ready) begin
      key_tile[fill_address[T_BITS-1:0]]<=k_data;
      value_tile[fill_address[T_BITS-1:0]]<=v_data;
    end
    query_q<=query_mem[component[Q_BITS-1:0]];
    key_q<=key_tile[tile_address[T_BITS-1:0]];
    value_q<=value_tile[tile_address[T_BITS-1:0]];
    output_q<=output_mem[component[Q_BITS-1:0]];
    if (output_write) output_mem[component[Q_BITS-1:0]]<=add_result[0];
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; flags<=0; length<=0; component<=0;
      fill_component<=0; fill_address<=0; filled_tokens<=0; tile_token<=0;
      tile_offset<=0; processed<=0; score<=0; maximum<=0; next_maximum<=0;
      running_sum<=0; alpha<=0; probability<=0; temporary<=0;
      product0<=0; product1<=0; delta0<=0; delta1<=0; inverse<=0; payload<=0;
      old_output<=0; current_value<=0;
    end else case (state)
      IDLE: if (cmd_valid) begin
        length<=cmd_len; component<=0; fill_component<=0; fill_address<=0;
        filled_tokens<=0; tile_token<=0; tile_offset<=0; processed<=0;
        score<=0; maximum<=32'hff800000; running_sum<=0; failed<=0; flags<=0;
        if (cmd_len==0 || cmd_len>MAX_SEQ_LEN) begin failed<=1; state<=ERROR_WAIT0; end
        else state<=QUERY;
      end
      QUERY: if (q_valid) begin
        if (q_last!=(component+1==HEAD_DIM)) begin failed<=1; state<=ERROR_WAIT0; end
        else if (q_last) begin component<=0; state<=FILL; end
        else component<=component+1;
      end
      FILL: if (kv_valid) begin
        if (kv_last!=(fill_component+1==HEAD_DIM)) begin failed<=1; state<=ERROR_WAIT0; end
        else begin
          fill_address<=fill_address+1;
          if (kv_last) begin
            fill_component<=0; filled_tokens<=filled_tokens+1;
            if (filled_tokens+1==TILE_TOKENS || processed+filled_tokens+1==length) begin
              component<=0; tile_offset<=0; tile_token<=0; score<=0; state<=DOT_READ;
            end
          end else fill_component<=fill_component+1;
        end
      end
      DOT_READ: state<=DOT_ISSUE;
      DOT_ISSUE: if (mul_ready[0]) state<=DOT_WAIT;
      DOT_WAIT: if (mul_valid[0]) begin
        flags<=flags | mul_status[0];
        if (|mul_status[0][4:2]) begin failed<=1; state<=ERROR_WAIT0; end
        else begin temporary<=mul_result[0]; state<=DOT_ADD; end
      end
      DOT_ADD: if (add_ready[0]) state<=DOT_ADD_WAIT;
      DOT_ADD_WAIT: if (add_valid[0]) begin
        flags<=flags | add_status[0]; score<=add_result[0];
        if (|add_status[0][4:2]) begin failed<=1; state<=ERROR_WAIT0; end
        else if (component+1<HEAD_DIM) begin component<=component+1; state<=DOT_READ; end
        else state<=SCALE;
      end
      SCALE: if (mul_ready[0]) state<=SCALE_WAIT;
      SCALE_WAIT: if (mul_valid[0]) begin
        flags<=flags | mul_status[0]; score<=mul_result[0];
        if (|mul_status[0][4:2] || mul_result[0][30:23]==255) begin
          failed<=1; flags<=flags | mul_status[0] | 5'b10000; state<=ERROR_WAIT0;
        end else if (processed==0) begin
          maximum<=mul_result[0]; alpha<=0; probability<=32'h3f800000;
          state<=SUM_SCALE;
        end else begin
          next_maximum<=greater(mul_result[0],maximum) ? mul_result[0] : maximum;
          state<=DIFFERENCE;
        end
      end
      DIFFERENCE: if (&add_ready) state<=DIFFERENCE_WAIT;
      DIFFERENCE_WAIT: if (&add_valid) begin
        flags<=flags | add_status[0] | add_status[1];
        if (|add_status[0][4:2] || |add_status[1][4:2]) begin
          failed<=1; state<=ERROR_WAIT0;
        end else begin
          delta0<=add_result[0]; delta1<=add_result[1]; state<=EXPONENTIATE;
        end
      end
      EXPONENTIATE: state<=EXP_WAIT;
      EXP_WAIT: if (&exp_valid) begin
        flags<=flags | exp_status[0] | exp_status[1];
        if (|exp_status[0][4:2] || |exp_status[1][4:2]) begin
          failed<=1; state<=ERROR_WAIT0;
        end else begin
          alpha<=exp_result[0]; probability<=exp_result[1]; maximum<=next_maximum;
          state<=SUM_SCALE;
        end
      end
      SUM_SCALE: if (mul_ready[0]) state<=SUM_SCALE_WAIT;
      SUM_SCALE_WAIT: if (mul_valid[0]) begin
        flags<=flags | mul_status[0];
        if (|mul_status[0][4:2]) begin failed<=1; state<=ERROR_WAIT0; end
        else begin temporary<=mul_result[0]; state<=SUM_ADD; end
      end
      SUM_ADD: if (add_ready[0]) state<=SUM_ADD_WAIT;
      SUM_ADD_WAIT: if (add_valid[0]) begin
        flags<=flags | add_status[0];
        if (|add_status[0][4:2]) begin failed<=1; state<=ERROR_WAIT0; end
        else begin running_sum<=add_result[0]; component<=0; state<=O_READ; end
      end
      O_READ: state<=O_LATCH;
      O_LATCH: begin
        old_output<=processed==0 ? 32'd0 : output_q;
        current_value<={value_q,16'd0}; state<=O_SCALE;
      end
      O_SCALE: if (&mul_ready) state<=O_SCALE_WAIT;
      O_SCALE_WAIT: if (&mul_valid) begin
        flags<=flags | mul_status[0] | mul_status[1];
        if (|mul_status[0][4:2] || |mul_status[1][4:2]) begin
          failed<=1; state<=ERROR_WAIT0;
        end else begin product0<=mul_result[0]; product1<=mul_result[1]; state<=O_ADD; end
      end
      O_ADD: if (add_ready[0]) state<=O_ADD_WAIT;
      O_ADD_WAIT: if (add_valid[0]) begin
        flags<=flags | add_status[0];
        if (|add_status[0][4:2]) begin failed<=1; state<=ERROR_WAIT0; end
        else if (component+1<HEAD_DIM) begin component<=component+1; state<=O_READ; end
        else begin
          processed<=processed+1; component<=0; score<=0;
          if (tile_token+1<filled_tokens) begin
            tile_token<=tile_token+1; tile_offset<=tile_offset+HEAD_DIM; state<=DOT_READ;
          end else if (processed+1<length) begin
            fill_address<=0; fill_component<=0; filled_tokens<=0; state<=FILL;
          end else state<=RECIP;
        end
      end
      RECIP: state<=RECIP_WAIT;
      RECIP_WAIT: if (recip_valid) begin
        flags<=flags | recip_status;
        if (|recip_status[4:2]) begin failed<=1; state<=ERROR_WAIT0; end
        else begin inverse<=recip_result; component<=0; state<=NORMALIZE_READ; end
      end
      NORMALIZE_READ: state<=NORMALIZE_LATCH;
      NORMALIZE_LATCH: begin old_output<=output_q; state<=NORMALIZE; end
      NORMALIZE: if (mul_ready[0]) state<=NORMALIZE_WAIT;
      NORMALIZE_WAIT: if (mul_valid[0]) begin
        flags<=flags | mul_status[0];
        if (|mul_status[0][4:2]) begin failed<=1; state<=ERROR_WAIT0; end
        else begin payload<=mul_result[0]; state<=OUTPUT; end
      end
      OUTPUT: if (out_ready) begin
        if (component+1==HEAD_DIM) state<=COMPLETE_WAIT;
        else begin component<=component+1; state<=NORMALIZE_READ; end
      end
      COMPLETE_WAIT: state<=FINISH;
      ERROR_WAIT0: state<=ERROR_WAIT1;
      ERROR_WAIT1: state<=FINISH;
      FINISH: state<=IDLE;
      default: begin failed<=1; state<=ERROR_WAIT0; end
    endcase
  end
endmodule
