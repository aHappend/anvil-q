module anvil_q1_ht_cdc_mailbox #(
  parameter WIDTH = 1
) (
  input wire source_clk,
  input wire destination_clk,
  input wire rst_n,
  input wire source_valid,
  output wire source_ready,
  input wire [(WIDTH > 0 ? WIDTH : 1)-1:0] source_data,
  output wire destination_valid,
  input wire destination_ready,
  output wire [(WIDTH > 0 ? WIDTH : 1)-1:0] destination_data
);
  wire source_rst_n, destination_rst_n;
  anvil_q1_ht_reset_sync u_source_reset(source_clk, rst_n, source_rst_n);
  anvil_q1_ht_reset_sync u_destination_reset(destination_clk, rst_n, destination_rst_n);

  generate
    if (WIDTH > 0) begin : g_legal
      reg [WIDTH-1:0] held_data, received_data;
      reg request_toggle, acknowledged, received_toggle, received_valid;
      (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
      reg request_meta, request_sync, acknowledge_meta, acknowledge_sync;

      assign source_ready = source_rst_n && request_toggle == acknowledge_sync;
      assign destination_valid = destination_rst_n && received_valid;
      assign destination_data = destination_valid ? received_data : {WIDTH{1'b0}};

      always @(posedge source_clk or negedge source_rst_n) begin
        if (!source_rst_n) begin
          held_data <= 0;
          request_toggle <= 0;
          acknowledge_meta <= 0;
          acknowledge_sync <= 0;
        end else begin
          acknowledge_meta <= acknowledged;
          acknowledge_sync <= acknowledge_meta;
          if (source_valid && source_ready) begin
            held_data <= source_data;
            request_toggle <= !request_toggle;
          end
        end
      end

      always @(posedge destination_clk or negedge destination_rst_n) begin
        if (!destination_rst_n) begin
          request_meta <= 0;
          request_sync <= 0;
          received_toggle <= 0;
          acknowledged <= 0;
          received_valid <= 0;
          received_data <= 0;
        end else begin
          request_meta <= request_toggle;
          request_sync <= request_meta;
          if (!received_valid && request_sync != received_toggle) begin
            // held_data cannot change until the returned acknowledgement crosses back.
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
    end else begin : g_illegal
      initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: mailbox WIDTH must be positive");
      assign source_ready = 0;
      assign destination_valid = 0;
      assign destination_data = 0;
    end
  endgenerate
endmodule
