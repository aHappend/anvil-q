module anvil_q4_fp_mem_arbiter #(
  parameter integer CLIENTS=2,
  localparam integer SC=(CLIENTS>=1 && CLIENTS<=17) ? CLIENTS : 1,
  localparam integer CW=SC>1 ? $clog2(SC) : 1
) (
  input wire clk, rst_n, flush,
  output wire idle,
  input wire [SC-1:0] c_req_valid, c_req_write,
  output wire [SC-1:0] c_req_ready,
  input wire [4*SC-1:0] c_req_kind,
  input wire [3*SC-1:0] c_req_proj,
  input wire [32*SC-1:0] c_req_layer, c_req_row, c_req_col, c_req_wdata, c_req_stride,
  output wire [SC-1:0] c_rsp_valid, c_rsp_error,
  input wire [SC-1:0] c_rsp_ready,
  output wire [32*SC-1:0] c_rsp_rdata,
  output wire mem_req_valid, mem_req_write,
  input wire mem_req_ready,
  output wire [3:0] mem_req_kind,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_layer, mem_req_row, mem_req_col, mem_req_wdata, mem_req_stride,
  input wire mem_rsp_valid, mem_rsp_error,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata
);
  generate if (CLIENTS!=SC) begin : invalid_parameters
    initial $fatal(1,"PARAMETER ERROR: native memory arbiter clients");
    assign idle=0;
    assign c_req_ready=0; assign c_rsp_valid=0; assign c_rsp_error=0;
    assign c_rsp_rdata=0; assign mem_req_valid=0; assign mem_req_write=0;
    assign mem_req_kind=0; assign mem_req_proj=0; assign mem_req_layer=0;
    assign mem_req_row=0; assign mem_req_col=0; assign mem_req_wdata=0;
    assign mem_req_stride=0; assign mem_rsp_ready=0;
  end else begin : legal
    localparam [1:0] PICK=0,CAPTURE=1,REQUEST=2,RESPONSE=3;
    reg [1:0] state;
    reg [CW-1:0] owner, cursor;
    reg write_register;
    reg [3:0] kind_register;
    reg [2:0] proj_register;
    reg [31:0] layer_register,row_register,col_register,data_register,stride_register;
    reg found;
    reg [CW-1:0] selected;
    integer i, index;
    always @* begin
      found=0; selected=0; index=0;
      for (i=0;i<SC;i=i+1) begin
        index=i+integer'(cursor);
        if (index>=SC) index=index-SC;
        if (!found && c_req_valid[index]) begin found=1; selected=CW'(index); end
      end
    end
    assign idle=rst_n && !flush && state==PICK && !found;
    assign mem_req_valid=rst_n && !flush && state==REQUEST;
    assign mem_req_write=mem_req_valid && write_register;
    assign mem_req_kind=mem_req_valid ? kind_register : 4'd0;
    assign mem_req_proj=mem_req_valid ? proj_register : 3'd0;
    assign mem_req_layer=mem_req_valid ? layer_register : 32'd0;
    assign mem_req_row=mem_req_valid ? row_register : 32'd0;
    assign mem_req_col=mem_req_valid ? col_register : 32'd0;
    assign mem_req_wdata=mem_req_valid ? data_register : 32'd0;
    assign mem_req_stride=mem_req_valid ? stride_register : 32'd0;
    assign mem_rsp_ready=rst_n && !flush && state==RESPONSE && c_rsp_ready[owner];
    for (genvar n=0;n<SC;n=n+1) begin : clients
      assign c_req_ready[n]=rst_n && !flush && state==CAPTURE && owner==n;
      assign c_rsp_valid[n]=rst_n && !flush && state==RESPONSE && owner==n && mem_rsp_valid;
      assign c_rsp_error[n]=c_rsp_valid[n] && mem_rsp_error;
      assign c_rsp_rdata[n*32+:32]=c_rsp_valid[n] ? mem_rsp_rdata : 32'd0;
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=PICK; owner<=0; cursor<=0; write_register<=0;
        kind_register<=0; proj_register<=0; layer_register<=0;
        row_register<=0; col_register<=0; data_register<=0; stride_register<=0;
      end else if (flush) begin state<=PICK; owner<=0; cursor<=0; end
      else case (state)
        PICK: if (found) begin owner<=selected; state<=CAPTURE; end
        CAPTURE: if (c_req_valid[owner]) begin
          write_register<=c_req_write[owner]; kind_register<=c_req_kind[owner*4+:4];
          proj_register<=c_req_proj[owner*3+:3]; layer_register<=c_req_layer[owner*32+:32];
          row_register<=c_req_row[owner*32+:32]; col_register<=c_req_col[owner*32+:32];
          data_register<=c_req_wdata[owner*32+:32]; stride_register<=c_req_stride[owner*32+:32];
          state<=REQUEST;
        end
        REQUEST: if (mem_req_ready) state<=RESPONSE;
        RESPONSE: if (mem_rsp_valid && mem_rsp_ready) begin
          if (owner==SC-1) cursor<=0; else cursor<=owner+1'b1;
          state<=PICK;
        end
        default: state<=PICK;
      endcase
    end
  end endgenerate
endmodule
