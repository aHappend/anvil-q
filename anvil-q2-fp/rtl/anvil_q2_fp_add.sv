module anvil_q2_fp_add(
  input wire clk, rst_n,
  input wire in_valid, output wire in_ready,
  input wire [31:0] in_a, in_b,
  output wire out_valid, input wire out_ready,
  output wire [31:0] out_data,
  output wire out_error
);
  import anvil_q2_fp_pkg::*;
  localparam IDLE=0, ORDER=1, DISTANCE=2, ALIGN=3, SUM=4,
    LOCATE=5, NORMALIZE=6, ROUND=7, PACK=8, OUTPUT=9;
  reg [3:0] state;
  reg [31:0] a, b, result, special_result;
  reg special, sign_bit, subtract;
  reg [26:0] big_mantissa, small_mantissa, aligned_small, normalized;
  reg [27:0] total;
  reg [24:0] rounded;
  reg [8:0] big_exponent, small_exponent, distance, exponent;
  reg [4:0] normalize_shift;

  wire a_is_big=a[30:0]>=b[30:0];
  wire [31:0] big=a_is_big ? a : b;
  wire [31:0] smaller=a_is_big ? b : a;
  wire [8:0] distance_next=big_exponent-small_exponent;
  wire [26:0] aligned_next=shift_jam27(small_mantissa,{23'd0,distance});
  wire [27:0] total_next=subtract ?
    {1'b0,big_mantissa}-{1'b0,aligned_small} :
    {1'b0,big_mantissa}+{1'b0,aligned_small};

  function automatic [4:0] leading_zeros27(input [26:0] value);
    reg [31:0] shifted;
    reg [4:0] count;
    begin
      shifted={value,5'd0}; count=0;
      if (shifted[31:16]==0) begin shifted=shifted << 16; count=count+5'd16; end
      if (shifted[31:24]==0) begin shifted=shifted << 8; count=count+5'd8; end
      if (shifted[31:28]==0) begin shifted=shifted << 4; count=count+5'd4; end
      if (shifted[31:30]==0) begin shifted=shifted << 2; count=count+5'd2; end
      if (!shifted[31]) count=count+5'd1;
      leading_zeros27=count;
    end
  endfunction

  wire [4:0] leading=leading_zeros27(total[26:0]);
  wire [8:0] available_shift=big_exponent-9'd1;
  wire [4:0] shift_next=(available_shift<{4'd0,leading}) ?
    available_shift[4:0] : leading;
  wire [26:0] normalized_next=total[27] ?
    {total[27:2],(total[1]|total[0])} : total[26:0] << normalize_shift;
  wire [8:0] normalized_exponent=total[27] ?
    big_exponent+9'd1 : big_exponent-{4'd0,normalize_shift};
  wire round_up=normalized[2] && ((|normalized[1:0]) || normalized[3]);
  wire [24:0] rounded_next={1'b0,normalized[26:3]}+{24'd0,round_up};
  wire [8:0] packed_exponent=exponent+{8'd0,rounded[24]};
  wire [23:0] packed_mantissa=rounded[24] ? rounded[24:1] : rounded[23:0];
  wire [7:0] encoded_exponent=(packed_exponent==1 && !packed_mantissa[23]) ?
    8'd0 : packed_exponent[7:0];

  assign in_ready=rst_n && state==IDLE;
  assign out_valid=rst_n && state==OUTPUT;
  assign out_data=rst_n ? result : 32'd0;
  assign out_error=out_valid && !fp_is_finite(result);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; a<=0; b<=0; result<=0; special_result<=0;
      special<=0; sign_bit<=0; subtract<=0;
      big_mantissa<=0; small_mantissa<=0; aligned_small<=0; normalized<=0;
      total<=0; rounded<=0; big_exponent<=0; small_exponent<=0;
      distance<=0; exponent<=0; normalize_shift<=0;
    end else case (state)
      IDLE: if (in_valid) begin a<=in_a; b<=in_b; state<=ORDER; end
      ORDER: begin
        sign_bit<=big[31]; subtract<=big[31]!=smaller[31];
        big_mantissa<={fp_sig(big),3'd0};
        small_mantissa<={fp_sig(smaller),3'd0};
        big_exponent<=big[30:23]==0 ? 9'd1 : {1'b0,big[30:23]};
        small_exponent<=smaller[30:23]==0 ? 9'd1 : {1'b0,smaller[30:23]};
        special<=1;
        if (fp_is_nan(a) || fp_is_nan(b) ||
            (fp_is_inf(a) && fp_is_inf(b) && a[31]!=b[31]))
          special_result<=FP_NAN;
        else if (fp_is_inf(a)) special_result<=a;
        else if (fp_is_inf(b)) special_result<=b;
        else if (fp_is_zero(a) && fp_is_zero(b))
          special_result<={a[31]&b[31],31'd0};
        else begin special<=0; special_result<=0; end
        state<=DISTANCE;
      end
      DISTANCE: begin distance<=distance_next; state<=ALIGN; end
      ALIGN: begin aligned_small<=aligned_next; state<=SUM; end
      SUM: begin total<=total_next; state<=LOCATE; end
      LOCATE: begin
        normalize_shift<=(total[27] || total==0) ? 5'd0 : shift_next;
        state<=NORMALIZE;
      end
      NORMALIZE: begin
        normalized<=normalized_next; exponent<=normalized_exponent; state<=ROUND;
      end
      ROUND: begin rounded<=rounded_next; state<=PACK; end
      PACK: begin
        if (special) result<=special_result;
        else if (total==0) result<=FP_ZERO;
        else if (packed_exponent>=9'd255) result<={sign_bit,8'hff,23'd0};
        else result<={sign_bit,encoded_exponent,packed_mantissa[22:0]};
        state<=OUTPUT;
      end
      OUTPUT: if (out_ready) state<=IDLE;
      default: begin result<=FP_NAN; state<=OUTPUT; end
    endcase
  end
endmodule
