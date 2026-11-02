module anvil_d1_bank_scheduler #(
  parameter integer BANKS=8, CLIENTS=7, QUEUE_DEPTH=3,
  localparam integer SB=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) ? BANKS : 1,
  localparam integer SC=(CLIENTS>=1 && CLIENTS<=32) ? CLIENTS : 1
) (
  input wire clk, rst_n, flush,
  output wire idle, drain_done, fault,
  input wire [SC-1:0] c_req_valid, c_req_write,
  output wire [SC-1:0] c_req_ready,
  input wire [SC*4-1:0] c_req_kind,
  input wire [SC*32-1:0] c_req_layer,
  input wire [SC*3-1:0] c_req_proj,
  input wire [SC*32-1:0] c_req_row, c_req_col, c_req_wdata,
  output wire [SC-1:0] c_rsp_valid, c_rsp_error,
  input wire [SC-1:0] c_rsp_ready,
  output wire [SC*32-1:0] c_rsp_rdata,
  output wire [SB-1:0] mem_req_valid, mem_req_write,
  input wire [SB-1:0] mem_req_ready,
  output wire [SB*4-1:0] mem_req_kind,
  output wire [SB*32-1:0] mem_req_layer,
  output wire [SB*3-1:0] mem_req_proj,
  output wire [SB*32-1:0] mem_req_row, mem_req_col, mem_req_wdata,
  output wire [SB*64-1:0] mem_req_tag,
  input wire [SB-1:0] mem_rsp_valid, mem_rsp_error,
  output wire [SB-1:0] mem_rsp_ready,
  input wire [SB*32-1:0] mem_rsp_rdata,
  input wire [SB*64-1:0] mem_rsp_tag
);
  wire [SB-1:0] raw_valid, raw_write;
  wire [SB*4-1:0] raw_kind;
  wire [SB*32-1:0] raw_layer, raw_row, raw_col, raw_wdata;
  wire [SB*3-1:0] raw_proj;
  wire [SB*64-1:0] raw_tag;
  wire request_enable=rst_n && !flush;
  anvil_q3_bank_scheduler #(.BANKS(BANKS),.CLIENTS(CLIENTS),.QUEUE_DEPTH(QUEUE_DEPTH)) scheduler (
    .clk(clk),.rst_n(rst_n),.flush(flush),.idle(idle),.drain_done(drain_done),.fault(fault),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
    .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
    .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
    .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
    .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error),
    .mem_req_valid(raw_valid),.mem_req_ready(mem_req_ready & {SB{request_enable}}),
    .mem_req_write(raw_write),.mem_req_kind(raw_kind),.mem_req_layer(raw_layer),
    .mem_req_proj(raw_proj),.mem_req_row(raw_row),.mem_req_col(raw_col),
    .mem_req_wdata(raw_wdata),.mem_req_tag(raw_tag),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag)
  );
  generate for (genvar b=0;b<SB;b=b+1) begin: annul_boundary
    assign mem_req_valid[b]=request_enable && raw_valid[b];
    assign mem_req_write[b]=mem_req_valid[b] && raw_write[b];
    assign mem_req_kind[b*4+:4]=mem_req_valid[b] ? raw_kind[b*4+:4] : 4'd0;
    assign mem_req_layer[b*32+:32]=mem_req_valid[b] ? raw_layer[b*32+:32] : 32'd0;
    assign mem_req_proj[b*3+:3]=mem_req_valid[b] ? raw_proj[b*3+:3] : 3'd0;
    assign mem_req_row[b*32+:32]=mem_req_valid[b] ? raw_row[b*32+:32] : 32'd0;
    assign mem_req_col[b*32+:32]=mem_req_valid[b] ? raw_col[b*32+:32] : 32'd0;
    assign mem_req_wdata[b*32+:32]=mem_req_valid[b] ? raw_wdata[b*32+:32] : 32'd0;
    assign mem_req_tag[b*64+:64]=mem_req_valid[b] ? raw_tag[b*64+:64] : 64'd0;
  end endgenerate
endmodule
