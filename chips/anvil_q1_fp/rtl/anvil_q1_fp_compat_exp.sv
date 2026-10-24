module anvil_q1_fp_compat_exp(
  input wire clk, rst_n, in_valid,
  output wire in_ready,
  input wire signed [63:0] x,
  output wire out_valid,
  output wire [31:0] result
);
  reg [2:0] state;
  reg [2:0] iteration;
  reg [63:0] magnitude, residual, shifts;
  reg signed [63:0] term, total;
  reg signed [127:0] product;
  reg [31:0] result_reg;
  wire div_ready, div_valid, div_zero;
  wire [127:0] quotient;
  wire [63:0] remainder;
  wire [127:0] numerator;
  wire [63:0] divisor;
  wire signed [63:0] next_term;
  assign numerator=state==1 ? {64'd0,magnitude} :
    (product<0 ? -product : product);
  assign divisor=state==1 ? 64'd11629080 : (64'd16777216*iteration);
  assign next_term=product<0 ? -$signed(quotient[63:0]) : $signed(quotient[63:0]);
  anvil_q1_fp_compat_div divider(
    .clk(clk),.rst_n(rst_n),.in_valid(state==1 || state==4),
    .in_ready(div_ready),.numerator(numerator),.denominator(divisor),
    .out_valid(div_valid),.quotient(quotient),.remainder(remainder),
    .divide_by_zero(div_zero));
  assign in_ready=rst_n && state==0;
  assign out_valid=rst_n && state==7;
  assign result=out_valid ? result_reg : 0;
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; iteration<=0; magnitude<=0; residual<=0; shifts<=0;
      term<=0; total<=0; product<=0; result_reg<=0;
    end else case(state)
      0: if(in_valid) begin
        if(x< -64'sd1048576) begin result_reg<=0; state<=7; end
        else if(x>=0) begin result_reg<=16777216; state<=7; end
        else begin magnitude<=(-x)<<8; state<=1; end
      end
      1: if(div_ready) state<=2;
      2: if(div_valid) begin
        shifts<=quotient[63:0]; residual<=remainder;
        term<=16777216; total<=16777216; iteration<=1; state<=3;
      end
      3: begin product<=-$signed(term)*$signed({1'b0,residual}); state<=4; end
      4: if(div_ready) state<=5;
      5: if(div_valid) begin
        term<=next_term; total<=total+next_term;
        if(iteration==6) state<=6;
        else begin iteration<=iteration+1; state<=3; end
      end
      6: begin result_reg<=total<0 ? 0 : (total>>shifts); state<=7; end
      7: state<=0;
      default: state<=0;
    endcase
  end
endmodule

module anvil_q1_fp_compat_silu(
  input wire clk, rst_n, in_valid,
  output wire in_ready,
  input wire signed [31:0] x,
  output wire out_valid,
  output wire signed [31:0] result
);
  reg [3:0] state;
  reg signed [31:0] value, result_reg;
  reg [31:0] exponential;
  reg [63:0] sigmoid;
  reg signed [96:0] product;
  wire exp_ready, exp_valid, div_ready, div_valid, div_zero;
  wire [31:0] exp_result;
  wire [127:0] quotient;
  wire [63:0] remainder;
  wire signed [63:0] magnitude;
  assign magnitude=value<0 ? -$signed({{32{value[31]}},value}) : {32'd0,value};
  anvil_q1_fp_compat_exp exp_kernel(
    .clk(clk),.rst_n(rst_n),.in_valid(state==1),.in_ready(exp_ready),
    .x(-magnitude),.out_valid(exp_valid),.result(exp_result));
  anvil_q1_fp_compat_div divider(
    .clk(clk),.rst_n(rst_n),.in_valid(state==3),.in_ready(div_ready),
    .numerator(value>=0 ? 128'd281474976710656 : ({96'd0,exponential}<<24)),
    .denominator(64'd16777216+exponential),.out_valid(div_valid),
    .quotient(quotient),.remainder(remainder),.divide_by_zero(div_zero));
  assign in_ready=rst_n && state==0;
  assign out_valid=rst_n && state==7;
  assign result=out_valid ? result_reg : 0;
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; value<=0; result_reg<=0; exponential<=0; sigmoid<=0; product<=0;
    end else case(state)
      0: if(in_valid) begin value<=x; state<=1; end
      1: if(exp_ready) state<=2;
      2: if(exp_valid) begin exponential<=exp_result; state<=3; end
      3: if(div_ready) state<=4;
      4: if(div_valid) begin sigmoid<=quotient[63:0]; state<=5; end
      5: begin product<=$signed(value)*$signed({1'b0,sigmoid}); state<=6; end
      6: begin
        result_reg<=anvil_q1_fp_compat_pkg::sat32(
          anvil_q1_fp_compat_pkg::round_shift({{31{product[96]}},product},24));
        state<=7;
      end
      7: state<=0;
      default: state<=0;
    endcase
  end
endmodule
