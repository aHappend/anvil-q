module anvil_qn1_fp32_sqrt (
  input wire clk, rst_n, flush, start,
  input wire [31:0] radicand,
  input wire in_error,
  output wire ready, done,
  output wire [31:0] result,
  output wire out_error
);
  import anvil_qn1_pkg::*;
  wire [23:0] raw = {radicand[30:23] != 0,radicand[22:0]};
  wire [5:0] shift = raw == 0 ? 6'd0 : leading_zero32({8'd0,raw})-6'd8;
  wire [23:0] normalized = raw << shift;
  wire signed [11:0] input_exponent =
    (radicand[30:23] == 0 ? -12'sd126 :
     $signed({4'd0,radicand[30:23]})-12'sd127)-$signed({6'd0,shift});
  reg active, done_reg, failed, negative;
  reg [5:0] cycle;
  reg [53:0] pairs;
  reg [28:0] remainder;
  reg [26:0] root;
  reg signed [11:0] exponent;
  reg [31:0] value, rounded_value;
  reg result_failed, rounded_failed;
  wire [30:0] shifted_remainder = {remainder,pairs[53:52]};
  wire [30:0] trial = {2'd0,root,2'b01};
  wire take_bit = shifted_remainder >= trial;
  wire [30:0] next_remainder = take_bit ?
    shifted_remainder-trial : shifted_remainder;
  wire [26:0] sticky_root = {root[26:1],root[0] | (|remainder)};
  wire [32:0] packed_result = round_pack32(negative,exponent,sticky_root);
  assign ready = rst_n && !flush && !active;
  assign done = rst_n && !flush && done_reg;
  assign result = rst_n && !flush ? value : 32'd0;
  assign out_error = rst_n && !flush && result_failed;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active <= 0; done_reg <= 0; failed <= 0; negative <= 0; cycle <= 0;
      pairs <= 0; remainder <= 0; root <= 0; exponent <= 0;
      value <= 0; result_failed <= 0; rounded_value <= 0; rounded_failed <= 0;
    end else if (flush) begin
      active <= 0; done_reg <= 0; value <= 0; result_failed <= 0;
    end else begin
      done_reg <= 0;
      if (start && ready) begin
        active <= 1; cycle <= 1;
        pairs <= {30'd0,normalized} << (input_exponent[0] ? 6'd30 : 6'd29);
        remainder <= 0; root <= 0;
        exponent <= input_exponent >>> 1;
        negative <= radicand[31] && raw == 0;
        failed <= in_error || fp32_invalid(radicand) || (radicand[31] && raw != 0);
      end else if (active) begin
        cycle <= cycle+1'b1;
        if (cycle <= 27) begin
          pairs <= {pairs[51:0],2'd0};
          remainder <= next_remainder[28:0];
          root <= {root[25:0],take_bit};
        end else if (cycle == 28) begin
          rounded_value <= failed || packed_result[32] ? 32'd0 : packed_result[31:0];
          rounded_failed <= failed || packed_result[32];
        end else if (cycle == 33) begin
          value <= rounded_value; result_failed <= rounded_failed;
          active <= 0; done_reg <= 1;
        end
      end
    end
  end
endmodule
