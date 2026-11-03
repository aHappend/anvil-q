module anvil_q3_ht_scratch_arbiter #(
  parameter CLIENTS=3,
  localparam NC=CLIENTS>=1 && CLIENTS<=16 ? CLIENTS : 1,
  localparam CW=NC>1 ? $clog2(NC) : 1
) (
  input wire clk, rst_n, flush,
  input wire [NC-1:0] c_req_valid, c_req_write,
  output wire [NC-1:0] c_req_ready,
  input wire [NC*32-1:0] c_req_slot, c_req_index, c_req_wdata,
  output wire [NC-1:0] c_rsp_valid, c_rsp_error,
  input wire [NC-1:0] c_rsp_ready,
  output wire [NC*32-1:0] c_rsp_rdata,
  output wire idle, fault,
  output wire req_valid, req_write,
  input wire req_ready,
  output wire [31:0] req_slot, req_index, req_wdata,
  input wire rsp_valid, rsp_error,
  output wire rsp_ready,
  input wire [31:0] rsp_rdata
);
  reg pending, waiting, failed, write_command;
  reg [CW-1:0] owner, pointer;
  reg [31:0] slot, index, write_data;
  integer offset, candidate, selected;
  wire running=rst_n && CLIENTS==NC && !flush && !failed;
  wire accepted=req_valid && req_ready;
  wire response_transfer=rsp_valid && rsp_ready;

  generate if (CLIENTS!=NC) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: scratch arbiter clients");
  end endgenerate
  always @* begin
    selected=-1;
    candidate=0;
    for (offset=0;offset<NC;offset=offset+1) begin
      candidate=pointer+offset;
      if (candidate>=NC) candidate=candidate-NC;
      if (selected<0 && c_req_valid[candidate]) selected=candidate;
    end
  end
  assign req_valid=running && pending;
  assign req_write=req_valid && write_command;
  assign req_slot=req_valid ? slot : 32'd0;
  assign req_index=req_valid ? index : 32'd0;
  assign req_wdata=req_write ? write_data : 32'd0;
  assign rsp_ready=running && waiting && c_rsp_ready[owner];
  assign idle=running && !pending && !waiting;
  assign fault=rst_n && failed;
  genvar client;
  generate for (client=0;client<NC;client=client+1) begin: clients
    assign c_req_ready[client]=accepted && owner==client;
    assign c_rsp_valid[client]=running && waiting && owner==client && rsp_valid;
    assign c_rsp_error[client]=c_rsp_valid[client] && rsp_error;
    assign c_rsp_rdata[client*32+:32]=
      c_rsp_valid[client] && !rsp_error ? rsp_rdata : 32'd0;
  end endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pending<=0; waiting<=0; failed<=0; write_command<=0;
      owner<=0; pointer<=0; slot<=0; index<=0; write_data<=0;
    end else if (flush) begin
      pending<=0; waiting<=0; failed<=0; pointer<=0;
    end else if (!failed) begin
      if (rsp_valid && !waiting) failed<=1;
      if (!pending && !waiting && selected>=0) begin
        pending<=1;
        owner<=CW'(selected);
        write_command<=c_req_write[selected];
        slot<=c_req_slot[selected*32+:32];
        index<=c_req_index[selected*32+:32];
        write_data<=c_req_wdata[selected*32+:32];
      end
      if (accepted) begin pending<=0; waiting<=1; end
      if (response_transfer) begin
        waiting<=0;
        pointer<=owner==NC-1 ? 0 : owner+1'b1;
      end
    end
  end
endmodule
