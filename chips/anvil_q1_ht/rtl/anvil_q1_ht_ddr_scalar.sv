module anvil_q1_ht_ddr_scalar (
  input wire clk, ddr_clk, rst_n,
  input wire req_valid,
  output wire req_ready,
  input wire req_write,
  input wire [32:0] req_address,
  input wire [511:0] req_wdata,
  input wire [63:0] req_byteenable,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [511:0] rsp_data,
  output wire rsp_error,
  output wire protocol_error,
  output wire [32:0] avm_address,
  output wire [7:0] avm_burstcount,
  output wire avm_read, avm_write,
  output wire [511:0] avm_writedata,
  output wire [63:0] avm_byteenable,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid,
  input wire [1:0] avm_response,
  input wire avm_writeresponsevalid
);
  localparam IDLE = 2'd0, ISSUE = 2'd1, WAIT_RESPONSE = 2'd2, RESULT = 2'd3;
  reg [1:0] state;
  reg outstanding, wr, failed, fault;
  reg [32:0] address;
  reg [511:0] write_data, read_data;
  reg [63:0] byteenable;
  wire core_rst_n, ddr_rst_n;
  wire command_valid, command_ready, mailbox_ready, result_ready;
  wire [609:0] command;
  wire [512:0] result;
  wire accepted = (avm_read || avm_write) && !avm_waitrequest;
  wire response_allowed = state == WAIT_RESPONSE || accepted;
  wire response = response_allowed && (wr ? avm_writeresponsevalid : avm_readdatavalid);
  anvil_q1_ht_reset_sync u_core_reset(clk, rst_n, core_rst_n);
  anvil_q1_ht_reset_sync u_ddr_reset(ddr_clk, rst_n, ddr_rst_n);
  anvil_q1_ht_cdc_mailbox #(.WIDTH(610)) u_request (
    .source_clk(clk), .destination_clk(ddr_clk), .rst_n(rst_n),
    .source_valid(req_valid && !outstanding), .source_ready(mailbox_ready),
    .source_data({req_write, req_address, req_wdata, req_byteenable}),
    .destination_valid(command_valid), .destination_ready(command_ready),
    .destination_data(command)
  );
  anvil_q1_ht_cdc_mailbox #(.WIDTH(513)) u_response (
    .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n),
    .source_valid(state == RESULT), .source_ready(result_ready),
    .source_data({failed, read_data}), .destination_valid(rsp_valid),
    .destination_ready(rsp_ready), .destination_data(result)
  );
  assign req_ready = core_rst_n && !outstanding && mailbox_ready;
  assign rsp_data = rsp_valid && !result[512] ? result[511:0] : 512'b0;
  assign rsp_error = rsp_valid && result[512];
  assign command_ready = ddr_rst_n && state == IDLE;
  assign protocol_error = ddr_rst_n && fault;
  assign avm_read = ddr_rst_n && state == ISSUE && !wr;
  assign avm_write = ddr_rst_n && state == ISSUE && wr;
  assign avm_address = avm_read || avm_write ? address : 33'b0;
  assign avm_burstcount = avm_read || avm_write ? 8'd1 : 8'b0;
  assign avm_writedata = avm_write ? write_data : 512'b0;
  assign avm_byteenable = avm_read ? 64'hffffffffffffffff :
                         avm_write ? byteenable : 64'b0;
  always @(posedge clk or negedge core_rst_n) begin
    if (!core_rst_n) outstanding <= 0;
    else begin
      if (req_valid && req_ready) outstanding <= 1;
      if (rsp_valid && rsp_ready) outstanding <= 0;
    end
  end
  always @(posedge ddr_clk or negedge ddr_rst_n) begin
    if (!ddr_rst_n) begin
      state <= IDLE;
      wr <= 0;
      failed <= 0;
      fault <= 0;
      address <= 0;
      write_data <= 0;
      read_data <= 0;
      byteenable <= 0;
    end else begin
      if ((avm_readdatavalid && (!response_allowed || wr)) ||
          (avm_writeresponsevalid && (!response_allowed || !wr))) fault <= 1;
      case (state)
        IDLE: if (command_valid) begin
          wr <= command[609];
          address <= command[608:576];
          write_data <= command[575:64];
          byteenable <= command[63:0];
          read_data <= 0;
          failed <= fault || command[581:576] != 0;
          if (fault || command[581:576] != 0) state <= RESULT;
          else state <= ISSUE;
        end
        ISSUE, WAIT_RESPONSE: begin
          if (accepted) state <= WAIT_RESPONSE;
          if (response) begin
            failed <= avm_response != 0;
            if (!wr) read_data <= avm_readdata;
            state <= RESULT;
          end
        end
        RESULT: if (result_ready) state <= IDLE;
      endcase
    end
  end
endmodule
