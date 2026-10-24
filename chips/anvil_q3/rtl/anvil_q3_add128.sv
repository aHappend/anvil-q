module anvil_q3_add128 #(
  parameter SUBTRACT=0
) (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire signed [127:0] in_a, in_b,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire signed [127:0] out_sum
);
  reg busy, result_valid, result_error, carry;
  reg [2:0] segment;
  reg [127:0] a, b, partial, result;
  wire [16:0] segment_sum={1'b0,a[segment*16+:16]}+
    {1'b0,b[segment*16+:16]}+{16'd0,carry};
  wire [127:0] completed={segment_sum[15:0],partial[111:0]};
  assign in_ready=rst_n && !flush && !busy && (!result_valid || out_ready);
  assign out_valid=rst_n && !flush && result_valid;
  assign out_error=out_valid && result_error;
  assign out_sum=out_valid ? $signed(result) : 128'sd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy<=0; result_valid<=0; result_error<=0; carry<=0;
      segment<=0; a<=0; b<=0; partial<=0; result<=0;
    end else if (flush) begin
      busy<=0; result_valid<=0; result_error<=0;
    end else begin
      if (result_valid && out_ready) result_valid<=0;
      if (in_valid && in_ready) begin
        a<=in_a; b<=SUBTRACT ? ~in_b : in_b;
        partial<=0; carry<=SUBTRACT!=0; segment<=0; busy<=1;
      end else if (busy) begin
        partial[segment*16+:16]<=segment_sum[15:0];
        carry<=segment_sum[16];
        if (segment==7) begin
          busy<=0;
          result_valid<=1;
          result<=completed;
          result_error<=(a[127]==b[127]) && (completed[127]!=a[127]);
        end else segment<=segment+1'b1;
      end
    end
  end
endmodule
