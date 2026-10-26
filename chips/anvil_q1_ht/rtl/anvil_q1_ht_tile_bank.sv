module anvil_q1_ht_tile_bank #(
  parameter TILE_BEATS = 256
) (
  input wire ddr_clk,
  input wire write_enable,
  input wire [7:0] write_address,
  input wire [511:0] write_data,
  input wire clk,
  input wire read_enable,
  input wire [7:0] read_address,
  output reg [511:0] read_data
);
  generate
    if (TILE_BEATS >= 1 && TILE_BEATS <= 256) begin : g_legal
      (* ramstyle = "M20K, no_rw_check" *)
      reg [511:0] storage [0:TILE_BEATS-1];

      always @(posedge ddr_clk) begin
        if (write_enable)
          storage[write_address] <= write_data;
      end

      always @(posedge clk) begin
        if (read_enable)
          read_data <= storage[read_address];
      end
    end else begin : g_illegal
      initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: TILE_BEATS must be 1..256");
      always @* read_data = 512'b0;
    end
  endgenerate
endmodule
