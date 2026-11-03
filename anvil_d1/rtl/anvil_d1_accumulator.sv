module anvil_d1_accumulator (
  input wire clk, rst_n, flush, in_valid, in_first,
  output wire in_ready,
  input wire signed [127:0] in_value,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire signed [127:0] out_sum
);
  reg signed [127:0] committed_sum;
  anvil_d1_add128 add (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(in_valid),.in_ready(in_ready),
    .in_a(in_first ? 128'sd0 : committed_sum),.in_b(in_value),
    .out_valid(out_valid),.out_ready(out_ready),
    .out_error(out_error),.out_sum(out_sum)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) committed_sum<=0;
    else if (flush) committed_sum<=0;
    else if (out_valid && out_ready && !out_error) committed_sum<=out_sum;
  end
endmodule
