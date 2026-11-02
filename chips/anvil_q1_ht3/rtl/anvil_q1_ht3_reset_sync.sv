module anvil_q1_ht3_reset_sync (
  input wire clk, rst_n,
  output wire run_n
);
  (* async_reg = "true" *) reg [1:0] release_pipe;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) release_pipe <= 0;
    else release_pipe <= {release_pipe[0], 1'b1};
  end
  assign run_n = rst_n && release_pipe[1];
endmodule
