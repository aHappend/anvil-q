module anvil_q1_ht2_mac_lane (
  input wire clk, rst_n, enable, clear,
  input wire beat_valid, fp16, active_lane,
  input wire [15:0] activation, weight,
  input wire [1:0] product_context,
  input wire reduce_first, reduce_second, reduce_third,
  output wire [31:0] result,
  output wire arithmetic_error
);
  import anvil_q1_ht2_fp_pkg::*;
  reg [31:0] context0, context1, context2, context3;
  reg [2:0] tag0, tag1, tag2, tag3;
  reg failed;
  wire product_valid, add_valid;
  wire [31:0] product, sum;
  wire reducing = reduce_first || reduce_second || reduce_third;
  wire [2:0] issue_tag = reduce_first ? 3'd4 : reduce_second ? 3'd5 :
                                            reduce_third ? 3'd6 : {1'b0, product_context};
  wire [31:0] current_context = product_context == 0 ? context0 :
    product_context == 1 ? context1 : product_context == 2 ? context2 : context3;
  wire [31:0] accumulation_operand =
    add_valid && tag3 == {1'b0, product_context} ? sum : current_context;
  wire [31:0] first_left = add_valid && tag3 == 0 ? sum : context0;
  wire [31:0] first_right = add_valid && tag3 == 1 ? sum : context1;
  wire [31:0] add_a = reduce_first ? first_left :
                                  (reduce_second || reduce_third) ? sum : accumulation_operand;
  wire [31:0] add_b = reduce_first ? first_right : reduce_second ? context2 :
                                                    reduce_third ? context3 : product;
  wire issue_valid = active_lane && (product_valid || reducing);

  anvil_q1_ht2_fp16_mul u_multiply (
    .clk(clk), .rst_n(rst_n), .enable(enable),
    .in_valid(beat_valid && active_lane), .in_fp16(fp16),
    .in_a(activation), .in_b(weight), .out_valid(product_valid), .out_data(product)
  );
  anvil_q1_ht2_fp32_add u_accumulate (
    .clk(clk), .rst_n(rst_n), .enable(enable), .in_valid(issue_valid),
    .in_a(add_a), .in_b(add_b), .out_valid(add_valid), .out_data(sum)
  );
  assign result = rst_n && active_lane ? sum : 32'b0;
  assign arithmetic_error = rst_n && active_lane &&
    (failed || (add_valid && fp32_nonfinite(sum)));

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      context0 <= 0;
      context1 <= 0;
      context2 <= 0;
      context3 <= 0;
      tag0 <= 0;
      tag1 <= 0;
      tag2 <= 0;
      tag3 <= 0;
      failed <= 0;
    end else if (enable) begin
      tag0 <= issue_tag;
      tag1 <= tag0;
      tag2 <= tag1;
      tag3 <= tag2;
      if (clear) begin
        context0 <= 0;
        context1 <= 0;
        context2 <= 0;
        context3 <= 0;
        failed <= 0;
      end else begin
        if (add_valid) case (tag3)
          0: context0 <= sum;
          1: context1 <= sum;
          2: context2 <= sum;
          3: context3 <= sum;
          default: begin end
        endcase
        if ((product_valid && fp32_nonfinite(product)) ||
            (add_valid && fp32_nonfinite(sum))) failed <= 1;
      end
    end
  end
endmodule
