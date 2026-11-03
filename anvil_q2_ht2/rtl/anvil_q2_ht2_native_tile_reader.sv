module anvil_q2_ht2_native_tile_reader (
  input wire clk, rst_n, annul, s_valid,
  output wire s_ready,
  input wire [511:0] s_descriptor,
  input wire [31:0] s_row, s_column,
  input wire [7:0] s_count,
  input wire [63:0] s_tag,
  output wire m_valid,
  input wire m_ready,
  output wire m_error, m_fp16,
  output wire [2047:0] m_data,
  output wire [63:0] m_tag,
  output wire idle,
  output wire mem_valid,
  input wire mem_ready,
  output wire [32:0] mem_address,
  input wire mem_rsp_valid, mem_rsp_error,
  output wire mem_rsp_ready,
  input wire [511:0] mem_rsp_data
);
  localparam [3:0] IDLE=0, VALIDATE=1, PRODUCT=2, OFFSET=3,
    ADDRESS=4, CHECK=5, LOOKUP=6, REQUEST=7, WAIT_MEMORY=8,
    NEXT=9, RESPONSE=10, DRAIN=11;
  reg [3:0] state;
  reg [511:0] descriptor;
  reg [31:0] row, column;
  reg [7:0] count;
  reg [63:0] tag, row_offset, element_offset, address;
  reg [2:0] beat, beats, replacement;
  reg failed, fp16;
  reg [2559:0] image;
  reg [7:0] cached;
  reg [26:0] cache_address [0:7];
  reg [511:0] cache_data [0:7];
  reg hit;
  reg [2:0] hit_index;
  integer i, q;
  wire [63:0] base=descriptor[0+:64];
  wire [63:0] extent=descriptor[64+:64];
  wire [31:0] rows=descriptor[256+:32], columns=descriptor[288+:32];
  wire [31:0] stride=descriptor[320+:32], flags=descriptor[416+:32];
  wire [64:0] region_end={1'b0,base}+{1'b0,extent};
  wire [64:0] element_end={1'b0,element_offset}+{56'd0,count,1'b0};
  wire [32:0] request_address={address[32:6],6'd0}+{24'd0,beat,6'd0};
  wire [9:0] covered_bytes={4'd0,address[5:0]}+{1'b0,count,1'b0}+10'd63;
  wire [2559:0] shifted_image=image >> {address[5:0],3'd0};
  wire available=rst_n && !annul;

  always @* begin
    hit=0; hit_index=0;
    for (i=0;i<8;i=i+1)
      if (!hit && cached[i] && cache_address[i]==request_address[32:6]) begin
        hit=1; hit_index=3'(i);
      end
  end
  assign s_ready=available && state==IDLE;
  assign idle=rst_n && state==IDLE;
  assign m_valid=available && state==RESPONSE;
  assign m_error=m_valid && failed;
  assign m_fp16=m_valid && !failed && fp16;
  assign m_data=m_valid && !failed ? shifted_image[2047:0] : 2048'd0;
  assign m_tag=m_valid ? tag : 64'd0;
  assign mem_valid=available && state==REQUEST;
  assign mem_address=mem_valid ? request_address : 33'd0;
  assign mem_rsp_ready=rst_n && (state==WAIT_MEMORY || state==DRAIN);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; descriptor<=0; row<=0; column<=0; count<=0;
      tag<=0; row_offset<=0; element_offset<=0; address<=0;
      beat<=0; beats<=0; replacement<=0; failed<=0; fp16<=0;
      image<=0; cached<=0;
      for (q=0;q<8;q=q+1) begin cache_address[q]<=0; cache_data[q]<=0; end
    end else if (annul) begin
      cached<=0;
      if ((state==WAIT_MEMORY || state==DRAIN) &&
          !(mem_rsp_valid && mem_rsp_ready)) state<=DRAIN;
      else state<=IDLE;
    end else case (state)
      IDLE: if (s_valid) begin
        descriptor<=s_descriptor; row<=s_row; column<=s_column;
        count<=s_count; tag<=s_tag; beat<=0; failed<=0; image<=0;
        state<=VALIDATE;
      end
      VALIDATE: begin
        if (count==0 || count>128 || rows==0 || rows>151936 ||
            columns==0 || columns>8960 || row>=rows ||
            {1'b0,column}+{25'd0,count}>{1'b0,columns} ||
            (flags!=32'h101 && flags!=32'h102) ||
            descriptor[128+:128]!=0 || descriptor[352+:64]!=0 ||
            descriptor[448+:64]!=0 || base[0] || stride[0] ||
            stride<(columns << 1) || extent==0 ||
            region_end>65'h200000000) begin failed<=1; state<=RESPONSE; end
        else begin fp16<=flags[1:0]==2; state<=PRODUCT; end
      end
      PRODUCT: begin row_offset<={32'd0,row}*{32'd0,stride}; state<=OFFSET; end
      OFFSET: begin element_offset<=row_offset+{31'd0,column,1'b0}; state<=ADDRESS; end
      ADDRESS: begin address<=base+element_offset; state<=CHECK; end
      CHECK: begin
        if (element_end>{1'b0,extent} || (|address[63:33]) || address[0]) begin
          failed<=1; state<=RESPONSE;
        end else begin beats<=covered_bytes[8:6]; state<=LOOKUP; end
      end
      LOOKUP: begin
        if (hit) begin image[512*beat+:512]<=cache_data[hit_index]; state<=NEXT; end
        else state<=REQUEST;
      end
      REQUEST: if (mem_ready) state<=WAIT_MEMORY;
      WAIT_MEMORY: if (mem_rsp_valid) begin
        if (mem_rsp_error) begin failed<=1; cached<=0; state<=RESPONSE; end
        else begin
          image[512*beat+:512]<=mem_rsp_data;
          cache_data[replacement]<=mem_rsp_data;
          cache_address[replacement]<=request_address[32:6]; cached[replacement]<=1;
          replacement<=replacement+3'd1; state<=NEXT;
        end
      end
      NEXT: begin
        if (beat+3'd1==beats) state<=RESPONSE;
        else begin beat<=beat+3'd1; state<=LOOKUP; end
      end
      RESPONSE: if (m_ready) state<=IDLE;
      DRAIN: if (mem_rsp_valid) state<=IDLE;
      default: begin failed<=1; cached<=0; state<=RESPONSE; end
    endcase
  end
endmodule
