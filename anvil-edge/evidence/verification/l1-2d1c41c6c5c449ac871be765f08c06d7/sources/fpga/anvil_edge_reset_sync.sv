module anvil_edge_reset_sync (
  input wire clk, reset_n,
  output wire rst_n
);
  (* async_reg="true" *) reg reset_meta, reset_sync;
  always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin reset_meta<=0; reset_sync<=0; end
    else begin reset_meta<=1; reset_sync<=reset_meta; end
  end
  assign rst_n=reset_n && reset_sync;
endmodule
