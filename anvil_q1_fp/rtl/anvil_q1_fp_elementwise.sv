module anvil_q1_fp_elementwise #(
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
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error,
  input wire [1:0] cmd_precision
);
  reg [5:0] state;
  reg [1:0] mode, precision;
  reg failed;
  reg [31:0] index, a, b, value, temporary, exponential;
  reg signed [63:0] compat_product;
  wire signed [32:0] compat_sum;
  wire idle, complete, fault;
  wire [31:0] rd;
  reg issue, wr;
  reg [31:0] row, wd;
  wire add_valid, mul_valid, exp_valid, recip_valid, silu_valid, silu_ready;
  wire [31:0] add_result, mul_result, exp_result, recip_result;
  wire signed [31:0] silu_result;
  wire [4:0] add_status, mul_status, exp_status, recip_status;
  wire native_fault;
  reg [31:0] add_a, add_b, mul_a, mul_b;
  generate if(NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || INTERMEDIATE_SIZE<=0 ||
              MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>16777215 ||
              HIDDEN_SIZE%8!=0 || INTERMEDIATE_SIZE%8!=0 ||
              128'(NUM_LAYERS)>128'd4294967295 ||
              128'(HIDDEN_SIZE)*15>128'd4294967295 ||
              128'(INTERMEDIATE_SIZE)*15>128'd4294967295) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q1 PARAMETER ERROR: elementwise dimensions");
  end endgenerate
  assign compat_sum=$signed({a[31],a})+$signed({b[31],b});
  anvil_q1_fp_add add_pipeline(clk,rst_n,state==16 || state==20,
    add_a,add_b,add_valid,add_result,add_status);
  anvil_q1_fp_mul mul_pipeline(clk,rst_n,state==24 || state==26 || state==28,
    mul_a,mul_b,mul_valid,mul_result,mul_status);
  anvil_q1_fp_exp exp_pipeline(clk,rst_n,state==18,{1'b1,a[30:0]},
    exp_valid,exp_result,exp_status);
  anvil_q1_fp_reciprocal reciprocal_pipeline(clk,rst_n,state==22,temporary,
    recip_valid,recip_result,recip_status);
  anvil_q1_fp_compat_silu compat_silu(clk,rst_n,state==8,silu_ready,a,
    silu_valid,silu_result);
  assign native_fault=
    ((state==17 || state==21) && add_valid && |add_status[4:2]) ||
    (state==19 && exp_valid && |exp_status[4:2]) ||
    (state==23 && recip_valid && |recip_status[4:2]) ||
    ((state==25 || state==27 || state==29) && mul_valid && |mul_status[4:2]);
  always @* begin
    add_a=a; add_b=b;
    if(state==20) begin add_a=32'h3f800000; add_b=exponential; end
    mul_a=temporary; mul_b=exponential;
    if(state==26) begin mul_a=a; mul_b=temporary; end
    if(state==28) begin mul_a=temporary; mul_b=b; end
  end
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
      5: begin issue=1; wr=1; row=mode==0 ? 7 : (mode==1 ? 0 : 11); wd=value; end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; failed<=0; mode<=0; precision<=0; index<=0; a<=0; b<=0;
      value<=0; temporary<=0; exponential<=0; compat_product<=0;
    end else if(fault || native_fault) begin failed<=1; state<=15; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; mode<=cmd_mode; precision<=cmd_precision; index<=0;
        if(cmd_mode>2 || cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_precision==3)
          begin failed<=1; state<=14; end
        else state<=1;
      end
      1: if(issue) state<=2;
      2: if(complete) begin
        if(precision!=0 && rd[30:23]==255) begin failed<=1; state<=15; end
        else begin a<=rd; state<=3; end
      end
      3: if(issue) state<=4;
      4: if(complete) begin
        if(precision!=0 && rd[30:23]==255) begin failed<=1; state<=15; end
        else begin
          b<=rd;
          if(precision==0) begin
            if(mode==2) state<=8; else state<=7;
          end else if(mode==2) state<=18;
          else state<=16;
        end
      end
      7: begin value<=anvil_q1_fp_compat_pkg::sat32({{95{compat_sum[32]}},compat_sum}); state<=5; end
      8: if(silu_ready) state<=9;
      9: if(silu_valid) begin temporary<=silu_result; state<=10; end
      10: begin compat_product<=$signed(temporary)*$signed(b); state<=11; end
      11: begin
        value<=anvil_q1_fp_compat_pkg::sat32(
          anvil_q1_fp_compat_pkg::round_shift({{64{compat_product[63]}},compat_product},16));
        state<=5;
      end
      16: state<=17;
      17: if(add_valid) begin value<=add_result; state<=5; end
      18: state<=19;
      19: if(exp_valid) begin exponential<=exp_result; state<=20; end
      20: state<=21;
      21: if(add_valid) begin temporary<=add_result; state<=22; end
      22: state<=23;
      23: if(recip_valid) begin
        temporary<=recip_result;
        if(a[31]) state<=24; else state<=26;
      end
      24: state<=25;
      25: if(mul_valid) begin temporary<=mul_result; state<=26; end
      26: state<=27;
      27: if(mul_valid) begin temporary<=mul_result; state<=28; end
      28: state<=29;
      29: if(mul_valid) begin value<=mul_result; state<=5; end
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
