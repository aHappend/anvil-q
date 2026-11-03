module anvil_q2_fp_cache_codec #(
  parameter FP_FORMAT=0, CACHE_BLOCK=16,
  parameter SCB=(CACHE_BLOCK>0 && CACHE_BLOCK<=65536) ? CACHE_BLOCK : 1
)(
  input wire clk, rst_n,
  input wire in_valid, output wire in_ready,
  input wire in_decode,
  input wire [SCB*16-1:0] in_values,
  input wire [SCB*8-1:0] in_quantized,
  input wire [31:0] in_exponent,
  output wire out_valid, input wire out_ready,
  output wire [SCB*16-1:0] out_values,
  output wire [SCB*8-1:0] out_quantized,
  output wire [31:0] out_exponent,
  output wire out_error
);
  import anvil_q2_fp_pkg::*;
  localparam IDLE=0, SCAN=1, CHOOSE_EXP=2, CHECK_EXP=3,
    QUANTIZE=4, ROUND_INTEGER=5, EXPAND_INTEGER=6, RESCALE=7,
    CONVERT=8, STORE=9, OUTPUT=10, EXPAND_INPUT=11;
  localparam MIN_EXP=(FP_FORMAT==0) ? -139 : -30;
  localparam MAX_EXP=(FP_FORMAT==0) ? 122 : 10;
  reg [3:0] state;
  reg decode, failed;
  reg [SCB*16-1:0] values, reconstructed;
  reg [SCB*8-1:0] quantized;
  reg signed [12:0] exponent;
  reg [31:0] index, maximum, exponent_word;
  reg signed [31:0] integer_value;
  reg [31:0] expanded_value, scaled_value, integer_float, reconstructed_float;
  reg [15:0] reconstructed_half;
  wire [15:0] selected=values[index*16+:16];
  wire [31:0] selected32=expand16(selected,FP_FORMAT);
  wire [31:0] selected_abs={1'b0,selected32[30:0]};
  wire signed [12:0] negative_exponent=-exponent;
  wire signed [31:0] quantized_integer=fp_to_int_rne(scaled_value);
  wire [7:0] byte_value=quantized[index*8+:8];
  wire signed [31:0] decoded_integer={{24{byte_value[7]}},byte_value};
  wire [31:0] threshold=fp_scale2(32'h42fe0000,exponent);
  integer i, maximum_top;
  reg signed [12:0] initial_exponent;
  always @* begin
    maximum_top=0;
    for (i=0;i<24;i=i+1)
      if (fp_sig(maximum) & (24'd1 << i)) maximum_top=i;
    initial_exponent=fp_exp2(maximum)+maximum_top-13'sd6;
  end
  assign in_ready=rst_n && state==IDLE;
  assign out_valid=rst_n && state==OUTPUT;
  assign out_values=rst_n ? reconstructed : {SCB*16{1'b0}};
  assign out_quantized=rst_n ? quantized : {SCB*8{1'b0}};
  assign out_exponent=rst_n ? exponent_word : 32'd0;
  assign out_error=out_valid && failed;
  generate if ((FP_FORMAT!=0 && FP_FORMAT!=1) || CACHE_BLOCK<=0 ||
               CACHE_BLOCK>65536 || (CACHE_BLOCK & (CACHE_BLOCK-1))!=0 ||
               SCB!=CACHE_BLOCK) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_FP PARAMETER ERROR: cache codec geometry");
  end endgenerate
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; decode<=0; failed<=0; values<=0; reconstructed<=0;
      quantized<=0; exponent<=0; index<=0; maximum<=0; exponent_word<=0;
      integer_value<=0;
      expanded_value<=0; scaled_value<=0; integer_float<=0;
      reconstructed_float<=0; reconstructed_half<=0;
    end else case (state)
      IDLE: if (in_valid) begin
        decode<=in_decode; failed<=0; values<=in_values;
        reconstructed<=0; quantized<=in_quantized; maximum<=0; index<=0;
        if (in_decode) begin
          if ($signed(in_exponent)<MIN_EXP || $signed(in_exponent)>MAX_EXP ||
              in_exponent[31:16]!={16{in_exponent[15]}}) begin
            failed<=1; exponent_word<=in_exponent; state<=OUTPUT;
          end else begin
            exponent<=in_exponent[12:0]; exponent_word<=in_exponent;
            state<=EXPAND_INPUT;
          end
        end else state<=SCAN;
      end
      SCAN: begin
        if (!fp_is_finite(selected32)) begin failed<=1; state<=OUTPUT; end
        else begin
          if (selected_abs>maximum) maximum<=selected_abs;
          if (index+1<SCB) index<=index+1;
          else begin index<=0; state<=CHOOSE_EXP; end
        end
      end
      CHOOSE_EXP: begin
        if (maximum==0) exponent<=0;
        else exponent<=initial_exponent;
        state<=CHECK_EXP;
      end
      CHECK_EXP: begin
        if (maximum>threshold) begin
          exponent<=exponent+13'sd1;
          exponent_word<={{19{exponent[12]}},exponent}+32'd1;
        end else exponent_word<={{19{exponent[12]}},exponent};
        state<=EXPAND_INPUT;
      end
      EXPAND_INPUT: begin
        if (exponent<MIN_EXP || exponent>MAX_EXP) begin failed<=1; state<=OUTPUT; end
        else if (decode) begin
          if (byte_value==8'h80) begin failed<=1; state<=OUTPUT; end
          else begin integer_value<=decoded_integer; state<=EXPAND_INTEGER; end
        end else begin expanded_value<=selected32; state<=QUANTIZE; end
      end
      QUANTIZE: begin
        scaled_value<=fp_scale2(expanded_value,negative_exponent);
        state<=ROUND_INTEGER;
      end
      ROUND_INTEGER: begin
        if (!fp_is_finite(scaled_value) ||
                     quantized_integer < -32'sd127 || quantized_integer > 32'sd127) begin
          failed<=1; state<=OUTPUT;
        end else begin
          integer_value<=quantized_integer;
          quantized[index*8+:8]<=quantized_integer[7:0];
          state<=EXPAND_INTEGER;
        end
      end
      EXPAND_INTEGER: begin integer_float<=fp_from_int(integer_value); state<=RESCALE; end
      RESCALE: begin reconstructed_float<=fp_scale2(integer_float,exponent); state<=CONVERT; end
      CONVERT: begin reconstructed_half<=narrow16(reconstructed_float,FP_FORMAT); state<=STORE; end
      STORE: begin
        if (!fp_is_finite(reconstructed_float) ||
            !fp_is_finite(expand16(reconstructed_half,FP_FORMAT))) begin
          failed<=1; state<=OUTPUT;
        end else begin
          reconstructed[index*16+:16]<=reconstructed_half;
          if (index+1<SCB) begin index<=index+1; state<=EXPAND_INPUT; end
          else state<=OUTPUT;
        end
      end
      OUTPUT: if (out_ready) state<=IDLE;
      default: begin failed<=1; state<=OUTPUT; end
    endcase
  end
endmodule
