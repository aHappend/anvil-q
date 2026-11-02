module anvil_d1_mem_mux #(
  parameter integer CLIENTS=4,
  localparam integer NC=CLIENTS>0 ? CLIENTS : 1,
  localparam integer SW=NC>1 ? $clog2(NC) : 1
) (
  input wire rst_n, flush,
  input wire [SW-1:0] select_client,
  input wire [NC-1:0] s_req_valid, s_req_write,
  output wire [NC-1:0] s_req_ready,
  input wire [NC*4-1:0] s_req_kind,
  input wire [NC*32-1:0] s_req_layer,
  input wire [NC*3-1:0] s_req_proj,
  input wire [NC*32-1:0] s_req_row, s_req_col, s_req_wdata,
  output wire [NC-1:0] s_rsp_valid,
  input wire [NC-1:0] s_rsp_ready,
  output wire [NC*32-1:0] s_rsp_rdata,
  output wire [NC-1:0] s_rsp_error,
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
  wire enabled=rst_n && !flush && select_client<NC;
  assign c_req_valid=enabled && s_req_valid[select_client];
  assign c_req_write=c_req_valid && s_req_write[select_client];
  assign c_req_kind=c_req_valid ? s_req_kind[select_client*4+:4] : 4'd0;
  assign c_req_layer=c_req_valid ? s_req_layer[select_client*32+:32] : 32'd0;
  assign c_req_proj=c_req_valid ? s_req_proj[select_client*3+:3] : 3'd0;
  assign c_req_row=c_req_valid ? s_req_row[select_client*32+:32] : 32'd0;
  assign c_req_col=c_req_valid ? s_req_col[select_client*32+:32] : 32'd0;
  assign c_req_wdata=c_req_valid ? s_req_wdata[select_client*32+:32] : 32'd0;
  assign c_rsp_ready=enabled && s_rsp_ready[select_client];
  generate
    if (CLIENTS<1 || CLIENTS>16) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: memory mux clients");
    end
    for (genvar n=0;n<NC;n=n+1) begin: routes
      assign s_req_ready[n]=enabled && select_client==n && c_req_ready;
      assign s_rsp_valid[n]=enabled && select_client==n && c_rsp_valid;
      assign s_rsp_error[n]=s_rsp_valid[n] && c_rsp_error;
      assign s_rsp_rdata[n*32+:32]=s_rsp_valid[n] ? c_rsp_rdata : 32'd0;
    end
  endgenerate
endmodule
