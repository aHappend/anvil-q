module anvil_q2_fp_scalar(
  input wire clk, rst_n,
  input wire in_valid, output wire in_ready,
  input wire [2:0] in_op,
  input wire [31:0] in_a, in_b,
  output wire out_valid, input wire out_ready,
  output wire [31:0] out_data,
  output wire out_error
);
  import anvil_q2_fp_pkg::*;
  localparam IDLE=0, ADD=1, MUL_EXACT=2, MUL_ROUND=3,
    DIV_PREPARE=4, DIV_ITERATE=5, DIV_ROUND=6,
    SQRT_PREPARE=7, SQRT_ITERATE=8, SQRT_ROUND=9, SCALE=10, OUTPUT=11;
  reg [3:0] state;
  reg [31:0] a, b, result;
  reg [63:0] product;
  reg sign_bit;
  reg signed [12:0] result_exponent;
  reg [24:0] remainder_div;
  reg [23:0] divisor;
  reg [26:0] quotient;
  reg [5:0] remaining;
  reg [53:0] radicand;
  reg [55:0] remainder_sqrt;
  reg [26:0] root;
  reg [23:0] a_mantissa, b_mantissa;
  reg signed [12:0] a_exponent, b_exponent;
  integer i, a_top, b_top;
  wire div_subtract=remainder_div>={1'b0,divisor};
  wire [24:0] div_difference=div_subtract ?
    remainder_div-{1'b0,divisor} : remainder_div;
  wire [55:0] sqrt_candidate={remainder_sqrt[53:0],radicand[53:52]};
  wire [55:0] sqrt_trial={27'd0,root,2'b01};
  wire sqrt_subtract=sqrt_candidate>=sqrt_trial;
  wire [55:0] sqrt_difference=sqrt_subtract ?
    sqrt_candidate-sqrt_trial : sqrt_candidate;
  wire [31:0] add_result=fp_add(a,b);

  assign in_ready=rst_n && state==IDLE;
  assign out_valid=rst_n && state==OUTPUT;
  assign out_data=rst_n ? result : 32'd0;
  assign out_error=out_valid && !fp_is_finite(result);

  always @* begin
    a_top=0; b_top=0;
    for (i=0;i<24;i=i+1) begin
      if (fp_sig(a) & (24'd1 << i)) a_top=i;
      if (fp_sig(b) & (24'd1 << i)) b_top=i;
    end
    a_mantissa=fp_sig(a) << (23-a_top);
    b_mantissa=fp_sig(b) << (23-b_top);
    a_exponent=fp_exp2(a)+a_top;
    b_exponent=fp_exp2(b)+b_top;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; a<=0; b<=0; result<=0; product<=0;
      sign_bit<=0; result_exponent<=0; remainder_div<=0; divisor<=0;
      quotient<=0; remaining<=0; radicand<=0; remainder_sqrt<=0; root<=0;
    end else case (state)
      IDLE: if (in_valid) begin
        a<=in_a; b<=in_b;
        case (in_op)
          0: state<=ADD;
          1: state<=MUL_EXACT;
          2: state<=DIV_PREPARE;
          3: state<=SQRT_PREPARE;
          4: state<=SCALE;
          default: begin result<=FP_NAN; state<=OUTPUT; end
        endcase
      end
      ADD: begin result<=add_result; state<=OUTPUT; end
      MUL_EXACT: begin product<=exact_product(a,b); state<=MUL_ROUND; end
      MUL_ROUND: begin result<=round_product(product); state<=OUTPUT; end
      DIV_PREPARE: begin
        sign_bit<=a[31]^b[31];
        if (fp_is_nan(a) || fp_is_nan(b) ||
            (fp_is_zero(a) && fp_is_zero(b)) || (fp_is_inf(a) && fp_is_inf(b))) begin
          result<=FP_NAN; state<=OUTPUT;
        end else if (fp_is_inf(a) || fp_is_zero(b)) begin
          result<={a[31]^b[31],8'hff,23'd0}; state<=OUTPUT;
        end else if (fp_is_zero(a) || fp_is_inf(b)) begin
          result<={a[31]^b[31],31'd0}; state<=OUTPUT;
        end else begin
          remainder_div<={1'b0,a_mantissa};
          divisor<=b_mantissa; quotient<=0; remaining<=27;
          result_exponent<=a_exponent-b_exponent-13'sd26;
          state<=DIV_ITERATE;
        end
      end
      DIV_ITERATE: begin
        quotient<={quotient[25:0],div_subtract};
        remainder_div<={div_difference[23:0],1'b0};
        remaining<=remaining-1'b1;
        if (remaining==1) state<=DIV_ROUND;
      end
      DIV_ROUND: begin
        result<=pack48(sign_bit,{21'd0,quotient[26:1],
                               (quotient[0] || (|remainder_div))},result_exponent);
        state<=OUTPUT;
      end
      SQRT_PREPARE: begin
        if (fp_is_nan(a) || (a[31] && !fp_is_zero(a))) begin
          result<=FP_NAN; state<=OUTPUT;
        end else if (fp_is_zero(a) || fp_is_inf(a)) begin result<=a; state<=OUTPUT; end
        else begin
          if (a_exponent[0]) radicand<={a_mantissa,30'd0};
          else radicand<={1'b0,a_mantissa,29'd0};
          result_exponent<=(a_exponent >>> 1)-13'sd26;
          remainder_sqrt<=0; root<=0; remaining<=27;
          state<=SQRT_ITERATE;
        end
      end
      SQRT_ITERATE: begin
        radicand<={radicand[51:0],2'd0};
        root<={root[25:0],sqrt_subtract};
        remainder_sqrt<=sqrt_difference;
        remaining<=remaining-1'b1;
        if (remaining==1) state<=SQRT_ROUND;
      end
      SQRT_ROUND: begin
        result<=pack48(1'b0,{21'd0,root[26:1],(root[0] || (|remainder_sqrt))},
                       result_exponent);
        state<=OUTPUT;
      end
      SCALE: begin result<=fp_scale2(a,$signed(b[12:0])); state<=OUTPUT; end
      OUTPUT: if (out_ready) state<=IDLE;
      default: begin result<=FP_NAN; state<=OUTPUT; end
    endcase
  end
endmodule
