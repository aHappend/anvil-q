module anvil_q2_rope #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, NUM_Q_HEADS=12,
  NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768
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
  reg [3:0] state;
  reg failed, key_vector;
  reg [31:0] position, head, pair_index;
  reg signed [31:0] x, y;
  reg signed [31:0] cosine, sine;
  wire signed [63:0] x_cos, y_sin, y_cos, x_sin;
  wire signed [64:0] rotated_x, rotated_y;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd;
  anvil_q2_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,HIDDEN_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,1,4,1,MAX_SEQ_LEN) parameters_ok();
  assign x_cos = $signed({{32{x[31]}},x})*$signed({{32{cosine[31]}},cosine});
  assign y_sin = $signed({{32{y[31]}},y})*$signed({{32{sine[31]}},sine});
  assign y_cos = $signed({{32{y[31]}},y})*$signed({{32{cosine[31]}},cosine});
  assign x_sin = $signed({{32{x[31]}},x})*$signed({{32{sine[31]}},sine});
  assign rotated_x = $signed({x_cos[63],x_cos})-$signed({y_sin[63],y_sin});
  assign rotated_y = $signed({y_cos[63],y_cos})+$signed({x_sin[63],x_sin});
  assign cmd_ready = rst_n && state==0;
  assign done = rst_n && state==15;
  assign error = done && failed;
  anvil_q2_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(wr),.kind(kind),.layer(32'd0),
    .proj(3'd0),.row(row),.col(col),.wdata(wd),
    .idle(idle),.complete(complete),.rdata(rd),.fault(fault),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
  always @* begin
    issue=0; wr=0; kind=0; row=0; col=0; wd=0;
    if(rst_n && idle) case(state)
      1,3,9,11: begin
        issue=1; kind=8; row=key_vector ? 3 : 2;
        col=head*HEAD_DIM+pair_index+((state==3 || state==11) ? HEAD_DIM/2 : 0);
        wr=state==9 || state==11;
        if(state==9) wd=anvil_q2_pkg::sat32(anvil_q2_pkg::round_shift({{63{rotated_x[64]}},rotated_x},30));
        if(state==11) wd=anvil_q2_pkg::sat32(anvil_q2_pkg::round_shift({{63{rotated_y[64]}},rotated_y},30));
      end
      5,7: begin issue=1; kind=11; row=position; col=2*pair_index+(state==7); end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=0; failed<=0; key_vector<=0; position<=0; head<=0;
      pair_index<=0; x<=0; y<=0; cosine<=0; sine<=0;
    end else if(fault) begin failed<=1; state<=15; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; position<=cmd_pos; head<=0; pair_index<=0; key_vector<=0;
        if(cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN)
          begin failed<=1; state<=14; end
        else state<=1;
      end
      1: if(issue) state<=2;
      2: if(complete) begin x<=rd; state<=3; end
      3: if(issue) state<=4;
      4: if(complete) begin y<=rd; state<=5; end
      5: if(issue) state<=6;
      6: if(complete) begin cosine<=rd; state<=7; end
      7: if(issue) state<=8;
      8: if(complete) begin sine<=rd; state<=9; end
      9: if(issue) state<=10;
      10: if(complete) state<=11;
      11: if(issue) state<=12;
      12: if(complete) begin
        if(pair_index+1<HEAD_DIM/2) begin pair_index<=pair_index+1; state<=1; end
        else if(head+1<(key_vector ? NUM_KV_HEADS : NUM_Q_HEADS)) begin
          pair_index<=0; head<=head+1; state<=1;
        end else if(!key_vector) begin key_vector<=1; head<=0; pair_index<=0; state<=1; end
        else state<=15;
      end
      14: state<=15;
      15: state<=0;
      default: state<=0;
    endcase
  end
endmodule
