module anvil_q4_gqa_attention (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, cmd_epoch, committed_tokens,
  input wire [31:0] hidden, intermediate, query_heads, kv_heads, head_dim, gqa_ratio,
  input wire [31:0] context_capacity,
  output wire cache_cmd_valid,
  input wire cache_cmd_ready,
  output wire cache_cmd_write, cache_cmd_value,
  output wire [31:0] cache_cmd_layer, cache_cmd_pos, cache_cmd_epoch,
  output wire [31:0] cache_cmd_head, cache_cmd_dimension, cache_committed_tokens,
  input wire cache_out_valid,
  output wire cache_out_ready,
  input wire [31:0] cache_result,
  input wire cache_error,
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
  import anvil_q4_fp_pkg::*;
  localparam [5:0] IDLE=0, D_ISSUE=1, D_WAIT=2, ROOT_ISSUE=3, ROOT_WAIT=4,
    INVERSE_ISSUE=5, INVERSE_WAIT=6, CACHE_WRITE=7, CACHE_WRITE_WAIT=8,
    Q_READ=9, Q_WAIT=10, K_READ=11, K_WAIT=12, PRODUCT_ISSUE=13, PRODUCT_WAIT=14,
    ADD_ISSUE=15, ADD_WAIT=16, SCALE_ISSUE=17, SCALE_WAIT=18, SCORE_STORE=19,
    EXP_READ=20, EXP_READ_WAIT=21, SUB_ISSUE=22, SUB_WAIT=23,
    EXP_ISSUE=24, EXP_WAIT=25, EXP_STORE=26, TOTAL_ISSUE=27, TOTAL_WAIT=28,
    NORM_READ=29, NORM_READ_WAIT=30, NORM_ISSUE=31, NORM_WAIT=32, NORM_STORE=33,
    CONTEXT_READ=34, CONTEXT_READ_WAIT=35, V_READ=36, V_WAIT=37,
    CONTEXT_MUL=38, CONTEXT_MUL_WAIT=39, CONTEXT_ADD=40, CONTEXT_ADD_WAIT=41,
    OUTPUT_WRITE=42, OUTPUT_WAIT=43, NEXT_HEAD=44, COMPLETE=45;
  reg [5:0] state;
  reg [31:0] layer, position, epoch, committed, dimension, q_heads, ratio, stride;
  reg [31:0] q_head, kv_head, ratio_index, q_base, component, time_index;
  reg [31:0] operand, inverse_scale, query_value, cache_value, product;
  reg [31:0] accumulator, maximum, total, working, weight;
  reg failed;
  (* ramstyle="M20K", nomem2reg *) reg [31:0] scores [0:131071];
  reg [31:0] score_q;
  always @(posedge clk) begin
    if (rst_n && !flush) begin
      if (state==SCORE_STORE || state==EXP_STORE || state==NORM_STORE)
        scores[time_index[16:0]]<=working;
      if (state==EXP_READ || state==NORM_READ || state==CONTEXT_READ)
        score_q<=scores[time_index[16:0]];
    end
  end
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire issue=(state==Q_READ || state==OUTPUT_WRITE) && port_idle;
  anvil_q4_mem_port scratch_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(state==OUTPUT_WRITE),.kind(4'd8),.layer(32'd0),.proj(3'd0),
    .row(state==OUTPUT_WRITE ? 32'd5 : 32'd2),.col(q_base+component),
    .wdata(state==OUTPUT_WRITE ? accumulator : 32'd0),.stride(stride),.rdata(rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),
    .mem_req_wdata(mem_req_wdata),.mem_req_stride(mem_req_stride),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  assign cache_cmd_valid=rst_n && !flush &&
    (state==CACHE_WRITE || state==K_READ || state==V_READ);
  assign cache_cmd_write=cache_cmd_valid && state==CACHE_WRITE;
  assign cache_cmd_value=cache_cmd_valid && state==V_READ;
  assign cache_cmd_layer=cache_cmd_valid ? layer : 32'd0;
  assign cache_cmd_pos=cache_cmd_valid ? (state==CACHE_WRITE ? position : time_index) : 32'd0;
  assign cache_cmd_epoch=cache_cmd_valid ? epoch : 32'd0;
  assign cache_cmd_head=cache_cmd_valid ? kv_head : 32'd0;
  assign cache_cmd_dimension=cache_cmd_valid ? component : 32'd0;
  assign cache_committed_tokens=cache_cmd_valid ? committed : 32'd0;
  assign cache_out_ready=rst_n && !flush &&
    (state==CACHE_WRITE_WAIT || state==K_WAIT || state==V_WAIT);

  wire fp_ready, fp_valid, exp_ready, exp_valid;
  wire [31:0] fp_result, exp_result;
  wire [4:0] fp_flags, exp_flags;
  wire fp_issue=state==D_ISSUE || state==ROOT_ISSUE || state==INVERSE_ISSUE ||
    state==PRODUCT_ISSUE || state==ADD_ISSUE || state==SCALE_ISSUE ||
    state==SUB_ISSUE || state==TOTAL_ISSUE || state==NORM_ISSUE ||
    state==CONTEXT_MUL || state==CONTEXT_ADD;
  wire fp_wait=state==D_WAIT || state==ROOT_WAIT || state==INVERSE_WAIT ||
    state==PRODUCT_WAIT || state==ADD_WAIT || state==SCALE_WAIT ||
    state==SUB_WAIT || state==TOTAL_WAIT || state==NORM_WAIT ||
    state==CONTEXT_MUL_WAIT || state==CONTEXT_ADD_WAIT;
  wire [3:0] operation=state==D_ISSUE ? 4'd9 : state==ROOT_ISSUE ? 4'd4 :
    state==INVERSE_ISSUE || state==NORM_ISSUE ? 4'd3 :
    state==PRODUCT_ISSUE || state==SCALE_ISSUE || state==CONTEXT_MUL ? 4'd2 :
    state==SUB_ISSUE ? 4'd1 : 4'd0;
  wire [31:0] left=state==D_ISSUE ? dimension :
    state==INVERSE_ISSUE ? 32'h3f800000 : state==PRODUCT_ISSUE ? query_value :
    state==ADD_ISSUE || state==SCALE_ISSUE || state==CONTEXT_ADD ? accumulator :
    state==SUB_ISSUE || state==NORM_ISSUE ? working :
    state==TOTAL_ISSUE ? total : state==CONTEXT_MUL ? weight : operand;
  wire [31:0] right=state==PRODUCT_ISSUE || state==CONTEXT_MUL ? cache_value :
    state==ADD_ISSUE || state==CONTEXT_ADD ? product :
    state==SCALE_ISSUE ? inverse_scale : state==SUB_ISSUE ? maximum :
    state==TOTAL_ISSUE ? working : state==NORM_ISSUE ? total : operand;
  anvil_q4_fp32 arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(fp_issue),.in_ready(fp_ready),.op(operation),.a(left),.b(right),
    .out_valid(fp_valid),.out_ready(fp_wait),.result(fp_result),.flags(fp_flags)
  );
  anvil_q4_exp exponential (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==EXP_ISSUE),.in_ready(exp_ready),.x(operand),
    .out_valid(exp_valid),.out_ready(state==EXP_WAIT),.result(exp_result),.flags(exp_flags)
  );
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  wire cache_completion=cache_out_valid &&
    (state==CACHE_WRITE_WAIT || state==K_WAIT || state==V_WAIT);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; layer<=0; position<=0; epoch<=0; committed<=0; dimension<=0;
      q_heads<=0; ratio<=0; stride<=0; q_head<=0; kv_head<=0; ratio_index<=0;
      q_base<=0; component<=0; time_index<=0; operand<=0; inverse_scale<=0;
      query_value<=0; cache_value<=0; product<=0; accumulator<=0;
      maximum<=0; total<=0; working<=0; weight<=0; failed<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (fault || (cache_completion && cache_error)) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        layer<=cmd_layer; position<=cmd_pos; epoch<=cmd_epoch; committed<=committed_tokens;
        dimension<=head_dim; q_heads<=query_heads; ratio<=gqa_ratio;
        stride<=hidden>intermediate ? hidden : intermediate;
        q_head<=0; kv_head<=0; ratio_index<=0; q_base<=0;
        component<=0; time_index<=0; accumulator<=0;
        maximum<=32'hff800000; total<=0; failed<=0;
        if (head_dim<2 || head_dim>256 || head_dim[0] || query_heads==0 ||
            query_heads>128 || kv_heads==0 || kv_heads>128 ||
            (gqa_ratio!=1 && gqa_ratio!=3 && gqa_ratio!=6 &&
              gqa_ratio!=7 && gqa_ratio!=8) || cmd_pos>=context_capacity ||
            cmd_pos!=committed_tokens || context_capacity>131072) begin
          failed<=1; state<=COMPLETE;
        end else state<=D_ISSUE;
      end
      D_ISSUE: if (fp_ready) state<=D_WAIT;
      D_WAIT: if (fp_valid) begin operand<=fp_result; state<=ROOT_ISSUE; end
      ROOT_ISSUE: if (fp_ready) state<=ROOT_WAIT;
      ROOT_WAIT: if (fp_valid) begin operand<=fp_result; state<=INVERSE_ISSUE; end
      INVERSE_ISSUE: if (fp_ready) state<=INVERSE_WAIT;
      INVERSE_WAIT: if (fp_valid) begin inverse_scale<=fp_result; state<=CACHE_WRITE; end
      CACHE_WRITE: if (cache_cmd_ready) state<=CACHE_WRITE_WAIT;
      CACHE_WRITE_WAIT: if (cache_out_valid) state<=Q_READ;
      Q_READ: if (issue) state<=Q_WAIT;
      Q_WAIT: if (complete) begin query_value<=rdata; state<=K_READ; end
      K_READ: if (cache_cmd_ready) state<=K_WAIT;
      K_WAIT: if (cache_out_valid) begin cache_value<=cache_result; state<=PRODUCT_ISSUE; end
      PRODUCT_ISSUE: if (fp_ready) state<=PRODUCT_WAIT;
      PRODUCT_WAIT: if (fp_valid) begin product<=fp_result; state<=ADD_ISSUE; end
      ADD_ISSUE: if (fp_ready) state<=ADD_WAIT;
      ADD_WAIT: if (fp_valid) begin
        accumulator<=fp_result;
        if (component+1<dimension) begin component<=component+1'b1; state<=Q_READ; end
        else state<=SCALE_ISSUE;
      end
      SCALE_ISSUE: if (fp_ready) state<=SCALE_WAIT;
      SCALE_WAIT: if (fp_valid) begin working<=fp_result; state<=SCORE_STORE; end
      SCORE_STORE: begin
        if (is_nan(working)) maximum<=32'h7fc00000;
        else if (ordered_less(maximum,working)) maximum<=working;
        if (time_index<position) begin
          time_index<=time_index+1'b1; component<=0; accumulator<=0; state<=Q_READ;
        end else begin time_index<=0; state<=EXP_READ; end
      end
      EXP_READ: state<=EXP_READ_WAIT;
      EXP_READ_WAIT: begin working<=score_q; state<=SUB_ISSUE; end
      SUB_ISSUE: if (fp_ready) state<=SUB_WAIT;
      SUB_WAIT: if (fp_valid) begin operand<=fp_result; state<=EXP_ISSUE; end
      EXP_ISSUE: if (exp_ready) state<=EXP_WAIT;
      EXP_WAIT: if (exp_valid) begin working<=exp_result; state<=EXP_STORE; end
      EXP_STORE: state<=TOTAL_ISSUE;
      TOTAL_ISSUE: if (fp_ready) state<=TOTAL_WAIT;
      TOTAL_WAIT: if (fp_valid) begin
        total<=fp_result;
        if (time_index<position) begin time_index<=time_index+1'b1; state<=EXP_READ; end
        else begin time_index<=0; state<=NORM_READ; end
      end
      NORM_READ: state<=NORM_READ_WAIT;
      NORM_READ_WAIT: begin working<=score_q; state<=NORM_ISSUE; end
      NORM_ISSUE: if (fp_ready) state<=NORM_WAIT;
      NORM_WAIT: if (fp_valid) begin working<=fp_result; state<=NORM_STORE; end
      NORM_STORE: begin
        if (time_index<position) begin time_index<=time_index+1'b1; state<=NORM_READ; end
        else begin
          time_index<=0; component<=0; accumulator<=0; state<=CONTEXT_READ;
        end
      end
      CONTEXT_READ: state<=CONTEXT_READ_WAIT;
      CONTEXT_READ_WAIT: begin weight<=score_q; state<=V_READ; end
      V_READ: if (cache_cmd_ready) state<=V_WAIT;
      V_WAIT: if (cache_out_valid) begin cache_value<=cache_result; state<=CONTEXT_MUL; end
      CONTEXT_MUL: if (fp_ready) state<=CONTEXT_MUL_WAIT;
      CONTEXT_MUL_WAIT: if (fp_valid) begin product<=fp_result; state<=CONTEXT_ADD; end
      CONTEXT_ADD: if (fp_ready) state<=CONTEXT_ADD_WAIT;
      CONTEXT_ADD_WAIT: if (fp_valid) begin
        accumulator<=fp_result;
        if (time_index<position) begin time_index<=time_index+1'b1; state<=CONTEXT_READ; end
        else state<=OUTPUT_WRITE;
      end
      OUTPUT_WRITE: if (issue) state<=OUTPUT_WAIT;
      OUTPUT_WAIT: if (complete) begin
        if (component+1<dimension) begin
          component<=component+1'b1; time_index<=0; accumulator<=0; state<=CONTEXT_READ;
        end else state<=NEXT_HEAD;
      end
      NEXT_HEAD: begin
        if (q_head+1<q_heads) begin
          q_head<=q_head+1'b1; q_base<=q_base+dimension;
          if (ratio_index+1<ratio) ratio_index<=ratio_index+1'b1;
          else begin ratio_index<=0; kv_head<=kv_head+1'b1; end
          component<=0; time_index<=0; accumulator<=0;
          maximum<=32'hff800000; total<=0; state<=Q_READ;
        end else state<=COMPLETE;
      end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
