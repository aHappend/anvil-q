module anvil_q2_ht2_descriptor_check #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  parameter NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, annul, s_valid,
  output wire s_ready,
  input wire [511:0] s_descriptor,
  input wire [8:0] s_index,
  input wire [5:0] s_mode,
  output wire m_valid,
  input wire m_ready,
  output wire m_error,
  output wire [1:0] m_regions,
  output wire [98:0] m_region_base,
  output wire [101:0] m_region_end
);
  localparam SAFE_GROUP=GROUP_SIZE>=1 ? GROUP_SIZE : 1;
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=1536 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=8960 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 &&
    NUM_KV_HEADS>=1 && NUM_KV_HEADS<=2 &&
    HEAD_DIM>=2 && HEAD_DIM<=128 && (HEAD_DIM & 1)==0 &&
    HIDDEN_SIZE==NUM_Q_HEADS*HEAD_DIM &&
    (NUM_KV_HEADS==1 || (NUM_KV_HEADS==2 && (NUM_Q_HEADS & 1)==0)) &&
    (HIDDEN_SIZE & 7)==0 && (INTERMEDIATE_SIZE & 7)==0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7)==0 &&
    GROUP_SIZE>=1 && GROUP_SIZE<=128 &&
    (GROUP_SIZE & (GROUP_SIZE-1))==0 &&
    (HIDDEN_SIZE & (SAFE_GROUP-1))==0 &&
    (INTERMEDIATE_SIZE & (SAFE_GROUP-1))==0 &&
    VOCAB_SIZE>=1 && VOCAB_SIZE<=151936 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: native descriptor geometry");
    assign s_ready=0; assign m_valid=0; assign m_error=0;
    assign m_regions=0; assign m_region_base=0; assign m_region_end=0;
  end else begin: implementation
    localparam GROUP_SHIFT=$clog2(GROUP_SIZE);
    localparam [2:0] IDLE=0, SHAPE=1, PRODUCTS=2, LENGTHS=3,
      BOUNDS=4, PACK=5, RESPONSE=6;
    reg [2:0] state;
    reg [511:0] descriptor;
    reg [8:0] index;
    reg [5:0] mode;
    reg failed, reserved, quantized;
    reg [1:0] regions;
    reg [98:0] bases;
    reg [101:0] ends;
    reg [31:0] expected_rows, expected_cols;
    reg expected_reserved, matrix;
    reg [1:0] expected_format;
    reg [31:0] main_bytes, zero_bytes, scale_bytes;
    reg [63:0] main_product, zero_product, scale_product;
    reg [63:0] main_minimum, zero_length, scale_length;
    wire [63:0] base=descriptor[0+:64];
    wire [63:0] extent=descriptor[64+:64];
    wire [63:0] zero_base=descriptor[128+:64];
    wire [63:0] scale_base=descriptor[192+:64];
    wire [31:0] rows=descriptor[256+:32];
    wire [31:0] cols=descriptor[288+:32];
    wire [31:0] stride=descriptor[320+:32];
    wire [31:0] zero_stride=descriptor[352+:32];
    wire [31:0] scale_stride=descriptor[384+:32];
    wire [31:0] flags=descriptor[416+:32];
    wire [31:0] groups=cols >> GROUP_SHIFT;
    wire [64:0] main_end={1'b0,base}+{1'b0,extent};
    wire [64:0] zero_end={1'b0,zero_base}+{1'b0,zero_length};
    wire [64:0] scale_end={1'b0,scale_base}+{1'b0,scale_length};
    wire native_format=flags[1:0]==1 || flags[1:0]==2;

    always @* begin
      expected_rows=1; expected_cols=HIDDEN_SIZE;
      expected_reserved=0; matrix=0;
      if (index==0) expected_rows=VOCAB_SIZE;
      else if (index==1) begin expected_rows=VOCAB_SIZE; matrix=1; end
      else if (index==3) begin
        expected_rows=MAX_SEQ_LEN; expected_cols=HEAD_DIM;
      end else if (index>=4 && index<16) expected_reserved=1;
      else if (index>=16 && index<16+16*NUM_LAYERS) begin
        case (index[3:0])
          0,3: begin expected_rows=HIDDEN_SIZE; matrix=1; end
          1,2: begin expected_rows=NUM_KV_HEADS*HEAD_DIM; matrix=1; end
          4,5: begin expected_rows=INTERMEDIATE_SIZE; matrix=1; end
          6: begin
            expected_rows=HIDDEN_SIZE; expected_cols=INTERMEDIATE_SIZE; matrix=1;
          end
          7,8,9: begin end
          10,11: expected_cols=NUM_KV_HEADS*HEAD_DIM;
          default: expected_reserved=1;
        endcase
      end else if (index>=16+16*NUM_LAYERS) expected_reserved=1;
      expected_format=mode[1:0];
      if (matrix && mode[3:2]==1) expected_format=0;
      if (matrix && mode[3:2]==2) expected_format=3;
    end

    assign s_ready=rst_n && !annul && state==IDLE;
    assign m_valid=rst_n && !annul && state==RESPONSE;
    assign m_error=m_valid && failed;
    assign m_regions=m_valid && !failed ? regions : 2'd0;
    assign m_region_base=m_valid && !failed ? bases : 99'd0;
    assign m_region_end=m_valid && !failed ? ends : 102'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; descriptor<=0; index<=0; mode<=0;
        failed<=0; reserved<=0; quantized<=0; regions<=0; bases<=0; ends<=0;
        main_bytes<=0; zero_bytes<=0; scale_bytes<=0;
        main_product<=0; zero_product<=0; scale_product<=0;
        main_minimum<=0; zero_length<=0; scale_length<=0;
      end else if (annul) begin
        state<=IDLE; failed<=0; regions<=0; bases<=0; ends<=0;
      end else case (state)
        IDLE: if (s_valid && s_ready) begin
          descriptor<=s_descriptor; index<=s_index; mode<=s_mode;
          failed<=0; regions<=0; bases<=0; ends<=0; state<=SHAPE;
        end
        SHAPE: begin
          reserved<=expected_reserved;
          quantized<=!native_format;
          failed<=index>=16+16*NUM_LAYERS ||
            (mode[1:0]!=1 && mode[1:0]!=2) || mode[3:2]==3 ||
            (expected_reserved ? descriptor!=0 :
              (rows!=expected_rows || cols!=expected_cols ||
                flags!={23'd0,1'b1,6'd0,expected_format} ||
                descriptor[448+:64]!=0 ||
                (native_format &&
                  (base[0] || stride[0] || zero_base!=0 || scale_base!=0 ||
                    zero_stride!=0 || scale_stride!=0)) ||
                (!native_format && (scale_base[0] || scale_stride[0]))));
          if (native_format) main_bytes<=cols << 1;
          else if (flags[1:0]==0) main_bytes<=(cols+32'd1) >> 1;
          else main_bytes<=(cols+32'd3) >> 2;
          zero_bytes<=flags[1:0]==0 ? (groups+32'd1) >> 1 :
            (groups+32'd3) >> 2;
          scale_bytes<=groups << 1;
          state<=PRODUCTS;
        end
        PRODUCTS: begin
          main_product<={32'd0,rows-32'd1}*{32'd0,stride};
          zero_product<={32'd0,rows-32'd1}*{32'd0,zero_stride};
          scale_product<={32'd0,rows-32'd1}*{32'd0,scale_stride};
          state<=LENGTHS;
        end
        LENGTHS: begin
          main_minimum<=main_product+{32'd0,main_bytes};
          zero_length<=zero_product+{32'd0,zero_bytes};
          scale_length<=scale_product+{32'd0,scale_bytes};
          state<=BOUNDS;
        end
        BOUNDS: begin
          if (!reserved &&
              (stride<main_bytes || extent<main_minimum || extent==0 ||
                main_end>65'h200000000 ||
                (quantized && (zero_stride<zero_bytes || scale_stride<scale_bytes ||
                  zero_end>65'h200000000 || scale_end>65'h200000000))))
            failed<=1;
          state<=PACK;
        end
        PACK: begin
          regions<=reserved ? 0 : (quantized ? 3 : 1);
          bases<={scale_base[32:0],zero_base[32:0],base[32:0]};
          ends<={scale_end[33:0],zero_end[33:0],main_end[33:0]};
          state<=RESPONSE;
        end
        RESPONSE: if (m_ready) state<=IDLE;
        default: begin failed<=1; regions<=0; state<=RESPONSE; end
      endcase
    end
  end endgenerate
endmodule
