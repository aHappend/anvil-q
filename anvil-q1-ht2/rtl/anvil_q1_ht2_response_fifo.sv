module anvil_q1_ht2_response_fifo (
  input wire source_clk, destination_clk, rst_n,
  input wire source_valid,
  output wire source_ready,
  input wire [514:0] source_data,
  output wire destination_valid,
  input wire destination_ready,
  output wire [514:0] destination_data
);
  wire source_run_n, destination_run_n;
  reg [9:0] write_binary, write_gray, read_binary, read_gray;
  (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
  reg [9:0] read_meta, read_sync, write_meta, write_sync;
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [514:0] storage [0:511];
  reg [514:0] read_q;
  reg output_owned;
  wire full = write_gray == {~read_sync[9:8], read_sync[7:0]};
  wire empty = read_gray == write_sync;
  wire push = source_valid && source_ready;
  wire fetch = destination_run_n && (!output_owned || destination_ready) && !empty;
  wire [9:0] next_write = write_binary + 1'b1;
  wire [9:0] next_read = read_binary + 1'b1;

  anvil_q1_ht2_reset_sync u_source_reset(source_clk, rst_n, source_run_n);
  anvil_q1_ht2_reset_sync u_destination_reset(destination_clk, rst_n, destination_run_n);
  assign source_ready = source_run_n && !full;
  assign destination_valid = destination_run_n && output_owned;
  assign destination_data = destination_valid ? read_q : 515'b0;

  always @(posedge source_clk) begin
    if (push) storage[write_binary[8:0]] <= source_data;
  end
  always @(posedge destination_clk) begin
    if (fetch) read_q <= storage[read_binary[8:0]];
  end
  always @(posedge source_clk or negedge source_run_n) begin
    if (!source_run_n) begin
      write_binary <= 0;
      write_gray <= 0;
      read_meta <= 0;
      read_sync <= 0;
    end else begin
      read_meta <= read_gray;
      read_sync <= read_meta;
      if (push) begin
        write_binary <= next_write;
        write_gray <= (next_write >> 1) ^ next_write;
      end
    end
  end
  always @(posedge destination_clk or negedge destination_run_n) begin
    if (!destination_run_n) begin
      read_binary <= 0;
      read_gray <= 0;
      write_meta <= 0;
      write_sync <= 0;
      output_owned <= 0;
    end else begin
      write_meta <= write_gray;
      write_sync <= write_meta;
      if (!output_owned || destination_ready) output_owned <= fetch;
      if (fetch) begin
        read_binary <= next_read;
        read_gray <= (next_read >> 1) ^ next_read;
      end
    end
  end
endmodule
