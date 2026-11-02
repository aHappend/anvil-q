module anvil_d1_mem_port (
  input wire clk, rst_n, flush, issue,
  output wire idle, complete, fault,
  input wire write,
  input wire [3:0] kind,
  input wire [31:0] layer,
  input wire [2:0] proj,
  input wire [31:0] row, col, wdata,
  output wire [31:0] rdata,
  output wire c_req_valid,
  input wire c_req_ready,
  output wire c_req_write,
  output wire [3:0] c_req_kind,
  output wire [31:0] c_req_layer,
  output wire [2:0] c_req_proj,
  output wire [31:0] c_req_row, c_req_col, c_req_wdata,
  input wire c_rsp_valid,
  output wire c_rsp_ready,
  input wire [31:0] c_rsp_rdata,
  input wire c_rsp_error
);
  localparam IDLE=0, REQUEST=1, RESPONSE=2, FAULTED=3;
  reg [1:0] state;
  reg armed, request_write;
  reg [3:0] request_kind;
  reg [2:0] request_proj;
  reg [31:0] request_layer, request_row, request_col, request_data;
  wire enabled=rst_n && armed && !flush;
  wire request_transfer=c_req_valid && c_req_ready;
  wire expected=state==RESPONSE || request_transfer;
  assign idle=enabled && state==IDLE;
  assign c_req_valid=enabled && state==REQUEST;
  assign c_req_write=c_req_valid && request_write;
  assign c_req_kind=c_req_valid ? request_kind : 4'd0;
  assign c_req_layer=c_req_valid ? request_layer : 32'd0;
  assign c_req_proj=c_req_valid ? request_proj : 3'd0;
  assign c_req_row=c_req_valid ? request_row : 32'd0;
  assign c_req_col=c_req_valid ? request_col : 32'd0;
  assign c_req_wdata=c_req_valid ? request_data : 32'd0;
  assign c_rsp_ready=enabled && state!=FAULTED;
  assign complete=c_rsp_valid && c_rsp_ready;
  assign fault=complete && (!expected || c_rsp_error);
  assign rdata=complete ? c_rsp_rdata : 32'd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; request_write<=0; request_kind<=0; request_proj<=0;
      request_layer<=0; request_row<=0; request_col<=0; request_data<=0;
    end else begin
      armed<=1;
      if (flush) state<=IDLE;
      else if (complete) begin
        if (fault) state<=FAULTED;
        else state<=IDLE;
      end else case (state)
        IDLE: if (issue && idle) begin
          request_write<=write; request_kind<=kind; request_layer<=layer;
          request_proj<=proj; request_row<=row; request_col<=col; request_data<=wdata;
          state<=REQUEST;
        end
        REQUEST: if (request_transfer) state<=RESPONSE;
        RESPONSE: state<=RESPONSE;
        FAULTED: state<=FAULTED;
        default: state<=FAULTED;
      endcase
    end
  end
endmodule
