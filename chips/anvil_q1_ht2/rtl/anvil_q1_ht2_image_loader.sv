module anvil_q1_ht2_image_loader (
  input wire clk, ddr_clk, rst_n,
  input wire allow_acquire, clear_error,
  output wire acquire_pending, busy, failed, image_modified,
  input wire load_valid,
  output wire load_ready,
  input wire [32:0] load_address,
  input wire [511:0] load_data,
  input wire [63:0] load_byteenable,
  input wire load_last,
  output wire load_done, load_error,
  output wire dma_valid,
  input wire dma_ready,
  output wire [32:0] dma_address,
  output wire [511:0] dma_data,
  output wire [63:0] dma_byteenable,
  input wire dma_rsp_valid,
  output wire dma_rsp_ready,
  input wire dma_error
);
  localparam FREE = 3'd0, RECEIVE = 3'd1, WRITE = 3'd2,
    WRITE_WAIT = 3'd3, FINISH = 3'd4, RELEASE = 3'd5;
  localparam WAIT_LOAD = 3'd0, REQUEST = 3'd1, GRANT = 3'd2,
    UPLOAD = 3'd3, WAIT_RESULT = 3'd4, REPORT = 3'd5, RETURN = 3'd6;
  wire core_run_n, ddr_run_n;
  reg [2:0] core_state, ddr_state;
  reg failed_core, failed_ddr, result_error, last;
  reg [32:0] address;
  reg [511:0] data;
  reg [63:0] byteenable;
  reg [1:0] clear_state;
  reg clear_pending;
  wire acquire_valid, acquire_ready, acquire_source_ready;
  wire grant_valid, grant_source_ready;
  wire beat_valid, beat_ready, beat_source_ready;
  wire [609:0] beat;
  wire result_valid, result_source_ready;
  wire [1:0] result;
  wire release_valid, release_source_ready;
  wire clear_valid, clear_source_ready;
  wire beat_bad = (|beat[581:576]);
  wire grant = acquire_valid && acquire_ready;

  anvil_q1_ht2_reset_sync u_core_reset(clk, rst_n, core_run_n);
  anvil_q1_ht2_reset_sync u_ddr_reset(ddr_clk, rst_n, ddr_run_n);
  anvil_q1_ht2_mailbox u_acquire (
    .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n),
    .source_valid(ddr_state == REQUEST), .source_ready(acquire_source_ready),
    .source_data(1'b0), .destination_valid(acquire_valid),
    .destination_ready(acquire_ready), .destination_data()
  );
  anvil_q1_ht2_mailbox u_grant (
    .source_clk(clk), .destination_clk(ddr_clk), .rst_n(rst_n),
    .source_valid(grant), .source_ready(grant_source_ready), .source_data(1'b0),
    .destination_valid(grant_valid), .destination_ready(ddr_state == GRANT),
    .destination_data()
  );
  anvil_q1_ht2_mailbox #(.WIDTH(610)) u_beats (
    .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n),
    .source_valid(load_valid && load_ready), .source_ready(beat_source_ready),
    .source_data({load_last, load_address, load_data, load_byteenable}),
    .destination_valid(beat_valid), .destination_ready(beat_ready), .destination_data(beat)
  );
  anvil_q1_ht2_mailbox #(.WIDTH(2)) u_result (
    .source_clk(clk), .destination_clk(ddr_clk), .rst_n(rst_n),
    .source_valid(core_state == FINISH), .source_ready(result_source_ready),
    .source_data({last || result_error, result_error}), .destination_valid(result_valid),
    .destination_ready(ddr_state == WAIT_RESULT), .destination_data(result)
  );
  anvil_q1_ht2_mailbox u_release (
    .source_clk(ddr_clk), .destination_clk(clk), .rst_n(rst_n),
    .source_valid(ddr_state == RETURN), .source_ready(release_source_ready),
    .source_data(1'b0), .destination_valid(release_valid),
    .destination_ready(core_state == RELEASE), .destination_data()
  );
  anvil_q1_ht2_mailbox u_clear (
    .source_clk(clk), .destination_clk(ddr_clk), .rst_n(rst_n),
    .source_valid(clear_state == 1), .source_ready(clear_source_ready), .source_data(1'b0),
    .destination_valid(clear_valid), .destination_ready(ddr_state == WAIT_LOAD),
    .destination_data()
  );
  assign acquire_pending = core_run_n && acquire_valid;
  assign acquire_ready = core_run_n && core_state == FREE && allow_acquire &&
    !failed_core && !clear_pending && !clear_error && clear_state == 0 && grant_source_ready;
  assign image_modified = core_run_n && grant;
  assign busy = core_run_n && (core_state != FREE || clear_pending || clear_state != 0);
  assign failed = core_run_n && failed_core;
  assign load_ready = ddr_run_n && ddr_state == UPLOAD && !failed_ddr && beat_source_ready;
  assign load_done = ddr_run_n && ddr_state == REPORT;
  assign load_error = ddr_run_n && failed_ddr;
  assign beat_ready = core_run_n && core_state == RECEIVE;
  assign dma_valid = core_run_n && core_state == WRITE;
  assign dma_address = dma_valid ? address : 33'b0;
  assign dma_data = dma_valid ? data : 512'b0;
  assign dma_byteenable = dma_valid ? byteenable : 64'b0;
  assign dma_rsp_ready = core_run_n &&
    (core_state == WRITE_WAIT || (dma_valid && dma_ready));

  always @(posedge clk or negedge core_run_n) begin
    if (!core_run_n) begin
      core_state <= FREE;
      failed_core <= 0;
      result_error <= 0;
      last <= 0;
      address <= 0;
      data <= 0;
      byteenable <= 0;
      clear_state <= 0;
      clear_pending <= 0;
    end else begin
      if (clear_error) clear_pending <= 1;
      case (clear_state)
        0: if (core_state == FREE && (clear_pending || clear_error)) begin
          clear_state <= 1;
          clear_pending <= 0;
        end
        1: if (clear_source_ready) clear_state <= 2;
        2: if (clear_source_ready) begin clear_state <= 0; failed_core <= 0; end
        default: clear_state <= 0;
      endcase
      case (core_state)
        FREE: if (grant) begin result_error <= 0; core_state <= RECEIVE; end
        RECEIVE: if (beat_valid && beat_ready) begin
          address <= beat[608:576];
          data <= beat[575:64];
          byteenable <= beat[63:0];
          last <= beat[609];
          if (beat_bad) begin
            result_error <= 1;
            failed_core <= 1;
            core_state <= FINISH;
          end else core_state <= WRITE;
        end
        WRITE: if (dma_valid && dma_ready) begin
          if (dma_rsp_valid) begin
            if (dma_error) begin
              result_error <= 1;
              failed_core <= 1;
              core_state <= FINISH;
            end else core_state <= FINISH;
          end else core_state <= WRITE_WAIT;
        end
        WRITE_WAIT: if (dma_rsp_valid && dma_rsp_ready) begin
          if (dma_error) begin
            result_error <= 1;
            failed_core <= 1;
            core_state <= FINISH;
          end else core_state <= FINISH;
        end
        FINISH: if (result_source_ready) begin
          if (last || result_error) core_state <= RELEASE;
          else core_state <= RECEIVE;
        end
        RELEASE: if (release_valid) core_state <= FREE;
        default: begin failed_core <= 1; result_error <= 1; core_state <= FINISH; end
      endcase
    end
  end
  always @(posedge ddr_clk or negedge ddr_run_n) begin
    if (!ddr_run_n) begin ddr_state <= WAIT_LOAD; failed_ddr <= 0; end
    else begin
      if (clear_valid && ddr_state == WAIT_LOAD) failed_ddr <= 0;
      case (ddr_state)
        WAIT_LOAD: if (load_valid && !failed_ddr && !clear_valid) ddr_state <= REQUEST;
        REQUEST: if (acquire_source_ready) ddr_state <= GRANT;
        GRANT: if (grant_valid) ddr_state <= UPLOAD;
        UPLOAD: if (load_valid && load_ready) ddr_state <= WAIT_RESULT;
        WAIT_RESULT: if (result_valid) begin
          if (result[1]) begin failed_ddr <= result[0]; ddr_state <= REPORT; end
          else ddr_state <= UPLOAD;
        end
        REPORT: ddr_state <= RETURN;
        RETURN: if (release_source_ready) ddr_state <= WAIT_LOAD;
        default: begin failed_ddr <= 1; ddr_state <= WAIT_LOAD; end
      endcase
    end
  end
endmodule
