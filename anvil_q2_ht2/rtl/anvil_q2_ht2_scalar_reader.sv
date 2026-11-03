module anvil_q2_ht2_scalar_reader (
  input wire clk, rst_n, annul, s_valid, m_ready,
  input wire [511:0] s_descriptor,
  input wire [31:0] s_row, s_column,
  input wire [63:0] s_tag,
  output wire s_ready, m_valid, m_error, m_fp16, idle,
  output wire [15:0] m_native,
  output wire [31:0] m_fp32,
  output wire [63:0] m_tag,
  output wire mem_valid,
  input wire mem_ready,
  output wire [32:0] mem_address,
  input wire mem_rsp_valid, mem_rsp_error,
  output wire mem_rsp_ready,
  input wire [511:0] mem_rsp_data
);
  localparam [3:0] IDLE=0, VALIDATE=1, PRODUCT=2, OFFSET=3,
    ADDRESS=4, CHECK=5, LOOKUP=6, REQUEST=7, WAIT_MEMORY=8,
    CONVERT_SEND=9, CONVERT_WAIT=10, RESPONSE=11, DRAIN=12;
  reg [3:0] state;
  reg [511:0] descriptor, cache_data;
  reg [31:0] row, column;
  reg [63:0] tag, row_offset, element_offset, address;
  reg [32:0] cache_address;
  reg cache_valid, fp16, response_error;
  reg [15:0] native_data;
  reg [31:0] converted_data;
  wire [63:0] base=descriptor[0+:64];
  wire [63:0] extent=descriptor[64+:64];
  wire [31:0] rows=descriptor[256+:32];
  wire [31:0] columns=descriptor[288+:32];
  wire [31:0] stride=descriptor[320+:32];
  wire [31:0] flags=descriptor[416+:32];
  wire [64:0] region_end={1'b0,base}+{1'b0,extent};
  wire [64:0] element_end={1'b0,element_offset}+65'd2;
  wire [32:0] aligned_address={address[32:6],6'd0};
  wire [8:0] word_bit={address[5:0],3'd0};
  wire convert_ready, convert_valid, convert_error;
  wire [31:0] converted;
  wire [63:0] converted_tag;

  anvil_q2_ht2_convert_pipe conversion (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(rst_n && !annul && state==CONVERT_SEND),.s_ready(convert_ready),
    .s_to_fp32(1'b1),.s_fp16(fp16),.s_data({16'd0,native_data}),.s_tag(tag),
    .m_ready(rst_n && !annul && state==CONVERT_WAIT),
    .m_valid(convert_valid),.m_error(convert_error),
    .m_data(converted),.m_tag(converted_tag)
  );
  assign s_ready=rst_n && !annul && state==IDLE;
  assign idle=s_ready;
  assign m_valid=rst_n && !annul && state==RESPONSE;
  assign m_error=m_valid && response_error;
  assign m_fp16=m_valid && !response_error && fp16;
  assign m_native=m_valid && !response_error ? native_data : 16'd0;
  assign m_fp32=m_valid && !response_error ? converted_data : 32'd0;
  assign m_tag=m_valid ? tag : 64'd0;
  assign mem_valid=rst_n && !annul && state==REQUEST;
  assign mem_address=mem_valid ? aligned_address : 33'd0;
  assign mem_rsp_ready=rst_n && (state==WAIT_MEMORY || state==DRAIN);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; descriptor<=0; cache_data<=0; row<=0; column<=0;
      tag<=0; row_offset<=0; element_offset<=0; address<=0;
      cache_address<=0; cache_valid<=0; fp16<=0; response_error<=0;
      native_data<=0; converted_data<=0;
    end else if (annul) begin
      cache_valid<=0; response_error<=0; native_data<=0; converted_data<=0;
      if ((state==WAIT_MEMORY || state==DRAIN) && !mem_rsp_valid) state<=DRAIN;
      else state<=IDLE;
    end else case (state)
      IDLE: if (s_valid) begin
        descriptor<=s_descriptor; row<=s_row; column<=s_column;
        tag<=s_tag; response_error<=0; native_data<=0; converted_data<=0;
        state<=VALIDATE;
      end
      VALIDATE: begin
        if (rows==0 || rows>151936 || columns==0 || columns>8960 ||
            row>=rows || column>=columns ||
            (flags!=32'h101 && flags!=32'h102) ||
            descriptor[128+:128]!=0 || descriptor[352+:64]!=0 ||
            descriptor[448+:64]!=0 || base[0] || stride[0] ||
            stride<(columns << 1) || extent==0 ||
            region_end>65'h200000000) begin
          response_error<=1; state<=RESPONSE;
        end else begin fp16<=flags[1:0]==2; state<=PRODUCT; end
      end
      PRODUCT: begin row_offset<={32'd0,row}*{32'd0,stride}; state<=OFFSET; end
      OFFSET: begin
        element_offset<=row_offset+{31'd0,column,1'b0}; state<=ADDRESS;
      end
      ADDRESS: begin address<=base+element_offset; state<=CHECK; end
      CHECK: begin
        if (element_end>{1'b0,extent} || (|address[63:33]) || address[0]) begin
          response_error<=1; state<=RESPONSE;
        end else state<=LOOKUP;
      end
      LOOKUP: begin
        if (cache_valid && cache_address==aligned_address) begin
          native_data<=cache_data[word_bit+:16]; state<=CONVERT_SEND;
        end else state<=REQUEST;
      end
      REQUEST: if (mem_ready) state<=WAIT_MEMORY;
      WAIT_MEMORY: if (mem_rsp_valid) begin
        if (mem_rsp_error) begin
          cache_valid<=0; response_error<=1; state<=RESPONSE;
        end else begin
          cache_data<=mem_rsp_data; cache_address<=aligned_address; cache_valid<=1;
          native_data<=mem_rsp_data[word_bit+:16]; state<=CONVERT_SEND;
        end
      end
      CONVERT_SEND: if (convert_ready) state<=CONVERT_WAIT;
      CONVERT_WAIT: if (convert_valid) begin
        response_error<=convert_error || converted_tag!=tag;
        converted_data<=converted; state<=RESPONSE;
      end
      RESPONSE: if (m_ready) state<=IDLE;
      DRAIN: if (mem_rsp_valid) state<=IDLE;
      default: begin response_error<=1; state<=RESPONSE; end
    endcase
  end
endmodule
