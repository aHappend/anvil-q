module anvil_q1_ht3_mac_lane (
  input wire clk, rst_n, enable, clear, beat_valid, active_lane, fp16,
  input wire [1:0] beat_context,
  input wire [15:0] activation, weight,
  input wire reduce_first, reduce_second, reduce_third,
  output wire [31:0] result,
  output wire arithmetic_error
);
  import anvil_q1_ht3_fp_pkg::*;
  reg [31:0] contexts [0:3];
  reg [31:0] reduction, result_q;
  reg active_q, failed;
  reg [1:0] product_context [0:3], addition_context [0:3];
  reg [1:0] addition_kind [0:3];
  wire product_valid, addition_valid;
  wire [31:0] product_data, addition_data;
  wire [31:0] activation_fp = expand16(activation, fp16);
  wire [31:0] weight_fp = expand16(weight, fp16);
  wire participating = clear ? active_lane : active_q;
  wire reduction_request = active_q &&
    (reduce_first || reduce_second || reduce_third);
  wire [31:0] feedback = addition_valid && addition_kind[3] == 0 &&
      addition_context[3] == product_context[3] ?
        addition_data : contexts[product_context[3]];
  wire [31:0] add_a = reduce_first ? contexts[0] :
    (reduce_second || reduce_third) ? reduction : feedback;
  wire [31:0] add_b = reduce_first ? contexts[1] :
    reduce_second ? contexts[2] : reduce_third ? contexts[3] : product_data;
  wire [1:0] request_kind =
    reduce_first ? 2'd1 : reduce_second ? 2'd2 : reduce_third ? 2'd3 : 2'd0;

  assign result = rst_n && active_q ? result_q : 32'b0;
  assign arithmetic_error = rst_n && active_q && failed;
  anvil_q1_ht3_fp32_mul u_product (
    .clk(clk), .rst_n(rst_n), .enable(enable),
    .in_valid(beat_valid && participating),
    .in_a(participating ? activation_fp : 32'b0),
    .in_b(participating ? weight_fp : 32'b0),
    .out_valid(product_valid), .out_data(product_data)
  );
  anvil_q1_ht3_fp32_add u_accumulate (
    .clk(clk), .rst_n(rst_n), .enable(enable),
    .in_valid(product_valid || reduction_request),
    .in_a(add_a), .in_b(add_b),
    .out_valid(addition_valid), .out_data(addition_data)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      contexts[0] <= 0;
      contexts[1] <= 0;
      contexts[2] <= 0;
      contexts[3] <= 0;
      reduction <= 0;
      result_q <= 0;
      active_q <= 0;
      failed <= 0;
    end else if (enable) begin
      if (clear) begin
        contexts[0] <= 0;
        contexts[1] <= 0;
        contexts[2] <= 0;
        contexts[3] <= 0;
        reduction <= 0;
        result_q <= 0;
        active_q <= active_lane;
        failed <= beat_valid && active_lane &&
          (fp32_nonfinite(activation_fp) || fp32_nonfinite(weight_fp));
      end else begin
        if (beat_valid && active_q &&
            (fp32_nonfinite(activation_fp) || fp32_nonfinite(weight_fp)))
          failed <= 1;
        if (product_valid && fp32_nonfinite(product_data)) failed <= 1;
        if (addition_valid) begin
          if (fp32_nonfinite(addition_data)) failed <= 1;
          if (addition_kind[3] == 0)
            contexts[addition_context[3]] <= addition_data;
          else if (addition_kind[3] == 3) result_q <= addition_data;
          else reduction <= addition_data;
        end
      end
    end
  end
  generate for (genvar stage = 0; stage < 4; stage = stage + 1) begin: g_tags
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        product_context[stage] <= 0;
        addition_context[stage] <= 0;
        addition_kind[stage] <= 0;
      end else if (enable) begin
        if (stage == 0) begin
          product_context[stage] <= beat_context;
          addition_context[stage] <= product_context[3];
          addition_kind[stage] <= request_kind;
        end else begin
          product_context[stage] <= product_context[stage-1];
          addition_context[stage] <= addition_context[stage-1];
          addition_kind[stage] <= addition_kind[stage-1];
        end
      end
    end
  end endgenerate
endmodule
