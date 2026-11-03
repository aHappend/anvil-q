module anvil_q2_ht2_projection_store_pipe (
  input wire clk, rst_n, annul, s_valid,
  output wire s_ready,
  input wire s_fp16, s_bias_valid, s_last,
  input wire [127:0] s_sum,
  input wire [31:0] s_bias, s_row,
  input wire [3:0] s_token_mask,
  input wire [63:0] s_tag,
  output wire m_valid,
  input wire m_ready,
  output wire m_error, m_last,
  output wire [63:0] m_data, m_tag,
  output wire [31:0] m_row,
  output wire [3:0] m_token_mask,
  output wire idle
);
  reg [7:0] valid, lasts, errors;
  reg [3:0] biased, half;
  reg [127:0] bypass [0:3];
  reg [31:0] rows [0:7];
  reg [3:0] masks [0:7];
  reg [63:0] tags [0:7];
  wire advance=!valid[7] || m_ready;
  wire [127:0] added, converted;
  wire [3:0] add_error, conversion_error, conversion_valid, conversion_ready;
  wire [255:0] conversion_tag;
  wire conversion_fault=(|(conversion_error & masks[7])) ||
    (valid[7] && conversion_valid!=4'b1111);
  integer i;
  genvar t;

  for (t=0;t<4;t=t+1) begin: token
    anvil_q2_ht2_fp32_add_pipe bias_addition (
      .clk(clk),.rst_n(rst_n),.advance(advance && !annul),
      .a(s_token_mask[t] ? s_sum[32*t+:32] : 32'd0),
      .b(s_token_mask[t] && s_bias_valid ? s_bias : 32'd0),
      .sum(added[32*t+:32]),.error(add_error[t])
    );
    anvil_q2_ht2_convert_pipe conversion (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .s_valid(valid[3]),.s_ready(conversion_ready[t]),
      .s_to_fp32(1'b0),.s_fp16(half[3]),
      .s_data(masks[3][t] ?
        (biased[3] ? added[32*t+:32] : bypass[3][32*t+:32]) : 32'd0),
      .s_tag(tags[3]),.m_valid(conversion_valid[t]),.m_ready(m_ready),
      .m_error(conversion_error[t]),.m_data(converted[32*t+:32]),
      .m_tag(conversion_tag[64*t+:64])
    );
    assign m_data[16*t+:16]=m_valid && !m_error && masks[7][t] ?
      converted[32*t+:16] : 16'd0;
  end
  assign s_ready=rst_n && !annul && advance;
  assign m_valid=rst_n && !annul && valid[7];
  assign m_error=m_valid && (errors[7] || conversion_fault ||
    conversion_tag!={4{tags[7]}});
  assign m_last=m_valid && lasts[7];
  assign m_row=m_valid ? rows[7] : 32'd0;
  assign m_token_mask=m_valid ? masks[7] : 4'd0;
  assign m_tag=m_valid ? tags[7] : 64'd0;
  assign idle=rst_n && valid==0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0; lasts<=0; errors<=0; biased<=0; half<=0;
      for (i=0;i<4;i=i+1) bypass[i]<=0;
      for (i=0;i<8;i=i+1) begin rows[i]<=0; masks[i]<=0; tags[i]<=0; end
    end else if (annul) begin
      valid<=0; errors<=0;
    end else if (advance) begin
      valid<={valid[6:0],s_valid};
      lasts<={lasts[6:0],s_last};
      biased<={biased[2:0],s_bias_valid}; half<={half[2:0],s_fp16};
      errors<={errors[6:0],1'b0};
      errors[4]<=errors[3] || (biased[3] && (|(add_error & masks[3])));
      bypass[0]<=s_sum;
      for (i=1;i<4;i=i+1) bypass[i]<=bypass[i-1];
      rows[0]<=s_row; masks[0]<=s_token_mask; tags[0]<=s_tag;
      for (i=1;i<8;i=i+1) begin
        rows[i]<=rows[i-1]; masks[i]<=masks[i-1]; tags[i]<=tags[i-1];
      end
    end
  end
endmodule
