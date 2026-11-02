module anvil_q3_ht_ddr_record_port (
  input wire clk, rst_n, flush,
  input wire in_valid,
  output wire in_ready,
  input wire in_write,
  input wire [32:0] in_address,
  input wire [511:0] in_wdata,
  input wire [63:0] in_byteenable,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire [511:0] out_rdata,
  output wire idle, drain_done, fault,
  output wire memory_req_valid,
  input wire memory_req_ready,
  output wire memory_req_write,
  output wire [32:0] memory_req_address,
  output wire [511:0] memory_req_wdata,
  output wire [63:0] memory_req_byteenable,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata
);
  reg pending, waiting, valid, failed, poisoned, write_command, response_error;
  reg [32:0] address;
  reg [511:0] write_data, response_data;
  reg [63:0] byteenable;
  wire accepted=memory_req_valid && memory_req_ready;
  wire expected_return=waiting || (accepted && !write_command);
  wire busy=pending || waiting || valid;
  wire discard=flush || poisoned;
  wire issue=in_valid && in_ready;

  assign in_ready=rst_n && !discard && !failed && !busy;
  assign out_valid=rst_n && !discard && valid;
  assign out_error=out_valid && response_error;
  assign out_rdata=out_valid && !response_error ? response_data : 512'd0;
  assign drain_done=rst_n && !busy;
  assign idle=drain_done && !discard && !failed;
  assign fault=rst_n && failed;
  assign memory_req_valid=rst_n && pending;
  assign memory_req_write=memory_req_valid && write_command;
  assign memory_req_address=memory_req_valid ? address : 33'd0;
  assign memory_req_wdata=memory_req_write ? write_data : 512'd0;
  assign memory_req_byteenable=memory_req_valid ? byteenable : 64'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pending<=0; waiting<=0; valid<=0; failed<=0; poisoned<=0;
      write_command<=0; response_error<=0; address<=0;
      write_data<=0; response_data<=0; byteenable<=0;
    end else begin
      if (flush) begin
        poisoned<=1;
        failed<=0;
      end else if (poisoned && !busy) poisoned<=0;
      if (discard || (out_valid && out_ready)) begin
        valid<=0;
        response_data<=0;
        response_error<=0;
      end
      if (issue) begin
        if (in_address[5:0]!=0) begin
          valid<=1; response_error<=1; response_data<=0;
        end else begin
          pending<=1;
          write_command<=in_write;
          address<=in_address;
          write_data<=in_wdata;
          byteenable<=in_byteenable;
        end
      end
      if (accepted) begin
        pending<=0;
        if (!write_command) waiting<=1;
        else if (!discard) begin
          valid<=1; response_error<=0; response_data<=0;
        end
      end
      if (memory_rsp_valid) begin
        if (!expected_return) failed<=1;
        else begin
          waiting<=0;
          if (!discard) begin
            valid<=1;
            response_error<=memory_rsp_error;
            response_data<=memory_rsp_rdata;
          end
        end
      end
    end
  end
endmodule
