module anvil_q1_ht3_tensor_array (
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
  reg [1:0] next_context;
  reg [63:0] mask_q;
  reg [3:0] slots_q;
  reg fp16_q, failed;
  reg [8191:0] result_q;
  wire [8191:0] lane_data;
  wire [255:0] lane_error;
  wire accept = in_valid && in_ready;
  wire configuration_match =
    in_slots == slots_q && in_mask == mask_q && in_fp16 == fp16_q;
  wire legal_beat = state == IDLE ? in_first && in_slots != 0 :
    state == ACTIVE && !in_first && configuration_match;
  wire beat = accept && legal_beat;
  wire clear = beat && state == IDLE;
  wire advance = run_n && state != RESPONSE;
  wire reduce_first = state == DRAIN && age == 8;
  wire reduce_second = state == DRAIN && age == 13;
  wire reduce_third = state == DRAIN && age == 18;

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  assign in_ready = run_n && (state == IDLE || state == ACTIVE);
  assign out_valid = run_n && state == RESPONSE;
  assign out_data = out_valid ? result_q : 8192'b0;
  assign out_mask = out_valid ? mask_q : 64'b0;
  assign out_slots = out_valid ? slots_q : 4'b0;
  assign out_error = out_valid && failed;

  generate for (genvar s = 0; s < 4; s = s + 1) begin: g_slot
    for (genvar row = 0; row < 64; row = row + 1) begin: g_row
      wire participating = state == IDLE ?
        in_slots[s] && in_mask[row] : slots_q[s] && mask_q[row];
      anvil_q1_ht3_mac_lane u_lane (
        .clk(clk), .rst_n(rst_n), .enable(advance), .clear(clear),
        .beat_valid(beat), .active_lane(participating), .fp16(in_fp16),
        .beat_context(state == IDLE ? 2'b0 : next_context),
        .activation(in_activation[16*s+:16]), .weight(in_weights[16*row+:16]),
        .reduce_first(reduce_first), .reduce_second(reduce_second),
        .reduce_third(reduce_third),
        .result(lane_data[32*(64*s+row)+:32]),
        .arithmetic_error(lane_error[64*s+row])
      );
    end
  end endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      age <= 0;
      next_context <= 0;
      mask_q <= 0;
      slots_q <= 0;
      fp16_q <= 0;
      failed <= 0;
      result_q <= 0;
    end else if (run_n) begin
      case (state)
        IDLE: if (accept) begin
          mask_q <= in_mask;
          slots_q <= in_slots;
          fp16_q <= in_fp16;
          failed <= !legal_beat;
          result_q <= 0;
          age <= 0;
          next_context <= 1;
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
          if (age == 23) begin
            result_q <= lane_data;
            failed <= |lane_error;
            state <= RESPONSE;
          end else age <= age + 1'b1;
        end
        BAD_DRAIN: begin
          if (age == 9) begin
            result_q <= 0;
            state <= RESPONSE;
          end else age <= age + 1'b1;
        end
        RESPONSE: if (out_ready) begin
          next_context <= 0;
          state <= IDLE;
        end
        default: begin
          failed <= 1;
          age <= 0;
          state <= BAD_DRAIN;
        end
      endcase
    end
  end
endmodule
