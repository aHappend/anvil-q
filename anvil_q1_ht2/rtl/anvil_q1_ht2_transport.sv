module anvil_q1_ht2_transport (
  input wire clk, ddr_clk, rst_n,
  input wire req_valid,
  output wire req_ready,
  input wire req_write,
  input wire [32:0] req_address,
  input wire [7:0] req_burstcount,
  input wire [511:0] req_writedata,
  input wire [63:0] req_byteenable,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire rsp_write, rsp_last, rsp_error,
  output wire [511:0] rsp_data,
  output wire available, protocol_error, ddr_read_beat,
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
  localparam IDLE = 2'd0, COMMAND = 2'd1, COLLECT = 2'd2, SEND_ERROR = 2'd3;
  wire core_run_n, ddr_run_n;
  wire command_source_ready, command_valid, command_ready;
  wire response_source_ready, response_valid;
  wire [617:0] command_data;
  wire [514:0] response_data;
  reg core_owned;
  reg [1:0] state;
  reg writing, failed, ddr_recovered;
  reg [32:0] address;
  reg [7:0] burstcount;
  reg [511:0] writedata;
  reg [63:0] byteenable;

  // Physical bus debt survives a logical reset; clients and FIFO ownership do not.
  reg [9:0] bus_ledger [0:0];
  initial bus_ledger[0] = 10'b0;
  wire [9:0] ledger = bus_ledger[0];
  wire bus_empty = ledger[7:0] == 0;
  wire bus_fault = ledger[9];
  wire issue = ddr_run_n && state == COMMAND && bus_empty && !bus_fault;
  wire physical_accept = issue && !avm_waitrequest;
  wire read_allowed = (!bus_empty && !ledger[8]) || (physical_accept && !writing);
  wire write_allowed = (!bus_empty && ledger[8]) || (physical_accept && writing);
  wire physical_read = avm_readdatavalid && read_allowed;
  wire physical_write = avm_writeresponsevalid && write_allowed;
  wire unexpected = (avm_readdatavalid && !read_allowed) ||
    (avm_writeresponsevalid && !write_allowed) ||
    (avm_readdatavalid && avm_writeresponsevalid);
  wire [7:0] physical_remaining = bus_empty ? burstcount : ledger[7:0];
  wire physical_read_last = physical_read && physical_remaining == 1;
  wire capture_read = ddr_run_n && physical_read &&
    (state == COLLECT || (state == COMMAND && physical_accept));
  wire capture_write = ddr_run_n && physical_write &&
    (state == COLLECT || (state == COMMAND && physical_accept));
  wire [33:0] command_end = {1'b0, command_data[616:584]} +
    {20'b0, command_data[583:576], 6'b0};
  wire command_bad = command_data[583:576] == 0 ||
    (|command_data[589:584]) || command_end > 34'h200000000 ||
    (command_data[617] && command_data[583:576] != 1);
  wire response_enqueue = capture_read || capture_write || state == SEND_ERROR;
  wire [514:0] outgoing_response = capture_read ?
    {1'b0, physical_read_last, failed || avm_response != 0, avm_readdata} :
    {writing, 1'b1, failed || avm_response != 0, 512'b0};
  reg [9:0] next_ledger;
  (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
  reg available_meta, available_sync, fault_meta, fault_sync;

  anvil_q1_ht2_reset_sync u_core_reset(clk, rst_n, core_run_n);
  anvil_q1_ht2_reset_sync u_ddr_reset(ddr_clk, rst_n, ddr_run_n);
  anvil_q1_ht2_mailbox #(.WIDTH(618)) u_commands (
    .source_clk(clk), .destination_clk(ddr_clk), .rst_n(rst_n),
    .source_valid(core_run_n && req_valid && !core_owned && available_sync && !fault_sync),
    .source_ready(command_source_ready),
    .source_data({req_write, req_address, req_burstcount, req_writedata, req_byteenable}),
    .destination_valid(command_valid), .destination_ready(command_ready),
    .destination_data(command_data)
  );
  // One owned transaction has at most 255 beats; 512 entries absorb it without Avalon backpressure.
  anvil_q1_ht2_response_fifo u_responses (
    .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n),
    .source_valid(ddr_run_n && response_enqueue),
    .source_ready(response_source_ready), .source_data(outgoing_response),
    .destination_valid(response_valid), .destination_ready(core_run_n && rsp_ready && core_owned),
    .destination_data(response_data)
  );
  assign req_ready = core_run_n && !core_owned && available_sync &&
    !fault_sync && command_source_ready;
  assign rsp_valid = core_run_n && core_owned && response_valid;
  assign rsp_write = rsp_valid && response_data[514];
  assign rsp_last = rsp_valid && response_data[513];
  assign rsp_error = rsp_valid && response_data[512];
  assign rsp_data = rsp_valid ? response_data[511:0] : 512'b0;
  assign available = core_run_n && available_sync && !fault_sync;
  assign protocol_error = core_run_n && fault_sync;
  assign command_ready = ddr_run_n && ddr_recovered &&
    state == IDLE && bus_empty && !bus_fault;
  assign avm_read = issue && !writing;
  assign avm_write = issue && writing;
  assign avm_address = issue ? address : 33'b0;
  assign avm_burstcount = issue ? burstcount : 8'b0;
  assign avm_writedata = avm_write ? writedata : 512'b0;
  assign avm_byteenable = issue ? (writing ? byteenable : 64'hffffffffffffffff) : 64'b0;
  assign ddr_read_beat = ddr_run_n && physical_read;

  always @* begin
    next_ledger = ledger;
    if (physical_accept) next_ledger[8:0] = {writing, writing ? 8'd1 : burstcount};
    if (physical_read) next_ledger[7:0] = physical_remaining - 1'b1;
    if (physical_write) next_ledger[7:0] = 0;
    if (unexpected || (ddr_run_n && response_enqueue && !response_source_ready))
      next_ledger[9] = 1;
  end
  always @(posedge ddr_clk) begin
    bus_ledger[0] <= next_ledger;
  end
  always @(posedge clk or negedge core_run_n) begin
    if (!core_run_n) begin
      core_owned <= 0;
      available_meta <= 0;
      available_sync <= 0;
      fault_meta <= 0;
      fault_sync <= 0;
    end else begin
      available_meta <= ddr_recovered && !bus_fault;
      available_sync <= available_meta;
      fault_meta <= bus_fault;
      fault_sync <= fault_meta;
      if (req_valid && req_ready) core_owned <= 1;
      if (rsp_valid && rsp_ready && rsp_last) core_owned <= 0;
    end
  end
  always @(posedge ddr_clk or negedge ddr_run_n) begin
    if (!ddr_run_n) ddr_recovered <= 0;
    else if (bus_fault) ddr_recovered <= 0;
    else if (bus_empty) ddr_recovered <= 1;
  end
  always @(posedge ddr_clk or negedge ddr_run_n) begin
    if (!ddr_run_n) begin
      state <= IDLE;
      writing <= 0;
      failed <= 0;
      address <= 0;
      burstcount <= 0;
      writedata <= 0;
      byteenable <= 0;
    end else case (state)
      IDLE: if (command_valid && command_ready) begin
        writing <= command_data[617];
        address <= command_data[616:584];
        burstcount <= command_data[583:576];
        writedata <= command_data[575:64];
        byteenable <= command_data[63:0];
        failed <= command_bad;
        if (command_bad) state <= SEND_ERROR;
        else state <= COMMAND;
      end
      COMMAND: if (physical_accept) begin
        state <= COLLECT;
        if (physical_read) begin
          failed <= avm_response != 0;
          if (physical_read_last) state <= IDLE;
        end
        if (physical_write) begin failed <= avm_response != 0; state <= IDLE; end
      end
      COLLECT: begin
        if (physical_read) begin
          failed <= failed || avm_response != 0;
          if (physical_read_last) state <= IDLE;
        end
        if (physical_write) begin failed <= failed || avm_response != 0; state <= IDLE; end
      end
      SEND_ERROR: if (response_source_ready) state <= IDLE;
      default: begin failed <= 1; state <= SEND_ERROR; end
    endcase
  end
endmodule
