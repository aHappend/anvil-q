module anvil_qn1_tensor_array (
  input wire clk, rst_n, flush, in_valid, in_w4,
  output wire in_ready,
  input wire [1023:0] q, z,
  input wire [4095:0] scale_bf16, activation_bf16, weight_bf16,
  input wire [255:0] lane_mask,
  input wire [31:0] in_tag,
  output wire out_valid,
  output wire [31:0] out_sum, out_tag,
  output wire out_error,
  input wire out_ready
);
  import anvil_qn1_pkg::*;
  reg [48:0] valid;
  reg [31:0] tags [0:48];
  wire ce = !valid[48] || out_ready;
  reg [31:0] captured_a [0:255], captured_b [0:255];
  reg [31:0] activation [0:255][0:3];
  reg [255:0] input_failed;
  wire [31:0] weights [0:255], products [0:255];
  wire [255:0] weight_failed, product_failed;
  wire [31:0] tree [1:511];
  wire [511:1] tree_failed;
  assign in_ready = rst_n && !flush && ce;
  assign out_valid = rst_n && !flush && valid[48];
  assign out_sum = rst_n && !flush && valid[48] ? tree[1] : 32'd0;
  assign out_tag = rst_n && !flush && valid[48] ? tags[48] : 32'd0;
  assign out_error = out_valid && tree_failed[1];
  integer stage;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid <= 0;
      for (stage=0; stage<=48; stage=stage+1) tags[stage] <= 0;
    end else if (flush) begin
      valid <= 0;
      for (stage=0; stage<=48; stage=stage+1) tags[stage] <= 0;
    end else if (ce) begin
      valid <= {valid[47:0],in_valid};
      tags[0] <= in_valid ? in_tag : 32'd0;
      for (stage=1; stage<=48; stage=stage+1) tags[stage] <= tags[stage-1];
    end
  end
  genvar lane, level, node;
  generate
    for (lane=0; lane<256; lane=lane+1) begin: lanes
      wire [31:0] quantized_delta = delta32(q[lane*4+:4],z[lane*4+:4]);
      wire invalid_activation = bf16_invalid(activation_bf16[lane*16+:16]);
      wire invalid_weight = in_w4 ? bf16_scale_invalid(scale_bf16[lane*16+:16]) :
        bf16_invalid(weight_bf16[lane*16+:16]);
      integer delay_index;
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          captured_a[lane] <= 0; captured_b[lane] <= 0; input_failed[lane] <= 0;
          for (delay_index=0; delay_index<4; delay_index=delay_index+1)
            activation[lane][delay_index] <= 0;
        end else if (flush) begin
          captured_a[lane] <= 0; captured_b[lane] <= 0; input_failed[lane] <= 0;
          for (delay_index=0; delay_index<4; delay_index=delay_index+1)
            activation[lane][delay_index] <= 0;
        end else if (ce) begin
          captured_a[lane] <= !in_valid || !lane_mask[lane] ? 32'd0 :
            in_w4 ? quantized_delta : 32'h3f800000;
          captured_b[lane] <= !in_valid || !lane_mask[lane] ? 32'd0 :
            in_w4 ? {scale_bf16[lane*16+:16],16'd0} :
                    {weight_bf16[lane*16+:16],16'd0};
          activation[lane][0] <= in_valid && lane_mask[lane] ?
            {activation_bf16[lane*16+:16],16'd0} : 32'd0;
          input_failed[lane] <= in_valid && lane_mask[lane] &&
            (invalid_activation || invalid_weight);
          for (delay_index=1; delay_index<4; delay_index=delay_index+1)
            activation[lane][delay_index] <= activation[lane][delay_index-1];
        end
      end
      // The four-stage weight path requires four activation delay intervals.
      reg [31:0] delayed_activation;
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) delayed_activation <= 0;
        else if (flush) delayed_activation <= 0;
        else if (ce) delayed_activation <= activation[lane][3];
      end
      anvil_qn1_fp32_mul weight_formation (
        .clk(clk),.rst_n(rst_n),.flush(flush),.ce(ce),
        .a(captured_a[lane]),.b(captured_b[lane]),.in_error(input_failed[lane]),
        .result(weights[lane]),.out_error(weight_failed[lane])
      );
      anvil_qn1_fp32_mul activation_multiply (
        .clk(clk),.rst_n(rst_n),.flush(flush),.ce(ce),
        .a(weights[lane]),.b(delayed_activation),.in_error(weight_failed[lane]),
        .result(products[lane]),.out_error(product_failed[lane])
      );
      assign tree[256+lane] = products[lane];
      assign tree_failed[256+lane] = product_failed[lane];
    end
    for (level=0; level<8; level=level+1) begin: reduction_levels
      for (node=0; node<(128>>level); node=node+1) begin: adjacent_pairs
        localparam INDEX = (128>>level)+node;
        anvil_qn1_fp32_add add (
          .clk(clk),.rst_n(rst_n),.flush(flush),.ce(ce),
          .a(tree[2*INDEX]),.b(tree[2*INDEX+1]),
          .in_error(tree_failed[2*INDEX] || tree_failed[2*INDEX+1]),
          .result(tree[INDEX]),.out_error(tree_failed[INDEX])
        );
      end
    end
  endgenerate
endmodule
