module anvil_q2_ht2_exp_datapath (
  input wire clk, rst_n, advance,
  input wire [31:0] s_data,
  output wire [31:0] m_data,
  output wire m_error
);
  import anvil_q2_ht2_fp_pkg::*;
  reg [31:0] argument1;
  reg special1, error1;
  reg [31:0] exceptional1;
  wire [31:0] ranged8, argument10, argument17, integer10;
  wire [31:0] high17, low17, low21, reduced21, residual25;
  wire range_error8, high_error17, low_error17, reduce_error21, reduce_error25;
  reg signed [9:0] power9;
  reg [8:0] magnitude9;
  reg integer_sign9;
  reg [31:0] encoded10;
  wire [11:0] distance8=12'd150-{4'd0,ranged8[30:23]};
  wire [26:0] bits8=right_jam27(
    {(|ranged8[30:23]),ranged8[22:0],3'd0},distance8);
  wire [24:0] rounded8={1'b0,bits8[26:3]}+
    {24'd0,(bits8[2] && (bits8[1] || bits8[0] || bits8[3]))};
  wire [5:0] leading9=leading32({23'd0,magnitude9});
  wire [31:0] normalized9={23'd0,magnitude9} << leading9;
  wire [8:0] exponent9=9'd158-{3'd0,leading9};
  wire [9:0] power157;
  wire [31:0] polynomial [0:12];
  wire [31:0] residual [0:12];
  wire [12:0] polynomial_error;
  wire range_error25, high_error25, low_error25, reduce_high_error25;
  wire [33:0] exceptional160;
  reg signed [11:0] exponent158, exponent159;
  reg [26:0] significand158, significand159;
  reg [31:0] result160;
  reg error160;
  wire error_polynomial160;
  wire [11:0] underflow_distance=12'sd1-exponent158;
  wire [32:0] packed_result=pack_fp32(1'b0,exponent159,significand159);
  wire input_special=s_data[30:23]==8'hff || s_data[30:0]>31'h43000000;
  wire input_nan=s_data[30:23]==8'hff && (|s_data[22:0]);
  genvar step;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      argument1<=0; special1<=0; error1<=0; exceptional1<=0;
      power9<=0; magnitude9<=0; integer_sign9<=0; encoded10<=0;
      exponent158<=0; exponent159<=0; significand158<=0; significand159<=0;
      result160<=0; error160<=0;
    end else if (advance) begin
      argument1<=input_special ? 32'd0 : s_data;
      special1<=input_special;
      error1<=s_data[30:23]==8'hff || (input_special && !s_data[31]);
      exceptional1<=input_nan ? 32'h7fc00000 :
        (s_data[31] ? 32'd0 : 32'h7f800000);
      magnitude9<=rounded8[8:0]; integer_sign9<=ranged8[31];
      power9<=ranged8[31] ? -$signed({1'b0,rounded8[8:0]}) :
        $signed({1'b0,rounded8[8:0]});
      encoded10<=magnitude9==0 ? 32'd0 :
        {integer_sign9,exponent9[7:0],normalized9[30:8]};
      exponent158<=$signed({4'd0,polynomial[12][30:23]})+
        $signed({{2{power157[9]}},power157});
      significand158<={1'b1,polynomial[12][22:0],3'd0};
      if (exponent158<1) begin
        exponent159<=1;
        significand159<=right_jam27(significand158,underflow_distance);
      end else begin exponent159<=exponent158; significand159<=significand158; end
      result160<=packed_result[31:0]; error160<=packed_result[32];
    end
  end
  anvil_q2_ht2_fp32_mul_pipe range_multiply (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .a(argument1),.b(32'h3fb8aa3b),.product(ranged8),.error(range_error8)
  );
  assign integer10=encoded10;
  anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(9)) argument_delay (
    .clk(clk),.rst_n(rst_n),.advance(advance),.s_data(argument1),.m_data(argument10)
  );
  anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(7)) high_argument_delay (
    .clk(clk),.rst_n(rst_n),.advance(advance),.s_data(argument10),.m_data(argument17)
  );
  anvil_q2_ht2_fp32_mul_pipe high_multiply (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .a(integer10),.b(32'h3f317200),.product(high17),.error(high_error17)
  );
  anvil_q2_ht2_fp32_mul_pipe low_multiply (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .a(integer10),.b(32'h35bfbe8e),.product(low17),.error(low_error17)
  );
  anvil_q2_ht2_fp32_add_pipe high_subtract (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .a(argument17),.b({~high17[31],high17[30:0]}),
    .sum(reduced21),.error(reduce_error21)
  );
  anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(4)) low_delay (
    .clk(clk),.rst_n(rst_n),.advance(advance),.s_data(low17),.m_data(low21)
  );
  anvil_q2_ht2_fp32_add_pipe low_subtract (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .a(reduced21),.b({~low21[31],low21[30:0]}),
    .sum(residual25),.error(reduce_error25)
  );
  anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(17)) range_error_delay (
    .clk(clk),.rst_n(rst_n),.advance(advance),.s_data(range_error8),.m_data(range_error25)
  );
  anvil_q2_ht2_delay #(.WIDTH(2),.STAGES(8)) multiply_error_delay (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .s_data({high_error17,low_error17}),.m_data({high_error25,low_error25})
  );
  anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(4)) subtract_error_delay (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .s_data(reduce_error21),.m_data(reduce_high_error25)
  );
  assign residual[0]=residual25;
  assign polynomial[0]=exp_coefficient(12);
  assign polynomial_error[0]=range_error25 || high_error25 || low_error25 ||
    reduce_high_error25 || reduce_error25;
  generate for (step=0;step<12;step=step+1) begin: horner
    wire [31:0] multiplied;
    wire multiply_error, addition_error, previous_error, delayed_multiply_error;
    anvil_q2_ht2_fp32_mul_pipe multiply (
      .clk(clk),.rst_n(rst_n),.advance(advance),
      .a(polynomial[step]),.b(residual[step]),
      .product(multiplied),.error(multiply_error)
    );
    anvil_q2_ht2_fp32_add_pipe addition (
      .clk(clk),.rst_n(rst_n),.advance(advance),
      .a(multiplied),.b(exp_coefficient(11-step)),
      .sum(polynomial[step+1]),.error(addition_error)
    );
    anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(11)) residual_delay (
      .clk(clk),.rst_n(rst_n),.advance(advance),
      .s_data(residual[step]),.m_data(residual[step+1])
    );
    anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(11)) previous_error_delay (
      .clk(clk),.rst_n(rst_n),.advance(advance),
      .s_data(polynomial_error[step]),.m_data(previous_error)
    );
    anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(4)) multiply_error_delay (
      .clk(clk),.rst_n(rst_n),.advance(advance),
      .s_data(multiply_error),.m_data(delayed_multiply_error)
    );
    assign polynomial_error[step+1]=previous_error || delayed_multiply_error || addition_error;
  end endgenerate
  anvil_q2_ht2_delay #(.WIDTH(10),.STAGES(148)) power_delay (
    .clk(clk),.rst_n(rst_n),.advance(advance),.s_data(power9),.m_data(power157)
  );
  anvil_q2_ht2_delay #(.WIDTH(34),.STAGES(159)) special_delay (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .s_data({special1,error1,exceptional1}),.m_data(exceptional160)
  );
  anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(3)) final_error_delay (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .s_data(polynomial_error[12]),.m_data(error_polynomial160)
  );
  assign m_data=!rst_n ? 32'd0 : (exceptional160[33] ? exceptional160[31:0] : result160);
  assign m_error=rst_n && (exceptional160[33] ? exceptional160[32] :
    (error160 || error_polynomial160));
endmodule
