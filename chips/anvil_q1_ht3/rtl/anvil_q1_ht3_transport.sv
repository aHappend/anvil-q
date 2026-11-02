module anvil_q1_ht3_transport (
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
  wire core_run_n, ddr_run_n;
  wire command_source_ready, command_valid, command_ready;
  wire [617:0] command_data;
  wire response_source_ready, response_valid;
  wire [514:0] response_data;
  wire [9:0] response_used;
  reg bus_pending, held_write, recovered, transaction_failed;
  reg [32:0] held_address;
  reg [7:0] held_beats;
  reg [511:0] held_data;
  reg [63:0] held_mask;
  reg [9:0] reserved_beats;
  reg [7:0] synthetic_remaining;
  reg synthetic_write;
  (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
  reg available_meta, available_sync, fault_meta, fault_sync;

  // Physical debt is power-up initialized and deliberately survives logical reset.
  reg [4:0] debt_count;
  reg [3:0] debt_read, debt_write;
  reg [7:0] debt_remaining;
  reg bus_fault;
  reg [7:0] debt_lengths [0:15];
  reg debt_writes [0:15];
  initial begin
    debt_count = 0;
    debt_read = 0;
    debt_write = 0;
    debt_remaining = 0;
    bus_fault = 0;
  end
  wire physical_accept = ddr_run_n && bus_pending && !avm_waitrequest;
  wire physical_owned = debt_count != 0 || physical_accept;
  wire physical_writing = debt_count != 0 ? debt_writes[debt_read] : held_write;
  wire [7:0] physical_remaining = debt_count != 0 ? debt_remaining :
    held_write ? 8'd1 : held_beats;
  wire physical_read = avm_readdatavalid && physical_owned && !physical_writing;
  wire physical_write = avm_writeresponsevalid && physical_owned && physical_writing;
  wire physical_response = physical_read || physical_write;
  wire physical_last = physical_write || (physical_read && physical_remaining == 1);
  wire unexpected = (avm_readdatavalid && (!physical_owned || physical_writing)) ||
    (avm_writeresponsevalid && (!physical_owned || !physical_writing)) ||
    (avm_readdatavalid && avm_writeresponsevalid);
  wire debt_push = physical_accept && !(debt_count == 0 && physical_last);
  wire debt_pop = physical_last && debt_count != 0;
  wire [5:0] prospective_debt = {1'b0,debt_count} +
    {5'b0,debt_push} - {5'b0,debt_pop};
  wire capture_response = ddr_run_n && recovered && physical_response;
  wire synthetic_response = ddr_run_n && synthetic_remaining != 0;
  wire enqueue_response = capture_response || synthetic_response;
  wire [514:0] outgoing_response = capture_response ?
    {physical_writing, physical_last,
     bus_fault || transaction_failed || avm_response != 0,
     physical_read ? avm_readdata : 512'b0} :
    {synthetic_write, synthetic_remaining == 1, 1'b1, 512'b0};
  wire [33:0] command_end = {1'b0,command_data[616:584]} +
    {20'b0,command_data[583:576],6'b0};
  wire command_bad = command_data[583:576] == 0 ||
    (|command_data[589:584]) || command_end > 34'h200000000 ||
    (command_data[617] && command_data[583:576] != 1);
  wire synthetic_command = command_bad || bus_fault;
  wire [7:0] requested_responses = command_data[617] ||
    command_data[583:576] == 0 ? 8'd1 : command_data[583:576];
  wire stage_free = !bus_pending || physical_accept;
  wire synthetic_free = synthetic_remaining == 0 ||
    (synthetic_remaining == 1 && response_source_ready);
  wire [10:0] total_reservation = {1'b0,response_used} +
    {1'b0,reserved_beats} + {3'b0,requested_responses};
  wire credits = total_reservation <= 512;
  wire same_kind = prospective_debt == 0 ||
    command_data[617] == physical_writing;
  wire launch = command_valid && command_ready;
  wire [10:0] next_reserved = {1'b0,reserved_beats} +
    (launch ? {3'b0,requested_responses} : 11'b0) -
    ((enqueue_response && response_source_ready) ? 11'd1 : 11'd0);

  anvil_q1_ht3_reset_sync u_core_reset(clk, rst_n, core_run_n);
  anvil_q1_ht3_reset_sync u_ddr_reset(ddr_clk, rst_n, ddr_run_n);
  anvil_q1_ht3_async_fifo #(.WIDTH(618), .DEPTH(16)) u_commands (
    .source_clk(clk), .destination_clk(ddr_clk), .rst_n(rst_n),
    .source_valid(core_run_n && req_valid && available_sync && !fault_sync),
    .source_ready(command_source_ready),
    .source_data({req_write,req_address,req_burstcount,req_writedata,req_byteenable}),
    .destination_valid(command_valid), .destination_ready(command_ready),
    .destination_data(command_data), .source_used()
  );
  anvil_q1_ht3_async_fifo #(.WIDTH(515), .DEPTH(512)) u_responses (
    .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n),
    .source_valid(enqueue_response), .source_ready(response_source_ready),
    .source_data(outgoing_response), .destination_valid(response_valid),
    .destination_ready(core_run_n && rsp_ready),
    .destination_data(response_data), .source_used(response_used)
  );
  assign req_ready = core_run_n && available_sync && !fault_sync && command_source_ready;
  assign rsp_valid = core_run_n && response_valid;
  assign rsp_write = rsp_valid && response_data[514];
  assign rsp_last = rsp_valid && response_data[513];
  assign rsp_error = rsp_valid && response_data[512];
  assign rsp_data = rsp_valid ? response_data[511:0] : 512'b0;
  assign available = core_run_n && available_sync && !fault_sync;
  assign protocol_error = core_run_n && fault_sync;
  assign command_ready = ddr_run_n && (recovered || bus_fault) && stage_free &&
    synthetic_free && credits && prospective_debt < 16 &&
    (synthetic_command ? prospective_debt == 0 : same_kind);
  assign avm_read = ddr_run_n && bus_pending && !held_write;
  assign avm_write = ddr_run_n && bus_pending && held_write;
  assign avm_address = ddr_run_n && bus_pending ? held_address : 33'b0;
  assign avm_burstcount = ddr_run_n && bus_pending ? held_beats : 8'b0;
  assign avm_writedata = avm_write ? held_data : 512'b0;
  assign avm_byteenable = ddr_run_n && bus_pending ?
    (held_write ? held_mask : 64'hffffffffffffffff) : 64'b0;
  assign ddr_read_beat = ddr_run_n && physical_read;

  always @(posedge ddr_clk) begin
    if (physical_accept) begin
      debt_lengths[debt_write] <= held_write ? 8'd1 : held_beats;
      debt_writes[debt_write] <= held_write;
    end
    if (debt_push) debt_write <= debt_write + 1'b1;
    if (debt_pop) debt_read <= debt_read + 1'b1;
    case ({debt_push,debt_pop})
      2'b10: debt_count <= debt_count + 1'b1;
      2'b01: debt_count <= debt_count - 1'b1;
      default: begin end
    endcase
    if (physical_response) begin
      if (!physical_last) debt_remaining <= physical_remaining - 1'b1;
      else if (debt_count > 1) debt_remaining <= debt_lengths[debt_read + 4'd1];
      else if (debt_push) debt_remaining <= held_write ? 8'd1 : held_beats;
      else debt_remaining <= 0;
    end else if (physical_accept && debt_count == 0)
      debt_remaining <= held_write ? 8'd1 : held_beats;
    if (unexpected || prospective_debt > 16 ||
        (ddr_run_n && enqueue_response && !response_source_ready) ||
        (ddr_run_n && next_reserved > 512)) bus_fault <= 1;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      available_meta <= 0;
      available_sync <= 0;
      fault_meta <= 0;
      fault_sync <= 0;
    end else if (core_run_n) begin
      available_meta <= recovered && !bus_fault;
      available_sync <= available_meta;
      fault_meta <= bus_fault;
      fault_sync <= fault_meta;
    end
  end
  always @(posedge ddr_clk or negedge rst_n) begin
    if (!rst_n) begin
      bus_pending <= 0;
      held_write <= 0;
      held_address <= 0;
      held_beats <= 0;
      held_data <= 0;
      held_mask <= 0;
      recovered <= 0;
      transaction_failed <= 0;
      reserved_beats <= 0;
      synthetic_remaining <= 0;
      synthetic_write <= 0;
    end else if (ddr_run_n) begin
      if (!recovered && debt_count == 0 && !bus_fault) recovered <= 1;
      if (physical_response) begin
        if (physical_last) transaction_failed <= 0;
        else transaction_failed <= transaction_failed || avm_response != 0;
      end
      reserved_beats <= next_reserved[9:0];
      if (synthetic_response && response_source_ready)
        synthetic_remaining <= synthetic_remaining - 1'b1;
      if (physical_accept) bus_pending <= 0;
      if (launch) begin
        if (synthetic_command) begin
          synthetic_remaining <= requested_responses;
          synthetic_write <= command_data[617];
        end else begin
          bus_pending <= 1;
          held_write <= command_data[617];
          held_address <= command_data[616:584];
          held_beats <= command_data[583:576];
          held_data <= command_data[575:64];
          held_mask <= command_data[63:0];
        end
      end
    end
  end
endmodule
