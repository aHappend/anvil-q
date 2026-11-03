module anvil_q1_ht2_burst_reader (
  input wire clk, rst_n,
  input wire cmd_valid,
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
  localparam IDLE = 2'd0, RECEIVE = 2'd1, RESPONSE = 2'd2;
  wire run_n;
  reg [1:0] state;
  reg two_beats, second_beat, failed;
  reg [1023:0] data;
  wire [33:0] exclusive_end =
    {1'b0, cmd_address} + {20'b0, cmd_burstcount, 6'b0};
  wire invalid_command = (cmd_burstcount != 1 && cmd_burstcount != 2) ||
    (|cmd_address[5:0]) || exclusive_end > 34'h200000000;
  wire command_transfer = cmd_valid && cmd_ready;
  wire data_transfer = mem_data_valid && mem_data_ready;

  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  assign cmd_ready = run_n && state == IDLE && (invalid_command || mem_ready);
  assign mem_valid = run_n && state == IDLE && cmd_valid && !invalid_command;
  assign mem_address = mem_valid ? cmd_address : 33'b0;
  assign mem_burstcount = mem_valid ? cmd_burstcount : 8'b0;
  assign mem_data_ready = run_n &&
    (state == RECEIVE || (mem_valid && mem_ready));
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_data = rsp_valid ? data : 1024'b0;
  assign rsp_error = rsp_valid && failed;

  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      two_beats <= 0;
      second_beat <= 0;
      failed <= 0;
      data <= 0;
    end else case (state)
      IDLE: if (command_transfer) begin
        data <= 0;
        failed <= invalid_command;
        two_beats <= cmd_burstcount == 2;
        second_beat <= 0;
        if (invalid_command) state <= RESPONSE;
        else if (data_transfer) begin
          data[511:0] <= mem_data;
          failed <= mem_error;
          if (cmd_burstcount == 1) state <= RESPONSE;
          else begin second_beat <= 1; state <= RECEIVE; end
        end else state <= RECEIVE;
      end
      RECEIVE: if (data_transfer) begin
        if (second_beat) data[1023:512] <= mem_data;
        else data[511:0] <= mem_data;
        failed <= failed || mem_error;
        if (!two_beats || second_beat) state <= RESPONSE;
        else second_beat <= 1;
      end
      RESPONSE: if (rsp_valid && rsp_ready) state <= IDLE;
      default: begin failed <= 1; data <= 0; state <= RESPONSE; end
    endcase
  end
endmodule
