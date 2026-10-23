module anvil_q2_rmsnorm #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, MAX_SEQ_LEN=32768
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
  localparam SAFE_H = HIDDEN_SIZE > 0 ? HIDDEN_SIZE : 1;
  reg [4:0] state;
  reg failed;
  reg [31:0] layer, index, src, dst;
  reg [3:0] norm_kind;
  reg [95:0] sum;
  reg [63:0] reciprocal, denominator;
  reg [127:0] mean;
  reg [64:0] sqrt_remainder;
  reg [6:0] sqrt_remaining;
  reg [15:0] gamma_raw;
  reg signed [31:0] x, gamma;
  reg signed [63:0] scaled_x;
  reg signed [127:0] result;
  wire signed [63:0] square, norm_product;
  wire [66:0] sqrt_candidate = {sqrt_remainder,mean[127:126]};
  wire [66:0] sqrt_trial = {1'b0,denominator,2'b01};
  wire sqrt_subtract = sqrt_candidate >= sqrt_trial;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  wire divide_ready, divide_done, divide_error;
  wire [128:0] divide_quotient;
  wire divide_start=rst_n && (state==3 || (state==5 && denominator!=0));
  anvil_q2_divider divider(
    .clk(clk),.rst_n(rst_n),.start(divide_start),
    .numerator(state==3 ? ({33'd0,sum} << 32) : (129'd1 << 64)),
    .denominator(state==3 ? 64'(SAFE_H) : denominator),
    .ready(divide_ready),.done(divide_done),.error(divide_error),
    .quotient(divide_quotient));
  generate if(NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || HIDDEN_SIZE%8!=0 ||
              MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>16777215 ||
              128'(HIDDEN_SIZE)*15>128'd4294967295 ||
              128'(NUM_LAYERS)>128'd4294967295) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2 PARAMETER ERROR: RMSNorm dimensions");
  end endgenerate
  assign square = $signed({{32{x[31]}},x}) *
                  $signed({{32{x[31]}},x});
  assign norm_product = $signed({{32{x[31]}},x}) *
                        $signed({{32{gamma[31]}},gamma});
  assign cmd_ready = rst_n && state==0;
  assign done = rst_n && state==15;
  assign error = done && failed;
  anvil_q2_mem_port memory_port(
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
        wd=anvil_q2_pkg::sat32(anvil_q2_pkg::round_shift(result,48));
      end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=0; failed<=0; layer<=0; index<=0; src<=0; dst<=0;
      norm_kind<=0; sum<=0; reciprocal<=0; mean<=0; denominator<=0; x<=0; gamma<=0;
      gamma_raw<=0; sqrt_remainder<=0; sqrt_remaining<=0; scaled_x<=0; result<=0;
    end else if(fault || (divide_done && divide_error)) begin failed<=1; state<=15; end
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
        x<=rd; state<=19;
      end
      19: begin
        sum<=sum+{32'd0,square};
        if(index+1<HIDDEN_SIZE) begin index<=index+1; state<=1; end
        else state<=3;
      end
      3: if(divide_ready) state<=12;
      12: if(divide_done) begin
        mean<=divide_quotient[127:0]+128'd18446744073710; state<=4;
      end
      4: begin
        denominator<=0; sqrt_remainder<=0; sqrt_remaining<=64; state<=16;
      end
      16: begin
        mean<={mean[125:0],2'b00};
        sqrt_remainder<=sqrt_subtract ?
          65'(sqrt_candidate-sqrt_trial) : sqrt_candidate[64:0];
        denominator<={denominator[62:0],sqrt_subtract};
        sqrt_remaining<=sqrt_remaining-1'b1;
        if(sqrt_remaining==1) state<=5;
      end
      5: if(denominator==0) begin failed<=1; state<=15; end
         else if(divide_ready) state<=13;
      13: if(divide_done) begin reciprocal<=divide_quotient[63:0]; index<=0; state<=6; end
      6: if(issue) state<=7;
      7: if(complete) begin x<=rd; state<=8; end
      8: if(issue) state<=9;
      9: if(complete) begin
        gamma_raw<=rd[15:0]; state<=20;
      end
      20: if(anvil_q2_pkg::f16_invalid(gamma_raw)) begin failed<=1; state<=15; end
      else begin gamma<=anvil_q2_pkg::f16_q16(gamma_raw); state<=17; end
      17: begin scaled_x<=norm_product; state<=18; end
      18: begin
        result<=$signed({{64{scaled_x[63]}},scaled_x}) *
                $signed({64'd0,reciprocal});
        state<=10;
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
