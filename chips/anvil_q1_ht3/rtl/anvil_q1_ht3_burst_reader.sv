module anvil_q1_ht3_burst_reader (
  input wire clk, rst_n, cmd_valid,
  output wire cmd_ready,
  input wire [32:0] cmd_address,
  input wire [7:0] cmd_burstcount,
  output wire mem_valid,
  input wire mem_ready,
  output wire [32:0] mem_address,
  output wire [7:0] mem_burstcount,
  input wire mem_data_valid,
  output wire mem_data_ready,
  input wire [511:0] mem_data,
  input wire mem_error,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [1023:0] rsp_data,
  output wire rsp_error
);
  localparam IDLE = 2'd0, SEND = 2'd1, RECEIVE = 2'd2, RESPONSE = 2'd3;
  wire run_n;
  reg [1:0] state;
  reg [32:0] address;
  reg [7:0] beats, remaining;
  reg [1023:0] result;
  reg failed;
  wire [33:0] command_end = {1'b0, cmd_address} +
    {20'b0, cmd_burstcount, 6'b0};
  wire command_bad = cmd_burstcount == 0 || cmd_burstcount > 2 ||
    (|cmd_address[5:0]) || command_end > 34'h200000000;
  wire request = mem_valid && mem_ready;
  wire response = mem_data_valid && mem_data_ready;
  wire [7:0] beats_left = state == SEND ? beats : remaining;

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  assign cmd_ready = run_n && state == IDLE;
  assign mem_valid = run_n && state == SEND;
  assign mem_address = mem_valid ? address : 33'b0;
  assign mem_burstcount = mem_valid ? beats : 8'b0;
  assign mem_data_ready = run_n && (state == RECEIVE || request);
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_data = rsp_valid ? result : 1024'b0;
  assign rsp_error = rsp_valid && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      address <= 0;
      beats <= 0;
      remaining <= 0;
      result <= 0;
      failed <= 0;
    end else if (run_n) begin
      case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          address <= cmd_address;
          beats <= cmd_burstcount;
          remaining <= cmd_burstcount;
          result <= 0;
          failed <= command_bad;
          if (command_bad) state <= RESPONSE;
          else state <= SEND;
        end
        SEND: if (request) state <= RECEIVE;
        RESPONSE: if (rsp_ready) state <= IDLE;
        default: begin end
      endcase
      if (response) begin
        if (beats_left == beats) result[511:0] <= mem_data;
        else result[1023:512] <= mem_data;
        failed <= failed || mem_error;
        remaining <= beats_left - 1'b1;
        if (beats_left == 1) state <= RESPONSE;
      end
    end
  end
endmodule
