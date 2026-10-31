module anvil_q1_ht2_dma_mux (
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
  localparam PICK = 2'd0, SEND = 2'd1, RECEIVE = 2'd2;
  wire run_n;
  reg [1:0] state, owner;
  reg writing, fault;
  reg [32:0] address;
  reg [7:0] beats, remaining;
  reg [511:0] data;
  reg [63:0] byteenable;
  wire [1:0] selected = client_valid[3] ? 2'd3 :
    client_valid[2] ? 2'd2 : client_valid[1] ? 2'd1 : 2'd0;
  wire response_bad = rsp_write != writing || rsp_last != (remaining == 1);
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  assign client_ready = run_n && state == PICK ? (4'b0001 << selected) : 4'b0;
  assign client_rsp_valid = run_n && state == RECEIVE && rsp_valid ?
    (4'b0001 << owner) : 4'b0;
  assign client_rsp_data = (|client_rsp_valid) ? rsp_data : 512'b0;
  assign client_rsp_error = (|client_rsp_valid) && (rsp_error || response_bad);
  assign busy = run_n && state != PICK;
  assign protocol_error = run_n && fault;
  assign req_valid = run_n && state == SEND;
  assign req_write = req_valid && writing;
  assign req_address = req_valid ? address : 33'b0;
  assign req_burstcount = req_valid ? beats : 8'b0;
  assign req_writedata = req_valid && writing ? data : 512'b0;
  assign req_byteenable = req_valid ? byteenable : 64'b0;
  assign rsp_ready = run_n && state == RECEIVE && client_rsp_ready[owner];
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= PICK;
      owner <= 0;
      writing <= 0;
      fault <= 0;
      address <= 0;
      beats <= 0;
      remaining <= 0;
      data <= 0;
      byteenable <= 0;
    end else case (state)
      PICK: if (|client_valid) begin
        owner <= selected;
        writing <= client_write[selected];
        address <= client_address[33*selected+:33];
        beats <= client_burstcount[8*selected+:8];
        remaining <= client_write[selected] ? 8'd1 : client_burstcount[8*selected+:8];
        data <= client_writedata[512*selected+:512];
        byteenable <= client_byteenable[64*selected+:64];
        state <= SEND;
      end
      SEND: if (req_valid && req_ready) state <= RECEIVE;
      RECEIVE: if (rsp_valid && rsp_ready) begin
        if (response_bad) fault <= 1;
        if (rsp_last) begin remaining <= 0; state <= PICK; end
        else remaining <= remaining - 1'b1;
      end
      default: begin fault <= 1; state <= PICK; end
    endcase
  end
endmodule
