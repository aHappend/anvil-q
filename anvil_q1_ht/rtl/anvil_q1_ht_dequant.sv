module anvil_q1_ht_dequant (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  output wire in_ready,
  input wire in_bf16,
  input wire [31:0] in_qweight,
  input wire [31:0] in_qzero,
  input wire [2:0] in_lane,
  input wire [15:0] in_value,
  output wire out_valid,
  input wire out_ready,
  output wire signed [36:0] out_weight,
  output wire out_error
);
  reg input_valid, result_valid;
  reg bf16, invalid, result_error;
  reg signed [4:0] difference;
  reg [31:0] scale;
  reg signed [31:0] converted;
  (* multstyle = "dsp" *) reg signed [36:0] product;
  wire [4:0] shift = anvil_q1_ht_numeric_pkg::awq_shift(in_lane);
  wire [3:0] qweight = in_qweight >> shift;
  wire [3:0] qzero = in_qzero >> shift;
  wire result_ready = !result_valid || out_ready;
  wire input_ready = !input_valid || result_ready;

  assign in_ready = rst_n && input_ready;
  assign out_valid = rst_n && result_valid;
  assign out_weight = out_valid && !result_error ? product : 37'sd0;
  assign out_error = out_valid && result_error;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      input_valid <= 0;
      result_valid <= 0;
      bf16 <= 0;
      invalid <= 0;
      result_error <= 0;
      difference <= 0;
      scale <= 0;
      converted <= 0;
      product <= 0;
    end else begin
      if (input_ready) begin
        input_valid <= in_valid;
        if (in_valid) begin
          bf16 <= in_bf16;
          difference <= $signed({1'b0, qweight}) - $signed({1'b0, qzero});
          scale <= anvil_q1_ht_numeric_pkg::fp16_scale(in_value);
          converted <= anvil_q1_ht_numeric_pkg::bf16_q16(in_value);
          invalid <= in_bf16 ? anvil_q1_ht_numeric_pkg::bf16_invalid(in_value) :
                              anvil_q1_ht_numeric_pkg::scale_invalid(in_value);
        end
      end
      if (result_ready) begin
        result_valid <= input_valid;
        if (input_valid) begin
          if (bf16) product <= {{5{converted[31]}}, converted};
          else product <= difference * $signed({1'b0, scale});
          result_error <= invalid;
        end
      end
    end
  end
endmodule
