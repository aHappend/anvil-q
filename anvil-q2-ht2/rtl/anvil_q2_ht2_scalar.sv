module anvil_q2_ht2_scalar (
  input wire clk, rst_n, annul, s_valid, m_ready,
  input wire [2:0] s_operation,
  input wire [31:0] s_a, s_b,
  input wire [63:0] s_tag,
  output wire s_ready, m_valid, m_error,
  output wire [31:0] m_data,
  output wire [63:0] m_tag
);
  import anvil_q2_ht2_fp_pkg::*;
  localparam [2:0] OP_ADD=0, OP_MUL=1, OP_RECIPROCAL=2,
    OP_RSQRT=3, OP_EXP=4, OP_SIGMOID=5;
  localparam [3:0] IDLE=0, CLASSIFY=1, RUN=2, MUL_WAIT=3,
    ADD_WAIT=4, INVERSE_SEND=5, INVERSE_WAIT=6,
    SCALE_DENORMALIZE=7, SCALE_PACK=8, RESPONSE=9;
  localparam [3:0] DIRECT=0, RANGE_MUL=1, RANGE_INTEGER=2,
    RANGE_HIGH=3, RANGE_SUB_HIGH=4, RANGE_LOW=5, RANGE_SUB_LOW=6,
    POLY_SETUP=7, POLY_MUL=8, POLY_ADD=9, POLY_NEXT=10,
    SIG_ADD=11, SIG_INVERSE=12, SIG_RESULT=13, SIG_MUL=14, FINISH=15;
  reg [3:0] state, pc, return_pc;
  reg [2:0] operation;
  reg [31:0] argument, second, temporary, reduced_high, residual;
  reg [31:0] accumulator, integer_fp32, exponential, response;
  reg [63:0] tag;
  reg negative, response_error;
  reg signed [9:0] integer_power;
  reg [3:0] coefficient_index, wait_cycles;
  reg signed [11:0] scale_exponent;
  reg [26:0] scale_significand;
  reg [31:0] arithmetic_a, arithmetic_b;
  reg launch_mul, launch_add;
  reg [3:0] next_pc;
  wire [31:0] multiplied, added, inverted;
  wire multiply_error, add_error, inverse_error;
  wire inverse_ready, inverse_valid;
  wire [63:0] inverse_tag;
  wire advance=rst_n && !annul;

  wire [11:0] integer_distance=12'd150-{4'd0,temporary[30:23]};
  wire [26:0] integer_bits=right_jam27(
    {(|temporary[30:23]),temporary[22:0],3'd0},integer_distance);
  wire [24:0] rounded_integer={1'b0,integer_bits[26:3]}+
    {24'd0,(integer_bits[2] &&
      (integer_bits[1] || integer_bits[0] || integer_bits[3]))};
  wire [8:0] integer_magnitude=rounded_integer[8:0];
  wire [5:0] integer_leading=leading32({23'd0,integer_magnitude});
  wire [31:0] normalized_integer={23'd0,integer_magnitude} << integer_leading;
  wire [8:0] encoded_integer_exponent=9'd158-{3'd0,integer_leading};
  wire signed [9:0] signed_integer=temporary[31] ?
    -$signed({1'b0,integer_magnitude}) : $signed({1'b0,integer_magnitude});
  wire [31:0] encoded_integer=integer_magnitude==0 ? 32'd0 :
    {temporary[31],encoded_integer_exponent[7:0],normalized_integer[30:8]};
  wire [11:0] scale_distance=12'sd1-scale_exponent;
  wire [32:0] scaled=pack_fp32(1'b0,scale_exponent,scale_significand);

  always @* begin
    arithmetic_a=0; arithmetic_b=0; launch_mul=0; launch_add=0;
    next_pc=FINISH;
    if (rst_n && !annul && state==RUN) begin
      case (pc)
        DIRECT: begin
          arithmetic_a=argument; arithmetic_b=second;
          launch_mul=operation==OP_MUL; launch_add=operation==OP_ADD;
        end
        RANGE_MUL: begin
          arithmetic_a=argument; arithmetic_b=32'h3fb8aa3b;
          launch_mul=1; next_pc=RANGE_INTEGER;
        end
        RANGE_HIGH: begin
          arithmetic_a=integer_fp32; arithmetic_b=32'h3f317200;
          launch_mul=1; next_pc=RANGE_SUB_HIGH;
        end
        RANGE_SUB_HIGH: begin
          arithmetic_a=argument; arithmetic_b={~temporary[31],temporary[30:0]};
          launch_add=1; next_pc=RANGE_LOW;
        end
        RANGE_LOW: begin
          arithmetic_a=integer_fp32; arithmetic_b=32'h35bfbe8e;
          launch_mul=1; next_pc=RANGE_SUB_LOW;
        end
        RANGE_SUB_LOW: begin
          arithmetic_a=reduced_high; arithmetic_b={~temporary[31],temporary[30:0]};
          launch_add=1; next_pc=POLY_SETUP;
        end
        POLY_MUL: begin
          arithmetic_a=accumulator; arithmetic_b=residual;
          launch_mul=1; next_pc=POLY_ADD;
        end
        POLY_ADD: begin
          arithmetic_a=temporary; arithmetic_b=exp_coefficient(int'(coefficient_index));
          launch_add=1; next_pc=POLY_NEXT;
        end
        SIG_ADD: begin
          arithmetic_a=32'h3f800000; arithmetic_b=exponential;
          launch_add=1; next_pc=SIG_INVERSE;
        end
        SIG_MUL: begin
          arithmetic_a=exponential; arithmetic_b=temporary;
          launch_mul=1; next_pc=FINISH;
        end
        default: begin end
      endcase
    end
  end

  anvil_q2_ht2_fp32_mul_pipe multiply (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .a(arithmetic_a),.b(arithmetic_b),
    .product(multiplied),.error(multiply_error)
  );
  anvil_q2_ht2_fp32_add_pipe addition (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .a(arithmetic_a),.b(arithmetic_b),.sum(added),.error(add_error)
  );
  anvil_q2_ht2_inverse inverse (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(rst_n && !annul && state==INVERSE_SEND),
    .s_ready(inverse_ready),.s_rsqrt(operation==OP_RSQRT),
    .s_data(operation==OP_SIGMOID ? temporary : argument),.s_tag(tag),
    .m_ready(rst_n && !annul && state==INVERSE_WAIT),
    .m_valid(inverse_valid),.m_error(inverse_error),
    .m_data(inverted),.m_tag(inverse_tag)
  );

  assign s_ready=rst_n && !annul && state==IDLE;
  assign m_valid=rst_n && !annul && state==RESPONSE;
  assign m_error=m_valid && response_error;
  assign m_data=m_valid ? response : 32'd0;
  assign m_tag=m_valid ? tag : 64'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; pc<=0; return_pc<=0; operation<=0;
      argument<=0; second<=0; temporary<=0; reduced_high<=0; residual<=0;
      accumulator<=0; integer_fp32<=0; exponential<=0; response<=0; tag<=0;
      negative<=0; response_error<=0; integer_power<=0;
      coefficient_index<=0; wait_cycles<=0;
      scale_exponent<=0; scale_significand<=0;
    end else if (annul) begin
      state<=IDLE; response<=0; response_error<=0; wait_cycles<=0;
    end else case (state)
      IDLE: if (s_valid) begin
        operation<=s_operation; second<=s_b; tag<=s_tag;
        argument<=s_operation==OP_SIGMOID ? {1'b1,s_a[30:0]} : s_a;
        negative<=s_a[31]; response<=0; response_error<=0;
        state<=CLASSIFY;
      end
      CLASSIFY: begin
        if (operation>OP_SIGMOID) begin
          response<=32'h7fc00000; response_error<=1; state<=RESPONSE;
        end else if (operation==OP_ADD || operation==OP_MUL) begin
          pc<=DIRECT; state<=RUN;
        end else if (operation==OP_RECIPROCAL || operation==OP_RSQRT)
          state<=INVERSE_SEND;
        else if (argument[30:23]==8'hff) begin
          response_error<=1; state<=RESPONSE;
          if (|argument[22:0]) response<=32'h7fc00000;
          else if (operation==OP_SIGMOID)
            response<=negative ? 32'd0 : 32'h3f800000;
          else response<=argument[31] ? 32'd0 : 32'h7f800000;
        end else if (argument[30:0]>31'h43000000) begin
          state<=RESPONSE;
          if (operation==OP_SIGMOID)
            response<=negative ? 32'd0 : 32'h3f800000;
          else begin
            response<=argument[31] ? 32'd0 : 32'h7f800000;
            response_error<=!argument[31];
          end
        end else if (argument[30:0]==0 && operation==OP_EXP) begin
          response<=32'h3f800000; state<=RESPONSE;
        end else begin pc<=RANGE_MUL; state<=RUN; end
      end
      RUN: begin
        if (launch_mul) begin
          wait_cycles<=7; return_pc<=next_pc; state<=MUL_WAIT;
        end else if (launch_add) begin
          wait_cycles<=4; return_pc<=next_pc; state<=ADD_WAIT;
        end else case (pc)
          RANGE_INTEGER: begin
            integer_power<=signed_integer; integer_fp32<=encoded_integer;
            pc<=RANGE_HIGH;
          end
          POLY_SETUP: begin
            residual<=temporary; accumulator<=exp_coefficient(12);
            coefficient_index<=11; pc<=POLY_MUL;
          end
          POLY_NEXT: begin
            accumulator<=temporary;
            if (coefficient_index==0) begin
              scale_significand<={1'b1,temporary[22:0],3'd0};
              scale_exponent<=$signed({4'd0,temporary[30:23]})+
                $signed({{2{integer_power[9]}},integer_power});
              state<=SCALE_DENORMALIZE;
            end else begin
              coefficient_index<=coefficient_index-4'd1; pc<=POLY_MUL;
            end
          end
          SIG_INVERSE: state<=INVERSE_SEND;
          SIG_RESULT: begin
            if (negative) pc<=SIG_MUL;
            else begin response<=temporary; state<=RESPONSE; end
          end
          FINISH: begin response<=temporary; state<=RESPONSE; end
          default: begin
            response<=32'h7fc00000; response_error<=1; state<=RESPONSE;
          end
        endcase
      end
      MUL_WAIT: begin
        wait_cycles<=wait_cycles-4'd1;
        if (wait_cycles==1) begin
          if (multiply_error) begin
            response<=multiplied; response_error<=1; state<=RESPONSE;
          end else begin temporary<=multiplied; pc<=return_pc; state<=RUN; end
        end
      end
      ADD_WAIT: begin
        wait_cycles<=wait_cycles-4'd1;
        if (wait_cycles==1) begin
          if (add_error) begin
            response<=added; response_error<=1; state<=RESPONSE;
          end else begin
            temporary<=added; pc<=return_pc; state<=RUN;
            if (return_pc==RANGE_LOW) reduced_high<=added;
          end
        end
      end
      INVERSE_SEND: if (inverse_ready) state<=INVERSE_WAIT;
      INVERSE_WAIT: if (inverse_valid) begin
        if (inverse_error || inverse_tag!=tag) begin
          response<=inverted; response_error<=1; state<=RESPONSE;
        end else if (operation==OP_SIGMOID) begin
          temporary<=inverted; pc<=SIG_RESULT; state<=RUN;
        end else begin response<=inverted; state<=RESPONSE; end
      end
      SCALE_DENORMALIZE: begin
        if (scale_exponent<1) begin
          scale_significand<=right_jam27(scale_significand,scale_distance);
          scale_exponent<=1;
        end
        state<=SCALE_PACK;
      end
      SCALE_PACK: begin
        if (scaled[32]) begin
          response<=scaled[31:0]; response_error<=1; state<=RESPONSE;
        end else if (operation==OP_SIGMOID) begin
          exponential<=scaled[31:0]; pc<=SIG_ADD; state<=RUN;
        end else begin response<=scaled[31:0]; state<=RESPONSE; end
      end
      RESPONSE: if (m_ready) state<=IDLE;
      default: begin
        response<=32'h7fc00000; response_error<=1; state<=RESPONSE;
      end
    endcase
  end
endmodule
