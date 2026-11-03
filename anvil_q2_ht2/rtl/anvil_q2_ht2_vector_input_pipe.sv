module anvil_q2_ht2_vector_input_pipe (
  input wire clk, rst_n, annul, s_valid,
  output wire s_ready,
  input wire [7:0] s_count,
  input wire s_fp16, s_b_fp16,
  input wire [2047:0] s_a, s_b,
  input wire [63:0] s_tag,
  output wire m_valid,
  input wire m_ready,
  output wire m_error, m_last,
  output wire [31:0] m_a, m_b,
  output wire [63:0] m_tag,
  output wire idle
);
  reg active, invalid_count, fp16, b_fp16;
  reg [7:0] count, next_word;
  reg [2047:0] a, b;
  reg [63:0] tag;
  reg [3:0] lasts;
  wire [1:0] input_ready, output_valid, output_error;
  wire [127:0] output_tag;
  wire available=rst_n && !annul;
  wire offer=available && active && !invalid_count && next_word<count;
  wire accept=offer && (&input_ready);
  wire output_transfer=m_valid && m_ready;
  wire advance=!output_valid[0] || m_ready;
  wire [15:0] native_a=a[16*next_word[6:0]+:16];
  wire [15:0] native_b=b[16*next_word[6:0]+:16];
  wire [31:0] converted_a, converted_b;

  anvil_q2_ht2_convert_pipe convert_a (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(offer),.s_ready(input_ready[0]),.s_to_fp32(1'b1),.s_fp16(fp16),
    .s_data({16'd0,native_a}),.s_tag(tag),
    .m_valid(output_valid[0]),.m_ready(m_ready),
    .m_error(output_error[0]),.m_data(converted_a),.m_tag(output_tag[63:0])
  );
  anvil_q2_ht2_convert_pipe convert_b (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(offer),.s_ready(input_ready[1]),.s_to_fp32(1'b1),.s_fp16(b_fp16),
    .s_data({16'd0,native_b}),.s_tag(tag),
    .m_valid(output_valid[1]),.m_ready(m_ready),
    .m_error(output_error[1]),.m_data(converted_b),.m_tag(output_tag[127:64])
  );

  assign s_ready=available && !active;
  assign m_valid=available && active && (invalid_count || (|output_valid));
  assign m_error=m_valid && (invalid_count || output_valid!=2'b11 ||
    (|output_error) || output_tag!={2{tag}});
  assign m_last=m_valid && (invalid_count || lasts[3]);
  assign m_a=m_valid && !m_error ? converted_a : 32'd0;
  assign m_b=m_valid && !m_error ? converted_b : 32'd0;
  assign m_tag=m_valid ? tag : 64'd0;
  assign idle=rst_n && !active;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active<=0; invalid_count<=0; fp16<=0; b_fp16<=0; count<=0; next_word<=0;
      a<=0; b<=0; tag<=0; lasts<=0;
    end else if (annul) begin
      active<=0; invalid_count<=0; lasts<=0;
    end else begin
      if (s_valid && s_ready) begin
        active<=1; invalid_count<=s_count==0 || s_count>128;
        count<=s_count; next_word<=0; fp16<=s_fp16;
        b_fp16<=s_b_fp16;
        a<=s_a; b<=s_b; tag<=s_tag;
      end
      if (advance) lasts<={lasts[2:0],offer && next_word+8'd1==count};
      if (accept) next_word<=next_word+8'd1;
      if (output_transfer && m_last) active<=0;
    end
  end
endmodule
