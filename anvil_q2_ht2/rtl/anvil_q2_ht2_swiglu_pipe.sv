module anvil_q2_ht2_swiglu_pipe (
  input wire clk, rst_n, annul, s_valid,
  output wire s_ready,
  input wire s_fp16, s_last,
  input wire [31:0] s_gate, s_up, s_index,
  input wire [63:0] s_tag,
  output wire m_valid,
  input wire m_ready,
  output wire m_error, m_last,
  output wire [31:0] m_index, m_fp32,
  output wire [15:0] m_data,
  output wire [63:0] m_tag
);
  wire advance;
  wire enabled=rst_n && !annul && advance;
  reg [237:0] valid;
  reg [3:0] errors;
  wire [31:0] exponential160, denominator164, reciprocal217;
  wire exp_error160, add_error164, reciprocal_error217;
  wire [31:0] exponential217, negative_sigmoid224, positive_sigmoid224, sigmoid224;
  wire sign224;
  wire sigmoid_error224, error164, error217, error224, error231, error238;
  wire delayed_exp_error164, previous_error217, previous_error224;
  wire previous_error231, previous_error238;
  wire [31:0] gate224, gated231, up231, product238;
  wire gate_error231, product_error238;
  wire [97:0] metadata238, metadata242;
  wire [31:0] converted, fp32_242;
  wire conversion_valid, conversion_error;
  wire [63:0] conversion_tag;

  anvil_q2_ht2_exp_datapath exponential (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data({1'b1,s_gate[30:0]}),.m_data(exponential160),.m_error(exp_error160)
  );
  anvil_q2_ht2_fp32_add_pipe denominator (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .a(32'h3f800000),.b(exponential160),.sum(denominator164),.error(add_error164)
  );
  anvil_q2_ht2_sigmoid_reciprocal reciprocal (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data(denominator164),.m_data(reciprocal217),.m_error(reciprocal_error217)
  );
  anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(57)) exponential_delay (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data(exponential160),.m_data(exponential217)
  );
  anvil_q2_ht2_fp32_mul_pipe negative_sigmoid (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .a(exponential217),.b(reciprocal217),
    .product(negative_sigmoid224),.error(sigmoid_error224)
  );
  anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(7)) positive_sigmoid (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data(reciprocal217),.m_data(positive_sigmoid224)
  );
  anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(224)) sign_delay (
    .clk(clk),.rst_n(rst_n),.advance(enabled),.s_data(s_gate[31]),.m_data(sign224)
  );
  assign sigmoid224=sign224 ? negative_sigmoid224 : positive_sigmoid224;
  anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(224)) gate_delay (
    .clk(clk),.rst_n(rst_n),.advance(enabled),.s_data(s_gate),.m_data(gate224)
  );
  anvil_q2_ht2_fp32_mul_pipe gate_multiply (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .a(gate224),.b(sigmoid224),.product(gated231),.error(gate_error231)
  );
  anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(231)) up_delay (
    .clk(clk),.rst_n(rst_n),.advance(enabled),.s_data(s_up),.m_data(up231)
  );
  anvil_q2_ht2_fp32_mul_pipe up_multiply (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .a(gated231),.b(up231),.product(product238),.error(product_error238)
  );
  anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(4)) exp_error_delay (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data(exp_error160),.m_data(delayed_exp_error164)
  );
  assign error164=delayed_exp_error164 || add_error164;
  anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(53)) reciprocal_error_delay (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data(error164),.m_data(previous_error217)
  );
  assign error217=previous_error217 || reciprocal_error217;
  anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(7)) sigmoid_error_delay (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data(error217),.m_data(previous_error224)
  );
  assign error224=previous_error224 || (sign224 && sigmoid_error224);
  anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(7)) gate_error_delay (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data(error224),.m_data(previous_error231)
  );
  assign error231=previous_error231 || gate_error231;
  anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(7)) product_error_delay (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data(error231),.m_data(previous_error238)
  );
  assign error238=previous_error238 || product_error238;
  anvil_q2_ht2_delay #(.WIDTH(98),.STAGES(238)) input_metadata (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data({s_fp16,s_last,s_index,s_tag}),.m_data(metadata238)
  );
  anvil_q2_ht2_convert_pipe conversion (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(valid[237]),.s_ready(advance),
    .s_to_fp32(1'b0),.s_fp16(metadata238[97]),
    .s_data(product238),.s_tag(metadata238[63:0]),
    .m_valid(conversion_valid),.m_ready(m_ready),
    .m_error(conversion_error),.m_data(converted),.m_tag(conversion_tag)
  );
  anvil_q2_ht2_delay #(.WIDTH(98),.STAGES(4)) output_metadata (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data(metadata238),.m_data(metadata242)
  );
  anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(4)) result_delay (
    .clk(clk),.rst_n(rst_n),.advance(enabled),
    .s_data(product238),.m_data(fp32_242)
  );
  assign s_ready=rst_n && !annul && advance;
  assign m_valid=rst_n && !annul && conversion_valid;
  assign m_error=m_valid && (errors[3] || conversion_error ||
    conversion_tag!=metadata242[63:0]);
  assign m_last=m_valid && (m_error || metadata242[96]);
  assign m_index=m_valid ? metadata242[95:64] : 32'd0;
  assign m_fp32=m_valid && !m_error ? fp32_242 : 32'd0;
  assign m_data=m_valid && !m_error ? converted[15:0] : 16'd0;
  assign m_tag=m_valid ? metadata242[63:0] : 64'd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin valid<=0; errors<=0; end
    else if (annul) begin valid<=0; errors<=0; end
    else if (advance) begin
      valid<={valid[236:0],s_valid};
      errors<={errors[2:0],valid[237] && error238};
    end
  end
endmodule
