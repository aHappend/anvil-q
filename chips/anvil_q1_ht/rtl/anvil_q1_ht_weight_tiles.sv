module anvil_q1_ht_weight_tiles #(
  parameter TILE_BEATS = 256
) (
  input wire clk,
  input wire ddr_clk,
  input wire rst_n,

  input wire fill_valid,
  output wire fill_ready,
  output wire fill_bank,
  input wire [8:0] fill_beats,
  input wire [63:0] fill_tail,
  input wire fill_data_valid,
  output wire fill_data_ready,
  input wire [511:0] fill_data,
  input wire fill_last,
  input wire fill_abort,
  output wire fill_error,

  output wire tile_valid,
  input wire tile_ready,
  output wire tile_bank,
  output wire [8:0] tile_beats,
  output wire [63:0] tile_tail,
  input wire release_valid,
  output wire release_ready,

  input wire read_valid,
  output wire read_ready,
  input wire [7:0] read_address,
  output wire read_rsp_valid,
  input wire read_rsp_ready,
  output wire [511:0] read_data,
  output wire [63:0] read_mask,
  output wire compute_error
);
  wire core_rst_n, ddr_rst_n;
  anvil_q1_ht_reset_sync u_core_reset(clk, rst_n, core_rst_n);
  anvil_q1_ht_reset_sync u_ddr_reset(ddr_clk, rst_n, ddr_rst_n);

  generate
    if (TILE_BEATS >= 1 && TILE_BEATS <= 256) begin : g_legal
      reg [1:0] ddr_owned, full_toggle, release_seen;
      reg filling, filling_bank, next_fill, ddr_failed;
      reg [8:0] written, expected;
      reg [8:0] bank_beats [0:1];
      reg [63:0] bank_tail [0:1];
      reg [1:0] core_available, full_seen, release_toggle;
      reg computing, computing_bank, next_compute, core_failed;
      reg [8:0] core_beats [0:1];
      reg [63:0] core_tail [0:1];
      (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
      reg [1:0] full_meta, full_sync, release_meta, release_sync;

      reg request_pending, request_bank;
      reg [7:0] request_address;
      reg [63:0] request_mask;
      reg response_valid, response_bank;
      reg [63:0] response_mask;
      wire output_space = !response_valid || read_rsp_ready;
      wire move_request = request_pending && output_space && !core_failed;
      wire fill_transfer = fill_data_valid && fill_data_ready;
      wire final_fill = written + 9'd1 == expected;
      wire read_transfer = read_valid && read_ready;
      wire legal_read = {1'b0, read_address} < core_beats[computing_bank];
      wire [511:0] bank_read [0:1];
      genvar bank;

      assign fill_ready = ddr_rst_n && !ddr_failed && !filling && !ddr_owned[next_fill];
      assign fill_bank = ddr_rst_n ? next_fill : 1'b0;
      assign fill_data_ready = ddr_rst_n && !ddr_failed && filling && !fill_abort;
      assign fill_error = ddr_rst_n && ddr_failed;
      assign tile_valid =
        core_rst_n && !core_failed && !computing && core_available[next_compute];
      assign tile_bank = core_rst_n ? next_compute : 1'b0;
      assign tile_beats = tile_valid ? core_beats[next_compute] : 9'b0;
      assign tile_tail = tile_valid ? core_tail[next_compute] : 64'b0;
      assign release_ready =
        core_rst_n && !core_failed && computing && !request_pending && !response_valid;
      assign read_ready = core_rst_n && !core_failed && computing &&
                          (!request_pending || output_space) && !release_valid;
      assign read_rsp_valid = core_rst_n && !core_failed && response_valid;
      assign read_data = read_rsp_valid ? bank_read[response_bank] : 512'b0;
      assign read_mask = read_rsp_valid ? response_mask : 64'b0;
      assign compute_error = core_rst_n && core_failed;

      for (bank = 0; bank < 2; bank = bank + 1) begin : g_bank
        anvil_q1_ht_tile_bank #(.TILE_BEATS(TILE_BEATS)) u_storage (
          .ddr_clk(ddr_clk),
          .write_enable(fill_transfer && filling_bank == bank &&
                        fill_last == final_fill),
          .write_address(written[7:0]),
          .write_data(fill_data),
          .clk(clk),
          .read_enable(core_rst_n && move_request && request_bank == bank),
          .read_address(request_address),
          .read_data(bank_read[bank])
        );
      end

      always @(posedge ddr_clk or negedge ddr_rst_n) begin
        if (!ddr_rst_n) begin
          release_meta <= 0;
          release_sync <= 0;
        end else begin
          release_meta <= release_toggle;
          release_sync <= release_meta;
        end
      end

      always @(posedge clk or negedge core_rst_n) begin
        if (!core_rst_n) begin
          full_meta <= 0;
          full_sync <= 0;
        end else begin
          full_meta <= full_toggle;
          full_sync <= full_meta;
        end
      end

      integer d;
      always @(posedge ddr_clk or negedge ddr_rst_n) begin
        if (!ddr_rst_n) begin
          ddr_owned <= 0;
          full_toggle <= 0;
          release_seen <= 0;
          filling <= 0;
          filling_bank <= 0;
          next_fill <= 0;
          ddr_failed <= 0;
          written <= 0;
          expected <= 0;
          for (d = 0; d < 2; d = d + 1) begin
            bank_beats[d] <= 0;
            bank_tail[d] <= 0;
          end
        end else begin
          for (d = 0; d < 2; d = d + 1) begin
            if (release_sync[d] != release_seen[d]) begin
              release_seen[d] <= release_sync[d];
              ddr_owned[d] <= 0;
            end
          end
          if (fill_valid && fill_ready) begin
            if (fill_beats == 0 || fill_beats > TILE_BEATS || fill_tail == 0)
              ddr_failed <= 1;
            else begin
              filling <= 1;
              filling_bank <= next_fill;
              ddr_owned[next_fill] <= 1;
              written <= 0;
              expected <= fill_beats;
              bank_beats[next_fill] <= fill_beats;
              bank_tail[next_fill] <= fill_tail;
            end
          end
          if (fill_abort && filling) begin
            filling <= 0;
            ddr_owned[filling_bank] <= 0;
            written <= 0;
          end else if (fill_transfer) begin
            if (fill_last != final_fill) begin
              ddr_failed <= 1;
              filling <= 0;
              ddr_owned[filling_bank] <= 0;
            end else if (final_fill) begin
              full_toggle[filling_bank] <= !full_toggle[filling_bank];
              filling <= 0;
              next_fill <= !next_fill;
            end else
              written <= written + 9'd1;
          end
        end
      end

      integer c;
      always @(posedge clk or negedge core_rst_n) begin
        if (!core_rst_n) begin
          core_available <= 0;
          full_seen <= 0;
          release_toggle <= 0;
          computing <= 0;
          computing_bank <= 0;
          next_compute <= 0;
          core_failed <= 0;
          request_pending <= 0;
          request_bank <= 0;
          request_address <= 0;
          request_mask <= 0;
          response_valid <= 0;
          response_bank <= 0;
          response_mask <= 0;
          for (c = 0; c < 2; c = c + 1) begin
            core_beats[c] <= 0;
            core_tail[c] <= 0;
          end
        end else begin
          for (c = 0; c < 2; c = c + 1) begin
            if (full_sync[c] != full_seen[c]) begin
              full_seen[c] <= full_sync[c];
              if (core_available[c] || (computing && computing_bank == c))
                core_failed <= 1;
              else begin
                // Source metadata is frozen from fill start until ownership returns.
                core_beats[c] <= bank_beats[c];
                core_tail[c] <= bank_tail[c];
                core_available[c] <= 1;
              end
            end
          end
          if (tile_valid && tile_ready) begin
            computing <= 1;
            computing_bank <= next_compute;
            core_available[next_compute] <= 0;
          end
          if (release_valid && release_ready) begin
            computing <= 0;
            release_toggle[computing_bank] <= !release_toggle[computing_bank];
            next_compute <= !next_compute;
          end
          if (response_valid && read_rsp_ready)
            response_valid <= 0;
          if (move_request) begin
            response_valid <= 1;
            response_bank <= request_bank;
            response_mask <= request_mask;
            request_pending <= 0;
          end
          if (read_transfer) begin
            if (!legal_read) begin
              core_failed <= 1;
              response_valid <= 0;
              request_pending <= 0;
            end else begin
              request_pending <= 1;
              request_bank <= computing_bank;
              request_address <= read_address;
              request_mask <= {1'b0, read_address} + 9'd1 == core_beats[computing_bank] ?
                              core_tail[computing_bank] : 64'hffffffffffffffff;
            end
          end
        end
      end
    end else begin : g_illegal
      initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: TILE_BEATS must be 1..256");
      assign fill_ready = 0;
      assign fill_bank = 0;
      assign fill_data_ready = 0;
      assign fill_error = ddr_rst_n;
      assign tile_valid = 0;
      assign tile_bank = 0;
      assign tile_beats = 0;
      assign tile_tail = 0;
      assign release_ready = 0;
      assign read_ready = 0;
      assign read_rsp_valid = 0;
      assign read_data = 0;
      assign read_mask = 0;
      assign compute_error = core_rst_n;
    end
  endgenerate
endmodule
