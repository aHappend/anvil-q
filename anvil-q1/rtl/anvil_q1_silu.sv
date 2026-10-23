module anvil_q1_silu(
  input wire clk, rst_n, start,
  output wire ready, done, error,
  input wire signed [31:0] argument,
  output wire signed [31:0] value
);
  reg [2:0] state;
  reg failed;
  reg signed [31:0] x, result;
  reg [31:0] exponential;
  wire [63:0] magnitude, numerator, divisor, sigmoid;
  wire signed [64:0] product;
  wire exp_ready, exp_done, exp_error, div_ready, div_done, div_error;
  wire [31:0] exp_value;
  assign magnitude=x<0 ? -$signed({{32{x[31]}},x}) : {32'd0,x};
  assign numerator=x>=0 ? 64'd281474976710656 : ({32'd0,exponential}<<24);
  assign divisor=64'd16777216+{32'd0,exponential};
  assign product=$signed({{33{x[31]}},x})*$signed({39'd0,sigmoid[25:0]});
  assign ready=rst_n && state==0;
  assign done=rst_n && state==6;
  assign error=done && failed;
  assign value=rst_n ? result : 32'sd0;
  anvil_q1_exp exponential_unit(
    .clk(clk),.rst_n(rst_n),.start(state==1),.ready(exp_ready),
    .done(exp_done),.error(exp_error),.argument(-$signed(magnitude)),.value(exp_value));
  anvil_q1_unsigned_divider #(64) division(
    .clk(clk),.rst_n(rst_n),.start(state==3),.ready(div_ready),
    .done(div_done),.error(div_error),.numerator(numerator),
    .divisor(divisor),.quotient(sigmoid));
  always @(posedge clk) begin
    if(!rst_n) begin state<=0; failed<=0; x<=0; result<=0; exponential<=0; end
    else case(state)
      0: if(start) begin x<=argument; failed<=0; state<=1; end
      1: if(exp_ready) state<=2;
      2: if(exp_done) begin
        if(exp_error) begin failed<=1; state<=6; end
        else begin exponential<=exp_value; state<=3; end
      end
      3: if(div_ready) state<=4;
      4: if(div_done) begin
        if(div_error) begin failed<=1; state<=6; end
        else begin
          result<=anvil_q1_pkg::sat32(anvil_q1_pkg::round_shift(
            {{63{product[64]}},product},24));
          state<=6;
        end
      end
      6: state<=0;
      default: state<=0;
    endcase
  end
endmodule
