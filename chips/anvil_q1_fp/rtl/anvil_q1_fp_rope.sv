module anvil_q1_fp_rope #(
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
  reg [4:0] state;
  reg failed, key_vector;
  reg [1:0] precision;
  reg [31:0] position, head, pair_index, x, y, cosine, sine, result_x, result_y;
  reg signed [63:0] compat_products [0:3];
  wire signed [64:0] rotated_x, rotated_y;
  wire [3:0] mul_valid;
  wire [31:0] mul_result [0:3];
  wire [4:0] mul_status [0:3];
  reg [31:0] fp_products [0:3];
  wire [1:0] add_valid;
  wire [31:0] add_result [0:1];
  wire [4:0] add_status [0:1];
  wire native_fault;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd;
  integer i;
  anvil_q1_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,HIDDEN_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,1,4,1,MAX_SEQ_LEN) parameters_ok();
  anvil_q1_fp_mul x_cos(clk,rst_n,state==18,x,cosine,mul_valid[0],mul_result[0],mul_status[0]);
  anvil_q1_fp_mul y_sin(clk,rst_n,state==18,y,sine,mul_valid[1],mul_result[1],mul_status[1]);
  anvil_q1_fp_mul y_cos(clk,rst_n,state==18,y,cosine,mul_valid[2],mul_result[2],mul_status[2]);
  anvil_q1_fp_mul x_sin(clk,rst_n,state==18,x,sine,mul_valid[3],mul_result[3],mul_status[3]);
  anvil_q1_fp_add subtract_pipeline(clk,rst_n,state==20,
    fp_products[0],{!fp_products[1][31],fp_products[1][30:0]},
    add_valid[0],add_result[0],add_status[0]);
  anvil_q1_fp_add add_pipeline(clk,rst_n,state==20,fp_products[2],fp_products[3],
    add_valid[1],add_result[1],add_status[1]);
  assign native_fault=(state==19 && &mul_valid &&
    (|mul_status[0][4:2] || |mul_status[1][4:2] || |mul_status[2][4:2] || |mul_status[3][4:2])) ||
    (state==21 && &add_valid && (|add_status[0][4:2] || |add_status[1][4:2]));
  assign rotated_x=$signed({compat_products[0][63],compat_products[0]})-
                   $signed({compat_products[1][63],compat_products[1]});
  assign rotated_y=$signed({compat_products[2][63],compat_products[2]})+
                   $signed({compat_products[3][63],compat_products[3]});
  assign cmd_ready=rst_n && state==0;
  assign done=rst_n && state==15;
  assign error=done && failed;
  anvil_q1_mem_port memory_port(
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
        if(state==9) wd=result_x;
        if(state==11) wd=result_y;
      end
      5,7: begin issue=1; kind=11; row=position; col=2*pair_index+(state==7); end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; failed<=0; key_vector<=0; precision<=0; position<=0; head<=0;
      pair_index<=0; x<=0; y<=0; cosine<=0; sine<=0; result_x<=0; result_y<=0;
      for(i=0;i<4;i=i+1) begin compat_products[i]<=0; fp_products[i]<=0; end
    end else if(fault || native_fault) begin failed<=1; state<=15; end
    else if(complete && precision!=0 && rd[30:23]==255 &&
      (state==2 || state==4 || state==6 || state==8)) begin failed<=1; state<=15; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; precision<=cmd_precision; position<=cmd_pos;
        head<=0; pair_index<=0; key_vector<=0;
        if(cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_precision==3)
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
      8: if(complete) begin sine<=rd; if(precision==0) state<=16; else state<=18; end
      16: begin
        compat_products[0]<=$signed(x)*$signed(cosine);
        compat_products[1]<=$signed(y)*$signed(sine);
        compat_products[2]<=$signed(y)*$signed(cosine);
        compat_products[3]<=$signed(x)*$signed(sine);
        state<=17;
      end
      17: begin
        result_x<=anvil_q1_fp_compat_pkg::sat32(
          anvil_q1_fp_compat_pkg::round_shift({{63{rotated_x[64]}},rotated_x},30));
        result_y<=anvil_q1_fp_compat_pkg::sat32(
          anvil_q1_fp_compat_pkg::round_shift({{63{rotated_y[64]}},rotated_y},30));
        state<=9;
      end
      18: state<=19;
      19: if(&mul_valid) begin
        for(i=0;i<4;i=i+1) fp_products[i]<=mul_result[i];
        state<=20;
      end
      20: state<=21;
      21: if(&add_valid) begin result_x<=add_result[0]; result_y<=add_result[1]; state<=9; end
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
