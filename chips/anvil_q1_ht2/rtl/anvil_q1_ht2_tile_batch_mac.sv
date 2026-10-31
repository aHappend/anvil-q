module anvil_q1_ht2_tile_batch_mac (
  input wire clk, rst_n, in_valid, in_first, in_last, in_fp16,
  output wire in_ready,
  input wire [3:0] in_slots,
  input wire [63:0] in_mask,
  input wire [63:0] in_activation,
  input wire [1023:0] in_weights,
  output wire out_valid,
  input wire out_ready,
  output wire [8191:0] out_data,
  output wire [63:0] out_mask,
  output wire [3:0] out_slots,
  output wire out_error
);
  localparam IDLE = 3'd0, ACTIVE = 3'd1, DRAIN = 3'd2,
             BAD_DRAIN = 3'd3, RESPONSE = 3'd4;
  wire run_n;
  reg [2:0] state;
  reg [4:0] age;
  reg [1:0] next_context, phase0, phase1, phase2;
  reg [63:0] mask;
  reg [3:0] slots;
  reg format_fp16, failed;
  reg [8191:0] result;
  wire [8191:0] lane_result;
  wire [255:0] lane_error;
  wire accept = in_valid && in_ready;
  wire configuration_match = in_mask == mask && in_slots == slots &&
                                                    in_fp16 == format_fp16;
  wire legal_beat = state == IDLE ? in_first :
                                 state == ACTIVE && !in_first && configuration_match;
  wire beat = accept && legal_beat;
  wire clear = beat && state == IDLE;
  wire advance = run_n && state != RESPONSE;
  wire reduce_first = state == DRAIN && age == 6;
  wire reduce_second = state == DRAIN && age == 10;
  wire reduce_third = state == DRAIN && age == 14;
  genvar slot, lane;

  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  assign in_ready = run_n && (state == IDLE || state == ACTIVE);
  assign out_valid = run_n && state == RESPONSE;
  assign out_data = out_valid ? result : 8192'b0;
  assign out_mask = out_valid ? mask : 64'b0;
  assign out_slots = out_valid ? slots : 4'b0;
  assign out_error = out_valid && failed;

  generate for (slot = 0; slot < 4; slot = slot + 1) begin : g_slot
    for (lane = 0; lane < 64; lane = lane + 1) begin : g_lane
      // Input masks apply on the first beat before held configuration is installed.
      wire participating = state == IDLE ? in_slots[slot] && in_mask[lane] :
                                                           slots[slot] && mask[lane];
      anvil_q1_ht2_mac_lane u_lane (
        .clk(clk), .rst_n(run_n), .enable(advance), .clear(clear),
        .beat_valid(beat), .fp16(in_fp16), .active_lane(participating),
        .activation(in_activation[16*slot+:16]), .weight(in_weights[16*lane+:16]),
        .product_context(phase2), .reduce_first(reduce_first),
        .reduce_second(reduce_second), .reduce_third(reduce_third),
        .result(lane_result[32*(64*slot+lane)+:32]),
        .arithmetic_error(lane_error[64*slot+lane])
      );
    end
  end endgenerate

  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      age <= 0;
      next_context <= 0;
      phase0 <= 0;
      phase1 <= 0;
      phase2 <= 0;
      mask <= 0;
      slots <= 0;
      format_fp16 <= 0;
      failed <= 0;
      result <= 0;
    end else begin
      if (advance) begin
        phase0 <= next_context;
        phase1 <= phase0;
        phase2 <= phase1;
      end
      case (state)
        IDLE: if (accept) begin
          mask <= in_mask;
          slots <= in_slots;
          format_fp16 <= in_fp16;
          result <= 0;
          age <= 0;
          failed <= !legal_beat;
          next_context <= 1;
          phase0 <= 0;
          if (!legal_beat) state <= BAD_DRAIN;
          else if (in_last) state <= DRAIN;
          else state <= ACTIVE;
        end
        ACTIVE: if (accept) begin
          if (!legal_beat) begin
            failed <= 1;
            age <= 0;
            state <= BAD_DRAIN;
          end else begin
            next_context <= next_context + 1'b1;
            if (in_last) begin
              age <= 0;
              state <= DRAIN;
            end
          end
        end
        DRAIN: begin
          if (age == 18) begin
            result <= lane_result;
            failed <= |lane_error;
            state <= RESPONSE;
          end else age <= age + 1'b1;
        end
        BAD_DRAIN: begin
          if (age == 8) begin
            result <= 0;
            state <= RESPONSE;
          end else age <= age + 1'b1;
        end
        RESPONSE: if (out_valid && out_ready) begin
          next_context <= 0;
          state <= IDLE;
        end
        default: begin
          failed <= 1;
          result <= 0;
          age <= 0;
          state <= BAD_DRAIN;
        end
      endcase
    end
  end
endmodule
