module anvil_q1_gqa_attention #(
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
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  localparam RATIO = NUM_KV_HEADS>0 && NUM_Q_HEADS>=NUM_KV_HEADS ?
                      NUM_Q_HEADS/NUM_KV_HEADS : 1;
  localparam KV_SIZE = NUM_KV_HEADS*HEAD_DIM;
  reg [4:0] state;
  reg failed, value_cache, context_pass;
  reg [31:0] layer, position, index, head, time_index, dim, component;
  reg [31:0] kv_head, head_in_group;
  reg signed [31:0] context_value;
  reg signed [31:0] q, cache_data;
  reg signed [95:0] dot, max_score, current_score, weighted;
  reg [63:0] denominator;
  reg [31:0] exponential;
  wire signed [31:0] read_key, read_value;
  wire signed [63:0] dot_product;
  wire signed [127:0] division_input, division_result;
  wire [128:0] division_magnitude, division_numerator, division_quotient;
  wire [63:0] division_denominator;
  wire div_ready, div_done, div_error;
  wire exp_ready, exp_done, exp_error;
  wire [31:0] exp_value;
  wire signed [64:0] weighted_product;
  wire signed [96:0] score_difference;
  wire signed [63:0] exp_argument;
  wire [63:0] sqrt_dim;
  wire [127:0] dim_scaled;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  anvil_q1_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,HIDDEN_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,1,4,1,MAX_SEQ_LEN) parameters_ok();
  assign read_key=(complete && state==9) ? rd : 32'sd0;
  assign read_value=(complete && state==14) ? rd : 32'sd0;
  assign dot_product=$signed({{32{q[31]}},q})*
                     $signed({{32{read_key[31]}},read_key});
  assign dim_scaled=128'(HEAD_DIM)<<32;
  assign sqrt_dim=anvil_q1_pkg::isqrt128(dim_scaled);
  assign division_input=state==10 || state==18 ?
    $signed({{32{dot[95]}},dot}) : $signed({{32{weighted[95]}},weighted});
  assign division_denominator=state==10 || state==18 ? sqrt_dim : denominator;
  assign division_magnitude=division_input<0 ?
    -$signed({division_input[127],division_input}) : {1'b0,division_input};
  assign division_numerator=division_magnitude+({65'd0,division_denominator}>>1);
  assign division_result=division_input<0 ?
    -$signed(division_quotient[127:0]) : $signed(division_quotient[127:0]);
  anvil_q1_unsigned_divider #(129) division(
    .clk(clk),.rst_n(rst_n),.start(state==10 || state==20),.ready(div_ready),
    .done(div_done),.error(div_error),.numerator(division_numerator),
    .divisor(division_denominator),.quotient(division_quotient));
  anvil_q1_exp exponential_unit(
    .clk(clk),.rst_n(rst_n),.start(state==22),.ready(exp_ready),
    .done(exp_done),.error(exp_error),.argument(exp_argument),.value(exp_value));
  assign weighted_product=$signed({{33{read_value[31]}},read_value})*
                          $signed({33'd0,exponential});
  assign score_difference=$signed({current_score[95],current_score})-
                          $signed({max_score[95],max_score});
  assign exp_argument=score_difference < -97'sd1048576 ? -64'sd1048577 :
                      (score_difference > 0 ? 64'sd0 : $signed(score_difference[63:0]));
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
      8: begin
        issue=1; kind=9; ml=layer; row=time_index;
        col=kv_head*HEAD_DIM+dim;
      end
      13: begin
        issue=1; kind=10; ml=layer; row=time_index;
        col=kv_head*HEAD_DIM+component;
      end
      16: begin
        issue=1; wr=1; kind=8; row=5; col=head*HEAD_DIM+component;
        wd=context_value;
      end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; failed<=0; value_cache<=0; context_pass<=0;
      layer<=0; position<=0; index<=0; head<=0; time_index<=0; dim<=0;
      component<=0; q<=0; cache_data<=0; dot<=0; max_score<=0;
      current_score<=0; weighted<=0; denominator<=0; exponential<=0;
      kv_head<=0; head_in_group<=0; context_value<=0;
    end else if(fault) begin failed<=1; state<=31; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; layer<=cmd_layer; position<=cmd_pos; index<=0; value_cache<=0;
        head<=0; time_index<=0; dim<=0; component<=0; context_pass<=0;
        kv_head<=0; head_in_group<=0;
        dot<=0; max_score<={1'b1,95'd0}; weighted<=0; denominator<=0;
        if(cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || sqrt_dim==0)
          begin failed<=1; state<=30; end
        else state<=1;
      end
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
        dot<=dot+{{32{dot_product[63]}},dot_product};
        if(dim+1<HEAD_DIM) begin dim<=dim+1; state<=6; end
        else state<=10;
      end
      10: if(div_ready) state<=18;
      18: if(div_done) begin
        if(div_error) begin failed<=1; state<=31; end
        else begin current_score<=division_result[95:0]; state<=11; end
      end
      11: if(!context_pass) begin
        if(current_score>max_score) max_score<=current_score;
        if(time_index<position) begin time_index<=time_index+1; dim<=0; dot<=0; state<=6; end
        else begin context_pass<=1; time_index<=0; dim<=0; dot<=0; state<=6; end
      end else state<=22;
      22: if(exp_ready) state<=23;
      23: if(exp_done) begin
        if(exp_error) begin failed<=1; state<=31; end
        else begin exponential<=exp_value; state<=12; end
      end
      12: begin denominator<=denominator+exponential; state<=13; end
      13: if(issue) state<=14;
      14: if(complete) begin weighted<=weighted+{{31{weighted_product[64]}},weighted_product}; state<=15; end
      15: if(time_index<position) begin
        time_index<=time_index+1; dim<=0; dot<=0; state<=6;
      end else if(denominator==0) begin failed<=1; state<=31; end
      else state<=20;
      20: if(div_ready) state<=21;
      21: if(div_done) begin
        if(div_error) begin failed<=1; state<=31; end
        else begin context_value<=anvil_q1_pkg::sat32(division_result); state<=16; end
      end
      16: if(issue) state<=17;
      17: if(complete) begin
        time_index<=0; dim<=0; dot<=0; weighted<=0; denominator<=0;
        if(component+1<HEAD_DIM) begin component<=component+1; state<=6; end
        else if(head+1<NUM_Q_HEADS) begin
          head<=head+1; component<=0; context_pass<=0;
          if(head_in_group==RATIO-1) begin
            head_in_group<=0; kv_head<=kv_head+1;
          end else head_in_group<=head_in_group+1;
          max_score<={1'b1,95'd0}; state<=6;
        end else state<=31;
      end
      30: state<=31;
      31: state<=0;
      default: state<=0;
    endcase
  end
endmodule
