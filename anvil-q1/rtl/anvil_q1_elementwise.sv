module anvil_q1_elementwise #(
  parameter NUM_LAYERS=24, HIDDEN_SIZE=896, INTERMEDIATE_SIZE=4864,
  MAX_SEQ_LEN=32768
)(
  input wire clk, rst_n, cmd_valid, output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, input wire [1:0] cmd_mode,
  output wire done, error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  reg [3:0] state;
  reg [1:0] mode;
  reg failed;
  reg [31:0] index;
  reg signed [31:0] a,b;
  wire signed [31:0] silu_value;
  wire signed [32:0] sum;
  wire signed [63:0] product;
  wire silu_ready, silu_done, silu_error;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [31:0] row, wd;
  generate if(NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || INTERMEDIATE_SIZE<=0 ||
              MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>16777215 ||
              HIDDEN_SIZE%8!=0 || INTERMEDIATE_SIZE%8!=0 ||
              128'(NUM_LAYERS)>128'd4294967295 ||
              128'(HIDDEN_SIZE)*15>128'd4294967295 ||
              128'(INTERMEDIATE_SIZE)*15>128'd4294967295) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q1 PARAMETER ERROR: elementwise dimensions");
  end endgenerate
  assign sum=$signed({a[31],a})+$signed({b[31],b});
  anvil_q1_silu silu(
    .clk(clk),.rst_n(rst_n),.start(state==7),.ready(silu_ready),
    .done(silu_done),.error(silu_error),.argument(a),.value(silu_value));
  assign product=$signed({{32{silu_value[31]}},silu_value})*
                 $signed({{32{b[31]}},b});
  assign cmd_ready=rst_n && state==0;
  assign done=rst_n && state==15;
  assign error=done && failed;
  anvil_q1_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(wr),.kind(4'd8),.layer(32'd0),
    .proj(3'd0),.row(row),.col(index),.wdata(wd),
    .idle(idle),.complete(complete),.rdata(rd),.fault(fault),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
  always @* begin
    issue=0; wr=0; row=0; wd=0;
    if(rst_n && idle) case(state)
      1: begin issue=1; row=mode==0 ? 0 : (mode==1 ? 7 : 9); end
      3: begin issue=1; row=mode==0 ? 6 : (mode==1 ? 12 : 10); end
      5: begin
        issue=1; wr=1; row=mode==0 ? 7 : (mode==1 ? 0 : 11);
        if(mode==2)
          wd=anvil_q1_pkg::sat32(anvil_q1_pkg::round_shift({{64{product[63]}},product},16));
        else wd=anvil_q1_pkg::sat32({{95{sum[32]}},sum});
      end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if(!rst_n) begin state<=0; failed<=0; mode<=0; index<=0; a<=0; b<=0; end
    else if(fault) begin failed<=1; state<=15; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; mode<=cmd_mode; index<=0;
        if(cmd_mode>2 || cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN)
          begin failed<=1; state<=14; end
        else state<=1;
      end
      1: if(issue) state<=2;
      2: if(complete) begin a<=rd; state<=3; end
      3: if(issue) state<=4;
      4: if(complete) begin
        b<=rd;
        if(mode==2) state<=7;
        else state<=5;
      end
      7: if(silu_ready) state<=8;
      8: if(silu_done) begin
        if(silu_error) begin failed<=1; state<=15; end
        else state<=5;
      end
      5: if(issue) state<=6;
      6: if(complete) begin
        if(index+1<(mode==2 ? INTERMEDIATE_SIZE : HIDDEN_SIZE))
          begin index<=index+1; state<=1; end
        else state<=15;
      end
      14: state<=15;
      15: state<=0;
      default: state<=0;
    endcase
  end
endmodule
