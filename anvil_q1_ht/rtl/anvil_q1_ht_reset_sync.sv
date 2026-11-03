module anvil_q1_ht_reset_sync (
  input wire clk,
  input wire rst_n,
  output wire local_rst_n
);
  (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
  reg [1:0] release_pipe;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      release_pipe <= 2'b00;
    else
      release_pipe <= {release_pipe[0], 1'b1};
  end

  assign local_rst_n = rst_n && release_pipe[1];
endmodule
