module anvil_d1_add128 #(
  parameter integer SUBTRACT=0
) (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire signed [127:0] in_a, in_b,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire signed [127:0] out_sum
);
  reg armed, busy, valid, overflow, carry, sign_a, sign_b;
  reg [1:0] stage;
  reg [127:0] a, b, partial, result;
  wire [127:0] selected_b=SUBTRACT!=0 ? ~in_b : in_b;
  wire [32:0] first_sum={1'b0,in_a[31:0]}+{1'b0,selected_b[31:0]}+
    {32'd0,(SUBTRACT!=0)};
  wire [32:0] next_sum={1'b0,a[stage*32+:32]}+
    {1'b0,b[stage*32+:32]}+{32'd0,carry};
  wire [127:0] completed={next_sum[31:0],partial[95:0]};
  wire completed_overflow=SUBTRACT!=0 ?
    ((sign_a!=sign_b) && (completed[127]!=sign_a)) :
    ((sign_a==sign_b) && (completed[127]!=sign_a));
  assign in_ready=rst_n && armed && !flush && !busy && !valid;
  assign out_valid=rst_n && !flush && valid;
  assign out_error=out_valid && overflow;
  assign out_sum=rst_n && !flush ? $signed(result) : 128'sd0;
  generate if (SUBTRACT!=0 && SUBTRACT!=1) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: add/subtract mode");
  end endgenerate
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      armed<=0; busy<=0; valid<=0; overflow<=0; carry<=0;
      sign_a<=0; sign_b<=0; stage<=0; a<=0; b<=0; partial<=0; result<=0;
    end else begin
      armed<=1;
      if (flush) begin busy<=0; valid<=0; overflow<=0; result<=0; stage<=0; end
      else begin
        if (out_valid && out_ready) valid<=0;
        if (in_valid && in_ready) begin
          a<=in_a; b<=selected_b; sign_a<=in_a[127]; sign_b<=in_b[127];
          partial<={96'd0,first_sum[31:0]}; carry<=first_sum[32];
          stage<=1; busy<=1; overflow<=0;
        end else if (busy) begin
          partial[stage*32+:32]<=next_sum[31:0]; carry<=next_sum[32];
          if (stage==3) begin
            result<=completed; overflow<=completed_overflow;
            busy<=0; valid<=1; stage<=0;
          end else stage<=stage+1'b1;
        end
      end
    end
  end
endmodule
