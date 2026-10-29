module anvil_q2_fp_dot_lane #(
  parameter FP_FORMAT=0
)(
  input wire clk, rst_n,
  input wire in_valid, output wire in_ready,
  input wire [15:0] in_a,
  input wire [127:0] in_b,
  input wire in_first, in_last,
  output wire out_valid, input wire out_ready,
  output wire [255:0] out_sum,
  output wire out_last
);
  import anvil_q2_fp_pkg::*;
  reg v1, v2, v3, first1, first2, last1, last2, last3;
  reg [63:0] product1 [0:7];
  reg [31:0] product2 [0:7], sum3 [0:7], accumulator [0:7];
  wire ready3=!v3 || out_ready;
  wire ready2=!v2 || ready3;
  wire ready1=!v1 || ready2;
  assign in_ready=rst_n && ready1;
  assign out_valid=rst_n && v3;
  assign out_last=rst_n && last3;
  genvar j;
  generate
    if (FP_FORMAT!=0 && FP_FORMAT!=1) begin: invalid_parameters
      initial $fatal(1,"ANVIL_Q2_FP PARAMETER ERROR: lane format");
    end
    for (j=0;j<8;j=j+1) begin: outputs
      wire [31:0] accumulated_sum=fp_add(accumulator[j],product2[j]);
      // +0 plus -0 is +0 under RNE; other rounded products pass unchanged.
      wire [31:0] first_sum=fp_is_zero(product2[j]) ? FP_ZERO : product2[j];
      wire [31:0] next_sum=first2 ? first_sum : accumulated_sum;
      assign out_sum[j*32+:32]=rst_n ? sum3[j] : 32'd0;
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          sum3[j]<=0;
          accumulator[j]<=0;
        end else if (ready3 && v2) begin
          sum3[j]<=next_sum;
          accumulator[j]<=next_sum;
        end
      end
    end
  endgenerate
  integer i;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      v1<=0; v2<=0; v3<=0;
      first1<=0; first2<=0; last1<=0; last2<=0; last3<=0;
      for (i=0;i<8;i=i+1) begin
        product1[i]<=0; product2[i]<=0;
      end
    end else begin
      if (ready3) begin
        v3<=v2;
        if (v2) begin
          last3<=last2;
        end
      end
      if (ready2) begin
        v2<=v1;
        if (v1) begin
          first2<=first1; last2<=last1;
          for (i=0;i<8;i=i+1) product2[i]<=round_product(product1[i]);
        end
      end
      if (ready1) begin
        v1<=in_valid;
        if (in_valid) begin
          first1<=in_first; last1<=in_last;
          for (i=0;i<8;i=i+1)
            product1[i]<=exact_product(expand16(in_a,FP_FORMAT),
                                      expand16(in_b[i*16+:16],FP_FORMAT));
        end
      end
    end
  end
endmodule
