module anvil_qn1_client_router (
  input wire clk, rst_n, flush,
  input wire [7:0] client_valid, client_write,
  output wire [7:0] client_ready,
  input wire [31:0] client_kind,
  input wire [23:0] client_proj,
  input wire [255:0] client_layer, client_row, client_col, client_wdata, client_tag,
  output wire [7:0] client_rsp_valid,
  input wire [7:0] client_rsp_ready,
  output wire [255:0] client_rsp_data, client_rsp_tag,
  output wire [7:0] client_rsp_error,
  output wire req_valid,
  input wire req_ready,
  output wire req_write,
  output wire [3:0] req_kind,
  output wire [2:0] req_proj,
  output wire [31:0] req_layer, req_row, req_col, req_wdata, req_tag,
  input wire rsp_valid,
  output wire rsp_ready,
  input wire [31:0] rsp_data, rsp_tag,
  input wire rsp_error,
  output wire error
);
  reg pinned;
  reg [2:0] owner, next_client;
  reg found;
  reg [2:0] selected;
  integer offset, candidate;
  always @* begin
    found=0; selected=0;
    if (pinned) begin found=1; selected=owner; end
    else for (offset=0;offset<8;offset=offset+1) begin
      candidate=32'(next_client)+offset;
      if (candidate>=8) candidate=candidate-8;
      if (!found && client_valid[candidate]) begin
        found=1; selected=3'(candidate);
      end
    end
  end
  wire active=rst_n && !flush;
  wire bad_response=rsp_valid && rsp_tag[31:28]>=8;
  assign error=active && bad_response;
  assign req_valid=active && found && client_valid[selected] && !bad_response;
  assign req_write=req_valid && client_write[selected];
  assign req_kind=req_valid ? client_kind[selected*4+:4] : 4'd0;
  assign req_proj=req_valid ? client_proj[selected*3+:3] : 3'd0;
  assign req_layer=req_valid ? client_layer[selected*32+:32] : 32'd0;
  assign req_row=req_valid ? client_row[selected*32+:32] : 32'd0;
  assign req_col=req_valid ? client_col[selected*32+:32] : 32'd0;
  assign req_wdata=req_valid ? client_wdata[selected*32+:32] : 32'd0;
  assign req_tag=req_valid ? {1'b0,selected,client_tag[selected*32+:28]} : 32'd0;
  assign rsp_ready=active && (bad_response || client_rsp_ready[rsp_tag[30:28]]);
  genvar client;
  generate for (client=0;client<8;client=client+1) begin: clients
    assign client_ready[client]=req_valid && selected==client && req_ready;
    assign client_rsp_valid[client]=active && rsp_valid && !bad_response &&
      rsp_tag[31:28]==client;
    assign client_rsp_data[client*32+:32]=client_rsp_valid[client] ? rsp_data : 32'd0;
    assign client_rsp_tag[client*32+:32]=client_rsp_valid[client] ?
      {4'd0,rsp_tag[27:0]} : 32'd0;
    assign client_rsp_error[client]=client_rsp_valid[client] && rsp_error;
  end endgenerate
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin pinned<=0; owner<=0; next_client<=0; end
    else if (flush) begin pinned<=0; owner<=0; next_client<=0; end
    else if (req_valid) begin
      if (req_ready) begin pinned<=0; next_client<=selected+3'd1; end
      else begin pinned<=1; owner<=selected; end
    end
  end
endmodule
