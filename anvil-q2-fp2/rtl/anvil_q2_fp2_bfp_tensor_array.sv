module anvil_q2_fp2_bfp_tensor_array (
  input wire clk, rst_n, flush,
  input wire w_valid,
  input wire [511:0] w_data,
  input wire [15:0] w_scale,
  input wire w_format, w_first, w_last,
  input wire [31:0] w_tag,
  input wire w_error,
  output wire w_ready,
  input wire in_valid,
  input wire [2047:0] in_a,
  input wire [127:0] in_mask,
  input wire in_first, in_last,
  input wire [31:0] in_tag,
  output wire in_ready,
  output wire out_valid,
  output wire [31:0] out_data,
  output wire out_first, out_last,
  output wire [31:0] out_tag,
  output wire out_error,
  input wire out_ready
);
  wire weight_valid, weight_first, weight_last, weight_error;
  wire [2047:0] weight_data;
  wire [31:0] weight_tag;
  reg [37:0] valid;
  reg [37:0] first_pipe, last_pipe;
  reg [31:0] tag_pipe [0:37];
  wire enable=!valid[37] || out_ready;
  wire pair_fire=in_valid && in_ready;
  anvil_q2_fp2_ping_pong_prefetch ping_pong_prefetch (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .w_valid(w_valid),.w_ready(w_ready),.w_data(w_data),.w_scale(w_scale),
    .w_format(w_format),.w_first(w_first),.w_last(w_last),
    .w_tag(w_tag),.w_error(w_error),
    .tile_valid(weight_valid),.tile_ready(pair_fire),
    .tile_data(weight_data),.tile_first(weight_first),.tile_last(weight_last),
    .tile_tag(weight_tag),.tile_error(weight_error)
  );
  assign in_ready=rst_n && !flush && enable && weight_valid;
  assign out_valid=rst_n && !flush && valid[37];
  assign out_first=out_valid && first_pipe[37];
  assign out_last=out_valid && last_pipe[37];
  assign out_tag=out_valid ? tag_pipe[37] : 32'd0;

  reg [2047:0] a_pipe [0:5], b_pipe [0:5];
  reg [5:0] error_pipe;
  wire [127:0] input_nonfinite;
  wire [2047:0] masked_a, masked_b;
  wire [1023:0] maximum_a [0:5], maximum_b [0:5];
  genvar lane;
  generate for (lane=0;lane<128;lane=lane+1) begin: capture_lanes
    wire [15:0] a=in_mask[lane] ? in_a[16*lane+:16] : 16'd0;
    wire [15:0] b=in_mask[lane] ? weight_data[16*lane+:16] : 16'd0;
    assign masked_a[16*lane+:16]=a;
    assign masked_b[16*lane+:16]=b;
    assign input_nonfinite[lane]=(&a[14:7]) || (&b[14:7]);
    assign maximum_a[0][8*lane+:8]=a_pipe[0][16*lane+7+:8]==0 ?
      8'd1 : a_pipe[0][16*lane+7+:8];
    assign maximum_b[0][8*lane+:8]=b_pipe[0][16*lane+7+:8]==0 ?
      8'd1 : b_pipe[0][16*lane+7+:8];
  end endgenerate

  wire association_error=weight_error || weight_tag!=in_tag ||
    weight_first!=in_first || weight_last!=in_last || (|input_nonfinite);
  integer stage;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0;
      first_pipe<=0;
      last_pipe<=0;
      error_pipe<=0;
      for (stage=0;stage<38;stage=stage+1) tag_pipe[stage]<=0;
    end else if (flush) begin
      valid<=0;
      error_pipe<=0;
    end else if (enable) begin
      valid<={valid[36:0],pair_fire};
      first_pipe<={first_pipe[36:0],in_first};
      last_pipe<={last_pipe[36:0],in_last};
      tag_pipe[0]<=in_tag;
      for (stage=1;stage<38;stage=stage+1)
        tag_pipe[stage]<=tag_pipe[stage-1];
      error_pipe<={error_pipe[4:0],association_error};
    end
  end
  integer operand_stage;
  always @(posedge clk) begin
    if (rst_n && !flush && enable) begin
      if (pair_fire) begin
        a_pipe[0]<=masked_a;
        b_pipe[0]<=masked_b;
      end
      for (operand_stage=1;operand_stage<6;operand_stage=operand_stage+1)
        if (valid[operand_stage-1]) begin
          a_pipe[operand_stage]<=a_pipe[operand_stage-1];
          b_pipe[operand_stage]<=b_pipe[operand_stage-1];
        end
    end
  end

  genvar level, node;
  generate for (level=1;level<=5;level=level+1) begin: group_max
    for (node=0;node<128;node=node+1) begin: nodes
      if (node<(128 >> level)) begin: active
        reg [7:0] a_max, b_max;
        wire [7:0] al=maximum_a[level-1][16*node+:8];
        wire [7:0] ar=maximum_a[level-1][16*node+8+:8];
        wire [7:0] bl=maximum_b[level-1][16*node+:8];
        wire [7:0] br=maximum_b[level-1][16*node+8+:8];
        assign maximum_a[level][8*node+:8]=a_max;
        assign maximum_b[level][8*node+:8]=b_max;
        always @(posedge clk) begin
          if (rst_n && !flush && enable && valid[level-1]) begin
            a_max<=al>=ar ? al : ar;
            b_max<=bl>=br ? bl : br;
          end
        end
      end else begin: unused
        assign maximum_a[level][8*node+:8]=8'd0;
        assign maximum_b[level][8*node+:8]=8'd0;
      end
    end
  end endgenerate

  reg aligned_error;
  reg signed [12:0] group_exponent [0:3];
  genvar group_index;
  generate for (group_index=0;group_index<4;group_index=group_index+1) begin: bases
    wire signed [12:0] base=$signed({5'd0,maximum_a[5][8*group_index+:8]})+
      $signed({5'd0,maximum_b[5][8*group_index+:8]})-13'sd268;
    always @(posedge clk) begin
      if (rst_n && !flush && enable && valid[5])
        group_exponent[group_index]<=base;
    end
  end endgenerate
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) aligned_error<=0;
    else if (flush) aligned_error<=0;
    else if (enable && valid[5]) aligned_error<=error_pipe[5];
  end

  wire [4095:0] tree_data [0:7];
  wire [127:0] tree_error [0:7], tree_valid [0:7];
  generate for (lane=0;lane<128;lane=lane+1) begin: aligned_lanes
    localparam GROUP_INDEX=lane >> 5;
    wire [15:0] a=a_pipe[5][16*lane+:16];
    wire [15:0] b=b_pipe[5][16*lane+:16];
    wire [7:0] ea=a[14:7]==0 ? 8'd1 : a[14:7];
    wire [7:0] eb=b[14:7]==0 ? 8'd1 : b[14:7];
    reg sign6;
    reg [7:0] ma6, mb6, residual_a6, residual_b6;
    always @(posedge clk) begin
      if (rst_n && !flush && enable && valid[5]) begin
        sign6<=a[15]^b[15];
        ma6<={|a[14:7],a[6:0]};
        mb6<={|b[14:7],b[6:0]};
        residual_a6<=maximum_a[5][8*GROUP_INDEX+:8]-ea;
        residual_b6<=maximum_b[5][8*GROUP_INDEX+:8]-eb;
      end
    end
    anvil_q2_fp2_bfp_mul3 product (
      .clk(clk),.rst_n(rst_n),.flush(flush),.enable(enable),
      .in_valid(valid[6]),.in_error(aligned_error),.in_sign(sign6),
      .in_ma(ma6),.in_mb(mb6),.in_group_exponent(group_exponent[GROUP_INDEX]),
      .in_residual_a(residual_a6),.in_residual_b(residual_b6),
      .out_valid(tree_valid[0][lane]),.out_data(tree_data[0][32*lane+:32]),
      .out_error(tree_error[0][lane])
    );
  end endgenerate

  generate for (level=1;level<=7;level=level+1) begin: reduction
    for (node=0;node<128;node=node+1) begin: nodes
      if (node<(128 >> level)) begin: active
        anvil_q2_fp2_add4 addition (
          .clk(clk),.rst_n(rst_n),.flush(flush),.enable(enable),
          .in_valid(tree_valid[level-1][2*node]),
          .in_error(tree_error[level-1][2*node] || tree_error[level-1][2*node+1]),
          .in_a(tree_data[level-1][64*node+:32]),
          .in_b(tree_data[level-1][64*node+32+:32]),
          .out_valid(tree_valid[level][node]),
          .out_data(tree_data[level][32*node+:32]),
          .out_error(tree_error[level][node])
        );
      end else begin: unused
        assign tree_valid[level][node]=1'b0;
        assign tree_data[level][32*node+:32]=32'd0;
        assign tree_error[level][node]=1'b0;
      end
    end
  end endgenerate
  assign out_data=out_valid ? tree_data[7][31:0] : 32'd0;
  assign out_error=out_valid && tree_error[7][0];
endmodule
