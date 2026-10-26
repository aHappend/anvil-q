module anvil_q1_ht_weight_stream (
  input wire clk, rst_n, abort_error,
  input wire command_valid,
  output wire command_ready,
  input wire [3:0] command_kind,
  input wire [31:0] command_layer,
  input wire [2:0] command_proj,
  input wire [31:0] command_offset, command_bytes,
  input wire [7:0] command_packet_bytes,
  output wire packet_valid,
  input wire packet_ready,
  output wire [1023:0] packet_data,
  output wire packet_last,
  output wire done, error,

  output wire lookup_valid,
  input wire lookup_ready,
  output wire [31:0] lookup_index,
  input wire lookup_rsp_valid,
  output wire lookup_rsp_ready,
  input wire [32:0] lookup_base,
  input wire [31:0] lookup_length,
  input wire lookup_error,

  output wire dma_valid,
  input wire dma_ready,
  output wire [32:0] dma_address,
  output wire [31:0] dma_bytes,
  output wire dma_abort,
  input wire dma_done,
  output wire dma_done_ready,
  input wire dma_error,
  input wire [26:0] dma_tiles,

  input wire tile_valid,
  output wire tile_ready,
  input wire [8:0] tile_beats,
  output wire release_valid,
  input wire release_ready,
  output wire read_valid,
  input wire read_ready,
  output wire [7:0] read_address,
  input wire read_rsp_valid,
  output wire read_rsp_ready,
  input wire [511:0] read_data,
  input wire [63:0] read_mask,
  input wire tile_error
);
  localparam IDLE = 4'd0, LOOKUP = 4'd1, LOOKUP_WAIT = 4'd2,
             ADDRESS = 4'd3, ISSUE = 4'd4, RUN = 4'd5, COMPLETE = 4'd6;
  localparam NO_TILE = 2'd0, READ = 2'd1, RESPONSE = 2'd2, RELEASE = 2'd3;
  reg [3:0] state;
  reg [1:0] tile_state;
  reg failed, completion_seen;
  reg [31:0] descriptor_index, offset, length, remaining;
  reg [32:0] base;
  reg [33:0] start_address, end_offset;
  reg [31:0] transfer_bytes;
  reg [7:0] packet_bytes;
  reg [5:0] skip;
  reg [8:0] beats, beat_index;
  reg [26:0] released_tiles, expected_tiles;
  reg [1535:0] reservoir;
  reg [8:0] buffered;
  wire pop = packet_valid && packet_ready;
  wire capture = read_rsp_valid && read_rsp_ready;
  wire [8:0] available_bytes = 9'd64 - {3'b0, skip};
  wire [31:0] not_buffered = remaining - {23'b0, buffered};
  wire [8:0] capture_bytes =
    not_buffered < {23'b0, available_bytes} ? {1'b0, not_buffered[7:0]} : available_bytes;
  wire [511:0] shifted_data = read_data >> {skip, 3'b0};
  wire [63:0] needed_mask =
    capture_bytes == 64 ? 64'hffffffffffffffff :
                         (64'h1 << capture_bytes) - 64'h1;
  wire capture_bad = (((read_mask >> skip) & needed_mask) != needed_mask);
  wire [33:0] physical_end = {1'b0, base} + end_offset;
  wire [33:0] aligned_length = {28'b0, start_address[5:0]} + {2'b0, length};

  assign command_ready = rst_n && state == IDLE;
  assign lookup_valid = rst_n && state == LOOKUP;
  assign lookup_index = lookup_valid ? descriptor_index : 32'b0;
  assign lookup_rsp_ready = rst_n && (state == LOOKUP_WAIT ||
                                     (state == LOOKUP && lookup_ready));
  assign dma_valid = rst_n && state == ISSUE;
  assign dma_address = dma_valid ? {start_address[32:6], 6'b0} : 33'b0;
  assign dma_bytes = dma_valid ? transfer_bytes : 32'b0;
  assign dma_done_ready = rst_n && state == RUN && !completion_seen;
  assign dma_abort = rst_n && state == RUN && (abort_error || tile_error);
  assign packet_valid = rst_n && state == RUN && !failed && remaining != 0 &&
                        buffered >= {1'b0, packet_bytes};
  assign packet_data = packet_valid ? reservoir[1023:0] : 1024'b0;
  assign packet_last = packet_valid && remaining == {24'b0, packet_bytes};
  assign done = rst_n && state == COMPLETE;
  assign error = done && failed;
  assign tile_ready = rst_n && state == RUN && tile_state == NO_TILE &&
                      (!completion_seen || released_tiles < expected_tiles);
  assign read_valid = rst_n && state == RUN && tile_state == READ &&
                      (failed || buffered <= 9'd128);
  assign read_address = read_valid ? beat_index[7:0] : 8'b0;
  assign read_rsp_ready = rst_n && state == RUN && tile_state == RESPONSE && !pop;
  assign release_valid = rst_n && state == RUN && tile_state == RELEASE;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      tile_state <= NO_TILE;
      failed <= 0;
      completion_seen <= 0;
      descriptor_index <= 0;
      offset <= 0;
      length <= 0;
      remaining <= 0;
      base <= 0;
      start_address <= 0;
      end_offset <= 0;
      transfer_bytes <= 0;
      packet_bytes <= 0;
      skip <= 0;
      beats <= 0;
      beat_index <= 0;
      released_tiles <= 0;
      expected_tiles <= 0;
      reservoir <= 0;
      buffered <= 0;
    end else begin
      case (state)
        IDLE: if (command_valid) begin
          failed <= 0;
          completion_seen <= 0;
          released_tiles <= 0;
          expected_tiles <= 0;
          reservoir <= 0;
          buffered <= 0;
          tile_state <= NO_TILE;
          offset <= command_offset;
          length <= command_bytes;
          remaining <= command_bytes;
          packet_bytes <= command_packet_bytes;
          end_offset <= {2'b0, command_offset} + {2'b0, command_bytes};
          descriptor_index <= (command_layer << 6) + (command_layer << 5) +
                              {25'b0, command_kind, 3'b0} + {29'b0, command_proj};
          if (command_layer >= 24 || command_kind > 7 ||
              command_kind == 5 || command_kind == 6 || command_kind == 7 ||
              command_bytes == 0 || command_packet_bytes == 0 ||
              command_packet_bytes > 128) begin
            failed <= 1;
            state <= COMPLETE;
          end else state <= LOOKUP;
        end
        LOOKUP, LOOKUP_WAIT: begin
          if (lookup_valid && lookup_ready) state <= LOOKUP_WAIT;
          if (lookup_rsp_valid && lookup_rsp_ready) begin
            base <= lookup_base;
            start_address <= {1'b0, lookup_base} + {2'b0, offset};
            if (lookup_error || end_offset > {2'b0, lookup_length}) begin
              failed <= 1;
              state <= COMPLETE;
            end else state <= ADDRESS;
          end
        end
        ADDRESS: begin
          skip <= start_address[5:0];
          transfer_bytes <= aligned_length[31:0];
          if (physical_end > 34'h200000000 || |aligned_length[33:32]) begin
            failed <= 1;
            state <= COMPLETE;
          end else state <= ISSUE;
        end
        ISSUE: if (dma_ready) state <= RUN;
        RUN: begin
          if (dma_done && dma_done_ready) begin
            completion_seen <= 1;
            expected_tiles <= dma_tiles;
            if (dma_error) failed <= 1;
          end
          if (tile_error) failed <= 1;
          if (abort_error) failed <= 1;
          if (pop) begin
            reservoir <= reservoir >> {packet_bytes, 3'b0};
            buffered <= buffered - {1'b0, packet_bytes};
            remaining <= remaining - {24'b0, packet_bytes};
            if (remaining < {24'b0, packet_bytes}) failed <= 1;
          end
          case (tile_state)
            NO_TILE: if (tile_valid && tile_ready) begin
              beats <= tile_beats;
              beat_index <= 0;
              tile_state <= READ;
            end
            READ: if (read_valid && read_ready) tile_state <= RESPONSE;
            RESPONSE: if (capture) begin
              skip <= 0;
              if (!failed && not_buffered != 0) begin
                reservoir <= reservoir |
                  ({{1024{1'b0}}, shifted_data} << {buffered, 3'b0});
                buffered <= buffered + capture_bytes;
                if (capture_bad) failed <= 1;
              end
              if (beat_index + 9'd1 == beats) tile_state <= RELEASE;
              else begin
                beat_index <= beat_index + 9'd1;
                tile_state <= READ;
              end
            end
            RELEASE: if (release_ready) begin
              released_tiles <= released_tiles + 27'd1;
              tile_state <= NO_TILE;
            end
          endcase
          if (completion_seen && tile_state == NO_TILE &&
              released_tiles == expected_tiles && (failed || remaining == 0))
            state <= COMPLETE;
          if (tile_error && completion_seen) state <= COMPLETE;
          if (!failed && remaining != 0 && remaining < {24'b0, packet_bytes}) failed <= 1;
        end
        COMPLETE: state <= IDLE;
        default: begin
          failed <= 1;
          state <= COMPLETE;
        end
      endcase
    end
  end
endmodule
