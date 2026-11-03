module anvil_q1_fp2_fp32_binary #(
  parameter MULTIPLY=0
) (
  input wire clk, rst_n, in_valid,
  output wire in_ready,
  input wire out_ready,
  input wire [31:0] a, b,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  generate if (MULTIPLY!=0 && MULTIPLY!=1) begin: invalid_parameters
    initial $fatal(1,"FP2 BINARY PARAMETER ERROR: MULTIPLY must be 0 or 1");
  end endgenerate
  reg [8:0] valid;
  wire advance=!valid[8] || out_ready;
  reg [31:0] a0, b0;
  wire [23:0] sa0={a0[30:23]!=0,a0[22:0]};
  wire [23:0] sb0={b0[30:23]!=0,b0[22:0]};
  wire a_inf=a0[30:23]==255 && a0[22:0]==0;
  wire b_inf=b0[30:23]==255 && b0[22:0]==0;
  wire a_nan=a0[30:23]==255 && a0[22:0]!=0;
  wire b_nan=b0[30:23]==255 && b0[22:0]!=0;
  wire a_zero=a0[30:0]==0, b_zero=b0[30:0]==0;
  wire product_invalid=(a_inf && b_zero) || (b_inf && a_zero);
  wire product_nan=a_nan || b_nan || product_invalid;
  wire product_sign=a0[31]^b0[31];
  wire signed [9:0] base_a=a0[30:23]==0 ? -10'sd149 :
    $signed({2'd0,a0[30:23]})-10'sd150;
  wire signed [9:0] base_b=b0[30:23]==0 ? -10'sd149 :
    $signed({2'd0,b0[30:23]})-10'sd150;
  wire [8:0] add_shift_a=a0[30:23]==0 ? 9'd149 : 9'({1'b0,a0[30:23]})+9'd148;
  wire [8:0] add_shift_b=b0[30:23]==0 ? 9'd149 : 9'({1'b0,b0[30:23]})+9'd148;
  wire [8:0] input_meta_a=anvil_q1_fp2_pkg::fp32_meta(a0), input_meta_b=anvil_q1_fp2_pkg::fp32_meta(b0);
  wire [8:0] add_meta=anvil_q1_fp2_pkg::merge_meta(input_meta_a,input_meta_b);
  wire [8:0] multiply_meta={
    (input_meta_a[8] || input_meta_b[8] || product_invalid),4'd0,
    product_nan,
    (!product_nan && (a_inf || b_inf) && !product_sign),
    (!product_nan && (a_inf || b_inf) && product_sign),
    (!product_nan && !(a_inf || b_inf) && (a_zero || b_zero) && product_sign)};
  wire [31:0] result8;
  wire [4:0] status8;
  assign in_ready=rst_n && advance;
  assign out_valid=rst_n && valid[8];
  assign result=out_valid ? result8 : 32'd0;
  assign status=out_valid ? status8 : 5'd0;
  always @(posedge clk) begin
    if (!rst_n) valid<=0;
    else if (advance) valid<={valid[7:0],in_valid};
  end
  always @(posedge clk) if (rst_n && advance) begin
    a0<=in_valid ? a : 32'd0; b0<=in_valid ? b : 32'd0;
  end
  generate if (MULTIPLY==1) begin: multiply_pipeline
    reg [47:0] product1, product2, normalized3, coarse4, shifted5;
    reg signed [10:0] base1, base2;
    reg [5:0] high2;
    reg [2:0] fine4;
    reg sticky4, sticky5;
    reg [8:0] metadata [1:6];
    reg sign_bit [1:6];
    reg zero [3:6], normal [3:6];
    reg signed [11:0] exponent [3:6];
    reg [23:0] kept6;
    reg guard6, sticky6;
    reg [36:0] packed7, packed8;
    wire upper_nonzero=|product1[47:24];
    wire [5:0] product_high=upper_nonzero ?
      6'd24+{1'b0,anvil_q1_fp2_pkg::leading24(product1[47:24])} :
      {1'b0,anvil_q1_fp2_pkg::leading24(product1[23:0])};
    wire signed [11:0] biased_exponent=
      $signed({base2[10],base2})+$signed({6'd0,high2})+12'sd127;
    // Shift only for gradual underflow; discarded bits remain in the sticky tail.
    wire [5:0] underflow_shift=exponent[3]>0 ? 6'd0 :
      (exponent[3]<=-12'sd47 ? 6'd48 : 6'(12'sd1-exponent[3]));
    wire [5:0] coarse_shift={underflow_shift[5:3],3'd0};
    wire [47:0] coarse_mask=~(48'hffffffffffff << coarse_shift);
    wire [47:0] fine_mask=~(48'hffffffffffff << fine4);
    wire [36:0] packed_result=anvil_q1_fp2_pkg::pack_fp32(
      metadata[6],sign_bit[6],zero[6],normal[6],exponent[6],
      kept6,guard6,sticky6);
    integer m;
    assign result8=packed8[31:0];
    assign status8=packed8[36:32];
    always @(posedge clk) if (rst_n && advance) begin
      product1<=a0[30:23]==255 || b0[30:23]==255 ? 48'd0 : sa0*sb0;
      base1<=$signed({base_a[9],base_a})+$signed({base_b[9],base_b});
      metadata[1]<=multiply_meta; sign_bit[1]<=product_sign;
      for (m=2;m<=6;m=m+1) begin
        metadata[m]<=metadata[m-1]; sign_bit[m]<=sign_bit[m-1];
      end
      product2<=product1; base2<=base1; high2<=product_high;
      normalized3<=product2 << (6'd47-high2);
      exponent[3]<=biased_exponent;
      normal[3]<=biased_exponent>0; zero[3]<=product2==0;
      for (m=4;m<=6;m=m+1) begin
        exponent[m]<=exponent[m-1];
        normal[m]<=normal[m-1]; zero[m]<=zero[m-1];
      end
      coarse4<=normalized3 >> coarse_shift;
      fine4<=underflow_shift[2:0];
      sticky4<=|(normalized3 & coarse_mask);
      shifted5<=coarse4 >> fine4;
      sticky5<=sticky4 || |(coarse4 & fine_mask);
      kept6<=shifted5[47:24]; guard6<=shifted5[23];
      sticky6<=sticky5 || |shifted5[22:0];
      packed7<=packed_result; packed8<=packed7;
    end
  end else begin: add_pipeline
  reg [47:0] magnitude_a1, magnitude_b1;
  reg [8:0] shift_a1, shift_b1;
  reg sign_a1, sign_b1;
  reg [8:0] metadata [1:7];
  reg [575:0] coarse_a2, coarse_b2;
  reg [4:0] fine_a2, fine_b2;
  reg sign_a2, sign_b2;
  reg signed [575:0] aligned_a3, aligned_b3, sum4;
  reg [575:0] magnitude5, magnitude6;
  reg sign5, sign6, sign7, zero7, normal7;
  reg [9:0] high6;
  reg signed [11:0] exponent7;
  reg [23:0] kept7;
  reg guard7, sticky7;
  reg [31:0] add_result8;
  reg [4:0] add_status8;
  wire [36:0] packed_result=anvil_q1_fp2_pkg::pack_fp32(metadata[7],sign7,zero7,normal7,
    exponent7,kept7,guard7,sticky7);
  reg [575:0] shifted_magnitude;
  reg [23:0] kept_next;
  reg guard_next, sticky_next;
  integer distance, i;
  assign result8=add_result8;
  assign status8=add_status8;
  always @* begin
    distance=high6>=172 ? $signed({22'd0,high6})-23 : 149;
    shifted_magnitude=magnitude6 >> distance;
    kept_next=shifted_magnitude[23:0];
    guard_next=|(magnitude6 & (576'd1 << (distance-1)));
    sticky_next=|(magnitude6 & ((576'd1 << (distance-1))-1));
  end
  always @(posedge clk) if (rst_n && advance) begin
    magnitude_a1<=a0[30:23]==255 ? 48'd0 : {24'd0,sa0};
    magnitude_b1<=b0[30:23]==255 ? 48'd0 : {24'd0,sb0};
    shift_a1<=add_shift_a; shift_b1<=add_shift_b;
    sign_a1<=a0[31]; sign_b1<=b0[31]; metadata[1]<=add_meta;
    for (i=2;i<8;i=i+1) metadata[i]<=metadata[i-1];
    coarse_a2<={528'd0,magnitude_a1} << {shift_a1[8:5],5'd0};
    coarse_b2<={528'd0,magnitude_b1} << {shift_b1[8:5],5'd0};
    fine_a2<=shift_a1[4:0]; fine_b2<=shift_b1[4:0];
    sign_a2<=sign_a1; sign_b2<=sign_b1;
    aligned_a3<=sign_a2 ? -$signed(coarse_a2 << fine_a2) :
      $signed(coarse_a2 << fine_a2);
    aligned_b3<=sign_b2 ? -$signed(coarse_b2 << fine_b2) :
      $signed(coarse_b2 << fine_b2);
    sum4<=aligned_a3+aligned_b3;
    magnitude5<=sum4[575] ? -sum4 : sum4; sign5<=sum4[575];
    magnitude6<=magnitude5; sign6<=sign5; high6<=anvil_q1_fp2_pkg::leading576(magnitude5);
    exponent7<=$signed({2'd0,high6})-12'sd171;
    normal7<=high6>=172; zero7<=magnitude6==0; sign7<=sign6;
    kept7<=kept_next; guard7<=guard_next; sticky7<=sticky_next;
    add_result8<=packed_result[31:0]; add_status8<=packed_result[36:32];
  end
  end endgenerate
endmodule
