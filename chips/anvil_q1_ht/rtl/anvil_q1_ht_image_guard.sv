module anvil_q1_ht_image_guard (
  input wire clk, ddr_clk, rst_n,
  input wire engine_busy, configuration_busy, csr_active, descriptors_initialized,
  input wire load_valid, dma_load_idle, dma_load_done, dma_load_error,
  input wire clear_load_error,
  output wire load_enable, load_clear,
  output wire image_modified, load_busy, load_failed, core_available,
  output wire emif_initialized
);
  localparam FREE = 2'd0, OWNED = 2'd1, CLEAR = 2'd2;
  localparam WAIT_LOAD = 3'd0, REQUEST = 3'd1, GRANT = 3'd2,
    UPLOAD = 3'd3, RETURN = 3'd4;
  reg [1:0] core_state;
  reg [2:0] ddr_state;
  reg failed, clear_pending, returned_error, clear_return_pending;
  wire core_rst_n, ddr_rst_n;
  wire acquire_valid, acquire_ready, acquire_source_ready;
  wire control_valid, control_ready, control_source_ready, control_clear;
  wire returned_valid, returned_ready, returned_source_ready;
  wire [1:0] returned_data;
  (* async_reg = "true", altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
  reg ddr_up_meta, ddr_up_sync;
  anvil_q1_ht_reset_sync u_core_reset(clk, rst_n, core_rst_n);
  anvil_q1_ht_reset_sync u_ddr_reset(ddr_clk, rst_n, ddr_rst_n);
  anvil_q1_ht_cdc_mailbox u_acquire (
    .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n),
    .source_valid(ddr_state == REQUEST), .source_ready(acquire_source_ready),
    .source_data(1'b0), .destination_valid(acquire_valid),
    .destination_ready(acquire_ready), .destination_data()
  );
  anvil_q1_ht_cdc_mailbox u_control (
    .source_clk(clk), .destination_clk(ddr_clk), .rst_n(rst_n),
    .source_valid(control_valid), .source_ready(control_source_ready),
    .source_data(core_state == CLEAR), .destination_valid(control_ready),
    .destination_ready(1'b1), .destination_data(control_clear)
  );
  anvil_q1_ht_cdc_mailbox #(.WIDTH(2)) u_return (
    .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n),
    .source_valid(returned_valid), .source_ready(returned_source_ready),
    .source_data({clear_return_pending, clear_return_pending ? 1'b0 : returned_error}),
    .destination_valid(returned_ready), .destination_ready(1'b1),
    .destination_data(returned_data)
  );
  assign acquire_ready = core_rst_n && core_state == FREE && !clear_pending &&
    !clear_load_error && !engine_busy && !configuration_busy && !csr_active &&
    descriptors_initialized && control_source_ready;
  assign control_valid = core_rst_n &&
    ((acquire_valid && acquire_ready) || core_state == CLEAR);
  assign load_enable = ddr_rst_n && ddr_state == UPLOAD && !dma_load_done;
  assign load_clear = ddr_rst_n && control_ready && control_clear && dma_load_idle;
  assign returned_valid = ddr_rst_n &&
    (ddr_state == RETURN || clear_return_pending);
  assign image_modified = acquire_valid && acquire_ready;
  assign load_busy = core_rst_n && (core_state != FREE || clear_pending);
  assign load_failed = core_rst_n && failed;
  assign core_available = core_rst_n && core_state == FREE && !acquire_valid &&
    !clear_pending && !clear_load_error;
  assign emif_initialized = core_rst_n && ddr_up_sync;
  always @(posedge clk or negedge core_rst_n) begin
    if (!core_rst_n) begin
      core_state <= FREE;
      failed <= 0;
      clear_pending <= 0;
      ddr_up_meta <= 0;
      ddr_up_sync <= 0;
    end else begin
      ddr_up_meta <= ddr_rst_n;
      ddr_up_sync <= ddr_up_meta;
      if (clear_load_error) clear_pending <= 1;
      if (acquire_valid && acquire_ready) core_state <= OWNED;
      if (core_state == FREE && (clear_pending || clear_load_error) &&
          !engine_busy && !configuration_busy) core_state <= CLEAR;
      if (core_state == CLEAR && control_source_ready) begin
        core_state <= OWNED;
        clear_pending <= 0;
      end
      if (returned_ready) begin
        failed <= returned_data[1] ? 1'b0 : returned_data[0];
        core_state <= FREE;
      end
    end
  end
  always @(posedge ddr_clk or negedge ddr_rst_n) begin
    if (!ddr_rst_n) begin
      ddr_state <= WAIT_LOAD;
      returned_error <= 0;
      clear_return_pending <= 0;
    end else begin
      if (load_clear) clear_return_pending <= 1;
      if (clear_return_pending && returned_source_ready) clear_return_pending <= 0;
      case (ddr_state)
        WAIT_LOAD: if (load_valid && !dma_load_error) ddr_state <= REQUEST;
        REQUEST: if (acquire_source_ready) ddr_state <= GRANT;
        GRANT: if (control_ready && !control_clear) ddr_state <= UPLOAD;
        UPLOAD: if (dma_load_done) begin
          returned_error <= dma_load_error;
          ddr_state <= RETURN;
        end
        RETURN: if (returned_source_ready) ddr_state <= WAIT_LOAD;
        default: ddr_state <= WAIT_LOAD;
      endcase
    end
  end
endmodule
