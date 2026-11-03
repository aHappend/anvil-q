module anvil_q4_dequant (
  input wire clk, rst_n, flush,
  input wire in_valid,
  output wire in_ready,
  input wire lane_active,
  input wire [1:0] weight_format,
  input wire activation_format,
  input wire asymmetric,
  input wire [2:0] lane,
  input wire [31:0] payload, zero_point, scale,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] result,
  output wire [4:0] flags,
  output wire error
);
  import anvil_q4_fp_pkg::*;

  localparam [3:0] IDLE = 0, DECODE = 1, INTEGER_ISSUE = 2, INTEGER_WAIT = 3,
    MULTIPLY_ISSUE = 4, MULTIPLY_WAIT = 5, NARROW_ISSUE = 6, NARROW_WAIT = 7,
    WIDEN_ISSUE = 8, WIDEN_WAIT = 9, RESPONSE = 10;
  reg [3:0] state;
  reg active, native_fp16, unsigned_weights;
  reg [1:0] format;
  reg [2:0] selected_lane;
  reg [31:0] packed_payload, zero, group_scale, operand, result_register;
  reg [4:0] flag_register;
  reg failed;

  function automatic [4:0] awq_shift(input [2:0] index);
    begin
      case (index)
        0: awq_shift = 0;
        1: awq_shift = 16;
        2: awq_shift = 4;
        3: awq_shift = 20;
        4: awq_shift = 8;
        5: awq_shift = 24;
        6: awq_shift = 12;
        default: awq_shift = 28;
      endcase
    end
  endfunction

  wire [31:0] shifted_w4 = packed_payload >> awq_shift(selected_lane);
  wire [31:0] shifted_w8 = packed_payload >> {selected_lane[1:0], 3'b000};
  wire [31:0] w4_integer = unsigned_weights ? {28'd0, shifted_w4[3:0]} :
    {{28{shifted_w4[3]}}, shifted_w4[3:0]};
  wire [31:0] w8_integer = unsigned_weights ? {24'd0, shifted_w8[7:0]} :
    {{24{shifted_w8[7]}}, shifted_w8[7:0]};
  wire [31:0] integer_weight = format == 1 ? w4_integer : w8_integer;
  wire [31:0] integer_zero = unsigned_weights ? zero : 32'd0;
  wire malformed_scale = group_scale[31] || is_zero(group_scale) ||
    group_scale[30:23] == 8'hff;
  wire malformed_zero = unsigned_weights &&
    (format == 1 ? zero[31:4] != 0 : zero[31:8] != 0);

  wire fp_in_valid = state == INTEGER_ISSUE || state == MULTIPLY_ISSUE ||
    state == NARROW_ISSUE || state == WIDEN_ISSUE;
  wire fp_in_ready, fp_out_valid;
  wire fp_out_ready = state == INTEGER_WAIT || state == MULTIPLY_WAIT ||
    state == NARROW_WAIT || state == WIDEN_WAIT;
  wire [3:0] fp_op = state == INTEGER_ISSUE ? 4'd9 :
    state == MULTIPLY_ISSUE ? 4'd2 : state == NARROW_ISSUE ? 4'd7 :
    (format == 0 && native_fp16 ? 4'd6 : 4'd5);
  wire [31:0] fp_b = state == MULTIPLY_ISSUE ? group_scale : 32'd0;
  wire [31:0] fp_result;
  wire [4:0] fp_flags;

  anvil_q4_fp32 arithmetic (
    .clk(clk), .rst_n(rst_n), .flush(flush),
    .in_valid(fp_in_valid), .in_ready(fp_in_ready),
    .op(fp_op), .a(operand), .b(fp_b),
    .out_valid(fp_out_valid), .out_ready(fp_out_ready),
    .result(fp_result), .flags(fp_flags)
  );

  assign in_ready = rst_n && !flush && state == IDLE;
  assign out_valid = rst_n && !flush && state == RESPONSE;
  assign result = rst_n && !flush ? result_register : 32'd0;
  assign flags = rst_n && !flush ? flag_register : 5'd0;
  assign error = out_valid && failed;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      active <= 1'b0;
      native_fp16 <= 1'b0;
      unsigned_weights <= 1'b0;
      format <= 0;
      selected_lane <= 0;
      packed_payload <= 0;
      zero <= 0;
      group_scale <= 0;
      operand <= 0;
      result_register <= 0;
      flag_register <= 0;
      failed <= 1'b0;
    end else if (flush) begin
      state <= IDLE;
      failed <= 1'b0;
      result_register <= 0;
      flag_register <= 0;
    end else case (state)
      IDLE: if (in_valid && in_ready) begin
        active <= lane_active;
        native_fp16 <= activation_format;
        unsigned_weights <= asymmetric;
        format <= weight_format;
        selected_lane <= lane;
        packed_payload <= payload;
        zero <= zero_point;
        group_scale <= scale;
        failed <= 1'b0;
        flag_register <= 0;
        result_register <= 0;
        state <= DECODE;
      end
      DECODE: begin
        if (!active) state <= RESPONSE;
        else if (format > 2 || (format == 2 && selected_lane[2]) ||
            (format == 0 && packed_payload[31:16] != 0) ||
            (format != 0 && (malformed_scale || malformed_zero))) begin
          failed <= 1'b1;
          state <= RESPONSE;
        end else if (format == 0) begin
          operand <= {16'd0, packed_payload[15:0]};
          state <= WIDEN_ISSUE;
        end else begin
          operand <= integer_weight - integer_zero;
          state <= INTEGER_ISSUE;
        end
      end
      INTEGER_ISSUE: if (fp_in_ready) state <= INTEGER_WAIT;
      INTEGER_WAIT: if (fp_out_valid) begin
        operand <= fp_result;
        flag_register <= flag_register | fp_flags;
        state <= MULTIPLY_ISSUE;
      end
      MULTIPLY_ISSUE: if (fp_in_ready) state <= MULTIPLY_WAIT;
      MULTIPLY_WAIT: if (fp_out_valid) begin
        operand <= fp_result;
        flag_register <= flag_register | fp_flags;
        state <= NARROW_ISSUE;
      end
      NARROW_ISSUE: if (fp_in_ready) state <= NARROW_WAIT;
      NARROW_WAIT: if (fp_out_valid) begin
        operand <= fp_result;
        flag_register <= flag_register | fp_flags;
        state <= WIDEN_ISSUE;
      end
      WIDEN_ISSUE: if (fp_in_ready) state <= WIDEN_WAIT;
      WIDEN_WAIT: if (fp_out_valid) begin
        result_register <= fp_result;
        flag_register <= flag_register | fp_flags;
        state <= RESPONSE;
      end
      RESPONSE: if (out_ready) state <= IDLE;
      default: begin
        failed <= 1'b1;
        state <= RESPONSE;
      end
    endcase
  end
endmodule
