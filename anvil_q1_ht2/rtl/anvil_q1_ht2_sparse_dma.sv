module anvil_q1_ht2_sparse_dma (
  input wire clk, rst_n, req_valid,
  output wire req_ready,
  input wire [32:0] req_address,
  input wire [7:0] req_burstcount,
  input wire [63:0] req_activations,
  input wire [3:0] req_slots,
  input wire [15:0] req_threshold,
  output wire dma_valid,
  input wire dma_ready,
  output wire [32:0] dma_address,
  output wire [7:0] dma_burstcount,
  output wire decision_valid,
  input wire decision_ready,
  output wire decision_skipped, decision_error
);
  localparam IDLE = 2'd0, CLASSIFY = 2'd1, DMA = 2'd2, RESPONSE = 2'd3;
  wire run_n;
  reg [1:0] state;
  reg [32:0] address;
  reg [7:0] burstcount;
  reg [63:0] activations;
  reg [3:0] slots;
  reg [15:0] threshold;
  reg skipped, failed;
  reg predicate_skip, predicate_error;
  integer slot;
  wire [33:0] exclusive_end =
    {1'b0, address} + {20'b0, burstcount, 6'b0};

  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    predicate_skip = 1'b1;
    predicate_error = slots == 0 || burstcount == 0 || address[5:0] != 0 ||
      exclusive_end > 34'h200000000 ||
      threshold[14:7] == 8'hff || (threshold[15] && threshold[14:0] != 0);
    for (slot = 0; slot < 4; slot = slot + 1) begin
      if (slots[slot]) begin
        if (activations[16*slot+7+:8] == 8'hff) predicate_error = 1'b1;
        if (activations[16*slot+:15] > threshold[14:0]) predicate_skip = 1'b0;
      end
    end
  end

  assign req_ready = run_n && state == IDLE;
  assign dma_valid = run_n && state == DMA;
  assign dma_address = dma_valid ? address : 33'b0;
  assign dma_burstcount = dma_valid ? burstcount : 8'b0;
  assign decision_valid = run_n && state == RESPONSE;
  assign decision_skipped = decision_valid && skipped;
  assign decision_error = decision_valid && failed;

  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      address <= 0;
      burstcount <= 0;
      activations <= 0;
      slots <= 0;
      threshold <= 0;
      skipped <= 0;
      failed <= 0;
    end else case (state)
      IDLE: if (req_valid && req_ready) begin
        address <= req_address;
        burstcount <= req_burstcount;
        activations <= req_activations;
        slots <= req_slots;
        threshold <= req_threshold;
        skipped <= 0;
        failed <= 0;
        state <= CLASSIFY;
      end
      CLASSIFY: begin
        failed <= predicate_error;
        skipped <= predicate_skip && !predicate_error;
        if (predicate_error || predicate_skip) state <= RESPONSE;
        else state <= DMA;
      end
      DMA: if (dma_valid && dma_ready) state <= RESPONSE;
      RESPONSE: if (decision_valid && decision_ready) state <= IDLE;
      default: begin
        skipped <= 0;
        failed <= 1;
        state <= RESPONSE;
      end
    endcase
  end
endmodule
