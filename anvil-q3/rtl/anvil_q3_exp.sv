module anvil_q3_exp (
  input wire clk, rst_n, flush, start,
  input wire signed [63:0] x,
  output wire ready, done, error,
  output wire [31:0] value
);
  localparam [3:0] IDLE=0, BOUNDARY=1, RANGE_LAUNCH=2, RANGE_WAIT=3,
    MULTIPLY=4, TERM_LAUNCH=5, TERM_WAIT=6, FINALIZE=7;
  reg [3:0] state;
  reg done_reg, error_reg;
  reg [31:0] value_reg, range_input, range_shift;
  reg [23:0] residue;
  reg [2:0] term_index;
  reg signed [31:0] term, total;
  reg [55:0] product;
  wire [31:0] term_magnitude = term[31] ? -term : term;
  wire divide_start = rst_n && !flush &&
    (state==RANGE_LAUNCH || state==TERM_LAUNCH);
  wire divide_ready, divide_done, divide_error;
  wire [31:0] divide_quotient;
  wire [23:0] divide_remainder;
  wire [31:0] divide_numerator =
    state==RANGE_LAUNCH ? range_input : product[55:24];
  wire [23:0] divide_denominator =
    state==RANGE_LAUNCH ? 24'd11629080 : {21'd0,term_index};
  wire signed [31:0] next_term =
    term[31] ? $signed(divide_quotient) : -$signed(divide_quotient);
  wire [20:0] range_magnitude = (~x[20:0])+21'd1;

  assign ready = rst_n && !flush && state==IDLE && divide_ready;
  assign done = rst_n && !flush && done_reg;
  assign error = done && error_reg;
  assign value = rst_n && !flush ? value_reg : 32'd0;

  anvil_q3_divider #(.NUM_W(32),.DEN_W(24)) divider (
    .clk(clk),.rst_n(rst_n),.flush(flush),.start(divide_start),
    .numerator(divide_numerator),.denominator(divide_denominator),
    .ready(divide_ready),.done(divide_done),.error(divide_error),
    .quotient(divide_quotient),.remainder(divide_remainder)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      done_reg <= 0;
      error_reg <= 0;
      value_reg <= 0;
      range_input <= 0;
      range_shift <= 0;
      residue <= 0;
      term_index <= 0;
      term <= 0;
      total <= 0;
      product <= 0;
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
          if (x < -64'sd1048576) begin
            value_reg <= 0;
            state <= BOUNDARY;
          end else if (x >= 0) begin
            value_reg <= 32'd16777216;
            state <= BOUNDARY;
          end else begin
            range_input <= {3'd0,range_magnitude,8'd0};
            state <= RANGE_LAUNCH;
          end
        end
        BOUNDARY: begin
          done_reg <= 1;
          state <= IDLE;
        end
        RANGE_LAUNCH: if (divide_ready) state <= RANGE_WAIT;
        RANGE_WAIT: if (divide_done) begin
          if (divide_error) begin
            done_reg <= 1;
            error_reg <= 1;
            value_reg <= 0;
            state <= IDLE;
          end else begin
            range_shift <= divide_quotient;
            residue <= divide_remainder;
            term <= 32'sd16777216;
            total <= 32'sd16777216;
            term_index <= 3'd1;
            state <= MULTIPLY;
          end
        end
        MULTIPLY: begin
          product <= term_magnitude*residue;
          state <= TERM_LAUNCH;
        end
        TERM_LAUNCH: if (divide_ready) state <= TERM_WAIT;
        TERM_WAIT: if (divide_done) begin
          if (divide_error) begin
            done_reg <= 1;
            error_reg <= 1;
            value_reg <= 0;
            state <= IDLE;
          end else begin
            term <= next_term;
            total <= total+next_term;
            if (term_index == 3'd6) state <= FINALIZE;
            else begin
              term_index <= term_index+1'b1;
              state <= MULTIPLY;
            end
          end
        end
        FINALIZE: begin
          value_reg <= total[31] ? 32'd0 : ($unsigned(total) >> range_shift);
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
