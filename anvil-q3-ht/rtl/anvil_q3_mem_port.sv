module anvil_q3_mem_port (
  input wire clk, rst_n, flush, issue,
  output wire idle, complete, fault,
  input wire write,
  input wire [3:0] kind,
  input wire [31:0] layer,
  input wire [2:0] proj,
  input wire [31:0] row, col, wdata,
  output wire [31:0] rdata,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  localparam IDLE=0, REQUEST=1, RESPONSE=2, FAULTED=3;
  reg [1:0] state;
  reg complete_reg, fault_reg, request_write;
  reg [3:0] request_kind;
  reg [2:0] request_proj;
  reg [31:0] request_layer, request_row, request_col, request_data, response_data;
  wire enabled=rst_n && !flush;
  wire request_transfer=mem_req_valid && mem_req_ready;
  wire expected_response=state==RESPONSE || (state==REQUEST && request_transfer);

  assign idle=enabled && state==IDLE;
  assign complete=enabled && complete_reg;
  assign fault=complete && fault_reg;
  assign rdata=enabled ? response_data : 32'd0;
  assign mem_req_valid=enabled && state==REQUEST;
  assign mem_req_write=mem_req_valid && request_write;
  assign mem_req_kind=mem_req_valid ? request_kind : 4'd0;
  assign mem_req_layer=mem_req_valid ? request_layer : 32'd0;
  assign mem_req_proj=mem_req_valid ? request_proj : 3'd0;
  assign mem_req_row=mem_req_valid ? request_row : 32'd0;
  assign mem_req_col=mem_req_valid ? request_col : 32'd0;
  assign mem_req_wdata=mem_req_valid ? request_data : 32'd0;
  assign mem_rsp_ready=enabled && state!=FAULTED;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; complete_reg<=0; fault_reg<=0;
      request_write<=0; request_kind<=0; request_proj<=0;
      request_layer<=0; request_row<=0; request_col<=0; request_data<=0;
      response_data<=0;
    end else if (flush) begin
      state<=IDLE; complete_reg<=0; fault_reg<=0; response_data<=0;
    end else begin
      complete_reg<=0;
      fault_reg<=0;
      if (mem_rsp_valid && mem_rsp_ready) begin
        complete_reg<=1;
        fault_reg<=!expected_response || mem_rsp_error;
        response_data<=mem_rsp_rdata;
        if (!expected_response || mem_rsp_error) state<=FAULTED;
        else state<=IDLE;
      end else case (state)
        IDLE: if (issue) begin
          request_write<=write; request_kind<=kind; request_layer<=layer;
          request_proj<=proj; request_row<=row; request_col<=col;
          request_data<=wdata;
          state<=REQUEST;
        end
        REQUEST: if (mem_req_ready) state<=RESPONSE;
        RESPONSE: state<=RESPONSE;
        FAULTED: state<=FAULTED;
        default: begin state<=FAULTED; complete_reg<=1; fault_reg<=1; end
      endcase
    end
  end
endmodule
