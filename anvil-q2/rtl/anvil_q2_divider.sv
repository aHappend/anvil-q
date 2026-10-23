module anvil_q2_divider (
  input wire clk, rst_n, start,
  input wire [128:0] numerator,
  input wire [63:0] denominator,
  output wire ready,
  output reg done, error,
  output reg [128:0] quotient
);
  reg busy;
  reg [7:0] remaining;
  reg [128:0] dividend;
  reg [63:0] divisor, remainder;
  wire [64:0] trial = {remainder,dividend[128]};
  wire subtract = trial >= {1'b0,divisor};
  assign ready = rst_n && !busy;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy<=0; remaining<=0; dividend<=0; divisor<=0; remainder<=0;
      quotient<=0; done<=0; error<=0;
    end else begin
      done<=0;
      if (start && ready) begin
        quotient<=0; remainder<=0; error<=denominator==0;
        if (denominator==0) done<=1;
        else begin
          dividend<=numerator; divisor<=denominator;
          remaining<=129; busy<=1;
        end
      end else if (busy) begin
        remainder<=subtract ? 64'(trial-{1'b0,divisor}) : trial[63:0];
        dividend<={dividend[127:0],1'b0};
        quotient<={quotient[127:0],subtract};
        remaining<=remaining-1'b1;
        if (remaining==1) begin busy<=0; done<=1; end
      end
    end
  end
endmodule
