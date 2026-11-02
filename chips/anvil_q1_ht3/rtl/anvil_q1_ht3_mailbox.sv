module anvil_q1_ht3_mailbox #(
  parameter WIDTH = 1
) (
  input wire source_clk, destination_clk, rst_n,
  input wire source_valid,
  output wire source_ready,
  input wire [(WIDTH > 0 ? WIDTH : 1)-1:0] source_data,
  output wire destination_valid,
  input wire destination_ready,
  output wire [(WIDTH > 0 ? WIDTH : 1)-1:0] destination_data
);
  localparam W = WIDTH > 0 ? WIDTH : 1;
  wire source_run_n, destination_run_n;
  reg [W-1:0] held_data, received_data;
  reg request_toggle, acknowledged, received_toggle, received_valid;
  (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
  reg request_meta, request_sync, acknowledge_meta, acknowledge_sync;
  initial if (WIDTH < 1) $fatal(1, "PARAMETER ERROR: HT3 mailbox width");
  anvil_q1_ht3_reset_sync u_source_reset(source_clk, rst_n, source_run_n);
  anvil_q1_ht3_reset_sync u_destination_reset(destination_clk, rst_n, destination_run_n);
  assign source_ready = source_run_n && request_toggle == acknowledge_sync;
  assign destination_valid = destination_run_n && received_valid;
  assign destination_data = destination_valid ? received_data : {W{1'b0}};
  always @(posedge source_clk or negedge rst_n) begin
    if (!rst_n) begin
      held_data <= 0;
      request_toggle <= 0;
      acknowledge_meta <= 0;
      acknowledge_sync <= 0;
    end else if (source_run_n) begin
      acknowledge_meta <= acknowledged;
      acknowledge_sync <= acknowledge_meta;
      if (source_valid && source_ready) begin
        held_data <= source_data;
        request_toggle <= !request_toggle;
      end
    end
  end
  always @(posedge destination_clk or negedge rst_n) begin
    if (!rst_n) begin
      request_meta <= 0;
      request_sync <= 0;
      received_toggle <= 0;
      acknowledged <= 0;
      received_valid <= 0;
      received_data <= 0;
    end else if (destination_run_n) begin
      request_meta <= request_toggle;
      request_sync <= request_meta;
      if (!received_valid && request_sync != received_toggle) begin
        received_data <= held_data;
        received_toggle <= request_sync;
        received_valid <= 1;
      end
      if (received_valid && destination_ready) begin
        acknowledged <= received_toggle;
        received_valid <= 0;
      end
    end
  end
endmodule
