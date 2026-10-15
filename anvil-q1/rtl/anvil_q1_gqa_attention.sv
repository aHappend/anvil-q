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
  import anvil_q1_pkg::*;
  localparam RATIO = NUM_KV_HEADS>0 && NUM_Q_HEADS>=NUM_KV_HEADS ?
                      NUM_Q_HEADS/NUM_KV_HEADS : 1;
  localparam KV_SIZE = NUM_KV_HEADS*HEAD_DIM;
  reg [4:0] state;
  reg failed, value_cache, context_pass;
  reg [31:0] layer, position, index, head, time_index, dim, component;
  reg signed [15:0] q, cache_data;
  reg signed [63:0] dot, max_score, current_score, weighted;
  reg [63:0] denominator;
  reg [31:0] exponential;
  wire signed [15:0] read_value;
  wire signed [31:0] dot_product;
  wire signed [95:0] scaled_score, weighted_product;
  wire [47:0] sqrt_dim;
  wire [95:0] dim_scaled;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  anvil_q1_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,HIDDEN_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,1,4,1,MAX_SEQ_LEN) parameters_ok();
  assign read_value=rd[15:0];
  assign dot_product=$signed(q)*$signed(read_value);
  assign dim_scaled=96'(HEAD_DIM)<<32;
  assign sqrt_dim=isqrt96(dim_scaled);
  assign scaled_score=round_div(
    $signed({{32{dot[63]}},dot}) <<< 16,{16'd0,sqrt_dim});
  assign weighted_product=$signed(read_value)*$signed({1'b0,exponential});
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
        row=position; col=index; wd={16'd0,cache_data};
      end
      6: begin issue=1; kind=8; row=2; col=head*HEAD_DIM+dim; end
      8: begin
        issue=1; kind=9; ml=layer; row=time_index;
        col=(head/RATIO)*HEAD_DIM+dim;
      end
      13: begin
        issue=1; kind=10; ml=layer; row=time_index;
        col=(head/RATIO)*HEAD_DIM+component;
      end
      16: begin
        issue=1; wr=1; kind=8; row=5; col=head*HEAD_DIM+component;
        wd={16'd0,sat16(round_div($signed({{32{weighted[63]}},weighted}),denominator))};
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
    end else if(fault) begin failed<=1; state<=31; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; layer<=cmd_layer; position<=cmd_pos; index<=0; value_cache<=0;
        head<=0; time_index<=0; dim<=0; component<=0; context_pass<=0;
        dot<=0; max_score<=64'sh8000000000000000; weighted<=0; denominator<=0;
        if(cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || sqrt_dim==0)
          begin failed<=1; state<=30; end
        else state<=1;
      end
      1: if(issue) state<=2;
      2: if(complete) begin cache_data<=rd[15:0]; state<=3; end
      3: if(issue) state<=4;
      4: if(complete) begin
        if(index+1<KV_SIZE) begin index<=index+1; state<=1; end
        else if(!value_cache) begin value_cache<=1; index<=0; state<=1; end
        else state<=6;
      end
      6: if(issue) state<=7;
      7: if(complete) begin q<=rd[15:0]; state<=8; end
      8: if(issue) state<=9;
      9: if(complete) begin
        dot<=dot+{{32{dot_product[31]}},dot_product};
        if(dim+1<HEAD_DIM) begin dim<=dim+1; state<=6; end
        else state<=10;
      end
      10: begin current_score<=scaled_score[63:0]; state<=11; end
      11: if(!context_pass) begin
        if(current_score>max_score) max_score<=current_score;
        if(time_index<position) begin time_index<=time_index+1; dim<=0; dot<=0; state<=6; end
        else begin context_pass<=1; time_index<=0; dim<=0; dot<=0; state<=6; end
      end else begin exponential<=exp_q24(current_score-max_score); state<=12; end
      12: begin denominator<=denominator+exponential; state<=13; end
      13: if(issue) state<=14;
      14: if(complete) begin weighted<=weighted+weighted_product[63:0]; state<=15; end
      15: if(time_index<position) begin
        time_index<=time_index+1; dim<=0; dot<=0; state<=6;
      end else if(denominator==0) begin failed<=1; state<=31; end
      else state<=16;
      16: if(issue) state<=17;
      17: if(complete) begin
        time_index<=0; dim<=0; dot<=0; weighted<=0; denominator<=0;
        if(component+1<HEAD_DIM) begin component<=component+1; state<=6; end
        else if(head+1<NUM_Q_HEADS) begin
          head<=head+1; component<=0; context_pass<=0;
          max_score<=64'sh8000000000000000; state<=6;
        end else state<=31;
      end
      30: state<=31;
      31: state<=0;
      default: state<=0;
    endcase
  end
endmodule
