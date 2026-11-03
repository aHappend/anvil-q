module anvil_q3_ht2_ddr_arbiter #(
  parameter CLIENTS=7,
  localparam NC=CLIENTS>=1 && CLIENTS<=16 ? CLIENTS : 1,
  localparam CW=NC>1 ? $clog2(NC) : 1
) (
  input wire clk, rst_n, flush,
  input wire [NC-1:0] c_req_valid, c_req_write,
  output wire [NC-1:0] c_req_ready,
  input wire [NC*33-1:0] c_req_address,
  input wire [NC*512-1:0] c_req_wdata,
  input wire [NC*64-1:0] c_req_byteenable,
  input wire [NC*8-1:0] c_req_burstcount,
  output wire [NC-1:0] c_rsp_valid, c_rsp_error,
  output wire [NC*512-1:0] c_rsp_rdata,
  output wire idle, fault, drain_done,
  output wire [32:0] avm_address,
  output wire avm_read, avm_write,
  output wire [511:0] avm_writedata,
  output wire [63:0] avm_byteenable,
  output wire [7:0] avm_burstcount,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid,
  input wire [1:0] avm_response
);
  generate if (NC!=CLIENTS) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: DDR client count");
    assign c_req_ready=0; assign c_rsp_valid=0; assign c_rsp_error=0;
    assign c_rsp_rdata=0; assign idle=0; assign fault=0; assign drain_done=0;
    assign avm_address=0; assign avm_read=0; assign avm_write=0;
    assign avm_writedata=0; assign avm_byteenable=0; assign avm_burstcount=0;
  end else begin: datapath
    reg pending, outstanding, failed, writing;
    reg [CW-1:0] pointer, owner;
    reg [32:0] address;
    reg [511:0] data;
    reg [63:0] byteenable;
    reg [7:0] beats, remaining;
    integer selected, candidate;
    reg malformed;
    reg [33:0] end_address;
    wire enabled=rst_n && !flush && !failed;
    wire accepted=(avm_read || avm_write) && !avm_waitrequest;
    wire read_accepted=accepted && !writing;
    wire known_return=outstanding || read_accepted;
    wire returned=rst_n && avm_readdatavalid;
    wire [7:0] return_remaining=outstanding ? remaining : beats;
    wire transport_error=avm_response!=0;

    always @* begin
      selected=-1;
      candidate=0;
      end_address=0;
      malformed=0;
      for (integer offset=0;offset<NC;offset=offset+1) begin
        candidate=pointer+offset;
        if (candidate>=NC) candidate=candidate-NC;
        if (selected<0 && c_req_valid[candidate]) selected=candidate;
      end
      if (selected>=0) begin
        end_address={1'b0,c_req_address[selected*33+:33]}+
          ({26'd0,c_req_burstcount[selected*8+:8]}<<6);
        malformed=c_req_address[selected*33+:6]!=0 ||
          c_req_burstcount[selected*8+:8]==0 ||
          c_req_burstcount[selected*8+:8]>16 ||
          (c_req_write[selected] && c_req_burstcount[selected*8+:8]!=1) ||
          end_address>34'h200000000 ||
          ({1'b0,c_req_address[selected*33+:12]}+
            ({5'd0,c_req_burstcount[selected*8+:8]}<<6)>13'd4096);
      end
    end
    assign avm_read=enabled && pending && !writing;
    assign avm_write=enabled && pending && writing;
    assign avm_address=avm_read || avm_write ? address : 33'd0;
    assign avm_writedata=avm_write ? data : 512'd0;
    assign avm_byteenable=avm_read || avm_write ? byteenable : 64'd0;
    assign avm_burstcount=avm_read || avm_write ? beats : 8'd0;
    assign idle=rst_n && !flush && !pending && !outstanding;
    assign drain_done=rst_n && !flush && !pending && !outstanding;
    assign fault=rst_n && !flush && failed;
    for (genvar c=0;c<NC;c=c+1) begin: clients
      assign c_req_ready[c]=accepted && owner==c;
      assign c_rsp_valid[c]=returned && known_return && owner==c;
      assign c_rsp_error[c]=rst_n && !flush &&
        (failed || transport_error ||
         (returned && !known_return));
      assign c_rsp_rdata[c*512+:512]=c_rsp_valid[c] ? avm_readdata : 512'd0;
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        pending<=0; outstanding<=0; failed<=0; writing<=0;
        pointer<=0; owner<=0; address<=0; data<=0;
        byteenable<=0; beats<=0; remaining<=0;
      end else begin
        if (read_accepted) begin outstanding<=1; remaining<=beats; end
        if (returned && known_return) begin
          remaining<=return_remaining-1'b1;
          if (return_remaining==1) outstanding<=0;
        end
        if (flush) begin
          pending<=0; failed<=0; address<=0; data<=0; byteenable<=0; beats<=0;
        end else if (transport_error || (returned && !known_return)) begin
          pending<=0; failed<=1; address<=0; data<=0; byteenable<=0; beats<=0;
        end else if (accepted) begin
          pending<=0; address<=0; data<=0; byteenable<=0; beats<=0;
          pointer<=owner==NC-1 ? {CW{1'b0}} : owner+1'b1;
        end else if (enabled && !pending && !outstanding && selected>=0) begin
          if (malformed) failed<=1;
          else begin
            pending<=1; owner<=CW'(selected);
            address<=c_req_address[selected*33+:33];
            data<=c_req_wdata[selected*512+:512];
            byteenable<=c_req_byteenable[selected*64+:64];
            beats<=c_req_burstcount[selected*8+:8];
            writing<=c_req_write[selected];
          end
        end
      end
    end
  end endgenerate
endmodule
