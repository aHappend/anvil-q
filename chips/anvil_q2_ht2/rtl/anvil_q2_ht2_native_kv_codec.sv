module anvil_q2_ht2_native_kv_codec #(
  parameter CACHE_BLOCK=16,
  parameter WORDS=(CACHE_BLOCK>=1 && CACHE_BLOCK<=128) ? CACHE_BLOCK : 1
) (
  input wire clk, rst_n, annul, s_valid, s_encode, s_int8,
  input wire [WORDS*16-1:0] s_data,
  input wire [WORDS*16+15:0] s_record,
  output wire s_ready, m_valid, m_error,
  input wire m_ready,
  output wire [WORDS*16-1:0] m_data,
  output wire [WORDS*16+15:0] m_record,
  output wire [9:0] m_byte_length
);
  import anvil_q2_ht2_fp_pkg::*;
  localparam LEGAL=CACHE_BLOCK>=1 && CACHE_BLOCK<=128 &&
    (CACHE_BLOCK & (CACHE_BLOCK-1))==0 && WORDS==CACHE_BLOCK;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: native codec block");
    assign s_ready=0; assign m_valid=0; assign m_error=0;
    assign m_data=0; assign m_record=0; assign m_byte_length=0;
  end else begin: implementation
    localparam [4:0] IDLE=0, SCAN=1, SCALE_PREP=2, DIVIDE=3,
      SCALE_ROUND=4, QUANT_PREP=5, QUANT_ROUND=6, PRODUCT=7,
      LEADING=8, NORMALIZE=9, DENORMALIZE=10, ROUND=11, PACK=12,
      STORE=13, NEXT=14, COPY=15, DECODE=16, RESPONSE=17;
    reg [4:0] state, divide_return;
    reg encode, failed;
    reg [7:0] index;
    reg [WORDS*16-1:0] source, decoded;
    reg [WORDS*16+15:0] record;
    reg [14:0] maximum;
    reg [15:0] scale;
    reg [7:0] scale_exponent;
    reg [15:0] numerator, denominator, quotient;
    reg [16:0] remainder;
    reg [4:0] division_step;
    reg [7:0] code;
    reg [14:0] product, product_hold;
    reg [5:0] leading;
    reg [26:0] normalized, denormal;
    reg signed [11:0] product_exponent;
    reg [11:0] effective_exponent, rounded_exponent;
    reg [8:0] rounded;
    reg [15:0] reconstructed;
    reg [9:0] byte_length;

    wire [15:0] value=source[index*16+:16];
    wire [15:0] stored_value=record[index*16+:16];
    wire [7:0] stored_code=record[16+index*8+:8];
    wire [7:0] x_sig={(|value[14:7]),value[6:0]};
    wire [7:0] s_sig={(|scale[14:7]),scale[6:0]};
    wire [7:0] maximum_sig={(|maximum[14:7]),maximum[6:0]};
    wire [7:0] maximum_exp=maximum[14:7]==0 ? 8'd1 : maximum[14:7];
    wire [7:0] proposed_exp=maximum_exp>7 ?
      maximum_exp-8'd7+{7'd0,maximum_sig>=254} : 8'd1;
    wire [7:0] scale_shift=maximum_exp-proposed_exp;
    wire signed [11:0] x_factor=value[14:7]==0 ? -12'sd133 :
      $signed({4'd0,value[14:7]})-12'sd134;
    wire signed [11:0] s_factor=scale[14:7]==0 ? -12'sd133 :
      $signed({4'd0,scale[14:7]})-12'sd134;
    wire signed [11:0] exponent_gap=x_factor-s_factor;
    wire [16:0] trial={remainder[15:0],numerator[15]};
    wire subtract=trial>={1'b0,denominator};
    wire [17:0] twice_remainder={remainder,1'b0};
    wire round_up=twice_remainder>{2'd0,denominator} ||
      (twice_remainder=={2'd0,denominator} && quotient[0]);
    wire [16:0] rounded_quotient={1'b0,quotient}+{16'd0,round_up};
    wire [7:0] q_magnitude=rounded_quotient>127 ?
      8'd127 : rounded_quotient[7:0];
    wire [7:0] code_magnitude=code[7] ? (~code+8'd1) : code;
    wire [5:0] product_leading=leading32({product,17'd0});
    wire signed [11:0] biased_product=
      s_factor+12'sd141-$signed({6'd0,leading});
    wire signed [11:0] underflow_distance=12'sd1-product_exponent;
    wire [11:0] final_exponent=rounded_exponent+{11'd0,rounded[8]};
    wire [7:0] final_significand=rounded[8] ? rounded[8:1] : rounded[7:0];

    assign s_ready=rst_n && !annul && state==IDLE;
    assign m_valid=rst_n && !annul && state==RESPONSE;
    assign m_error=m_valid && failed;
    assign m_data=m_valid && !failed ? decoded : {WORDS*16{1'b0}};
    assign m_record=m_valid && !failed ? record : {(WORDS*16+16){1'b0}};
    assign m_byte_length=m_valid ? byte_length : 10'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; divide_return<=0; encode<=0; failed<=0;
        index<=0; source<=0; decoded<=0; record<=0; maximum<=0; scale<=0;
        scale_exponent<=0; numerator<=0; denominator<=0; quotient<=0;
        remainder<=0; division_step<=0; code<=0; product<=0; product_hold<=0;
        leading<=0; normalized<=0; denormal<=0; product_exponent<=0;
        effective_exponent<=0; rounded_exponent<=0; rounded<=0;
        reconstructed<=0; byte_length<=0;
      end else if (annul) begin
        state<=IDLE;
        failed<=0;
      end else case (state)
        IDLE: if (s_valid && s_ready) begin
          encode<=s_encode; source<=s_data;
          record<=s_encode ? {(WORDS*16+16){1'b0}} : s_record;
          decoded<=0; maximum<=0; index<=0; failed<=0;
          byte_length<=s_int8 ? 10'(WORDS+2) : 10'(WORDS*2);
          if (!s_int8) state<=COPY;
          else if (s_encode) state<=SCAN;
          else begin
            scale<=s_record[15:0];
            if (s_record[15] || s_record[14:0]==0 ||
                s_record[14:7]==8'hff) begin failed<=1; state<=RESPONSE; end
            else state<=DECODE;
          end
        end
        SCAN: begin
          if (value[14:7]==8'hff) failed<=1;
          if (value[14:0]>maximum) maximum<=value[14:0];
          if (index==WORDS-1) begin index<=0; state<=SCALE_PREP; end
          else index<=index+8'd1;
        end
        SCALE_PREP: begin
          if (failed) state<=RESPONSE;
          else if (maximum==0) begin
            scale<=16'h3f80;
            record[15:0]<=16'h3f80;
            state<=QUANT_PREP;
          end else begin
            numerator<={8'd0,maximum_sig} << scale_shift;
            denominator<=127; quotient<=0; remainder<=0; division_step<=15;
            scale_exponent<=proposed_exp;
            divide_return<=SCALE_ROUND;
            state<=DIVIDE;
          end
        end
        DIVIDE: begin
          numerator<={numerator[14:0],1'b0};
          quotient<={quotient[14:0],subtract};
          remainder<=subtract ? trial-{1'b0,denominator} : trial;
          if (division_step==0) state<=divide_return;
          else division_step<=division_step-5'd1;
        end
        SCALE_ROUND: begin
          if (rounded_quotient==0) begin
            scale<=16'h0001; record[15:0]<=16'h0001;
          end else if (rounded_quotient>=256) begin
            scale<={1'b0,(scale_exponent+8'd1),7'd0};
            record[15:0]<={1'b0,(scale_exponent+8'd1),7'd0};
          end else if (rounded_quotient<128) begin
            scale<={9'd0,rounded_quotient[6:0]};
            record[15:0]<={9'd0,rounded_quotient[6:0]};
          end else begin
            scale<={1'b0,scale_exponent,rounded_quotient[6:0]};
            record[15:0]<={1'b0,scale_exponent,rounded_quotient[6:0]};
          end
          state<=QUANT_PREP;
        end
        QUANT_PREP: begin
          if (x_sig==0 || exponent_gap<=-9) begin code<=0; state<=PRODUCT; end
          else if (exponent_gap>=8) begin
            code<=value[15] ? 8'h81 : 8'h7f;
            state<=PRODUCT;
          end else begin
            if (exponent_gap>=0) begin
              numerator<={8'd0,x_sig} << exponent_gap;
              denominator<={8'd0,s_sig};
            end else begin
              numerator<={8'd0,x_sig};
              denominator<={8'd0,s_sig} << (-exponent_gap);
            end
            quotient<=0; remainder<=0; division_step<=15;
            divide_return<=QUANT_ROUND;
            state<=DIVIDE;
          end
        end
        QUANT_ROUND: begin
          code<=value[15] ? (~q_magnitude+8'd1) : q_magnitude;
          state<=PRODUCT;
        end
        DECODE: begin
          if (stored_code==8'h80) begin failed<=1; state<=RESPONSE; end
          else begin code<=stored_code; state<=PRODUCT; end
        end
        PRODUCT: begin
          product<=code_magnitude[6:0]*s_sig;
          if (encode) record[16+index*8+:8]<=code;
          state<=LEADING;
        end
        LEADING: begin
          leading<=product_leading;
          product_hold<=product;
          state<=NORMALIZE;
        end
        NORMALIZE: begin
          normalized<={product_hold,12'd0} << leading;
          product_exponent<=product_hold==0 ? 12'sd1 : biased_product;
          state<=DENORMALIZE;
        end
        DENORMALIZE: begin
          if (product_exponent<1) begin
            denormal<=right_jam27(normalized,underflow_distance);
            effective_exponent<=1;
          end else begin
            denormal<=normalized;
            effective_exponent<=product_exponent;
          end
          state<=ROUND;
        end
        ROUND: begin
          rounded<={1'b0,denormal[26:19]}+
            {8'd0,(denormal[18] && ((|denormal[17:0]) || denormal[19]))};
          rounded_exponent<=effective_exponent;
          state<=PACK;
        end
        PACK: begin
          if (final_exponent>=255 && final_significand!=0) begin
            failed<=1;
            reconstructed<={code[7],8'hff,7'd0};
          end else if (final_significand==0) reconstructed<=0;
          else if (!final_significand[7])
            reconstructed<={code[7],8'd0,final_significand[6:0]};
          else reconstructed<={code[7],final_exponent[7:0],final_significand[6:0]};
          state<=STORE;
        end
        STORE: begin
          decoded[index*16+:16]<=reconstructed;
          state<=NEXT;
        end
        NEXT: begin
          if (index==WORDS-1) state<=RESPONSE;
          else begin
            index<=index+8'd1;
            if (encode) state<=QUANT_PREP;
            else state<=DECODE;
          end
        end
        COPY: begin
          if (encode) begin
            if (value[14:7]==8'hff) failed<=1;
            record[index*16+:16]<=value;
            decoded[index*16+:16]<=value;
          end else begin
            if (stored_value[14:7]==8'hff) failed<=1;
            decoded[index*16+:16]<=stored_value;
          end
          if (index==WORDS-1) state<=RESPONSE;
          else index<=index+8'd1;
        end
        RESPONSE: if (m_ready) state<=IDLE;
        default: begin failed<=1; state<=RESPONSE; end
      endcase
    end
  end endgenerate
endmodule
