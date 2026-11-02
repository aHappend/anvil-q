module anvil_q1_fp2_telemetry_csr #(
  parameter COUNTER_BITS=64
) (
  input wire clk, rst_n,
  input wire csr_req_valid,
  output wire csr_req_ready,
  input wire csr_req_write,
  input wire [11:0] csr_req_addr,
  input wire [31:0] csr_req_wdata,
  input wire [3:0] csr_req_wstrb,
  output wire csr_rsp_valid,
  input wire csr_rsp_ready,
  output wire [31:0] csr_rsp_rdata,
  output wire csr_rsp_error,
  input wire active, error_event,
  input wire fp_ddr_stall_event,
  input wire [6:0] alignment_events,
  input wire epilogue_bubble_event,
  input wire ulp_valid,
  input wire [31:0] ulp_distance
);
  localparam BITS=COUNTER_BITS>=1 && COUNTER_BITS<=64 ? COUNTER_BITS : 64;
  localparam [63:0] LIMIT=64'hffffffffffffffff >> (64-BITS);
  generate if (COUNTER_BITS<1 || COUNTER_BITS>64) begin: invalid_parameters
    initial $fatal(1,"FP2 TELEMETRY PARAMETER ERROR: COUNTER_BITS must be 1..64");
  end endgenerate
  function automatic [63:0] saturating_add(input [63:0] value, increment);
    reg [64:0] sum;
    begin
      sum={1'b0,value}+{1'b0,increment};
      saturating_add=sum>{1'b0,LIMIT} ? LIMIT : sum[63:0];
    end
  endfunction
  reg enabled, sticky_error;
  reg pending, response_valid, pending_error, response_error;
  reg [31:0] pending_data, response_data;
  reg [63:0] ddr_count, exponent_count, bubble_count, ulp_sum;
  reg [63:0] finite_count, nonfinite_count;
  reg [31:0] ulp_max;
  reg [63:0] snap_ddr, snap_exponent, snap_bubble, snap_sum;
  reg [63:0] snap_finite, snap_nonfinite;
  reg [31:0] snap_max;
  reg [31:0] read_data;
  reg request_error;
  wire [31:0] write_mask={{8{csr_req_wstrb[3]}},{8{csr_req_wstrb[2]}},
    {8{csr_req_wstrb[1]}},{8{csr_req_wstrb[0]}}};
  wire accepted=csr_req_valid && csr_req_ready;
  wire control_write=accepted && csr_req_write && !request_error;
  wire clear_event=control_write && csr_req_wstrb[0] && csr_req_wdata[1];
  wire snapshot_event=control_write && csr_req_wstrb[0] && csr_req_wdata[2];
  wire saturated=ddr_count==LIMIT || exponent_count==LIMIT || bubble_count==LIMIT ||
    ulp_sum==LIMIT || finite_count==LIMIT || nonfinite_count==LIMIT;
  assign csr_req_ready=rst_n && !pending && !response_valid;
  assign csr_rsp_valid=rst_n && response_valid;
  assign csr_rsp_rdata=csr_rsp_valid ? response_data : 32'd0;
  assign csr_rsp_error=csr_rsp_valid && response_error;
  always @* begin
    read_data=0; request_error=0;
    if (csr_req_addr[1:0]!=0) request_error=1;
    else if (csr_req_write) begin
      if (csr_req_addr!=12'h004 || |(csr_req_wdata & write_mask & 32'hfffffff8))
        request_error=1;
    end else case (csr_req_addr)
      12'h000: read_data=32'h02020002;
      12'h004: read_data={31'd0,enabled};
      12'h008: read_data={29'd0,saturated,sticky_error,active};
      12'h020: read_data=snap_ddr[31:0];
      12'h024: read_data=snap_ddr[63:32];
      12'h030: read_data=snap_exponent[31:0];
      12'h034: read_data=snap_exponent[63:32];
      12'h040: read_data=snap_bubble[31:0];
      12'h044: read_data=snap_bubble[63:32];
      12'h050: read_data=snap_sum[31:0];
      12'h054: read_data=snap_sum[63:32];
      12'h060: read_data=snap_max;
      12'h068: read_data=snap_finite[31:0];
      12'h06c: read_data=snap_finite[63:32];
      12'h070: read_data=snap_nonfinite[31:0];
      12'h074: read_data=snap_nonfinite[63:32];
      default: request_error=1;
    endcase
    if (request_error) read_data=0;
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      enabled<=0; sticky_error<=0; pending<=0; response_valid<=0;
      pending_error<=0; response_error<=0; pending_data<=0; response_data<=0;
      ddr_count<=0; exponent_count<=0; bubble_count<=0; ulp_sum<=0;
      finite_count<=0; nonfinite_count<=0; ulp_max<=0;
      snap_ddr<=0; snap_exponent<=0; snap_bubble<=0; snap_sum<=0;
      snap_finite<=0; snap_nonfinite<=0; snap_max<=0;
    end else begin
      if (response_valid && csr_rsp_ready) response_valid<=0;
      if (pending) begin
        pending<=0; response_valid<=1;
        response_data<=pending_data; response_error<=pending_error;
      end
      if (accepted) begin
        pending<=1; pending_data<=read_data; pending_error<=request_error;
      end
      if (control_write && csr_req_wstrb[0]) enabled<=csr_req_wdata[0];
      if (clear_event) begin
        sticky_error<=0;
        ddr_count<=0; exponent_count<=0; bubble_count<=0; ulp_sum<=0;
        finite_count<=0; nonfinite_count<=0; ulp_max<=0;
        snap_ddr<=0; snap_exponent<=0; snap_bubble<=0; snap_sum<=0;
        snap_finite<=0; snap_nonfinite<=0; snap_max<=0;
      end else begin
        if (error_event) sticky_error<=1;
        if (snapshot_event) begin
          snap_ddr<=ddr_count; snap_exponent<=exponent_count; snap_bubble<=bubble_count;
          snap_sum<=ulp_sum; snap_max<=ulp_max;
          snap_finite<=finite_count; snap_nonfinite<=nonfinite_count;
        end
        if (enabled) begin
          ddr_count<=saturating_add(ddr_count,{63'd0,fp_ddr_stall_event});
          exponent_count<=saturating_add(exponent_count,{57'd0,alignment_events});
          bubble_count<=saturating_add(bubble_count,{63'd0,epilogue_bubble_event});
          if (ulp_valid) begin
            if (ulp_distance==32'hffffffff)
              nonfinite_count<=saturating_add(nonfinite_count,64'd1);
            else begin
              ulp_sum<=saturating_add(ulp_sum,{32'd0,ulp_distance});
              finite_count<=saturating_add(finite_count,64'd1);
              if (ulp_distance>ulp_max) ulp_max<=ulp_distance;
            end
          end
        end
      end
    end
  end
endmodule
