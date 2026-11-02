module anvil_qn1_qknorm_rope #(
  parameter HEAD_DIM=128, NUM_Q_HEADS=32, NUM_KV_HEADS=8,
  parameter NUM_LAYERS=36, MAX_SEQ_LEN=40960,
  localparam SD=(HEAD_DIM==8 || HEAD_DIM==16 || HEAD_DIM==32 ||
    HEAD_DIM==64 || HEAD_DIM==128) ? HEAD_DIM : 1,
  localparam SH=SD>1 ? SD/2 : 1
) (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire in_is_key,
  input wire [5:0] in_head,
  input wire [31:0] in_layer, in_pos,
  input wire [SD*16-1:0] in_data, in_gamma,
  input wire [SH*16-1:0] in_cos, in_sin,
  output wire out_valid, out_error, out_is_key,
  output wire [5:0] out_head,
  output wire [31:0] out_layer, out_pos,
  output wire [SD*16-1:0] out_data,
  input wire out_ready
);
  import anvil_qn1_pkg::*;
  localparam LEGAL=(HEAD_DIM==8 || HEAD_DIM==16 || HEAD_DIM==32 ||
    HEAD_DIM==64 || HEAD_DIM==128) &&
    NUM_LAYERS>=1 && NUM_LAYERS<=36 && NUM_KV_HEADS>=1 && NUM_KV_HEADS<=8 &&
    NUM_Q_HEADS<=32 && (NUM_Q_HEADS==2*NUM_KV_HEADS || NUM_Q_HEADS==4*NUM_KV_HEADS) &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=40960;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: QK-Norm/RoPE geometry");
    assign in_ready=0;
    assign out_valid=0; assign out_error=0; assign out_is_key=0;
    assign out_head=0; assign out_layer=0; assign out_pos=0; assign out_data=0;
  end else begin: datapath
    reg owned, result_valid, result_failed, key_vector, head_failed;
    reg [7:0] age;
    reg [5:0] head;
    reg [31:0] layer, position;
    reg [SD*16-1:0] captured, gamma, result_data;
    reg [SH*16-1:0] cosine, sine;
    wire [SD-1:0] invalid_element;
    wire [SH-1:0] invalid_coefficient;
    wire invalid_head=(|invalid_element) || (|invalid_coefficient) ||
      in_layer>=NUM_LAYERS || in_pos>=MAX_SEQ_LEN ||
      (in_is_key ? in_head>=NUM_KV_HEADS : in_head>=NUM_Q_HEADS);
    wire [31:0] tree [1:255];
    wire [255:1] tree_failed;
    wire [23:0] sum_raw={tree[1][30:23]!=0,tree[1][22:0]};
    wire [5:0] sum_shift=sum_raw==0 ? 6'd0 : leading_zero32({8'd0,sum_raw})-6'd8;
    wire signed [11:0] sum_exponent=(tree[1][30:23]==0 ? -12'sd126 :
      $signed({4'd0,tree[1][30:23]})-12'sd127)-$signed({6'd0,sum_shift});
    wire [23:0] sum_mantissa=sum_raw << sum_shift;
    wire [32:0] mean_packed=round_pack32(1'b0,
      sum_exponent-12'($clog2(SD)),{sum_mantissa,3'd0});
    reg [31:0] mean;
    reg mean_failed;
    wire [31:0] epsilon_sum, root, reciprocal;
    wire epsilon_failed, root_failed, reciprocal_failed;
    wire root_ready, root_done, reciprocal_ready, reciprocal_done;
    wire [SD*16-1:0] rounded_output;
    wire [SD-1:0] rotated_failed;

    assign in_ready=rst_n && !flush && !owned;
    assign out_valid=rst_n && !flush && result_valid;
    assign out_error=out_valid && result_failed;
    assign out_is_key=out_valid && key_vector;
    assign out_head=out_valid ? head : 6'd0;
    assign out_layer=out_valid ? layer : 32'd0;
    assign out_pos=out_valid ? position : 32'd0;
    assign out_data=out_valid ? result_data : {SD*16{1'b0}};
    anvil_qn1_fp32_add epsilon_add (
      .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
      .a(mean),.b(anvil_qn1_pkg::EPSILON32),.in_error(mean_failed),
      .result(epsilon_sum),.out_error(epsilon_failed)
    );
    anvil_qn1_fp32_sqrt square_root (
      .clk(clk),.rst_n(rst_n),.flush(flush),.start(owned && age==45),
      .radicand(epsilon_sum),.in_error(epsilon_failed || head_failed),
      .ready(root_ready),.done(root_done),.result(root),.out_error(root_failed)
    );
    anvil_qn1_fp32_div inverse_root (
      .clk(clk),.rst_n(rst_n),.flush(flush),.start(owned && age==79),
      .numerator(32'h3f800000),.denominator(root),.in_error(root_failed),
      .ready(reciprocal_ready),.done(reciprocal_done),
      .result(reciprocal),.out_error(reciprocal_failed)
    );
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        owned<=0; result_valid<=0; result_failed<=0; key_vector<=0; head_failed<=0;
        age<=0; head<=0; layer<=0; position<=0;
        captured<=0; gamma<=0; cosine<=0; sine<=0; result_data<=0;
        mean<=0; mean_failed<=0;
      end else if (flush) begin
        owned<=0; result_valid<=0; result_failed<=0; head_failed<=0;
        age<=0; result_data<=0; mean<=0; mean_failed<=0;
      end else begin
        if (in_valid && in_ready) begin
          owned<=1; age<=0; head_failed<=invalid_head;
          captured<=in_data; gamma<=in_gamma;
          cosine<=in_pos==0 ? {SH{16'h3f80}} : in_cos;
          sine<=in_pos==0 ? {SH{16'h0000}} : in_sin;
          key_vector<=in_is_key; head<=in_head; layer<=in_layer; position<=in_pos;
        end
        if (owned && !result_valid) begin
          age<=age+1'b1;
          if (age==39) begin
            mean<=mean_packed[32] ? 32'd0 : mean_packed[31:0];
            mean_failed<=tree_failed[1] || mean_packed[32] || head_failed;
          end
          if (age==132) begin
            result_valid<=1;
            result_failed<=head_failed || (|rotated_failed);
            result_data<=head_failed || (|rotated_failed) ?
              {SD*16{1'b0}} : rounded_output;
          end
        end
        if (out_valid && out_ready) begin
          owned<=0; result_valid<=0; result_failed<=0; age<=0;
        end
      end
    end
    genvar i, level, node, pair_index;
    for (i=0;i<128;i=i+1) begin: squares
      if (i<SD) begin: active_coordinate
        assign invalid_element[i]=bf16_invalid(in_data[i*16+:16]) ||
          bf16_invalid(in_gamma[i*16+:16]);
        anvil_qn1_fp32_mul square (
          .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
          .a({captured[i*16+:16],16'd0}),.b({captured[i*16+:16],16'd0}),
          .in_error(head_failed),.result(tree[128+i]),.out_error(tree_failed[128+i])
        );
      end else begin: alignment_padding
        assign tree[128+i]=32'd0;
        assign tree_failed[128+i]=1'b0;
      end
    end
    for (level=0;level<7;level=level+1) begin: sum_levels
      for (node=0;node<(64>>level);node=node+1) begin: adjacent_pairs
        localparam INDEX=(64>>level)+node;
        anvil_qn1_fp32_add sum (
          .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
          .a(tree[2*INDEX]),.b(tree[2*INDEX+1]),
          .in_error(tree_failed[2*INDEX] || tree_failed[2*INDEX+1]),
          .result(tree[INDEX]),.out_error(tree_failed[INDEX])
        );
      end
    end
    wire [31:0] scaled [0:SD-1], gamma_product [0:SD-1];
    wire [SD-1:0] scale_failed, gamma_failed;
    reg [SD*16-1:0] unit_vector, normalized_head;
    reg [SD-1:0] unit_failed, normalized_failed;
    for (i=0;i<SD;i=i+1) begin: normalize
      wire [16:0] unit_rounded=round_bf16(scaled[i]);
      wire [16:0] gamma_rounded=round_bf16(gamma_product[i]);
      anvil_qn1_fp32_mul x_scale (
        .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
        .a({captured[i*16+:16],16'd0}),.b(reciprocal),.in_error(reciprocal_failed),
        .result(scaled[i]),.out_error(scale_failed[i])
      );
      anvil_qn1_fp32_mul gamma_scale (
        .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
        .a({unit_vector[i*16+:16],16'd0}),.b({gamma[i*16+:16],16'd0}),
        .in_error(unit_failed[i]),.result(gamma_product[i]),.out_error(gamma_failed[i])
      );
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          unit_vector[i*16+:16]<=0; normalized_head[i*16+:16]<=0;
          unit_failed[i]<=0; normalized_failed[i]<=0;
        end else if (flush) begin
          unit_vector[i*16+:16]<=0; normalized_head[i*16+:16]<=0;
          unit_failed[i]<=0; normalized_failed[i]<=0;
        end else begin
          unit_vector[i*16+:16]<=unit_rounded[15:0];
          unit_failed[i]<=scale_failed[i] || unit_rounded[16];
          normalized_head[i*16+:16]<=gamma_rounded[15:0];
          normalized_failed[i]<=gamma_failed[i] || gamma_rounded[16];
        end
      end
    end
    for (pair_index=0;pair_index<SH;pair_index=pair_index+1) begin: split_half_rope
      assign invalid_coefficient[pair_index]=bf16_invalid(in_cos[pair_index*16+:16]) ||
        bf16_invalid(in_sin[pair_index*16+:16]);
      wire [31:0] x={normalized_head[pair_index*16+:16],16'd0};
      wire [31:0] y={normalized_head[(pair_index+SH)*16+:16],16'd0};
      wire [31:0] c={cosine[pair_index*16+:16],16'd0};
      wire [31:0] s={sine[pair_index*16+:16],16'd0};
      wire pair_failed=normalized_failed[pair_index] || normalized_failed[pair_index+SH];
      wire [31:0] xc, ys, xs, yc, rotated_x, rotated_y;
      wire xc_failed, ys_failed, xs_failed, yc_failed, x_failed, y_failed;
      wire [16:0] final_x=round_bf16(rotated_x);
      wire [16:0] final_y=round_bf16(rotated_y);
      anvil_qn1_fp32_mul mul_xc (
        .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
        .a(x),.b(c),.in_error(pair_failed),.result(xc),.out_error(xc_failed)
      );
      anvil_qn1_fp32_mul mul_ys (
        .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
        .a(y),.b(s),.in_error(pair_failed),.result(ys),.out_error(ys_failed)
      );
      anvil_qn1_fp32_mul mul_xs (
        .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
        .a(x),.b(s),.in_error(pair_failed),.result(xs),.out_error(xs_failed)
      );
      anvil_qn1_fp32_mul mul_yc (
        .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
        .a(y),.b(c),.in_error(pair_failed),.result(yc),.out_error(yc_failed)
      );
      anvil_qn1_fp32_add rotate_x (
        .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
        .a(xc),.b({!ys[31],ys[30:0]}),.in_error(xc_failed || ys_failed),
        .result(rotated_x),.out_error(x_failed)
      );
      anvil_qn1_fp32_add rotate_y (
        .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
        .a(xs),.b(yc),.in_error(xs_failed || yc_failed),
        .result(rotated_y),.out_error(y_failed)
      );
      assign rounded_output[pair_index*16+:16]=final_x[15:0];
      assign rounded_output[(pair_index+SH)*16+:16]=final_y[15:0];
      assign rotated_failed[pair_index]=x_failed || final_x[16];
      assign rotated_failed[pair_index+SH]=y_failed || final_y[16];
    end
  end endgenerate
endmodule
