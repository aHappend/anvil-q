module anvil_q2_ht_kv_codec #(
  parameter CACHE_BLOCK=16,
  parameter WORDS=(CACHE_BLOCK>=1 && CACHE_BLOCK<=128) ? CACHE_BLOCK : 1
) (
  input wire clk, rst_n, annul,
  input wire s_valid,
  output wire s_ready,
  input wire s_encode,
  input wire [1:0] s_mode,
  input wire [WORDS*32-1:0] s_data,
  input wire [WORDS*32-1:0] s_record,
  output wire m_valid,
  input wire m_ready,
  output wire [WORDS*32-1:0] m_data,
  output wire [WORDS*32-1:0] m_record,
  output wire [9:0] m_byte_length,
  output wire m_error
);
  localparam LEGAL = CACHE_BLOCK>=1 && CACHE_BLOCK<=128 &&
    (CACHE_BLOCK & (CACHE_BLOCK-1))==0 && WORDS==CACHE_BLOCK;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT PARAMETER ERROR: codec block size");
    assign s_ready = 0; assign m_valid = 0; assign m_data = 0;
    assign m_record = 0; assign m_byte_length = 0; assign m_error = 0;
  end else begin: implementation
    localparam [2:0] IDLE=0, SCAN=1, EXPONENT=2, ENCODE=3, DECODE=4, RESPONSE=5;
    reg [2:0] state;
    reg [1:0] mode;
    reg [8:0] index;
    reg [WORDS*32-1:0] source_data, record, decoded;
    reg [31:0] maximum;
    reg [4:0] exponent;
    reg [9:0] byte_length;
    reg failed;
    wire [31:0] word_value = source_data[index*32+:32];
    wire [31:0] magnitude = word_value[31] ? (~word_value+32'd1) : word_value;
    wire [32:0] rounded_magnitude = exponent==0 ? {1'b0,magnitude} :
      ({1'b0,magnitude}+(33'd1 << (exponent-5'd1))) >> exponent;
    wire [7:0] quantized_magnitude = rounded_magnitude>127 ?
      8'd127 : rounded_magnitude[7:0];
    wire [7:0] encoded_byte = word_value[31] ?
      (~quantized_magnitude+8'd1) : quantized_magnitude;
    wire [7:0] decoded_byte = record[(index+9'd1)*8+:8];
    wire signed [63:0] decoded_extended = {{56{decoded_byte[7]}},decoded_byte};
    wire signed [63:0] expanded = decoded_extended <<< exponent;
    wire signed [63:0] encoded_extended = {{56{encoded_byte[7]}},encoded_byte};
    wire signed [63:0] encoded_expanded = encoded_extended <<< exponent;

    function automatic [31:0] clamp32(input signed [63:0] value);
      begin
        if (value>64'sd2147483647) clamp32 = 32'h7fffffff;
        else if (value< -64'sd2147483648) clamp32 = 32'h80000000;
        else clamp32 = value[31:0];
      end
    endfunction

    assign s_ready = rst_n && !annul && state==IDLE;
    assign m_valid = rst_n && !annul && state==RESPONSE;
    assign m_data = m_valid ? decoded : {WORDS*32{1'b0}};
    assign m_record = m_valid ? record : {WORDS*32{1'b0}};
    assign m_byte_length = m_valid ? byte_length : 10'd0;
    assign m_error = m_valid && failed;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE; mode <= 0; index <= 0;
        source_data <= 0; record <= 0; decoded <= 0;
        maximum <= 0; exponent <= 0; byte_length <= 0; failed <= 0;
      end else if (annul) begin
        state <= IDLE; failed <= 0;
      end else case (state)
        IDLE: if (s_valid && s_ready) begin
          mode <= s_mode;
          index <= 0;
          source_data <= s_data;
          decoded <= 0;
          maximum <= 0;
          failed <= 0;
          exponent <= 0;
          record <= s_encode ? {WORDS*32{1'b0}} : s_record;
          case (s_mode)
            0: byte_length <= CACHE_BLOCK*4;
            1: byte_length <= CACHE_BLOCK*2;
            2: byte_length <= CACHE_BLOCK+1;
            default: byte_length <= 0;
          endcase
          if (s_mode>2) begin
            failed <= 1;
            state <= RESPONSE;
          end else if (s_encode) begin
            if (s_mode==2) state <= SCAN;
            else state <= ENCODE;
          end else begin
            if (s_mode==2) begin
              if (s_record[7:0]>25) begin failed <= 1; state <= RESPONSE; end
              else begin exponent <= s_record[4:0]; state <= DECODE; end
            end else state <= DECODE;
          end
        end
        SCAN: begin
          if (magnitude>maximum) maximum <= magnitude;
          if (index==CACHE_BLOCK-1) begin index <= 0; state <= EXPONENT; end
          else index <= index+9'd1;
        end
        EXPONENT: begin
          if ({1'b0,maximum}>(33'd127 << exponent) && exponent<25)
            exponent <= exponent+5'd1;
          else begin record[7:0] <= {3'd0,exponent}; state <= ENCODE; end
        end
        ENCODE: begin
          case (mode)
            0: begin
              record[index*32+:32] <= word_value;
              decoded[index*32+:32] <= word_value;
            end
            1: begin
              record[index*16+:16] <= word_value[15:0];
              decoded[index*32+:32] <= {16'd0,word_value[15:0]};
            end
            2: begin
              record[(index+9'd1)*8+:8] <= encoded_byte;
              decoded[index*32+:32] <= clamp32(encoded_expanded);
            end
            default: failed <= 1;
          endcase
          if (index==CACHE_BLOCK-1) state <= RESPONSE;
          else index <= index+9'd1;
        end
        DECODE: begin
          case (mode)
            0: decoded[index*32+:32] <= record[index*32+:32];
            1: decoded[index*32+:32] <= {16'd0,record[index*16+:16]};
            2: begin
              if (decoded_byte==8'h80) failed <= 1;
              decoded[index*32+:32] <= clamp32(expanded);
            end
            default: failed <= 1;
          endcase
          if (index==CACHE_BLOCK-1) state <= RESPONSE;
          else index <= index+9'd1;
        end
        RESPONSE: if (m_ready) state <= IDLE;
        default: begin failed <= 1; state <= RESPONSE; end
      endcase
    end
  end endgenerate
endmodule
