module anvil_q1_fp_gqa_attention #(
  parameter NUM_LAYERS=24, HIDDEN_SIZE=896, NUM_Q_HEADS=14,
  NUM_KV_HEADS=2, HEAD_DIM=64, MAX_SEQ_LEN=32768
)(
  input wire clk, rst_n, cmd_valid, output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, output wire done, error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error,
  input wire [1:0] cmd_precision
);
  localparam RATIO=NUM_KV_HEADS>0 && NUM_Q_HEADS>=NUM_KV_HEADS ?
    NUM_Q_HEADS/NUM_KV_HEADS : 1;
  localparam KV_SIZE=NUM_KV_HEADS*HEAD_DIM;
  localparam [36:0] DIM_PACKED=anvil_q1_fp_pkg::pack_grid(
    69'(HEAD_DIM>0 ? HEAD_DIM : 1),1'b0,11'sd0,1'b0);
  reg [6:0] state;
  reg failed, value_cache, context_pass;
  reg [1:0] precision;
  reg [31:0] layer, position, index, head, kv_head, group_offset;
  reg [31:0] time_index, dim, component, q, cache_data;
  reg signed [95:0] dot, max_score, current_score, weighted;
  reg signed [63:0] compat_product;
  reg signed [64:0] compat_weighted_product;
  reg [63:0] denominator, sqrt_dim;
  reg [31:0] exponential, output_value;
  reg [31:0] fp_dot, fp_max, fp_score, fp_weighted, fp_denominator;
  reg [31:0] inverse_dim, temporary;
  wire signed [96:0] score_difference;
  wire signed [63:0] exp_argument;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  wire div_ready, div_valid, div_zero, sqrt_ready, sqrt_valid;
  wire signed [127:0] div_result;
  wire [63:0] sqrt_result;
  wire compat_exp_ready, compat_exp_valid;
  wire [31:0] compat_exp_result;
  wire mul_valid, add_valid, exp_valid, recip_valid, rsqrt_valid;
  wire [31:0] mul_result, add_result, exp_result, recip_result, rsqrt_result;
  wire [4:0] mul_status, add_status, exp_status, recip_status, rsqrt_status;
  reg [31:0] mul_a, mul_b, add_a, add_b;
  wire native_fault, score_greater;
  anvil_q1_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,HIDDEN_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,1,4,1,MAX_SEQ_LEN) parameters_ok();
  assign score_difference=$signed({current_score[95],current_score})-
    $signed({max_score[95],max_score});
  assign exp_argument=score_difference< -97'sd1048576 ? -64'sd1048577 :
    (score_difference>0 ? 64'sd0 : $signed(score_difference[63:0]));
  assign score_greater=(fp_score[30:0]==0 && fp_max[30:0]==0) ? 1'b0 :
    (fp_score[31]!=fp_max[31] ? !fp_score[31] :
      (fp_score[31] ? fp_score[30:0]<fp_max[30:0] : fp_score[30:0]>fp_max[30:0]));
  anvil_q1_fp_compat_sqrt dimension_sqrt(
    clk,rst_n,state==62,sqrt_ready,128'(HEAD_DIM)<<32,sqrt_valid,sqrt_result);
  anvil_q1_fp_compat_round_div divider(
    clk,rst_n,state==10 || state==56,div_ready,
    state==10 ? $signed({{32{dot[95]}},dot}) : $signed({{32{weighted[95]}},weighted}),
    state==10 ? sqrt_dim : denominator,div_valid,div_result,div_zero);
  anvil_q1_fp_compat_exp compat_exp(clk,rst_n,state==42,compat_exp_ready,
    exp_argument,compat_exp_valid,compat_exp_result);
  anvil_q1_fp_mul multiply_pipeline(
    clk,rst_n,state==32 || state==40 || state==52 || state==60,
    mul_a,mul_b,mul_valid,mul_result,mul_status);
  anvil_q1_fp_add add_pipeline(
    clk,rst_n,state==34 || state==44 || state==48 || state==54,
    add_a,add_b,add_valid,add_result,add_status);
  anvil_q1_fp_exp exp_pipeline(clk,rst_n,state==46,temporary,exp_valid,exp_result,exp_status);
  anvil_q1_fp_reciprocal reciprocal_pipeline(clk,rst_n,state==58,fp_denominator,
    recip_valid,recip_result,recip_status);
  anvil_q1_fp_rsqrt rsqrt_pipeline(clk,rst_n,state==64,DIM_PACKED[31:0],
    rsqrt_valid,rsqrt_result,rsqrt_status);
  assign native_fault=
    ((state==33 || state==41 || state==53 || state==61) && mul_valid && |mul_status[4:2]) ||
    ((state==35 || state==45 || state==49 || state==55) && add_valid && |add_status[4:2]) ||
    (state==47 && exp_valid && |exp_status[4:2]) ||
    (state==59 && recip_valid && |recip_status[4:2]) ||
    (state==65 && rsqrt_valid && |rsqrt_status[4:2]);
  always @* begin
    mul_a=q; mul_b=cache_data; add_a=fp_dot; add_b=temporary;
    if(state==40) begin mul_a=fp_dot; mul_b=inverse_dim; end
    if(state==52) begin mul_a=cache_data; mul_b=exponential; end
    if(state==60) begin mul_a=fp_weighted; mul_b=temporary; end
    if(state==44) begin add_a=fp_score; add_b={!fp_max[31],fp_max[30:0]}; end
    if(state==48) begin add_a=fp_denominator; add_b=exponential; end
    if(state==54) begin add_a=fp_weighted; add_b=temporary; end
  end
  assign cmd_ready=rst_n && state==0;
  assign done=rst_n && state==31;
  assign error=done && failed;
  anvil_q1_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(wr),.kind(kind),.layer(ml),
    .proj(3'd0),.row(row),.col(col),.wdata(wd),
    .idle(idle),.complete(complete),.rdata(rd),.fault(fault),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
  always @* begin
    issue=0; wr=0; kind=0; row=0; col=0; wd=0; ml=0;
    if(rst_n && idle) case(state)
      1: begin issue=1; kind=8; row=value_cache ? 4 : 3; col=index; end
      3: begin
        issue=1; wr=1; kind=value_cache ? 10 : 9; ml=layer;
        row=position; col=index; wd=cache_data;
      end
      6: begin issue=1; kind=8; row=2; col=head*HEAD_DIM+dim; end
      8: begin issue=1; kind=9; ml=layer; row=time_index; col=kv_head*HEAD_DIM+dim; end
      13: begin issue=1; kind=10; ml=layer; row=time_index; col=kv_head*HEAD_DIM+component; end
      16: begin
        issue=1; wr=1; kind=8; row=5; col=head*HEAD_DIM+component; wd=output_value;
      end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; failed<=0; precision<=0; value_cache<=0; context_pass<=0;
      layer<=0; position<=0; index<=0; head<=0; time_index<=0; dim<=0;
      component<=0; q<=0; cache_data<=0; dot<=0; max_score<=0;
      current_score<=0; weighted<=0; denominator<=0; exponential<=0;
      kv_head<=0; group_offset<=0; compat_product<=0; compat_weighted_product<=0;
      sqrt_dim<=0; fp_dot<=0; fp_max<=0; fp_score<=0; fp_weighted<=0;
      fp_denominator<=0; inverse_dim<=0; temporary<=0; output_value<=0;
    end else if(fault || native_fault) begin failed<=1; state<=31; end
    else if(complete && precision!=0 && rd[30:23]==255 &&
      (state==2 || state==7 || state==9 || state==14)) begin failed<=1; state<=31; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; precision<=cmd_precision; layer<=cmd_layer; position<=cmd_pos;
        index<=0; value_cache<=0; head<=0; kv_head<=0; group_offset<=0;
        time_index<=0; dim<=0; component<=0; context_pass<=0;
        dot<=0; max_score<={1'b1,95'd0}; weighted<=0; denominator<=0;
        fp_dot<=0; fp_max<=32'hff800000; fp_weighted<=0; fp_denominator<=0;
        if(cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_precision==3)
          begin failed<=1; state<=30; end
        else if(cmd_precision==0) state<=62;
        else state<=64;
      end
      62: if(sqrt_ready) state<=63;
      63: if(sqrt_valid) begin
        if(sqrt_result==0) begin failed<=1; state<=31; end
        else begin sqrt_dim<=sqrt_result; state<=1; end
      end
      64: state<=65;
      65: if(rsqrt_valid) begin inverse_dim<=rsqrt_result; state<=1; end
      1: if(issue) state<=2;
      2: if(complete) begin cache_data<=rd; state<=3; end
      3: if(issue) state<=4;
      4: if(complete) begin
        if(index+1<KV_SIZE) begin index<=index+1; state<=1; end
        else if(!value_cache) begin value_cache<=1; index<=0; state<=1; end
        else state<=6;
      end
      6: if(issue) state<=7;
      7: if(complete) begin q<=rd; state<=8; end
      8: if(issue) state<=9;
      9: if(complete) begin
        cache_data<=rd;
        if(precision==0) state<=36; else state<=32;
      end
      36: begin compat_product<=$signed(q)*$signed(cache_data); state<=37; end
      37: begin dot<=dot+{{32{compat_product[63]}},compat_product}; state<=39; end
      32: state<=33;
      33: if(mul_valid) begin temporary<=mul_result; state<=34; end
      34: state<=35;
      35: if(add_valid) begin fp_dot<=add_result; state<=39; end
      39: if(dim+1<HEAD_DIM) begin dim<=dim+1; state<=6; end
          else if(precision==0) state<=10;
          else state<=40;
      10: if(div_ready) state<=38;
      38: if(div_valid) begin
        if(div_zero) begin failed<=1; state<=31; end
        else begin current_score<=div_result[95:0]; state<=11; end
      end
      40: state<=41;
      41: if(mul_valid) begin fp_score<=mul_result; state<=11; end
      11: if(!context_pass) begin
        if(precision==0) begin if(current_score>max_score) max_score<=current_score; end
        else if(score_greater) fp_max<=fp_score;
        dim<=0; dot<=0; fp_dot<=0; state<=6;
        if(time_index<position) time_index<=time_index+1;
        else begin context_pass<=1; time_index<=0; end
      end else if(precision==0) state<=42;
      else state<=44;
      42: if(compat_exp_ready) state<=43;
      43: if(compat_exp_valid) begin exponential<=compat_exp_result; state<=12; end
      44: state<=45;
      45: if(add_valid) begin temporary<=add_result; state<=46; end
      46: state<=47;
      47: if(exp_valid) begin exponential<=exp_result; state<=12; end
      12: if(precision==0) begin denominator<=denominator+exponential; state<=13; end
          else state<=48;
      48: state<=49;
      49: if(add_valid) begin fp_denominator<=add_result; state<=13; end
      13: if(issue) state<=14;
      14: if(complete) begin
        cache_data<=rd;
        if(precision==0) state<=50; else state<=52;
      end
      50: begin compat_weighted_product<=$signed(cache_data)*$signed({1'b0,exponential}); state<=51; end
      51: begin weighted<=weighted+{{31{compat_weighted_product[64]}},compat_weighted_product}; state<=15; end
      52: state<=53;
      53: if(mul_valid) begin temporary<=mul_result; state<=54; end
      54: state<=55;
      55: if(add_valid) begin fp_weighted<=add_result; state<=15; end
      15: if(time_index<position) begin
        time_index<=time_index+1; dim<=0; dot<=0; fp_dot<=0; state<=6;
      end else if((precision==0 && denominator==0) ||
        (precision!=0 && (fp_denominator[31] || fp_denominator[30:0]==0)))
        begin failed<=1; state<=31; end
      else if(precision==0) state<=56;
      else state<=58;
      56: if(div_ready) state<=57;
      57: if(div_valid) begin
        if(div_zero) begin failed<=1; state<=31; end
        else begin output_value<=anvil_q1_fp_compat_pkg::sat32(div_result); state<=16; end
      end
      58: state<=59;
      59: if(recip_valid) begin temporary<=recip_result; state<=60; end
      60: state<=61;
      61: if(mul_valid) begin output_value<=mul_result; state<=16; end
      16: if(issue) state<=17;
      17: if(complete) begin
        time_index<=0; dim<=0; dot<=0; weighted<=0; denominator<=0;
        fp_dot<=0; fp_weighted<=0; fp_denominator<=0;
        if(component+1<HEAD_DIM) begin component<=component+1; state<=6; end
        else if(head+1<NUM_Q_HEADS) begin
          head<=head+1; component<=0; context_pass<=0;
          if(group_offset+1==RATIO) begin group_offset<=0; kv_head<=kv_head+1; end
          else group_offset<=group_offset+1;
          max_score<={1'b1,95'd0}; fp_max<=32'hff800000; state<=6;
        end else state<=31;
      end
      30: state<=31;
      31: state<=0;
      default: state<=0;
    endcase
  end
endmodule
