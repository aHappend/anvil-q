module anvil_q3_ht_host_loader (
  input wire clk, rst_n,
  input wire inference_idle, memory_idle, ddr_cal_ready, model_commit,
  output wire model_ready, busy, fault,
  input wire host_req_valid, host_req_write,
  input wire [32:0] host_req_address,
  input wire [511:0] host_req_wdata,
  input wire [63:0] host_req_byteenable,
  output wire host_req_ready,
  output wire host_rsp_valid,
  input wire host_rsp_ready,
  output wire [511:0] host_rsp_rdata,
  output wire host_rsp_error,
  output wire memory_req_valid,
  input wire memory_req_ready,
  output wire memory_req_write,
  output wire [32:0] memory_req_address,
  output wire [511:0] memory_req_wdata,
  output wire [63:0] memory_req_byteenable,
  input wire memory_rsp_valid,
  input wire [511:0] memory_rsp_rdata,
  input wire memory_rsp_error
);
  localparam IDLE=2'd0, REQUEST=2'd1, READ_WAIT=2'd2, RESPONSE=2'd3;
  reg [1:0] state;
  reg committed, failed, request_write, response_error;
  reg [32:0] address;
  reg [511:0] write_data, response_data;
  reg [63:0] byteenable;
  wire host_transfer=host_req_valid && host_req_ready;
  wire memory_transfer=memory_req_valid && memory_req_ready;
  wire expected_read=state==READ_WAIT ||
    (memory_transfer && !request_write);
  wire bad_commit=model_commit &&
    (!ddr_cal_ready || !inference_idle || !memory_idle ||
     (state!=IDLE && state!=RESPONSE));
  wire unexpected_response=memory_rsp_valid && !expected_read;

  assign host_req_ready=rst_n && !failed && ddr_cal_ready && inference_idle &&
    memory_idle && state==IDLE;
  assign host_rsp_valid=rst_n && state==RESPONSE;
  assign host_rsp_rdata=host_rsp_valid ? response_data : 512'd0;
  assign host_rsp_error=host_rsp_valid && response_error;
  assign model_ready=rst_n && committed && !failed;
  assign busy=rst_n && state!=IDLE;
  assign fault=rst_n && failed;
  assign memory_req_valid=rst_n && state==REQUEST;
  assign memory_req_write=memory_req_valid && request_write;
  assign memory_req_address=memory_req_valid ? address : 33'd0;
  assign memory_req_wdata=memory_req_valid && request_write ? write_data : 512'd0;
  assign memory_req_byteenable=memory_req_valid ?
    (request_write ? byteenable : 64'hffffffffffffffff) : 64'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; committed<=0; failed<=0; request_write<=0;
      address<=0; write_data<=0; byteenable<=0;
      response_data<=0; response_error<=0;
    end else begin
      if (bad_commit || unexpected_response) begin
        failed<=1;
        committed<=0;
      end else if (model_commit) committed<=1;

      case (state)
        IDLE: if (host_transfer) begin
          request_write<=host_req_write;
          address<=host_req_address;
          write_data<=host_req_wdata;
          byteenable<=host_req_byteenable;
          response_data<=0;
          response_error<=0;
          if (host_req_write) committed<=0;
          if (host_req_address[5:0]!=0) begin
            response_error<=1;
            state<=RESPONSE;
          end else state<=REQUEST;
        end
        REQUEST: if (memory_transfer) begin
          if (request_write) begin
            response_data<=0;
            response_error<=0;
            state<=RESPONSE;
          end else if (memory_rsp_valid) begin
            response_data<=memory_rsp_rdata;
            response_error<=memory_rsp_error;
            state<=RESPONSE;
          end else state<=READ_WAIT;
        end
        READ_WAIT: if (memory_rsp_valid) begin
          response_data<=memory_rsp_rdata;
          response_error<=memory_rsp_error;
          state<=RESPONSE;
        end
        RESPONSE: if (host_rsp_ready) begin
          response_data<=0;
          response_error<=0;
          state<=IDLE;
        end
        default: begin failed<=1; committed<=0; state<=IDLE; end
      endcase
    end
  end
endmodule
