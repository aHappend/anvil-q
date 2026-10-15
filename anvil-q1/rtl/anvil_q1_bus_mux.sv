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
  wire [N*137-1:0] c_request;
  wire [136:0] request;
  genvar g;
  assign active=rst_n && select<N;
  assign request=active ? c_request[select*137+:137] : 137'b0;
  assign {mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,
          mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata}=request;
  assign mem_rsp_ready=active ? c_rsp_ready[select] : 0;
  generate for(g=0;g<N;g=g+1) begin: routes
    assign c_request[g*137+:137]=
      {c_req_valid[g],c_req_write[g],c_req_kind[g*4+:4],
       c_req_layer[g*32+:32],c_req_proj[g*3+:3],c_req_row[g*32+:32],
       c_req_col[g*32+:32],c_req_wdata[g*32+:32]};
    assign c_req_ready[g]=active && select==g && mem_req_ready;
    assign c_rsp_valid[g]=active && select==g && mem_rsp_valid;
    assign c_rsp_rdata[g*32+:32]=(active && select==g) ? mem_rsp_rdata : 0;
    assign c_rsp_error[g]=active && select==g && mem_rsp_error;
  end endgenerate
endmodule
