module anvil_q1_ht2_panel_prefetch (
  input wire clk, rst_n, abort_error,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [32:0] cmd_address,
  input wire [12:0] cmd_columns,
  input wire cmd_w4,
  output wire out_valid,
  input wire out_ready,
  output wire [1023:0] out_data,
  output wire [12:0] out_column,
  output wire out_error,
  output wire busy, done, error,
  output wire mem_valid,
  input wire mem_ready,
  output wire [32:0] mem_address,
  output wire [7:0] mem_burstcount,
  input wire mem_data_valid,
  output wire mem_data_ready,
  input wire [511:0] mem_data,
  input wire mem_error
);
  localparam IDLE = 2'd0, ACTIVE = 2'd1, DRAIN = 2'd2, COMPLETE = 2'd3;
  wire run_n;
  reg [1:0] state;
  reg w4, failed, request_owned, half, first_error, output_owned;
  reg [32:0] address;
  reg [12:0] columns, requested, produced, consumed;
  reg [7:0] remaining;
  reg [511:0] low_q, high_q;
  reg low_error_q, high_error_q;
  reg [12:0] column_q;
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [512:0] low_words [0:127];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [512:0] high_words [0:127];
  wire [12:0] columns_left = columns - requested;
  wire [6:0] request_columns = columns_left >= 64 ? 7'd64 : columns_left[6:0];
  wire [7:0] request_beats = w4 ? {1'b0, request_columns} : {request_columns, 1'b0};
  wire [13:0] occupied = {1'b0, produced} - {1'b0, consumed};
  wire command_transfer = cmd_valid && cmd_ready;
  wire memory_command = mem_valid && mem_ready;
  wire memory_beat = mem_data_valid && mem_data_ready;
  wire [7:0] beats_left = request_owned ? remaining : request_beats;
  wire fetch = run_n && state == ACTIVE && !abort_error &&
    (!output_owned || out_ready) && produced != consumed;
  wire [33:0] command_end = {1'b0, cmd_address} +
    (cmd_w4 ? {15'b0, cmd_columns, 6'b0} : {14'b0, cmd_columns, 7'b0});
  wire command_bad = cmd_columns == 0 || cmd_columns > 4864 ||
    (|cmd_address[5:0]) || command_end > 34'h200000000;
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  assign cmd_ready = run_n && state == IDLE && !abort_error;
  assign mem_valid = run_n && state == ACTIVE && !abort_error &&
    !request_owned && requested < columns && occupied <= 64;
  assign mem_address = mem_valid ? address : 33'b0;
  assign mem_burstcount = mem_valid ? request_beats : 8'b0;
  assign mem_data_ready = run_n && (request_owned || memory_command);
  assign out_valid = run_n && state == ACTIVE && output_owned && !abort_error;
  assign out_data = out_valid ? {w4 ? 512'b0 : high_q, low_q} : 1024'b0;
  assign out_column = out_valid ? column_q : 13'b0;
  assign out_error = out_valid && (low_error_q || (!w4 && high_error_q));
  assign busy = run_n && state != IDLE;
  assign done = run_n && state == COMPLETE;
  assign error = done && failed;

  always @(posedge clk) begin
    if (run_n) begin
      if (state == ACTIVE && memory_beat && !abort_error) begin
        if (w4 || !half) low_words[produced[6:0]] <= {mem_error, mem_data};
        else high_words[produced[6:0]] <= {first_error || mem_error, mem_data};
      end
      if (fetch) begin
        {low_error_q, low_q} <= low_words[consumed[6:0]];
        {high_error_q, high_q} <= high_words[consumed[6:0]];
      end
    end
  end
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      w4 <= 0;
      failed <= 0;
      request_owned <= 0;
      half <= 0;
      first_error <= 0;
      output_owned <= 0;
      address <= 0;
      columns <= 0;
      requested <= 0;
      produced <= 0;
      consumed <= 0;
      remaining <= 0;
      column_q <= 0;
    end else begin
      if (memory_command) begin
        request_owned <= 1;
        remaining <= request_beats;
        requested <= requested + {6'b0, request_columns};
        address <= address + {19'b0, request_beats, 6'b0};
      end
      if (memory_beat) begin
        remaining <= beats_left - 1'b1;
        if (beats_left == 1) request_owned <= 0;
        if (mem_error) failed <= 1;
      end
      if (abort_error && state == ACTIVE) begin
        failed <= 1;
        output_owned <= 0;
        state <= DRAIN;
      end else case (state)
        IDLE: if (command_transfer) begin
          w4 <= cmd_w4;
          address <= cmd_address;
          columns <= cmd_columns;
          requested <= 0;
          produced <= 0;
          consumed <= 0;
          half <= 0;
          first_error <= 0;
          output_owned <= 0;
          failed <= command_bad;
          if (command_bad) state <= COMPLETE;
          else state <= ACTIVE;
        end
        ACTIVE: begin
          if (memory_beat) begin
            if (w4 || half) produced <= produced + 1'b1;
            if (!w4) half <= !half;
            first_error <= mem_error;
          end
          if (!output_owned || out_ready) output_owned <= fetch;
          if (fetch) begin
            column_q <= consumed;
            consumed <= consumed + 1'b1;
          end
          if (out_valid && out_ready && column_q + 1'b1 == columns) begin
            output_owned <= 0;
            state <= COMPLETE;
          end
        end
        DRAIN: if (!request_owned || (memory_beat && beats_left == 1)) state <= COMPLETE;
        COMPLETE: state <= IDLE;
        default: begin failed <= 1; output_owned <= 0; state <= DRAIN; end
      endcase
    end
  end
endmodule
