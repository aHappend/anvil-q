module anvil_q2_fp2_ping_pong_prefetch (
  input wire clk, rst_n, flush,
  input wire w_valid,
  output wire w_ready,
  input wire [511:0] w_data,
  input wire [15:0] w_scale,
  input wire w_format, w_first, w_last,
  input wire [31:0] w_tag,
  input wire w_error,
  output wire tile_valid,
  input wire tile_ready,
  output wire [2047:0] tile_data,
  output wire tile_first, tile_last,
  output wire [31:0] tile_tag,
  output wire tile_error
);
  reg [1:0] full;
  reg fill_slot, read_slot;
  reg [1:0] beat_count;
  reg [1:0] format_slot, first_slot, last_slot, error_slot;
  reg [31:0] tag_slot [0:1];
  reg [2047:0] data_slot [0:1];
  wire [1023:0] decoded;
  wire [63:0] decode_error;
  genvar lane;
  generate for (lane=0;lane<64;lane=lane+1) begin: mx_lanes
    anvil_q2_fp2_mx_decode decoder (
      .in_payload(w_data[8*lane+:8]),
      .in_scale(lane<32 ? w_scale[7:0] : w_scale[15:8]),
      .out_bf16(decoded[16*lane+:16]),.out_error(decode_error[lane])
    );
  end endgenerate
  wire first_beat=beat_count==0;
  wire format=first_beat ? w_format : format_slot[fill_slot];
  wire last_beat=format ? beat_count==1 : beat_count==3;
  wire metadata_error=!first_beat &&
    (w_format!=format_slot[fill_slot] ||
     w_first!=first_slot[fill_slot] || w_last!=last_slot[fill_slot] ||
     w_tag!=tag_slot[fill_slot]);
  wire beat_error=w_error || metadata_error || (format && (|decode_error));

  assign w_ready=rst_n && !flush && !full[fill_slot];
  assign tile_valid=rst_n && !flush && full[read_slot];
  assign tile_data=tile_valid ? data_slot[read_slot] : 2048'd0;
  assign tile_first=tile_valid && first_slot[read_slot];
  assign tile_last=tile_valid && last_slot[read_slot];
  assign tile_tag=tile_valid ? tag_slot[read_slot] : 32'd0;
  assign tile_error=tile_valid && error_slot[read_slot];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      full<=0;
      fill_slot<=0;
      read_slot<=0;
      beat_count<=0;
      format_slot<=0;
      first_slot<=0;
      last_slot<=0;
      error_slot<=0;
      tag_slot[0]<=0;
      tag_slot[1]<=0;
    end else if (flush) begin
      full<=0;
      fill_slot<=0;
      read_slot<=0;
      beat_count<=0;
      error_slot<=0;
    end else begin
      if (tile_valid && tile_ready) begin
        full[read_slot]<=0;
        read_slot<=!read_slot;
      end
      if (w_valid && w_ready) begin
        if (first_beat) begin
          format_slot[fill_slot]<=w_format;
          first_slot[fill_slot]<=w_first;
          last_slot[fill_slot]<=w_last;
          tag_slot[fill_slot]<=w_tag;
          error_slot[fill_slot]<=beat_error;
        end else error_slot[fill_slot]<=error_slot[fill_slot] || beat_error;
        if (last_beat) begin
          full[fill_slot]<=1;
          fill_slot<=!fill_slot;
          beat_count<=0;
        end else beat_count<=beat_count+2'd1;
      end
    end
  end

  always @(posedge clk) begin
    if (w_valid && w_ready) begin
      if (format)
        data_slot[fill_slot][1024*beat_count[0]+:1024]<=decoded;
      else
        data_slot[fill_slot][512*beat_count+:512]<=w_data;
    end
  end
endmodule
