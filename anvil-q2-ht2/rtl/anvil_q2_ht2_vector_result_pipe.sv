module anvil_q2_ht2_vector_result_pipe (
  input wire clk, rst_n, annul, s_valid,
  output wire s_ready,
  input wire [2:0] s_operation,
  input wire s_fp16, s_last,
  input wire [31:0] s_data, s_aux, s_exponential, s_normalizer, s_index,
  input wire [63:0] s_tag,
  output wire m_valid,
  input wire m_ready,
  output wire m_error, m_last,
  output wire [31:0] m_index, m_fp32,
  output wire [15:0] m_data,
  output wire [63:0] m_tag
);
  wire advance;
  wire [31:0] first_product, second_product, added;
  wire first_error, second_error, add_error;
  wire [31:0] aux7, product14, add14, selected;
  wire error14, add_error14;
  wire [98:0] metadata14, metadata18;
  wire [31:0] fp32_18, converted;
  wire conversion_valid, conversion_error;
  wire [63:0] conversion_tag;
  wire [1:0] operation14;
  wire available=rst_n && !annul;
  wire valid14=valid[13];
  wire fp16_14=metadata14[98];
  wire last_18=metadata18[96];
  wire [1:0] selected_operation=s_operation==0 ? 2'd0 :
    (s_operation==1 ? 2'd1 : 2'd2);
  wire invalid_operation=s_operation!=0 && s_operation!=1 &&
    s_operation!=3 && s_operation!=4;
  wire [31:0] first_a=s_operation==3 ? s_exponential : s_data;
  wire [31:0] first_b=(s_operation==0 || s_operation==3) ?
    s_normalizer : s_aux;

  anvil_q2_ht2_fp32_mul_pipe multiply_first (
    .clk(clk),.rst_n(rst_n),.advance(available && advance),
    .a(first_a),.b(first_b),.product(first_product),.error(first_error)
  );
  anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(7)) auxiliary_delay (
    .clk(clk),.rst_n(rst_n),.advance(available && advance),.s_data(s_aux),.m_data(aux7)
  );
  anvil_q2_ht2_fp32_mul_pipe multiply_gamma (
    .clk(clk),.rst_n(rst_n),.advance(available && advance),
    .a(first_product),.b(aux7),.product(second_product),.error(second_error)
  );
  anvil_q2_ht2_delay #(.WIDTH(33),.STAGES(7)) product_delay (
    .clk(clk),.rst_n(rst_n),.advance(available && advance),
    .s_data({first_error,first_product}),.m_data({error14,product14})
  );
  anvil_q2_ht2_fp32_add_pipe addition (
    .clk(clk),.rst_n(rst_n),.advance(available && advance),
    .a(s_data),.b(s_aux),.sum(added),.error(add_error)
  );
  anvil_q2_ht2_delay #(.WIDTH(33),.STAGES(10)) addition_delay (
    .clk(clk),.rst_n(rst_n),.advance(available && advance),
    .s_data({add_error,added}),.m_data({add_error14,add14})
  );
  anvil_q2_ht2_delay #(.WIDTH(99),.STAGES(14)) input_metadata (
    .clk(clk),.rst_n(rst_n),.advance(available && advance),
    .s_data({s_fp16,invalid_operation,s_last,s_index,s_tag}),.m_data(metadata14)
  );
  anvil_q2_ht2_delay #(.WIDTH(2),.STAGES(14)) operation_delay (
    .clk(clk),.rst_n(rst_n),.advance(available && advance),
    .s_data(selected_operation),.m_data(operation14)
  );
  reg [13:0] valid;
  assign selected=operation14==0 ? second_product :
    (operation14==1 ? add14 : product14);
  wire selected_error=metadata14[97] || (operation14==0 ?
    (error14 || second_error) : (operation14==1 ? add_error14 : error14));
  wire [3:0] errors18;
  reg [3:0] errors;
  assign errors18=errors;
  anvil_q2_ht2_convert_pipe conversion (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(valid14),.s_ready(advance),.s_to_fp32(1'b0),.s_fp16(fp16_14),
    .s_data(selected),.s_tag(metadata14[63:0]),
    .m_valid(conversion_valid),.m_ready(m_ready),
    .m_error(conversion_error),.m_data(converted),.m_tag(conversion_tag)
  );
  anvil_q2_ht2_delay #(.WIDTH(99),.STAGES(4)) output_metadata (
    .clk(clk),.rst_n(rst_n),.advance(available && advance),
    .s_data(metadata14),.m_data(metadata18)
  );
  anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(4)) result_delay (
    .clk(clk),.rst_n(rst_n),.advance(available && advance),
    .s_data(selected),.m_data(fp32_18)
  );
  assign s_ready=available && advance;
  assign m_valid=available && conversion_valid;
  assign m_error=m_valid && (errors18[3] || conversion_error ||
    conversion_tag!=metadata18[63:0]);
  assign m_last=m_valid && (m_error || last_18);
  assign m_index=m_valid ? metadata18[95:64] : 32'd0;
  assign m_fp32=m_valid && !m_error ? fp32_18 : 32'd0;
  assign m_data=m_valid && !m_error ? converted[15:0] : 16'd0;
  assign m_tag=m_valid ? metadata18[63:0] : 64'd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin valid<=0; errors<=0; end
    else if (annul) begin valid<=0; errors<=0; end
    else if (advance) begin
      valid<={valid[12:0],s_valid};
      errors<={errors[2:0],valid14 && selected_error};
    end
  end
endmodule
