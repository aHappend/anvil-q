module anvil_q1_ht3_dma_mux #(
  parameter DEPTH = 8, CHECK_RESPONSE_LAST = 1
) (
  input wire clk, rst_n,
  input wire [3:0] client_valid,
  output wire [3:0] client_ready,
  input wire [3:0] client_write,
  input wire [131:0] client_address,
  input wire [31:0] client_burstcount,
  input wire [2047:0] client_writedata,
  input wire [255:0] client_byteenable,
  output wire [3:0] client_rsp_valid,
  input wire [3:0] client_rsp_ready,
  output wire [511:0] client_rsp_data,
  output wire client_rsp_error,
  output wire busy, protocol_error,
  output wire req_valid,
  input wire req_ready,
  output wire req_write,
  output wire [32:0] req_address,
  output wire [7:0] req_burstcount,
  output wire [511:0] req_writedata,
  output wire [63:0] req_byteenable,
  input wire rsp_valid,
  output wire rsp_ready,
  input wire rsp_write, rsp_last, rsp_error,
  input wire [511:0] rsp_data
);
  localparam LEGAL = DEPTH >= 1 && DEPTH <= 32 &&
    (CHECK_RESPONSE_LAST == 0 || CHECK_RESPONSE_LAST == 1);
  localparam N = LEGAL ? DEPTH : 1;
  localparam P = N > 1 ? $clog2(N) : 1;
  initial if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 DMA ownership depth");
  generate if (!LEGAL) begin: g_invalid
    assign client_ready = 0;
    assign client_rsp_valid = 0;
    assign client_rsp_data = 0;
    assign client_rsp_error = 0;
    assign busy = 0;
    assign protocol_error = 0;
    assign req_valid = 0;
    assign req_write = 0;
    assign req_address = 0;
    assign req_burstcount = 0;
    assign req_writedata = 0;
    assign req_byteenable = 0;
    assign rsp_ready = 0;
  end else begin: g_legal
  wire run_n;
  reg [P-1:0] read_pointer, write_pointer;
  reg [P:0] count;
  reg [1:0] next_priority, locked_owner;
  reg locked, fault, output_owned, output_error;
  reg [1:0] output_owner;
  reg [511:0] output_data;
  reg [7:0] remaining;
  reg [1:0] selected;
  reg found;
  integer scan;
  reg [1:0] candidate;
  (* nomem2reg *) reg [1:0] owners [0:N-1];
  reg writing [0:N-1];
  (* nomem2reg *) reg [7:0] lengths [0:N-1];
  wire [1:0] chosen = locked ? locked_owner : selected;
  wire chosen_valid = client_valid[chosen];
  wire chosen_write = client_write[chosen];
  wire [7:0] chosen_beats = client_burstcount[8*chosen+:8];
  wire [32:0] chosen_address = client_address[33*chosen+:33];
  wire [33:0] exclusive_end = {1'b0, chosen_address} +
    {20'b0, chosen_beats, 6'b0};
  wire command_bad = chosen_beats == 0 || (chosen_write && chosen_beats != 1) ||
    (|chosen_address[5:0]) || exclusive_end > 34'h200000000;
  wire output_space = !output_owned || client_rsp_ready[output_owner];
  wire issue = req_valid && req_ready;
  wire synthetic = run_n && chosen_valid && command_bad && count == 0 &&
    !locked && output_space;
  wire incoming_owned = count != 0 || issue;
  wire [1:0] incoming_owner = count != 0 ? owners[read_pointer] : chosen;
  wire incoming_write = count != 0 ? writing[read_pointer] : chosen_write;
  wire [7:0] incoming_remaining = count != 0 ? remaining : chosen_beats;
  wire response_bad = rsp_write != incoming_write ||
    (CHECK_RESPONSE_LAST && rsp_last != (incoming_remaining == 1));
  wire receive = rsp_valid && rsp_ready;
  wire retire = receive && incoming_owned && incoming_remaining == 1;
  wire push = issue && !(count == 0 && retire);
  wire pop = retire && count != 0;
  wire credit = count < N || (run_n && count != 0 &&
    rsp_valid && output_space && remaining == 1);
  wire [P-1:0] following_read = read_pointer + 1'b1 == N ?
    {P{1'b0}} : read_pointer + 1'b1;
  wire [P-1:0] following_write = write_pointer + 1'b1 == N ?
    {P{1'b0}} : write_pointer + 1'b1;

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    selected = next_priority;
    found = 0;
    candidate = 0;
    for (scan = 0; scan < 4; scan = scan + 1) begin
      candidate = next_priority + 2'(scan);
      if (!found && client_valid[candidate]) begin
        selected = candidate;
        found = 1;
      end
    end
  end
  assign req_valid = run_n && LEGAL && chosen_valid && !command_bad && credit;
  assign req_write = req_valid && chosen_write;
  assign req_address = req_valid ? chosen_address : 33'b0;
  assign req_burstcount = req_valid ? chosen_beats : 8'b0;
  assign req_writedata = req_valid && chosen_write ?
    client_writedata[512*chosen+:512] : 512'b0;
  assign req_byteenable = req_valid ? client_byteenable[64*chosen+:64] : 64'b0;
  assign client_ready = run_n && (issue || synthetic) ? 4'b0001 << chosen : 4'b0;
  assign rsp_ready = run_n && output_space && incoming_owned && !synthetic;
  assign client_rsp_valid = run_n && output_owned ? 4'b0001 << output_owner : 4'b0;
  assign client_rsp_data = (|client_rsp_valid) ? output_data : 512'b0;
  assign client_rsp_error = (|client_rsp_valid) && output_error;
  assign busy = run_n && (count != 0 || locked || output_owned);
  assign protocol_error = run_n && fault;

  always @(posedge clk) begin
    if (run_n && push) begin
      owners[write_pointer] <= chosen;
      writing[write_pointer] <= chosen_write;
      lengths[write_pointer] <= chosen_beats;
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      read_pointer <= 0;
      write_pointer <= 0;
      count <= 0;
      next_priority <= 0;
      locked_owner <= 0;
      locked <= 0;
      fault <= 0;
      output_owned <= 0;
      output_error <= 0;
      output_owner <= 0;
      output_data <= 0;
      remaining <= 0;
    end else if (run_n) begin
      if (req_valid && !req_ready) begin
        locked <= 1;
        locked_owner <= chosen;
      end
      if (issue || synthetic) begin
        locked <= 0;
        next_priority <= chosen + 1'b1;
      end
      if (push) write_pointer <= following_write;
      if (pop) read_pointer <= following_read;
      case ({push, pop})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: begin end
      endcase
      if (issue && count == 0) remaining <= chosen_beats;
      if (receive) begin
        output_owned <= 1;
        output_owner <= incoming_owner;
        output_data <= rsp_data;
        output_error <= rsp_error || response_bad;
        if (response_bad) fault <= 1;
        if (incoming_remaining != 1) remaining <= incoming_remaining - 1'b1;
        else if (count > 1) remaining <= lengths[following_read];
        else if (count == 1 && issue) remaining <= chosen_beats;
        else remaining <= 0;
      end else if (synthetic) begin
        output_owned <= 1;
        output_owner <= chosen;
        output_data <= 0;
        output_error <= 1;
        fault <= 1;
      end else if (output_owned && client_rsp_ready[output_owner])
        output_owned <= 0;
      if (rsp_valid && !incoming_owned) fault <= 1;
    end
  end
  end endgenerate
endmodule
