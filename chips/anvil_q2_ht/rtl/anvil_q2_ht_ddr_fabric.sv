module anvil_q2_ht_ddr_fabric #(
  parameter CLIENTS=3,
  parameter READ_OUTSTANDING=8,
  parameter CP=(CLIENTS>=1 && CLIENTS<=4) ? CLIENTS : 1
) (
  input wire clk, rst_n, ddr_ready, ddr_fault,
  input wire [32:0] p_address,
  input wire p_read,
  input wire [4:0] p_burstcount,
  output wire p_waitrequest,
  output wire [511:0] p_readdata,
  output wire p_readdatavalid,
  output wire [1:0] p_response,
  input wire [32:0] k_address,
  input wire k_read,
  input wire [4:0] k_burstcount,
  output wire k_waitrequest,
  output wire [511:0] k_readdata,
  output wire k_readdatavalid,
  output wire [1:0] k_response,
  input wire [CP-1:0] c_req_valid, c_req_write,
  output wire [CP-1:0] c_req_ready,
  input wire [CP*33-1:0] c_req_addr,
  input wire [CP*512-1:0] c_req_wdata,
  input wire [CP*64-1:0] c_req_be,
  output wire [CP-1:0] c_rsp_valid,
  input wire [CP-1:0] c_rsp_ready,
  output wire [CP*512-1:0] c_rsp_rdata,
  output wire [CP-1:0] c_rsp_error,
  output wire idle, fault,
  output wire [32:0] avm_address,
  output wire avm_read, avm_write,
  output wire [511:0] avm_writedata,
  output wire [63:0] avm_byteenable,
  output wire [4:0] avm_burstcount,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid, avm_writeresponsevalid,
  input wire [1:0] avm_response
);
  localparam LEGAL=CLIENTS>=1 && CLIENTS<=4 && CP==CLIENTS &&
    READ_OUTSTANDING>=1 && READ_OUTSTANDING<=16;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT PARAMETER ERROR: DDR fabric depths");
    assign p_waitrequest=0; assign p_readdata=0;
    assign p_readdatavalid=0; assign p_response=0;
    assign k_waitrequest=0; assign k_readdata=0;
    assign k_readdatavalid=0; assign k_response=0;
    assign c_req_ready=0; assign c_rsp_valid=0;
    assign c_rsp_rdata=0; assign c_rsp_error=0; assign idle=0; assign fault=0;
    assign avm_address=0; assign avm_read=0; assign avm_write=0;
    assign avm_writedata=0; assign avm_byteenable=0; assign avm_burstcount=0;
  end else begin: implementation
    localparam CLIENT_COUNT=CLIENTS+2;
    localparam OW=$clog2(CLIENT_COUNT);
    localparam PW=READ_OUTSTANDING<=1 ? 1 : $clog2(READ_OUTSTANDING);
    reg held, held_write;
    reg [OW-1:0] held_owner;
    reg [32:0] held_address;
    reg [4:0] held_count;
    reg [511:0] held_data;
    reg [63:0] held_mask;
    reg [OW-1:0] next_owner;
    reg [OW-1:0] read_owner [0:READ_OUTSTANDING-1];
    reg [4:0] read_count [0:READ_OUTSTANDING-1];
    reg [PW-1:0] read_head, read_tail;
    reg [4:0] reads_outstanding, read_beat;
    reg write_pending;
    reg [OW-1:0] write_owner;
    reg [CLIENTS-1:0] client_busy, response_valid, response_error;
    reg [511:0] response_data [0:CLIENTS-1];
    reg fault_pulse;
    reg selection_valid;
    reg [OW-1:0] selection;
    reg [CLIENTS-1:0] ready;
    integer offset, candidate, i;
    genvar client;
    wire command_accept=held && !avm_waitrequest;
    wire read_push=command_accept && !held_write;
    wire read_return=avm_readdatavalid && reads_outstanding!=0;
    wire read_pop=read_return && read_beat+5'd1==read_count[read_head];
    wire write_return=avm_writeresponsevalid && write_pending;
    wire read_credit=reads_outstanding<READ_OUTSTANDING;
    wire capture=rst_n && !held && ddr_ready && selection_valid;
    wire [OW-1:0] returning_owner=read_owner[read_head];
    wire [5:0] p_last_offset={1'b0,p_address[11:6]}+
      {1'b0,p_burstcount}-6'd1;
    wire p_malformed=(|p_address[5:0]) || p_burstcount==0 ||
      p_burstcount>16 || p_last_offset<{1'b0,p_address[11:6]};
    wire [5:0] k_last_offset={1'b0,k_address[11:6]}+
      {1'b0,k_burstcount}-6'd1;
    wire k_malformed=(|k_address[5:0]) || k_burstcount==0 ||
      k_burstcount>16 || k_last_offset<{1'b0,k_address[11:6]};

    always @* begin
      selection_valid=0;
      selection=0;
      candidate=0;
      for (offset=0; offset<CLIENT_COUNT; offset=offset+1) begin
        candidate=next_owner+offset;
        if (candidate>=CLIENT_COUNT) candidate=candidate-CLIENT_COUNT;
        if (!selection_valid) begin
          if (candidate==0) begin
            if (p_read && !p_malformed && read_credit) begin
              selection=0;
              selection_valid=1;
            end
          end else if (candidate==1) begin
            if (k_read && !k_malformed && read_credit) begin
              selection=1;
              selection_valid=1;
            end
          end else if (c_req_valid[candidate-2] && !client_busy[candidate-2] &&
              (c_req_write[candidate-2] ? !write_pending : read_credit)) begin
            selection=OW'(candidate);
            selection_valid=1;
          end
        end
      end
      ready=0;
      if (capture && selection>=2) ready[selection-2]=1;
    end

    // Read-client acceptance reserves a private unbackpressurable response slot.
    assign c_req_ready=rst_n ? ready : {CLIENTS{1'b0}};
    assign p_waitrequest=rst_n && !(capture && selection==0);
    assign p_readdatavalid=rst_n && read_return && returning_owner==0;
    assign p_readdata=p_readdatavalid ? avm_readdata : 512'd0;
    assign p_response=p_readdatavalid ? avm_response : 2'd0;
    assign k_waitrequest=rst_n && !(capture && selection==1);
    assign k_readdatavalid=rst_n && read_return && returning_owner==1;
    assign k_readdata=k_readdatavalid ? avm_readdata : 512'd0;
    assign k_response=k_readdatavalid ? avm_response : 2'd0;
    for (client=0; client<CLIENTS; client=client+1) begin: responses
      assign c_rsp_valid[client]=rst_n && response_valid[client];
      assign c_rsp_rdata[client*512+:512]=c_rsp_valid[client] ?
        response_data[client] : 512'd0;
      assign c_rsp_error[client]=c_rsp_valid[client] && response_error[client];
    end
    assign avm_read=rst_n && held && !held_write;
    assign avm_write=rst_n && held && held_write;
    assign avm_address=rst_n && held ? held_address : 33'd0;
    assign avm_burstcount=rst_n && held ? held_count : 5'd0;
    assign avm_writedata=avm_write ? held_data : 512'd0;
    assign avm_byteenable=rst_n && held ? held_mask : 64'd0;
    assign idle=rst_n && !held && reads_outstanding==0 && !write_pending &&
      !(|client_busy) && !(|response_valid);
    assign fault=rst_n && fault_pulse;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        held<=0; held_write<=0; held_owner<=0; held_address<=0;
        held_count<=0; held_data<=0; held_mask<=0; next_owner<=0;
        read_head<=0; read_tail<=0; reads_outstanding<=0; read_beat<=0;
        write_pending<=0; write_owner<=0; client_busy<=0;
        response_valid<=0; response_error<=0; fault_pulse<=0;
        for (i=0; i<READ_OUTSTANDING; i=i+1) begin
          read_owner[i]<=0; read_count[i]<=0;
        end
        for (i=0; i<CLIENTS; i=i+1) response_data[i]<=0;
      end else begin
        fault_pulse<=ddr_fault ||
          (p_read && p_malformed) ||
          (k_read && k_malformed) ||
          (avm_readdatavalid && reads_outstanding==0) ||
          (avm_writeresponsevalid && !write_pending) ||
          ((avm_readdatavalid || avm_writeresponsevalid) && avm_response!=0);
        for (i=0; i<CLIENTS; i=i+1) begin
          if (response_valid[i] && c_rsp_ready[i]) begin
            response_valid[i]<=0;
            client_busy[i]<=0;
          end
        end
        if (capture) begin
          held_owner<=selection;
          if (selection==CLIENT_COUNT-1) next_owner<=0;
          else next_owner<=selection+1'b1;
          if (selection==0) begin
            held<=1; held_write<=0;
            held_address<=p_address; held_count<=p_burstcount;
            held_data<=0; held_mask<={64{1'b1}};
          end else if (selection==1) begin
            held<=1; held_write<=0;
            held_address<=k_address; held_count<=k_burstcount;
            held_data<=0; held_mask<={64{1'b1}};
          end else begin
            client_busy[selection-2]<=1;
            if (|c_req_addr[(selection-2)*33+:6]) begin
              response_valid[selection-2]<=1;
              response_error[selection-2]<=1;
              response_data[selection-2]<=0;
              fault_pulse<=1;
            end else begin
              held<=1; held_write<=c_req_write[selection-2];
              held_address<=c_req_addr[(selection-2)*33+:33];
              held_count<=1;
              held_data<=c_req_wdata[(selection-2)*512+:512];
              held_mask<=c_req_write[selection-2] ?
                c_req_be[(selection-2)*64+:64] : {64{1'b1}};
            end
          end
        end
        if (command_accept) begin
          held<=0;
          if (held_write) begin
            write_pending<=1;
            write_owner<=held_owner;
          end
        end
        if (read_push) begin
          read_owner[read_tail]<=held_owner;
          read_count[read_tail]<=held_count;
          if (read_tail==READ_OUTSTANDING-1) read_tail<=0;
          else read_tail<=read_tail+1'b1;
        end
        case ({read_push,read_pop})
          2'b10: reads_outstanding<=reads_outstanding+5'd1;
          2'b01: reads_outstanding<=reads_outstanding-5'd1;
          default: begin end
        endcase
        if (read_return) begin
          if (returning_owner>=2) begin
            response_valid[returning_owner-2]<=1;
            response_error[returning_owner-2]<=avm_response!=0;
            response_data[returning_owner-2]<=avm_readdata;
          end
          if (read_pop) begin
            read_beat<=0;
            if (read_head==READ_OUTSTANDING-1) read_head<=0;
            else read_head<=read_head+1'b1;
          end else read_beat<=read_beat+5'd1;
        end
        if (write_return) begin
          write_pending<=0;
          response_valid[write_owner-2]<=1;
          response_error[write_owner-2]<=avm_response!=0;
          response_data[write_owner-2]<=0;
        end
      end
    end
  end endgenerate
endmodule
