module anvil_q4_fp_channel_mux #(
  parameter integer CLIENTS=2
) (
  input wire clk, rst_n, flush,
  output wire idle,
  input wire [17*CLIENTS-1:0] c_req_valid, c_req_write,
  output wire [17*CLIENTS-1:0] c_req_ready,
  input wire [68*CLIENTS-1:0] c_req_kind,
  input wire [51*CLIENTS-1:0] c_req_proj,
  input wire [544*CLIENTS-1:0] c_req_layer,c_req_row,c_req_col,c_req_wdata,c_req_stride,
  output wire [17*CLIENTS-1:0] c_rsp_valid,c_rsp_error,
  input wire [17*CLIENTS-1:0] c_rsp_ready,
  output wire [544*CLIENTS-1:0] c_rsp_rdata,
  output wire [16:0] mem_req_valid,mem_req_write,
  input wire [16:0] mem_req_ready,
  output wire [67:0] mem_req_kind,
  output wire [50:0] mem_req_proj,
  output wire [543:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata,mem_req_stride,
  input wire [16:0] mem_rsp_valid,mem_rsp_error,
  output wire [16:0] mem_rsp_ready,
  input wire [543:0] mem_rsp_rdata
);
  wire [16:0] channel_idle;
  assign idle=rst_n && !flush && &channel_idle;
  for (genvar n=0;n<17;n=n+1) begin : channels
    wire [CLIENTS-1:0] req_valid,req_write,req_ready,rsp_valid,rsp_ready,rsp_error;
    wire [4*CLIENTS-1:0] req_kind;
    wire [3*CLIENTS-1:0] req_proj;
    wire [32*CLIENTS-1:0] req_layer,req_row,req_col,req_data,req_stride,rsp_data;
    for (genvar c=0;c<CLIENTS;c=c+1) begin : clients
      assign req_valid[c]=c_req_valid[c*17+n];
      assign req_write[c]=c_req_write[c*17+n];
      assign c_req_ready[c*17+n]=req_ready[c];
      assign req_kind[c*4+:4]=c_req_kind[c*68+n*4+:4];
      assign req_proj[c*3+:3]=c_req_proj[c*51+n*3+:3];
      assign req_layer[c*32+:32]=c_req_layer[c*544+n*32+:32];
      assign req_row[c*32+:32]=c_req_row[c*544+n*32+:32];
      assign req_col[c*32+:32]=c_req_col[c*544+n*32+:32];
      assign req_data[c*32+:32]=c_req_wdata[c*544+n*32+:32];
      assign req_stride[c*32+:32]=c_req_stride[c*544+n*32+:32];
      assign c_rsp_valid[c*17+n]=rsp_valid[c];
      assign c_rsp_error[c*17+n]=rsp_error[c];
      assign rsp_ready[c]=c_rsp_ready[c*17+n];
      assign c_rsp_rdata[c*544+n*32+:32]=rsp_data[c*32+:32];
    end
    anvil_q4_fp_mem_arbiter #(.CLIENTS(CLIENTS)) ownership (
      .clk(clk),.rst_n(rst_n),.flush(flush),.idle(channel_idle[n]),
      .c_req_valid(req_valid),.c_req_write(req_write),.c_req_ready(req_ready),
      .c_req_kind(req_kind),.c_req_proj(req_proj),.c_req_layer(req_layer),
      .c_req_row(req_row),.c_req_col(req_col),.c_req_wdata(req_data),.c_req_stride(req_stride),
      .c_rsp_valid(rsp_valid),.c_rsp_error(rsp_error),.c_rsp_ready(rsp_ready),
      .c_rsp_rdata(rsp_data),
      .mem_req_valid(mem_req_valid[n]),.mem_req_ready(mem_req_ready[n]),
      .mem_req_write(mem_req_write[n]),.mem_req_kind(mem_req_kind[n*4+:4]),
      .mem_req_proj(mem_req_proj[n*3+:3]),.mem_req_layer(mem_req_layer[n*32+:32]),
      .mem_req_row(mem_req_row[n*32+:32]),.mem_req_col(mem_req_col[n*32+:32]),
      .mem_req_wdata(mem_req_wdata[n*32+:32]),.mem_req_stride(mem_req_stride[n*32+:32]),
      .mem_rsp_valid(mem_rsp_valid[n]),.mem_rsp_error(mem_rsp_error[n]),
      .mem_rsp_ready(mem_rsp_ready[n]),.mem_rsp_rdata(mem_rsp_rdata[n*32+:32])
    );
  end
endmodule
