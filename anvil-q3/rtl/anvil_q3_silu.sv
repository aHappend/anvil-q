module anvil_q3_silu (
  input wire clk, rst_n, flush, start,
  input wire signed [31:0] x,
  output wire ready, done, error,
  output wire signed [31:0] value
);
  localparam [3:0] IDLE=0, EXP_LAUNCH=1, EXP_WAIT=2,
    DIVIDE_LAUNCH=3, DIVIDE_WAIT=4, MULTIPLY=5, FINALIZE=6;
  reg [3:0] state;
  reg done_reg, error_reg, negative;
  reg [31:0] magnitude, exponent_value;
  reg [24:0] sigmoid;
  reg [56:0] product;
  reg signed [31:0] value_reg;
  wire [31:0] input_magnitude = x[31] ? (~$unsigned(x)+32'd1) : $unsigned(x);
  wire signed [32:0] negative_magnitude = -$signed({1'b0,magnitude});
  wire exp_ready, exp_done, exp_error;
  wire [31:0] exp_value;
  wire divide_ready, divide_done, divide_error;
  wire [48:0] divide_quotient;
  wire [25:0] divide_remainder;
  wire [48:0] divide_numerator =
    negative ? {exponent_value[24:0],24'd0} : 49'd281474976710656;
  wire [25:0] divide_denominator = 26'd16777216+{1'b0,exponent_value[24:0]};
  wire [33:0] rounded_magnitude =
    {1'b0,product[56:24]}+{33'd0,product[23]};

  assign ready = rst_n && !flush && state==IDLE && exp_ready && divide_ready;
  assign done = rst_n && !flush && done_reg;
  assign error = done && error_reg;
  assign value = rst_n && !flush ? value_reg : 32'sd0;

  anvil_q3_exp exp_unit (
    .clk(clk),.rst_n(rst_n),.flush(flush),.start(state==EXP_LAUNCH),
    .x({{31{negative_magnitude[32]}},negative_magnitude}),
    .ready(exp_ready),.done(exp_done),.error(exp_error),.value(exp_value)
  );
  anvil_q3_divider #(.NUM_W(49),.DEN_W(26)) divider (
    .clk(clk),.rst_n(rst_n),.flush(flush),.start(state==DIVIDE_LAUNCH),
    .numerator(divide_numerator),.denominator(divide_denominator),
    .ready(divide_ready),.done(divide_done),.error(divide_error),
    .quotient(divide_quotient),.remainder(divide_remainder)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      done_reg <= 0;
      error_reg <= 0;
      negative <= 0;
      magnitude <= 0;
      exponent_value <= 0;
      sigmoid <= 0;
      product <= 0;
      value_reg <= 0;
    end else if (flush) begin
      state <= IDLE;
      done_reg <= 0;
      error_reg <= 0;
      value_reg <= 0;
    end else begin
      done_reg <= 0;
      error_reg <= 0;
      case (state)
        IDLE: if (start && ready) begin
          magnitude <= input_magnitude;
          negative <= x[31];
          state <= EXP_LAUNCH;
        end
        EXP_LAUNCH: if (exp_ready) state <= EXP_WAIT;
        EXP_WAIT: if (exp_done) begin
          if (exp_error) begin
            done_reg <= 1;
            error_reg <= 1;
            value_reg <= 0;
            state <= IDLE;
          end else begin
            exponent_value <= exp_value;
            state <= DIVIDE_LAUNCH;
          end
        end
        DIVIDE_LAUNCH: if (divide_ready) state <= DIVIDE_WAIT;
        DIVIDE_WAIT: if (divide_done) begin
          if (divide_error || divide_quotient > 49'd16777216) begin
            done_reg <= 1;
            error_reg <= 1;
            value_reg <= 0;
            state <= IDLE;
          end else begin
            sigmoid <= divide_quotient[24:0];
            state <= MULTIPLY;
          end
        end
        MULTIPLY: begin
          product <= magnitude*sigmoid;
          state <= FINALIZE;
        end
        FINALIZE: begin
          if (negative) begin
            if (rounded_magnitude >= 34'd2147483648) value_reg <= 32'sh80000000;
            else value_reg <= -$signed(rounded_magnitude[31:0]);
          end else begin
            if (rounded_magnitude > 34'd2147483647) value_reg <= 32'sh7fffffff;
            else value_reg <= $signed(rounded_magnitude[31:0]);
          end
          done_reg <= 1;
          state <= IDLE;
        end
        default: begin
          state <= IDLE;
          done_reg <= 1;
          error_reg <= 1;
          value_reg <= 0;
        end
      endcase
    end
  end
endmodule
