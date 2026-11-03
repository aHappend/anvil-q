module anvil_q2_ht_tensor_array (
  input wire clk, rst_n,
  input wire s_valid, s_mode,
  input wire [127:0] s_keep,
  input wire [4095:0] s_act,
  input wire [511:0] s_w4, s_zero,
  input wire [2047:0] s_scale, s_bf16,
  input wire [63:0] s_tag,
  input wire m_ready,
  output wire s_ready, m_valid, m_mode,
  output wire signed [127:0] m_sum,
  output wire [31:0] m_fp32,
  output wire [63:0] m_tag,
  output wire m_error
);
  reg [34:0] valid_pipeline, mode_pipeline;
  reg [63:0] tag_pipeline [0:34];
  wire advance = rst_n && (!valid_pipeline[34] || m_ready);
  wire signed [127:0] integer_node [1:255];
  wire [31:0] floating_node [1:255];
  wire error_node [1:255];
  integer stage;
  genvar bank_index, bank_lane, node;

  assign s_ready = advance;
  assign m_valid = rst_n && valid_pipeline[34];
  assign m_mode = m_valid && mode_pipeline[34];
  assign m_sum = m_valid && !mode_pipeline[34] ? integer_node[1] : 128'sd0;
  assign m_fp32 = m_valid && mode_pipeline[34] ? floating_node[1] : 32'd0;
  assign m_tag = m_valid ? tag_pipeline[34] : 64'd0;
  assign m_error = m_valid && error_node[1];

  generate
    for (bank_index=0; bank_index<16; bank_index=bank_index+1) begin: banks
      for (bank_lane=0; bank_lane<8; bank_lane=bank_lane+1) begin: lanes
        localparam J = bank_index+16*bank_lane;
        wire signed [68:0] lane_product;
        anvil_q2_ht_tensor_lane lane (
          .clk(clk),.rst_n(rst_n),.advance(advance),
          .keep(s_valid && s_keep[J]),.mode(s_mode),
          .activation(s_act[J*32+:32]),
          .weight4(s_w4[J*4+:4]),.zero4(s_zero[J*4+:4]),
          .scale16(s_scale[J*16+:16]),.weight_bf16(s_bf16[J*16+:16]),
          .product(lane_product),.product_fp32(floating_node[128+J]),
          .error(error_node[128+J]));
        assign integer_node[128+J] = {{59{lane_product[68]}},lane_product};
      end
    end
    for (node=1; node<128; node=node+1) begin: reduction
      reg [3:0] error_delay;
      wire addition_error;
      anvil_q2_ht_add128_pipe integer_add (
        .clk(clk),.rst_n(rst_n),.advance(advance),
        .a(integer_node[2*node]),.b(integer_node[2*node+1]),
        .sum(integer_node[node]));
      anvil_q2_ht_fp32_add_pipe floating_add (
        .clk(clk),.rst_n(rst_n),.advance(advance),
        .a(floating_node[2*node]),.b(floating_node[2*node+1]),
        .sum(floating_node[node]),.error(addition_error));
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) error_delay <= 0;
        else if (advance)
          error_delay <= {error_delay[2:0],
            (error_node[2*node] || error_node[2*node+1])};
      end
      assign error_node[node] = error_delay[3] || addition_error;
    end
  endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipeline <= 0;
      mode_pipeline <= 0;
      for (stage=0; stage<35; stage=stage+1) tag_pipeline[stage] <= 0;
    end else if (advance) begin
      valid_pipeline <= {valid_pipeline[33:0],s_valid};
      mode_pipeline <= {mode_pipeline[33:0],s_mode};
      tag_pipeline[0] <= s_valid ? s_tag : 64'd0;
      for (stage=1; stage<35; stage=stage+1)
        tag_pipeline[stage] <= tag_pipeline[stage-1];
    end
  end
endmodule
