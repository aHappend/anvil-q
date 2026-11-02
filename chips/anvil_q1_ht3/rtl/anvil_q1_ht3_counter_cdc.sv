module anvil_q1_ht3_counter_cdc (
  input wire clk, ddr_clk, rst_n, ddr_read_beat, req_valid,
  output wire req_ready, rsp_valid,
  input wire rsp_ready,
  output wire [63:0] rsp_data
);
  localparam IDLE = 2'd0, WAIT_ACK = 2'd1, RESPONSE = 2'd2;
  wire core_run_n, ddr_run_n;
  reg [1:0] state;
  reg request_toggle, acknowledged_toggle;
  (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
  reg request_meta, request_sync, acknowledge_meta, acknowledge_sync;
  reg [63:0] live_bytes, held_bytes, result;
  anvil_q1_ht3_reset_sync u_core_reset(clk, rst_n, core_run_n);
  anvil_q1_ht3_reset_sync u_ddr_reset(ddr_clk, rst_n, ddr_run_n);
  assign req_ready = core_run_n && state == IDLE;
  assign rsp_valid = core_run_n && state == RESPONSE;
  assign rsp_data = rsp_valid ? result : 64'b0;
  always @(posedge ddr_clk or negedge rst_n) begin
    if (!rst_n) begin
      request_meta <= 0;
      request_sync <= 0;
      acknowledged_toggle <= 0;
      live_bytes <= 0;
      held_bytes <= 0;
    end else if (ddr_run_n) begin
      request_meta <= request_toggle;
      request_sync <= request_meta;
      if (ddr_read_beat) live_bytes <= live_bytes + 64'd64;
      if (request_sync != acknowledged_toggle) begin
        held_bytes <= live_bytes;
        acknowledged_toggle <= request_sync;
      end
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      request_toggle <= 0;
      acknowledge_meta <= 0;
      acknowledge_sync <= 0;
      result <= 0;
    end else if (core_run_n) begin
      acknowledge_meta <= acknowledged_toggle;
      acknowledge_sync <= acknowledge_meta;
      case (state)
        IDLE: if (req_valid && req_ready) begin
          request_toggle <= !request_toggle;
          state <= WAIT_ACK;
        end
        WAIT_ACK: if (acknowledge_sync == request_toggle) begin
          result <= held_bytes;
          state <= RESPONSE;
        end
        RESPONSE: if (rsp_ready) state <= IDLE;
        default: state <= IDLE;
      endcase
    end
  end
endmodule
