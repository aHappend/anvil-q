module anvil_q2_ht_kv_burst (
  input wire clk, rst_n, invalidate,
  input wire [32:0] region_base, region_length,
  input wire req_valid,
  output wire req_ready,
  input wire req_write,
  input wire [32:0] req_address,
  input wire [511:0] req_data,
  input wire [63:0] req_mask,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [511:0] rsp_data,
  output wire rsp_error,
  output wire idle,
  output wire [32:0] k_address,
  output wire k_read,
  output wire [4:0] k_burstcount,
  input wire k_waitrequest,
  input wire [511:0] k_readdata,
  input wire k_readdatavalid,
  input wire [1:0] k_response,
  output wire write_valid,
  input wire write_ready,
  output wire [32:0] write_address,
  output wire [511:0] write_data,
  output wire [63:0] write_mask,
  input wire write_rsp_valid,
  output wire write_rsp_ready,
  input wire write_rsp_error
);
  localparam [2:0] IDLE=0, READ_COMMAND=1, READ_DATA=2, HIT=3,
    WRITE_COMMAND=4, WRITE_RESPONSE=5, RESPONSE=6;
  reg [2:0] state;
  reg failed, invalidated, operation_write, from_cache;
  reg [32:0] address;
  reg [511:0] data, hit_data, first_beat;
  reg [63:0] mask;
  reg [4:0] count, returned, cached_count;
  reg [26:0] cached_base;
  reg [15:0] cached_valid;
  reg [3:0] target;
  (* ramstyle = "M20K, no_rw_check" *)
  reg [511:0] lines [0:15];
  wire [33:0] region_end={1'b0,region_base}+{1'b0,region_length};
  wire [33:0] request_end={1'b0,req_address}+34'd64;
  wire malformed=(|req_address[5:0]) || req_address<region_base ||
    request_end>region_end || region_end>34'd8589934592;
  wire [27:0] remaining_beats=(region_end-{1'b0,req_address}) >> 6;
  wire [6:0] page_beats=7'd64-{1'b0,req_address[11:6]};
  wire [4:0] bounded_region=remaining_beats>16 ? 5'd16 : remaining_beats[4:0];
  wire [4:0] request_count=page_beats<{2'd0,bounded_region} ?
    page_beats[4:0] : bounded_region;
  wire [26:0] line_offset=req_address[32:6]-cached_base;
  wire hit=req_address[32:6]>=cached_base && line_offset<{22'd0,cached_count} &&
    line_offset<16 && cached_valid[line_offset[3:0]];
  wire accept=req_valid && req_ready;
  assign req_ready=rst_n && !invalidate && state==IDLE;
  assign rsp_valid=rst_n && state==RESPONSE;
  assign rsp_data=rsp_valid && !failed && !operation_write ?
    (from_cache ? hit_data : first_beat) : 512'd0;
  assign rsp_error=rsp_valid && failed;
  assign idle=rst_n && state==IDLE;
  assign k_read=rst_n && state==READ_COMMAND;
  assign k_address=k_read ? address : 33'd0;
  assign k_burstcount=k_read ? count : 5'd0;
  assign write_valid=rst_n && state==WRITE_COMMAND;
  assign write_address=write_valid ? address : 33'd0;
  assign write_data=write_valid ? data : 512'd0;
  assign write_mask=write_valid ? mask : 64'd0;
  assign write_rsp_ready=rst_n && state==WRITE_RESPONSE;
  always @(posedge clk) begin
    if (rst_n && state==READ_DATA && k_readdatavalid && returned<count &&
        !invalidate && !invalidated && k_response==0)
      lines[returned[3:0]]<=k_readdata;
    if (rst_n && state==HIT) hit_data<=lines[target];
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; invalidated<=0; address<=0; data<=0; mask<=0;
      count<=0; returned<=0; cached_count<=0; cached_base<=0;
      cached_valid<=0; target<=0;
      operation_write<=0; from_cache<=0;
    end else begin
      if (invalidate) begin
        cached_valid<=0;
        if (state!=IDLE) invalidated<=1;
      end
      case (state)
        IDLE: if (accept) begin
          address<=req_address; data<=req_data; mask<=req_mask;
          failed<=malformed; invalidated<=0;
          operation_write<=req_write; from_cache<=hit && !req_write;
          if (malformed) state<=RESPONSE;
          else if (req_write) begin cached_valid<=0; state<=WRITE_COMMAND; end
          else if (hit) begin target<=line_offset[3:0]; state<=HIT; end
          else begin
            cached_valid<=0; cached_base<=req_address[32:6];
            cached_count<=request_count; count<=request_count; returned<=0;
            state<=READ_COMMAND;
          end
        end
        READ_COMMAND: if (!k_waitrequest) state<=READ_DATA;
        READ_DATA: if (k_readdatavalid) begin
          if (k_response!=0 || returned>=count) begin failed<=1; cached_valid<=0; end
          else if (!invalidate && !invalidated && !failed)
            cached_valid[returned[3:0]]<=1;
          if (returned+5'd1==count) state<=RESPONSE;
          returned<=returned+5'd1;
        end
        HIT: state<=RESPONSE;
        WRITE_COMMAND: if (write_ready) state<=WRITE_RESPONSE;
        WRITE_RESPONSE: if (write_rsp_valid) begin
          failed<=write_rsp_error; state<=RESPONSE;
        end
        RESPONSE: if (rsp_ready) begin state<=IDLE; invalidated<=0; end
        default: begin failed<=1; cached_valid<=0; state<=RESPONSE; end
      endcase
    end
  end
  // The first beat is the requested beat; future beats only populate the line cache.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) first_beat<=0;
    else if (state==READ_DATA && k_readdatavalid && returned==0)
      first_beat<=k_readdata;
  end
endmodule
