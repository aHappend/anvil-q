module anvil_q3_fp_dot8 (
  input wire clk, rst_n, flush, in_valid, out_ready,
  input wire in_fp16, in_awq,
  input wire [127:0] weight16, activation16,
  input wire [31:0] q_nibbles, z_nibbles,
  input wire [127:0] scale_f16,
  input wire [7:0] lane_mask,
  output wire in_ready, out_valid, out_error,
  output wire [31:0] out_dot,
  output wire [4:0] out_flags
);
  import anvil_q3_fp_pkg::*;

  reg mode_awq;
  reg [4:0] outstanding;
  wire mode_allowed = outstanding == 0 || mode_awq == in_awq;
  wire select_awq = outstanding == 0 ? in_awq : mode_awq;
  wire accept = in_valid && in_ready;
  wire retire = out_valid && out_ready;
  wire prefix_ready, prefix_valid, prefix_consume, prefix_error;
  wire [255:0] delta_operands, scale_operands, dequantized;
  wire [128:0] prefix_meta;
  wire [4:0] prefix_flags;
  wire [7:0] scale_errors;
  wire [127:0] masked_activations;
  wire [255:0] product_a, product_b, products;
  wire product_ready, product_valid, product_consume, product_error;
  wire [4:0] product_flags;
  wire [127:0] pairs0;
  wire [63:0] pairs1;
  wire [127:0] add0_a, add0_b;
  wire [63:0] add1_a, add1_b;
  wire add0_ready, add0_valid, add0_error;
  wire add1_ready, add1_valid, add1_error;
  wire add2_ready;
  wire [4:0] add0_flags, add1_flags;
  wire [31:0] root;
  wire [4:0] root_flags;
  wire root_error;

  assign in_ready = rst_n && !flush && mode_allowed &&
    (in_awq ? prefix_ready : product_ready);
  assign prefix_consume = select_awq && product_ready;
  assign product_consume = add0_ready;

  genvar lane;
  generate for (lane=0; lane<8; lane=lane+1) begin: lanes
    wire signed [4:0] delta =
      $signed({1'b0,q_nibbles[lane*4+:4]}) -
      $signed({1'b0,z_nibbles[lane*4+:4]});
    assign masked_activations[lane*16+:16] =
      lane_mask[lane] ? activation16[lane*16+:16] : 16'd0;
    assign delta_operands[lane*32+:32] =
      lane_mask[lane] ? delta32(delta) : 32'd0;
    assign scale_operands[lane*32+:32] = lane_mask[lane] ?
      widen16(scale_f16[lane*16+:16],1'b1) : 32'd0;
    assign scale_errors[lane] =
      lane_mask[lane] && scale_invalid(scale_f16[lane*16+:16]);
    assign product_a[lane*32+:32] = select_awq ?
      widen16(prefix_meta[lane*16+:16],prefix_meta[128]) :
      widen16(masked_activations[lane*16+:16],in_fp16);
    assign product_b[lane*32+:32] = select_awq ?
      dequantized[lane*32+:32] :
      (lane_mask[lane] ? widen16(weight16[lane*16+:16],in_fp16) : 32'd0);
  end endgenerate

  anvil_q3_fp_vector #(.LANES(8),.MULTIPLY(1),.META_W(129)) awq_prefix (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(in_valid && mode_allowed && in_awq),.in_ready(prefix_ready),
    .in_a(delta_operands),.in_b(scale_operands),
    .in_meta({in_fp16,masked_activations}),.in_flags(5'd0),
    .in_error(|scale_errors),
    .out_valid(prefix_valid),.out_ready(prefix_consume),.out_data(dequantized),
    .out_meta(prefix_meta),.out_flags(prefix_flags),.out_error(prefix_error)
  );
  anvil_q3_fp_vector #(.LANES(8),.MULTIPLY(1)) multiply (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(select_awq ? prefix_valid : (in_valid && mode_allowed && !in_awq)),
    .in_ready(product_ready),.in_a(product_a),.in_b(product_b),
    .in_meta(1'b0),.in_flags(select_awq ? prefix_flags : 5'd0),
    .in_error(select_awq && prefix_error),
    .out_valid(product_valid),.out_ready(product_consume),.out_data(products),
    .out_meta(),.out_flags(product_flags),.out_error(product_error)
  );

  generate for (lane=0; lane<4; lane=lane+1) begin: adjacent0
    assign add0_a[lane*32+:32] = products[(2*lane)*32+:32];
    assign add0_b[lane*32+:32] = products[(2*lane+1)*32+:32];
  end
  for (lane=0; lane<2; lane=lane+1) begin: adjacent1
    assign add1_a[lane*32+:32] = pairs0[(2*lane)*32+:32];
    assign add1_b[lane*32+:32] = pairs0[(2*lane+1)*32+:32];
  end endgenerate

  anvil_q3_fp_vector #(.LANES(4),.MULTIPLY(0)) reduce0 (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(product_valid),.in_ready(add0_ready),.in_a(add0_a),.in_b(add0_b),
    .in_meta(1'b0),.in_flags(product_flags),.in_error(product_error),
    .out_valid(add0_valid),.out_ready(add1_ready),.out_data(pairs0),
    .out_meta(),.out_flags(add0_flags),.out_error(add0_error)
  );
  anvil_q3_fp_vector #(.LANES(2),.MULTIPLY(0)) reduce1 (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(add0_valid),.in_ready(add1_ready),.in_a(add1_a),.in_b(add1_b),
    .in_meta(1'b0),.in_flags(add0_flags),.in_error(add0_error),
    .out_valid(add1_valid),.out_ready(add2_ready),.out_data(pairs1),
    .out_meta(),.out_flags(add1_flags),.out_error(add1_error)
  );
  anvil_q3_fp_vector #(.LANES(1),.MULTIPLY(0)) reduce2 (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(add1_valid),.in_ready(add2_ready),
    .in_a(pairs1[31:0]),.in_b(pairs1[63:32]),
    .in_meta(1'b0),.in_flags(add1_flags),.in_error(add1_error),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(root),
    .out_meta(),.out_flags(root_flags),.out_error(root_error)
  );
  assign out_dot = root;
  assign out_flags = root_flags;
  assign out_error = root_error;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      outstanding <= 0;
      mode_awq <= 0;
    end else if (flush) begin
      outstanding <= 0;
      mode_awq <= 0;
    end else begin
      if (accept && outstanding == 0) mode_awq <= in_awq;
      case ({accept,retire})
        2'b10: outstanding <= outstanding + 5'd1;
        2'b01: outstanding <= outstanding - 5'd1;
        default: outstanding <= outstanding;
      endcase
    end
  end
endmodule

module anvil_q3_fp_vector #(
  parameter LANES=1, MULTIPLY=0, META_W=1
) (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire [LANES*32-1:0] in_a, in_b,
  input wire [META_W-1:0] in_meta,
  input wire [4:0] in_flags,
  input wire in_error,
  output wire out_valid,
  input wire out_ready,
  output wire [LANES*32-1:0] out_data,
  output wire [META_W-1:0] out_meta,
  output wire [4:0] out_flags,
  output wire out_error
);
  reg [2:0] valid;
  reg [META_W+5:0] meta0, meta1, meta2;
  wire ready2 = !valid[2] || out_ready;
  wire ready1 = !valid[1] || ready2;
  wire ready0 = !valid[0] || ready1;
  wire [LANES*5-1:0] leaf_flags;
  reg [4:0] combined_flags;
  integer i;

  assign in_ready = rst_n && !flush && ready0;
  assign out_valid = rst_n && !flush && valid[2];
  assign out_meta = out_valid ? meta2[META_W-1:0] : {META_W{1'b0}};
  assign out_error = out_valid && meta2[META_W+5];
  assign out_flags = out_valid ? combined_flags : 5'd0;

  always @* begin
    combined_flags = meta2[META_W+:5];
    for (i=0; i<LANES; i=i+1)
      combined_flags = combined_flags | leaf_flags[i*5+:5];
  end

  genvar lane;
  generate for (lane=0; lane<LANES; lane=lane+1) begin: operators
    if (MULTIPLY != 0) begin: product
      anvil_q3_fp_mul leaf (
        .clk(clk),.rst_n(rst_n),.flush(flush),.in_valid(in_valid),
        .in_a(in_a[lane*32+:32]),.in_b(in_b[lane*32+:32]),
        .in_ready(),.out_valid(),.out_ready(out_ready),
        .out_data(out_data[lane*32+:32]),.out_flags(leaf_flags[lane*5+:5])
      );
    end else begin: sum
      anvil_q3_fp_add leaf (
        .clk(clk),.rst_n(rst_n),.flush(flush),.in_valid(in_valid),
        .in_a(in_a[lane*32+:32]),.in_b(in_b[lane*32+:32]),
        .in_ready(),.out_valid(),.out_ready(out_ready),
        .out_data(out_data[lane*32+:32]),.out_flags(leaf_flags[lane*5+:5])
      );
    end
  end endgenerate

  // Identical three-stage enables keep metadata and all arithmetic lanes atomic.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid <= 0;
      meta0 <= 0;
      meta1 <= 0;
      meta2 <= 0;
    end else if (flush) begin
      valid <= 0;
    end else begin
      if (ready0) begin
        valid[0] <= in_valid;
        if (in_valid) meta0 <= {in_error,in_flags,in_meta};
      end
      if (ready1) begin
        valid[1] <= valid[0];
        if (valid[0]) meta1 <= meta0;
      end
      if (ready2) begin
        valid[2] <= valid[1];
        if (valid[1]) meta2 <= meta1;
      end
    end
  end
endmodule
