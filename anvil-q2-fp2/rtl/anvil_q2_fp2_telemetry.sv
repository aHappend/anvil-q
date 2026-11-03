module anvil_q2_fp2_telemetry #(
  parameter COUNTER_BITS=64
) (
  input wire clk, rst_n,
  input wire event_active,
  input wire event_mem_stall,
  input wire event_weight_underflow,
  input wire event_tensor_bubble,
  input wire event_epilogue_stall,
  input wire [15:0] event_kv_bytes,
  input wire event_ddr_read,
  input wire event_ddr_write,
  input wire [15:0] event_kv_reuses,
  input wire event_token_complete,
  input wire event_mx_saturation,
  input wire event_error_complete,
  input wire csr_req_valid, csr_req_write,
  input wire [15:0] csr_req_addr,
  input wire [31:0] csr_req_wdata,
  input wire [3:0] csr_req_wstrb,
  output wire csr_req_ready,
  output wire csr_rsp_valid,
  output wire [31:0] csr_rsp_rdata,
  output wire csr_rsp_error,
  input wire csr_rsp_ready
);
  localparam CW=(COUNTER_BITS>=1 && COUNTER_BITS<=64) ? COUNTER_BITS : 1;
  localparam [64:0] MAXIMUM={1'b0,64'hffffffffffffffff} >> (64-CW);
  generate if (COUNTER_BITS<1 || COUNTER_BITS>64) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_FP2 PARAMETER ERROR: COUNTER_BITS must be 1..64");
  end endgenerate
  reg [CW-1:0] live [0:11], snapshot [0:11];
  reg snapshot_selected, pending, response_valid;
  reg [31:0] read_capture, response_data;
  reg error_capture, response_error;
  wire accept=csr_req_valid && csr_req_ready;
  wire control_write=accept && csr_req_write && csr_req_addr==16'h0008;
  wire clear=control_write && csr_req_wstrb[0] && csr_req_wdata[0];
  wire capture=control_write && csr_req_wstrb[0] && csr_req_wdata[1];
  wire [63:0] increments [0:11];
  assign increments[0]={63'd0,event_active};
  assign increments[1]={63'd0,event_mem_stall};
  assign increments[2]={63'd0,event_weight_underflow};
  assign increments[3]={63'd0,event_tensor_bubble};
  assign increments[4]={63'd0,event_epilogue_stall};
  assign increments[5]={48'd0,event_kv_bytes};
  assign increments[6]={63'd0,event_ddr_read};
  assign increments[7]={63'd0,event_ddr_write};
  assign increments[8]={48'd0,event_kv_reuses};
  assign increments[9]={63'd0,event_token_complete};
  assign increments[10]={63'd0,event_mx_saturation};
  assign increments[11]={63'd0,event_error_complete};
  genvar counter;
  generate for (counter=0;counter<12;counter=counter+1) begin: counters
    wire [64:0] sum={1'b0,{{(64-CW){1'b0}},live[counter]}}+
      {1'b0,increments[counter]};
    wire [CW-1:0] saturated=sum>MAXIMUM ? MAXIMUM[CW-1:0] : sum[CW-1:0];
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        live[counter]<=0;
        snapshot[counter]<=0;
      end else if (clear) begin
        live[counter]<=0;
        snapshot[counter]<=0;
      end else begin
        live[counter]<=saturated;
        if (capture) snapshot[counter]<=live[counter];
      end
    end
  end endgenerate
  wire [4:0] counter_index=csr_req_addr[7:3]-5'd2;
  reg [63:0] selected_counter;
  reg [31:0] request_data;
  reg request_error;
  always @* begin
    selected_counter=0;
    request_data=0;
    request_error=0;
    if (csr_req_addr[1:0]!=0) request_error=1;
    else case (csr_req_addr)
      16'h0000: begin
        request_data=32'h00020200;
        request_error=csr_req_write;
      end
      16'h0004: begin
        request_data={22'd0,snapshot_selected,event_active,8'h0f};
        request_error=csr_req_write;
      end
      16'h0008: request_data=0;
      default: begin
        if (csr_req_addr>=16'h0010 && csr_req_addr<=16'h006c) begin
          selected_counter=snapshot_selected ?
            {{(64-CW){1'b0}},snapshot[counter_index]} :
            {{(64-CW){1'b0}},live[counter_index]};
          request_data=csr_req_addr[2] ? selected_counter[63:32] :
            selected_counter[31:0];
          request_error=csr_req_write;
        end else request_error=1;
      end
    endcase
  end
  assign csr_req_ready=rst_n && !pending && !response_valid;
  assign csr_rsp_valid=rst_n && response_valid;
  assign csr_rsp_rdata=rst_n ? response_data : 32'd0;
  assign csr_rsp_error=csr_rsp_valid && response_error;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      snapshot_selected<=0;
      pending<=0;
      response_valid<=0;
      read_capture<=0;
      response_data<=0;
      error_capture<=0;
      response_error<=0;
    end else begin
      if (clear) snapshot_selected<=capture;
      else if (capture) snapshot_selected<=1;
      if (response_valid && csr_rsp_ready) response_valid<=0;
      if (pending) begin
        pending<=0;
        response_valid<=1;
        response_data<=read_capture;
        response_error<=error_capture;
      end
      if (accept) begin
        pending<=1;
        read_capture<=request_data;
        error_capture<=request_error;
      end
    end
  end
endmodule
