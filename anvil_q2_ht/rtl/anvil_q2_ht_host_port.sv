module anvil_q2_ht_host_port (
  input wire clk, rst_n, inhibit, ddr_ready,
  input wire operation_busy, configuration_valid,
  input wire host_req_valid, host_req_write,
  input wire [32:0] host_req_addr,
  input wire [511:0] host_req_wdata,
  input wire [63:0] host_req_be,
  output wire host_req_ready, host_rsp_valid,
  input wire host_rsp_ready,
  output wire [511:0] host_rsp_rdata,
  output wire host_rsp_error,
  output wire idle, memory_idle, write_accepted,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [32:0] mem_req_addr,
  output wire [511:0] mem_req_wdata,
  output wire [63:0] mem_req_be,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [511:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  localparam [1:0] IDLE=0, REQUEST=1, WAIT_RESPONSE=2, RESPONSE=3;
  reg [1:0] state;
  reg write_request, failed;
  reg [32:0] address;
  reg [511:0] write_data, result;
  reg [63:0] byte_mask;
  wire accepting=host_req_valid && host_req_ready;
  wire forbidden=(|host_req_addr[5:0]) ||
    (host_req_write && configuration_valid);
  assign host_req_ready=rst_n && !inhibit && !operation_busy &&
    ddr_ready && state==IDLE;
  assign host_rsp_valid=rst_n && state==RESPONSE;
  assign host_rsp_rdata=host_rsp_valid ? result : 512'd0;
  assign host_rsp_error=host_rsp_valid && failed;
  assign idle=rst_n && state==IDLE;
  assign memory_idle=rst_n && (state==IDLE || state==RESPONSE);
  assign write_accepted=rst_n && accepting && host_req_write && !forbidden;
  assign mem_req_valid=rst_n && state==REQUEST;
  assign mem_req_write=mem_req_valid && write_request;
  assign mem_req_addr=mem_req_valid ? address : 33'd0;
  assign mem_req_wdata=mem_req_write ? write_data : 512'd0;
  assign mem_req_be=mem_req_valid ?
    (write_request ? byte_mask : {64{1'b1}}) : 64'd0;
  assign mem_rsp_ready=rst_n && state==WAIT_RESPONSE;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; write_request<=0; failed<=0;
      address<=0; write_data<=0; result<=0; byte_mask<=0;
    end else case (state)
      IDLE: if (accepting) begin
        write_request<=host_req_write;
        address<=host_req_addr;
        write_data<=host_req_wdata;
        byte_mask<=host_req_be;
        result<=0;
        failed<=forbidden;
        if (forbidden) state<=RESPONSE;
        else state<=REQUEST;
      end
      REQUEST: if (mem_req_ready) state<=WAIT_RESPONSE;
      WAIT_RESPONSE: if (mem_rsp_valid) begin
        result<=write_request ? 512'd0 : mem_rsp_rdata;
        failed<=mem_rsp_error;
        state<=RESPONSE;
      end
      RESPONSE: if (host_rsp_ready) state<=IDLE;
      default: begin state<=RESPONSE; failed<=1; result<=0; end
    endcase
  end
endmodule
