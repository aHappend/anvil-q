module anvil_q2_ht2_inverse (
  input wire clk, rst_n, annul, s_valid, m_ready,
  input wire s_rsqrt,
  input wire [31:0] s_data,
  input wire [63:0] s_tag,
  output wire s_ready, m_valid, m_error,
  output wire [31:0] m_data,
  output wire [63:0] m_tag
);
  import anvil_q2_ht2_fp_pkg::*;
  localparam [3:0] IDLE=0, CLASSIFY=1, SETUP=2, DIVIDE=3,
    SQRT_SETUP=4, SQRT_STEP=5, NORMALIZE=6, DENORMALIZE=7,
    PACK=8, RESPONSE=9;
  reg [3:0] state;
  reg rsqrt, sign_bit, response_error;
  reg [31:0] operand, response;
  reg [63:0] tag;
  reg [23:0] mantissa;
  reg signed [11:0] unbiased, exponent;
  reg [24:0] divisor, remainder;
  reg [55:0] quotient, radicand;
  reg [6:0] remaining;
  reg [27:0] root;
  reg [29:0] sqrt_remainder;
  reg division_sticky;
  reg [26:0] significand;

  wire [23:0] source_mantissa={(|operand[30:23]),operand[22:0]};
  wire [5:0] leading=leading32({source_mantissa,8'd0});
  wire signed [11:0] effective_exponent=operand[30:23]==0 ?
    12'sd1 : $signed({4'd0,operand[30:23]});
  wire [25:0] shifted_remainder={remainder,1'b0};
  wire [25:0] difference=shifted_remainder-{1'b0,divisor};
  wire quotient_bit=shifted_remainder>={1'b0,divisor};
  wire [29:0] sqrt_shifted={sqrt_remainder[27:0],radicand[55:54]};
  wire [29:0] sqrt_trial={root,2'b01};
  wire sqrt_bit=sqrt_shifted>=sqrt_trial;
  wire [29:0] sqrt_difference=sqrt_shifted-sqrt_trial;
  wire [27:0] candidate=rsqrt ? root : quotient[27:0];
  wire sticky=rsqrt ? (division_sticky || (|sqrt_remainder)) : (|remainder);
  wire [11:0] underflow_distance=12'sd1-exponent;
  wire [32:0] packed_result=pack_fp32(sign_bit,exponent,significand);

  assign s_ready=rst_n && !annul && state==IDLE;
  assign m_valid=rst_n && !annul && state==RESPONSE;
  assign m_error=m_valid && response_error;
  assign m_data=m_valid ? response : 32'd0;
  assign m_tag=m_valid ? tag : 64'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; rsqrt<=0; sign_bit<=0; response_error<=0;
      operand<=0; response<=0; tag<=0; mantissa<=0; unbiased<=0;
      exponent<=0; divisor<=0; remainder<=0; quotient<=0;
      radicand<=0; remaining<=0; root<=0; sqrt_remainder<=0;
      division_sticky<=0; significand<=0;
    end else if (annul) begin
      state<=IDLE; response_error<=0; response<=0;
    end else case (state)
      IDLE: if (s_valid) begin
        operand<=s_data; rsqrt<=s_rsqrt; tag<=s_tag;
        sign_bit<=s_data[31]; response_error<=0; response<=0;
        state<=CLASSIFY;
      end
      CLASSIFY: begin
        if (operand[30:23]==8'hff) begin
          response_error<=1;
          if ((|operand[22:0]) || (rsqrt && operand[31]))
            response<=32'h7fc00000;
          else response<={operand[31],31'd0};
          state<=RESPONSE;
        end else if (operand[30:0]==0) begin
          response<={operand[31],8'hff,23'd0};
          response_error<=1; state<=RESPONSE;
        end else if (rsqrt && operand[31]) begin
          response<=32'h7fc00000; response_error<=1; state<=RESPONSE;
        end else begin
          mantissa<=source_mantissa << leading;
          unbiased<=effective_exponent-12'sd127-$signed({6'd0,leading});
          state<=SETUP;
        end
      end
      SETUP: begin
        // Generate floor(2^50/M), or floor(2^77/(M*2^e[0])).
        divisor<=rsqrt ? ({1'b0,mantissa} << unbiased[0]) : {1'b0,mantissa};
        remainder<=1; quotient<=0;
        remaining<=rsqrt ? 7'd77 : 7'd50;
        exponent<=rsqrt ? 12'sd126-(unbiased >>> 1) : 12'sd126-unbiased;
        state<=DIVIDE;
      end
      DIVIDE: begin
        remainder<=quotient_bit ? difference[24:0] : shifted_remainder[24:0];
        quotient<={quotient[54:0],quotient_bit};
        remaining<=remaining-7'd1;
        if (remaining==1) begin
          if (rsqrt) state<=SQRT_SETUP;
          else state<=NORMALIZE;
        end
      end
      SQRT_SETUP: begin
        radicand<=quotient; division_sticky<=|remainder;
        root<=0; sqrt_remainder<=0; remaining<=28; state<=SQRT_STEP;
      end
      SQRT_STEP: begin
        sqrt_remainder<=sqrt_bit ? sqrt_difference : sqrt_shifted;
        root<={root[26:0],sqrt_bit};
        radicand<={radicand[53:0],2'd0};
        remaining<=remaining-7'd1;
        if (remaining==1) state<=NORMALIZE;
      end
      NORMALIZE: begin
        if (candidate[27]) begin
          significand<={candidate[27:2],((|candidate[1:0]) || sticky)};
          exponent<=exponent+12'sd1;
        end else
          significand<={candidate[26:1],(candidate[0] || sticky)};
        state<=DENORMALIZE;
      end
      DENORMALIZE: begin
        if (exponent<1) begin
          significand<=right_jam27(significand,underflow_distance);
          exponent<=1;
        end
        state<=PACK;
      end
      PACK: begin
        response<=packed_result[31:0]; response_error<=packed_result[32];
        state<=RESPONSE;
      end
      RESPONSE: if (m_ready) state<=IDLE;
      default: begin
        response<=32'h7fc00000; response_error<=1; state<=RESPONSE;
      end
    endcase
  end
endmodule
