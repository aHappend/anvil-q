module anvil_q3_ht_mac16 #(
  parameter META_WIDTH=160,
  localparam MW=META_WIDTH>0 ? META_WIDTH : 1
) (
  input wire clk, rst_n, flush,
  input wire in_valid,
  output wire in_ready,
  input wire [63:0] q_nibbles, z_nibbles,
  input wire [255:0] scale_f16,
  input wire [511:0] activation_q16,
  input wire [15:0] lane_mask,
  input wire [MW-1:0] in_meta,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire signed [72:0] out_sum,
  output wire [MW-1:0] out_meta
);
  generate if (META_WIDTH<1) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: MAC metadata width");
  end endgenerate

  reg [8:0] valid_pipe, error_pipe;
  reg [MW-1:0] metadata [0:8];
  wire advance=!valid_pipe[8] || out_ready;
  wire enabled=rst_n && !flush && advance;
  wire [15:0] invalid_scale;
  wire input_error=|(invalid_scale & lane_mask);
  wire signed [72:0] final_sum;
  integer stage;

  assign in_ready=enabled;
  assign out_valid=rst_n && !flush && valid_pipe[8];
  assign out_error=out_valid && error_pipe[8];
  assign out_sum=out_valid ? final_sum : 73'sd0;
  assign out_meta=out_valid ? metadata[8] : {MW{1'b0}};

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe<=0;
      error_pipe<=0;
    end else if (flush) begin
      valid_pipe<=0;
      error_pipe<=0;
    end else if (advance) begin
      valid_pipe<={valid_pipe[7:0],in_valid};
      error_pipe<={error_pipe[7:0],in_valid && input_error};
    end
  end

  always @(posedge clk) begin
    if (enabled) begin
      metadata[0]<=in_meta;
      for (stage=1;stage<9;stage=stage+1)
        metadata[stage]<=metadata[stage-1];
    end
  end

  wire [16*69-1:0] lane_products;
  genvar lane, node;
  generate for (lane=0;lane<16;lane=lane+1) begin: lanes
    reg [3:0] q0, z0;
    reg [15:0] scale0;
    reg signed [31:0] activation0, activation1, activation2;
    reg signed [4:0] delta1;
    reg [31:0] scale1;
    reg signed [36:0] weight2;
    reg signed [53:0] product_low3;
    reg signed [52:0] product_high3;
    reg signed [68:0] product4;
    wire signed [37:0] decoded_weight=
      delta1*$signed({1'b0,scale1});
    wire signed [68:0] extended_low={{15{product_low3[53]}},product_low3};
    wire signed [68:0] extended_high={{16{product_high3[52]}},product_high3};
    assign invalid_scale[lane]=
      anvil_q3_pkg::f16_scale_invalid(scale_f16[lane*16+:16]);
    assign lane_products[lane*69+:69]=product4;

    always @(posedge clk) begin
      if (enabled) begin
        q0<=lane_mask[lane] ? q_nibbles[lane*4+:4] : 4'd0;
        z0<=lane_mask[lane] ? z_nibbles[lane*4+:4] : 4'd0;
        scale0<=lane_mask[lane] ? scale_f16[lane*16+:16] : 16'd0;
        activation0<=lane_mask[lane] ? activation_q16[lane*32+:32] : 32'd0;
        delta1<=$signed({1'b0,q0})-$signed({1'b0,z0});
        scale1<=anvil_q3_pkg::f16_scale(scale0);
        activation1<=activation0;
        weight2<=decoded_weight[36:0];
        activation2<=activation1;
        product_low3<=weight2*$signed({1'b0,activation2[15:0]});
        product_high3<=weight2*$signed(activation2[31:16]);
        product4<=extended_low+(extended_high<<<16);
      end
    end
  end endgenerate

  wire [8*70-1:0] level5;
  wire [4*71-1:0] level6;
  wire [2*72-1:0] level7;
  generate for (node=0;node<8;node=node+1) begin: reduction5
    reg signed [69:0] sum;
    wire signed [68:0] a=lane_products[node*138+:69];
    wire signed [68:0] b=lane_products[node*138+69+:69];
    assign level5[node*70+:70]=sum;
    always @(posedge clk)
      if (enabled) sum<=$signed({a[68],a})+$signed({b[68],b});
  end
  for (node=0;node<4;node=node+1) begin: reduction6
    reg signed [70:0] sum;
    wire signed [69:0] a=level5[node*140+:70];
    wire signed [69:0] b=level5[node*140+70+:70];
    assign level6[node*71+:71]=sum;
    always @(posedge clk)
      if (enabled) sum<=$signed({a[69],a})+$signed({b[69],b});
  end
  for (node=0;node<2;node=node+1) begin: reduction7
    reg signed [71:0] sum;
    wire signed [70:0] a=level6[node*142+:71];
    wire signed [70:0] b=level6[node*142+71+:71];
    assign level7[node*72+:72]=sum;
    always @(posedge clk)
      if (enabled) sum<=$signed({a[70],a})+$signed({b[70],b});
  end endgenerate
  reg signed [72:0] sum8;
  wire signed [71:0] a7=level7[0+:72];
  wire signed [71:0] b7=level7[72+:72];
  assign final_sum=sum8;
  always @(posedge clk)
    if (enabled) sum8<=$signed({a7[71],a7})+$signed({b7[71],b7});
endmodule
