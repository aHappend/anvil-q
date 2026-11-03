module anvil_q1_ht3_panel_prefetch #(
  parameter TILE_BEATS = 256
) (
  input wire clk, rst_n, abort_error, cmd_valid,
  output wire cmd_ready,
  input wire [32:0] cmd_address,
  input wire [12:0] cmd_columns,
  input wire cmd_compact,
  output wire out_valid,
  input wire out_ready,
  output wire [1023:0] out_data,
  output wire [12:0] out_column,
  output wire out_error, busy, done, error,
  output wire mem_valid,
  input wire mem_ready,
  output wire [32:0] mem_address,
  output wire [7:0] mem_burstcount,
  input wire mem_data_valid,
  output wire mem_data_ready,
  input wire [511:0] mem_data,
  input wire mem_error
);
  localparam LEGAL = TILE_BEATS >= 1 && TILE_BEATS <= 256;
  localparam BURST_LIMIT = LEGAL && TILE_BEATS < 128 ? TILE_BEATS : 128;
  localparam IDLE = 2'd0, ACTIVE = 2'd1, DRAIN = 2'd2, COMPLETE = 2'd3;
  wire run_n;
  reg [1:0] state;
  reg compact, failed, half, output_owned;
  reg request_visible;
  reg [32:0] visible_address;
  reg [7:0] visible_beats;
  reg [32:0] address;
  reg [12:0] columns, produced, consumed, column_q;
  reg [13:0] total_beats, requested, returned, consumed_beats;
  reg [511:0] low_q, high_q;
  reg low_error_q, high_error_q;
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [512:0] low_words [0:127];
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [512:0] high_words [0:127];
  wire [13:0] left = total_beats - requested;
  wire [7:0] burst_limit = compact && BURST_LIMIT > 64 ? 8'd64 : 8'(BURST_LIMIT);
  wire [7:0] next_beats = left >= burst_limit ? burst_limit : left[7:0];
  wire [14:0] reserved = {1'b0, requested} - {1'b0, consumed_beats};
  wire [14:0] reserved_next = reserved + {7'b0, next_beats};
  wire command = cmd_valid && cmd_ready;
  wire request = mem_valid && mem_ready;
  wire response = mem_data_valid && mem_data_ready;
  wire fetch = run_n && state == ACTIVE &&
    (!output_owned || out_ready) && produced != consumed && !abort_error;
  wire [33:0] command_end = {1'b0, cmd_address} +
    (cmd_compact ? {15'b0, cmd_columns, 6'b0} : {14'b0, cmd_columns, 7'b0});
  wire command_bad = cmd_columns == 0 || cmd_columns > 4864 ||
    (|cmd_address[5:0]) || command_end > 34'h200000000;

  initial if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 panel prefetch TILE_BEATS");
  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  assign cmd_ready = run_n && LEGAL && state == IDLE && !abort_error;
  assign mem_valid = run_n && (request_visible ||
    (state == ACTIVE && !abort_error && requested != total_beats &&
     reserved_next <= (compact ? 128 : 256)));
  assign mem_address = !mem_valid ? 33'b0 : request_visible ? visible_address : address;
  assign mem_burstcount = !mem_valid ? 8'b0 : request_visible ? visible_beats : next_beats;
  assign mem_data_ready = run_n && (state == ACTIVE || state == DRAIN) &&
    (returned != requested || request);
  assign out_valid = run_n && output_owned;
  assign out_data = out_valid ? {compact ? 512'b0 : high_q, low_q} : 1024'b0;
  assign out_column = out_valid ? column_q : 13'b0;
  assign out_error = out_valid && (low_error_q || (!compact && high_error_q));
  assign busy = run_n && state != IDLE;
  assign done = run_n && state == COMPLETE;
  assign error = done && failed;

  always @(posedge clk) begin
    if (run_n) begin
      if (state == ACTIVE && response && !abort_error) begin
        if (compact || !half) low_words[produced[6:0]] <= {mem_error, mem_data};
        else high_words[produced[6:0]] <= {mem_error, mem_data};
      end
      if (fetch) begin
        {low_error_q, low_q} <= low_words[consumed[6:0]];
        {high_error_q, high_q} <= high_words[consumed[6:0]];
      end
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      compact <= 0;
      failed <= 0;
      half <= 0;
      output_owned <= 0;
      request_visible <= 0;
      visible_address <= 0;
      visible_beats <= 0;
      address <= 0;
      columns <= 0;
      produced <= 0;
      consumed <= 0;
      column_q <= 0;
      total_beats <= 0;
      requested <= 0;
      returned <= 0;
      consumed_beats <= 0;
    end else if (run_n) begin
      if (mem_valid && !mem_ready) begin
        request_visible <= 1;
        visible_address <= mem_address;
        visible_beats <= mem_burstcount;
      end
      if (request) begin
        request_visible <= 0;
        requested <= requested + {6'b0, mem_burstcount};
        address <= address + {19'b0, mem_burstcount, 6'b0};
      end
      if (response) begin
        returned <= returned + 1'b1;
        if (mem_error) failed <= 1;
      end
      if (out_valid && out_ready) output_owned <= 0;
      if (abort_error && state == ACTIVE) begin
        failed <= 1;
        state <= DRAIN;
      end else case (state)
        IDLE: if (command) begin
          compact <= cmd_compact;
          address <= cmd_address;
          columns <= cmd_columns;
          total_beats <= cmd_compact ? {1'b0, cmd_columns} : {cmd_columns, 1'b0};
          requested <= 0;
          returned <= 0;
          consumed_beats <= 0;
          produced <= 0;
          consumed <= 0;
          half <= 0;
          output_owned <= 0;
          failed <= command_bad;
          if (command_bad) state <= COMPLETE;
          else state <= ACTIVE;
        end
        ACTIVE: begin
          if (response) begin
            if (compact || half) produced <= produced + 1'b1;
            if (!compact) half <= !half;
          end
          if (fetch) begin
            output_owned <= 1;
            column_q <= consumed;
            consumed <= consumed + 1'b1;
            consumed_beats <= consumed_beats + (compact ? 14'd1 : 14'd2);
          end
          if (out_valid && out_ready && column_q + 1'b1 == columns)
            state <= COMPLETE;
        end
        DRAIN: if (!request_visible && !request && (returned == requested ||
          (response && returned + 1'b1 == requested)) &&
          (!output_owned || out_ready)) state <= COMPLETE;
        COMPLETE: state <= IDLE;
        default: begin failed <= 1; state <= DRAIN; end
      endcase
    end
  end
endmodule
