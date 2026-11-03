module anvil_q2_ht2_rope_pair (
  input wire clk, rst_n, annul, s_valid, m_ready,
  input wire s_fp16,
  input wire [63:0] s_data, s_coefficients, s_tag,
  output wire s_ready, m_valid, m_error,
  output wire [31:0] m_data,
  output wire [63:0] m_fp32, m_tag
);
  localparam [2:0] IDLE=0, ISSUE=1, WAIT_ARITHMETIC=2,
    CONVERT_SEND=3, CONVERT_WAIT=4, RESPONSE=5;
  reg [2:0] state, step;
  reg fp16, response_error;
  reg [63:0] source, coefficients, tag, result;
  reg [31:0] temporary, product;
  reg [31:0] rounded;
  reg [31:0] arithmetic_a, arithmetic_b;
  reg multiply;
  wire arithmetic_ready, arithmetic_valid, arithmetic_error;
  wire [31:0] arithmetic_result;
  wire [63:0] arithmetic_tag;
  wire [1:0] convert_ready, convert_valid, convert_error;
  wire [63:0] converted;
  wire [127:0] converted_tags;
  genvar word_index;

  always @* begin
    arithmetic_a=0; arithmetic_b=0; multiply=0;
    if (rst_n && !annul && state==ISSUE) begin
      case (step)
        0: begin arithmetic_a=source[31:0]; arithmetic_b=coefficients[31:0]; multiply=1; end
        1: begin arithmetic_a=source[63:32]; arithmetic_b=coefficients[63:32]; multiply=1; end
        2: begin arithmetic_a=product; arithmetic_b={~temporary[31],temporary[30:0]}; end
        3: begin arithmetic_a=source[63:32]; arithmetic_b=coefficients[31:0]; multiply=1; end
        4: begin arithmetic_a=source[31:0]; arithmetic_b=coefficients[63:32]; multiply=1; end
        5: begin arithmetic_a=product; arithmetic_b=temporary; end
        default: begin arithmetic_a=32'h7fc00000; end
      endcase
    end
  end

  anvil_q2_ht2_scalar arithmetic (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(rst_n && !annul && state==ISSUE),.s_ready(arithmetic_ready),
    .s_operation({2'd0,multiply}),.s_a(arithmetic_a),.s_b(arithmetic_b),.s_tag(tag),
    .m_ready(rst_n && !annul && state==WAIT_ARITHMETIC),
    .m_valid(arithmetic_valid),.m_error(arithmetic_error),
    .m_data(arithmetic_result),.m_tag(arithmetic_tag)
  );
  generate for (word_index=0;word_index<2;word_index=word_index+1) begin: boundary
    anvil_q2_ht2_convert_pipe conversion (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .s_valid(rst_n && !annul && state==CONVERT_SEND && (&convert_ready)),
      .s_ready(convert_ready[word_index]),.s_to_fp32(1'b0),.s_fp16(fp16),
      .s_data(result[32*word_index+:32]),.s_tag(tag),
      .m_ready(rst_n && !annul && state==CONVERT_WAIT && (&convert_valid)),
      .m_valid(convert_valid[word_index]),.m_error(convert_error[word_index]),
      .m_data(converted[32*word_index+:32]),
      .m_tag(converted_tags[64*word_index+:64])
    );
  end endgenerate

  assign s_ready=rst_n && !annul && state==IDLE;
  assign m_valid=rst_n && !annul && state==RESPONSE;
  assign m_error=m_valid && response_error;
  assign m_data=m_valid && !response_error ? rounded : 32'd0;
  assign m_fp32=m_valid && !response_error ? result : 64'd0;
  assign m_tag=m_valid ? tag : 64'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; step<=0; fp16<=0; response_error<=0;
      source<=0; coefficients<=0; tag<=0; result<=0;
      temporary<=0; product<=0; rounded<=0;
    end else if (annul) begin
      state<=IDLE; response_error<=0; result<=0; rounded<=0;
    end else case (state)
      IDLE: if (s_valid) begin
        source<=s_data; coefficients<=s_coefficients; tag<=s_tag;
        fp16<=s_fp16; step<=0; response_error<=0; result<=0;
        rounded<=0; state<=ISSUE;
      end
      ISSUE: if (arithmetic_ready) state<=WAIT_ARITHMETIC;
      WAIT_ARITHMETIC: if (arithmetic_valid) begin
        if (arithmetic_error || arithmetic_tag!=tag) begin
          response_error<=1; state<=RESPONSE;
        end else begin
          temporary<=arithmetic_result;
          if (step==0 || step==3) product<=arithmetic_result;
          if (step==2) result[31:0]<=arithmetic_result;
          if (step==5) begin
            result[63:32]<=arithmetic_result; state<=CONVERT_SEND;
          end else begin step<=step+3'd1; state<=ISSUE; end
        end
      end
      CONVERT_SEND: if (&convert_ready) state<=CONVERT_WAIT;
      CONVERT_WAIT: if (&convert_valid) begin
        response_error<=(|convert_error) ||
          converted_tags[63:0]!=tag || converted_tags[127:64]!=tag;
        rounded<={converted[47:32],converted[15:0]}; state<=RESPONSE;
      end
      RESPONSE: if (m_ready) state<=IDLE;
      default: begin response_error<=1; state<=RESPONSE; end
    endcase
  end
endmodule
