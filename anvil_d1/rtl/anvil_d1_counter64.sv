module anvil_d1_counter64 (
  input wire clk, rst_n, clear, snapshot,
  input wire [35:0] increment,
  output wire [63:0] live_value, snapshot_value,
  output wire overflow
);
  reg [63:0] live, saved;
  reg overflow_sticky;
  wire [32:0] low_sum={1'b0,live[31:0]}+{1'b0,increment[31:0]};
  wire [32:0] high_sum={1'b0,live[63:32]}+{29'd0,increment[35:32]}+
    {32'd0,low_sum[32]};
  assign live_value=rst_n ? live : 64'd0;
  assign snapshot_value=rst_n ? saved : 64'd0;
  assign overflow=rst_n && overflow_sticky;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin live<=0; saved<=0; overflow_sticky<=0; end
    else if (clear) begin live<=0; saved<=0; overflow_sticky<=0; end
    else begin
      if (snapshot) saved<=live;
      if (high_sum[32]) begin live<=64'hffffffffffffffff; overflow_sticky<=1; end
      else live<={high_sum[31:0],low_sum[31:0]};
    end
  end
endmodule
