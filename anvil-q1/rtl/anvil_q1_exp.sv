module anvil_q1_exp(
  input wire clk, rst_n, start,
  output wire ready, done, error,
  input wire signed [63:0] argument,
  output wire [31:0] value
);
  reg [3:0] state;
  reg failed, negative;
  reg [63:0] remainder;
  reg [4:0] exponent;
  reg [2:0] term_index;
  reg signed [63:0] term, total;
  reg [31:0] result;
  wire signed [63:0] product, next_term, next_total;
  wire div_ready, div_done, div_error;
  wire [63:0] quotient, numerator, divisor;
  assign product=-term*$signed(remainder);
  assign numerator=product<0 ? -product : product;
  assign divisor={61'd0,term_index}<<24;
  assign next_term=negative ? -$signed(quotient) : $signed(quotient);
  assign next_total=total+next_term;
  assign ready=rst_n && state==0;
  assign done=rst_n && state==8;
  assign error=done && failed;
  assign value=rst_n ? result : 32'd0;
  anvil_q1_unsigned_divider #(64) division(
    .clk(clk),.rst_n(rst_n),.start(state==3),.ready(div_ready),
    .done(div_done),.error(div_error),.numerator(numerator),
    .divisor(divisor),.quotient(quotient));
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; failed<=0; negative<=0; remainder<=0; exponent<=0;
      term_index<=0; term<=0; total<=0; result<=0;
    end else case(state)
      0: if(start) begin
        failed<=0; exponent<=0;
        if(argument < -64'sd1048576) begin result<=0; state<=8; end
        else if(argument>=0) begin result<=32'd16777216; state<=8; end
        else begin remainder<=(-argument)<<8; state<=1; end
      end
      1: if(remainder>=64'd11629080) begin
        remainder<=remainder-64'd11629080; exponent<=exponent+1;
      end else begin
        term<=64'sd16777216; total<=64'sd16777216; term_index<=1; state<=3;
      end
      3: if(div_ready) begin negative<=product<0; state<=4; end
      4: if(div_done) begin
        if(div_error) begin failed<=1; state<=8; end
        else begin
          term<=next_term; total<=next_total;
          if(term_index==6) begin
            result<=next_total<0 ? 32'd0 : (next_total>>exponent);
            state<=8;
          end else begin term_index<=term_index+1; state<=3; end
        end
      end
      8: state<=0;
      default: state<=0;
    endcase
  end
endmodule
