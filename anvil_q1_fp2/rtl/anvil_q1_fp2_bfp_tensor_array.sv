module anvil_q1_fp2_bfp_tensor_array (
  input wire clk, rst_n, in_valid,
  output wire in_ready,
  input wire out_ready, format_mx,
  input wire [1023:0] a, b,
  input wire [15:0] a_scale, b_scale,
  input wire [63:0] lane_mask,
  input wire [31:0] acc_in,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status,
  output wire [6:0] alignment_events
);
  reg [15:0] valid;
  wire advance=!valid[15] || out_ready;
  reg [15:0] a0 [0:63], b0 [0:63];
  (* nomem2reg *) reg [4:0] conversion0 [0:63];
  reg [63:0] mask0;
  reg [31:0] acc0, acc1, acc2, acc3;
  wire [20:0] mx_a [0:63], mx_b [0:63];
  wire [45:0] product_wire [0:63];
  reg [45:0] product1 [0:63], product2 [0:63], product3 [0:63];
  reg signed [10:0] maximum2 [0:7];
  reg [8:0] metadata2 [0:7];
  reg signed [10:0] maximum3;
  reg [8:0] metadata [3:14];
  reg [6:0] events [5:15];
  reg [63:0] event_bits4;
  wire [3:0] event_octet [0:7];
  wire [4:0] event_quarter [0:3];
  wire [5:0] event_half [0:1];
  wire [6:0] event_total;
  (* nomem2reg *) reg [543:0] coarse4 [0:63];
  (* nomem2reg *) reg [4:0] fine4 [0:63];
  reg [63:0] sign4;
  (* nomem2reg *) reg signed [543:0] aligned5 [0:63];
  reg [543:0] acc_coarse4;
  reg [4:0] acc_fine4;
  reg acc_sign4;
  reg signed [543:0] acc5;
  reg signed [543:0] tree6 [0:31], tree7 [0:15], tree8 [0:7];
  reg signed [543:0] tree9 [0:3], tree10 [0:1], tree11;
  wire [543:0] csa_sum=aligned5[0]^aligned5[1]^acc5;
  wire [543:0] csa_carry=(aligned5[0]&aligned5[1]) |
    (aligned5[0]&acc5) | (aligned5[1]&acc5);
  reg [543:0] magnitude12, magnitude13;
  reg sign12, sign13, sign14;
  reg [9:0] high13;
  reg [23:0] kept14;
  reg guard14, sticky14, normal14, zero14;
  reg signed [11:0] exponent14;
  reg [31:0] result15;
  reg [4:0] status15;
  wire [36:0] packed_result=anvil_q1_fp2_pkg::pack_fp32(metadata[14],sign14,zero14,normal14,
    exponent14,kept14,guard14,sticky14);
  reg [543:0] shifted_magnitude;
  reg [23:0] kept_next;
  reg guard_next, sticky_next;
  integer distance;
  integer i;
  genvar g;

  assign in_ready=rst_n && advance;
  assign out_valid=rst_n && valid[15];
  assign result=out_valid ? result15 : 32'd0;
  assign status=out_valid ? status15 : 5'd0;
  assign alignment_events=out_valid ? events[15] : 7'd0;
  function automatic [3:0] count8(input [7:0] bits);
    reg [1:0] p0, p1, p2, p3;
    reg [2:0] h0, h1;
    begin
      p0={1'b0,bits[0]}+{1'b0,bits[1]};
      p1={1'b0,bits[2]}+{1'b0,bits[3]};
      p2={1'b0,bits[4]}+{1'b0,bits[5]};
      p3={1'b0,bits[6]}+{1'b0,bits[7]};
      h0={1'b0,p0}+{1'b0,p1}; h1={1'b0,p2}+{1'b0,p3};
      count8={1'b0,h0}+{1'b0,h1};
    end
  endfunction
  generate for (g=0;g<64;g=g+1) begin: lanes
    assign mx_a[g]=anvil_q1_fp2_pkg::mx_to_bf16(a[g*8+:8],a_scale[(g<32 ? 0 : 8)+:8]);
    assign mx_b[g]=anvil_q1_fp2_pkg::mx_to_bf16(b[g*8+:8],b_scale[(g<32 ? 0 : 8)+:8]);
    assign product_wire[g]=anvil_q1_fp2_pkg::bf16_product(a0[g],b0[g],conversion0[g],mask0[g]);
    wire extends_below_window=product3[g][15:0]!=0 &&
      ($signed({2'd0,product3[g][25:17]})+
       $signed({7'd0,anvil_q1_fp2_pkg::trailing16(product3[g][15:0])}) < maximum3+11'sd203);
    always @(posedge clk) if (rst_n && advance)
      event_bits4[g]<=extends_below_window;
  end endgenerate
  generate for (g=0;g<8;g=g+1) begin: event_octets
    assign event_octet[g]=count8(event_bits4[g*8+:8]);
  end
  for (g=0;g<4;g=g+1) begin: event_quarters
    assign event_quarter[g]={1'b0,event_octet[g*2]}+{1'b0,event_octet[g*2+1]};
  end
  for (g=0;g<2;g=g+1) begin: event_halves
    assign event_half[g]={1'b0,event_quarter[g*2]}+{1'b0,event_quarter[g*2+1]};
  end endgenerate
  assign event_total={1'b0,event_half[0]}+{1'b0,event_half[1]};

  generate for (g=0;g<8;g=g+1) begin: groups
    wire signed [10:0] m0=anvil_q1_fp2_pkg::max_exp($signed(product1[8*g][36:26]),
      $signed(product1[8*g+1][36:26]));
    wire signed [10:0] m1=anvil_q1_fp2_pkg::max_exp($signed(product1[8*g+2][36:26]),
      $signed(product1[8*g+3][36:26]));
    wire signed [10:0] m2=anvil_q1_fp2_pkg::max_exp($signed(product1[8*g+4][36:26]),
      $signed(product1[8*g+5][36:26]));
    wire signed [10:0] m3=anvil_q1_fp2_pkg::max_exp($signed(product1[8*g+6][36:26]),
      $signed(product1[8*g+7][36:26]));
    wire [8:0] f0=anvil_q1_fp2_pkg::merge_meta(product1[8*g][45:37],product1[8*g+1][45:37]);
    wire [8:0] f1=anvil_q1_fp2_pkg::merge_meta(product1[8*g+2][45:37],product1[8*g+3][45:37]);
    wire [8:0] f2=anvil_q1_fp2_pkg::merge_meta(product1[8*g+4][45:37],product1[8*g+5][45:37]);
    wire [8:0] f3=anvil_q1_fp2_pkg::merge_meta(product1[8*g+6][45:37],product1[8*g+7][45:37]);
    always @(posedge clk) if (rst_n && advance) begin
      maximum2[g]<=anvil_q1_fp2_pkg::max_exp(anvil_q1_fp2_pkg::max_exp(m0,m1),anvil_q1_fp2_pkg::max_exp(m2,m3));
      metadata2[g]<=anvil_q1_fp2_pkg::merge_meta(anvil_q1_fp2_pkg::merge_meta(f0,f1),anvil_q1_fp2_pkg::merge_meta(f2,f3));
    end
  end endgenerate
  wire signed [10:0] max01=anvil_q1_fp2_pkg::max_exp(maximum2[0],maximum2[1]);
  wire signed [10:0] max23=anvil_q1_fp2_pkg::max_exp(maximum2[2],maximum2[3]);
  wire signed [10:0] max45=anvil_q1_fp2_pkg::max_exp(maximum2[4],maximum2[5]);
  wire signed [10:0] max67=anvil_q1_fp2_pkg::max_exp(maximum2[6],maximum2[7]);
  wire [8:0] meta01=anvil_q1_fp2_pkg::merge_meta(metadata2[0],metadata2[1]);
  wire [8:0] meta23=anvil_q1_fp2_pkg::merge_meta(metadata2[2],metadata2[3]);
  wire [8:0] meta45=anvil_q1_fp2_pkg::merge_meta(metadata2[4],metadata2[5]);
  wire [8:0] meta67=anvil_q1_fp2_pkg::merge_meta(metadata2[6],metadata2[7]);
  wire [8:0] global_meta=anvil_q1_fp2_pkg::merge_meta(
    anvil_q1_fp2_pkg::merge_meta(anvil_q1_fp2_pkg::merge_meta(meta01,meta23),anvil_q1_fp2_pkg::merge_meta(meta45,meta67)),anvil_q1_fp2_pkg::fp32_meta(acc2));
  wire [543:0] acc_sig3=acc3[30:23]==255 ? 544'd0 :
    {520'd0,acc3[30:23]!=0,acc3[22:0]};
  wire [8:0] acc_shift3=anvil_q1_fp2_pkg::fp32_grid_shift(acc3);

  always @* begin
    distance=high13>=140 ? $signed({22'd0,high13})-23 : 117;
    shifted_magnitude=magnitude13 >> distance;
    kept_next=shifted_magnitude[23:0];
    guard_next=|(magnitude13 & (544'd1 << (distance-1)));
    sticky_next=|(magnitude13 & ((544'd1 << (distance-1))-1));
  end

  always @(posedge clk) begin
    if (!rst_n) valid<=0;
    else if (advance) valid<={valid[14:0],in_valid};
  end
  always @(posedge clk) if (rst_n && advance) begin
    mask0<=in_valid ? lane_mask : 64'd0;
    acc0<=in_valid ? acc_in : 32'd0;
    for (i=0;i<64;i=i+1) begin
      a0[i]<=format_mx ? mx_a[i][15:0] : a[i*16+:16];
      b0[i]<=format_mx ? mx_b[i][15:0] : b[i*16+:16];
      conversion0[i]<=format_mx ? (mx_a[i][20:16] | mx_b[i][20:16]) : 5'd0;
      product1[i]<=product_wire[i];
      product2[i]<=product1[i];
      product3[i]<=product2[i];
      coarse4[i]<={528'd0,product3[i][15:0]} <<
        {product3[i][25:22],5'd0};
      fine4[i]<=product3[i][21:17];
      sign4[i]<=product3[i][16];
      aligned5[i]<=sign4[i] ? -$signed(coarse4[i] << fine4[i]) :
        $signed(coarse4[i] << fine4[i]);
    end
    acc1<=acc0; acc2<=acc1; acc3<=acc2;
    maximum3<=anvil_q1_fp2_pkg::max_exp(anvil_q1_fp2_pkg::max_exp(anvil_q1_fp2_pkg::max_exp(max01,max23),anvil_q1_fp2_pkg::max_exp(max45,max67)),anvil_q1_fp2_pkg::fp32_high(acc2));
    metadata[3]<=global_meta;
    for (i=4;i<15;i=i+1) metadata[i]<=metadata[i-1];
    events[5]<=event_total;
    for (i=6;i<16;i=i+1) events[i]<=events[i-1];
    acc_coarse4<=acc_sig3 << {acc_shift3[8:5],5'd0};
    acc_fine4<=acc_shift3[4:0]; acc_sign4<=acc3[31];
    acc5<=acc_sign4 ? -$signed(acc_coarse4 << acc_fine4) :
      $signed(acc_coarse4 << acc_fine4);
    tree6[0]<=$signed(csa_sum)+$signed(csa_carry << 1);
    for (i=1;i<32;i=i+1) tree6[i]<=aligned5[2*i]+aligned5[2*i+1];
    for (i=0;i<16;i=i+1) tree7[i]<=tree6[2*i]+tree6[2*i+1];
    for (i=0;i<8;i=i+1) tree8[i]<=tree7[2*i]+tree7[2*i+1];
    for (i=0;i<4;i=i+1) tree9[i]<=tree8[2*i]+tree8[2*i+1];
    for (i=0;i<2;i=i+1) tree10[i]<=tree9[2*i]+tree9[2*i+1];
    tree11<=tree10[0]+tree10[1];
    magnitude12<=tree11[543] ? -tree11 : tree11;
    sign12<=tree11[543];
    magnitude13<=magnitude12; sign13<=sign12;
    high13<=anvil_q1_fp2_pkg::leading544(magnitude12);
    kept14<=kept_next; guard14<=guard_next; sticky14<=sticky_next;
    exponent14<=$signed({2'd0,high13})-12'sd139;
    normal14<=high13>=140; zero14<=magnitude13==0; sign14<=sign13;
    result15<=packed_result[31:0]; status15<=packed_result[36:32];
  end
endmodule
