module anvil_q4_fp_gqa_attention (
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
  localparam [5:0] IDLE=0, SCALE_LOAD=1, CACHE_WRITE=7, CACHE_WRITE_WAIT=8,
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
  // RNE(1/sqrt(2*half_dimension)), with no rounded intermediate root.
  function automatic [31:0] attention_scale(input [7:0] half_dimension);
    begin
      case (half_dimension)
        8'd1: attention_scale=32'h3f3504f3;
        8'd2: attention_scale=32'h3f000000;
        8'd3: attention_scale=32'h3ed105ec;
        8'd4: attention_scale=32'h3eb504f3;
        8'd5: attention_scale=32'h3ea1e89b;
        8'd6: attention_scale=32'h3e93cd3a;
        8'd7: attention_scale=32'h3e88d677;
        8'd8: attention_scale=32'h3e800000;
        8'd9: attention_scale=32'h3e715bef;
        8'd10: attention_scale=32'h3e64f92e;
        8'd11: attention_scale=32'h3e5a514a;
        8'd12: attention_scale=32'h3e5105ec;
        8'd13: attention_scale=32'h3e48d2ab;
        8'd14: attention_scale=32'h3e41848f;
        8'd15: attention_scale=32'h3e3af4ba;
        8'd16: attention_scale=32'h3e3504f3;
        8'd17: attention_scale=32'h3e2f9d53;
        8'd18: attention_scale=32'h3e2aaaab;
        8'd19: attention_scale=32'h3e261d5f;
        8'd20: attention_scale=32'h3e21e89b;
        8'd21: attention_scale=32'h3e1e01b3;
        8'd22: attention_scale=32'h3e1a5fb2;
        8'd23: attention_scale=32'h3e16fb06;
        8'd24: attention_scale=32'h3e13cd3a;
        8'd25: attention_scale=32'h3e10d0c3;
        8'd26: attention_scale=32'h3e0e00d5;
        8'd27: attention_scale=32'h3e0b5948;
        8'd28: attention_scale=32'h3e08d677;
        8'd29: attention_scale=32'h3e067532;
        8'd30: attention_scale=32'h3e0432a5;
        8'd31: attention_scale=32'h3e020c52;
        8'd32: attention_scale=32'h3e000000;
        8'd33: attention_scale=32'h3dfc1764;
        8'd34: attention_scale=32'h3df85b42;
        8'd35: attention_scale=32'h3df4c867;
        8'd36: attention_scale=32'h3df15bef;
        8'd37: attention_scale=32'h3dee133e;
        8'd38: attention_scale=32'h3deaebf5;
        8'd39: attention_scale=32'h3de7e3ed;
        8'd40: attention_scale=32'h3de4f92e;
        8'd41: attention_scale=32'h3de229ed;
        8'd42: attention_scale=32'h3ddf7483;
        8'd43: attention_scale=32'h3ddcd76e;
        8'd44: attention_scale=32'h3dda514a;
        8'd45: attention_scale=32'h3dd7e0cf;
        8'd46: attention_scale=32'h3dd584cd;
        8'd47: attention_scale=32'h3dd33c2e;
        8'd48: attention_scale=32'h3dd105ec;
        8'd49: attention_scale=32'h3dcee116;
        8'd50: attention_scale=32'h3dcccccd;
        8'd51: attention_scale=32'h3dcac83f;
        8'd52: attention_scale=32'h3dc8d2ab;
        8'd53: attention_scale=32'h3dc6eb5a;
        8'd54: attention_scale=32'h3dc511a3;
        8'd55: attention_scale=32'h3dc344e6;
        8'd56: attention_scale=32'h3dc1848f;
        8'd57: attention_scale=32'h3dbfd012;
        8'd58: attention_scale=32'h3dbe26eb;
        8'd59: attention_scale=32'h3dbc889f;
        8'd60: attention_scale=32'h3dbaf4ba;
        8'd61: attention_scale=32'h3db96ace;
        8'd62: attention_scale=32'h3db7ea74;
        8'd63: attention_scale=32'h3db6734a;
        8'd64: attention_scale=32'h3db504f3;
        8'd65: attention_scale=32'h3db39f19;
        8'd66: attention_scale=32'h3db2416a;
        8'd67: attention_scale=32'h3db0eb96;
        8'd68: attention_scale=32'h3daf9d53;
        8'd69: attention_scale=32'h3dae565c;
        8'd70: attention_scale=32'h3dad166c;
        8'd71: attention_scale=32'h3dabdd46;
        8'd72: attention_scale=32'h3daaaaab;
        8'd73: attention_scale=32'h3da97e62;
        8'd74: attention_scale=32'h3da85835;
        8'd75: attention_scale=32'h3da737f0;
        8'd76: attention_scale=32'h3da61d5f;
        8'd77: attention_scale=32'h3da50855;
        8'd78: attention_scale=32'h3da3f8a2;
        8'd79: attention_scale=32'h3da2ee1d;
        8'd80: attention_scale=32'h3da1e89b;
        8'd81: attention_scale=32'h3da0e7f5;
        8'd82: attention_scale=32'h3d9fec04;
        8'd83: attention_scale=32'h3d9ef4a4;
        8'd84: attention_scale=32'h3d9e01b3;
        8'd85: attention_scale=32'h3d9d130e;
        8'd86: attention_scale=32'h3d9c2896;
        8'd87: attention_scale=32'h3d9b422c;
        8'd88: attention_scale=32'h3d9a5fb2;
        8'd89: attention_scale=32'h3d99810c;
        8'd90: attention_scale=32'h3d98a61f;
        8'd91: attention_scale=32'h3d97ced0;
        8'd92: attention_scale=32'h3d96fb06;
        8'd93: attention_scale=32'h3d962aa9;
        8'd94: attention_scale=32'h3d955da2;
        8'd95: attention_scale=32'h3d9493d9;
        8'd96: attention_scale=32'h3d93cd3a;
        8'd97: attention_scale=32'h3d9309af;
        8'd98: attention_scale=32'h3d924925;
        8'd99: attention_scale=32'h3d918b87;
        8'd100: attention_scale=32'h3d90d0c3;
        8'd101: attention_scale=32'h3d9018c6;
        8'd102: attention_scale=32'h3d8f6381;
        8'd103: attention_scale=32'h3d8eb0e0;
        8'd104: attention_scale=32'h3d8e00d5;
        8'd105: attention_scale=32'h3d8d534f;
        8'd106: attention_scale=32'h3d8ca83f;
        8'd107: attention_scale=32'h3d8bff97;
        8'd108: attention_scale=32'h3d8b5948;
        8'd109: attention_scale=32'h3d8ab544;
        8'd110: attention_scale=32'h3d8a137d;
        8'd111: attention_scale=32'h3d8973e8;
        8'd112: attention_scale=32'h3d88d677;
        8'd113: attention_scale=32'h3d883b1e;
        8'd114: attention_scale=32'h3d87a1d2;
        8'd115: attention_scale=32'h3d870a87;
        8'd116: attention_scale=32'h3d867532;
        8'd117: attention_scale=32'h3d85e1c7;
        8'd118: attention_scale=32'h3d85503e;
        8'd119: attention_scale=32'h3d84c08b;
        8'd120: attention_scale=32'h3d8432a5;
        8'd121: attention_scale=32'h3d83a682;
        8'd122: attention_scale=32'h3d831c1a;
        8'd123: attention_scale=32'h3d829362;
        8'd124: attention_scale=32'h3d820c52;
        8'd125: attention_scale=32'h3d8186e2;
        8'd126: attention_scale=32'h3d81030a;
        8'd127: attention_scale=32'h3d8080c1;
        8'd128: attention_scale=32'h3d800000;
        default: attention_scale=32'h7fc00000;
      endcase
    end
  endfunction
  wire [31:0] scale_value=attention_scale(dimension[8:1]);
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
  anvil_q4_fp_mem_port scratch_port (
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
  wire fp_issue=state==PRODUCT_ISSUE || state==ADD_ISSUE || state==SCALE_ISSUE ||
    state==SUB_ISSUE || state==TOTAL_ISSUE || state==NORM_ISSUE ||
    state==CONTEXT_MUL || state==CONTEXT_ADD;
  wire fp_wait=state==PRODUCT_WAIT || state==ADD_WAIT || state==SCALE_WAIT ||
    state==SUB_WAIT || state==TOTAL_WAIT || state==NORM_WAIT ||
    state==CONTEXT_MUL_WAIT || state==CONTEXT_ADD_WAIT;
  wire [3:0] operation=state==NORM_ISSUE ? 4'd3 :
    state==PRODUCT_ISSUE || state==SCALE_ISSUE || state==CONTEXT_MUL ? 4'd2 :
    state==SUB_ISSUE ? 4'd1 : 4'd0;
  wire [31:0] left=state==PRODUCT_ISSUE ? query_value :
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
  anvil_q4_fp_exp exponential (
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
            gqa_ratio<1 || gqa_ratio>8 ||
            {32'd0,query_heads}!={32'd0,kv_heads}*{32'd0,gqa_ratio} ||
            {32'd0,hidden}!={32'd0,query_heads}*{32'd0,head_dim} ||
            cmd_pos>=context_capacity || context_capacity==0 ||
            cmd_pos!=committed_tokens || context_capacity>131072) begin
          failed<=1; state<=COMPLETE;
        end else state<=SCALE_LOAD;
      end
      SCALE_LOAD: begin inverse_scale<=scale_value; state<=CACHE_WRITE; end
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
