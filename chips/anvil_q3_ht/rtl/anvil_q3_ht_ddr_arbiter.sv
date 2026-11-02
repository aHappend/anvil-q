module anvil_q3_ht_ddr_arbiter #(
  parameter CLIENTS=4, READ_SLOTS=8,
  localparam NC=CLIENTS>=1 && CLIENTS<=16 ? CLIENTS : 1,
  localparam NS=READ_SLOTS>=1 && READ_SLOTS<=64 ? READ_SLOTS : 1,
  localparam CW=NC>1 ? $clog2(NC) : 1,
  localparam SW=NS>1 ? $clog2(NS) : 1
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
  output wire idle, fault,
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
  localparam LEGAL=NC==CLIENTS && NS==READ_SLOTS;
  reg failed, pending, write_command;
  reg [CW-1:0] pointer, owner;
  reg [32:0] address;
  reg [511:0] write_data;
  reg [63:0] byteenable;
  reg [7:0] beats;
  reg [SW-1:0] head, tail;
  reg [31:0] count;
  (* nomem2reg *) reg [CW-1:0] read_owner [0:NS-1];
  (* nomem2reg *) reg [7:0] remaining [0:NS-1];
  integer offset, candidate, selected;
  reg [32:0] selected_address;
  reg [7:0] selected_beats;
  reg selected_write, malformed;
  reg [33:0] selected_end;
  wire accepted=rst_n && pending && !avm_waitrequest;
  wire read_accepted=accepted && !write_command;
  wire returned=rst_n && avm_readdatavalid;
  wire known_return=count!=0 || read_accepted;
  wire [CW-1:0] response_owner=count!=0 ? read_owner[head] : owner;
  wire [7:0] response_remaining=count!=0 ? remaining[head] : beats;
  wire pop=returned && known_return && response_remaining==1;
  wire take_selection=rst_n && LEGAL && !flush && !failed &&
    !pending && selected>=0;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: DDR arbiter clients or read slots");
  end endgenerate

  always @* begin
    selected=-1;
    candidate=0;
    selected_address=0;
    selected_beats=0;
    selected_write=0;
    selected_end=0;
    malformed=0;
    for (offset=0;offset<NC;offset=offset+1) begin
      candidate=pointer+offset;
      if (candidate>=NC) candidate=candidate-NC;
      if (selected<0 && c_req_valid[candidate] &&
          (c_req_write[candidate] || count<NS))
        selected=candidate;
    end
    if (selected>=0) begin
      selected_address=c_req_address[selected*33+:33];
      selected_beats=c_req_burstcount[selected*8+:8];
      selected_write=c_req_write[selected];
      selected_end={1'b0,selected_address}+({26'd0,selected_beats}<<6);
      malformed=selected_address[5:0]!=0 || selected_beats==0 ||
        selected_beats>16 || selected_end>34'h200000000 ||
        ({1'b0,selected_address[11:0]}+({5'd0,selected_beats}<<6)>13'd4096) ||
        (selected_write && selected_beats!=1);
    end
  end

  assign avm_read=rst_n && pending && !write_command;
  assign avm_write=rst_n && pending && write_command;
  assign avm_address=pending && rst_n ? address : 33'd0;
  assign avm_writedata=avm_write ? write_data : 512'd0;
  assign avm_byteenable=pending && rst_n ? byteenable : 64'd0;
  assign avm_burstcount=pending && rst_n ? beats : 8'd0;
  assign idle=rst_n && !pending && count==0;
  assign fault=rst_n && failed;
  genvar client;
  generate for (client=0;client<NC;client=client+1) begin: clients
    assign c_req_ready[client]=accepted && owner==client;
    assign c_rsp_valid[client]=returned && known_return && response_owner==client;
    assign c_rsp_error[client]=c_rsp_valid[client] && avm_response!=0;
    assign c_rsp_rdata[client*512+:512]=c_rsp_valid[client] ? avm_readdata : 512'd0;
  end endgenerate

  always @(posedge clk) begin
    if (read_accepted) begin
      read_owner[tail]<=owner;
      remaining[tail]<=returned && count==0 ? beats-1'b1 : beats;
    end
    if (returned && count!=0 && !pop)
      remaining[head]<=remaining[head]-1'b1;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      failed<=0; pending<=0; write_command<=0; pointer<=0; owner<=0;
      address<=0; write_data<=0; byteenable<=0; beats<=0;
      head<=0; tail<=0; count<=0;
    end else begin
      if (flush) failed<=0;
      if (returned && (!known_return || avm_response!=0)) failed<=1;
      if (accepted) begin
        pending<=0;
        pointer<=owner==NC-1 ? 0 : owner+1'b1;
      end
      if (take_selection) begin
        if (malformed) failed<=1;
        else begin
          pending<=1;
          owner<=CW'(selected);
          address<=selected_address;
          beats<=selected_beats;
          write_command<=selected_write;
          write_data<=c_req_wdata[selected*512+:512];
          byteenable<=c_req_byteenable[selected*64+:64];
        end
      end
      case ({read_accepted,pop})
        2'b10: count<=count+1'b1;
        2'b01: count<=count-1'b1;
        default: count<=count;
      endcase
      if (read_accepted) tail<=tail==NS-1 ? 0 : tail+1'b1;
      if (pop) head<=head==NS-1 ? 0 : head+1'b1;
    end
  end
endmodule
