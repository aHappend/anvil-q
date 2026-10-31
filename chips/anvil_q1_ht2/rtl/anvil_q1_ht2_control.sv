module anvil_q1_ht2_control (
  input wire clk, ddr_clk, rst_n,
  input wire initialized, image_valid, execution_busy, image_loading, pending_results,
  input wire sticky_error, ddr_read_beat,
  input wire [2:0] accepted_tokens,
  input wire completed_batch,
  input wire [31:0] eligible_bytes, avoided_bytes,
  output wire [3:0] configuration,
  output wire [15:0] sparse_threshold,
  output wire invalidate_image, invalidate_prefix,
  input wire csr_valid, csr_write,
  input wire [15:0] csr_address,
  input wire [31:0] csr_wdata,
  output wire csr_ready, csr_rsp_valid,
  input wire csr_rsp_ready,
  output wire [31:0] csr_rdata,
  output wire csr_error,
  output wire legacy_valid, legacy_write,
  output wire [15:0] legacy_address,
  output wire [31:0] legacy_wdata,
  input wire legacy_ready, legacy_rsp_valid,
  output wire legacy_rsp_ready,
  input wire [31:0] legacy_rdata,
  input wire legacy_error
);
  localparam IDLE = 3'd0, RESPONSE = 3'd1, FORWARD = 3'd2,
    FORWARD_WAIT = 3'd3, DDR_SEND = 3'd4, DDR_WAIT = 3'd5;
  wire run_n;
  reg [2:0] state;
  reg [3:0] config_word;
  reg [15:0] threshold;
  reg invalidate_pulse, response_error;
  reg [31:0] response_data;
  reg forwarded_write;
  reg [15:0] forwarded_address;
  reg [31:0] forwarded_data;
  reg [63:0] accepted_counter, batches_counter, eligible_counter, avoided_counter;
  reg [63:0] snapshot0, snapshot1, snapshot2, snapshot3, snapshot4;
  reg [4:0] snapshot_owned;
  wire mutation_busy = execution_busy || image_loading || pending_results;
  wire transfer = csr_valid && csr_ready;
  wire reserved_address = csr_address == 16'h010c ||
    (csr_address >= 16'h0138 && csr_address <= 16'h014c);
  wire counter_address = csr_address >= 16'h0110 && csr_address <= 16'h0134;
  wire [2:0] counter_index = 3'((csr_address-16'h0110) >> 3);
  wire [63:0] live_counter = counter_index == 0 ? accepted_counter :
    counter_index == 1 ? batches_counter :
    counter_index == 3 ? eligible_counter : avoided_counter;
  wire [63:0] selected_snapshot = counter_index == 0 ? snapshot0 :
    counter_index == 1 ? snapshot1 : counter_index == 2 ? snapshot2 :
    counter_index == 3 ? snapshot3 : snapshot4;
  wire ddr_snapshot_ready, ddr_snapshot_valid;
  wire [63:0] ddr_snapshot;

  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  anvil_q1_ht2_counter_cdc u_physical_bytes (
    .clk(clk), .ddr_clk(ddr_clk), .rst_n(rst_n), .ddr_read_beat(ddr_read_beat),
    .req_valid(run_n && state == DDR_SEND), .req_ready(ddr_snapshot_ready),
    .rsp_valid(ddr_snapshot_valid), .rsp_ready(run_n && state == DDR_WAIT),
    .rsp_data(ddr_snapshot)
  );
  assign configuration = run_n ? config_word : 4'b0;
  assign sparse_threshold = run_n ? threshold : 16'b0;
  assign invalidate_image = run_n && invalidate_pulse;
  assign invalidate_prefix = run_n && invalidate_pulse;
  assign csr_ready = run_n && state == IDLE;
  assign csr_rsp_valid = run_n && state == RESPONSE;
  assign csr_rdata = csr_rsp_valid ? response_data : 32'b0;
  assign csr_error = csr_rsp_valid && response_error;
  assign legacy_valid = run_n && state == FORWARD;
  assign legacy_write = legacy_valid && forwarded_write;
  assign legacy_address = legacy_valid ? forwarded_address : 16'b0;
  assign legacy_wdata = legacy_valid ? forwarded_data : 32'b0;
  assign legacy_rsp_ready = run_n &&
    (state == FORWARD_WAIT || (legacy_valid && legacy_ready));

  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      config_word <= 0;
      threshold <= 0;
      invalidate_pulse <= 0;
      response_error <= 0;
      response_data <= 0;
      forwarded_write <= 0;
      forwarded_address <= 0;
      forwarded_data <= 0;
      accepted_counter <= 0;
      batches_counter <= 0;
      eligible_counter <= 0;
      avoided_counter <= 0;
      snapshot0 <= 0;
      snapshot1 <= 0;
      snapshot2 <= 0;
      snapshot3 <= 0;
      snapshot4 <= 0;
      snapshot_owned <= 0;
    end else begin
      invalidate_pulse <= 0;
      accepted_counter <= accepted_counter + {61'b0, accepted_tokens};
      if (completed_batch) batches_counter <= batches_counter + 1'b1;
      eligible_counter <= eligible_counter + {32'b0, eligible_bytes};
      avoided_counter <= avoided_counter + {32'b0, avoided_bytes};
      case (state)
        IDLE: if (transfer) begin
          response_data <= 0;
          response_error <= 0;
          state <= RESPONSE;
          if (csr_address[1:0] != 0) response_error <= 1;
          else if (csr_address == 16'h000c) begin
            if (!csr_write) response_data <= {31'b0, config_word[1:0] != 2};
            else if (mutation_busy || csr_wdata > 1) response_error <= 1;
            else begin
              if (!csr_wdata[0]) config_word[1:0] <= 2;
              else if (config_word[1:0] != 1) config_word[1:0] <= 0;
              invalidate_pulse <= 1;
            end
          end else if (csr_address <= 16'h003c) begin
            forwarded_write <= csr_write;
            forwarded_address <= csr_address;
            forwarded_data <= csr_wdata;
            state <= FORWARD;
          end else if (csr_address == 16'h0100) begin
            if (!csr_write) response_data <= {28'b0, config_word};
            else if (mutation_busy || csr_wdata[31:4] != 0 || csr_wdata[1:0] == 3)
              response_error <= 1;
            else begin
              config_word <= csr_wdata[3:0];
              if (csr_wdata[1:0] != config_word[1:0]) invalidate_pulse <= 1;
            end
          end else if (csr_address == 16'h0104) begin
            if (!csr_write) response_data <= {16'b0, threshold};
            else if (mutation_busy || csr_wdata[31:16] != 0 ||
                csr_wdata[14:7] == 8'hff ||
                (csr_wdata[15] && csr_wdata[14:0] != 0)) response_error <= 1;
            else threshold <= csr_wdata[15:0];
          end else if (csr_address == 16'h0108) begin
            if (csr_write) response_error <= 1;
            else response_data <= {28'b0, sticky_error, mutation_busy, image_valid, initialized};
          end else if (reserved_address) begin
            if (csr_write) response_error <= 1;
          end else if (counter_address) begin
            if (csr_write) response_error <= 1;
            else if (!csr_address[2]) begin
              if (counter_index == 2) state <= DDR_SEND;
              else begin
                response_data <= live_counter[31:0];
                snapshot_owned[counter_index] <= 1;
                case (counter_index)
                  0: snapshot0 <= live_counter;
                  1: snapshot1 <= live_counter;
                  3: snapshot3 <= live_counter;
                  4: snapshot4 <= live_counter;
                  default: begin response_data <= 0; response_error <= 1; end
                endcase
              end
            end else if (!snapshot_owned[counter_index]) response_error <= 1;
            else begin
              response_data <= selected_snapshot[63:32];
              snapshot_owned[counter_index] <= 0;
            end
          end else response_error <= 1;
        end
        FORWARD: if (legacy_valid && legacy_ready) begin
          if (legacy_rsp_valid && legacy_rsp_ready) begin
            response_data <= legacy_rdata;
            response_error <= legacy_error;
            state <= RESPONSE;
          end else state <= FORWARD_WAIT;
        end
        FORWARD_WAIT: if (legacy_rsp_valid && legacy_rsp_ready) begin
          response_data <= legacy_rdata;
          response_error <= legacy_error;
          state <= RESPONSE;
        end
        DDR_SEND: if (ddr_snapshot_ready) state <= DDR_WAIT;
        DDR_WAIT: if (ddr_snapshot_valid) begin
          snapshot2 <= ddr_snapshot;
          snapshot_owned[2] <= 1;
          response_data <= ddr_snapshot[31:0];
          state <= RESPONSE;
        end
        RESPONSE: if (csr_rsp_valid && csr_rsp_ready) state <= IDLE;
        default: begin response_data <= 0; response_error <= 1; state <= RESPONSE; end
      endcase
    end
  end
endmodule
