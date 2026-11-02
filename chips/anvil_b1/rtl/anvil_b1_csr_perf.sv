module anvil_b1_csr_perf (
  input wire clk, rst_n,
  input wire csr_valid, csr_write,
  input wire [11:0] csr_addr,
  input wire [31:0] csr_wdata,
  input wire csr_rready,
  output wire csr_ready, csr_rvalid, csr_error,
  output wire [31:0] csr_rdata,
  input wire event_busy, event_error, event_cycle, event_mac_tile,
  input wire [9:0] event_valid_trits, event_nonzero_trits,
  input wire [15:0] event_weight_bytes, event_weight_bus_bytes,
  input wire [15:0] event_w4_bytes, event_bf16_bytes,
  input wire event_stall, event_token_ok, event_token_fail,
  input wire [15:0] event_saturation, event_metadata_bytes
);
  localparam integer COUNTERS=13;
  reg response_valid, response_error, sticky_error, snapshot_valid;
  reg [31:0] response_data;
  reg [63:0] live [0:COUNTERS-1];
  reg [63:0] snapshot [0:COUNTERS-1];
  wire [15:0] delta [0:COUNTERS-1];
  wire accept=csr_valid && csr_ready;
  wire control=accept && csr_write && csr_addr==12'h010 && csr_wdata[31:2]==0;
  wire clear=control && csr_wdata[0];
  wire capture=control && !csr_wdata[0] && csr_wdata[1];
  reg decode_error;
  reg [31:0] decode_data;
  integer index;

  function automatic [63:0] saturating_increment(
    input [63:0] value, input [15:0] increment
  );
    reg [16:0] low_sum;
    reg c1, c2, c3, overflow;
    begin
      low_sum={1'b0,value[15:0]}+{1'b0,increment};
      c1=low_sum[16];
      c2=c1 && (&value[31:16]);
      c3=c2 && (&value[47:32]);
      overflow=c3 && (&value[63:48]);
      if (overflow) saturating_increment=64'hffffffffffffffff;
      else saturating_increment={
        value[63:48]+{15'd0,c3},
        value[47:32]+{15'd0,c2},
        value[31:16]+{15'd0,c1},
        low_sum[15:0]};
    end
  endfunction

  assign delta[0]={15'd0,event_cycle};
  assign delta[1]={15'd0,event_mac_tile};
  assign delta[2]={6'd0,event_valid_trits};
  assign delta[3]={6'd0,event_nonzero_trits};
  assign delta[4]=event_weight_bytes;
  assign delta[5]=event_weight_bus_bytes;
  assign delta[6]=event_w4_bytes;
  assign delta[7]=event_bf16_bytes;
  assign delta[8]={15'd0,event_stall};
  assign delta[9]={15'd0,event_token_ok};
  assign delta[10]={15'd0,event_token_fail};
  assign delta[11]=event_saturation;
  assign delta[12]=event_metadata_bytes;
  assign csr_ready=rst_n && (!response_valid || csr_rready);
  assign csr_rvalid=rst_n && response_valid;
  assign csr_error=csr_rvalid && response_error;
  assign csr_rdata=rst_n ? response_data : 32'd0;

  always @* begin
    decode_error=0;
    decode_data=0;
    index=0;
    if (csr_addr[1:0]!=0) decode_error=1;
    else if (csr_write) begin
      if (csr_addr!=12'h010 || csr_wdata[31:2]!=0) decode_error=1;
    end else case (csr_addr)
      12'h000: decode_data=32'h41423130;
      12'h004: decode_data=32'h00010000;
      12'h008: decode_data={29'd0,snapshot_valid,sticky_error,event_busy};
      12'h010: decode_data=0;
      default: begin
        if (csr_addr>=12'h020 && csr_addr<=12'h084) begin
          index=(csr_addr-12'h020)>>3;
          if (!snapshot_valid) decode_error=1;
          else if (csr_addr[2]) decode_data=snapshot[index][63:32];
          else decode_data=snapshot[index][31:0];
        end else decode_error=1;
      end
    endcase
  end

  integer c;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      response_valid<=0; response_error<=0; response_data<=0;
      sticky_error<=0; snapshot_valid<=0;
      for (c=0;c<COUNTERS;c=c+1) begin live[c]<=0; snapshot[c]<=0; end
    end else begin
      if (accept) begin
        response_valid<=1;
        response_error<=decode_error;
        response_data<=decode_data;
      end else if (csr_rready) response_valid<=0;
      if (clear) begin
        sticky_error<=0; snapshot_valid<=0;
        for (c=0;c<COUNTERS;c=c+1) live[c]<=0;
      end else begin
        sticky_error<=sticky_error || event_error;
        for (c=0;c<COUNTERS;c=c+1)
          live[c]<=saturating_increment(live[c],delta[c]);
        if (capture) begin
          snapshot_valid<=1;
          for (c=0;c<COUNTERS;c=c+1) snapshot[c]<=live[c];
        end
      end
    end
  end
endmodule
