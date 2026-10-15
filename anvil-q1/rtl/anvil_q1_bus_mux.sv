module anvil_q1_bus_mux #(parameter N=2)(
  input wire rst_n, input wire [31:0] select,
  input wire [N-1:0] c_req_valid, output wire [N-1:0] c_req_ready,
  input wire [N-1:0] c_req_write, input wire [N*4-1:0] c_req_kind,
  input wire [N*32-1:0] c_req_layer, input wire [N*3-1:0] c_req_proj,
  input wire [N*32-1:0] c_req_row, c_req_col, c_req_wdata,
  output wire [N-1:0] c_rsp_valid, input wire [N-1:0] c_rsp_ready,
  output wire [N*32-1:0] c_rsp_rdata, output wire [N-1:0] c_rsp_error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  wire active;
  assign active=rst_n && select<N;
  assign mem_req_valid=active ? c_req_valid[select] : 0;
  assign mem_req_write=active ? c_req_write[select] : 0;
  assign mem_req_kind=active ? c_req_kind[select*4+:4] : 0;
  assign mem_req_layer=active ? c_req_layer[select*32+:32] : 0;
  assign mem_req_proj=active ? c_req_proj[select*3+:3] : 0;
  assign mem_req_row=active ? c_req_row[select*32+:32] : 0;
  assign mem_req_col=active ? c_req_col[select*32+:32] : 0;
  assign mem_req_wdata=active ? c_req_wdata[select*32+:32] : 0;
  assign mem_rsp_ready=active ? c_rsp_ready[select] : 0;
  genvar g;
  generate for(g=0;g<N;g=g+1) begin: routes
    assign c_req_ready[g]=active && select==g && mem_req_ready;
    assign c_rsp_valid[g]=active && select==g && mem_rsp_valid;
    assign c_rsp_rdata[g*32+:32]=rst_n ? mem_rsp_rdata : 0;
    assign c_rsp_error[g]=active && select==g && mem_rsp_error;
  end endgenerate
endmodule
