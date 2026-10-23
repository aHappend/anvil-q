module anvil_q2_exp (
  input wire clk, rst_n, start,
  input wire signed [63:0] x,
  output wire ready,
  output reg done,
  output reg [31:0] result
);
  localparam IDLE=3'd0, RANGE=3'd1, MULTIPLY_SETUP=3'd2,
             MULTIPLY=3'd3, DIVIDE_SETUP=3'd4, DIVIDE=3'd5,
             ACCUMULATE=3'd6, FINISH=3'd7;
  reg [2:0] state;
  reg [5:0] remaining;
  reg [28:0] range_dividend;
  reg [23:0] range_remainder;
  reg [4:0] exponent;
  reg [2:0] iteration;
  reg term_negative;
  reg [24:0] term_magnitude, multiplier;
  reg [48:0] product, multiplicand;
  reg [23:0] dividend, quotient;
  reg [2:0] remainder;
  reg signed [27:0] total;
  wire [24:0] range_trial={range_remainder,range_dividend[28]};
  wire range_subtract=range_trial>=25'd11629080;
  wire [3:0] trial={remainder,dividend[23]};
  wire subtract=trial>={1'b0,iteration};
  wire signed [25:0] next_term=term_negative ?
    -$signed({2'd0,quotient}) : $signed({2'd0,quotient});

  assign ready=rst_n && state==IDLE;
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=IDLE; remaining<=0; range_dividend<=0; range_remainder<=0;
      exponent<=0; iteration<=0; term_negative<=0; term_magnitude<=0;
      multiplier<=0; product<=0; multiplicand<=0; dividend<=0;
      quotient<=0; remainder<=0; total<=0; done<=0; result<=0;
    end else begin
      done<=0;
      case(state)
        IDLE: if(start) begin
          if(x < -64'sd1048576) begin result<=0; done<=1; end
          else if(x>=0) begin result<=32'd16777216; done<=1; end
          else begin
            range_dividend<=29'((-x)<<8);
            range_remainder<=0; exponent<=0; remaining<=29;
            iteration<=1; term_negative<=0; term_magnitude<=25'd16777216;
            total<=28'sd16777216; state<=RANGE;
          end
        end
        RANGE: begin
          range_remainder<=range_subtract ?
            24'(range_trial-25'd11629080) : range_trial[23:0];
          range_dividend<={range_dividend[27:0],1'b0};
          exponent<={exponent[3:0],range_subtract};
          remaining<=remaining-1'b1;
          if(remaining==1) state<=MULTIPLY_SETUP;
        end
        MULTIPLY_SETUP: begin
          multiplier<=term_magnitude; multiplicand<={25'd0,range_remainder};
          product<=0; remaining<=25; term_negative<=!term_negative;
          state<=MULTIPLY;
        end
        MULTIPLY: begin
          if(multiplier[0]) product<=product+multiplicand;
          multiplier<={1'b0,multiplier[24:1]};
          multiplicand<={multiplicand[47:0],1'b0};
          remaining<=remaining-1'b1;
          if(remaining==1) state<=DIVIDE_SETUP;
        end
        DIVIDE_SETUP: begin
          // Bounds: |term|<=2^24, r<11629080, hence product<2^48.
          dividend<=product[47:24]; quotient<=0; remainder<=0;
          remaining<=24; state<=DIVIDE;
        end
        DIVIDE: begin
          remainder<=subtract ? 3'(trial-{1'b0,iteration}) : trial[2:0];
          dividend<={dividend[22:0],1'b0};
          quotient<={quotient[22:0],subtract};
          remaining<=remaining-1'b1;
          if(remaining==1) state<=ACCUMULATE;
        end
        ACCUMULATE: begin
          term_magnitude<={1'b0,quotient};
          total<=total+{{2{next_term[25]}},next_term};
          if(iteration==6) state<=FINISH;
          else begin iteration<=iteration+1'b1; state<=MULTIPLY_SETUP; end
        end
        FINISH: begin
          result<=total<0 ? 32'd0 : ({4'd0,total} >> exponent);
          done<=1; state<=IDLE;
        end
        default: state<=IDLE;
      endcase
    end
  end
endmodule
