module anvil_q1_fp_rmsnorm #(
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
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error,
  input wire [1:0] cmd_precision
);
  localparam SAFE_H=HIDDEN_SIZE>0 ? HIDDEN_SIZE : 1;
  localparam [36:0] H_PACKED=anvil_q1_fp_pkg::pack_grid(
    69'(SAFE_H),1'b0,11'sd0,1'b0);
  reg [5:0] state;
  reg failed;
  reg [1:0] precision;
  reg [31:0] layer, index, src, dst;
  reg [3:0] norm_kind;
  reg [95:0] sum;
  reg [63:0] reciprocal, denominator;
  reg [127:0] mean;
  reg signed [31:0] x, gamma;
  reg signed [63:0] square, norm_product;
  reg signed [127:0] compat_result;
  reg [31:0] fp_sum, temporary, inverse_h, inverse_rms, output_value;
  wire idle, complete, fault;
  wire [31:0] rd, native_gamma;
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  wire div_ready, div_valid, div_zero, sqrt_ready, sqrt_valid;
  wire [127:0] quotient;
  wire [63:0] remainder, sqrt_result;
  wire mul_valid, add_valid, recip_valid, rsqrt_valid;
  wire [31:0] mul_result, add_result, recip_result, rsqrt_result;
  wire [4:0] mul_status, add_status, recip_status, rsqrt_status;
  reg [31:0] mul_a, mul_b, add_a, add_b;
  wire native_fault;
  generate if(NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || HIDDEN_SIZE%8!=0 ||
              MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>16777215 ||
              128'(HIDDEN_SIZE)*15>128'd4294967295 ||
              128'(NUM_LAYERS)>128'd4294967295) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q1 PARAMETER ERROR: RMSNorm dimensions");
  end endgenerate
  assign native_gamma=anvil_q1_fp_pkg::widen16(rd[15:0],precision);
  anvil_q1_fp_compat_div divider(
    clk,rst_n,state==3 || state==5,div_ready,
    state==3 ? ({32'd0,sum}<<32) : 128'd18446744073709551616,
    state==3 ? 64'(SAFE_H) : denominator,
    div_valid,quotient,remainder,div_zero);
  anvil_q1_fp_compat_sqrt square_root(
    clk,rst_n,state==4,sqrt_ready,mean,sqrt_valid,sqrt_result);
  anvil_q1_fp_mul multiply_pipeline(
    clk,rst_n,state==20 || state==28 || state==36 || state==38,
    mul_a,mul_b,mul_valid,mul_result,mul_status);
  anvil_q1_fp_add add_pipeline(clk,rst_n,state==22 || state==30,
    add_a,add_b,add_valid,add_result,add_status);
  anvil_q1_fp_reciprocal reciprocal_pipeline(clk,rst_n,state==26,
    H_PACKED[31:0],recip_valid,recip_result,recip_status);
  anvil_q1_fp_rsqrt rsqrt_pipeline(clk,rst_n,state==32,temporary,
    rsqrt_valid,rsqrt_result,rsqrt_status);
  assign native_fault=
    ((state==21 || state==29 || state==37 || state==39) && mul_valid && |mul_status[4:2]) ||
    ((state==23 || state==31) && add_valid && |add_status[4:2]) ||
    (state==27 && recip_valid && |recip_status[4:2]) ||
    (state==33 && rsqrt_valid && |rsqrt_status[4:2]);
  always @* begin
    mul_a=x; mul_b=x; add_a=fp_sum; add_b=temporary;
    if(state==28) begin mul_a=fp_sum; mul_b=inverse_h; end
    if(state==30) begin add_a=temporary; add_b=32'h358637bd; end
    if(state==36) begin mul_a=x; mul_b=gamma; end
    if(state==38) begin mul_a=temporary; mul_b=inverse_rms; end
  end
  assign cmd_ready=rst_n && state==0;
  assign done=rst_n && state==15;
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
      1,6: begin issue=1; kind=8; row=src; col=index; end
      8: begin issue=1; kind=norm_kind; ml=norm_kind==7 ? 0 : layer; col=index; end
      10: begin issue=1; wr=1; kind=8; row=dst; col=index; wd=output_value; end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; failed<=0; precision<=0; layer<=0; index<=0; src<=0; dst<=0;
      norm_kind<=0; sum<=0; reciprocal<=0; mean<=0; denominator<=0; x<=0; gamma<=0;
      square<=0; norm_product<=0; compat_result<=0; fp_sum<=0; temporary<=0;
      inverse_h<=0; inverse_rms<=0; output_value<=0;
    end else if(fault || native_fault) begin failed<=1; state<=15; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; layer<=cmd_layer; precision<=cmd_precision;
        index<=0; sum<=0; fp_sum<=0;
        if(cmd_mode>2 || cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_precision==3)
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
        if(precision!=0 && rd[30:23]==255) begin failed<=1; state<=15; end
        else begin
          x<=rd;
          if(precision==0) state<=16; else state<=20;
        end
      end
      16: begin square<=$signed(x)*$signed(x); state<=17; end
      17: begin sum<=sum+{32'd0,square}; state<=18; end
      18: if(index+1<HIDDEN_SIZE) begin index<=index+1; state<=1; end else state<=3;
      3: if(div_ready) state<=40;
      40: if(div_valid) begin
        if(div_zero) begin failed<=1; state<=15; end
        else begin mean<=quotient+128'd18446744073710; state<=4; end
      end
      4: if(sqrt_ready) state<=41;
      41: if(sqrt_valid) begin denominator<=sqrt_result; state<=5; end
      5: if(div_ready) state<=42;
      42: if(div_valid) begin
        if(div_zero) begin failed<=1; state<=15; end
        else begin reciprocal<=quotient[63:0]; index<=0; state<=6; end
      end
      20: state<=21;
      21: if(mul_valid) begin temporary<=mul_result; state<=22; end
      22: state<=23;
      23: if(add_valid) begin fp_sum<=add_result; state<=24; end
      24: if(index+1<HIDDEN_SIZE) begin index<=index+1; state<=1; end else state<=26;
      26: state<=27;
      27: if(recip_valid) begin inverse_h<=recip_result; state<=28; end
      28: state<=29;
      29: if(mul_valid) begin temporary<=mul_result; state<=30; end
      30: state<=31;
      31: if(add_valid) begin temporary<=add_result; state<=32; end
      32: state<=33;
      33: if(rsqrt_valid) begin inverse_rms<=rsqrt_result; index<=0; state<=6; end
      6: if(issue) state<=7;
      7: if(complete) begin
        if(precision!=0 && rd[30:23]==255) begin failed<=1; state<=15; end
        else begin x<=rd; state<=8; end
      end
      8: if(issue) state<=9;
      9: if(complete) begin
        if(precision==0) begin
          if(anvil_q1_fp_compat_pkg::f16_invalid(rd[15:0])) begin failed<=1; state<=15; end
          else begin gamma<=anvil_q1_fp_compat_pkg::f16_q16(rd[15:0]); state<=43; end
        end else if(rd[31:16]!=0 || native_gamma[30:23]==255)
          begin failed<=1; state<=15; end
        else begin gamma<=native_gamma; state<=36; end
      end
      43: begin norm_product<=$signed(x)*$signed(gamma); state<=44; end
      44: begin compat_result<=$signed(norm_product)*$signed({1'b0,reciprocal}); state<=45; end
      45: begin
        output_value<=anvil_q1_fp_compat_pkg::sat32(
          anvil_q1_fp_compat_pkg::round_shift(compat_result,48)); state<=10;
      end
      36: state<=37;
      37: if(mul_valid) begin temporary<=mul_result; state<=38; end
      38: state<=39;
      39: if(mul_valid) begin output_value<=mul_result; state<=10; end
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
