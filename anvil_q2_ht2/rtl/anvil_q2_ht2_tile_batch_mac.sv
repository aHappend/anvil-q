module anvil_q2_ht2_tile_batch_mac (
  input wire clk, rst_n, annul, s_valid, m_ready, s_fp16, s_weight_fp16,
  input wire [3:0] s_token_mask,
  input wire [511:0] s_keep,
  input wire [8191:0] s_act,
  input wire [2047:0] s_weight,
  input wire [127:0] s_bias,
  input wire [63:0] s_tag,
  output wire s_ready, m_valid, m_error,
  output wire [127:0] m_sum,
  output wire [63:0] m_tag,
  output wire [3:0] m_token_mask
);
  reg [38:0] valid;
  reg [63:0] tags [0:38];
  reg [3:0] masks [0:38];
  reg [127:0] biases [0:34];
  wire advance=!valid[38] || m_ready;
  wire [31:0] tree [0:3][0:7][0:127];
  wire errors [0:3][0:7][0:127];
  wire [31:0] sums [0:3];
  wire [3:0] final_error;
  integer i;
  genvar t,j,l;

  assign s_ready=rst_n && !annul && advance;
  assign m_valid=rst_n && !annul && valid[38];
  assign m_sum=m_valid ? {sums[3],sums[2],sums[1],sums[0]} : 128'd0;
  assign m_tag=m_valid ? tags[38] : 64'd0;
  assign m_token_mask=m_valid ? masks[38] : 4'd0;
  assign m_error=m_valid && (|final_error);

  generate for (t=0;t<4;t=t+1) begin: token_slot
    for (j=0;j<128;j=j+1) begin: lane
      anvil_q2_ht2_product_pipe multiplier (
        .clk(clk),.rst_n(rst_n),.advance(advance),.fp16(s_fp16),
        .weight_fp16(s_weight_fp16),
        .keep(s_valid && s_token_mask[t] && s_keep[128*t+j]),
        .a(s_act[(128*t+j)*16+:16]),.b(s_weight[j*16+:16]),
        .product(tree[t][0][j]),.error(errors[t][0][j])
      );
    end
    for (l=0;l<7;l=l+1) begin: reduction_level
      for (j=0;j<(128 >> (l+1));j=j+1) begin: pair
        wire local_error;
        reg [3:0] inherited_error;
        always @(posedge clk or negedge rst_n) begin
          if (!rst_n) inherited_error<=0;
          else if (advance)
            inherited_error<={inherited_error[2:0],
              (errors[t][l][2*j] || errors[t][l][2*j+1])};
        end
        anvil_q2_ht2_fp32_add_pipe adder (
          .clk(clk),.rst_n(rst_n),.advance(advance),
          .a(tree[t][l][2*j]),.b(tree[t][l][2*j+1]),
          .sum(tree[t][l+1][j]),.error(local_error)
        );
        assign errors[t][l+1][j]=local_error || inherited_error[3];
      end
    end
    wire bias_error;
    reg [3:0] inherited_error;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) inherited_error<=0;
      else if (advance)
        inherited_error<={inherited_error[2:0],errors[t][7][0]};
    end
    anvil_q2_ht2_fp32_add_pipe bias_adder (
      .clk(clk),.rst_n(rst_n),.advance(advance),
      .a(tree[t][7][0]),.b(biases[34][32*t+:32]),
      .sum(sums[t]),.error(bias_error)
    );
    assign final_error[t]=masks[38][t] && (bias_error || inherited_error[3]);
  end endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0;
      for (i=0;i<39;i=i+1) begin tags[i]<=0; masks[i]<=0; end
      for (i=0;i<35;i=i+1) biases[i]<=0;
    end else if (annul) begin
      valid<=0;
    end else if (advance) begin
      valid<={valid[37:0],s_valid};
      tags[0]<=s_valid ? s_tag : 64'd0;
      masks[0]<=s_valid ? s_token_mask : 4'd0;
      for (i=0;i<4;i=i+1)
        biases[0][i*32+:32]<=s_valid && s_token_mask[i] ?
          s_bias[i*32+:32] : 32'd0;
      for (i=1;i<39;i=i+1) begin tags[i]<=tags[i-1]; masks[i]<=masks[i-1]; end
      for (i=1;i<35;i=i+1) biases[i]<=biases[i-1];
    end
  end
endmodule
