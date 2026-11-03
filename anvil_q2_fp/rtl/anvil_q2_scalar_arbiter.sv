module anvil_q2_scalar_arbiter #(parameter N=1)(
  input wire clk, rst_n,
  input wire [N-1:0] c_req_valid,
  output wire [N-1:0] c_req_ready,
  input wire [N-1:0] c_req_write,
  input wire [N*4-1:0] c_req_kind,
  input wire [N*32-1:0] c_req_layer,
  input wire [N*3-1:0] c_req_proj,
  input wire [N*32-1:0] c_req_row, c_req_col, c_req_wdata,
  output wire [N-1:0] c_rsp_valid,
  input wire [N-1:0] c_rsp_ready,
  output wire [N*32-1:0] c_rsp_rdata,
  output wire [N-1:0] c_rsp_error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  reg [1:0] state;
  reg [31:0] owner, cursor;
  integer grant, offset, candidate;
  wire req_active=rst_n && state==1;
  wire rsp_active=rst_n && state==2;
  assign mem_req_valid=req_active && c_req_valid[owner];
  assign mem_req_write=req_active ? c_req_write[owner] : 0;
  assign mem_req_kind=req_active ? c_req_kind[owner*4+:4] : 0;
  assign mem_req_layer=req_active ? c_req_layer[owner*32+:32] : 0;
  assign mem_req_proj=req_active ? c_req_proj[owner*3+:3] : 0;
  assign mem_req_row=req_active ? c_req_row[owner*32+:32] : 0;
  assign mem_req_col=req_active ? c_req_col[owner*32+:32] : 0;
  assign mem_req_wdata=req_active ? c_req_wdata[owner*32+:32] : 0;
  assign mem_rsp_ready=rsp_active && c_rsp_ready[owner];
  genvar g;
  generate for(g=0;g<N;g=g+1) begin: clients
    assign c_req_ready[g]=req_active && owner==g && mem_req_ready;
    assign c_rsp_valid[g]=rsp_active && owner==g && mem_rsp_valid;
    assign c_rsp_rdata[g*32+:32]=(rsp_active && owner==g) ? mem_rsp_rdata : 0;
    assign c_rsp_error[g]=rsp_active && owner==g && mem_rsp_error;
  end endgenerate
  always @* begin
    grant=-1;
    candidate=0;
    for(offset=0;offset<N;offset=offset+1) begin
      candidate=cursor+offset;
      if(candidate>=N) candidate=candidate-N;
      if(grant<0 && c_req_valid[candidate]) grant=candidate;
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin state<=0; owner<=0; cursor<=0; end
    else case(state)
      0: if(grant>=0) begin owner<=grant; state<=1; end
      1: if(mem_req_valid && mem_req_ready) state<=2;
      2: if(mem_rsp_valid && mem_rsp_ready) begin
        if(owner==N-1) cursor<=0; else cursor<=owner+1;
        state<=0;
      end
      default: state<=0;
    endcase
  end
endmodule
