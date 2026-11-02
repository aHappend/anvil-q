module anvil_q1_ht3_async_fifo #(
  parameter WIDTH = 515, DEPTH = 512
) (
  input wire source_clk, destination_clk, rst_n,
  input wire source_valid,
  output wire source_ready,
  input wire [(WIDTH > 0 ? WIDTH : 1)-1:0] source_data,
  output wire destination_valid,
  input wire destination_ready,
  output wire [(WIDTH > 0 ? WIDTH : 1)-1:0] destination_data,
  output wire [(DEPTH > 1 ? $clog2(DEPTH) : 1):0] source_used
);
  localparam LEGAL = WIDTH >= 1 && WIDTH <= 2048 && DEPTH >= 2 &&
    DEPTH <= 512 && (DEPTH & (DEPTH-1)) == 0;
  localparam W = WIDTH > 0 ? WIDTH : 1;
  localparam A = DEPTH > 1 ? $clog2(DEPTH) : 1;
  initial if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 asynchronous FIFO geometry");
  generate if (!LEGAL) begin: g_invalid
    assign source_ready = 0;
    assign destination_valid = 0;
    assign destination_data = 0;
    assign source_used = 0;
  end else begin: g_legal
    wire source_run_n, destination_run_n;
    reg [A:0] write_binary, write_gray, read_binary, read_gray;
    (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
    reg [A:0] read_meta, read_sync, write_meta, write_sync;
    (* ramstyle = "M20K", nomem2reg *) reg [W-1:0] storage [0:DEPTH-1];
    reg [W-1:0] read_data;
    reg output_owned;
    wire [A:0] full_mask = {2'b11,{(A-1){1'b0}}};
    wire full = write_gray == (read_sync ^ full_mask);
    wire empty = read_gray == write_sync;
    wire push = source_valid && source_ready;
    wire fetch = destination_run_n && (!output_owned || destination_ready) && !empty;
    wire [A:0] next_write = write_binary + 1'b1;
    wire [A:0] next_read = read_binary + 1'b1;
    reg [A:0] synchronized_read_binary;
    integer bit_index;
    always @* begin
      synchronized_read_binary[A] = read_sync[A];
      for (bit_index = A-1; bit_index >= 0; bit_index = bit_index - 1)
        synchronized_read_binary[bit_index] =
          synchronized_read_binary[bit_index+1] ^ read_sync[bit_index];
    end
    anvil_q1_ht3_reset_sync u_source_reset(source_clk, rst_n, source_run_n);
    anvil_q1_ht3_reset_sync u_destination_reset(destination_clk, rst_n, destination_run_n);
    assign source_ready = source_run_n && !full;
    assign source_used = source_run_n ? write_binary - synchronized_read_binary : 0;
    assign destination_valid = destination_run_n && output_owned;
    assign destination_data = destination_valid ? read_data : {W{1'b0}};
    always @(posedge source_clk) begin
      if (push) storage[write_binary[A-1:0]] <= source_data;
    end
    always @(posedge destination_clk) begin
      if (fetch) read_data <= storage[read_binary[A-1:0]];
    end
    always @(posedge source_clk or negedge rst_n) begin
      if (!rst_n) begin
        write_binary <= 0;
        write_gray <= 0;
        read_meta <= 0;
        read_sync <= 0;
      end else if (source_run_n) begin
        read_meta <= read_gray;
        read_sync <= read_meta;
        if (push) begin
          write_binary <= next_write;
          write_gray <= (next_write >> 1) ^ next_write;
        end
      end
    end
    always @(posedge destination_clk or negedge rst_n) begin
      if (!rst_n) begin
        read_binary <= 0;
        read_gray <= 0;
        write_meta <= 0;
        write_sync <= 0;
        output_owned <= 0;
      end else if (destination_run_n) begin
        write_meta <= write_gray;
        write_sync <= write_meta;
        if (!output_owned || destination_ready) output_owned <= fetch;
        if (fetch) begin
          read_binary <= next_read;
          read_gray <= (next_read >> 1) ^ next_read;
        end
      end
    end
  end endgenerate
endmodule
