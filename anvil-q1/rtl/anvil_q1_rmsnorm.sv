module anvil_q1_rmsnorm #(
  parameter NUM_LAYERS=24, HIDDEN_SIZE=896, MAX_SEQ_LEN=32768
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
  import anvil_q1_pkg::*;
  localparam SAFE_H = HIDDEN_SIZE > 0 ? HIDDEN_SIZE : 1;
  reg [3:0] state;
  reg failed;
  reg [31:0] layer, index, src, dst;
  reg [3:0] norm_kind;
  reg [63:0] sum, reciprocal;
  reg [95:0] mean;
  reg [47:0] denominator;
  reg signed [15:0] x, gamma;
  wire signed [15:0] read_x;
  wire signed [31:0] square;
  wire signed [95:0] result;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  generate if(NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || HIDDEN_SIZE%8!=0 ||
              MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>16777215 ||
              128'(HIDDEN_SIZE)>128'd4294967295 ||
              128'(NUM_LAYERS)>128'd4294967295) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q1 PARAMETER ERROR: RMSNorm dimensions");
  end endgenerate
  assign read_x = rd[15:0];
  assign square = $signed(read_x) * $signed(read_x);
  assign result = $signed(x) * $signed(gamma) * $signed({1'b0,reciprocal});
  assign cmd_ready = rst_n && state==0;
  assign done = rst_n && state==15;
  assign error = done && failed;
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
      1,6: begin issue=1; kind=8; row=src; col=index; end
      8: begin issue=1; kind=norm_kind; ml=norm_kind==7 ? 0 : layer; col=index; end
      10: begin
        issue=1; wr=1; kind=8; row=dst; col=index;
        wd={16'd0,sat16(round_shift(result,24))};
      end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; failed<=0; layer<=0; index<=0; src<=0; dst<=0;
      norm_kind<=0; sum<=0; reciprocal<=0; mean<=0; denominator<=0; x<=0; gamma<=0;
    end else if(fault) begin failed<=1; state<=15; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; layer<=cmd_layer; index<=0; sum<=0;
        if(cmd_mode>2 || cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN)
          begin failed<=1; state<=14; end
        else begin
          src<=cmd_mode==1 ? 7 : 0;
          dst<=cmd_mode==0 ? 1 : (cmd_mode==1 ? 8 : 14);
          norm_kind<=cmd_mode==0 ? 5 : (cmd_mode==1 ? 6 : 7);
          state<=1;
        end
      end
      1: if(issue) state<=2;
      2: if(complete) begin
        sum<=sum+{32'd0,square};
        if(index+1<HIDDEN_SIZE) begin index<=index+1; state<=1; end
        else state<=3;
      end
      3: begin mean<=(({32'd0,sum}<<16)/SAFE_H)+96'd4295; state<=4; end
      4: begin denominator<=isqrt96(mean); state<=5; end
      5: if(denominator==0) begin failed<=1; state<=15; end
         else begin reciprocal<=64'd4294967296/denominator; index<=0; state<=6; end
      6: if(issue) state<=7;
      7: if(complete) begin x<=rd[15:0]; state<=8; end
      8: if(issue) state<=9;
      9: if(complete) begin
        if(f16_invalid(rd[15:0])) begin failed<=1; state<=15; end
        else begin gamma<=f16_q8(rd[15:0]); state<=10; end
      end
      10: if(issue) state<=11;
      11: if(complete) begin
        if(index+1<HIDDEN_SIZE) begin index<=index+1; state<=6; end
        else state<=15;
      end
      14: state<=15;
      15: state<=0;
      default: state<=0;
    endcase
  end
endmodule
