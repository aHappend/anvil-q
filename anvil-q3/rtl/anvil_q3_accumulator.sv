module anvil_q3_accumulator (
  input wire clk, rst_n, flush,
  input wire in_valid,
  output wire in_ready,
  input wire in_first,
  input wire signed [127:0] in_value,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire signed [127:0] out_sum
);
  reg busy, result_valid, result_error, carry;
  reg [2:0] segment;
  reg [127:0] accumulator, base, operand, partial;
  reg [127:0] result;
  wire [16:0] segment_sum =
    {1'b0,base[segment*16+:16]} +
    {1'b0,operand[segment*16+:16]} + {16'd0,carry};
  wire [127:0] completed = {segment_sum[15:0],partial[111:0]};

  assign in_ready = rst_n && !flush && !busy && (!result_valid || out_ready);
  assign out_valid = rst_n && !flush && result_valid;
  assign out_error = out_valid && result_error;
  assign out_sum = out_valid ? $signed(result) : 128'sd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy <= 0;
      result_valid <= 0;
      result_error <= 0;
      carry <= 0;
      segment <= 0;
      accumulator <= 0;
      base <= 0;
      operand <= 0;
      partial <= 0;
      result <= 0;
    end else if (flush) begin
      busy <= 0;
      result_valid <= 0;
      result_error <= 0;
      accumulator <= 0;
    end else begin
      if (result_valid && out_ready) result_valid <= 0;
      if (in_valid && in_ready) begin
        busy <= 1;
        base <= in_first ? 128'd0 : accumulator;
        operand <= in_value;
        segment <= 0;
        partial <= 0;
        carry <= 0;
      end else if (busy) begin
        partial[segment*16+:16] <= segment_sum[15:0];
        carry <= segment_sum[16];
        if (segment == 3'd7) begin
          busy <= 0;
          accumulator <= completed;
          result <= completed;
          result_error <= (base[127] == operand[127]) &&
                          (completed[127] != base[127]);
          result_valid <= 1;
        end else segment <= segment+1'b1;
      end
    end
  end
endmodule
