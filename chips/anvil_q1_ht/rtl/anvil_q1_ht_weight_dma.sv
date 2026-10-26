module anvil_q1_ht_weight_dma #(
  parameter TILE_BEATS = 256
) (
  input wire clk,
  input wire ddr_clk,
  input wire rst_n,
  input wire request_valid,
  output wire request_ready,
  input wire [32:0] request_address,
  input wire [31:0] request_bytes,
  input wire request_abort,
  output wire completion_valid,
  input wire completion_ready,
  output wire completion_error,
  output wire [26:0] completion_tiles,

  input wire load_enable,
  input wire load_clear,
  input wire load_valid,
  output wire load_ready,
  input wire [32:0] load_address,
  input wire [511:0] load_data,
  input wire [63:0] load_byteenable,
  input wire load_last,
  output wire load_done,
  output wire load_error,
  output wire load_idle,

  output wire fill_valid,
  input wire fill_ready,
  output wire [8:0] fill_beats,
  output wire [63:0] fill_tail,
  output wire fill_data_valid,
  input wire fill_data_ready,
  output wire [511:0] fill_data,
  output wire fill_last,
  output wire fill_abort,
  input wire fill_error,

  output wire [32:0] avm_address,
  output wire [7:0] avm_burstcount,
  output wire avm_read,
  output wire avm_write,
  output wire [511:0] avm_writedata,
  output wire [63:0] avm_byteenable,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid,
  input wire [1:0] avm_response,
  input wire avm_writeresponsevalid,
  output wire [63:0] accepted_read_beats,
  output wire protocol_error
);
  wire core_rst_n, ddr_rst_n;
  anvil_q1_ht_reset_sync u_core_reset(clk, rst_n, core_rst_n);
  anvil_q1_ht_reset_sync u_ddr_reset(ddr_clk, rst_n, ddr_rst_n);

  generate
    if (TILE_BEATS >= 1 && TILE_BEATS <= 256) begin : g_legal
      localparam IDLE = 4'd0, VALIDATE = 4'd1, BOUNDS = 4'd2,
                 TILE_PLAN = 4'd3, FILL = 4'd4, BURST_PLAN = 4'd5,
                 READ_ISSUE = 4'd6, READ_WAIT = 4'd7, NEXT_TILE = 4'd8,
                 ABORT_TILE = 4'd9, COMPLETE = 4'd10;
      reg [3:0] state;
      reg outstanding, read_failed, upload_open, upload_failed;
      reg load_finished, failed_protocol;
      reg [1:0] write_state;
      reg [32:0] write_address;
      reg [511:0] write_data;
      reg [63:0] write_mask;
      reg write_last;
      reg [33:0] cursor, end_address;
      reg [31:0] byte_count;
      reg [26:0] remaining;
      reg [8:0] tile_goal, tile_remaining;
      reg [63:0] final_mask, tile_mask;
      reg [4:0] burst_beats, burst_remaining;
      reg [31:0] read_count_low, read_count_high;
      reg [26:0] published_tiles;
      (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
      reg abort_meta, abort_sync;
      wire mailbox_ready, command_valid, command_ready;
      wire [64:0] command_data;
      wire result_ready;
      wire [27:0] result_data;
      wire read_accept = avm_read && !avm_waitrequest;
      wire read_response_allowed = state == READ_WAIT || read_accept;
      wire read_response = avm_readdatavalid && read_response_allowed;
      wire write_accept = avm_write && !avm_waitrequest;
      wire write_response_allowed = write_state == 2 || write_accept;
      wire write_response = avm_writeresponsevalid && write_response_allowed;
      wire response_bad = avm_response != 2'b00;
      wire [6:0] page_remaining = 7'd64 - {1'b0, cursor[11:6]};
      wire [4:0] tile_burst_limit =
        tile_remaining > 9'd16 ? 5'd16 : tile_remaining[4:0];
      wire [4:0] next_burst =
        page_remaining < {2'b0, tile_burst_limit} ? page_remaining[4:0] : tile_burst_limit;
      wire response_success =
        !read_failed && !abort_sync && !response_bad && !fill_error && fill_data_ready;

      anvil_q1_ht_cdc_mailbox #(.WIDTH(65)) u_request (
        .source_clk(clk), .destination_clk(ddr_clk), .rst_n(rst_n),
        .source_valid(request_valid && !outstanding),
        .source_ready(mailbox_ready),
        .source_data({request_address, request_bytes}),
        .destination_valid(command_valid),
        .destination_ready(command_ready),
        .destination_data(command_data)
      );
      anvil_q1_ht_cdc_mailbox #(.WIDTH(28)) u_completion (
        .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n),
        .source_valid(state == COMPLETE), .source_ready(result_ready),
        .source_data({read_failed, published_tiles}),
        .destination_valid(completion_valid),
        .destination_ready(completion_ready),
        .destination_data(result_data)
      );
      assign request_ready = core_rst_n && !outstanding && mailbox_ready;
      assign completion_error = completion_valid && result_data[27];
      assign completion_tiles = completion_valid ? result_data[26:0] : 27'b0;
      assign command_ready =
        ddr_rst_n && !failed_protocol && state == IDLE && write_state == 0 && !upload_open;
      assign load_ready = ddr_rst_n && load_enable && !upload_failed && !failed_protocol &&
                          state == IDLE && write_state == 0 && (!command_valid || upload_open);
      assign load_idle = ddr_rst_n && !upload_open && write_state == 0;
      assign load_done = ddr_rst_n && load_finished;
      assign load_error = ddr_rst_n && upload_failed;
      assign fill_valid = ddr_rst_n && state == FILL && !fill_error && !abort_sync;
      assign fill_beats = fill_valid ? tile_goal : 9'b0;
      assign fill_tail = fill_valid ? tile_mask : 64'b0;
      assign fill_data_valid = ddr_rst_n && read_response && response_success;
      assign fill_data = fill_data_valid ? avm_readdata : 512'b0;
      assign fill_last = fill_data_valid && tile_remaining == 9'd1;
      assign fill_abort = ddr_rst_n && state == ABORT_TILE;
      assign avm_read = ddr_rst_n && state == READ_ISSUE;
      assign avm_write = ddr_rst_n && write_state == 1;
      assign avm_address = avm_read ? cursor[32:0] : (avm_write ? write_address : 33'b0);
      assign avm_burstcount = avm_read ? {3'b0, burst_beats} : (avm_write ? 8'd1 : 8'd0);
      assign avm_writedata = avm_write ? write_data : 512'b0;
      assign avm_byteenable = avm_read ? 64'hffffffffffffffff : (avm_write ? write_mask : 64'b0);
      assign accepted_read_beats = ddr_rst_n ? {read_count_high, read_count_low} : 64'b0;
      assign protocol_error = ddr_rst_n && failed_protocol;

      always @(posedge clk or negedge core_rst_n) begin
        if (!core_rst_n)
          outstanding <= 0;
        else begin
          if (request_valid && request_ready)
            outstanding <= 1;
          if (completion_valid && completion_ready)
            outstanding <= 0;
        end
      end

      always @(posedge ddr_clk or negedge ddr_rst_n) begin
        if (!ddr_rst_n) begin abort_meta <= 0; abort_sync <= 0; end
        else begin abort_meta <= request_abort; abort_sync <= abort_meta; end
      end
      always @(posedge ddr_clk or negedge ddr_rst_n) begin
        if (!ddr_rst_n) begin
          state <= IDLE;
          read_failed <= 0;
          upload_open <= 0;
          upload_failed <= 0;
          load_finished <= 0;
          failed_protocol <= 0;
          write_state <= 0;
          write_address <= 0;
          write_data <= 0;
          write_mask <= 0;
          write_last <= 0;
          cursor <= 0;
          end_address <= 0;
          byte_count <= 0;
          remaining <= 0;
          tile_goal <= 0;
          tile_remaining <= 0;
          final_mask <= 0;
          tile_mask <= 0;
          burst_beats <= 0;
          burst_remaining <= 0;
          read_count_low <= 0;
          read_count_high <= 0;
          published_tiles <= 0;
        end else begin
          load_finished <= 0;
          if (load_clear && state == IDLE && write_state == 0 && !upload_open)
            upload_failed <= 0;
          if ((avm_readdatavalid && !read_response_allowed) ||
              (avm_writeresponsevalid && !write_response_allowed))
            failed_protocol <= 1;
          if (read_response) begin
            read_count_low <= read_count_low + 32'd1;
            if (&read_count_low)
              read_count_high <= read_count_high + 32'd1;
          end

          if (load_valid && load_ready) begin
            if (load_address[5:0] != 0) begin
              upload_failed <= 1;
              upload_open <= 0;
              load_finished <= 1;
            end else begin
              write_address <= load_address;
              write_data <= load_data;
              write_mask <= load_byteenable;
              write_last <= load_last;
              upload_open <= 1;
              write_state <= 1;
            end
          end
          if (write_accept)
            write_state <= 2;
          if (write_response) begin
            write_state <= 0;
            if (response_bad) begin
              upload_failed <= 1;
              upload_open <= 0;
              load_finished <= 1;
            end else if (write_last) begin
              upload_open <= 0;
              load_finished <= 1;
            end
          end

          case (state)
            IDLE: if (command_valid && command_ready) begin
              cursor <= {1'b0, command_data[64:32]};
              byte_count <= command_data[31:0];
              read_failed <= 0;
              published_tiles <= 0;
              state <= VALIDATE;
            end
            VALIDATE: begin
              end_address <= cursor + {2'b0, byte_count};
              remaining <= {1'b0, byte_count[31:6]} +
                           (byte_count[5:0] != 0 ? 27'd1 : 27'd0);
              final_mask <= byte_count[5:0] == 0 ? 64'hffffffffffffffff :
                            (64'd1 << byte_count[5:0]) - 64'd1;
              state <= BOUNDS;
            end
            BOUNDS: begin
              if (byte_count == 0 || cursor[5:0] != 0 ||
                  end_address > 34'h200000000) begin
                read_failed <= 1;
                state <= COMPLETE;
              end else
                state <= TILE_PLAN;
            end
            TILE_PLAN: begin
              tile_goal <= remaining > TILE_BEATS ? TILE_BEATS : remaining[8:0];
              tile_mask <= remaining > TILE_BEATS ? 64'hffffffffffffffff : final_mask;
              state <= FILL;
            end
            FILL: begin
              if (fill_error) begin
                read_failed <= 1;
                state <= COMPLETE;
              end else if (fill_valid && fill_ready) begin
                tile_remaining <= tile_goal;
                state <= BURST_PLAN;
              end
            end
            BURST_PLAN: begin
              burst_beats <= next_burst;
              burst_remaining <= next_burst;
              state <= READ_ISSUE;
            end
            READ_ISSUE, READ_WAIT: begin
              if (read_accept)
                state <= READ_WAIT;
              if (read_response) begin
                cursor <= {cursor[33:6] + 28'd1, 6'b0};
                remaining <= remaining - 27'd1;
                tile_remaining <= tile_remaining - 9'd1;
                burst_remaining <= burst_remaining - 5'd1;
                if (!response_success)
                  read_failed <= 1;
                if (response_success && tile_remaining == 9'd1)
                  published_tiles <= published_tiles + 27'd1;
                if (burst_remaining == 5'd1) begin
                  if (read_failed || !response_success)
                    state <= ABORT_TILE;
                  else if (tile_remaining == 9'd1)
                    state <= NEXT_TILE;
                  else
                    state <= BURST_PLAN;
                end
              end
            end
            NEXT_TILE: begin
              if (remaining == 0)
                state <= COMPLETE;
              else
                state <= TILE_PLAN;
            end
            ABORT_TILE: state <= COMPLETE;
            COMPLETE: if (result_ready) state <= IDLE;
            default: begin
              read_failed <= 1;
              failed_protocol <= 1;
              state <= COMPLETE;
            end
          endcase
          if (abort_sync && state != IDLE && state != COMPLETE && state != ABORT_TILE) begin
            read_failed <= 1;
            // An asserted Avalon command must survive waitrequest; drain its burst.
            if (state != READ_ISSUE && state != READ_WAIT) state <= ABORT_TILE;
          end
        end
      end
    end else begin : g_illegal
      initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: TILE_BEATS must be 1..256");
      assign request_ready = 0;
      assign completion_valid = 0;
      assign completion_error = 0;
      assign completion_tiles = 0;
      assign load_ready = 0;
      assign load_done = 0;
      assign load_error = ddr_rst_n;
      assign load_idle = 0;
      assign fill_valid = 0;
      assign fill_beats = 0;
      assign fill_tail = 0;
      assign fill_data_valid = 0;
      assign fill_data = 0;
      assign fill_last = 0;
      assign fill_abort = 0;
      assign avm_address = 0;
      assign avm_burstcount = 0;
      assign avm_read = 0;
      assign avm_write = 0;
      assign avm_writedata = 0;
      assign avm_byteenable = 0;
      assign accepted_read_beats = 0;
      assign protocol_error = ddr_rst_n;
    end
  endgenerate
endmodule
